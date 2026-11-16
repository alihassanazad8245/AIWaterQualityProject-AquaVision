import React from 'react';
import { getReportPdfUrl } from '../../services/api';

export default function ReportPreviewModal({ report, onClose }) {
  if (!report) return null;

  // Defensive parsing in case structured_data is stored as a JSON string
  let structured = report.structured_data;
  if (typeof structured === 'string') {
    try {
      structured = JSON.parse(structured);
    } catch {
      structured = {};
    }
  }
  structured = structured || {};

  const parameters = Array.isArray(structured.parameters) ? structured.parameters : [];
  const ml = structured.ml_evaluation || {};
  const forecast = Array.isArray(structured.forecast) ? structured.forecast : [];
  const recs = Array.isArray(structured.recommendations) ? structured.recommendations : [];
  const violations = Array.isArray(structured.violations) ? structured.violations : [];
  const pdfUrl = getReportPdfUrl(report.id);

  // Normalize class probabilities whether array of dicts, simple dict, or list of tuples
  let classProbs = [];
  if (ml.class_probabilities) {
    if (Array.isArray(ml.class_probabilities)) {
      classProbs = ml.class_probabilities.map((item, idx) => {
        if (item && typeof item === 'object') {
          const name = item.class_name || item.name || item.label || `Class ${idx + 1}`;
          const val = item.probability !== undefined ? item.probability : item.prob;
          const display = typeof val === 'number' 
            ? `${(val <= 1 ? val * 100 : val).toFixed(1)}%` 
            : String(val || '0%');
          return { name, display };
        }
        return { name: `Tier ${idx + 1}`, display: String(item) };
      });
    } else if (typeof ml.class_probabilities === 'object') {
      classProbs = Object.entries(ml.class_probabilities).map(([k, v]) => ({
        name: k,
        display: typeof v === 'number' ? `${(v <= 1 ? v * 100 : v).toFixed(1)}%` : String(v),
      }));
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-brand-dark/50 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto animate-in fade-in duration-200">
      <div className="bg-brand-surface rounded-2xl max-w-4xl w-full max-h-[90vh] border border-brand-silver/80 shadow-2xl flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="p-5 sm:p-6 border-b border-brand-silver/40 flex items-center justify-between bg-brand-surface sticky top-0 z-10">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-tech-code text-xs text-brand-primary font-bold">
                AQUAVISION AI WATER QUALITY LAB
              </span>
              <span className="text-brand-silver">•</span>
              <span className="font-tech-code text-xs text-brand-charcoal">
                REPORT #{report.id}
              </span>
            </div>
            <h2 className="text-lg sm:text-xl font-extrabold text-brand-dark">{report.title || 'Water Quality Comprehensive Audit'}</h2>
          </div>

          <div className="flex items-center gap-2.5">
            <a
              href={pdfUrl}
              download
              className="flex items-center gap-1.5 px-3.5 py-2 bg-brand-primary hover:bg-brand-primary-dark text-white rounded-xl text-xs font-bold shadow-sm transition-all"
            >
              <span className="material-symbols-outlined text-[18px]">download</span>
              <span>Download PDF</span>
            </a>
            <button
              onClick={onClose}
              className="p-2 rounded-xl text-brand-charcoal hover:text-brand-dark hover:bg-brand-surfaceAlt transition-colors"
              title="Close Preview"
            >
              <span className="material-symbols-outlined text-[22px]">close</span>
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-5 sm:p-6 overflow-y-auto space-y-6 text-brand-dark text-xs leading-relaxed">
          {/* Metadata Banner */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-brand-surfaceAlt border border-brand-silver/60">
            <div>
              <span className="text-brand-charcoal uppercase text-[10px] font-bold block mb-0.5">Water Source / Tanker</span>
              <span className="font-bold text-sm text-brand-dark">{report.tanker_id || 'Unknown Tanker'}</span>
            </div>
            <div>
              <span className="text-brand-charcoal uppercase text-[10px] font-bold block mb-0.5">Location</span>
              <span className="font-bold text-sm text-brand-dark">
                {report.city ? `${report.city}, ${report.province || 'Pakistan'}` : 'Pakistan Standards Basin'}
              </span>
            </div>
            <div>
              <span className="text-brand-charcoal uppercase text-[10px] font-bold block mb-0.5">Calculated WQI Score</span>
              <span className="font-mono-data font-bold text-base text-brand-primary">
                {report.wqi_score !== null && report.wqi_score !== undefined ? report.wqi_score : 'N/A'}
              </span>
            </div>
            <div>
              <span className="text-brand-charcoal uppercase text-[10px] font-bold block mb-0.5">NSDWQ Verdict</span>
              <span className={`inline-flex px-2 py-0.5 rounded-full text-[11px] font-bold ${
                String(report.status || '').toLowerCase().includes('safe') || String(report.status || '').toLowerCase().includes('verified')
                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                  : String(report.status || '').toLowerCase().includes('observation')
                  ? 'bg-brand-warning text-brand-dark border border-amber-300'
                  : 'bg-rose-100 text-rose-800 border border-rose-300'
              }`}>
                {report.status || 'Verified Safe'}
              </span>
            </div>
          </div>

          {/* Machine Learning Pipeline Insights */}
          <div className="p-5 rounded-xl bg-brand-secondary/20 border border-brand-secondary/50 space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-tech-code text-xs font-bold text-brand-primary uppercase">
                Machine Learning Pipeline Inference
              </span>
              <span className="text-[11px] font-semibold text-brand-charcoal">
                Ensemble: Gradient Boosting + CatBoost + ARIMA
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-1">
              <div className="bg-brand-surface p-3 rounded-lg border border-brand-silver/50">
                <span className="text-brand-charcoal text-[11px] font-medium block">Classification Tier:</span>
                <span className="font-bold text-base text-brand-dark">{ml.predicted_class || report.quality_class || 'Good'}</span>
              </div>
              <div className="bg-brand-surface p-3 rounded-lg border border-brand-silver/50">
                <span className="text-brand-charcoal text-[11px] font-medium block">Regression WQI Index:</span>
                <span className="font-mono-data font-bold text-base text-brand-primary">
                  {ml.wqi_calculated !== undefined ? ml.wqi_calculated : report.wqi_score}
                </span>
              </div>
              <div className="bg-brand-surface p-3 rounded-lg border border-brand-silver/50">
                <span className="text-brand-charcoal text-[11px] font-medium block">Limit Violations Detected:</span>
                <span className={`font-bold text-base ${violations.length > 0 ? 'text-rose-600' : 'text-emerald-700'}`}>
                  {violations.length} {violations.length === 1 ? 'Parameter' : 'Parameters'}
                </span>
              </div>
            </div>

            {/* Class Probabilities Bar */}
            {classProbs.length > 0 && (
              <div className="pt-2">
                <span className="text-[11px] font-bold text-brand-charcoal block mb-1.5">Class Probability Distribution:</span>
                <div className="flex gap-2 flex-wrap font-mono-data text-[11px]">
                  {classProbs.map((p, idx) => (
                    <span key={idx} className="px-2 py-1 bg-brand-surface rounded border border-brand-silver/50">
                      <strong>{p.name}:</strong> {p.display}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Measured Parameters Table vs Pakistan NSDWQ Standards */}
          {parameters.length > 0 && (
            <div>
              <h3 className="text-sm font-bold text-brand-dark mb-2 flex items-center justify-between">
                <span>Measured Telemetry vs. Pakistan NSDWQ & WHO Standards</span>
                <span className="font-tech-code text-[11px] text-brand-charcoal font-normal">
                  {parameters.length} Parameters Evaluated
                </span>
              </h3>

              <div className="overflow-x-auto rounded-xl border border-brand-silver/60">
                <table className="w-full text-left text-xs">
                  <thead className="bg-brand-primary text-white font-tech-code text-[11px]">
                    <tr>
                      <th className="py-2.5 px-4">PARAMETER</th>
                      <th className="py-2.5 px-4">MEASURED VALUE</th>
                      <th className="py-2.5 px-4">UNIT</th>
                      <th className="py-2.5 px-4">NSDWQ LIMIT</th>
                      <th className="py-2.5 px-4 text-right">COMPLIANCE</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-brand-silver/30 font-medium">
                    {parameters.map((p, idx) => (
                      <tr key={idx} className={idx % 2 === 0 ? 'bg-brand-surface' : 'bg-brand-surfaceAlt/40'}>
                        <td className="py-2 px-4 font-bold text-brand-dark">{p.parameter}</td>
                        <td className="py-2 px-4 font-mono-data font-bold text-brand-primary">{p.value}</td>
                        <td className="py-2 px-4 font-tech-code text-brand-charcoal">{p.unit}</td>
                        <td className="py-2 px-4 font-mono-data">{p.standard}</td>
                        <td className="py-2 px-4 text-right">
                          <span className={`px-2 py-0.5 rounded font-tech-code text-[10px] font-bold ${
                            p.verdict === 'PASSED'
                              ? 'bg-emerald-100 text-emerald-800'
                              : p.verdict === 'BORDERLINE'
                              ? 'bg-brand-warning text-brand-dark border border-amber-300'
                              : 'bg-rose-100 text-rose-800 font-bold'
                          }`}>
                            {p.verdict || 'PASSED'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 5-Year ARIMA Forecast Table */}
          {forecast.length > 0 && (
            <div className="p-4 rounded-xl bg-brand-surfaceAlt border border-brand-silver/50">
              <h4 className="font-bold text-xs text-brand-dark mb-1">5-Year Historical Risk-Score Projection (ARIMA Population Forecast)</h4>
              <p className="text-[11px] text-brand-charcoal mb-3">Model-projected multi-year baseline risk index based on regional telemetry trends:</p>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                {forecast.map((step, idx) => {
                  const val = step.forecast !== undefined 
                    ? step.forecast 
                    : (step.predicted_risk_score !== undefined 
                        ? step.predicted_risk_score 
                        : (step.predicted_wqi !== undefined ? step.predicted_wqi : step.predicted_value));
                  const displayVal = typeof val === 'number' ? val.toFixed(2) : String(val || 'N/A');
                  return (
                    <div key={idx} className="bg-brand-surface p-2.5 rounded-lg border border-brand-silver/40 text-center">
                      <span className="font-tech-code text-[10px] text-brand-charcoal block">YEAR {step.step || step.year || idx + 1}</span>
                      <span className="font-mono-data font-bold text-sm text-brand-primary">
                        {displayVal}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* AI Clinical & Diagnostic Observations */}
          <div>
            <h3 className="text-sm font-bold text-brand-dark mb-2">AI Diagnostic Observations</h3>
            <div className="p-4 rounded-xl bg-brand-surfaceAlt border border-brand-silver/60 text-brand-dark leading-relaxed whitespace-pre-line text-xs font-sans">
              {report.narrative || structured.narrative || 'Detailed parameter assessment completed. Water quality readings meet regulatory requirements for general consumption.'}
            </div>
          </div>

          {/* Prioritized Engineering Recommendations */}
          {recs.length > 0 && (
            <div>
              <h3 className="text-sm font-bold text-brand-dark mb-2">Prioritized Engineering Remediation Plans</h3>
              <div className="space-y-2">
                {recs.map((r, idx) => (
                  <div key={idx} className="p-3 rounded-xl bg-brand-secondary/30 border border-brand-secondary/60 flex items-start gap-2.5">
                    <span className="w-5 h-5 rounded-full bg-brand-primary text-white font-bold text-[10px] flex items-center justify-center flex-shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <div>
                      <strong className="text-brand-dark">{r.parameter}:</strong>{' '}
                      <span className="text-brand-charcoal">{r.action}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Research & Sensor Disclaimer */}
          <div className="pt-3 border-t border-brand-silver/40 text-[11px] text-brand-charcoal italic">
            <strong>Research & Demonstration Notice:</strong> Telemetry marked DEMO DATA reflects simulated physical IoT sensors.
            Predictions are screening estimates generated by machine learning models and do not replace certified laboratory testing.
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-brand-silver/40 bg-brand-surfaceAlt flex items-center justify-between">
          <div className="font-tech-code text-[11px] text-brand-charcoal">
            Generated: {report.created_at ? new Date(report.created_at).toLocaleString() : 'Recent'}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-brand-charcoal hover:text-brand-dark hover:bg-brand-surface"
            >
              Close
            </button>
            <a
              href={pdfUrl}
              download
              className="px-4 py-2 rounded-xl text-xs font-bold bg-brand-primary hover:bg-brand-primary-dark text-white flex items-center gap-1.5 shadow-sm"
            >
              <span className="material-symbols-outlined text-[16px]">download</span>
              Download PDF
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
