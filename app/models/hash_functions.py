"""
Custom implementations of SHA-256 and RIPEMD-160 hash functions.
Following official specifications:
- SHA-256: FIPS 180-4
- RIPEMD-160: ISO/IEC 10118-3
"""

def _rotr(n, b):
    """Rotate right: rotate n right by b bits (32-bit)"""
    return ((n >> b) | (n << (32 - b))) & 0xffffffff

def _shr(n, b):
    """Shift right"""
    return n >> b

def _sha256_ch(x, y, z):
    """SHA-256 Ch function"""
    return (x & y) ^ (~x & z)

def _sha256_maj(x, y, z):
    """SHA-256 Maj function"""
    return (x & y) ^ (x & z) ^ (y & z)

def _sha256_sigma0(x):
    """SHA-256 Σ0 function"""
    return _rotr(x, 2) ^ _rotr(x, 13) ^ _rotr(x, 22)

def _sha256_sigma1(x):
    """SHA-256 Σ1 function"""
    return _rotr(x, 6) ^ _rotr(x, 11) ^ _rotr(x, 25)

def _sha256_gamma0(x):
    """SHA-256 σ0 function"""
    return _rotr(x, 7) ^ _rotr(x, 18) ^ _shr(x, 3)

def _sha256_gamma1(x):
    """SHA-256 σ1 function"""
    return _rotr(x, 17) ^ _rotr(x, 19) ^ _shr(x, 10)

def sha256(data: bytes) -> bytes:
    """
    Custom SHA-256 implementation following FIPS 180-4.
    
    Args:
        data: Input bytes to hash
        
    Returns:
        32-byte hash digest
    """
    # Initial hash values (first 32 bits of fractional parts of square roots of first 8 primes)
    H = [
        0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
        0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
    ]
    
    # Round constants (first 32 bits of fractional parts of cube roots of first 64 primes)
    K = [
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
        0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
        0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
        0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
        0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
        0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
        0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
    ]
    
    # Pre-processing: padding the message
    msg = bytearray(data)
    msg_len = len(data)
    msg.append(0x80)  # Append bit '1' followed by zeros
    
    # Pad until message length ≡ 448 (mod 512)
    while (len(msg) % 64) != 56:
        msg.append(0x00)
    
    # Append original message length in bits as 64-bit big-endian
    msg.extend((msg_len * 8).to_bytes(8, 'big'))
    
    # Process message in 512-bit (64-byte) chunks
    for chunk_start in range(0, len(msg), 64):
        chunk = msg[chunk_start:chunk_start + 64]
        
        # Create message schedule (64 x 32-bit words)
        W = []
        for i in range(16):
            W.append(int.from_bytes(chunk[i*4:(i+1)*4], 'big'))
        
        for i in range(16, 64):
            s0 = _sha256_gamma0(W[i-15])
            s1 = _sha256_gamma1(W[i-2])
            W.append((W[i-16] + s0 + W[i-7] + s1) & 0xffffffff)
        
        # Initialize working variables
        a, b, c, d, e, f, g, h = H
        
        # Main loop (64 rounds)
        for i in range(64):
            S1 = _sha256_sigma1(e)
            ch = _sha256_ch(e, f, g)
            temp1 = (h + S1 + ch + K[i] + W[i]) & 0xffffffff
            S0 = _sha256_sigma0(a)
            maj = _sha256_maj(a, b, c)
            temp2 = (S0 + maj) & 0xffffffff
            
            h = g
            g = f
            f = e
            e = (d + temp1) & 0xffffffff
            d = c
            c = b
            b = a
            a = (temp1 + temp2) & 0xffffffff
        
        # Add compressed chunk to current hash value
        H[0] = (H[0] + a) & 0xffffffff
        H[1] = (H[1] + b) & 0xffffffff
        H[2] = (H[2] + c) & 0xffffffff
        H[3] = (H[3] + d) & 0xffffffff
        H[4] = (H[4] + e) & 0xffffffff
        H[5] = (H[5] + f) & 0xffffffff
        H[6] = (H[6] + g) & 0xffffffff
        H[7] = (H[7] + h) & 0xffffffff
    
    # Produce final hash value (big-endian)
    digest = b''.join(h.to_bytes(4, 'big') for h in H)
    return digest


def _rotl(n, b):
    """Rotate left: rotate n left by b bits (32-bit)"""
    return ((n << b) | (n >> (32 - b))) & 0xffffffff

def _ripemd160_f(j, x, y, z):
    """RIPEMD-160 selection function"""
    if j < 16:
        return x ^ y ^ z
    elif 16 <= j < 32:
        return (x & y) | (~x & z)
    elif 32 <= j < 48:
        return (x | ~y) ^ z
    elif 48 <= j < 64:
        return (x & z) | (y & ~z)
    else:  # 64 <= j < 80
        return x ^ (y | ~z)

def _ripemd160_K(j):
    """RIPEMD-160 left line constants"""
    if j < 16:
        return 0x00000000
    elif 16 <= j < 32:
        return 0x5A827999
    elif 32 <= j < 48:
        return 0x6ED9EBA1
    elif 48 <= j < 64:
        return 0x8F1BBCDC
    else:  # 64 <= j < 80
        return 0xA953FD4E

