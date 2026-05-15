#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Mason Aquatics — Windows Installer
    Run this script as Administrator from the folder containing your project files.

.DESCRIPTION
    This script will:
      1. Verify it is running as Administrator
      2. Install Python 3.11 if not already present
      3. Create the installation directory at C:\MasonAquatics
      4. Copy all project files into the correct folder structure
      5. Write requirements.txt
      6. Create a Python virtual environment and install all dependencies
      7. Initialise the SQLite database
      8. Create a Start-MasonAquatics.bat launcher
      9. Create a Desktop shortcut
     10. Configure Windows Firewall to allow port 5000 (local only)
     11. Optionally register a Task Scheduler task to auto-start on login
     12. Launch the app and open the browser

.NOTES
    Place this script in the same folder as your Mason Aquatics project files
    before running.  All .py and .html files must be present alongside it.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ── Colour helpers ─────────────────────────────────────────────────────────────
function Write-Header  { param([string]$msg) Write-Host "`n═══  $msg  ═══" -ForegroundColor Cyan }
function Write-Ok      { param([string]$msg) Write-Host "  ✓  $msg" -ForegroundColor Green }
function Write-Info    { param([string]$msg) Write-Host "  →  $msg" -ForegroundColor Yellow }
function Write-Err     { param([string]$msg) Write-Host "  ✗  $msg" -ForegroundColor Red }

# ══════════════════════════════════════════════════════════════════════════════
# 0. BANNER
# ══════════════════════════════════════════════════════════════════════════════
Clear-Host
Write-Host @"

  ███╗   ███╗ █████╗ ███████╗ ██████╗ ███╗   ██╗
  ████╗ ████║██╔══██╗██╔════╝██╔═══██╗████╗  ██║
  ██╔████╔██║███████║███████╗██║   ██║██╔██╗ ██║
  ██║╚██╔╝██║██╔══██║╚════██║██║   ██║██║╚██╗██║
  ██║ ╚═╝ ██║██║  ██║███████║╚██████╔╝██║ ╚████║
  ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝
       A Q U A T I C S   —   F i s h   R o o m
"@ -ForegroundColor Cyan
Write-Host "  Windows Installer  |  Phases 1–10 Complete`n" -ForegroundColor DarkCyan

# ══════════════════════════════════════════════════════════════════════════════
# 1. ADMIN CHECK
# ══════════════════════════════════════════════════════════════════════════════
Write-Header "Step 1 — Administrator Check"
$currentPrincipal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Err "This script must be run as Administrator."
    Write-Err "Right-click the script → 'Run with PowerShell' → confirm UAC prompt."
    pause; exit 1
}
Write-Ok "Running as Administrator"

# ══════════════════════════════════════════════════════════════════════════════
# 2. CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
Write-Header "Step 2 — Configuration"

$InstallDir  = "C:\MasonAquatics"
$VenvDir     = "$InstallDir\.venv"
$PythonVer   = "3.11.9"
$PythonUrl   = "https://www.python.org/ftp/python/$PythonVer/python-$PythonVer-amd64.exe"
$PythonInst  = "$env:TEMP\python-$PythonVer-amd64.exe"
$ScriptDir   = $PSScriptRoot   # folder this .ps1 lives in
$DesktopPath = [Environment]::GetFolderPath("CommonDesktopDirectory")
$Port        = 5000

Write-Info "Install directory : $InstallDir"
Write-Info "Source directory  : $ScriptDir"
Write-Info "Virtual env       : $VenvDir"
Write-Info "App port          : $Port"

# ══════════════════════════════════════════════════════════════════════════════
# 3. PYTHON CHECK / INSTALL
# ══════════════════════════════════════════════════════════════════════════════
Write-Header "Step 3 — Python"

function Find-Python {
    # Try py launcher first, then direct python/python3 commands
    foreach ($cmd in @('py', 'python', 'python3')) {
        try {
            $ver = & $cmd --version 2>&1
            if ($ver -match 'Python 3\.(\d+)') {
                $minor = [int]$Matches[1]
                if ($minor -ge 9) {
                    return (Get-Command $cmd).Source
                }
            }
        } catch {}
    }
    # Search common install paths
    $paths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "C:\Python311\python.exe",
        "C:\Python310\python.exe",
        "C:\Python39\python.exe"
    )
    foreach ($p in $paths) {
        if (Test-Path $p) { return $p }
    }
    return $null
}

$PythonExe = Find-Python

