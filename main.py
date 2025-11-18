import base64
from app.models.blockchain import Blockchain
from app.models.wallet import Wallet
from app.models.transaction import Transaction
#from app.models.util import b64encode

if __name__ == "__main__":
    chain = Blockchain()

    alice = Wallet()
    bob = Wallet()

    transaction = Transaction(
        sender_address=alice.get_address,
        sender_pubkey=base64.b64encode(alice.public_key.to_string()).decode(),
        receiver_address=bob.get_address,
        amount=10
    )

    transaction.signature = transaction.sign(alice)

    print(type(transaction.signature))

    chain.add_new_transaction(transaction.to_dict())
    chain.mine()

    for b in chain.chain:
        print(vars(b))