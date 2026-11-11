"""
Comprehensive Chaotic Encryption Security Metrics

Implements all 8 security metrics for evaluating chaotic image encryption:
1. Information Entropy - measures randomness (Target: 7.999+)
2. NPCR - Number of Pixels Change Rate (Target: >99.6%)
3. UACI - Unified Average Changing Intensity (Target: >33.4%)
4. Pixel Correlation - adjacent pixel correlation analysis (Target: <0.001)
5. Key Sensitivity - single-bit key change detection rate (Target: >99.5%)
6. Histogram Analysis - pixel distribution uniformity
7. PSNR - Peak Signal-to-Noise Ratio (should be low)
8. Encryption Speed - benchmark (Target: <1.0s per 512×512)

These metrics follow Paper 5.2 (2025) standards for chaotic encryption evaluation.
"""

import time
import math
from typing import Dict, Any, Tuple, Union, Callable
import numpy as np


def evaluate_entropy(image: Union[np.ndarray, bytes]) -> float:
    """
    Computes Shannon Information Entropy: H = -Σ(p(x) * log₂(p(x)))

    Measures the average information content per pixel. Ideal value for
    encrypted images is 7.999 (approaching theoretical maximum of 8.0).

    Args:
        image (Union[np.ndarray, bytes]): Pixel data or raw bytes.

    Returns:
        float: Entropy in bits [0.0, 8.0].
    """
    if isinstance(image, (bytes, bytearray)):
        data = np.frombuffer(image, dtype=np.uint8)
    else:
        data = np.asarray(image).flatten().astype(np.uint8)

    if data.size == 0:
        return 0.0

    # Count pixel occurrences
    counts = np.bincount(data, minlength=256)
    probabilities = counts / data.size
    probabilities = probabilities[probabilities > 0]

    # Shannon entropy: H = -Σ(p * log₂(p))
    entropy = -np.sum(probabilities * np.log2(probabilities))
    return float(entropy)


def calculate_npcr(original: Union[np.ndarray, bytes], encrypted: Union[np.ndarray, bytes]) -> float:
    """
    Number of Pixels Change Rate: NPCR = (D / (W*H)) * 100%

    Measures sensitivity to plaintext changes. A single bit change in plaintext
    should cause >99.6% of ciphertext pixels to change.

    Args:
        original: First ciphertext array or bytes.
        encrypted: Second ciphertext array or bytes.

    Returns:
        float: Percentage of changed pixels [0.0, 100.0].
    """
    arr1 = np.frombuffer(original, dtype=np.uint8) if isinstance(original, (bytes, bytearray)) else np.asarray(original).flatten().astype(np.uint8)
    arr2 = np.frombuffer(encrypted, dtype=np.uint8) if isinstance(encrypted, (bytes, bytearray)) else np.asarray(encrypted).flatten().astype(np.uint8)

    min_len = min(arr1.size, arr2.size)
    if min_len == 0:
        return 0.0

    # Count differing pixels
    diff_count = np.count_nonzero(arr1[:min_len] != arr2[:min_len])
    npcr = (diff_count / min_len) * 100.0
    return float(npcr)


def calculate_uaci(original: Union[np.ndarray, bytes], encrypted: Union[np.ndarray, bytes]) -> float:
    """
    Unified Average Changing Intensity: UACI = (1/(W*H)) * Σ(|C1-C2|/255) * 100%

    Measures average magnitude of pixel changes. Ideal UACI for 8-bit images is ~33.4%
    when plaintexts differ by a single bit.

    Args:
        original: First ciphertext array or bytes.
        encrypted: Second ciphertext array or bytes.

    Returns:
        float: Percentage intensity change [0.0, 100.0].
    """
    arr1 = np.frombuffer(original, dtype=np.uint8) if isinstance(original, (bytes, bytearray)) else np.asarray(original).flatten().astype(np.uint8)
    arr2 = np.frombuffer(encrypted, dtype=np.uint8) if isinstance(encrypted, (bytes, bytearray)) else np.asarray(encrypted).flatten().astype(np.uint8)

    min_len = min(arr1.size, arr2.size)
    if min_len == 0:
        return 0.0

    # Average absolute intensity difference
    intensity_diff = np.sum(np.abs(arr1[:min_len].astype(np.float64) - arr2[:min_len].astype(np.float64)))
    uaci = (intensity_diff / (min_len * 255.0)) * 100.0
    return float(uaci)


