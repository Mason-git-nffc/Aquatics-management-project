#Requires -RunAsAdministrator
# Mason Aquatics - Windows Installer
# Run as Administrator from the folder containing all project files.

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Header { param([string]$m) Write-Host ("`n===  $m  ===") -ForegroundColor Cyan }
function Write-Ok     { param([string]$m) Write-Host ("  OK  " + $m) -ForegroundColor Green }
function Write-Info   { param([string]$m) Write-Host ("  >>  " + $m) -ForegroundColor Yellow }
function Write-Err    { param([string]$m) Write-Host ("  !!  " + $m) -ForegroundColor Red }

Clear-Host
Write-Host ""
Write-Host "  ================================================" -ForegroundColor Cyan
Write-Host "   Mason Aquatics - Fish Room Management System"    -ForegroundColor Cyan
Write-Host "   Windows Installer  |  All Phases Complete"       -ForegroundColor Cyan
Write-Host "  ================================================" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Admin check ───────────────────────────────────────────────────────
Write-Header "Step 1 - Administrator Check"
$principal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Err "Must be run as Administrator. Right-click and choose Run with PowerShell."
    pause; exit 1
}
Write-Ok "Running as Administrator"

# ── Step 2: Configuration ─────────────────────────────────────────────────────
Write-Header "Step 2 - Configuration"
$InstallDir  = "C:\MasonAquatics"
$VenvDir     = $InstallDir + "\.venv"
$PythonVer   = "3.11.9"
$PythonUrl   = "https://www.python.org/ftp/python/" + $PythonVer + "/python-" + $PythonVer + "-amd64.exe"
$PythonInst  = $env:TEMP + "\python-installer.exe"
$ScriptDir   = if ($PSScriptRoot -and $PSScriptRoot -ne "") { $PSScriptRoot } else { if ($MyInvocation.MyCommand.Path) { Split-Path -Parent $MyInvocation.MyCommand.Path } else { $PWD.Path } }
$DesktopPath = [Environment]::GetFolderPath("CommonDesktopDirectory")
$Port        = 5000
$VenvPython  = $VenvDir + "\Scripts\python.exe"
$VenvPip     = $VenvDir + "\Scripts\pip.exe"
$BatPath     = $InstallDir + "\Start-MasonAquatics.bat"
$ReqFile     = $InstallDir + "\requirements.txt"

Write-Info ("Install dir : " + $InstallDir)
Write-Info ("Source dir  : " + $ScriptDir)
Write-Info ("Port        : " + $Port)

# ── Step 3: Python ────────────────────────────────────────────────────────────
Write-Header "Step 3 - Python"

function Find-Python {
    foreach ($cmd in @('py','python','python3')) {
        try {
            $v = & $cmd --version 2>&1
            if ($v -match 'Python 3\.(\d+)' -and [int]$Matches[1] -ge 9) {
                $found = Get-Command $cmd -ErrorAction SilentlyContinue
                if ($found) { return $found.Source }
            }
        } catch {}
    }
    $paths = @(
        ($env:LOCALAPPDATA + "\Programs\Python\Python311\python.exe"),
        ($env:LOCALAPPDATA + "\Programs\Python\Python310\python.exe"),
        ($env:LOCALAPPDATA + "\Programs\Python\Python39\python.exe"),
        "C:\Python311\python.exe",
        "C:\Python310\python.exe",
        "C:\Python39\python.exe"
    )
    foreach ($p in $paths) { if (Test-Path $p) { return $p } }
    return $null
}

$PythonExe = Find-Python
if ($PythonExe) {
    Write-Ok ("Found: " + (& $PythonExe --version 2>&1) + " at " + $PythonExe)
} else {
    Write-Info ("Downloading Python " + $PythonVer + " ...")
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $PythonUrl -OutFile $PythonInst -UseBasicParsing
        Write-Info "Installing Python silently ..."
        $argString = "/quiet InstallAllUsers=1 PrependPath=1 Include_pip=1 Include_launcher=1"
        Start-Process -FilePath $PythonInst -ArgumentList $argString -Wait -NoNewWindow
        Remove-Item $PythonInst -Force -ErrorAction SilentlyContinue
        $env:PATH = ([System.Environment]::GetEnvironmentVariable("PATH","Machine")) + ";" +
                    ([System.Environment]::GetEnvironmentVariable("PATH","User"))
        $PythonExe = Find-Python
        if (-not $PythonExe) { throw "Python not found after install." }
        Write-Ok ("Installed: " + (& $PythonExe --version 2>&1))
    } catch {
        Write-Err "Python install failed. Install manually from https://www.python.org/downloads/"
        pause; exit 1
    }
}

