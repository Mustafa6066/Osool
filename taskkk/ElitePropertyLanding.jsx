import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence, useScroll, useTransform } from 'framer-motion';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Sphere, MeshDistortMaterial } from '@react-three/drei';
import { useWeb3, useEliteProperty } from '../services/Web3Service';
import { FaEthereum, FaRocket, FaShieldAlt, FaChartLine, FaUsers, FaGift } from 'react-icons/fa';
import { BsLightningChargeFill } from 'react-icons/bs';
import { HiSparkles } from 'react-icons/hi';
import confetti from 'canvas-confetti';

// 3D Animated Orb Component
const AnimatedOrb = () => {
  return (
    <Canvas camera={{ position: [0, 0, 5] }}>
      <ambientLight intensity={0.5} />
      <directionalLight position={[10, 10, 5]} intensity={1} />
      <Sphere args={[1, 100, 200]} scale={2.5}>
        <MeshDistortMaterial
          color="#D4AF37"
          attach="material"
          distort={0.5}
          speed={2}
          roughness={0}
          metalness={0.8}
        />
      </Sphere>
      <OrbitControls enableZoom={false} autoRotate />
    </Canvas>
  );
};

// Particle Background
const ParticleBackground = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const particles = [];
    const particleCount = 100;

    class Particle {
      constructor() {
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.size = Math.random() * 2;
        this.speedX = Math.random() * 0.5 - 0.25;
        this.speedY = Math.random() * 0.5 - 0.25;
        this.opacity = Math.random() * 0.5 + 0.2;
      }

      update() {
        this.x += this.speedX;
        this.y += this.speedY;

        if (this.x > canvas.width) this.x = 0;
        if (this.x < 0) this.x = canvas.width;
        if (this.y > canvas.height) this.y = 0;
        if (this.y < 0) this.y = canvas.height;
      }

      draw() {
        ctx.fillStyle = `rgba(212, 175, 55, ${this.opacity})`;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    for (let i = 0; i < particleCount; i++) {
      particles.push(new Particle());
    }

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      particles.forEach(particle => {
        particle.update();
        particle.draw();
      });
      requestAnimationFrame(animate);
    };

    animate();

    const handleResize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return <canvas ref={canvasRef} className="fixed inset-0 pointer-events-none opacity-30" />;
};

