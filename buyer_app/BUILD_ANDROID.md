# Building Android APK - Complete Guide

## Important: Buildozer Limitations

**Buildozer only works on Linux/Mac.** If you're on Windows, you have these options:

1. **WSL2 (Windows Subsystem for Linux)** - Recommended
2. **Linux Virtual Machine** - VMware/VirtualBox
3. **Docker** - Use our pre-configured Docker setup
4. **Google Colab** - Free cloud-based building
5. **GitHub Actions** - Automated CI/CD

---

## Option 1: WSL2 on Windows (Recommended)

### Install WSL2

```powershell
# Run in PowerShell as Administrator
wsl --install
# Restart computer
```

### Setup in WSL2

```bash
# Open WSL2 terminal (Ubuntu)
cd /mnt/c/Users/Omera/Desktop/xrpl-offline-payments/buyer_app

# Install dependencies
sudo apt update
sudo apt install -y python3-pip python3-venv git zip unzip default-jdk

# Install buildozer
pip3 install --user buildozer cython

# Install Android dependencies
sudo apt install -y build-essential libssl-dev libffi-dev \
    python3-dev autoconf automake libtool pkg-config \
    zlib1g-dev libncurses5-dev libncursesw5-dev \
    libtinfo5 cmake libffi-dev libssl-dev

# Build APK
buildozer -v android debug

# APK will be in: bin/xrplbuyerapp-0.1-armeabi-v7a-debug.apk
```

---

## Option 2: Docker (Works on Windows/Mac/Linux)

### Create Dockerfile

Already created below - see `Dockerfile` in this directory.

### Build with Docker

```bash
# Build Docker image (first time only)
docker build -t xrpl-buyer-builder .

# Build APK
docker run --rm -v "%cd%":/home/user/app xrpl-buyer-builder

# APK will be in: bin/ folder
```

---

## Option 3: Google Colab (Free, Cloud-based)

### Steps:

1. Go to https://colab.research.google.com/
2. Create new notebook
3. Run these cells:

```python
# Cell 1: Install buildozer
!pip install buildozer cython
!sudo apt update
!sudo apt install -y default-jdk

# Cell 2: Upload your app
from google.colab import files
# Upload main.py, requirements.txt, buildozer.spec as a ZIP

# Cell 3: Extract and build
!unzip buyer_app.zip
%cd buyer_app
!buildozer -v android debug

# Cell 4: Download APK
from google.colab import files
!ls -la bin/
files.download('bin/xrplbuyerapp-0.1-armeabi-v7a-debug.apk')
```

---

## Option 4: GitHub Actions (Automated)

Create `.github/workflows/build-android.yml` in your repo (see file below).

Then:
1. Push code to GitHub
2. Actions will automatically build APK
3. Download from Actions tab

---

## Option 5: Linux/Mac Native

### Ubuntu/Debian

```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3-pip git zip unzip default-jdk \
    build-essential libssl-dev libffi-dev python3-dev

# Install buildozer
pip3 install --user buildozer cython

# Build
cd buyer_app
buildozer -v android debug
```

### macOS

```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python3 git
pip3 install buildozer cython

# Build
cd buyer_app
buildozer -v android debug
```

---

## Troubleshooting

### Error: "Unknown command/target android"

This means buildozer isn't finding `buildozer.spec`. Make sure:
```bash
# Verify buildozer.spec exists
ls -la buildozer.spec

# Try reinitializing
buildozer init
# Then merge our settings into the new spec file
```

### Error: "SDK/NDK not found"

Buildozer auto-downloads these. If it fails:
```bash
# Clear cache
buildozer android clean

# Retry with verbose
buildozer -v android debug
```

### Error: "Permission denied"

```bash
chmod +x ./run_desktop.sh
sudo chown -R $USER:$USER .buildozer
```

### Build too slow

```bash
# Use specific architecture only
# Edit buildozer.spec:
# android.archs = arm64-v8a

# Or use multiple cores
export MAKEFLAGS="-j4"
buildozer -v android debug
```

---

## Quick Test Without Building APK

You can test the app on your computer first:

```bash
# Windows
run_desktop.bat

# Linux/Mac
./run_desktop.sh
```

The app works in desktop mode with simulated Bluetooth!

---

## Installing APK on Device

### Via USB (ADB)

```bash
# Install ADB
# Windows: Download from https://developer.android.com/studio/releases/platform-tools
# Linux: sudo apt install adb
# Mac: brew install android-platform-tools

# Enable USB debugging on phone (Settings → Developer Options)

# Connect phone and install
adb install bin/xrplbuyerapp-0.1-armeabi-v7a-debug.apk
```

### Via File Transfer

1. Copy APK to phone (USB, email, cloud storage)
2. Open APK file on phone
3. Allow "Install from unknown sources"
4. Install

---

## Which Option Should I Use?

- **Just testing?** → Use desktop mode (`run_desktop.bat`)
- **Windows user?** → Use WSL2 (best) or Docker
- **Mac/Linux user?** → Native buildozer
- **No setup wanted?** → Google Colab
- **Team project?** → GitHub Actions

---

## Build Time

First build: **20-60 minutes** (downloads Android SDK/NDK)
Subsequent builds: **5-10 minutes**

---

## Need Help?

1. Check buildozer logs in `.buildozer/`
2. Common issues: https://buildozer.readthedocs.io/
3. Python-for-Android docs: https://python-for-android.readthedocs.io/
