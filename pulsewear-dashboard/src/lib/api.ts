/**
 * Data access layer — typed client for the PulseWear FastAPI backend.
 *
 * All functions accept an optional `fetch` argument so they work in both
 * SvelteKit server load functions (which pass SvelteKit's enhanced fetch)
 * and browser contexts (which use the native fetch).
 */

import type { Theme, MonthlyDataPoint, RoadmapItem } from './data';

export const API_BASE = 'http://localhost:8000';

// ── Response shapes returned by the FastAPI ──────────────────────────────────

interface ThemesResponse {
  themes: Theme[];
}

interface TrendsResponse {
  months: MonthlyDataPoint[];
  total_periods: number;
}

interface RoadmapResponse {
  roadmap: RoadmapItem[];
}

// ── Fetch helpers ─────────────────────────────────────────────────────────────

export async function fetchThemes(
  fetchFn: typeof fetch = fetch
): Promise<Theme[]> {
  const res = await fetchFn(`${API_BASE}/themes`);
  if (!res.ok) throw new Error(`/themes ${res.status}`);
  const data: ThemesResponse = await res.json();
  return data.themes;
}

export async function fetchTrends(
  fetchFn: typeof fetch = fetch
): Promise<MonthlyDataPoint[]> {
  const res = await fetchFn(`${API_BASE}/trends`);
  if (!res.ok) throw new Error(`/trends ${res.status}`);
  const data: TrendsResponse = await res.json();
  return data.months;
}

export async function fetchRoadmap(
  fetchFn: typeof fetch = fetch
): Promise<RoadmapItem[]> {
  const res = await fetchFn(`${API_BASE}/roadmap`);
  if (!res.ok) throw new Error(`/roadmap ${res.status}`);
  const data: RoadmapResponse = await res.json();
  return data.roadmap;
}
