import React, { useState } from 'react';
import { addTankerReading } from '../../services/api';

export default function ManualReadingModal({ tankers = [], initialTankerId, onClose, onReadingAdded }) {
  const [selectedId, setSelectedId] = useState(initialTankerId || tankers[0]?.id || '');
  const activeTanker = tankers.find((t) => t.id === selectedId) || tankers[0];

  const [formData, setFormData] = useState({
    pH: activeTanker?.measurements?.pH ?? 7.2,
    TDS: activeTanker?.measurements?.TDS ?? 350,
    Turbidity: activeTanker?.measurements?.Turbidity ?? 2.5,
    Temperature: activeTanker?.measurements?.Temperature ?? 22.0,
    EC: activeTanker?.measurements?.EC ?? 480,
    Dissolved_Oxygen: activeTanker?.measurements?.Dissolved_Oxygen ?? 6.5,
    Chloramines: activeTanker?.measurements?.Chloramines ?? 2.1,
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Sync initial measurements if user changes tanker in dropdown
  const handleTankerChange = (newId) => {
    setSelectedId(newId);
    const t = tankers.find((item) => item.id === newId);
    if (t?.measurements) {
      setFormData({
        pH: t.measurements.pH ?? 7.2,
        TDS: t.measurements.TDS ?? 350,
        Turbidity: t.measurements.Turbidity ?? 2.5,
        Temperature: t.measurements.Temperature ?? 22.0,
        EC: t.measurements.EC ?? 480,
        Dissolved_Oxygen: t.measurements.Dissolved_Oxygen ?? 6.5,
        Chloramines: t.measurements.Chloramines ?? 2.1,
      });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedId) {
      setError('Please select a water tanker.');
      return;
    }

    const pHVal = parseFloat(formData.pH);
    if (isNaN(pHVal) || pHVal < 0 || pHVal > 14) {
      setError('pH must be between 0.0 and 14.0.');
      return;
    }

    const tdsVal = parseFloat(formData.TDS);
    if (isNaN(tdsVal) || tdsVal < 0) {
      setError('TDS must be a positive number.');
      return;
    }

    const turbVal = parseFloat(formData.Turbidity);
    if (isNaN(turbVal) || turbVal < 0) {
      setError('Turbidity cannot be negative.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload = {
        pH: pHVal,
        TDS: tdsVal,
        Turbidity: turbVal,
        Temperature: parseFloat(formData.Temperature) || 22.0,
        EC: parseFloat(formData.EC) || 500.0,
        Dissolved_Oxygen: parseFloat(formData.Dissolved_Oxygen) || 6.5,
        Chloramines: parseFloat(formData.Chloramines) || 2.0,
      };

      const updatedTanker = await addTankerReading(selectedId, payload);
      onReadingAdded(updatedTanker);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to record manual reading.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-brand-dark/50 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto animate-in fade-in duration-200">
      <div className="bg-brand-surface rounded-2xl max-w-md w-full border border-brand-silver/70 shadow-2xl p-6">
        <div className="flex items-center justify-between pb-3 border-b border-brand-silver/40">
          <div>
            <span className="font-tech-code text-xs text-brand-primary font-bold">
              LABORATORY INFLUX
            </span>
            <h3 className="text-lg font-bold text-brand-dark">Log Manual Field Reading</h3>
          </div>
          <button 
            onClick={onClose} 
            className="text-brand-charcoal hover:text-brand-dark p-1 rounded-lg hover:bg-brand-surfaceAlt"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4 text-xs">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl">
              {error}
            </div>
          )}

          <div>
            <label className="font-bold text-brand-dark block mb-1">Target Water Tanker</label>
            <select
              value={selectedId}
              onChange={(e) => handleTankerChange(e.target.value)}
              className="w-full p-2.5 rounded-xl border border-brand-silver bg-brand-surface text-brand-dark font-medium focus:ring-1 focus:ring-brand-primary"
            >
              {tankers.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.id} — {t.name} ({t.city})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="font-bold text-brand-dark block mb-1">pH Level (0.0 - 14.0)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                max="14"
                required
                value={formData.pH}
                onChange={(e) => setFormData({ ...formData, pH: e.target.value })}
                className="w-full p-2 rounded-xl border border-brand-silver bg-brand-surface font-mono-data text-xs"
              />
            </div>
            <div>
              <label className="font-bold text-brand-dark block mb-1">TDS (mg/L)</label>
              <input
                type="number"
                step="1"
                min="0"
                required
                value={formData.TDS}
                onChange={(e) => setFormData({ ...formData, TDS: e.target.value })}
                className="w-full p-2 rounded-xl border border-brand-silver bg-brand-surface font-mono-data text-xs"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="font-bold text-brand-dark block mb-1">Turbidity (NTU)</label>
              <input
                type="number"
                step="0.1"
                min="0"
                required
                value={formData.Turbidity}
                onChange={(e) => setFormData({ ...formData, Turbidity: e.target.value })}
                className="w-full p-2 rounded-xl border border-brand-silver bg-brand-surface font-mono-data text-xs"
              />
            </div>
            <div>
              <label className="font-bold text-brand-dark block mb-1">Temperature (°C)</label>
              <input
                type="number"
                step="0.1"
                required
                value={formData.Temperature}
                onChange={(e) => setFormData({ ...formData, Temperature: e.target.value })}
                className="w-full p-2 rounded-xl border border-brand-silver bg-brand-surface font-mono-data text-xs"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2">
            <div>
              <label className="text-[10px] text-brand-charcoal font-bold block mb-1">EC (µS/cm)</label>
              <input
                type="number"
                step="1"
                value={formData.EC}
                onChange={(e) => setFormData({ ...formData, EC: e.target.value })}
                className="w-full p-1.5 rounded-lg border border-brand-silver bg-brand-surface font-mono-data text-xs"
              />
            </div>
            <div>
              <label className="text-[10px] text-brand-charcoal font-bold block mb-1">DO (mg/L)</label>
              <input
                type="number"
                step="0.1"
                value={formData.Dissolved_Oxygen}
                onChange={(e) => setFormData({ ...formData, Dissolved_Oxygen: e.target.value })}
                className="w-full p-1.5 rounded-lg border border-brand-silver bg-brand-surface font-mono-data text-xs"
              />
            </div>
            <div>
              <label className="text-[10px] text-brand-charcoal font-bold block mb-1">Chloramines</label>
              <input
                type="number"
                step="0.1"
                value={formData.Chloramines}
                onChange={(e) => setFormData({ ...formData, Chloramines: e.target.value })}
                className="w-full p-1.5 rounded-lg border border-brand-silver bg-brand-surface font-mono-data text-xs"
              />
            </div>
          </div>

          <div className="p-3 bg-brand-surfaceAlt rounded-xl border border-brand-silver/50 text-[11px] text-brand-charcoal">
            Logging this reading automatically recalculates the Water Quality Index (WQI), logs an audit trail event, and appends to the tanker&apos;s historical telemetry graph.
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
                  <span className="inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                  Recording...
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[16px]">save</span>
                  Record Reading
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

