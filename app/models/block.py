from .util import timestamp, hash_dict

class Block:
    def __init__(self, index, transactions, previous_hash, nonce=0, mining_time=None, difficulty=None):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp()
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.mining_time = mining_time  # Time in seconds to mine this block
        self.difficulty = difficulty  # Difficulty level when block was mined

    def compute_hash(self):
        # Only hash the core block data, not mining_time or difficulty
        hash_data = {
            'index': self.index,
            'transactions': self.transactions,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }
        return hash_dict(hash_data)
    
    def to_dict(self):
        """Convert block to dictionary for JSON serialization"""
        return {
            'index': self.index,
            'transactions': self.transactions,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': getattr(self, 'hash', None),
            'mining_time': self.mining_time,
            'difficulty': self.difficulty
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create block from dictionary (deserialization)"""
        block = cls(
            index=data['index'],
            transactions=data['transactions'],
            previous_hash=data['previous_hash'],
            nonce=data['nonce'],
            mining_time=data.get('mining_time'),
            difficulty=data.get('difficulty')
        )
        # Restore original timestamp
        block.timestamp = data['timestamp']
        # Restore hash if present
        if 'hash' in data and data['hash']:
            block.hash = data['hash']
        return block