if ($PythonExe) {
    $ver = & $PythonExe --version 2>&1
    Write-Ok "Found Python: $ver  ($PythonExe)"
} else {
    Write-Info "Python 3.9+ not found. Downloading Python $PythonVer ..."
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $PythonUrl -OutFile $PythonInst -UseBasicParsing
        Write-Info "Installing Python silently (this may take a minute) ..."
        $args = "/quiet InstallAllUsers=1 PrependPath=1 Include_pip=1 Include_launcher=1"
        Start-Process -FilePath $PythonInst -ArgumentList $args -Wait -NoNewWindow
        Remove-Item $PythonInst -Force -ErrorAction SilentlyContinue

        # Refresh PATH
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" +
                    [System.Environment]::GetEnvironmentVariable("PATH","User")

        $PythonExe = Find-Python
        if (-not $PythonExe) { throw "Python still not found after install." }
        Write-Ok "Python installed: $(& $PythonExe --version 2>&1)"
    } catch {
        Write-Err "Failed to install Python automatically."
        Write-Err "Please install Python 3.11 manually from https://www.python.org/downloads/"
        Write-Err "Then re-run this script."
        pause; exit 1
    }
}

# ══════════════════════════════════════════════════════════════════════════════
# 4. CREATE INSTALL DIRECTORY STRUCTURE
# ══════════════════════════════════════════════════════════════════════════════
Write-Header "Step 4 — Creating Directory Structure"

$dirs = @(
    $InstallDir,
    "$InstallDir\routes",
    "$InstallDir\templates\articles",
    "$InstallDir\templates\species",
    "$InstallDir\templates\tanks",
    "$InstallDir\templates\breeding",
    "$InstallDir\templates\sales",
    "$InstallDir\templates\gallery",
    "$InstallDir\templates\public",
    "$InstallDir\templates\labels",
    "$InstallDir\templates\reports",
    "$InstallDir\templates\costs",
    "$InstallDir\static\uploads\photos",
    "$InstallDir\static\generated",
    "$InstallDir\instance"
)
foreach ($d in $dirs) {
    New-Item -ItemType Directory -Path $d -Force | Out-Null
}
Write-Ok "Directory structure created"

# ══════════════════════════════════════════════════════════════════════════════
# 5. COPY PROJECT FILES
# ══════════════════════════════════════════════════════════════════════════════
Write-Header "Step 5 — Copying Project Files"

# Helper: copy a file with existence check and friendly message
function Copy-ProjectFile {
    param([string]$Src, [string]$Dst)
    if (Test-Path $Src) {
        Copy-Item -Path $Src -Destination $Dst -Force
        Write-Ok "  $([System.IO.Path]::GetFileName($Src)) → $($Dst.Replace($InstallDir,''))"
    } else {
        Write-Info "  SKIP (not found): $Src"
    }
}

# ── Root Python files ──────────────────────────────────────────────────────
Copy-ProjectFile "$ScriptDir\app.py"    "$InstallDir\app.py"
Copy-ProjectFile "$ScriptDir\models.py" "$InstallDir\models.py"

# ── Routes ────────────────────────────────────────────────────────────────
$routeMap = @{
    "main.py"     = "routes\main.py"
    "tanks.py"    = "routes\tanks.py"
    "articles.py" = "routes\articles.py"
    "breeding.py" = "routes\breeding.py"
    "costs.py"    = "routes\costs.py"
    "gallery.py"  = "routes\gallery.py"
    "labels.py"   = "routes\labels.py"
    "public.py"   = "routes\public.py"
    "reports.py"  = "routes\reports.py"
    "species.py"  = "routes\species.py"
    "sales.py"    = "routes\sales.py"
}
# Create empty __init__.py
New-Item -ItemType File -Path "$InstallDir\routes\__init__.py" -Force | Out-Null
foreach ($src in $routeMap.Keys) {
    Copy-ProjectFile "$ScriptDir\$src" "$InstallDir\$($routeMap[$src])"
}

