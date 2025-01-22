# XceptaPay Kivy App

_App to pay with XRP._

## Purpose

The XceptaPay app enables users to make BLE payments to XceptaPay kiosks using Android or iOS devices.

### System Requirements

To use this system, you will need:

1. **Kivy App** – Available for desktop, Android, and iOS.
2. **API Backend** – Hosted in a separate repository using Node.js, Express, and MongoDB.
3. **ESP32 Device** – Runs custom C firmware to handle BLE transactions.

### How XceptaPay Works

1. The Kivy app scans for nearby XceptaPay BLE-enabled kiosks.
2. Users select the kiosk and initiate a transaction.
3. The app communicates with the ESP32 device via BLE to process the payment.
4. The backend API stores and verifies transactions, ensuring secure payments with XRP.

### Installation

#### Prerequisites

- Python 3.8+
- Kivy framework
- Android/iOS build tools (KivyMD, Buildozer for Android)

#### Steps to Install

1. Clone the repository:
   ```sh
   git clone https://github.com/yourusername/xceptapay-kivy.git
   cd xceptapay-kivy
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Run the app locally:
   ```sh
   python main.py
   ```

### Deployment

#### Android (Using Buildozer)

1. Install Buildozer:
   ```sh
   pip install buildozer
   ```
2. Build the APK:
   ```sh
   buildozer android debug
   ```

#### iOS (Using Xcode & Kivy-iOS)

Refer to the [Kivy-iOS documentation](https://kivy.org/doc/stable/guide/packaging-ios.html) for detailed setup instructions.

### API Integration

- Ensure the backend API is running before initiating transactions.
- Update `config.py` with the API endpoint.

### Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature-name`).
3. Commit your changes (`git commit -m 'Add feature'`).
4. Push to your branch (`git push origin feature-name`).
5. Create a pull request.

### License

This project is licensed under the MIT License.

### Support

For any issues, please open a ticket on the [GitHub Issues page](https://github.com/yourusername/xceptapay-kivy/issues).


