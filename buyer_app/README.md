# XRPL Buyer Mobile App

A mobile-style Kivy application for buyers to manage XRPL wallets, open payment channels, and send signed claims via Bluetooth to offline vending machines.

## Features

- **Wallet Management**
  - Create new wallet
  - Import existing wallet from seed
  - Request testnet funds from faucet
  - Secure seed storage

- **Payment Channels**
  - Open payment channels to merchant addresses
  - Configure amount, destination tag, and settle delay
  - Automatic channel ID extraction

- **Claim Creation & Sending**
  - Create signed payment claims
  - Scan and connect to Bluetooth devices (ESP32 vending machines)
  - Send claims directly to vending machine via Bluetooth

## Quick Start (Desktop Testing)

```bash
cd buyer_app
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

## Usage Flow

1. **Setup Wallet** (Wallet Screen)
   - Create a new wallet or import existing one
   - Optionally request testnet funds via faucet
   - Backup your seed securely

2. **Open Payment Channel** (Channel Screen)
   - Enter merchant address (from vending machine)
   - Set destination tag (e.g., 700123)
   - Set channel amount in XRP
   - Click "Open Channel" to submit transaction

3. **Create & Send Claims** (Claim Screen)
   - Scan for Bluetooth devices
   - Connect to ESP32 vending machine
   - Enter claim amount (cumulative)
   - Click "Create & Send via BT" to send claim

## Building for Android

### Prerequisites
- Python 3.8+
- Buildozer (for APK building)

### Build APK

```bash
# Install buildozer
pip install buildozer

# Initialize buildozer (first time only)
buildozer init

# Build debug APK
buildozer -v android debug

# Build and deploy to connected device
buildozer android debug deploy run
```

The buildozer.spec file is pre-configured with:
- Android permissions for Bluetooth
- Required dependencies
- Proper package naming

### Install APK

After building, the APK will be in `bin/` directory:
```bash
adb install bin/xrplbuyerapp-0.1-debug.apk
```

## Desktop Testing

The app includes desktop mode for testing without Android/Bluetooth hardware:
- Bluetooth operations are simulated (prints to console)
- All XRPL functions work normally against testnet
- Window sized to mobile dimensions (480x800)

## Configuration

### Environment Variables

- `RPC_URL`: XRPL RPC endpoint (default: `https://s.altnet.rippletest.net:51234`)

### Wallet Storage

Wallet seeds are stored in:
- Linux/Mac: `~/.xrpl_buyer/wallet.json`
- Windows: `C:\Users\<username>\.xrpl_buyer\wallet.json`

**⚠️ IMPORTANT: Backup your seed! If you lose it, you lose access to your funds.**

## Bluetooth Protocol

The app sends claim JSON via Bluetooth Serial Profile (SPP):
```json
{
  "channel_id": "ABC123...",
  "amount_drops": "1000000",
  "signature": "DEF456...",
  "pubkey": "ED012...",
  "key_type": "ed25519",
  "generated_at": "2025-01-15T12:34:56Z"
}
```

The vending machine (ESP32 + Kivy app) receives this via BLE and processes it.

## Architecture

```
buyer_app/
├── main.py              # Main application
├── requirements.txt     # Python dependencies
├── buildozer.spec      # Android build config
└── README.md           # This file
```

### Classes

- `WalletManager`: Manages wallet creation, import, and storage
- `BluetoothManager`: Handles BLE scanning, connection, and data transfer
- `WalletScreen`: UI for wallet management
- `ChannelScreen`: UI for opening payment channels
- `ClaimScreen`: UI for creating and sending claims
- `XRPLBuyerApp`: Main Kivy application

## Testing with Vending Machine

1. Start the vending machine app (in `../app/`)
2. Connect vending machine BLE (usually named "ESP32_VENDING" or similar)
3. Open buyer app
4. Create/import wallet
5. Open payment channel to merchant address
6. Scan and connect to vending machine via Bluetooth
7. Create and send claim - vending machine should verify and dispense

## Security Notes

- Seeds are stored in plaintext on device - use device encryption
- For production, implement proper key management (keystore/keychain)
- Always test on Testnet before using Mainnet
- Verify merchant addresses carefully before opening channels

## Troubleshooting

### Bluetooth Connection Issues
- Ensure Bluetooth is enabled
- Grant location permissions (required for BLE scan on Android)
- Pair device first in Android settings if needed
- Check ESP32 is advertising

### Transaction Failures
- Ensure wallet has sufficient XRP balance
- Check RPC endpoint is accessible
- Verify merchant address is valid
- Check destination tag matches vending machine

### Build Errors
- Update buildozer: `pip install --upgrade buildozer`
- Clear buildozer cache: `buildozer android clean`
- Check Android SDK/NDK versions in buildozer.spec

## License

MIT
