from .util import timestamp, hash_dict

class Block:
    def __init__(self, index, transactions, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp()
        self.previous_hash = previous_hash
        self.nonce = nonce

    def compute_hash(self):
        return hash_dict(self.__dict__)