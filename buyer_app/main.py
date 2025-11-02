#!/usr/bin/env python3
"""
XRPL Buyer Mobile App
Manages buyer wallet, opens payment channels, and sends claims via Bluetooth to vending machines
"""

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
import json
import os
from pathlib import Path

# XRPL imports
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import PaymentChannelCreate
from xrpl.transaction import autofill, sign, submit_and_wait
from xrpl.core.binarycodec import encode_for_signing_claim
from xrpl.core.keypairs import sign as xrpl_sign
from xrpl.utils import xrp_to_drops, drops_to_xrp
from xrpl.models.requests.account_channels import AccountChannels
from datetime import datetime

try:
    from xrpl.wallet import generate_faucet_wallet
except:
    generate_faucet_wallet = None

# Bluetooth imports
try:
    from jnius import autoclass
    from android.permissions import request_permissions, Permission
    ANDROID = True
except Exception:
    # Catches ImportError, Exception (no JAVA_HOME), and other issues
    ANDROID = False
    print("[INFO] Running in desktop mode (Bluetooth features limited)")


class WalletManager:
    """Manages buyer wallet state"""
    def __init__(self):
        self.wallet = None
        self.config_dir = Path.home() / ".xrpl_buyer"
        self.config_dir.mkdir(exist_ok=True)
        self.wallet_file = self.config_dir / "wallet.json"
        self.load_wallet()

    def load_wallet(self):
        """Load wallet from file if exists"""
        if self.wallet_file.exists():
            try:
                with open(self.wallet_file, 'r') as f:
                    data = json.load(f)
                    self.wallet = Wallet(data['seed'], sequence=0)
                    return True
            except Exception as e:
                print(f"Error loading wallet: {e}")
        return False

    def save_wallet(self):
        """Save wallet to file"""
        if self.wallet:
            with open(self.wallet_file, 'w') as f:
                json.dump({
                    'seed': self.wallet.seed,
                    'address': self.wallet.classic_address,
                    'public_key': self.wallet.public_key
                }, f, indent=2)

    def create_new_wallet(self, seed=None):
        """Create new wallet from seed or generate new"""
        if seed:
            self.wallet = Wallet.from_seed(seed)
        else:
            self.wallet = Wallet.create()
        self.save_wallet()
        return self.wallet

    def get_address(self):
        return self.wallet.classic_address if self.wallet else None

    def get_seed(self):
        return self.wallet.seed if self.wallet else None


class BluetoothManager:
    """Manages Bluetooth connectivity"""
    def __init__(self):
        self.connected = False
        self.device_address = None
        self.socket = None

        if ANDROID:
            self.BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
            self.BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')
            self.BluetoothSocket = autoclass('android.bluetooth.BluetoothSocket')
            self.UUID = autoclass('java.util.UUID')

    def request_permissions(self):
        """Request Bluetooth permissions on Android"""
        if ANDROID:
            request_permissions([
                Permission.BLUETOOTH,
                Permission.BLUETOOTH_ADMIN,
                Permission.BLUETOOTH_CONNECT,
                Permission.ACCESS_FINE_LOCATION
            ])

    def scan_devices(self):
        """Scan for available Bluetooth devices"""
        if not ANDROID:
            return [{"name": "ESP32_VENDING_DEMO", "address": "00:00:00:00:00:00"}]

        adapter = self.BluetoothAdapter.getDefaultAdapter()
        if not adapter:
            return []

        devices = []
        bonded = adapter.getBondedDevices().toArray()
        for device in bonded:
            devices.append({
                "name": device.getName(),
                "address": device.getAddress()
            })
        return devices

    def connect(self, device_address):
        """Connect to Bluetooth device"""
        if not ANDROID:
            # Desktop mode - simulate connection
            self.connected = True
            self.device_address = device_address
            return True

        try:
            adapter = self.BluetoothAdapter.getDefaultAdapter()
            device = adapter.getRemoteDevice(device_address)
            uuid = self.UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")  # SPP UUID
            self.socket = device.createRfcommSocketToServiceRecord(uuid)
            self.socket.connect()
            self.connected = True
            self.device_address = device_address
            return True
        except Exception as e:
            print(f"Bluetooth connection error: {e}")
            return False

    def disconnect(self):
        """Disconnect from Bluetooth device"""
        if self.socket and ANDROID:
            try:
                self.socket.close()
            except:
                pass
        self.connected = False
        self.device_address = None

    def send_claim(self, claim_json):
        """Send claim JSON via Bluetooth"""
        if not self.connected:
            return False

        if not ANDROID:
            # Desktop mode - just print
            print(f"[BLUETOOTH SEND] Would send to {self.device_address}:")
            print(json.dumps(claim_json, indent=2))
            return True

        try:
            data = json.dumps(claim_json).encode('utf-8')
            output_stream = self.socket.getOutputStream()
            output_stream.write(data)
            output_stream.flush()
            return True
        except Exception as e:
            print(f"Bluetooth send error: {e}")
            return False


