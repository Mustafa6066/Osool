// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title OsoolEGPStablecoin (OEGP)
 * @notice EGP-pegged stablecoin for Osool liquidity pools
 * @dev 1 OEGP = 1 EGP (Egyptian Pound)
 *
 * Minting & Burning Flow:
 * 1. User deposits EGP via Paymob payment gateway (off-chain)
 * 2. Backend verifies payment, calls mint() to issue OEGP
 * 3. User trades OEGP in liquidity pools
 * 4. User can redeem OEGP for EGP via backend (burns OEGP, sends EGP)
 *
 * CBE Law 194 Compliance:
 * - OEGP is NOT a cryptocurrency (it's a receipt token)
 * - Backed 1:1 by EGP held in Osool's bank account
 * - Minting requires verified EGP deposit
 * - Burning triggers EGP withdrawal via Paymob
 *
 * Security Features:
 * - Only authorized minters can mint (backend relayer wallet)
 * - Emergency pause mechanism
 * - Blacklist for compliance (AML/KYC)
 * - Maximum supply cap for safety
 *
 * Phase 6: Osool Production Transformation
 */

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

contract OsoolEGPStablecoin is ERC20, AccessControl, Pausable {

    // ═══════════════════════════════════════════════════════════════
    // ROLES
    // ═══════════════════════════════════════════════════════════════

    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant BURNER_ROLE = keccak256("BURNER_ROLE");
    bytes32 public constant BLACKLISTER_ROLE = keccak256("BLACKLISTER_ROLE");

    // ═══════════════════════════════════════════════════════════════
    // STATE VARIABLES
    // ═══════════════════════════════════════════════════════════════

    // Maximum supply cap (100 million OEGP = 100 million EGP)
    uint256 public constant MAX_SUPPLY = 100_000_000 * 10**18;

    // Blacklist for AML/KYC compliance
    mapping(address => bool) public blacklisted;

    // Mint/Burn tracking for transparency
    uint256 public totalMinted;
    uint256 public totalBurned;

    // Reserve tracking (should match bank account balance)
    uint256 public reserveBalance;  // In wei (18 decimals)

    // ═══════════════════════════════════════════════════════════════
    // EVENTS
    // ═══════════════════════════════════════════════════════════════

    event Minted(
        address indexed to,
        uint256 amount,
        string paymobReference,
        uint256 newReserveBalance
    );

    event Burned(
        address indexed from,
        uint256 amount,
        string withdrawalReference,
        uint256 newReserveBalance
    );

    event Blacklisted(address indexed account, bool status);

    event ReserveAdjusted(uint256 oldBalance, uint256 newBalance, string reason);

    // ═══════════════════════════════════════════════════════════════
    // CONSTRUCTOR
    // ═══════════════════════════════════════════════════════════════

    constructor() ERC20("Osool EGP Stablecoin", "OEGP") {
        // Grant admin role to deployer
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);

        // Grant minter and burner roles to deployer (will delegate to backend)
        _grantRole(MINTER_ROLE, msg.sender);
        _grantRole(BURNER_ROLE, msg.sender);
        _grantRole(BLACKLISTER_ROLE, msg.sender);
    }

    // ═══════════════════════════════════════════════════════════════
    // MINTING (Deposit EGP → Receive OEGP)
    // ═══════════════════════════════════════════════════════════════

    /**
     * @notice Mint OEGP tokens after verifying EGP deposit
     * @dev Only callable by authorized minter (backend relayer)
     * @param to Recipient address
     * @param amount Amount to mint (in wei, 18 decimals)
     * @param paymobReference Paymob payment reference for tracking
     */
    function mint(
        address to,
        uint256 amount,
        string calldata paymobReference
    ) external onlyRole(MINTER_ROLE) whenNotPaused {
        require(to != address(0), "Cannot mint to zero address");
        require(!blacklisted[to], "Recipient is blacklisted");
        require(amount > 0, "Amount must be greater than 0");
        require(totalSupply() + amount <= MAX_SUPPLY, "Exceeds max supply");

        // Update reserve balance (should match bank account)
        reserveBalance += amount;
        totalMinted += amount;

        // Mint tokens
        _mint(to, amount);

        emit Minted(to, amount, paymobReference, reserveBalance);
    }

    /**
     * @notice Batch mint for multiple users (gas optimization)
     * @param recipients Array of recipient addresses
     * @param amounts Array of amounts to mint
     * @param paymobReference Batch payment reference
     */
    function batchMint(
        address[] calldata recipients,
        uint256[] calldata amounts,
        string calldata paymobReference
    ) external onlyRole(MINTER_ROLE) whenNotPaused {
        require(recipients.length == amounts.length, "Array length mismatch");
        require(recipients.length <= 100, "Batch too large");

        uint256 totalAmount = 0;
        for (uint256 i = 0; i < recipients.length; i++) {
            require(recipients[i] != address(0), "Invalid recipient");
            require(!blacklisted[recipients[i]], "Recipient is blacklisted");
            require(amounts[i] > 0, "Invalid amount");

            totalAmount += amounts[i];
            _mint(recipients[i], amounts[i]);
        }

        require(totalSupply() + totalAmount <= MAX_SUPPLY, "Exceeds max supply");

        reserveBalance += totalAmount;
        totalMinted += totalAmount;

        emit Minted(address(0), totalAmount, paymobReference, reserveBalance);
    }

    // ═══════════════════════════════════════════════════════════════
    // BURNING (Redeem OEGP → Withdraw EGP)
    // ═══════════════════════════════════════════════════════════════

    /**
     * @notice Burn OEGP tokens to withdraw EGP
     * @dev Only callable by authorized burner (backend) after initiating EGP withdrawal
     * @param from Address to burn from
     * @param amount Amount to burn
     * @param withdrawalReference Paymob withdrawal reference
     */
    function burn(
        address from,
        uint256 amount,
        string calldata withdrawalReference
    ) external onlyRole(BURNER_ROLE) {
        require(from != address(0), "Cannot burn from zero address");
        require(!blacklisted[from], "Account is blacklisted");
        require(amount > 0, "Amount must be greater than 0");
        require(balanceOf(from) >= amount, "Insufficient balance");
        require(reserveBalance >= amount, "Reserve underflow");

        // Update reserve balance
        reserveBalance -= amount;
        totalBurned += amount;

        // Burn tokens
        _burn(from, amount);

        emit Burned(from, amount, withdrawalReference, reserveBalance);
    }

    /**
     * @notice User-initiated burn (must approve contract first)
     * @dev User burns their tokens, backend processes EGP withdrawal
     * @param amount Amount to burn
     */
    function burnSelf(uint256 amount) external whenNotPaused {
        require(!blacklisted[msg.sender], "Account is blacklisted");
        require(amount > 0, "Amount must be greater than 0");
        require(balanceOf(msg.sender) >= amount, "Insufficient balance");
        require(reserveBalance >= amount, "Reserve underflow");

        // Update reserve balance
        reserveBalance -= amount;
        totalBurned += amount;

        // Burn tokens
        _burn(msg.sender, amount);

        emit Burned(msg.sender, amount, "user_initiated", reserveBalance);
    }

    // ═══════════════════════════════════════════════════════════════
    // BLACKLIST (AML/KYC COMPLIANCE)
    // ═══════════════════════════════════════════════════════════════

    /**
     * @notice Add address to blacklist
     * @param account Address to blacklist
     */
    function addToBlacklist(address account) external onlyRole(BLACKLISTER_ROLE) {
        require(account != address(0), "Invalid address");
        blacklisted[account] = true;
        emit Blacklisted(account, true);
    }

    /**
     * @notice Remove address from blacklist
     * @param account Address to remove from blacklist
     */
    function removeFromBlacklist(address account) external onlyRole(BLACKLISTER_ROLE) {
        blacklisted[account] = false;
        emit Blacklisted(account, false);
    }

    // ═══════════════════════════════════════════════════════════════
    // RESERVE MANAGEMENT
    // ═══════════════════════════════════════════════════════════════

    /**
     * @notice Adjust reserve balance (for reconciliation)
     * @dev Only admin can adjust if bank balance differs from on-chain reserve
     * @param newBalance New reserve balance
     * @param reason Reason for adjustment
     */
    function adjustReserve(
        uint256 newBalance,
        string calldata reason
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 oldBalance = reserveBalance;
        reserveBalance = newBalance;
        emit ReserveAdjusted(oldBalance, newBalance, reason);
    }

    // ═══════════════════════════════════════════════════════════════
    // EMERGENCY FUNCTIONS
    // ═══════════════════════════════════════════════════════════════

    /**
     * @notice Pause all transfers (emergency)
     */
    function pause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _pause();
    }

    /**
     * @notice Unpause transfers
     */
    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }

    // ═══════════════════════════════════════════════════════════════
    // VIEW FUNCTIONS
    // ═══════════════════════════════════════════════════════════════

    /**
     * @notice Get current reserve ratio (should always be 100%)
     * @return ratio Reserve ratio in basis points (10000 = 100%)
     */
    function getReserveRatio() external view returns (uint256 ratio) {
        if (totalSupply() == 0) return 10000;
        return (reserveBalance * 10000) / totalSupply();
    }

    /**
     * @notice Get comprehensive stablecoin stats
     */
    function getStats() external view returns (
        uint256 _totalSupply,
        uint256 _totalMinted,
        uint256 _totalBurned,
        uint256 _reserveBalance,
        uint256 _reserveRatio,
        uint256 _maxSupply
    ) {
        _totalSupply = totalSupply();
        _totalMinted = totalMinted;
        _totalBurned = totalBurned;
        _reserveBalance = reserveBalance;
        _reserveRatio = _totalSupply > 0 ? (reserveBalance * 10000) / _totalSupply : 10000;
        _maxSupply = MAX_SUPPLY;
    }

    // ═══════════════════════════════════════════════════════════════
    // OVERRIDES (Blacklist Enforcement)
    // ═══════════════════════════════════════════════════════════════

    /**
     * @dev Override transfer to enforce blacklist
     */
    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 amount
    ) internal virtual override whenNotPaused {
        require(!blacklisted[from], "Sender is blacklisted");
        require(!blacklisted[to], "Recipient is blacklisted");
        super._beforeTokenTransfer(from, to, amount);
    }

    /**
     * @notice Check if account can transfer tokens
     */
    function canTransfer(address account) external view returns (bool) {
        return !blacklisted[account] && !paused();
    }
}
