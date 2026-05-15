param(
    [switch]$NoBrowser,
    [switch]$SkipChecks,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)
$BackendDir = Join-Path $ProjectRoot "backend"
$WebDir = Join-Path $ProjectRoot "web"
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$InstallScript = Join-Path $ScriptDir "install.ps1"
$BackendHealthUrl = "http://127.0.0.1:8000/api/health"
$FrontendUrl = "http://127.0.0.1:5173"
$BackendPort = 8000
$FrontendPort = 5173

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

function Open-BrowserUrl {
    param([string]$Url)

    if ($DryRun) {
        Write-Host "[dry-run] Would open $Url" -ForegroundColor DarkGray
        return
    }

    try {
        Start-Process -FilePath "explorer.exe" -ArgumentList $Url | Out-Null
    } catch {
        Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "start", "", $Url -WindowStyle Hidden | Out-Null
    }
}

function Get-PowerShellExecutable {
    $powershell = Get-Command powershell -ErrorAction SilentlyContinue
    if ($powershell) {
        return $powershell.Source
    }

    $pwsh = Get-Command pwsh -ErrorAction SilentlyContinue
    if ($pwsh) {
        return $pwsh.Source
    }

    throw "PowerShell executable not found."
}

function Get-WindowsTerminalExecutable {
    $wt = Get-Command wt -ErrorAction SilentlyContinue
    if ($wt) {
        return $wt.Source
    }

    return $null
}

function Quote-Single {
    param([string]$Value)
    return "'" + $Value.Replace("'", "''") + "'"
}

function Convert-ToEncodedCommand {
    param([string]$ScriptText)

    return [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($ScriptText))
}

function Build-LauncherScript {
    param(
        [string]$Title,
        [string]$WorkingDirectory,
        [string]$CommandText
    )

    return '$Host.UI.RawUI.WindowTitle = {0}; Set-Location -LiteralPath {1}; {2}' -f `
        (Quote-Single $Title), `
        (Quote-Single $WorkingDirectory), `
        $CommandText
}

function Invoke-InstallScript {
    param(
        [switch]$CheckOnly,
        [switch]$SkipValidation
    )

    $arguments = @(
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        $InstallScript
    )

    if ($CheckOnly) {
        $arguments += "-CheckOnly"
    }

    if ($SkipValidation) {
        $arguments += "-SkipValidation"
    }

    & $script:PowerShellExe @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Install script failed."
    }
}

function Test-UrlReady {
    param([string]$Url)

    try {
        $requestParameters = @{
            Uri        = $Url
            TimeoutSec = 2
            ErrorAction = "Stop"
        }

        $invokeWebRequest = Get-Command Invoke-WebRequest -ErrorAction Stop
        if ($invokeWebRequest.Parameters.ContainsKey("UseBasicParsing")) {
            $requestParameters["UseBasicParsing"] = $true
        }

        $null = Invoke-WebRequest @requestParameters
        return $true
    } catch {
        return $false
    }
}

function Test-PortListening {
    param([int]$Port)

    try {
        $connections = @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction Stop)
        return $connections.Count -gt 0
    } catch {
        return $false
    }
}

function Wait-ForUrl {
    param(
        [string]$Name,
        [string]$Url,
        [int]$TimeoutSeconds = 60
    )

    if ($DryRun) {
        Write-Ok "[dry-run] Would wait for $Name at $Url"
        return
    }

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-UrlReady -Url $Url) {
            Write-Ok "$Name is ready"
            return
        }

        Start-Sleep -Seconds 1
    }

    throw "$Name did not become ready within $TimeoutSeconds seconds."
}

function Start-AppWindow {
    param(
        [string]$Title,
        [string]$WorkingDirectory,
        [string]$CommandText
    )

    if ($DryRun) {
        Write-Host "[dry-run] $Title -> $CommandText" -ForegroundColor DarkGray
        return
    }

    $launcher = Build-LauncherScript -Title $Title -WorkingDirectory $WorkingDirectory -CommandText $CommandText
    Start-Process -FilePath $script:PowerShellExe `
        -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $launcher) `
        -WorkingDirectory $WorkingDirectory | Out-Null
}

function Start-AppTabs {
    param(
        [array]$Tabs
    )

    if ($Tabs.Count -eq 0) {
        return $true
    }

    if (-not $script:WindowsTerminalExe) {
        return $false
    }

    if ($DryRun) {
        foreach ($tab in $Tabs) {
            Write-Host "[dry-run] tab $($tab.Title) -> $($tab.CommandText)" -ForegroundColor DarkGray
        }
        return $true
    }

    $tabCommands = @()
    foreach ($tab in $Tabs) {
        $launcher = Build-LauncherScript -Title $tab.Title -WorkingDirectory $tab.WorkingDirectory -CommandText $tab.CommandText
        $encoded = Convert-ToEncodedCommand -ScriptText $launcher
        $tabCommands += 'new-tab --title "{0}" "{1}" -NoExit -EncodedCommand {2}' -f `
            $tab.Title.Replace('"', '\"'), `
            $script:PowerShellExe, `
            $encoded
    }

    $arguments = "-w new " + ($tabCommands -join " ; ")
    Start-Process -FilePath $script:WindowsTerminalExe -ArgumentList $arguments | Out-Null
    return $true
}

