# Engineering Team Status Board

**Sprint**: Day 2 Multi-Cipher Hardening & Evaluation Integration  
**Leadership**: Chief System Architect: Surya (`Vincenzo-sur`)  
**Repository Branch**: `main`  
**Date**: 2026-11-11  

---

## Member Task & Factor Matrix

| Factor # | Factor Name | Assigned Engineering Role | Status | Target Deliverables | Interfaces Defined |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Factor 1** | Cryptography & Key Management | Cryptography Engineer | Completed (Multi-Cipher) | `encryption/encrypt.py`, `decrypt.py`, `key_manager.py`, `chaotic_image_encryption.py`, `sine_map_permutation.py`, `prime_circulant_substitution.py`, `tent_map_diffusion.py` | `encrypt_image()`, `decrypt_image()`, `generate_encryption_key()` |
| **Factor 2** | Hashing & Content Fingerprinting | Cryptography Engineer | Completed | `hashing/hash_utils.py`, `tests/test_hashing.py` | `calculate_hash()`, `calculate_hash_bytes()` |
| **Factor 3** | Smart Contract Registry & Web3 | Blockchain Engineer | In Progress | `blockchain/contracts/ImageRegistry.sol`, `blockchain/blockchain_service.py`, `blockchain/deploy.py` | `registerImage()`, `getImageDetails()`, `grantAccess()`, `revokeAccess()`, `verifyOwnership()` |
| **Factor 4** | Decentralized Storage (IPFS) | Storage & IPFS Engineer | In Progress | `storage/ipfs_service.py`, `storage/README.md` | `upload_to_ipfs()`, `retrieve_from_ipfs()` |
| **Factor 5** | Wallet Auth & Access Control | Security Engineer | In Progress | `security/authentication.py`, `security/access_control.py`, `docs/security_design.md` | `verify_signature()`, `check_permission()` |
| **Factor 6** | REST API & Streamlit Dashboard | Full-Stack Engineer | Updated (Multi-Cipher) | `backend/main.py`, `backend/routes/`, `backend/schemas/`, `frontend/app.py` | `POST /upload`, `GET /images/{id}/verify`, `POST /decrypt`, etc. |
| **Factor 7** | Evaluation Metrics & Benchmarks | Performance & Security Engineer | Completed | `evaluation/entropy.py`, `npcr.py`, `uaci.py`, `histogram.py`, `correlation.py`, `chaotic_encryption_metrics.py` | NPCR, UACI, Entropy, Key Sensitivity, PSNR, Comparative Suite |

---

## Detailed Factor Tracking

### Factor 1: Cryptography & Key Management
- **Owner**: Cryptography Engineer
- **Specification**: Unified multi-cipher engine supporting `AES-256-GCM` (default), hardened `Chaotic-Tent-Map` (Sine Map + Prime Circulant + Skewed Tent Map), and `Hybrid-Chaotic-AES`, all enforcing fresh 96-bit CSPRNG nonces, domain-separated HMAC-SHA256 subkeys, and 128-bit AEAD tag verification.
- **Dependencies**: OpenSSL / Python `cryptography` library, `numpy`.
- **Handoff Criteria**: Byte-for-byte round-trip recovery passes across PNG, RGBA, and JPEG payloads; tampering with ciphertext, tag, or associated data raises `AuthenticationError`.

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
