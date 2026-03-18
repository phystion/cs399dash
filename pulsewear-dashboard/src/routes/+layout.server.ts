/**
 * Layout server load — data access layer entry point.
 *
 * Fetches themes, trends, and roadmap from the FastAPI backend on every
 * server-side render. All child pages receive this data automatically via
 * their `data` prop (Svelte 5: `let { data } = $props()`).
 *
 * Falls back to the pre-generated static JSON files if the backend is
 * unavailable (e.g. during build or when the server is offline).
 */

import { fetchThemes, fetchTrends, fetchRoadmap } from '$lib/api';
import {
  themes as staticThemes,
  monthlyTrends as staticTrends,
  roadmapItems as staticRoadmap,
} from '$lib/data';

export async function load({ fetch }: { fetch: typeof globalThis.fetch }) {
  try {
    const [themes, monthlyTrends, roadmapItems] = await Promise.all([
      fetchThemes(fetch),
      fetchTrends(fetch),
      fetchRoadmap(fetch),
    ]);
    console.log(
      `[data layer] loaded from API — ${themes.length} themes, ${monthlyTrends.length} months, ${roadmapItems.length} roadmap items`
    );
    return { themes, monthlyTrends, roadmapItems, source: 'api' as const };
  } catch (err) {
    console.warn('[data layer] API unavailable, falling back to static JSON:', err);
    return {
      themes: staticThemes,
      monthlyTrends: staticTrends,
      roadmapItems: staticRoadmap,
      source: 'static' as const,
    };
  }
}
