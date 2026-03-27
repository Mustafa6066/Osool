'use client';

import { useState } from 'react';
import SideNav from '@/components/nav/SideNav';
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

      <SideNav onInvite={openInvite} />

      {/* Main content — offset by sidebar collapsed width on desktop, pad bottom for mobile tab bar */}
      <div className="flex flex-col min-h-dvh lg:pl-14 pb-16 lg:pb-0 overflow-x-hidden overflow-y-auto">
        {children}
      </div>
    </>
  );
}
