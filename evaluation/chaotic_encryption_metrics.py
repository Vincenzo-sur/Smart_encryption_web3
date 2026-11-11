"""
Cryptographic & Chaotic Encryption Evaluation Suite

Composes the shared evaluation metrics (Shannon Entropy, NPCR, UACI,
Histogram Chi-Square Uniformity, Adjacent Pixel Correlation) with
Key Sensitivity, PSNR, and multi-cipher comparative benchmarking
(`AES-256-GCM` vs. `Chaotic-Tent-Map` vs. `Hybrid-Chaotic-AES`).
"""

import io
import math
import time
from typing import Any, Callable, Dict, Tuple, Union

import numpy as np
from PIL import Image

from encryption.encrypt import (
    ALGORITHM_AES_GCM,
    ALGORITHM_CHAOTIC,
    ALGORITHM_HYBRID,
    SUPPORTED_ALGORITHMS,
    encrypt_image,
)
from encryption.key_manager import generate_encryption_key
from evaluation.correlation import calculate_adjacent_correlation
from evaluation.entropy import calculate_entropy
from evaluation.histogram import analyze_histogram
from evaluation.npcr import calculate_npcr
from evaluation.uaci import calculate_uaci

# Re-export canonical metric names for compatibility
evaluate_entropy = calculate_entropy


def compute_pixel_correlation(image: Union[np.ndarray, bytes], direction: str = "horizontal") -> float:
    """
    Computes adjacent pixel/byte correlation by reshaping 1D streams into a
    2D matrix when necessary and delegating to `calculate_adjacent_correlation`.
    """
    if isinstance(image, (bytes, bytearray)):
        data = np.frombuffer(image, dtype=np.uint8)
        if data.size < 4:
            return 0.0
        side = int(math.isqrt(data.size))
        matrix = data[: side * side].reshape(side, side)
    else:
        arr = np.asarray(image)
        if arr.ndim == 1:
            if arr.size < 4:
                return 0.0
            side = int(math.isqrt(arr.size))
            matrix = arr[: side * side].reshape(side, side)
        else:
            matrix = arr

    return calculate_adjacent_correlation(matrix, direction=direction)


def measure_key_sensitivity(
    encrypt_func: Callable[[bytes, bytes], bytes],
    image: Union[np.ndarray, bytes],
    key: bytes
) -> float:
    """
    Measures percentage of ciphertext bytes changed when a single bit of the
    256-bit key is flipped (Target: >99.5%).
    """
    if isinstance(image, np.ndarray):
        image_bytes = image.astype(np.uint8).tobytes()
    else:
        image_bytes = bytes(image)

    if not isinstance(key, (bytes, bytearray)) or len(key) != 32:
        raise ValueError("Key must be 32 bytes")

    c1 = encrypt_func(image_bytes, bytes(key))

    key_modified = bytearray(key)
    key_modified[0] ^= 0x01
    c2 = encrypt_func(image_bytes, bytes(key_modified))

    return float(calculate_npcr(c1, c2))


def calculate_psnr(original: Union[np.ndarray, bytes], encrypted: Union[np.ndarray, bytes]) -> float:
    """
    Computes Peak Signal-to-Noise Ratio (dB) between plaintext and ciphertext.
    Low PSNR (<20 dB) indicates strong visual obfuscation.
    """
    arr1 = (
        np.frombuffer(original, dtype=np.uint8)
        if isinstance(original, (bytes, bytearray))
        else np.asarray(original, dtype=np.uint8).flatten()
    )
    arr2 = (
        np.frombuffer(encrypted, dtype=np.uint8)
        if isinstance(encrypted, (bytes, bytearray))
        else np.asarray(encrypted, dtype=np.uint8).flatten()
    )

    min_len = min(arr1.size, arr2.size)
    if min_len == 0:
        return 0.0

    mse = float(np.mean((arr1[:min_len].astype(np.float64) - arr2[:min_len].astype(np.float64)) ** 2))
    if mse == 0.0:
        return 100.0

    return float(10.0 * math.log10((255.0 ** 2) / mse))


