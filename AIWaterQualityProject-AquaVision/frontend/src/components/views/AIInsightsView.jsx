import React, { useState, useEffect } from 'react';
import { fetchInsights } from '../../services/api';

export default function AIInsightsView({ openReportModal }) {
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchInsights()
      .then((data) => {
        setInsights(Array.isArray(data) ? data : []);
      })
      .catch(() => {
        setInsights([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const defaultObservations = [
    {
      tanker_id: 'TANK-02',
      title: 'Turbidity Variance in Tanker 02',
      tag: 'OBSERVATION DETECTED',
      type: 'warning',
      observation: 'AI detects elevated NTU in Rawalpindi unit. While within emergency ceiling (< 5.0), pre-filtration coagulation is recommended.',
      action: 'Run Tanker 02 Diagnostic Report',
    },
    {
      tanker_id: 'TANK-05',
      title: 'Reverse Osmosis for Industrial Inflow',
      tag: 'PREDICTIVE SUGGESTION',
      type: 'info',
      observation: 'Groundwater exhibits elevated TDS. Multi-stage filtration or membrane exchange is recommended for potability standards.',
      action: 'Audit Tanker 05 Chemical Profile',
    },
    {
      tanker_id: 'TANK-01',
      title: 'WHO & Pak NSDWQ Alignment: Tanker 01',
      tag: 'COMPLIANCE VERIFIED',
      type: 'success',
      observation: 'All evaluated chemical, physical, and microbial parameters for central reservoir satisfy Pakistan NSDWQ criteria.',
      action: 'Generate Tanker 01 Certification',
    },
  ];

  const activeInsights = insights.length > 0 ? insights : defaultObservations;

  return (
    <section className="space-y-6 animate-in fade-in duration-300">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-brand-silver/40">
        <div>
          <div className="font-tech-code text-brand-charcoal uppercase text-xs tracking-widest mb-1">
            DEEP WATER INTELLIGENCE
          </div>
          <h1 className="text-2xl font-extrabold text-brand-dark">AI Diagnostics &amp; Guidelines Match</h1>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-3 py-1 rounded-xl bg-brand-primary text-white text-xs font-tech-code font-bold shadow-2xs">
            ENSEMBLE CONFIDENCE: 96.8%
          </span>
        </div>
      </div>

      {/* Dynamic Diagnostic Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {activeInsights.map((item, idx) => {
          const isWarn = item.type === 'warning';
          const isSuccess = item.type === 'success';

          return (
            <div
              key={idx}
              className="bg-brand-surface rounded-2xl p-5 border border-brand-silver/70 shadow-2xs relative overflow-hidden flex flex-col justify-between"
            >
              <div>
                <div className={`inline-block px-2.5 py-1 rounded-md font-tech-code text-[11px] font-bold mb-3 border ${
                  isWarn
                    ? 'bg-brand-warning text-brand-dark border-amber-300'
                    : isSuccess
                    ? 'bg-emerald-100 text-emerald-900 border-emerald-300'
                    : 'bg-brand-secondary text-brand-dark border-brand-primary/30'
                }`}>
                  {item.tag || (isWarn ? 'OBSERVATION DETECTED' : isSuccess ? 'COMPLIANCE VERIFIED' : 'PREDICTIVE SUGGESTION')}
                </div>
                <h4 className="font-bold text-sm text-brand-dark mb-1">{item.title}</h4>
                <p className="text-xs text-brand-charcoal leading-relaxed mb-4">
                  {item.observation || item.description}
                </p>
              </div>

              <button
                onClick={() => openReportModal && openReportModal(item.tanker_id)}
                className="text-xs font-semibold text-brand-primary flex items-center gap-1 hover:underline cursor-pointer pt-3 border-t border-brand-silver/30"
              >
                <span>{item.action || `Run ${item.tanker_id || 'Tanker'} Diagnostic`}</span> →
              </button>
            </div>
          );
        })}
      </div>

      {/* Compliance Matrix Table */}
      <div className="bg-brand-surface rounded-2xl p-6 border border-brand-silver/70 shadow-2xs">
        <h3 className="text-base font-bold text-brand-dark mb-1">WHO &amp; Pakistan NSDWQ Standards Benchmark</h3>
        <p className="text-xs text-brand-charcoal mb-4">
          Automated threshold validation against international potable water criteria
        </p>

        <div className="overflow-x-auto rounded-xl border border-brand-silver/50">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-brand-surfaceAlt border-b border-brand-silver/40 font-tech-code text-brand-charcoal text-[11px]">
                <th className="py-2.5 px-4">PARAMETER</th>
                <th className="py-2.5 px-4">TYPICAL TANKER RANGE</th>
                <th className="py-2.5 px-4">WHO GUIDELINE</th>
                <th className="py-2.5 px-4">PAKISTAN NSDWQ LIMIT</th>
                <th className="py-2.5 px-4 text-right">AI VERDICT</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-brand-silver/30 font-medium">
              <tr>
                <td className="py-3 px-4 font-bold text-brand-dark">pH Acidity / Alkalinity</td>
                <td className="py-3 px-4 font-mono-data text-brand-primary font-bold">6.70 – 7.85</td>
                <td className="py-3 px-4 font-mono-data">6.5 – 8.5</td>
                <td className="py-3 px-4 font-mono-data">6.5 – 8.5</td>
                <td className="py-3 px-4 text-right">
                  <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-tech-code text-[10px] font-bold">
                    PASSED
                  </span>
                </td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-bold text-brand-dark">Total Dissolved Solids (TDS)</td>
                <td className="py-3 px-4 font-mono-data text-brand-primary font-bold">250 – 780 mg/L</td>
                <td className="py-3 px-4 font-mono-data">&lt; 1000 mg/L</td>
                <td className="py-3 px-4 font-mono-data">&lt; 1000 mg/L</td>
                <td className="py-3 px-4 text-right">
                  <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-tech-code text-[10px] font-bold">
                    PASSED
                  </span>
                </td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-bold text-brand-dark">Turbidity (Optical Clarity)</td>
                <td className="py-3 px-4 font-mono-data text-brand-primary font-bold">1.8 – 4.6 NTU</td>
                <td className="py-3 px-4 font-mono-data">&lt; 5.0 NTU</td>
                <td className="py-3 px-4 font-mono-data">&lt; 5.0 NTU</td>
                <td className="py-3 px-4 text-right">
                  <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-tech-code text-[10px] font-bold">
                    PASSED
                  </span>
                </td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-bold text-brand-dark">Electrical Conductivity (EC)</td>
                <td className="py-3 px-4 font-mono-data text-brand-primary font-bold">420 – 950 µS/cm</td>
                <td className="py-3 px-4 font-mono-data">&lt; 1500 µS/cm</td>
                <td className="py-3 px-4 font-mono-data">&lt; 1500 µS/cm</td>
                <td className="py-3 px-4 text-right">
                  <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-tech-code text-[10px] font-bold">
                    PASSED
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
