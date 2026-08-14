import React from 'react';
import { motion } from 'framer-motion';
import { Droplet, Leaf, Sprout, ShieldCheck } from 'lucide-react';

export default function MetricCards({ data }) {
  if (!data) return null;

  const cards = [
    {
      title: "Vapor Pressure Deficit",
      value: `${data.vpd_kpa} kPa`,
      sub: "Atmospheric Water Demand",
      icon: Droplet,
      iconColor: "text-agri-sky",
      badgeColor: "bg-agri-skyLight text-agri-sky"
    },
    {
      title: "Candidate Target Target",
      value: `${data.optimal_target_reduction_pct}% Reduction`,
      sub: "Optimal Candidate Peak",
      icon: Leaf,
      iconColor: "text-agri-deep",
      badgeColor: "bg-agri-sageLight text-agri-deep"
    },
    {
      title: "Predicted Intrinsic WUE",
      value: `${data.predicted_intrinsic_wue}`,
      sub: "μmol CO₂ / mol H₂O",
      icon: Sprout,
      iconColor: "text-agri-leaf",
      badgeColor: "bg-agri-sageLight text-agri-leaf"
    },
    {
      title: "95% Confidence Interval",
      value: `[${data.ci_95_lower}, ${data.ci_95_upper}]`,
      sub: "Bootstrap Uncertainty Window",
      icon: ShieldCheck,
      iconColor: "text-emerald-700",
      badgeColor: "bg-emerald-50 text-emerald-800"
    }
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <motion.div
            key={card.title}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: idx * 0.07 }}
            whileHover={{ y: -4 }}
            className="card-agri bg-agri-cardSoft flex flex-col justify-between hover:shadow-[0_8px_25px_rgba(46,125,50,0.15)] transition-all cursor-default"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-extrabold text-agri-textMuted uppercase tracking-wider">
                {card.title}
              </span>
              <div className={`p-1.5 rounded-lg ${card.badgeColor}`}>
                <Icon className={`w-4 h-4 ${card.iconColor}`} />
              </div>
            </div>

            <div className="text-2xl font-black text-agri-textDark tracking-tight my-1">
              {card.value}
            </div>

            <div className="text-xs font-semibold text-agri-deep mt-1">
              {card.sub}
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
