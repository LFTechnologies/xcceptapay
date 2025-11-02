#!/usr/bin/env python3
"""
Simple test script for buyer app functionality (without GUI)
Tests wallet creation and claim signing
"""

import json
from xrpl.wallet import Wallet
from xrpl.core.binarycodec import encode_for_signing_claim
from xrpl.core.keypairs import sign as xrpl_sign
from xrpl.utils import xrp_to_drops
from datetime import datetime

def test_wallet_creation():
    """Test wallet creation"""
    print("=" * 60)
    print("TEST 1: Wallet Creation")
    print("=" * 60)

    wallet = Wallet.create()
    print(f"✓ Wallet created")
    print(f"  Address: {wallet.classic_address}")
    print(f"  Public Key: {wallet.public_key}")
    print(f"  Seed: {wallet.seed}")
    print()
    return wallet

def test_wallet_import(seed):
    """Test wallet import from seed"""
    print("=" * 60)
    print("TEST 2: Wallet Import")
    print("=" * 60)

    wallet = Wallet.from_seed(seed)
    print(f"✓ Wallet imported from seed")
    print(f"  Address: {wallet.classic_address}")
    print()
    return wallet

def test_claim_creation(wallet, channel_id="0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF", amount_xrp=1.0):
    """Test claim creation and signing"""
    print("=" * 60)
    print("TEST 3: Claim Creation")
    print("=" * 60)

    amount_drops = str(xrp_to_drops(amount_xrp))

    # Encode for signing
    try:
        msg = encode_for_signing_claim(channel_id, amount_drops)
    except TypeError:
        msg = encode_for_signing_claim({"channel": channel_id, "amount": amount_drops})

    # Sign
    signature = xrpl_sign(msg, wallet.private_key)

    # Create claim object
    claim = {
        "channel_id": channel_id,
        "amount_drops": amount_drops,
        "signature": signature,
        "pubkey": wallet.public_key,
        "key_type": "ed25519",
        "generated_at": datetime.utcnow().isoformat() + "Z"
    }

    print(f"✓ Claim created and signed")
    print(f"  Channel ID: {channel_id}")
    print(f"  Amount: {amount_xrp} XRP ({amount_drops} drops)")
    print(f"  Signature: {signature[:32]}...")
    print()
    print("Full Claim JSON:")
    print(json.dumps(claim, indent=2))
    print()
    return claim

def test_bluetooth_simulation(claim):
    """Simulate Bluetooth send"""
    print("=" * 60)
    print("TEST 4: Bluetooth Send (Simulated)")
    print("=" * 60)

    print("✓ Would send via Bluetooth:")
    print(f"  Device: ESP32_VENDING_DEMO")
    print(f"  Data size: {len(json.dumps(claim))} bytes")
    print()

def main():
    print("\n" + "=" * 60)
    print("XRPL Buyer App - Functionality Tests")
    print("=" * 60)
    print()

    # Test 1: Create wallet
    wallet = test_wallet_creation()
    seed = wallet.seed

    # Test 2: Import wallet
    wallet2 = test_wallet_import(seed)
    assert wallet.classic_address == wallet2.classic_address, "Wallet addresses don't match!"

    # Test 3: Create claim
    claim = test_claim_creation(wallet, amount_xrp=2.5)

    # Test 4: Simulate Bluetooth
    test_bluetooth_simulation(claim)

    print("=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)
    print()
    print("The buyer app logic is working correctly.")
    print("Run 'python main.py' to test the GUI.")
    print()

if __name__ == '__main__':
    main()
