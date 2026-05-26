import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Home, TrendingUp, MapPin, Wallet, ArrowRight, CheckCircle2 } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

type Step = 'goal' | 'region' | 'budget' | 'complete';

interface OnboardingData {
    goal: string;
    regions: string[];
    budget: string;
}

interface OnboardingFlowProps {
    onComplete: (data: OnboardingData) => void;
    onSkip: () => void;
}

export default function OnboardingFlow({ onComplete, onSkip }: OnboardingFlowProps) {
    const { language } = useLanguage();
    const isAr = language === 'ar';
    const [step, setStep] = useState<Step>('goal');
    const [data, setData] = useState<OnboardingData>({ goal: '', regions: [], budget: '' });

    const goals = [
        { id: 'investment', icon: TrendingUp, labelEn: 'Investment & ROI', labelAr: '????????? ???????' },
        { id: 'living', icon: Home, labelEn: 'Finding a Home', labelAr: '????? ??????????' },
        { id: 'both', icon: CheckCircle2, labelEn: 'Mix of Both', labelAr: '??? ????????' }
    ];

    const regions = [
        { id: 'new_cairo', labelEn: 'New Cairo', labelAr: '??????? ???????' },
        { id: 'sheikh_zayed', labelEn: 'Sheikh Zayed', labelAr: '????? ????' },
        { id: 'north_coast', labelEn: 'North Coast', labelAr: '?????? ???????' },
        { id: 'new_capital', labelEn: 'New Capital', labelAr: '??????? ????????' },
        { id: 'other', labelEn: 'Other / Not Sure', labelAr: '??? ????? / ????' }
    ];

    const budgets = [
        { id: 'under_5m', labelEn: 'Under 5M EGP', labelAr: '??? ?? ? ?????' },
        { id: '5m_15m', labelEn: '5M - 15M EGP', labelAr: '? - ?? ?????' },
        { id: '15m_30m', labelEn: '15M - 30M EGP', labelAr: '?? - ?? ?????' },
        { id: 'above_30m', labelEn: 'Above 30M EGP', labelAr: '???? ?? ?? ?????' }
    ];

    const handleGoalSelect = (goalId: string) => {
        setData(prev => ({ ...prev, goal: goalId }));
        setTimeout(() => setStep('region'), 400);
    };

    const toggleRegion = (regionId: string) => {
        setData(prev => {
            const isSelected = prev.regions.includes(regionId);
            if (regionId === 'other') return { ...prev, regions: ['other'] };
            const newRegions = isSelected 
                ? prev.regions.filter(r => r !== regionId)
                : [...prev.regions.filter(r => r !== 'other'), regionId];
            return { ...prev, regions: newRegions };
        });
    };

    const handleRegionNext = () => {
        if (data.regions.length > 0) {
            setStep('budget');
        }
    };

    const handleBudgetSelect = (budgetId: string) => {
        const finalData = { ...data, budget: budgetId };
        setData(finalData);
        setStep('complete');
        setTimeout(() => {
            onComplete(finalData);
        }, 800);
    };

    return (
        <div className="w-full max-w-2xl mx-auto my-8 p-6 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-3xl shadow-xl overflow-hidden relative">
            {/* Progress Bar */}
            <div className="absolute top-0 start-0 w-full h-1.5 bg-[var(--color-surface)]">
                <motion.div 
                    className="h-full bg-emerald-500"
                    initial={{ scaleX: 0.33 }}
                    animate={{ scaleX: step === 'goal' ? 0.33 : step === 'region' ? 0.66 : step === 'budget' ? 0.9 : 1 }}
                    transition={{ duration: 0.5 }}
                    style={{ transformOrigin: 'left' }}
                />
            </div>

            <div className="flex justify-between items-center mb-8">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-500">
                        {step === 'goal' && <TrendingUp className="w-5 h-5" />}
                        {step === 'region' && <MapPin className="w-5 h-5" />}
                        {step === 'budget' && <Wallet className="w-5 h-5" />}
                        {step === 'complete' && <CheckCircle2 className="w-5 h-5" />}
                    </div>
                    <div>
                        <h3 className="font-bold text-lg text-[var(--color-text-primary)]">
                            {isAr ? '???? ?????? ??????' : 'Let\'s personalize your experience'}
                        </h3>
                        <p className="text-sm text-[var(--color-text-secondary)]">
                            {step === 'goal' && (isAr ? '?? ?? ???? ????????' : 'What is your primary goal?')}
                            {step === 'region' && (isAr ? '??? ???? ???????' : 'Where would you like to buy?')}
                            {step === 'budget' && (isAr ? '?? ?? ???????? ?????????' : 'What is your expected budget?')}
                            {step === 'complete' && (isAr ? '???? ???????...' : 'Setting things up...')}
                        </p>
                    </div>
                </div>
                <button onClick={onSkip} className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors">
                    {isAr ? '????' : 'Skip'}
                </button>
            </div>

            <div className="min-h-[240px] relative">
                <AnimatePresence mode="wait">
                    {step === 'goal' && (
                        <motion.div
                            key="goal"
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            className="grid grid-cols-1 md:grid-cols-3 gap-4"
                        >
                            {goals.map((g) => {
                                const Icon = g.icon;
                                const isSelected = data.goal === g.id;
                                return (
                                    <button
                                        key={g.id}
                                        onClick={() => handleGoalSelect(g.id)}
                                        className={"p-6 rounded-2xl border-2 transition-all duration-300 flex flex-col items-center gap-4 text-center " + (isSelected ? 'border-emerald-500 bg-emerald-500/5' : 'border-[var(--color-border)] hover:border-emerald-500/50 hover:bg-[var(--color-surface)]')}
                                    >
                                        <div className={"p-3 rounded-xl transition-colors " + (isSelected ? 'bg-emerald-500 text-white' : 'bg-[var(--color-surface)] text-[var(--color-text-secondary)]')}>
                                            <Icon className="w-6 h-6" />
                                        </div>
                                        <span className="font-semibold text-[var(--color-text-primary)]">
                                            {isAr ? g.labelAr : g.labelEn}
                                        </span>
                                    </button>
                                );
                            })}
                        </motion.div>
                    )}

                    {step === 'region' && (
                        <motion.div
                            key="region"
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            className="flex flex-col h-full"
                        >
                            <div className="flex flex-wrap gap-3 flex-1 mb-6 mt-2">
                                {regions.map((r) => {
                                    const isSelected = data.regions.includes(r.id);
                                    return (
                                        <button
                                            key={r.id}
                                            onClick={() => toggleRegion(r.id)}
                                            className={"px-5 py-3 rounded-full border-2 text-sm font-medium transition-all " + (isSelected ? 'border-emerald-500 bg-emerald-500 text-white shadow-md' : 'border-[var(--color-border)] bg-transparent text-[var(--color-text-primary)] hover:border-emerald-500/50')}
                                        >
                                            {isAr ? r.labelAr : r.labelEn}
                                        </button>
                                    );
                                })}
                            </div>
                            <div className="flex justify-end mt-auto">
                                <button
                                    onClick={handleRegionNext}
                                    disabled={data.regions.length === 0}
                                    className="flex items-center gap-2 px-6 py-3 bg-emerald-500 text-white rounded-xl font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-emerald-600 transition-colors"
                                >
                                    {isAr ? '??????' : 'Next'}
                                    <ArrowRight className="w-4 h-4 rtl:-scale-x-100" />
                                </button>
                            </div>
                        </motion.div>
                    )}

                    {step === 'budget' && (
                        <motion.div
                            key="budget"
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: -20 }}
                            className="grid grid-cols-2 gap-4"
                        >
                            {budgets.map((b) => {
                                const isSelected = data.budget === b.id;
                                return (
                                    <button
                                        key={b.id}
                                        onClick={() => handleBudgetSelect(b.id)}
                                        className={"p-5 rounded-2xl border-2 transition-all duration-300 flex items-center justify-center text-center " + (isSelected ? 'border-emerald-500 bg-emerald-500/10 text-emerald-600' : 'border-[var(--color-border)] hover:border-emerald-500/50 hover:bg-[var(--color-surface)] text-[var(--color-text-primary)]')}
                                    >
                                        <span className="font-semibold">
                                            {isAr ? b.labelAr : b.labelEn}
                                        </span>
                                    </button>
                                );
                            })}
                        </motion.div>
                    )}

                    {step === 'complete' && (
                        <motion.div
                            key="complete"
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="flex flex-col items-center justify-center h-[240px] text-center"
                        >
                            <div className="w-16 h-16 bg-emerald-500 rounded-full flex items-center justify-center text-white mb-4 shadow-lg shadow-emerald-500/20">
                                <CheckCircle2 className="w-8 h-8" />
                            </div>
                            <h3 className="text-xl font-bold text-[var(--color-text-primary)] mb-2">
                                {isAr ? '?? ??? ????????!' : 'Preferences Saved!'}
                            </h3>
                            <p className="text-[var(--color-text-secondary)] max-w-md mx-auto">
                                {isAr ? '??? ???? ???? ?????? ???? ????? ???????? ???? ????? ????????.' : 'We are now preparing the best real estate opportunities that match your requirements.'}
                            </p>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
