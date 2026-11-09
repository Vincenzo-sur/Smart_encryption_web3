"""
Security and Access Control package.
"""

from security.authentication import (
    generate_challenge,
    verify_signature,
    AuthenticationError,
    InvalidSignatureError
)
from security.access_control import (
    AccessController,
    check_permission,
    verify_owner,
    grant_permission,
    revoke_permission,
    AccessControlError,
    UnauthorizedAccessError
)

__all__ = [
    "generate_challenge",
    "verify_signature",
    "AuthenticationError",
    "InvalidSignatureError",
    "AccessController",
    "check_permission",
    "verify_owner",
    "grant_permission",
    "revoke_permission",
    "AccessControlError",
    "UnauthorizedAccessError"
]
