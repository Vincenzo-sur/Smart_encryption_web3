"""
Blockchain Web3 Service Layer

Provides high-level Python integration with Ethereum EVM smart contracts (Ganache / Mainnet).
Handles connection health, transaction creation, gas management, receipt polling,
and contract state queries for ImageRegistry.sol.
"""

import os
import json
from dataclasses import dataclass
from typing import Optional, Dict, Any, Union
from web3 import Web3
from web3.exceptions import Web3Exception


class BlockchainError(Exception):
    """Base exception for blockchain service operations."""
    pass


class BlockchainConnectionError(BlockchainError):
    """Raised when the Ethereum node RPC is unreachable."""
    pass


class ImageNotFoundError(BlockchainError):
    """Raised when querying a non-existent image record."""
    pass


class BlockchainTransactionError(BlockchainError):
    """Raised when a smart contract transaction reverts or fails."""
    pass


@dataclass(frozen=True)
class BlockchainImageRecord:
    """Strongly typed representation of an on-chain ImageRecord."""
    image_id: str
    owner: str
    image_hash: str
    ipfs_cid: str
    timestamp: int
    exists: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "image_id": self.image_id,
            "owner": self.owner,
            "image_hash": self.image_hash,
            "ipfs_cid": self.ipfs_cid,
            "timestamp": self.timestamp,
            "exists": self.exists
        }


# Standard ABI for ImageRegistry.sol
IMAGE_REGISTRY_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "_imageHash", "type": "bytes32"},
            {"internalType": "string", "name": "_ipfsCid", "type": "string"}
        ],
        "name": "registerImage",
        "outputs": [{"internalType": "bytes32", "name": "imageId", "type": "bytes32"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "_imageId", "type": "bytes32"}],
        "name": "getImageDetails",
        "outputs": [
            {"internalType": "address", "name": "owner", "type": "address"},
            {"internalType": "bytes32", "name": "imageHash", "type": "bytes32"},
            {"internalType": "string", "name": "ipfsCid", "type": "string"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"internalType": "bool", "name": "exists", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "_imageId", "type": "bytes32"},
            {"internalType": "address", "name": "_grantee", "type": "address"}
        ],
        "name": "grantAccess",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "_imageId", "type": "bytes32"},
            {"internalType": "address", "name": "_revokedUser", "type": "address"}
        ],
        "name": "revokeAccess",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "_imageId", "type": "bytes32"},
            {"internalType": "address", "name": "_claimant", "type": "address"}
        ],
        "name": "verifyOwnership",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "_imageId", "type": "bytes32"},
            {"internalType": "address", "name": "_user", "type": "address"}
        ],
        "name": "hasAccess",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "bytes32", "name": "imageId", "type": "bytes32"},
            {"indexed": True, "internalType": "address", "name": "owner", "type": "address"},
            {"indexed": False, "internalType": "bytes32", "name": "imageHash", "type": "bytes32"},
            {"indexed": False, "internalType": "string", "name": "ipfsCid", "type": "string"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"}
        ],
        "name": "ImageRegistered",
        "type": "event"
    }
]


