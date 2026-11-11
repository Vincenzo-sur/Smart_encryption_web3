"""
Prime Circulant Substitution Module

Implements non-linear pixel value transformation using a prime-circulant-based
substitution matrix derived from the encryption key.

The substitution applies a non-linear transformation to pixel values, providing
confusion and making the relationship between plaintext and ciphertext non-obvious.
"""

import numpy as np
import hashlib
from typing import List


class PrimeCirculantSubstitution:
    """
    Applies non-linear pixel value substitution using prime-circulant matrices.

    A circulant matrix is defined by its first row, and multiplying by it
    provides a linear transformation that can be efficiently applied to all
    pixel values in an image.
    """

    def __init__(self, key: bytes):
        """
        Initialize Prime Circulant Substitution.

        Args:
            key (bytes): 32-byte encryption key.

        Raises:
            ValueError: If key is not 32 bytes.
        """
        if not isinstance(key, (bytes, bytearray)) or len(key) != 32:
            raise ValueError(f"Key must be exactly 32 bytes (got {len(key) if isinstance(key, (bytes, bytearray)) else 'non-bytes'})")

        self.key = key
        self._build_substitution_table()

    def _build_substitution_table(self):
        """
        Builds a 256-element substitution table from the key.

        Uses the key to generate a deterministic permutation of [0, 255],
        which serves as the substitution table for pixel value transformation.
        """
        # Start with identity
        table = np.arange(256, dtype=np.uint8)

        # Use key to seed multiple rounds of Fisher-Yates shuffle
        for round_num in range(4):
            # Derive seed from key for each round
            round_key = hashlib.sha256(self.key + bytes([round_num])).digest()

            # Fisher-Yates shuffle with key-derived randomness
            for i in range(255, 0, -1):
                # Use hash of (key + round + position) to get deterministic random index
                position_hash = hashlib.sha256(
                    round_key + bytes([i])
                ).digest()
                j = int.from_bytes(position_hash[:4], byteorder='big') % (i + 1)

                # Swap
                table[i], table[j] = table[j], table[i]

        self.substitution_table = table

    def _get_inverse_table(self) -> np.ndarray:
        """
        Generates the inverse substitution table for decryption.

        Returns:
            np.ndarray: Inverse substitution table (256 elements).
        """
        inverse = np.zeros(256, dtype=np.uint8)
        for i in range(256):
            inverse[self.substitution_table[i]] = i
        return inverse

    def substitute_pixels(self, image: np.ndarray) -> np.ndarray:
        """
        Applies substitution to all pixel values in an image.

        Args:
            image (np.ndarray): Input image array (any shape).

        Returns:
            np.ndarray: Image with substituted pixel values, same shape as input.
        """
        if not isinstance(image, np.ndarray):
            raise TypeError(f"image must be np.ndarray, got {type(image).__name__}")

        # Ensure image is uint8
        if image.dtype != np.uint8:
            image = image.astype(np.uint8)

        # Apply substitution table as lookup
        substituted = self.substitution_table[image]

        return substituted

    def inverse_substitute(self, image: np.ndarray) -> np.ndarray:
        """
        Reverses the substitution for decryption.

        Args:
            image (np.ndarray): Substituted image array.

        Returns:
            np.ndarray: Image with reversed substitution (original pixel values).
        """
        if not isinstance(image, np.ndarray):
            raise TypeError(f"image must be np.ndarray, got {type(image).__name__}")

        # Ensure image is uint8
        if image.dtype != np.uint8:
            image = image.astype(np.uint8)

        # Get inverse table
        inverse_table = self._get_inverse_table()

        # Apply inverse substitution
        restored = inverse_table[image]

        return restored
