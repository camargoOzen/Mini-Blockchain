from flask import Blueprint, jsonify, request, current_app
from app.models.wallet import Wallet
from app.models.transaction import Transaction
from app.instance import blockchain, wallets, peers
from app.services.save_service import save_wallets, save_blockchain
import base64
import requests

api_bp = Blueprint("api", __name__, url_prefix="/api")

def get_port():
    return current_app.config.get("NODE_PORT")

def broadcast_unconfirmed_transactions(uncon_tx):
    current_port = str(get_port())
    try:
        self_url = f"http://localhost:{current_port}"
    except Exception:
        self_url = None
    # Accept either a single transaction or an iterable of transactions
    if isinstance(uncon_tx, (dict, Transaction)):
        tx_list = [uncon_tx]
    else:
        tx_list = list(uncon_tx)

    # Normalize payload: ensure transactions are JSON-serializable dicts
    payload = []
    for tx in tx_list:
        if isinstance(tx, dict):
            payload.append(tx)
        elif hasattr(tx, 'to_dict') and callable(tx.to_dict):
            payload.append(tx.to_dict())
        else:
            payload.append(tx)

    print(payload)

    for peer in peers:
        if self_url and peer == self_url:
            continue
        try:
            requests.post(f"{peer}/update/uncon_tx", json={"un_tx": payload}, timeout=3)
            print(f"Transaction(s) successfully sent to {peer}")
        except requests.RequestException as e:
            print(f"Peer {peer} unreachable: {e}")

def broadcast_block(new_block):
    current_port = str(get_port())
    try:
        self_url = f"http://localhost:{current_port}"
    except Exception:
        self_url = None

    block_payload = new_block if isinstance(new_block, dict) else (new_block.to_dict() if hasattr(new_block, 'to_dict') else new_block)

    for peer in peers:
        if self_url and peer == self_url:
            continue
        try:
            requests.post(f"{peer}/update/block", json={"block": block_payload}, timeout=3)
            print(f"Block successfully sent to {peer}")
        except requests.RequestException as e:
            print(f"Peer {peer} unreachable: {e}")

@api_bp.route("/wallet/create", methods=["POST"])
def create_wallet():
    """Create a new wallet and return its address and public key."""
    try:
        wallet = Wallet()
        address = wallet.get_address
        pubkey = base64.b64encode(wallet.public_key.to_string()).decode()
        
        # Store wallet in memory and save to disk
        wallets[address] = wallet
        save_wallets(str(get_port()),wallets)
        
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
            save_wallets(str(get_port()),wallets)
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
        
        sender_address = data["sender_address"]
        amount = data["amount"]
        
        # Check sender balance
        balance = 0
        for block in blockchain.chain:
            for tx in block.transactions:
                if isinstance(tx, dict):
                    if tx.get("receiver_address") == sender_address:
                        balance += tx.get("amount", 0)
                    if tx.get("sender_address") == sender_address:
                        balance -= tx.get("amount", 0)
        
        # Check pending transactions
        for tx in blockchain.unconfirmed_transactions:
            if isinstance(tx, dict):
                if tx.get("receiver_address") == sender_address:
                    balance += tx.get("amount", 0)
                if tx.get("sender_address") == sender_address:
                    balance -= tx.get("amount", 0)
        
        # Validate sufficient balance
        if balance < amount:
            return jsonify({
                "success": False,
                "error": f"Insufficient balance. Available: {balance} coins, Required: {amount} coins"
            }), 400
        
        # Create transaction
        transaction = Transaction(
            sender_address=sender_address,
            sender_pubkey=data["sender_pubkey"],
            receiver_address=data["receiver_address"],
            amount=amount
        )
        
        # Sign transaction if we have the wallet
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
            broadcast_unconfirmed_transactions(transaction.to_dict())
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
    port = get_port()
    try:
        data = request.get_json() or {}
        miner_address = data.get("miner_address")
        
        result = blockchain.mine(miner_address=miner_address, mining_reward=50)
        
        if result:
            message = f"Block #{result['index']} mined successfully"
            if miner_address:
                message += f" - Miner rewarded 50 coins"
            save_blockchain(port)
            broadcast_block(blockchain.last_block.to_dict())
            return jsonify({
                "success": True,
                "message": message,
                "block_index": result['index'],
                "mining_time": result['mining_time'],
                "difficulty": result['difficulty'],
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
            broadcast_unconfirmed_transactions(faucet_transaction)
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
                "previous_hash": block.previous_hash,
                "difficulty": block.difficulty if hasattr(block, 'difficulty') else 4,
                "mining_time": block.mining_time if hasattr(block, 'mining_time') else 0
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

@api_bp.route("/mining/stats", methods=["GET"])
def get_mining_stats():
    """Get current mining statistics."""
    try:
        current_difficulty = blockchain.get_difficulty()
        total_blocks = len(blockchain.chain)
        blocks_until_next = blockchain.blocks_until_next_difficulty()
        
        # Calculate average mining time for last 10 blocks
        recent_blocks = blockchain.chain[-10:] if len(blockchain.chain) > 10 else blockchain.chain[1:]  # Skip genesis
        mining_times = [b.mining_time for b in recent_blocks if hasattr(b, 'mining_time') and b.mining_time is not None]
        avg_mining_time = sum(mining_times) / len(mining_times) if mining_times else 0
        
        return jsonify({
            "success": True,
            "current_difficulty": current_difficulty,
            "total_blocks": total_blocks,
            "blocks_until_next_difficulty": blocks_until_next,
            "average_mining_time": round(avg_mining_time, 2),
            "difficulty_increment_interval": blockchain.DIFFICULTY_INCREMENT_INTERVAL
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route("/blockchain/validate", methods=["GET"])
def validate_blockchain():
    """Validate the integrity of the blockchain."""
    try:
        validation_result = blockchain.validate_chain()
        
        return jsonify({
            "success": True,
            "valid": validation_result['valid'],
            "total_blocks": validation_result['total_blocks'],
            "errors": validation_result['errors']
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