class WalletScreen(Screen):
    """Screen for wallet management"""
    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.app_ref = app_ref
        self.name = 'wallet'

        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # Title
        layout.add_widget(Label(
            text='[b]XRPL Buyer Wallet[/b]',
            markup=True,
            size_hint_y=0.1,
            font_size='24sp'
        ))

        # Wallet info
        self.wallet_info = Label(
            text='No wallet loaded',
            size_hint_y=0.2,
            font_size='14sp'
        )
        layout.add_widget(self.wallet_info)

        # Buttons
        btn_layout = GridLayout(cols=1, spacing=10, size_hint_y=0.4)

        self.btn_new = Button(text='Create New Wallet', font_size='18sp')
        self.btn_new.bind(on_press=self.create_wallet)
        btn_layout.add_widget(self.btn_new)

        self.btn_import = Button(text='Import Wallet (Seed)', font_size='18sp')
        self.btn_import.bind(on_press=self.show_import_dialog)
        btn_layout.add_widget(self.btn_import)

        self.btn_faucet = Button(text='Get Testnet Funds (Faucet)', font_size='18sp')
        self.btn_faucet.bind(on_press=self.request_faucet)
        btn_layout.add_widget(self.btn_faucet)

        self.btn_show_seed = Button(text='Show Seed', font_size='18sp')
        self.btn_show_seed.bind(on_press=self.show_seed)
        btn_layout.add_widget(self.btn_show_seed)

        layout.add_widget(btn_layout)

        # Navigation
        self.btn_next = Button(
            text='Next: Open Channel',
            size_hint_y=0.15,
            font_size='18sp',
            background_color=(0.2, 0.6, 0.8, 1)
        )
        self.btn_next.bind(on_press=lambda x: self.app_ref.screen_manager.set_screen('channel'))
        layout.add_widget(self.btn_next)

        self.add_widget(layout)

    def on_enter(self):
        """Called when screen is displayed"""
        self.update_wallet_info()

    def update_wallet_info(self):
        """Update wallet display"""
        if self.app_ref.wallet_manager.wallet:
            addr = self.app_ref.wallet_manager.get_address()
            self.wallet_info.text = f'Address:\n{addr[:20]}...\n{addr[20:]}'
        else:
            self.wallet_info.text = 'No wallet loaded'

    def create_wallet(self, instance):
        """Create new wallet"""
        self.app_ref.wallet_manager.create_new_wallet()
        self.update_wallet_info()
        self.show_popup('Success', 'New wallet created!\nPlease backup your seed.')

    def show_import_dialog(self, instance):
        """Show import wallet dialog"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)

        content.add_widget(Label(text='Enter seed:'))
        seed_input = TextInput(multiline=False, size_hint_y=0.3)
        content.add_widget(seed_input)

        btn_layout = BoxLayout(size_hint_y=0.3, spacing=10)

        popup = Popup(title='Import Wallet', content=content, size_hint=(0.9, 0.5))

        def import_wallet(instance):
            seed = seed_input.text.strip()
            if seed:
                try:
                    self.app_ref.wallet_manager.create_new_wallet(seed)
                    self.update_wallet_info()
                    popup.dismiss()
                    self.show_popup('Success', 'Wallet imported successfully!')
                except Exception as e:
                    self.show_popup('Error', f'Invalid seed: {str(e)}')

        btn_import = Button(text='Import')
        btn_import.bind(on_press=import_wallet)
        btn_cancel = Button(text='Cancel')
        btn_cancel.bind(on_press=popup.dismiss)

        btn_layout.add_widget(btn_import)
        btn_layout.add_widget(btn_cancel)
        content.add_widget(btn_layout)

        popup.open()

    def request_faucet(self, instance):
        """Request testnet funds"""
        if not generate_faucet_wallet:
            self.show_popup('Error', 'Faucet not available in this xrpl-py version')
            return

        def do_faucet(dt):
            try:
                client = JsonRpcClient(self.app_ref.rpc_url)
                wallet = generate_faucet_wallet(client, debug=True)
                self.app_ref.wallet_manager.create_new_wallet(wallet.seed)
                self.update_wallet_info()
                self.show_popup('Success', f'Faucet wallet created!\nAddress: {wallet.classic_address}')
            except Exception as e:
                self.show_popup('Error', f'Faucet failed: {str(e)}')

        self.show_popup('Please Wait', 'Requesting testnet funds...')
        Clock.schedule_once(do_faucet, 0.5)

    def show_seed(self, instance):
        """Show wallet seed"""
        seed = self.app_ref.wallet_manager.get_seed()
        if seed:
            content = BoxLayout(orientation='vertical', padding=10, spacing=10)
            content.add_widget(Label(text='[b]BACKUP THIS SEED[/b]\n(tap to copy)', markup=True))

            seed_label = TextInput(
                text=seed,
                multiline=False,
                readonly=True,
                size_hint_y=0.3
            )
            content.add_widget(seed_label)

            btn_close = Button(text='Close', size_hint_y=0.2)
            popup = Popup(title='Wallet Seed', content=content, size_hint=(0.9, 0.5))
            btn_close.bind(on_press=popup.dismiss)
            content.add_widget(btn_close)
            popup.open()
        else:
            self.show_popup('Error', 'No wallet loaded')

    def show_popup(self, title, message):
        """Show popup message"""
        content = BoxLayout(orientation='vertical', padding=10)
        content.add_widget(Label(text=message))
        btn = Button(text='OK', size_hint_y=0.3)
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.4))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()


class ChannelScreen(Screen):
    """Screen for opening payment channels"""
    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.app_ref = app_ref
        self.name = 'channel'

        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # Title
        layout.add_widget(Label(
            text='[b]Open Payment Channel[/b]',
            markup=True,
            size_hint_y=0.08,
            font_size='24sp'
        ))

        # Form
        form = GridLayout(cols=2, spacing=10, size_hint_y=0.5)

        form.add_widget(Label(text='Merchant Address:', size_hint_x=0.4))
        self.merchant_addr = TextInput(multiline=False, size_hint_x=0.6)
        form.add_widget(self.merchant_addr)

        form.add_widget(Label(text='Destination Tag:', size_hint_x=0.4))
        self.dest_tag = TextInput(text='700123', multiline=False, size_hint_x=0.6)
        form.add_widget(self.dest_tag)

        form.add_widget(Label(text='Amount (XRP):', size_hint_x=0.4))
        self.amount_xrp = TextInput(text='2.0', multiline=False, size_hint_x=0.6)
        form.add_widget(self.amount_xrp)

        form.add_widget(Label(text='Settle Delay (sec):', size_hint_x=0.4))
        self.settle_delay = TextInput(text='600', multiline=False, size_hint_x=0.6)
        form.add_widget(self.settle_delay)

        layout.add_widget(form)

        # Status
        self.status_label = Label(
            text='Ready to open channel',
            size_hint_y=0.15,
            font_size='14sp'
        )
        layout.add_widget(self.status_label)

        # Buttons
        btn_layout = GridLayout(cols=2, spacing=10, size_hint_y=0.15)

        self.btn_open = Button(text='Open Channel', background_color=(0.2, 0.8, 0.2, 1))
        self.btn_open.bind(on_press=self.open_channel)
        btn_layout.add_widget(self.btn_open)

        btn_back = Button(text='Back')
        btn_back.bind(on_press=lambda x: self.app_ref.screen_manager.set_screen('wallet'))
        btn_layout.add_widget(btn_back)

        layout.add_widget(btn_layout)

        # Next button
        self.btn_next = Button(
            text='Next: Create Claim',
            size_hint_y=0.12,
            background_color=(0.2, 0.6, 0.8, 1)
        )
        self.btn_next.bind(on_press=lambda x: self.app_ref.screen_manager.set_screen('claim'))
        layout.add_widget(self.btn_next)

        self.add_widget(layout)

    def open_channel(self, instance):
        """Open payment channel"""
        if not self.app_ref.wallet_manager.wallet:
            self.show_popup('Error', 'No wallet loaded')
            return

        try:
            merchant = self.merchant_addr.text.strip()
            tag = int(self.dest_tag.text.strip())
            amount = float(self.amount_xrp.text.strip())
            delay = int(self.settle_delay.text.strip())

            if not merchant:
                self.show_popup('Error', 'Please enter merchant address')
                return

            self.status_label.text = 'Opening channel...'
            self.btn_open.disabled = True

            def do_open(dt):
                try:
                    client = JsonRpcClient(self.app_ref.rpc_url)
                    wallet = self.app_ref.wallet_manager.wallet

                    # Create transaction
                    tx = PaymentChannelCreate(
                        account=wallet.classic_address,
                        destination=merchant,
                        amount=str(xrp_to_drops(amount)),
                        settle_delay=delay,
                        public_key=wallet.public_key,
                        destination_tag=tag
                    )

                    # Submit
                    filled = autofill(tx, client)
                    signed = sign(filled, wallet)
                    result = submit_and_wait(signed, client)

                    # Extract channel ID
                    channel_id = self.extract_channel_id(result.result, client, wallet.classic_address, merchant)

                    if channel_id:
                        self.app_ref.channel_id = channel_id
                        self.status_label.text = f'Channel opened!\nID: {channel_id[:16]}...'
                        self.show_popup('Success', f'Channel ID:\n{channel_id}')
                    else:
                        self.status_label.text = 'Failed to get channel ID'
                        self.show_popup('Error', 'Could not extract channel ID')

                except Exception as e:
                    self.status_label.text = f'Error: {str(e)}'
                    self.show_popup('Error', str(e))
                finally:
                    self.btn_open.disabled = False

            Clock.schedule_once(do_open, 0.5)

        except ValueError as e:
            self.show_popup('Error', f'Invalid input: {str(e)}')
            self.btn_open.disabled = False

    def extract_channel_id(self, tx_result, client, source, destination):
        """Extract channel ID from transaction result"""
        # Try from metadata
        meta = tx_result.get('meta') or tx_result.get('meta_json')
        if meta:
            nodes = meta.get('AffectedNodes', [])
            for node in nodes:
                created = node.get('CreatedNode')
                if created and created.get('LedgerEntryType') == 'PayChannel':
                    cid = created.get('LedgerIndex')
                    if cid:
                        return cid

        # Fallback: query account channels
        req = AccountChannels(account=source, destination_account=destination)
        resp = client.request(req)
        channels = (resp.result or {}).get('channels', [])
        if channels:
            return channels[-1].get('channel_id')

        return None

    def show_popup(self, title, message):
        """Show popup message"""
        content = BoxLayout(orientation='vertical', padding=10)
        content.add_widget(Label(text=message))
        btn = Button(text='OK', size_hint_y=0.3)
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.4))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()


class ClaimScreen(Screen):
    """Screen for creating and sending claims"""
    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.app_ref = app_ref
        self.name = 'claim'

        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # Title
        layout.add_widget(Label(
            text='[b]Create & Send Claim[/b]',
            markup=True,
            size_hint_y=0.08,
            font_size='24sp'
        ))

        # Form
        form = GridLayout(cols=2, spacing=10, size_hint_y=0.3)

        form.add_widget(Label(text='Channel ID:', size_hint_x=0.3))
        self.channel_id = TextInput(multiline=False, size_hint_x=0.7, readonly=True)
        form.add_widget(self.channel_id)

        form.add_widget(Label(text='Claim Amount (XRP):', size_hint_x=0.3))
        self.claim_amount = TextInput(text='1.0', multiline=False, size_hint_x=0.7)
        form.add_widget(self.claim_amount)

        layout.add_widget(form)

        # Bluetooth section
        bt_layout = BoxLayout(orientation='vertical', spacing=10, size_hint_y=0.25)
        bt_layout.add_widget(Label(text='[b]Bluetooth[/b]', markup=True, size_hint_y=0.2))

        self.bt_status = Label(text='Not connected', size_hint_y=0.3, font_size='14sp')
        bt_layout.add_widget(self.bt_status)

        bt_btn_layout = GridLayout(cols=2, spacing=10, size_hint_y=0.5)

        self.btn_scan = Button(text='Scan Devices')
        self.btn_scan.bind(on_press=self.scan_bluetooth)
        bt_btn_layout.add_widget(self.btn_scan)

        self.btn_disconnect = Button(text='Disconnect', disabled=True)
        self.btn_disconnect.bind(on_press=self.disconnect_bluetooth)
        bt_btn_layout.add_widget(self.btn_disconnect)

        bt_layout.add_widget(bt_btn_layout)
        layout.add_widget(bt_layout)

        # Status
        self.status_label = Label(
            text='Ready to create claim',
            size_hint_y=0.12,
            font_size='14sp'
        )
        layout.add_widget(self.status_label)

        # Action buttons
        btn_layout = GridLayout(cols=2, spacing=10, size_hint_y=0.15)

        self.btn_send = Button(
            text='Create & Send via BT',
            background_color=(0.2, 0.8, 0.2, 1)
        )
        self.btn_send.bind(on_press=self.create_and_send_claim)
        btn_layout.add_widget(self.btn_send)

        btn_back = Button(text='Back')
        btn_back.bind(on_press=lambda x: self.app_ref.screen_manager.set_screen('channel'))
        btn_layout.add_widget(btn_back)

        layout.add_widget(btn_layout)

        # Home button
        btn_home = Button(
            text='Home',
            size_hint_y=0.1,
            background_color=(0.6, 0.6, 0.6, 1)
        )
        btn_home.bind(on_press=lambda x: self.app_ref.screen_manager.set_screen('wallet'))
        layout.add_widget(btn_home)

        self.add_widget(layout)

    def on_enter(self):
        """Called when screen is displayed"""
        if self.app_ref.channel_id:
            self.channel_id.text = self.app_ref.channel_id
        self.update_bt_status()

    def update_bt_status(self):
        """Update Bluetooth status"""
        if self.app_ref.bt_manager.connected:
            self.bt_status.text = f'Connected to:\n{self.app_ref.bt_manager.device_address}'
            self.btn_disconnect.disabled = False
        else:
            self.bt_status.text = 'Not connected'
            self.btn_disconnect.disabled = True

    def scan_bluetooth(self, instance):
        """Scan for Bluetooth devices"""
        self.app_ref.bt_manager.request_permissions()
        devices = self.app_ref.bt_manager.scan_devices()

        if not devices:
            self.show_popup('No Devices', 'No Bluetooth devices found')
            return

        # Show device selection popup
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text='Select device:', size_hint_y=0.2))

        scroll = ScrollView(size_hint_y=0.6)
        device_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
        device_layout.bind(minimum_height=device_layout.setter('height'))

        popup = Popup(title='Bluetooth Devices', content=content, size_hint=(0.9, 0.7))

        for device in devices:
            def connect_device(instance, addr=device['address']):
                if self.app_ref.bt_manager.connect(addr):
                    self.update_bt_status()
                    popup.dismiss()
                    self.show_popup('Connected', f'Connected to {addr}')
                else:
                    self.show_popup('Error', 'Failed to connect')

            btn = Button(
                text=f"{device['name']}\n{device['address']}",
                size_hint_y=None,
                height=60
            )
            btn.bind(on_press=connect_device)
            device_layout.add_widget(btn)

        scroll.add_widget(device_layout)
        content.add_widget(scroll)

        btn_cancel = Button(text='Cancel', size_hint_y=0.2)
        btn_cancel.bind(on_press=popup.dismiss)
        content.add_widget(btn_cancel)

        popup.open()

    def disconnect_bluetooth(self, instance):
        """Disconnect from Bluetooth device"""
        self.app_ref.bt_manager.disconnect()
        self.update_bt_status()

    def create_and_send_claim(self, instance):
        """Create claim and send via Bluetooth"""
        if not self.app_ref.wallet_manager.wallet:
            self.show_popup('Error', 'No wallet loaded')
            return

        if not self.channel_id.text:
            self.show_popup('Error', 'No channel ID. Please open a channel first.')
            return

        if not self.app_ref.bt_manager.connected:
            self.show_popup('Error', 'Not connected to Bluetooth device')
            return

        try:
            amount = float(self.claim_amount.text.strip())
            channel = self.channel_id.text.strip()
            wallet = self.app_ref.wallet_manager.wallet

            # Create claim
            amount_drops = str(xrp_to_drops(amount))

            try:
                msg = encode_for_signing_claim(channel, amount_drops)
            except TypeError:
                msg = encode_for_signing_claim({"channel": channel, "amount": amount_drops})

            signature = xrpl_sign(msg, wallet.private_key)

            claim = {
                "channel_id": channel,
                "amount_drops": amount_drops,
                "signature": signature,
                "pubkey": wallet.public_key,
                "key_type": "ed25519",
                "generated_at": datetime.utcnow().isoformat() + "Z"
            }

            # Send via Bluetooth
            if self.app_ref.bt_manager.send_claim(claim):
                self.status_label.text = f'Claim sent! {amount} XRP'
                self.show_popup('Success', f'Claim for {amount} XRP sent via Bluetooth!')
            else:
                self.status_label.text = 'Failed to send claim'
                self.show_popup('Error', 'Failed to send claim via Bluetooth')

        except Exception as e:
            self.status_label.text = f'Error: {str(e)}'
            self.show_popup('Error', str(e))

    def show_popup(self, title, message):
        """Show popup message"""
        content = BoxLayout(orientation='vertical', padding=10)
        content.add_widget(Label(text=message))
        btn = Button(text='OK', size_hint_y=0.3)
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.4))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()


class BuyerScreenManager:
    """Manages screen transitions"""
    def __init__(self, screen_manager):
        self.screen_manager = screen_manager

    def set_screen(self, screen_name):
        """Switch to screen"""
        self.screen_manager.current = screen_name


class XRPLBuyerApp(App):
    """Main Kivy application"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.wallet_manager = WalletManager()
        self.bt_manager = BluetoothManager()
        self.channel_id = None
        self.rpc_url = os.environ.get('RPC_URL', 'https://s.altnet.rippletest.net:51234')
        self.screen_manager = None

    def build(self):
        """Build the app UI"""
        try:
            Window.size = (480, 800)
        except:
            pass

        sm = ScreenManager()
        self.screen_manager = BuyerScreenManager(sm)

        # Add screens
        sm.add_widget(WalletScreen(self))
        sm.add_widget(ChannelScreen(self))
        sm.add_widget(ClaimScreen(self))

        return sm


if __name__ == '__main__':
    XRPLBuyerApp().run()
