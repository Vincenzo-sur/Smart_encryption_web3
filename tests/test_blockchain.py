"""
Unit Tests for Blockchain Data Structures, Service Initialization, and Smart Contract Specifications
"""

import os
from pathlib import Path
import pytest
from blockchain.blockchain_service import BlockchainService, BlockchainImageRecord, IMAGE_REGISTRY_ABI


class TestBlockchainService:
    def test_solidity_file_exists(self):
        sol_file = Path("blockchain/contracts/ImageRegistry.sol")
        assert sol_file.exists()
        content = sol_file.read_text(encoding="utf-8")
        assert "contract ImageRegistry" in content
        assert "registerImage" in content
        assert "getImageDetails" in content
        assert "grantAccess" in content
        assert "revokeAccess" in content
        assert "hasAccess" in content

    def test_abi_structure(self):
        function_names = [item["name"] for item in IMAGE_REGISTRY_ABI if item.get("type") == "function"]
        assert "registerImage" in function_names
        assert "getImageDetails" in function_names
        assert "grantAccess" in function_names
        assert "revokeAccess" in function_names
        assert "hasAccess" in function_names

    def test_image_record_dataclass(self):
        record = BlockchainImageRecord(
            image_id="0x" + "a" * 64,
            owner="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            image_hash="0x" + "b" * 64,
            ipfs_cid="QmTest1234567890",
            timestamp=1700000000,
            exists=True
        )
        assert record.exists is True
        d = record.to_dict()
        assert d["ipfs_cid"] == "QmTest1234567890"

    def test_service_initialization_defaults(self):
        svc = BlockchainService(rpc_url="http://127.0.0.1:8545")
        assert svc.rpc_url == "http://127.0.0.1:8545"
        # Since Ganache may or may not be running right now, is_connected returns bool safely
        assert isinstance(svc.is_connected(), bool)
