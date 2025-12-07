"use client";

import { motion } from "framer-motion";
import Image from "next/image";

const sportsImages = [
  { 
    src: "/images/gorilla-basketball.png", 
    alt: "Parlay Gorilla dominating basketball with a powerful slam dunk",
    sport: "Basketball"
  },
  { 
    src: "/images/gorilla-football.png", 
    alt: "Parlay Gorilla making a one-handed touchdown catch in football",
    sport: "Football"
  },
  { 
    src: "/images/gorilla-hockey.png", 
    alt: "Parlay Gorilla on a breakaway scoring in hockey",
    sport: "Hockey"
  },
  { 
    src: "/images/gorilla-soccer.png", 
    alt: "Parlay Gorilla executing a bicycle kick in soccer",
    sport: "Soccer"
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.2,
      delayChildren: 0.1,
    },
  },
};

const imageVariants = {
  hidden: { 
    opacity: 0, 
    y: 60,
    scale: 0.95,
  },
  visible: { 
    opacity: 1, 
    y: 0,
    scale: 1,
    transition: {
      duration: 0.8,
      ease: "easeOut",
    },
  },
};

export default function SportsShowcase() {
  return (
    <section 
      className="w-full py-24 md:py-32 relative z-30 overflow-hidden"
      aria-label="Sports Showcase"
    >
      {/* Background gradient effect */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-emerald-950/20 to-black/40 backdrop-blur-sm" />
      
      {/* Floating accent orbs */}
      <motion.div
        className="absolute top-20 left-10 w-72 h-72 bg-emerald-500/10 rounded-full blur-[100px]"
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.3, 0.5, 0.3],
        }}
        transition={{
          duration: 6,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      <motion.div
        className="absolute bottom-20 right-10 w-96 h-96 bg-cyan-500/10 rounded-full blur-[120px]"
        animate={{
          scale: [1.2, 1, 1.2],
          opacity: [0.4, 0.2, 0.4],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />

      <div className="container mx-auto px-4 relative z-10">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <motion.span 
            className="inline-block px-4 py-2 mb-6 text-sm font-semibold tracking-wider text-emerald-400 uppercase bg-emerald-500/10 border border-emerald-500/30 rounded-full backdrop-blur-sm"
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
          >
            Multi-Sport Coverage
          </motion.span>
          
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-black mb-6">
            <span className="text-white">The Parlay Gorilla </span>
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-green-400 to-cyan-400">
              Dominates
            </span>
            <span className="text-white"> Every Sport</span>
          </h2>
          
          <p className="text-xl text-gray-400 max-w-2xl mx-auto font-medium leading-relaxed">
            Build winning parlays across NFL, NBA, NHL, and more. 
            Mix sports for better diversification and bigger payouts.
          </p>
        </motion.div>

        {/* Image Grid */}
        <motion.div
          className="grid grid-cols-1 md:grid-cols-2 gap-8 lg:gap-10 max-w-6xl mx-auto"
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.15 }}
        >
          {sportsImages.map((img, index) => (
            <motion.div
              key={index}
              variants={imageVariants}
              className="group relative"
            >
              {/* Glow effect behind card */}
              <div className="absolute -inset-1 bg-gradient-to-r from-emerald-500/20 to-cyan-500/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              
              {/* Card Container */}
              <div className="relative rounded-2xl overflow-hidden bg-[#0a0a0a] border border-emerald-500/10 hover:border-emerald-500/40 transition-all duration-500 hover-glow">
                {/* Image */}
                <div className="relative aspect-[4/3] overflow-hidden bg-gradient-to-b from-black/50 to-black">
                  <Image
                    src={img.src}
                    alt={img.alt}
                    width={1600}
                    height={1200}
                    className="w-full h-full object-cover object-top transform group-hover:scale-105 transition-transform duration-700 ease-out"
                    priority={index < 2}
                  />
                  
                  {/* Overlay gradient */}
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent opacity-60 group-hover:opacity-40 transition-opacity duration-500" />
                  
                  {/* Sport label */}
                  <div className="absolute bottom-4 left-4 flex items-center gap-2">
                    <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                    <span className="text-sm font-bold text-white/90 uppercase tracking-wider">
                      {img.sport}
                    </span>
                  </div>
                  
                  {/* Hover indicator */}
                  <motion.div 
                    className="absolute top-4 right-4 px-3 py-1.5 bg-emerald-500/20 backdrop-blur-md rounded-full border border-emerald-500/30 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                    whileHover={{ scale: 1.05 }}
                  >
                    <span className="text-xs font-semibold text-emerald-400">Win Now</span>
                  </motion.div>
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Bottom CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="text-center mt-16"
        >
          <p className="text-gray-400 font-medium">
            <span className="text-emerald-400 font-semibold">5+ Sports</span> covered with real-time odds from all major sportsbooks
          </p>
        </motion.div>
      </div>
    </section>
  );
}

