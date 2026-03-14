// Web3 Context Provider
import React, { createContext, useContext, useEffect, useState } from 'react';
import { ethers } from 'ethers';
import Web3Modal from 'web3modal';
import WalletConnectProvider from '@walletconnect/web3-provider';
import { toast } from 'react-hot-toast';

// Contract ABIs and addresses
import ElitePropertyPlatformABI from '../abis/ElitePropertyPlatform.json';
import ElitePropertyTokenABI from '../abis/ElitePropertyToken.json';
import EliteMembershipNFTABI from '../abis/EliteMembershipNFT.json';

// Contract addresses (update with deployed addresses)
const CONTRACT_ADDRESSES = {
  PLATFORM: process.env.NEXT_PUBLIC_PLATFORM_ADDRESS,
  TOKEN: process.env.NEXT_PUBLIC_TOKEN_ADDRESS,
  NFT: process.env.NEXT_PUBLIC_NFT_ADDRESS,
};

// Supported networks
const NETWORKS = {
  1: { name: 'Ethereum Mainnet', currency: 'ETH', explorer: 'https://etherscan.io' },
  137: { name: 'Polygon', currency: 'MATIC', explorer: 'https://polygonscan.com' },
  56: { name: 'BSC', currency: 'BNB', explorer: 'https://bscscan.com' },
};

// Web3 Context
const Web3Context = createContext({});

export const useWeb3 = () => useContext(Web3Context);

// Web3Modal configuration
const providerOptions = {
  walletconnect: {
    package: WalletConnectProvider,
    options: {
      rpc: {
        1: process.env.NEXT_PUBLIC_RPC_URL_MAINNET,
        137: process.env.NEXT_PUBLIC_RPC_URL_POLYGON,
        56: process.env.NEXT_PUBLIC_RPC_URL_BSC,
      },
    },
  },
};

export const Web3Provider = ({ children }) => {
  const [web3Modal, setWeb3Modal] = useState(null);
  const [provider, setProvider] = useState(null);
  const [signer, setSigner] = useState(null);
  const [account, setAccount] = useState(null);
  const [chainId, setChainId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [contracts, setContracts] = useState({});

  useEffect(() => {
    const modal = new Web3Modal({
      network: 'polygon',
      cacheProvider: true,
      providerOptions,
      theme: {
        background: "rgb(15, 58, 95)",
        main: "rgb(253, 251, 247)",
        secondary: "rgb(212, 175, 55)",
        border: "rgba(195, 195, 195, 0.14)",
        hover: "rgb(16, 26, 32)"
      }
    });
    setWeb3Modal(modal);
  }, []);

  const connectWallet = async () => {
    try {
      setLoading(true);
      const instance = await web3Modal.connect();
      const provider = new ethers.providers.Web3Provider(instance);
      const signer = provider.getSigner();
      const address = await signer.getAddress();
      const network = await provider.getNetwork();

      setProvider(provider);
      setSigner(signer);
      setAccount(address);
      setChainId(network.chainId);

      // Initialize contracts
      const platformContract = new ethers.Contract(
        CONTRACT_ADDRESSES.PLATFORM,
        ElitePropertyPlatformABI,
        signer
      );
      const tokenContract = new ethers.Contract(
        CONTRACT_ADDRESSES.TOKEN,
        ElitePropertyTokenABI,
        signer
      );
      const nftContract = new ethers.Contract(
        CONTRACT_ADDRESSES.NFT,
        EliteMembershipNFTABI,
        signer
      );

      setContracts({ platform: platformContract, token: tokenContract, nft: nftContract });

      // Subscribe to accounts change
      instance.on("accountsChanged", (accounts) => {
        if (accounts.length > 0) {
          setAccount(accounts[0]);
        } else {
          disconnectWallet();
        }
      });

      // Subscribe to chainId change
      instance.on("chainChanged", (chainId) => {
        window.location.reload();
      });

      toast.success('Wallet connected successfully!');
    } catch (error) {
      console.error('Failed to connect wallet:', error);
      toast.error('Failed to connect wallet');
    } finally {
      setLoading(false);
    }
  };

  const disconnectWallet = async () => {
    if (web3Modal) {
      web3Modal.clearCachedProvider();
    }
    setProvider(null);
    setSigner(null);
    setAccount(null);
    setChainId(null);
    setContracts({});
  };

  const switchNetwork = async (targetChainId) => {
    try {
      await window.ethereum.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: ethers.utils.hexValue(targetChainId) }],
      });
    } catch (error) {
      if (error.code === 4902) {
        // Chain not added, add it
        const network = NETWORKS[targetChainId];
        await window.ethereum.request({
          method: 'wallet_addEthereumChain',
          params: [{
            chainId: ethers.utils.hexValue(targetChainId),
            chainName: network.name,
            nativeCurrency: {
              name: network.currency,
              symbol: network.currency,
              decimals: 18,
            },
            blockExplorerUrls: [network.explorer],
          }],
        });
      }
    }
  };

  const value = {
    account,
    chainId,
    provider,
    signer,
    contracts,
    loading,
    connectWallet,
    disconnectWallet,
    switchNetwork,
  };

  return <Web3Context.Provider value={value}>{children}</Web3Context.Provider>;
};

