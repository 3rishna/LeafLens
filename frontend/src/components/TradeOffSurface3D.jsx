import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';

export default function TradeOffSurface3D({ temp, rh, isDrought }) {
  const [surfaceData, setSurfaceData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/surface3d?temp=${temp}&rh=${rh}&is_drought=${isDrought}`)
      .then((res) => res.json())
      .then((data) => {
        setSurfaceData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load 3D surface:", err);
        setLoading(false);
      });
  }, [temp, rh, isDrought]);

  if (loading) {
    return (
      <div className="bg-white border border-agri-border rounded-2xl p-12 text-center text-agri-textMuted text-sm font-semibold">
        Generating 3D Biophysical Trade-Off Mesh...
      </div>
    );
  }

  if (!surfaceData) return null;

  return (
    <div className="bg-white border border-agri-border rounded-2xl p-5 shadow-sm">
      <h3 className="text-base font-extrabold text-agri-textDark mb-1">
        3D Response Surface: Intrinsic WUE vs. Reduction (%) vs. VPD (kPa)
      </h3>
      <p className="text-xs text-agri-textMuted font-medium mb-4">
        Interactive Rotatable Surface Plot — Left-click & drag to rotate 3D view
      </p>

      <div className="w-full flex justify-center">
        <Plot
          data={[
            {
              z: surfaceData.z_wue_surface,
              x: surfaceData.x_reductions,
              y: surfaceData.y_vpds,
              type: 'surface',
              colorscale: 'Greens',
              colorbar: { title: 'Intrinsic WUE', len: 0.8 }
            }
          ]}
          layout={{
            autosize: true,
            margin: { l: 10, r: 10, b: 10, t: 10 },
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            scene: {
              xaxis: { title: 'Stomatal Reduction (%)', titlefont: { size: 11, color: '#1C281D' } },
              yaxis: { title: 'VPD (kPa)', titlefont: { size: 11, color: '#1C281D' } },
              zaxis: { title: 'Intrinsic WUE', titlefont: { size: 11, color: '#1C281D' } },
              camera: { eye: { x: 1.4, y: 1.4, z: 1.2 } }
            }
          }}
          useResizeHandler={true}
          style={{ width: '100%', height: '480px' }}
          config={{ responsive: true, displayModeBar: false }}
        />
      </div>
    </div>
  );
}
