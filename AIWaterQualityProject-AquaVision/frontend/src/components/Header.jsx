import React, { useState, useEffect } from 'react';

export default function Header({
  profile,
  currentView,
  setCurrentView,
  openReportModal,
  onOpenEditProfile,
}) {
  const [timeStr, setTimeStr] = useState('');
  const [alertsOpen, setAlertsOpen] = useState(false);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(now.toLocaleTimeString('en-US', { hour12: true }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Compute initials from profile name
  const getInitials = (name) => {
    if (!name) return 'AV';
    const parts = name.trim().split(/\s+/);
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  };

  return (
    <header className="sticky top-0 z-40 h-16 bg-brand-surface/90 backdrop-blur-md border-b border-brand-silver/50 px-8 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-sm font-semibold text-brand-dark">
          <span className="text-brand-charcoal font-normal">Location:</span>
          <span className="px-2.5 py-1 rounded-lg bg-brand-secondary/40 text-brand-dark text-xs font-bold border border-brand-secondary flex items-center gap-1.5">
            <span className="material-symbols-outlined text-[15px] text-brand-primary">science</span>
            Research Laboratory Unit A
          </span>
        </div>
        <span className="text-brand-silver">|</span>
        <div className="flex items-center gap-2 text-xs font-tech-code text-brand-charcoal">
          <span className="text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded border border-emerald-300 font-bold">
            TELEMETRY OK
          </span>
          <span>SYNC: <span className="font-mono-data font-bold">{timeStr || 'LIVE'}</span></span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Quick Report Generate Button in Header */}
        <button
          onClick={openReportModal}
          className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-brand-primary hover:bg-brand-primary-dark text-white shadow-sm transition-all"
        >
          <span className="material-symbols-outlined text-[16px]">add_circle</span>
          Generate Report
        </button>

        {/* Quick AI Assistant shortcut */}
        <button
          onClick={() => setCurrentView('ai-assistant')}
          className="flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-bold bg-brand-secondary/40 hover:bg-brand-secondary text-brand-dark border border-brand-secondary transition-all"
        >
          <span className="material-symbols-outlined text-[16px] text-brand-primary">smart_toy</span>
          AI Copilot
        </button>

        {/* Alerts Notification Bell */}
        <div className="relative">
          <button
            onClick={() => setAlertsOpen(!alertsOpen)}
            className="relative p-2 rounded-xl border border-brand-silver/60 hover:bg-brand-surfaceAlt text-brand-charcoal hover:text-brand-dark transition-all"
            title="System Alerts"
          >
            <span className="material-symbols-outlined text-[20px]">notifications</span>
            <span className="absolute top-1 right-1 w-2.5 h-2.5 rounded-full bg-amber-500 ring-2 ring-white"></span>
          </button>

          {alertsOpen && (
            <div className="absolute right-0 mt-2 w-80 bg-brand-surface rounded-2xl shadow-xl border border-brand-silver/60 p-3 z-50 animate-in fade-in">
              <div className="flex items-center justify-between pb-2 mb-2 border-b border-brand-silver/40 px-2">
                <span className="font-bold text-xs uppercase tracking-wider text-brand-charcoal">System Alerts</span>
                <button
                  onClick={() => setAlertsOpen(false)}
                  className="text-brand-charcoal hover:text-brand-dark text-xs font-semibold"
                >
                  Close
                </button>
              </div>
              <div className="space-y-2">
                <div className="p-2.5 rounded-xl bg-brand-warning/60 border border-brand-warning text-xs">
                  <div className="font-bold text-brand-dark flex items-center gap-1">
                    <span className="material-symbols-outlined text-[16px] text-amber-700">warning</span>
                    Turbidity Calibration Notice
                  </div>
                  <div className="text-brand-charcoal mt-1 text-[11px]">
                    Automatic coagulation recommendations available in AI Insights tab.
                  </div>
                </div>
                <div className="p-2.5 rounded-xl bg-brand-secondary/30 border border-brand-secondary text-xs">
                  <div className="font-bold text-brand-dark flex items-center gap-1">
                    <span className="material-symbols-outlined text-[16px] text-brand-primary">info</span>
                    Ensemble Machine Learning Active
                  </div>
                  <div className="text-brand-charcoal mt-1 text-[11px]">
                    CatBoost WQI Regressor &amp; LangGraph Copilot operational.
                  </div>
                </div>
              </div>
              <button
                onClick={() => {
                  setCurrentView('activity');
                  setAlertsOpen(false);
                }}
                className="mt-3 w-full py-1.5 text-center text-xs font-semibold text-brand-primary hover:underline"
              >
                View full activity audit log →
              </button>
            </div>
          )}
        </div>

        {/* User Profile Badge & Edit Profile Trigger */}
        <button
          onClick={onOpenEditProfile}
          title="Click to Edit Profile"
          className="flex items-center gap-2.5 pl-2.5 py-1 border-l border-brand-silver/40 hover:bg-brand-surfaceAlt rounded-xl transition-colors cursor-pointer group text-left"
        >
          <div className="w-9 h-9 rounded-xl bg-brand-primary/15 group-hover:bg-brand-primary/25 border border-brand-primary/30 flex items-center justify-center text-brand-primary font-bold text-xs shadow-xs transition-colors">
            {getInitials(profile?.name)}
          </div>
          <div className="hidden md:block">
            <div className="font-bold text-xs text-brand-dark leading-tight group-hover:text-brand-primary transition-colors flex items-center gap-1">
              <span>{profile?.name || 'Dr. Alweef'}</span>
              <span className="material-symbols-outlined text-[14px] text-brand-charcoal group-hover:text-brand-primary">edit</span>
            </div>
            <div className="text-[11px] text-brand-charcoal font-medium">
              {profile?.designation || 'Chief Water Analyst'}
            </div>
          </div>
        </button>
      </div>
    </header>
  );
}
