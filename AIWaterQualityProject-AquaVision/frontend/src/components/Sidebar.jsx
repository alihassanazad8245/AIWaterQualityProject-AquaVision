import React from 'react';

export default function Sidebar({ currentView, setCurrentView, reportsCount = 0, tankersCount = 0 }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: 'dashboard' },
    { id: 'tankers', label: 'Tankers Fleet', icon: 'local_shipping', count: tankersCount },
    { id: 'live', label: 'Live Monitoring', icon: 'monitoring', badge: 'LIVE' },
    { id: 'analytics', label: 'Analytics', icon: 'analytics' },
    { id: 'ai-insights', label: 'AI Insights', icon: 'psychology', badge: 'New', badgeColor: 'bg-brand-warning text-brand-dark' },
    { id: 'ai-assistant', label: 'AI Assistant', icon: 'smart_toy', badge: 'AI Copilot', badgeColor: 'bg-brand-secondary text-brand-dark' },
    { id: 'reports', label: 'Reports', icon: 'description', count: reportsCount },
    { id: 'activity', label: 'Activity Logs', icon: 'history' },
    { id: 'settings', label: 'Settings', icon: 'settings' },
  ];

  return (
    <aside className="fixed left-0 top-0 h-full w-72 bg-brand-surface z-50 flex flex-col justify-between border-r border-brand-silver/50 shadow-xs transition-all">
      <div className="flex flex-col h-full">
        {/* Brand Header */}
        <div className="p-6 border-b border-brand-silver/30 flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-brand-primary text-white flex items-center justify-center font-bold text-lg shadow-md shadow-brand-primary/20 ring-2 ring-brand-secondary/40">
            AV
          </div>
          <div>
            <div className="font-bold text-base tracking-tight text-brand-dark flex items-center gap-1.5">
              AquaVision
              <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 live-pulse"></span>
            </div>
            <div className="font-tech-code text-[10px] text-brand-charcoal uppercase tracking-widest">
              AI WATER QUALITY SYSTEMS
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-5 space-y-1.5 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = currentView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setCurrentView(item.id)}
                className={`w-full flex items-center px-4 py-2.5 rounded-xl font-medium text-sm transition-all duration-150 ${
                  isActive
                    ? 'bg-brand-primary text-white shadow-sm shadow-brand-primary/25 font-semibold'
                    : 'text-brand-charcoal hover:bg-brand-surfaceAlt hover:text-brand-dark'
                }`}
              >
                <span
                  className={`material-symbols-outlined mr-3 text-[20px] ${
                    isActive ? 'text-white' : 'text-brand-primary'
                  }`}
                >
                  {item.icon}
                </span>
                <span>{item.label}</span>

                {item.badge && (
                  <span
                    className={`ml-auto font-tech-code text-[10px] px-2 py-0.5 rounded-full font-bold ${
                      item.badgeColor || 'bg-brand-secondary text-brand-dark'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}

                {item.count !== undefined && item.count > 0 && (
                  <span className={`ml-auto font-tech-code text-[11px] px-2 py-0.5 rounded-md font-bold ${
                    isActive ? 'bg-white/20 text-white' : 'text-brand-charcoal bg-brand-surfaceAlt'
                  }`}>
                    {item.count}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