def benchmark_encryption_speed(
    encrypt_func: Callable[[bytes, bytes], bytes],
    image_size: Tuple[int, int] = (512, 512),
    num_runs: int = 3
) -> Dict[str, float]:
    """Benchmarks encryption latency and throughput on a synthetic RGB PNG image."""
    height, width = image_size
    rng = np.random.default_rng(42)
    img = Image.fromarray(rng.integers(0, 256, size=(height, width, 3), dtype=np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    image_data = buf.getvalue()
    key = generate_encryption_key(32)

    times = []
    for _ in range(num_runs):
        t0 = time.perf_counter()
        encrypt_func(image_data, key)
        t1 = time.perf_counter()
        times.append(t1 - t0)

    avg_time = float(np.mean(times))
    throughput_mbps = (len(image_data) / (1024 * 1024)) / avg_time if avg_time > 0 else 0.0

    return {
        "avg_time": avg_time,
        "min_time": float(np.min(times)),
        "max_time": float(np.max(times)),
        "image_size": height * width,
        "payload_bytes": len(image_data),
        "throughput_mbps": float(throughput_mbps),
    }


def run_full_security_evaluation(image: Union[np.ndarray, bytes], key: bytes) -> Dict[str, Any]:
    """Runs statistical distribution and correlation metrics on an encrypted payload."""
    results: Dict[str, Any] = {
        "entropy": evaluate_entropy(image),
        "histogram": analyze_histogram(image),
    }
    for direction in ("horizontal", "vertical", "diagonal"):
        results[f"correlation_{direction}"] = compute_pixel_correlation(image, direction)
    return results


def compare_cipher_algorithms(width: int = 128, height: int = 128) -> Dict[str, Dict[str, Any]]:
    """
    Runs comparative statistical, differential, and speed evaluation across
    AES-256-GCM, Chaotic-Tent-Map, and Hybrid-Chaotic-AES.
    """
    rng = np.random.default_rng(1234)
    arr = rng.integers(0, 256, size=(height, width, 3), dtype=np.uint8)
    buf = io.BytesIO()
    Image.fromarray(arr, mode="RGB").save(buf, format="PNG")
    raw_bytes = buf.getvalue()

    modified = bytearray(raw_bytes)
    modified[len(modified) // 2] ^= 0x01
    modified_bytes = bytes(modified)

    key = generate_encryption_key(32)
    report: Dict[str, Dict[str, Any]] = {}

    for algo in SUPPORTED_ALGORITHMS:
        enc_fn = lambda data, k, a=algo: encrypt_image(data, k, algorithm=a).ciphertext
        c1 = enc_fn(raw_bytes, key)
        c2 = enc_fn(modified_bytes, key)
        speed = benchmark_encryption_speed(enc_fn, (256, 256), num_runs=3)

        report[algo] = {
            "entropy": evaluate_entropy(c1),
            "npcr": calculate_npcr(c1, c2),
            "uaci": calculate_uaci(c1, c2),
            "key_sensitivity": measure_key_sensitivity(enc_fn, raw_bytes, key),
            "psnr_db": calculate_psnr(raw_bytes, c1),
            "correlation_horizontal": compute_pixel_correlation(c1, "horizontal"),
            "correlation_vertical": compute_pixel_correlation(c1, "vertical"),
            "correlation_diagonal": compute_pixel_correlation(c1, "diagonal"),
            "avg_time_s": speed["avg_time"],
            "throughput_mbps": speed["throughput_mbps"],
        }

    return report


if __name__ == "__main__":
    summary = compare_cipher_algorithms()
    for algo_name, metrics in summary.items():
        print(f"\n=== {algo_name} ===")
        for metric_name, val in metrics.items():
            print(f"  {metric_name:24s}: {val:.4f}")
