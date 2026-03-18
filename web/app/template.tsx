'use client';

import { motion } from 'framer-motion';
import { usePathname } from 'next/navigation';

export default function Template({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  // Determine direction based on common navigation patterns or just use a generic fade/slide
  // For standard fluid transition, a slight fade + upward motion looks clean and professional.
  
  return (
    <motion.div
      key={pathname}
      initial={{ opacity: 0, y: 12, filter: 'blur(4px)' }}
      animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      transition={{ 
        type: 'spring', 
        stiffness: 260, 
        damping: 20, 
        mass: 1,
        duration: 0.4 
      }}
      className="flex-1 w-full h-full flex flex-col"
    >
      {children}
    </motion.div>
  );
}
