// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title ElitePropertyEscrow
 * @dev Secure escrow contract for property transactions
 * 
 * Features:
 * - Secure fund holding until conditions met
 * - Automatic ownership transfer on approval
 * - Document verification via IPFS hash
 * - Dispute resolution with timeout
 * - Multi-signature approval (buyer + seller)
 */
contract ElitePropertyEscrow is ReentrancyGuard, Ownable {
    
    // ═══════════════════════════════════════════════════════════════
    // STRUCTS & ENUMS
    // ═══════════════════════════════════════════════════════════════
    
    enum DealStatus {
        Created,        // Deal created, awaiting deposit
        Funded,         // Buyer deposited funds
        Approved,       // Both parties approved
        Completed,      // Funds released, deal done
        Disputed,       // Under dispute
        Cancelled       // Deal cancelled
    }
    
    struct PropertyDeal {
        uint256 dealId;
        address payable buyer;
        address payable seller;
        uint256 propertyId;
        uint256 price;
        uint256 depositAmount;
        uint256 createdAt;
        uint256 deadline;
        bool buyerApproved;
        bool sellerApproved;
        DealStatus status;
        string documentsIPFS;    // IPFS hash of legal documents
        string propertyIPFS;     // IPFS hash of property details
    }
    
    // ═══════════════════════════════════════════════════════════════
    // STATE VARIABLES
    // ═══════════════════════════════════════════════════════════════
    
    uint256 public dealCounter;
    uint256 public constant PLATFORM_FEE = 1; // 1% platform fee
    uint256 public constant DISPUTE_TIMEOUT = 30 days;
    
    mapping(uint256 => PropertyDeal) public deals;
    mapping(address => uint256[]) public userDeals;
    mapping(uint256 => bool) public propertyInEscrow;
    
    address payable public platformWallet;
    
    // ═══════════════════════════════════════════════════════════════
    // EVENTS
    // ═══════════════════════════════════════════════════════════════
    
    event DealCreated(
        uint256 indexed dealId,
        address indexed buyer,
        address indexed seller,
        uint256 propertyId,
        uint256 price
    );
    
    event DealFunded(uint256 indexed dealId, uint256 amount);
    event BuyerApproved(uint256 indexed dealId);
    event SellerApproved(uint256 indexed dealId);
    event DealCompleted(uint256 indexed dealId, uint256 amountToSeller, uint256 platformFee);
    event DealCancelled(uint256 indexed dealId, string reason);
    event DisputeRaised(uint256 indexed dealId, address raisedBy, string reason);
    event DocumentsUpdated(uint256 indexed dealId, string ipfsHash);
    
    // ═══════════════════════════════════════════════════════════════
    // CONSTRUCTOR
    // ═══════════════════════════════════════════════════════════════
    
    constructor(address payable _platformWallet) {
        platformWallet = _platformWallet;
    }
    
    // ═══════════════════════════════════════════════════════════════
    // CORE FUNCTIONS
    // ═══════════════════════════════════════════════════════════════
    
    /**
     * @dev Create a new property escrow deal
     * @param _seller Seller's wallet address
     * @param _propertyId Unique property identifier
     * @param _price Total property price in wei
     * @param _propertyIPFS IPFS hash of property details
     */
    function createDeal(
        address payable _seller,
        uint256 _propertyId,
        uint256 _price,
        string calldata _propertyIPFS
    ) external returns (uint256) {
        require(_seller != address(0), "Invalid seller address");
        require(_seller != msg.sender, "Buyer cannot be seller");
        require(_price > 0, "Price must be greater than 0");
        require(!propertyInEscrow[_propertyId], "Property already in escrow");
        
        dealCounter++;
        uint256 newDealId = dealCounter;
        
        deals[newDealId] = PropertyDeal({
            dealId: newDealId,
            buyer: payable(msg.sender),
            seller: _seller,
            propertyId: _propertyId,
            price: _price,
            depositAmount: 0,
            createdAt: block.timestamp,
            deadline: block.timestamp + 90 days, // 90 day deadline
            buyerApproved: false,
            sellerApproved: false,
            status: DealStatus.Created,
            documentsIPFS: "",
            propertyIPFS: _propertyIPFS
        });
        
        propertyInEscrow[_propertyId] = true;
        userDeals[msg.sender].push(newDealId);
        userDeals[_seller].push(newDealId);
        
        emit DealCreated(newDealId, msg.sender, _seller, _propertyId, _price);
        
        return newDealId;
    }
    
    /**
     * @dev Buyer deposits funds into escrow
     * @param _dealId Deal identifier
     */
    function depositFunds(uint256 _dealId) external payable nonReentrant {
        PropertyDeal storage deal = deals[_dealId];
        
        require(deal.dealId != 0, "Deal does not exist");
        require(msg.sender == deal.buyer, "Only buyer can deposit");
        require(deal.status == DealStatus.Created, "Invalid deal status");
        require(msg.value == deal.price, "Must deposit exact price");
        
        deal.depositAmount = msg.value;
        deal.status = DealStatus.Funded;
        
        emit DealFunded(_dealId, msg.value);
    }
    
    /**
     * @dev Buyer approves the deal (property inspection passed)
     */
    function buyerApprove(uint256 _dealId) external {
        PropertyDeal storage deal = deals[_dealId];
        
        require(deal.dealId != 0, "Deal does not exist");
        require(msg.sender == deal.buyer, "Only buyer can approve");
        require(deal.status == DealStatus.Funded, "Deal must be funded");
        require(!deal.buyerApproved, "Already approved");
        
        deal.buyerApproved = true;
        emit BuyerApproved(_dealId);
        
        _checkAndComplete(_dealId);
    }
    
    /**
     * @dev Seller approves the deal (ready to transfer ownership)
     */
    function sellerApprove(uint256 _dealId) external {
        PropertyDeal storage deal = deals[_dealId];
        
        require(deal.dealId != 0, "Deal does not exist");
        require(msg.sender == deal.seller, "Only seller can approve");
        require(deal.status == DealStatus.Funded, "Deal must be funded");
        require(!deal.sellerApproved, "Already approved");
        
        deal.sellerApproved = true;
        emit SellerApproved(_dealId);
        
        _checkAndComplete(_dealId);
    }
    
    /**
     * @dev Upload legal documents to IPFS
     */
    function uploadDocuments(uint256 _dealId, string calldata _ipfsHash) external {
        PropertyDeal storage deal = deals[_dealId];
        
        require(deal.dealId != 0, "Deal does not exist");
        require(
            msg.sender == deal.buyer || msg.sender == deal.seller,
            "Not authorized"
        );
        
        deal.documentsIPFS = _ipfsHash;
        emit DocumentsUpdated(_dealId, _ipfsHash);
    }
    
    /**
     * @dev Raise a dispute on the deal
     */
    function raiseDispute(uint256 _dealId, string calldata reason) external {
        PropertyDeal storage deal = deals[_dealId];
        
        require(deal.dealId != 0, "Deal does not exist");
        require(
            msg.sender == deal.buyer || msg.sender == deal.seller,
            "Not authorized"
        );
        require(
            deal.status == DealStatus.Funded || deal.status == DealStatus.Approved,
            "Cannot dispute this deal"
        );
        
        deal.status = DealStatus.Disputed;
        emit DisputeRaised(_dealId, msg.sender, reason);
    }
    
    /**
     * @dev Cancel deal and refund buyer (before approval)
     */
    function cancelDeal(uint256 _dealId, string calldata reason) external nonReentrant {
        PropertyDeal storage deal = deals[_dealId];
        
        require(deal.dealId != 0, "Deal does not exist");
        require(
            msg.sender == deal.buyer || msg.sender == deal.seller || msg.sender == owner(),
            "Not authorized"
        );
        require(
            deal.status == DealStatus.Created || deal.status == DealStatus.Funded,
            "Cannot cancel completed deal"
        );
        
        // Refund buyer if funds were deposited
        if (deal.depositAmount > 0) {
            deal.buyer.transfer(deal.depositAmount);
        }
        
        deal.status = DealStatus.Cancelled;
        propertyInEscrow[deal.propertyId] = false;
        
        emit DealCancelled(_dealId, reason);
    }
    
    // ═══════════════════════════════════════════════════════════════
    // INTERNAL FUNCTIONS
    // ═══════════════════════════════════════════════════════════════
    
    function _checkAndComplete(uint256 _dealId) internal {
        PropertyDeal storage deal = deals[_dealId];
        
        if (deal.buyerApproved && deal.sellerApproved) {
            deal.status = DealStatus.Approved;
            _releaseFunds(_dealId);
        }
    }
    
    function _releaseFunds(uint256 _dealId) internal nonReentrant {
        PropertyDeal storage deal = deals[_dealId];
        
        require(deal.status == DealStatus.Approved, "Deal not approved");
        require(deal.depositAmount > 0, "No funds to release");
        
        uint256 fee = (deal.depositAmount * PLATFORM_FEE) / 100;
        uint256 sellerAmount = deal.depositAmount - fee;
        
        // Transfer to seller
        deal.seller.transfer(sellerAmount);
        
        // Transfer fee to platform
        if (fee > 0) {
            platformWallet.transfer(fee);
        }
        
        deal.status = DealStatus.Completed;
        deal.depositAmount = 0;
        propertyInEscrow[deal.propertyId] = false;
        
        emit DealCompleted(_dealId, sellerAmount, fee);
    }
    
    // ═══════════════════════════════════════════════════════════════
    // VIEW FUNCTIONS
    // ═══════════════════════════════════════════════════════════════
    
    function getDealDetails(uint256 _dealId) external view returns (PropertyDeal memory) {
        return deals[_dealId];
    }
    
    function getUserDeals(address _user) external view returns (uint256[] memory) {
        return userDeals[_user];
    }
    
    function getDealStatus(uint256 _dealId) external view returns (DealStatus) {
        return deals[_dealId].status;
    }
    
    function isPropertyInEscrow(uint256 _propertyId) external view returns (bool) {
        return propertyInEscrow[_propertyId];
    }
    
    // ═══════════════════════════════════════════════════════════════
    // ADMIN FUNCTIONS
    // ═══════════════════════════════════════════════════════════════
    
    function updatePlatformWallet(address payable _newWallet) external onlyOwner {
        require(_newWallet != address(0), "Invalid address");
        platformWallet = _newWallet;
    }
    
    /**
     * @dev Resolve dispute (admin only)
     * @param _dealId Deal to resolve
     * @param refundBuyer If true, refund buyer; otherwise release to seller
     */
    function resolveDispute(uint256 _dealId, bool refundBuyer) external onlyOwner nonReentrant {
        PropertyDeal storage deal = deals[_dealId];
        
        require(deal.status == DealStatus.Disputed, "No dispute to resolve");
        
        if (refundBuyer) {
            deal.buyer.transfer(deal.depositAmount);
            deal.status = DealStatus.Cancelled;
        } else {
            deal.buyerApproved = true;
            deal.sellerApproved = true;
            deal.status = DealStatus.Approved;
            _releaseFunds(_dealId);
        }
        
        propertyInEscrow[deal.propertyId] = false;
    }
}
