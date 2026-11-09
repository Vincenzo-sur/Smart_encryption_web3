// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ImageRegistry
 * @dev Immutable on-chain registry for encrypted image records, SHA-256 integrity digests,
 * IPFS CIDs, and granular access control lists (ACL).
 */
contract ImageRegistry {
    
    struct ImageRecord {
        bytes32 imageId;
        address owner;
        bytes32 imageHash;
        string ipfsCid;
        uint256 timestamp;
        bool exists;
    }

    // Storage: imageId => ImageRecord
    mapping(bytes32 => ImageRecord) private images;

    // Storage: imageId => userAddress => isAuthorized
    mapping(bytes32 => mapping(address => bool)) private accessPermissions;

    // Events
    event ImageRegistered(
        bytes32 indexed imageId,
        address indexed owner,
        bytes32 imageHash,
        string ipfsCid,
        uint256 timestamp
    );

    event AccessGranted(
        bytes32 indexed imageId,
        address indexed owner,
        address indexed grantee
    );

    event AccessRevoked(
        bytes32 indexed imageId,
        address indexed owner,
        address indexed revokedUser
    );

    // Modifiers
    modifier onlyImageOwner(bytes32 _imageId) {
        require(images[_imageId].exists, "ImageRegistry: Image not registered");
        require(images[_imageId].owner == msg.sender, "ImageRegistry: Caller is not the image owner");
        _;
    }

    /**
     * @notice Registers a new encrypted image record on the blockchain.
     * @param _imageHash SHA-256 cryptographic digest of the encrypted payload (bytes32).
     * @param _ipfsCid IPFS Content Identifier string where the encrypted payload resides.
     * @return imageId Unique bytes32 identifier generated from owner, hash, CID, and timestamp.
     */
    function registerImage(
        bytes32 _imageHash,
        string calldata _ipfsCid
    ) external returns (bytes32 imageId) {
        require(_imageHash != bytes32(0), "ImageRegistry: Invalid image hash");
        require(bytes(_ipfsCid).length > 0, "ImageRegistry: IPFS CID cannot be empty");

        // Deterministic unique imageId derivation
        imageId = keccak256(
            abi.encodePacked(msg.sender, _imageHash, _ipfsCid, block.timestamp)
        );

        require(!images[imageId].exists, "ImageRegistry: Image ID collision");

        images[imageId] = ImageRecord({
            imageId: imageId,
            owner: msg.sender,
            imageHash: _imageHash,
            ipfsCid: _ipfsCid,
            timestamp: block.timestamp,
            exists: true
        });

        emit ImageRegistered(imageId, msg.sender, _imageHash, _ipfsCid, block.timestamp);
    }

    /**
     * @notice Retrieves the stored metadata of an image by its imageId.
     * @param _imageId Unique identifier of the image.
     */
    function getImageDetails(bytes32 _imageId)
        external
        view
        returns (
            address owner,
            bytes32 imageHash,
            string memory ipfsCid,
            uint256 timestamp,
            bool exists
        )
    {
        ImageRecord memory record = images[_imageId];
        require(record.exists, "ImageRegistry: Image does not exist");
        return (
            record.owner,
            record.imageHash,
            record.ipfsCid,
            record.timestamp,
            record.exists
        );
    }

    /**
     * @notice Grants decryption authorization to a specified Ethereum address.
     * @param _imageId Unique identifier of the image.
     * @param _grantee Ethereum address receiving authorization.
     */
    function grantAccess(bytes32 _imageId, address _grantee)
        external
        onlyImageOwner(_imageId)
    {
        require(_grantee != address(0), "ImageRegistry: Invalid grantee address");
        require(_grantee != msg.sender, "ImageRegistry: Owner already has access");

        accessPermissions[_imageId][_grantee] = true;
        emit AccessGranted(_imageId, msg.sender, _grantee);
    }

    /**
     * @notice Revokes decryption authorization from a specified Ethereum address.
     * @param _imageId Unique identifier of the image.
     * @param _revokedUser Ethereum address losing authorization.
     */
    function revokeAccess(bytes32 _imageId, address _revokedUser)
        external
        onlyImageOwner(_imageId)
    {
        require(accessPermissions[_imageId][_revokedUser], "ImageRegistry: Address is not authorized");

        accessPermissions[_imageId][_revokedUser] = false;
        emit AccessRevoked(_imageId, msg.sender, _revokedUser);
    }

    /**
     * @notice Verifies if a given address is the owner of an image.
     * @param _imageId Unique identifier of the image.
     * @param _claimant Address to test for ownership.
     */
    function verifyOwnership(bytes32 _imageId, address _claimant)
        external
        view
        returns (bool)
    {
        if (!images[_imageId].exists) {
            return false;
        }
        return images[_imageId].owner == _claimant;
    }

    /**
     * @notice Checks if an address has permission to access the image (owner or granted delegate).
     * @param _imageId Unique identifier of the image.
     * @param _user Address to verify.
     */
    function hasAccess(bytes32 _imageId, address _user)
        external
        view
        returns (bool)
    {
        if (!images[_imageId].exists) {
            return false;
        }
        if (images[_imageId].owner == _user) {
            return true;
        }
        return accessPermissions[_imageId][_user];
    }
}