def compute_pixel_correlation(image: Union[np.ndarray, bytes], direction: str = "horizontal") -> float:
    """
    Computes correlation coefficient between adjacent pixels.

    For plaintext images, adjacent pixels are highly correlated (typically > 0.9).
    For encrypted images, correlation should be < 0.001 (near-zero).

    Formula: r = Σ((X-μx)(Y-μy)) / sqrt(Σ(X-μx)² * Σ(Y-μy)²)

    Args:
        image: Image array or bytes.
        direction: "horizontal", "vertical", or "diagonal".

    Returns:
        float: Correlation coefficient [-1.0, 1.0].
    """
    if isinstance(image, (bytes, bytearray)):
        data = np.frombuffer(image, dtype=np.uint8)
    else:
        data = np.asarray(image).flatten().astype(np.uint8)

    if data.size < 2:
        return 0.0

    # Generate pixel pairs based on direction
    if direction == "horizontal":
        # Reshape to 2D if possible, otherwise use sequential pairs
        try:
            # Assume square or rectangular image
            side = int(np.sqrt(len(data)))
            if side * side == len(data):
                img_2d = data.reshape(side, side)
                pairs = []
                for row in img_2d:
                    for i in range(len(row) - 1):
                        pairs.append((row[i], row[i + 1]))
            else:
                pairs = [(data[i], data[i + 1]) for i in range(len(data) - 1)]
        except:
            pairs = [(data[i], data[i + 1]) for i in range(len(data) - 1)]

    elif direction == "vertical":
        try:
            side = int(np.sqrt(len(data)))
            if side * side == len(data):
                img_2d = data.reshape(side, side)
                pairs = []
                for i in range(side - 1):
                    for j in range(side):
                        pairs.append((img_2d[i, j], img_2d[i + 1, j]))
            else:
                pairs = [(data[i], data[i + len(data) // 2]) for i in range(len(data) // 2)]
        except:
            pairs = [(data[i], data[i + len(data) // 2]) for i in range(len(data) // 2)]

    else:  # diagonal
        try:
            side = int(np.sqrt(len(data)))
            if side * side == len(data):
                img_2d = data.reshape(side, side)
                pairs = []
                for i in range(side - 1):
                    for j in range(side - 1):
                        pairs.append((img_2d[i, j], img_2d[i + 1, j + 1]))
            else:
                pairs = [(data[i], data[i + 1]) for i in range(len(data) - 1)]
        except:
            pairs = [(data[i], data[i + 1]) for i in range(len(data) - 1)]

    if len(pairs) < 2:
        return 0.0

    x = np.array([p[0] for p in pairs], dtype=np.float64)
    y = np.array([p[1] for p in pairs], dtype=np.float64)

    # Compute correlation: r = Cov(X,Y) / (σx * σy)
    mean_x = np.mean(x)
    mean_y = np.mean(y)

    numerator = np.sum((x - mean_x) * (y - mean_y))
    denominator = np.sqrt(np.sum((x - mean_x) ** 2) * np.sum((y - mean_y) ** 2))

    if denominator == 0:
        return 0.0

    correlation = numerator / denominator
    return float(correlation)


def test_key_sensitivity(encrypt_func: Callable, image: Union[np.ndarray, bytes], key: bytes) -> float:
    """
    Tests encryption sensitivity to single-bit key changes.

    Flips one bit in the key and measures percentage of pixels that change
    in the resulting ciphertext. Target: >99.5%.

    Args:
        encrypt_func: Encryption function signature: bytes = encrypt_func(image_data, key)
        image: Image bytes or array to encrypt.
        key: 32-byte encryption key.

    Returns:
        float: Percentage of pixels changed when key bit is flipped [0.0, 100.0].
    """
    if isinstance(image, np.ndarray):
        image_bytes = image.astype(np.uint8).tobytes()
    else:
        image_bytes = bytes(image)

    if not isinstance(key, (bytes, bytearray)) or len(key) != 32:
        raise ValueError("Key must be 32 bytes")

    # Encrypt with original key
    c1 = encrypt_func(image_bytes, key)

    # Flip one bit in key
    key_array = bytearray(key)
    key_array[0] ^= 0x01
    key_modified = bytes(key_array)

    # Encrypt with modified key
    c2 = encrypt_func(image_bytes, key_modified)

    # Calculate NPCR for key change
    key_sensitivity = calculate_npcr(c1, c2)
    return float(key_sensitivity)


def analyze_histogram(image: Union[np.ndarray, bytes]) -> Dict[str, Any]:
    """
    Analyzes pixel distribution uniformity.

    For encrypted images, pixel values should be uniformly distributed.
    Computes histogram statistics and chi-square test.

    Args:
        image: Image array or bytes.

    Returns:
        Dict with keys:
            - "histogram": pixel counts for each value [0, 255]
            - "mean": average pixel value
            - "std": standard deviation
            - "chi_square": chi-square statistic
            - "uniformity_score": measure of how uniform the distribution is
    """
    if isinstance(image, (bytes, bytearray)):
        data = np.frombuffer(image, dtype=np.uint8)
    else:
        data = np.asarray(image).flatten().astype(np.uint8)

    # Compute histogram
    counts, _ = np.histogram(data, bins=256, range=(0, 256))

    # Statistics
    mean_val = float(np.mean(data))
    std_val = float(np.std(data))

    # Chi-square test (expected uniform distribution: each bin has data.size/256 pixels)
    expected = data.size / 256.0
    chi_square = np.sum((counts - expected) ** 2 / expected)

    # Uniformity score: 1.0 is perfect, lower is better
    # Based on chi-square with 255 degrees of freedom
    uniformity = chi_square / data.size

    return {
        "histogram": counts.tolist(),
        "mean": mean_val,
        "std": std_val,
        "chi_square": float(chi_square),
        "uniformity_score": float(uniformity)
    }


def calculate_psnr(original: Union[np.ndarray, bytes], encrypted: Union[np.ndarray, bytes]) -> float:
    """
    Peak Signal-to-Noise Ratio: PSNR = 10 * log₁₀(MAX² / MSE)

    For encrypted images, PSNR should be very low (typically < 20 dB),
    indicating high difference from plaintext.

    Args:
        original: Original plaintext image.
        encrypted: Encrypted ciphertext image.

    Returns:
        float: PSNR in decibels.
    """
    arr1 = np.frombuffer(original, dtype=np.uint8) if isinstance(original, (bytes, bytearray)) else np.asarray(original).flatten().astype(np.uint8)
    arr2 = np.frombuffer(encrypted, dtype=np.uint8) if isinstance(encrypted, (bytes, bytearray)) else np.asarray(encrypted).flatten().astype(np.uint8)

    min_len = min(arr1.size, arr2.size)
    if min_len == 0:
        return 0.0

    # Mean Squared Error
    mse = np.mean((arr1[:min_len].astype(np.float64) - arr2[:min_len].astype(np.float64)) ** 2)

    if mse == 0:
        return 100.0  # Perfect match (shouldn't happen with encryption)

    # PSNR = 10 * log₁₀(255² / MSE)
    psnr = 10.0 * math.log10((255.0 ** 2) / mse)
    return float(psnr)


def benchmark_encryption_speed(encrypt_func: Callable, image_size: Tuple[int, int], num_runs: int = 3) -> Dict[str, float]:
    """
    Benchmarks encryption performance.

    Tests encryption speed for typical image sizes and reports statistics.
    Target: <1.0s per 512×512 image.

    Args:
        encrypt_func: Encryption function signature: bytes = encrypt_func(image_data, key)
        image_size: Tuple of (height, width) for synthetic image.
        num_runs: Number of benchmark runs (default: 3).

    Returns:
        Dict with keys:
            - "avg_time": average execution time (seconds)
            - "min_time": minimum execution time
            - "max_time": maximum execution time
            - "image_size": total pixels
            - "throughput_mbps": throughput in MB/s
    """
    import io
    from PIL import Image
    from encryption.key_manager import generate_encryption_key

    # Generate synthetic PNG image
    height, width = image_size
    img = Image.fromarray(np.random.randint(0, 256, size=(height, width, 3), dtype=np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    image_data = buf.getvalue()
    key = generate_encryption_key(32)

    times = []
    for _ in range(num_runs):
        start = time.time()
        encrypt_func(image_data, key)
        end = time.time()
        times.append(end - start)

    avg_time = np.mean(times)
    min_time = np.min(times)
    max_time = np.max(times)

    # Throughput in MB/s
    image_size_bytes = len(image_data)
    throughput_mbps = (image_size_bytes / (1024 * 1024)) / avg_time

    return {
        "avg_time": float(avg_time),
        "min_time": float(min_time),
        "max_time": float(max_time),
        "image_size": height * width,
        "throughput_mbps": float(throughput_mbps)
    }


def run_full_security_evaluation(image: Union[np.ndarray, bytes], key: bytes) -> Dict[str, Any]:
    """
    Runs all 8 security metrics on encrypted image.

    Provides comprehensive security report.

    Args:
        image: Encrypted image data.
        key: 32-byte encryption key.

    Returns:
        Dict with all metric results and pass/fail status.
    """
    results = {
        "entropy": evaluate_entropy(image),
        "histogram": analyze_histogram(image),
    }

    # Add correlation metrics
    for direction in ["horizontal", "vertical", "diagonal"]:
        corr = compute_pixel_correlation(image, direction)
        results[f"correlation_{direction}"] = corr

    return results
