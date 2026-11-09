# Blockchain Subsystem

## Overview
The Blockchain subsystem anchors image ownership, integrity fingerprints, and access control lists immutably on Ethereum.

## Directory Structure
- `contracts/ImageRegistry.sol`: Solidity ^0.8.20 smart contract.
- `blockchain_service.py`: Web3.py integration service client.
- `deploy.py`: Contract compilation and deployment runner.

## Smart Contract Functions
- `registerImage(bytes32 _imageHash, string _ipfsCid) -> bytes32`: Registers a new image record.
- `getImageDetails(bytes32 _imageId) -> (owner, imageHash, ipfsCid, timestamp, exists)`: View record details.
- `grantAccess(bytes32 _imageId, address _grantee)`: Grants decryption permission to another address.
- `revokeAccess(bytes32 _imageId, address _revokedUser)`: Revokes previously granted access.
- `verifyOwnership(bytes32 _imageId, address _claimant) -> bool`: Checks ownership status.
- `hasAccess(bytes32 _imageId, address _user) -> bool`: Checks if user is owner or authorized delegate.

## Local Ganache Deployment
1. Start Ganache on port `8545`:
   ```bash
   npx ganache --port 8545 --networkId 1337
   ```
2. Run deployment:
   ```bash
   python blockchain/deploy.py
   ```
3. Copy the output contract address into `.env`:
   ```
   IMAGE_REGISTRY_CONTRACT_ADDRESS=0x...
   ```
