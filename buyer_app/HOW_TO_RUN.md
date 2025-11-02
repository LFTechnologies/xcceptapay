# How to Run the Buyer App

## 🎯 Choose Your Method

### Method 1: Double-Click (Easiest) ✅

1. Open File Explorer
2. Navigate to: `C:\Users\Omera\Desktop\xrpl-offline-payments\buyer_app`
3. **Double-click** `run_desktop.bat`
4. Done! The app will start.

---

### Method 2: PowerShell

```powershell
# Navigate to directory
cd C:\Users\Omera\Desktop\xrpl-offline-payments\buyer_app

# Run the launcher (note the .\ prefix)
.\run_desktop.bat

# Or use PowerShell script
.\run_desktop.ps1
```

**Important:** PowerShell requires `.\` before the script name!

---

### Method 3: Command Prompt (CMD)

```cmd
cd C:\Users\Omera\Desktop\xrpl-offline-payments\buyer_app
run_desktop.bat
```

---

### Method 4: Manual Setup

```powershell
# 1. Create virtual environment
python -m venv .venv

# 2. Activate it
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python main.py
```

---

## ⚠️ Common Errors

### Error: "Unable to find JAVA_HOME" ⚠️

This happens if pyjnius (Android Bluetooth library) got installed but Java isn't available.

**Quick Fix - Run clean install:**
```powershell
.\clean_and_run.bat
```

This removes the old environment and reinstalls without pyjnius (not needed on desktop).

**Manual Fix:**
```powershell
# Remove old venv
rmdir /s /q .venv

# Run setup again
.\run_desktop.bat
```

---

### Error: "run_desktop.bat is not recognized"

**In PowerShell, you need the `.\` prefix:**

❌ Wrong:
```powershell
run_desktop.bat
```

✅ Correct:
```powershell
.\run_desktop.bat
```

**Or just double-click the file in File Explorer!**

---

### Error: "python is not recognized"

Install Python from: https://www.python.org/downloads/

Make sure to check "Add Python to PATH" during installation.

---

### Error: "No module named 'kivy'"

Run the installation script:
```powershell
.\run_desktop.bat
```

It will automatically install dependencies.

---

### Error: "Execution of scripts is disabled"

PowerShell scripts are blocked. Use one of these:

**Option A:** Use the `.bat` file instead:
```powershell
.\run_desktop.bat
```

**Option B:** Enable PowerShell scripts (run as Admin):
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Option C:** Just double-click `run_desktop.bat` in File Explorer!

---

## 🧪 Test Without GUI

To test just the core functionality (wallet, claim signing):

```powershell
# Activate venv first
.venv\Scripts\activate

# Run tests
python test_app.py
```

---

## 📱 What You'll See

When the app starts, you'll see a mobile-sized window (480x800) with three screens:

1. **Wallet Screen** - Create/import wallet
2. **Channel Screen** - Open payment channels
3. **Claim Screen** - Create and send claims

Navigate using the buttons at the bottom of each screen.

---

## 🔧 Troubleshooting

### App won't start

1. Check Python is installed: `python --version`
2. Make sure you're in the right directory
3. Try manual setup (Method 4 above)

### Kivy installation fails

Try installing Visual C++ Build Tools:
https://visualstudio.microsoft.com/visual-cpp-build-tools/

Then retry:
```powershell
pip install -r requirements.txt
```

### Window is too small/large

The app defaults to 480x800 (mobile size). Just resize the window manually.

---

## 🎉 Quick Start Commands

```powershell
# Clone or navigate to project
cd C:\Users\Omera\Desktop\xrpl-offline-payments\buyer_app

# Run the app (easiest method)
.\run_desktop.bat

# That's it!
```

---

## 📚 Next Steps

Once the app is running:

1. **Create a wallet** (Wallet Screen)
2. **Get testnet funds** using the Faucet button
3. **Open a channel** to a merchant address
4. **Try sending a claim** (Bluetooth will be simulated on desktop)

See [QUICKSTART.md](QUICKSTART.md) for detailed usage instructions.

---

## 🚀 Building for Android?

Desktop testing is great, but to build an actual APK for your phone:

- See: [setup_wsl2.md](setup_wsl2.md) (Windows users)
- See: [BUILD_ANDROID.md](BUILD_ANDROID.md) (All platforms)

---

## 💡 Pro Tips

- **First time?** Let `run_desktop.bat` handle everything
- **Developing?** Use Method 4 (manual) to stay in the venv
- **Just testing?** Run `python test_app.py` for quick validation
- **Building APK?** You need Linux (WSL2 on Windows)

---

Need help? Check [START_HERE.md](START_HERE.md) for the full guide!
