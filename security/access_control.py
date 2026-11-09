"""
Security Access Control Module

Evaluates role-based access control (RBAC) permissions against on-chain smart contract state.
Ensures that unauthorized parties are strictly forbidden from obtaining decrypted image payloads.
"""

from typing import Optional, Dict, Set
from blockchain.blockchain_service import BlockchainService, BlockchainError


class AccessControlError(Exception):
    """Base exception for access control violations."""
    pass


class UnauthorizedAccessError(AccessControlError):
    """Raised when an unauthorized entity attempts to access a protected image."""
    pass


class AccessController:
    """Evaluates and manages image access rights via BlockchainService."""

    def __init__(self, blockchain_service: Optional[BlockchainService] = None):
        self.blockchain_service = blockchain_service or BlockchainService()
        # In-memory backup ACL registry for Day 1 isolated testing before contract deployment
        self._local_permissions: Dict[str, Set[str]] = {}
        self._local_owners: Dict[str, str] = {}

    def set_local_owner(self, image_id: str, owner_address: str) -> None:
        """Registers ownership in the local fallback ACL."""
        clean_id = image_id.lower()
        self._local_owners[clean_id] = owner_address.lower()
        if clean_id not in self._local_permissions:
            self._local_permissions[clean_id] = set()

    def grant_permission(
        self,
        image_id: str,
        user_address: str,
        sender_address: str,
        private_key: Optional[str] = None
    ) -> str:
        """
        Grants permission to user_address.
        Executes on-chain via BlockchainService if contract is active, or updates local ACL.
        """
        clean_id = image_id.lower()
        clean_user = user_address.lower()
        clean_sender = sender_address.lower()

        # If connected to blockchain contract, delegate to on-chain state
        if self.blockchain_service.is_connected() and self.blockchain_service.contract:
            return self.blockchain_service.grant_access(image_id, user_address, sender_address, private_key)

        # Fallback local registry check
        owner = self._local_owners.get(clean_id)
        if owner and owner != clean_sender:
            raise UnauthorizedAccessError(f"Address '{sender_address}' is not the owner of image '{image_id}'")

        if clean_id not in self._local_permissions:
            self._local_permissions[clean_id] = set()
        self._local_permissions[clean_id].add(clean_user)
        return "local_tx_granted"

    def revoke_permission(
        self,
        image_id: str,
        user_address: str,
        sender_address: str,
        private_key: Optional[str] = None
    ) -> str:
        """
        Revokes permission from user_address.
        """
        clean_id = image_id.lower()
        clean_user = user_address.lower()
        clean_sender = sender_address.lower()

        if self.blockchain_service.is_connected() and self.blockchain_service.contract:
            return self.blockchain_service.revoke_access(image_id, user_address, sender_address, private_key)

        owner = self._local_owners.get(clean_id)
        if owner and owner != clean_sender:
            raise UnauthorizedAccessError(f"Address '{sender_address}' is not the owner of image '{image_id}'")

        if clean_id in self._local_permissions:
            self._local_permissions[clean_id].discard(clean_user)
        return "local_tx_revoked"

    def verify_owner(self, user_address: str, image_id: str) -> bool:
        """Verifies if user_address is the recorded owner."""
        clean_id = image_id.lower()
        clean_user = user_address.lower()

        if self.blockchain_service.is_connected() and self.blockchain_service.contract:
            try:
                return self.blockchain_service.verify_ownership(image_id, user_address)
            except Exception:
                pass

        return self._local_owners.get(clean_id) == clean_user

    def check_permission(self, user_address: str, image_id: str) -> bool:
        """
        Checks whether user_address is either the owner or an authorized recipient.

        Args:
            user_address (str): Checksummed or lowercase Ethereum address.
            image_id (str): Identifier of the image.

        Returns:
            bool: True if authorized, False otherwise.
        """
        clean_id = image_id.lower()
        clean_user = user_address.lower()

        if self.blockchain_service.is_connected() and self.blockchain_service.contract:
            try:
                return self.blockchain_service.has_access(image_id, user_address)
            except Exception:
                pass

        # Check local ACL
        if self._local_owners.get(clean_id) == clean_user:
            return True
        return clean_user in self._local_permissions.get(clean_id, set())


# Default instance helper functions
_default_access_controller = AccessController()


def check_permission(user_address: str, image_id: str) -> bool:
    """Helper function to check user access rights."""
    return _default_access_controller.check_permission(user_address, image_id)


def verify_owner(user_address: str, image_id: str) -> bool:
    """Helper function to check ownership."""
    return _default_access_controller.verify_owner(user_address, image_id)


def grant_permission(image_id: str, user_address: str, sender_address: str, private_key: Optional[str] = None) -> str:
    """Helper function to grant access."""
    return _default_access_controller.grant_permission(image_id, user_address, sender_address, private_key)


def revoke_permission(image_id: str, user_address: str, sender_address: str, private_key: Optional[str] = None) -> str:
    """Helper function to revoke access."""
    return _default_access_controller.revoke_permission(image_id, user_address, sender_address, private_key)
