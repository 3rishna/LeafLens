import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Dna, Sprout, ShieldCheck, Maximize2, X } from 'lucide-react';

export default function RiceVisualCards() {
  const [activeModal, setActiveModal] = useState(null);

  const cardsData = [
    {
      id: 'microscopy',
      title: 'Rice Leaf Microscopy (OsEPF1 / OsSTOMAGEN)',
      badge: 'SEM 1000x',
      badgeIcon: Dna,
      category: 'Biological Control Target',
      shortDesc: 'Stomatal pore density directly regulates transpirational water loss vs. CO₂ assimilation rate.',
      imageSrc: '/figures/stomatal_microscopy.jpg',
      fullCaption: 'Scanning Electron Micrograph (SEM) of Oryza sativa leaf surface at 1000x magnification. Each pair of guard cells surrounds a stomatal pore. CRISPR editing of promoter regions (e.g. OsEPF1, OsSTOMAGEN) modulates pore frequency to optimize water-use efficiency under heat and drought stress.'
    },
    {
      id: 'paddy_landscape',
      title: 'Telangana Paddy Field Landscape',
      badge: 'NASA Data',
      badgeIcon: ShieldCheck,
      category: 'Field Optimization',
      shortDesc: 'Clean panoramic view of dense green paddy fields across Warangal, Nizamabad, Karimnagar, Nalgonda, and Khammam.',
      imageSrc: '/figures/rice_field.jpg',
      fullCaption: 'Authentic green paddy cultivation field in Telangana, India. Bright young green rice plants grown under canal irrigation and tropical micro-climates. The machine learning model integrates 11 years of NASA POWER climate metrics across all 5 agricultural districts to determine seasonal stomatal reduction targets.'
    }
  ];

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-6">
        {cardsData.map((card, idx) => {
          const BadgeIcon = card.badgeIcon;
          return (
            <motion.div
              key={card.id}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: idx * 0.1 }}
              whileHover={{ scale: 1.02, y: -4 }}
              onClick={() => setActiveModal(card)}
              className="bg-white border border-agri-border border-l-4 border-l-agri-deep rounded-2xl p-4 shadow-sm hover:shadow-[0_10px_30px_rgba(46,125,50,0.2)] transition-all cursor-pointer flex flex-col sm:flex-row items-center gap-4 group"
            >
              <div className="relative overflow-hidden rounded-xl border border-agri-sageBorder flex-shrink-0 w-full sm:w-40 h-32">
                <img
                  src={card.imageSrc}
                  alt={card.title}
                  className="w-full h-full object-cover transform group-hover:scale-108 transition-transform duration-500"
                />
                <div className="absolute top-2 left-2 bg-agri-textDark/80 text-white text-[10px] font-extrabold px-2 py-0.5 rounded backdrop-blur-sm flex items-center gap-1">
                  <BadgeIcon className="w-3 h-3 text-agri-sage" />
                  <span>{card.badge}</span>
                </div>
                <div className="absolute inset-0 bg-agri-deep/20 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <span className="bg-white/90 text-agri-deep text-[10px] font-extrabold px-2.5 py-1 rounded-full shadow flex items-center gap-1">
                    <Maximize2 className="w-3 h-3" /> Expand View
                  </span>
                </div>
              </div>

              <div className="flex-1">
                <div className="text-xs font-extrabold text-agri-deep uppercase tracking-wider mb-1 flex items-center gap-1.5">
                  <Sprout className="w-3.5 h-3.5 text-agri-leaf" />
                  <span>{card.category}</span>
                </div>
                <h4 className="text-sm font-extrabold text-agri-textDark mb-1 group-hover:text-agri-deep transition-colors">
                  {card.title}
                </h4>
                <p className="text-xs text-agri-textMuted font-medium leading-relaxed">
                  {card.shortDesc}
                </p>
                <div className="text-[11px] font-bold text-agri-leaf mt-2 flex items-center gap-1 group-hover:underline">
                  <span>Click to enlarge view</span> &rarr;
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Interactive Lightbox Modal */}
      <AnimatePresence>
        {activeModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setActiveModal(null)}
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
                onClick={() => setActiveModal(null)}
                className="absolute top-4 right-4 z-10 p-2 rounded-full bg-agri-textDark/70 hover:bg-agri-textDark text-white backdrop-blur-md transition-all cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>

              <div className="relative h-80 sm:h-96 w-full bg-black">
                <img
                  src={activeModal.imageSrc}
                  alt={activeModal.title}
                  className="w-full h-full object-contain"
                />
              </div>

              <div className="p-6 bg-agri-cardSoft border-t border-agri-border">
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2.5 py-1 rounded-md bg-agri-sageLight border border-agri-sageBorder text-agri-deep text-xs font-bold">
                    {activeModal.badge}
                  </span>
                  <span className="text-xs font-extrabold text-agri-textMuted uppercase">
                    {activeModal.category}
                  </span>
                </div>
                <h3 className="text-lg font-black text-agri-textDark mb-2">
                  {activeModal.title}
                </h3>
                <p className="text-xs sm:text-sm text-agri-textMuted font-medium leading-relaxed">
                  {activeModal.fullCaption}
                </p>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
