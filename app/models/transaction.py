import ecdsa
import hashlib
import json
from .util import hash_dict, b64decode, sha256

class Transaction:
    def __init__(self, sender_address, sender_pubkey, receiver_address, amount, signature=None):
        self.sender_address = sender_address
        self.sender_pubkey = sender_pubkey
        self.receiver_address = receiver_address
        self.amount = amount
        self.signature = signature

    def to_dict(self):
        return {
            "sender_address": self.sender_address,
            "sender_pubkey": self.sender_pubkey,
            "receiver_address": self.receiver_address,
            "amount": self.amount,
            "signature": self.signature
        }
    
    def to_hash(self):
        # Build a deterministic byte representation for signing/verifying
        transaction_copy = {
            "sender_address": self.sender_address,
            "sender_pubkey": self.sender_pubkey,
            "receiver_address": self.receiver_address,
            "amount": self.amount
        }
        encoded = json.dumps(transaction_copy, sort_keys=True).encode()
        return sha256(encoded)
    
    def sign(self, private_wallet):
        message = self.to_hash()
        self.signature = private_wallet.sign(message)
        return self.signature

    def verify_signature(self) -> bool:
        try:
            # sender_pubkey is expected to be a base64-encoded public key string
            pubkey_bytes = b64decode(self.sender_pubkey)
            pubkey = ecdsa.VerifyingKey.from_string(pubkey_bytes, curve=ecdsa.SECP256k1)

            # Recompute address from provided public key and compare
            sha = sha256(pubkey_bytes)
            ripemd = hashlib.new('ripemd160', sha).digest()
            if ripemd.hex() != self.sender_address:
                return False

            signature = b64decode(self.signature)
            pubkey.verify(signature, self.to_hash())
            return True
        except Exception:
            return False

    @classmethod
    def from_dict(cls, data: dict):
        """Create a Transaction from a dict/JSON payload.

        Expected keys: sender_address, sender_pubkey, receiver_address, amount
        Optional: signature
        """
        if not isinstance(data, dict):
            raise ValueError("data must be a dict")

        required = ("sender_address", "sender_pubkey", "receiver_address", "amount")
        for key in required:
            if key not in data:
                raise ValueError(f"missing required transaction field: {key}")

        return cls(
            sender_address=data["sender_address"],
            sender_pubkey=data["sender_pubkey"],
            receiver_address=data["receiver_address"],
            amount=data["amount"],
            signature=data.get("signature")
        )