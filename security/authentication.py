"""
Security Authentication Module: Ethereum Wallet Identity Verification

Implements challenge-response authentication using cryptographic signatures (EIP-191).
Recovers the signer's public Ethereum address from personal_sign messages without trusting
arbitrary user-supplied client addresses.
"""

import time
import secrets
from typing import Optional, Tuple
from eth_account import Account
from eth_account.messages import encode_defunct


class AuthenticationError(Exception):
    """Base exception for identity and signature authentication failures."""
    pass


class InvalidSignatureError(AuthenticationError):
    """Raised when an Ethereum wallet signature is invalid or recovery fails."""
    pass


def generate_challenge(wallet_address: str, expiration_seconds: int = 300) -> str:
    """
    Generates a cryptographically strong, timestamped authentication challenge.

    Args:
        wallet_address (str): The claiming Ethereum address.
        expiration_seconds (int): Validity window for the challenge.

    Returns:
        str: Challenge message text for the user to sign in their wallet.
    """
    nonce = secrets.token_hex(16)
    timestamp = int(time.time())
    expires_at = timestamp + expiration_seconds
    return (
        f"Authenticate with SmartEncryptionWeb3:\n"
        f"Wallet: {wallet_address.lower()}\n"
        f"Nonce: {nonce}\n"
        f"IssuedAt: {timestamp}\n"
        f"ExpiresAt: {expires_at}"
    )


def verify_signature(
    message: str,
    signature: str,
    expected_address: str,
    check_expiration: bool = True
) -> bool:
    """
    Recovers the public address from an EIP-191 signed message and compares
    it against the expected address.

    Args:
        message (str): The exact text that was signed.
        signature (str): The hex-encoded signature (0x...).
        expected_address (str): The claimed Ethereum address.
        check_expiration (bool): Whether to parse and enforce 'ExpiresAt'.

    Returns:
        bool: True if signature matches expected_address and is unexpired.

    Raises:
        InvalidSignatureError: If signature format is invalid or address mismatch.
    """
    if not message or not signature or not expected_address:
        raise InvalidSignatureError("Message, signature, and expected_address must be provided")

    # Optional expiration check if timestamp is embedded
    if check_expiration and "ExpiresAt: " in message:
        try:
            expires_line = [line for line in message.splitlines() if line.startswith("ExpiresAt: ")][0]
            expires_at = int(expires_line.split("ExpiresAt: ")[1].strip())
            if time.time() > expires_at:
                raise InvalidSignatureError("Authentication challenge has expired")
        except (IndexError, ValueError) as exc:
            raise InvalidSignatureError(f"Malformed challenge timestamp: {exc}") from exc

    try:
        clean_sig = signature.strip()
        encoded_message = encode_defunct(text=message)
        recovered_address = Account.recover_message(encoded_message, signature=clean_sig)
        
        is_match = recovered_address.lower() == expected_address.lower()
        if not is_match:
            raise InvalidSignatureError(
                f"Signature address mismatch: recovered '{recovered_address}', expected '{expected_address}'"
            )
        return True
    except InvalidSignatureError:
        raise
    except Exception as exc:
        raise InvalidSignatureError(f"Cryptographic signature recovery failed: {exc}") from exc
