"""
Histogram Analysis Module

Analyzes gray-level and color-channel distributions of plaintext vs ciphertext,
including 256-bin frequency counts, variance, and chi-square uniformity metrics.
"""

from typing import Union, Dict, Any
import numpy as np


def compute_histogram(image_data: Union[np.ndarray, bytes]) -> np.ndarray:
    """
    Computes 256-bin histogram of pixel/byte intensity values.

    Returns:
        np.ndarray: Frequency counts for intensity values [0, 255].
    """
    if isinstance(image_data, (bytes, bytearray)):
        data = np.frombuffer(image_data, dtype=np.uint8)
    else:
        data = np.asarray(image_data, dtype=np.uint8).flatten()

    counts = np.bincount(data, minlength=256)
    return counts[:256]


def calculate_variance_of_histogram(counts: np.ndarray) -> float:
    """Computes histogram variance to test uniformity."""
    mean_val = np.mean(counts)
    return float(np.mean((counts - mean_val) ** 2))


def analyze_histogram(image_data: Union[np.ndarray, bytes]) -> Dict[str, Any]:
    """
    Computes full histogram uniformity statistics including chi-square test.

    Args:
        image_data: Pixel array or raw bytes.

    Returns:
        Dict containing histogram counts, mean, std, variance, chi_square, and uniformity_score.
    """
    if isinstance(image_data, (bytes, bytearray)):
        data = np.frombuffer(image_data, dtype=np.uint8)
    else:
        data = np.asarray(image_data, dtype=np.uint8).flatten()

    if data.size == 0:
        return {
            "histogram": [0] * 256,
            "mean": 0.0,
            "std": 0.0,
            "variance": 0.0,
            "chi_square": 0.0,
            "uniformity_score": 0.0,
        }

    counts = compute_histogram(data)
    expected = data.size / 256.0
    chi_square = float(np.sum(((counts.astype(np.float64) - expected) ** 2) / expected))

    return {
        "histogram": counts.tolist(),
        "mean": float(np.mean(data)),
        "std": float(np.std(data)),
        "variance": calculate_variance_of_histogram(counts),
        "chi_square": chi_square,
        "uniformity_score": float(chi_square / data.size),
    }
