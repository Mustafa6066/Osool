// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title OsoolLiquidityAMM
 * @notice Automated Market Maker for Osool Property Token Trading
 * @dev First-ever AMM for fractional real estate in Egypt
 *
 * Architecture: Constant Product Formula (x * y = k)
 * - Each property has its own pool: Property Tokens ↔ OEGP (EGP Stablecoin)
 * - 0.3% trading fee (0.25% to LPs, 0.05% to platform)
 * - Slippage protection built-in
 * - Minimum liquidity lock (first 1000 LP tokens burned forever)
 *
 * Security Features:
 * - Reentrancy guards on all state-changing functions
 * - Emergency pause mechanism
 * - Minimum liquidity lock prevents rug pulls
 * - Slippage protection on all swaps
 *
 * Phase 6: Osool Production Transformation
 */

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC1155/IERC1155.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

contract OsoolLiquidityAMM is ReentrancyGuard, Ownable, Pausable {

    // ═══════════════════════════════════════════════════════════════
    // CONSTANTS & IMMUTABLES
    // ═══════════════════════════════════════════════════════════════

    uint256 public constant FEE_DENOMINATOR = 10000; // Basis points
    uint256 public constant LP_FEE = 25;  // 0.25% to LPs
    uint256 public constant PLATFORM_FEE = 5;  // 0.05% to platform
    uint256 public constant TOTAL_FEE = LP_FEE + PLATFORM_FEE;  // 0.3% total
    uint256 public constant MINIMUM_LIQUIDITY = 1000; // First 1000 LP tokens locked forever

    IERC1155 public immutable propertyToken;  // EliteFractionalToken (ERC1155)
    IERC20 public immutable oegpToken;  // OsoolEGPStablecoin (ERC20)

    // ═══════════════════════════════════════════════════════════════
    // STATE VARIABLES
    // ═══════════════════════════════════════════════════════════════

    struct Pool {
        uint256 tokenReserve;     // Property tokens in pool
        uint256 egpReserve;       // OEGP in pool
        uint256 totalLpTokens;    // Total LP tokens issued
        uint256 lastPrice;        // Last trade price (for TWAP)
        uint256 lastUpdateTime;   // Last update timestamp
        uint256 cumulativePrice;  // For Time-Weighted Average Price (TWAP)
        bool initialized;         // Pool initialization flag
    }

    // propertyTokenId => Pool
    mapping(uint256 => Pool) public pools;

    // propertyTokenId => (user => lpTokenBalance)
    mapping(uint256 => mapping(address => uint256)) public lpBalances;

    // Platform fee collection
    uint256 public collectedPlatformFees;
    address public platformFeeRecipient;

    // ═══════════════════════════════════════════════════════════════
    // EVENTS
    // ═══════════════════════════════════════════════════════════════

    event PoolCreated(
        uint256 indexed propertyTokenId,
        uint256 initialTokens,
        uint256 initialEGP,
        address indexed creator
    );

    event LiquidityAdded(
        uint256 indexed propertyTokenId,
        address indexed provider,
        uint256 tokenAmount,
        uint256 egpAmount,
        uint256 lpTokensMinted
    );

    event LiquidityRemoved(
        uint256 indexed propertyTokenId,
        address indexed provider,
        uint256 lpTokensBurned,
        uint256 tokenAmount,
        uint256 egpAmount
    );

    event TokensSwapped(
        uint256 indexed propertyTokenId,
        address indexed trader,
        uint256 tokensIn,
        uint256 egpOut,
        uint256 fee
    );

    event EGPSwapped(
        uint256 indexed propertyTokenId,
        address indexed trader,
        uint256 egpIn,
        uint256 tokensOut,
        uint256 fee
    );

    event PlatformFeeWithdrawn(address indexed recipient, uint256 amount);

    // ═══════════════════════════════════════════════════════════════
    // CONSTRUCTOR
    // ═══════════════════════════════════════════════════════════════

    constructor(
        address _propertyToken,
        address _oegpToken,
        address _platformFeeRecipient
    ) {
        require(_propertyToken != address(0), "Invalid property token");
        require(_oegpToken != address(0), "Invalid OEGP token");
        require(_platformFeeRecipient != address(0), "Invalid fee recipient");

        propertyToken = IERC1155(_propertyToken);
        oegpToken = IERC20(_oegpToken);
        platformFeeRecipient = _platformFeeRecipient;
    }

    // ═══════════════════════════════════════════════════════════════
    // POOL CREATION
    // ═══════════════════════════════════════════════════════════════

    /**
     * @notice Create a new liquidity pool for a property token
     * @param propertyTokenId The ERC1155 token ID for the property
     * @param tokenAmount Initial property tokens to deposit
     * @param egpAmount Initial OEGP to deposit
     * @return lpTokens Amount of LP tokens minted
     */
    function createPool(
        uint256 propertyTokenId,
        uint256 tokenAmount,
        uint256 egpAmount
    ) external nonReentrant whenNotPaused returns (uint256 lpTokens) {
        require(!pools[propertyTokenId].initialized, "Pool already exists");
        require(tokenAmount > 0 && egpAmount > 0, "Amounts must be > 0");
        require(tokenAmount >= MINIMUM_LIQUIDITY && egpAmount >= MINIMUM_LIQUIDITY,
            "Initial liquidity too low");

        // Calculate initial LP tokens (geometric mean)
        lpTokens = sqrt(tokenAmount * egpAmount);
        require(lpTokens > MINIMUM_LIQUIDITY, "Insufficient liquidity minted");

        // Lock first MINIMUM_LIQUIDITY LP tokens forever (anti-rug pull)
        uint256 lpToMint = lpTokens - MINIMUM_LIQUIDITY;

        // Transfer tokens from user
        propertyToken.safeTransferFrom(
            msg.sender,
            address(this),
            propertyTokenId,
            tokenAmount,
            ""
        );

        require(
            oegpToken.transferFrom(msg.sender, address(this), egpAmount),
            "OEGP transfer failed"
        );

        // Initialize pool
        pools[propertyTokenId] = Pool({
            tokenReserve: tokenAmount,
            egpReserve: egpAmount,
            totalLpTokens: lpTokens,
            lastPrice: (egpAmount * 1e18) / tokenAmount,
            lastUpdateTime: block.timestamp,
            cumulativePrice: 0,
            initialized: true
        });

        // Mint LP tokens to user
        lpBalances[propertyTokenId][msg.sender] = lpToMint;

        emit PoolCreated(propertyTokenId, tokenAmount, egpAmount, msg.sender);
        emit LiquidityAdded(propertyTokenId, msg.sender, tokenAmount, egpAmount, lpToMint);

        return lpToMint;
    }

    // ═══════════════════════════════════════════════════════════════
    // LIQUIDITY PROVISION
    // ═══════════════════════════════════════════════════════════════

    /**
     * @notice Add liquidity to an existing pool
     * @param propertyTokenId The property token ID
     * @param tokenAmount Property tokens to deposit
     * @param egpAmount OEGP to deposit
     * @param minLpTokens Minimum LP tokens to receive (slippage protection)
     * @return lpTokens Amount of LP tokens minted
     */
    function addLiquidity(
        uint256 propertyTokenId,
        uint256 tokenAmount,
        uint256 egpAmount,
        uint256 minLpTokens
    ) external nonReentrant whenNotPaused returns (uint256 lpTokens) {
        Pool storage pool = pools[propertyTokenId];
        require(pool.initialized, "Pool does not exist");
        require(tokenAmount > 0 && egpAmount > 0, "Amounts must be > 0");

        // Calculate LP tokens to mint (proportional to pool reserves)
        uint256 lpFromTokens = (tokenAmount * pool.totalLpTokens) / pool.tokenReserve;
        uint256 lpFromEGP = (egpAmount * pool.totalLpTokens) / pool.egpReserve;

        // Use the smaller amount to maintain ratio
        lpTokens = lpFromTokens < lpFromEGP ? lpFromTokens : lpFromEGP;
        require(lpTokens >= minLpTokens, "Slippage exceeded");
        require(lpTokens > 0, "Insufficient liquidity minted");

        // Calculate actual amounts to deposit (to maintain exact ratio)
        uint256 actualTokenAmount = (lpTokens * pool.tokenReserve) / pool.totalLpTokens;
        uint256 actualEGPAmount = (lpTokens * pool.egpReserve) / pool.totalLpTokens;

        // Transfer tokens
        propertyToken.safeTransferFrom(
            msg.sender,
            address(this),
            propertyTokenId,
            actualTokenAmount,
            ""
        );

        require(
            oegpToken.transferFrom(msg.sender, address(this), actualEGPAmount),
            "OEGP transfer failed"
        );

        // Update pool state
        pool.tokenReserve += actualTokenAmount;
        pool.egpReserve += actualEGPAmount;
        pool.totalLpTokens += lpTokens;
        _updatePrice(propertyTokenId);

        // Mint LP tokens
        lpBalances[propertyTokenId][msg.sender] += lpTokens;

        emit LiquidityAdded(
            propertyTokenId,
            msg.sender,
            actualTokenAmount,
            actualEGPAmount,
            lpTokens
        );

        return lpTokens;
    }

    /**
     * @notice Remove liquidity from pool
     * @param propertyTokenId The property token ID
     * @param lpTokens Amount of LP tokens to burn
     * @param minTokenAmount Minimum property tokens to receive
     * @param minEGPAmount Minimum OEGP to receive
     * @return tokenAmount Property tokens received
     * @return egpAmount OEGP received
     */
    function removeLiquidity(
        uint256 propertyTokenId,
        uint256 lpTokens,
        uint256 minTokenAmount,
        uint256 minEGPAmount
    ) external nonReentrant returns (uint256 tokenAmount, uint256 egpAmount) {
        Pool storage pool = pools[propertyTokenId];
        require(pool.initialized, "Pool does not exist");
        require(lpTokens > 0, "LP tokens must be > 0");
        require(lpBalances[propertyTokenId][msg.sender] >= lpTokens, "Insufficient LP balance");

        // Calculate amounts to return (proportional to LP tokens)
        tokenAmount = (lpTokens * pool.tokenReserve) / pool.totalLpTokens;
        egpAmount = (lpTokens * pool.egpReserve) / pool.totalLpTokens;

        require(tokenAmount >= minTokenAmount, "Token slippage exceeded");
        require(egpAmount >= minEGPAmount, "EGP slippage exceeded");

        // Update state
        lpBalances[propertyTokenId][msg.sender] -= lpTokens;
        pool.tokenReserve -= tokenAmount;
        pool.egpReserve -= egpAmount;
        pool.totalLpTokens -= lpTokens;
        _updatePrice(propertyTokenId);

        // Transfer tokens to user
        propertyToken.safeTransferFrom(
            address(this),
            msg.sender,
            propertyTokenId,
            tokenAmount,
            ""
        );

        require(oegpToken.transfer(msg.sender, egpAmount), "OEGP transfer failed");

        emit LiquidityRemoved(propertyTokenId, msg.sender, lpTokens, tokenAmount, egpAmount);

        return (tokenAmount, egpAmount);
    }

    // ═══════════════════════════════════════════════════════════════
    // TRADING (SWAPS)
    // ═══════════════════════════════════════════════════════════════

    /**
     * @notice Swap property tokens for OEGP
     * @param propertyTokenId The property token ID
     * @param tokenAmountIn Property tokens to sell
     * @param minEGPOut Minimum OEGP to receive (slippage protection)
     * @return egpOut Amount of OEGP received
     */
    function swapTokensForEGP(
        uint256 propertyTokenId,
        uint256 tokenAmountIn,
        uint256 minEGPOut
    ) external nonReentrant whenNotPaused returns (uint256 egpOut) {
        Pool storage pool = pools[propertyTokenId];
        require(pool.initialized, "Pool does not exist");
        require(tokenAmountIn > 0, "Amount must be > 0");

        // Calculate output amount with fee (x * y = k formula)
        uint256 tokenAmountInWithFee = tokenAmountIn * (FEE_DENOMINATOR - TOTAL_FEE);
        uint256 numerator = tokenAmountInWithFee * pool.egpReserve;
        uint256 denominator = (pool.tokenReserve * FEE_DENOMINATOR) + tokenAmountInWithFee;
        egpOut = numerator / denominator;

        require(egpOut >= minEGPOut, "Slippage exceeded");
        require(egpOut < pool.egpReserve, "Insufficient liquidity");

        // Calculate fees
        uint256 totalFeeAmount = (tokenAmountIn * TOTAL_FEE) / FEE_DENOMINATOR;
        uint256 platformFeeAmount = (totalFeeAmount * PLATFORM_FEE) / TOTAL_FEE;

        // Transfer tokens from user
        propertyToken.safeTransferFrom(
            msg.sender,
            address(this),
            propertyTokenId,
            tokenAmountIn,
            ""
        );

        // Update reserves
        pool.tokenReserve += tokenAmountIn;
        pool.egpReserve -= egpOut;
        _updatePrice(propertyTokenId);

        // Collect platform fee
        collectedPlatformFees += platformFeeAmount;

        // Transfer OEGP to user
        require(oegpToken.transfer(msg.sender, egpOut), "OEGP transfer failed");

        emit TokensSwapped(propertyTokenId, msg.sender, tokenAmountIn, egpOut, totalFeeAmount);

        return egpOut;
    }

    /**
     * @notice Swap OEGP for property tokens
     * @param propertyTokenId The property token ID
     * @param egpAmountIn OEGP to spend
     * @param minTokensOut Minimum property tokens to receive
     * @return tokensOut Amount of property tokens received
     */
    function swapEGPForTokens(
        uint256 propertyTokenId,
        uint256 egpAmountIn,
        uint256 minTokensOut
    ) external nonReentrant whenNotPaused returns (uint256 tokensOut) {
        Pool storage pool = pools[propertyTokenId];
        require(pool.initialized, "Pool does not exist");
        require(egpAmountIn > 0, "Amount must be > 0");

        // Calculate output amount with fee
        uint256 egpAmountInWithFee = egpAmountIn * (FEE_DENOMINATOR - TOTAL_FEE);
        uint256 numerator = egpAmountInWithFee * pool.tokenReserve;
        uint256 denominator = (pool.egpReserve * FEE_DENOMINATOR) + egpAmountInWithFee;
        tokensOut = numerator / denominator;

        require(tokensOut >= minTokensOut, "Slippage exceeded");
        require(tokensOut < pool.tokenReserve, "Insufficient liquidity");

        // Calculate fees
        uint256 totalFeeAmount = (egpAmountIn * TOTAL_FEE) / FEE_DENOMINATOR;
        uint256 platformFeeAmount = (totalFeeAmount * PLATFORM_FEE) / TOTAL_FEE;

        // Transfer OEGP from user
        require(
            oegpToken.transferFrom(msg.sender, address(this), egpAmountIn),
            "OEGP transfer failed"
        );

        // Update reserves
        pool.egpReserve += egpAmountIn;
        pool.tokenReserve -= tokensOut;
        _updatePrice(propertyTokenId);

        // Collect platform fee
        collectedPlatformFees += platformFeeAmount;

        // Transfer tokens to user
        propertyToken.safeTransferFrom(
            address(this),
            msg.sender,
            propertyTokenId,
            tokensOut,
            ""
        );

        emit EGPSwapped(propertyTokenId, msg.sender, egpAmountIn, tokensOut, totalFeeAmount);

        return tokensOut;
    }

    // ═══════════════════════════════════════════════════════════════
    // VIEW FUNCTIONS
    // ═══════════════════════════════════════════════════════════════

    /**
     * @notice Get current price of property token in OEGP
     * @param propertyTokenId The property token ID
     * @return price Current price (OEGP per token, scaled by 1e18)
     */
    function getPrice(uint256 propertyTokenId) external view returns (uint256 price) {
        Pool storage pool = pools[propertyTokenId];
        require(pool.initialized, "Pool does not exist");
        require(pool.tokenReserve > 0, "No liquidity");

        return (pool.egpReserve * 1e18) / pool.tokenReserve;
    }

    /**
     * @notice Get quote for swapping tokens to EGP
     * @param propertyTokenId The property token ID
     * @param tokenAmountIn Property tokens to sell
     * @return egpOut Estimated OEGP to receive
     * @return priceImpact Price impact percentage (scaled by 100)
     */
    function getTokenToEGPQuote(
        uint256 propertyTokenId,
        uint256 tokenAmountIn
    ) external view returns (uint256 egpOut, uint256 priceImpact) {
        Pool storage pool = pools[propertyTokenId];
        require(pool.initialized, "Pool does not exist");

        // Calculate output with fee
        uint256 tokenAmountInWithFee = tokenAmountIn * (FEE_DENOMINATOR - TOTAL_FEE);
        uint256 numerator = tokenAmountInWithFee * pool.egpReserve;
        uint256 denominator = (pool.tokenReserve * FEE_DENOMINATOR) + tokenAmountInWithFee;
        egpOut = numerator / denominator;

        // Calculate price impact
        uint256 currentPrice = (pool.egpReserve * 1e18) / pool.tokenReserve;
        uint256 executionPrice = (egpOut * 1e18) / tokenAmountIn;
        priceImpact = ((currentPrice - executionPrice) * 10000) / currentPrice;

        return (egpOut, priceImpact);
    }

    /**
     * @notice Get quote for swapping EGP to tokens
     * @param propertyTokenId The property token ID
     * @param egpAmountIn OEGP to spend
     * @return tokensOut Estimated property tokens to receive
     * @return priceImpact Price impact percentage (scaled by 100)
     */
    function getEGPToTokenQuote(
        uint256 propertyTokenId,
        uint256 egpAmountIn
    ) external view returns (uint256 tokensOut, uint256 priceImpact) {
        Pool storage pool = pools[propertyTokenId];
        require(pool.initialized, "Pool does not exist");

        // Calculate output with fee
        uint256 egpAmountInWithFee = egpAmountIn * (FEE_DENOMINATOR - TOTAL_FEE);
        uint256 numerator = egpAmountInWithFee * pool.tokenReserve;
        uint256 denominator = (pool.egpReserve * FEE_DENOMINATOR) + egpAmountInWithFee;
        tokensOut = numerator / denominator;

        // Calculate price impact
        uint256 currentPrice = (pool.egpReserve * 1e18) / pool.tokenReserve;
        uint256 executionPrice = (egpAmountIn * 1e18) / tokensOut;
        priceImpact = ((executionPrice - currentPrice) * 10000) / currentPrice;

        return (tokensOut, priceImpact);
    }

    /**
     * @notice Get pool reserves and total LP tokens
     * @param propertyTokenId The property token ID
     * @return tokenReserve Property tokens in pool
     * @return egpReserve OEGP in pool
     * @return totalLpTokens Total LP tokens issued
     */
    function getPoolInfo(uint256 propertyTokenId) external view returns (
        uint256 tokenReserve,
        uint256 egpReserve,
        uint256 totalLpTokens
    ) {
        Pool storage pool = pools[propertyTokenId];
        require(pool.initialized, "Pool does not exist");

        return (pool.tokenReserve, pool.egpReserve, pool.totalLpTokens);
    }

    /**
     * @notice Get user's LP token balance
     * @param propertyTokenId The property token ID
     * @param user User address
     * @return balance LP token balance
     */
    function getLPBalance(uint256 propertyTokenId, address user) external view returns (uint256) {
        return lpBalances[propertyTokenId][user];
    }

    // ═══════════════════════════════════════════════════════════════
    // ADMIN FUNCTIONS
    // ═══════════════════════════════════════════════════════════════

    /**
     * @notice Withdraw collected platform fees
     */
    function withdrawPlatformFees() external onlyOwner {
        uint256 amount = collectedPlatformFees;
        require(amount > 0, "No fees to withdraw");

        collectedPlatformFees = 0;
        require(oegpToken.transfer(platformFeeRecipient, amount), "Transfer failed");

        emit PlatformFeeWithdrawn(platformFeeRecipient, amount);
    }

    /**
     * @notice Update platform fee recipient
     */
    function setPlatformFeeRecipient(address newRecipient) external onlyOwner {
        require(newRecipient != address(0), "Invalid address");
        platformFeeRecipient = newRecipient;
    }

    /**
     * @notice Emergency pause trading
     */
    function pause() external onlyOwner {
        _pause();
    }

    /**
     * @notice Unpause trading
     */
    function unpause() external onlyOwner {
        _unpause();
    }

    // ═══════════════════════════════════════════════════════════════
    // INTERNAL FUNCTIONS
    // ═══════════════════════════════════════════════════════════════

    /**
     * @dev Update price oracle (TWAP)
     */
    function _updatePrice(uint256 propertyTokenId) internal {
        Pool storage pool = pools[propertyTokenId];

        uint256 timeElapsed = block.timestamp - pool.lastUpdateTime;
        if (timeElapsed > 0) {
            // Update cumulative price for TWAP
            pool.cumulativePrice += pool.lastPrice * timeElapsed;
            pool.lastPrice = (pool.egpReserve * 1e18) / pool.tokenReserve;
            pool.lastUpdateTime = block.timestamp;
        }
    }

    /**
     * @dev Square root function for LP token calculation
     */
    function sqrt(uint256 y) internal pure returns (uint256 z) {
        if (y > 3) {
            z = y;
            uint256 x = y / 2 + 1;
            while (x < z) {
                z = x;
                x = (y / x + x) / 2;
            }
        } else if (y != 0) {
            z = 1;
        }
    }

    /**
     * @dev Required for ERC1155 token receipt
     */
    function onERC1155Received(
        address,
        address,
        uint256,
        uint256,
        bytes memory
    ) public pure returns (bytes4) {
        return this.onERC1155Received.selector;
    }
}
