/**
 * Thirdweb Client Configuration
 * 
 * This sets up the "Invisible Wallet" for Osool.
 * Users log in with Google/Phone - we create a wallet for them automatically.
 */

import { createThirdwebClient } from "thirdweb";

// Get your Client ID from https://thirdweb.com/dashboard (It's free)
// Store this in .env.local as NEXT_PUBLIC_TEMPLATE_CLIENT_ID
export const client = createThirdwebClient({
    clientId: process.env.NEXT_PUBLIC_TEMPLATE_CLIENT_ID || "your_client_id_here",
});
