from flask import Blueprint, current_app, request, render_template, jsonify
import requests

peers = set()

main_bp = Blueprint("main", __name__)

def get_port():
    return current_app.config.get("NODE_PORT")

def get_bootstrap_port():
    return current_app.config.get("BOOTSTRAP_PORT")

def update_list_peers(new_peers):
    global peers
    peers |= set(new_peers)

def connect_to_bootstrap():
    port = get_port()
    bootstrap_port = get_bootstrap_port()
    bootstrap_url = f"http://localhost:{bootstrap_port}"
    if bootstrap_port is not None:    
        try:
            requests.post(f"{bootstrap_url}/register",
                        json={"peer": f"http://localhost:{port}"})
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