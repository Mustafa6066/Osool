'use client';

import { useState, useEffect } from 'react';
import { X, Gift, Copy, Check, Loader2, AlertCircle, Link as LinkIcon } from 'lucide-react';
import { generateInvitation, getMyInvitations, InvitationResponse, MyInvitationsResponse } from '@/lib/api';

interface InvitationModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export default function InvitationModal({ isOpen, onClose }: InvitationModalProps) {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [invitation, setInvitation] = useState<InvitationResponse | null>(null);
    const [myInvitations, setMyInvitations] = useState<MyInvitationsResponse | null>(null);
    const [copied, setCopied] = useState(false);

    // Load existing invitations on open
    useEffect(() => {
        if (isOpen) {
            loadMyInvitations();
        }
    }, [isOpen]);

    const loadMyInvitations = async () => {
        try {
            const data = await getMyInvitations();
            setMyInvitations(data);
        } catch (err) {
            console.error('Failed to load invitations:', err);
        }
    };

    const handleGenerate = async () => {
        setIsLoading(true);
        setError(null);

        try {
            const data = await generateInvitation();
            setInvitation(data);
            // Refresh my invitations
            await loadMyInvitations();
        } catch (err: any) {
            const errorMessage = err.response?.data?.detail || err.message || 'Failed to generate invitation';
            setError(errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    const handleCopy = async () => {
        if (!invitation?.invitation_link) return;

        try {
            await navigator.clipboard.writeText(invitation.invitation_link);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    const handleClose = () => {
        setInvitation(null);
        setError(null);
        onClose();
    };

    if (!isOpen) return null;

    const remainingText = myInvitations?.invitations_remaining === 'unlimited'
        ? 'Unlimited invitations available'
        : `${myInvitations?.invitations_remaining || 0} invitation(s) remaining`;

    const canGenerate = myInvitations?.invitations_remaining === 'unlimited' ||
        (typeof myInvitations?.invitations_remaining === 'number' && myInvitations.invitations_remaining > 0);

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-white dark:bg-slate-900 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl border border-slate-200 dark:border-slate-700 animate-in zoom-in-95 duration-200">

                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-slate-100 dark:border-slate-800">
                    <div className="flex items-center gap-3">
                        <div className="p-2.5 bg-green-100 dark:bg-green-900/30 rounded-xl">
                            <Gift size={22} className="text-green-600 dark:text-green-400" />
                        </div>
                        <div>
                            <h2 className="text-lg font-bold text-slate-900 dark:text-white">Invite a Friend</h2>
                            <p className="text-xs text-slate-500">{remainingText}</p>
                        </div>
                    </div>
                    <button
                        onClick={handleClose}
                        className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-4">

                    {/* Error Message */}
                    {error && (
                        <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl flex items-center gap-2 text-red-600 dark:text-red-400 text-sm">
                            <AlertCircle size={18} />
                            <span>{error}</span>
                        </div>
                    )}

                    {/* Show invitation link if generated */}
                    {invitation ? (
                        <div className="space-y-4">
                            <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl">
                                <p className="text-sm font-medium text-green-700 dark:text-green-400 mb-2">
                                    ✅ Invitation link generated!
                                </p>
                                <div className="flex items-center gap-2 bg-white dark:bg-slate-800 p-3 rounded-lg border border-green-200 dark:border-green-800">
                                    <LinkIcon size={16} className="text-slate-400 flex-shrink-0" />
                                    <input
                                        type="text"
                                        value={invitation.invitation_link}
                                        readOnly
                                        className="flex-1 bg-transparent text-sm text-slate-700 dark:text-slate-300 outline-none truncate"
                                    />
                                    <button
                                        onClick={handleCopy}
                                        className={`p-2 rounded-lg transition-colors ${copied ? 'bg-green-100 text-green-600' : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-600'}`}
                                    >
                                        {copied ? <Check size={16} /> : <Copy size={16} />}
                                    </button>
                                </div>
                            </div>

                            <p className="text-xs text-slate-500 text-center">
                                Share this link with your friend. It can only be used once.
                            </p>

                            {/* Generate Another Button */}
                            {canGenerate && (
                                <button
                                    onClick={handleGenerate}
                                    disabled={isLoading}
                                    className="w-full py-3 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium rounded-xl hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors disabled:opacity-50"
                                >
                                    Generate Another Link
                                </button>
                            )}
                        </div>
                    ) : (
                        <>
                            {/* Info Box */}
                            <div className="p-4 bg-slate-50 dark:bg-slate-800/50 rounded-xl">
                                <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                                    Osool is invite-only during beta. Generate a unique invitation link
                                    to share with friends. Each link can only be used once.
                                </p>
                            </div>

                            {/* Generate Button */}
                            <button
                                onClick={handleGenerate}
                                disabled={isLoading || !canGenerate}
                                className="w-full py-3.5 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-bold rounded-xl shadow-lg shadow-green-500/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            >
                                {isLoading ? (
                                    <>
                                        <Loader2 size={20} className="animate-spin" />
                                        Generating...
                                    </>
                                ) : (
                                    <>
                                        <Gift size={20} />
                                        Generate Invitation Link
                                    </>
                                )}
                            </button>

                            {!canGenerate && (
                                <p className="text-xs text-center text-amber-600 dark:text-amber-400">
                                    You've used all your invitations. Contact an admin for more.
                                </p>
                            )}
                        </>
                    )}

                    {/* Previous Invitations */}
                    {myInvitations && myInvitations.invitations.length > 0 && (
                        <div className="pt-4 border-t border-slate-100 dark:border-slate-800">
                            <p className="text-xs font-semibold text-slate-500 uppercase mb-2">
                                Your Invitations ({myInvitations.total_invitations})
                            </p>
                            <div className="space-y-2 max-h-32 overflow-y-auto">
                                {myInvitations.invitations.map((inv, idx) => (
                                    <div key={idx} className="flex items-center justify-between text-xs p-2 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                                        <span className="font-mono text-slate-600 dark:text-slate-400 truncate max-w-[150px]">
                                            {inv.code.substring(0, 12)}...
                                        </span>
                                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${inv.is_used ? 'bg-slate-200 dark:bg-slate-700 text-slate-500' : 'bg-green-100 dark:bg-green-900/30 text-green-600'}`}>
                                            {inv.is_used ? 'Used' : 'Active'}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
