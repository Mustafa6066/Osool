const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
    console.log("🚀 Deploying Elite Property Advisor Smart Contracts...\n");

    // Get the deployer account
    const [deployer] = await hre.ethers.getSigners();
    console.log("Deploying contracts with account:", deployer.address);
    console.log("Account balance:", (await deployer.getBalance()).toString());

    // ═══════════════════════════════════════════════════════════════
    // DEPLOY EXISTING CONTRACTS
    // ═══════════════════════════════════════════════════════════════

    // Deploy EliteSubscriptionToken
    console.log("\n📜 Deploying EliteSubscriptionToken...");
    const EliteSubscriptionToken = await hre.ethers.getContractFactory("EliteSubscriptionToken");
    const subscriptionToken = await EliteSubscriptionToken.deploy();
    await subscriptionToken.deployed();
    console.log("✅ EliteSubscriptionToken deployed to:", subscriptionToken.address);

    // Deploy ElitePropertyEscrow
    console.log("\n📜 Deploying ElitePropertyEscrow...");
    const ElitePropertyEscrow = await hre.ethers.getContractFactory("ElitePropertyEscrow");
    const escrow = await ElitePropertyEscrow.deploy(deployer.address);
    await escrow.deployed();
    console.log("✅ ElitePropertyEscrow deployed to:", escrow.address);

    // ═══════════════════════════════════════════════════════════════
    // DEPLOY NEW PLATFORM CONTRACTS
    // ═══════════════════════════════════════════════════════════════

    // Deploy ElitePropertyToken (EPT)
    console.log("\n📜 Deploying Elite Property Token (EPT)...");
    const ElitePropertyToken = await hre.ethers.getContractFactory("ElitePropertyToken");
    const eptToken = await ElitePropertyToken.deploy();
    await eptToken.deployed();
    console.log("✅ EPT Token deployed to:", eptToken.address);
    console.log("   Total Supply: 100,000,000 EPT");

    // Deploy EliteMembershipNFT
    console.log("\n📜 Deploying Elite Membership NFT...");
    const EliteMembershipNFT = await hre.ethers.getContractFactory("EliteMembershipNFT");
    const membershipNFT = await EliteMembershipNFT.deploy();
    await membershipNFT.deployed();
    console.log("✅ Membership NFT deployed to:", membershipNFT.address);

    // Deploy ElitePropertyPlatform
    console.log("\n📜 Deploying Elite Property Platform...");
    const ElitePropertyPlatform = await hre.ethers.getContractFactory("ElitePropertyPlatform");
    const platform = await ElitePropertyPlatform.deploy(eptToken.address, membershipNFT.address);
    await platform.deployed();
    console.log("✅ Platform deployed to:", platform.address);

    // ═══════════════════════════════════════════════════════════════
    // CONFIGURE CONTRACTS
    // ═══════════════════════════════════════════════════════════════

    console.log("\n⚙️ Configuring contracts...");

    // Transfer ownership of NFT contract to Platform
    console.log("   - Transferring NFT ownership to platform...");
    await membershipNFT.transferOwnership(platform.address);
    console.log("   ✅ NFT ownership transferred");

    // Transfer ownership of EPT token to Platform (for minting rewards)
    console.log("   - Transferring token ownership to platform...");
    await eptToken.transferOwnership(platform.address);
    console.log("   ✅ Token ownership transferred");

    // ═══════════════════════════════════════════════════════════════
    // SAVE DEPLOYMENT INFO
    // ═══════════════════════════════════════════════════════════════

    const deploymentInfo = {
        network: hre.network.name,
        timestamp: new Date().toISOString(),
        deployer: deployer.address,
        contracts: {
            // Existing contracts
            EliteSubscriptionToken: subscriptionToken.address,
            ElitePropertyEscrow: escrow.address,
            // New platform contracts
            ElitePropertyToken: eptToken.address,
            EliteMembershipNFT: membershipNFT.address,
            ElitePropertyPlatform: platform.address
        }
    };

    // Ensure deployments directory exists
    const deploymentsDir = path.join(__dirname, "..", "deployments");
    if (!fs.existsSync(deploymentsDir)) {
        fs.mkdirSync(deploymentsDir, { recursive: true });
    }

    // Save deployment info
    const filename = `${hre.network.name}-${Date.now()}.json`;
    fs.writeFileSync(
        path.join(deploymentsDir, filename),
        JSON.stringify(deploymentInfo, null, 2)
    );

    // ═══════════════════════════════════════════════════════════════
    // OUTPUT SUMMARY
    // ═══════════════════════════════════════════════════════════════

    console.log("\n" + "═".repeat(60));
    console.log("🎉 DEPLOYMENT COMPLETE!");
    console.log("═".repeat(60));
    console.log(`
Contract Addresses:
───────────────────
EliteSubscriptionToken: ${subscriptionToken.address}
ElitePropertyEscrow:    ${escrow.address}
ElitePropertyToken:     ${eptToken.address}
EliteMembershipNFT:     ${membershipNFT.address}
ElitePropertyPlatform:  ${platform.address}

📝 Update blockchain.js CONTRACT_ADDRESSES with:
───────────────────────────────────────────────
subscription: '${subscriptionToken.address}'
escrow: '${escrow.address}'
eptToken: '${eptToken.address}'
nft: '${membershipNFT.address}'
platform: '${platform.address}'

📄 Deployment saved to: deployments/${filename}
    `);
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
