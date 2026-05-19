#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Mason Aquatics - Windows Installer
    Run as Administrator from the folder containing your project files.

.DESCRIPTION
    1.  Verifies Administrator rights
    2.  Installs Python 3.11 if not present
    3.  Creates C:\MasonAquatics with the full correct directory structure
    4.  Copies every project file to its exact correct destination path
    5.  Writes requirements.txt
    6.  Creates a Python virtual environment and installs all dependencies
    7.  Initialises the SQLite database
    8.  Creates Start-MasonAquatics.bat launcher
    9.  Creates a Desktop shortcut
    10. Adds a Windows Firewall rule for port 5000
    11. Optionally registers a Task Scheduler task to auto-start on login
    12. Optionally launches the app and opens the browser
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Header { param([string]$msg) Write-Host ""; Write-Host "=== $msg ===" -ForegroundColor Cyan }
function Write-Ok     { param([string]$msg) Write-Host "  [OK] $msg" -ForegroundColor Green  }
function Write-Info   { param([string]$msg) Write-Host "  [->] $msg" -ForegroundColor Yellow }
function Write-Err    { param([string]$msg) Write-Host "  [!!] $msg" -ForegroundColor Red    }

# ===========================================================================
# 0. BANNER
# ===========================================================================
Clear-Host
Write-Host "  Mason Aquatics - Fish Room Management System" -ForegroundColor Cyan
Write-Host "  Windows Installer" -ForegroundColor DarkCyan
Write-Host ""

# ===========================================================================
# 1. ADMIN CHECK
# ===========================================================================
Write-Header "Step 1 - Administrator Check"
$principal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Err "This script must be run as Administrator."
    Write-Err "Right-click the script and choose Run with PowerShell, then confirm UAC."
    pause; exit 1
}
Write-Ok "Running as Administrator"

# ===========================================================================
# 2. CONFIGURATION
# ===========================================================================
Write-Header "Step 2 - Configuration"

$InstallDir  = "C:\MasonAquatics"
$VenvDir     = "$InstallDir\.venv"
$PythonVer   = "3.11.9"
$PythonUrl   = "https://www.python.org/ftp/python/$PythonVer/python-$PythonVer-amd64.exe"
$PythonInst  = Join-Path $env:TEMP "python-$PythonVer-amd64.exe"
$ScriptDir   = $PSScriptRoot
$DesktopPath = [Environment]::GetFolderPath("CommonDesktopDirectory")
$Port        = 5000

Write-Info "Install directory : $InstallDir"
Write-Info "Source directory  : $ScriptDir"
Write-Info "Virtual env       : $VenvDir"
Write-Info "App port          : $Port"

# ===========================================================================
# 3. PYTHON CHECK / INSTALL
# ===========================================================================
Write-Header "Step 3 - Python"

function Find-Python {
    foreach ($cmd in @('py', 'python', 'python3')) {
        try {
            $v = & $cmd --version 2>&1
            if ($v -match 'Python 3\.(\d+)') {
                if ([int]$Matches[1] -ge 9) {
                    $found = Get-Command $cmd -ErrorAction SilentlyContinue
                    if ($found) { return $found.Source }
                }
            }
        } catch {}
    }
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "C:\Python311\python.exe",
        "C:\Python310\python.exe",
        "C:\Python39\python.exe"
    )
    foreach ($p in $candidates) {
        if (Test-Path $p) { return $p }
    }
    return $null
}

$PythonExe = Find-Python
if ($PythonExe) {
    $pyVer = & $PythonExe --version 2>&1
    Write-Ok "Found Python: $pyVer  ($PythonExe)"
} else {
    Write-Info "Python 3.9+ not found. Downloading Python $PythonVer ..."
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $PythonUrl -OutFile $PythonInst -UseBasicParsing
        Write-Info "Installing Python silently (this may take a minute) ..."
        Start-Process -FilePath $PythonInst `
            -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_pip=1 Include_launcher=1" `
            -Wait -NoNewWindow
        Remove-Item $PythonInst -Force -ErrorAction SilentlyContinue
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" +
                    [System.Environment]::GetEnvironmentVariable("PATH","User")
        $PythonExe = Find-Python
        if (-not $PythonExe) { throw "Python still not found after install." }
        Write-Ok "Python installed: $(& $PythonExe --version 2>&1)"
    } catch {
        Write-Err "Failed to install Python automatically."
        Write-Err "Install Python 3.11 from https://www.python.org/downloads/ then re-run this script."
        pause; exit 1
    }
}

