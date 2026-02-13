param(
    [ValidateSet("start", "rebuild", "stop", "status")]
    [string]$Action = "start"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ComposeFile = Join-Path $RepoRoot "docker-compose.dev.yml"
$ProjectName = "genassist_dev"

function Invoke-Compose {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )

    Push-Location $RepoRoot
    try {
        & docker compose -f $ComposeFile -p $ProjectName @Args
        if ($LASTEXITCODE -ne 0) {
            throw "docker compose failed (exit code $LASTEXITCODE)"
        }
    }
    finally {
        Pop-Location
    }
}

function Wait-ForDockerDaemon {
    param(
        [int]$TimeoutSeconds = 120
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        & docker info 1>$null 2>$null
        if ($LASTEXITCODE -eq 0) {
            return
        }
        Start-Sleep -Seconds 2
    }

    throw "Docker daemon is not ready. Start Docker Desktop and retry."
}

function Ensure-DockerReady {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "Docker CLI not found in PATH."
    }

    if (-not (Test-Path $ComposeFile)) {
        throw "Compose file not found: $ComposeFile"
    }

    & docker desktop status 1>$null 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Starting Docker Desktop..."
        & docker desktop start
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to start Docker Desktop."
        }
    }

    Wait-ForDockerDaemon
}

switch ($Action) {
    "start" {
        Ensure-DockerReady
        Invoke-Compose -Args @("up", "-d", "--no-build")
        Invoke-Compose -Args @("ps")
        break
    }
    "rebuild" {
        Ensure-DockerReady
        Invoke-Compose -Args @("build", "app", "whisper")
        Invoke-Compose -Args @("up", "-d", "--no-build")
        Invoke-Compose -Args @("ps")
        break
    }
    "stop" {
        Ensure-DockerReady
        Invoke-Compose -Args @("down")
        break
    }
    "status" {
        Ensure-DockerReady
        Invoke-Compose -Args @("ps")
        break
    }
    default {
        throw "Unsupported action: $Action"
    }
}
