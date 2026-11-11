"""
Unit Tests for Authenticated Image Encryption, Decryption, and Key Management

Covers default AES-256-GCM behavior, strict nonce uniqueness, tamper rejection,
and multi-algorithm dispatch.
"""

import io
import pytest
from PIL import Image
from encryption.key_manager import generate_encryption_key, key_to_hex, hex_to_key, KeyManagementError
from encryption.encrypt import (
    encrypt_image,
    EncryptionResult,
    EncryptionError,
    ALGORITHM_AES_GCM,
    SUPPORTED_ALGORITHMS,
)
from encryption.decrypt import decrypt_image, AuthenticationError, DecryptionError


def create_synthetic_image_bytes(width: int = 64, height: int = 64) -> bytes:
    """Creates synthetic PNG image bytes for testing."""
    img = Image.new("RGB", (width, height), color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestKeyManager:
    def test_key_generation_length(self):
        key = generate_encryption_key(32)
        assert isinstance(key, bytes)
        assert len(key) == 32

    def test_key_hex_roundtrip(self):
        key = generate_encryption_key(32)
        hex_str = key_to_hex(key)
        recovered = hex_to_key(hex_str)
        assert recovered == key

    def test_invalid_key_length(self):
        with pytest.raises(ValueError):
            generate_encryption_key(10)


class TestEncryptionDecryption:
    @pytest.mark.parametrize("algorithm", SUPPORTED_ALGORITHMS)
    def test_roundtrip_recovery(self, algorithm):
        original_bytes = create_synthetic_image_bytes()
        key = generate_encryption_key(32)

        result = encrypt_image(original_bytes, key, algorithm=algorithm)
        assert isinstance(result, EncryptionResult)
        assert result.algorithm == algorithm
        assert len(result.nonce) == 12
        assert len(result.tag) == 16
        assert len(result.ciphertext) > 0
        assert result.ciphertext != original_bytes

        recovered_bytes = decrypt_image(
            ciphertext=result.ciphertext,
            key=key,
            nonce=result.nonce,
            tag=result.tag,
            algorithm=algorithm,
        )
        assert recovered_bytes == original_bytes

    @pytest.mark.parametrize("algorithm", SUPPORTED_ALGORITHMS)
    def test_unpacking_interface(self, algorithm):
        """Tests that `ciphertext, metadata = encrypt_image(...)` preserves algorithm dispatch."""
        original_bytes = create_synthetic_image_bytes()
        key = generate_encryption_key(32)

        ciphertext, metadata = encrypt_image(original_bytes, key, algorithm=algorithm)
        assert isinstance(ciphertext, bytes)
        assert isinstance(metadata, dict)
        assert metadata["algorithm"] == algorithm
        assert "nonce" in metadata
        assert "tag" in metadata

        recovered = decrypt_image(ciphertext, key, metadata)
        assert recovered == original_bytes

    @pytest.mark.parametrize("algorithm", SUPPORTED_ALGORITHMS)
    def test_nonce_uniqueness(self, algorithm):
        """Ensures consecutive encryptions under the same key generate unique nonces and ciphertexts."""
        data = create_synthetic_image_bytes()
        key = generate_encryption_key(32)

        r1 = encrypt_image(data, key, algorithm=algorithm)
        r2 = encrypt_image(data, key, algorithm=algorithm)

        assert r1.nonce != r2.nonce
        assert r1.ciphertext != r2.ciphertext

    @pytest.mark.parametrize("algorithm", SUPPORTED_ALGORITHMS)
    def test_tampered_ciphertext_fails(self, algorithm):
        """Modifying any byte of the ciphertext must trigger AuthenticationError."""
        original_bytes = create_synthetic_image_bytes()
        key = generate_encryption_key(32)
        result = encrypt_image(original_bytes, key, algorithm=algorithm)

        corrupted = bytearray(result.ciphertext)
        corrupted[0] ^= 0xFF

        with pytest.raises(AuthenticationError):
            decrypt_image(
                ciphertext=bytes(corrupted),
                key=key,
                nonce=result.nonce,
                tag=result.tag,
                algorithm=algorithm,
            )

    @pytest.mark.parametrize("algorithm", SUPPORTED_ALGORITHMS)
    def test_incorrect_key_fails(self, algorithm):
        """Decrypting with a different 256-bit key must fail authentication."""
        original_bytes = create_synthetic_image_bytes()
        key1 = generate_encryption_key(32)
        key2 = generate_encryption_key(32)

        result = encrypt_image(original_bytes, key1, algorithm=algorithm)

        with pytest.raises(AuthenticationError):
            decrypt_image(
                ciphertext=result.ciphertext,
                key=key2,
                nonce=result.nonce,
                tag=result.tag,
                algorithm=algorithm,
            )

    def test_default_algorithm_is_aes_gcm(self):
        data = create_synthetic_image_bytes()
        key = generate_encryption_key(32)
        result = encrypt_image(data, key)
        assert result.algorithm == ALGORITHM_AES_GCM

    def test_empty_image_error(self):
        key = generate_encryption_key(32)
        with pytest.raises(ValueError):
            encrypt_image(b"", key)
