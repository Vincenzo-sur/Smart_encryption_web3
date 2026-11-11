"""
Dedicated Verification Tests for Hardened Chaotic Tent Map & Hybrid Encryption,
Statistical Metrics, Format Preservation, and REST API Algorithm Dispatch.
"""

import io
import numpy as np
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from backend.main import app
from encryption.encrypt import (
    ALGORITHM_AES_GCM,
    ALGORITHM_CHAOTIC,
    ALGORITHM_HYBRID,
    SUPPORTED_ALGORITHMS,
    encrypt_image,
)
from encryption.decrypt import AuthenticationError, decrypt_image
from encryption.key_manager import generate_encryption_key
from encryption.prime_circulant_substitution import PrimeCirculantSubstitution
from encryption.sine_map_permutation import SineMapPermutation
from encryption.tent_map_diffusion import TentMapDiffusion
from evaluation.chaotic_encryption_metrics import (
    calculate_psnr,
    compare_cipher_algorithms,
    compute_pixel_correlation,
    evaluate_entropy,
    measure_key_sensitivity,
)
from evaluation.npcr import calculate_npcr
from evaluation.uaci import calculate_uaci


def _make_gradient_bytes(fmt: str = "PNG", mode: str = "RGB", size=(128, 128)) -> bytes:
    w, h = size
    arr = np.zeros((h, w, 4 if mode == "RGBA" else 3), dtype=np.uint8)
    y_idx = np.arange(h)[:, None]
    x_idx = np.arange(w)[None, :]
    arr[:, :, 0] = (x_idx * 2) % 256
    arr[:, :, 1] = (y_idx * 2) % 256
    arr[:, :, 2] = (x_idx + y_idx) % 256
    if mode == "RGBA":
        arr[:, :, 3] = 200
    img = Image.fromarray(arr, mode=mode)
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def _make_textured_png_bytes(size=(128, 128)) -> bytes:
    """Creates a realistic high-detail PNG (>=32KB) suitable for 256-bin entropy tests."""
    w, h = size
    rng = np.random.default_rng(99)
    arr = rng.integers(0, 256, size=(h, w, 3), dtype=np.uint8)
    buf = io.BytesIO()
    Image.fromarray(arr, mode="RGB").save(buf, format="PNG")
    return buf.getvalue()


class TestChaoticPrimitives:
    def test_sine_map_bounds_and_lossless_2d_3d_roundtrip(self):
        key = generate_encryption_key(32)
        nonce = b"\x01" * 12
        rng = np.random.default_rng(7)
        arr3d = rng.integers(0, 256, size=(32, 32, 3), dtype=np.uint8)

        permuter = SineMapPermutation(key, (32, 32), nonce=nonce)
        assert 0.87 <= permuter.mu <= 0.999
        assert 0.0 < permuter.x0 < 1.0

        permuted = permuter.permute_pixels(arr3d)
        assert permuted.dtype == np.uint8
        assert permuted.shape == arr3d.shape
        restored = permuter.inverse_permute(permuted)
        assert np.array_equal(restored, arr3d)

    def test_prime_circulant_bijective_sbox(self):
        key = generate_encryption_key(32)
        sub = PrimeCirculantSubstitution(key, nonce=b"\x02" * 12)
        assert len(set(sub.substitution_table.tolist())) == 256
        arr = np.arange(256, dtype=np.uint8)
        assert np.array_equal(sub.inverse_substitute(sub.substitute_pixels(arr)), arr)

    def test_tent_map_no_zero_collapse_on_large_payload(self):
        """Regression test: Tent Map keystream must stay high-entropy well past 53 bytes."""
        key = generate_encryption_key(32)
        diffuser = TentMapDiffusion(key, nonce=b"\x03" * 12)
        seq = diffuser._generate_tent_sequence(65536)
        tail = seq[1024:]
        assert np.count_nonzero(tail) > len(tail) * 0.95
        assert evaluate_entropy(tail) > 7.98

        payload = np.full(16384, 42, dtype=np.uint8)
        diffused = diffuser.diffuse_image(payload)
        assert evaluate_entropy(diffused) > 7.95
        assert np.array_equal(diffuser.inverse_diffuse(diffused), payload)