# ===========================================================================
# 4. DIRECTORY STRUCTURE
# ===========================================================================
Write-Header "Step 4 - Creating Directory Structure"

$dirs = @(
    $InstallDir,
    "$InstallDir\routes",
    "$InstallDir\templates",
    "$InstallDir\templates\species",
    "$InstallDir\templates\tanks",
    "$InstallDir\templates\breeding",
    "$InstallDir\templates\sales",
    "$InstallDir\templates\gallery",
    "$InstallDir\templates\public",
    "$InstallDir\templates\labels",
    "$InstallDir\templates\reports",
    "$InstallDir\templates\costs",
    "$InstallDir\templates\articles",
    "$InstallDir\static\uploads\photos",
    "$InstallDir\static\generated",
    "$InstallDir\instance"
)
foreach ($d in $dirs) {
    New-Item -ItemType Directory -Path $d -Force | Out-Null
}
Write-Ok "Directory structure created"

# ===========================================================================
# 5. COPY PROJECT FILES
#
# Every file has an explicit source name mapped to its exact destination.
# Source names use the prefixed flat names (e.g. species_list.html) AND
# the natural subfolder paths (e.g. templates\species\list.html).
# Both passes run; the subfolder pass runs second so if both exist the
# already-organised file wins.
# ===========================================================================
Write-Header "Step 5 - Copying Project Files"

# Create empty routes package init
$routesInit = "$InstallDir\routes\__init__.py"
if (-not (Test-Path $routesInit)) {
    New-Item -ItemType File -Path $routesInit -Force | Out-Null
}

