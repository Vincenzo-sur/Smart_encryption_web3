"""
Chaotic Image Encryption Orchestrator

Main encryption pipeline combining:
1. Sine Map Permutation (spatial diffusion)
2. Prime Circulant Substitution (value transformation)
3. Tent Map Diffusion (chaos-based XOR diffusion)

This orchestrator converts image bytes to pixel arrays, applies the three-stage
pipeline, and returns encrypted bytes with deterministic metadata generation.
"""

import io
import hashlib
import numpy as np
from typing import Tuple, Union, Optional
from PIL import Image

from encryption.sine_map_permutation import SineMapPermutation
from encryption.prime_circulant_substitution import PrimeCirculantSubstitution
from encryption.tent_map_diffusion import TentMapDiffusion


class ChaoticImageEncryption:
    """
    Orchestrates complete chaotic encryption pipeline for images.

    Pipeline:
    plaintext bytes → Image array (H×W×C) → Sine Permutation →
    Prime Substitution → Tent Diffusion → encrypted array → bytes
    """

    def __init__(self, key: bytes):
        """
        Initialize chaotic encryption pipeline.

        Args:
            key (bytes): 32-byte encryption key.

        Raises:
            ValueError: If key is not 32 bytes.
        """
        if not isinstance(key, (bytes, bytearray)) or len(key) != 32:
            raise ValueError(f"Key must be exactly 32 bytes (got {len(key) if isinstance(key, (bytes, bytearray)) else 'non-bytes'})")

        self.key = key

    def _load_image_to_array(self, image_bytes: Union[bytes, bytearray]) -> Tuple[np.ndarray, Tuple[int, int]]:
        """
        Loads image bytes and converts to numpy array.

        Args:
            image_bytes: Raw image file bytes (PNG, JPG, etc.).

        Returns:
            Tuple of (pixel_array, (height, width)).

        Raises:
            ValueError: If image cannot be loaded.
        """
        try:
            img = Image.open(io.BytesIO(image_bytes))
            # Convert to RGB if necessary
            if img.mode not in ('RGB', 'L', 'RGBA'):
                img = img.convert('RGB')
            # Drop alpha channel if present
            if img.mode == 'RGBA':
                img = img.convert('RGB')

            arr = np.array(img, dtype=np.uint8)
            height, width = arr.shape[:2]

            return arr, (height, width)
        except Exception as exc:
            raise ValueError(f"Failed to load image: {exc}") from exc

    def _array_to_image_bytes(self, arr: np.ndarray) -> bytes:
        """
        Converts numpy array back to image bytes (PNG).

        Args:
            arr: Pixel array (uint8).

        Returns:
            bytes: PNG-encoded image.
        """
        # Ensure array is 3D for PIL
        if len(arr.shape) == 2:
            arr = np.stack([arr] * 3, axis=-1)

        # Clip to valid range
        arr = np.clip(arr, 0, 255).astype(np.uint8)

        img = Image.fromarray(arr, mode='RGB' if arr.shape[2] == 3 else 'L')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        return buf.getvalue()

    def _generate_nonce(self) -> bytes:
        """
        Generates 12-byte nonce from key for consistency.

        Returns:
            bytes: 12-byte nonce.
        """
        # Use deterministic approach: hash of key
        hash_val = hashlib.sha256(self.key + b'nonce').digest()
        return hash_val[:12]

    def _generate_tag(self, ciphertext: bytes) -> bytes:
        """
        Generates authentication tag from ciphertext.

        Args:
            ciphertext: Encrypted image bytes.

        Returns:
            bytes: 16-byte authentication tag.
        """
        # Tag is SHA-256 of (key + ciphertext)
        tag_input = self.key + ciphertext
        tag = hashlib.sha256(tag_input).digest()
        return tag[:16]

    def encrypt(self, image_bytes: Union[bytes, bytearray]) -> Tuple[bytes, bytes, bytes]:
        """
        Encrypts image using chaotic pipeline.

        Args:
            image_bytes: Raw image file bytes.

        Returns:
            Tuple of (ciphertext, nonce, tag).

        Raises:
            ValueError: If image cannot be processed.
        """
        if not isinstance(image_bytes, (bytes, bytearray)):
            raise TypeError(f"image_bytes must be bytes/bytearray, got {type(image_bytes).__name__}")

        if len(image_bytes) == 0:
            raise ValueError("image_bytes cannot be empty")

        # Step 1: Load image to array
        pixel_array, (height, width) = self._load_image_to_array(image_bytes)

        # Step 2: Apply Sine Map Permutation
        sine_permuter = SineMapPermutation(self.key, (height, width))
        permuted = sine_permuter.permute_pixels(pixel_array)

        # Step 3: Apply Prime Circulant Substitution
        substituter = PrimeCirculantSubstitution(self.key)
        substituted = substituter.substitute_pixels(permuted)

        # Step 4: Apply Tent Map Diffusion
        diffuser = TentMapDiffusion(self.key)
        diffused = diffuser.diffuse_image(substituted)

        # Step 5: Convert back to bytes
        ciphertext = self._array_to_image_bytes(diffused)

        # Step 6: Generate nonce and tag
        nonce = self._generate_nonce()
        tag = self._generate_tag(ciphertext)

        return ciphertext, nonce, tag

    def decrypt(self, ciphertext: Union[bytes, bytearray], nonce: bytes, tag: bytes, verify_tag: bool = True) -> bytes:
        """
        Decrypts image using reverse chaotic pipeline.

        Args:
            ciphertext: Encrypted image bytes.
            nonce: 12-byte nonce.
            tag: 16-byte authentication tag.
            verify_tag: If True, verify tag before decryption.

        Returns:
            bytes: Decrypted image bytes.

        Raises:
            ValueError: If parameters are invalid.
            ValueError: If tag verification fails.
        """
        if not isinstance(ciphertext, (bytes, bytearray)):
            raise TypeError(f"ciphertext must be bytes/bytearray, got {type(ciphertext).__name__}")

        if len(nonce) != 12:
            raise ValueError(f"nonce must be 12 bytes (got {len(nonce)})")

        if len(tag) != 16:
            raise ValueError(f"tag must be 16 bytes (got {len(tag)})")

        # Verify tag if requested
        if verify_tag:
            expected_tag = self._generate_tag(bytes(ciphertext))
            if expected_tag != bytes(tag):
                raise ValueError("Authentication tag verification failed: ciphertext has been modified or wrong key")

        # Step 1: Load encrypted image to array
        encrypted_array, (height, width) = self._load_image_to_array(ciphertext)

        # Step 2: Reverse Tent Map Diffusion
        diffuser = TentMapDiffusion(self.key)
        dediffused = diffuser.inverse_diffuse(encrypted_array)

        # Step 3: Reverse Prime Circulant Substitution
        substituter = PrimeCirculantSubstitution(self.key)
        unsubstituted = substituter.inverse_substitute(dediffused)

        # Step 4: Reverse Sine Map Permutation
        sine_permuter = SineMapPermutation(self.key, (height, width))
        depermuted = sine_permuter.inverse_permute(unsubstituted)

        # Step 5: Convert back to bytes
        plaintext = self._array_to_image_bytes(depermuted)

        return plaintext
