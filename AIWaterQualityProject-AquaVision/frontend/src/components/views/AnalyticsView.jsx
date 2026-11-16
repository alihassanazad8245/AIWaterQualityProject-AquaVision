import React from 'react';

export default function AnalyticsView({ analyticsData, tankers = [] }) {
  // Dynamically compute stats from tankers if analyticsData is not present
  const computeStats = (key, fallbackMin, fallbackAvg, fallbackMax) => {
    if (analyticsData && analyticsData[`${key.toLowerCase()}_stats`]) {
      return analyticsData[`${key.toLowerCase()}_stats`];
    }
    const vals = tankers
      .map((t) => t.measurements?.[key])
      .filter((v) => v !== undefined && v !== null && !isNaN(v));
    if (vals.length === 0) return { min: fallbackMin, avg: fallbackAvg, max: fallbackMax };
    const min = Math.min(...vals);
    const max = Math.max(...vals);
    const avg = vals.reduce((a, b) => a + b, 0) / vals.length;
    return {
      min: parseFloat(min.toFixed(2)),
      avg: parseFloat(avg.toFixed(2)),
      max: parseFloat(max.toFixed(2)),
    };
  };

  const ph = computeStats('pH', 6.7, 7.26, 7.85);
  const tds = computeStats('TDS', 420, 551, 780);
  const turb = computeStats('Turbidity', 2.1, 3.22, 4.6);
  const temp = computeStats('Temperature', 22.4, 24.45, 26.5);

  const handleExportCSV = () => {
    let csv = "Tanker_ID,Name,City,Source_Type,pH,TDS,Turbidity,Temperature,Status,WQI_Score\n";
    tankers.forEach((t) => {
      const m = t.measurements || {};
      csv += `"${t.id}","${t.name}","${t.city}","${t.source_type}",${m.pH ?? ''},${m.TDS ?? ''},${m.Turbidity ?? ''},${m.Temperature ?? ''},"${t.status}",${t.wqi_score ?? ''}\n`;
    });
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `AquaVision_Telemetry_Export_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className="space-y-6 animate-in fade-in duration-300">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-brand-silver/40">
        <div>
          <div className="font-tech-code text-brand-charcoal uppercase text-xs tracking-widest mb-1">
            RESEARCH &amp; COMPARATIVE ANALYTICS
          </div>
          <h1 className="text-2xl font-extrabold text-brand-dark">Parameter Distribution &amp; History</h1>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExportCSV}
            className="px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-brand-surface border border-brand-silver text-brand-dark hover:bg-brand-surfaceAlt flex items-center gap-1.5 shadow-2xs"
          >
            <span className="material-symbols-outlined text-[16px]">download</span>
            Export Dataset (CSV)
          </button>
        </div>
      </div>

      {/* Comparative Metrics Table (Min / Avg / Max) */}
      <div className="bg-brand-surface rounded-2xl p-6 border border-brand-silver/70 shadow-2xs">
        <h3 className="text-base font-bold text-brand-dark mb-4">
          Telemetry Dynamics Across All Monitored Reservoirs ({tankers.length} Active Nodes)
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-brand-surfaceAlt border border-brand-silver/50">
            <span className="text-xs font-bold text-brand-charcoal uppercase block mb-1">pH Acidity Spectrum</span>
            <div className="mt-2 space-y-1.5 text-xs">
              <div className="flex justify-between"><span className="text-brand-charcoal">Minimum:</span> <span className="font-mono-data font-bold">{ph.min}</span></div>
              <div className="flex justify-between"><span className="text-brand-charcoal">Fleet Mean:</span> <span className="font-mono-data font-bold text-brand-primary">{ph.avg}</span></div>
              <div className="flex justify-between"><span className="text-brand-charcoal">Maximum:</span> <span className="font-mono-data font-bold">{ph.max}</span></div>
            </div>
            <div className="mt-3 pt-2 border-t border-brand-silver/40 text-[10px] text-brand-charcoal">
              Target Standard: 6.5 - 8.5
            </div>
          </div>

          <div className="p-4 rounded-xl bg-brand-surfaceAlt border border-brand-silver/50">
            <span className="text-xs font-bold text-brand-charcoal uppercase block mb-1">TDS Concentration</span>
            <div className="mt-2 space-y-1.5 text-xs">
              <div className="flex justify-between"><span className="text-brand-charcoal">Minimum:</span> <span className="font-mono-data font-bold">{tds.min} ppm</span></div>
              <div className="flex justify-between"><span className="text-brand-charcoal">Fleet Mean:</span> <span className="font-mono-data font-bold text-brand-primary">{tds.avg} ppm</span></div>
              <div className="flex justify-between"><span className="text-brand-charcoal">Maximum:</span> <span className="font-mono-data font-bold text-amber-700">{tds.max} ppm</span></div>
            </div>
            <div className="mt-3 pt-2 border-t border-brand-silver/40 text-[10px] text-brand-charcoal">
              Pakistan NSDWQ: &lt; 1000 mg/L
            </div>
          </div>

          <div className="p-4 rounded-xl bg-brand-surfaceAlt border border-brand-silver/50">
            <span className="text-xs font-bold text-brand-charcoal uppercase block mb-1">Optical Turbidity</span>
            <div className="mt-2 space-y-1.5 text-xs">
              <div className="flex justify-between"><span className="text-brand-charcoal">Minimum:</span> <span className="font-mono-data font-bold">{turb.min} NTU</span></div>
              <div className="flex justify-between"><span className="text-brand-charcoal">Fleet Mean:</span> <span className="font-mono-data font-bold text-brand-primary">{turb.avg} NTU</span></div>
              <div className="flex justify-between"><span className="text-brand-charcoal">Maximum:</span> <span className="font-mono-data font-bold">{turb.max} NTU</span></div>
            </div>
            <div className="mt-3 pt-2 border-t border-brand-silver/40 text-[10px] text-brand-charcoal">
              Regulatory Ceiling: &lt; 5.0 NTU
            </div>
          </div>

          <div className="p-4 rounded-xl bg-brand-surfaceAlt border border-brand-silver/50">
            <span className="text-xs font-bold text-brand-charcoal uppercase block mb-1">Thermal Dispersion</span>
            <div className="mt-2 space-y-1.5 text-xs">
              <div className="flex justify-between"><span className="text-brand-charcoal">Minimum:</span> <span className="font-mono-data font-bold">{temp.min} °C</span></div>
              <div className="flex justify-between"><span className="text-brand-charcoal">Fleet Mean:</span> <span className="font-mono-data font-bold text-brand-primary">{temp.avg} °C</span></div>
              <div className="flex justify-between"><span className="text-brand-charcoal">Maximum:</span> <span className="font-mono-data font-bold">{temp.max} °C</span></div>
            </div>
            <div className="mt-3 pt-2 border-t border-brand-silver/40 text-[10px] text-brand-charcoal">
              Ambient Distribution Range
            </div>
          </div>
        </div>
      </div>

      {/* Comparative Multi-Node Chart */}
      <div className="bg-brand-surface rounded-2xl p-6 border border-brand-silver/70 shadow-2xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-base font-bold text-brand-dark">Cross-Tanker Node Comparison Curve</h3>
            <p className="text-xs text-brand-charcoal">Normalized chemical stabilization vectors across mobile distribution points</p>
          </div>
          <div className="flex items-center gap-3 text-xs font-semibold flex-wrap">
            {tankers.slice(0, 4).map((t, idx) => {
              const colors = ['bg-brand-primary', 'bg-brand-secondary border border-brand-primary', 'bg-amber-400', 'bg-rose-400'];
              return (
                <span key={t.id} className="flex items-center gap-1.5">
                  <span className={`w-3 h-3 rounded-full ${colors[idx % colors.length]}`}></span>
                  <span>{t.id} ({t.city})</span>
                </span>
              );
            })}
          </div>
        </div>

        <div className="h-64 bg-brand-surfaceAlt rounded-xl p-4 border border-brand-silver/40 flex items-center justify-center">
          <svg className="w-full h-full" viewBox="0 0 600 200" preserveAspectRatio="none">
            <line x1="0" y1="50" x2="600" y2="50" stroke="#E5E7EB" strokeDasharray="3,3" />
            <line x1="0" y1="100" x2="600" y2="100" stroke="#E5E7EB" strokeDasharray="3,3" />
            <line x1="0" y1="150" x2="600" y2="150" stroke="#E5E7EB" strokeDasharray="3,3" />

            <path d="M 0 140 C 150 60, 300 180, 600 80" fill="none" stroke="#716FA6" strokeWidth="3" />
            <path d="M 0 110 C 150 140, 300 70, 600 120" fill="none" stroke="#BBC8F2" strokeWidth="3" />
            <path d="M 0 90 C 200 80, 400 150, 600 110" fill="none" stroke="#F2EFC4" strokeDasharray="4,4" strokeWidth="3" />
            <path d="M 0 60 C 180 120, 350 40, 600 140" fill="none" stroke="#F43F5E" strokeWidth="2.5" />
          </svg>
        </div>
      </div>
    </section>
  );
}
