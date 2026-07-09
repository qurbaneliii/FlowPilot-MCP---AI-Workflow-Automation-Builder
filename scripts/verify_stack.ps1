param(
    [int]$TimeoutSeconds = 60
)

$ErrorActionPreference = "Stop"

function Write-Fail {
    param([string]$Message)
    Write-Host "FAIL: $Message" -ForegroundColor Red
    exit 1
}

function Wait-ForJsonHealth {
    param(
        [string]$Url,
        [int]$TimeoutSeconds
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $lastError = $null

    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-RestMethod -Uri $Url -TimeoutSec 5
            if (
                $response.status -eq "ok" -and
                $response.dependencies.database -eq "ok"
            ) {
                return $response
            }
            $lastError = "health returned status=$($response.status), database=$($response.dependencies.database)"
        }
        catch {
            $lastError = $_.Exception.Message
        }
        Start-Sleep -Seconds 2
    }

    Write-Fail "Backend health did not report database=ok within $TimeoutSeconds seconds. Last error: $lastError"
}

function Wait-ForHttpOk {
    param(
        [string]$Url,
        [int]$TimeoutSeconds
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $lastError = $null

    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $Url -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                return
            }
            $lastError = "HTTP $($response.StatusCode)"
        }
        catch {
            $lastError = $_.Exception.Message
        }
        Start-Sleep -Seconds 2
    }

    Write-Fail "Frontend root did not return HTTP 200 within $TimeoutSeconds seconds. Last error: $lastError"
}

Write-Host "Starting FlowPilot MCP stack..."
docker compose up --build -d

Write-Host "Waiting for backend health and database probe..."
$health = Wait-ForJsonHealth -Url "http://127.0.0.1:8000/api/v1/health" -TimeoutSeconds $TimeoutSeconds

Write-Host "Waiting for frontend root..."
Wait-ForHttpOk -Url "http://127.0.0.1:3000" -TimeoutSeconds $TimeoutSeconds

Write-Host "PASS: FlowPilot MCP stack is healthy." -ForegroundColor Green
Write-Host "Backend dependencies: database=$($health.dependencies.database), openai=$($health.dependencies.openai)"
