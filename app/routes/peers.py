from flask import Blueprint, current_app, request, jsonify
import requests
import json

peers = set()

peers_bp = Blueprint("peers",__name__)

@peers_bp.route("/info")
def info():
    port = current_app.config.get("NODE_PORT")
    return jsonify({"port",port})

def get_port():
    return current_app.config.get("NODE_PORT")

@peers_bp.route('/register', methods=['POST'])
def register_peer():
    new_peer = request.json.get("peer")
    port = current_app.config.get("NODE_PORT")

    if new_peer and new_peer != f"http://localhost:{port}":
        peers.add(new_peer)
        return jsonify({"message": "Peer registered", "peers": list(peers)}), 200    
    return jsonify({"error":"Invalid peer"}), 400
    
@peers_bp.route('/peers', methods=['GET'])
def get_peers():
    return jsonify(list(peers)), 200

@peers_bp.route('/broadcast', methods=['POST'])
def broadcast():
    data = request.json.get("data")

    for peer in peers:
        try:
            requests.post(f"{peer}/message",json={"data": data})
        except:
            print(f"Peer {peer} unreachable")

    return jsonify({"message": "Broadcast complete"}), 200

@peers_bp.route('/message', methods=['POST'])
def recive_message():
    port = current_app.config.get("NODE_PORT")
    print(f"[Node {port}] Resive message:", request.json.get("data"))
    return jsonify({"status": "resived"}), 200

def connect_to_bootstrap(bootstrap_url):
    port = get_port()
    try:
        requests.post(f"{bootstrap_url}/register",
                      json={"peer": f"http://localhost:{port}"})
        print(f"Connected to bootstrap node {bootstrap_url}")
    except:
        print("Bootstrap connection failed")