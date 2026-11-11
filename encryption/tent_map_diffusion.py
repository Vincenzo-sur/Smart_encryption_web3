"""
Tent Map Diffusion Module

Implements chaotic diffusion using the Tent Map chaos system.
The Tent Map is defined as: x_{i+1} = 2*x_i if x_i < 0.5 else 2*(1 - x_i)

Diffusion spreads the effect of each plaintext bit across the entire ciphertext,
ensuring that a single bit change in plaintext causes significant changes in ciphertext.
Uses XOR operation: c[i] = s[i] ⊕ d[i] ⊕ c[i-1]
where s[i] is substituted pixel, d[i] is diffusion value, and c[i-1] is previous ciphertext.
"""

import numpy as np
import hashlib
from typing import Tuple


class TentMapDiffusion:
    """
    Applies chaotic diffusion using Tent Map to achieve strict avalanche criterion.

    The Tent Map is ergodic and sensitive to initial conditions, making it ideal
    for cryptographic diffusion. Each pixel's ciphertext depends on all previous
    pixels due to the chain-based XOR operation.
    """

    def __init__(self, key: bytes):
        """
        Initialize Tent Map Diffusion.

        Args:
            key (bytes): 32-byte encryption key.

        Raises:
            ValueError: If key is not 32 bytes.
        """
        if not isinstance(key, (bytes, bytearray)) or len(key) != 32:
            raise ValueError(f"Key must be exactly 32 bytes (got {len(key) if isinstance(key, (bytes, bytearray)) else 'non-bytes'})")

        self.key = key
        self._derive_parameters()

    def _derive_parameters(self):
        """
        Derives Tent Map initial condition (x0) from the encryption key.

        The x0 value should be in (0, 1) excluding 0 and 1 to ensure proper chaos.
        """
        # Derive x0 from key hash
        hash_val = hashlib.sha256(self.key).digest()
        x0_raw = int.from_bytes(hash_val[:8], byteorder='big') / (2**64)
        # Ensure x0 is in (0.1, 0.9) range for stability
        self.x0 = 0.1 + x0_raw * 0.8

    def _generate_tent_sequence(self, length: int) -> np.ndarray:
        """
        Generates chaotic diffusion sequence using Tent Map.

        Args:
            length (int): Number of diffusion values to generate.

        Returns:
            np.ndarray: Array of chaotic values scaled to [0, 255].
        """
        sequence = np.zeros(length, dtype=np.uint8)
        x = self.x0

        for i in range(length):
            # Tent Map iteration
            if x < 0.5:
                x = 2.0 * x
            else:
                x = 2.0 * (1.0 - x)

            # Convert to uint8 [0, 255]
            diffusion_val = int(x * 255) & 0xFF
            sequence[i] = diffusion_val

        return sequence

    def _flatten_image(self, image: np.ndarray) -> Tuple[np.ndarray, Tuple]:
        """
        Flattens image to 1D for diffusion while preserving shape info.

        Args:
            image (np.ndarray): Input image array.

        Returns:
            Tuple of (flattened array, original shape).
        """
        original_shape = image.shape
        flat_array = image.flatten().astype(np.uint8)
        return flat_array, original_shape

    def diffuse_image(self, image: np.ndarray) -> np.ndarray:
        """
        Applies Tent Map diffusion with XOR to encrypted image.

        Diffusion formula: c[i] = s[i] ⊕ d[i] ⊕ c[i-1]
        where s[i] is input pixel, d[i] is diffusion value, c[i-1] is previous output.

        Args:
            image (np.ndarray): Substituted image array (uint8).

        Returns:
            np.ndarray: Diffused image with same shape as input.
        """
        if not isinstance(image, np.ndarray):
            raise TypeError(f"image must be np.ndarray, got {type(image).__name__}")

        # Flatten image
        flat_image, original_shape = self._flatten_image(image)

        if len(flat_image) == 0:
            raise ValueError("Image cannot be empty")

        # Generate diffusion sequence
        diffusion_seq = self._generate_tent_sequence(len(flat_image))

        # Apply diffusion with chaining
        ciphertext = np.zeros(len(flat_image), dtype=np.uint8)
        prev_cipher = 0

        for i in range(len(flat_image)):
            # c[i] = s[i] ⊕ d[i] ⊕ c[i-1]
            ciphertext[i] = flat_image[i] ^ diffusion_seq[i] ^ prev_cipher
            prev_cipher = ciphertext[i]

        # Restore to original shape
        return ciphertext.reshape(original_shape)

    def inverse_diffuse(self, image: np.ndarray) -> np.ndarray:
        """
        Reverses Tent Map diffusion for decryption.

        Inverse formula: s[i] = c[i] ⊕ d[i] ⊕ c[i-1]
        (Same formula, due to XOR properties)

        Args:
            image (np.ndarray): Diffused image array (uint8).

        Returns:
            np.ndarray: Recovered substituted image with same shape as input.
        """
        if not isinstance(image, np.ndarray):
            raise TypeError(f"image must be np.ndarray, got {type(image).__name__}")

        # Flatten image
        flat_image, original_shape = self._flatten_image(image)

        if len(flat_image) == 0:
            raise ValueError("Image cannot be empty")

        # Generate same diffusion sequence (deterministic)
        diffusion_seq = self._generate_tent_sequence(len(flat_image))

        # Reverse diffusion with chaining
        plaintext = np.zeros(len(flat_image), dtype=np.uint8)
        prev_cipher = 0

        for i in range(len(flat_image)):
            # s[i] = c[i] ⊕ d[i] ⊕ c[i-1]
            plaintext[i] = flat_image[i] ^ diffusion_seq[i] ^ prev_cipher
            prev_cipher = flat_image[i]  # Use input ciphertext, not output

        # Restore to original shape
        return plaintext.reshape(original_shape)
