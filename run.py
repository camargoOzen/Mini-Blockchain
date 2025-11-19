from app import create_app
from app.routes.peers import  peers_bp, connect_to_bootstrap

app = create_app()
app.register_blueprint(peers_bp)

if __name__ == "__main__":
    import sys
    
    PORT = int(sys.argv[1])
    app.config["NODE_PORT"] = PORT
    
    bootstrap = None

    if len(sys.argv) >= 3:
        bootstrap = sys.argv[2]

    with app.app_context():    
        if bootstrap:
            connect_to_bootstrap(bootstrap_url=bootstrap)
        
    app.run(port=PORT)
