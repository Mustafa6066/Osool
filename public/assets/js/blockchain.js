/**
 * Elite Property Advisor - Blockchain Integration Layer
 * Web3 service for wallet connection, subscription management, and escrow
 * 
 * Supported Networks:
 * - Polygon (Primary) - Low fees
 * - Ethereum Mainnet - High-value transactions
 * - Local Hardhat - Development
 */

// Contract ABIs (simplified for demo)
const SUBSCRIPTION_ABI = [
    "function activateTrial() external",
    "function subscribeWithTokens(uint256 tier) external",
    "function subscribeWithReferral(uint256 tier, address referrer) external",
    "function earnFromPurchase(uint256 purchaseAmount) external",
    "function stake(uint256 amount) external",
    "function unstake() external",
    "function balanceOf(address owner) view returns (uint256)",
    "function isSubscriptionActive(address user) view returns (bool)",
    "function getSubscriptionTier(address user) view returns (uint256)",
    "function getSubscriptionDetails(address user) view returns (uint256, uint256, uint256, bool, uint256, uint256)",
    "function getStakingDiscount(address user) view returns (uint256)",
    "event SubscriptionCreated(address indexed user, uint256 tier, uint256 expiresAt)",
    "event LoyaltyPointsEarned(address indexed user, uint256 amount, string reason)"
];

const ESCROW_ABI = [
    "function createDeal(address seller, uint256 propertyId, uint256 price, string propertyIPFS) returns (uint256)",
    "function depositFunds(uint256 dealId) external payable",
    "function buyerApprove(uint256 dealId) external",
    "function sellerApprove(uint256 dealId) external",
    "function uploadDocuments(uint256 dealId, string ipfsHash) external",
    "function raiseDispute(uint256 dealId, string reason) external",
    "function cancelDeal(uint256 dealId, string reason) external",
    "function getDealDetails(uint256 dealId) view returns (tuple(uint256, address, address, uint256, uint256, uint256, uint256, uint256, bool, bool, uint8, string, string))",
    "function getUserDeals(address user) view returns (uint256[])",
    "function isPropertyInEscrow(uint256 propertyId) view returns (bool)",
    "event DealCreated(uint256 indexed dealId, address indexed buyer, address indexed seller, uint256 propertyId, uint256 price)",
    "event DealCompleted(uint256 indexed dealId, uint256 amountToSeller, uint256 platformFee)"
];

// Elite Property Platform ABI (Unified Platform Contract)
const PLATFORM_ABI = [
    // Escrow functions
    "function createEscrow(uint256 propertyId, address buyer, uint256 price, string propertyDetailsIPFS) returns (uint256)",
    "function fundEscrow(uint256 escrowId) external payable",
    "function completeEscrow(uint256 escrowId) external payable",
    // Subscription functions
    "function purchaseSubscription(uint256 tier, address referrer) external",
    "function stakeTokensForBenefits(uint256 amount) external",
    // View functions
    "function isSubscriptionActive(address user) view returns (bool)",
    "function getUserTier(address user) view returns (uint256)",
    "function getStakingBenefits(address user) view returns (string)",
    "function subscriptionPrices(uint256 tier) view returns (uint256)",
    "function subscriptions(address user) view returns (uint256, uint256, uint256, uint256, bool)",
    "function escrows(uint256 id) view returns (uint256, address, address, uint256, uint256, uint256, string, uint8, bool, bool)",
    "function totalValueLocked() view returns (uint256)",
    // Events
    "event EscrowCreated(uint256 escrowId, address seller, address buyer, uint256 price)",
    "event EscrowFunded(uint256 escrowId, uint256 amount)",
    "event EscrowCompleted(uint256 escrowId)",
    "event SubscriptionPurchased(address user, uint256 tier, uint256 duration)",
    "event ReferralRewarded(address referrer, address referee, uint256 reward)"
];

// EPT Token ABI
const EPT_TOKEN_ABI = [
    "function balanceOf(address owner) view returns (uint256)",
    "function approve(address spender, uint256 amount) returns (bool)",
    "function allowance(address owner, address spender) view returns (uint256)",
    "function transfer(address to, uint256 amount) returns (bool)",
    "function totalSupply() view returns (uint256)"
];