# ── Step 4: Directory structure ───────────────────────────────────────────────
Write-Header "Step 4 - Creating Directory Structure"
$dirs = @(
    $InstallDir,
    ($InstallDir + "\routes"),
    ($InstallDir + "\templates\articles"),
    ($InstallDir + "\templates\species"),
    ($InstallDir + "\templates\tanks"),
    ($InstallDir + "\templates\breeding"),
    ($InstallDir + "\templates\sales"),
    ($InstallDir + "\templates\gallery"),
    ($InstallDir + "\templates\public"),
    ($InstallDir + "\templates\labels"),
    ($InstallDir + "\templates\reports"),
    ($InstallDir + "\templates\costs"),
    ($InstallDir + "\static\uploads\photos"),
    ($InstallDir + "\static\generated"),
    ($InstallDir + "\instance")
)
foreach ($d in $dirs) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
Write-Ok "All directories created"

# ── Step 5: Copy files ────────────────────────────────────────────────────────
Write-Header "Step 5 - Copying Project Files"

function Copy-If-Exists {
    param([string]$Src, [string]$Dst)
    if (Test-Path $Src) {
        Copy-Item -Path $Src -Destination $Dst -Force
        Write-Ok ([System.IO.Path]::GetFileName($Src) + " -> " + $Dst.Replace($InstallDir,""))
    } else {
        Write-Info ("Skipping (not found): " + [System.IO.Path]::GetFileName($Src))
    }
}

Copy-If-Exists ($ScriptDir + "\app.py")    ($InstallDir + "\app.py")
Copy-If-Exists ($ScriptDir + "\models.py") ($InstallDir + "\models.py")

New-Item -ItemType File -Path ($InstallDir + "\routes\__init__.py") -Force | Out-Null