def _ripemd160_Kp(j):
    """RIPEMD-160 right line constants"""
    if j < 16:
        return 0x50A28BE6
    elif 16 <= j < 32:
        return 0x5C4DD124
    elif 32 <= j < 48:
        return 0x6D703EF3
    elif 48 <= j < 64:
        return 0x7A6D76E9
    else:  # 64 <= j < 80
        return 0x00000000

def ripemd160(data: bytes) -> bytes:
    """
    Custom RIPEMD-160 implementation following ISO/IEC 10118-3.
    
    Args:
        data: Input bytes to hash
        
    Returns:
        20-byte hash digest
    """
    # Initial hash values
    H = [0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0]
    
    # Message permutation for left line
    r = [
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
        7, 4, 13, 1, 10, 6, 15, 3, 12, 0, 9, 5, 2, 14, 11, 8,
        3, 10, 14, 4, 9, 15, 8, 1, 2, 7, 0, 6, 13, 11, 5, 12,
        1, 9, 11, 10, 0, 8, 12, 4, 13, 3, 7, 15, 14, 5, 6, 2,
        4, 0, 5, 9, 7, 12, 2, 10, 14, 1, 3, 8, 11, 6, 15, 13
    ]
    
    # Message permutation for right line
    rp = [
        5, 14, 7, 0, 9, 2, 11, 4, 13, 6, 15, 8, 1, 10, 3, 12,
        6, 11, 3, 7, 0, 13, 5, 10, 14, 15, 8, 12, 4, 9, 1, 2,
        15, 5, 1, 3, 7, 14, 6, 9, 11, 8, 12, 2, 10, 0, 4, 13,
        8, 6, 4, 1, 3, 11, 15, 0, 5, 12, 2, 13, 9, 7, 10, 14,
        12, 15, 10, 4, 1, 5, 8, 7, 6, 2, 13, 14, 0, 3, 9, 11
    ]
    
    # Rotation amounts for left line
    s = [
        11, 14, 15, 12, 5, 8, 7, 9, 11, 13, 14, 15, 6, 7, 9, 8,
        7, 6, 8, 13, 11, 9, 7, 15, 7, 12, 15, 9, 11, 7, 13, 12,
        11, 13, 6, 7, 14, 9, 13, 15, 14, 8, 13, 6, 5, 12, 7, 5,
        11, 12, 14, 15, 14, 15, 9, 8, 9, 14, 5, 6, 8, 6, 5, 12,
        9, 15, 5, 11, 6, 8, 13, 12, 5, 12, 13, 14, 11, 8, 5, 6
    ]
    
    # Rotation amounts for right line
    sp = [
        8, 9, 9, 11, 13, 15, 15, 5, 7, 7, 8, 11, 14, 14, 12, 6,
        9, 13, 15, 7, 12, 8, 9, 11, 7, 7, 12, 7, 6, 15, 13, 11,
        9, 7, 15, 11, 8, 6, 6, 14, 12, 13, 5, 14, 13, 13, 7, 5,
        15, 5, 8, 11, 14, 14, 6, 14, 6, 9, 12, 9, 12, 5, 15, 8,
        8, 5, 12, 9, 12, 5, 14, 6, 8, 13, 6, 5, 15, 13, 11, 11
    ]
    
    # Pre-processing: padding
    msg = bytearray(data)
    msg_len = len(data)
    msg.append(0x80)
    
    while (len(msg) % 64) != 56:
        msg.append(0x00)
    
    # Append length in bits as 64-bit little-endian
    msg.extend((msg_len * 8).to_bytes(8, 'little'))
    
    # Process message in 512-bit chunks
    for chunk_start in range(0, len(msg), 64):
        chunk = msg[chunk_start:chunk_start + 64]
        
        # Break chunk into 16 x 32-bit little-endian words
        X = []
        for i in range(16):
            X.append(int.from_bytes(chunk[i*4:(i+1)*4], 'little'))
        
        # Initialize working variables
        AL, BL, CL, DL, EL = H
        AR, BR, CR, DR, ER = H
        
        # 80 rounds
        for j in range(80):
            # Left line
            T = (AL + _ripemd160_f(j, BL, CL, DL) + X[r[j]] + _ripemd160_K(j)) & 0xffffffff
            T = (_rotl(T, s[j]) + EL) & 0xffffffff
            AL = EL
            EL = DL
            DL = _rotl(CL, 10)
            CL = BL
            BL = T
            
            # Right line
            T = (AR + _ripemd160_f(79 - j, BR, CR, DR) + X[rp[j]] + _ripemd160_Kp(j)) & 0xffffffff
            T = (_rotl(T, sp[j]) + ER) & 0xffffffff
            AR = ER
            ER = DR
            DR = _rotl(CR, 10)
            CR = BR
            BR = T
        
        # Update hash values
        T = (H[1] + CL + DR) & 0xffffffff
        H[1] = (H[2] + DL + ER) & 0xffffffff
        H[2] = (H[3] + EL + AR) & 0xffffffff
        H[3] = (H[4] + AL + BR) & 0xffffffff
        H[4] = (H[0] + BL + CR) & 0xffffffff
        H[0] = T
    
    # Produce final hash (little-endian)
    digest = b''.join(h.to_bytes(4, 'little') for h in H)
    return digest
