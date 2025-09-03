# check_06.py  — ASCII-only / column auto-detection
import os
import pandas as pd

EXCEL_PATH = os.environ.get("EXCEL_PATH", "TaskManagerAPI_TestPack.xlsx")

def find_col(df, candidates):
    cols = list(df.columns)
    low = [c.lower() for c in cols]
    for cand in candidates:
        cand_l = cand.lower()
        # exact / contains match on both original and lowercase
        for i, c in enumerate(cols):
            if cand in c or cand_l in low[i]:
                return c
    return None

df = pd.read_excel(EXCEL_PATH, sheet_name="06_Automation")

col_method   = find_col(df, ["メソッド", "method"])
col_status   = find_col(df, ["期待ステータス", "expected", "status"])
col_contains = find_col(df, ["expect_contains（任意）", "expect_contains", "contains"])
col_url      = find_col(df, ["URL", "url"])

print("---- Sheet: 06_Automation ----")
print("Columns:", list(df.columns))
print("Detected -> method:", col_method, "| status:", col_status, "| contains:", col_contains, "| url:", col_url)

if not all([col_method, col_status, col_url]):
    print("[ERROR] 必須カラム（method/status/url）が見つかりません。列名を確認してください。")
    raise SystemExit(1)

def uniq(vals):
    return sorted({str(v) for v in vals})

# Metrics
post_expect   = uniq(df.loc[df[col_method].astype(str).str.upper()=="POST",   col_status])
delete_expect = uniq(df.loc[df[col_method].astype(str).str.upper()=="DELETE", col_status])
contains_vals = uniq(df.loc[df[col_method].astype(str).str.upper()=="DELETE", col_contains]) if col_contains else []
filter_rows   = int(df[col_url].astype(str).str.contains(r"\?completed=", case=False).sum())

print("Rows:", len(df))
print("POST expected:", post_expect)
print("DELETE expected:", delete_expect)
print("DELETE expect_contains:", contains_vals)
print("Filter rows (?completed=) count (should be 0):", filter_rows)

# Quick verdicts
ok_post   = post_expect == ["201"]
ok_del    = delete_expect == ["200"]
ok_cont   = any("deleted successfully" in v.lower() for v in contains_vals) if contains_vals else False
ok_filter = (filter_rows == 0)

print("Verdict -> POST=201:", ok_post, "| DELETE=200:", ok_del, "| contains 'deleted successfully':", ok_cont, "| no filter rows:", ok_filter)
