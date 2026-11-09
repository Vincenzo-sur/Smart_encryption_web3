"""
Number of Pixels Change Rate (NPCR) Metric Evaluation Module

Quantifies the percentage of different pixel positions between two ciphertexts C1 and C2
originating from plaintexts that differ by a single bit.
"""

from typing import Union
import numpy as np


def calculate_npcr(c1: Union[np.ndarray, bytes], c2: Union[np.ndarray, bytes]) -> float:
    """
    Computes NPCR percentage:
    NPCR = (sum(D(i, j)) / (W * H)) * 100%
    where D(i, j) = 1 if C1(i, j) != C2(i, j), else 0.

    Args:
        c1: First ciphertext array or bytes.
        c2: Second ciphertext array or bytes.

    Returns:
        float: Percentage of changed pixels (ideal > 99.6%).
    """
    arr1 = np.frombuffer(c1, dtype=np.uint8) if isinstance(c1, (bytes, bytearray)) else np.asarray(c1).flatten()
    arr2 = np.frombuffer(c2, dtype=np.uint8) if isinstance(c2, (bytes, bytearray)) else np.asarray(c2).flatten()

    min_len = min(arr1.size, arr2.size)
    if min_len == 0:
        return 0.0

    diff_count = np.count_nonzero(arr1[:min_len] != arr2[:min_len])
    return float((diff_count / min_len) * 100.0)
