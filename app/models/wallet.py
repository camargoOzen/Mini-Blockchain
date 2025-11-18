import ecdsa
import hashlib
from .util import sha256, b64encode

class Wallet:
    def __init__(self):
        self.private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        self.public_key = self.private_key.get_verifying_key()
    
    @property
    def get_address(self) -> str:
        sha = sha256(self.public_key.to_string())
        ripemd = hashlib.new('ripemd160', sha).digest()
        return ripemd.hex()

    def sign(self, message: bytes) -> str:
        return b64encode(self.private_key.sign(message))
        
if __name__ == "__main__":
    w1 = Wallet()

    print(w1.private_key)
    print(w1.public_key)
    print(w1.get_address())
    message = "Hello World"
    print("Sign:", w1.sign(message.encode()))