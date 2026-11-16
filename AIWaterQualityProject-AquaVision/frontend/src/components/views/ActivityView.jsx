import React, { useState, useEffect } from 'react';
import { getActivityLogs } from '../../services/api';

export default function ActivityView() {
  const [logs, setLogs] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);

  const fetchLogs = () => {
    getActivityLogs(50)
      .then((data) => {
        setLogs(Array.isArray(data) ? data : []);
      })
      .catch(() => {
        setLogs([]);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 15000); // 15s refresh
    return () => clearInterval(interval);
  }, []);

  const filteredLogs = filter === 'all'
    ? logs
    : logs.filter((l) => (l.category || '').toLowerCase() === filter.toLowerCase());

  return (
    <section className="space-y-6 animate-in fade-in duration-300">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-brand-silver/40">
        <div>
          <div className="font-tech-code text-brand-charcoal uppercase text-xs tracking-widest mb-1 flex items-center gap-2">
            <span>AUDIT TRAIL &amp; PERSISTENT SYSTEM LOG</span>
            <span className="w-2 h-2 rounded-full bg-emerald-500 live-pulse"></span>
          </div>
          <h1 className="text-2xl font-extrabold text-brand-dark">System Telemetry &amp; AI Audit Logs</h1>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1 bg-brand-surface p-1 rounded-xl border border-brand-silver text-xs font-semibold">
          {['all', 'telemetry', 'ai', 'report', 'alert'].map((cat) => (
            <button
              key={cat}
              onClick={() => setFilter(cat)}
              className={`px-3 py-1 rounded-lg capitalize transition-all cursor-pointer ${
                filter === cat
                  ? 'bg-brand-primary text-white font-bold shadow-2xs'
                  : 'text-brand-charcoal hover:text-brand-dark'
              }`}
            >
              {cat}
            </button>
          ))}
          <button
            onClick={fetchLogs}
            className="p-1 rounded-lg text-brand-charcoal hover:text-brand-dark hover:bg-brand-surfaceAlt"
            title="Refresh logs"
          >
            <span className="material-symbols-outlined text-[16px]">refresh</span>
          </button>
        </div>
      </div>

      <div className="bg-brand-surface rounded-2xl border border-brand-silver/70 shadow-2xs divide-y divide-brand-silver/30 overflow-hidden">
        {loading && logs.length === 0 ? (
          <div className="p-8 text-center text-xs text-brand-charcoal">
            <span className="inline-block w-4 h-4 border-2 border-brand-primary border-t-transparent rounded-full animate-spin mb-2"></span>
            <div>Loading system audit logs...</div>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="p-8 text-center text-xs text-brand-charcoal">
            No audit events found for category: &quot;{filter}&quot;
          </div>
        ) : (
          filteredLogs.map((log) => {
            const catLower = (log.category || '').toLowerCase();
            const tag = log.tag || log.category?.toUpperCase() || 'INFO';
            const isAlert = catLower === 'alert' || catLower === 'warning';
            const isAI = catLower === 'ai';
            const isReport = catLower === 'report';

            return (
              <div
                key={log.id}
                className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs hover:bg-brand-surfaceAlt/40 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span
                    className={`px-2 py-0.5 rounded font-tech-code text-[10px] font-bold ${
                      isAlert
                        ? 'bg-rose-100 text-rose-800 border border-rose-300'
                        : isReport
                        ? 'bg-brand-warning text-brand-dark border border-amber-300'
                        : isAI
                        ? 'bg-brand-primary text-white'
                        : 'bg-brand-secondary text-brand-dark'
                    }`}
                  >
                    {tag}
                  </span>
                  <span className="font-bold text-brand-dark">{log.message}</span>
                </div>
                <span className="font-tech-code text-brand-charcoal text-[11px] sm:self-center">
                  [{log.created_at || log.time || 'Timestamp recorded'}]
                </span>
              </div>
            );
          })
        )}
      </div>
    </section>
  );
}
