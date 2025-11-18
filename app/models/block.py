from .util import timestamp, hash_dict

class Block:
    def __init__(self, index, transactions, previous_hash, nonce=0):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp()
        self.previous_hash = previous_hash
        self.nonce = nonce

    def compute_hash(self):
        # Ensure transactions are JSON-serializable (convert Transaction objects to dicts)
        serialized_transactions = []
        for tx in self.transactions:
            if hasattr(tx, 'to_dict') and callable(tx.to_dict):
                serialized_transactions.append(tx.to_dict())
            else:
                serialized_transactions.append(tx)

        block_dict = {
            'index': self.index,
            'transactions': serialized_transactions,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }

        return hash_dict(block_dict)