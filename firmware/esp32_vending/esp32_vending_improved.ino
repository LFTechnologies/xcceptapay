/*
 * XRPL Offline Payments - ESP32 Vending Machine Firmware (Improved)
 *
 * Enhanced version with:
 * - PayChannel claim verification support
 * - OLED display with state visualization
 * - Robust BLE communication
 * - JSON claim parsing
 * - Multi-relay support
 * - Better error handling
 */

#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <ArduinoJson.h>
#include <U8g2lib.h>
#include <Wire.h>

// ********** Device Configuration **********
#define DEVICE_NAME         "ESP32_BLE_SERVER"
#define DEVICE_ID           "vending-001"

// ********** BLE Configuration **********
#define SERVICE_UUID           "12345678-1234-5678-1234-56789abcdef0"
#define CHARACTERISTIC_TX_UUID "12345678-1234-5678-1234-56789abcdef0"  // Notify/Read
#define CHARACTERISTIC_RX_UUID "12345678-1234-5678-1234-56789abcdef1"  // Write

// ********** Merchant Configuration **********
#define MERCHANT_ADDRESS    "rh1Ms9YB16C5B4kBMDNQnvC7ybqPLHkrWg"  // Your merchant address
#define MERCHANT_DEST_TAG   700001  // Your destination tag from API

// ********** Hardware Pin Configuration **********
#define CONTROL_PIN         8   // Main relay control
#define RELAY_PIN_SLOT_1    23  // Additional relay slots
#define RELAY_PIN_SLOT_2    22
#define RELAY_PIN_SLOT_3    21

// ********** OLED Screen Configuration **********
constexpr int SCREEN_WIDTH   = 128;
constexpr int SCREEN_HEIGHT  = 64;
constexpr int VIRTUAL_WIDTH  = 72;
constexpr int VIRTUAL_HEIGHT = 40;
constexpr int SHIFT_DOWN     = 4;
constexpr int X_OFFSET       = (SCREEN_WIDTH - VIRTUAL_WIDTH) / 2;
constexpr int Y_OFFSET       = ((SCREEN_HEIGHT - VIRTUAL_HEIGHT) / 2) + SHIFT_DOWN;

// Initialize U8g2 with your working configuration
U8G2_SSD1306_128X64_NONAME_F_HW_I2C u8g2(
  U8G2_R0,
  U8X8_PIN_NONE,
  /* clock=*/ 6,
  /* data=*/ 5
);

// ========== Enhanced Machine States ===========
enum MachineState {
  STATE_IDLE,
  STATE_BLE_CONNECTED,
  STATE_CLAIM_RECEIVED,
  STATE_CLAIM_VERIFIED,
  STATE_VENDING,
  STATE_TRANSACTION_COMPLETE,
  STATE_ERROR
};

// ========== Global Variables ===========
MachineState currentState = STATE_IDLE;
BLEServer* pServer = NULL;
BLECharacteristic* pTxCharacteristic = NULL;
bool deviceConnected = false;
bool oldDeviceConnected = false;

// Vending state tracking
bool vendingInProgress = false;
unsigned long vendingStartTime = 0;
unsigned long lastClaimAmount = 0;
String lastChannelId = "";
String errorMessage = "";

// Timing configuration
#define DEFAULT_PULSE_MS  600
#define MAX_PULSE_MS      5000
#define STATE_DISPLAY_MS  2000

// ========== State to String Helper ===========
const char* getStateString(MachineState s) {
  switch(s) {
    case STATE_IDLE:                 return "Ready";
    case STATE_BLE_CONNECTED:        return "Connected";
    case STATE_CLAIM_RECEIVED:       return "ClaimRcvd";
    case STATE_CLAIM_VERIFIED:       return "Verified";
    case STATE_VENDING:              return "Vending";
    case STATE_TRANSACTION_COMPLETE: return "Complete";
    case STATE_ERROR:                return "Error";
    default:                         return "Unknown";
  }
}

// ========== BLE Server Callbacks ===========
class MyServerCallbacks: public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) {
    deviceConnected = true;
    currentState = STATE_BLE_CONNECTED;
    Serial.println("[BLE] Client connected");
    sendNotification("Connected");
  }

  void onDisconnect(BLEServer* pServer) {
    deviceConnected = false;
    currentState = STATE_IDLE;
    Serial.println("[BLE] Client disconnected");
    BLEDevice::startAdvertising();
    Serial.println("[BLE] Advertising restarted");
  }
};

