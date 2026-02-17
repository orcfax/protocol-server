"""Ensure signing works as anticipated."""

import binascii
import json

import cbor2
import pytest
import pycardano as pyc

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from main import verify_signature_cbor, verify_signature


@pytest.mark.asyncio
async def test_verify_signature():
    """Ensure verify signature works and is helpful."""

    skey_json = {
        "type": "PaymentSigningKeyShelley_ed25519",
        "description": "PaymentSigningKeyShelley_ed25519",
        "cborHex": "58204a87403c87f01c7104d14965322b49064ad4ff2cd5a38e9c2e341cebe3494eea",
    }
    pkey_json = {
        "type": "PaymentVerificationKeyShelley_ed25519",
        "description": "PaymentVerificationKeyShelley_ed25519",
        "cborHex": "58205a002828b53dd51c3081eb419494a4c47a93a220253cdca1cc39856b6ec5a2c4",
    }
    skey = pyc.PaymentSigningKey.from_json(json.dumps(skey_json))
    payload = {
        "current": 1,
        "average": 10,
        "time": 12345,
    }
    # Ensure JSON-byte data is validated.
    data = json.dumps(payload).encode()
    signed_data = skey.sign(data)
    signature = binascii.hexlify(signed_data).decode()
    res = await verify_signature_cbor(pkey_json["cborHex"], signature, data.decode())

    assert res == {
        "valid": True,
        "signing key": "58205a002828b53dd51c3081eb419494a4c47a93a220253cdca1cc39856b6ec5a2c4",
        "ed25519": "5a002828b53dd51c3081eb419494a4c47a93a220253cdca1cc39856b6ec5a2c4",
        "payload": '{"current": 1, "average": 10, "time": 12345}',
    }
    # Hexlify the JSON.
    data = binascii.hexlify(json.dumps(payload).encode())
    signed_data = skey.sign(data)
    signature = binascii.hexlify(signed_data).decode()
    res = await verify_signature_cbor(pkey_json["cborHex"], signature, data.decode())
    assert res == {
        "valid": True,
        "signing key": "58205a002828b53dd51c3081eb419494a4c47a93a220253cdca1cc39856b6ec5a2c4",
        "ed25519": "5a002828b53dd51c3081eb419494a4c47a93a220253cdca1cc39856b6ec5a2c4",
        "payload": '{"current": 1, "average": 10, "time": 12345}',
    }
    # Ensure we don't get false positives for bad data.
    res = await verify_signature_cbor(pkey_json["cborHex"], signature, "")
    assert res == {
        "valid": False,
    }
    # Invalid signature.
    res = await verify_signature_cbor(pkey_json["cborHex"], "", data.decode())
    assert res == {
        "valid": False,
    }
    # Ensure verification works for the ed25519 signature.
    res = await verify_signature(
        "5a002828b53dd51c3081eb419494a4c47a93a220253cdca1cc39856b6ec5a2c4",
        signature,
        data.decode(),
    )


def test_signing():
    """Understand signature behavior.

    Ensure PyC signs the same ways as the standard ed25519 library.
    """

    skey = "58204a87403c87f01c7104d14965322b49064ad4ff2cd5a38e9c2e341cebe3494eea"
    skey_unhex = binascii.unhexlify(skey)
    skey_cbor = cbor2.loads(skey_unhex)
    ed25519_skey = Ed25519PrivateKey.from_private_bytes(skey_cbor)
    sign_a = ed25519_skey.sign("data".encode())
    skey_pyc = pyc.PaymentSigningKey.from_cbor(skey)
    sign_b = skey_pyc.sign("data".encode())
    assert sign_a == sign_b
