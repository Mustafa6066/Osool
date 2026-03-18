'use client';

import { useState } from 'react';
import SmartNav from '@/components/nav/SmartNav';
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

      {/* Content area — desktop nav offset comes from SmartNav CSS variable */}
      <div
        className="flex flex-col min-h-dvh pt-0 pb-0 overflow-x-hidden overflow-y-auto transition-[padding] duration-300 sm:[padding-inline-start:var(--desktop-nav-offset,0px)]"
      >
        {children}
      </div>

      <SmartNav onInvite={openInvite} />
    </>
  );
}
