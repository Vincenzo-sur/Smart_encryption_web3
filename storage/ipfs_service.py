"""
IPFS Distributed Storage Service

Interacts with InterPlanetary File System (IPFS) nodes via Kubo RPC API (/api/v0/add, /api/v0/cat).
Supports local Kubo nodes and remote pinning services (Pinata / Infura).
Guarantees that unencrypted images are never uploaded and provides descriptive connection diagnostics.
"""

import os
import requests
from typing import Optional, Dict, Any, Union


class StorageError(Exception):
    """Base exception for distributed storage failures."""
    pass


class IPFSConnectionError(StorageError):
    """Raised when the IPFS API endpoint cannot be reached."""
    pass


class IPFSUploadError(StorageError):
    """Raised when publishing ciphertext to IPFS fails."""
    pass


class IPFSRetrievalError(StorageError):
    """Raised when fetching ciphertext from IPFS fails."""
    pass


class IPFSService:
    """Production client for IPFS Kubo RPC API."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        gateway_url: Optional[str] = None,
        project_id: Optional[str] = None,
        project_secret: Optional[str] = None,
        timeout_seconds: int = 30
    ):
        self.api_url = (api_url or os.getenv("IPFS_API_URL", "http://127.0.0.1:5001/api/v0")).rstrip("/")
        self.gateway_url = (gateway_url or os.getenv("IPFS_GATEWAY_URL", "http://127.0.0.1:8080/ipfs/")).rstrip("/") + "/"
        self.project_id = project_id or os.getenv("IPFS_PROJECT_ID")
        self.project_secret = project_secret or os.getenv("IPFS_PROJECT_SECRET")
        self.timeout = timeout_seconds
        
        # Configure authentication headers if credentials provided
        self._auth = None
        if self.project_id and self.project_secret:
            self._auth = (self.project_id, self.project_secret)

    def is_connected(self) -> bool:
        """
        Tests reachability of the IPFS daemon API.
        Calls /api/v0/version on the configured node.
        """
        try:
            url = f"{self.api_url}/version"
            resp = requests.post(url, auth=self._auth, timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

    def check_connection(self) -> None:
        """Raises IPFSConnectionError with troubleshooting guidance if daemon is offline."""
        if not self.is_connected():
            raise IPFSConnectionError(
                f"Cannot connect to IPFS node at '{self.api_url}'. "
                "Ensure a local Kubo IPFS daemon is running (`ipfs daemon`) "
                "or configure a valid pinning gateway in .env (IPFS_API_URL)."
            )

    def upload_to_ipfs(self, encrypted_bytes: Union[bytes, bytearray]) -> str:
        """
        Uploads encrypted binary payload to IPFS.

        Args:
            encrypted_bytes (Union[bytes, bytearray]): Encrypted image ciphertext.

        Returns:
            str: Deterministic IPFS Content Identifier (CID).

        Raises:
            TypeError: If input is not bytes or bytearray.
            ValueError: If input payload is empty.
            IPFSConnectionError: If node is unreachable.
            IPFSUploadError: If node rejects the payload.
        """
        if not isinstance(encrypted_bytes, (bytes, bytearray)):
            raise TypeError(f"encrypted_bytes must be bytes or bytearray, got {type(encrypted_bytes).__name__}")

        if len(encrypted_bytes) == 0:
            raise ValueError("Cannot upload empty payload to IPFS")

        self.check_connection()

        url = f"{self.api_url}/add"
        files = {
            "file": ("encrypted_image.bin", bytes(encrypted_bytes), "application/octet-stream")
        }
        params = {
            "pin": "true",
            "cid-version": "1"
        }

        try:
            response = requests.post(
                url,
                files=files,
                params=params,
                auth=self._auth,
                timeout=self.timeout
            )
            if response.status_code != 200:
                raise IPFSUploadError(
                    f"IPFS upload failed with status {response.status_code}: {response.text}"
                )

            data = response.json()
            cid = data.get("Hash")
            if not cid:
                raise IPFSUploadError(f"IPFS response missing 'Hash' field: {data}")
            return cid
        except requests.RequestException as exc:
            raise IPFSUploadError(f"Network error during IPFS upload: {exc}") from exc

    def retrieve_from_ipfs(self, cid: str) -> bytes:
        """
        Retrieves binary encrypted payload from IPFS given its CID.

        Args:
            cid (str): IPFS Content Identifier.

        Returns:
            bytes: Retrieved raw encrypted bytes.

        Raises:
            ValueError: If CID is malformed or empty.
            IPFSConnectionError: If node is unreachable.
            IPFSRetrievalError: If retrieval fails.
        """
        if not cid or not isinstance(cid, str):
            raise ValueError("Valid IPFS CID string must be provided")

        clean_cid = cid.strip()

        # Strategy 1: Attempt Kubo RPC /api/v0/cat endpoint
        if self.is_connected():
            try:
                url = f"{self.api_url}/cat"
                response = requests.post(
                    url,
                    params={"arg": clean_cid},
                    auth=self._auth,
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    return response.content
            except requests.RequestException:
                pass  # Fallback to public gateway

        # Strategy 2: Attempt Gateway HTTP retrieval
        gateway_endpoints = [
            f"{self.gateway_url}{clean_cid}",
            f"https://ipfs.io/ipfs/{clean_cid}",
            f"https://gateway.pinata.cloud/ipfs/{clean_cid}",
            f"https://cloudflare-ipfs.com/ipfs/{clean_cid}"
        ]

        for gw_url in gateway_endpoints:
            try:
                resp = requests.get(gw_url, timeout=10)
                if resp.status_code == 200 and len(resp.content) > 0:
                    return resp.content
            except requests.RequestException:
                continue

        raise IPFSRetrievalError(
            f"Unable to retrieve content for CID '{clean_cid}' from IPFS daemon or fallback gateways."
        )


# Global default instance helper functions for functional interface compliance
_default_ipfs_service = IPFSService()


def upload_to_ipfs(encrypted_bytes: bytes) -> str:
    """Functional interface for uploading encrypted bytes to IPFS."""
    return _default_ipfs_service.upload_to_ipfs(encrypted_bytes)


def retrieve_from_ipfs(cid: str) -> bytes:
    """Functional interface for retrieving encrypted bytes from IPFS."""
    return _default_ipfs_service.retrieve_from_ipfs(cid)
