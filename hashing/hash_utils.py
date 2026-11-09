"""
Cryptographic Hashing Utilities

Provides functions to compute SHA-256 digests over binary data (images, ciphertext, metadata).
Outputs standard lowercase hexadecimal strings as well as raw 32-byte sequences compatible
with Ethereum EVM bytes32 smart contract types.
"""

import hashlib
from typing import Union


def calculate_hash(file_bytes: Union[bytes, bytearray]) -> str:
    """
    Calculates the SHA-256 cryptographic digest of a binary byte sequence.

    Args:
        file_bytes (Union[bytes, bytearray]): Raw bytes to hash.

    Returns:
        str: 64-character lowercase hexadecimal SHA-256 digest.

    Raises:
        TypeError: If input is not bytes or bytearray.
    """
    if not isinstance(file_bytes, (bytes, bytearray)):
        raise TypeError(f"Expected bytes-like object, got {type(file_bytes).__name__}")
    
    hasher = hashlib.sha256()
    hasher.update(file_bytes)
    return hasher.hexdigest().lower()


def calculate_hash_bytes(file_bytes: Union[bytes, bytearray]) -> bytes:
    """
    Calculates the SHA-256 cryptographic digest returning raw 32 bytes (bytes32).
    Directly compatible with Solidity bytes32 mappings and event arguments.

    Args:
        file_bytes (Union[bytes, bytearray]): Raw bytes to hash.

    Returns:
        bytes: 32-byte binary digest.

    Raises:
        TypeError: If input is not bytes or bytearray.
    """
    if not isinstance(file_bytes, (bytes, bytearray)):
        raise TypeError(f"Expected bytes-like object, got {type(file_bytes).__name__}")
    
    hasher = hashlib.sha256()
    hasher.update(file_bytes)
    return hasher.digest()
