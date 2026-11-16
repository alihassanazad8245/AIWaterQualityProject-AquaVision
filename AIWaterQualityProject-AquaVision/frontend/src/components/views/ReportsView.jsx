import React, { useState } from 'react';
import { getReportPdfUrl } from '../../services/api';

export default function ReportsView({ reports = [], openReportModal, setSelectedReport }) {
  const [searchTerm, setSearchTerm] = useState('');

  const filtered = reports.filter((r) => {
    const term = searchTerm.toLowerCase();
    const id = String(r.id || '').toLowerCase();
    const title = String(r.title || '').toLowerCase();
    const tankerId = String(r.tanker_id || '').toLowerCase();
    const city = String(r.city || '').toLowerCase();
    const status = String(r.status || '').toLowerCase();
    return id.includes(term) || title.includes(term) || tankerId.includes(term) || city.includes(term) || status.includes(term);
  });

  return (
    <section className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-brand-silver/40">
        <div>
          <div className="font-tech-code text-brand-charcoal uppercase text-xs tracking-widest mb-1">
            ARCHIVE &amp; EXPORT SYSTEM
          </div>
          <h1 className="text-2xl font-extrabold text-brand-dark">Research &amp; Quality Reports</h1>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => openReportModal && openReportModal()}
            className="bg-brand-primary hover:bg-brand-primary-dark text-white px-4 py-2.5 rounded-xl font-semibold text-xs transition-all shadow-sm flex items-center gap-2 cursor-pointer"
          >
            <span className="material-symbols-outlined text-[18px]">add_circle</span>
            Generate New Report
          </button>
        </div>
      </div>

      {/* Filter / Search Bar */}
      <div className="flex items-center gap-3 bg-brand-surface p-3.5 rounded-2xl border border-brand-silver/70 shadow-2xs">
        <span className="material-symbols-outlined text-brand-charcoal text-[20px]">search</span>
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder="Search reports by ID, tanker, city, or status..."
          className="flex-1 text-xs bg-transparent focus:outline-none text-brand-dark placeholder-brand-charcoal/60"
        />
        {searchTerm && (
          <button onClick={() => setSearchTerm('')} className="text-brand-charcoal text-xs hover:text-brand-dark font-medium cursor-pointer">
            Clear
          </button>
        )}
      </div>

      {/* Reports List Table */}
      <div className="bg-brand-surface rounded-2xl border border-brand-silver/70 shadow-2xs overflow-hidden">
        {filtered.length === 0 ? (
          <div className="p-12 text-center text-xs text-brand-charcoal space-y-3">
            <span className="material-symbols-outlined text-4xl text-brand-silver">folder_open</span>
            <p className="font-semibold text-brand-dark">No reports match your search criteria.</p>
            <button
              onClick={() => openReportModal && openReportModal()}
              className="px-4 py-2 bg-brand-primary hover:bg-brand-primary-dark text-white rounded-xl font-bold text-xs shadow-2xs cursor-pointer"
            >
              Generate a New Water Quality Report
            </button>
          </div>
        ) : (
          <div className="divide-y divide-brand-silver/30">
            {filtered.map((r) => {
              const pdfUrl = getReportPdfUrl(r.id);
              const statusStr = String(r.status || 'Verified Safe');
              const isSafe = statusStr.toLowerCase().includes('safe') || statusStr.toLowerCase().includes('verified');
              const isObs = statusStr.toLowerCase().includes('observation') || statusStr.toLowerCase().includes('borderline');

              return (
                <div
                  key={r.id}
                  className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-brand-surfaceAlt/40 transition-colors"
                >
                  <div className="flex items-start sm:items-center gap-4">
                    <div className="w-10 h-10 rounded-xl bg-brand-secondary/40 text-brand-primary flex items-center justify-center font-bold flex-shrink-0">
                      <span className="material-symbols-outlined text-[22px]">description</span>
                    </div>

                    <div>
                      <div className="font-bold text-sm text-brand-dark flex items-center gap-2">
                        <span>{r.title}</span>
                        <span className="font-tech-code text-[11px] text-brand-primary font-normal">
                          [{r.id}]
                        </span>
                      </div>
                      <div className="text-xs text-brand-charcoal font-tech-code mt-0.5">
                        {r.tanker_id} • {r.city ? `${r.city}, ${r.province || ''}` : 'National Water Grid'} • {r.created_at ? new Date(r.created_at).toLocaleDateString() : 'Recent'}
                      </div>
                      <div className="flex items-center gap-3 text-[11px] font-mono-data text-brand-charcoal mt-1">
                        <span>WQI Score: <strong className="text-brand-dark">{r.wqi_score}</strong></span>
                        <span>Quality Tier: <strong className="text-brand-dark">{r.quality_class || 'Good'}</strong></span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-center">
                    <span
                      className={`px-2.5 py-1 rounded-full text-xs font-bold border ${
                        isSafe
                          ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                          : isObs
                          ? 'bg-brand-warning text-brand-dark border-amber-300'
                          : 'bg-rose-100 text-rose-800 border-rose-300'
                      }`}
                    >
                      {statusStr}
                    </span>

                    <button
                      onClick={() => setSelectedReport(r)}
                      className="px-3 py-1.5 rounded-lg border border-brand-silver text-xs font-semibold text-brand-dark hover:bg-brand-surfaceAlt flex items-center gap-1 cursor-pointer"
                    >
                      <span className="material-symbols-outlined text-[15px]">visibility</span>
                      Preview
                    </button>

                    <a
                      href={pdfUrl}
                      download
                      className="px-3 py-1.5 rounded-lg bg-brand-primary text-white text-xs font-bold hover:bg-brand-primary-dark flex items-center gap-1 shadow-2xs"
                    >
                      <span className="material-symbols-outlined text-[15px]">download</span>
                      PDF
                    </a>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
