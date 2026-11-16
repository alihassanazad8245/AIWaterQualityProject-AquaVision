import React, { useState } from 'react';
import { updateProfile } from '../../services/api';

export default function EditProfileModal({ profile, onClose, onProfileUpdated }) {
  const [formData, setFormData] = useState({
    name: profile?.name || 'Dr. Alweef',
    designation: profile?.designation || 'Chief Water Analyst',
    role: profile?.role || 'Senior Water Safety Director',
    organization: profile?.organization || 'National Water Quality Authority',
    avatar_url: profile?.avatar_url || '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      setError('Please provide a full name.');
      return;
    }
    setLoading(true);
    setError(null);

    try {
      const updated = await updateProfile(formData);
      onProfileUpdated(updated);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to update user profile');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-brand-dark/50 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-200">
      <div className="bg-brand-surface rounded-2xl max-w-md w-full border border-brand-silver/70 shadow-2xl p-6 overflow-hidden">
        <div className="flex items-center justify-between pb-3 border-b border-brand-silver/40">
          <div>
            <span className="font-tech-code text-xs text-brand-primary font-bold">
              USER PREFERENCES
            </span>
            <h3 className="text-lg font-bold text-brand-dark">Edit Research Profile</h3>
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
            <label className="font-bold text-brand-dark block mb-1">Full Name & Title</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g. Dr. Alweef or Ali Hassan"
              className="w-full p-2.5 rounded-xl border border-brand-silver bg-brand-surface text-brand-dark font-medium focus:ring-1 focus:ring-brand-primary focus:border-brand-primary"
            />
          </div>

          <div>
            <label className="font-bold text-brand-dark block mb-1">Designation</label>
            <input
              type="text"
              required
              value={formData.designation}
              onChange={(e) => setFormData({ ...formData, designation: e.target.value })}
              placeholder="e.g. Chief Water Analyst or Lead Researcher"
              className="w-full p-2.5 rounded-xl border border-brand-silver bg-brand-surface text-brand-dark font-medium focus:ring-1 focus:ring-brand-primary focus:border-brand-primary"
            />
          </div>

          <div>
            <label className="font-bold text-brand-dark block mb-1">System Role</label>
            <input
              type="text"
              required
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value })}
              placeholder="e.g. Administrator or Water Quality Analyst"
              className="w-full p-2.5 rounded-xl border border-brand-silver bg-brand-surface text-brand-dark font-medium focus:ring-1 focus:ring-brand-primary focus:border-brand-primary"
            />
          </div>

          <div>
            <label className="font-bold text-brand-dark block mb-1">Organization / Institution</label>
            <input
              type="text"
              required
              value={formData.organization}
              onChange={(e) => setFormData({ ...formData, organization: e.target.value })}
              placeholder="e.g. National Water Quality Authority"
              className="w-full p-2.5 rounded-xl border border-brand-silver bg-brand-surface text-brand-dark font-medium focus:ring-1 focus:ring-brand-primary focus:border-brand-primary"
            />
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
                  Saving...
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[16px]">check</span>
                  Save Profile
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

