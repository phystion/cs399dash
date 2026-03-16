<script lang="ts">
  import PageHeader from '$lib/components/PageHeader.svelte';
  import { summaryStats, themes } from '$lib/data';

  type BandKey = 'positive' | 'negative' | 'mixed';

  type GroupData = {
    key: BandKey;
    title: string;
    tone: string;
    items: typeof themes;
    totalVolume: number;
    share: number;
    topCluster: (typeof themes)[number] | null;
    summary: string;
    weightedPositive: number;
    weightedNegative: number;
  };

  const BAND_META: Record<BandKey, { title: string; tone: string }> = {
    negative: { title: 'Negative', tone: 'Most important issues to resolve' },
    mixed: { title: 'Mixed', tone: 'Themes that could still move positive' },
    positive: { title: 'Positive', tone: 'Strengths worth protecting' }
  };

  const BAND_COLORS: Record<BandKey, string> = {
    positive: '#059669',
    negative: '#dc2626',
    mixed: '#4A90E2'
  };

  const RING_R = 78;
  const RING_C = 2 * Math.PI * RING_R;

  let hoveredGroup = $state<BandKey | null>(null);
  let selectedGroup = $state<BandKey | null>(null);

  function getBand(positivePct: number): BandKey {
    if (positivePct >= 65) return 'positive';
    if (positivePct >= 45) return 'mixed';
    return 'negative';
  }

  function pct(part: number, total: number) {
    return Math.round((part / Math.max(total, 1)) * 100);
  }

  function bandImportance(theme: typeof themes[number], key: BandKey) {
    if (key === 'positive') return theme.volume * (theme.positive_pct / 100);
    if (key === 'negative') return theme.volume * (theme.negative_pct / 100);
    return theme.volume * (1 - Math.abs(theme.positive_pct - 50) / 50);
  }

  function fallbackSummary(key: BandKey) {
    if (key === 'negative') return 'Placeholder: add the main issue patterns for this group.';
    if (key === 'mixed') return 'Placeholder: add the themes that could be improved to push sentiment positive.';
    return 'Placeholder: add the strengths that should be maintained.';
  }

  function sentimentHeadline(key: BandKey) {
    if (key === 'positive') return 'Positive';
    if (key === 'negative') return 'Negative';
    return 'Mixed';
  }

  function themeMetric(theme: (typeof themes)[number], key: BandKey) {
    if (key === 'negative') return `${theme.negative_pct}% negative`;
    if (key === 'positive') return `${theme.positive_pct}% positive`;
    return `${theme.positive_pct}% / ${theme.negative_pct}%`;
  }

  const groupedThemes = $derived(() =>
    (['negative', 'mixed', 'positive'] as BandKey[]).map((key) => {
      const items = [...themes]
        .filter((theme) => getBand(theme.positive_pct) === key)
        .sort((a, b) => bandImportance(b, key) - bandImportance(a, key));

      const totalVolume = items.reduce((sum, theme) => sum + theme.volume, 0);
      const topCluster = items[0] ?? null;
      const weightedPositive = Math.round(
        items.reduce((sum, theme) => sum + theme.volume * (theme.positive_pct / 100), 0) / Math.max(totalVolume, 1)
      );
      const weightedNegative = 100 - weightedPositive;

      return {
        key,
        ...BAND_META[key],
        items,
        totalVolume,
        share: pct(totalVolume, summaryStats.total_feedback),
        topCluster,
        summary: topCluster?.description ?? fallbackSummary(key),
        weightedPositive,
        weightedNegative
      } satisfies GroupData;
    })
  );

  const groupMap = $derived(() =>
    Object.fromEntries(groupedThemes().map((group) => [group.key, group])) as Record<BandKey, GroupData>
  );

  const defaultGroup = $derived(() => groupMap().mixed);

  const activeGroup = $derived(() => {
    if (selectedGroup) return groupMap()[selectedGroup];
    if (hoveredGroup) return groupMap()[hoveredGroup];
    return defaultGroup();
  });

  const ringSegments = $derived(() => {
    let offset = 0;
    return (['positive', 'negative', 'mixed'] as BandKey[]).map((key) => {
      const share = groupMap()[key].share;
      const rawLength = (share / 100) * RING_C;
      const segment = {
        key,
        share,
        color: BAND_COLORS[key],
        dasharray: `${rawLength} ${Math.max(RING_C - rawLength, 0)}`,
        dashoffset: -offset,
      };
      offset += rawLength;
      return segment;
    });
  });
</script>

<PageHeader title="Sentiment" />

