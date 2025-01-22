import asyncio
import threading
import json
import os
import requests

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

from bleak import BleakScanner, BleakClient
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import Payment
from xrpl.models.requests import AccountInfo
from xrpl.transaction import autofill, sign, submit_and_wait
from xrpl.wallet import Wallet
from xrpl.ledger import get_latest_validated_ledger_sequence
from xrpl.account import get_next_valid_seq_number

class UserProfile:
    def __init__(self, username, email, balance, transaction_history, wallet, seed):
        self.username = username
        self.email = email
        self.balance = balance
        self.transaction_history = transaction_history
        self.wallet = wallet
        self.seed = seed


################################################################################
# CONFIG: Point to your Express-based API
API_BASE_URL = "http://localhost:3000"

def get_user_by_id(user_id, token):
    """Fetch a single user by ID, using the token for authorization."""
    url = f"{API_BASE_URL}/users/{user_id}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()  # The user doc from your Node.js API
    except Exception as e:
        return {"error": str(e)}


################################################################################
# If you want to load/create a wallet on startup, define load_wallet here
# or in a separate file. We'll keep it as is for now:

#WALLET_INFO_FILE = "wallet_info.json"

#def load_wallet():
#    if os.path.exists(WALLET_INFO_FILE):
#        try:
#            with open(WALLET_INFO_FILE, "r") as f:
#                data = json.load(f)
#                seed = data.get("seed")
#                if seed:
#                    return Wallet.from_seed(seed)
#        except Exception as e:
#            print(f"Failed to load wallet info: {e}")
#    w = Wallet.create()
#    save_wallet_info(w.seed)
#    return w

#def save_wallet_info(seed):
#    with open(WALLET_INFO_FILE, "w") as f:
#        json.dump({"seed": seed}, f)
#    print("Wallet info saved.")



#wallet = load_wallet()
#print(f"Current wallet: Address: {wallet.classic_address}, Seed: {wallet.seed}")
##WALLET DB#################################################################


def load_wallet(user_id, token):
    """
    Fetch the user's seed from the Node.js server (GET /users/:id),
    create a Wallet from xrpl-py. If no seed on server, create + save.
    """
    # 1) GET /users/:id
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = f"{API_BASE_URL}/users/{user_id}"
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        user_doc = resp.json()  # e.g., { "_id": "...", "seed": "...", "wallet": "...", ...}
    except Exception as e:
        print(f"Error fetching user from server: {e}")
        # Optionally fallback to generating a new wallet
        # Or just re-raise
        raise

    # 2) If user_doc has 'seed', create the wallet
    seed = user_doc.get("seed")
    if seed:
        w = Wallet.from_seed(seed)
        print(f"Loaded wallet from DB: {w.classic_address}")
        return w
    else:
        # If no seed in DB, create a new one and save
        w = Wallet.create()
        print("No seed in DB. Creating new wallet and saving...")
        save_wallet_info(w.seed, user_id, token)
        return w