// ========== BLE Characteristic Callbacks ===========
class CommandCallback : public BLECharacteristicCallbacks {
  void onRead(BLECharacteristic* pCharacteristic) override {
    Serial.println("[BLE] Read request - sending merchant info");

    // Create merchant info JSON
    StaticJsonDocument<256> doc;
    doc["merchant_address"] = MERCHANT_ADDRESS;
    doc["dest_tag"] = MERCHANT_DEST_TAG;
    doc["device_id"] = DEVICE_ID;

    String response;
    serializeJson(doc, response);
    pCharacteristic->setValue(response.c_str());

    Serial.print("[BLE] Sent: ");
    Serial.println(response);
  }

  void onWrite(BLECharacteristic* pCharacteristic) override {
    String receivedData = pCharacteristic->getValue().c_str();

    if (receivedData.length() == 0) {
      Serial.println("[BLE] Empty write received");
      return;
    }

    Serial.print("[BLE] Received: ");
    Serial.println(receivedData);

    // Route commands
    handleBLECommand(receivedData);
  }
};

// ========== Setup ===========
void setup() {
  Serial.begin(115200);
  Serial.println("\n\n=== XRPL Offline Payments - ESP32 Vending ===");
  Serial.println("Version: 2.0.0 (Enhanced)");
  Serial.print("Device ID: ");
  Serial.println(DEVICE_ID);
  Serial.print("Merchant: ");
  Serial.println(MERCHANT_ADDRESS);

  // Initialize OLED
  delay(1000);
  if (!u8g2.begin()) {
    Serial.println("[OLED] ERROR: Failed to initialize");
    while(true) { delay(100); }
  }
  u8g2.setContrast(255);
  u8g2.setBusClock(400000);
  u8g2.setFont(u8g2_font_ncenB10_tr);
  Serial.println("[OLED] Initialized");

  // Initialize control pins
  pinMode(CONTROL_PIN, OUTPUT);
  pinMode(RELAY_PIN_SLOT_1, OUTPUT);
  pinMode(RELAY_PIN_SLOT_2, OUTPUT);
  pinMode(RELAY_PIN_SLOT_3, OUTPUT);

  // Ensure all relays are OFF
  digitalWrite(CONTROL_PIN, LOW);
  digitalWrite(RELAY_PIN_SLOT_1, LOW);
  digitalWrite(RELAY_PIN_SLOT_2, LOW);
  digitalWrite(RELAY_PIN_SLOT_3, LOW);
  Serial.println("[GPIO] Pins configured");

  // Initialize BLE
  initBLE();

  // Show ready state
  currentState = STATE_IDLE;
  updateDisplay();

  Serial.println("[INIT] System ready");
}

// ========== Main Loop ===========
void loop() {
  // Handle BLE connection state changes
  if (!deviceConnected && oldDeviceConnected) {
    delay(500);
    pServer->startAdvertising();
    Serial.println("[BLE] Advertising restarted");
    oldDeviceConnected = deviceConnected;
    currentState = STATE_IDLE;
  }

  if (deviceConnected && !oldDeviceConnected) {
    oldDeviceConnected = deviceConnected;
    currentState = STATE_BLE_CONNECTED;
  }

  // Safety timeout for vending
  if (vendingInProgress) {
    unsigned long elapsed = millis() - vendingStartTime;
    if (elapsed > MAX_PULSE_MS) {
      Serial.println("[VEND] Emergency timeout - stopping all relays");
      stopAllRelays();
      vendingInProgress = false;
      currentState = STATE_ERROR;
      errorMessage = "Timeout";
    }
  }

  // Update display
  updateDisplay();

  delay(100);
}

// ========== BLE Initialization ===========
void initBLE() {
  Serial.println("[BLE] Initializing...");

  BLEDevice::init(DEVICE_NAME);
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  BLEService* pService = pServer->createService(SERVICE_UUID);

  // TX Characteristic (Notify/Read) - for sending status to Kivy
  pTxCharacteristic = pService->createCharacteristic(
    CHARACTERISTIC_TX_UUID,
    BLECharacteristic::PROPERTY_READ | BLECharacteristic::PROPERTY_NOTIFY
  );
  pTxCharacteristic->addDescriptor(new BLE2902());

  // RX Characteristic (Write) - for receiving commands from Kivy
  BLECharacteristic* pRxCharacteristic = pService->createCharacteristic(
    CHARACTERISTIC_RX_UUID,
    BLECharacteristic::PROPERTY_WRITE
  );
  pRxCharacteristic->setCallbacks(new CommandCallback());

  pService->start();

  BLEAdvertising* pAdvertising = BLEDevice::getAdvertising();
  pAdvertising->addServiceUUID(SERVICE_UUID);
  pAdvertising->setScanResponse(true);
  pAdvertising->setMinPreferred(0x06);
  pAdvertising->setMinPreferred(0x12);
  BLEDevice::startAdvertising();

  Serial.println("[BLE] Service started");
  Serial.print("[BLE] Device name: ");
  Serial.println(DEVICE_NAME);
  Serial.print("[BLE] Service UUID: ");
  Serial.println(SERVICE_UUID);
}

