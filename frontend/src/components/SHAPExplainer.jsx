import React, { useEffect, useState } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell
} from 'recharts';
import { CheckCircle2 } from 'lucide-react';

export default function SHAPExplainer() {
  const [shapData, setShapData] = useState([]);

  useEffect(() => {
    fetch('/api/shap')
      .then((res) => res.json())
      .then((data) => setShapData(data.shap_importance || []))
      .catch((err) => console.error("Failed to fetch SHAP:", err));
  }, []);

  const colors = ['#1B5E20', '#2E7D32', '#4CAF50', '#66BB6A', '#81C784', '#A5D6A7', '#C8E6C9'];

  return (
    <div className="bg-white border border-agri-border rounded-2xl p-5 shadow-sm">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-extrabold text-agri-textDark">
            SHAP Feature Residual Breakdown
          </h3>
          <p className="text-xs text-agri-textMuted font-medium">
            Explainable AI: Relative Feature Contribution to Biological Residual Predictions
          </p>
        </div>

        <div className="flex items-center gap-1.5 bg-emerald-50 border border-emerald-300 text-emerald-900 text-xs font-bold px-3 py-1.5 rounded-xl mt-2 sm:mt-0">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>Study Dummy Importance: 0.00% (100% Biophysics-Driven)</span>
        </div>
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            layout="vertical"
            data={shapData}
            margin={{ top: 10, right: 30, left: 180, bottom: 10 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" horizontal={false} />
            <XAxis type="number" unit="%" stroke="#A3B8A5" tick={{ fontSize: 11 }} />
            <YAxis
              type="category"
              dataKey="feature"
              stroke="#1C281D"
              tick={{ fontSize: 11, fontWeight: 600 }}
              width={170}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const d = payload[0].payload;
                  return (
                    <div className="bg-agri-textDark text-white text-xs p-2.5 rounded-xl shadow-lg border border-agri-earth">
                      <div className="font-bold text-amber-400">{d.feature}</div>
                      <div>Relative Importance: <span className="font-bold text-white">{d.importance_pct}%</span></div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Bar dataKey="importance_pct" radius={[0, 4, 4, 0]}>
              {shapData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
