"""
Chaotic Tent Map Decryption Module

Performs authenticated decryption and integrity verification of ciphertext.
Verifies the 128-bit authentication tag before releasing any decrypted image bytes.

Maintains API compatibility with previous AES-256-GCM implementation.
"""

from typing import Dict, Any, Optional, Union
from encryption.chaotic_image_encryption import ChaoticImageEncryption


class DecryptionError(Exception):
    """Base exception for decryption operations."""
    pass


class AuthenticationError(DecryptionError):
    """Raised when authentication tag verification fails (tampered ciphertext or wrong key)."""
    pass


def decrypt_image(
    ciphertext: Union[bytes, bytearray],
    key: bytes,
    metadata: Optional[Union[Dict[str, Any], bytes]] = None,
    nonce: Optional[bytes] = None,
    tag: Optional[bytes] = None,
    associated_data: Optional[bytes] = None
) -> bytes:
    """
    Decrypts and authenticates ciphertext using Chaotic Tent Map encryption.

    Performs 3-stage reverse pipeline: Inverse Tent Diffusion → Inverse Substitution → Inverse Permutation

    Args:
        ciphertext (Union[bytes, bytearray]): Encrypted image bytes.
        key (bytes): 32-byte (256-bit) symmetric key.
        metadata (Optional[Union[Dict[str, Any], bytes]]): Dictionary containing 'nonce' and 'tag' (hex or bytes),
                                                           or direct bytes if nonce is passed here.
        nonce (Optional[bytes]): 12-byte initialization vector (if not provided in metadata).
        tag (Optional[bytes]): 16-byte authentication tag (if not provided in metadata).
        associated_data (Optional[bytes]): Optional unencrypted associated data (not used in chaotic encryption).

    Returns:
        bytes: Fully recovered, authentic raw image bytes.

    Raises:
        AuthenticationError: If tag verification fails due to modified ciphertext, corrupt tag, or wrong key.
        ValueError: If key, nonce, or tag format is invalid.
        DecryptionError: For unexpected runtime decryption faults.
    """
    if not isinstance(ciphertext, (bytes, bytearray)):
        raise TypeError(f"ciphertext must be bytes or bytearray, got {type(ciphertext).__name__}")

    if not isinstance(key, (bytes, bytearray)) or len(key) != 32:
        raise ValueError(f"Chaotic encryption key must be exactly 32 bytes (got {len(key) if isinstance(key, (bytes, bytearray)) else 'non-bytes'})")

    # Resolve nonce and tag from metadata dict or direct arguments
    resolved_nonce: Optional[bytes] = nonce
    resolved_tag: Optional[bytes] = tag

    if isinstance(metadata, dict):
        if "nonce" in metadata:
            raw_nonce = metadata["nonce"]
            resolved_nonce = bytes.fromhex(raw_nonce) if isinstance(raw_nonce, str) else raw_nonce
        if "tag" in metadata:
            raw_tag = metadata["tag"]
            resolved_tag = bytes.fromhex(raw_tag) if isinstance(raw_tag, str) else raw_tag
    elif isinstance(metadata, (bytes, bytearray)) and resolved_nonce is None:
        resolved_nonce = bytes(metadata)

    if resolved_nonce is None or len(resolved_nonce) != 12:
        raise ValueError(f"Chaotic encryption nonce must be exactly 12 bytes (got {len(resolved_nonce) if resolved_nonce else 'None'})")

    if resolved_tag is None or len(resolved_tag) != 16:
        raise ValueError(f"Chaotic encryption tag must be exactly 16 bytes (got {len(resolved_tag) if resolved_tag else 'None'})")

    try:
        # Initialize chaotic decryption pipeline
        cipher = ChaoticImageEncryption(key)

        # Decrypt with tag verification
        decrypted_bytes = cipher.decrypt(
            ciphertext=bytes(ciphertext),
            nonce=resolved_nonce,
            tag=resolved_tag,
            verify_tag=True
        )

        return decrypted_bytes
    except ValueError as exc:
        # Convert ValueError from tag verification failure to AuthenticationError
        if "Authentication tag verification failed" in str(exc) or "modified" in str(exc):
            raise AuthenticationError(
                "Authentication tag verification failed: The ciphertext has been modified or the key is invalid."
            ) from exc
        raise ValueError(str(exc)) from exc
    except AuthenticationError:
        raise
    except Exception as exc:
        raise DecryptionError(f"Decryption operation failed: {exc}") from exc
