import React, { useState } from 'react';
import { createTanker } from '../../services/api';

export default function AddTankerModal({ onClose, onTankerCreated }) {
  const [formData, setFormData] = useState({
    id: `TANK-${String(Math.floor(Math.random() * 90) + 10).padStart(2, '0')}`,
    name: '',
    source_type: 'Municipal Supply',
    capacity_liters: 12000,
    city: 'Islamabad',
    province: 'Federal Capital',
    status: 'Normal',
    pH: 7.2,
    TDS: 280,
    Turbidity: 2.1,
    Temperature: 21.5,
    EC: 450,
    Dissolved_Oxygen: 6.8,
    Chloramines: 2.2,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      setError('Please provide a name/location label for the water tanker.');
      return;
    }
    if (!formData.id.trim()) {
      setError('Please provide a unique tanker identifier.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload = {
        id: formData.id.trim().toUpperCase(),
        name: formData.name.trim(),
        source_type: formData.source_type,
        capacity_liters: parseInt(formData.capacity_liters, 10) || 10000,
        city: formData.city.trim(),
        province: formData.province.trim(),
        status: formData.status,
        measurements: {
          pH: parseFloat(formData.pH),
          TDS: parseFloat(formData.TDS),
          Turbidity: parseFloat(formData.Turbidity),
          Temperature: parseFloat(formData.Temperature),
          EC: parseFloat(formData.EC),
          Dissolved_Oxygen: parseFloat(formData.Dissolved_Oxygen),
          Chloramines: parseFloat(formData.Chloramines),
        },
      };

      const result = await createTanker(payload);
      onTankerCreated(result);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to create tanker.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-brand-dark/50 backdrop-blur-xs flex items-center justify-center p-4 overflow-y-auto animate-in fade-in duration-200">
      <div className="bg-brand-surface rounded-2xl max-w-lg w-full max-h-[90vh] border border-brand-silver/70 shadow-2xl p-6 overflow-y-auto">
        <div className="flex items-center justify-between pb-3 border-b border-brand-silver/40">
          <div>
            <span className="font-tech-code text-xs text-brand-primary font-bold">
              FLEET &amp; ASSET MANAGEMENT
            </span>
            <h3 className="text-lg font-bold text-brand-dark">Register New Water Tanker</h3>
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

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="font-bold text-brand-dark block mb-1">Tanker Identifier (ID)</label>
              <input
                type="text"
                required
                value={formData.id}
                onChange={(e) => setFormData({ ...formData, id: e.target.value })}
                placeholder="e.g. TANK-05"
                className="w-full p-2.5 rounded-xl border border-brand-silver bg-brand-surface text-brand-dark font-tech-code uppercase focus:ring-1 focus:ring-brand-primary"
              />
            </div>
            <div>
              <label className="font-bold text-brand-dark block mb-1">Source / Deployment Type</label>
              <select
                value={formData.source_type}
                onChange={(e) => setFormData({ ...formData, source_type: e.target.value })}
                className="w-full p-2.5 rounded-xl border border-brand-silver bg-brand-surface text-brand-dark font-medium focus:ring-1 focus:ring-brand-primary"
              >
                <option value="Municipal Supply">Municipal Supply</option>
                <option value="RO Filtration">RO Filtration Plant</option>
                <option value="Ground Reservoir">Ground Reservoir</option>
                <option value="River Extraction">River Extraction</option>
                <option value="Borehole Well">Borehole Well</option>
              </select>
            </div>
          </div>

          <div>
            <label className="font-bold text-brand-dark block mb-1">Station / Tanker Name</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g. Rawalpindi Cantonment Unit 3"
              className="w-full p-2.5 rounded-xl border border-brand-silver bg-brand-surface text-brand-dark font-medium focus:ring-1 focus:ring-brand-primary"
            />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="font-bold text-brand-dark block mb-1">Capacity (Liters)</label>
              <input
                type="number"
                min="1000"
                step="500"
                value={formData.capacity_liters}
                onChange={(e) => setFormData({ ...formData, capacity_liters: e.target.value })}
                className="w-full p-2 rounded-xl border border-brand-silver bg-brand-surface text-xs"
              />
            </div>
            <div>
              <label className="font-bold text-brand-dark block mb-1">City</label>
              <input
                type="text"
                required
                value={formData.city}
                onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                className="w-full p-2 rounded-xl border border-brand-silver bg-brand-surface text-xs"
              />
            </div>
            <div>
              <label className="font-bold text-brand-dark block mb-1">Province</label>
              <input
                type="text"
                required
                value={formData.province}
                onChange={(e) => setFormData({ ...formData, province: e.target.value })}
                className="w-full p-2 rounded-xl border border-brand-silver bg-brand-surface text-xs"
              />
            </div>
          </div>

          <div className="p-3 bg-brand-surfaceAlt rounded-xl border border-brand-silver/50 space-y-2">
            <span className="font-bold text-brand-dark block">Initial Sensor Telemetry Calibration</span>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              <div>
                <label className="text-[10px] text-brand-charcoal font-bold block mb-0.5">pH (0 - 14)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="14"
                  value={formData.pH}
                  onChange={(e) => setFormData({ ...formData, pH: e.target.value })}
                  className="w-full p-1.5 rounded-lg border border-brand-silver bg-brand-surface font-mono-data text-xs"
                />
              </div>
              <div>
                <label className="text-[10px] text-brand-charcoal font-bold block mb-0.5">TDS (mg/L)</label>
                <input
                  type="number"
                  step="1"
                  min="10"
                  value={formData.TDS}
                  onChange={(e) => setFormData({ ...formData, TDS: e.target.value })}
                  className="w-full p-1.5 rounded-lg border border-brand-silver bg-brand-surface font-mono-data text-xs"
                />
              </div>
              <div>
                <label className="text-[10px] text-brand-charcoal font-bold block mb-0.5">Turbidity (NTU)</label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  value={formData.Turbidity}
                  onChange={(e) => setFormData({ ...formData, Turbidity: e.target.value })}
                  className="w-full p-1.5 rounded-lg border border-brand-silver bg-brand-surface font-mono-data text-xs"
                />
              </div>
              <div>
                <label className="text-[10px] text-brand-charcoal font-bold block mb-0.5">Temp (°C)</label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.Temperature}
                  onChange={(e) => setFormData({ ...formData, Temperature: e.target.value })}
                  className="w-full p-1.5 rounded-lg border border-brand-silver bg-brand-surface font-mono-data text-xs"
                />
              </div>
            </div>
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
                  Registering...
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[16px]">add_circle</span>
                  Register Tanker
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

