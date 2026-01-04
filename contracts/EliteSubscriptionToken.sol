// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title EliteSubscriptionToken
 * @dev ERC-20 token for Elite Property Advisor subscription and loyalty system
 * 
 * Features:
 * - Subscription tier management (Explorer, Premium, Platinum)
 * - Loyalty points earning (1% of property purchases)
 * - Staking rewards for premium features
 * - Referral bonus distribution
 */
contract EliteSubscriptionToken is ERC20, Ownable, ReentrancyGuard {
    
    // ═══════════════════════════════════════════════════════════════
    // SUBSCRIPTION TIERS
    // ═══════════════════════════════════════════════════════════════
    
    uint256 public constant EXPLORER_TIER = 100 * 10**18;   // 100 tokens
    uint256 public constant PREMIUM_TIER = 300 * 10**18;    // 300 tokens
    uint256 public constant PLATINUM_TIER = 1000 * 10**18;  // 1000 tokens
    
    uint256 public constant MONTH = 30 days;
    uint256 public constant TRIAL_PERIOD = 7 days;
    
    // ═══════════════════════════════════════════════════════════════
    // STATE VARIABLES
    // ═══════════════════════════════════════════════════════════════
    
    struct Subscription {
        uint256 tier;           // 1=Explorer, 2=Premium, 3=Platinum
        uint256 expiresAt;
        uint256 loyaltyPoints;
        bool hasUsedTrial;
        address referrer;
    }
    
    mapping(address => Subscription) public subscriptions;
    mapping(address => uint256) public stakedAmount;
    mapping(address => uint256) public stakingStartTime;
    
    // Staking rewards: tokens staked -> discount percentage
    uint256 public constant STAKE_1000_DISCOUNT = 5;   // 5% discount
    uint256 public constant STAKE_5000_DISCOUNT = 10;  // 10% discount
    uint256 public constant STAKE_10000_DISCOUNT = 15; // 15% discount
    
    // Referral rewards
    uint256 public constant REFERRAL_REWARD = 500 * 10**18; // 500 tokens per referral
    uint256 public constant REFEREE_BONUS = 100 * 10**18;   // 100 tokens for new user
    
    // ═══════════════════════════════════════════════════════════════
    // EVENTS
    // ═══════════════════════════════════════════════════════════════
    
    event SubscriptionCreated(address indexed user, uint256 tier, uint256 expiresAt);
    event SubscriptionRenewed(address indexed user, uint256 tier, uint256 expiresAt);
    event LoyaltyPointsEarned(address indexed user, uint256 amount, string reason);
    event TokensStaked(address indexed user, uint256 amount);
    event TokensUnstaked(address indexed user, uint256 amount, uint256 reward);
    event ReferralReward(address indexed referrer, address indexed referee, uint256 amount);
    event TrialActivated(address indexed user, uint256 expiresAt);
    
    // ═══════════════════════════════════════════════════════════════
    // CONSTRUCTOR
    // ═══════════════════════════════════════════════════════════════
    
    constructor() ERC20("Elite Advisor Token", "ELITE") {
        // Mint initial supply to contract for rewards
        _mint(address(this), 10_000_000 * 10**18); // 10 million tokens
    }
    
    // ═══════════════════════════════════════════════════════════════
    // SUBSCRIPTION FUNCTIONS
    // ═══════════════════════════════════════════════════════════════
    
    /**
     * @dev Activate free trial (7 days of Premium)
     */
    function activateTrial() external {
        require(!subscriptions[msg.sender].hasUsedTrial, "Trial already used");
        
        subscriptions[msg.sender].tier = 2; // Premium trial
        subscriptions[msg.sender].expiresAt = block.timestamp + TRIAL_PERIOD;
        subscriptions[msg.sender].hasUsedTrial = true;
        
        emit TrialActivated(msg.sender, subscriptions[msg.sender].expiresAt);
    }
    
    /**
     * @dev Subscribe using loyalty tokens
     * @param tier Subscription tier (1=Explorer, 2=Premium, 3=Platinum)
     */
    function subscribeWithTokens(uint256 tier) external nonReentrant {
        require(tier >= 1 && tier <= 3, "Invalid tier");
        
        uint256 requiredTokens;
        if (tier == 1) requiredTokens = EXPLORER_TIER;
        else if (tier == 2) requiredTokens = PREMIUM_TIER;
        else requiredTokens = PLATINUM_TIER;
        
        // Apply staking discount
        uint256 discount = getStakingDiscount(msg.sender);
        uint256 finalCost = requiredTokens - (requiredTokens * discount / 100);
        
        require(balanceOf(msg.sender) >= finalCost, "Insufficient tokens");
        
        // Burn tokens for subscription
        _burn(msg.sender, finalCost);
        
        // Extend or create subscription
        if (subscriptions[msg.sender].expiresAt > block.timestamp) {
            subscriptions[msg.sender].expiresAt += MONTH;
        } else {
            subscriptions[msg.sender].expiresAt = block.timestamp + MONTH;
        }
        subscriptions[msg.sender].tier = tier;
        
        emit SubscriptionRenewed(msg.sender, tier, subscriptions[msg.sender].expiresAt);
    }
    
    /**
     * @dev Subscribe with referral code
     */
    function subscribeWithReferral(uint256 tier, address referrer) external nonReentrant {
        require(referrer != msg.sender, "Cannot refer yourself");
        require(referrer != address(0), "Invalid referrer");
        require(subscriptions[msg.sender].referrer == address(0), "Already has referrer");
        
        // Set referrer
        subscriptions[msg.sender].referrer = referrer;
        
        // Give bonus to referee
        _transfer(address(this), msg.sender, REFEREE_BONUS);
        emit LoyaltyPointsEarned(msg.sender, REFEREE_BONUS, "Referral signup bonus");
        
        // Give reward to referrer
        _transfer(address(this), referrer, REFERRAL_REWARD);
        emit ReferralReward(referrer, msg.sender, REFERRAL_REWARD);
        
        // Now subscribe
        this.subscribeWithTokens(tier);
    }
    
    // ═══════════════════════════════════════════════════════════════
    // LOYALTY & REWARDS
    // ═══════════════════════════════════════════════════════════════
    
    /**
     * @dev Earn tokens from property purchase (1% cashback)
     * @param purchaseAmount Property price in wei
     */
    function earnFromPurchase(uint256 purchaseAmount) external {
        // Convert 1% of purchase to tokens (simplified conversion)
        uint256 reward = purchaseAmount / 100;
        
        subscriptions[msg.sender].loyaltyPoints += reward;
        _transfer(address(this), msg.sender, reward);
        
        emit LoyaltyPointsEarned(msg.sender, reward, "Property purchase cashback");
    }
    
    /**
     * @dev Stake tokens for premium benefits
     */
    function stake(uint256 amount) external nonReentrant {
        require(amount > 0, "Cannot stake 0");
        require(balanceOf(msg.sender) >= amount, "Insufficient balance");
        
        _transfer(msg.sender, address(this), amount);
        stakedAmount[msg.sender] += amount;
        stakingStartTime[msg.sender] = block.timestamp;
        
        emit TokensStaked(msg.sender, amount);
    }
    
    /**
     * @dev Unstake tokens with rewards
     */
    function unstake() external nonReentrant {
        uint256 staked = stakedAmount[msg.sender];
        require(staked > 0, "Nothing staked");
        
        // Calculate staking reward (5% APY simplified)
        uint256 stakingDuration = block.timestamp - stakingStartTime[msg.sender];
        uint256 reward = (staked * 5 * stakingDuration) / (365 days * 100);
        
        stakedAmount[msg.sender] = 0;
        stakingStartTime[msg.sender] = 0;
        
        _transfer(address(this), msg.sender, staked + reward);
        
        emit TokensUnstaked(msg.sender, staked, reward);
    }
    
    // ═══════════════════════════════════════════════════════════════
    // VIEW FUNCTIONS
    // ═══════════════════════════════════════════════════════════════
    
    function getStakingDiscount(address user) public view returns (uint256) {
        uint256 staked = stakedAmount[user];
        if (staked >= 10000 * 10**18) return STAKE_10000_DISCOUNT;
        if (staked >= 5000 * 10**18) return STAKE_5000_DISCOUNT;
        if (staked >= 1000 * 10**18) return STAKE_1000_DISCOUNT;
        return 0;
    }
    
    function isSubscriptionActive(address user) public view returns (bool) {
        return subscriptions[user].expiresAt > block.timestamp;
    }
    
    function getSubscriptionTier(address user) public view returns (uint256) {
        if (!isSubscriptionActive(user)) return 0;
        return subscriptions[user].tier;
    }
    
    function getSubscriptionDetails(address user) public view returns (
        uint256 tier,
        uint256 expiresAt,
        uint256 loyaltyPoints,
        bool hasUsedTrial,
        uint256 staked,
        uint256 stakingDiscount
    ) {
        Subscription memory sub = subscriptions[user];
        return (
            isSubscriptionActive(user) ? sub.tier : 0,
            sub.expiresAt,
            sub.loyaltyPoints,
            sub.hasUsedTrial,
            stakedAmount[user],
            getStakingDiscount(user)
        );
    }
    
    // ═══════════════════════════════════════════════════════════════
    // ADMIN FUNCTIONS
    // ═══════════════════════════════════════════════════════════════
    
    /**
     * @dev Airdrop tokens to early adopters
     */
    function airdrop(address[] calldata recipients, uint256 amount) external onlyOwner {
        for (uint256 i = 0; i < recipients.length; i++) {
            _transfer(address(this), recipients[i], amount);
        }
    }
    
    /**
     * @dev Grant subscription to user (admin only)
     */
    function grantSubscription(address user, uint256 tier, uint256 months) external onlyOwner {
        subscriptions[user].tier = tier;
        subscriptions[user].expiresAt = block.timestamp + (months * MONTH);
        
        emit SubscriptionCreated(user, tier, subscriptions[user].expiresAt);
    }
}