# ── Templates — flat file name → correct template path mapping ─────────────
$templateMap = @{
    # base-level
    "base.html"             = "templates\base.html"
    "settings.html"         = "templates\settings.html"
    "dashboard.html"        = "templates\dashboard.html"
    # articles (new Phase 10)
    "articles_list.html"    = "templates\articles\list.html"
    "articles_form.html"    = "templates\articles\form.html"
    "articles_detail.html"  = "templates\articles\detail.html"
    # species
    "species_detail.html"   = "templates\species\detail.html"
    "species_list.html"     = "templates\species\list.html"
    "species_form.html"     = "templates\species\form.html"
    # tanks
    "tanks_detail.html"     = "templates\tanks\detail.html"
    "tanks_list.html"       = "templates\tanks\list.html"
    "tanks_edit.html"       = "templates\tanks\edit.html"
    "edit.html"             = "templates\tanks\edit.html"       # alternate flat name
    # breeding
    "breeding_list.html"    = "templates\breeding\list.html"
    "breeding_form.html"    = "templates\breeding\form.html"
    "list.html"             = "templates\breeding\list.html"    # alternate flat name
    "form.html"             = "templates\breeding\form.html"    # alternate flat name
    # sales
    "sales_list.html"       = "templates\sales\list.html"
    "sales_form.html"       = "templates\sales\form.html"
    "customer_list.html"    = "templates\sales\customer_list.html"
    "customer_detail.html"  = "templates\sales\customer_detail.html"
    "customer_form.html"    = "templates\sales\customer_form.html"
    # gallery
    "gallery_index.html"    = "templates\gallery\index.html"
    # public
    "public_species.html"   = "templates\public\species.html"
    # labels
    "labels_index.html"     = "templates\labels\index.html"
    # reports
    "available_list.html"   = "templates\reports\available_list.html"
    # costs
    "cost_dashboard.html"   = "templates\costs\dashboard.html"
    "feed_log.html"         = "templates\costs\feed_log.html"
    "power.html"            = "templates\costs\power.html"
}
foreach ($src in $templateMap.Keys) {
    $srcPath = "$ScriptDir\$src"
    $dstPath = "$InstallDir\$($templateMap[$src])"
    # Don't overwrite an already-copied file with a lower-priority name
    if ((Test-Path $srcPath) -and (-not (Test-Path $dstPath))) {
        Copy-ProjectFile $srcPath $dstPath
    } elseif (Test-Path $srcPath) {
        Copy-ProjectFile $srcPath $dstPath
    }
}

Write-Ok "File copy complete"

# ══════════════════════════════════════════════════════════════════════════════
# 6. WRITE requirements.txt
# ══════════════════════════════════════════════════════════════════════════════
Write-Header "Step 6 — Writing requirements.txt"

$requirements = @"
# Mason Aquatics — Python dependencies
Flask>=2.3.0
Flask-SQLAlchemy>=3.1.0
Pillow>=10.0.0
reportlab>=4.0.0
qrcode[pil]>=7.4.0
"@

# Prefer any requirements.txt already present in the source folder
if (Test-Path "$ScriptDir\requirements.txt") {
    Copy-Item "$ScriptDir\requirements.txt" "$InstallDir\requirements.txt" -Force
    Write-Ok "Copied existing requirements.txt"
} else {
    $requirements | Set-Content "$InstallDir\requirements.txt" -Encoding UTF8
    Write-Ok "Generated requirements.txt"
}

# ══════════════════════════════════════════════════════════════════════════════
# 7. VIRTUAL ENVIRONMENT + PACKAGES
# ══════════════════════════════════════════════════════════════════════════════
Write-Header "Step 7 — Virtual Environment & Packages"

Write-Info "Creating virtual environment ..."
& $PythonExe -m venv $VenvDir
if (-not $?) { Write-Err "venv creation failed."; pause; exit 1 }
Write-Ok "Virtual environment created at $VenvDir"

$PipExe    = "$VenvDir\Scripts\pip.exe"
$VenvPython = "$VenvDir\Scripts\python.exe"

Write-Info "Upgrading pip ..."
& $VenvPython -m pip install --upgrade pip --quiet
Write-Ok "pip upgraded"

Write-Info "Installing packages (this may take a few minutes) ..."
& $PipExe install -r "$InstallDir\requirements.txt" --quiet
if (-not $?) { Write-Err "Package installation failed."; pause; exit 1 }
Write-Ok "All packages installed"

# ══════════════════════════════════════════════════════════════════════════════
# 8. INITIALISE DATABASE
# ══════════════════════════════════════════════════════════════════════════════
Write-Header "Step 8 — Database Initialisation"

$initScript = @"
import sys, os
sys.path.insert(0, r'$InstallDir')
os.chdir(r'$InstallDir')
from app import create_app, init_db
app = create_app()
init_db(app)
print('Database initialised successfully.')
"@

$initPath = "$env:TEMP\ma_init_db.py"
$initScript | Set-Content $initPath -Encoding UTF8

& $VenvPython $initPath
if ($?) {
    Write-Ok "SQLite database initialised (instance\mason_aquatics.db)"
} else {
    Write-Info "Database init returned an error — it may initialise on first run instead."
}
Remove-Item $initPath -Force -ErrorAction SilentlyContinue

# ══════════════════════════════════════════════════════════════════════════════
# 9. CREATE LAUNCHER (Start-MasonAquatics.bat)
# ══════════════════════════════════════════════════════════════════════════════
Write-Header "Step 9 — Creating Launcher"

