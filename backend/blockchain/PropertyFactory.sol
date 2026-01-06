// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title PropertyToken
 * @dev Unique ERC20 Token representing shares in a specific property.
 * Automatically deployed by the Factory.
 */
contract PropertyToken is ERC20, Ownable {
    uint256 public propertyId;
    
    constructor(
        string memory name, 
        string memory symbol, 
        uint256 _propertyId, 
        uint256 initialSupply, 
        address initialHolder
    ) ERC20(name, symbol) Ownable(msg.sender) { // Pass msg.sender (Factory) as initial owner
        propertyId = _propertyId;
        _mint(initialHolder, initialSupply);
        // Transfer ownership to the ultimate admin or keep Factory as admin? 
        // For now, keep Factory as owner or transfer to initialHolder.
        transferOwnership(initialHolder);
    }
}

/**
 * @title PropertyFactory
 * @dev Deploys fractional tokens for real estate assets and handles dividend distribution.
 */
contract PropertyFactory is Ownable, ReentrancyGuard {
    
    // Mapping from Property ID (DB/Off-chain) to Token Address
    mapping(uint256 => address) public propertyTokens;
    
    event PropertyTokenDeployed(uint256 indexed propertyId, address tokenAddress, string name, string symbol);
    event DividendsDistributed(uint256 indexed propertyId, uint256 amount);

    constructor(address initialOwner) Ownable(initialOwner) {}

    /**
     * @dev Deploys a new ERC20 token for a property.
     * @param _propertyId Database ID of the property
     * @param _name Token Name (e.g. "Osool Villa 101")
     * @param _symbol Token Symbol (e.g. "OS-101")
     * @param _initialSupply Total shares (e.g., 1,000,000 for 1M EGP valuation)
     */
    function deployPropertyToken(
        uint256 _propertyId,
        string memory _name,
        string memory _symbol,
        uint256 _initialSupply
    ) external onlyOwner returns (address) {
        require(propertyTokens[_propertyId] == address(0), "Token already exists for this property");

        PropertyToken newToken = new PropertyToken(
            _name,
            _symbol,
            _propertyId,
            _initialSupply,
            msg.sender // Admin gets the supply to distribute
        );

        propertyTokens[_propertyId] = address(newToken);

        emit PropertyTokenDeployed(_propertyId, address(newToken), _name, _symbol);
        return address(newToken);
    }

    /**
     * @dev Distribute Dividends (Rental Income) to token holders.
     * simplified: Currently just emits event for off-chain calculation 
     * or could be expanded to a full PaymentSplitter.
     * Real dividend logic is complex (snapshotting balances etc). 
     * For MVP/Production V1, we use an off-chain airdrop model based on this event trigger.
     */
    function recordDividend(uint256 _propertyId, uint256 _amountEGP) external onlyOwner {
        require(propertyTokens[_propertyId] != address(0), "Property token not found");
        emit DividendsDistributed(_propertyId, _amountEGP);
        // In full version: Transfer USDC/EURN to contract and allow claiming.
    }
    
    /**
     * @dev Helper to get token address
     */
    function getPropertyToken(uint256 _propertyId) external view returns (address) {
        return propertyTokens[_propertyId];
    }
}