// NFT Membership ABI
const NFT_ABI = [
    "function balanceOf(address owner) view returns (uint256)",
    "function userToTokenId(address user) view returns (uint256)",
    "function memberships(uint256 tokenId) view returns (uint8, uint256, uint256, bool)",
    "function upgradeMembership(uint256 tokenId, uint8 newTier) external"
];

// Network configurations
const NETWORKS = {
    polygon: {
        chainId: '0x89',
        chainName: 'Polygon Mainnet',
        rpcUrls: ['https://polygon-rpc.com'],
        nativeCurrency: { name: 'MATIC', symbol: 'MATIC', decimals: 18 },
        blockExplorerUrls: ['https://polygonscan.com']
    },
    mumbai: {
        chainId: '0x13881',
        chainName: 'Polygon Mumbai Testnet',
        rpcUrls: ['https://rpc-mumbai.maticvigil.com'],
        nativeCurrency: { name: 'MATIC', symbol: 'MATIC', decimals: 18 },
        blockExplorerUrls: ['https://mumbai.polygonscan.com']
    },
    localhost: {
        chainId: '0x7A69',
        chainName: 'Hardhat Local',
        rpcUrls: ['http://127.0.0.1:8545']
    }
};

// Contract addresses (update after deployment)
const CONTRACT_ADDRESSES = {
    polygon: {
        subscription: '0x0000000000000000000000000000000000000000',
        escrow: '0x0000000000000000000000000000000000000000',
        // New unified platform contracts
        platform: '0x0000000000000000000000000000000000000000',
        eptToken: '0x0000000000000000000000000000000000000000',
        nft: '0x0000000000000000000000000000000000000000'
    },
    mumbai: {
        subscription: '0x0000000000000000000000000000000000000000',
        escrow: '0x0000000000000000000000000000000000000000',
        platform: '0x0000000000000000000000000000000000000000',
        eptToken: '0x0000000000000000000000000000000000000000',
        nft: '0x0000000000000000000000000000000000000000'
    },
    localhost: {
        subscription: '0x5FbDB2315678afecb367f032d93F642f64180aa3',
        escrow: '0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512',
        platform: '0xDc64a140Aa3E981100a9becA4E685f962f0cF6C9',
        eptToken: '0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0',
        nft: '0xCf7Ed3AccA5a467e9e704C703E8D87F634fB0Fc9'
    }
};

/**
 * BlockchainService - Main Web3 integration class
 */
class BlockchainService {
    constructor() {
        this.provider = null;
        this.signer = null;
        this.address = null;
        this.network = null;
        this.subscriptionContract = null;
        this.escrowContract = null;
        // New platform contracts
        this.platformContract = null;
        this.eptTokenContract = null;
        this.nftContract = null;
        this.isConnected = false;
    }

    // ═══════════════════════════════════════════════════════════════
    // WALLET CONNECTION
    // ═══════════════════════════════════════════════════════════════

    /**
     * Check if MetaMask is available
     */
    isMetaMaskAvailable() {
        return typeof window.ethereum !== 'undefined';
    }

    /**
     * Connect to MetaMask wallet
     */
    async connectWallet() {
        if (!this.isMetaMaskAvailable()) {
            throw new Error('الرجاء تثبيت MetaMask للمتابعة');
        }

        try {
            // Request account access
            const accounts = await window.ethereum.request({
                method: 'eth_requestAccounts'
            });

            if (accounts.length === 0) {
                throw new Error('لم يتم اختيار أي حساب');
            }

            this.address = accounts[0];

            // Create ethers provider (using ethers v5 CDN-compatible method)
            if (typeof ethers !== 'undefined') {
                this.provider = new ethers.providers.Web3Provider(window.ethereum);
                this.signer = this.provider.getSigner();
            }

            // Get network
            const chainId = await window.ethereum.request({ method: 'eth_chainId' });
            this.network = this._getNetworkName(chainId);

            // Initialize contracts
            this._initContracts();

            this.isConnected = true;

            // Listen for account changes
            window.ethereum.on('accountsChanged', (accounts) => {
                if (accounts.length === 0) {
                    this.disconnect();
                } else {
                    this.address = accounts[0];
                    this._updateUI();
                }
            });

            // Listen for network changes
            window.ethereum.on('chainChanged', () => {
                window.location.reload();
            });

            this._updateUI();
            return { address: this.address, network: this.network };

        } catch (error) {
            console.error('Wallet connection failed:', error);
            throw error;
        }
    }