class TestFormatPreservationAndAEAD:
    @pytest.mark.parametrize("algorithm", [ALGORITHM_CHAOTIC, ALGORITHM_HYBRID])
    @pytest.mark.parametrize(
        ("fmt", "mode"),
        [("PNG", "RGB"), ("PNG", "RGBA"), ("JPEG", "RGB")],
    )
    def test_exact_byte_for_byte_recovery_across_formats(self, algorithm, fmt, mode):
        original = _make_gradient_bytes(fmt=fmt, mode=mode, size=(64, 64))
        key = generate_encryption_key(32)

        result = encrypt_image(original, key, algorithm=algorithm)
        # Ciphertext must NOT contain PNG/JPEG magic headers
        assert not result.ciphertext.startswith(b"\x89PNG")
        assert not result.ciphertext.startswith(b"\xff\xd8\xff")

        recovered = decrypt_image(result.ciphertext, key, result.to_metadata())
        assert recovered == original

    @pytest.mark.parametrize("algorithm", SUPPORTED_ALGORITHMS)
    def test_associated_data_authenticated(self, algorithm):
        original = _make_gradient_bytes()
        key = generate_encryption_key(32)
        aad = b"owner=0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"

        result = encrypt_image(original, key, associated_data=aad, algorithm=algorithm)
        assert decrypt_image(result.ciphertext, key, result.to_metadata(), associated_data=aad) == original

        with pytest.raises(AuthenticationError):
            decrypt_image(result.ciphertext, key, result.to_metadata(), associated_data=b"owner=attacker")


class TestChaoticSecurityMetrics:
    @pytest.mark.parametrize("algorithm", [ALGORITHM_CHAOTIC, ALGORITHM_HYBRID])
    def test_statistical_and_differential_targets(self, algorithm):
        original = _make_textured_png_bytes(size=(128, 128))
        modified = bytearray(original)
        modified[-17] ^= 0x01  # Flip bit near end to verify full-buffer bidirectional avalanche
        key = generate_encryption_key(32)

        enc_fn = lambda data, k: encrypt_image(data, k, algorithm=algorithm).ciphertext
        c1 = enc_fn(original, key)
        c2 = enc_fn(bytes(modified), key)

        assert evaluate_entropy(c1) > 7.98
        assert calculate_npcr(c1, c2) > 99.0
        assert 28.0 < calculate_uaci(c1, c2) < 39.0
        assert measure_key_sensitivity(enc_fn, original, key) > 99.0
        assert abs(compute_pixel_correlation(c1, "horizontal")) < 0.05
        assert calculate_psnr(original, c1) < 20.0

    def test_comparative_benchmark_runs_cleanly(self):
        summary = compare_cipher_algorithms(width=64, height=64)
        assert set(summary.keys()) == set(SUPPORTED_ALGORITHMS)
        for metrics in summary.values():
            assert metrics["entropy"] > 7.95


class TestBackendAlgorithmDispatch:
    @pytest.mark.parametrize("algorithm", SUPPORTED_ALGORITHMS)
    def test_api_upload_verify_and_decrypt_all_ciphers(self, algorithm):
        client = TestClient(app)
        image_bytes = _make_gradient_bytes(size=(64, 64))
        owner = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"

        upload_resp = client.post(
            "/upload",
            files={"file": ("sample.png", image_bytes, "image/png")},
            data={"owner_address": owner, "algorithm": algorithm},
        )
        assert upload_resp.status_code == 200
        up_data = upload_resp.json()
        assert up_data["encryption_metadata"]["algorithm"] == algorithm

        verify_resp = client.get(f"/images/{up_data['image_id']}/verify")
        assert verify_resp.status_code == 200
        assert verify_resp.json()["is_valid"] is True

        decrypt_resp = client.post(
            f"/images/{up_data['image_id']}/decrypt",
            json={
                "key_hex": up_data["key_hex"],
                "nonce_hex": up_data["encryption_metadata"]["nonce"],
                "tag_hex": up_data["encryption_metadata"]["tag"],
                "requester_address": owner,
            },
        )
        assert decrypt_resp.status_code == 200
        assert decrypt_resp.content == image_bytes
