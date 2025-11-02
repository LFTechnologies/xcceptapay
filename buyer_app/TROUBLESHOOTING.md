# Troubleshooting Guide

## 🔴 Error: "Unable to find JAVA_HOME"

### What Happened?
The app tried to load `pyjnius` (Android Bluetooth library) but it requires Java, which isn't needed on desktop.

### ✅ Quick Fix

Run the clean installer:
```powershell
.\clean_and_run.bat
```

This will:
1. Delete the old virtual environment
2. Create a fresh one
3. Install only desktop-required packages (no pyjnius)
4. Launch the app

### 🔧 Manual Fix

```powershell
# 1. Remove old virtual environment
rmdir /s /q .venv

# 2. Create new one
python -m venv .venv

# 3. Activate it
.venv\Scripts\activate

# 4. Install dependencies (pyjnius is now commented out)
pip install -r requirements.txt

# 5. Run app
python main.py
```

### Why This Happened
The original `requirements.txt` included `pyjnius` which is only needed for Android. I've updated it to:
- ✅ Desktop: pyjnius is commented out (not installed)
- ✅ Android: buildozer automatically includes it

---

## 🟡 Error: "run_desktop.bat is not recognized"

### What Happened?
PowerShell requires `.\` prefix for scripts in the current directory.

### ✅ Fix

**Option 1:** Add the `.\` prefix:
```powershell
.\run_desktop.bat
```

**Option 2:** Double-click the file in File Explorer

**Option 3:** Use CMD instead of PowerShell:
```cmd
run_desktop.bat
```

---

## 🟡 Error: "python is not recognized"

### What Happened?
Python isn't installed or not in your PATH.

### ✅ Fix

1. Install Python from: https://www.python.org/downloads/
2. During installation, **check "Add Python to PATH"**
3. Restart your terminal
4. Verify: `python --version`

---

## 🟡 Error: "No module named 'kivy'"

### What Happened?
Dependencies aren't installed yet.

### ✅ Fix

```powershell
.\run_desktop.bat
```

This automatically installs all dependencies.

Or manually:
```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🟡 Error: "Cannot activate virtual environment"

### What Happened?
Virtual environment isn't created or activation failed.

### ✅ Fix

**Create venv:**
```powershell
python -m venv .venv
```

**Then activate:**
```powershell
.venv\Scripts\activate
```

**If PowerShell blocks scripts:**
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Or just use the `.bat` file:
```powershell
.\run_desktop.bat
```

---

## 🟡 Error: "Microsoft Visual C++ 14.0 is required"

### What Happened?
Kivy needs C++ build tools to compile some components.

### ✅ Fix

**Option 1:** Install Visual C++ Build Tools
- Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- Install "Desktop development with C++"
- Restart terminal
- Run: `pip install -r requirements.txt`

**Option 2:** Use pre-built wheels
```powershell
pip install --upgrade pip
pip install kivy --only-binary :all:
pip install xrpl-py
```

---

## 🟡 Error: Kivy window won't open

### What Happened?
Graphics driver or OpenGL issue.

### ✅ Fix

**Set software rendering:**
```powershell
# In PowerShell, before running
$env:KIVY_GL_BACKEND = "angle_sdl2"
python main.py
```

**Or update graphics drivers:**
- NVIDIA: https://www.nvidia.com/Download/index.aspx
- AMD: https://www.amd.com/support
- Intel: https://www.intel.com/content/www/us/en/download-center/home.html

---

## 🟡 Error: "buildozer: command not found"

### What Happened?
Buildozer only works on Linux/Mac, not Windows.

### ✅ Fix for Windows

**Use WSL2:**
See: [setup_wsl2.md](setup_wsl2.md)

**Or use Docker:**
See: [BUILD_ANDROID.md](BUILD_ANDROID.md#option-2-docker-works-on-windowsmaclinux)

**Or use Google Colab:**
See: [BUILD_ANDROID.md](BUILD_ANDROID.md#option-3-google-colab-free-cloud-based)

---

## 🟡 Error: App crashes on startup

### What Happened?
Various possible causes.

### ✅ Fix

**1. Clean install:**
```powershell
.\clean_and_run.bat
```

**2. Check Python version:**
```powershell
python --version
```
Need Python 3.8 or higher.

**3. Check dependencies:**
```powershell
.venv\Scripts\activate
pip list
```

Should see:
- kivy
- xrpl-py
- (NOT pyjnius on desktop)

**4. Run tests:**
```powershell
.venv\Scripts\activate
python test_app.py
```

This tests core logic without the GUI.

---

## 🟢 App runs but Bluetooth doesn't work

### What Happened?
Desktop mode simulates Bluetooth (it's not real).

### ✅ This is Normal!

Desktop mode prints:
```
[INFO] Running in desktop mode (Bluetooth features limited)
```

Bluetooth simulation:
- ✅ Scan shows demo device
- ✅ Connect "succeeds" (fake)
- ✅ Send prints to console (not real BT)

**To use real Bluetooth:**
- Build Android APK (see [BUILD_ANDROID.md](BUILD_ANDROID.md))
- Install on phone
- Use with actual ESP32 device

---

## 🟢 Transactions fail / "Insufficient XRP"

### What Happened?
Wallet needs XRP balance for transactions.

### ✅ Fix

**Get testnet funds:**
1. Open app
2. Wallet Screen → "Get Testnet Funds (Faucet)"
3. Wait 10-30 seconds
4. Wallet will be created with 1000 XRP (testnet)

**Or manually fund:**
- Testnet Faucet: https://xrpl.org/xrp-testnet-faucet.html
- Enter your wallet address
- Receive free testnet XRP

---

## 🟢 Channel creation fails

### What Happened?
Invalid merchant address or insufficient balance.

### ✅ Fix

**Check merchant address:**
- Must be valid XRPL address (starts with 'r')
- Copy from your vending machine app
- Example: `rN7n7otQDd6FczFgLdlqtyMVrn3HMtthP4`

**Check balance:**
- Need XRP for: channel amount + transaction fees
- Use testnet faucet to get more XRP

**Check RPC connection:**
```powershell
curl https://s.altnet.rippletest.net:51234
```
Should return JSON response.

---

## 📊 Still Having Issues?

### Diagnostic Steps

**1. Run test script:**
```powershell
.venv\Scripts\activate
python test_app.py
```

**2. Check versions:**
```powershell
python --version
pip list | findstr kivy
pip list | findstr xrpl
```

**3. Check logs:**
Look for error messages in the terminal output.

**4. Clean install:**
```powershell
.\clean_and_run.bat
```

**5. Try manual setup:**
See: [HOW_TO_RUN.md](HOW_TO_RUN.md#method-4-manual-setup)

---

## 📚 More Help

- **How to run:** [HOW_TO_RUN.md](HOW_TO_RUN.md)
- **Usage guide:** [QUICKSTART.md](QUICKSTART.md)
- **Build Android:** [BUILD_ANDROID.md](BUILD_ANDROID.md)
- **Full docs:** [README.md](README.md)

---

## 🆘 Quick Reference

| Problem | Quick Fix |
|---------|-----------|
| JAVA_HOME error | `.\clean_and_run.bat` |
| Can't find script | Use `.\` prefix in PowerShell |
| No Python | Install from python.org |
| No kivy | Run `.\run_desktop.bat` |
| C++ required | Install VS Build Tools |
| Bluetooth doesn't work | Normal on desktop - build APK |
| No XRP | Use Faucet button |
| Can't build APK | Need WSL2 on Windows |

---

**Pro Tip:** When in doubt, run `.\clean_and_run.bat` for a fresh start!
