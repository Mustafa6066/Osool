"use client";

/**
 * Thirdweb Provider Component
 * 
 * Wraps the app with Thirdweb context for wallet connectivity.
 */

import { ThirdwebProvider } from "thirdweb/react";

export default function ThirdwebWrapper({
    children
}: {
    children: React.ReactNode
}) {
    return (
        <ThirdwebProvider>
            {children}
        </ThirdwebProvider>
    );
}
