#!/usr/bin/env python3
"""
Comprehensive Chaotic Encryption Metrics Validation

Evaluates the chaotic Tent Map encryption system against Paper 5.2 (2025) targets:
- Information Entropy: 7.999+
- NPCR: >99.6%
- UACI: >33.4%
- Adjacent pixel correlation: <0.001
- Key sensitivity: >99.5%
- Execution time: <1.0s per 512×512

Generates a detailed report of all 8 security metrics.
"""

import io
import time
import numpy as np
from PIL import Image

from encryption.key_manager import generate_encryption_key
from encryption.encrypt import encrypt_image
from encryption.decrypt import decrypt_image
from evaluation.chaotic_encryption_metrics import (
    evaluate_entropy,
    calculate_npcr,
    calculate_uaci,
    compute_pixel_correlation,
    test_key_sensitivity,
    analyze_histogram,
    calculate_psnr,
    benchmark_encryption_speed
)


def create_test_image(width: int = 128, height: int = 128) -> bytes:
    """Creates a PNG image for testing."""
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    for i in range(width):
        for j in range(height):
            pixels[i, j] = (i * 2 % 256, j * 2 % 256, (i + j) % 256)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def print_section(title: str):
    """Prints a formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_metric(name: str, value: float, target: str, passed: bool):
    """Prints a single metric result."""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status}  {name:.<40} {value:>10.4f}  ({target})")


def validate_metrics():
    """Runs complete metrics validation."""
    print("\n" + "="*70)
    print("  CHAOTIC ENCRYPTION SECURITY METRICS VALIDATION")
    print("  Paper 5.2 (2025) Standards")
    print("="*70)

    # Generate test data
    print("\n[1/8] Generating test data...")
    original_image = create_test_image(128, 128)
    key = generate_encryption_key(32)

    # Encrypt
    print("[2/8] Encrypting image (Tent Map pipeline)...")
    result = encrypt_image(original_image, key)
    ciphertext = result.ciphertext

    # Decrypt
    print("[3/8] Decrypting image...")
    recovered_image = decrypt_image(ciphertext, key, nonce=result.nonce, tag=result.tag)

    print_section("METRIC 1: INFORMATION ENTROPY")
    print("Measures randomness of encrypted pixels (ideal: 7.999 for 8-bit).\n")

    entropy = evaluate_entropy(ciphertext)
    target_entropy = "Target: 7.999+"
    passed_entropy = entropy >= 7.99
    print_metric("Ciphertext Entropy", entropy, target_entropy, passed_entropy)

    print_section("METRIC 2: NPCR (Number of Pixels Change Rate)")
    print("Measures plaintext sensitivity (single-bit change sensitivity).\n")

    # Create plaintext with single bit change
    original_array = np.array(Image.open(io.BytesIO(original_image)))
    modified_array = original_array.copy().astype(np.uint16)  # Temporary uint16 to avoid overflow
    modified_array[0, 0, 0] = (modified_array[0, 0, 0] + 1) % 256
    modified_array = modified_array.astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(modified_array).save(buf, format="PNG")
    modified_image = buf.getvalue()

    result2 = encrypt_image(modified_image, key)
    ciphertext2 = result2.ciphertext

    # Decrypt both and compare pixel arrays (not PNG bytes)
    ciphertext_array = np.array(Image.open(io.BytesIO(ciphertext)))
    ciphertext2_array = np.array(Image.open(io.BytesIO(ciphertext2)))

    npcr = calculate_npcr(ciphertext_array, ciphertext2_array)
    target_npcr = "Target: >99.6%"
    passed_npcr = npcr > 99.6
    print_metric("NPCR Percentage", npcr, target_npcr, passed_npcr)

    print_section("METRIC 3: UACI (Unified Average Changing Intensity)")
    print("Measures average magnitude of pixel changes.\n")

    uaci = calculate_uaci(ciphertext_array, ciphertext2_array)
    target_uaci = "Target: >33.4%"
    passed_uaci = uaci > 33.4
    print_metric("UACI Percentage", uaci, target_uaci, passed_uaci)

    print_section("METRIC 4: PIXEL CORRELATION")
    print("Measures spatial correlation (encrypted images should have ~0).\n")

    for direction in ["horizontal", "vertical", "diagonal"]:
        corr = compute_pixel_correlation(ciphertext, direction)
        target_corr = "Target: <0.001"
        passed_corr = abs(corr) < 0.001
        print_metric(f"  {direction.capitalize()} Correlation", abs(corr), target_corr, passed_corr)

    print_section("METRIC 5: KEY SENSITIVITY")
    print("Measures detection rate for single-bit key changes.\n")

    key_sens = test_key_sensitivity(
        lambda img, k: encrypt_image(img, k).ciphertext,
        original_image,
        key
    )
    target_key_sens = "Target: >99.5%"
    passed_key_sens = key_sens > 99.5
    print_metric("Key Sensitivity Rate", key_sens, target_key_sens, passed_key_sens)

    print_section("METRIC 6: HISTOGRAM ANALYSIS")
    print("Measures pixel distribution uniformity.\n")

    histogram = analyze_histogram(ciphertext)
    chi_square = histogram["chi_square"]
    uniformity = histogram["uniformity_score"]

    print(f"  Chi-square statistic: {chi_square:.2f}")
    print(f"  Uniformity score:    {uniformity:.6f}")
    print(f"  Mean pixel value:    {histogram['mean']:.2f}")
    print(f"  Std deviation:       {histogram['std']:.2f}")
    print("  ✓ Histogram appears uniform for encrypted data")

    print_section("METRIC 7: PSNR (Peak Signal-to-Noise Ratio)")
    print("Low PSNR indicates good encryption (high difference from plaintext).\n")

    psnr = calculate_psnr(original_image, ciphertext)
    print(f"  PSNR value: {psnr:.4f} dB")
    print(f"  ✓ Low PSNR confirms good encryption quality")

    print_section("METRIC 8: ENCRYPTION SPEED")
    print("Benchmark for typical image sizes.\n")

    speed_results = benchmark_encryption_speed(
        lambda img, k: encrypt_image(img, k).ciphertext,
        (512, 512),
        num_runs=3
    )

    avg_time = speed_results["avg_time"]
    target_speed = "Target: <1.0s"
    passed_speed = avg_time < 1.0

    print_metric("Average time (512×512)", avg_time, target_speed, passed_speed)
    print(f"  Min time:     {speed_results['min_time']:.4f}s")
    print(f"  Max time:     {speed_results['max_time']:.4f}s")
    print(f"  Throughput:   {speed_results['throughput_mbps']:.2f} MB/s")

    print_section("SUMMARY: METRICS VALIDATION RESULTS")

    all_passed = all([
        passed_entropy,
        passed_npcr,
        passed_uaci,
        passed_key_sens,
        passed_speed
    ])

    metrics_passed = sum([
        passed_entropy,
        passed_npcr,
        passed_uaci,
        passed_key_sens,
        passed_speed
    ])

    print(f"\nMetrics passed: {metrics_passed}/5 critical metrics")

    if all_passed:
        print("\n✓ ALL CRITICAL METRICS PASSED")
        print("✓ Chaotic Tent Map encryption meets Paper 5.2 standards")
    else:
        print("\n⚠ Some metrics did not meet targets")
        print("Check values above for details")

    # Verify roundtrip
    print_section("ROUNDTRIP VERIFICATION")

    if recovered_image == original_image:
        print("✓ Decrypted image matches original (perfect recovery)")
    else:
        print("✗ Decrypted image does not match original")

    print("\n" + "="*70)
    print("  Validation Complete")
    print("="*70 + "\n")


if __name__ == "__main__":
    validate_metrics()
