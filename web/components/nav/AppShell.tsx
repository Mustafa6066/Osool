'use client';

import { useState } from 'react';
import FloatingHeader from './FloatingHeader';
import BottomBar from './BottomBar';
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

      {/* Content area — offset for floating header + bottom bar */}
      <div
        className="flex flex-col h-screen pt-[60px] pb-[72px] md:pb-0 overflow-x-hidden overflow-y-auto"
      >
        {children}
      </div>

      <BottomBar onInvite={openInvite} />
    </>
  );
}