// Main Landing Page Component
const ElitePropertyLanding = () => {
  const { connectWallet, account, loading } = useWeb3();
  const { purchaseSubscription, getTokenBalance } = useEliteProperty();
  const [selectedTier, setSelectedTier] = useState(1);
  const [referralCode, setReferralCode] = useState('');
  const [emailSubmitted, setEmailSubmitted] = useState(false);
  const [countdown, setCountdown] = useState({ days: 3, hours: 12, minutes: 45, seconds: 30 });
  const [subscriberCount, setSubscriberCount] = useState(42);
  const { scrollY } = useScroll();
  const y = useTransform(scrollY, [0, 300], [0, -50]);

  // Countdown Timer
  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown(prev => {
        if (prev.seconds > 0) return { ...prev, seconds: prev.seconds - 1 };
        if (prev.minutes > 0) return { ...prev, minutes: prev.minutes - 1, seconds: 59 };
        if (prev.hours > 0) return { ...prev, hours: prev.hours - 1, minutes: 59, seconds: 59 };
        if (prev.days > 0) return { ...prev, days: prev.days - 1, hours: 23, minutes: 59, seconds: 59 };
        return prev;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Simulate live subscriber count
  useEffect(() => {
    const interval = setInterval(() => {
      if (Math.random() > 0.7) {
        setSubscriberCount(prev => prev + 1);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const handleEarlyAccess = async (e) => {
    e.preventDefault();
    setEmailSubmitted(true);
    
    // Trigger celebration
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 },
      colors: ['#D4AF37', '#0F3A5F', '#FDFBF7']
    });
  };

  const handleSubscribe = async () => {
    if (!account) {
      await connectWallet();
      return;
    }

    try {
      await purchaseSubscription(selectedTier, referralCode || undefined);
      confetti({
        particleCount: 200,
        spread: 100,
        origin: { y: 0.5 }
      });
    } catch (error) {
      console.error('Subscription failed:', error);
    }
  };

  const tiers = [
    {
      name: 'Explorer',
      price: '100 EPT',
      usdPrice: '$49',
      color: 'from-amber-600 to-amber-700',
      features: [
        'AI Lifestyle Property Matcher',
        'Virtual AI Concierge 24/7',
        'Market Insights Dashboard',
        'Basic 3D Property Tours',
        '1,000 Loyalty Tokens'
      ],
      popular: false
    },
    {
      name: 'Premium',
      price: '300 EPT',
      usdPrice: '$149',
      color: 'from-blue-600 to-blue-700',
      features: [
        'Everything in Explorer',
        'AI Property Valuation',
        'Investment Portfolio Optimizer',
        'Priority Customer Support',
        '5,000 Loyalty Tokens'
      ],
      popular: true
    },
    {
      name: 'Platinum',
      price: '1000 EPT',
      usdPrice: '$499',
      color: 'from-purple-600 to-purple-700',
      features: [
        'Everything in Premium',
        'AI Virtual Staging',
        'Personal AI Real Estate Agent',
        'Off-Market Property Access',
        '20,000 Loyalty Tokens'
      ],
      popular: false
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-900 via-blue-900 to-slate-900 text-white overflow-hidden">
      <ParticleBackground />
      
      {/* Navigation */}
      <nav className="relative z-50 px-6 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center space-x-2"
          >
            <HiSparkles className="text-3xl text-yellow-400" />
            <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-yellow-400 to-yellow-600">
              Elite Property
            </span>
          </motion.div>
          
          <motion.button
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            onClick={connectWallet}
            disabled={loading}
            className="px-6 py-3 bg-gradient-to-r from-yellow-400 to-yellow-600 rounded-full font-semibold text-slate-900 hover:shadow-2xl hover:shadow-yellow-500/25 transition-all duration-300 flex items-center gap-2"
          >
            <FaEthereum />
            {account ? `${account.slice(0, 6)}...${account.slice(-4)}` : 'Connect Wallet'}
          </motion.button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center px-6">
        <motion.div 
          style={{ y }}
          className="absolute inset-0 flex items-center justify-center opacity-20"
        >
          <div className="w-96 h-96">
            <AnimatedOrb />
          </div>
        </motion.div>

        <div className="relative z-10 max-w-7xl mx-auto text-center">
          {/* Live Counter */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-green-500/20 to-green-600/20 rounded-full mb-8 border border-green-500/30"
          >
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <span className="text-green-400 text-sm font-medium">
              {subscriberCount} Elite Members Already Joined
            </span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-6xl md:text-8xl font-bold mb-6"
          >
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-yellow-400 via-yellow-500 to-orange-500">
              AI-Powered
            </span>
            <br />
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500">
              Luxury Real Estate
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="text-xl md:text-2xl text-gray-300 mb-8 max-w-3xl mx-auto"
          >
            Experience the future of property investment with blockchain security, 
            AI intelligence, and exclusive access to premium Egyptian real estate.
          </motion.p>

          {/* Limited Time Offer */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4 }}
            className="bg-gradient-to-r from-red-500/20 to-orange-500/20 rounded-2xl p-6 mb-8 max-w-2xl mx-auto border border-red-500/30"
          >
            <h3 className="text-2xl font-bold mb-4 text-orange-400">
              🔥 Founding Members Special - 50% OFF Forever!
            </h3>
            <div className="flex justify-center gap-8">
              {Object.entries(countdown).map(([unit, value]) => (
                <div key={unit} className="text-center">
                  <div className="text-3xl font-bold text-white">{value}</div>
                  <div className="text-sm text-gray-400 capitalize">{unit}</div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Early Access Form */}
          {!emailSubmitted ? (
            <motion.form
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              onSubmit={handleEarlyAccess}
              className="flex flex-col sm:flex-row gap-4 max-w-md mx-auto mb-12"
            >
              <input
                type="email"
                placeholder="Enter your email for early access"
                required
                className="flex-1 px-6 py-4 rounded-full bg-white/10 backdrop-blur-md border border-white/20 focus:border-yellow-400 focus:outline-none focus:ring-2 focus:ring-yellow-400/20"
              />
              <button
                type="submit"
                className="px-8 py-4 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full font-semibold text-slate-900 hover:shadow-2xl hover:shadow-yellow-500/25 transition-all duration-300 flex items-center gap-2 whitespace-nowrap"
              >
                <FaRocket /> Get Early Access
              </button>
            </motion.form>
          ) : (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className="text-center mb-12"
            >
              <div className="text-3xl mb-4">🎉</div>
              <h3 className="text-2xl font-bold text-green-400 mb-2">You're on the list!</h3>
              <p className="text-gray-300">Check your email for exclusive founder benefits</p>
            </motion.div>
          )}

          {/* Trust Indicators */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="flex flex-wrap justify-center gap-8 text-sm text-gray-400"
          >
            <span className="flex items-center gap-2">
              <FaShieldAlt className="text-green-400" /> Smart Contract Secured
            </span>
            <span className="flex items-center gap-2">
              <BsLightningChargeFill className="text-yellow-400" /> Instant Transactions
            </span>
            <span className="flex items-center gap-2">
              <FaChartLine className="text-blue-400" /> 98% ROI Accuracy
            </span>
          </motion.div>
        </div>
      </section>

      {/* Subscription Tiers */}
      <section className="relative py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            className="text-4xl md:text-5xl font-bold text-center mb-4"
          >
            Choose Your Elite Status
          </motion.h2>
          
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-xl text-gray-300 text-center mb-12"
          >
            Join the first 100 members and lock in founder pricing forever
          </motion.p>

          <div className="grid md:grid-cols-3 gap-8">
            {tiers.map((tier, index) => (
              <motion.div
                key={tier.name}
                initial={{ opacity: 0, y: 50 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`relative rounded-3xl p-8 backdrop-blur-md border ${
                  tier.popular 
                    ? 'bg-gradient-to-b from-white/20 to-white/5 border-yellow-400/50 scale-105' 
                    : 'bg-white/5 border-white/10'
                }`}
              >
                {tier.popular && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <span className="bg-gradient-to-r from-yellow-400 to-orange-500 text-slate-900 px-4 py-1 rounded-full text-sm font-bold">
                      MOST POPULAR
                    </span>
                  </div>
                )}
                
                <h3 className="text-2xl font-bold mb-2">{tier.name}</h3>
                <div className="mb-6">
                  <span className="text-4xl font-bold">{tier.usdPrice}</span>
                  <span className="text-gray-400">/month</span>
                  <div className="text-sm text-gray-400 mt-1">or {tier.price}</div>
                </div>
                
                <ul className="space-y-3 mb-8">
                  {tier.features.map((feature, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-green-400 mt-1">✓</span>
                      <span className="text-gray-300">{feature}</span>
                    </li>
                  ))}
                </ul>
                
                <button
                  onClick={() => {
                    setSelectedTier(index);
                    handleSubscribe();
                  }}
                  className={`w-full py-4 rounded-full font-semibold transition-all duration-300 ${
                    tier.popular
                      ? 'bg-gradient-to-r from-yellow-400 to-orange-500 text-slate-900 hover:shadow-2xl hover:shadow-yellow-500/25'
                      : 'bg-white/10 hover:bg-white/20 border border-white/20'
                  }`}
                >
                  {account ? 'Subscribe Now' : 'Connect Wallet'}
                </button>
              </motion.div>
            ))}
          </div>

          {/* Referral Program */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            className="mt-16 text-center"
          >
            <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-3xl p-8 max-w-2xl mx-auto border border-purple-500/30">
              <FaGift className="text-5xl text-purple-400 mx-auto mb-4" />
              <h3 className="text-2xl font-bold mb-4">Earn While You Invest</h3>
              <p className="text-gray-300 mb-6">
                Refer friends and earn 20% commission + 1,000 EPT tokens for each subscription!
              </p>
              <div className="flex gap-4 max-w-md mx-auto">
                <input
                  type="text"
                  placeholder="Enter referral code (optional)"
                  value={referralCode}
                  onChange={(e) => setReferralCode(e.target.value)}
                  className="flex-1 px-4 py-3 rounded-full bg-white/10 backdrop-blur-md border border-white/20 focus:border-purple-400 focus:outline-none"
                />
                <button className="px-6 py-3 bg-gradient-to-r from-purple-400 to-pink-500 rounded-full font-semibold text-white">
                  Apply Code
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Blockchain Features */}
      <section className="relative py-20 px-6 bg-black/30">
        <div className="max-w-7xl mx-auto">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            className="text-4xl md:text-5xl font-bold text-center mb-12"
          >
            Powered by Blockchain Technology
          </motion.h2>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: <FaEthereum className="text-4xl" />,
                title: 'Smart Contract Escrow',
                description: 'Secure property transactions with automated fund release and instant ownership transfer',
                color: 'from-blue-400 to-blue-600'
              },
              {
                icon: <HiSparkles className="text-4xl" />,
                title: 'Property NFTs',
                description: 'Tokenized ownership enabling fractional investments and easy transfers',
                color: 'from-purple-400 to-purple-600'
              },
              {
                icon: <FaShieldAlt className="text-4xl" />,
                title: 'Immutable History',
                description: 'Complete transaction history stored on-chain for transparency',
                color: 'from-green-400 to-green-600'
              },
              {
                icon: <FaChartLine className="text-4xl" />,
                title: 'Staking Rewards',
                description: 'Earn passive income by staking EPT tokens for platform benefits',
                color: 'from-yellow-400 to-yellow-600'
              },
              {
                icon: <FaUsers className="text-4xl" />,
                title: 'DAO Governance',
                description: 'Platinum members vote on platform features and property listings',
                color: 'from-pink-400 to-pink-600'
              },
              {
                icon: <BsLightningChargeFill className="text-4xl" />,
                title: 'Multi-Chain Support',
                description: 'Deploy on Ethereum, Polygon, and BSC for flexibility',
                color: 'from-orange-400 to-orange-600'
              }
            ].map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="relative group"
              >
                <div className="absolute inset-0 bg-gradient-to-r opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-2xl blur-xl"
                     style={{ background: `linear-gradient(to right, ${feature.color})` }} />
                <div className="relative bg-white/5 backdrop-blur-md rounded-2xl p-6 border border-white/10 hover:border-white/20 transition-all duration-300">
                  <div className={`bg-gradient-to-r ${feature.color} bg-clip-text text-transparent mb-4`}>
                    {feature.icon}
                  </div>
                  <h3 className="text-xl font-bold mb-2">{feature.title}</h3>
                  <p className="text-gray-400">{feature.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Social Proof */}
      <section className="relative py-20 px-6">
        <div className="max-w-7xl mx-auto text-center">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            className="text-3xl md:text-4xl font-bold mb-12"
          >
            Join Elite Investors & Industry Leaders
          </motion.h2>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {[
              { value: '$2.5M+', label: 'Total Value Locked' },
              { value: '98%', label: 'AI Prediction Accuracy' },
              { value: '500+', label: 'Properties Listed' },
              { value: '4.9/5', label: 'User Rating' }
            ].map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, scale: 0.8 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
              >
                <div className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-yellow-400 to-orange-500 bg-clip-text text-transparent">
                  {stat.value}
                </div>
                <div className="text-gray-400 mt-2">{stat.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Footer */}
      <section className="relative py-20 px-6 bg-gradient-to-t from-black/50 to-transparent">
        <div className="max-w-4xl mx-auto text-center">
          <motion.h2
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            className="text-3xl md:text-5xl font-bold mb-6"
          >
            Be Among The First 100 Elite Members
          </motion.h2>
          
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-xl text-gray-300 mb-8"
          >
            Lock in founder pricing forever and shape the future of real estate
          </motion.p>

          <motion.button
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            onClick={handleSubscribe}
            className="px-12 py-6 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full font-bold text-xl text-slate-900 hover:shadow-2xl hover:shadow-yellow-500/25 transition-all duration-300 transform hover:scale-105"
          >
            Claim Your Founder Status Now
          </motion.button>

          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="mt-8 text-gray-400"
          >
            <p className="text-sm">
              🔒 Secured by Smart Contracts | 💎 Exclusive NFT Badge | 🚀 Priority Access Forever
            </p>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default ElitePropertyLanding;
