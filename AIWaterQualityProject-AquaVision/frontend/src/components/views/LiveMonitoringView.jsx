import React from 'react';

export default function LiveMonitoringView({
  tankers = [],
  selectedTanker,
  setSelectedTanker,
  openReportModal,
  onOpenManualReading,
}) {
  const activeTanker = selectedTanker || tankers[0];

  if (!activeTanker) {
    return (
      <div className="p-12 text-center bg-brand-surface rounded-2xl border border-brand-silver/60">
        <span className="material-symbols-outlined text-4xl text-brand-charcoal mb-2">monitoring</span>
        <h3 className="font-bold text-base text-brand-dark">No Monitored Tankers Found</h3>
        <p className="text-xs text-brand-charcoal mt-1">Please register or seed tankers first.</p>
      </div>
    );
  }

  const measurements = activeTanker.measurements || {};
  // Handle both reading_history (from SQLite) and legacy history
  const history = activeTanker.reading_history || activeTanker.history || [];

  return (
    <section className="space-y-6 animate-in fade-in duration-300">
      {/* Header & Notice */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-brand-silver/40">
        <div>
          <div className="font-tech-code text-brand-charcoal uppercase text-xs tracking-widest mb-1 flex items-center gap-2">
            <span>REAL-TIME IOT TELEMETRY ACQUISITION</span>
            <span className="w-2 h-2 rounded-full bg-emerald-500 live-pulse"></span>
          </div>
          <h1 className="text-2xl font-extrabold text-brand-dark">Live Water Quality Telemetry</h1>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <span className="px-3 py-1 rounded-xl bg-brand-warning text-brand-dark text-xs font-tech-code font-bold border border-amber-300">
            SIMULATED DEMO PROBES
          </span>
          <button
            onClick={() => onOpenManualReading && onOpenManualReading(activeTanker.id)}
            className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-brand-surface border border-brand-silver text-brand-dark hover:bg-brand-surfaceAlt flex items-center gap-1.5 shadow-2xs"
          >
            <span className="material-symbols-outlined text-[16px] text-brand-primary">edit_note</span>
            Log Field Reading
          </button>
          <button
            onClick={() => openReportModal(activeTanker.id)}
            className="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-brand-primary text-white hover:bg-brand-primary-dark flex items-center gap-1.5 shadow-sm"
          >
            <span className="material-symbols-outlined text-[16px]">description</span>
            Generate AI Report
          </button>
        </div>
      </div>

      {/* Tanker Selection Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        {tankers.map((t) => {
          const isSelected = t.id === activeTanker.id;
          const statusLower = (t.status || '').toLowerCase();
          const dotColor =
            statusLower === 'normal' || statusLower === 'good'
              ? 'bg-emerald-500'
              : statusLower === 'warning'
              ? 'bg-amber-400'
              : 'bg-rose-500';

          return (
            <button
              key={t.id}
              onClick={() => setSelectedTanker(t)}
              className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 whitespace-nowrap cursor-pointer ${
                isSelected
                  ? 'bg-brand-primary text-white shadow-sm'
                  : 'bg-brand-surface border border-brand-silver/60 text-brand-charcoal hover:text-brand-dark hover:bg-brand-surfaceAlt'
              }`}
            >
              <span className="material-symbols-outlined text-[16px]">
                {isSelected ? 'radio_button_checked' : 'radio_button_unchecked'}
              </span>
              <span>{t.id}: {t.name.split(' - ')[1] || t.name}</span>
              <span className={`w-2 h-2 rounded-full ${dotColor}`}></span>
            </button>
          );
        })}
      </div>

      {/* 4 Primary Telemetry Parameter Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* pH Card */}
        <div className="bg-brand-surface rounded-2xl p-5 border border-brand-silver/70 shadow-2xs relative overflow-hidden">
          <div className="flex items-center justify-between mb-2">
            <span className="text-brand-charcoal uppercase text-xs font-semibold">Acidity / Alkalinity</span>
            <span className="font-tech-code text-xs px-2 py-0.5 rounded bg-brand-secondary/40 text-brand-primary font-bold">
              pH
            </span>
          </div>
          <div className="flex items-baseline gap-2 mb-2">
            <span className="font-mono-data text-3xl font-bold text-brand-dark">{measurements.pH?.toFixed(2) ?? '—'}</span>
            <span className="text-xs text-brand-charcoal">pH units</span>
          </div>
          <div className="flex items-center justify-between text-xs pt-2 border-t border-brand-silver/30">
            <span className="text-brand-charcoal">NSDWQ: 6.5 - 8.5</span>
            <span className={`font-bold ${measurements.pH >= 6.5 && measurements.pH <= 8.5 ? 'text-emerald-600' : 'text-rose-600'}`}>
              {measurements.pH >= 6.5 && measurements.pH <= 8.5 ? 'Optimal' : 'Out of Bounds'}
            </span>
          </div>
        </div>

        {/* TDS Card */}
        <div className="bg-brand-surface rounded-2xl p-5 border border-brand-silver/70 shadow-2xs relative overflow-hidden">
          <div className="flex items-center justify-between mb-2">
            <span className="text-brand-charcoal uppercase text-xs font-semibold">Total Dissolved Solids</span>
            <span className="font-tech-code text-xs px-2 py-0.5 rounded bg-brand-secondary/40 text-brand-primary font-bold">
              TDS
            </span>
          </div>
          <div className="flex items-baseline gap-2 mb-2">
            <span className="font-mono-data text-3xl font-bold text-brand-dark">{measurements.TDS ?? '—'}</span>
            <span className="text-xs text-brand-charcoal">mg/L (ppm)</span>
          </div>
          <div className="flex items-center justify-between text-xs pt-2 border-t border-brand-silver/30">
            <span className="text-brand-charcoal">Pak Limit: &lt; 1000</span>
            <span className={`font-bold ${measurements.TDS <= 500 ? 'text-emerald-600' : measurements.TDS <= 1000 ? 'text-amber-600' : 'text-rose-600'}`}>
              {measurements.TDS <= 500 ? 'Excellent' : measurements.TDS <= 1000 ? 'Acceptable' : 'Elevated'}
            </span>
          </div>
        </div>

        {/* Turbidity Card */}
        <div className="bg-brand-surface rounded-2xl p-5 border border-brand-silver/70 shadow-2xs relative overflow-hidden">
          <div className="flex items-center justify-between mb-2">
            <span className="text-brand-charcoal uppercase text-xs font-semibold">Optical Clarity</span>
            <span className="font-tech-code text-xs px-2 py-0.5 rounded bg-brand-secondary/40 text-brand-primary font-bold">
              TURB
            </span>
          </div>
          <div className="flex items-baseline gap-2 mb-2">
            <span className="font-mono-data text-3xl font-bold text-brand-dark">{measurements.Turbidity?.toFixed(1) ?? '—'}</span>
            <span className="text-xs text-brand-charcoal">NTU</span>
          </div>
          <div className="flex items-center justify-between text-xs pt-2 border-t border-brand-silver/30">
            <span className="text-brand-charcoal">NSDWQ Limit: &lt; 5.0</span>
            <span className={`font-bold ${measurements.Turbidity <= 5.0 ? 'text-emerald-600' : 'text-rose-600'}`}>
              {measurements.Turbidity <= 5.0 ? 'Compliant' : 'Elevated'}
            </span>
          </div>
        </div>

        {/* Temperature Card */}
        <div className="bg-brand-surface rounded-2xl p-5 border border-brand-silver/70 shadow-2xs relative overflow-hidden">
          <div className="flex items-center justify-between mb-2">
            <span className="text-brand-charcoal uppercase text-xs font-semibold">Water Temperature</span>
            <span className="font-tech-code text-xs px-2 py-0.5 rounded bg-brand-secondary/40 text-brand-primary font-bold">
              TEMP
            </span>
          </div>
          <div className="flex items-baseline gap-2 mb-2">
            <span className="font-mono-data text-3xl font-bold text-brand-dark">{measurements.Temperature ?? '—'}</span>
            <span className="text-xs text-brand-charcoal">°C</span>
          </div>
          <div className="flex items-center justify-between text-xs pt-2 border-t border-brand-silver/30">
            <span className="text-brand-charcoal">EC: {measurements.EC || 500} µS/cm</span>
            <span className="text-emerald-600 font-bold">Stable</span>
          </div>
        </div>
      </div>

      {/* Historical Telemetry Curve for Selected Tanker */}
      <div className="bg-brand-surface rounded-2xl p-6 border border-brand-silver/70 shadow-2xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-base font-bold text-brand-dark">
              {activeTanker.name} — Chronological Telemetry Waveform
            </h3>
            <p className="text-xs text-brand-charcoal">
              Telemetry buffer: {history.length} logged data points for {activeTanker.id}
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-semibold">
            <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-brand-primary"></span> pH</span>
            <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-brand-secondary border border-brand-primary"></span> TDS</span>
            <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-amber-400"></span> Turbidity</span>
          </div>
        </div>

        {/* Dynamic Responsive SVG Line Chart */}
        <div className="h-64 bg-brand-surfaceAlt rounded-xl p-4 border border-brand-silver/40 flex items-center justify-center">
          <svg className="w-full h-full" viewBox="0 0 600 200" preserveAspectRatio="none">
            {/* Horizontal Grid */}
            <line x1="0" y1="40" x2="600" y2="40" stroke="#E5E7EB" strokeDasharray="3,3" />
            <line x1="0" y1="90" x2="600" y2="90" stroke="#E5E7EB" strokeDasharray="3,3" />
            <line x1="0" y1="140" x2="600" y2="140" stroke="#E5E7EB" strokeDasharray="3,3" />

            {/* Dynamic line points from history or fallback */}
            {history.length > 1 ? (() => {
              const count = history.length;
              const stepX = 600 / (count - 1);

              const phPoints = history.map((h, i) => {
                const x = i * stepX;
                const val = parseFloat(h.pH) || 7.0;
                const y = 180 - ((val - 6) / 3) * 160;
                return `${x},${Math.max(10, Math.min(190, y))}`;
              }).join(' ');

              const tdsPoints = history.map((h, i) => {
                const x = i * stepX;
                const val = parseFloat(h.TDS) || 400;
                const y = 180 - ((val - 200) / 700) * 160;
                return `${x},${Math.max(10, Math.min(190, y))}`;
              }).join(' ');

              const turbPoints = history.map((h, i) => {
                const x = i * stepX;
                const val = parseFloat(h.Turbidity) || 2.0;
                const y = 180 - (val / 6) * 160;
                return `${x},${Math.max(10, Math.min(190, y))}`;
              }).join(' ');

              return (
                <>
                  <polyline points={phPoints} fill="none" stroke="#716FA6" strokeWidth="3" />
                  <polyline points={tdsPoints} fill="none" stroke="#BBC8F2" strokeWidth="2.5" />
                  <polyline points={turbPoints} fill="none" stroke="#EAB308" strokeWidth="2" strokeDasharray="4,4" />
                </>
              );
            })() : (
              // If only 1 reading exists, draw smooth baseline
              <>
                <line x1="0" y1="100" x2="600" y2="100" stroke="#716FA6" strokeWidth="3" />
                <line x1="0" y1="120" x2="600" y2="120" stroke="#BBC8F2" strokeWidth="2.5" />
                <line x1="0" y1="140" x2="600" y2="140" stroke="#EAB308" strokeWidth="2" strokeDasharray="4,4" />
              </>
            )}
          </svg>
        </div>

        {/* Telemetry Log Table */}
        <div className="overflow-x-auto rounded-xl border border-brand-silver/50">
          <table className="w-full text-left text-xs">
            <thead className="bg-brand-surfaceAlt font-tech-code text-[11px] text-brand-charcoal">
              <tr>
                <th className="py-2.5 px-4">TIMESTAMP</th>
                <th className="py-2.5 px-4">pH</th>
                <th className="py-2.5 px-4">TDS (mg/L)</th>
                <th className="py-2.5 px-4">TURBIDITY (NTU)</th>
                <th className="py-2.5 px-4">TEMP (°C)</th>
                <th className="py-2.5 px-4 text-right">STATUS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-silver/30 font-medium">
              {history.length > 0 ? (
                history.slice(-8).reverse().map((h, idx) => (
                  <tr key={idx} className="hover:bg-brand-surfaceAlt/40">
                    <td className="py-2 px-4 font-tech-code text-brand-charcoal">{h.timestamp || 'Recorded'}</td>
                    <td className="py-2 px-4 font-mono-data font-bold text-brand-primary">{h.pH}</td>
                    <td className="py-2 px-4 font-mono-data font-bold">{h.TDS}</td>
                    <td className="py-2 px-4 font-mono-data">{h.Turbidity}</td>
                    <td className="py-2 px-4 font-mono-data">{h.Temperature}</td>
                    <td className="py-2 px-4 text-right">
                      <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-tech-code text-[10px] font-bold">
                        VERIFIED
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="6" className="py-4 text-center text-brand-charcoal">
                    No historical logs yet. Use &quot;Log Field Reading&quot; to add a telemetry entry.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
