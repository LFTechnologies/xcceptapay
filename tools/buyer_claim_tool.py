#!/usr/bin/env python3
import argparse
import json
import os
import sys
from datetime import datetime

from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import PaymentChannelCreate, PaymentChannelFund
from xrpl.transaction import autofill, sign, submit_and_wait
from xrpl.core.binarycodec import encode_for_signing_claim
from xrpl.core.keypairs import sign as xrpl_sign
from xrpl.utils import xrp_to_drops
from xrpl.models.requests.account_channels import AccountChannels

try:
    from xrpl.wallet import generate_faucet_wallet  # faucet helper (testnet)
except Exception:
    generate_faucet_wallet = None

DEFAULT_RPC = os.environ.get("RPC_URL", "https://s.altnet.rippletest.net:51234")

def eprint(*a, **k): print(*a, **k, file=sys.stderr)

def load_wallet_from_env(prefix="BUYER"):
    seed = os.environ.get(f"{prefix}_SEED")
    if not seed:
        raise SystemExit(f"Env var {prefix}_SEED not set. Set it or use --use-faucet.")
    return Wallet(seed)

def faucet_wallet(client: JsonRpcClient):
    if generate_faucet_wallet is None:
        raise SystemExit("Upgrade xrpl-py or fund a wallet manually: faucet helper missing.")
    w = generate_faucet_wallet(client, debug=True)
    eprint(f"[faucet] Address: {w.classic_address}")
    eprint(f"[faucet] Seed:    {w.seed}")
    return w

def submit_tx(client: JsonRpcClient, wallet: Wallet, tx):
    filled = autofill(tx, client)
    signed = sign(filled, wallet)
    result = submit_and_wait(signed, client)
    return result.result

from typing import Optional

def extract_channel_id_from_meta(tx_result: dict) -> Optional[str]:
    meta = tx_result.get("meta") or tx_result.get("meta_json")
    if not meta:
        return None
    nodes = meta.get("AffectedNodes") or []
    for node in nodes:
        created = node.get("CreatedNode")
        if not created:
            continue
        if created.get("LedgerEntryType") == "PayChannel":
            # Primary: CreatedNode.LedgerIndex (channel id)
            cid = created.get("LedgerIndex")
            if cid:
                return cid
            # Rare: NewFields.Channel
            nf = created.get("NewFields") or {}
            if "Channel" in nf:
                return nf["Channel"]
    return None

def lookup_channel_via_api(client: JsonRpcClient, source: str, destination: str):
    """Fallback using account_channels to find recent channel id."""
    req = AccountChannels(account=source, destination_account=destination)
    resp = client.request(req)
    channels = (resp.result or {}).get("channels") or []
    # Choose the most recently created (last in list)
    if not channels:
        return None
    # Prefer one with nonzero "settle_delay" and matching destination
    for ch in reversed(channels):
        if ch.get("destination_account") == destination:
            return ch.get("channel_id")
    # Fallback last entry
    return channels[-1].get("channel_id")

def open_channel(client: JsonRpcClient, buyer_wallet: Wallet, destination: str, dest_tag: int, amount_xrp: float, settle_delay_s: int = 600):
    amount_drops = str(xrp_to_drops(amount_xrp))
    tx = PaymentChannelCreate(
        account=buyer_wallet.classic_address,
        destination=destination,
        amount=amount_drops,
        settle_delay=settle_delay_s,
        public_key=buyer_wallet.public_key,
        destination_tag=int(dest_tag),
    )
    eprint("[open] Submitting PaymentChannelCreate...")
    result = submit_tx(client, buyer_wallet, tx)

    # Try meta extraction
    channel_id = extract_channel_id_from_meta(result)
    if not channel_id:
        # Fallback: ask the ledger for channels between these accounts
        eprint("[open] Could not parse channel id from meta; falling back to account_channels...")
        channel_id = lookup_channel_via_api(client, buyer_wallet.classic_address, destination)

    if not channel_id:
        raise RuntimeError("Could not determine channel_id from transaction or ledger.")

    eprint(f"[open] Channel created: {channel_id}")
    return result, channel_id

