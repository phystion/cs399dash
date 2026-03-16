<script lang="ts">
  import type { Theme } from '$lib/data';

  interface Props {
    theme: Theme;
    linkable?: boolean;
  }

  let { theme, linkable = true }: Props = $props();

  // Sentiment label: good / mixed / critical based on positive_pct
  const sentimentClass = $derived(
    theme.positive_pct >= 60 ? 'good' :
    theme.positive_pct >= 45 ? 'mixed' : 'critical'
  );
  const sentimentLabel = $derived(
    theme.positive_pct >= 60 ? 'Positive' :
    theme.positive_pct >= 45 ? 'Mixed' : 'Needs Attention'
  );
</script>

<svelte:element
  this={linkable ? 'a' : 'div'}
  href={linkable ? `/feedback?cluster=${theme.cluster_id}` : undefined}
  class="glass theme-card fade-in-up"
>
  <div class="tc-header">
    <span class="tc-name">{theme.name}</span>
    {#if theme.roadmap_id}
      <span class="badge badge-blue tc-badge">{theme.roadmap_id}</span>
    {:else}
      <span class="badge badge-gray tc-badge">Unassigned</span>
    {/if}
  </div>

  <p class="tc-volume">{theme.volume.toLocaleString()} responses</p>

  <!-- Sentiment bar: blue = positive portion, rest = track -->
  <div class="tc-bar" role="img" aria-label="{theme.positive_pct}% positive sentiment">
    <div class="bar-fill" style="width: {theme.positive_pct}%;"></div>
  </div>

  <div class="tc-footer">
    <span class="sentiment-tag {sentimentClass}">{sentimentLabel}</span>
    <span class="tc-pct">{theme.positive_pct}% / {theme.negative_pct}%</span>
  </div>
</svelte:element>

<style>
  .theme-card {
    display: block;
    padding: 18px 20px;
    text-decoration: none;
    color: inherit;
    cursor: pointer;
    transition: border-color var(--transition);
  }

  .theme-card:hover {
    border-color: rgba(15, 23, 42, 0.18);
  }

  .tc-header {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    margin-bottom: 8px;
  }

  .tc-name {
    flex: 1;
    font-size: 0.9rem;
    font-weight: 700;
    color: var(--text);
    line-height: 1.3;
  }

  .tc-badge { flex-shrink: 0; font-size: 0.67rem; margin-top: 1px; }

  .tc-volume {
    font-size: 0.78rem;
    color: var(--text-muted);
    margin-bottom: 10px;
  }

  .tc-bar {
    height: 5px;
    border-radius: 6px;
    background: rgba(15,23,42,0.07);
    overflow: hidden;
    margin-bottom: 10px;
  }

  .bar-fill {
    height: 100%;
    border-radius: 6px;
    background: linear-gradient(90deg, var(--blue-light), var(--navy));
    transition: width 0.7s var(--ease);
  }

  .tc-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  /* Sentiment tag */
  .sentiment-tag {
    font-size: 0.72rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 6px;
  }

  .sentiment-tag.good {
    background: rgba(5, 150, 105, 0.10);
    color: #059669;
  }

  .sentiment-tag.mixed {
    background: rgba(74, 144, 226, 0.14);
    color: #1A5FAF;
  }

  .sentiment-tag.critical {
    background: rgba(220, 38, 38, 0.09);
    color: #DC2626;
  }

  .tc-pct {
    font-size: 0.73rem;
    color: var(--text-subtle);
  }
</style>
