# Mason Aquatics — Installation Guide

## What This Guide Covers

Installing Mason Aquatics from scratch on a Windows PC using the files in the
GitHub repository. The installer handles everything automatically — Python,
packages, database, launcher, desktop shortcut and firewall rule.

---

## Requirements

| Requirement | Notes |
|---|---|
| Windows 10 or 11 | 64-bit |
| Internet connection | Needed during install only (downloads Python if missing, installs packages) |
| Administrator access | The installer must run as Administrator |
| ~200 MB free disk space | For Python, packages and the app |

Python is **not** required beforehand — the installer downloads and installs it
automatically if it is not found.

---

## Step 1 — Download the project files

Open **PowerShell** or **Command Prompt** and run:

```
git clone https://github.com/Mason-git-nffc/Aquatics-management-project.git
```

This creates a folder called `Aquatics-management-project` wherever you ran the
command. Inside it you will find a `mason_aquatics` subfolder — that is the
folder you work from.

**No git installed?**

Go to `https://github.com/Mason-git-nffc/Aquatics-management-project`, click
the green **Code** button, then **Download ZIP**. Extract the ZIP. You will
have the same `Aquatics-management-project` folder.

---

## Step 2 — Open the project folder

Navigate into:

```
Aquatics-management-project\mason_aquatics\
```

You should see these files and folders inside it:

```
mason_aquatics\
├── Install-MasonAquaticsNEw.ps1   ← the installer
├── app.py
├── models.py
├── routes\
├── templates\
└── ... (other files)
```

---

## Step 3 — Run the installer as Administrator

1. In File Explorer, navigate to the `mason_aquatics` folder
2. Right-click **`Install-MasonAquaticsNEw.ps1`**
3. Choose **Run with PowerShell**
4. When the UAC prompt appears, click **Yes**

> If you see a red error saying "running scripts is disabled", run this first
> in an Administrator PowerShell window, then try again:
> ```
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```

---

## Step 4 — Follow the installer prompts

The installer runs through 13 steps automatically. The only decisions you are
asked to make are at the end:

| Prompt | Recommended answer |
|---|---|
| **Auto-start Mason Aquatics when Windows logs in?** | `Y` if this PC is a dedicated fish room computer, `N` otherwise |
| **Launch Mason Aquatics now?** | `Y` |

### What the installer does automatically

| Step | Action |
|---|---|
| 1 | Checks you are running as Administrator |
| 2 | Sets configuration (installs to `C:\MasonAquatics`, port 5000) |
| 3 | Finds Python 3.9+ or downloads and installs Python 3.11.9 silently |
| 4 | Creates the full directory structure at `C:\MasonAquatics` |
| 5 | Copies every project file to its correct location |
| 6 | Creates `requirements.txt` listing all Python packages |
| 7 | Creates a Python virtual environment and installs all packages |
| 8 | Initialises the SQLite database and seeds 30 tanks (T#01–T#30) |
| 9 | Creates `Start-MasonAquatics.bat` launcher |
| 10 | Creates a **Mason Aquatics** shortcut on the Desktop |
| 11 | Adds a Windows Firewall rule allowing port 5000 |
| 12 | (Optional) Registers a Task Scheduler task to start at login |
| 13 | (Optional) Launches the app and opens your browser |

---

## Step 5 — Use the app

If you chose to launch at the end of Step 4, your browser opens automatically
at:

```
http://localhost:5000
```

If you did not launch it, double-click **Mason Aquatics** on your Desktop, or
run `C:\MasonAquatics\Start-MasonAquatics.bat`.

The server prints a URL in the console window. Leave that window open while
using the app — closing it stops the server.

---

## Installed file locations

| Location | Contents |
|---|---|
| `C:\MasonAquatics\` | All application files |
| `C:\MasonAquatics\instance\mason_aquatics.db` | SQLite database (your data lives here) |
| `C:\MasonAquatics\static\uploads\photos\` | Uploaded fish photos |
| `C:\MasonAquatics\static\generated\` | Generated QR codes and PDF labels |
| `C:\MasonAquatics\Start-MasonAquatics.bat` | Launcher script |
| Desktop | **Mason Aquatics** shortcut |

---

## Accessing from other devices on your network

The app listens on all network interfaces (`0.0.0.0`), so other devices on the
same Wi-Fi or LAN can reach it.

1. Find your PC's local IP address — run `ipconfig` in Command Prompt and look
   for the **IPv4 Address** under your active network adapter (e.g.
   `192.168.1.42`)
2. On any other device on the same network, open a browser and go to:
   ```
   http://192.168.1.42:5000
   ```

The firewall rule created by the installer allows inbound connections on port
5000 from private and domain networks.

---

## Starting and stopping the app

**Start:** Double-click the **Mason Aquatics** shortcut on the Desktop, or run
`C:\MasonAquatics\Start-MasonAquatics.bat`

**Stop:** Press **Ctrl + C** in the console window, or simply close it

---

## Updating to a newer version

When new files are pushed to the GitHub repository:

1. Download the updated files (re-clone or download ZIP as in Step 1)
2. Copy the updated files from `mason_aquatics\` into `C:\MasonAquatics\`
   maintaining the same folder structure
3. Re-run the installer **OR** manually copy only the changed files

The database is not touched by updates — your data is safe.

---

## Troubleshooting

### "Running scripts is disabled"
Open PowerShell as Administrator and run:
```
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```
Then try the installer again.

### "Python still not found after install"
Close the PowerShell window completely, re-open it as Administrator, then
re-run the installer. This forces the new PATH to be picked up.

### Browser shows "This site can't be reached"
- Check the console window is still open (server is running)
- Confirm you are using `http://` not `https://`
- Try `http://127.0.0.1:5000` as an alternative address

### App shows a 500 error on first load
The database may not have initialised. Open a Command Prompt, run:
```
cd C:\MasonAquatics
.venv\Scripts\python.exe app.py
```
Look at the error message printed — it will indicate which file or import is
failing.

### Port 5000 is already in use
Another application is using port 5000. Either stop that application, or edit
`Start-MasonAquatics.bat` and change `app.py` to run on a different port by
adding `--port 5001` — or edit `app.py` and change `port=5000` to `port=5001`,
then update the shortcut target accordingly.

---

## Uninstalling

1. Delete the folder `C:\MasonAquatics` — this removes the app and all data
2. Delete the **Mason Aquatics** shortcut from the Desktop
3. Remove the firewall rule: open Windows Defender Firewall → Inbound Rules →
   find **Mason Aquatics (port 5000)** → right-click → Delete
4. If you enabled auto-start, open Task Scheduler → Task Scheduler Library →
   find **MasonAquatics** → right-click → Delete

---

## Package reference

The following Python packages are installed automatically:

| Package | Purpose |
|---|---|
| `Flask` | Web framework |
| `Flask-SQLAlchemy` | Database ORM |
| `Pillow` | Image processing for photo uploads |
| `reportlab` | PDF generation (labels and available list) |
| `qrcode[pil]` | QR code generation for tank labels |
