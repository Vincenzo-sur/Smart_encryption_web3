"""
Unit Tests for SHA-256 Cryptographic Hashing
"""

import pytest
from hashing.hash_utils import calculate_hash, calculate_hash_bytes


class TestHashing:
    def test_known_hash_output(self):
        # Known SHA-256 for b"hello world"
        # 64-char hex: b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9
        data = b"hello world"
        digest_hex = calculate_hash(data)
        assert digest_hex == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        assert len(digest_hex) == 64

    def test_hash_bytes_output(self):
        data = b"blockchain-assisted-image-encryption"
        raw_digest = calculate_hash_bytes(data)
        assert isinstance(raw_digest, bytes)
        assert len(raw_digest) == 32
        assert raw_digest.hex() == calculate_hash(data)

    def test_different_inputs_produce_different_digests(self):
        d1 = calculate_hash(b"Image Payload Alpha")
        d2 = calculate_hash(b"Image Payload Beta")
        assert d1 != d2

    def test_type_error_on_non_bytes(self):
        with pytest.raises(TypeError):
            calculate_hash("not bytes input")  # type: ignore
