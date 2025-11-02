# Quick Start Guide - XRPL Buyer App

This is a mobile-style buyer app that connects to your XRPL offline vending machine via Bluetooth.

## What This App Does

1. **Manages your XRPL wallet** - Create or import a wallet to hold XRP
2. **Opens payment channels** - Lock XRP in a channel to the vending machine merchant
3. **Creates signed claims** - Sign claims for purchases
4. **Sends via Bluetooth** - Transmits claims directly to the vending machine's ESP32

## Desktop Testing (Windows)

### Option 1: Double-click to run
Simply double-click `run_desktop.bat` in File Explorer - it will:
- Create a virtual environment
- Install dependencies
- Launch the app

### Option 2: From PowerShell
```powershell
.\run_desktop.bat
```

### Option 3: Manual setup
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Desktop Testing (Linux/Mac)

### Option 1: Run script
```bash
chmod +x run_desktop.sh
./run_desktop.sh
```

### Option 2: Manual setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Testing the Functionality

### Without GUI (core logic only)
```bash
# After activating venv and installing requirements:
python test_app.py
```

This tests:
- ✓ Wallet creation
- ✓ Wallet import from seed
- ✓ Claim signing
- ✓ Bluetooth simulation

## Using the App

### Screen 1: Wallet Management
1. Click **"Create New Wallet"** for a fresh wallet
   - OR **"Import Wallet"** if you have an existing seed
   - OR **"Get Testnet Funds"** to auto-create a funded wallet
2. **Important:** Click "Show Seed" and backup your seed securely!
3. Click **"Next: Open Channel"**

### Screen 2: Open Payment Channel
1. Enter the **Merchant Address** (get this from your vending machine)
2. Enter **Destination Tag** (default: 700123)
3. Enter **Amount (XRP)** - how much to lock in the channel
4. Click **"Open Channel"**
5. Wait for confirmation (channel ID will be displayed)
6. Click **"Next: Create Claim"**

### Screen 3: Create & Send Claims
1. Click **"Scan Devices"** to find Bluetooth devices
2. Select your ESP32 vending machine from the list
3. Wait for connection confirmation
4. Enter **Claim Amount** (must be ≤ channel amount)
5. Click **"Create & Send via BT"**
6. The claim is sent to the vending machine!

## Desktop Mode Notes

In desktop mode (non-Android):
- Bluetooth operations are **simulated** (printed to console)
- All XRPL functions work **normally** against Testnet
- You can test the full flow except actual BT transmission
- Window is sized to mobile dimensions (480x800)

## Building for Android

See [README.md](README.md#building-for-android) for full instructions.

Quick version:
```bash
pip install buildozer
buildozer -v android debug
# APK will be in bin/ folder
```

## Testing with Real Vending Machine

1. **Start vending machine app** (in `../app/`)
2. **Note the merchant address** displayed in vending app
3. **Open this buyer app** on your phone
4. **Create/import wallet** and fund it (testnet faucet)
5. **Open a channel** to the merchant address
6. **Connect via Bluetooth** to ESP32
7. **Send a claim** - vending machine should verify and dispense!

## Troubleshooting

### "No module named 'xrpl'" error
Run: `pip install -r requirements.txt`

### Window won't resize
This is normal on desktop - just resize manually

### Bluetooth not finding devices
- On Android: Grant location permissions
- On desktop: This is expected (simulated mode)

### Transaction failed
- Check you have XRP balance (use faucet)
- Verify RPC endpoint is accessible
- Check merchant address is valid

## Next Steps

- Backup your seed securely
- Test on Testnet first
- Try the full flow with your vending machine
- For production, fund wallet with real XRP on Mainnet

## Support

See the main [README.md](README.md) for:
- Architecture details
- Security notes
- Build configuration
- Bluetooth protocol specs
