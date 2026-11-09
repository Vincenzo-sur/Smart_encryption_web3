"""
Encryption subsystem package.
Exposes AES-256-GCM authenticated encryption, decryption, and key management utilities.
"""

from encryption.key_manager import generate_encryption_key, key_to_hex, hex_to_key, KeyManagementError
from encryption.encrypt import encrypt_image, EncryptionResult, EncryptionError
from encryption.decrypt import decrypt_image, DecryptionError, AuthenticationError

__all__ = [
    "generate_encryption_key",
    "key_to_hex",
    "hex_to_key",
    "encrypt_image",
    "decrypt_image",
    "EncryptionResult",
    "EncryptionError",
    "DecryptionError",
    "AuthenticationError",
    "KeyManagementError"
]
