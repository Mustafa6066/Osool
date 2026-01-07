// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

// Elite Fractional Token (ERC1155) - Represents shares in properties
contract EliteFractionalToken is ERC1155, Ownable {
    using SafeMath for uint256;

    string public name = "Elite Fractional Property";
    string public symbol = "EFP";

    constructor() ERC1155("https://api.osool.eg/metadata/{id}.json") {}

    function mint(address account, uint256 id, uint256 amount, bytes memory data) external onlyOwner {
        _mint(account, id, amount, data);
    }

    function setURI(string memory newuri) external onlyOwner {
        _setURI(newuri);
    }
}


// Elite Property Token (EPT) - Platform's native token
contract ElitePropertyToken is ERC20, Ownable {
    using SafeMath for uint256;
    
    uint256 public constant INITIAL_SUPPLY = 100000000 * 10**18; // 100M tokens
    
    constructor() ERC20("Elite Property Token", "EPT") {
        _mint(msg.sender, INITIAL_SUPPLY);
    }
    
    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }
}

// Membership NFT Contract
contract EliteMembershipNFT is ERC721, Ownable {
    uint256 private _tokenIdCounter;
    
    enum MembershipTier { EXPLORER, PREMIUM, PLATINUM }
    
    struct Membership {
        MembershipTier tier;
        uint256 expiryDate;
        uint256 loyaltyPoints;
        bool isActive;
    }
    
    mapping(uint256 => Membership) public memberships;
    mapping(address => uint256) public userToTokenId;
    
    string public baseURI;
    
    event MembershipMinted(address user, uint256 tokenId, MembershipTier tier);
    event MembershipUpgraded(uint256 tokenId, MembershipTier newTier);
    
    constructor() ERC721("Elite Property Membership", "EPM") {}
    
    function mintMembership(address to, MembershipTier tier) external onlyOwner returns (uint256) {
        uint256 tokenId = _tokenIdCounter++;
        _safeMint(to, tokenId);
        
        memberships[tokenId] = Membership({
            tier: tier,
            expiryDate: block.timestamp + 30 days,
            loyaltyPoints: 1000, // Welcome bonus
            isActive: true
        });
        
        userToTokenId[to] = tokenId;
        emit MembershipMinted(to, tokenId, tier);
        
        return tokenId;
    }
    
    function upgradeMembership(uint256 tokenId, MembershipTier newTier) external {
        require(ownerOf(tokenId) == msg.sender, "Not the owner");
        require(memberships[tokenId].tier < newTier, "Can only upgrade");
        
        memberships[tokenId].tier = newTier;
        emit MembershipUpgraded(tokenId, newTier);
    }
    
    function _baseURI() internal view override returns (string memory) {
        return baseURI;
    }
    
    function setBaseURI(string memory _newBaseURI) external onlyOwner {
        baseURI = _newBaseURI;
    }
}

