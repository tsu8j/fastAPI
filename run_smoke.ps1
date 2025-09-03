Param(
    [string]$BaseUrl = $env:BASE_URL
)
if (-not $BaseUrl) { $BaseUrl = "http://127.0.0.1:8000" }

$OutDir = "./results"
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }

Write-Host "== Smoke run against $BaseUrl =="

function Invoke-Req {
    param(
        [Parameter(Mandatory=$true)][string]$Method,
        [Parameter(Mandatory=$true)][string]$Url,
        [string]$Body = $null
    )
    $fullUrl = "$BaseUrl$Url"
    $headers = @{"Content-Type"="application/json"}

    try {
        if ($Body) {
            $resp = Invoke-WebRequest -Uri $fullUrl -Method $Method -Headers $headers -Body $Body -ErrorAction Stop
        } else {
            $resp = Invoke-WebRequest -Uri $fullUrl -Method $Method -Headers $headers -ErrorAction Stop
        }
        $status = [int]$resp.StatusCode
        $content = $resp.Content
    } catch {
        $status = [int]$_.Exception.Response.StatusCode
        try {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $content = $reader.ReadToEnd()
        } catch {
            $content = ""
        }
    }
    return @{ status = $status; content = $content }
}

# 1) Create task A
$r = Invoke-Req -Method POST -Url "/tasks/" -Body '{"title":"Buy milk","description":"2% milk","completed":false}'
$r.status | Out-File "$OutDir/create1.status" -Encoding ascii
$r.content | Out-File "$OutDir/create1.json" -Encoding utf8

# Parse TASK_ID from response (supports .id or .task_id)
$TASK_ID = $null
try {
    $json = $r.content | ConvertFrom-Json -ErrorAction Stop
    if ($null -ne $json.id) { $TASK_ID = $json.id }
    elseif ($null -ne $json.task_id) { $TASK_ID = $json.task_id }
} catch {
    $TASK_ID = $null
}
if (-not $TASK_ID) {
    Write-Error "Failed to parse TASK_ID from create1.json"
    exit 1
}
Write-Host "Created TASK_ID=$TASK_ID"

# 2) Create task B (completed)
$r = Invoke-Req -Method POST -Url "/tasks/" -Body '{"title":"Pay bills","completed":true}'
$r.status | Out-File "$OutDir/create2.status" -Encoding ascii
$r.content | Out-File "$OutDir/create2.json" -Encoding utf8

# 3) Get all
$r = Invoke-Req -Method GET -Url "/tasks/"
$r.status | Out-File "$OutDir/get_all.status" -Encoding ascii
$r.content | Out-File "$OutDir/get_all.json" -Encoding utf8

# 4) Get by ID
$r = Invoke-Req -Method GET -Url "/tasks/$TASK_ID"
$r.status | Out-File "$OutDir/get_by_id.status" -Encoding ascii
$r.content | Out-File "$OutDir/get_by_id.json" -Encoding utf8

# 5) Update partial (title only)
$r = Invoke-Req -Method PUT -Url "/tasks/$TASK_ID" -Body '{"title":"Only title changed"}'
$r.status | Out-File "$OutDir/put_partial.status" -Encoding ascii
$r.content | Out-File "$OutDir/put_partial.json" -Encoding utf8

# 6) Filter completed=true
$r = Invoke-Req -Method GET -Url "/tasks/?completed=true"
$r.status | Out-File "$OutDir/filter_true.status" -Encoding ascii
$r.content | Out-File "$OutDir/filter_true.json" -Encoding utf8

# 7) Filter completed=false
$r = Invoke-Req -Method GET -Url "/tasks/?completed=false"
$r.status | Out-File "$OutDir/filter_false.status" -Encoding ascii
$r.content | Out-File "$OutDir/filter_false.json" -Encoding utf8

# 8) Delete
$r = Invoke-Req -Method DELETE -Url "/tasks/$TASK_ID"
$r.status | Out-File "$OutDir/delete.status" -Encoding ascii
$r.content | Out-File "$OutDir/delete.json" -Encoding utf8

# 9) Verify 404 after delete
$r = Invoke-Req -Method GET -Url "/tasks/$TASK_ID"
$r.status | Out-File "$OutDir/get_after_delete.status" -Encoding ascii
$r.content | Out-File "$OutDir/get_after_delete.json" -Encoding utf8

# 10) Negative: invalid id
$r = Invoke-Req -Method GET -Url "/tasks/abc"
$r.status | Out-File "$OutDir/invalid_id_get.status" -Encoding ascii
$r.content | Out-File "$OutDir/invalid_id_get.json" -Encoding utf8

Write-Host "== Done. See $OutDir for results =="
