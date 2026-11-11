"""
Chaotic Tent Map Encryption Module

Performs authenticated symmetric encryption on raw image bytes using chaotic systems.
Implements 3-stage pipeline: Sine Map Permutation → Prime Circulant Substitution → Tent Map Diffusion.
Generates deterministic nonce and authentication tag from key for reproducibility.

Maintains API compatibility with previous AES-256-GCM implementation.
"""

import uuid
from dataclasses import dataclass
from typing import Dict, Any, Optional, Union
from encryption.chaotic_image_encryption import ChaoticImageEncryption


class EncryptionError(Exception):
    """Exception raised during encryption failures."""
    pass


@dataclass(frozen=True)
class EncryptionResult:
    """
    Immutable container for Chaotic encryption outputs.
    Allows tuple unpacking: `ciphertext, metadata = result`.
    """
    ciphertext: bytes
    nonce: bytes
    tag: bytes
    key_id: str

    def to_metadata(self) -> Dict[str, Any]:
        """Serializes cryptographic metadata to dictionary with hexadecimal fields."""
        return {
            "algorithm": "Chaotic-Tent-Map",
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
    Encrypts raw image bytes using Chaotic Tent Map encryption.

    Pipeline: Sine Map Permutation → Prime Circulant Substitution → Tent Map Diffusion

    Args:
        image_bytes (Union[bytes, bytearray]): Raw binary image data (PNG, JPG, etc.).
        key (bytes): 32-byte (256-bit) symmetric key.
        associated_data (Optional[bytes]): Optional unencrypted data (not used in chaotic encryption).
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
        raise ValueError(f"Chaotic encryption key must be exactly 32 bytes (got {len(key) if isinstance(key, (bytes, bytearray)) else 'non-bytes'})")

    try:
        # Initialize chaotic encryption pipeline
        cipher = ChaoticImageEncryption(key)

        # Encrypt using chaotic pipeline
        ciphertext, nonce, tag = cipher.encrypt(bytes(image_bytes))

        assigned_key_id = key_id or str(uuid.uuid4())

        return EncryptionResult(
            ciphertext=ciphertext,
            nonce=nonce,
            tag=tag,
            key_id=assigned_key_id
        )
    except ValueError as exc:
        raise ValueError(str(exc)) from exc
    except Exception as exc:
        raise EncryptionError(f"Encryption execution failed: {exc}") from exc
