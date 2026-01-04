// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title Osool Property Ledger
 * @dev Stores immutable property history and verification data for the Osool Real Estate OS.
 */
contract PropertyLedger {
    
    struct Property {
        uint256 id;
        string location;
        string developer;
        uint256 price;
        address currentOwner;
        bool isVerified;
        uint256 registrationDate;
    }

    struct HistoryEvent {
        uint256 timestamp;
        string eventType; // "Created", "Transferred", "PriceUpdated"
        string details;
    }

    // Mappings
    mapping(uint256 => Property) public properties;
    mapping(uint256 => HistoryEvent[]) public propertyHistory;
    uint256 public nextPropertyId;
    address public admin;

    // Events
    event PropertyRegistered(uint256 indexed id, string location, address owner);
    event OwnershipTransferred(uint256 indexed id, address from, address to);

    constructor() {
        admin = msg.sender;
        nextPropertyId = 1;
    }

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can perform this action");
        _;
    }

    function registerProperty(string memory _location, string memory _developer, uint256 _price) public returns (uint256) {
        uint256 newId = nextPropertyId;
        
        properties[newId] = Property({
            id: newId,
            location: _location,
            developer: _developer,
            price: _price,
            currentOwner: msg.sender,
            isVerified: false, // Requires admin verification
            registrationDate: block.timestamp
        });

        _addHistory(newId, "Created", "Property registered on Osool Ledger");
        
        emit PropertyRegistered(newId, _location, msg.sender);
        nextPropertyId++;
        return newId;
    }

    function verifyProperty(uint256 _id) public onlyAdmin {
        properties[_id].isVerified = true;
        _addHistory(_id, "Verified", "Property verified by Osool Admin");
    }

    function transferOwnership(uint256 _id, address _newOwner) public {
        require(msg.sender == properties[_id].currentOwner, "Not the property owner");
        require(_newOwner != address(0), "Invalid address");

        address oldOwner = properties[_id].currentOwner;
        properties[_id].currentOwner = _newOwner;

        _addHistory(_id, "Transferred", "Ownership transferred");
        emit OwnershipTransferred(_id, oldOwner, _newOwner);
    }

    function getHistory(uint256 _id) public view returns (HistoryEvent[] memory) {
        return propertyHistory[_id];
    }

    function _addHistory(uint256 _id, string memory _type, string memory _details) internal {
        propertyHistory[_id].push(HistoryEvent({
            timestamp: block.timestamp,
            eventType: _type,
            details: _details
        }));
    }
}
