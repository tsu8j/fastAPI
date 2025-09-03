#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
OUT_DIR="${OUT_DIR:-./results}"
mkdir -p "$OUT_DIR"

echo "== Smoke run against $BASE_URL =="

# helper: curl with status capture
_curl() {
  local method="$1"; shift
  local url="$1"; shift
  local data="${1:-}"; shift || true
  if [[ -n "$data" ]]; then
    curl -s -o "$OUT_DIR/body.tmp" -w "%{http_code}" -X "$method" "$BASE_URL$url" -H "Content-Type: application/json" -d "$data"
  else
    curl -s -o "$OUT_DIR/body.tmp" -w "%{http_code}" -X "$method" "$BASE_URL$url"
  fi
}

# 1) Create task A
STATUS=$(_curl POST "/tasks/" '{"title":"Buy milk","description":"2% milk","completed":false}')
echo "$STATUS" > "$OUT_DIR/create1.status"
cp "$OUT_DIR/body.tmp" "$OUT_DIR/create1.json"
TASK_ID=$(jq -r '.id // .task_id // empty' "$OUT_DIR/create1.json")
if [[ -z "$TASK_ID" || "$TASK_ID" == "null" ]]; then
  echo "Failed to parse TASK_ID from create1.json"; exit 1
fi
echo "Created TASK_ID=$TASK_ID"

# 2) Create task B (completed)
STATUS=$(_curl POST "/tasks/" '{"title":"Pay bills","completed":true}')
echo "$STATUS" > "$OUT_DIR/create2.status"
cp "$OUT_DIR/body.tmp" "$OUT_DIR/create2.json"

# 3) Get all
STATUS=$(_curl GET "/tasks/")
echo "$STATUS" > "$OUT_DIR/get_all.status"
cp "$OUT_DIR/body.tmp" "$OUT_DIR/get_all.json"

# 4) Get by ID
STATUS=$(_curl GET "/tasks/$TASK_ID")
echo "$STATUS" > "$OUT_DIR/get_by_id.status"
cp "$OUT_DIR/body.tmp" "$OUT_DIR/get_by_id.json"

# 5) Update partial (title only) - expect other fields unchanged
STATUS=$(_curl PUT "/tasks/$TASK_ID" '{"title":"Only title changed"}')
echo "$STATUS" > "$OUT_DIR/put_partial.status"
cp "$OUT_DIR/body.tmp" "$OUT_DIR/put_partial.json"

# 6) Filter completed=true
STATUS=$(_curl GET "/tasks/?completed=true")
echo "$STATUS" > "$OUT_DIR/filter_true.status"
cp "$OUT_DIR/body.tmp" "$OUT_DIR/filter_true.json"

# 7) Filter completed=false
STATUS=$(_curl GET "/tasks/?completed=false")
echo "$STATUS" > "$OUT_DIR/filter_false.status"
cp "$OUT_DIR/body.tmp" "$OUT_DIR/filter_false.json"

# 8) Delete
STATUS=$(_curl DELETE "/tasks/$TASK_ID")
echo "$STATUS" > "$OUT_DIR/delete.status"
cp "$OUT_DIR/body.tmp" "$OUT_DIR/delete.json"

# 9) Verify 404 after delete
STATUS=$(_curl GET "/tasks/$TASK_ID")
echo "$STATUS" > "$OUT_DIR/get_after_delete.status"
cp "$OUT_DIR/body.tmp" "$OUT_DIR/get_after_delete.json"

# 10) Negative: invalid id
STATUS=$(_curl GET "/tasks/abc")
echo "$STATUS" > "$OUT_DIR/invalid_id_get.status"
cp "$OUT_DIR/body.tmp" "$OUT_DIR/invalid_id_get.json"

echo "== Done. See $OUT_DIR for results =="
