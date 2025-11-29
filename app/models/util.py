from .hash_functions import sha256 as custom_sha256
import json
import base64
import time 
import ecdsa

def timestamp() -> int:
    return int(time.time())

def to_json(obj) -> str:
    return json.dumps(obj, indent=4, sort_keys=True)

def sha256(data: bytes) -> bytes:
    '''
    Deterministic SHA256 hash from bytes using custom implementation
    returns hash in bytes
    '''
    return custom_sha256(data)

def hash_dict(data: dict) -> str:
    '''
    Use sha256 hash for a dictionary
    returns hash in hex string
    '''
    encoded = json.dumps(data, sort_keys=True).encode()
    return custom_sha256(encoded).hex()

def b64encode(byte_string: bytes) -> str:
    return base64.b64encode(byte_string).decode()

def b64decode(string: str) -> bytes:
    return base64.b64decode(string)