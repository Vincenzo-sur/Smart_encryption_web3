"""
Image Decryption Module

Performs authenticated decryption and integrity verification across all
supported cipher modes (`AES-256-GCM`, `Chaotic-Tent-Map`, `Hybrid-Chaotic-AES`).
Verifies the 128-bit authentication tag before releasing any decrypted bytes.
"""

from typing import Any, Dict, Optional, Union

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from encryption.chaotic_image_encryption import ChaoticImageEncryption
from encryption.encrypt import (
    ALGORITHM_AES_GCM,
    ALGORITHM_CHAOTIC,
    ALGORITHM_HYBRID,
    SUPPORTED_ALGORITHMS,
    _derive_hybrid_keys,
)


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
    associated_data: Optional[bytes] = None,
    algorithm: Optional[str] = None
) -> bytes:
    """
    Decrypts and authenticates ciphertext using the matching cipher algorithm.

    Args:
        ciphertext (Union[bytes, bytearray]): Encrypted image bytes.
        key (bytes): 32-byte (256-bit) symmetric key.
        metadata (Optional[Union[Dict[str, Any], bytes]]): Metadata dictionary containing
            'nonce', 'tag', and optional 'algorithm', or direct nonce bytes.
        nonce (Optional[bytes]): 12-byte initialization vector (if not provided in metadata).
        tag (Optional[bytes]): 16-byte authentication tag (if not provided in metadata).
        associated_data (Optional[bytes]): Optional unencrypted associated data authenticated with tag.
        algorithm (Optional[str]): Explicit algorithm override. Defaults to metadata['algorithm']
            or 'AES-256-GCM'.

    Returns:
        bytes: Fully recovered, authentic raw image bytes.

    Raises:
        AuthenticationError: If tag verification fails due to modified ciphertext, corrupt tag, or wrong key.
        ValueError: If key, nonce, tag, or algorithm format is invalid.
        DecryptionError: For unexpected runtime decryption faults.
    """
    if not isinstance(ciphertext, (bytes, bytearray)):
        raise TypeError(f"ciphertext must be bytes or bytearray, got {type(ciphertext).__name__}")

    if not isinstance(key, (bytes, bytearray)) or len(key) != 32:
        got = len(key) if isinstance(key, (bytes, bytearray)) else "non-bytes"
        raise ValueError(f"Encryption key must be exactly 32 bytes (got {got})")

    resolved_nonce: Optional[bytes] = nonce
    resolved_tag: Optional[bytes] = tag
    resolved_algorithm: Optional[str] = algorithm

    if isinstance(metadata, dict):
        if resolved_nonce is None and "nonce" in metadata:
            raw_nonce = metadata["nonce"]
            resolved_nonce = bytes.fromhex(raw_nonce) if isinstance(raw_nonce, str) else raw_nonce
        if resolved_tag is None and "tag" in metadata:
            raw_tag = metadata["tag"]
            resolved_tag = bytes.fromhex(raw_tag) if isinstance(raw_tag, str) else raw_tag
        if resolved_algorithm is None and "algorithm" in metadata:
            resolved_algorithm = metadata["algorithm"]
    elif isinstance(metadata, (bytes, bytearray)) and resolved_nonce is None:
        resolved_nonce = bytes(metadata)

    if resolved_algorithm is None:
        resolved_algorithm = ALGORITHM_AES_GCM

    if resolved_algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError(
            f"Unsupported algorithm '{resolved_algorithm}'. Expected one of {SUPPORTED_ALGORITHMS}"
        )

    if resolved_nonce is None or len(resolved_nonce) != 12:
        got = len(resolved_nonce) if resolved_nonce else "None"
        raise ValueError(f"Encryption nonce must be exactly 12 bytes (got {got})")

    if resolved_tag is None or len(resolved_tag) != 16:
        got = len(resolved_tag) if resolved_tag else "None"
        raise ValueError(f"Encryption tag must be exactly 16 bytes (got {got})")

    key_bytes = bytes(key)
    cipher_bytes = bytes(ciphertext)
    nonce_bytes = bytes(resolved_nonce)
    tag_bytes = bytes(resolved_tag)

    try:
        if resolved_algorithm == ALGORITHM_AES_GCM:
            aesgcm = AESGCM(key_bytes)
            combined_payload = cipher_bytes + tag_bytes
            return aesgcm.decrypt(nonce_bytes, combined_payload, associated_data)

        if resolved_algorithm == ALGORITHM_CHAOTIC:
            cipher = ChaoticImageEncryption(key_bytes)
            return cipher.decrypt(
                ciphertext=cipher_bytes,
                nonce=nonce_bytes,
                tag=tag_bytes,
                verify_tag=True,
                associated_data=associated_data,
            )

        # ALGORITHM_HYBRID
        chaotic_key, aes_key = _derive_hybrid_keys(key_bytes, nonce_bytes)
        aesgcm = AESGCM(aes_key)
        chaotic_payload = aesgcm.decrypt(nonce_bytes, cipher_bytes + tag_bytes, associated_data)
        return ChaoticImageEncryption(chaotic_key).decrypt_payload(chaotic_payload, nonce_bytes)

    except InvalidTag as exc:
        raise AuthenticationError(
            "Authentication tag verification failed: The ciphertext has been modified or the key is invalid."
        ) from exc
    except AuthenticationError:
        raise
    except ValueError as exc:
        if "Authentication tag verification failed" in str(exc) or "modified" in str(exc):
            raise AuthenticationError(
                "Authentication tag verification failed: The ciphertext has been modified or the key is invalid."
            ) from exc
        raise ValueError(str(exc)) from exc
    except Exception as exc:
        raise DecryptionError(f"Decryption operation failed: {exc}") from exc
