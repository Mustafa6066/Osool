'use client';

import { useState, useRef, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { User, ChevronDown, LinkIcon, LogOut, Gift } from 'lucide-react';
import Link from 'next/link';

interface ProfileDropdownProps {
    onGenerateInvitation: () => void;
}

export default function ProfileDropdown({ onGenerateInvitation }: ProfileDropdownProps) {
    const { user, logout } = useAuth();
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    if (!user) return null;

    // Get display name with specific admin titles
    const getDisplayName = () => {
        // Specific mapping for core team
        const email = user.email?.toLowerCase();
        if (email === 'mustafa@osool.eg') return 'Mr. Mustafa';
        if (email === 'hani@osool.eg') return 'Mr. Hani';
        if (email === 'abady@osool.eg') return 'Mr. Abady';
        if (email === 'sama@osool.eg') return 'Mrs. Sama';

        // Enhanced fallback logic
        if (user.full_name && user.full_name !== 'Wallet User') return user.full_name;
        if (user.full_name === 'Wallet User' && user.wallet_address) {
            return `${user.wallet_address.substring(0, 6)}...${user.wallet_address.substring(38)}`;
        }
        return user.email?.split('@')[0] || 'User';
    };

    const displayName = getDisplayName();

    // Get user initials for avatar
    const getInitials = () => {
        // Use clean name without title for initials
        let name = displayName;
        if (name.startsWith('Mr. ') || name.startsWith('Mrs. ')) {
            name = name.split(' ')[1];
        }

        const parts = name.split(' ');
        if (parts.length >= 2) {
            return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
        }
        return name.substring(0, 2).toUpperCase();
    };

    return (
        <div className="relative" ref={dropdownRef}>
            {/* Profile Button */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-2 px-3 py-2 rounded-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:border-green-500 transition-all"
            >
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center text-white text-sm font-bold">
                    {getInitials()}
                </div>
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300 hidden sm:block max-w-[120px] truncate">
                    {displayName}
                </span>
                <ChevronDown size={16} className={`text-slate-500 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
            </button>

            {/* Dropdown Menu */}
            {isOpen && (
                <div className="absolute right-0 top-full mt-2 w-64 bg-white dark:bg-slate-900 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-700 py-2 z-50 animate-in fade-in slide-in-from-top-2 duration-200">
                    {/* User Info */}
                    <div className="px-4 py-3 border-b border-slate-100 dark:border-slate-800">
                        <p className="text-sm font-semibold text-slate-900 dark:text-white truncate">{displayName}</p>
                        <p className="text-xs text-slate-500 truncate">{user.email}</p>
                    </div>

                    {/* Menu Items */}
                    <div className="py-2">
                        <button
                            onClick={() => {
                                setIsOpen(false);
                                onGenerateInvitation();
                            }}
                            className="w-full flex items-center gap-3 px-4 py-2.5 text-left text-sm text-slate-700 dark:text-slate-300 hover:bg-green-50 dark:hover:bg-green-900/20 hover:text-green-600 dark:hover:text-green-400 transition-colors"
                        >
                            <Gift size={18} />
                            <span className="font-medium">Invite a Friend</span>
                        </button>

                        <Link
                            href="/chat"
                            onClick={() => setIsOpen(false)}
                            className="w-full flex items-center gap-3 px-4 py-2.5 text-left text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                        >
                            <User size={18} />
                            <span>Chat with AMR</span>
                        </Link>
                    </div>

                    {/* Logout */}
                    <div className="border-t border-slate-100 dark:border-slate-800 pt-2">
                        <button
                            onClick={() => {
                                setIsOpen(false);
                                logout();
                            }}
                            className="w-full flex items-center gap-3 px-4 py-2.5 text-left text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                        >
                            <LogOut size={18} />
                            <span>Sign Out</span>
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
