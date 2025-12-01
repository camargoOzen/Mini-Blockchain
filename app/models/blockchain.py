from .block import Block
from .transaction import Transaction
from .util import timestamp
import time

class Blockchain:

    BASE_DIFFICULTY = 3
    DIFFICULTY_INCREMENT_INTERVAL = 1000  # Increase difficulty every 1000 blocks

    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []
        # Try to load existing blockchain, otherwise create genesis
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, [], "0", difficulty=self.BASE_DIFFICULTY, mining_time=0)
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]
    
    def get_difficulty(self):
        """Calculate current difficulty based on blockchain length"""
        total_blocks = len(self.chain)
        return self.BASE_DIFFICULTY + (total_blocks // self.DIFFICULTY_INCREMENT_INTERVAL)
    
    def blocks_until_next_difficulty(self):
        """Calculate how many blocks until next difficulty increase"""
        total_blocks = len(self.chain)
        return self.DIFFICULTY_INCREMENT_INTERVAL - (total_blocks % self.DIFFICULTY_INCREMENT_INTERVAL)
    
    @staticmethod
    def is_valid_proof(block, block_hash, difficulty):
        return (block_hash.startswith('0' * difficulty) and block_hash == block.compute_hash())
    
    @staticmethod
    def valid_block(block, block_hash):
        return (block_hash == block.compute_hash())
    
    def load_from_dict(self, data: dict):
        # Expect a dict with a 'chain' key containing a list of block dicts
        if not isinstance(data, dict):
            raise ValueError("data must be a dict")

        if 'chain' not in data:
            raise ValueError("data must contain a 'chain' list")

        new_chain = []
        for block_data in data['chain']:
            # Reconstruct Block from dict (transactions may be dicts)
            block = Block.from_dict(block_data)
            new_chain.append(block)

        # Replace local chain only after successful reconstruction
        self.chain = new_chain
    
    def to_dict(self):
        return {
            "chain": [block.to_dict() for block in self.chain]
        }
    
    def add_block(self, block, proof):
        previous_hash = self.last_block.hash

        if previous_hash != block.previous_hash:
            return False
        
        if not Blockchain.is_valid_proof(block, proof, block.difficulty):
            return False
        
        block.hash = proof
        self.chain.append(block)
        return True
    
    def proof_of_work(self, block):
        """Perform proof of work and track mining time"""
        block.nonce = 0
        difficulty = block.difficulty
        
        start_time = time.time()
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()
        end_time = time.time()
        
        # Store mining time in seconds (rounded to 2 decimals)
        block.mining_time = round(end_time - start_time, 2)
        
        return computed_hash

    def add_new_transaction(self, transaction: dict):
        """Accept either a Transaction instance or a dict (JSON) representing a transaction.

        If a dict is provided, convert it to a Transaction with `Transaction.from_dict`.
        The method verifies the signature before adding to unconfirmed transactions.
        Supports coinbase/faucet transactions (no sender) which skip signature verification.
        Returns True on success, False on invalid input or failed verification.
        """
        # Check if this is a coinbase/faucet transaction (no sender)
        if isinstance(transaction, dict):
            sender = transaction.get("sender_address")
            if sender is None or sender == "COINBASE" or sender == "FAUCET":
                # For coinbase transactions, just add directly
                self.unconfirmed_transactions.append(transaction)
                return True
            
            # Convert dict payloads to Transaction objects
            try:
                veryfy_tx = Transaction.from_dict(transaction)
            except Exception:
                return False
        else:
            veryfy_tx = transaction

        # Must be a Transaction now
        if not isinstance(veryfy_tx, Transaction):
            return False

        # Require a signature and valid verification
        if not veryfy_tx.signature:
            return False

        if not veryfy_tx.verify_signature():
            return False

        self.unconfirmed_transactions.append(transaction)
        return True

    def mine(self, miner_address=None, mining_reward=50):
        """Mine pending transactions into a new block.
        
        Args:
            miner_address: Address to receive mining reward (optional)
            mining_reward: Amount of coins to reward the miner (default 50)
        
        Returns:
            dict with block index and mining time, or False if mining failed
        """
        if not self.unconfirmed_transactions and not miner_address:
            return False
        
        # Create coinbase transaction for mining reward
        if miner_address:
            coinbase_transaction = {
                "sender_address": "COINBASE",
                "sender_pubkey": None,
                "receiver_address": miner_address,
                "amount": mining_reward,
                "signature": None
            }
            # Prepend coinbase transaction to the list
            transactions_to_mine = [coinbase_transaction] + self.unconfirmed_transactions
        else:
            transactions_to_mine = self.unconfirmed_transactions
        
        last_block = self.last_block
        current_difficulty = self.get_difficulty()

        new_block = Block(index=last_block.index+1,
                                transactions=transactions_to_mine,
                                previous_hash=last_block.hash,
                                difficulty=current_difficulty)
        
        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)
        self.unconfirmed_transactions = []
    
        return {
            'index': new_block.index,
            'mining_time': new_block.mining_time,
            'difficulty': new_block.difficulty
        }