"""
Histogram Analysis Module

Analyzes gray-level and color-channel distributions of plaintext vs ciphertext.
"""

from typing import Union, Tuple, Dict
import numpy as np


def compute_histogram(image_data: Union[np.ndarray, bytes]) -> np.ndarray:
    """
    Computes 256-bin histogram of pixel intensity values.

    Returns:
        np.ndarray: Frequency counts for intensity values [0, 255].
    """
    if isinstance(image_data, (bytes, bytearray)):
        data = np.frombuffer(image_data, dtype=np.uint8)
    else:
        data = np.asarray(image_data).flatten()

    counts = np.bincount(data, minlength=256)
    return counts[:256]


def calculate_variance_of_histogram(counts: np.ndarray) -> float:
    """Computes histogram variance to test uniformity."""
    mean_val = np.mean(counts)
    return float(np.mean((counts - mean_val) ** 2))