// Main Platform Contract
contract ElitePropertyPlatform is Ownable, ReentrancyGuard {
    using SafeMath for uint256;
    
    ElitePropertyToken public eptToken;
    EliteMembershipNFT public membershipNFT;
    EliteFractionalToken public fractionalToken;
    
    // Property Escrow Structure
    struct PropertyEscrow {
        uint256 propertyId;
        address payable seller;
        address payable buyer;
        uint256 price;
        uint256 depositAmount;
        uint256 deadline;
        string propertyDetailsIPFS;
        EscrowStatus status;
        bool buyerSigned;
        bool sellerSigned;
    }
    
    enum EscrowStatus { CREATED, FUNDED, COMPLETED, CANCELLED }
    
    // Subscription Structure
    struct Subscription {
        uint256 tier; // 0: Explorer, 1: Premium, 2: Platinum
        uint256 expiryDate;
        uint256 tokensStaked;
        uint256 referralCount;
        bool autoRenew;
    }
    
    // State Variables
    mapping(uint256 => PropertyEscrow) public escrows;
    mapping(address => Subscription) public subscriptions;
    mapping(address => uint256) public referralRewards;
    mapping(address => address) public referredBy;
    mapping(address => uint256[]) public userPropertyHistory;
    
    uint256 public escrowCounter;
    uint256 public totalValueLocked;
    uint256 public platformFeePercentage = 100; // 1%
    
    // Subscription Pricing (in EPT tokens)
    uint256[3] public subscriptionPrices = [100 * 10**18, 300 * 10**18, 1000 * 10**18];
    
    // Events
    // Events
    event EscrowCreated(uint256 escrowId, address seller, address buyer, uint256 price);
    event EscrowFunded(uint256 escrowId, uint256 amount);
    event EscrowCompleted(uint256 escrowId);
    event SubscriptionPurchased(address user, uint256 tier, uint256 duration);
    event ReferralRewarded(address referrer, address referee, uint256 reward);
    event PropertyTokenized(uint256 propertyId, string metadataURI);
    event FractionalShareMinted(uint256 propertyId, address investor, uint256 amount);
    
    constructor(address _eptToken, address _membershipNFT, address _fractionalToken) {
        eptToken = ElitePropertyToken(_eptToken);
        membershipNFT = EliteMembershipNFT(_membershipNFT);
        fractionalToken = EliteFractionalToken(_fractionalToken);
    }
    
    // ==================== PAUSABLE ====================

    bool public paused = false;

    modifier whenNotPaused() {
        require(!paused, "Contract is paused");
        _;
    }

    function emergencyPause() external onlyOwner {
        paused = !paused;
    }
    
    // ==================== FRACTIONAL INVESTING ====================

    function mintFractionalShares(address to, uint256 amount, uint256 propertyId) external onlyOwner whenNotPaused {
        fractionalToken.mint(to, propertyId, amount, "");
        emit FractionalShareMinted(propertyId, to, amount);
    }

    // ==================== ESCROW FUNCTIONS ====================
    
    function createEscrow(
        uint256 _propertyId,
        address payable _buyer,
        uint256 _price,
        string memory _propertyDetailsIPFS
    ) external whenNotPaused returns (uint256) {
        uint256 escrowId = escrowCounter++;
        
        escrows[escrowId] = PropertyEscrow({
            propertyId: _propertyId,
            seller: payable(msg.sender),
            buyer: _buyer,
            price: _price,
            depositAmount: _price.mul(10).div(100), // 10% deposit
            deadline: block.timestamp + 30 days,
            propertyDetailsIPFS: _propertyDetailsIPFS,
            status: EscrowStatus.CREATED,
            buyerSigned: false,
            sellerSigned: false
        });
        
        emit EscrowCreated(escrowId, msg.sender, _buyer, _price);
        return escrowId;
    }
    
    function fundEscrow(uint256 _escrowId) external payable nonReentrant whenNotPaused {
        PropertyEscrow storage escrow = escrows[_escrowId];
        require(msg.sender == escrow.buyer, "Only buyer can fund");
        require(escrow.status == EscrowStatus.CREATED, "Invalid status");
        require(msg.value >= escrow.depositAmount, "Insufficient deposit");
        
        escrow.status = EscrowStatus.FUNDED;
        totalValueLocked = totalValueLocked.add(msg.value);
        
        emit EscrowFunded(_escrowId, msg.value);
    }
    
    function completeEscrow(uint256 _escrowId) external payable nonReentrant whenNotPaused {
        PropertyEscrow storage escrow = escrows[_escrowId];
        require(escrow.status == EscrowStatus.FUNDED, "Not funded");
        require(block.timestamp <= escrow.deadline, "Deadline passed");
        
        if (msg.sender == escrow.buyer) {
            require(msg.value >= escrow.price.sub(escrow.depositAmount), "Insufficient payment");
            escrow.buyerSigned = true;
        } else if (msg.sender == escrow.seller) {
            escrow.sellerSigned = true;
        } else {
            revert("Unauthorized");
        }
        
        if (escrow.buyerSigned && escrow.sellerSigned) {
            // Calculate platform fee
            uint256 platformFee = escrow.price.mul(platformFeePercentage).div(10000);
            uint256 sellerAmount = escrow.price.sub(platformFee);
            
            // Transfer funds
            escrow.seller.transfer(sellerAmount);
            
            // Update state
            escrow.status = EscrowStatus.COMPLETED;
            totalValueLocked = totalValueLocked.sub(escrow.price);
            userPropertyHistory[escrow.buyer].push(escrow.propertyId);
            
            // Reward buyer with loyalty tokens (1% of purchase price)
            uint256 loyaltyReward = escrow.price.mul(100).div(10000);
            eptToken.mint(escrow.buyer, loyaltyReward);
            
            emit EscrowCompleted(_escrowId);
        }
    }
    
    // ==================== SUBSCRIPTION FUNCTIONS ====================
    
    function purchaseSubscription(uint256 _tier, address _referrer) external whenNotPaused {
        require(_tier < 3, "Invalid tier");
        require(eptToken.balanceOf(msg.sender) >= subscriptionPrices[_tier], "Insufficient EPT");
        
        // Transfer tokens from user
        eptToken.transferFrom(msg.sender, address(this), subscriptionPrices[_tier]);
        
        // Update subscription
        subscriptions[msg.sender] = Subscription({
            tier: _tier,
            expiryDate: block.timestamp + 30 days,
            tokensStaked: subscriptionPrices[_tier],
            referralCount: subscriptions[msg.sender].referralCount,
            autoRenew: true
        });
        
        // Mint membership NFT if first time
        if (membershipNFT.balanceOf(msg.sender) == 0) {
            EliteMembershipNFT.MembershipTier nftTier = EliteMembershipNFT.MembershipTier(_tier);
            membershipNFT.mintMembership(msg.sender, nftTier);
        }
        
        // Handle referral
        if (_referrer != address(0) && _referrer != msg.sender) {
            referredBy[msg.sender] = _referrer;
            uint256 referralReward = subscriptionPrices[_tier].mul(20).div(100); // 20% referral bonus
            eptToken.mint(_referrer, referralReward);
            referralRewards[_referrer] = referralRewards[_referrer].add(referralReward);
            subscriptions[_referrer].referralCount++;
            
            emit ReferralRewarded(_referrer, msg.sender, referralReward);
        }
        
        emit SubscriptionPurchased(msg.sender, _tier, 30 days);
    }
    
    function stakeTokensForBenefits(uint256 _amount) external whenNotPaused {
        require(eptToken.balanceOf(msg.sender) >= _amount, "Insufficient balance");
        eptToken.transferFrom(msg.sender, address(this), _amount);
        
        subscriptions[msg.sender].tokensStaked = subscriptions[msg.sender].tokensStaked.add(_amount);
        
        // Auto-upgrade tier based on staked amount
        if (subscriptions[msg.sender].tokensStaked >= 5000 * 10**18 && subscriptions[msg.sender].tier < 2) {
            subscriptions[msg.sender].tier = 2; // Platinum
        } else if (subscriptions[msg.sender].tokensStaked >= 1000 * 10**18 && subscriptions[msg.sender].tier < 1) {
            subscriptions[msg.sender].tier = 1; // Premium
        }
    }
    
    // ==================== VIEW FUNCTIONS ====================
    
    function isSubscriptionActive(address _user) external view returns (bool) {
        return subscriptions[_user].expiryDate > block.timestamp;
    }
    
    function getUserTier(address _user) external view returns (uint256) {
        if (subscriptions[_user].expiryDate > block.timestamp) {
            return subscriptions[_user].tier;
        }
        return 0; // Default to Explorer
    }
    
    function getStakingBenefits(address _user) external view returns (string memory) {
        uint256 staked = subscriptions[_user].tokensStaked;
        
        if (staked >= 50000 * 10**18) return "Platinum Elite: Personal AI Agent + 0% Platform Fees";
        if (staked >= 10000 * 10**18) return "Gold: Priority Support + Early Access";
        if (staked >= 5000 * 10**18) return "Silver: 50% Fee Discount";
        if (staked >= 1000 * 10**18) return "Bronze: 25% Fee Discount";
        return "No staking benefits";
    }
    
    // ==================== ADMIN FUNCTIONS ====================
    
    function setPlatformFee(uint256 _feePercentage) external onlyOwner {
        require(_feePercentage <= 300, "Max 3%");
        platformFeePercentage = _feePercentage;
    }
    
    function withdrawPlatformFees() external onlyOwner {
        uint256 balance = address(this).balance;
        require(balance > 0, "No fees to withdraw");
        payable(owner()).transfer(balance);
    }
    
    function emergencyPause() external onlyOwner {
        paused = !paused;
    }
}
