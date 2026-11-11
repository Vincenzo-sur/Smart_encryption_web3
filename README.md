# Blockchain-Assisted Secure Image Encryption and Integrity Verification

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-FF4B4B.svg)](https://streamlit.io/)
[![Solidity](https://img.shields.io/badge/Solidity-%5E0.8.20-363636.svg)](https://soliditylang.org/)

An enterprise-grade decentralized system designed to guarantee confidential storage, decentralized availability, and verifiable integrity for digital imagery.

By combining symmetric authenticated encryption (AES-256-GCM), decentralized content addressing (IPFS), and immutable smart contract registries on Ethereum, the platform ensures that images are encrypted before leaving the client environment, stored securely on IPFS, anchored on-chain for tamper-evident attestation, and decrypted exclusively by authorized Ethereum wallets.

---

## Architecture Overview

```
[Streamlit Frontend]  <--->  [FastAPI Backend Gateway]
                                    |
      +--------------------+--------+--------+--------------------+
      |                    |                 |                    |
[Cryptography]      [IPFS Storage]     [Security & ACL]     [Blockchain]
(AES-256-GCM)       (Kubo / Pinning)   (EIP-191 Auth)       (Web3 & Solidity)
```

### Core Subsystems
1. **Cryptography Subsystem (`encryption/`, `hashing/`)**:
   - Multi-mode authenticated cipher engine supporting `AES-256-GCM` (default), hardened `Chaotic-Tent-Map` (Sine Map + Prime Circulant + Skewed Tent Map), and `Hybrid-Chaotic-AES` with fresh 96-bit CSPRNG nonces per encryption.
   - 128-bit authentication tag verification (GCM / HMAC-SHA256) ensuring immediate detection of ciphertext, metadata, or associated data tampering.
   - SHA-256 cryptographic hashing producing hexadecimal digests and EVM `bytes32` values.
2. **Blockchain Subsystem (`blockchain/`)**:
   - Solidity smart contract (`ImageRegistry.sol`) anchoring image IDs, owners, SHA-256 digests, and IPFS CIDs.
   - On-chain Access Control List (ACL) managing permission grants and revocations.
   - Web3.py client service (`blockchain_service.py`) for RPC transaction dispatching and receipt confirmation.
3. **Storage Subsystem (`storage/`)**:
   - IPFS Kubo RPC client supporting local nodes and pinning providers (Pinata).
   - Invariant guarantee: raw, unencrypted images are strictly prohibited from IPFS ingress.
4. **Security Subsystem (`security/`)**:
   - Wallet identity verification using EIP-191 personal signatures (`personal_sign`).
   - Role-Based Access Control (RBAC) ensuring unauthorized entities cannot obtain or decrypt payloads.
5. **Service Layer (`backend/`, `frontend/`)**:
   - Asynchronous FastAPI REST API exposing validated endpoints with interactive Swagger documentation.
   - Streamlit telemetry dashboard for upload, verification, decryption, and access delegation.

---

## Directory Layout

```
├── backend/                  # FastAPI REST API, routes, and Pydantic schemas
├── blockchain/               # Solidity smart contracts, deploy scripts, Web3 service
│   └── contracts/
│       └── ImageRegistry.sol # On-chain image registry and ACL contract
├── docs/                     # Architectural specifications, security models, status
│   ├── architecture.md       # Layered system architecture
│   ├── data_flow.md          # End-to-end data pipelines
│   ├── module_interfaces.md  # Standard typing and module contracts
│   ├── security_design.md    # Cryptographic threat models & EIP-191 verification
│   ├── setup.md              # Detailed local development guide
│   └── team_status.md        # Engineering team sprint tracking board
├── encryption/               # AES-256-GCM cipher engine and key manager
├── evaluation/               # Statistical metric skeletons (Entropy, NPCR, UACI)
├── frontend/                 # Streamlit web dashboard application
├── hashing/                  # SHA-256 digest computation utilities
├── security/                 # Wallet identity verification and access control
├── storage/                  # IPFS Kubo client and gateway interfaces
├── tests/                    # Pytest test suites (unit, contract, integration)
├── .env.example              # Environment variables template
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

---

## Quickstart Guide

### 1. Installation
Ensure Python 3.10+ is installed:
```bash
# Clone the repository
git clone https://github.com/Vincenzo-sur/<repo-name>.git
cd Smart_encryption_web3

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1   # On Windows
source venv/bin/activate      # On Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
```

### 2. Launch Backend API
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive Swagger API Documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- System Health Check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 3. Launch Frontend Dashboard
```bash
python -m streamlit run frontend/app.py
```
- Dashboard UI: [http://localhost:8501](http://localhost:8501)

### 4. Run Test Suites
```bash
python -m pytest tests/ -v
```

---

## Reviewer & Technical Documentation
Detailed specifications, architectural decisions, and module contracts can be found in `docs/`:
- **[System Architecture](docs/architecture.md)**: Cryptographic and distributed network blueprint.
- **[Module Interfaces](docs/module_interfaces.md)**: Exact parameter types, return signatures, and exception hierarchy.
- **[Security Design](docs/security_design.md)**: Threat modeling, EIP-191 wallet challenge-response protocol.
- **[Team Status Board](docs/team_status.md)**: Internal sprint board tracking module progress.
