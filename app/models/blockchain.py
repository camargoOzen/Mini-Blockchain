from .block import Block
from .transaction import Transaction
from .util import timestamp

class Blockchain:

    difficlty = 4

    def __init__(self):
        self.unconfirmed_transactions = []
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, [], "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]
    
    @staticmethod
    def is_valid_proof(block, block_hash):
        return (block_hash.startswith('0' * Blockchain.difficlty) and block_hash == block.compute_hash())
    
    def add_block(self, block, proof):
        previous_hash = self.last_block.hash

        if previous_hash != block.previous_hash:
            return False
        
        if not Blockchain.is_valid_proof(block, proof):
            return False
        
        block.hash = proof
        self.chain.append(block)
        return True
    
    def proof_of_work(self,block):
        block.nonce = 0
        
        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difficlty):
            block.nonce += 1
            computed_hash = block.compute_hash()
        
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

        new_block = Block(index=last_block.index+1,
                                transactions=transactions_to_mine,
                                previous_hash=last_block.hash)
        
        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)
        self.unconfirmed_transactions = []
        return new_block.index