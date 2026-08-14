import React, { useEffect, useState } from 'react';
import { Database, Search } from 'lucide-react';

export default function DatasetExplorer() {
  const [rows, setRows] = useState([]);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    fetch('/api/dataset?limit=100')
      .then((res) => res.json())
      .then((data) => setRows(data.data || []))
      .catch((err) => console.error("Failed to fetch dataset:", err));
  }, []);

  const filteredRows = rows.filter((r) => {
    const q = filter.toLowerCase();
    return (
      (r.Paper_ID && r.Paper_ID.toLowerCase().includes(q)) ||
      (r.Cultivar && r.Cultivar.toLowerCase().includes(q)) ||
      (r.Gene_Target && r.Gene_Target.toLowerCase().includes(q))
    );
  });

  return (
    <div className="bg-white border border-agri-border rounded-2xl p-5 shadow-sm">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-4">
        <div>
          <h3 className="text-base font-extrabold text-agri-textDark flex items-center gap-2">
            <Database className="w-4 h-4 text-agri-deep" />
            <span>Curated Research Master Dataset (168 Digitized Measurements)</span>
          </h3>
          <p className="text-xs text-agri-textMuted font-medium">
            100% Measured Biological Data (Caine2019, Karavolias2023, Karavolias2024)
          </p>
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 text-agri-textMuted absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search paper, cultivar, gene..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-full bg-agri-sageLight border border-agri-sageBorder rounded-xl pl-9 pr-3 py-1.5 text-xs font-semibold text-agri-textDark focus:outline-none focus:ring-2 focus:ring-agri-deep"
          />
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl border border-agri-border max-h-80">
        <table className="w-full text-left text-xs">
          <thead className="bg-agri-sageLight text-agri-deep font-extrabold uppercase text-[10px] tracking-wider sticky top-0 border-b border-agri-sageBorder">
            <tr>
              <th className="p-2.5">Paper ID</th>
              <th className="p-2.5">Cultivar</th>
              <th className="p-2.5">Gene Target</th>
              <th className="p-2.5">Reduction (%)</th>
              <th className="p-2.5">Photosynthesis A</th>
              <th className="p-2.5">Conductance gs</th>
              <th className="p-2.5">Intrinsic WUE</th>
              <th className="p-2.5">Temp (°C)</th>
              <th className="p-2.5">Water Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-agri-border bg-white font-medium text-agri-textDark">
            {filteredRows.map((r, idx) => (
              <tr key={idx} className="hover:bg-agri-sageLight/50 transition-colors">
                <td className="p-2.5 font-bold text-agri-deep">{r.Paper_ID}</td>
                <td className="p-2.5">{r.Cultivar}</td>
                <td className="p-2.5">{r.Gene_Target}</td>
                <td className="p-2.5 font-bold">{r.Relative_Stomatal_Reduction_Pct}%</td>
                <td className="p-2.5">{r.Photosynthetic_Rate_A}</td>
                <td className="p-2.5">{r.Stomatal_Conductance_gs}</td>
                <td className="p-2.5 font-extrabold text-agri-textDark">{r.WUE_intrinsic}</td>
                <td className="p-2.5">{r.Temperature_C}°C</td>
                <td className="p-2.5 font-semibold text-agri-textMuted">{r.Water_Treatment}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
