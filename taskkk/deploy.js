const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
  console.log("Starting Elite Property Platform deployment...\n");

  // Get the contract factories
  const ElitePropertyToken = await hre.ethers.getContractFactory("ElitePropertyToken");
  const EliteMembershipNFT = await hre.ethers.getContractFactory("EliteMembershipNFT");
  const ElitePropertyPlatform = await hre.ethers.getContractFactory("ElitePropertyPlatform");

  // Deploy ElitePropertyToken (EPT)
  console.log("1. Deploying Elite Property Token (EPT)...");
  const eptToken = await ElitePropertyToken.deploy();
  await eptToken.deployed();
  console.log("   ✅ EPT Token deployed to:", eptToken.address);
  console.log("   Total Supply: 100,000,000 EPT");

  // Deploy EliteMembershipNFT
  console.log("\n2. Deploying Elite Membership NFT...");
  const membershipNFT = await EliteMembershipNFT.deploy();
  await membershipNFT.deployed();
  console.log("   ✅ Membership NFT deployed to:", membershipNFT.address);

  // Deploy ElitePropertyPlatform
  console.log("\n3. Deploying Elite Property Platform...");
  const platform = await ElitePropertyPlatform.deploy(
    eptToken.address,
    membershipNFT.address
  );
  await platform.deployed();
  console.log("   ✅ Platform deployed to:", platform.address);

  // Configure contracts
  console.log("\n4. Configuring contracts...");

  // Transfer ownership of NFT contract to Platform
  console.log("   - Transferring NFT ownership to platform...");
  await membershipNFT.transferOwnership(platform.address);
  console.log("   ✅ NFT ownership transferred");

  // Approve platform to mint tokens (for rewards)
  console.log("   - Granting platform minting rights...");
  await eptToken.transferOwnership(platform.address);
  console.log("   ✅ Token minting rights granted");

  // Set base URI for NFTs (update with your IPFS gateway)
  console.log("   - Setting NFT metadata base URI...");
  await membershipNFT.setBaseURI("https://gateway.pinata.cloud/ipfs/YOUR_IPFS_HASH/");
  console.log("   ✅ Base URI set");

  // Initial token distribution (optional)
  console.log("\n5. Initial token distribution...");
  const [deployer] = await ethers.getSigners();
  
  // Mint some tokens for initial liquidity and marketing
  const marketingAmount = ethers.utils.parseEther("10000000"); // 10M tokens
  const liquidityAmount = ethers.utils.parseEther("20000000"); // 20M tokens
  
  console.log("   - Marketing wallet allocation: 10,000,000 EPT");
  console.log("   - Liquidity provision: 20,000,000 EPT");
  
  // Verify deployment
  console.log("\n6. Verifying deployment...");
  console.log("   - Platform fee:", await platform.platformFeePercentage() / 100 + "%");
  console.log("   - Subscription prices:");
  console.log("     • Explorer:", ethers.utils.formatEther(await platform.subscriptionPrices(0)), "EPT");
  console.log("     • Premium:", ethers.utils.formatEther(await platform.subscriptionPrices(1)), "EPT");
  console.log("     • Platinum:", ethers.utils.formatEther(await platform.subscriptionPrices(2)), "EPT");

  // Save deployment addresses
  const deploymentInfo = {
    network: hre.network.name,
    timestamp: new Date().toISOString(),
    contracts: {
      ElitePropertyToken: eptToken.address,
      EliteMembershipNFT: membershipNFT.address,
      ElitePropertyPlatform: platform.address
    },
    deployer: deployer.address
  };

  const fs = require("fs");
  fs.writeFileSync(
    `deployments/${hre.network.name}-${Date.now()}.json`,
    JSON.stringify(deploymentInfo, null, 2)
  );

  console.log("\n✅ Deployment complete!");
  console.log("\n📄 Deployment info saved to deployments/");
  
  // Contract verification instructions
  console.log("\n📋 Next steps:");
  console.log("1. Verify contracts on Etherscan/Polygonscan:");
  console.log(`   npx hardhat verify --network ${hre.network.name} ${eptToken.address}`);
  console.log(`   npx hardhat verify --network ${hre.network.name} ${membershipNFT.address}`);
  console.log(`   npx hardhat verify --network ${hre.network.name} ${platform.address} ${eptToken.address} ${membershipNFT.address}`);
  console.log("\n2. Update frontend with contract addresses");
  console.log("3. Add initial liquidity to DEX");
  console.log("4. Configure IPFS for property metadata");
  console.log("5. Set up monitoring and analytics");

  // Generate .env template
  console.log("\n📝 Add these to your .env file:");
  console.log(`NEXT_PUBLIC_PLATFORM_ADDRESS=${platform.address}`);
  console.log(`NEXT_PUBLIC_TOKEN_ADDRESS=${eptToken.address}`);
  console.log(`NEXT_PUBLIC_NFT_ADDRESS=${membershipNFT.address}`);
}

// Execute deployment
main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
