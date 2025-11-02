# 🚀 START HERE - XRPL Buyer App

## What is This?

A mobile app for buyers to:
1. Manage XRPL wallets
2. Open payment channels to vending machines
3. Create and send signed claims via Bluetooth
4. Interface with your offline XRPL vending machine

---

## ⚡ Quick Start Options

### Option 1: Test on Desktop (Fastest - No Build Needed)

**🔴 Got an error? See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)**

**Windows (PowerShell):**
```powershell
# If you got "JAVA_HOME" error before, run this instead:
.\clean_and_run.bat

# Otherwise:
.\run_desktop.bat
```

**Windows (CMD):**
```cmd
run_desktop.bat
```

**Or just double-click:** `run_desktop.bat` in File Explorer

**Linux/Mac:**
```bash
./run_desktop.sh
```

This runs the app with simulated Bluetooth so you can test the UI and XRPL functions.

---

### Option 2: Build Android APK

**Important:** Building Android APKs requires **Linux or Mac**.

#### If you're on Windows:

You have 3 choices:

**A) WSL2 (Recommended)** ⭐
- See: [setup_wsl2.md](setup_wsl2.md)
- Takes 10 minutes to set up
- Then builds work perfectly

**B) Docker**
- See: [BUILD_ANDROID.md](BUILD_ANDROID.md#option-2-docker-works-on-windowsmaclinux)
- Requires Docker Desktop

**C) Google Colab (No install needed)**
- See: [BUILD_ANDROID.md](BUILD_ANDROID.md#option-3-google-colab-free-cloud-based)
- Build in the cloud, download APK

#### If you're on Linux/Mac:

```bash
# Install buildozer
pip3 install buildozer cython

# Build APK
buildozer -v android debug

# APK will be in: bin/
```

Full instructions: [BUILD_ANDROID.md](BUILD_ANDROID.md)

---

## 📖 Documentation

| File | Purpose |
|------|---------|
| **START_HERE.md** | This file - quick overview |
| **QUICKSTART.md** | How to use the app |
| **README.md** | Full documentation |
| **BUILD_ANDROID.md** | Complete Android build guide |
| **setup_wsl2.md** | WSL2 setup for Windows users |

---

## 🎯 What to Do Now

### Step 1: Test on Desktop

```cmd
run_desktop.bat
```

Play with the app, create a wallet, try opening a channel (will fail without funds, but you'll see the UI).

### Step 2: Decide on Build Method

- **Windows?** → Read [setup_wsl2.md](setup_wsl2.md)
- **Linux/Mac?** → Read [BUILD_ANDROID.md](BUILD_ANDROID.md)
- **Just want to try?** → Desktop mode is enough!

### Step 3: Read Usage Guide

See [QUICKSTART.md](QUICKSTART.md) for:
- How to use each screen
- How to connect to vending machine
- How to send claims via Bluetooth

---

## 📱 App Screens

```
┌─────────────────────┐
│   Wallet Screen     │  Create/import wallet, get testnet funds
│   • Create Wallet   │
│   • Import Seed     │
│   • Get Faucet      │
└─────────────────────┘
          ↓
┌─────────────────────┐
│  Channel Screen     │  Open payment channel to merchant
│   • Merchant Addr   │
│   • Amount (XRP)    │
│   • Open Channel    │
└─────────────────────┘
          ↓
┌─────────────────────┐
│   Claim Screen      │  Connect via BT and send claims
│   • Scan BT         │
│   • Create Claim    │
│   • Send via BT     │
└─────────────────────┘
```

---

## 🔧 Files Explanation

```
buyer_app/
├── main.py              # Main app (run this)
├── test_app.py          # Test without UI
├── requirements.txt     # Python packages
├── buildozer.spec      # Android build config
├── Dockerfile          # Docker build option
│
├── START_HERE.md       # ← You are here
├── QUICKSTART.md       # Usage guide
├── README.md           # Full docs
├── BUILD_ANDROID.md    # Build instructions
└── setup_wsl2.md       # Windows/WSL2 setup
```

---

## ❓ Common Questions

### Can I test without building APK?

**Yes!** Use `run_desktop.bat` - it simulates Bluetooth and works great for testing.

### Why can't I build on Windows directly?

Buildozer (the Android build tool) requires Linux. Use WSL2 to get Linux on Windows.

### How long does building take?

- First build: 20-60 minutes (downloads Android SDK/NDK)
- Later builds: 5-10 minutes

### Can I use this on Mainnet?

The app works on both Testnet and Mainnet. Just change the RPC URL. **Always test on Testnet first!**

### Where is my wallet stored?

Desktop: `C:\Users\Omera\.xrpl_buyer\wallet.json`
Android: App private storage

**⚠️ Backup your seed!**

---

## 🚨 Build Error?

See [BUILD_ANDROID.md](BUILD_ANDROID.md#troubleshooting) for solutions.

Common fixes:
```bash
# Clear cache
buildozer android clean

# Reinstall buildozer
pip3 install --upgrade buildozer

# Check buildozer.spec exists
ls -la buildozer.spec
```

---

## 🎉 Next Steps

1. ✅ Test on desktop (`run_desktop.bat`)
2. ✅ Read [QUICKSTART.md](QUICKSTART.md)
3. ✅ Set up WSL2 if on Windows
4. ✅ Build APK
5. ✅ Install on phone
6. ✅ Connect to vending machine!

---

## 📞 Help

- Buildozer issues: https://buildozer.readthedocs.io/
- XRPL docs: https://xrpl.org/
- Kivy docs: https://kivy.org/doc/stable/

Happy building! 🎊