function Copy-One {
    param([string]$SrcPath, [string]$DstPath)
    if (Test-Path $SrcPath) {
        $dstDir = Split-Path $DstPath -Parent
        if (-not (Test-Path $dstDir)) {
            New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
        }
        Copy-Item -Path $SrcPath -Destination $DstPath -Force
        $rel = $DstPath.Replace($InstallDir + "\", "")
        Write-Ok "$([IO.Path]::GetFileName($SrcPath)) -> $rel"
        return $true
    }
    return $false
}

# --- Pass 1: flat prefixed filenames in the source directory ----------------
# Format: @(source-flat-name, destination-relative-to-InstallDir)
$flatMappings = @(
    # Root Python
    @("app.py",                   "app.py"),
    @("models.py",                "models.py"),

    # Routes (flat copies)
    @("main.py",                  "routes\main.py"),
    @("species.py",               "routes\species.py"),
    @("tanks.py",                 "routes\tanks.py"),
    @("breeding.py",              "routes\breeding.py"),
    @("sales.py",                 "routes\sales.py"),
    @("gallery.py",               "routes\gallery.py"),
    @("public.py",                "routes\public.py"),
    @("labels.py",                "routes\labels.py"),
    @("reports.py",               "routes\reports.py"),
    @("costs.py",                 "routes\costs.py"),
    @("articles.py",              "routes\articles.py"),

    # Base templates (no prefix needed, unique names)
    @("base.html",                "templates\base.html"),
    @("dashboard.html",           "templates\dashboard.html"),
    @("settings.html",            "templates\settings.html"),

    # Species templates (prefixed)
    @("species_list.html",        "templates\species\list.html"),
    @("species_form.html",        "templates\species\form.html"),
    @("species_detail.html",      "templates\species\detail.html"),

    # Tank templates (prefixed)
    @("tanks_list.html",          "templates\tanks\list.html"),
    @("tanks_detail.html",        "templates\tanks\detail.html"),
    @("tanks_edit.html",          "templates\tanks\edit.html"),

    # Breeding templates (prefixed)
    @("breeding_list.html",       "templates\breeding\list.html"),
    @("breeding_form.html",       "templates\breeding\form.html"),

    # Sales templates (prefixed)
    @("sales_list.html",          "templates\sales\list.html"),
    @("sales_form.html",          "templates\sales\form.html"),
    @("customer_list.html",       "templates\sales\customer_list.html"),
    @("customer_detail.html",     "templates\sales\customer_detail.html"),
    @("customer_form.html",       "templates\sales\customer_form.html"),

    # Gallery (prefixed)
    @("gallery_index.html",       "templates\gallery\index.html"),

    # Public (prefixed)
    @("public_species.html",      "templates\public\species.html"),

    # Labels (prefixed)
    @("labels_index.html",        "templates\labels\index.html"),

    # Reports (unique name)
    @("available_list.html",      "templates\reports\available_list.html"),

    # Costs (prefixed)
    @("cost_dashboard.html",      "templates\costs\dashboard.html"),
    @("feed_log.html",            "templates\costs\feed_log.html"),
    @("power.html",               "templates\costs\power.html"),

    # Articles (prefixed)
    @("articles_list.html",       "templates\articles\list.html"),
    @("articles_form.html",       "templates\articles\form.html"),
    @("articles_detail.html",     "templates\articles\detail.html")
)

foreach ($pair in $flatMappings) {
    $src = Join-Path $ScriptDir $pair[0]
    $dst = Join-Path $InstallDir $pair[1]
    Copy-One $src $dst | Out-Null
}

# --- Pass 2: files already inside routes\ or templates\ subfolders ----------
$subMappings = @(
    @("routes\main.py",                          "routes\main.py"),
    @("routes\species.py",                       "routes\species.py"),
    @("routes\tanks.py",                         "routes\tanks.py"),
    @("routes\breeding.py",                      "routes\breeding.py"),
    @("routes\sales.py",                         "routes\sales.py"),
    @("routes\gallery.py",                       "routes\gallery.py"),
    @("routes\public.py",                        "routes\public.py"),
    @("routes\labels.py",                        "routes\labels.py"),
    @("routes\reports.py",                       "routes\reports.py"),
    @("routes\costs.py",                         "routes\costs.py"),
    @("routes\articles.py",                      "routes\articles.py"),

    @("templates\base.html",                     "templates\base.html"),
    @("templates\dashboard.html",                "templates\dashboard.html"),
    @("templates\settings.html",                 "templates\settings.html"),

    @("templates\species\list.html",             "templates\species\list.html"),
    @("templates\species\form.html",             "templates\species\form.html"),
    @("templates\species\detail.html",           "templates\species\detail.html"),

    @("templates\tanks\list.html",               "templates\tanks\list.html"),
    @("templates\tanks\detail.html",             "templates\tanks\detail.html"),
    @("templates\tanks\edit.html",               "templates\tanks\edit.html"),

    @("templates\breeding\list.html",            "templates\breeding\list.html"),
    @("templates\breeding\form.html",            "templates\breeding\form.html"),

    @("templates\sales\list.html",               "templates\sales\list.html"),
    @("templates\sales\form.html",               "templates\sales\form.html"),
    @("templates\sales\customer_list.html",      "templates\sales\customer_list.html"),
    @("templates\sales\customer_detail.html",    "templates\sales\customer_detail.html"),
    @("templates\sales\customer_form.html",      "templates\sales\customer_form.html"),

    @("templates\gallery\index.html",            "templates\gallery\index.html"),
    @("templates\public\species.html",           "templates\public\species.html"),
    @("templates\labels\index.html",             "templates\labels\index.html"),
    @("templates\reports\available_list.html",   "templates\reports\available_list.html"),
    @("templates\costs\dashboard.html",          "templates\costs\dashboard.html"),
    @("templates\costs\feed_log.html",           "templates\costs\feed_log.html"),
    @("templates\costs\power.html",              "templates\costs\power.html"),
    @("templates\articles\list.html",            "templates\articles\list.html"),
    @("templates\articles\form.html",            "templates\articles\form.html"),
    @("templates\articles\detail.html",          "templates\articles\detail.html")
)

foreach ($pair in $subMappings) {
    $src = Join-Path $ScriptDir $pair[0]
    $dst = Join-Path $InstallDir $pair[1]
    Copy-One $src $dst | Out-Null
}

# Sanity check - warn about any critical missing files
$critical = @(
    "app.py",
    "models.py",
    "routes\main.py",
    "routes\species.py",
    "routes\tanks.py",
    "templates\base.html",
    "templates\dashboard.html"
)
$missing = @()
foreach ($f in $critical) {
    if (-not (Test-Path (Join-Path $InstallDir $f))) { $missing += $f }
}
if ($missing.Count -gt 0) {
    Write-Host ""
    Write-Err "The following critical files are missing and were NOT installed:"
    foreach ($f in $missing) { Write-Err "    $f" }
    Write-Err "Ensure all project files are in the same folder as this installer."
    Write-Host ""
}

Write-Ok "File copy complete"

# ===========================================================================
# 6. REQUIREMENTS.TXT
# ===========================================================================
Write-Header "Step 6 - requirements.txt"

$reqSrc = Join-Path $ScriptDir "requirements.txt"
if (Test-Path $reqSrc) {
    Copy-Item $reqSrc (Join-Path $InstallDir "requirements.txt") -Force
    Write-Ok "Copied existing requirements.txt"
} else {
    $reqLines = @(
        "Flask>=2.3.0",
        "Flask-SQLAlchemy>=3.1.0",
        "Pillow>=10.0.0",
        "reportlab>=4.0.0",
        "qrcode[pil]>=7.4.0"
    )
    $reqLines | Set-Content (Join-Path $InstallDir "requirements.txt") -Encoding UTF8
    Write-Ok "Generated default requirements.txt"
}

# ===========================================================================
# 7. VIRTUAL ENVIRONMENT + PACKAGES
# ===========================================================================
Write-Header "Step 7 - Virtual Environment and Packages"

Write-Info "Creating virtual environment ..."
& $PythonExe -m venv $VenvDir
if (-not $?) { Write-Err "venv creation failed."; pause; exit 1 }
Write-Ok "Virtual environment created at $VenvDir"

$PipExe     = "$VenvDir\Scripts\pip.exe"
$VenvPython = "$VenvDir\Scripts\python.exe"

Write-Info "Upgrading pip ..."
& $VenvPython -m pip install --upgrade pip --quiet
Write-Ok "pip upgraded"

Write-Info "Installing packages (this may take a few minutes) ..."
& $PipExe install -r "$InstallDir\requirements.txt" --quiet
if (-not $?) { Write-Err "Package installation failed."; pause; exit 1 }
Write-Ok "All packages installed"

# ===========================================================================
# 8. INITIALISE DATABASE
#
# The Python init script is built line by line and written to a temp file.
# This avoids ALL here-string quoting issues with Python syntax, r-strings,
# backslashes and single quotes inside PowerShell heredocs.
# ===========================================================================
Write-Header "Step 8 - Database Initialisation"

$initFile = Join-Path $env:TEMP "ma_init_db.py"

# Build each line explicitly - concatenate the variable where needed
$line1 = "import sys, os"
$line2 = "sys.path.insert(0, r'" + $InstallDir + "')"
$line3 = "os.chdir(r'" + $InstallDir + "')"
$line4 = "from app import create_app, init_db"
$line5 = "app = create_app()"
$line6 = "init_db(app)"
$line7 = "print('Database initialised successfully.')"

$pyLines = @($line1, $line2, $line3, $line4, $line5, $line6, $line7)
$pyLines | Set-Content $initFile -Encoding UTF8

& $VenvPython $initFile
if ($?) {
    Write-Ok "SQLite database initialised (instance\mason_aquatics.db)"
} else {
    Write-Info "DB init returned an error - it may initialise automatically on first run."
}
Remove-Item $initFile -Force -ErrorAction SilentlyContinue

# ===========================================================================
# 9. LAUNCHER (Start-MasonAquatics.bat)
#
# Built line by line - no here-strings.
# ===========================================================================
Write-Header "Step 9 - Creating Launcher"

$batPath = "$InstallDir\Start-MasonAquatics.bat"

$venvPythonQ = "`"$VenvDir\Scripts\python.exe`""
$portUrl     = "http://localhost:$Port"

$batLines = @(
    "@echo off",
    "title Mason Aquatics",
    "cd /d `"$InstallDir`"",
    "echo.",
    "echo  ================================================",
    "echo    Mason Aquatics ^| Fish Room Management System",
    "echo    $portUrl",
    "echo  ================================================",
    "echo.",
    "echo  Press Ctrl+C to stop the server.",
    "echo.",
    "start `"`" `"$portUrl`"",
    "$venvPythonQ app.py",
    "pause"
)
$batLines | Set-Content $batPath -Encoding ASCII
Write-Ok "Launcher created: $batPath"

