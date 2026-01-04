require("@nomiclabs/hardhat-waffle");
require("@nomiclabs/hardhat-etherscan");
require("hardhat-gas-reporter");
require("solidity-coverage");
require("hardhat-deploy");
require("dotenv").config();

// Define accounts array
const accounts = process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [];

/**
 * @type import('hardhat/config').HardhatUserConfig
 */
module.exports = {
  solidity: {
    version: "0.8.19",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
    },
  },
  
  networks: {
    // Local development
    hardhat: {
      chainId: 31337,
      forking: {
        url: process.env.ETH_MAINNET_URL || "",
        enabled: false,
      },
    },
    
    localhost: {
      url: "http://127.0.0.1:8545",
    },
    
    // Testnets
    sepolia: {
      url: process.env.SEPOLIA_URL || "",
      accounts,
      chainId: 11155111,
      gasPrice: 20000000000, // 20 gwei
    },
    
    goerli: {
      url: process.env.GOERLI_URL || "",
      accounts,
      chainId: 5,
    },
    
    mumbai: {
      url: process.env.MUMBAI_URL || "https://rpc-mumbai.maticvigil.com",
      accounts,
      chainId: 80001,
      gasPrice: 30000000000, // 30 gwei
    },
    
    bscTestnet: {
      url: process.env.BSC_TESTNET_URL || "https://data-seed-prebsc-1-s1.binance.org:8545",
      accounts,
      chainId: 97,
      gasPrice: 10000000000, // 10 gwei
    },
    
    // Mainnets
    ethereum: {
      url: process.env.ETH_MAINNET_URL || "",
      accounts,
      chainId: 1,
      gasPrice: "auto",
    },
    
    polygon: {
      url: process.env.POLYGON_URL || "https://polygon-rpc.com",
      accounts,
      chainId: 137,
      gasPrice: 100000000000, // 100 gwei
    },
    
    bsc: {
      url: process.env.BSC_URL || "https://bsc-dataseed.binance.org/",
      accounts,
      chainId: 56,
      gasPrice: 5000000000, // 5 gwei
    },
  },
  
  etherscan: {
    apiKey: {
      mainnet: process.env.ETHERSCAN_API_KEY || "",
      goerli: process.env.ETHERSCAN_API_KEY || "",
      sepolia: process.env.ETHERSCAN_API_KEY || "",
      polygon: process.env.POLYGONSCAN_API_KEY || "",
      polygonMumbai: process.env.POLYGONSCAN_API_KEY || "",
      bsc: process.env.BSCSCAN_API_KEY || "",
      bscTestnet: process.env.BSCSCAN_API_KEY || "",
    },
  },
  
  gasReporter: {
    enabled: process.env.REPORT_GAS === "true",
    currency: "USD",
    coinmarketcap: process.env.COINMARKETCAP_API_KEY,
    excludeContracts: [],
    src: "./contracts",
  },
  
  paths: {
    sources: "./contracts",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts",
  },
  
  mocha: {
    timeout: 40000,
  },
};