    /**
     * Disconnect wallet
     */
    disconnect() {
        this.provider = null;
        this.signer = null;
        this.address = null;
        this.isConnected = false;
        this._updateUI();
    }

    /**
     * Switch to Polygon network
     */
    async switchToPolygon() {
        try {
            await window.ethereum.request({
                method: 'wallet_switchEthereumChain',
                params: [{ chainId: NETWORKS.polygon.chainId }]
            });
        } catch (switchError) {
            // Network not added, try to add it
            if (switchError.code === 4902) {
                await window.ethereum.request({
                    method: 'wallet_addEthereumChain',
                    params: [NETWORKS.polygon]
                });
            } else {
                throw switchError;
            }
        }
    }

    // ═══════════════════════════════════════════════════════════════
    // SUBSCRIPTION FUNCTIONS
    // ═══════════════════════════════════════════════════════════════

    /**
     * Get token balance
     */
    async getTokenBalance() {
        if (!this.subscriptionContract) return 0;

        try {
            const balance = await this.subscriptionContract.balanceOf(this.address);
            return ethers.utils.formatEther(balance);
        } catch (error) {
            console.error('Failed to get balance:', error);
            return 0;
        }
    }

    /**
     * Check if subscription is active
     */
    async isSubscriptionActive() {
        if (!this.subscriptionContract) return false;

        try {
            return await this.subscriptionContract.isSubscriptionActive(this.address);
        } catch (error) {
            console.error('Failed to check subscription:', error);
            return false;
        }
    }

    /**
     * Get subscription details
     */
    async getSubscriptionDetails() {
        if (!this.subscriptionContract) {
            return { tier: 0, expiresAt: 0, loyaltyPoints: 0, hasUsedTrial: false, staked: 0, discount: 0 };
        }

        try {
            const [tier, expiresAt, loyaltyPoints, hasUsedTrial, staked, discount] =
                await this.subscriptionContract.getSubscriptionDetails(this.address);

            return {
                tier: tier.toNumber(),
                tierName: this._getTierName(tier.toNumber()),
                expiresAt: new Date(expiresAt.toNumber() * 1000),
                loyaltyPoints: ethers.utils.formatEther(loyaltyPoints),
                hasUsedTrial,
                staked: ethers.utils.formatEther(staked),
                discount: discount.toNumber()
            };
        } catch (error) {
            console.error('Failed to get subscription details:', error);
            return { tier: 0, expiresAt: 0, loyaltyPoints: 0, hasUsedTrial: false, staked: 0, discount: 0 };
        }
    }

    /**
     * Activate free trial
     */
    async activateTrial() {
        if (!this.subscriptionContract) throw new Error('Contracts not initialized');

        const tx = await this.subscriptionContract.activateTrial();
        await tx.wait();

        return tx.hash;
    }

    /**
     * Subscribe with tokens
     */
    async subscribe(tier) {
        if (!this.subscriptionContract) throw new Error('Contracts not initialized');

        const tx = await this.subscriptionContract.subscribeWithTokens(tier);
        await tx.wait();

        return tx.hash;
    }

    /**
     * Stake tokens
     */
    async stakeTokens(amount) {
        if (!this.subscriptionContract) throw new Error('Contracts not initialized');

        const amountWei = ethers.utils.parseEther(amount.toString());
        const tx = await this.subscriptionContract.stake(amountWei);
        await tx.wait();

        return tx.hash;
    }

    /**
     * Unstake tokens
     */
    async unstakeTokens() {
        if (!this.subscriptionContract) throw new Error('Contracts not initialized');

        const tx = await this.subscriptionContract.unstake();
        await tx.wait();

        return tx.hash;
    }

    // ═══════════════════════════════════════════════════════════════
    // ESCROW FUNCTIONS
    // ═══════════════════════════════════════════════════════════════

    /**
     * Create property escrow deal
     */
    async createEscrow(sellerAddress, propertyId, priceInMatic, propertyIPFS = '') {
        if (!this.escrowContract) throw new Error('Contracts not initialized');

        const priceWei = ethers.utils.parseEther(priceInMatic.toString());
        const tx = await this.escrowContract.createDeal(
            sellerAddress,
            propertyId,
            priceWei,
            propertyIPFS
        );

        const receipt = await tx.wait();

        // Get deal ID from event
        const event = receipt.events?.find(e => e.event === 'DealCreated');
        const dealId = event?.args?.dealId?.toNumber();

        return { txHash: tx.hash, dealId };
    }

