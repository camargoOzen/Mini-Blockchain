from app import create_app
from app.instance import wallets
from app.services.save_service import load_wallets, load_blockchain, save_blockchain
from app.models.blockchain import Blockchain
from app.instance import blockchain

app = create_app()

if __name__ == "__main__":
    import sys
    
    PORT = int(sys.argv[1])
    bootstrap = None
    if len(sys.argv) >= 3:
        bootstrap = sys.argv[2]

    app.config["NODE_PORT"] = PORT
    app.config["BOOTSTRAP_PORT"] = bootstrap 

    loaded_wallets = load_wallets(str(PORT))
    wallets.update(loaded_wallets)

    loaded_chain = load_blockchain(str(PORT))
    if loaded_chain:
        # Assign the loaded chain into the global blockchain instance
        blockchain.chain = loaded_chain
        print("Blockchain loaded from disk")
    else:
        blockchain = Blockchain()
        save_blockchain(PORT)
        
    app.run(port=PORT, debug=True)
