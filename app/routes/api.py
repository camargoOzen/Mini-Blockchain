from flask import Blueprint, jsonify, request
from app.models.blockchain import Blockchain
from app.models.wallet import Wallet
from app.models.transaction import Transaction
import base64

api_bp = Blueprint("api", __name__, url_prefix="/api")

# Global blockchain instance
blockchain = Blockchain()

# In-memory wallet storage for demo purposes
import json
import os

WALLETS_FILE = "wallets.json"

def load_wallets():
    loaded_wallets = {}
    if os.path.exists(WALLETS_FILE):
        try:
            with open(WALLETS_FILE, "r") as f:
                data = json.load(f)
                for address, pem in data.items():
                    loaded_wallets[address] = Wallet(private_key_pem=pem)
            print(f"Loaded {len(loaded_wallets)} wallets from disk")
        except Exception as e:
            print(f"Error loading wallets: {e}")
    return loaded_wallets

def save_wallets(wallets_dict):
    try:
        data = {addr: wallet.to_pem() for addr, wallet in wallets_dict.items()}
        with open(WALLETS_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error saving wallets: {e}")

# Load wallets on startup
wallets = load_wallets()

@api_bp.route("/wallet/create", methods=["POST"])
def create_wallet():
    """Create a new wallet and return its address and public key."""
    try:
        wallet = Wallet()
        address = wallet.get_address
        pubkey = base64.b64encode(wallet.public_key.to_string()).decode()
        
        # Store wallet in memory and save to disk
        wallets[address] = wallet
        save_wallets(wallets)
        
        return jsonify({
            "success": True,
            "address": address,
            "public_key": pubkey
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route("/wallet/<address>", methods=["DELETE"])
def delete_wallet(address):
    """Delete a wallet from the server."""
    try:
        if address in wallets:
            del wallets[address]
            save_wallets(wallets)
            return jsonify({"success": True, "message": "Wallet deleted successfully"}), 200
        else:
            # Idempotent response: if it's already gone, that's a success for the client
            return jsonify({"success": True, "message": "Wallet already deleted"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route("/wallet/balance/<address>", methods=["GET"])
def get_balance(address):
    """Calculate balance for a given address by scanning the blockchain."""
    try:
        balance = 0
        
        # Scan all blocks for transactions involving this address
        for block in blockchain.chain:
            for tx in block.transactions:
                if isinstance(tx, dict):
                    if tx.get("receiver_address") == address:
                        balance += tx.get("amount", 0)
                    if tx.get("sender_address") == address:
                        balance -= tx.get("amount", 0)
        
        return jsonify({
            "success": True,
            "address": address,
            "balance": balance
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route("/transaction", methods=["POST"])
def create_transaction():
    """Create and add a new transaction to the pending pool."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ["sender_address", "sender_pubkey", "receiver_address", "amount"]
        for field in required_fields:
            if field not in data:
                return jsonify({"success": False, "error": f"Missing field: {field}"}), 400
        
        # Create transaction
        transaction = Transaction(
            sender_address=data["sender_address"],
            sender_pubkey=data["sender_pubkey"],
            receiver_address=data["receiver_address"],
            amount=data["amount"]
        )
        
        # Sign transaction if we have the wallet
        sender_address = data["sender_address"]
        if sender_address in wallets:
            transaction.sign(wallets[sender_address])
        elif "signature" in data:
            # Use provided signature
            transaction.signature = data["signature"]
        else:
            return jsonify({
                "success": False,
                "error": "No signature provided and wallet not found in server"
            }), 400
        
        # Add to blockchain
        success = blockchain.add_new_transaction(transaction.to_dict())
        
        if success:
            return jsonify({
                "success": True,
                "message": "Transaction added to pending pool",
                "transaction": transaction.to_dict()
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Transaction verification failed"
            }), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route("/mine", methods=["POST"])
def mine_block():
    """Mine pending transactions into a new block with optional mining reward."""
    try:
        data = request.get_json() or {}
        miner_address = data.get("miner_address")
        
        result = blockchain.mine(miner_address=miner_address, mining_reward=50)
        
        if result:
            message = f"Block #{result} mined successfully"
            if miner_address:
                message += f" - Miner rewarded 50 coins"
            
            return jsonify({
                "success": True,
                "message": message,
                "block_index": result,
                "mining_reward": 50 if miner_address else 0
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "No transactions to mine"
            }), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route("/faucet", methods=["POST"])
def request_faucet():
    """Request free coins from the faucet."""
    try:
        data = request.get_json()
        
        if not data or "address" not in data:
            return jsonify({
                "success": False,
                "error": "Address is required"
            }), 400
        
        address = data["address"]
        faucet_amount = 100
        
        # Create faucet transaction (no sender)
        faucet_transaction = {
            "sender_address": "FAUCET",
            "sender_pubkey": None,
            "receiver_address": address,
            "amount": faucet_amount,
            "signature": None
        }
        
        # Add to pending transactions
        success = blockchain.add_new_transaction(faucet_transaction)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Faucet request successful! {faucet_amount} coins will be available after mining",
                "amount": faucet_amount,
                "pending": True
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Failed to add faucet transaction"
            }), 400
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route("/blockchain", methods=["GET"])
def get_blockchain():
    """Get the entire blockchain."""
    try:
        chain_data = []
        
        for block in blockchain.chain:
            chain_data.append({
                "index": block.index,
                "timestamp": block.timestamp,
                "transactions": block.transactions,
                "nonce": block.nonce,
                "hash": block.hash,
                "previous_hash": block.previous_hash
            })
        
        return jsonify({
            "success": True,
            "length": len(chain_data),
            "chain": chain_data
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route("/transactions/pending", methods=["GET"])
def get_pending_transactions():
    """Get all pending (unconfirmed) transactions."""
    try:
        return jsonify({
            "success": True,
            "count": len(blockchain.unconfirmed_transactions),
            "transactions": blockchain.unconfirmed_transactions
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
