// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title OsoolRegistry
 * @dev Legal-compliant property registry for Egyptian market
 * 
 * IMPORTANT: This contract does NOT handle crypto payments.
 * All monetary transactions flow through EGP channels (InstaPay/Fawry).
 * The blockchain only stores STATUS and OWNERSHIP records.
 * 
 * Compliance: CBE Law 194 of 2020
 */
contract OsoolRegistry is Ownable {
    
    // Status: 0=Available, 1=Reserved (Deposit Paid), 2=Sold
    enum Status { AVAILABLE, RESERVED, SOLD }

    struct Property {
        uint256 id;
        string legalDocumentHash;   // Hash of the PDF contract (Proof of Truth)
        uint256 priceEGP;           // Price in EGP (informational, not crypto)
        Status status;
        address owner;
        address reservedBy;
        uint256 listedAt;
        uint256 reservedAt;
        uint256 soldAt;
    }

    mapping(uint256 => Property) public properties;
    mapping(address => uint256[]) public ownerProperties;
    mapping(address => uint256[]) public reservedProperties;
    
    uint256 public nextId = 1;
    uint256 public totalListings;

    // ═══════════════════════════════════════════════════════════════
    // EVENTS - Frontend listens to these for real-time updates
    // ═══════════════════════════════════════════════════════════════
    
    event PropertyListed(
        uint256 indexed id, 
        address indexed owner, 
        uint256 priceEGP, 
        string documentHash
    );
    
    event PropertyStatusChanged(
        uint256 indexed id, 
        Status status, 
        address indexed user
    );
    
    event PropertySold(
        uint256 indexed id, 
        address indexed previousOwner, 
        address indexed newOwner
    );

    // ═══════════════════════════════════════════════════════════════
    // PUBLIC FUNCTIONS
    // ═══════════════════════════════════════════════════════════════

    /**
     * @dev List a new property (Anyone can list)
     * @param _docHash IPFS hash or SHA256 of legal documents
     * @param _priceEGP Price in Egyptian Pounds (just metadata)
     */
    function listProperty(string memory _docHash, uint256 _priceEGP) external {
        require(bytes(_docHash).length > 0, "Document hash required");
        require(_priceEGP > 0, "Price must be positive");

        uint256 propertyId = nextId;
        
        properties[propertyId] = Property({
            id: propertyId,
            legalDocumentHash: _docHash,
            priceEGP: _priceEGP,
            status: Status.AVAILABLE,
            owner: msg.sender,
            reservedBy: address(0),
            listedAt: block.timestamp,
            reservedAt: 0,
            soldAt: 0
        });

        ownerProperties[msg.sender].push(propertyId);
        nextId++;
        totalListings++;

        emit PropertyListed(propertyId, msg.sender, _priceEGP, _docHash);
        emit PropertyStatusChanged(propertyId, Status.AVAILABLE, msg.sender);
    }

    /**
     * @dev Update document hash (Owner only)
     */
    function updateDocumentHash(uint256 _id, string memory _newHash) external {
        require(properties[_id].owner == msg.sender, "Not the owner");
        require(properties[_id].status == Status.AVAILABLE, "Cannot update reserved/sold");
        
        properties[_id].legalDocumentHash = _newHash;
    }

    /**
     * @dev Update price (Owner only)
     */
    function updatePrice(uint256 _id, uint256 _newPriceEGP) external {
        require(properties[_id].owner == msg.sender, "Not the owner");
        require(properties[_id].status == Status.AVAILABLE, "Cannot update reserved/sold");
        
        properties[_id].priceEGP = _newPriceEGP;
    }

    // ═══════════════════════════════════════════════════════════════
    // ADMIN FUNCTIONS (Called by Backend after EGP payment verified)
    // ═══════════════════════════════════════════════════════════════

    /**
     * @dev Mark property as reserved after EGP deposit received
     * @notice This is called by the backend AFTER InstaPay/Fawry payment is verified
     * @param _id Property ID
     * @param _buyer Wallet address of the buyer (for identity linking)
     */
    function markReserved(uint256 _id, address _buyer) external onlyOwner {
        require(properties[_id].id != 0, "Property does not exist");
        require(properties[_id].status == Status.AVAILABLE, "Not available");
        require(_buyer != address(0), "Invalid buyer address");
        require(_buyer != properties[_id].owner, "Owner cannot reserve own property");
        
        properties[_id].status = Status.RESERVED;
        properties[_id].reservedBy = _buyer;
        properties[_id].reservedAt = block.timestamp;

        reservedProperties[_buyer].push(_id);

        emit PropertyStatusChanged(_id, Status.RESERVED, _buyer);
    }

    /**
     * @dev Cancel reservation (Admin only - for disputes or timeout)
     */
    function cancelReservation(uint256 _id) external onlyOwner {
        require(properties[_id].status == Status.RESERVED, "Not reserved");
        
        address previousReserver = properties[_id].reservedBy;
        
        properties[_id].status = Status.AVAILABLE;
        properties[_id].reservedBy = address(0);
        properties[_id].reservedAt = 0;

        emit PropertyStatusChanged(_id, Status.AVAILABLE, previousReserver);
    }

    /**
     * @dev Finalize sale after full bank transfer received
     * @notice Transfers on-chain ownership record
     */
    function markSold(uint256 _id) external onlyOwner {
        require(properties[_id].status == Status.RESERVED, "Must be reserved first");
        
        Property storage p = properties[_id];
        address previousOwner = p.owner;
        address newOwner = p.reservedBy;
        
        p.status = Status.SOLD;
        p.owner = newOwner;
        p.soldAt = block.timestamp;

        ownerProperties[newOwner].push(_id);

        emit PropertyStatusChanged(_id, Status.SOLD, newOwner);
        emit PropertySold(_id, previousOwner, newOwner);
    }

    // ═══════════════════════════════════════════════════════════════
    // VIEW FUNCTIONS
    // ═══════════════════════════════════════════════════════════════

    function getProperty(uint256 _id) external view returns (Property memory) {
        return properties[_id];
    }

    function getPropertyStatus(uint256 _id) external view returns (Status) {
        return properties[_id].status;
    }

    function isAvailable(uint256 _id) external view returns (bool) {
        return properties[_id].status == Status.AVAILABLE;
    }

    function getOwnerListings(address _owner) external view returns (uint256[] memory) {
        return ownerProperties[_owner];
    }

    function getBuyerReservations(address _buyer) external view returns (uint256[] memory) {
        return reservedProperties[_buyer];
    }

    /**
     * @dev Verify document authenticity
     * @param _id Property ID
     * @param _hash Hash to verify against
     */
    function verifyDocument(uint256 _id, string memory _hash) external view returns (bool) {
        return keccak256(bytes(properties[_id].legalDocumentHash)) == keccak256(bytes(_hash));
    }
}