$PowerShellExe = Get-PowerShellExecutable
$WindowsTerminalExe = Get-WindowsTerminalExecutable

Write-Host "TradeBrain start" -ForegroundColor White
Write-Host "Project root: $ProjectRoot" -ForegroundColor DarkGray

$backendAlreadyRunning = (Test-PortListening -Port $BackendPort) -or (Test-UrlReady -Url $BackendHealthUrl)
$frontendAlreadyRunning = (Test-PortListening -Port $FrontendPort) -or (Test-UrlReady -Url $FrontendUrl)

if ($backendAlreadyRunning -and $frontendAlreadyRunning) {
    Write-Step "Backend and frontend already running"
    if ($NoBrowser) {
        Write-Ok "TradeBrain is already available at $FrontendUrl"
    } else {
        Open-BrowserUrl -Url $FrontendUrl
        Write-Ok "Browser opened"
    }
    return
}

if (-not $SkipChecks) {
    Write-Step "Checking runtime"
    try {
        Invoke-InstallScript -CheckOnly -SkipValidation
        Write-Ok "Environment check passed"
    } catch {
        Write-WarnLine "Environment check failed. Running installer."
        Invoke-InstallScript
        Write-Ok "Environment has been prepared"
    }
} else {
    Write-WarnLine "Startup checks skipped by request"
}

$tabsToStart = @()

Write-Step "Starting backend"
if ($backendAlreadyRunning) {
    Write-Ok "Backend already running"
} else {
    if (-not (Test-Path $VenvPython)) {
        throw "Python runtime not found at .venv. Run scripts\install.bat or scripts\powershell\install.ps1 first."
    }

    $backendCommand = "& {0} -m uvicorn app.main:app --reload" -f (Quote-Single $VenvPython)
    $tabsToStart += @{
        Title = "TradeBrain Backend"
        WorkingDirectory = $BackendDir
        CommandText = $backendCommand
    }
    Write-Ok "Backend launch scheduled"
}

Write-Step "Starting frontend"
if ($frontendAlreadyRunning) {
    Write-Ok "Frontend already running"
} else {
    if ($NoBrowser) {
        $frontendCommand = "npm run dev"
    } else {
        $frontendCommand = "npm run dev -- --open"
    }
    $tabsToStart += @{
        Title = "TradeBrain Frontend"
        WorkingDirectory = $WebDir
        CommandText = $frontendCommand
    }
    Write-Ok "Frontend launch scheduled"
}

if ($tabsToStart.Count -gt 0) {
    Write-Step "Launching terminal"
    $startedInTabs = Start-AppTabs -Tabs $tabsToStart
    if ($startedInTabs) {
        Write-Ok "Started in Windows Terminal tabs"
    } else {
        Write-WarnLine "Windows Terminal not available, falling back to separate windows"
        foreach ($tab in $tabsToStart) {
            Start-AppWindow -Title $tab.Title -WorkingDirectory $tab.WorkingDirectory -CommandText $tab.CommandText
        }
        Write-Ok "Started in separate windows"
    }
}

if ((-not $NoBrowser) -and $frontendAlreadyRunning) {
    Write-Step "Opening browser"
    Open-BrowserUrl -Url $FrontendUrl
    Write-Ok "Browser opened"
}

Write-Step "Done"
Write-Host "TradeBrain launch request finished. Frontend URL: $FrontendUrl" -ForegroundColor White
