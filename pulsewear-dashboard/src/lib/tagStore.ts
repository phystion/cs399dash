import { writable } from 'svelte/store';

export const PRESET_TAGS = ['Bug', 'Feature', 'UX Issue', 'Performance', 'Critical', 'Monitor'];

export const topicTagsStore = writable<Record<number, string[]>>({});

export function toggleTag(clusterId: number, tag: string) {
  topicTagsStore.update(tags => {
    const existing = tags[clusterId] ?? [];
    if (existing.includes(tag)) {
      return { ...tags, [clusterId]: existing.filter(t => t !== tag) };
    }
    return { ...tags, [clusterId]: [...existing, tag] };
  });
}

export function addCustomTag(clusterId: number, tag: string) {
  const trimmed = tag.trim();
  if (!trimmed) return;
  topicTagsStore.update(tags => {
    const existing = tags[clusterId] ?? [];
    if (existing.includes(trimmed)) return tags;
    return { ...tags, [clusterId]: [...existing, trimmed] };
  });
}

export function removeTag(clusterId: number, tag: string) {
  topicTagsStore.update(tags => ({
    ...tags,
    [clusterId]: (tags[clusterId] ?? []).filter(t => t !== tag),
  }));
}
