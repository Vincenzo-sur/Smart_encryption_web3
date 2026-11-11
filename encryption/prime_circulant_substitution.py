"""
Prime Circulant Substitution Module

Implements non-linear byte/pixel value transformation using a prime-circulant
affine mixing step combined with HMAC-SHA256 keyed Fisher-Yates permutation
to construct a bijective 256-entry substitution box (S-box).
"""

import hashlib
import hmac

import numpy as np


class PrimeCirculantSubstitution:
    """
    Applies bijective non-linear byte substitution derived from (key, nonce).
    """

    # Odd primes coprime to 256 for invertible circulant stride selection
    _COPRIME_PRIMES = (
        3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59,
        61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127,
        131, 137, 139, 149, 151, 157, 163, 167, 173, 179, 181, 191,
        193, 197, 199, 211, 223, 227, 229, 233, 239, 241, 251,
    )

    def __init__(self, key: bytes, nonce: bytes = b""):
        """
        Initialize Prime Circulant Substitution.

        Args:
            key (bytes): 32-byte encryption key.
            nonce (bytes): Per-encryption nonce for S-box independence.

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
        self._build_substitution_table()
        self._inverse_table = self._build_inverse_table()

    def _build_substitution_table(self) -> None:
        """
        Builds a bijective 256-element S-box using prime-circulant affine
        permutation followed by keyed Fisher-Yates rounds.
        """
        seed = hmac.new(self.key, b"prime-circulant|" + self.nonce, hashlib.sha256).digest()
        prime = self._COPRIME_PRIMES[int.from_bytes(seed[:2], "big") % len(self._COPRIME_PRIMES)]
        offset = seed[2]

        # Prime-circulant affine initialization: bijection over Z_256 since gcd(prime, 256) == 1
        table = np.array([(i * prime + offset) & 0xFF for i in range(256)], dtype=np.uint8)

        # Keyed Fisher-Yates mixing rounds
        for round_num in range(4):
            round_key = hmac.new(
                self.key,
                b"sbox-round|" + self.nonce + bytes([round_num]),
                hashlib.sha256,
            ).digest()

            # Expand deterministic stream for indices 255..1 (32 bytes = 8 indices per block)
            pos = 255
            block_idx = 0
            while pos > 0:
                block = hashlib.sha256(round_key + block_idx.to_bytes(2, "big")).digest()
                for offset_bytes in range(0, 32, 4):
                    if pos <= 0:
                        break
                    j = int.from_bytes(block[offset_bytes:offset_bytes + 4], "big") % (pos + 1)
                    table[pos], table[j] = table[j], table[pos]
                    pos -= 1
                block_idx += 1

        self.substitution_table = table

    def _build_inverse_table(self) -> np.ndarray:
        """Constructs the exact inverse S-box table."""
        inverse = np.empty(256, dtype=np.uint8)
        inverse[self.substitution_table] = np.arange(256, dtype=np.uint8)
        return inverse

    def _get_inverse_table(self) -> np.ndarray:
        """Returns the inverse substitution lookup table."""
        return self._inverse_table

    def substitute_pixels(self, image: np.ndarray) -> np.ndarray:
        """
        Applies S-box substitution to all elements in a uint8 array.

        Args:
            image (np.ndarray): Input array (any shape).

        Returns:
            np.ndarray: Substituted uint8 array with same shape as input.
        """
        if not isinstance(image, np.ndarray):
            raise TypeError(f"image must be np.ndarray, got {type(image).__name__}")

        arr = image if image.dtype == np.uint8 else image.astype(np.uint8)
        return self.substitution_table[arr]

    def inverse_substitute(self, image: np.ndarray) -> np.ndarray:
        """
        Reverses the S-box substitution for decryption.

        Args:
            image (np.ndarray): Substituted array.

        Returns:
            np.ndarray: Original uint8 array with same shape as input.
        """
        if not isinstance(image, np.ndarray):
            raise TypeError(f"image must be np.ndarray, got {type(image).__name__}")

        arr = image if image.dtype == np.uint8 else image.astype(np.uint8)
        return self._inverse_table[arr]
