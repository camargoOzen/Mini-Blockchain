from app.models.blockchain import Blockchain
import os
import time

def test_persistence():
    print("1. Initializing Blockchain...")
    bc = Blockchain()
    
    # Ensure we start fresh for the test (optional, but good for determinism if we want)
    # But here we want to test if it loads existing or creates new. 
    # Let's just print current status.
    print(f"   Current chain length: {len(bc.chain)}")
    
    print("2. Mining a new block...")
    # Mine a block
    # We need a wallet address for the miner, let's fake one
    miner_address = "TEST_MINER_ADDRESS_123"
    result = bc.mine(miner_address=miner_address)
    
    if result:
        print(f"   Block mined! Index: {result['index']}")
    else:
        print("   Mining failed (maybe no transactions? forcing a transaction first)")
        # Add a dummy transaction if needed, but mine() allows empty with miner_address (coinbase)
        # Wait, mine() implementation:
        # if not self.unconfirmed_transactions and not miner_address: return False
        # We passed miner_address, so it should work.
        pass

    print("3. Verifying file existence...")
    if os.path.exists(Blockchain.BLOCKCHAIN_FILE):
        print(f"   {Blockchain.BLOCKCHAIN_FILE} exists.")
    else:
        print(f"   ERROR: {Blockchain.BLOCKCHAIN_FILE} does not exist!")
        return

    print("4. Simulating Server Restart (Creating new Blockchain instance)...")
    # Force reload
    bc2 = Blockchain()
    
    print(f"   New instance chain length: {len(bc2.chain)}")
    
    last_block = bc2.last_block
    print(f"   Last block index: {last_block.index}")
    
    if last_block.index == result['index']:
        print("SUCCESS: Persistence verified! Last block index matches.")
    else:
        print("FAILURE: Last block index does not match.")

if __name__ == "__main__":
    test_persistence()
