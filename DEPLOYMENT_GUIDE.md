# Osool Blockchain Deployment Guide

This guide covers the deployment of Osool smart contracts to both testnet (Polygon Amoy) and mainnet (Polygon PoS) networks.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Local Testing](#local-testing)
4. [Testnet Deployment (Amoy)](#testnet-deployment-amoy)
5. [Contract Verification](#contract-verification)
6. [Mainnet Deployment](#mainnet-deployment)
7. [Backend Configuration](#backend-configuration)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

```bash
# Node.js and npm (v18+ recommended)
node --version
npm --version

# Hardhat (installed via project dependencies)
npm install

# Polygon Amoy Testnet MATIC
# Get free testnet tokens from: https://faucet.polygon.technology/
```

### Required Accounts

1. **Wallet Setup**
   - Create a new MetaMask wallet for deployment (NEVER use your personal wallet)
   - Export the private key (keep it secure!)
   - Save the address as `ADMIN_WALLET_ADDRESS`

2. **API Keys**
   - Alchemy API key: https://www.alchemy.com/
   - PolygonScan API key: https://polygonscan.com/apis

---

## Environment Setup

### 1. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

### 2. Fill in Required Variables

```bash
# Deployment Wallet
PRIVATE_KEY=your_deployment_wallet_private_key
ADMIN_WALLET_ADDRESS=0xYourAdminAddress

# RPC URLs
POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
AMOY_RPC_URL=https://rpc-amoy.polygon.technology

# Block Explorer API Keys
POLYGONSCAN_API_KEY=your_polygonscan_api_key

# OpenAI (for data ingestion)
OPENAI_API_KEY=your_openai_api_key
```

### 3. Fund Your Deployment Wallet

**For Testnet (Amoy):**
- Visit: https://faucet.polygon.technology/
- Select "Polygon Amoy" network
- Enter your `ADMIN_WALLET_ADDRESS`
- Request tokens (you'll receive ~0.5 MATIC)

**For Mainnet:**
- Purchase MATIC from an exchange (Binance, Coinbase, etc.)
- Transfer to your `ADMIN_WALLET_ADDRESS`
- Recommended: 10-20 MATIC for deployment + initial operations

---

## Local Testing

### 1. Start Local Hardhat Node

```bash
cd blockchain
npx hardhat node
```

This starts a local Ethereum node at `http://127.0.0.1:8545/` with pre-funded test accounts.

### 2. Deploy to Local Network

In a new terminal:

```bash
npx hardhat run scripts/deploy-registry.js --network localhost
```

### 3. Test Contract Interactions

```bash
npx hardhat test
```

Expected output:
```
  OsoolRegistry Tests
    ✓ Should deploy with correct owner
    ✓ Should register a property
    ✓ Should reserve a property
    ✓ Should mark property as sold
    ✓ Should prevent double reservation
```

---

## Testnet Deployment (Amoy)

### 1. Compile Contracts

```bash
cd blockchain
npx hardhat compile
```

Expected output:
```
Compiling 5 files with 0.8.20
Compilation finished successfully
```

### 2. Deploy OsoolRegistry

```bash
npx hardhat run scripts/deploy-registry.js --network amoy
```

**Sample Output:**
```
Deploying OsoolRegistry to Polygon Amoy...
Admin address: 0xYourAdminAddress
Deploying contract...
OsoolRegistry deployed to: 0x1234...abcd
Transaction hash: 0x5678...efgh

✓ Deployment successful!

Save this address to your .env file:
OSOOL_REGISTRY_ADDRESS=0x1234...abcd
```

### 3. Deploy OsoolLiquidityAMM (Optional)

```bash
npx hardhat run scripts/deploy-amm.js --network amoy
```

### 4. Update Environment Variables

Update your `backend/.env` file:

```bash
# Testnet Configuration
OSOOL_REGISTRY_ADDRESS=0x1234...abcd
OSOOL_AMM_ADDRESS=0xAMM...address
POLYGON_RPC_URL=https://rpc-amoy.polygon.technology
CHAIN_ID=80002

# Disable simulation mode to use real blockchain
BLOCKCHAIN_SIMULATION_MODE=false
```

### 5. Verify Deployment

Visit PolygonScan Amoy Explorer:
```
https://amoy.polygonscan.com/address/0x1234...abcd
```

---

## Contract Verification

```bash
npx hardhat verify --network amoy 0x1234...abcd
```

---

## Mainnet Deployment

### ⚠️ CRITICAL SECURITY CHECKLIST

- [ ] **Audit Completed**: Professional smart contract audit
- [ ] **Testnet Validated**: Run on Amoy for 2+ weeks
- [ ] **Multisig Wallet**: Use Gnosis Safe for ownership
- [ ] **Emergency Pause**: Test pause functionality
- [ ] **Backup Keys**: Hardware wallet + encrypted backup

### 1. Deploy to Mainnet

```bash
npx hardhat run scripts/deploy-registry.js --network polygon
```

### 2. Transfer Ownership to Multisig

**CRITICAL: Do this immediately!**

### 3. Verify on PolygonScan

```bash
npx hardhat verify --network polygon 0xYourRegistryAddress
```

---

## Backend Configuration

After deployment, update `backend/.env`:

```bash
OSOOL_REGISTRY_ADDRESS=0xYourDeployedAddress
BLOCKCHAIN_SIMULATION_MODE=false
POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY
CHAIN_ID=137
```

Test backend integration:

```bash
curl http://localhost:8000/api/health
```

---

## Troubleshooting

### "Insufficient funds for gas"
Get testnet MATIC from: https://faucet.polygon.technology/

### "Contract verification failed"
```bash
npx hardhat flatten contracts/OsoolRegistry.sol > OsoolRegistry-flat.sol
```

### "Backend shows simulation mode"
```bash
# Restart backend
pkill -f uvicorn
python -m uvicorn app.main:app --reload
```

---

## Development Mode (Simulation)

For local development without contracts:

```bash
BLOCKCHAIN_SIMULATION_MODE=true
```

**Logs:**
```
[!] BLOCKCHAIN SIMULATION MODE ENABLED
[SIM] Property 123 reserved (TX: 0xSIM...00000123)
```

---

## Resources

- Polygon Docs: https://docs.polygon.technology/
- Hardhat Docs: https://hardhat.org/docs
- Amoy Faucet: https://faucet.polygon.technology/
- PolygonScan: https://polygonscan.com/

---

## Security Best Practices

1. Never commit private keys
2. Use hardware wallets for mainnet
3. Always use multisig for ownership
4. Get professional audits
5. Monitor contracts 24/7
6. Test everything on testnet first

---

**CBE Compliance:** All fiat payments through InstaPay/Fawry only.
