"""
Unified Average Changing Intensity (UACI) Metric Evaluation Module

Measures the average intensity of differences between two ciphertexts.
"""

from typing import Union
import numpy as np


def calculate_uaci(c1: Union[np.ndarray, bytes], c2: Union[np.ndarray, bytes]) -> float:
    """
    Computes UACI percentage:
    UACI = (1 / (W * H)) * sum(|C1(i, j) - C2(i, j)| / 255) * 100%

    Args:
        c1: First ciphertext array or bytes.
        c2: Second ciphertext array or bytes.

    Returns:
        float: UACI percentage (ideal ~ 33.4% for 8-bit images).
    """
    arr1 = np.frombuffer(c1, dtype=np.uint8) if isinstance(c1, (bytes, bytearray)) else np.asarray(c1, dtype=np.float64).flatten()
    arr2 = np.frombuffer(c2, dtype=np.uint8) if isinstance(c2, (bytes, bytearray)) else np.asarray(c2, dtype=np.float64).flatten()

    min_len = min(arr1.size, arr2.size)
    if min_len == 0:
        return 0.0

    intensity_diff = np.sum(np.abs(arr1[:min_len].astype(np.float64) - arr2[:min_len].astype(np.float64)))
    uaci = (intensity_diff / (min_len * 255.0)) * 100.0
    return float(uaci)
