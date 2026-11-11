"""
Sine Map Chaotic Permutation Module

Implements pixel-level permutation using the Sine Map chaotic generator.
The Sine Map is defined as: x_{i+1} = μ * sin(π * x_i)
where μ is derived from the encryption key.

This achieves diffusion by rearranging pixel positions, making the spatial
correlation in the encrypted image negligible.
"""

import numpy as np
from typing import Tuple
import hashlib


class SineMapPermutation:
    """
    Generates pixel permutation sequences using the Sine Map chaos system.

    The Sine Map is sensitive to initial conditions, ensuring that different keys
    produce completely different permutation sequences.
    """

    def __init__(self, key: bytes, image_shape: Tuple[int, int]):
        """
        Initialize Sine Map permutation generator.

        Args:
            key (bytes): 32-byte encryption key.
            image_shape (Tuple[int, int]): Tuple of (height, width) for the image.

        Raises:
            ValueError: If key is not 32 bytes or image_shape is invalid.
        """
        if not isinstance(key, (bytes, bytearray)) or len(key) != 32:
            raise ValueError(f"Key must be exactly 32 bytes (got {len(key) if isinstance(key, (bytes, bytearray)) else 'non-bytes'})")

        if not isinstance(image_shape, tuple) or len(image_shape) != 2:
            raise ValueError("image_shape must be a tuple of (height, width)")

        height, width = image_shape
        if height <= 0 or width <= 0:
            raise ValueError("Image dimensions must be positive")

        self.key = key
        self.height = height
        self.width = width
        self.total_pixels = height * width

        # Derive Sine Map parameters from key
        self._derive_parameters()

    def _derive_parameters(self):
        """
        Derives Sine Map parameters (μ and x0) from the encryption key.

        Uses SHA-256 hashing to extract deterministic parameters from the key.
        """
        # Derive μ (control parameter) from key
        # μ is typically in range [0, 1] for chaos in Sine Map
        hash1 = hashlib.sha256(self.key).digest()
        mu_val = int.from_bytes(hash1[:8], byteorder='big') / (2**64)
        # Scale μ to typical chaotic region [2.0, 4.0]
        self.mu = 2.0 + mu_val * 2.0

        # Derive initial x0 from key
        hash2 = hashlib.sha256(self.key + b'x0').digest()
        x0_val = int.from_bytes(hash2[:8], byteorder='big') / (2**64)
        # Ensure x0 is in (0, 1) excluding boundaries
        self.x0 = 0.1 + x0_val * 0.8

    def _generate_sine_sequence(self, length: int) -> np.ndarray:
        """
        Generates chaotic sequence using Sine Map.

        Args:
            length (int): Number of values to generate.

        Returns:
            np.ndarray: Array of chaotic values in [0, 1).
        """
        sequence = np.zeros(length, dtype=np.float64)
        x = self.x0

        for i in range(length):
            # Sine Map iteration: x_{i+1} = μ * sin(π * x_i)
            x = self.mu * np.sin(np.pi * x)
            # Ensure x stays in [0, 1] by taking absolute value
            x = np.abs(x)
            sequence[i] = x

        return sequence

    def _generate_permutation_indices(self) -> np.ndarray:
        """
        Generates permutation indices for pixel rearrangement.

        Returns:
            np.ndarray: Array of permutation indices.
        """
        # Generate chaotic sequence
        chaotic_seq = self._generate_sine_sequence(self.total_pixels)

        # Convert chaotic values to indices [0, total_pixels)
        indices = np.argsort(chaotic_seq)

        return indices

    def permute_pixels(self, image: np.ndarray) -> np.ndarray:
        """
        Rearranges pixel positions using Sine Map-generated permutation.

        Handles multi-channel images by permuting within each channel separately.

        Args:
            image (np.ndarray): Input image array (H×W or H×W×C).

        Returns:
            np.ndarray: Permuted image array with same shape as input.
        """
        if not isinstance(image, np.ndarray):
            raise TypeError(f"image must be np.ndarray, got {type(image).__name__}")

        original_shape = image.shape

        # Handle multi-channel images
        if len(original_shape) == 3:
            # Image is H×W×C
            h, w, c = original_shape
            if h != self.height or w != self.width:
                raise ValueError(
                    f"Image dimensions {(h, w)} don't match expected {(self.height, self.width)}"
                )

            # Apply permutation to each channel
            permuted_channels = []
            for ch in range(c):
                channel = image[:, :, ch].astype(np.float64)
                flat_channel = channel.flatten()
                indices = self._generate_permutation_indices()
                permuted_flat = flat_channel[indices]
                permuted_channel = permuted_flat.reshape((h, w))
                permuted_channels.append(permuted_channel)

            return np.stack(permuted_channels, axis=-1)

        elif len(original_shape) == 2:
            # Grayscale image: H×W
            h, w = original_shape
            if h != self.height or w != self.width:
                raise ValueError(
                    f"Image dimensions {(h, w)} don't match expected {(self.height, self.width)}"
                )

            flat_image = image.flatten().astype(np.float64)
            indices = self._generate_permutation_indices()
            permuted = flat_image[indices]
            return permuted.reshape(original_shape)

        else:
            raise ValueError(f"Unsupported image shape: {original_shape}")

    def inverse_permute(self, image: np.ndarray) -> np.ndarray:
        """
        Reverses the permutation for decryption.

        Handles multi-channel images by reversing permutation within each channel separately.

        Args:
            image (np.ndarray): Permuted image array (H×W or H×W×C).

        Returns:
            np.ndarray: Restored image array.
        """
        if not isinstance(image, np.ndarray):
            raise TypeError(f"image must be np.ndarray, got {type(image).__name__}")

        original_shape = image.shape

        # Handle multi-channel images
        if len(original_shape) == 3:
            # Image is H×W×C
            h, w, c = original_shape
            if h != self.height or w != self.width:
                raise ValueError(
                    f"Image dimensions {(h, w)} don't match expected {(self.height, self.width)}"
                )

            # Reverse permutation for each channel
            restored_channels = []
            for ch in range(c):
                channel = image[:, :, ch].astype(np.float64)
                flat_channel = channel.flatten()
                indices = self._generate_permutation_indices()
                inverse_indices = np.argsort(indices)
                restored_flat = flat_channel[inverse_indices]
                restored_channel = restored_flat.reshape((h, w))
                restored_channels.append(restored_channel)

            return np.stack(restored_channels, axis=-1)

        elif len(original_shape) == 2:
            # Grayscale image: H×W
            h, w = original_shape
            if h != self.height or w != self.width:
                raise ValueError(
                    f"Image dimensions {(h, w)} don't match expected {(self.height, self.width)}"
                )

            flat_image = image.flatten().astype(np.float64)
            indices = self._generate_permutation_indices()
            inverse_indices = np.argsort(indices)
            restored = flat_image[inverse_indices]
            return restored.reshape(original_shape)

        else:
            raise ValueError(f"Unsupported image shape: {original_shape}")
