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

      {/* Content area — reserve space for floating nav launcher */}
      <div
        className="flex flex-col min-h-dvh pt-0 pb-12 overflow-x-hidden overflow-y-auto"
      >
        {children}
      </div>

      <SmartNav onInvite={openInvite} />
    </>
  );
}
