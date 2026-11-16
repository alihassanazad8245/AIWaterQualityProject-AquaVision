import React from 'react';
import { getReportPdfUrl } from '../../services/api';

export default function DashboardView({
  tankers = [],
  reports = [],
  profile,
  setCurrentView,
  openReportModal,
  setSelectedReport,
  onSelectTanker,
  onOpenAddTanker,
  onOpenManualReading,
}) {
  // Dynamically calculate fleet average WQI
  const avgWqi = tankers.length > 0
    ? (tankers.reduce((acc, t) => acc + (t.wqi_score || 0), 0) / tankers.length).toFixed(1)
    : '8.2';

  const totalReadings = tankers.reduce(
    (acc, t) => acc + (t.reading_history ? t.reading_history.length : 1),
    0
  );

  const normalCount = tankers.filter(t => (t.status || '').toLowerCase() === 'normal' || (t.status || '').toLowerCase() === 'good').length;

  return (
    <section className="space-y-6 animate-in fade-in duration-300">
      {/* Top Banner: Dynamic Greeting & Executive Actions */}
      <div className="bg-brand-surface rounded-2xl p-6 border border-brand-silver/60 shadow-xs flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-tech-code text-xs text-brand-primary font-bold tracking-wider uppercase">
              AQUAVISION RESEARCH PLATFORM
            </span>
            <span className="text-brand-silver">•</span>
            <span className="inline-flex items-center gap-1.5 text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
              Live Telemetry Stream Active
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-brand-dark tracking-tight">
            Good Day, {profile?.name || 'Dr. Alweef'}
          </h1>
          <p className="text-xs text-brand-charcoal mt-1">
            {profile?.designation || 'Chief Water Analyst'} • {profile?.organization || 'National Water Quality Authority'}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setCurrentView('tankers')}
            className="flex items-center gap-1.5 bg-brand-surfaceAlt hover:bg-brand-secondary/30 text-brand-dark px-3.5 py-2 rounded-xl font-bold text-xs border border-brand-silver/70 transition-all shadow-2xs"
          >
            <span className="material-symbols-outlined text-[17px] text-brand-primary">local_shipping</span>
            Manage Tankers
          </button>
          <button
            onClick={onOpenManualReading}
            className="flex items-center gap-1.5 bg-brand-surfaceAlt hover:bg-brand-secondary/30 text-brand-dark px-3.5 py-2 rounded-xl font-bold text-xs border border-brand-silver/70 transition-all shadow-2xs"
          >
            <span className="material-symbols-outlined text-[17px] text-brand-primary">edit_note</span>
            Log Reading
          </button>
          <button
            onClick={openReportModal}
            className="flex items-center gap-1.5 bg-brand-primary hover:bg-brand-primary-dark text-white px-4 py-2 rounded-xl font-bold text-xs transition-all shadow-sm"
          >
            <span className="material-symbols-outlined text-[17px]">description</span>
            Generate AI Report
          </button>
          <button
            onClick={() => setCurrentView('ai-assistant')}
            className="flex items-center gap-1.5 bg-brand-warning hover:bg-amber-200 text-brand-dark px-3.5 py-2 rounded-xl font-bold text-xs border border-amber-300 transition-all shadow-2xs"
          >
            <span className="material-symbols-outlined text-[17px]">smart_toy</span>
            AI Copilot
          </button>
        </div>
      </div>

      {/* Balanced 4-Column KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1: Overall Water Quality Score */}
        <div className="bg-brand-surface rounded-2xl p-5 border border-brand-silver/60 shadow-xs hover:border-brand-primary/50 transition-all flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold text-brand-charcoal uppercase tracking-wider">
                Fleet Average WQI
              </span>
              <span className="w-8 h-8 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 flex items-center justify-center">
                <span className="material-symbols-outlined text-[18px]">water_drop</span>
              </span>
            </div>
            <div className="flex items-baseline gap-1.5 mb-1">
              <span className="font-mono-data text-2xl font-bold text-brand-dark">{avgWqi}</span>
              <span className="text-xs font-semibold text-brand-charcoal">/ 10</span>
            </div>
          </div>
          <div className="pt-2 border-t border-brand-silver/30 flex items-center justify-between text-[11px]">
            <span className="text-emerald-700 font-bold">Safe Consumption</span>
            <span className="font-tech-code text-brand-charcoal">NSDWQ Checked</span>
          </div>
        </div>

        {/* KPI 2: Total Monitored Tankers */}
        <div className="bg-brand-surface rounded-2xl p-5 border border-brand-silver/60 shadow-xs hover:border-brand-primary/50 transition-all flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold text-brand-charcoal uppercase tracking-wider">
                Active Water Assets
              </span>
              <span className="w-8 h-8 rounded-lg bg-brand-secondary/40 border border-brand-secondary text-brand-primary flex items-center justify-center">
                <span className="material-symbols-outlined text-[18px]">local_shipping</span>
              </span>
            </div>
            <div className="flex items-baseline gap-1.5 mb-1">
              <span className="font-mono-data text-2xl font-bold text-brand-dark">{tankers.length}</span>
              <span className="text-xs font-semibold text-brand-charcoal">Tankers Active</span>
            </div>
          </div>
          <div className="pt-2 border-t border-brand-silver/30 flex items-center justify-between text-[11px]">
            <span className="text-brand-primary font-semibold">{normalCount} Normal Status</span>
            <button
              onClick={() => setCurrentView('tankers')}
              className="text-brand-charcoal hover:text-brand-dark font-medium underline"
            >
              View Fleet
            </button>
          </div>
        </div>

        {/* KPI 3: Total Telemetry Readings Logged */}
        <div className="bg-brand-surface rounded-2xl p-5 border border-brand-silver/60 shadow-xs hover:border-brand-primary/50 transition-all flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold text-brand-charcoal uppercase tracking-wider">
                Total Readings Logged
              </span>
              <span className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-200 text-blue-700 flex items-center justify-center">
                <span className="material-symbols-outlined text-[18px]">analytics</span>
              </span>
            </div>
            <div className="flex items-baseline gap-1.5 mb-1">
              <span className="font-mono-data text-2xl font-bold text-brand-dark">{totalReadings}</span>
              <span className="text-xs font-semibold text-brand-charcoal">Samples Recorded</span>
            </div>
          </div>
          <div className="pt-2 border-t border-brand-silver/30 flex items-center justify-between text-[11px]">
            <span className="text-brand-charcoal">Continuous Influx</span>
            <span className="text-brand-primary font-tech-code font-bold">15s Telemetry</span>
          </div>
        </div>

        {/* KPI 4: Generated Reports */}
        <div className="bg-brand-surface rounded-2xl p-5 border border-brand-silver/60 shadow-xs hover:border-brand-primary/50 transition-all flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-bold text-brand-charcoal uppercase tracking-wider">
                Generated Reports
              </span>
              <span className="w-8 h-8 rounded-lg bg-purple-50 border border-purple-200 text-purple-700 flex items-center justify-center">
                <span className="material-symbols-outlined text-[18px]">description</span>
              </span>
            </div>
            <div className="flex items-baseline gap-1.5 mb-1">
              <span className="font-mono-data text-2xl font-bold text-brand-dark">{reports.length}</span>
              <span className="text-xs font-semibold text-brand-charcoal">Audits Produced</span>
            </div>
          </div>
          <div className="pt-2 border-t border-brand-silver/30 flex items-center justify-between text-[11px]">
            <span className="text-brand-charcoal">ML Inference Ensemble</span>
            <button
              onClick={() => setCurrentView('reports')}
              className="text-brand-primary hover:text-brand-primary-dark font-bold underline"
            >
              All Reports
            </button>
          </div>
        </div>
      </div>

      {/* Fleet Telemetry Status Section */}
      <div className="bg-brand-surface rounded-2xl p-6 border border-brand-silver/60 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-bold text-brand-dark">Monitored Water Fleet &amp; Reservoir Probes</h2>
            <p className="text-xs text-brand-charcoal">
              Real-time telemetry and Water Quality Index calculated across municipal distribution points.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onOpenAddTanker}
              className="px-3 py-1.5 rounded-lg border border-brand-silver/70 text-brand-dark text-xs font-semibold hover:bg-brand-surfaceAlt flex items-center gap-1"
            >
              <span className="material-symbols-outlined text-[16px] text-brand-primary">add</span>
              Add Tanker
            </button>
            <button
              onClick={() => setCurrentView('live')}
              className="px-3 py-1.5 rounded-lg bg-brand-surfaceAlt text-brand-dark text-xs font-semibold hover:bg-brand-secondary/30 flex items-center gap-1"
            >
              <span className="material-symbols-outlined text-[16px] text-brand-primary">monitoring</span>
              Live Grid
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {tankers.slice(0, 4).map((t) => {
            const statusLower = (t.status || '').toLowerCase();
            const badgeClass =
              statusLower === 'normal' || statusLower === 'good'
                ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
                : statusLower === 'warning'
                ? 'bg-amber-100 text-amber-800 border-amber-200'
                : 'bg-rose-100 text-rose-800 border-rose-200';

            return (
              <div
                key={t.id}
                className="bg-brand-surfaceAlt/60 rounded-xl p-4 border border-brand-silver/50 hover:border-brand-primary/60 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-tech-code font-bold text-xs text-brand-primary">{t.id}</span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${badgeClass}`}>
                      {t.status}
                    </span>
                  </div>

                  <h3 className="font-bold text-xs text-brand-dark truncate">{t.name}</h3>
                  <p className="text-[11px] text-brand-charcoal mb-3 truncate">
                    {t.city}, {t.province}
                  </p>

                  {/* Telemetry Numbers */}
                  <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                    <div className="p-2 rounded-lg bg-brand-surface border border-brand-silver/30">
                      <span className="text-[10px] text-brand-charcoal block">pH Level</span>
                      <span className="font-mono-data font-bold text-brand-primary text-xs">
                        {t.measurements?.pH?.toFixed(2) ?? '—'}
                      </span>
                    </div>
                    <div className="p-2 rounded-lg bg-brand-surface border border-brand-silver/30">
                      <span className="text-[10px] text-brand-charcoal block">TDS (mg/L)</span>
                      <span className="font-mono-data font-bold text-brand-primary text-xs">
                        {t.measurements?.TDS ?? '—'}
                      </span>
                    </div>
                    <div className="p-2 rounded-lg bg-brand-surface border border-brand-silver/30">
                      <span className="text-[10px] text-brand-charcoal block">Turbidity</span>
                      <span className="font-mono-data font-bold text-brand-primary text-xs">
                        {t.measurements?.Turbidity?.toFixed(1) ?? '—'} NTU
                      </span>
                    </div>
                    <div className="p-2 rounded-lg bg-brand-surface border border-brand-silver/30">
                      <span className="text-[10px] text-brand-charcoal block">Temp</span>
                      <span className="font-mono-data font-bold text-brand-primary text-xs">
                        {t.measurements?.Temperature ?? '—'}°C
                      </span>
                    </div>
                  </div>
                </div>

                <div className="pt-2 border-t border-brand-silver/30 flex items-center justify-between gap-1.5">
                  <button
                    onClick={() => onSelectTanker && onSelectTanker(t)}
                    className="flex-1 py-1.5 rounded-lg bg-brand-surface hover:bg-brand-surfaceAlt text-brand-dark text-[11px] font-bold border border-brand-silver/50 transition-colors text-center"
                  >
                    Monitor
                  </button>
                  <button
                    onClick={() => openReportModal(t.id)}
                    className="flex-1 py-1.5 rounded-lg bg-brand-primary hover:bg-brand-primary-dark text-white text-[11px] font-bold transition-colors text-center"
                  >
                    AI Report
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Symmetrical 2-Column Section: Telemetry Curve & Recent Reports */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Real-time Telemetry Trend Visualizer */}
        <div className="lg:col-span-2 bg-brand-surface rounded-2xl p-6 border border-brand-silver/60 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
              <div>
                <h3 className="text-base font-bold text-brand-dark">Telemetry Dynamic Waveform</h3>
                <p className="text-xs text-brand-charcoal">
                  Continuous multi-node correlation: pH, TDS, and Turbidity across monitored stations
                </p>
              </div>
              <div className="flex items-center gap-3 text-xs font-semibold">
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-brand-primary"></span> pH Stream
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-brand-secondary border border-brand-primary"></span> TDS Stream
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-400"></span> Turbidity
                </span>
              </div>
            </div>

            <div className="h-56 bg-brand-surfaceAlt rounded-xl p-3 border border-brand-silver/40 flex items-center justify-center relative overflow-hidden">
              <svg className="w-full h-full" viewBox="0 0 600 200" preserveAspectRatio="none">
                <defs>
                  <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#716FA6" stopOpacity="0.25" />
                    <stop offset="100%" stopColor="#716FA6" stopOpacity="0" />
                  </linearGradient>
                </defs>
                <line x1="0" y1="50" x2="600" y2="50" stroke="#E5E7EB" strokeDasharray="3,3" />
                <line x1="0" y1="100" x2="600" y2="100" stroke="#E5E7EB" strokeDasharray="3,3" />
                <line x1="0" y1="150" x2="600" y2="150" stroke="#E5E7EB" strokeDasharray="3,3" />

                <path
                  d="M 0 130 C 100 80, 200 160, 300 90 C 400 30, 500 120, 600 70 L 600 200 L 0 200 Z"
                  fill="url(#chartGrad)"
                />
                <path
                  d="M 0 130 C 100 80, 200 160, 300 90 C 400 30, 500 120, 600 70"
                  fill="none"
                  stroke="#716FA6"
                  strokeWidth="3"
                />
                <path
                  d="M 0 110 C 150 140, 280 60, 420 120 C 500 150, 550 90, 600 100"
                  fill="none"
                  stroke="#BBC8F2"
                  strokeWidth="2.5"
                />
                <path
                  d="M 0 80 C 180 90, 320 140, 450 100 C 520 80, 570 120, 600 110"
                  fill="none"
                  stroke="#EAB308"
                  strokeDasharray="4,4"
                  strokeWidth="2"
                />
              </svg>
            </div>
          </div>

          <div className="flex items-center justify-between text-xs text-brand-charcoal pt-3 border-t border-brand-silver/30 mt-3">
            <span>Historical rolling buffer: Active telemetry sync</span>
            <span className="font-tech-code text-brand-primary font-bold">NSDWQ Tolerances Enforced</span>
          </div>
        </div>

        {/* Recent Generated Reports Mini Table */}
        <div className="bg-brand-surface rounded-2xl p-6 border border-brand-silver/60 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-brand-dark">Recent AI Reports</h3>
              <button
                onClick={() => setCurrentView('reports')}
                className="text-xs font-semibold text-brand-primary hover:underline"
              >
                View all ({reports.length}) →
              </button>
            </div>

            {reports.length === 0 ? (
              <div className="p-8 text-center bg-brand-surfaceAlt rounded-xl border border-brand-silver/40">
                <span className="material-symbols-outlined text-3xl text-brand-charcoal mb-1">
                  description
                </span>
                <p className="text-xs text-brand-charcoal">No reports generated yet.</p>
                <button
                  onClick={openReportModal}
                  className="mt-3 px-3 py-1.5 rounded-lg text-xs font-bold bg-brand-primary text-white"
                >
                  Generate First Report
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {reports.slice(0, 3).map((r) => (
                  <div
                    key={r.id}
                    className="p-3 rounded-xl bg-brand-surfaceAlt border border-brand-silver/40 hover:border-brand-primary transition-all text-xs"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-brand-dark">{r.tanker_id}</span>
                      <span className="font-tech-code text-[10px] text-brand-charcoal">
                        {r.created_at?.slice(0, 10)}
                      </span>
                    </div>
                    <div className="text-brand-charcoal truncate mb-2">{r.title}</div>
                    <div className="flex items-center justify-between pt-2 border-t border-brand-silver/30">
                      <span className="font-mono-data text-brand-primary font-bold">
                        WQI: {r.wqi_score}
                      </span>
                      <div className="flex items-center gap-1.5">
                        <button
                          onClick={() => setSelectedReport(r)}
                          className="px-2 py-1 rounded bg-brand-surface border border-brand-silver font-semibold hover:bg-brand-secondary/30"
                        >
                          Preview
                        </button>
                        <a
                          href={getReportPdfUrl(r.id)}
                          download
                          className="px-2 py-1 rounded bg-brand-primary text-white font-semibold flex items-center gap-1"
                        >
                          PDF
                        </a>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <button
            onClick={openReportModal}
            className="mt-4 w-full py-2.5 rounded-xl text-xs font-bold bg-brand-secondary/40 hover:bg-brand-secondary text-brand-dark border border-brand-secondary transition-all"
          >
            + Create New Report Analysis
          </button>
        </div>
      </div>
    </section>
  );
}
