import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sprout, Play, Maximize2, X, Sun } from 'lucide-react';

export default function Header({ onReplayIntro }) {
  const [showHeaderModal, setShowHeaderModal] = useState(false);

  return (
    <>
      <header className="bg-white border border-agri-border border-l-4 border-l-agri-deep rounded-2xl p-5 md:p-6 mb-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4 relative overflow-hidden">
        {/* Floating Micro Particles / Water Droplets Background Effect */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden opacity-30">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="absolute w-1.5 h-1.5 rounded-full bg-agri-leaf animate-pulse"
              style={{
                top: `${(i * 15) + 10}%`,
                left: `${(i * 18) + 5}%`,
                animationDelay: `${i * 0.4}s`
              }}
            />
          ))}
        </div>

        <div className="z-10 max-w-3xl">
          <div className="flex items-center gap-2.5 mb-1.5">
            <div className="p-2 bg-agri-sageLight rounded-xl border border-agri-sageBorder">
              <Sprout className="w-6 h-6 text-agri-deep" />
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-agri-textDark tracking-tight">
              CRISPR Rice Engineering System
            </h1>

            {onReplayIntro && (
              <button
                onClick={onReplayIntro}
                title="Replay Opening Intro Animation"
                className="ml-2 flex items-center gap-1 px-2.5 py-1 rounded-lg bg-agri-sageLight hover:bg-agri-sageBorder text-agri-deep text-[11px] font-bold border border-agri-sageBorder transition-colors cursor-pointer"
              >
                <Play className="w-3 h-3 fill-agri-deep" />
                <span>Intro</span>
              </button>
            )}
          </div>

          <p className="text-xs md:text-sm text-agri-textMuted font-bold leading-relaxed">
            Physics-Informed Machine Learning to Optimize CRISPR Stomatal Engineering for Climate-Resilient Rice in Telangana
          </p>
        </div>

        {/* Distinct Header Card: Close-to-mid shot of Young Rice Seedlings in Water under Sun */}
        <motion.div
          whileHover={{ scale: 1.03, y: -2 }}
          onClick={() => setShowHeaderModal(true)}
          className="hidden md:flex items-center gap-3 bg-agri-sageLight/90 hover:bg-agri-sageLight border border-agri-sageBorder p-2.5 rounded-xl shadow-inner z-10 max-w-xs cursor-pointer group transition-all hover:shadow-[0_8px_20px_rgba(46,125,50,0.15)]"
        >
          <div className="relative w-20 h-20 rounded-lg overflow-hidden border border-agri-sageBorder flex-shrink-0">
            <img
              src="/figures/climate_sun.jpg"
              alt="Young Rice Seedlings in Sun"
              className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
            />
            <div className="absolute inset-0 bg-agri-deep/20 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
              <Maximize2 className="w-4 h-4 text-white drop-shadow" />
            </div>
          </div>
          <div className="text-xs">
            <div className="font-extrabold text-agri-deep flex items-center gap-1">
              <Sun className="w-3 h-3 text-amber-600" />
              <span>Young Seedlings & VPD</span>
            </div>
            <div className="text-[11px] text-agri-textMuted font-medium leading-tight mt-0.5 group-hover:text-agri-textDark transition-colors">
              Young rice seedlings in water under strong solar radiation & VPD heat stress
            </div>
            <div className="text-[10px] font-bold text-agri-leaf mt-1">Click to enlarge &rarr;</div>
          </div>
        </motion.div>

        {/* Soft Sage Gradient Overlay */}
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-agri-sageLight/50 to-transparent pointer-events-none" />
      </header>

      {/* Interactive Lightbox Modal for Header Rice Image */}
      <AnimatePresence>
        {showHeaderModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setShowHeaderModal(false)}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-agri-textDark/80 backdrop-blur-md"
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white border border-agri-border rounded-2xl max-w-3xl w-full overflow-hidden shadow-2xl relative"
            >
              <button
                onClick={() => setShowHeaderModal(false)}
                className="absolute top-4 right-4 z-10 p-2 rounded-full bg-agri-textDark/70 hover:bg-agri-textDark text-white backdrop-blur-md transition-all cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>

              <div className="relative h-80 sm:h-96 w-full bg-black">
                <img
                  src="/figures/climate_sun.jpg"
                  alt="Young Rice Seedlings under High Sun"
                  className="w-full h-full object-contain"
                />
              </div>

              <div className="p-6 bg-agri-cardSoft border-t border-agri-border">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2.5 py-1 rounded-md bg-amber-100 border border-amber-300 text-amber-800 text-xs font-bold flex items-center gap-1">
                    <Sun className="w-3.5 h-3.5 text-amber-600" />
                    <span>Solar Radiation & VPD</span>
                  </span>
                  <span className="text-xs font-extrabold text-agri-textMuted uppercase">
                    Telangana Seasonal Heat Stress
                  </span>
                </div>
                <h3 className="text-lg font-black text-agri-textDark mb-2">
                  Young Rice Seedlings Under Solar Radiation & Atmospheric Vapor Deficit
                </h3>
                <p className="text-xs sm:text-sm text-agri-textMuted font-medium leading-relaxed">
                  Atmospheric solar radiation (PPFD) and ambient temperature determine the evaporative demand (VPD) pulling water through rice guard cells. Under high Pre-Monsoon summer radiation in Telangana, stomatal density optimization protects seedling turgor and prevents canopy wilting.
                </p>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