// Custom Hooks for Contract Interactions
export const useEliteProperty = () => {
  const { contracts, account, signer } = useWeb3();
  
  // Create Property Escrow
  const createEscrow = async (propertyId, buyer, price, ipfsHash) => {
    try {
      const tx = await contracts.platform.createEscrow(
        propertyId,
        buyer,
        ethers.utils.parseEther(price.toString()),
        ipfsHash
      );
      const receipt = await tx.wait();
      
      // Find the escrow ID from events
      const event = receipt.events?.find(e => e.event === 'EscrowCreated');
      return event?.args?.escrowId?.toNumber();
    } catch (error) {
      console.error('Failed to create escrow:', error);
      throw error;
    }
  };

  // Fund Escrow with Deposit
  const fundEscrow = async (escrowId, depositAmount) => {
    try {
      const tx = await contracts.platform.fundEscrow(escrowId, {
        value: ethers.utils.parseEther(depositAmount.toString())
      });
      await tx.wait();
      toast.success('Escrow funded successfully!');
    } catch (error) {
      console.error('Failed to fund escrow:', error);
      toast.error('Failed to fund escrow');
      throw error;
    }
  };

  // Complete Escrow Transaction
  const completeEscrow = async (escrowId, remainingAmount) => {
    try {
      const tx = await contracts.platform.completeEscrow(escrowId, {
        value: remainingAmount ? ethers.utils.parseEther(remainingAmount.toString()) : 0
      });
      await tx.wait();
      toast.success('Property transaction completed!');
    } catch (error) {
      console.error('Failed to complete escrow:', error);
      toast.error('Failed to complete transaction');
      throw error;
    }
  };

  // Purchase Subscription
  const purchaseSubscription = async (tier, referrer = ethers.constants.AddressZero) => {
    try {
      // First approve token spending
      const prices = await contracts.platform.subscriptionPrices(tier);
      const approveTx = await contracts.token.approve(
        CONTRACT_ADDRESSES.PLATFORM,
        prices
      );
      await approveTx.wait();

      // Then purchase subscription
      const tx = await contracts.platform.purchaseSubscription(tier, referrer);
      await tx.wait();
      toast.success(`Subscription activated! Welcome to ${['Explorer', 'Premium', 'Platinum'][tier]} tier!`);
    } catch (error) {
      console.error('Failed to purchase subscription:', error);
      toast.error('Failed to purchase subscription');
      throw error;
    }
  };

  // Stake Tokens for Benefits
  const stakeTokens = async (amount) => {
    try {
      const amountWei = ethers.utils.parseEther(amount.toString());
      
      // Approve tokens
      const approveTx = await contracts.token.approve(
        CONTRACT_ADDRESSES.PLATFORM,
        amountWei
      );
      await approveTx.wait();

      // Stake tokens
      const tx = await contracts.platform.stakeTokensForBenefits(amountWei);
      await tx.wait();
      toast.success('Tokens staked successfully!');
    } catch (error) {
      console.error('Failed to stake tokens:', error);
      toast.error('Failed to stake tokens');
      throw error;
    }
  };

  // Get User Subscription Status
  const getSubscriptionStatus = async (userAddress = account) => {
    if (!contracts.platform || !userAddress) return null;
    
    try {
      const [isActive, tier, subscription] = await Promise.all([
        contracts.platform.isSubscriptionActive(userAddress),
        contracts.platform.getUserTier(userAddress),
        contracts.platform.subscriptions(userAddress)
      ]);

      return {
        isActive,
        tier: tier.toNumber(),
        expiryDate: new Date(subscription.expiryDate.toNumber() * 1000),
        tokensStaked: ethers.utils.formatEther(subscription.tokensStaked),
        referralCount: subscription.referralCount.toNumber(),
        autoRenew: subscription.autoRenew
      };
    } catch (error) {
      console.error('Failed to get subscription status:', error);
      return null;
    }
  };

  // Get Token Balance
  const getTokenBalance = async (userAddress = account) => {
    if (!contracts.token || !userAddress) return '0';
    
    try {
      const balance = await contracts.token.balanceOf(userAddress);
      return ethers.utils.formatEther(balance);
    } catch (error) {
      console.error('Failed to get token balance:', error);
      return '0';
    }
  };

  // Get Membership NFT
  const getMembershipNFT = async (userAddress = account) => {
    if (!contracts.nft || !userAddress) return null;
    
    try {
      const tokenId = await contracts.nft.userToTokenId(userAddress);
      if (tokenId.eq(0)) return null;
      
      const membership = await contracts.nft.memberships(tokenId);
      return {
        tokenId: tokenId.toString(),
        tier: membership.tier,
        expiryDate: new Date(membership.expiryDate.toNumber() * 1000),
        loyaltyPoints: membership.loyaltyPoints.toNumber(),
        isActive: membership.isActive
      };
    } catch (error) {
      console.error('Failed to get membership NFT:', error);
      return null;
    }
  };

  return {
    createEscrow,
    fundEscrow,
    completeEscrow,
    purchaseSubscription,
    stakeTokens,
    getSubscriptionStatus,
    getTokenBalance,
    getMembershipNFT
  };
};

