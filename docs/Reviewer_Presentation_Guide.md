# Project Reviewer Presentation and Viva Defense Guide
## Blockchain-Assisted Secure Image Encryption and Integrity Verification

**Project Lead**: Surya (Vincenzo-sur)  
**Live Hosted URL**: [https://smartencryptionweb3-mhbtweplhqfheouujeagnx.streamlit.app/](https://smartencryptionweb3-mhbtweplhqfheouujeagnx.streamlit.app/)  
**GitHub Repository**: [https://github.com/Vincenzo-sur/Smart_encryption_web3](https://github.com/Vincenzo-sur/Smart_encryption_web3)

---

## 1. The 30-Second Elevator Pitch
> *\"Our project is **Blockchain-Assisted Secure Image Encryption and Integrity Verification**. It solves the critical trade-off between confidentiality and decentralized accessibility for sensitive digital imagery. By combining multi-cipher authenticated encryption (AES-256-GCM and chaotic maps), decentralized IPFS storage, and an immutable Ethereum smart contract, images are encrypted before leaving the client, stored decentralized without exposing plaintext, verified against on-chain hash attestations, and decrypted exclusively by authorized Ethereum wallets.\"*

---

## 2. Problem Statement & Motivation
1. **Centralized Cloud Storage Risks**: Storing sensitive imagery (medical scans, legal evidence, confidential IP) on centralized servers (AWS, Google Drive) introduces single points of failure, insider threats, and vulnerability to silent modification without audit trails.
2. **The Decentralized Storage Paradox**: Decentralized networks like IPFS solve availability and single points of failure, but IPFS is **publicly readable by default** -- anyone with a Content Identifier (CID) can view raw files.
3. **The Zero-Trust Solution**: Enforce a strict software invariant where raw images are never sent to IPFS. The blockchain anchors a 32-byte cryptographic SHA-256 hash and governs on-chain Access Control Lists (ACL), making tampering detectable with zero tolerance.

---

## 3. The 4-Tier System Architecture

`
[Client / Streamlit UI]  <--->  [FastAPI Backend Gateway]
                                         |
          +--------------------+---------+---------+--------------------+
          |                    |                   |                    |
   [Cryptography]       [Decentralized]     [Smart Contract]     [Wallet Identity]
(AES-GCM / Chaos /    (IPFS Storage Kubo)    (ImageRegistry.sol  (EIP-191 Signature
     Hybrid)                                   on Ethereum)         Verification)
`

1. **Tier 1: Multi-Cipher Cryptography Subsystem**: Supports AES-256-GCM (NIST FIPS AEAD standard), Chaotic-Tent-Map (Sine Map permutation + Prime Circulant substitution + Skewed Tent Map diffusion), and Hybrid-Chaotic-AES. Every encryption uses fresh 96-bit CSPRNG nonces and 128-bit authentication tags to ensure immediate tamper detection.
2. **Tier 2: Decentralized Storage Layer (IPFS)**: Only encrypted ciphertext is published to IPFS. IPFS returns a deterministic Content Identifier (CID) used for content-addressed retrieval.
3. **Tier 3: Smart Contract Ledger (ImageRegistry.sol on Ethereum)**: Anchors image IDs, owner wallet addresses, SHA-256 digests, and IPFS CIDs on-chain. Provides an on-chain Access Control List (ACL) with grantAccess() and evokeAccess() methods.
4. **Tier 4: Web3 Identity & Access Control Layer**: Uses EIP-191 cryptographic signatures (personal_sign) to authenticate user wallets using elliptic curve public key recovery (ecrecover), completely eliminating passwords.

---

## 4. Step-by-Step Live Demonstration Script

**Live URL to Open**: [https://smartencryptionweb3-mhbtweplhqfheouujeagnx.streamlit.app/](https://smartencryptionweb3-mhbtweplhqfheouujeagnx.streamlit.app/)

### Step 1: Upload & Encrypt (Tab 1)
* **Action**: Select an image file (PNG/JPEG/WebP) and choose an algorithm (Chaotic-Tent-Map or AES-256-GCM).
* **Action**: Leave the custom key field blank and click **\"Encrypt & Register on Blockchain\"**.
* **What to Say**: *\"The system encrypts the raw image client-side, computes its SHA-256 fingerprint, stores ciphertext on IPFS, and registers the hash on Ethereum. The secret key is shown in the yellow box and never leaves client memory.\"*

### Step 2: Cross-Check Integrity (Tab 2)
* **Action**: Paste the Image ID and click **\"Verify Integrity\"**.
* **What to Say**: *\"The backend queries the ciphertext, recalculates its SHA-256 hash, and compares it with the immutable blockchain ledger record. Notice the green confirmation: Cryptographic integrity verified.\"*

### Step 3: Authorized Decryption (Tab 2)
* **Action**: Paste Key, Nonce, and Tag, then click **\"Decrypt Image\"**.
* **What to Say**: *\"The system evaluates smart contract permissions, verifies the 128-bit authentication tag, and recovers the exact original image bit-for-bit with 100% fidelity.\"*

### Step 4: Prove Tamper-Proofing (Zero-Trust Security)
* **Action**: Change just 1 character in the Key or Tag, then click **\"Decrypt Image\"** again.
* **What to Say**: *\"Notice that altering even a single character causes an immediate Authentication Failed error. The AEAD engine has zero tolerance for modified ciphertext or incorrect keys.\"*

---

## 5. Tough Reviewer Questions & Model Answers

### Q1: \"Why not store the entire image directly on the blockchain?\"
> **Answer**: *\"Storing large binary files on the Ethereum blockchain is cost-prohibitive due to gas fees. Our hybrid design stores the heavy encrypted payload off-chain on IPFS and keeps only 32-byte hashes (ytes32), CIDs, and ACL permissions on-chain. This provides blockchain immutability at minimal cost.\"*

### Q2: \"Why use Chaotic Encryption instead of just standard AES?\"
> **Answer**: *\"Digital images have high adjacent pixel correlation ( \approx 0.99$) and massive data redundancy. Our Chaotic Tent Map engine uses non-linear dynamical permutation (Sine Map) and substitution (Prime Circulant) to completely eliminate spatial correlation ( \approx 0.0008$) and achieve near-ideal Shannon Entropy (7.996 bits/byte) and high NPCR (>99.6%).\"*

### Q3: \"How is user authentication handled without passwords?\"
> **Answer**: *\"We follow the Web3 EIP-191 standard. The server issues a cryptographically random, timestamped challenge. The user signs it with their private key in their Ethereum wallet. The backend verifies the address using elliptic curve recovery (ecrecover). There are no stored passwords.\"*

### Q4: \"How thoroughly has this project been tested?\"
> **Answer**: *\"The project has an automated test suite of 49 test cases with 100% pass rate covering AES-GCM, chaotic permutations, hashing, Web3 smart contract interactions, and FastAPI integration.\"*

---

## 6. Current Project Status & Milestones
* **Current Milestone**: Phase 2 Complete (~60% Progress). 100% of core cryptography, smart contracts, FastAPI REST backend, Streamlit dashboard, automated tests, and live cloud hosting are operational.
* **Next Roadmap (Phase 3 & 4)**: Deploy contract to Sepolia testnet with MetaMask in-browser signing, remote Pinata IPFS pinning credentials, and ECIES public-key wrapping for automated key sharing.
