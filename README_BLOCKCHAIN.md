# 🏛️ Elite Property Advisor - Blockchain Integration

This document provides instructions for the blockchain components of the Elite Property Advisor platform.

## Smart Contracts

The platform uses the following smart contracts:

| Contract | Description |
|----------|-------------|
| `EliteSubscriptionToken.sol` | ERC-20 token for subscriptions and loyalty rewards |
| `ElitePropertyEscrow.sol` | Secure escrow for property transactions |
| `ElitePropertyPlatform.sol` | Unified platform with token, NFT membership, and escrow |
| `ElitePropertyToken.sol` | EPT token (100M supply) - part of platform |
| `EliteMembershipNFT.sol` | NFT membership with tiers (Explorer/Premium/Platinum) |

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your private key and RPC URLs
```

### 3. Compile Contracts

```bash
npm run compile
```

### 4. Deploy to Local Network

```bash
# Terminal 1: Start local node
npm run node

# Terminal 2: Deploy contracts
npm run deploy:local
```

### 5. Deploy to Testnet (Mumbai)

```bash
npm run deploy:mumbai
```

## Subscription Tiers

| Tier | Token Cost | Features |
|------|------------|----------|
| Explorer | 100 EPT | Basic AI matching, Virtual concierge |
| Premium | 300 EPT | + Valuation, Portfolio optimizer |
| Platinum | 1000 EPT | + Virtual staging, Personal AI agent |

## Staking Benefits

| Staked Amount | Benefit |
|---------------|---------|
| 1,000+ EPT | Bronze: 25% fee discount |
| 5,000+ EPT | Silver: 50% fee discount |
| 10,000+ EPT | Gold: Priority support + early access |
| 50,000+ EPT | Platinum Elite: 0% fees + personal AI agent |

## Files Structure

```
contracts/
├── ElitePropertyEscrow.sol      # Property escrow
├── EliteSubscriptionToken.sol   # Subscription token
└── ElitePropertyPlatform.sol    # Unified platform

scripts/
└── deploy.js                    # Deployment script

public/assets/js/
└── blockchain.js                # Frontend Web3 integration

deployments/
└── [network]-[timestamp].json   # Deployment outputs
```

## Frontend Integration

The `blockchain.js` file provides a `BlockchainService` class:

```javascript
// Connect wallet
await blockchainService.connectWallet();

// Check subscription
const isActive = await blockchainService.isSubscriptionActive();

// Get token balance
const balance = await blockchainService.getTokenBalance();

// Subscribe
await blockchainService.subscribe(2); // Premium tier
```

## Marketing Strategy

See `taskkk/MARKETING_STRATEGY.md` for the complete first 100 subscribers acquisition plan.