<main class="page-container">
  <section class="glass sentiment-hero fade-in-up">
    <div class="hero-ring-col">
      <svg viewBox="0 0 200 200" class="ring-svg" aria-label="Sentiment distribution">
        <circle cx="100" cy="100" r={RING_R} class="ring-track"></circle>

        {#each ringSegments() as segment (segment.key)}
          <circle
            cx="100"
            cy="100"
            r={RING_R}
            class="ring-segment"
            class:segment-active={hoveredGroup === segment.key || selectedGroup === segment.key}
            role="button"
            tabindex="0"
            aria-label={`${segment.key} sentiment sector`}
            aria-pressed={selectedGroup === segment.key}
            stroke={segment.color}
            stroke-dasharray={segment.dasharray}
            stroke-dashoffset={segment.dashoffset}
            onmouseenter={() => hoveredGroup = segment.key}
            onmouseleave={() => hoveredGroup = null}
            onclick={() => selectedGroup = selectedGroup === segment.key ? null : segment.key}
            onkeydown={(event) => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                selectedGroup = selectedGroup === segment.key ? null : segment.key;
              }
            }}
          ></circle>
        {/each}

        <circle cx="100" cy="100" r="52" class="ring-core"></circle>
        <text x="100" y="94" text-anchor="middle" class="ring-core-label">
          {selectedGroup || hoveredGroup ? activeGroup().title : 'Overall'}
        </text>
        <text x="100" y="118" text-anchor="middle" class="ring-core-value">
          {selectedGroup || hoveredGroup ? `${activeGroup().share}%` : 'Mixed'}
        </text>
      </svg>
    </div>

    <div class="hero-copy">
      <span class="hero-label">Sentiment Summary</span>
      <h2 class="hero-title">{activeGroup().title}</h2>
      <p class="hero-text">{activeGroup().tone}</p>

      <div class="hero-stats">
        <div class="hero-stat">
          <span class="hero-stat-label">Share of feedback</span>
          <strong>{activeGroup().share}%</strong>
        </div>
        <div class="hero-stat">
          <span class="hero-stat-label">Amount of data</span>
          <strong>{activeGroup().totalVolume.toLocaleString()} responses</strong>
        </div>
        <div class="hero-stat">
          <span class="hero-stat-label">Highest priority cluster</span>
          <strong>{activeGroup().topCluster?.name ?? 'Placeholder cluster'}</strong>
        </div>
      </div>

      <div class="hero-detail-card">
        <span class="hero-stat-label">Group description</span>
        <p class="hero-detail">{activeGroup().summary}</p>
      </div>

      <div class="hero-legend">
        {#each groupedThemes() as group}
          <button
            type="button"
            class="legend-item"
            class:legend-active={hoveredGroup === group.key || selectedGroup === group.key}
            onmouseenter={() => hoveredGroup = group.key}
            onmouseleave={() => hoveredGroup = null}
            onclick={() => selectedGroup = selectedGroup === group.key ? null : group.key}
          >
            <span class={`legend-dot dot-${group.key}`}></span>
            <span>{group.title}</span>
            <strong>{group.share}%</strong>
          </button>
        {/each}
      </div>
    </div>
  </section>

  <section class="actions-grid">
    {#each groupedThemes() as group, groupIndex (group.key)}
      <section class="glass action-card fade-in-up" style={`animation-delay:${60 + groupIndex * 40}ms`}>
        <div class="action-head">
          <div>
            <p class="action-title">{group.title}</p>
            <p class="action-copy">{group.tone}</p>
          </div>
          <span class={`action-pill band-${group.key}`}>{group.share}%</span>
        </div>

        <p class="group-detail">{group.summary}</p>

        <div class="theme-list">
          {#each group.items as theme}
            <a href={`/feedback?cluster=${theme.cluster_id}`} class="theme-row">
              <div class="theme-row-top">
                <span class="theme-name">{theme.name}</span>
                <span class={`theme-pill band-${group.key}`}>
                  {group.key === 'negative' ? theme.negative_pct : theme.positive_pct}%
                </span>
              </div>

              <div class="sentiment-bar" aria-hidden="true">
                <div class="bar-positive" style={`width:${theme.positive_pct}%`}></div>
                <div class="bar-negative" style={`width:${theme.negative_pct}%`}></div>
              </div>

              <div class="theme-meta">
                <span>{themeMetric(theme, group.key)}</span>
                <span>{theme.volume.toLocaleString()} responses</span>
              </div>
            </a>
          {/each}
        </div>
      </section>
    {/each}
  </section>
</main>

<style>
  main {
    padding-bottom: 72px;
  }

  .sentiment-hero {
    display: grid;
    grid-template-columns: 240px 1fr;
    gap: 24px;
    align-items: center;
    padding: 22px;
    margin-bottom: 18px;
  }

  .hero-ring-col {
    display: flex;
    justify-content: center;
  }

  .ring-svg {
    width: 188px;
    height: 188px;
    overflow: visible;
  }

  .ring-track,
  .ring-segment {
    fill: none;
    stroke-width: 22;
    transform: rotate(-90deg);
    transform-origin: 100px 100px;
    stroke-linecap: butt;
  }

  .ring-track {
    stroke: rgba(15, 23, 42, 0.06);
  }

  .ring-segment {
    cursor: pointer;
    transition: opacity 0.2s ease, stroke-width 0.2s ease;
    opacity: 0.82;
    animation: ringReveal 0.7s cubic-bezier(0.22, 1, 0.36, 1) both;
  }

  .ring-segment:hover,
  .ring-segment.segment-active {
    opacity: 1;
    stroke-width: 26;
  }

  .ring-segment:focus {
    outline: none;
  }

  .ring-segment:focus-visible {
    outline: none;
    opacity: 1;
    stroke-width: 26;
  }

  .ring-core {
    fill: #fff;
    stroke: rgba(15, 23, 42, 0.08);
  }

  .ring-core-label {
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    fill: #7A9BB8;
  }

  .ring-core-value {
    font-size: 18px;
    font-weight: 800;
    fill: #0D1B2E;
  }

  .hero-label,
  .action-copy,
  .group-detail,
  .theme-meta span,
  .hero-text,
  .hero-detail,
  .hero-stat-label {
    font-size: 0.78rem;
    color: var(--text-muted);
    line-height: 1.45;
  }

  .hero-label {
    display: inline-block;
    margin-bottom: 6px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-subtle);
  }

  .hero-title {
    font-size: 1.8rem;
    font-weight: 800;
    letter-spacing: -0.04em;
    color: var(--text);
  }

  .hero-text {
    margin-top: 6px;
  }

  .hero-stats {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    margin-top: 16px;
  }

  .hero-stat {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 10px 12px;
    border-radius: var(--radius);
    background: rgba(15, 23, 42, 0.04);
  }

  .hero-stat strong {
    font-size: 0.86rem;
    color: var(--text);
  }

  .hero-detail-card {
    margin-top: 14px;
    padding: 12px 14px;
    border-radius: var(--radius);
    background: rgba(15, 23, 42, 0.04);
  }

  .hero-detail {
    margin-top: 6px;
  }

  .group-detail {
    margin-top: 14px;
  }

  .hero-legend {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 16px;
  }

  .legend-item {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 8px 10px;
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: 999px;
    background: #fff;
    font-size: 0.76rem;
    color: var(--text-muted);
    transition: border-color var(--transition), background var(--transition);
  }

  .legend-item.legend-active,
  .legend-item:hover {
    border-color: rgba(27, 58, 107, 0.18);
    background: rgba(255, 255, 255, 0.88);
  }

  .legend-item strong {
    color: var(--text);
  }

  .legend-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .dot-positive { background: #059669; }
  .dot-negative { background: #dc2626; }
  .dot-mixed { background: #4A90E2; }

  .actions-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 14px;
  }

  .action-card {
    padding: 18px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .action-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 10px;
  }

  .action-title {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text);
  }

  .action-copy {
    margin-top: 4px;
  }

  .group-detail {
    margin-top: 0;
    padding: 12px 14px;
    border-radius: var(--radius);
    background: rgba(15, 23, 42, 0.04);
  }

  .action-pill,
  .theme-pill {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 4px 9px;
    border-radius: 999px;
    font-size: 0.67rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    white-space: nowrap;
  }

  .band-positive {
    background: rgba(5, 150, 105, 0.10);
    color: var(--positive);
  }

  .band-negative {
    background: rgba(220, 38, 38, 0.10);
    color: var(--negative);
  }

  .band-mixed {
    background: rgba(74, 144, 226, 0.12);
    color: #1a5faf;
  }

  .theme-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .theme-row {
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 12px;
    border: 1px solid rgba(15, 23, 42, 0.07);
    border-radius: var(--radius);
    text-decoration: none;
    color: inherit;
    transition: border-color var(--transition), background var(--transition);
  }

  .theme-row:hover {
    border-color: rgba(27, 58, 107, 0.18);
    background: rgba(255, 255, 255, 0.88);
  }

  .theme-row-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
  }

  .theme-name {
    font-size: 0.84rem;
    font-weight: 700;
    color: var(--text);
    line-height: 1.35;
  }

  .sentiment-bar {
    display: flex;
    width: 100%;
    height: 8px;
    overflow: hidden;
    border-radius: 999px;
    background: rgba(15, 23, 42, 0.06);
  }

  .bar-positive {
    background: linear-gradient(90deg, rgba(5, 150, 105, 0.72), #059669);
  }

  .bar-negative {
    background: linear-gradient(90deg, rgba(220, 38, 38, 0.72), #dc2626);
  }

  .theme-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  @media (max-width: 1100px) {
    .sentiment-hero {
      grid-template-columns: 1fr;
    }

    .actions-grid {
      grid-template-columns: 1fr;
    }

    .hero-stats {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
  }

  @media (max-width: 680px) {
    .hero-legend,
    .theme-row-top,
    .action-head {
      flex-direction: column;
      align-items: flex-start;
    }

    .hero-stats {
      grid-template-columns: 1fr;
    }
  }

  @keyframes ringReveal {
    from {
      opacity: 0;
      transform: rotate(-100deg) scale(0.96);
      transform-origin: 100px 100px;
    }
    to {
      opacity: 0.82;
      transform: rotate(-90deg) scale(1);
      transform-origin: 100px 100px;
    }
  }
</style>
