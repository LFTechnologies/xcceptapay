# Quick WSL2 Setup for Building Android APK

## Why WSL2?

Buildozer (Android APK builder) **only works on Linux**. WSL2 gives you a full Linux environment inside Windows.

## Step 1: Install WSL2 (One-time setup)

### Open PowerShell as Administrator

Right-click Start → Windows PowerShell (Admin)

```powershell
# Install WSL2
wsl --install

# Restart your computer
```

After restart, Ubuntu will automatically open and ask you to create a username/password.

## Step 2: Setup Build Environment in WSL2

Open "Ubuntu" from Start Menu, then run:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install build dependencies
sudo apt install -y python3-pip python3-venv git zip unzip default-jdk \
    build-essential libssl-dev libffi-dev python3-dev autoconf automake \
    libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev \
    libtinfo5 cmake

# Install buildozer
pip3 install --user buildozer cython

# Add to PATH (run this or add to ~/.bashrc)
export PATH="$HOME/.local/bin:$PATH"
```

## Step 3: Access Your Files

Your Windows files are accessible in WSL2 at `/mnt/c/`

```bash
# Navigate to your project
cd /mnt/c/Users/Omera/Desktop/xrpl-offline-payments/buyer_app

# Verify files
ls -la
```

## Step 4: Build APK

```bash
# First build (takes 20-60 minutes - downloads Android SDK/NDK)
buildozer -v android debug

# The APK will be in:
# /mnt/c/Users/Omera/Desktop/xrpl-offline-payments/buyer_app/bin/
```

## Step 5: Install APK on Your Phone

### Option A: USB Cable + ADB

```bash
# In WSL2, install ADB
sudo apt install adb

# Connect phone via USB (enable USB debugging in Developer Options)
adb devices

# Install APK
adb install bin/xrplbuyerapp-0.1-armeabi-v7a-debug.apk
```

### Option B: Manual Transfer

1. Open File Explorer in Windows
2. Go to: `C:\Users\Omera\Desktop\xrpl-offline-payments\buyer_app\bin\`
3. Copy the `.apk` file to your phone (USB, email, cloud)
4. On phone: Open the APK file → Install

## Troubleshooting

### "wsl: command not found"

You need Windows 10 version 2004+ or Windows 11.

Check version: `winver` in Run dialog (Win+R)

### "buildozer: command not found"

```bash
# Make sure PATH is set
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Build fails with permission errors

```bash
# Fix permissions
chmod +x run_desktop.sh
sudo chown -R $USER:$USER .buildozer
```

### WSL2 uses too much RAM

Create/edit `C:\Users\Omera\.wslconfig`:
```ini
[wsl2]
memory=4GB
processors=2
```

Then restart WSL: `wsl --shutdown` in PowerShell

## Tips

### Access WSL files from Windows

In File Explorer, type: `\\wsl$\Ubuntu\home\<your-username>\`

### Copy files to WSL home (faster builds)

```bash
# Copy project to WSL home for faster builds
cp -r /mnt/c/Users/Omera/Desktop/xrpl-offline-payments/buyer_app ~/buyer_app
cd ~/buyer_app
buildozer android debug
```

### Subsequent builds are faster

First build: 20-60 minutes (downloads SDK/NDK)
Later builds: 5-10 minutes

### Save disk space

```bash
# After successful build, clean cache
buildozer android clean
```

## Alternative: Test Without Building

You can test the app on your Windows PC first:

```cmd
cd C:\Users\Omera\Desktop\xrpl-offline-payments\buyer_app
run_desktop.bat
```

The app works in desktop mode with simulated Bluetooth!

## Need More Help?

- WSL2 docs: https://docs.microsoft.com/en-us/windows/wsl/
- Buildozer docs: https://buildozer.readthedocs.io/
- See [BUILD_ANDROID.md](BUILD_ANDROID.md) for Docker/Colab alternatives