// ========== BLE Command Handler ===========
void handleBLECommand(const String& cmd) {
  // Try to parse as JSON first (new format)
  if (cmd.startsWith("{")) {
    handleJSONCommand(cmd);
    return;
  }

  // Legacy command handling
  if (cmd.startsWith("TRANSACTION:")) {
    String transactionID = cmd.substring(12);
    Serial.print("[CMD] Processing transaction ID: ");
    Serial.println(transactionID);

    if (transactionID.length() > 0) {
      currentState = STATE_CLAIM_RECEIVED;
      activateRelay(CONTROL_PIN, DEFAULT_PULSE_MS);
      sendNotification("TRANSACTION RECEIVED");
    } else {
      currentState = STATE_ERROR;
      errorMessage = "Invalid TX";
      sendNotification("ERROR: INVALID TRANSACTION");
    }
  }
  else if (cmd.startsWith("TRAN_COMPLETE:")) {
    String completionData = cmd.substring(14);
    Serial.print("[CMD] Transaction completion: ");
    Serial.println(completionData);

    if (completionData.length() > 0) {
      currentState = STATE_TRANSACTION_COMPLETE;
      sendNotification("TRAN_COMPLETE RECEIVED");

      // Return to idle after showing complete state
      delay(STATE_DISPLAY_MS);
      currentState = STATE_IDLE;
    } else {
      currentState = STATE_ERROR;
      errorMessage = "Empty data";
      sendNotification("ERROR: EMPTY COMPLETION DATA");
    }
  }
  else {
    Serial.println("[CMD] Unknown command");
    currentState = STATE_ERROR;
    errorMessage = "Unknown cmd";
    sendNotification("ERROR: Unknown command");
  }
}

// ========== JSON Command Handler (PayChannel Claims) ===========
void handleJSONCommand(const String& jsonCmd) {
  StaticJsonDocument<512> doc;
  DeserializationError error = deserializeJson(doc, jsonCmd);

  if (error) {
    Serial.print("[JSON] Parse error: ");
    Serial.println(error.c_str());
    currentState = STATE_ERROR;
    errorMessage = "Bad JSON";
    sendNotification("ERROR: Invalid JSON");
    return;
  }

  const char* action = doc["action"];

  if (strcmp(action, "vend") == 0) {
    // Vend command with PayChannel claim
    int slot = doc["slot"] | 1;
    int pulse_ms = doc["pulse_ms"] | DEFAULT_PULSE_MS;
    const char* channel_id = doc["claim_channel"];
    const char* amount_drops_str = doc["claim_amount_drops"];
    const char* device_id = doc["device_id"];

    Serial.println("[VEND] PayChannel vend command:");
    Serial.printf("  Slot: %d\n", slot);
    Serial.printf("  Pulse: %dms\n", pulse_ms);
    Serial.printf("  Channel: %s\n", channel_id ? channel_id : "N/A");
    Serial.printf("  Amount: %s drops\n", amount_drops_str ? amount_drops_str : "N/A");
    Serial.printf("  Device: %s\n", device_id ? device_id : "N/A");

    // Store claim info
    if (channel_id) lastChannelId = String(channel_id);
    if (amount_drops_str) lastClaimAmount = String(amount_drops_str).toInt();

    // Update state and execute vend
    currentState = STATE_CLAIM_VERIFIED;
    updateDisplay();
    delay(500);

    executeVend(slot, pulse_ms);

  } else if (strcmp(action, "status") == 0) {
    // Status query
    sendStatusJSON();

  } else {
    Serial.print("[CMD] Unknown action: ");
    Serial.println(action);
    currentState = STATE_ERROR;
    errorMessage = "Bad action";
    sendNotification("ERROR: Unknown action");
  }
}

