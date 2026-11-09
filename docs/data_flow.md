# System Data Flow Specifications

This document outlines the end-to-end data pipelines for image encryption, blockchain registration, integrity verification, and access-controlled decryption.

---

## Flow 1: Upload, Encryption, Storage, and Registration Pipeline

```
[User / Streamlit UI]
          |
     (1) Image File + Owner Wallet Address
          v
[FastAPI Backend: POST /upload]
          |
     (2) Generate 256-bit Key (or retrieve user session key)
          v
[Encryption Engine: encrypt_image()]
          |
     (3) Produce Ciphertext + 12-byte Nonce + 16-byte Tag
          v
[Hashing Engine: calculate_hash()]
          |
     (4) Calculate SHA-256 Digest of Ciphertext
          v
[Storage Service: upload_to_ipfs()]
          |
     (5) Transmit Ciphertext to IPFS -> Obtain CID
          v
[Blockchain Service: register_image()]
          |
     (6) Submit Transaction (image_hash, CID) to ImageRegistry.sol
          v
[Ethereum Smart Contract]
          |
     (7) Emit ImageRegistered event, store ImageRecord on-chain
          v
[Response to User]: Image ID, IPFS CID, SHA-256 Hash, Transaction Hash
```

### Detailed Sequence
1. **User Initiation**: The user selects an image file via the Streamlit interface and connects their Ethereum wallet address.
2. **Key Generation**: A 256-bit AES key is generated via `os.urandom`.
3. **Authenticated Encryption**: `encrypt_image()` executes AES-256-GCM over the image bytes, yielding the encrypted payload, a distinct 12-byte nonce, and an authentication tag.
4. **Digest Generation**: `calculate_hash()` computes the SHA-256 hex digest directly over the encrypted bytes.
5. **Decentralized Storage**: The encrypted payload is uploaded to IPFS via `upload_to_ipfs()`. IPFS returns a deterministic Content Identifier (CID).
6. **On-Chain Attestation**: `register_image()` invokes the smart contract `registerImage(imageHash, ipfsCid)` function, anchoring the SHA-256 digest and CID under the owner's address.
7. **Acknowledgement**: The backend returns the `imageId`, `ipfsCid`, `imageHash`, and blockchain transaction receipt to the user.

---

## Flow 2: Retrieval, Integrity Verification, Authorization & Decryption Pipeline

```
[User / Streamlit UI]
          |
     (1) Request Image ID + Submit Wallet Signature
          v
[FastAPI Backend: GET /images/{id}/verify & POST /decrypt]
          |
     (2) Verify Wallet Signature (EIP-191) via Security Engine
          v
[Blockchain Service: getImageDetails() & hasAccess()]
          |
     (3) Query ImageRegistry.sol: Verify existence, ACL, and retrieve (image_hash, CID)
          v
[Storage Service: retrieve_from_ipfs(CID)]
          |
     (4) Fetch Encrypted Bytes from IPFS
          v
[Hashing Engine: calculate_hash(retrieved_bytes)]
          |
     (5) Compare Recalculated Hash == Blockchain Recorded Hash
          |
          +--- MISMATCH ---> Abort with IntegrityViolationError
          |
          +--- MATCH    ---> Proceed to Decryption
                                    v
                       [Encryption Engine: decrypt_image()]
                                    v
                       (6) Authenticate Tag and Decrypt Ciphertext
                                    v
                       [Deliver Recovered Image to User]
```

### Integrity & Security Invariants
- **Pre-Decryption Integrity Check**: Decryption is never attempted if the recalculated SHA-256 hash of the retrieved IPFS bytes fails to match the on-chain recorded hash.
- **Access Control Enforcement**: If `hasAccess(requester, imageId)` returns `false` on the smart contract, the backend immediately halts and raises HTTP 403 Forbidden without exposing ciphertext or key data.
- **Cryptographic Authentication**: Even if an unauthorized party bypasses intermediate checks, AES-256-GCM authentication tag verification will fail if any byte of the ciphertext, tag, or key is invalid.
