"""
Sine Map Chaotic Permutation Module

Implements byte- and pixel-level spatial permutation using the 1D Sine Map
chaotic system:
    x_{i+1} = mu * sin(pi * x_i)

Control parameter mu is constrained to the valid chaotic regime [0.87, 0.999]
so trajectories remain strictly bounded in (0, 1). A transient burn-in phase is
discarded before sampling, and parameters are derived from (key, nonce) via
HMAC-SHA256 so each encryption uses an independent permutation.
"""

import hashlib
import hmac
import math
from typing import Tuple, Union

import numpy as np


class SineMapPermutation:
    """
    Generates invertible permutation sequences using the Sine Map chaos system.
    Supports both 1D raw byte arrays and 2D/3D uint8 image matrices.
    """

    BURN_IN_ITERATIONS = 100

    def __init__(
        self,
        key: bytes,
        image_shape: Union[int, Tuple[int, ...]],
        nonce: bytes = b""
    ):
        """
        Initialize Sine Map permutation generator.

        Args:
            key (bytes): 32-byte encryption key.
            image_shape (Union[int, Tuple[int, ...]]): Total element count (int)
                or image shape tuple (height, width[, channels]).
            nonce (bytes): Per-encryption nonce for permutation independence.

        Raises:
            ValueError: If key is not 32 bytes or image_shape is invalid.
        """
        if not isinstance(key, (bytes, bytearray)) or len(key) != 32:
            got = len(key) if isinstance(key, (bytes, bytearray)) else "non-bytes"
            raise ValueError(f"Key must be exactly 32 bytes (got {got})")

        if not isinstance(nonce, (bytes, bytearray)):
            raise TypeError("nonce must be bytes or bytearray")

        if isinstance(image_shape, int):
            if image_shape <= 0:
                raise ValueError("Image length must be positive")
            self.height = 1
            self.width = image_shape
            self.total_pixels = image_shape
        elif isinstance(image_shape, tuple) and len(image_shape) >= 2:
            height, width = int(image_shape[0]), int(image_shape[1])
            if height <= 0 or width <= 0:
                raise ValueError("Image dimensions must be positive")
            self.height = height
            self.width = width
            self.total_pixels = height * width
        else:
            raise ValueError("image_shape must be a positive int or a tuple of (height, width[, ...])")

        self.key = bytes(key)
        self.nonce = bytes(nonce)
        self._derive_parameters()
        self._cached_indices: np.ndarray | None = None

    def _derive_parameters(self) -> None:
        """
        Derives Sine Map parameters (mu, x0) from (key, nonce) via HMAC-SHA256.
        Constrains mu to [0.87, 0.999] so x stays strictly within (0, 1).
        """
        digest = hmac.new(self.key, b"sine-map-params|" + self.nonce, hashlib.sha256).digest()
        mu_unit = int.from_bytes(digest[:8], byteorder="big") / (2**64)
        x0_unit = int.from_bytes(digest[8:16], byteorder="big") / (2**64)

        self.mu = 0.87 + mu_unit * 0.129
        self.x0 = 0.05 + x0_unit * 0.90

    def _generate_sine_sequence(self, length: int) -> np.ndarray:
        """
        Generates chaotic sequence using scalar math.sin after transient burn-in.

        Args:
            length (int): Number of chaotic values to generate.

        Returns:
            np.ndarray: Float64 array of chaotic values in (0, 1).
        """
        x = self.x0
        mu = self.mu
        pi = math.pi
        sin = math.sin

        for _ in range(self.BURN_IN_ITERATIONS):
            x = mu * sin(pi * x)
            if x <= 1e-12 or x >= 1.0 - 1e-12:
                x = 0.3141592653589793

        sequence = np.empty(length, dtype=np.float64)
        for i in range(length):
            x = mu * sin(pi * x)
            if x <= 1e-12 or x >= 1.0 - 1e-12:
                # Re-seed perturbatively from index to prevent fixed-point trapping
                x = ((x + (i + 1) * 0.6180339887498949) % 0.9) + 0.05
            sequence[i] = x

        return sequence

    def _generate_permutation_indices(self) -> np.ndarray:
        """
        Generates deterministic permutation indices for the configured size.

        Returns:
            np.ndarray: Integer permutation index array of length `total_pixels`.
        """
        if self._cached_indices is None:
            chaotic_seq = self._generate_sine_sequence(self.total_pixels)
            self._cached_indices = np.argsort(chaotic_seq, kind="mergesort")
        return self._cached_indices

    def permute_pixels(self, image: np.ndarray) -> np.ndarray:
        """
        Rearranges byte/pixel positions using the Sine Map permutation.

        Args:
            image (np.ndarray): Input uint8 array (1D, HxW, or HxWxC).

        Returns:
            np.ndarray: Permuted uint8 array with the exact same shape as input.
        """
        if not isinstance(image, np.ndarray):
            raise TypeError(f"image must be np.ndarray, got {type(image).__name__}")

        arr = image if image.dtype == np.uint8 else image.astype(np.uint8)
        original_shape = arr.shape
        indices = self._generate_permutation_indices()

        if arr.ndim == 1:
            if arr.shape[0] != self.total_pixels:
                raise ValueError(
                    f"Array length {arr.shape[0]} does not match expected {self.total_pixels}"
                )
            return arr[indices].copy()

        if arr.ndim == 2:
            h, w = original_shape
            if (h, w) != (self.height, self.width):
                raise ValueError(f"Image dimensions {(h, w)} don't match expected {(self.height, self.width)}")
            return arr.reshape(-1)[indices].reshape(original_shape)

        if arr.ndim == 3:
            h, w, c = original_shape
            if (h, w) != (self.height, self.width):
                raise ValueError(f"Image dimensions {(h, w)} don't match expected {(self.height, self.width)}")
            flat_channels = arr.reshape(self.total_pixels, c)
            return flat_channels[indices, :].reshape(original_shape)

        raise ValueError(f"Unsupported image shape: {original_shape}")

    def inverse_permute(self, image: np.ndarray) -> np.ndarray:
        """
        Reverses the Sine Map permutation in O(N) time.

        Args:
            image (np.ndarray): Permuted uint8 array (1D, HxW, or HxWxC).

        Returns:
            np.ndarray: Restored uint8 array with the exact same shape as input.
        """
        if not isinstance(image, np.ndarray):
            raise TypeError(f"image must be np.ndarray, got {type(image).__name__}")

        arr = image if image.dtype == np.uint8 else image.astype(np.uint8)
        original_shape = arr.shape
        indices = self._generate_permutation_indices()

        if arr.ndim == 1:
            if arr.shape[0] != self.total_pixels:
                raise ValueError(
                    f"Array length {arr.shape[0]} does not match expected {self.total_pixels}"
                )
            restored = np.empty_like(arr)
            restored[indices] = arr
            return restored

        if arr.ndim == 2:
            h, w = original_shape
            if (h, w) != (self.height, self.width):
                raise ValueError(f"Image dimensions {(h, w)} don't match expected {(self.height, self.width)}")
            restored = np.empty(self.total_pixels, dtype=np.uint8)
            restored[indices] = arr.reshape(-1)
            return restored.reshape(original_shape)

        if arr.ndim == 3:
            h, w, c = original_shape
            if (h, w) != (self.height, self.width):
                raise ValueError(f"Image dimensions {(h, w)} don't match expected {(self.height, self.width)}")
            restored = np.empty((self.total_pixels, c), dtype=np.uint8)
            restored[indices, :] = arr.reshape(self.total_pixels, c)
            return restored.reshape(original_shape)

        raise ValueError(f"Unsupported image shape: {original_shape}")