def save_wallet_info(seed, user_id, token):
    """
    Save the seed to the database via PUT /users/:id 
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = f"{API_BASE_URL}/users/{user_id}"
    body = {
        "seed": seed  # server must handle storing this securely in user doc
    }
    try:
        resp = requests.put(url, json=body, headers=headers)
        resp.raise_for_status()
        updated_user = resp.json()
        print("Wallet info saved to DB:", updated_user)
    except Exception as e:
        print(f"Error saving wallet info to DB: {e}")
        raise


################################################################################
# BLE Client
XRP_RPC_URL = "https://s.altnet.rippletest.net:51234" 
class BLEClient:
    def __init__(self):
        self.client = None
        self.device = None
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._start_loop, daemon=True)

    def _start_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run_coroutine(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result()

    def start(self):
        self.thread.start()

    async def scan_and_connect(self):
        devices = await BleakScanner.discover()
        for d in devices:
            if d.name == "ESP32_BLE_SERVER":  # Update if needed
                self.device = d
                break
        if self.device:
            self.client = BleakClient(self.device.address)
            try:
                await self.client.connect()
                return True
            except Exception as e:
                print(f"Failed to connect: {e}")
        return False

    async def disconnect(self):
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            print("Disconnected from ESP32.")
            self.client = None

    async def read_characteristic(self):
        if self.client and self.client.is_connected:
            try:
                value = await self.client.read_gatt_char("12345678-1234-5678-1234-56789abcdef0")
                return value.decode("utf-8")
            except Exception as e:
                print(f"Failed to read characteristic: {e}")
        return None

################################################################################
# MAIN SCREEN
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "main"

        # We'll initialize self.user to None
        self.user = None

        # Create the top-level layout
        layout = BoxLayout(orientation='vertical')

        # BLE client
        self.ble_client = BLEClient()
        self.ble_client.start()

        # 1) User info bar
        user_info_bar = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        self.username_label = Label(text="User: ???", halign='left')
        self.email_label = Label(text="Email: ???", halign='right')
        user_info_bar.add_widget(self.username_label)
        user_info_bar.add_widget(self.email_label)
        layout.add_widget(user_info_bar)

        # 2) Status label
        self.label = Label(text="Press Connect to start", halign='center', size_hint=(1, 0.1))
        layout.add_widget(self.label)

        # 3) Balance + refresh
        balance_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        self.balance_label = Label(text="Balance: 0 XRP", halign='center')
        refresh_button = Button(text="Refresh Balance", size_hint=(None, 1), width=150)
        refresh_button.bind(on_press=self.refresh_balance)
        balance_layout.add_widget(self.balance_label)
        balance_layout.add_widget(refresh_button)
        layout.add_widget(balance_layout)

        # 4) BLE Connect/Disconnect
        connect_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
        self.connect_button = Button(text="Connect to ESP32")
        self.connect_button.bind(on_press=self.connect_to_device)
        connect_layout.add_widget(self.connect_button)

        self.disconnect_button = Button(text="Disconnect", disabled=True)
        self.disconnect_button.bind(on_press=self.disconnect_from_device)
        connect_layout.add_widget(self.disconnect_button)
        layout.add_widget(connect_layout)

        # 5) Transaction History
        layout.add_widget(Label(text="Transaction History:", size_hint=(1, 0.1)))
        self.history_scroll = ScrollView(size_hint=(1, 0.4))
        self.history_layout = GridLayout(cols=1, size_hint_y=None)
        self.history_layout.bind(minimum_height=self.history_layout.setter('height'))
        self.history_scroll.add_widget(self.history_layout)
        layout.add_widget(self.history_scroll)

        # 6) Amount + Send
        self.amount_field = TextInput(hint_text="Enter amount (XRP)", multiline=False, size_hint=(1, 0.1))
        layout.add_widget(self.amount_field)

        self.send_button = Button(text="Send XRP", size_hint=(1, 0.1))
        self.send_button.bind(on_press=self.send_xrp)
        layout.add_widget(self.send_button)

        # 7) Bottom bar
        bottom_bar = BoxLayout(orientation='horizontal', size_hint=(1, 0.1), padding=0, spacing=2)
        button_icons = [
            "\uf013",  # Settings (cog)
            "\uf016",  # Home
            "\uf018",  # Envelope (messages)
            "\uf020",  # Shopping cart
            "\uf022",  # Users
        ]
        for icon in button_icons:
            btn = Button(text=icon, font_name="font-awesome/FontAwesome.ttf", font_size=24, size_hint=(1, 1))
            if icon == "\uf013":  # settings
                btn.bind(on_press=self.open_settings)
            bottom_bar.add_widget(btn)
        layout.add_widget(bottom_bar)

        # Add the layout to the screen
        self.add_widget(layout)

    def on_pre_enter(self, *args):
        """ Called each time we switch to the MainScreen. """
        super().on_pre_enter(*args)
        app = self.manager.app

        # If user is logged in, fetch from DB
        if getattr(app, "jwt_token", None) and getattr(app, "current_user", None):
            user_id = app.current_user.get("id")  # user doc from login
            if user_id:
                result = get_user_by_id(user_id, app.jwt_token)
                if "error" in result:
                    self.label.text = f"Error fetching user from DB: {result['error']}"
                else:
                    # result is the real user doc from the server
                    self.user = self._to_userprofile(result)
                    # Update UI
                    self.username_label.text = f"User: {self.user.username}"
                    self.email_label.text = f"Email: {self.user.email}"
                    self.balance_label.text = f"Balance: {self.user.balance:.2f} XRP"
                    self._refresh_transaction_ui()
            else:
                self.label.text = "No 'id' found in current_user."
        else:
            self.label.text = "No token or user found, not logged in."
    def get_user_on_server(self, user_id):
        """
        GET /users/:id from the Node.js server.
        Returns: a dict with user data or {"error": "..."} on failure.
        """
        app = self.manager.app
        if not app or not app.jwt_token:
            return {"error": "No app token found."}

        token = app.jwt_token
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        url = f"{API_BASE_URL}/users/{user_id}"
        try:
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()  # Should be the user doc from server
        except Exception as e:
            return {"error": str(e)}


    def _to_userprofile(self, user_doc):
        """Convert the server user doc into a local UserProfile-like object."""
        return UserProfile(
            username=user_doc.get("username", "Unknown"),
            email=user_doc.get("email", ""),
            balance=user_doc.get("balance", 0),
            transaction_history=user_doc.get("transaction_history", []),
            wallet=user_doc.get("wallet", ""),
            seed=user_doc.get("seed", "")
        )

    def _refresh_transaction_ui(self):
        """Rebuild the transaction history portion with fresh data."""
        self.history_layout.clear_widgets()
        if self.user and self.user.transaction_history:
            for tx in self.user.transaction_history:
                tx_label = Label(
                    text=(
                        f"Date: {tx['date']}, "
                        f"Amount: {tx['amount']} XRP, "
                        f"Recipient: {tx['recipient']}, "
                        f"Status: {tx['status']}"
                    ),
                    size_hint_y=None,
                    height=40
                )
                self.history_layout.add_widget(tx_label)

    ########################################################################
    # BLE Methods
    def connect_to_device(self, instance):
        connected = self.ble_client.run_coroutine(self.ble_client.scan_and_connect())
        if connected:
            self.label.text = "Connected! Reading address..."
            self.receiving_address = self.ble_client.run_coroutine(self.ble_client.read_characteristic())
            if self.receiving_address:
                self.label.text = f"Receiving Address: {self.receiving_address}"
                self.disconnect_button.disabled = False
            else:
                self.label.text = "Failed to read address."
        else:
            self.label.text = "Failed to connect."

    def disconnect_from_device(self, instance):
        self.ble_client.run_coroutine(self.ble_client.disconnect())
        self.label.text = "Disconnected."
        self.disconnect_button.disabled = True

    ########################################################################
    # XRPL Methods
    def load_user_from_db(self):
        app = self.manager.app
        if app and app.jwt_token and app.current_user:
            user_id = app.current_user.get("id")
            if not user_id:
                self.label.text = "No user ID in current_user."
                return False
            user_doc = self.get_user_on_server(user_id)  # e.g. GET /users/:id
            if "error" in user_doc:
                self.label.text = f"Error fetching user from server: {user_doc['error']}"
                return False
            # user_doc might contain {"wallet":"rExample","seed":"sExample",...}
            self.user.wallet = user_doc.get("wallet", "")
            self.user.seed = user_doc.get("seed", "")
            return True
        else:
            self.label.text = "Not logged in or missing token."
            return False

    def send_xrp(self, instance):
        # 1. Check we have a BLE-based receiving address
        if not getattr(self, "receiving_address", None):
            self.label.text = "No receiving address. Connect first!"
            return

        try:
            # 2. Get the send amount
            amount = self.amount_field.text.strip()
            if not amount.isdigit():
                self.label.text = "Invalid amount. Enter a numeric amount."
                return

            # 3. Fetch latest wallet & seed from DB
            if not self.load_user_from_db():
                # If it fails, load_user_from_db can set self.label.text with an error
                return

            # 4. Build a local XRPL Wallet object from the newly fetched seed
            from xrpl.wallet import Wallet
            if not self.user.seed:
                self.label.text = "No seed found in user data."
                return
            send_wallet = Wallet(seed=self.user.seed)  # real sequence is autofilled later

            client = JsonRpcClient(XRP_RPC_URL)
            amount_drops = str(int(amount) * 1_000_000)
            current_validated_ledger = get_latest_validated_ledger_sequence(client)
            sequence_number = get_next_valid_seq_number(send_wallet.classic_address, client)

            payment_tx = Payment(
                account=send_wallet.classic_address,
                amount=amount_drops,
                destination=self.receiving_address,
                last_ledger_sequence=current_validated_ledger + 20,
                sequence=sequence_number,
                fee="10",
            )

            # 6. Autofill, sign, submit
            autofilled_tx = autofill(payment_tx, client)
            signed_tx = sign(autofilled_tx, send_wallet)
            tx_response = submit_and_wait(signed_tx, client)

            print("Transaction Response:", tx_response)
            if hasattr(tx_response, "result"):
                engine_result = tx_response.result.get("TransactionResult", False)
                validated = tx_response.result.get("validated", False)
                tx_hash = tx_response.result.get("tx_json", {}).get("hash", "Unknown")
            else:
                self.label.text = "Unexpected response format. Check console for details."
                return

            # 7. Check final result
            if engine_result == "tesSUCCESS" and validated:
                self.label.text = (
                    f"Transaction successful!\n"
                    f"Amount: {int(amount_drops) / 1_000_000:.6f} XRP\n"
                    f"Recipient: {self.receiving_address}\n"
                    f"Transaction Hash: {tx_hash}"
                )
            else:
                self.label.text = (
                    f"Transaction status unclear.\n"
                    f"Engine Result: {engine_result}\n"
                    f"Validated: {validated}\n"
                    f"Amount: {int(amount_drops) / 1_000_000:.6f} XRP"
                )
                self.refresh_balance(None)
        except Exception as e:
            self.label.text = f"Error during transaction: {str(e)}"


    ########################################################################
    # Settings, etc.
    def create_new_wallet(self, instance):
        global wallet
        wallet = Wallet.create()
        save_wallet_info(wallet.seed)

        # Fix the hasattr calls:
        if hasattr(self, "wallet_address_label"):
            self.wallet_address_label.text = f"Wallet Address:\n{wallet.classic_address}"
        if hasattr(self, "seed_label"):
            self.seed_label.text = f"Seed:\n{wallet.seed}"

        self.label.text = "New wallet created successfully!"

    def refresh_balance(self, *args):
        """
        Refresh the user's XRP balance using xrpl-py and update a Label.
        """
        try:
            from xrpl.clients import JsonRpcClient
            from xrpl.models.requests import AccountInfo

            # Suppose your seed is in self.user.seed, or you already have a global wallet
            # For now, let's assume you have a 'wallet' loaded similarly to 'send_xrp'
            client = JsonRpcClient(XRP_RPC_URL)
            # Re-create the Wallet object or store a global wallet
            from xrpl.wallet import Wallet
            seed = self.user.seed
            if not seed:
                self.label.text = "No seed found for refreshing balance."
                return

            wallet = Wallet(seed, 0)

            # Prepare an AccountInfo request
            request = AccountInfo(
                account=wallet.classic_address,
                ledger_index="validated",
                strict=True
            )
            response = client.request(request).result

            if "account_data" in response:
                balance_drops = int(response["account_data"]["Balance"])
                balance_xrp = balance_drops / 1_000_000
                # update your UI label for balance
                self.balance_label.text = f"Balance: {balance_xrp:.6f} XRP"
            else:
                self.label.text = "Could not retrieve account data."
        except Exception as e:
            self.label.text = f"Error refreshing balance: {str(e)}"

    

    def save_custom_wallet(self, instance):
        new_address = self.custom_address_input.text.strip()
        new_seed = self.custom_seed_input.text.strip()

        # 1) Update local user object
        if new_address:
            self.user.wallet = new_address
            if hasattr(self, "wallet_address_label"):
                self.wallet_address_label.text = f"Wallet Address:\n{self.user.wallet}"
        if new_seed:
            self.user.seed = new_seed
            if hasattr(self, "seed_label"):
                self.seed_label.text = "Seed: [Hidden]"

        # 2) Also update on the server (PUT /users/:id)
        app = self.manager.app
        if app and app.jwt_token and app.current_user:
            user_id = app.current_user.get("id")
            if user_id:
                # Prepare the fields to update
                updates = {}
                if new_address:
                    updates["wallet"] = new_address
                if new_seed:
                    updates["seed"] = new_seed

                if updates:
                    resp = self.update_user_on_server(user_id, updates)
                    if "error" in resp:
                        self.label.text = f"Error updating wallet info on server: {resp['error']}"
                        return

        self.label.text = "Wallet updated successfully!"


    def update_user_on_server(self, user_id, updates):
        """Utility to do PUT /users/:id with the token from the app."""
        app = self.manager.app
        token = app.jwt_token
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        url = f"{API_BASE_URL}/users/{user_id}"

        try:
            r = requests.put(url, json=updates, headers=headers)
            r.raise_for_status()
            return r.json()  # The updated user doc
        except Exception as e:
            return {"error": str(e)}



    def save_user_data(self, instance):
        if not self.user:
            return
        if not getattr(self, "username_input", None) or not getattr(self, "email_input", None):
            return

        username = self.username_input.text.strip()
        email = self.email_input.text.strip()

        if username and email:
            self.label.text = f"User Data Updated:\nUsername: {username}\nEmail: {email}"
        elif username:
            self.label.text = "Username updated but email missing."
        elif email:
            self.label.text = "Email updated but username missing."
        else:
            self.label.text = "No changes made. Enter valid data."

    def open_settings(self, instance):
        tab_panel = TabbedPanel(size_hint=(1, 1), do_default_tab=False)
        # (same code for creating wallet tab, user data tab, etc. as before)
        # Make sure that references to self.user.* are used instead of mock_user
        # ...
        # Create the TabbedPanel
        tab_panel = TabbedPanel(size_hint=(1, 1), do_default_tab=False)

        # Wallet Tab
        wallet_tab = TabbedPanelItem(text="Wallet")
        wallet_content = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Display wallet information
        self.wallet_address_label = Label(
            text=f"Wallet Address:\n{self.user.wallet}", halign='center', size_hint=(1, 0.2)
        )
        self.seed_label = Label(
            text="Seed: [Hidden]", halign='center', size_hint=(1, 0.2)  # Seed is hidden by default
        )
        wallet_content.add_widget(self.wallet_address_label)
        wallet_content.add_widget(self.seed_label)

        # Button to reveal the seed
        def reveal_seed(instance):
            self.seed_label.text = (
                f"Seed:\n{self.user.seed}" if self.seed_label.text == "Seed: [Hidden]" else "Seed: [Hidden]"
            )

        reveal_button = Button(
            text="Show/Hide Seed",
            size_hint=(1, 0.1)
        )
        reveal_button.bind(on_press=reveal_seed)
        wallet_content.add_widget(reveal_button)

        # Input fields for a custom address and seed
        self.custom_address_input = TextInput(
            text=self.user.wallet, hint_text="Enter custom address", multiline=False, size_hint=(1, 0.1)
        )
        self.custom_seed_input = TextInput(
            text=self.user.seed, hint_text="Enter custom seed", multiline=False, size_hint=(1, 0.1)
        )
        wallet_content.add_widget(self.custom_address_input)
        wallet_content.add_widget(self.custom_seed_input)

        # Buttons for wallet actions
        wallet_buttons = BoxLayout(orientation='horizontal', size_hint=(1, 0.2))
        create_wallet_button = Button(text="Create New Wallet", size_hint=(0.5, 1))
        create_wallet_button.bind(on_press=self.create_new_wallet)
        wallet_buttons.add_widget(create_wallet_button)

        save_button = Button(text="Save Changes", size_hint=(0.5, 1))
        save_button.bind(on_press=self.save_custom_wallet)
        wallet_buttons.add_widget(save_button)

        wallet_content.add_widget(wallet_buttons)
        wallet_tab.add_widget(wallet_content)

        # User Data Tab
        user_tab = TabbedPanelItem(text="User Data")
        user_content = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Input fields for username and email
        self.username_input = TextInput(
            text=self.user.username, hint_text="Enter username", multiline=False, size_hint=(1, 0.1)
        )
        self.email_input = TextInput(
            text=self.user.email, hint_text="Enter email", multiline=False, size_hint=(1, 0.1)
        )
        user_content.add_widget(self.username_input)
        user_content.add_widget(self.email_input)

        # Buttons for saving user data
        user_buttons = BoxLayout(orientation='horizontal', size_hint=(1, 0.2))
        save_user_button = Button(text="Save User Data", size_hint=(1, 1))
        save_user_button.bind(on_press=self.save_user_data)
        user_buttons.add_widget(save_user_button)

        user_content.add_widget(user_buttons)
        user_tab.add_widget(user_content)

        # Add tabs to the TabbedPanel
        tab_panel.add_widget(wallet_tab)
        tab_panel.add_widget(user_tab)

        # Popup for settings
        
        settings_popup = Popup(title="Settings", content=tab_panel, size_hint=(0.8, 0.8))
        settings_popup.open()

        

    def refresh_balance(self, _):
        if not self.user:
            return
        try:
            client = JsonRpcClient(XRP_RPC_URL)
            request = AccountInfo(
                account=self.user.wallet,
                ledger_index="validated",
                strict=True
            )
            response = client.request(request).result
            if "account_data" in response:
                balance_drops = int(response["account_data"]["Balance"])
                balance_xrp = balance_drops / 1_000_000
                self.user.balance = balance_xrp
                self.balance_label.text = f"Balance: {balance_xrp:.6f} XRP"
            else:
                self.balance_label.text = "Balance: Not available"
        except Exception as e:
            self.balance_label.text = f"Error: {str(e)}"
