"""
Encryption subsystem package.
Exposes Chaotic Tent Map authenticated encryption, decryption, key management,
and chaotic components (Sine Map, Prime Circulant, Tent Map).
"""

from encryption.key_manager import generate_encryption_key, key_to_hex, hex_to_key, KeyManagementError
from encryption.encrypt import encrypt_image, EncryptionResult, EncryptionError
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
    "SineMapPermutation",
    "PrimeCirculantSubstitution",
    "TentMapDiffusion",
    "ChaoticImageEncryption"
]
