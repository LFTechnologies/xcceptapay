
from __future__ import annotations

import os, json, time, threading, asyncio
from typing import Optional

# --- Third-party (optional) ---
try:
    from bleak import BleakClient, BleakScanner  # BLE helper
except Exception:
    BleakClient = None
    BleakScanner = None

import requests

# xrpl-py imports (supporting multiple versions)
from xrpl.clients import JsonRpcClient
from xrpl.core.binarycodec import encode_for_signing_claim as _enc_new
try:
    # older path fallback
    from xrpl.core.binarycodec.main import encode_for_signing_claim as _enc_old  # type: ignore
except Exception:
    _enc_old = None

try:
    # preferred verify if available
    from xrpl.core.keypairs import verify as xrpl_verify
except Exception:
    try:
        from xrpl.core.keypairs.main import verify as xrpl_verify  # type: ignore
    except Exception:
        xrpl_verify = None

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from binascii import unhexlify

# --- Kivy ---
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock

# ==============================
# CONFIG / CONSTANTS
# ==============================
API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:3000").rstrip("/")
DEFAULT_USE_API = os.environ.get("USE_API", "true").lower() in ("1", "true", "yes")
XRP_RPC_HTTP = os.environ.get("XRP_RPC_HTTP", "https://s.altnet.rippletest.net:51234")

# Device-side exposure cap used for local checks (drops)
EXPOSURE_CAP_DROPS = int(os.environ.get("EXPOSURE_CAP_DROPS", "3000000"))

# Optional BLE UUIDs (must match ESP32 sketch if you use BLE vend)
SERVICE_UUID           = "12345678-1234-5678-1234-56789abcdef0"
CHARACTERISTIC_TX_UUID = "12345678-1234-5678-1234-56789abcdef0"  # READ/NOTIFY
CHARACTERISTIC_RX_UUID = "12345678-1234-5678-1234-56789abcdef1"  # WRITE
TARGET_NAME_HINT       = "ESP32_BLE_SERVER"

# ==============================
# Helpers: kv store (JSON file)
# ==============================
_KV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kv.json")

