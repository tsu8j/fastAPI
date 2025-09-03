#!/usr/bin/env python3
import os, json, datetime, sys, re, math
import pandas as pd
import requests

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
EXCEL_PATH = os.getenv("EXCEL_PATH", "TaskManagerAPI_TestPack.xlsx")
RESULTS_DIR = os.getenv("RESULTS_DIR", "./results")
EXECUTOR = os.getenv("EXECUTOR", "Jun")
RUN_ID = os.getenv("RUN_ID") or datetime.datetime.now().strftime("run-%Y%m%d-%H%M%S")

def ensure_dir(p):
    if not os.path.isdir(p):
        os.makedirs(p, exist_ok=True)

def templ(s, vars):
    if not isinstance(s, str):
        return s
    out = s
    for k, v in vars.items():
        out = out.replace("{{"+k+"}}", str(v))
    return out

def is_nan(x):
    try:
        return isinstance(x, float) and math.isnan(x)
    except Exception:
        return False

def body_to_bytes(body):
    # Convert a "body" that might be None/NaN/str/dict/list into bytes or None
    if body is None or is_nan(body):
        return None
    if isinstance(body, (dict, list)):
        return json.dumps(body, ensure_ascii=False).encode("utf-8")
    if isinstance(body, (int, float)) and not is_nan(body):
        # unlikely but if a number slipped in, send it as a JSON number
        return str(body).encode("utf-8")
    if isinstance(body, str):
        s = body.strip()
        if not s or s.lower() == "null":
            return None
        return s.encode("utf-8")
    # Fallback
    try:
        return json.dumps(body, ensure_ascii=False).encode("utf-8")
    except Exception:
        return None

def do_request(method, url, body):
    headers = {}
    data = body_to_bytes(body)
    if data is not None:
        headers["Content-Type"] = "application/json"
    try:
        resp = requests.request(method=method, url=url, headers=headers, data=data, timeout=15)
        status = str(resp.status_code)
        text = resp.text
    except requests.exceptions.RequestException as e:
        status = "ERR"
        text = str(e)
    return status, text

def extract_save_var(body_text, keys=("id","task_id")):
    try:
        obj = json.loads(body_text)
    except Exception:
        return None
    for k in keys:
        if isinstance(obj, dict) and k in obj:
            return obj[k]
    return None

def upsert_report(df_report, key, value):
    mask = df_report["項目"] == key
    if mask.any():
        df_report.loc[mask, "値"] = value
    else:
        df_report.loc[len(df_report)] = [key, value]

def main():
    ensure_dir(RESULTS_DIR)
    if not os.path.exists(EXCEL_PATH):
        print(f"[ERROR] Excel not found: {EXCEL_PATH}", file=sys.stderr); sys.exit(1)

    xls = pd.ExcelFile(EXCEL_PATH)
    if "06_Automation" not in xls.sheet_names:
        print("[ERROR] 06_Automation シートがありません。先に generate_automation_from_02.py を実行してください。", file=sys.stderr)
        sys.exit(1)
    df_auto = pd.read_excel(xls, sheet_name="06_Automation")

    exec_cols = ["RUN_ID","実行日","実行者","テストケースID","実際の結果","ステータス（Pass/Fail）","証跡（スクショ/ログのパス）","備考"]
    if "03_ExecutionLog" in xls.sheet_names:
        df_exec = pd.read_excel(xls, sheet_name="03_ExecutionLog")
        if "RUN_ID" not in df_exec.columns:
            df_exec["RUN_ID"] = ""
            df_exec = df_exec.reindex(columns=exec_cols, fill_value="")
    else:
        df_exec = pd.DataFrame(columns=exec_cols)

    if "02_TestCases" in xls.sheet_names:
        df_tc = pd.read_excel(xls, sheet_name="02_TestCases")
        total_cases = len(df_tc)
    else:
        total_cases = None

    vars_store = {}

    run_rows = []
    for idx, row in df_auto.iterrows():
        tcid = str(row.get("テストケースID","")).strip()
        method = str(row.get("メソッド","GET")).strip().upper()
        url_path = row.get("URL","/")
        body_raw = row.get("ボディ(JSON)","")
        expect_status = str(row.get("期待ステータス","200")).strip()
        save_as = str(row.get("save_as（任意）","")).strip()
        expect_contains = str(row.get("expect_contains（任意）","")).strip()

        if is_nan(url_path):
            url_path = "/"
        if is_nan(body_raw):
            body_raw = ""

        url = BASE_URL + templ(str(url_path), vars_store)
        body_str = templ(body_raw, vars_store) if isinstance(body_raw, str) else body_raw

        status, text = do_request(method, url, body_str)

        base = re.sub(r'[^A-Za-z0-9_\-]+','_', f"{idx+1:02d}_{tcid}")
        with open(os.path.join(RESULTS_DIR, f"{base}.status"), "w", encoding="utf-8") as f:
            f.write(status)
        with open(os.path.join(RESULTS_DIR, f"{base}.json"), "w", encoding="utf-8") as f:
            f.write(text)

        if save_as:
            val = extract_save_var(text, keys=("id","task_id"))
            if val is not None:
                vars_store[save_as] = val

        ok_set = set([s.strip() for s in str(expect_status).split("|") if s.strip()])
        pass_status = (status in ok_set) if ok_set else (status == "200")
        pass_contains = True
        if expect_contains:
            pass_contains = (expect_contains in text)
        verdict = "Pass" if (pass_status and pass_contains) else "Fail"

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        run_rows.append([RUN_ID, now, EXECUTOR, tcid, text, verdict, os.path.join(RESULTS_DIR, f"{base}.json"), ""])

    df_new = pd.DataFrame(run_rows, columns=exec_cols)
    df_exec_out = pd.concat([df_exec, df_new], ignore_index=True)
    df_exec_out = df_exec_out.drop_duplicates(subset=["RUN_ID","テストケースID"], keep="last")

    if "05_Report" in xls.sheet_names:
        df_report = pd.read_excel(xls, sheet_name="05_Report")
    else:
        df_report = pd.DataFrame(columns=["項目","値"])

    df_this = df_exec_out[df_exec_out["RUN_ID"] == RUN_ID]
    executed = len(df_this)
    passed = int((df_this["ステータス（Pass/Fail）"] == "Pass").sum())
    failed = int((df_this["ステータス（Pass/Fail）"] == "Fail").sum())

    def upsert(key, val):
        mask = df_report["項目"] == key
        if mask.any():
            df_report.loc[mask, "値"] = val
        else:
            df_report.loc[len(df_report)] = [key, val]

    if total_cases is not None:
        upsert("総テストケース数", total_cases)
    upsert("実行数（今回RUN）", executed)
    upsert("Pass数（今回RUN）", passed)
    upsert("Fail数（今回RUN）", failed)
    upsert("Pass率（今回RUN）", f"{(passed/executed*100):.1f}%" if executed else "")

    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        df_exec_out.to_excel(writer, index=False, sheet_name="03_ExecutionLog")
        df_report.to_excel(writer, index=False, sheet_name="05_Report")
        df_auto.to_excel(writer, index=False, sheet_name="06_Automation")

    print(f"[OK] Run complete. RUN_ID={RUN_ID}, executed={executed}, pass={passed}, fail={failed}")
    print(f"[INFO] Results saved under: {RESULTS_DIR}")
    print(f"[INFO] Excel updated: {EXCEL_PATH}")

if __name__ == "__main__":
    main()
