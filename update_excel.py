#!/usr/bin/env python3
import os, json, datetime, sys
import pandas as pd

EXCEL_PATH = os.getenv("EXCEL_PATH", "TaskManagerAPI_TestPack.xlsx")
RESULTS_DIR = os.getenv("RESULTS_DIR", "./results")
EXECUTOR = os.getenv("EXECUTOR", "Jun")

# Mapping from results base name to Test Case ID
MAPPING = {
    "create1": "TC-POST-001",
    "create2": "TC-POST-005",
    "get_all": "TC-GET-ALL-001",
    "get_by_id": "TC-GET-ID-001",
    "put_partial": "TC-PUT-002",
    "filter_true": "TC-FILTER-001",
    "filter_false": "TC-FILTER-002",
    "delete": "TC-DEL-001",
    "get_after_delete": "TC-DEL-002",
    "invalid_id_get": "TC-GET-ID-003",
}

# Expected status rules per test case (simple version)
EXPECTED = {
    "TC-POST-001": {"ok": {"200", "201"}},
    "TC-POST-005": {"ok": {"200", "201"}},
    "TC-GET-ALL-001": {"ok": {"200"}},
    "TC-GET-ID-001": {"ok": {"200"}},
    "TC-PUT-002": {"ok": {"200"}},
    "TC-FILTER-001": {"ok": {"200"}},
    "TC-FILTER-002": {"ok": {"200"}},
    "TC-DEL-001": {"ok": {"200", "204"}},
    "TC-DEL-002": {"ok": {"404"}},
    "TC-GET-ID-003": {"ok": {"422"}},
}

def load_status(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "N/A"

def load_body(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""

def judge(tcid, status):
    okset = EXPECTED.get(tcid, {}).get("ok", set())
    return "Pass" if status in okset else "Fail"

def main():
    if not os.path.exists(EXCEL_PATH):
        print(f"[ERROR] Excel not found: {EXCEL_PATH}", file=sys.stderr)
        sys.exit(1)
    if not os.path.isdir(RESULTS_DIR):
        print(f"[ERROR] Results dir not found: {RESULTS_DIR}", file=sys.stderr)
        sys.exit(1)

    # Read existing sheets
    xls = pd.ExcelFile(EXCEL_PATH)
    if "03_ExecutionLog" in xls.sheet_names:
        df_exec = pd.read_excel(xls, sheet_name="03_ExecutionLog")
    else:
        df_exec = pd.DataFrame(columns=["実行日", "実行者", "テストケースID", "実際の結果", "ステータス（Pass/Fail）", "証跡（スクショ/ログのパス）", "備考"])

    today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_rows = []
    for base, tcid in MAPPING.items():
        status_path = os.path.join(RESULTS_DIR, f"{base}.status")
        body_path = os.path.join(RESULTS_DIR, f"{base}.json")
        status = load_status(status_path)
        body = load_body(body_path)
        verdict = judge(tcid, status)
        new_rows.append([today, EXECUTOR, tcid, body, verdict, body_path, ""])

    df_new = pd.DataFrame(new_rows, columns=df_exec.columns)
    df_exec_out = pd.concat([df_exec, df_new], ignore_index=True)

    # Update report sheet if present
    if "05_Report" in xls.sheet_names:
        df_report = pd.read_excel(xls, sheet_name="05_Report")
        # Compute stats from df_exec_out
        executed = len(df_exec_out)
        passed = int((df_exec_out["ステータス（Pass/Fail）"] == "Pass").sum())
        failed = int((df_exec_out["ステータス（Pass/Fail）"] == "Fail").sum())
        # Update/insert rows for 実行数, Pass数, Fail数, Pass率
        def upsert(key, value):
            mask = df_report["項目"] == key
            if mask.any():
                df_report.loc[mask, "値"] = value
            else:
                df_report.loc[len(df_report)] = [key, value]

        upsert("実行数", executed)
        upsert("Pass数", passed)
        upsert("Fail数", failed)
        upsert("Pass率", f"{(passed/executed*100):.1f}%" if executed else "")

        # Write all sheets back
        with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df_exec_out.to_excel(writer, index=False, sheet_name="03_ExecutionLog")
            df_report.to_excel(writer, index=False, sheet_name="05_Report")
    else:
        with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df_exec_out.to_excel(writer, index=False, sheet_name="03_ExecutionLog")

    print("[OK] Excel updated:", EXCEL_PATH)

if __name__ == "__main__":
    main()
