import React, { useState, useEffect } from 'react';

// Extend Window interface for Ethereum provider
declare global {
    interface Window {
        ethereum?: {
            request: (args: { method: string; params?: unknown[] }) => Promise<unknown>;
            on: (event: string, callback: (...args: unknown[]) => void) => void;
            removeListener: (event: string, callback: (...args: unknown[]) => void) => void;
        };
    }
}

const WalletStatus = () => {
    const [address, setAddress] = useState<string | null>(null);
    const [chainId, setChainId] = useState<string | null>(null);
    const [isConnecting, setIsConnecting] = useState(false);

    useEffect(() => {
        checkConnection();
        if (window.ethereum) {
            window.ethereum.on('accountsChanged', checkConnection);
            window.ethereum.on('chainChanged', checkConnection);
        }
    }, []);

    const checkConnection = async () => {
        if (typeof window.ethereum !== 'undefined') {
            try {
                const accounts = await window.ethereum.request({ method: 'eth_accounts' }) as string[];
                const chain = await window.ethereum.request({ method: 'eth_chainId' }) as string;

                if (accounts.length > 0) {
                    setAddress(accounts[0]);
                    setChainId(chain);
                } else {
                    setAddress(null);
                }
            } catch (err) {
                console.error("Wallet check failed", err);
            }
        }
    };

    const connectWallet = async () => {
        if (typeof window.ethereum === 'undefined') {
            alert("Please install MetaMask!");
            return;
        }

        setIsConnecting(true);
        try {
            await window.ethereum.request({ method: 'eth_requestAccounts' });
            await checkConnection();
        } catch (err) {
            console.error(err);
        } finally {
            setIsConnecting(false);
        }
    };

    if (!address) {
        return (
            <button
                onClick={connectWallet}
                disabled={isConnecting}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
                {isConnecting ? "Connecting..." : "Connect Wallet"}
            </button>
        );
    }

    // Polygon Amoy Chain ID: 0x13882 (80002)
    const isAmoy = chainId === '0x13882';

    return (
        <div className="flex items-center gap-2 p-2 bg-gray-100 rounded-lg">
            <div className={`w-3 h-3 rounded-full ${isAmoy ? 'bg-green-500' : 'bg-red-500'}`} title={isAmoy ? "Connected to Amoy" : "Wrong Network"}></div>
            <span className="text-sm font-mono text-gray-800">
                {address.slice(0, 6)}...{address.slice(-4)}
            </span>
        </div>
    );
};

export default WalletStatus;
