import React, { useState } from 'react';
import { generateReport } from '../../services/api';

export default function GenerateReportModal({ tankers = [], initialTankerId, onClose, onReportGenerated }) {
  const [selectedTankerId, setSelectedTankerId] = useState(initialTankerId || tankers[0]?.id || 'TANK-01');
  const [customParams, setCustomParams] = useState({
    pH: '',
    TDS: '',
    Turbidity: '',
    Temperature: '',
  });
  const [useCustomParams, setUseCustomParams] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const selectedTanker = tankers.find((t) => t.id === selectedTankerId) || tankers[0];

  const handleGenerate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      let measurements = null;
      if (useCustomParams && selectedTanker) {
        measurements = { ...selectedTanker.measurements };
        if (customParams.pH) measurements.pH = parseFloat(customParams.pH);
        if (customParams.TDS) measurements.TDS = parseFloat(customParams.TDS);
        if (customParams.Turbidity) measurements.Turbidity = parseFloat(customParams.Turbidity);
        if (customParams.Temperature) measurements.Temperature = parseFloat(customParams.Temperature);
      }

      const report = await generateReport(
        selectedTankerId,
        measurements,
        `Generate comprehensive water quality report for ${selectedTanker?.name || selectedTankerId}`,
        'user-session'
      );

      setLoading(false);
      onReportGenerated(report);
      onClose();
    } catch (err) {
      setLoading(false);
      setError(err.message || 'Failed to generate report');
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-brand-dark/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-brand-surface rounded-2xl max-w-lg w-full border border-brand-silver/70 shadow-2xl p-6 animate-in fade-in">
        <div className="flex items-center justify-between pb-3 border-b border-brand-silver/40">
          <div>
            <span className="font-tech-code text-xs text-brand-primary font-bold">
              AQUAVISION DOCUMENTATION
            </span>
            <h3 className="text-lg font-bold text-brand-dark">Generate Laboratory Report</h3>
          </div>
          <button onClick={onClose} className="text-brand-charcoal hover:text-brand-dark">
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        <form onSubmit={handleGenerate} className="my-4 space-y-4 text-xs">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl">
              {error}
            </div>
          )}

          <div>
            <label className="font-bold text-brand-dark block mb-1">Target Water Source / Tanker</label>
            <select
              value={selectedTankerId}
              onChange={(e) => setSelectedTankerId(e.target.value)}
              className="w-full p-2.5 rounded-xl border border-brand-silver bg-brand-surface text-brand-dark font-medium focus:ring-1 focus:ring-brand-primary"
            >
              {tankers.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.id} — {t.name} ({t.source_type}, {t.city})
                </option>
              ))}
            </select>
          </div>

          {selectedTanker && (
            <div className="p-3 bg-brand-surfaceAlt rounded-xl border border-brand-silver/50 space-y-1.5">
              <span className="font-bold text-brand-dark block">Current Live Telemetry:</span>
              <div className="grid grid-cols-4 gap-2 font-mono-data text-[11px] text-brand-charcoal">
                <div>pH: <strong className="text-brand-primary">{selectedTanker.measurements.pH}</strong></div>
                <div>TDS: <strong className="text-brand-primary">{selectedTanker.measurements.TDS}</strong></div>
                <div>Turb: <strong className="text-brand-primary">{selectedTanker.measurements.Turbidity}</strong></div>
                <div>Temp: <strong className="text-brand-primary">{selectedTanker.measurements.Temperature}°C</strong></div>
              </div>
            </div>
          )}

          <div>
            <label className="flex items-center gap-2 cursor-pointer font-semibold text-brand-dark">
              <input
                type="checkbox"
                checked={useCustomParams}
                onChange={(e) => setUseCustomParams(e.target.checked)}
                className="rounded text-brand-primary focus:ring-brand-primary"
              />
              <span>Override with custom test parameters (optional)</span>
            </label>

            {useCustomParams && (
              <div className="grid grid-cols-2 gap-3 mt-3 p-3 bg-brand-surfaceAlt/60 rounded-xl border border-brand-silver/40">
                <div>
                  <label className="text-[11px] font-medium text-brand-charcoal block mb-1">pH</label>
                  <input
                    type="number"
                    step="0.01"
                    placeholder={selectedTanker?.measurements.pH}
                    value={customParams.pH}
                    onChange={(e) => setCustomParams({ ...customParams, pH: e.target.value })}
                    className="w-full p-2 rounded-lg border border-brand-silver bg-brand-surface text-xs"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-medium text-brand-charcoal block mb-1">TDS (mg/L)</label>
                  <input
                    type="number"
                    step="1"
                    placeholder={selectedTanker?.measurements.TDS}
                    value={customParams.TDS}
                    onChange={(e) => setCustomParams({ ...customParams, TDS: e.target.value })}
                    className="w-full p-2 rounded-lg border border-brand-silver bg-brand-surface text-xs"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-medium text-brand-charcoal block mb-1">Turbidity (NTU)</label>
                  <input
                    type="number"
                    step="0.1"
                    placeholder={selectedTanker?.measurements.Turbidity}
                    value={customParams.Turbidity}
                    onChange={(e) => setCustomParams({ ...customParams, Turbidity: e.target.value })}
                    className="w-full p-2 rounded-lg border border-brand-silver bg-brand-surface text-xs"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-medium text-brand-charcoal block mb-1">Temperature (°C)</label>
                  <input
                    type="number"
                    step="0.1"
                    placeholder={selectedTanker?.measurements.Temperature}
                    value={customParams.Temperature}
                    onChange={(e) => setCustomParams({ ...customParams, Temperature: e.target.value })}
                    className="w-full p-2 rounded-lg border border-brand-silver bg-brand-surface text-xs"
                  />
                </div>
              </div>
            )}
          </div>

          <div className="p-3 bg-brand-secondary/30 rounded-xl border border-brand-secondary text-[11px]">
            <span className="font-bold text-brand-dark">AI Pipeline:</span> Runs full LangGraph workflow, evaluates Pakistan NSDWQ &amp; WHO standards, and computes CatBoost WQI.
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-brand-silver/40">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-brand-charcoal hover:text-brand-dark"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 rounded-xl text-xs font-bold bg-brand-primary text-white hover:bg-brand-primary-dark transition-all shadow-sm flex items-center gap-1.5"
            >
              {loading ? (
                <>
                  <span className="inline-block w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  Processing AI Report...
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[16px]">description</span>
                  Generate &amp; Preview
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

