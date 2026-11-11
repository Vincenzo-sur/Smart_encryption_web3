"""
Tent Map Diffusion Module

Implements vectorized, non-collapsing chaotic diffusion using a multi-lane
skewed Tent Map paired with two-pass bidirectional non-linear chaining:
    x_{i+1} = x_i / p           if x_i < p
              (1 - x_i) / (1-p) otherwise

Unlike naive symmetric floating-point Tent Maps (p = 0.5), which lose all
IEEE-754 mantissa bits and collapse to 0.0 after ~53 iterations, a skewed Tent
Map (p in [0.43, 0.57], p != 0.5) combined with multi-lane vectorization and
periodic deterministic perturbation maintains full chaotic entropy over arbitrary
payload sizes. Bidirectional modular-addition + XOR chaining with a non-linear
middle S-box guarantees single-bit plaintext sensitivity across the entire buffer.
"""

import hashlib
import hmac
from typing import Tuple

import numpy as np

from encryption.prime_circulant_substitution import PrimeCirculantSubstitution


class TentMapDiffusion:
    """
    Applies non-collapsing Skewed Tent Map keystream generation and
    bidirectional avalanche diffusion.
    """

    NUM_LANES = 256
    BURN_IN_STEPS = 64

    def __init__(self, key: bytes, nonce: bytes = b""):
        """
        Initialize Tent Map Diffusion.

        Args:
            key (bytes): 32-byte encryption key.
            nonce (bytes): Per-encryption nonce for keystream independence.

        Raises:
            ValueError: If key is not 32 bytes.
        """
        if not isinstance(key, (bytes, bytearray)) or len(key) != 32:
            got = len(key) if isinstance(key, (bytes, bytearray)) else "non-bytes"
            raise ValueError(f"Key must be exactly 32 bytes (got {got})")

        if not isinstance(nonce, (bytes, bytearray)):
            raise TypeError("nonce must be bytes or bytearray")

        self.key = bytes(key)
        self.nonce = bytes(nonce)
        self._derive_parameters()
        self._mid_sbox = PrimeCirculantSubstitution(
            hmac.new(self.key, b"tent-mid-sbox|" + self.nonce, hashlib.sha256).digest(),
            self.nonce,
        )

    def _derive_parameters(self) -> None:
        """
        Derives skewed Tent Map parameter p != 0.5, 256 initial lane states,
        and bidirectional chaining IVs from (key, nonce) via HMAC-SHA256.
        """
        master = hmac.new(self.key, b"tent-map-params|" + self.nonce, hashlib.sha256).digest()

        # Derive skew p in [0.43, 0.485] or [0.515, 0.57] so p is bounded away from 0.5
        p_unit = int.from_bytes(master[:8], "big") / (2**64)
        if p_unit < 0.5:
            self.skew_p = 0.43 + (p_unit * 2.0) * 0.055
        else:
            self.skew_p = 0.515 + ((p_unit - 0.5) * 2.0) * 0.055

        # Extract initial scalar x0 (exposed for inspection) and chaining IVs
        x0_unit = int.from_bytes(master[8:16], "big") / (2**64)
        self.x0 = 0.1 + x0_unit * 0.8
        self.iv_forward = master[16]
        self.iv_backward = master[17]

        # Initialize 256 independent lane states from HMAC-SHA256
        lanes = np.empty(self.NUM_LANES, dtype=np.float64)
        perturbs = np.empty(self.NUM_LANES, dtype=np.float64)
        for block_idx in range(self.NUM_LANES // 4):
            digest = hmac.new(
                self.key,
                b"tent-lanes|" + self.nonce + block_idx.to_bytes(2, "big"),
                hashlib.sha256,
            ).digest()
            for j in range(4):
                lane_i = block_idx * 4 + j
                raw = int.from_bytes(digest[j * 8:(j + 1) * 8], "big") / (2**64)
                lanes[lane_i] = 0.05 + raw * 0.90
                perturbs[lane_i] = 1e-7 * (1.0 + ((lane_i + 1) % 97) / 97.0)

        self._init_lanes = lanes
        self._lane_perturbs = perturbs

    def _generate_tent_sequence(self, length: int) -> np.ndarray:
        """
        Generates `length` uniformly distributed uint8 chaotic diffusion bytes
        using the vectorized 256-lane skewed Tent Map.

        Args:
            length (int): Number of diffusion bytes required.

        Returns:
            np.ndarray: uint8 array of length `length`.
        """
        if length <= 0:
            return np.empty(0, dtype=np.uint8)

        x = self._init_lanes.copy()
        p = self.skew_p
        inv_p = 1.0 / p
        inv_1mp = 1.0 / (1.0 - p)
        perturbs = self._lane_perturbs

        # Transient burn-in
        for step in range(self.BURN_IN_STEPS):
            x = np.where(x < p, x * inv_p, (1.0 - x) * inv_1mp)
            if (step & 15) == 15:
                x = (x + perturbs) % 1.0

        steps_needed = (length + self.NUM_LANES - 1) // self.NUM_LANES
        out = np.empty((steps_needed, self.NUM_LANES), dtype=np.uint8)

        for step in range(steps_needed):
            x = np.where(x < p, x * inv_p, (1.0 - x) * inv_1mp)
            # Periodic perturbation and boundary guard prevent fixed-point trapping
            if (step & 31) == 31:
                x = (x + perturbs) % 1.0
            bad = (x <= 1e-9) | (x >= 1.0 - 1e-9)
            if np.any(bad):
                x = np.where(bad, (self._init_lanes + perturbs * (step + 1)) % 0.9 + 0.05, x)
            # Extract fractional middle bits into [0, 255] for uniform byte distribution
            out[step] = ((x * 16777216.0).astype(np.uint64) & 0xFF).astype(np.uint8)

        return out.reshape(-1)[:length]

    def _flatten_image(self, image: np.ndarray) -> Tuple[np.ndarray, Tuple[int, ...]]:
        """Flattens array to 1D uint8 while preserving original shape."""
        original_shape = image.shape
        flat_array = (image if image.dtype == np.uint8 else image.astype(np.uint8)).reshape(-1)
        return flat_array, original_shape

    def diffuse_image(self, image: np.ndarray) -> np.ndarray:
        """
        Applies bidirectional non-linear Tent Map diffusion to `image`.

        Forward pass:
            u[0] = ((s[0] + d1[0]) & 0xFF) ^ iv_forward
            u[i] = (s[i] + d1[i]) & 0xFF
            f = prefix_xor(u)
        Non-linear middle S-box:
            m = SBOX[f]
        Backward pass (over reversed m):
            v[0] = ((m_rev[0] + d2[0]) & 0xFF) ^ iv_backward
            v[i] = (m_rev[i] + d2[i]) & 0xFF
            c = prefix_xor(v)[::-1]

        Args:
            image (np.ndarray): Input uint8 array.

        Returns:
            np.ndarray: Diffused uint8 array with same shape as input.
        """
        if not isinstance(image, np.ndarray):
            raise TypeError(f"image must be np.ndarray, got {type(image).__name__}")

        flat_image, original_shape = self._flatten_image(image)
        n = flat_image.size
        if n == 0:
            raise ValueError("Image cannot be empty")

        seq = self._generate_tent_sequence(2 * n)
        d1 = seq[:n]
        d2 = seq[n:]

        # Pass 1: forward modular addition + prefix XOR
        u = ((flat_image.astype(np.uint16) + d1.astype(np.uint16)) & 0xFF).astype(np.uint8)
        u[0] ^= self.iv_forward
        f = np.bitwise_xor.accumulate(u)

        # Non-linear confusion bridge
        m = self._mid_sbox.substitute_pixels(f)

        # Pass 2: backward modular addition + prefix XOR
        m_rev = m[::-1]
        v = ((m_rev.astype(np.uint16) + d2.astype(np.uint16)) & 0xFF).astype(np.uint8)
        v[0] ^= self.iv_backward
        c_rev = np.bitwise_xor.accumulate(v)

        return c_rev[::-1].reshape(original_shape)

    def inverse_diffuse(self, image: np.ndarray) -> np.ndarray:
        """
        Reverses the bidirectional Tent Map diffusion losslessly.

        Args:
            image (np.ndarray): Diffused uint8 array.

        Returns:
            np.ndarray: Recovered uint8 array with same shape as input.
        """
        if not isinstance(image, np.ndarray):
            raise TypeError(f"image must be np.ndarray, got {type(image).__name__}")

        flat_image, original_shape = self._flatten_image(image)
        n = flat_image.size
        if n == 0:
            raise ValueError("Image cannot be empty")

        seq = self._generate_tent_sequence(2 * n)
        d1 = seq[:n]
        d2 = seq[n:]

        # Reverse Pass 2
        c_rev = flat_image[::-1]
        prev_c = np.empty(n, dtype=np.uint8)
        prev_c[0] = self.iv_backward
        if n > 1:
            prev_c[1:] = c_rev[:-1]
        xored_v = c_rev ^ prev_c
        m_rev = ((xored_v.astype(np.int16) - d2.astype(np.int16)) & 0xFF).astype(np.uint8)
        m = m_rev[::-1]

        # Reverse middle S-box
        f = self._mid_sbox.inverse_substitute(m)

        # Reverse Pass 1
        prev_f = np.empty(n, dtype=np.uint8)
        prev_f[0] = self.iv_forward
        if n > 1:
            prev_f[1:] = f[:-1]
        xored_u = f ^ prev_f
        s = ((xored_u.astype(np.int16) - d1.astype(np.int16)) & 0xFF).astype(np.uint8)

        return s.reshape(original_shape)
