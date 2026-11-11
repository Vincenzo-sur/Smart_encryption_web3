# Module Interfaces & Common Data Contracts

This document establishes the strict contract signatures, types, and exceptions across all subsystems. All modules must adhere to these interfaces without deviation.

---

## 1. Cryptography Subsystem (`encryption/`)

### 1.1 Data Structures
```python
from dataclasses import dataclass
from typing import Dict, Any

@dataclass(frozen=True)
class EncryptionResult:
    ciphertext: bytes
    nonce: bytes          # 12-byte CSPRNG IV
    tag: bytes            # 16-byte authentication tag (GCM or HMAC-SHA256)
    key_id: str           # Unique identifier or reference for key management
    algorithm: str = "AES-256-GCM"

    def to_metadata(self) -> Dict[str, Any]:
        """Serializes algorithm, nonce, tag, key_id, and length for storage/transport."""
        return {
            "algorithm": self.algorithm,
            "nonce": self.nonce.hex(),
            "tag": self.tag.hex(),
            "key_id": self.key_id,
            "ciphertext_length": len(self.ciphertext),
        }
```

### 1.2 Functions
#### `generate_encryption_key(length: int = 32) -> bytes`
- **Description**: Generates a cryptographically strong 256-bit (32-byte) symmetric key using `secrets.token_bytes`.
- **Returns**: `bytes` of length 32.
- **Exceptions**: `ValueError` / `KeyManagementError` on invalid length or CSPRNG failure.

#### `encrypt_image(image_bytes: bytes, key: bytes, associated_data: Optional[bytes] = None, key_id: Optional[str] = None, algorithm: str = "AES-256-GCM") -> EncryptionResult`
- **Description**: Encrypts raw image bytes using the selected cipher (`AES-256-GCM`, `Chaotic-Tent-Map`, or `Hybrid-Chaotic-AES`) with a fresh 12-byte CSPRNG nonce.
- **Parameters**:
  - `image_bytes`: `bytes` representing the raw binary image.
  - `key`: `bytes` of length 32.
  - `associated_data`: optional `bytes` bound to the authentication tag.
  - `algorithm`: cipher mode identifier.
- **Returns**: `EncryptionResult` containing ciphertext, nonce, tag, key_id, and algorithm.
- **Exceptions**: `EncryptionError`, `ValueError` if key length != 32 or algorithm is unsupported.

#### `decrypt_image(ciphertext: bytes, key: bytes, metadata: Optional[Union[Dict[str, Any], bytes]] = None, nonce: Optional[bytes] = None, tag: Optional[bytes] = None, associated_data: Optional[bytes] = None, algorithm: Optional[str] = None) -> bytes`
- **Description**: Authenticates and decrypts ciphertext, dispatching by explicit `algorithm` or `metadata["algorithm"]` (defaults to `AES-256-GCM`).
- **Returns**: Original `bytes` of the image (exact bit-for-bit recovery).
- **Exceptions**: `AuthenticationError` (if ciphertext, tag, AAD, or key fails verification), `DecryptionError`, `ValueError`.

---

## 2. Hashing Subsystem (`hashing/`)

#### `calculate_hash(file_bytes: bytes) -> str`
- **Description**: Computes the SHA-256 digest of binary content.
- **Parameters**: `file_bytes`: `bytes`.
- **Returns**: `str` lowercase hexadecimal representation (64 characters).

#### `calculate_hash_bytes(file_bytes: bytes) -> bytes`
- **Description**: Computes SHA-256 returning raw 32 bytes (`bytes32` for EVM smart contracts).
- **Parameters**: `file_bytes`: `bytes`.
- **Returns**: `bytes` of length 32.

---

## 3. Storage Subsystem (`storage/`)

### 3.1 Exceptions
- `IPFSConnectionError`: Raised when the IPFS endpoint is unreachable or misconfigured.
- `IPFSUploadError`: Raised when upload fails or CID is invalid.
- `IPFSRetrievalError`: Raised when retrieval of content fails or payload is empty.

### 3.2 Functions
#### `upload_to_ipfs(encrypted_bytes: bytes) -> str`
- **Description**: Publishes encrypted ciphertext to the configured IPFS node/pinning service.
- **Parameters**: `encrypted_bytes`: `bytes`.
- **Returns**: `str` IPFS CID.
- **Exceptions**: `IPFSConnectionError`, `IPFSUploadError`.

#### `retrieve_from_ipfs(cid: str) -> bytes`
- **Description**: Fetches the encrypted payload from IPFS given its CID.
- **Parameters**: `cid`: `str`.
- **Returns**: `bytes` of encrypted payload.
- **Exceptions**: `IPFSConnectionError`, `IPFSRetrievalError`.

---

## 4. Blockchain Subsystem (`blockchain/`)

### 4.1 Data Structures
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class BlockchainImageRecord:
    image_id: str
    owner: str
    image_hash: str
    ipfs_cid: str
    timestamp: int
    exists: bool
```

### 4.2 Functions
#### `register_image(image_hash: str, ipfs_cid: str, sender_address: str, private_key: Optional[str] = None) -> dict`
- **Description**: Submits transaction to `ImageRegistry.sol` to record the image hash and IPFS CID.
- **Returns**: `dict` containing `image_id`, `transaction_hash`, `block_number`.
- **Exceptions**: `BlockchainTransactionError`, `ContractError`.

#### `get_image_details(image_id: str) -> BlockchainImageRecord`
- **Description**: Queries `ImageRegistry.sol` view function for registered metadata.
- **Returns**: `BlockchainImageRecord`.
- **Exceptions**: `ImageNotFoundError`, `BlockchainQueryError`.

#### `grant_access(image_id: str, user_address: str, sender_address: str, private_key: str) -> str`
- **Description**: Authorizes `user_address` on-chain to access `image_id`.
- **Returns**: `str` transaction hash.

#### `revoke_access(image_id: str, user_address: str, sender_address: str, private_key: str) -> str`
- **Description**: Revokes on-chain access for `user_address`.
- **Returns**: `str` transaction hash.

---

## 5. Security & Access Control (`security/`)

#### `verify_signature(message: str, signature: str, expected_address: str) -> bool`
- **Description**: Recovers signer address from an EIP-191 personal sign payload and validates against `expected_address`.
- **Parameters**:
  - `message`: `str` challenge text.
  - `signature`: `str` hex-encoded signature (`0x...`).
  - `expected_address`: `str` checksummed Ethereum address.
- **Returns**: `bool` (True if signature matches expected address).

#### `check_permission(image_id: str, user_address: str) -> bool`
- **Description**: Verifies if `user_address` is the owner or an authorized recipient on-chain.
- **Returns**: `bool`.

---

## 6. Service / REST API Schemas (`backend/schemas/`)

- `POST /upload`: Multipart upload (image binary, owner address, signature).
  - Returns: `{"image_id": str, "ipfs_cid": str, "image_hash": str, "tx_hash": str}`
- `GET /images/{image_id}`:
  - Returns: `BlockchainImageRecord` representation.
- `GET /images/{image_id}/verify`:
  - Returns: `{"image_id": str, "is_valid": bool, "ipfs_hash": str, "ledger_hash": str, "match": bool}`
- `POST /images/{image_id}/decrypt`:
  - Body: `{"requester_address": str, "signature": str, "challenge": str}`
  - Returns: Binary image stream or `403 Forbidden`.