class BlockchainService:
    """Service client for managing Ethereum RPC connections and ImageRegistry interactions."""

    def __init__(
        self,
        rpc_url: Optional[str] = None,
        contract_address: Optional[str] = None,
        abi: Optional[list] = None
    ):
        self.rpc_url = rpc_url or os.getenv("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545")
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.contract_address = contract_address or os.getenv("IMAGE_REGISTRY_CONTRACT_ADDRESS")
        self.abi = abi or IMAGE_REGISTRY_ABI
        self.contract = None

        if self.contract_address and self.w3.is_address(self.contract_address):
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.contract_address),
                abi=self.abi
            )

    def is_connected(self) -> bool:
        """Returns True if the underlying Web3 provider is reachable and synced."""
        try:
            return self.w3.is_connected()
        except Exception:
            return False

    def check_connection(self) -> None:
        """Raises BlockchainConnectionError if the node is offline."""
        if not self.is_connected():
            raise BlockchainConnectionError(
                f"Cannot connect to Ethereum RPC endpoint at {self.rpc_url}. "
                "Ensure Ganache or an EVM testnet daemon is running."
            )

    def _normalize_bytes32(self, val: Union[str, bytes]) -> bytes:
        """Converts string hex (0x...) or raw bytes to a 32-byte binary object."""
        if isinstance(val, (bytes, bytearray)):
            if len(val) != 32:
                raise ValueError(f"bytes32 must be exactly 32 bytes (got {len(val)})")
            return bytes(val)
        elif isinstance(val, str):
            clean = val.strip()
            if clean.startswith("0x") or clean.startswith("0X"):
                clean = clean[2:]
            raw = bytes.fromhex(clean)
            if len(raw) != 32:
                raise ValueError(f"Hex string does not decode to 32 bytes (got {len(raw)})")
            return raw
        raise TypeError(f"Expected bytes or hex string for bytes32, got {type(val).__name__}")

    def register_image(
        self,
        image_hash: Union[str, bytes],
        ipfs_cid: str,
        sender_address: Optional[str] = None,
        private_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Submits registerImage transaction to ImageRegistry.sol.

        Returns:
            Dict containing 'image_id', 'transaction_hash', 'block_number'.
        """
        self.check_connection()
        if not self.contract:
            raise BlockchainError("Contract address is not configured. Deploy contract first.")

        hash_bytes32 = self._normalize_bytes32(image_hash)
        
        # Determine caller address
        if not sender_address:
            sender_address = os.getenv("DEPLOYER_ADDRESS") or self.w3.eth.accounts[0]
        
        checksum_sender = Web3.to_checksum_address(sender_address)
        
        try:
            tx_data = self.contract.functions.registerImage(hash_bytes32, ipfs_cid)
            
            if private_key:
                nonce = self.w3.eth.get_transaction_count(checksum_sender)
                tx_build = tx_data.build_transaction({
                    "from": checksum_sender,
                    "nonce": nonce,
                    "gas": 300000,
                    "gasPrice": self.w3.eth.gas_price
                })
                signed_tx = self.w3.eth.account.sign_transaction(tx_build, private_key=private_key)
                tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            else:
                # Direct Ganache unlocked account transaction
                tx_hash = tx_data.transact({"from": checksum_sender, "gas": 300000})

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status != 1:
                raise BlockchainTransactionError(f"Transaction failed or reverted on chain. Hash: {tx_hash.hex()}")

            # Parse ImageRegistered event from receipt
            events = self.contract.events.ImageRegistered().process_receipt(receipt)
            image_id = events[0]["args"]["imageId"].hex() if events else None

            return {
                "image_id": "0x" + image_id if image_id and not image_id.startswith("0x") else image_id,
                "transaction_hash": tx_hash.hex(),
                "block_number": receipt.blockNumber
            }
        except Exception as exc:
            raise BlockchainTransactionError(f"Failed to register image on-chain: {exc}") from exc

    def get_image_details(self, image_id: Union[str, bytes]) -> BlockchainImageRecord:
        """Queries on-chain ImageRecord by its image_id."""
        self.check_connection()
        if not self.contract:
            raise BlockchainError("Contract address is not configured.")

        id_bytes32 = self._normalize_bytes32(image_id)

        try:
            owner, img_hash, ipfs_cid, timestamp, exists = self.contract.functions.getImageDetails(id_bytes32).call()
            if not exists:
                raise ImageNotFoundError(f"Image ID '{image_id}' was not found on-chain.")

            return BlockchainImageRecord(
                image_id="0x" + id_bytes32.hex(),
                owner=owner,
                image_hash="0x" + img_hash.hex(),
                ipfs_cid=ipfs_cid,
                timestamp=timestamp,
                exists=exists
            )
        except Web3Exception as exc:
            raise ImageNotFoundError(f"Image details query reverted or not found: {exc}") from exc

    def grant_access(
        self,
        image_id: Union[str, bytes],
        grantee_address: str,
        sender_address: Optional[str] = None,
        private_key: Optional[str] = None
    ) -> str:
        """Grants access permissions to a specified address."""
        self.check_connection()
        id_bytes32 = self._normalize_bytes32(image_id)
        sender = Web3.to_checksum_address(sender_address or os.getenv("DEPLOYER_ADDRESS") or self.w3.eth.accounts[0])
        grantee = Web3.to_checksum_address(grantee_address)

        tx_data = self.contract.functions.grantAccess(id_bytes32, grantee)
        if private_key:
            nonce = self.w3.eth.get_transaction_count(sender)
            tx_build = tx_data.build_transaction({
                "from": sender,
                "nonce": nonce,
                "gas": 150000,
                "gasPrice": self.w3.eth.gas_price
            })
            signed = self.w3.eth.account.sign_transaction(tx_build, private_key=private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
        else:
            tx_hash = tx_data.transact({"from": sender, "gas": 150000})

        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status != 1:
            raise BlockchainTransactionError("grantAccess transaction reverted on-chain.")
        return tx_hash.hex()

    def revoke_access(
        self,
        image_id: Union[str, bytes],
        revoked_address: str,
        sender_address: Optional[str] = None,
        private_key: Optional[str] = None
    ) -> str:
        """Revokes access permissions from a specified address."""
        self.check_connection()
        id_bytes32 = self._normalize_bytes32(image_id)
        sender = Web3.to_checksum_address(sender_address or os.getenv("DEPLOYER_ADDRESS") or self.w3.eth.accounts[0])
        revoked = Web3.to_checksum_address(revoked_address)

        tx_data = self.contract.functions.revokeAccess(id_bytes32, revoked)
        if private_key:
            nonce = self.w3.eth.get_transaction_count(sender)
            tx_build = tx_data.build_transaction({
                "from": sender,
                "nonce": nonce,
                "gas": 150000,
                "gasPrice": self.w3.eth.gas_price
            })
            signed = self.w3.eth.account.sign_transaction(tx_build, private_key=private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
        else:
            tx_hash = tx_data.transact({"from": sender, "gas": 150000})

        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        if receipt.status != 1:
            raise BlockchainTransactionError("revokeAccess transaction reverted on-chain.")
        return tx_hash.hex()

    def verify_ownership(self, image_id: Union[str, bytes], claimant_address: str) -> bool:
        """Checks if claimant_address is the registered owner of image_id."""
        self.check_connection()
        id_bytes32 = self._normalize_bytes32(image_id)
        claimant = Web3.to_checksum_address(claimant_address)
        return self.contract.functions.verifyOwnership(id_bytes32, claimant).call()

    def has_access(self, image_id: Union[str, bytes], user_address: str) -> bool:
        """Checks if user_address has permission to access image_id."""
        self.check_connection()
        id_bytes32 = self._normalize_bytes32(image_id)
        user = Web3.to_checksum_address(user_address)
        return self.contract.functions.hasAccess(id_bytes32, user).call()
