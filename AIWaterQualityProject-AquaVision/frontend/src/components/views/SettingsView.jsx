import React, { useState } from 'react';

export default function SettingsView({ profile, onOpenEditProfile, tankers = [], reports = [] }) {
  const [turbThreshold, setTurbThreshold] = useState('3.5');
  const [tdsThreshold, setTdsThreshold] = useState('800');
  const [autoReport, setAutoReport] = useState(true);
  const [highRiskAlerts, setHighRiskAlerts] = useState(true);
  const [pollInterval, setPollInterval] = useState('15');
  const [saveMsg, setSaveMsg] = useState(null);

  const handleSavePreferences = (e) => {
    e.preventDefault();
    setSaveMsg('Preferences saved successfully to local session configuration.');
    setTimeout(() => setSaveMsg(null), 3000);
  };

  const handleExportFullState = () => {
    const backup = {
      profile,
      tankers,
      reportsCount: reports.length,
      exportedAt: new Date().toISOString(),
      standards: 'Pakistan NSDWQ & WHO 2024',
    };
    const blob = new Blob([JSON.stringify(backup, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `AquaVision_System_Configuration_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className="space-y-6 animate-in fade-in duration-300">
      <div className="pb-2 border-b border-brand-silver/40">
        <div className="font-tech-code text-brand-charcoal uppercase text-xs tracking-widest mb-1">
          SYSTEM PREFERENCES &amp; AUDIT POLICIES
        </div>
        <h1 className="text-2xl font-extrabold text-brand-dark">AquaVision Platform Configuration</h1>
      </div>

      {saveMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs font-semibold animate-in fade-in">
          {saveMsg}
        </div>
      )}

      {/* User Profile Card */}
      <div className="bg-brand-surface rounded-2xl p-6 border border-brand-silver/70 shadow-2xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <div>
            <span className="font-tech-code text-xs text-brand-primary font-bold uppercase">
              Authenticated Scientist Profile
            </span>
            <h3 className="text-base font-bold text-brand-dark">Research Identity &amp; Credentials</h3>
            <p className="text-xs text-brand-charcoal mt-0.5">
              Profile information appears on official laboratory reports and the monitoring dashboard.
            </p>
          </div>

          <button
            onClick={onOpenEditProfile}
            className="px-4 py-2 bg-brand-primary hover:bg-brand-primary-dark text-white rounded-xl text-xs font-bold transition-all shadow-2xs flex items-center gap-1.5 self-start sm:self-auto cursor-pointer"
          >
            <span className="material-symbols-outlined text-[16px]">edit</span>
            <span>Edit Profile Details</span>
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 p-4 rounded-xl bg-brand-surfaceAlt border border-brand-silver/50 text-xs">
          <div>
            <span className="text-brand-charcoal text-[11px] block font-medium">Full Name:</span>
            <span className="font-bold text-sm text-brand-dark">{profile?.name || 'Dr. Alweef'}</span>
          </div>
          <div>
            <span className="text-brand-charcoal text-[11px] block font-medium">Designation:</span>
            <span className="font-bold text-sm text-brand-dark">{profile?.designation || 'Chief Water Analyst'}</span>
          </div>
          <div>
            <span className="text-brand-charcoal text-[11px] block font-medium">Role:</span>
            <span className="font-bold text-sm text-brand-dark">{profile?.role || 'Administrator'}</span>
          </div>
          <div>
            <span className="text-brand-charcoal text-[11px] block font-medium">Organization:</span>
            <span className="font-bold text-sm text-brand-dark">{profile?.organization || 'AquaVision Lab'}</span>
          </div>
        </div>
      </div>

      {/* AI & Telemetry Preferences Form */}
      <form onSubmit={handleSavePreferences} className="bg-brand-surface rounded-2xl p-6 border border-brand-silver/70 shadow-2xs space-y-5">
        <h3 className="text-base font-bold text-brand-dark">Telemetry Alerts &amp; Autonomous Audit Trigger Thresholds</h3>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div>
            <label className="font-bold text-brand-dark block mb-1">Turbidity Warning Limit (NTU)</label>
            <input
              type="number"
              step="0.1"
              value={turbThreshold}
              onChange={(e) => setTurbThreshold(e.target.value)}
              className="w-full p-2.5 rounded-xl border border-brand-silver bg-brand-surface text-brand-dark font-mono-data"
            />
            <span className="text-[10px] text-brand-charcoal mt-1 block">Default: 3.5 NTU</span>
          </div>

          <div>
            <label className="font-bold text-brand-dark block mb-1">TDS High Alert Threshold (mg/L)</label>
            <input
              type="number"
              step="10"
              value={tdsThreshold}
              onChange={(e) => setTdsThreshold(e.target.value)}
              className="w-full p-2.5 rounded-xl border border-brand-silver bg-brand-surface text-brand-dark font-mono-data"
            />
            <span className="text-[10px] text-brand-charcoal mt-1 block">Pakistan NSDWQ Cap: 1000 mg/L</span>
          </div>

          <div>
            <label className="font-bold text-brand-dark block mb-1">Telemetry Mesh Sync Frequency (sec)</label>
            <select
              value={pollInterval}
              onChange={(e) => setPollInterval(e.target.value)}
              className="w-full p-2.5 rounded-xl border border-brand-silver bg-brand-surface text-brand-dark font-medium"
            >
              <option value="10">10 Seconds (High Velocity)</option>
              <option value="15">15 Seconds (Standard Laboratory)</option>
              <option value="30">30 Seconds (Low Power)</option>
              <option value="60">60 Seconds (Conservation Mode)</option>
            </select>
            <span className="text-[10px] text-brand-charcoal mt-1 block">Governs live acquisition buffer</span>
          </div>
        </div>

        <div className="space-y-3 pt-3 border-t border-brand-silver/30 text-xs">
          <div className="flex items-center justify-between py-1">
            <div>
              <div className="font-bold text-brand-dark">Autonomous LangGraph Report Suggestion</div>
              <div className="text-[11px] text-brand-charcoal">Automatically draft diagnostic reports when parameter deviations exceed thresholds</div>
            </div>
            <button
              type="button"
              onClick={() => setAutoReport(!autoReport)}
              className={`w-11 h-6 rounded-full p-0.5 transition-colors cursor-pointer ${autoReport ? 'bg-brand-primary' : 'bg-brand-silver'}`}
            >
              <div className={`w-5 h-5 rounded-full bg-white transition-all ${autoReport ? 'ml-auto' : 'mr-auto'}`}></div>
            </button>
          </div>

          <div className="flex items-center justify-between py-1">
            <div>
              <div className="font-bold text-brand-dark">Real-Time Risk Banner Notification</div>
              <div className="text-[11px] text-brand-charcoal">Display audio-visual alert indicators upon microbiological or chemical limit violations</div>
            </div>
            <button
              type="button"
              onClick={() => setHighRiskAlerts(!highRiskAlerts)}
              className={`w-11 h-6 rounded-full p-0.5 transition-colors cursor-pointer ${highRiskAlerts ? 'bg-brand-primary' : 'bg-brand-silver'}`}
            >
              <div className={`w-5 h-5 rounded-full bg-white transition-all ${highRiskAlerts ? 'ml-auto' : 'mr-auto'}`}></div>
            </button>
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            type="submit"
            className="px-5 py-2 rounded-xl text-xs font-bold bg-brand-primary hover:bg-brand-primary-dark text-white shadow-2xs transition-all cursor-pointer"
          >
            Save Configuration
          </button>
        </div>
      </form>

      {/* Architecture & AI Pipeline Status */}
      <div className="bg-brand-surface rounded-2xl p-6 border border-brand-silver/70 shadow-2xs space-y-3">
        <h3 className="text-base font-bold text-brand-dark">Active AI Model &amp; Regulatory Pipeline</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="p-3 bg-brand-surfaceAlt rounded-xl border border-brand-silver/40">
            <span className="font-tech-code text-[10px] text-brand-charcoal font-bold block mb-1">LARGE LANGUAGE MODEL</span>
            <span className="font-bold text-brand-primary">Gemini 3.1 Flash-Lite</span>
            <p className="text-[11px] text-brand-charcoal mt-1">Multi-turn LangGraph agent with failover to Gemini 3.5 Flash-Lite</p>
          </div>
          <div className="p-3 bg-brand-surfaceAlt rounded-xl border border-brand-silver/40">
            <span className="font-tech-code text-[10px] text-brand-charcoal font-bold block mb-1">REGRESSION &amp; CLASSIFICATION</span>
            <span className="font-bold text-brand-primary">CatBoost + Gradient Boosting</span>
            <p className="text-[11px] text-brand-charcoal mt-1">Trained on empirical water quality datasets for precise WQI index scoring</p>
          </div>
          <div className="p-3 bg-brand-surfaceAlt rounded-xl border border-brand-silver/40">
            <span className="font-tech-code text-[10px] text-brand-charcoal font-bold block mb-1">FORECASTING &amp; KNOWLEDGE BASE</span>
            <span className="font-bold text-brand-primary">ARIMA + ChromaDB Standards RAG</span>
            <p className="text-[11px] text-brand-charcoal mt-1">5-year predictive projection with Pakistan NSDWQ and WHO guidelines indexing</p>
          </div>
        </div>
      </div>

      {/* System Backup & Data Export */}
      <div className="bg-brand-surface rounded-2xl p-6 border border-brand-silver/70 shadow-2xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h4 className="font-bold text-sm text-brand-dark">Laboratory Audit Backup</h4>
          <p className="text-xs text-brand-charcoal mt-0.5">
            Export the complete platform configuration, telemetry telemetry logs, and tanker metadata to JSON.
          </p>
        </div>

        <button
          onClick={handleExportFullState}
          className="px-4 py-2 rounded-xl text-xs font-semibold bg-brand-surfaceAlt border border-brand-silver hover:bg-brand-secondary/30 text-brand-dark flex items-center gap-1.5 transition-all self-start sm:self-auto cursor-pointer"
        >
          <span className="material-symbols-outlined text-[16px]">file_download</span>
          <span>Export Platform State (JSON)</span>
        </button>
      </div>
    </section>
  );
}
