# Mini-Blockchain
This project is a minimal, fully functional blockchain implementation using python for demonstrates the core concepts behind blockchain technology: block, hashing and chain validation.

## Features
- **Block:**
    - Index
    - Timestamp
    - Transactions
    - Previous hash
- **SHA-256 cryptographic hashing**
- **Blockchain validation**
- **Web interface**
- **Peer to Peer network**

## Requirements

To run this project, you need:

- `Python` 3.8+

## How to run
Clone this repository
```bash
    git clone https://github.com/camargoOzen/Mini-Blockchain
    cd Mini-Blockchaingit 
```
Install the dependencies.
```bash
    pip install -r requirements.txt 
```
Run the blockchain in port 5000.
```bash
    python run.py 5000 
```
To create multiple custom nodes, open a new terminal and run.
```bash
    python run.py 5001 5000 
```