import React from 'react';
import { Sliders, Sun, Droplet, Radio, MapPin, Calendar } from 'lucide-react';

export default function ControlPanel({
  district,
  setDistrict,
  season,
  setSeason,
  temp,
  setTemp,
  rh,
  setRh,
  isDrought,
  setIsDrought,
  modelArch,
  setModelArch,
  useStreaming,
  setUseStreaming
}) {
  const districts = ['Warangal', 'Nizamabad', 'Karimnagar', 'Nalgonda', 'Khammam'];

  return (
    <section className="bg-white border border-agri-border rounded-2xl p-5 mb-6 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <Sliders className="w-4 h-4 text-agri-deep" />
        <h2 className="text-xs font-bold text-agri-deep uppercase tracking-wider">
          Climate & Environmental Controls
        </h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-5">
        {/* District Select with Soft Green Accent */}
        <div>
          <label className="block text-xs font-bold text-agri-textMuted mb-1.5 flex items-center gap-1">
            <MapPin className="w-3.5 h-3.5 text-agri-leaf" />
            <span>District Location</span>
          </label>
          <select
            value={district}
            onChange={(e) => setDistrict(e.target.value)}
            className="w-full bg-agri-sageLight border border-agri-sageBorder rounded-xl px-3 py-2 text-xs font-extrabold text-agri-deep focus:outline-none focus:ring-2 focus:ring-agri-deep"
          >
            {districts.map((d) => (
              <option key={d} value={d}>
                {d} District
              </option>
            ))}
          </select>
        </div>

        {/* Season Toggle with Soft Green Accent */}
        <div>
          <label className="block text-xs font-bold text-agri-textMuted mb-1.5 flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5 text-agri-leaf" />
            <span>Target Season</span>
          </label>
          <div className="flex items-center gap-2 bg-agri-cardSoft border border-agri-border rounded-xl p-1">
            <button
              type="button"
              onClick={() => setSeason('Kharif')}
              className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-bold transition-all ${
                season === 'Kharif'
                  ? 'bg-agri-deep text-white shadow-sm'
                  : 'text-agri-textMuted hover:text-agri-textDark'
              }`}
            >
              Kharif
            </button>
            <button
              type="button"
              onClick={() => setSeason('Pre_Monsoon')}
              className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-bold transition-all ${
                season === 'Pre_Monsoon'
                  ? 'bg-agri-deep text-white shadow-sm'
                  : 'text-agri-textMuted hover:text-agri-textDark'
              }`}
            >
              Pre-Monsoon
            </button>
          </div>
        </div>

        {/* Temperature Slider with Green-to-Blue Gradient */}
        <div>
          <div className="flex justify-between items-center text-xs font-bold text-agri-textMuted mb-1">
            <span className="flex items-center gap-1">
              <Sun className="w-3.5 h-3.5 text-amber-600" />
              <span>Temperature</span>
            </span>
            <span className="text-agri-deep font-extrabold">{temp}°C</span>
          </div>
          <div className="relative flex items-center">
            <input
              type="range"
              min="20.0"
              max="42.0"
              step="0.5"
              value={temp}
              onChange={(e) => setTemp(parseFloat(e.target.value))}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer bg-gradient-to-r from-agri-leaf via-amber-500 to-agri-sky accent-agri-deep"
            />
          </div>
        </div>

        {/* Humidity Slider with Green-to-Blue Gradient */}
        <div>
          <div className="flex justify-between items-center text-xs font-bold text-agri-textMuted mb-1">
            <span className="flex items-center gap-1">
              <Droplet className="w-3.5 h-3.5 text-agri-sky" />
              <span>Relative Humidity</span>
            </span>
            <span className="text-agri-sky font-extrabold">{rh}%</span>
          </div>
          <div className="relative flex items-center">
            <input
              type="range"
              min="20"
              max="95"
              step="1"
              value={rh}
              onChange={(e) => setRh(parseFloat(e.target.value))}
              className="w-full h-2 rounded-lg appearance-none cursor-pointer bg-gradient-to-r from-amber-500 via-agri-leaf to-agri-sky accent-agri-deep"
            />
          </div>
        </div>

        {/* Irrigation Scarcity & Streaming Toggles */}
        <div className="flex flex-col gap-2 justify-center">
          <label className="flex items-center gap-2 text-xs font-bold cursor-pointer text-agri-textDark">
            <input
              type="checkbox"
              checked={isDrought}
              onChange={(e) => setIsDrought(e.target.checked)}
              className="rounded text-agri-deep focus:ring-agri-deep accent-agri-deep"
            />
            <span>Irrigation Scarcity Scenario</span>
          </label>

          <label className="flex items-center gap-2 text-xs font-bold cursor-pointer text-agri-textDark">
            <input
              type="checkbox"
              checked={useStreaming}
              onChange={(e) => setUseStreaming(e.target.checked)}
              className="rounded text-agri-deep focus:ring-agri-deep accent-agri-deep"
            />
            <span className="flex items-center gap-1">
              <Radio className="w-3.5 h-3.5 text-agri-leaf animate-pulse" />
              <span>Realtime SSE Streaming</span>
            </span>
          </label>
        </div>
      </div>
    </section>
  );
}
