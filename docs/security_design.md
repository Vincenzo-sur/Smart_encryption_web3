# Security & Access Control Design Architecture

## 1. Threat Model & Security Objectives

The security architecture addresses threats targeting data confidentiality, integrity, non-repudiation, and unauthorized access in a decentralized environment:

1. **Passive Eavesdropping on Storage**: Attackers inspecting public IPFS blocks must not gain access to image content.
2. **Ciphertext Tampering**: Malicious actors altering bits of the encrypted image stored on IPFS must be immediately detected before decryption occurs.
3. **Identity Spoofing**: Attackers attempting to claim an image by supplying another user's public Ethereum address must be rejected without valid cryptographic proof of key ownership.
4. **Replay & Impersonation Attacks**: Replaying past signed requests must be mitigated through dynamic nonces / timestamped challenge payloads.
5. **Key Exposure Risks**: Symmetric encryption keys and Ethereum private keys must never be logged, committed to repositories, or exposed across public API routes.

---

## 2. Cryptographic Primitive Selection

### 2.1 AES-256-GCM (Default AEAD Transport Cipher)
- **Choice Justification**: Unlike unauthenticated modes such as CBC or CTR which are vulnerable to bit-flipping and padding oracle attacks, Galois/Counter Mode (GCM) combines CTR encryption with Galois field polynomial authentication.
- **Key Size**: 256 bits (32 bytes), providing defense against quantum brute-force searches (Grover's algorithm safety margin).
- **Nonce Requirement**: Exactly 96 bits (12 bytes) per encryption. Every encryption operation invokes a cryptographically secure random number generator (`os.urandom(12)`). Nonce reuse across identical keys is strictly prohibited.
- **Authentication Tag**: 128 bits (16 bytes). Verifies ciphertext integrity, nonce binding, and associated data simultaneously.

### 2.2 Hardened Chaotic-Tent-Map & Hybrid-Chaotic-AES Modes
- **Three-Stage Chaotic Pipeline**:
  1. **Sine Map Permutation**: Bounds control parameter $\mu \in [0.87, 0.999]$ with burn-in iterations to prevent out-of-range divergence.
  2. **Prime Circulant Substitution**: Constructs a bijective 256-entry S-box via coprime affine strides and keyed Fisher-Yates mixing.
  3. **Vectorized Skewed Tent Map Diffusion**: Uses 256 parallel lanes with $p \neq 0.5$ and periodic perturbation (avoiding binary64 shift-out collapse) followed by bidirectional modular-addition and prefix-XOR chaining for full-buffer avalanche sensitivity.
- **Encrypt-then-MAC & Domain Separation**: Per-encryption encryption and authentication subkeys are derived from `(master_key, nonce)` via HMAC-SHA256. Chaotic mode authenticates `(nonce, associated_data, ciphertext)` in constant time (`hmac.compare_digest`), while `Hybrid-Chaotic-AES` wraps the chaotic output inside AES-256-GCM.
- **Lossless Binary Invariant**: Operates directly on raw byte streams so PNG, RGBA, JPEG, and WebP payloads recover bit-for-bit without image container leaks on IPFS.

### 2.3 SHA-256 Content Attestation
- Cryptographically strong one-way hash computed over the encrypted payload.
- Serves as the primary immutable identifier anchored on the blockchain ledger (`bytes32`).

---

## 3. Wallet Identity Verification (EIP-191)

Web applications cannot trust client-provided wallet addresses alone. An attacker could trivially send `{"address": "0xOwner"}` in an HTTP header or body.

### 3.1 Challenge-Response Authentication Protocol
1. **Challenge Request**: The client requests a challenge message from the backend:
   ```
   "Sign this message to authenticate with ImageRegistry at timestamp: 1715000000 with nonce: 4a2f8b..."
   ```
2. **Client Signing**: The user signs the challenge message in their Web3 wallet (MetaMask / hardware wallet) using `personal_sign` (EIP-191 format with prefix `\x19Ethereum Signed Message:\n`).
3. **Server Recovery**: The backend recovers the public address using elliptic curve point recovery (`ecrecover` equivalent in `eth-account`):
   ```python
   recovered_address = Account.recover_message(encode_defunct(text=challenge), signature=sig)
   ```
4. **Validation**: The operation proceeds only if `recovered_address.lower() == claimed_address.lower()`.

---

## 4. Smart Contract Role-Based Access Control (RBAC)

The `ImageRegistry.sol` smart contract enforces ownership and delegated permissions:
- **Owner**: The wallet that executed `registerImage()`. Holds exclusive rights to grant or revoke read access.
- **Authorized Delegate**: A wallet address added to the image's `authorizedUsers` mapping via `grantAccess(imageId, delegateAddress)`.
- **Permission Verification**:
  ```solidity
  function hasAccess(bytes32 imageId, address user) external view returns (bool) {
      if (!images[imageId].exists) return false;
      return (images[imageId].owner == user || accessPermissions[imageId][user]);
  }
  ```

---

## 5. Key Lifecycle & Secrets Management

1. **Zero Secret Persistence in Code**:
   - Private keys and sensitive tokens are strictly read from environment variables (`.env`).
   - `.env.example` provides documentation with no real secrets.
2. **Ephemeral Encryption Keys**:
   - For Day 1, keys are generated per image and returned to the author during upload for client-side storage.
   - Decryption endpoints accept the user's key over TLS/HTTPS with validated wallet authentication, decrypt in-memory, and immediately purge key bytes from heap scope.
3. **Production Hardening (Roadmap)**:
   - Day 3-5: Asymmetric key encapsulation (ECIES) encrypting symmetric image keys under recipient public keys before storage.
