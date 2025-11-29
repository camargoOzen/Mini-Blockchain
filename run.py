from app import create_app

app = create_app()

if __name__ == "__main__":
    import sys
    
    PORT = int(sys.argv[1])
    bootstrap = None
    if len(sys.argv) >= 3:
        bootstrap = sys.argv[2]

    app.config["NODE_PORT"] = PORT
    app.config["BOOTSTRAP_PORT"] = bootstrap 

    app.run(port=PORT)
