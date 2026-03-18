'use client';

import { useState } from 'react';
import LiquidDock from '@/components/dock/LiquidDock';
import InvitationModal from '@/components/InvitationModal';

interface AppShellProps {
  children: React.ReactNode;
}

export default function AppShell({ children }: AppShellProps) {
  const [showInviteModal, setShowInviteModal] = useState(false);
  const openInvite = () => setShowInviteModal(true);

  return (
    <>
      <InvitationModal isOpen={showInviteModal} onClose={() => setShowInviteModal(false)} />

      {/* Content area — offset for bottom dock only */}
      <div
        className="flex flex-col h-screen pb-[80px] overflow-x-hidden overflow-y-auto"
      >
        {children}
      </div>

      <LiquidDock onInvite={openInvite} />
    </>
  );
}