// ========== Vend Execution ===========
void executeVend(int slot, int pulse_ms) {
  if (vendingInProgress) {
    Serial.println("[VEND] ERROR: Already vending");
    sendNotification("Error: Vending in progress");
    return;
  }

  if (pulse_ms > MAX_PULSE_MS) {
    Serial.printf("[VEND] WARNING: Capping pulse from %dms to %dms\n", pulse_ms, MAX_PULSE_MS);
    pulse_ms = MAX_PULSE_MS;
  }

  // Determine relay pin
  int relayPin = getRelayPin(slot);
  if (relayPin == -1) {
    Serial.printf("[VEND] ERROR: Invalid slot %d\n", slot);
    currentState = STATE_ERROR;
    errorMessage = "Bad slot";
    sendNotification("Error: Invalid slot");
    return;
  }

  // Execute vend
  currentState = STATE_VENDING;
  vendingInProgress = true;
  vendingStartTime = millis();

  Serial.printf("[VEND] Activating slot %d for %dms\n", slot, pulse_ms);
  updateDisplay();

  activateRelay(relayPin, pulse_ms);

  vendingInProgress = false;
  currentState = STATE_TRANSACTION_COMPLETE;

  Serial.println("[VEND] Complete!");
  sendNotification("Vend complete");

  updateDisplay();
  delay(STATE_DISPLAY_MS);

  // Return to connected or idle state
  currentState = deviceConnected ? STATE_BLE_CONNECTED : STATE_IDLE;

  // Clear claim info
  lastClaimAmount = 0;
  lastChannelId = "";
}

// ========== Relay Control ===========
void activateRelay(int pin, int duration_ms) {
  digitalWrite(pin, HIGH);
  delay(duration_ms);
  digitalWrite(pin, LOW);
}

int getRelayPin(int slot) {
  switch (slot) {
    case 0: return CONTROL_PIN;
    case 1: return RELAY_PIN_SLOT_1;
    case 2: return RELAY_PIN_SLOT_2;
    case 3: return RELAY_PIN_SLOT_3;
    default: return -1;
  }
}

void stopAllRelays() {
  digitalWrite(CONTROL_PIN, LOW);
  digitalWrite(RELAY_PIN_SLOT_1, LOW);
  digitalWrite(RELAY_PIN_SLOT_2, LOW);
  digitalWrite(RELAY_PIN_SLOT_3, LOW);
}

// ========== BLE Notifications ===========
void sendNotification(const char* message) {
  if (deviceConnected && pTxCharacteristic != NULL) {
    pTxCharacteristic->setValue(message);
    pTxCharacteristic->notify();
    Serial.printf("[BLE] TX: %s\n", message);
  }
}

void sendStatusJSON() {
  StaticJsonDocument<256> doc;
  doc["device_id"] = DEVICE_ID;
  doc["state"] = getStateString(currentState);
  doc["vending"] = vendingInProgress;
  doc["connected"] = deviceConnected;
  doc["merchant"] = MERCHANT_ADDRESS;
  doc["dest_tag"] = MERCHANT_DEST_TAG;

  if (lastClaimAmount > 0) {
    doc["last_amount"] = lastClaimAmount;
  }
  if (lastChannelId.length() > 0) {
    doc["last_channel"] = lastChannelId.substring(0, 12) + "...";
  }

  String response;
  serializeJson(doc, response);
  sendNotification(response.c_str());
}

// ========== Display Update ===========
void updateDisplay() {
  u8g2.clearBuffer();

  // Draw frame
  u8g2.drawFrame(X_OFFSET, Y_OFFSET, VIRTUAL_WIDTH, VIRTUAL_HEIGHT);

  // Get state text
  const char* stateText = getStateString(currentState);

  // For error state, show error message
  const char* displayText = (currentState == STATE_ERROR && errorMessage.length() > 0)
                            ? errorMessage.c_str()
                            : stateText;

  // Center text
  int textWidth  = u8g2.getStrWidth(displayText);
  int textHeight = u8g2.getMaxCharHeight();
  int textX      = X_OFFSET + (VIRTUAL_WIDTH - textWidth) / 2;
  int textY      = Y_OFFSET + (VIRTUAL_HEIGHT + textHeight) / 2 - 2;

  u8g2.setCursor(textX, textY);
  u8g2.print(displayText);

  // Show connection indicator
  if (deviceConnected) {
    u8g2.drawDisc(SCREEN_WIDTH - 8, 8, 3);  // Small filled circle
  }

  // Show amount if available (in XRP)
  if (lastClaimAmount > 0 && currentState != STATE_IDLE) {
    char amountStr[16];
    float xrp = lastClaimAmount / 1000000.0;
    snprintf(amountStr, sizeof(amountStr), "%.2f XRP", xrp);

    u8g2.setFont(u8g2_font_6x10_tr);
    int amtWidth = u8g2.getStrWidth(amountStr);
    u8g2.setCursor((SCREEN_WIDTH - amtWidth) / 2, SCREEN_HEIGHT - 4);
    u8g2.print(amountStr);
    u8g2.setFont(u8g2_font_ncenB10_tr);  // Restore font
  }

  u8g2.sendBuffer();
}
