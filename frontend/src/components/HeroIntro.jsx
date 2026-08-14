import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sprout, Sparkles, ArrowRight, Dna } from 'lucide-react';

export default function HeroIntro({ onComplete }) {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    // Cinematic 5-6 second total sequence
    const t1 = setTimeout(() => setPhase(1), 1800); // 1.8s: Leaf focus & stomata pulse
    const t2 = setTimeout(() => setPhase(2), 3800); // 3.8s: Text title reveal
    const t3 = setTimeout(() => {
      setPhase(3);
      if (onComplete) onComplete();
    }, 5800); // 5.8s: Smooth dissolve into active dashboard

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
    };
  }, [onComplete]);

  return (
    <AnimatePresence>
      {phase < 3 && (
        <motion.div
          initial={{ opacity: 1 }}
          exit={{ opacity: 0, scale: 0.98 }}
          transition={{ duration: 1.0, ease: "easeInOut" }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-agri-textDark overflow-hidden select-none"
        >
          {/* Background Cinematic Wide Rice Paddy Landscape (Distinct Early Morning Green Field) */}
          <motion.div
            initial={{ scale: 1, filter: "brightness(0.55) contrast(1.15)" }}
            animate={{
              scale: phase === 1 ? 1.08 : phase === 2 ? 1.14 : 1,
              filter: phase >= 1 ? "brightness(0.3) blur(1px)" : "brightness(0.55) contrast(1.15)"
            }}
            transition={{ duration: 2.2, ease: "easeInOut" }}
            className="absolute inset-0 bg-cover bg-center"
            style={{ backgroundImage: `url('/figures/rice_intro_cinematic.jpg')` }}
          />

          {/* Morning Sunrise Golden & Deep Leaf Green Gradient Overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-agri-textDark via-agri-deep/45 to-amber-950/25 mix-blend-multiply pointer-events-none" />

          {/* Floating Micro Droplet Particles */}
          <div className="absolute inset-0 pointer-events-none overflow-hidden">
            {[...Array(14)].map((_, i) => (
              <motion.div
                key={i}
                initial={{ y: "100vh", opacity: 0 }}
                animate={{
                  y: "-10vh",
                  opacity: [0, 0.7, 0],
                  x: [0, (i % 2 === 0 ? 35 : -35)]
                }}
                transition={{
                  duration: 5 + (i % 3),
                  repeat: Infinity,
                  delay: i * 0.3,
                  ease: "linear"
                }}
                className="absolute w-2 h-2 rounded-full bg-agri-sage/40 backdrop-blur-sm"
                style={{ left: `${(i * 7.5) + 3}%` }}
              />
            ))}
          </div>

          {/* Skip Intro Button */}
          <button
            onClick={() => {
              setPhase(3);
              if (onComplete) onComplete();
            }}
            className="absolute top-6 right-6 z-20 flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 hover:bg-white/20 text-white text-xs font-extrabold backdrop-blur-md border border-white/20 transition-all cursor-pointer shadow-lg"
          >
            <span>Skip Intro</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>

          {/* Phase 0: Cinematic Rice Paddy Field Opening */}
          {phase === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 25 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 1.0 }}
              className="z-10 text-center px-4"
            >
              <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-agri-deep/60 border border-agri-sage/30 text-agri-sage text-xs font-extrabold uppercase tracking-widest mb-4 backdrop-blur-md">
                <Sprout className="w-4 h-4 text-agri-sage" />
                <span>Telangana Climate-Resilient Agriculture</span>
              </div>
              <h2 className="text-3xl md:text-5xl font-black text-white tracking-tight">
                Oryza sativa Stomatal Optimization
              </h2>
            </motion.div>
          )}

          {/* Phase 1: Microscopic Stomata Pulsing Focus */}
          {phase === 1 && (
            <motion.div
              initial={{ opacity: 0, scale: 0.92 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.05 }}
              transition={{ duration: 1.0 }}
              className="z-10 flex flex-col items-center text-center px-4"
            >
              <div className="relative mb-6">
                <motion.div
                  animate={{ scale: [1, 1.3, 1], opacity: [0.3, 0.85, 0.3] }}
                  transition={{ duration: 1.6, repeat: Infinity, ease: "easeInOut" }}
                  className="w-28 h-28 rounded-full bg-agri-leaf/30 border-2 border-agri-sage absolute -inset-4 blur-md"
                />
                <div className="w-20 h-20 rounded-full bg-agri-deep border-2 border-agri-sage flex items-center justify-center shadow-2xl relative">
                  <Dna className="w-10 h-10 text-agri-sage animate-pulse" />
                </div>
              </div>
              <div className="text-agri-sage text-xs font-extrabold uppercase tracking-widest mb-1.5">
                Targeting Stomatal Conductance (gs) & Photosynthesis (A)
              </div>
              <h3 className="text-xl md:text-3xl font-extrabold text-white">
                Simulating CRISPR OsEPF1 Stomatal Density Edits
              </h3>
            </motion.div>
          )}

          {/* Phase 2: Final Title Reveal */}
          {phase === 2 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1.0 }}
              className="z-10 flex flex-col items-center text-center max-w-3xl px-6"
            >
              <Sparkles className="w-8 h-8 text-amber-400 mb-3 animate-bounce" />
              <h1 className="text-3xl md:text-5xl font-black text-white tracking-tight leading-tight mb-3">
                Optimising Stomatal Density for Telangana’s Climate
              </h1>
              <p className="text-sm md:text-base text-agri-sageLight font-medium leading-relaxed">
                Physics-Informed Machine Learning to Optimize CRISPR Stomatal Engineering for Climate-Resilient Rice
              </p>
            </motion.div>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