    /**
     * Deposit funds to escrow
     */
    async depositToEscrow(dealId, amountInMatic) {
        if (!this.escrowContract) throw new Error('Contracts not initialized');

        const amountWei = ethers.utils.parseEther(amountInMatic.toString());
        const tx = await this.escrowContract.depositFunds(dealId, { value: amountWei });
        await tx.wait();

        return tx.hash;
    }

    /**
     * Approve deal as buyer
     */
    async approveAsBuyer(dealId) {
        if (!this.escrowContract) throw new Error('Contracts not initialized');

        const tx = await this.escrowContract.buyerApprove(dealId);
        await tx.wait();

        return tx.hash;
    }

    /**
     * Approve deal as seller
     */
    async approveAsSeller(dealId) {
        if (!this.escrowContract) throw new Error('Contracts not initialized');

        const tx = await this.escrowContract.sellerApprove(dealId);
        await tx.wait();

        return tx.hash;
    }

    /**
     * Get user's deals
     */
    async getUserDeals() {
        if (!this.escrowContract) return [];

        try {
            const dealIds = await this.escrowContract.getUserDeals(this.address);
            const deals = [];

            for (const dealId of dealIds) {
                const deal = await this.escrowContract.getDealDetails(dealId);
                deals.push(this._formatDeal(deal, dealId.toNumber()));
            }

            return deals;
        } catch (error) {
            console.error('Failed to get user deals:', error);
            return [];
        }
    }

    // ═══════════════════════════════════════════════════════════════
    // INTERNAL HELPERS
    // ═══════════════════════════════════════════════════════════════

    _initContracts() {
        if (!this.signer || !this.network) return;

        const addresses = CONTRACT_ADDRESSES[this.network] || CONTRACT_ADDRESSES.localhost;

        if (typeof ethers !== 'undefined') {
            this.subscriptionContract = new ethers.Contract(
                addresses.subscription,
                SUBSCRIPTION_ABI,
                this.signer
            );

            this.escrowContract = new ethers.Contract(
                addresses.escrow,
                ESCROW_ABI,
                this.signer
            );

            // Initialize new platform contracts
            if (addresses.platform && addresses.platform !== '0x0000000000000000000000000000000000000000') {
                this.platformContract = new ethers.Contract(
                    addresses.platform,
                    PLATFORM_ABI,
                    this.signer
                );
            }

            if (addresses.eptToken && addresses.eptToken !== '0x0000000000000000000000000000000000000000') {
                this.eptTokenContract = new ethers.Contract(
                    addresses.eptToken,
                    EPT_TOKEN_ABI,
                    this.signer
                );
            }

            if (addresses.nft && addresses.nft !== '0x0000000000000000000000000000000000000000') {
                this.nftContract = new ethers.Contract(
                    addresses.nft,
                    NFT_ABI,
                    this.signer
                );
            }
        }
    }

    _getNetworkName(chainId) {
        switch (chainId) {
            case '0x89': return 'polygon';
            case '0x13881': return 'mumbai';
            case '0x7A69': return 'localhost';
            case '0x1': return 'ethereum';
            default: return 'unknown';
        }
    }

    _getTierName(tier) {
        switch (tier) {
            case 1: return 'Explorer';
            case 2: return 'Premium';
            case 3: return 'Platinum';
            default: return 'Free';
        }
    }

    _formatDeal(deal, dealId) {
        const statusNames = ['Created', 'Funded', 'Approved', 'Completed', 'Disputed', 'Cancelled'];
        return {
            dealId,
            buyer: deal[1],
            seller: deal[2],
            propertyId: deal[3]?.toNumber(),
            price: ethers.utils.formatEther(deal[4] || 0),
            depositAmount: ethers.utils.formatEther(deal[5] || 0),
            createdAt: new Date((deal[6]?.toNumber() || 0) * 1000),
            deadline: new Date((deal[7]?.toNumber() || 0) * 1000),
            buyerApproved: deal[8],
            sellerApproved: deal[9],
            status: statusNames[deal[10]] || 'Unknown',
            documentsIPFS: deal[11],
            propertyIPFS: deal[12]
        };
    }