// Transaction Monitor Hook
export const useTransactionMonitor = () => {
  const { provider } = useWeb3();
  const [pendingTxs, setPendingTxs] = useState([]);

  const addTransaction = (hash, description) => {
    setPendingTxs(prev => [...prev, { hash, description, status: 'pending' }]);
  };

  const updateTransaction = (hash, status) => {
    setPendingTxs(prev => 
      prev.map(tx => tx.hash === hash ? { ...tx, status } : tx)
    );
  };

  useEffect(() => {
    if (!provider) return;

    pendingTxs.forEach(async (tx) => {
      if (tx.status === 'pending') {
        try {
          const receipt = await provider.waitForTransaction(tx.hash);
          updateTransaction(tx.hash, receipt.status === 1 ? 'success' : 'failed');
        } catch (error) {
          updateTransaction(tx.hash, 'failed');
        }
      }
    });
  }, [provider, pendingTxs]);

  return { pendingTxs, addTransaction };
};

// IPFS Service for Property Data
export const IPFSService = {
  async uploadPropertyData(propertyData) {
    try {
      const response = await fetch('/api/ipfs/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(propertyData)
      });
      const { ipfsHash } = await response.json();
      return ipfsHash;
    } catch (error) {
      console.error('Failed to upload to IPFS:', error);
      throw error;
    }
  },

  async getPropertyData(ipfsHash) {
    try {
      const response = await fetch(`https://ipfs.io/ipfs/${ipfsHash}`);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch from IPFS:', error);
      throw error;
    }
  }
};

// Analytics Service
export const BlockchainAnalytics = {
  async getPropertyTransactionHistory(propertyId) {
    // Implementation to fetch transaction history from blockchain
  },

  async getPlatformStats() {
    // Implementation to fetch platform statistics
  },

  async getUserActivity(address) {
    // Implementation to fetch user activity
  }
};
