"""
Cryptographic Performance Benchmarking Module

Measures throughput (MB/s) and latency (milliseconds) for encryption and decryption pipelines.
"""

import time
from typing import Callable, Any, Dict, Tuple


def benchmark_execution_time(func: Callable, *args, iterations: int = 10, **kwargs) -> Dict[str, float]:
    """
    Measures the average latency of a function across multiple iterations.

    Returns:
        Dict containing 'average_ms', 'min_ms', 'max_ms', 'total_ms'.
    """
    times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        func(*args, **kwargs)
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000.0)

    return {
        "iterations": iterations,
        "average_ms": sum(times) / len(times),
        "min_ms": min(times),
        "max_ms": max(times),
        "total_ms": sum(times)
    }