# ===========================================================================
# 10. DESKTOP SHORTCUT
# ===========================================================================
Write-Header "Step 10 - Desktop Shortcut"

try {
    $WshShell = New-Object -ComObject WScript.Shell
    $lnkPath  = Join-Path $DesktopPath "Mason Aquatics.lnk"
    $Shortcut = $WshShell.CreateShortcut($lnkPath)
    $Shortcut.TargetPath       = $batPath
    $Shortcut.WorkingDirectory = $InstallDir
    $Shortcut.Description      = "Start the Mason Aquatics Fish Room Management System"
    $Shortcut.IconLocation     = "shell32.dll,25"
    $Shortcut.Save()
    Write-Ok "Desktop shortcut created: $lnkPath"
} catch {
    Write-Info "Could not create desktop shortcut - use Start-MasonAquatics.bat directly."
}

# ===========================================================================
# 11. FIREWALL
# ===========================================================================
Write-Header "Step 11 - Firewall"

$ruleName = "Mason Aquatics (port $Port)"
$existing = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Ok "Firewall rule already exists: $ruleName"
} else {
    try {
        New-NetFirewallRule `
            -DisplayName $ruleName `
            -Direction   Inbound `
            -Protocol    TCP `
            -LocalPort   $Port `
            -Action      Allow `
            -Profile     "Private,Domain" `
            -Description "Mason Aquatics Flask server on port $Port (local network only)" `
            | Out-Null
        Write-Ok "Firewall rule created: $ruleName (TCP $Port, Private/Domain)"
    } catch {
        Write-Info "Could not create firewall rule automatically - add it manually if needed."
    }
}

