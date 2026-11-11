"""
Pydantic Request and Response Schemas for FastAPI Service Layer
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class ChallengeResponse(BaseModel):
    wallet_address: str
    challenge: str
    issued_at: int
    expires_at: int


class ImageUploadResponse(BaseModel):
    image_id: str = Field(..., description="Unique bytes32 hex identifier of the image")
    owner: str = Field(..., description="Ethereum wallet address of the owner")
    image_hash: str = Field(..., description="SHA-256 digest of the encrypted payload")
    ipfs_cid: str = Field(..., description="IPFS Content Identifier")
    transaction_hash: Optional[str] = Field(None, description="Blockchain transaction hash if registered on-chain")
    encryption_metadata: Dict[str, Any] = Field(..., description="Cryptographic parameters (algorithm, nonce, tag)")
    key_hex: str = Field(..., description="Generated 256-bit symmetric key (client must store safely)")


class ImageDetailsResponse(BaseModel):
    image_id: str
    owner: str
    image_hash: str
    ipfs_cid: str
    timestamp: int
    exists: bool


class ImageVerificationResponse(BaseModel):
    image_id: str
    is_valid: bool
    recalculated_hash: str
    ledger_hash: str
    ipfs_cid: str
    status: str
    details: Optional[str] = None


class DecryptRequest(BaseModel):
    key_hex: str = Field(..., description="256-bit symmetric key in hexadecimal")
    nonce_hex: str = Field(..., description="12-byte nonce in hexadecimal")
    tag_hex: str = Field(..., description="16-byte authentication tag in hexadecimal")
    requester_address: str = Field(..., description="Ethereum address of the requester")
    algorithm: Optional[str] = Field(
        None,
        description="Cipher algorithm ('AES-256-GCM', 'Chaotic-Tent-Map', 'Hybrid-Chaotic-AES'). Auto-resolved from metadata cache if omitted."
    )
    signature: Optional[str] = Field(None, description="EIP-191 signature proving identity")
    challenge: Optional[str] = Field(None, description="Original challenge string signed by wallet")


class AccessPermissionRequest(BaseModel):
    target_user_address: str = Field(..., description="Address to grant or revoke access for")
    owner_address: str = Field(..., description="Address of the image owner")
    signature: Optional[str] = Field(None, description="EIP-191 signature from owner")
    challenge: Optional[str] = Field(None, description="Challenge text")


class GenericActionResponse(BaseModel):
    success: bool
    message: str
    transaction_hash: Optional[str] = None
