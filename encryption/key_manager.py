"""
Cryptographic Key Management Module

Responsible for cryptographically secure pseudorandom key generation, key validation,
and key representation formatting.
"""

import os
import secrets
from typing import Optional


class KeyManagementError(Exception):
    """Base exception for cryptographic key management operations."""
    pass


def generate_encryption_key(length_bytes: int = 32) -> bytes:
    """
    Generates a cryptographically strong symmetric key using OS CSPRNG.
    Default length is 32 bytes (256 bits) for AES-256-GCM.

    Args:
        length_bytes (int): Length of the key in bytes. Defaults to 32.

    Returns:
        bytes: Raw key bytes.

    Raises:
        ValueError: If key length is not 16, 24, or 32 bytes.
        KeyManagementError: If CSPRNG fails.
    """
    if length_bytes not in (16, 24, 32):
        raise ValueError(f"AES key length must be 16, 24, or 32 bytes (got {length_bytes})")
    
    try:
        return secrets.token_bytes(length_bytes)
    except Exception as exc:
        raise KeyManagementError(f"Failed to generate secure random key: {exc}") from exc


def key_to_hex(key: bytes) -> str:
    """Encodes raw key bytes to a lowercase hexadecimal string."""
    if not isinstance(key, (bytes, bytearray)):
        raise TypeError("Key must be a bytes-like object")
    return key.hex().lower()


def hex_to_key(key_hex: str) -> bytes:
    """Decodes a hexadecimal string to raw key bytes with validation."""
    if not isinstance(key_hex, str):
        raise TypeError("Key hex must be a string")
    
    clean_hex = key_hex.strip()
    if clean_hex.startswith("0x") or clean_hex.startswith("0X"):
        clean_hex = clean_hex[2:]
        
    try:
        key_bytes = bytes.fromhex(clean_hex)
    except ValueError as exc:
        raise KeyManagementError(f"Invalid hexadecimal key string: {exc}") from exc
        
    if len(key_bytes) not in (16, 24, 32):
        raise ValueError(f"Decoded key length must be 16, 24, or 32 bytes (got {len(key_bytes)})")
        
    return key_bytes
