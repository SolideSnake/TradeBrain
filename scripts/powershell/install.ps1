param(
    [switch]$CheckOnly,
    [switch]$SkipValidation
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)
$BackendDir = Join-Path $ProjectRoot "backend"
$WebDir = Join-Path $ProjectRoot "web"
$VenvDir = Join-Path $ProjectRoot ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$EnvFile = Join-Path $ProjectRoot ".env"
$EnvExample = Join-Path $ProjectRoot ".env.example"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-Ok {
    param([string]$Message)
    Write-Host "[ok] $Message" -ForegroundColor Green
}

function Write-WarnLine {
    param([string]$Message)
    Write-Host "[warn] $Message" -ForegroundColor Yellow
}

function Write-InfoLine {
    param([string]$Message)
    Write-Host "[info] $Message" -ForegroundColor Gray
}

function Get-PythonRuntime {
    $candidates = @(
        @{ Command = "py"; Prefix = @("-3.11") },
        @{ Command = "py"; Prefix = @("-3") },
        @{ Command = "python"; Prefix = @() }
    )

    foreach ($candidate in $candidates) {
        if (-not (Get-Command $candidate.Command -ErrorAction SilentlyContinue)) {
            continue
        }

        try {
            $version = & $candidate.Command @($candidate.Prefix + @("-c", "import sys; print('.'.join(map(str, sys.version_info[:3])))")) 2>$null
            if (-not $version) {
                continue
            }

            $parsedVersion = [Version]$version.Trim()
            return @{
                Command = $candidate.Command
                Prefix = $candidate.Prefix
                Version = $parsedVersion
            }
        } catch {
            continue
        }
    }

    throw "Python 3.11+ was not found. Please install Python 3.11 or newer."
}

function Invoke-External {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = $ProjectRoot
    )

    Push-Location $WorkingDirectory
    try {
        & $Command @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Command failed: $Command $($Arguments -join ' ')"
        }
    } finally {
        Pop-Location
    }
}

function Test-TcpPorts {
    param([int[]]$Ports)

    try {
        $listeners = Get-NetTCPConnection -State Listen -LocalPort $Ports -ErrorAction Stop
        return $listeners | Sort-Object LocalPort -Unique
    } catch {
        return @()
    }
}

Write-Host "TradeBrain bootstrap" -ForegroundColor White
Write-Host "Project root: $ProjectRoot" -ForegroundColor DarkGray

Write-Step "Checking Python"
$python = Get-PythonRuntime
if ($python.Version -lt [Version]"3.11.0") {
    throw "Python 3.11+ is required. Found $($python.Version)."
}
Write-Ok "Python $($python.Version) detected via '$($python.Command)'."

if (-not $CheckOnly) {
    Write-Step "Preparing virtual environment"
    if (-not (Test-Path $VenvPython)) {
        Write-InfoLine "Creating .venv"
        Invoke-External -Command $python.Command -Arguments ($python.Prefix + @("-m", "venv", $VenvDir))
    } else {
        Write-Ok ".venv already exists"
    }

    Write-Step "Installing backend dependencies"
    Invoke-External -Command $VenvPython -Arguments @("-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel")
    Invoke-External -Command $VenvPython -Arguments @("-m", "pip", "install", "-e", ".[dev]") -WorkingDirectory $BackendDir
} elseif (-not (Test-Path $VenvPython)) {
    throw "CheckOnly requested, but .venv is missing. Run the installer without -CheckOnly first."
}

Write-Step "Checking backend runtime"
Invoke-External -Command $VenvPython -Arguments @(
    "-c",
    "import fastapi, sqlalchemy, pydantic_settings, uvicorn, ib_async; print('backend imports ok')"
)
Write-Ok "Backend imports look good"

Write-Step "Checking Node.js and npm"
$nodeCommand = Get-Command node -ErrorAction SilentlyContinue
$npmCommand = Get-Command npm -ErrorAction SilentlyContinue
if (-not $nodeCommand) {
    throw "Node.js was not found. Please install Node.js 18+."
}
if (-not $npmCommand) {
    throw "npm was not found. Please install Node.js/npm 18+."
}

$nodeVersionRaw = (& node --version).Trim()
$nodeVersion = [Version]($nodeVersionRaw.TrimStart("v"))
if ($nodeVersion -lt [Version]"18.0.0") {
    throw "Node.js 18+ is required. Found $nodeVersionRaw."
}
Write-Ok "Node.js $nodeVersionRaw detected"
Write-Ok "npm $((& npm --version).Trim()) detected"

if (-not $CheckOnly) {
    Write-Step "Installing frontend dependencies"
    if (Test-Path (Join-Path $WebDir "package-lock.json")) {
        if (Test-Path (Join-Path $WebDir "node_modules")) {
            Invoke-External -Command "npm" -Arguments @("install") -WorkingDirectory $WebDir
        } else {
            Invoke-External -Command "npm" -Arguments @("ci") -WorkingDirectory $WebDir
        }
    } else {
        Invoke-External -Command "npm" -Arguments @("install") -WorkingDirectory $WebDir
    }
}

Write-Step "Checking project files"
if (-not (Test-Path $EnvFile)) {
    if (-not $CheckOnly -and (Test-Path $EnvExample)) {
        Copy-Item -Path $EnvExample -Destination $EnvFile
        Write-Ok "Created .env from .env.example"
    } else {
        Write-WarnLine ".env is missing. Copy .env.example to .env before live configuration."
    }
} else {
    Write-Ok ".env exists"
}

$staleDbPath = Join-Path $BackendDir "backend\tradebrain.db"
if (Test-Path $staleDbPath) {
    Write-WarnLine "Found stale database artifact at backend\\backend\\tradebrain.db. Current runtime uses backend\\tradebrain.db."
}

$ibkrPorts = @(Test-TcpPorts -Ports @(7496, 7497, 4001, 4002))
if ($ibkrPorts.Count -gt 0) {
    $portList = ($ibkrPorts | ForEach-Object { $_.LocalPort } | Sort-Object -Unique) -join ", "
    Write-Ok "Detected listening IBKR/TWS ports: $portList"
} else {
    Write-WarnLine "No TWS / IB Gateway ports detected (7496, 7497, 4001, 4002). This is fine unless you are testing live IBKR now."
}

if (-not $SkipValidation) {
    Write-Step "Running validation"
    Invoke-External -Command $VenvPython -Arguments @("-m", "pytest") -WorkingDirectory $BackendDir
    Invoke-External -Command "npm" -Arguments @("run", "build") -WorkingDirectory $WebDir
    Write-Ok "Validation passed"
} else {
    Write-WarnLine "Validation skipped by request"
}

Write-Step "Done"
Write-Host "Backend start:" -ForegroundColor White
Write-Host "  cd D:\code\TradeBrain\backend" -ForegroundColor Gray
Write-Host "  ..\.venv\Scripts\python -m uvicorn app.main:app --reload" -ForegroundColor Gray
Write-Host "Frontend start:" -ForegroundColor White
Write-Host "  cd D:\code\TradeBrain\web" -ForegroundColor Gray
Write-Host "  npm run dev" -ForegroundColor Gray
Write-Host "Open: http://127.0.0.1:5173" -ForegroundColor White
