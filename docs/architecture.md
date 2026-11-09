# System Architecture: Blockchain-Assisted Secure Image Encryption & Integrity Verification

## 1. System Overview
The Blockchain-Assisted Secure Image Encryption system is an enterprise-grade platform designed to guarantee confidential storage, decentralized availability, and verifiable integrity for digital imagery. 

By combining symmetric authenticated encryption (AES-256-GCM), cryptographic content addressing (SHA-256 and IPFS), and immutable smart contract registries on Ethereum, the platform ensures that:
- Images are encrypted before egress from the user environment.
- Encrypted payloads are permanently decoupled from centralized servers via IPFS.
- Ownership, access control lists (ACL), and payload digest fingerprints are immutably anchored on-chain.
- Decryption is mathematically and cryptographically restricted to verified wallet owners and authorized recipients.

---

## 2. Layered Architecture

```
+-----------------------------------------------------------------------+
|                         Presentation Layer                            |
|                 Streamlit Interactive Web Application                 |
+-----------------------------------------------------------------------+
                                   |  (HTTP REST / Multipart)
+-----------------------------------------------------------------------+
|                           API Gateway Layer                           |
|               FastAPI Service Engine (Routes & Schemas)               |
+-----------------------------------------------------------------------+
         |                     |                    |                |
         v                     v                    v                v
+------------------+  +-----------------+  +-----------------+  +-----------------+
|  Security & ACL  |  |  Cryptography   |  |     Storage     |  |   Blockchain    |
|   (Signature     |  |  (AES-256-GCM,  |  |  (IPFS Kubo API |  |   (Web3.py &    |
|  Verification)   |  |   SHA-256 Hash) |  |   & Gateways)   |  | ImageRegistry)  |
+------------------+  +-----------------+  +-----------------+  +-----------------+
                                                                         |
                                                                         v
                                                                +-----------------+
                                                                | Ethereum Ledger |
                                                                | (Ganache/Main)  |
                                                                +-----------------+
```

### 2.1 Encryption Layer
- **Algorithm**: Advanced Encryption Standard in Galois/Counter Mode (AES-256-GCM).
- **Security Properties**: Confidentiality, integrity, and authenticity in a single cryptographic primitive.
- **Key Derivation & Generation**: 256-bit cryptographically secure pseudorandom keys generated via CSPRNG (`os.urandom`).
- **Initialization Vector**: Unique 96-bit (12-byte) nonce generated per encryption cycle. Nonce reuse is strictly prohibited.
- **Integrity Tag**: 128-bit authentication tag calculated over ciphertext and verified during decryption.

### 2.2 Hashing Layer
- **Algorithm**: Secure Hash Algorithm 256-bit (SHA-256).
- **Scope**: Computed over the encrypted byte sequence prior to IPFS publication and on-chain registration.
- **Integrity Validation**: Cross-referenced against the smart contract record upon download before permitting decryption.

### 2.3 Storage Layer (IPFS)
- **Engine**: InterPlanetary File System (IPFS) utilizing Kubo RPC daemon or pinning providers.
- **Content Addressing**: Content Identifier (CIDv0 / CIDv1) generated deterministically from encrypted bytes.
- **Data Invariant**: Unencrypted images NEVER touch the IPFS network.

### 2.4 Blockchain Layer
- **Platform**: Ethereum Virtual Machine (EVM) compatible networks (Ganache for local development/testing).
- **Smart Contract**: `ImageRegistry.sol` (Solidity ^0.8.20).
- **State Stored**:
  - `imageId` (`bytes32` unique identifier)
  - `owner` (`address` of the registrant)
  - `imageHash` (`bytes32` SHA-256 digest of ciphertext)
  - `ipfsCid` (`string` IPFS Content Identifier)
  - `timestamp` (`uint256` block timestamp)
  - `exists` (`bool` status flag)
  - `authorizedUsers` (`mapping(address => bool)` per image)

### 2.5 Security & Access Control Layer
- **Identity Proof**: Ethereum cryptographic wallet signatures (EIP-191 personal sign).
- **Authorization**: On-chain verification of `msg.sender == owner` or `authorizedUsers[requester] == true`.
- **Zero-Trust Delivery**: Backend refuses to decrypt or release payload without validated signature and on-chain permission.

### 2.6 Backend Service Layer
- **Framework**: FastAPI (Asynchronous Python 3.13).
- **Responsibility**: Orchestration of cryptographic operations, IPFS upload/download, Web3 contract calls, and schema validation.

### 2.7 Frontend Presentation Layer
- **Framework**: Streamlit.
- **Features**: Drag-and-drop image upload, real-time status telemetry, verification dashboard, and permission delegation management.

---

## 3. Technology Stack Specification

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| Core Language | Python 3.13 | High productivity, extensive cryptographic and scientific ecosystem |
| Encryption | `cryptography` (Hazmat) | OpenSSL-backed, FIPS-compliant AES-256-GCM primitives |
| Image Processing | Pillow (PIL), NumPy | Resilient binary image manipulation and byte extraction |
| Cryptographic Hashing | `hashlib` | Optimized SHA-256 implementation |
| Smart Contracts | Solidity ^0.8.20 | Industry standard EVM contract development language |
| Blockchain Client | `web3.py`, `eth-account` | Mature Ethereum RPC client and cryptographic signing utilities |
| Storage Interface | IPFS HTTP Client (`requests`) | Direct integration with Kubo API / pinning gateways |
| REST API | FastAPI, Uvicorn, Pydantic | High-performance asynchronous API framework with auto-generated OpenAPI |
| Dashboard | Streamlit | Rapid interactive visualization and telemetry |
| Test Framework | Pytest | Standardized unit, integration, and property testing |