    _updateUI() {
        // Dispatch custom event for UI updates
        window.dispatchEvent(new CustomEvent('walletStateChanged', {
            detail: {
                isConnected: this.isConnected,
                address: this.address,
                network: this.network
            }
        }));
    }
}

// ═══════════════════════════════════════════════════════════════
// SIMULATED MODE (for demo without real blockchain)
// ═══════════════════════════════════════════════════════════════

class SimulatedBlockchainService {
    constructor() {
        this.address = null;
        this.isConnected = false;
        this.tokenBalance = 5000; // Start with 5000 demo tokens
        this.subscription = {
            tier: 0,
            expiresAt: 0,
            loyaltyPoints: 0,
            hasUsedTrial: false,
            staked: 0
        };
        this.deals = [];
    }

    async connectWallet() {
        // Simulate wallet connection
        this.address = '0x' + Array(40).fill(0).map(() =>
            Math.floor(Math.random() * 16).toString(16)
        ).join('');
        this.isConnected = true;

        this._updateUI();
        return { address: this.address, network: 'demo' };
    }

    disconnect() {
        this.address = null;
        this.isConnected = false;
        this._updateUI();
    }

    async getTokenBalance() {
        return this.tokenBalance;
    }

    async isSubscriptionActive() {
        return this.subscription.expiresAt > Date.now();
    }

    async getSubscriptionDetails() {
        const tierNames = ['Free', 'Explorer', 'Premium', 'Platinum'];
        return {
            tier: this.subscription.tier,
            tierName: tierNames[this.subscription.tier],
            expiresAt: new Date(this.subscription.expiresAt),
            loyaltyPoints: this.subscription.loyaltyPoints,
            hasUsedTrial: this.subscription.hasUsedTrial,
            staked: this.subscription.staked,
            discount: this.subscription.staked >= 10000 ? 15 :
                this.subscription.staked >= 5000 ? 10 :
                    this.subscription.staked >= 1000 ? 5 : 0
        };
    }

    async activateTrial() {
        if (this.subscription.hasUsedTrial) {
            throw new Error('Trial already used');
        }
        this.subscription.tier = 2;
        this.subscription.expiresAt = Date.now() + 7 * 24 * 60 * 60 * 1000; // 7 days
        this.subscription.hasUsedTrial = true;
        return 'demo_tx_' + Date.now();
    }

    async subscribe(tier) {
        const costs = { 1: 100, 2: 300, 3: 1000 };
        const cost = costs[tier] || 0;

        if (this.tokenBalance < cost) {
            throw new Error('Insufficient tokens');
        }

        this.tokenBalance -= cost;
        this.subscription.tier = tier;
        this.subscription.expiresAt = Date.now() + 30 * 24 * 60 * 60 * 1000; // 30 days

        return 'demo_tx_' + Date.now();
    }

    async stakeTokens(amount) {
        if (this.tokenBalance < amount) {
            throw new Error('Insufficient tokens');
        }
        this.tokenBalance -= amount;
        this.subscription.staked += amount;
        return 'demo_tx_' + Date.now();
    }

    async createEscrow(sellerAddress, propertyId, price) {
        const dealId = this.deals.length + 1;
        this.deals.push({
            dealId,
            buyer: this.address,
            seller: sellerAddress,
            propertyId,
            price,
            status: 'Created',
            createdAt: new Date()
        });
        return { txHash: 'demo_tx_' + Date.now(), dealId };
    }

    async getUserDeals() {
        return this.deals;
    }

    _updateUI() {
        window.dispatchEvent(new CustomEvent('walletStateChanged', {
            detail: {
                isConnected: this.isConnected,
                address: this.address,
                network: 'demo'
            }
        }));
    }
}

// ═══════════════════════════════════════════════════════════════
// GLOBAL INSTANCE
// ═══════════════════════════════════════════════════════════════

// Use simulated mode if ethers.js not available
const blockchainService = typeof ethers !== 'undefined'
    ? new BlockchainService()
    : new SimulatedBlockchainService();

// Make available globally
window.blockchainService = blockchainService;
window.BlockchainService = BlockchainService;
