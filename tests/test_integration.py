"""
End-to-End Pipeline and Security Verification Tests
"""

import io
import pytest
from PIL import Image
from eth_account import Account
from eth_account.messages import encode_defunct

from encryption.key_manager import generate_encryption_key, key_to_hex, hex_to_key
from encryption.encrypt import encrypt_image
from encryption.decrypt import decrypt_image, AuthenticationError
from hashing.hash_utils import calculate_hash
from security.authentication import generate_challenge, verify_signature, InvalidSignatureError
from security.access_control import AccessController, UnauthorizedAccessError
from evaluation.entropy import calculate_entropy
from evaluation.npcr import calculate_npcr
from evaluation.uaci import calculate_uaci


def create_sample_image() -> bytes:
    # Generate a 128x128 synthetic image with color gradients to provide sufficient entropy sample space
    img = Image.new("RGB", (128, 128))
    pixels = img.load()
    for i in range(128):
        for j in range(128):
            pixels[i, j] = (i * 2 % 256, j * 2 % 256, (i + j) % 256)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestSecurityAndAuth:
    def test_eip191_signature_verification(self):
        # Generate an ephemeral test wallet
        acct = Account.create()
        wallet_address = acct.address
        private_key = acct.key.hex()

        challenge = generate_challenge(wallet_address, expiration_seconds=60)
        encoded_msg = encode_defunct(text=challenge)
        signed = acct.sign_message(encoded_msg)
        sig_hex = signed.signature.hex()

        # Validate with verify_signature
        is_valid = verify_signature(challenge, sig_hex, wallet_address)
        assert is_valid is True

    def test_impersonation_signature_rejection(self):
        acct_legit = Account.create()
        acct_attacker = Account.create()

        challenge = generate_challenge(acct_legit.address, expiration_seconds=60)
        # Attacker signs the challenge
        signed_by_attacker = acct_attacker.sign_message(encode_defunct(text=challenge))

        with pytest.raises(InvalidSignatureError):
            verify_signature(challenge, signed_by_attacker.signature.hex(), acct_legit.address)


class TestFullCryptographicPipeline:
    def test_encryption_hashing_decryption_pipeline(self):
        # 1. Ingest image
        raw_image = create_sample_image()
        key = generate_encryption_key(32)

        # 2. Encrypt
        enc_result = encrypt_image(raw_image, key)
        ciphertext = enc_result.ciphertext
        metadata = enc_result.to_metadata()

        # 3. Calculate SHA-256
        cipher_hash = calculate_hash(ciphertext)
        assert len(cipher_hash) == 64

        # 4. Measure Shannon Entropy
        plaintext_entropy = calculate_entropy(raw_image)
        cipher_entropy = calculate_entropy(ciphertext)
        # Ciphertext entropy should be significantly high (> 7.0 for random AES-GCM bytes)
        assert cipher_entropy > 7.0

        # 5. Access Control check
        ac = AccessController()
        image_id = "0x" + cipher_hash[:32]
        owner_wallet = "0x1111111111111111111111111111111111111111"
        unauth_wallet = "0x9999999999999999999999999999999999999999"
        ac.set_local_owner(image_id, owner_wallet)

        assert ac.check_permission(owner_wallet, image_id) is True
        assert ac.check_permission(unauth_wallet, image_id) is False

        # Grant access
        ac.grant_permission(image_id, unauth_wallet, owner_wallet)
        assert ac.check_permission(unauth_wallet, image_id) is True

        # Revoke access
        ac.revoke_permission(image_id, unauth_wallet, owner_wallet)
        assert ac.check_permission(unauth_wallet, image_id) is False

        # 6. Decrypt
        recovered = decrypt_image(ciphertext, key, metadata)
        assert recovered == raw_image
