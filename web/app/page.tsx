"use client";

import Navigation from "@/components/Navigation";
import Hero from "@/components/Hero";
import Features from "@/components/Features";
import PropertyShowcase from "@/components/PropertyShowcase";
import HowItWorks from "@/components/HowItWorks";
import Footer from "@/components/Footer";

export default function Home() {
    return (
        <main className="min-h-screen bg-[var(--color-background)]">
            <Navigation />
            <Hero />
            <Features />
            <PropertyShowcase />
            <HowItWorks />
            <Footer />
        </main>
    );
}
