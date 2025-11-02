# ESP32 Vending Machine Firmware - Setup Guide

## Overview

This firmware enables your ESP32 to accept XRPL PayChannel claims offline via BLE and control vending/dispensing mechanisms through relay outputs.

## Hardware Requirements

### Required Components
- **ESP32 Development Board** (ESP32-DevKitC or compatible)
- **OLED Display**: SSD1306 128x64 I2C (optional but recommended)
- **Relay Module**: 1-4 channel relay board (5V trigger)
- **Power Supply**: 5V/12V depending on vending mechanism
- **Jumper Wires** for connections

### Optional Components
- Status LEDs for visual feedback
- Buzzer for audio feedback
- Enclosure for weatherproofing

## Wiring Diagram

### OLED Display (SSD1306)
```
ESP32 Pin 5  (GPIO 5)  → SDA (Data)
ESP32 Pin 6  (GPIO 6)  → SCL (Clock)
ESP32 VCC (3.3V)       → VCC
ESP32 GND              → GND
```

### Relay Connections
```
ESP32 Pin 8  (GPIO 8)  → Relay IN (Main/Slot 0)
ESP32 Pin 23 (GPIO 23) → Relay IN (Slot 1)
ESP32 Pin 22 (GPIO 22) → Relay IN (Slot 2)
ESP32 Pin 21 (GPIO 21) → Relay IN (Slot 3)
ESP32 VCC (5V)         → Relay VCC
ESP32 GND              → Relay GND
```

**Important**: Relays switch HIGH voltage! Connect your vending solenoid/motor between relay COM and NO (Normally Open) terminals.

## Software Setup

### Arduino IDE Setup

1. **Install Arduino IDE** (version 2.0+ recommended)
   - Download from: https://www.arduino.cc/en/software

2. **Add ESP32 Board Support**
   - Go to: **File → Preferences**
   - Add to "Additional Board Manager URLs":
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Go to: **Tools → Board → Boards Manager**
   - Search for "ESP32" and install "esp32 by Espressif Systems"

3. **Install Required Libraries**

   Go to **Tools → Manage Libraries** and install:

   - **U8g2** (by oliver) - for OLED display
   - **ArduinoJson** (by Benoit Blanchon) - for JSON parsing

   BLE libraries are included with ESP32 core, no additional installation needed.

### PlatformIO Setup (Alternative)

If using PlatformIO instead of Arduino IDE:

```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
lib_deps =
    olikraus/U8g2@^2.35.9
    bblanchon/ArduinoJson@^6.21.3
monitor_speed = 115200
```

## Configuration

### 1. Open the Firmware

Open `esp32_vending_improved.ino` in Arduino IDE.

### 2. Configure Your Merchant Address

Edit these lines in the firmware (around line 20):

```cpp
#define MERCHANT_ADDRESS    "rYourMerchantAddressHere"  // Replace with your XRPL address
#define MERCHANT_DEST_TAG   700001  // Use the tag from your API /devices/register
```

### 3. Configure Device ID

```cpp
#define DEVICE_ID           "vending-001"  // Unique ID for this device
```

### 4. Adjust BLE UUIDs (if needed)

UUIDs must match your Kivy app configuration:

```cpp
#define SERVICE_UUID           "12345678-1234-5678-1234-56789abcdef0"
#define CHARACTERISTIC_TX_UUID "12345678-1234-5678-1234-56789abcdef0"
#define CHARACTERISTIC_RX_UUID "12345678-1234-5678-1234-56789abcdef1"
```

### 5. Adjust Pin Configuration (if needed)

Modify these defines to match your wiring:

```cpp
#define CONTROL_PIN         8   // Main relay
#define RELAY_PIN_SLOT_1    23
#define RELAY_PIN_SLOT_2    22
#define RELAY_PIN_SLOT_3    21
```

## Uploading the Firmware

