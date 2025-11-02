#!/usr/bin/env python3
# generate_merchant_wallet.py
# Creates a funded XRPL Testnet wallet via the faucet and writes a .env.real snippet (local only).

import os, json, sys
from xrpl.clients import JsonRpcClient
from xrpl.wallet import generate_faucet_wallet
from xrpl.wallet import Wallet

RPC = os.environ.get("RPC_URL", "https://s.altnet.rippletest.net:51234")
OUT_ENV = os.environ.get("OUT_ENV", ".env.real")  # overwrite locally, do NOT commit

def main():
    client = JsonRpcClient(RPC)
    print("[*] Requesting a funded Testnet wallet from faucet (this contacts the XRPL Testnet faucet)...")
    wallet = generate_faucet_wallet(client, debug=False)
    print()
    print("=== MERCHANT WALLET GENERATED ===")
    print("Classic address:", wallet.classic_address)
    print("Seed (keep secret):", wallet.seed)
    print("Public key:", wallet.public_key)
    print("Private key (wallet.private_key):", getattr(wallet, "private_key", "<n/a>"))
    print()

    # Write a .env.real snippet locally (do NOT commit to git)
    env_lines = [
        "# XRPL Testnet merchant wallet (generated locally). Do NOT commit this file.",
        f"RPC_URL={RPC}",
        f"MERCHANT_SEED={wallet.seed}",
    ]
    with open(OUT_ENV, "w", encoding="utf-8") as f:
        f.write("\n".join(env_lines) + "\n")
    print(f"[+] Wrote local env snippet to {OUT_ENV}")
    print("[!] IMPORTANT: Keep the seed secret. Do not commit the file to source control.")

if __name__ == "__main__":
    main()
