import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import HeroIntro from './components/HeroIntro';
import Header from './components/Header';
import RiceVisualCards from './components/RiceVisualCards';
import ControlPanel from './components/ControlPanel';
import MetricCards from './components/MetricCards';
import ResearchPapers from './components/ResearchPapers';
import OptimizationCurve from './components/OptimizationCurve';
import TradeOffSurface3D from './components/TradeOffSurface3D';
import ModelEvaluation from './components/ModelEvaluation';
import SHAPExplainer from './components/SHAPExplainer';
import DatasetExplorer from './components/DatasetExplorer';
import { Activity, Box, BarChart2, ShieldCheck, Database } from 'lucide-react';

export default function App() {
  const [showIntro, setShowIntro] = useState(() => {
    return !sessionStorage.getItem('crispr_intro_seen');
  });

  const [district, setDistrict] = useState('Warangal');
  const [season, setSeason] = useState('Kharif');
  const [temp, setTemp] = useState(26.5);
  const [rh, setRh] = useState(60.0);
  const [isDrought, setIsDrought] = useState(true);
  const [modelArch, setModelArch] = useState('Physics-Informed Hybrid Model');
  const [useStreaming, setUseStreaming] = useState(false);

  const [predictionData, setPredictionData] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeTab, setActiveTab] = useState('curve');

  const handleIntroComplete = () => {
    setShowIntro(false);
    sessionStorage.setItem('crispr_intro_seen', 'true');
  };

  const handleReplayIntro = () => {
    setShowIntro(true);
  };

  // Fetch district defaults when district/season changes
  useEffect(() => {
    fetch(`/api/defaults?district=${district}&season=${season}`)
      .then((res) => res.json())
      .then((data) => {
        if (data.default_temp) setTemp(data.default_temp);
        if (data.default_rh) setRh(data.default_rh);
      })
      .catch((err) => console.error("Failed to fetch defaults:", err));
  }, [district, season]);

  // Execute prediction (REST or Streaming SSE)
  useEffect(() => {
    if (useStreaming) {
      setIsStreaming(true);
      const url = `/api/predict/stream?district=${district}&season=${season}&temperature_c=${temp}&relative_humidity_pct=${rh}&is_drought=${isDrought}&model_arch=${encodeURIComponent(modelArch)}`;
      const sse = new EventSource(url);

      let streamedReductions = [];
      let streamedHybrid = [];
      let streamedPhysics = [];
      let streamedLower = [];
      let streamedUpper = [];

      sse.addEventListener('step', (e) => {
        const item = JSON.parse(e.data);
        streamedReductions.push(item.reduction_pct);
        streamedHybrid.push(item.hybrid_wue);
        streamedPhysics.push(item.physics_wue);
        streamedLower.push(item.lower_ci);
        streamedUpper.push(item.upper_ci);

        const activePreds = modelArch.includes('Hybrid') ? streamedHybrid : streamedPhysics;
        let bestIdx = 0;
        let maxVal = -999;
        activePreds.forEach((v, idx) => {
          if (v > maxVal) {
            maxVal = v;
            bestIdx = idx;
          }
        });

        setPredictionData({
          district,
          season,
          temperature_c: temp,
          relative_humidity_pct: rh,
          vpd_kpa: roundVal(calcVpd(temp, rh)),
          optimal_target_reduction_pct: streamedReductions[bestIdx] || 0,
          predicted_intrinsic_wue: maxVal,
          ci_95_lower: roundVal(maxVal * 0.85),
          ci_95_upper: roundVal(maxVal * 1.15),
          reductions: [...streamedReductions],
          hybrid_predictions: [...streamedHybrid],
          physics_baseline_predictions: [...streamedPhysics],
          active_predictions: [...activePreds],
          confidence_lower: [...streamedLower],
          confidence_upper: [...streamedUpper]
        });
      });

      sse.addEventListener('complete', () => {
        setIsStreaming(false);
        sse.close();
      });

      sse.onerror = (err) => {
        setIsStreaming(false);
        sse.close();
      };

      return () => sse.close();
    } else {
      setIsStreaming(false);
      fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          district,
          season,
          temperature_c: temp,
          relative_humidity_pct: rh,
          is_drought: isDrought,
          model_arch: modelArch
        })
      })
        .then((res) => res.json())
        .then((data) => setPredictionData(data))
        .catch((err) => console.error("Failed to predict:", err));
    }
  }, [district, season, temp, rh, isDrought, modelArch, useStreaming]);

  const tabs = [
    { id: 'curve', label: 'Optimization Response Curve', icon: Activity },
    { id: 'surface3d', label: '3D Trade-Off Surface', icon: Box },
    { id: 'evaluation', label: 'Physics vs Hybrid Evaluation', icon: BarChart2 },
    { id: 'shap', label: 'Stomatal Mechanics & Explainability', icon: ShieldCheck },
    { id: 'dataset', label: 'Dataset Explorer', icon: Database },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      {/* Opening Hero Intro Animation Overlay */}
      {showIntro && <HeroIntro onComplete={handleIntroComplete} />}

      <Header onReplayIntro={handleReplayIntro} />

      <RiceVisualCards />

      {/* Seasonal Smooth Motion Container */}
      <AnimatePresence mode="wait">
        <motion.div
          key={`${district}-${season}`}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.35, ease: "easeOut" }}
        >
          <ControlPanel
            district={district}
            setDistrict={setDistrict}
            season={season}
            setSeason={setSeason}
            temp={temp}
            setTemp={setTemp}
            rh={rh}
            setRh={setRh}
            isDrought={isDrought}
            setIsDrought={setIsDrought}
            modelArch={modelArch}
            setModelArch={setModelArch}
            useStreaming={useStreaming}
            setUseStreaming={setUseStreaming}
          />
        </motion.div>
      </AnimatePresence>

      <MetricCards data={predictionData} />

      <ResearchPapers />

      {/* Tabs Bar */}
      <div className="flex border-b border-agri-border mb-6 gap-2 overflow-x-auto">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold transition-colors whitespace-nowrap border-b-2 ${
                isActive
                  ? 'border-agri-deep text-agri-deep bg-agri-sageLight/60 rounded-t-lg'
                  : 'border-transparent text-agri-textMuted hover:text-agri-textDark'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Panels */}
      {activeTab === 'curve' && <OptimizationCurve data={predictionData} />}
      {activeTab === 'surface3d' && <TradeOffSurface3D temp={temp} rh={rh} isDrought={isDrought} />}
      {activeTab === 'evaluation' && <ModelEvaluation data={predictionData} />}
      {activeTab === 'shap' && <SHAPExplainer />}
      {activeTab === 'dataset' && <DatasetExplorer />}

      {/* Footer */}
      <footer className="mt-12 pt-6 border-t border-agri-border text-center text-xs text-agri-textMuted font-medium">
        CRISPR Rice Engineering System | Department of Computer Science & Engineering, JNTUH
      </footer>
    </div>
  );
}

function calcVpd(t, rh) {
  const es = 0.6108 * Math.exp((17.27 * t) / (t + 237.3));
  const ea = es * (rh / 100.0);
  return Math.max(0.1, es - ea);
}

function roundVal(val) {
  return Math.round(val * 100) / 100;
}
