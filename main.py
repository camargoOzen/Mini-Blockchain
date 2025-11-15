import blockchain

if __name__ == "__main__":
    chain = blockchain.Blockchain()
    chain.add_new_transaction("Hello")
    chain.add_new_transaction("World")
    chain.mine()
    for b in chain.chain:
        print(vars(b))