def _kv_load():
    try:
        if os.path.exists(_KV_PATH):
            with open(_KV_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print("KV load error:", e)
    return {}

def kv_get(key, default=None):
    return _kv_load().get(key, default)

def kv_set(key, value):
    d = _kv_load()
    d[key] = value
    try:
        with open(_KV_PATH, "w", encoding="utf-8") as f:
            json.dump(d, f)
    except Exception as e:
        print("KV save error:", e)

# ==============================
# XRPL claim verification utils
# ==============================
def encode_for_signing_claim(channel_id: str, amount_drops: str | int) -> bytes:
    amt = str(int(str(amount_drops).strip()))  # normalize & strip leading zeros
    try:
        res = _enc_new(channel=channel_id, amount=amt)
    except TypeError:
        if _enc_old is None:
            raise
        res = _enc_old({"channel": channel_id, "amount": amt})
    if isinstance(res, str):
        return bytes.fromhex(res)
    return bytes(res)

def _ed25519_verify_raw(msg: bytes, sig_hex: str, pub_hex: str) -> bool:
    sig = unhexlify(str(sig_hex).strip())
    pub = unhexlify(str(pub_hex).strip())
    if len(pub) == 33 and pub[0] == 0xED:  # XRPL ed25519 prefix
        pub = pub[1:]
    try:
        Ed25519PublicKey.from_public_bytes(pub).verify(sig, msg)
        return True
    except Exception:
        return False

def verify_claim(channel_id: str, amount_drops: str, signature_hex: str, pubkey_hex: str) -> bool:
    msg = encode_for_signing_claim(channel_id, amount_drops)
    # Prefer xrpl's verify if available
    if xrpl_verify is not None:
        try:
            return bool(xrpl_verify(message=msg, signature=signature_hex, public_key=pubkey_hex))
        except TypeError:
            try:
                return bool(xrpl_verify(msg, signature_hex, pubkey_hex))
            except Exception:
                pass
        except Exception:
            pass
    # Fallback ed25519
    if pubkey_hex.upper().startswith("ED"):
        return _ed25519_verify_raw(msg, signature_hex, pubkey_hex)
    return False

def fetch_channel_pubkey(channel_id: str) -> Optional[str]:
    """Online: fetch PayChannel's PublicKey (uppercase hex) from Testnet."""
    try:
        client = JsonRpcClient(XRP_RPC_HTTP)
        req = {"method": "ledger_entry", "params": [{"index": channel_id, "ledger_index": "validated"}]}
        res = client._request_impl(req)  # low-level to avoid version drift
        pk = (res or {}).get("result", {}).get("node", {}).get("PublicKey")
        return pk.upper() if isinstance(pk, str) and pk else None
    except Exception:
        return None

# ==============================
# BLE helper (optional)
# ==============================
class _AsyncLoopThread:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.t = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.t.start()
    def call(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

class BleVendClient:
    def __init__(self, on_notify=None, log_fn=None):
        self._thr = _AsyncLoopThread()
        self._client = None
        self._connected = False
        self._on_notify = on_notify or (lambda msg: None)
        self._log = log_fn or (lambda msg: None)

    def connect(self, target_name=TARGET_NAME_HINT, service_uuid=SERVICE_UUID, timeout=10.0):
        return self._thr.call(self._connect_async(target_name, service_uuid, timeout))

    async def _connect_async(self, target_name, service_uuid, timeout):
        if BleakScanner is None:
            self._log("BLE unavailable (bleak not installed).")
            return False

        self._log(f"[BLE] scanning up to {timeout}s…")
        deadline = time.time() + timeout
        target = None
        while time.time() < deadline and target is None:
            devices = await BleakScanner.discover(timeout=2.0)
            for d in devices:
                if d.name == target_name:
                    target = d
                    break
        if target is None:
            self._log("[BLE] device not found.")
            return False

        self._log(f"[BLE] connecting to {target.address} ({target.name})…")
        self._client = BleakClient(target.address, timeout=15.0)
        await self._client.connect()
        try:
            ic = getattr(self._client, "is_connected", None)
            self._connected = await ic() if callable(ic) else bool(ic)
        except Exception:
            self._connected = True

        await self._client.get_services()
        try:
            await self._client.start_notify(CHARACTERISTIC_TX_UUID, self._notify_cb)
        except Exception:
            pass

        self._log("[BLE] connected.")
        return True

    async def _write_json(self, obj):
        if not self._client or not self._connected:
            self._log("[BLE] not connected.")
            return False
        try:
            raw = json.dumps(obj, separators=(",", ":"))
            await self._client.write_gatt_char(CHARACTERISTIC_RX_UUID, raw.encode("utf-8"), response=True)
            self._log(f"[BLE] → {raw}")
            return True
        except Exception as e:
            self._log(f"[BLE] write error: {e}")
            return False

    def _notify_cb(self, handle, data: bytearray):
        try:
            msg = data.decode("utf-8", errors="ignore")
        except Exception:
            msg = repr(data)
        Clock.schedule_once(lambda dt: self._on_notify(msg))

    def send_vend(self, *, channel_id, amount_drops, slot=1, pulse_ms=600, device_id="dev-kiosk"):
        payload = {
            "action": "vend",
            "slot": int(slot),
            "pulse_ms": int(pulse_ms),
            "claim_channel": str(channel_id),
            "claim_amount_drops": str(amount_drops),
            "device_id": str(device_id),
        }
        return self._thr.call(self._write_json(payload))

# ==============================
# Main Screen
# ==============================
class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "main"
        self.use_api = DEFAULT_USE_API

        root = BoxLayout(orientation="vertical", spacing=6, padding=6)

        # Status
        self.label = Label(text="Ready.", size_hint=(1, 0.11))
        root.add_widget(self.label)

        # Admin: API base & toggle
        admin_row1 = BoxLayout(size_hint=(1, 0.08), spacing=6)
        self.api_url_input = TextInput(text=API_BASE_URL, hint_text="API Base URL", multiline=False)
        self.btn_api_toggle = Button(text=("API: ON" if self.use_api else "API: OFF"), size_hint=(None,1), width=110)
        self.btn_api_toggle.bind(on_press=lambda *_: self._toggle_api())
        admin_row1.add_widget(self.api_url_input)
        admin_row1.add_widget(self.btn_api_toggle)
        root.add_widget(admin_row1)

        # Device config (used by register + queue payload)
        admin_row_device = BoxLayout(size_hint=(1, 0.08), spacing=6)
        self.device_id_input = TextInput(text="dev-kiosk", hint_text="device_id", multiline=False)
        self.exp_cap_input  = TextInput(text=str(EXPOSURE_CAP_DROPS), hint_text="Exposure cap (drops)", multiline=False)
        admin_row_device.add_widget(self.device_id_input)
        admin_row_device.add_widget(self.exp_cap_input)
        root.add_widget(admin_row_device)

        # Admin buttons
        admin_row2 = BoxLayout(size_hint=(1, 0.09), spacing=6)
        b_health   = Button(text="Health")
        b_register = Button(text="Register Device/Cap")
        b_receipts = Button(text="View Receipts")
        b_settle   = Button(text="Settle Now")
        b_health.bind(on_press=self.ui_admin_health)
        b_register.bind(on_press=self.ui_admin_register_device)
        b_receipts.bind(on_press=self.ui_view_receipts)
        b_settle.bind(on_press=self.ui_settle_now)
        for b in (b_health, b_register, b_receipts, b_settle):
            admin_row2.add_widget(b)
        root.add_widget(admin_row2)

        # Claim JSON input
        root.add_widget(Label(text="Paste Claim JSON:", size_hint=(1, 0.06)))
        self.claim_json_input = TextInput(
            hint_text='{"channel_id":"...","amount_drops":"...","signature":"...","pubkey":"..."}',
            multiline=True, size_hint=(1, 0.24)
        )
        root.add_widget(self.claim_json_input)

        claim_row = BoxLayout(size_hint=(1, 0.09), spacing=6)
        b_load   = Button(text="Load Claim JSON")
        b_verify = Button(text="Verify + Queue")
        b_load.bind(on_press=self.load_claim_from_json)
        b_verify.bind(on_press=self.ui_verify_and_queue)
        claim_row.add_widget(b_load)
        claim_row.add_widget(b_verify)
        root.add_widget(claim_row)

        # Optional BLE connect
        self.ble = BleVendClient(
            on_notify=lambda msg: setattr(self.label, "text", f"ESP32: {msg}"),
            log_fn=lambda s: setattr(self.label, "text", s),
        )
        b_ble = Button(text="Connect BLE (optional)", size_hint=(1, 0.08))
        b_ble.bind(on_press=lambda *_: self.ble.connect())
        root.add_widget(b_ble)

        self.add_widget(root)

        # locals
        self._last_claim: Optional[dict] = None

    # ----------- Admin helpers -----------
    def _api_base(self) -> str:
        raw = (self.api_url_input.text or "").strip()
        if not raw:
            return ""
        if raw.startswith("//"):
            raw = "http:" + raw
        if not raw.startswith("http://") and not raw.startswith("https://"):
            raw = "http://" + raw
        return raw.rstrip("/")

    def _toggle_api(self):
        self.use_api = not self.use_api
        self.btn_api_toggle.text = "API: ON" if self.use_api else "API: OFF"
        self.label.text = f"API {'enabled' if self.use_api else 'disabled'}."

    def ui_admin_health(self, *_):
        if not self.use_api:
            self.label.text = "API disabled."
            return
        try:
            r = requests.get(f"{self._api_base()}/health", timeout=4)
            self.label.text = (r.text[:200] + "…") if len(r.text) > 200 else r.text
        except Exception as e:
            self.label.text = f"Health error: {e}"

    def ui_admin_register_device(self, *_):
        if not self.use_api:
            self.label.text = "API disabled."
            return
        device_id = (self.device_id_input.text or "").strip() or "dev-kiosk"
        try:
            cap = int(self.exp_cap_input.text.strip())
        except Exception:
            self.label.text = "Invalid exposure cap."
            return
        try:
            r = requests.post(f"{self._api_base()}/devices/register",
                              json={"device_id": device_id, "exposure_cap_drops": cap},
                              timeout=5)
            self.label.text = "Registered." if r.ok else f"Register failed: {r.status_code}"
        except Exception as e:
            self.label.text = f"Register error: {e}"

    def ui_view_receipts(self, *_):
        if not self.use_api:
            self.label.text = "API disabled."
            return
        try:
            r = requests.get(f"{self._api_base()}/receipts", timeout=6)
            if not r.ok:
                self.label.text = f"Receipts failed: HTTP {r.status_code}"
                return
            items = r.json() or []
            if not items:
                self.label.text = "No receipts."
                return
            last = items[-1]
            ch  = last.get("channel_id","?")[-12:]
            amt = int(last.get("amount_drops",0))/1_000_000
            tx  = last.get("tx_hash","?")[:12]
            when= last.get("settledAt","")
            self.label.text = f"Last receipt: {amt:.6f} XRP\nch…{ch}\ntx…{tx}\n@{when}"
        except Exception as e:
            self.label.text = f"Receipts error: {e}"

    def ui_settle_now(self, *_):
        if not self.use_api:
            self.label.text = "API disabled."
            return
        try:
            r = requests.post(f"{self._api_base()}/claims/settle", json={}, timeout=10)
            data = r.json() if r.headers.get("content-type","").startswith("application/json") else {}
            if r.ok and data.get("ok"):
                self.label.text = f"Settled. tx: {data.get('tx_hash','?')}"
            else:
                self.label.text = f"Settle failed: {r.status_code} {data}"
        except Exception as e:
            self.label.text = f"Settle error: {e}"

    # ----------- Claim JSON flow -----------
    def load_claim_from_json(self, *_):
        try:
            raw = (self.claim_json_input.text or "").strip()
            if not raw:
                self.label.text = "Paste a claim JSON first."
                return
            claim = json.loads(raw)
            req = ["channel_id", "amount_drops", "signature"]
            miss = [k for k in req if not str(claim.get(k,"")).strip()]
            if miss:
                self.label.text = f"Missing: {', '.join(miss)}"
                return
            self._last_claim = claim
            self.label.text = "Claim loaded."
        except Exception as e:
            self.label.text = f"Bad JSON: {e}"

    def _device_may_dispense(self, channel_id: str, amount_drops: int):
        last = int(kv_get(f"last_seen:{channel_id}", 0) or 0)
        settled = int(kv_get(f"settled:{channel_id}", 0) or 0)
        if amount_drops <= last:
            return False, "stale_or_lower_amount"
        if (amount_drops - settled) > int(EXPOSURE_CAP_DROPS):
            return False, "exposure_cap_exceeded"
        return True, ""

    def _local_sig_check(self, claim: dict) -> bool:
        ch  = str(claim.get("channel_id","")).strip()
        amt = str(claim.get("amount_drops","")).strip()
        sig = str(claim.get("signature","")).strip()
        pk  = str(claim.get("pubkey","")).strip()
        if pk:
            return verify_claim(ch, amt, sig, pk)
        # Try to fetch channel.pubkey if not present
        onchain_pk = fetch_channel_pubkey(ch)
        if not onchain_pk:
            return False
        claim["pubkey"] = onchain_pk
        return verify_claim(ch, amt, sig, onchain_pk)

    def ui_verify_and_queue(self, *_):
        claim = self._last_claim
        if not claim:
            self.load_claim_from_json()
            claim = self._last_claim
            if not claim:
                return

        # Parse & validate
        ch  = str(claim.get("channel_id","")).strip()
        amt = str(claim.get("amount_drops","")).strip()
        sig = str(claim.get("signature","")).strip()
        if not (ch and amt and sig):
            self.label.text = "Claim missing required fields."
            return
        try:
            amt_i = int(amt)
            if amt_i <= 0:
                raise ValueError
        except Exception:
            self.label.text = "amount_drops must be positive integer string."
            return

        # Local signature verification (no server dependency)
        try:
            if not self._local_sig_check(claim):
                self.label.text = "Verify failed (signature/amount/pubkey)."
                return
        except Exception as e:
            self.label.text = f"Verify error: {type(e).__name__}"
            return

        # Device-side exposure/monotonic
        ok, reason = self._device_may_dispense(ch, amt_i)
        if not ok:
            self.label.text = f"Declined: {reason}"
            return

        # Persist last_seen, update UI
        kv_set(f"last_seen:{ch}", amt_i)
        base_msg = "Approved (Offline). Product may dispense."
        self.label.text = base_msg

        # Kick BLE vend (optional)
        try:
            if self.ble:
                self.ble.send_vend(channel_id=ch, amount_drops=str(amt_i), slot=1, pulse_ms=600,
                                   device_id=(self.device_id_input.text or "dev-kiosk").strip())
        except Exception:
            pass

        # Queue to API (optional)
        if self.use_api and self._api_base():
            try:
                payload = dict(claim)
                payload["device_id"] = (self.device_id_input.text or "dev-kiosk").strip()
                r = requests.post(f"{self._api_base()}/claims/queue", json=payload, timeout=6)
                if r.ok and (r.json().get("accepted") is True):
                    self.label.text = base_msg + "\nQueued for settlement."
                else:
                    self.label.text = base_msg + "\nQueue failed."
            except Exception:
                self.label.text = base_msg + "\nAPI offline (skipped)."
        else:
            self.label.text = base_msg + "\n(API off)"
