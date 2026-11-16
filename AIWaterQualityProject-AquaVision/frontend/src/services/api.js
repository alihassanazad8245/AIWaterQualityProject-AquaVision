/**
 * AquaVision Comprehensive API Client
 */

const API_BASE = '/api';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

// ==================== TANKERS ====================

export async function fetchTankers() {
  const res = await fetch(`${API_BASE}/tankers`);
  if (!res.ok) throw new Error('Failed to fetch tankers');
  return res.json();
}

export async function fetchTanker(id) {
  const res = await fetch(`${API_BASE}/tankers/${encodeURIComponent(id)}`);
  if (!res.ok) throw new Error(`Failed to fetch tanker ${id}`);
  return res.json();
}

export async function createTanker(data) {
  const res = await fetch(`${API_BASE}/tankers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to create tanker');
  }
  return res.json();
}

export async function updateTanker(id, data) {
  const res = await fetch(`${API_BASE}/tankers/${encodeURIComponent(id)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to update tanker ${id}`);
  }
  return res.json();
}

export async function deleteTanker(id) {
  const res = await fetch(`${API_BASE}/tankers/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to delete tanker ${id}`);
  }
  return res.json();
}

export async function addTankerReading(id, measurements) {
  const res = await fetch(`${API_BASE}/tankers/${encodeURIComponent(id)}/reading`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(measurements),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to record sensor reading');
  }
  return res.json();
}

// ==================== CHAT & COPILOT ====================

export async function sendChatMessage(message, sessionId = 'default-session', tankerId = null, contextMode = 'overall') {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      tanker_id: tankerId,
      context_mode: contextMode,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Chat request failed');
  }
  return res.json();
}

// ==================== REPORTS ====================

export async function generateReport(tankerId, measurements = null, query = null, sessionId = 'default-session') {
  const res = await fetch(`${API_BASE}/reports/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      tanker_id: tankerId,
      measurements,
      query,
      session_id: sessionId,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Report generation failed');
  }
  return res.json();
}

export async function fetchReports(limit = 50) {
  const res = await fetch(`${API_BASE}/reports?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch reports');
  return res.json();
}

export async function fetchReport(id) {
  const res = await fetch(`${API_BASE}/reports/${encodeURIComponent(id)}`);
  if (!res.ok) throw new Error(`Failed to fetch report ${id}`);
  return res.json();
}

export function getReportPdfUrl(reportId) {
  return `${API_BASE}/reports/${encodeURIComponent(reportId)}/pdf`;
}

// ==================== DYNAMIC ANALYTICS & INSIGHTS ====================

export async function fetchAnalytics() {
  const res = await fetch(`${API_BASE}/analytics`);
  if (!res.ok) throw new Error('Failed to fetch analytics');
  return res.json();
}

export async function fetchInsights() {
  const res = await fetch(`${API_BASE}/insights`);
  if (!res.ok) throw new Error('Failed to fetch insights');
  return res.json();
}

// ==================== PROFILE & ACTIVITY ====================

export async function fetchProfile() {
  const res = await fetch(`${API_BASE}/profile`);
  if (!res.ok) throw new Error('Failed to fetch user profile');
  return res.json();
}

export async function updateProfile(data) {
  const res = await fetch(`${API_BASE}/profile`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Failed to update profile');
  }
  return res.json();
}

export async function fetchActivityLogs(category = null, limit = 50) {
  const url = category && category !== 'all'
    ? `${API_BASE}/activity?category=${encodeURIComponent(category)}&limit=${limit}`
    : `${API_BASE}/activity?limit=${limit}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch activity logs');
  return res.json();
}

export const getActivityLogs = fetchActivityLogs;
