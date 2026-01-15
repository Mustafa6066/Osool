'use client';

import Link from 'next/link';
import { ArrowRight, UserPlus } from 'lucide-react';

export default function SignupPage() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-950 px-6">
            <div className="w-full max-w-md bg-white dark:bg-slate-900 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-800 p-8 space-y-6">
                <div className="text-center space-y-2">
                    <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto text-green-600 dark:text-green-400">
                        <UserPlus size={32} />
                    </div>
                    <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Create Account</h1>
                    <p className="text-slate-500 dark:text-slate-400 text-sm">Join Osool to access exclusive investment data.</p>
                </div>

                <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Full Name</label>
                        <input type="text" placeholder="Amr El-Sayed" className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:ring-2 focus:ring-green-500/20 focus:border-green-500 outline-none transition-all" />
                    </div>
                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Email Address</label>
                        <input type="email" placeholder="amr@example.com" className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:ring-2 focus:ring-green-500/20 focus:border-green-500 outline-none transition-all" />
                    </div>
                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Password</label>
                        <input type="password" placeholder="••••••••" className="w-full px-4 py-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 focus:ring-2 focus:ring-green-500/20 focus:border-green-500 outline-none transition-all" />
                    </div>

                    <button className="w-full py-4 bg-green-600 hover:bg-green-700 text-white font-bold rounded-xl shadow-lg shadow-green-500/30 transition-all flex items-center justify-center gap-2">
                        Sign Up <ArrowRight size={18} />
                    </button>
                </form>

                <div className="pt-4 text-center border-t border-slate-100 dark:border-slate-800">
                    <p className="text-sm text-slate-500">Already have an account? <Link href="/login" className="text-green-600 font-semibold hover:underline">Login</Link></p>
                </div>
            </div>
        </div>
    );
}
