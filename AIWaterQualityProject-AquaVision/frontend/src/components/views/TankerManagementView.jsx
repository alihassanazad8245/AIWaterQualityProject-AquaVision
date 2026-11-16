import React, { useState } from 'react';
import { deleteTanker } from '../../services/api';

export default function TankerManagementView({
  tankers = [],
  onOpenAddTanker,
  onOpenManualReading,
  onOpenGenerateReport,
  onTankerDeleted,
  onSelectTanker,
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [deletingId, setDeletingId] = useState(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);
  const [deleteError, setDeleteError] = useState(null);

  const filteredTankers = tankers.filter((t) => {
    const matchesSearch =
      t.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.city.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus =
      statusFilter === 'ALL' || t.status.toLowerCase() === statusFilter.toLowerCase();
    return matchesSearch && matchesStatus;
  });

  const handleDelete = async (id) => {
    setDeletingId(id);
    setDeleteError(null);
    try {
      await deleteTanker(id);
      setDeleteConfirmId(null);
      if (onTankerDeleted) onTankerDeleted(id);
    } catch (err) {
      setDeleteError(err.message || 'Failed to delete tanker.');
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Top Header & Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-brand-surface p-5 sm:p-6 rounded-2xl border border-brand-silver/60 shadow-xs">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-tech-code text-xs text-brand-primary font-bold">
              FLEET &amp; WATER ASSETS
            </span>
            <span className="text-brand-silver">•</span>
            <span className="font-tech-code text-xs text-brand-charcoal">
              {tankers.length} Active Tankers
            </span>
          </div>
          <h2 className="text-xl font-extrabold text-brand-dark">Tanker Fleet Management</h2>
          <p className="text-xs text-brand-charcoal mt-0.5">
            Register new distribution tankers, log calibrated field telemetry, and manage municipal water units.
          </p>
        </div>

        <div className="flex items-center gap-2.5 flex-wrap">
          <button
            onClick={onOpenManualReading}
            className="px-3.5 py-2 bg-brand-surfaceAlt hover:bg-brand-secondary/30 text-brand-dark border border-brand-silver/70 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5"
          >
            <span className="material-symbols-outlined text-[18px] text-brand-primary">edit_note</span>
            <span>Log Field Reading</span>
          </button>
          <button
            onClick={onOpenAddTanker}
            className="px-4 py-2 bg-brand-primary hover:bg-brand-primary-dark text-white rounded-xl text-xs font-bold transition-all shadow-sm flex items-center gap-1.5"
          >
            <span className="material-symbols-outlined text-[18px]">add</span>
            <span>Register Tanker</span>
          </button>
        </div>
      </div>

      {deleteError && (
        <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs">
          {deleteError}
        </div>
      )}

      {/* Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-brand-surface p-3.5 rounded-xl border border-brand-silver/60">
        <div className="relative w-full sm:w-80">
          <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-brand-charcoal text-[18px]">
            search
          </span>
          <input
            type="text"
            placeholder="Search by ID, name, city..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 rounded-lg border border-brand-silver/70 bg-brand-surfaceAlt text-xs text-brand-dark placeholder-brand-charcoal/60 focus:outline-none focus:ring-1 focus:ring-brand-primary"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <span className="text-[11px] font-bold text-brand-charcoal uppercase">Filter Status:</span>
          <div className="flex items-center gap-1 bg-brand-surfaceAlt p-1 rounded-lg border border-brand-silver/50">
            {['ALL', 'Normal', 'Warning', 'Critical'].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-2.5 py-1 rounded text-[11px] font-bold transition-all ${
                  statusFilter === st
                    ? 'bg-brand-surface text-brand-primary shadow-xs'
                    : 'text-brand-charcoal hover:text-brand-dark'
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Tankers Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredTankers.map((tanker) => {
          const isConfirming = deleteConfirmId === tanker.id;
          const statusLower = tanker.status.toLowerCase();
          const badgeClass =
            statusLower === 'normal'
              ? 'bg-emerald-100 text-emerald-800 border-emerald-200'
              : statusLower === 'warning'
              ? 'bg-amber-100 text-amber-800 border-amber-200'
              : 'bg-rose-100 text-rose-800 border-rose-200';

          return (
            <div
              key={tanker.id}
              className="bg-brand-surface rounded-2xl border border-brand-silver/60 p-5 shadow-xs hover:shadow-md transition-all flex flex-col justify-between"
            >
              <div>
                {/* Tanker Card Header */}
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-tech-code text-xs font-bold text-brand-primary">
                        {tanker.id}
                      </span>
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${badgeClass}`}>
                        {tanker.status}
                      </span>
                    </div>
                    <h3 className="font-bold text-sm text-brand-dark mt-1 leading-snug">
                      {tanker.name}
                    </h3>
                    <p className="text-[11px] text-brand-charcoal mt-0.5">
                      {tanker.city}, {tanker.province} • {tanker.source_type}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] uppercase font-bold text-brand-charcoal block">WQI Score</span>
                    <span className="font-mono-data font-bold text-base text-brand-primary">
                      {tanker.wqi_score}
                    </span>
                  </div>
                </div>

                {/* Telemetry Chips */}
                <div className="grid grid-cols-4 gap-2 p-3 bg-brand-surfaceAlt rounded-xl border border-brand-silver/40 text-center my-3">
                  <div>
                    <span className="text-[10px] text-brand-charcoal block font-medium">pH</span>
                    <span className="font-mono-data font-bold text-xs text-brand-dark">
                      {tanker.measurements?.pH?.toFixed(2) ?? '—'}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-brand-charcoal block font-medium">TDS</span>
                    <span className="font-mono-data font-bold text-xs text-brand-dark">
                      {tanker.measurements?.TDS ?? '—'}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-brand-charcoal block font-medium">Turb</span>
                    <span className="font-mono-data font-bold text-xs text-brand-dark">
                      {tanker.measurements?.Turbidity?.toFixed(1) ?? '—'}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-brand-charcoal block font-medium">Temp</span>
                    <span className="font-mono-data font-bold text-xs text-brand-dark">
                      {tanker.measurements?.Temperature ?? '—'}°C
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between text-[11px] text-brand-charcoal mb-4 px-1">
                  <span>Capacity: <strong className="text-brand-dark">{tanker.capacity_liters?.toLocaleString()} L</strong></span>
                  <span>Readings logged: <strong className="text-brand-dark">{tanker.reading_history?.length || 1}</strong></span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="pt-3 border-t border-brand-silver/40 flex items-center justify-between gap-2">
                {isConfirming ? (
                  <div className="flex items-center gap-2 w-full justify-between animate-in fade-in">
                    <span className="text-[11px] text-rose-600 font-bold">Delete permanently?</span>
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => handleDelete(tanker.id)}
                        disabled={deletingId === tanker.id}
                        className="px-2.5 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-[11px] font-bold"
                      >
                        {deletingId === tanker.id ? 'Deleting...' : 'Yes, Delete'}
                      </button>
                      <button
                        onClick={() => setDeleteConfirmId(null)}
                        className="px-2 py-1 bg-brand-surfaceAlt text-brand-charcoal hover:text-brand-dark rounded-lg text-[11px] font-semibold"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => onSelectTanker && onSelectTanker(tanker.id)}
                        title="View Live Graph & Monitoring"
                        className="p-1.5 rounded-lg bg-brand-surfaceAlt hover:bg-brand-secondary/30 text-brand-dark text-xs font-semibold flex items-center gap-1"
                      >
                        <span className="material-symbols-outlined text-[16px] text-brand-primary">monitoring</span>
                        <span className="hidden sm:inline">Monitor</span>
                      </button>
                      <button
                        onClick={() => onOpenGenerateReport && onOpenGenerateReport(tanker.id)}
                        title="Generate AI Report"
                        className="p-1.5 rounded-lg bg-brand-surfaceAlt hover:bg-brand-secondary/30 text-brand-dark text-xs font-semibold flex items-center gap-1"
                      >
                        <span className="material-symbols-outlined text-[16px] text-brand-primary">description</span>
                        <span className="hidden sm:inline">Report</span>
                      </button>
                    </div>

                    <button
                      onClick={() => setDeleteConfirmId(tanker.id)}
                      title="Delete tanker"
                      className="p-1.5 rounded-lg text-brand-charcoal hover:text-rose-600 hover:bg-rose-50 transition-colors"
                    >
                      <span className="material-symbols-outlined text-[18px]">delete</span>
                    </button>
                  </>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {filteredTankers.length === 0 && (
        <div className="p-12 text-center bg-brand-surface rounded-2xl border border-brand-silver/60">
          <span className="material-symbols-outlined text-4xl text-brand-charcoal/50 mb-2">water_drop</span>
          <h4 className="font-bold text-sm text-brand-dark">No tankers match your filter</h4>
          <p className="text-xs text-brand-charcoal mt-1">Try clearing search terms or register a new tanker above.</p>
        </div>
      )}
    </div>
  );
}