$routeFiles = @(
    "main.py","tanks.py","articles.py","breeding.py","costs.py",
    "gallery.py","labels.py","public.py","reports.py","species.py","sales.py"
)
foreach ($f in $routeFiles) {
    Copy-If-Exists ($ScriptDir + "\" + $f) ($InstallDir + "\routes\" + $f)
}

$tplBase = $InstallDir + "\templates\"
$tplMap  = @(
    @{ s="base.html";            d="base.html" },
    @{ s="settings.html";        d="settings.html" },
    @{ s="dashboard.html";       d="dashboard.html" },
    @{ s="articles_list.html";   d="articles\list.html" },
    @{ s="articles_form.html";   d="articles\form.html" },
    @{ s="articles_detail.html"; d="articles\detail.html" },
    @{ s="species_detail.html";  d="species\detail.html" },
    @{ s="species_list.html";    d="species\list.html" },
    @{ s="species_form.html";    d="species\form.html" },
    @{ s="tanks_detail.html";    d="tanks\detail.html" },
    @{ s="tanks_list.html";      d="tanks\list.html" },
    @{ s="edit.html";            d="tanks\edit.html" },
    @{ s="list.html";            d="breeding\list.html" },
    @{ s="form.html";            d="breeding\form.html" },
    @{ s="sales_list.html";      d="sales\list.html" },
    @{ s="sales_form.html";      d="sales\form.html" },
    @{ s="customer_list.html";   d="sales\customer_list.html" },
    @{ s="customer_detail.html"; d="sales\customer_detail.html" },
    @{ s="customer_form.html";   d="sales\customer_form.html" },
    @{ s="gallery_index.html";   d="gallery\index.html" },
    @{ s="public_species.html";  d="public\species.html" },
    @{ s="labels_index.html";    d="labels\index.html" },
    @{ s="available_list.html";  d="reports\available_list.html" },
    @{ s="cost_dashboard.html";  d="costs\dashboard.html" },
    @{ s="feed_log.html";        d="costs\feed_log.html" },
    @{ s="power.html";           d="costs\power.html" }
)
foreach ($t in $tplMap) {
    Copy-If-Exists ($ScriptDir + "\" + $t.s) ($tplBase + $t.d)
}
Write-Ok "File copy complete"

# ── Step 6: requirements.txt ──────────────────────────────────────────────────
Write-Header "Step 6 - requirements.txt"
$srcReq = $ScriptDir + "\requirements.txt"
if (Test-Path $srcReq) {
    Copy-Item $srcReq $ReqFile -Force
    Write-Ok "Copied existing requirements.txt"
} else {
    $lines = @(
        "# Mason Aquatics - Python dependencies",
        "Flask>=2.3.0",
        "Flask-SQLAlchemy>=3.1.0",
        "Pillow>=10.0.0",
        "reportlab>=4.0.0",
        "qrcode[pil]>=7.4.0"
    )
    $lines | Set-Content -Path $ReqFile -Encoding UTF8
    Write-Ok "Generated requirements.txt"
}

# ── Step 7: Virtual environment and packages ──────────────────────────────────
Write-Header "Step 7 - Virtual Environment and Packages"
Write-Info "Creating virtual environment ..."
& $PythonExe -m venv $VenvDir
if (-not $?) { Write-Err "venv creation failed."; pause; exit 1 }
Write-Ok ("Created: " + $VenvDir)

Write-Info "Upgrading pip ..."
& $VenvPython -m pip install --upgrade pip --quiet
Write-Ok "pip upgraded"

Write-Info "Installing packages (may take a few minutes) ..."
& $VenvPip install -r $ReqFile --quiet
if (-not $?) { Write-Err "Package install failed."; pause; exit 1 }
Write-Ok "All packages installed"

# ── Step 8: Initialise database ───────────────────────────────────────────────
Write-Header "Step 8 - Database Initialisation"

$initFile    = $env:TEMP + "\ma_init.py"
$escapedPath = $InstallDir.Replace("\","\\")
$initLines   = @(
    "import sys, os",
    ("sys.path.insert(0, '" + $escapedPath + "')"),
    ("os.chdir('"           + $escapedPath + "')"),
    "from app import create_app, init_db",
    "app = create_app()",
    "init_db(app)",
    "print('Database ready.')"
)
$initLines | Set-Content -Path $initFile -Encoding UTF8

& $VenvPython $initFile
if ($?) {
    Write-Ok "Database initialised (instance\mason_aquatics.db)"
} else {
    Write-Info "DB will auto-initialise on first run."
}
Remove-Item $initFile -Force -ErrorAction SilentlyContinue

# ── Step 9: Launcher batch file ───────────────────────────────────────────────
Write-Header "Step 9 - Creating Launcher"

$pyExeLine  = ('"' + $VenvDir + '\Scripts\python.exe" app.py')
$browserCmd = ('start "" "http://localhost:' + $Port + '"')
$cdCmd      = ('cd /d "' + $InstallDir + '"')
$echoUrl    = ('echo    http://localhost:' + $Port)

$batLines = @(
    "@echo off",
    "title Mason Aquatics",
    $cdCmd,
    "echo.",
    "echo  ================================================",
    "echo    Mason Aquatics - Fish Room Management System",
    $echoUrl,
    "echo  ================================================",
    "echo.",
    "echo  Press Ctrl+C to stop the server.",
    "echo.",
    $browserCmd,
    $pyExeLine,
    "pause"
)
$batLines | Set-Content -Path $BatPath -Encoding ASCII
Write-Ok ("Launcher: " + $BatPath)

# ── Step 10: Desktop shortcut ─────────────────────────────────────────────────
Write-Header "Step 10 - Desktop Shortcut"
try {
    $lnkPath  = $DesktopPath + "\Mason Aquatics.lnk"
    $wsh      = New-Object -ComObject WScript.Shell
    $lnk      = $wsh.CreateShortcut($lnkPath)
    $lnk.TargetPath       = $BatPath
    $lnk.WorkingDirectory = $InstallDir
    $lnk.Description      = "Start Mason Aquatics Fish Room Management System"
    $lnk.IconLocation     = "shell32.dll,25"
    $lnk.Save()
    Write-Ok ("Shortcut: " + $lnkPath)
} catch {
    Write-Info "Could not create shortcut - use Start-MasonAquatics.bat directly."
}

# ── Step 11: Firewall ─────────────────────────────────────────────────────────
Write-Header "Step 11 - Windows Firewall"
$ruleName = "Mason Aquatics Port " + $Port
if (Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue) {
    Write-Ok ("Rule already exists: " + $ruleName)
} else {
    try {
        New-NetFirewallRule `
            -DisplayName $ruleName `
            -Direction   Inbound `
            -Protocol    TCP `
            -LocalPort   $Port `
            -Action      Allow `
            -Profile     Private,Domain `
            -Description "Mason Aquatics Flask server - local network only" | Out-Null
        Write-Ok ("Rule created: TCP " + $Port + ", private/domain networks")
    } catch {
        Write-Info "Could not create firewall rule - add manually if needed."
    }
}

# ── Step 12: Auto-start ───────────────────────────────────────────────────────
Write-Header "Step 12 - Auto-Start at Login (Optional)"
$ans = ""
while ($ans -notin @("Y","N","y","n")) { $ans = Read-Host "  Auto-start on Windows login? (Y/N)" }

if ($ans -in @("Y","y")) {
    $taskName = "MasonAquatics"
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    $action   = New-ScheduledTaskAction -Execute $BatPath -WorkingDirectory $InstallDir
    $trigger  = New-ScheduledTaskTrigger -AtLogOn
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit 0
    $taskPrin = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
        -Settings $settings -Principal $taskPrin -Description "Starts Mason Aquatics at login" | Out-Null
    Write-Ok ("Task registered - runs at login for " + $env:USERNAME)
} else {
    Write-Info "Skipped. Use the Desktop shortcut to launch."
}

# ── Step 13: Launch ───────────────────────────────────────────────────────────
Write-Header "Step 13 - Launch"
$go = ""
while ($go -notin @("Y","N","y","n")) { $go = Read-Host "  Launch Mason Aquatics now? (Y/N)" }
if ($go -in @("Y","y")) {
    Write-Info ("Opening http://localhost:" + $Port + " ...")
    Start-Process -FilePath $BatPath
} else {
    Write-Info "Use the Desktop shortcut or Start-MasonAquatics.bat to launch."
}

Write-Host ""
Write-Host "  ================================================" -ForegroundColor Green
Write-Host "   Installation complete!" -ForegroundColor Green
Write-Host ("   Path : " + $InstallDir) -ForegroundColor White
Write-Host ("   URL  : http://localhost:" + $Port) -ForegroundColor White
Write-Host "  ================================================" -ForegroundColor Green
Write-Host ""
pause