$batContent = @"
@echo off
title Mason Aquatics
cd /d "$InstallDir"
echo.
echo  ================================================
echo    Mason Aquatics ^| Fish Room Management System
echo    http://localhost:$Port
echo  ================================================
echo.
echo  Press Ctrl+C to stop the server.
echo.
start "" "http://localhost:$Port"
"$VenvDir\Scripts\python.exe" app.py
pause
"@

$batPath = "$InstallDir\Start-MasonAquatics.bat"
$batContent | Set-Content $batPath -Encoding ASCII
Write-Ok "Launcher created: $batPath"

# ══════════════════════════════════════════════════════════════════════════════
# 10. DESKTOP SHORTCUT
# ══════════════════════════════════════════════════════════════════════════════
Write-Header "Step 10 — Desktop Shortcut"

try {
    $WshShell  = New-Object -ComObject WScript.Shell
    $Shortcut  = $WshShell.CreateShortcut("$DesktopPath\Mason Aquatics.lnk")
    $Shortcut.TargetPath       = $batPath
    $Shortcut.WorkingDirectory = $InstallDir
    $Shortcut.Description      = "Start the Mason Aquatics Fish Room Management System"
    $Shortcut.IconLocation     = "shell32.dll,25"   # fish-like icon from shell32
    $Shortcut.Save()
    Write-Ok "Desktop shortcut created: $DesktopPath\Mason Aquatics.lnk"
} catch {
    Write-Info "Could not create shortcut automatically — run Start-MasonAquatics.bat directly."
}

# ══════════════════════════════════════════════════════════════════════════════
# 11. FIREWALL RULE (localhost only — port 5000)
# ══════════════════════════════════════════════════════════════════════════════
Write-Header "Step 11 — Firewall"

$ruleName = "Mason Aquatics (port $Port)"
$existing = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Ok "Firewall rule already exists: '$ruleName'"
} else {
    try {
        New-NetFirewallRule `
            -DisplayName  $ruleName `
            -Direction    Inbound `
            -Protocol     TCP `
            -LocalPort    $Port `
            -Action       Allow `
            -Profile      Private,Domain `
            -Description  "Allows Mason Aquatics Flask server on port $Port (local network only)" `
            | Out-Null
        Write-Ok "Firewall rule created: '$ruleName' — TCP port $Port, private/domain networks"
    } catch {
        Write-Info "Could not create firewall rule automatically — you may need to add it manually."
    }
}

# ══════════════════════════════════════════════════════════════════════════════
# 12. OPTIONAL — TASK SCHEDULER (auto-start on login)
# ══════════════════════════════════════════════════════════════════════════════
Write-Header "Step 12 — Auto-Start (Optional)"

$autoStart = $null
while ($autoStart -notin @('Y','N','y','n')) {
    $autoStart = Read-Host "  Auto-start Mason Aquatics when Windows logs in? (Y/N)"
}

if ($autoStart -in @('Y','y')) {
    $taskName = "MasonAquatics"
    $action   = New-ScheduledTaskAction -Execute $batPath -WorkingDirectory $InstallDir
    $trigger  = New-ScheduledTaskTrigger -AtLogOn
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit 0
    $principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

    # Remove any previous registration
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

    Register-ScheduledTask `
        -TaskName  $taskName `
        -Action    $action `
        -Trigger   $trigger `
        -Settings  $settings `
        -Principal $principal `
        -Description "Starts Mason Aquatics Fish Room system at login" `
        | Out-Null

    Write-Ok "Task Scheduler task registered: '$taskName' — runs at login for $env:USERNAME"
} else {
    Write-Info "Skipped auto-start. Use the desktop shortcut or Start-MasonAquatics.bat to launch."
}

# ══════════════════════════════════════════════════════════════════════════════
# 13. LAUNCH
# ══════════════════════════════════════════════════════════════════════════════
Write-Header "Step 13 — Launch"

$launch = $null
while ($launch -notin @('Y','N','y','n')) {
    $launch = Read-Host "  Launch Mason Aquatics now? (Y/N)"
}

if ($launch -in @('Y','y')) {
    Write-Info "Starting server — your browser will open at http://localhost:$Port ..."
    Start-Process -FilePath $batPath
} else {
    Write-Info "To start later, double-click 'Mason Aquatics' on your Desktop."
}

# ══════════════════════════════════════════════════════════════════════════════
# COMPLETE
# ══════════════════════════════════════════════════════════════════════════════
Write-Host ""
Write-Host "  ════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "   Mason Aquatics installed successfully!" -ForegroundColor Green
Write-Host "   Install path : $InstallDir" -ForegroundColor White
Write-Host "   App URL      : http://localhost:$Port" -ForegroundColor White
Write-Host "   Launcher     : $batPath" -ForegroundColor White
Write-Host "  ════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
pause