1. **Connect ESP32** to your computer via USB
2. **Select Board**: Tools → Board → ESP32 Dev Module
3. **Select Port**: Tools → Port → (select your ESP32's COM port)
4. **Upload**: Click the Upload button (→)

Monitor the upload process. You should see:
```
Connecting....
Writing at 0x00001000... (100%)
Hash of data verified.
Leaving...
Hard resetting via RTS pin...
```

## Testing

### 1. Monitor Serial Output

Open **Tools → Serial Monitor** (set to 115200 baud)

You should see:
```
=== XRPL Offline Payments - ESP32 Vending ===
Version: 2.0.0 (Enhanced)
Device ID: vending-001
Merchant: rYourAddress...
[OLED] Initialized
[GPIO] Pins configured
[BLE] Initializing...
[BLE] Service started
[INIT] System ready
```

### 2. Check OLED Display

The display should show "Ready" centered in a box.

### 3. Test BLE Connection

- On your phone, use a BLE scanner app (e.g., "nRF Connect")
- Look for device named "ESP32_BLE_SERVER"
- Connect to it
- Display should change to "Connected"

### 4. Test Vend Command

From the Kivy app, send a vend command. The relay should click and the display shows:
- "Verified" → "Vending" → "Complete"

## Command Reference

### Read Command (from Kivy app)

ESP32 returns merchant info:
```json
{
  "merchant_address": "rYourAddress...",
  "dest_tag": 700001,
  "device_id": "vending-001"
}
```

### Vend Command (JSON)

```json
{
  "action": "vend",
  "slot": 1,
  "pulse_ms": 600,
  "claim_channel": "A1B2C3...",
  "claim_amount_drops": "2000000",
  "device_id": "vending-001"
}
```

### Status Command

```json
{
  "action": "status"
}
```

Response:
```json
{
  "device_id": "vending-001",
  "state": "Ready",
  "vending": false,
  "connected": true,
  "merchant": "rYourAddress...",
  "dest_tag": 700001
}
```

## Troubleshooting

### OLED Not Working

- Check I2C wiring (SDA/SCL)
- Try different I2C address: `0x3C` or `0x3D`
- Verify with I2C scanner sketch
- Check power (3.3V, not 5V for some OLEDs)

### BLE Not Advertising

- Ensure ESP32 board is properly selected
- Check serial monitor for BLE initialization errors
- Try resetting ESP32
- Update ESP32 core to latest version

### Relay Not Activating

- Check relay wiring (use 5V power for relay module)
- Verify GPIO pin numbers match your wiring
- Test relay manually: `digitalWrite(CONTROL_PIN, HIGH);`
- Some relays are active-LOW (invert logic if needed)

### Kivy App Can't Connect

- Ensure UUIDs match between ESP32 and app
- Check BLE is enabled on phone/tablet
- Reduce distance (BLE range ~10m)
- Restart both ESP32 and Kivy app

## Safety Features

- **Maximum pulse duration**: 5000ms (prevents relay burnout)
- **Emergency timeout**: Automatically stops vending if stuck
- **Concurrent vending prevention**: Only one vend at a time
- **State machine**: Clear state tracking prevents race conditions

## Production Deployment Tips

1. **Power Supply**: Use regulated 5V/12V supply, not USB
2. **Enclosure**: Use IP65 rated box for outdoor use
3. **Relay Protection**: Add flyback diodes for inductive loads
4. **Antenna**: External antenna improves BLE range
5. **Error Logging**: Monitor serial output for diagnostics
6. **Backup**: Keep a spare ESP32 pre-programmed

## Next Steps

1. Register this device with the API: `POST /devices/register`
2. Test with buyer tools to create PayChannel claims
3. Verify offline claim processing through Kivy app
4. Monitor settlements through the web dashboard

## Support

For issues and questions:
- Check serial monitor output first
- Review wiring against diagrams
- Test components individually
- Consult ESP32 documentation

## License

MIT License - See main project LICENSE file
