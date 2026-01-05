/**
 * OsoolRegistry Deployment Script
 * 
 * Deploys the legal-compliant property registry to Polygon.
 * Compatible with ethers v5 (hardhat-ethers)
 * 
 * Usage:
 *   npx hardhat run scripts/deploy-registry.js --network amoy
 */

const hre = require("hardhat");

async function main() {
    console.log("=".repeat(50));
    console.log("[*] Deploying OsoolRegistry Contract...");
    console.log("=".repeat(50));

    // Get the deployer account
    const [deployer] = await hre.ethers.getSigners();
    console.log("[*] Deployer address:", deployer.address);

    // Check balance (ethers v5 syntax)
    const balance = await deployer.getBalance();
    console.log("[*] Deployer balance:", hre.ethers.utils.formatEther(balance), "MATIC");

    if (balance.eq(0)) {
        console.log("\n[!] WARNING: Deployer has 0 balance!");
        console.log("[!] Get testnet MATIC from: https://faucet.polygon.technology/");
        process.exit(1);
    }

    // Deploy OsoolRegistry
    console.log("\n[*] Deploying OsoolRegistry...");
    const OsoolRegistry = await hre.ethers.getContractFactory("OsoolRegistry");
    const registry = await OsoolRegistry.deploy();

    await registry.deployed(); // ethers v5 syntax
    const registryAddress = registry.address; // ethers v5 syntax

    console.log("\n" + "=".repeat(50));
    console.log("[+] OsoolRegistry Deployed Successfully!");
    console.log("[+] Contract Address:", registryAddress);
    console.log("=".repeat(50));

    // Save deployment info
    console.log("\n[*] Next Steps:");
    console.log(`   1. Add to .env: OSOOL_REGISTRY_ADDRESS=${registryAddress}`);
    console.log(`   2. Add to web/.env.local: NEXT_PUBLIC_REGISTRY_ADDRESS=${registryAddress}`);
    console.log(`   3. Verify on PolygonScan:`);
    console.log(`      npx hardhat verify --network amoy ${registryAddress}`);

    // Test the contract
    console.log("\n[*] Testing contract...");
    const nextId = await registry.nextId();
    const totalListings = await registry.totalListings();
    console.log(`   - nextId: ${nextId}`);
    console.log(`   - totalListings: ${totalListings}`);
    console.log("\n[+] Deployment Complete!");

    return { registryAddress };
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("[!] Deployment failed:", error);
        process.exit(1);
    });
