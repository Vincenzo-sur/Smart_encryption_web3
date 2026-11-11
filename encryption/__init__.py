"""
Encryption subsystem package.
Exposes AES-256-GCM, hardened Chaotic Tent Map, and Hybrid Chaotic-AES
authenticated encryption, decryption, key management, and chaotic stage primitives.
"""

from encryption.key_manager import generate_encryption_key, key_to_hex, hex_to_key, KeyManagementError
from encryption.encrypt import (
    encrypt_image,
    EncryptionResult,
    EncryptionError,
    ALGORITHM_AES_GCM,
    ALGORITHM_CHAOTIC,
    ALGORITHM_HYBRID,
    SUPPORTED_ALGORITHMS,
)
from encryption.decrypt import decrypt_image, DecryptionError, AuthenticationError
from encryption.sine_map_permutation import SineMapPermutation
from encryption.prime_circulant_substitution import PrimeCirculantSubstitution
from encryption.tent_map_diffusion import TentMapDiffusion
from encryption.chaotic_image_encryption import ChaoticImageEncryption

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
    "KeyManagementError",
    "ALGORITHM_AES_GCM",
    "ALGORITHM_CHAOTIC",
    "ALGORITHM_HYBRID",
    "SUPPORTED_ALGORITHMS",
    "SineMapPermutation",
    "PrimeCirculantSubstitution",
    "TentMapDiffusion",
    "ChaoticImageEncryption",
]