# ===========================================================================
# 12. AUTO-START (OPTIONAL)
# ===========================================================================
Write-Header "Step 12 - Auto-Start (Optional)"

$autoStart = ""
while ($autoStart -notin @("Y","N","y","n")) {
    $autoStart = Read-Host "  Auto-start Mason Aquatics when Windows logs in? (Y/N)"
}

if ($autoStart -in @("Y","y")) {
    $taskName  = "MasonAquatics"
    $action    = New-ScheduledTaskAction -Execute $batPath -WorkingDirectory $InstallDir
    $trigger   = New-ScheduledTaskTrigger -AtLogOn
    $settings  = New-ScheduledTaskSettingsSet `
                     -AllowStartIfOnBatteries `
                     -DontStopIfGoingOnBatteries `
                     -ExecutionTimeLimit 0
    $principal = New-ScheduledTaskPrincipal `
                     -UserId    $env:USERNAME `
                     -LogonType Interactive `
                     -RunLevel  Highest

    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask `
        -TaskName    $taskName `
        -Action      $action `
        -Trigger     $trigger `
        -Settings    $settings `
        -Principal   $principal `
        -Description "Starts Mason Aquatics Fish Room system at login" `
        | Out-Null
    Write-Ok "Task Scheduler task registered: $taskName (runs at login for $env:USERNAME)"
} else {
    Write-Info "Skipped auto-start. Use the desktop shortcut or Start-MasonAquatics.bat to launch."
}

# ===========================================================================
# 13. LAUNCH
# ===========================================================================
Write-Header "Step 13 - Launch"

$launch = ""
while ($launch -notin @("Y","N","y","n")) {
    $launch = Read-Host "  Launch Mason Aquatics now? (Y/N)"
}

if ($launch -in @("Y","y")) {
    Write-Info "Starting server - browser will open at http://localhost:$Port ..."
    Start-Process -FilePath $batPath
} else {
    Write-Info "To start later, double-click Mason Aquatics on your Desktop."
}

# ===========================================================================
# COMPLETE
# ===========================================================================
Write-Host ""
Write-Host "  ================================================" -ForegroundColor Cyan
Write-Host "   Mason Aquatics installed successfully!"          -ForegroundColor Green
Write-Host "   Install path : $InstallDir"                      -ForegroundColor White
Write-Host "   App URL      : http://localhost:$Port"           -ForegroundColor White
Write-Host "   Launcher     : $batPath"                         -ForegroundColor White
Write-Host "  ================================================" -ForegroundColor Cyan
Write-Host ""
pause
