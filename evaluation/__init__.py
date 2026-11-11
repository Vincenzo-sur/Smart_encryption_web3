"""
Evaluation and Metrics package for cryptographic statistical and differential security assessment.
"""

from evaluation.entropy import calculate_entropy
from evaluation.histogram import (
    compute_histogram,
    calculate_variance_of_histogram,
    analyze_histogram,
)
from evaluation.correlation import calculate_adjacent_correlation
from evaluation.npcr import calculate_npcr
from evaluation.uaci import calculate_uaci
from evaluation.performance import benchmark_execution_time
from evaluation.chaotic_encryption_metrics import (
    calculate_psnr,
    measure_key_sensitivity,
    compare_cipher_algorithms,
)

__all__ = [
    "calculate_entropy",
    "compute_histogram",
    "calculate_variance_of_histogram",
    "analyze_histogram",
    "calculate_adjacent_correlation",
    "calculate_npcr",
    "calculate_uaci",
    "benchmark_execution_time",
    "calculate_psnr",
    "measure_key_sensitivity",
    "compare_cipher_algorithms",
]
