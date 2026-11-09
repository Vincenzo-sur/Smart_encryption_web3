"""
Correlation Analysis Module

Measures horizontal, vertical, and diagonal correlation of adjacent pixels.
"""

from typing import Tuple
import numpy as np


def calculate_adjacent_correlation(image_matrix: np.ndarray, direction: str = "horizontal") -> float:
    """
    Computes Pearson correlation coefficient between adjacent pixels.

    Args:
        image_matrix: 2D numpy array of image intensities.
        direction: 'horizontal', 'vertical', or 'diagonal'.

    Returns:
        float: Correlation coefficient r_xy (-1.0 to 1.0).
    """
    mat = np.asarray(image_matrix, dtype=np.float64)
    if mat.ndim > 2:
        mat = mat[:, :, 0]

    h, w = mat.shape
    if direction == "horizontal":
        x = mat[:, :-1].flatten()
        y = mat[:, 1:].flatten()
    elif direction == "vertical":
        x = mat[:-1, :].flatten()
        y = mat[1:, :].flatten()
    elif direction == "diagonal":
        x = mat[:-1, :-1].flatten()
        y = mat[1:, 1:].flatten()
    else:
        raise ValueError(f"Unknown direction: {direction}")

    if x.size == 0 or np.std(x) == 0 or np.std(y) == 0:
        return 0.0

    corr = np.corrcoef(x, y)[0, 1]
    return float(corr)
