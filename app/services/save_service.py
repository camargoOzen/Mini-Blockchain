# In-memory wallet storage for demo purposes
from app.models.wallet import Wallet
from app.models.block import Block
from app.instance import blockchain
import json
import os

WALLETS_FILE = "wallets.json"
BLOCKCHAIN_FILE = "blockchain.json"

def get_peer_directory(port):
    dir = f"data/{port}"
    os.makedirs(dir, exist_ok=True)
    return dir

def get_walles_file(port):
    dir = f"data/{port}"
    os.makedirs(dir, exist_ok=True)
    return os.path.join(dir, WALLETS_FILE)

def get_block_file(port):
    dir = f"data/{port}"
    os.makedirs(dir, exist_ok=True)
    return os.path.join(dir, BLOCKCHAIN_FILE)

def load_wallets(port):
    wallets_file = get_walles_file(port)
    loaded_wallets = {}
    if os.path.exists(wallets_file):
        try:
            with open(wallets_file, "r") as f:
                data = json.load(f)
                for address, pem in data.items():
                    loaded_wallets[address] = Wallet(private_key_pem=pem)
            print(f"Loaded {len(loaded_wallets)} wallets from disk")
        except Exception as e:
            print(f"Error loading wallets: {e}")
    
    return loaded_wallets

def save_wallets(port, wallets_dict):
    wallets_file = get_walles_file(port)
    try:
        data = {addr: wallet.to_pem() for addr, wallet in wallets_dict.items()}
        with open(wallets_file, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error saving wallets: {e}")

def save_blockchain(port):
    """Saves the current blockchain to a JSON file."""
    blockchain_file = get_block_file(port)
    blockchain_data = []
    for block in blockchain.chain:
        # Ensure transactions are serializable: convert Transaction objects to dicts
        blk = block.to_dict()
        txs = []
        for tx in blk.get('transactions', []):
            if hasattr(tx, 'to_dict') and callable(tx.to_dict):
                txs.append(tx.to_dict())
            else:
                txs.append(tx)
        blk['transactions'] = txs
        blockchain_data.append(blk)

    with open(blockchain_file, 'w') as f:
        json.dump(blockchain_data, f, indent=4)

def load_blockchain(port):
    """Loads the blockchain from a JSON file."""
    blockchain_file = get_block_file(port)
    if not os.path.exists(blockchain_file):
        return False
        
    with open(blockchain_file, 'r') as f:
        blockchain_data = json.load(f)
        
    new_blockchain = []
    for block_data in blockchain_data:    
        # Reconstruct Block object
        block = Block.from_dict(block_data)
        new_blockchain.append(block)
    # Do not directly mutate the global here; return the reconstructed chain
    print(f"Loaded {len(new_blockchain)} blocks from disk")
    return new_blockchain