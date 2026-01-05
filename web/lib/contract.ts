/**
 * Smart Contract Configuration
 * 
 * Connects the frontend to the OsoolRegistry contract on Polygon.
 */

import { getContract } from "thirdweb";
import { defineChain } from "thirdweb/chains";
import { client } from "./client";

// Polygon Amoy Testnet (ID: 80002) or Polygon Mainnet (ID: 137)
export const chain = defineChain(80002);

// Replace with your deployed contract address
const CONTRACT_ADDRESS = process.env.NEXT_PUBLIC_REGISTRY_ADDRESS || "0x0000000000000000000000000000000000000000";

// OsoolRegistry Contract Interface
export const osoolContract = getContract({
    client: client,
    chain: chain,
    address: CONTRACT_ADDRESS,
});

// Backend API URL
export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
