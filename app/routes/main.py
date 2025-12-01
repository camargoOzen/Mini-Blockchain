from flask import Blueprint, current_app, request, render_template, jsonify
import requests
from app.instance import peers, blockchain
from app.services.save_service import save_blockchain
from app.models.block import Block

main_bp = Blueprint("main", __name__)

def get_port():
    return current_app.config.get("NODE_PORT")

def get_bootstrap_port():
    return current_app.config.get("BOOTSTRAP_PORT")

def update_list_peers(new_peers):
    global peers
    peers |= set(new_peers)

def update_list_un_tx(new_txs):
    for new_tx in new_txs:
        blockchain.add_new_transaction(new_tx)

def sync_blockchain():
    bootstrap_port = get_bootstrap_port()
    if not bootstrap_port:
        # no bootstrap configured
        return

    bootstrap_url = f"http://localhost:{bootstrap_port}"
    try:
        r = requests.get(f"{bootstrap_url}/get/chain", timeout=3)
        if r.status_code == 200:
            remote_chain = r.json()
            # Basic format validation
            if isinstance(remote_chain, dict) and isinstance(remote_chain.get('chain'), list):
                try:
                    blockchain.load_from_dict(remote_chain)
                    save_blockchain(str(get_port()))
                    print("Blockchain synchronized with bootstrap")
                except Exception as e:
                    print("Failed to load remote chain:", e)
            else:
                print("Invalid chain format received from bootstrap")
        else:
            print(f"Bootstrap returned status {r.status_code}")
    except requests.RequestException as e:
        print("sync failed (network):", e)
    except Exception as e:
        print("sync failed:", e)

def sync_unconfirmed_transactions():
    bootstrap_port = get_bootstrap_port()
    if not bootstrap_port:
        return
    
    bootstrap_url = f"http://localhost:{bootstrap_port}"
    try:
        r = requests.get(f"{bootstrap_url}/get/un_tx", timeout=3)
        if r.status_code == 200:
            remote_list = r.json()
            # Basic format validation
            if isinstance(remote_list.get('un_tx'), list):
                try:
                    remote_unconfirmed_transactions = remote_list.get('un_tx')
                    blockchain.unconfirmed_transactions = remote_unconfirmed_transactions
                    print("Blockchain synchronized with bootstrap")
                except Exception as e:
                    print("Failed to load remote chain:", e)
            else:
                print("Invalid chain format received from bootstrap")
        else:
            print(f"Bootstrap returned status {r.status_code}")
    except requests.RequestException as e:
        print("sync failed (network):", e)
    except Exception as e:
        print("sync failed:", e)


def connect_to_bootstrap():
    port = get_port()
    bootstrap_port = get_bootstrap_port()
    bootstrap_url = f"http://localhost:{bootstrap_port}"
    if bootstrap_port is not None:    
        try:
            requests.post(f"{bootstrap_url}/register",
                        json={"peer": f"http://localhost:{port}"})
            sync_blockchain()
            sync_unconfirmed_transactions()
            print(f"Connected to bootstrap node {bootstrap_url}")
        except:
            print("Bootstrap connection failed")

def broadcast_peers():
    current_port = str(get_port())
    for peer in peers:
        if current_port not in peer:
            try:
                requests.post(f"{peer}/register/update",json={"peers": list(peers)})
                print(f"Peers successfuly send to {peer}")
            except:
                print(f"Peer {peer} unreachable")

@main_bp.route('/get/chain', methods=['GET'])
def get_chain():
    return jsonify(blockchain.to_dict()), 200

@main_bp.route('/get/un_tx', methods=['GET'])
def get_unconfirmed_transactions():
    return jsonify({"un_tx": list(blockchain.unconfirmed_transactions)})

@main_bp.route('/update/uncon_tx', methods=['POST'])
def update_unconfirmed_transactions():
    un_tx = request.json.get("un_tx")

    # Accept either a single transaction (dict) or a list of transactions
    if isinstance(un_tx, (list, set, tuple)):
        failures = []
        for tx in un_tx:
            ok = blockchain.add_new_transaction(tx)
            if not ok:
                failures.append(tx)

        if failures:
            return jsonify({"message": "Some transactions failed to add", "failed_count": len(failures)}), 400
        return jsonify({"message": "Transactions added successfully", "count": len(un_tx)}), 200

    else:
        # single transaction
        result = blockchain.add_new_transaction(un_tx)
        if result:
            return jsonify({"message": "Transaction added successfuly"}), 200
        return jsonify({"message": "Fail add transaction"}), 400

@main_bp.route('/update/block', methods=['POST'])
def update_block():
    new_block = request.json.get("block")
    block = Block.from_dict(new_block)
    # Use provided hash as proof if present, otherwise compute it
    proof = getattr(block, 'hash', None) or block.compute_hash()
    result = blockchain.add_block(block, proof)
    if result:
        save_blockchain(str(get_port()))
        blockchain.unconfirmed_transactions = []
        # Optionally clear pending transactions (they should be filtered by block content elsewhere)
        return jsonify({"message": "Block added successfuly"}), 200
    return jsonify({"message": "Fail add block"}), 400

@main_bp.route('/register', methods=['POST'])
def register_peer():
    new_peer = request.json.get("peer")
    port = current_app.config.get("NODE_PORT")

    if new_peer and new_peer != f"http://localhost:{port}":
        peers.add(new_peer)
        broadcast_peers()
        return jsonify({"message": "Peer registered", "peers": list(peers)}), 200    
    return jsonify({"error":"Invalid peer"}), 400

@main_bp.route('/register/update', methods=['POST'])
def update_peers():
    new_peers = request.json.get("peers")
    if not isinstance(new_peers, (list,set,tuple)):
        return jsonify({"error":"peers must be a list"}), 400
    
    update_list_peers(new_peers)
    return jsonify({"message":"List of peers updated successfuly"}), 200

@main_bp.route('/peers', methods=['GET'])
def get_peers():
    return jsonify(list(peers)), 200

@main_bp.route("/")
def home():
    peers.add(f"http://localhost:{get_port()}")
    connect_to_bootstrap()
    return render_template("index.html")