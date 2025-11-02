import json
from xrpl.core.binarycodec import encode_for_signing_claim
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

def test_local_verify_roundtrip():
    sk = Ed25519PrivateKey.generate()
    pk = sk.public_key()
    ch = "A"*64
    amt = "2500000"
    msg_hex = encode_for_signing_claim({"channel": ch, "amount": amt})
    sig = sk.sign(bytes.fromhex(msg_hex)).hex().upper()
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    Ed25519PublicKey.from_public_bytes(pk.public_bytes()).verify(bytes.fromhex(sig), bytes.fromhex(msg_hex))
