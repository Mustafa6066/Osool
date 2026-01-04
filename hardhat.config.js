require("@nomiclabs/hardhat-ethers");
require("dotenv").config();

// Define accounts array
const accounts = process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [];

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
    solidity: {
        version: "0.8.19",
        settings: {
            optimizer: {
                enabled: true,
                runs: 200
            }
        }
    },

    networks: {
        // Local development
        hardhat: {
            chainId: 31337
        },

        localhost: {
            url: "http://127.0.0.1:8545",
            chainId: 31337
        },

        // Testnets
        sepolia: {
            url: process.env.SEPOLIA_URL || "",
            accounts,
            chainId: 11155111
        },

        // Polygon Amoy Testnet (replaced Mumbai)
        amoy: {
            url: process.env.AMOY_RPC_URL || "https://rpc-amoy.polygon.technology",
            accounts,
            chainId: 80002,
            gasPrice: 30000000000 // 30 gwei
        },

        // Legacy Mumbai (deprecated but kept for reference)
        mumbai: {
            url: process.env.MUMBAI_RPC_URL || "https://rpc-mumbai.maticvigil.com",
            accounts,
            chainId: 80001
        },

        // Mainnets
        polygon: {
            url: process.env.POLYGON_RPC_URL || "https://polygon-rpc.com",
            accounts,
            chainId: 137
        }
    },

    paths: {
        sources: "./contracts",
        tests: "./test",
        cache: "./cache",
        artifacts: "./artifacts"
    }
};
