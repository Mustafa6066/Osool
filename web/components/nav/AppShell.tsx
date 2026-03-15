'use client';

import { useState } from 'react';
import SideRail from './SideRail';
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
      <SideRail onInvite={openInvite} />
      <BottomBar onInvite={openInvite} />

      {/* Content area — offset for side rail (desktop) and bottom bar (mobile) */}
      <div
        className="flex flex-col h-screen ps-0 md:ps-[60px] pb-20 md:pb-0"
        style={{ overflow: 'hidden' }}
      >
        {children}
      </div>
    </>
  );
}
