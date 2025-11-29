"""
Test script to verify custom hash implementations against known test vectors
"""
import sys
sys.path.insert(0, 'c:\\Proyectos\\Mini-Blockchain')

from app.models.hash_functions import sha256, ripemd160

def test_sha256():
    """Test SHA-256 against known test vectors from NIST"""
    print("Testing SHA-256 implementation...")
    
    # Test vector 1: Empty string
    result = sha256(b"")
    expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert result.hex() == expected, f"Empty string failed: {result.hex()}"
    print("[PASS] Empty string test passed")
    
    # Test vector 2: "abc"
    result = sha256(b"abc")
    expected = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert result.hex() == expected, f"'abc' failed: {result.hex()}"
    print("[PASS] 'abc' test passed")
    
    # Test vector 3: Longer message
    result = sha256(b"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq")
    expected = "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1"
    assert result.hex() == expected, f"Long message failed: {result.hex()}"
    print("[PASS] Long message test passed")
    
    # Test vector 4: "The quick brown fox..."
    result = sha256(b"The quick brown fox jumps over the lazy dog")
    expected = "d7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592"
    assert result.hex() == expected, f"Fox message failed: {result.hex()}"
    print("[PASS] 'The quick brown fox...' test passed")
    
    print("[SUCCESS] All SHA-256 tests passed!\n")

def test_ripemd160():
    """Test RIPEMD-160 against known test vectors"""
    print("Testing RIPEMD-160 implementation...")
    
    # Test vector 1: Empty string
    result = ripemd160(b"")
    expected = "9c1185a5c5e9fc54612808977ee8f548b2258d31"
    assert result.hex() == expected, f"Empty string failed: {result.hex()}"
    print("[PASS] Empty string test passed")
    
    # Test vector 2: "abc"
    result = ripemd160(b"abc")
    expected = "8eb208f7e05d987a9b044a8e98c6b087f15a0bfc"
    assert result.hex() == expected, f"'abc' failed: {result.hex()}"
    print("[PASS] 'abc' test passed")
    
    # Test vector 3: "message digest"
    result = ripemd160(b"message digest")
    expected = "5d0689ef49d2fae572b881b123a85ffa21595f36"
    assert result.hex() == expected, f"'message digest' failed: {result.hex()}"
    print("[PASS] 'message digest' test passed")
    
    # Test vector 4: a-z
    result = ripemd160(b"abcdefghijklmnopqrstuvwxyz")
    expected = "f71c27109c692c1b56bbdceb5b9d2865b3708dbc"
    assert result.hex() == expected, f"'a-z' failed: {result.hex()}"
    print("[PASS] 'a-z' test passed")
    
    print("[SUCCESS] All RIPEMD-160 tests passed!\n")

def test_blockchain_integration():
    """Test that the blockchain components work with custom hash functions"""
    print("Testing blockchain integration...")
    
    from app.models.wallet import Wallet
    from app.models.transaction import Transaction
    from app.models.block import Block
    
    # Test wallet creation and address generation
    wallet = Wallet()
    address = wallet.get_address
    assert len(address) == 40, f"Address should be 40 hex chars, got {len(address)}"
    print(f"[PASS] Wallet created with address: {address[:16]}...")
    
    # Test transaction creation and signing
    wallet2 = Wallet()
    tx = Transaction(
        sender_address=wallet.get_address,
        sender_pubkey=wallet.public_key.to_string().hex(),
        receiver_address=wallet2.get_address,
        amount=10
    )
    
    # Sign transaction
    from app.models.util import b64encode
    tx.sender_pubkey = b64encode(wallet.public_key.to_string())
    tx.sign(wallet)
    print(f"[PASS] Transaction signed")
    
    # Verify signature
    is_valid = tx.verify_signature()
    assert is_valid, "Transaction signature verification failed"
    print(f"[PASS] Transaction signature verified")
    
    # Test block hashing
    block = Block(0, [], "0")
    block_hash = block.compute_hash()
    assert len(block_hash) == 64, f"Block hash should be 64 hex chars, got {len(block_hash)}"
    print(f"[PASS] Block hash computed: {block_hash[:16]}...")
    
    print("[SUCCESS] All blockchain integration tests passed!\n")

if __name__ == "__main__":
    try:
        test_sha256()
        test_ripemd160()
        test_blockchain_integration()
        print("=" * 50)
        print("ALL TESTS PASSED SUCCESSFULLY!")
        print("=" * 50)
    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