def make_claim_json(channel_id: str, cumulative_xrp: float, buyer_wallet: Wallet, outfile: str = None):
    amount_drops = str(xrp_to_drops(cumulative_xrp))
    try:
        msg = encode_for_signing_claim(channel_id, amount_drops)
    except TypeError:
        msg = encode_for_signing_claim({"channel": channel_id, "amount": amount_drops})
    signature = xrpl_sign(msg, buyer_wallet.private_key)
    claim = {
        "channel_id": channel_id,
        "amount_drops": amount_drops,
        "signature": signature,
        "pubkey": buyer_wallet.public_key,
        "key_type": "ed25519",
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
    j = json.dumps(claim, indent=2)
    print(j)
    if outfile:
        with open(outfile, "w", encoding="utf-8") as f:
            f.write(j + "\n")
        eprint(f"[claim] Wrote {outfile}")
    return claim

def fund_channel(client: JsonRpcClient, buyer_wallet: Wallet, channel_id: str, add_xrp: float):
    amount_drops = str(xrp_to_drops(add_xrp))
    tx = PaymentChannelFund(
        account=buyer_wallet.classic_address,
        channel=channel_id,
        amount=amount_drops,
    )
    eprint(f"[fund] Adding {amount_drops} drops to {channel_id}...")
    result = submit_tx(client, buyer_wallet, tx)
    eprint("[fund] Success")
    return result

def main():
    ap = argparse.ArgumentParser(description="Buyer-side tool: open XRPL Payment Channel and emit claims (Testnet).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_open = sub.add_parser("open-channel", help="Open a new Payment Channel (buyer -> merchant).")
    ap_open.add_argument("--destination", required=True)
    ap_open.add_argument("--dest-tag", type=int, required=True)
    ap_open.add_argument("--amount-xrp", type=float, required=True)
    ap_open.add_argument("--use-faucet", action="store_true")
    ap_open.add_argument("--seed", help="Buyer seed if not using faucet or BUYER_SEED env.")
    ap_open.add_argument("--rpc", default=DEFAULT_RPC)
    ap_open.add_argument("--out", default="open_channel_result.json")

    ap_claim = sub.add_parser("make-claim", help="Create a cumulative claim JSON for an existing channel.")
    ap_claim.add_argument("--channel-id", required=True)
    ap_claim.add_argument("--cum-xrp", type=float, required=True)
    ap_claim.add_argument("--seed", help="Buyer seed if not using BUYER_SEED env.")
    ap_claim.add_argument("--rpc", default=DEFAULT_RPC)
    ap_claim.add_argument("--out", default="claim.json")

    ap_open_claim = sub.add_parser("open-and-claim", help="Open then emit a claim.")
    ap_open_claim.add_argument("--destination", required=True)
    ap_open_claim.add_argument("--dest-tag", type=int, required=True)
    ap_open_claim.add_argument("--amount-xrp", type=float, required=True)
    ap_open_claim.add_argument("--cum-xrp", type=float, required=True)
    ap_open_claim.add_argument("--use-faucet", action="store_true")
    ap_open_claim.add_argument("--seed")
    ap_open_claim.add_argument("--rpc", default=DEFAULT_RPC)
    ap_open_claim.add_argument("--out-open", default="open_channel_result.json")
    ap_open_claim.add_argument("--out-claim", default="claim.json")

    args = ap.parse_args()
    client = JsonRpcClient(args.rpc)

    if getattr(args, "use_faucet", False):
        buyer_wallet = faucet_wallet(client)
    elif getattr(args, "seed", None):
        buyer_wallet = Wallet.from_seed(args.seed)
    else:
        buyer_wallet = load_wallet_from_env("BUYER")

    if args.cmd == "open-channel":
        res, chan = open_channel(client, buyer_wallet, args.destination, args.dest_tag, args.amount_xrp)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2)
        print(json.dumps({"channel_id": chan, "result_file": args.out, "buyer_address": buyer_wallet.classic_address}, indent=2))
        return

    if args.cmd == "make-claim":
        make_claim_json(args.channel_id, args.cum_xrp, buyer_wallet, outfile=args.out)
        return

    if args.cmd == "open-and-claim":
        res, chan = open_channel(client, buyer_wallet, args.destination, args.dest_tag, args.amount_xrp)
        with open(args.out_open, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2)
        make_claim_json(chan, args.cum_xrp, buyer_wallet, outfile=args.out_claim)
        return

if __name__ == "__main__":
    main()
