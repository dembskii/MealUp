import { ENDPOINTS } from '../config/network';

const BASE = ENDPOINTS.ANALYTICS;

const defaultOpts = {
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' },
};

async function request(url, opts = {}) {
  const res = await fetch(url, { ...defaultOpts, ...opts });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Analytics API ${res.status}: ${text}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export async function getDailyLog(date) {
  return request(`${BASE}/daily/${date}`);
}

export async function getDailyLogsRange(dateFrom, dateTo) {
  const params = new URLSearchParams({ date_from: dateFrom, date_to: dateTo });
  return request(`${BASE}/daily?${params}`);
}

export async function createMealEntry(payload) {
  return request(`${BASE}/meals`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function deleteMealEntry(entryId) {
  return request(`${BASE}/meals/entry/${entryId}`, { method: 'DELETE' });
}

export default {
  getDailyLog,
  getDailyLogsRange,
  createMealEntry,
  deleteMealEntry,
};
