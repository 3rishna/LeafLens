import React from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceDot
} from 'recharts';

export default function OptimizationCurve({ data }) {
  if (!data || !data.reductions) return null;

  const chartData = data.reductions.map((r, idx) => ({
    reduction: r,
    wue: data.active_predictions[idx],
    lower: data.confidence_lower[idx],
    upper: data.confidence_upper[idx],
    band: [data.confidence_lower[idx], data.confidence_upper[idx]]
  }));

  const bestRed = data.optimal_target_reduction_pct;
  const bestWue = data.predicted_intrinsic_wue;

  return (
    <div className="bg-white border border-agri-border rounded-2xl p-5 shadow-sm">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-extrabold text-agri-textDark">
            Intrinsic WUE (A/gs) vs. Stomatal Reduction (%)
          </h3>
          <p className="text-xs text-agri-textMuted font-medium">
            District: <span className="font-bold text-agri-textDark">{data.district}</span> | Season: <span className="font-bold text-agri-textDark">{data.season}</span> | VPD: <span className="font-bold text-agri-deep">{data.vpd_kpa} kPa</span>
          </p>
        </div>

        <div className="flex items-center gap-4 text-xs font-semibold mt-2 sm:mt-0">
          <span className="flex items-center gap-1.5">
            <span className="w-3.5 h-1 bg-[#1B5E20] rounded"></span>
            <span>Hybrid Prediction</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 bg-[#C8E6C9] border border-[#2E7D32]/30 rounded"></span>
            <span>95% Sage Confidence Band</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 bg-[#E65100] rounded-full animate-ping opacity-75"></span>
            <span className="w-2.5 h-2.5 bg-[#E65100] rounded-full -ml-4"></span>
            <span>Peak Target ({bestRed}%)</span>
          </span>
        </div>
      </div>

      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 15, right: 20, left: 0, bottom: 15 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
            <XAxis
              dataKey="reduction"
              unit="%"
              tick={{ fontSize: 11, fill: '#4A5D4C', fontWeight: 600 }}
              stroke="#A3B8A5"
            />
            <YAxis
              tick={{ fontSize: 11, fill: '#4A5D4C', fontWeight: 600 }}
              stroke="#A3B8A5"
              domain={['auto', 'auto']}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const d = payload[0].payload;
                  return (
                    <div className="bg-agri-textDark text-white text-xs p-3 rounded-xl shadow-xl border border-agri-earth">
                      <div className="font-bold text-amber-400 mb-1">
                        Stomatal Reduction: {d.reduction}%
                      </div>
                      <div>Intrinsic WUE: <span className="font-bold text-white">{d.wue}</span></div>
                      <div className="text-[10px] text-agri-earthLight mt-1">
                        95% Bootstrap CI: [{d.lower}, {d.upper}]
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />

            {/* Soft Sage Green Confidence Area */}
            <Area
              type="monotone"
              dataKey="band"
              stroke="none"
              fill="#2E7D32"
              fillOpacity={0.14}
            />

            {/* Rich Deep Rice Green Prediction Line */}
            <Line
              type="monotone"
              dataKey="wue"
              stroke="#1B5E20"
              strokeWidth={3}
              dot={false}
              activeDot={{ r: 6, fill: '#1B5E20' }}
            />

            {/* Peak Target Marker */}
            <ReferenceDot
              x={bestRed}
              y={bestWue}
              r={8}
              fill="#E65100"
              stroke="#FFFFFF"
              strokeWidth={3}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
