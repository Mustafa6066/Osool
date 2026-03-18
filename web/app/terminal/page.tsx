"use client";

import { Suspense } from "react";
import AppShell from "@/components/nav/AppShell";
import TerminalCore from "@/components/terminal/TerminalCore";
import { Loader2 } from "lucide-react";

export default function TerminalPage() {
  return (
    <AppShell>
      <Suspense
        fallback={
          <div className="flex h-full items-center justify-center bg-black">
            <Loader2 className="h-6 w-6 animate-spin text-lime-400" />
          </div>
        }
      >
        <TerminalCore />
      </Suspense>
    </AppShell>
  );
}
