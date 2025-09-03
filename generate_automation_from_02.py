#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_automation_from_02_reqfixed.py
- Read 02_TestCases and produce 06_Automation aligned to the formal requirements:
  * POST success => 201, completed is not part of POST body, save_as=task_id
  * DELETE success => 200 with expect_contains "deleted successfully"
  * 404 for not-found cases
  * 422 for validation errors (empty title etc.)
  * PUT success => 200
  * Filter (/tasks/?completed=...) rows are dropped (not required)
"""
import os, re, json, sys
import pandas as pd

EXCEL_PATH = os.getenv("EXCEL_PATH", "TaskManagerAPI_TestPack.xlsx")

METHOD_RE = re.compile(r'^\s*(GET|POST|PUT|DELETE)\s+([^\s]+)', re.IGNORECASE | re.MULTILINE)
JSON_BLOCK_RE = re.compile(r'\{[\s\S]*\}', re.MULTILINE)

def normalize_url(url: str) -> str:
    if not url:
        return url
    url = url.replace("{id}", "{{task_id}}")
    url = url.replace("{existing_id}", "{{task_id}}")
    url = url.replace("{deleted_id}", "{{task_id}}")
    url = url.replace("{non_exist_id}", "999999")
    return url

def parse_body(text: str):
    if not isinstance(text, str):
        return ""
    m = JSON_BLOCK_RE.search(text)
    return m.group(0) if m else ""

def strip_completed_from_post(body_str: str) -> str:
    if not body_str:
        return body_str
    try:
        obj = json.loads(body_str)
        if isinstance(obj, dict) and "completed" in obj:
            obj.pop("completed", None)
            return json.dumps(obj, ensure_ascii=False)
        return body_str
    except Exception:
        return body_str

def main():
    if not os.path.exists(EXCEL_PATH):
        print(f"[ERROR] Excel not found: {EXCEL_PATH}"); sys.exit(1)

    xls = pd.ExcelFile(EXCEL_PATH)
    if "02_TestCases" not in xls.sheet_names:
        print("[ERROR] 02_TestCases シートが見つかりません。"); sys.exit(1)
    df02 = pd.read_excel(xls, sheet_name="02_TestCases")

    rows = []
    first_post_saved = False

    for _, r in df02.iterrows():
        tcid = str(r.get("テストケースID","")).strip()
        steps = str(r.get("テスト手順",""))
        input_data = str(r.get("入力データ",""))
        expected = str(r.get("期待結果",""))

        m = METHOD_RE.search(input_data if input_data else steps)
        if not m:
            continue
        method = m.group(1).upper()
        url = m.group(2).strip()

        # skip filter requirement
        if "?completed=" in url:
            continue

        url = normalize_url(url)
        body = parse_body(input_data)

        expect_status = "200"
        expect_contains = ""
        save_as = ""

        if method == "POST":
            body = strip_completed_from_post(body)
            expect_status = "201"
            if not first_post_saved:
                save_as = "task_id"
                first_post_saved = True
        elif method == "PUT":
            expect_status = "200"
        elif method == "DELETE":
            expect_status = "200"
            expect_contains = "deleted successfully"
        elif method == "GET":
            expect_status = "200"

        exp_lc = (expected + " " + steps).lower()
        if "not found" in exp_lc or "does not exist" in exp_lc or "404" in exp_lc:
            expect_status = "404"
        if "validation" in exp_lc or "バリデーション" in exp_lc or "400系" in exp_lc or '"title": ""' in input_data:
            expect_status = "422"

        rows.append([tcid, method, url, body, expect_status, save_as, expect_contains])

    df_auto = pd.DataFrame(rows, columns=[
        "テストケースID","メソッド","URL","ボディ(JSON)","期待ステータス","save_as（任意）","expect_contains（任意）"
    ])

    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="a", if_sheet_exists="replace") as w:
        df_auto.to_excel(w, index=False, sheet_name="06_Automation")

    print(f"[OK] 06_Automation を要件準拠で生成: {len(df_auto)} 件")
    print("→ run_all_cases_v2.py を実行して結果を確認してください。")

if __name__ == "__main__":
    main()
