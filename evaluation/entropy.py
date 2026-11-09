"""
Shannon Entropy Metric Evaluation Module

Calculates information entropy H(m) of plaintext and ciphertext image pixel matrices.
For an ideal 8-bit encrypted image, the theoretical entropy approaches 8.0 bits.
"""

import math
from typing import Union
import numpy as np


def calculate_entropy(image_array: Union[np.ndarray, bytes]) -> float:
    """
    Computes Shannon Information Entropy:
    H = - sum(p(x) * log2(p(x))) for all non-zero pixel probabilities.

    Args:
        image_array (Union[np.ndarray, bytes]): Image pixels or ciphertext byte stream.

    Returns:
        float: Shannon entropy score in bits (0.0 to 8.0 for 8-bit images).
    """
    if isinstance(image_array, (bytes, bytearray)):
        data = np.frombuffer(image_array, dtype=np.uint8)
    else:
        data = np.asarray(image_array).flatten()

    if data.size == 0:
        return 0.0

    counts = np.bincount(data, minlength=256)
    probabilities = counts / data.size
    probabilities = probabilities[probabilities > 0]

    entropy = -np.sum(probabilities * np.log2(probabilities))
    return float(entropy)
