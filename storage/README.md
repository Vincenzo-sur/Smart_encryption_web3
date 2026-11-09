# Storage Subsystem: IPFS Integration

## Overview
The storage module manages the decentralized persistence of encrypted image ciphertext via the InterPlanetary File System (IPFS).

## Invariants & Design Principles
1. **Confidentiality First**: Only encrypted ciphertext bytes may ever be sent to IPFS. Unencrypted images are strictly blocked by module typing and pipeline design.
2. **Deterministic Content Addressing**: Payloads are addressed by their cryptographic Content Identifier (CID).
3. **No Silent Storage Fallbacks**: If IPFS is offline, the service raises an explicit `IPFSConnectionError` rather than silently saving to the local filesystem.

## Setting Up IPFS

### Option A: Local Kubo Node
1. Install Kubo from [docs.ipfs.tech](https://docs.ipfs.tech/install/command-line-quick-start/).
2. Run:
   ```bash
   ipfs init
   ipfs daemon
   ```
3. Default RPC endpoint: `http://127.0.0.1:5001/api/v0`.

### Option B: Remote Pinning Service (Pinata)
Set variables in `.env`:
```env
IPFS_API_URL=https://api.pinata.cloud
IPFS_PROJECT_ID=your_api_key
IPFS_PROJECT_SECRET=your_secret_api_key
```
