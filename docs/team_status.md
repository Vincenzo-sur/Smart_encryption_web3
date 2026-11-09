# Engineering Team Status Board

**Sprint**: Day 1 Foundation  
**Leadership**: Chief System Architect: Surya (`Vincenzo-sur`)  
**Repository Branch**: `main`  
**Date**: 2026-11-09  

---

## Member Task & Factor Matrix

| Factor # | Factor Name | Assigned Engineering Role | Status | Target Deliverables | Interfaces Defined |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Factor 1** | Cryptography & Key Management | Cryptography Engineer | In Progress | `encryption/encrypt.py`, `encryption/decrypt.py`, `encryption/key_manager.py` | `encrypt_image()`, `decrypt_image()`, `generate_encryption_key()` |
| **Factor 2** | Hashing & Content Fingerprinting | Cryptography Engineer | In Progress | `hashing/hash_utils.py`, `tests/test_hashing.py` | `calculate_hash()`, `calculate_hash_bytes()` |
| **Factor 3** | Smart Contract Registry & Web3 | Blockchain Engineer | In Progress | `blockchain/contracts/ImageRegistry.sol`, `blockchain/blockchain_service.py`, `blockchain/deploy.py` | `registerImage()`, `getImageDetails()`, `grantAccess()`, `revokeAccess()`, `verifyOwnership()` |
| **Factor 4** | Decentralized Storage (IPFS) | Storage & IPFS Engineer | In Progress | `storage/ipfs_service.py`, `storage/README.md` | `upload_to_ipfs()`, `retrieve_from_ipfs()` |
| **Factor 5** | Wallet Auth & Access Control | Security Engineer | In Progress | `security/authentication.py`, `security/access_control.py`, `docs/security_design.md` | `verify_signature()`, `check_permission()` |
| **Factor 6** | REST API & Streamlit Dashboard | Full-Stack Engineer | In Progress | `backend/main.py`, `backend/routes/`, `backend/schemas/`, `frontend/app.py` | `POST /upload`, `GET /images/{id}/verify`, `POST /decrypt`, etc. |
| **Factor 7** | Evaluation Metrics Skeletons | Performance & Security Engineer | Planned (Day 3-5) | `evaluation/entropy.py`, `npcr.py`, `uaci.py`, `histogram.py` | NPCR, UACI, Shannon Entropy metrics |

---

## Detailed Factor Tracking

### Factor 1: Cryptography & Key Management
- **Owner**: Cryptography Engineer
- **Specification**: AES-256-GCM symmetric cipher engine operating directly on image bytes with dynamic 96-bit CSPRNG nonces and 128-bit integrity tags.
- **Dependencies**: OpenSSL / Python `cryptography` library.
- **Handoff Criteria**: Round-trip encryption-decryption test passes byte-for-byte; authentication tag verification rejects any tampered bit.

### Factor 2: Hashing & Content Fingerprinting
- **Owner**: Cryptography Engineer
- **Specification**: SHA-256 digest computation returning lowercase hexadecimal strings and EVM-compatible `bytes32`.
- **Dependencies**: Python standard library `hashlib`.
- **Handoff Criteria**: Digest verification test proves consistency and non-collision on sample images.

### Factor 3: Smart Contract & Blockchain Registry
- **Owner**: Blockchain Engineer
- **Specification**: Solidity contract `ImageRegistry.sol` tracking image IDs, owner address, SHA-256 digest, IPFS CID, and mapping for delegated access control.
- **Dependencies**: `web3.py`, EVM node (Ganache / simulated provider).
- **Handoff Criteria**: Contract compiles without warnings and registers images with event emissions.

### Factor 4: Decentralized Storage (IPFS)
- **Owner**: Storage & IPFS Engineer
- **Specification**: HTTP RPC integration with Kubo IPFS node (`/api/v0/add`, `/api/v0/cat`) with explicit connection exception reporting.
- **Dependencies**: Local Kubo daemon or remote gateway.
- **Handoff Criteria**: Strict validation ensuring only encrypted bytes are dispatched; diagnostic errors raised if offline.

### Factor 5: Wallet Auth & Access Control
- **Owner**: Security Engineer
- **Specification**: Cryptographic verification of EIP-191 signatures against claimed Ethereum addresses and smart contract ACL lookup.
- **Dependencies**: `eth-account`.
- **Handoff Criteria**: Rejects arbitrary unauthenticated addresses; accepts valid signed challenges.

### Factor 6: REST API & Streamlit Dashboard
- **Owner**: Full-Stack Engineer
- **Specification**: FastAPI backend exposing validated endpoints with Pydantic schemas, and an interactive Streamlit UI for user interaction.
- **Dependencies**: FastAPI, Uvicorn, Streamlit.
- **Handoff Criteria**: Backend boots with OpenAPI docs at `/docs`; Streamlit launches without errors.
