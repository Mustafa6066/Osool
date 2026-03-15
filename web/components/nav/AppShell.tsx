'use client';

import { useState } from 'react';
import FloatingHeader from './FloatingHeader';
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
      <FloatingHeader onInvite={openInvite} />

      {/* Content area — offset for floating header */}
      <div
        className="flex flex-col h-screen pt-[60px]"
        style={{ overflow: 'hidden' }}
      >
        {children}
      </div>
    </>
  );
}
