"use client";

import { useEffect, useState } from "react";

export default function ClientOnly({ children }: { children: React.ReactNode }) {
    const [hasMounted, setHasMounted] = useState(false);

    useEffect(() => {
        const timer = window.setTimeout(() => setHasMounted(true), 0);
        return () => window.clearTimeout(timer);
    }, []);

    if (!hasMounted) {
        return null;
    }

    return <>{children}</>;
}
