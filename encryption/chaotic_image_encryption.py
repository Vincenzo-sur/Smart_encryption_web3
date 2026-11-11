"""
Chaotic Image Encryption Orchestrator

Implements a lossless, authenticated 3-stage chaotic encryption pipeline:
1. Sine Map Permutation        (spatial/byte diffusion)
2. Prime Circulant Substitution (non-linear S-box confusion)
3. Tent Map Diffusion          (bidirectional chaotic avalanche)

Operates directly on raw bytes to preserve exact binary equivalence across
all image encodings (PNG, JPEG, WebP, RGBA, grayscale) without container leaks.
Uses fresh 96-bit CSPRNG nonces per encryption and HMAC-SHA256 authentication
with Associated Data (AEAD-style Encrypt-then-MAC).
"""

import hashlib
import hmac
import os
import struct
from typing import Optional, Tuple, Union

import numpy as np

from encryption.prime_circulant_substitution import PrimeCirculantSubstitution
from encryption.sine_map_permutation import SineMapPermutation
from encryption.tent_map_diffusion import TentMapDiffusion


class ChaoticImageEncryption:
    """
    Orchestrates the 3-stage chaotic encryption and Encrypt-then-MAC authentication.
    """

    def __init__(self, key: bytes):
        """
        Initialize chaotic encryption pipeline.

        Args:
            key (bytes): 32-byte master encryption key.

        Raises:
            ValueError: If key is not 32 bytes.
        """
        if not isinstance(key, (bytes, bytearray)) or len(key) != 32:
            got = len(key) if isinstance(key, (bytes, bytearray)) else "non-bytes"
            raise ValueError(f"Key must be exactly 32 bytes (got {got})")

        self.key = bytes(key)

    def _derive_stage_keys(self, nonce: bytes) -> Tuple[bytes, bytes]:
        """Derives domain-separated encryption and authentication subkeys from (key, nonce)."""
        enc_key = hmac.new(self.key, b"chaotic-enc-v2|" + nonce, hashlib.sha256).digest()
        auth_key = hmac.new(self.key, b"chaotic-auth-v2|" + nonce, hashlib.sha256).digest()
        return enc_key, auth_key

    def _compute_auth_tag(
        self,
        auth_key: bytes,
        nonce: bytes,
        ciphertext: bytes,
        associated_data: Optional[bytes] = None
    ) -> bytes:
        """
        Computes 128-bit (16-byte) HMAC-SHA256 authentication tag over
        nonce, length-prefixed associated_data, and ciphertext.
        """
        aad = bytes(associated_data) if associated_data is not None else b""
        mac = hmac.new(auth_key, digestmod=hashlib.sha256)
        mac.update(nonce)
        mac.update(struct.pack(">Q", len(aad)))
        mac.update(aad)
        mac.update(struct.pack(">Q", len(ciphertext)))
        mac.update(ciphertext)
        return mac.digest()[:16]

    def _transform_forward(self, raw_bytes: bytes, nonce: bytes, enc_key: bytes) -> bytes:
        """Executes Sine Permutation -> Prime Circulant Substitution -> Tent Diffusion on raw bytes."""
        data_arr = np.frombuffer(raw_bytes, dtype=np.uint8)

        permuter = SineMapPermutation(enc_key, data_arr.size, nonce=nonce)
        permuted = permuter.permute_pixels(data_arr)

        substituter = PrimeCirculantSubstitution(enc_key, nonce=nonce)
        substituted = substituter.substitute_pixels(permuted)

        diffuser = TentMapDiffusion(enc_key, nonce=nonce)
        diffused = diffuser.diffuse_image(substituted)

        return diffused.tobytes()

    def _transform_inverse(self, cipher_bytes: bytes, nonce: bytes, enc_key: bytes) -> bytes:
        """Executes Inverse Tent Diffusion -> Inverse Substitution -> Inverse Permutation."""
        cipher_arr = np.frombuffer(cipher_bytes, dtype=np.uint8)

        diffuser = TentMapDiffusion(enc_key, nonce=nonce)
        dediffused = diffuser.inverse_diffuse(cipher_arr)

        substituter = PrimeCirculantSubstitution(enc_key, nonce=nonce)
        unsubstituted = substituter.inverse_substitute(dediffused)

        permuter = SineMapPermutation(enc_key, cipher_arr.size, nonce=nonce)
        depermuted = permuter.inverse_permute(unsubstituted)

        return depermuted.tobytes()

    def encrypt_payload(
        self,
        raw_bytes: Union[bytes, bytearray],
        nonce: Optional[bytes] = None
    ) -> Tuple[bytes, bytes]:
        """
        Applies the 3-stage chaotic forward transform without generating a separate MAC tag.
        Used internally by Hybrid-Chaotic-AES where AES-GCM provides the AEAD tag.
        """
        if not isinstance(raw_bytes, (bytes, bytearray)):
            raise TypeError(f"raw_bytes must be bytes/bytearray, got {type(raw_bytes).__name__}")
        if len(raw_bytes) == 0:
            raise ValueError("image_bytes cannot be empty")

        resolved_nonce = bytes(nonce) if nonce is not None else os.urandom(12)
        if len(resolved_nonce) != 12:
            raise ValueError(f"nonce must be 12 bytes (got {len(resolved_nonce)})")

        enc_key, _ = self._derive_stage_keys(resolved_nonce)
        transformed = self._transform_forward(bytes(raw_bytes), resolved_nonce, enc_key)
        return transformed, resolved_nonce

    def decrypt_payload(self, transformed_bytes: Union[bytes, bytearray], nonce: bytes) -> bytes:
        """Reverses `encrypt_payload` for Hybrid-Chaotic-AES after outer AEAD verification."""
        if not isinstance(transformed_bytes, (bytes, bytearray)):
            raise TypeError(f"transformed_bytes must be bytes/bytearray, got {type(transformed_bytes).__name__}")
        if len(transformed_bytes) == 0:
            raise ValueError("ciphertext cannot be empty")
        if len(nonce) != 12:
            raise ValueError(f"nonce must be 12 bytes (got {len(nonce)})")

        enc_key, _ = self._derive_stage_keys(bytes(nonce))
        return self._transform_inverse(bytes(transformed_bytes), bytes(nonce), enc_key)

    def encrypt(
        self,
        image_bytes: Union[bytes, bytearray],
        associated_data: Optional[bytes] = None,
        nonce: Optional[bytes] = None
    ) -> Tuple[bytes, bytes, bytes]:
        """
        Encrypts raw image bytes using the authenticated 3-stage chaotic pipeline.

        Args:
            image_bytes (Union[bytes, bytearray]): Raw binary image data.
            associated_data (Optional[bytes]): Optional unencrypted data authenticated with the tag.
            nonce (Optional[bytes]): Optional 12-byte nonce (generated via os.urandom(12) if omitted).

        Returns:
            Tuple[bytes, bytes, bytes]: (ciphertext, nonce, tag)
        """
        if not isinstance(image_bytes, (bytes, bytearray)):
            raise TypeError(f"image_bytes must be bytes/bytearray, got {type(image_bytes).__name__}")
        if len(image_bytes) == 0:
            raise ValueError("image_bytes cannot be empty")

        resolved_nonce = bytes(nonce) if nonce is not None else os.urandom(12)
        if len(resolved_nonce) != 12:
            raise ValueError(f"nonce must be 12 bytes (got {len(resolved_nonce)})")

        enc_key, auth_key = self._derive_stage_keys(resolved_nonce)
        ciphertext = self._transform_forward(bytes(image_bytes), resolved_nonce, enc_key)
        tag = self._compute_auth_tag(auth_key, resolved_nonce, ciphertext, associated_data)

        return ciphertext, resolved_nonce, tag

    def decrypt(
        self,
        ciphertext: Union[bytes, bytearray],
        nonce: bytes,
        tag: bytes,
        verify_tag: bool = True,
        associated_data: Optional[bytes] = None
    ) -> bytes:
        """
        Verifies HMAC authentication tag and recovers exact original bytes.

        Args:
            ciphertext (Union[bytes, bytearray]): Encrypted bytes.
            nonce (bytes): 12-byte nonce.
            tag (bytes): 16-byte authentication tag.
            verify_tag (bool): If True, verifies tag in constant time before decryption.
            associated_data (Optional[bytes]): Optional associated data bound to tag.

        Returns:
            bytes: Recovered raw bytes matching the original input bit-for-bit.

        Raises:
            ValueError: If parameters are invalid or tag verification fails.
        """
        if not isinstance(ciphertext, (bytes, bytearray)):
            raise TypeError(f"ciphertext must be bytes/bytearray, got {type(ciphertext).__name__}")
        if len(ciphertext) == 0:
            raise ValueError("ciphertext cannot be empty")
        if len(nonce) != 12:
            raise ValueError(f"nonce must be 12 bytes (got {len(nonce)})")
        if len(tag) != 16:
            raise ValueError(f"tag must be 16 bytes (got {len(tag)})")

        enc_key, auth_key = self._derive_stage_keys(bytes(nonce))
        ciphertext_bytes = bytes(ciphertext)

        if verify_tag:
            expected_tag = self._compute_auth_tag(auth_key, bytes(nonce), ciphertext_bytes, associated_data)
            if not hmac.compare_digest(expected_tag, bytes(tag)):
                raise ValueError(
                    "Authentication tag verification failed: ciphertext has been modified or wrong key"
                )

        return self._transform_inverse(ciphertext_bytes, bytes(nonce), enc_key)
