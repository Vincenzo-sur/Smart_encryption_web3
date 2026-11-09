"""
AES-256-GCM Encryption Module

Performs authenticated symmetric encryption on raw image bytes.
Generates a fresh 96-bit (12-byte) initialization vector (nonce) for every encryption,
guaranteeing confidentiality, integrity, and authenticity.
"""

import os
import uuid
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple, Union
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EncryptionError(Exception):
    """Exception raised during encryption failures."""
    pass


@dataclass(frozen=True)
class EncryptionResult:
    """
    Immutable container for AES-GCM encryption outputs.
    Allows tuple unpacking: `ciphertext, metadata = result`.
    """
    ciphertext: bytes
    nonce: bytes
    tag: bytes
    key_id: str

    def to_metadata(self) -> Dict[str, Any]:
        """Serializes cryptographic metadata to dictionary with hexadecimal fields."""
        return {
            "algorithm": "AES-256-GCM",
            "nonce": self.nonce.hex(),
            "tag": self.tag.hex(),
            "key_id": self.key_id,
            "ciphertext_length": len(self.ciphertext),
        }

    def __iter__(self):
        """Allows unpacking as `ciphertext, metadata = encrypt_image(...)`."""
        yield self.ciphertext
        yield self.to_metadata()


def encrypt_image(
    image_bytes: Union[bytes, bytearray],
    key: bytes,
    associated_data: Optional[bytes] = None,
    key_id: Optional[str] = None
) -> EncryptionResult:
    """
    Encrypts raw image bytes using AES-256-GCM.

    Args:
        image_bytes (Union[bytes, bytearray]): Raw binary image data.
        key (bytes): 32-byte (256-bit) symmetric key.
        associated_data (Optional[bytes]): Optional unencrypted data authenticated with the tag.
        key_id (Optional[str]): Optional key identifier or session identifier.

    Returns:
        EncryptionResult: Object holding ciphertext, nonce, tag, and key_id.
                         Can also be unpacked as `(ciphertext, metadata)`.

    Raises:
        ValueError: If key is not 32 bytes or image_bytes is empty.
        EncryptionError: If the encryption operation fails.
    """
    if not isinstance(image_bytes, (bytes, bytearray)):
        raise TypeError(f"image_bytes must be bytes or bytearray, got {type(image_bytes).__name__}")
    
    if len(image_bytes) == 0:
        raise ValueError("image_bytes cannot be empty")
        
    if not isinstance(key, (bytes, bytearray)) or len(key) != 32:
        raise ValueError(f"AES-256-GCM key must be exactly 32 bytes (got {len(key) if isinstance(key, (bytes, bytearray)) else 'non-bytes'})")

    try:
        # 96-bit (12-byte) nonce strictly generated per NIST SP 800-38D recommendations
        nonce = os.urandom(12)
        aesgcm = AESGCM(key)
        
        # AESGCM.encrypt returns ciphertext with appended 16-byte authentication tag
        encrypted_payload = aesgcm.encrypt(nonce, bytes(image_bytes), associated_data)
        
        # Separate ciphertext and 16-byte tag for explicit storage and transport
        tag = encrypted_payload[-16:]
        ciphertext = encrypted_payload[:-16]
        
        assigned_key_id = key_id or str(uuid.uuid4())
        
        return EncryptionResult(
            ciphertext=ciphertext,
            nonce=nonce,
            tag=tag,
            key_id=assigned_key_id
        )
    except Exception as exc:
        raise EncryptionError(f"Encryption execution failed: {exc}") from exc
