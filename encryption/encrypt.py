"""
Image Encryption Module

Supports three authenticated symmetric cipher modes:
- `AES-256-GCM` (default): OpenSSL-backed AEAD cipher per NIST SP 800-38D.
- `Chaotic-Tent-Map`: Hardened 3-stage chaotic pipeline (Sine Map Permutation ->
  Prime Circulant Substitution -> Skewed Tent Map Diffusion) with HMAC-SHA256.
- `Hybrid-Chaotic-AES`: Defense-in-depth composition applying the 3-stage chaotic
  confusion/diffusion layer followed by AES-256-GCM authenticated encryption.

Every encryption generates a fresh 96-bit (12-byte) CSPRNG nonce.
"""

import hashlib
import hmac
import os
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, Union

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from encryption.chaotic_image_encryption import ChaoticImageEncryption

ALGORITHM_AES_GCM = "AES-256-GCM"
ALGORITHM_CHAOTIC = "Chaotic-Tent-Map"
ALGORITHM_HYBRID = "Hybrid-Chaotic-AES"
SUPPORTED_ALGORITHMS = (ALGORITHM_AES_GCM, ALGORITHM_CHAOTIC, ALGORITHM_HYBRID)


class EncryptionError(Exception):
    """Exception raised during encryption failures."""
    pass


@dataclass(frozen=True)
class EncryptionResult:
    """
    Immutable container for authenticated encryption outputs.
    Allows tuple unpacking: `ciphertext, metadata = result`.
    """
    ciphertext: bytes
    nonce: bytes
    tag: bytes
    key_id: str
    algorithm: str = ALGORITHM_AES_GCM

    def to_metadata(self) -> Dict[str, Any]:
        """Serializes cryptographic metadata to dictionary with hexadecimal fields."""
        return {
            "algorithm": self.algorithm,
            "nonce": self.nonce.hex(),
            "tag": self.tag.hex(),
            "key_id": self.key_id,
            "ciphertext_length": len(self.ciphertext),
        }

    def __iter__(self):
        """Allows unpacking as `ciphertext, metadata = encrypt_image(...)`."""
        yield self.ciphertext
        yield self.to_metadata()


def _derive_hybrid_keys(master_key: bytes, nonce: bytes) -> Tuple[bytes, bytes]:
    """Derives independent 256-bit chaotic and AES subkeys for Hybrid-Chaotic-AES."""
    chaotic_key = hmac.new(master_key, b"hybrid-chaotic-v1|" + nonce, hashlib.sha256).digest()
    aes_key = hmac.new(master_key, b"hybrid-aes-v1|" + nonce, hashlib.sha256).digest()
    return chaotic_key, aes_key


def encrypt_image(
    image_bytes: Union[bytes, bytearray],
    key: bytes,
    associated_data: Optional[bytes] = None,
    key_id: Optional[str] = None,
    algorithm: str = ALGORITHM_AES_GCM
) -> EncryptionResult:
    """
    Encrypts raw image bytes using the selected authenticated cipher mode.

    Args:
        image_bytes (Union[bytes, bytearray]): Raw binary image data.
        key (bytes): 32-byte (256-bit) symmetric key.
        associated_data (Optional[bytes]): Optional unencrypted data authenticated with the tag.
        key_id (Optional[str]): Optional key identifier or session identifier.
        algorithm (str): Cipher mode ('AES-256-GCM', 'Chaotic-Tent-Map', or 'Hybrid-Chaotic-AES').

    Returns:
        EncryptionResult: Object holding ciphertext, nonce, tag, key_id, and algorithm.
                         Can also be unpacked as `(ciphertext, metadata)`.

    Raises:
        ValueError: If key is not 32 bytes, image_bytes is empty, or algorithm is unsupported.
        EncryptionError: If the encryption operation fails.
    """
    if not isinstance(image_bytes, (bytes, bytearray)):
        raise TypeError(f"image_bytes must be bytes or bytearray, got {type(image_bytes).__name__}")

    if len(image_bytes) == 0:
        raise ValueError("image_bytes cannot be empty")

    if not isinstance(key, (bytes, bytearray)) or len(key) != 32:
        got = len(key) if isinstance(key, (bytes, bytearray)) else "non-bytes"
        raise ValueError(f"Encryption key must be exactly 32 bytes (got {got})")

    if algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError(
            f"Unsupported algorithm '{algorithm}'. Expected one of {SUPPORTED_ALGORITHMS}"
        )

    key_bytes = bytes(key)
    raw_bytes = bytes(image_bytes)

    try:
        nonce = os.urandom(12)

        if algorithm == ALGORITHM_AES_GCM:
            aesgcm = AESGCM(key_bytes)
            encrypted_payload = aesgcm.encrypt(nonce, raw_bytes, associated_data)
            tag = encrypted_payload[-16:]
            ciphertext = encrypted_payload[:-16]

        elif algorithm == ALGORITHM_CHAOTIC:
            cipher = ChaoticImageEncryption(key_bytes)
            ciphertext, nonce, tag = cipher.encrypt(
                raw_bytes,
                associated_data=associated_data,
                nonce=nonce
            )

        else:  # ALGORITHM_HYBRID
            chaotic_key, aes_key = _derive_hybrid_keys(key_bytes, nonce)
            chaotic_payload, _ = ChaoticImageEncryption(chaotic_key).encrypt_payload(
                raw_bytes,
                nonce=nonce
            )
            aesgcm = AESGCM(aes_key)
            encrypted_payload = aesgcm.encrypt(nonce, chaotic_payload, associated_data)
            tag = encrypted_payload[-16:]
            ciphertext = encrypted_payload[:-16]

        assigned_key_id = key_id or str(uuid.uuid4())

        return EncryptionResult(
            ciphertext=ciphertext,
            nonce=nonce,
            tag=tag,
            key_id=assigned_key_id,
            algorithm=algorithm,
        )
    except ValueError:
        raise
    except Exception as exc:
        raise EncryptionError(f"Encryption execution failed: {exc}") from exc
