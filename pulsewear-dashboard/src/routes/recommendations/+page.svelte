<script lang="ts">
  import { themes as staticThemes, monthlyTrends as staticTrends } from '$lib/data';
  import { topicTagsStore, toggleTag, addCustomTag, removeTag, PRESET_TAGS } from '$lib/tagStore';
  import PageHeader from '$lib/components/PageHeader.svelte';

  let { data } = $props();
  const themes = $derived(data.themes ?? staticThemes);
  const monthlyTrends = $derived(data.monthlyTrends ?? staticTrends);

  // ── Date range ───────────────────────────────────────────────
  const DATE_OPTS = [
    { value: '1m',  label: 'Last Month',     n: 1 },
    { value: '3m',  label: 'Last Quarter',   n: 3 },
    { value: '6m',  label: 'Last 6 Months',  n: 6 },
  ] as const;
  type DateRange = typeof DATE_OPTS[number]['value'];
  let dateRange = $state<DateRange>('3m');
  let showDateMenu = $state(false);

  const selectedOpt = $derived(DATE_OPTS.find(o => o.value === dateRange)!);

  const periodMonths = $derived(monthlyTrends.slice(-selectedOpt.n));

  // Period volume per cluster
  const periodData = $derived(
    themes.map(t => ({
      ...t,
      periodVolume: periodMonths.reduce((s, m) => s + m.volumes[t.cluster_id], 0),
    }))
  );

  const top3 = $derived([...periodData].sort((a, b) => b.periodVolume - a.periodVolume).slice(0, 3));
  const allSorted = $derived([...periodData].sort((a, b) => b.periodVolume - a.periodVolume));

  // ── View mode ────────────────────────────────────────────────
  type ViewMode = 'cards' | 'chart';
  let viewMode = $state<ViewMode>('cards');

  // ── Tags ────────────────────────────────────────────────────
  let openTagDropdown = $state<number | null>(null);
  let customTagInput = $state('');

  function handleAddCustom(cid: number) {
    addCustomTag(cid, customTagInput);
    customTagInput = '';
  }

  // ── Scatter chart ────────────────────────────────────────────
  const CW = 580, CH = 260;
  const CP = { t: 20, r: 20, b: 64, l: 60 };
  const CIW = CW - CP.l - CP.r;
  const CIH = CH - CP.t - CP.b;

  function niceLineTicks(dMin: number, dMax: number, count = 5): { lo: number; hi: number; ticks: number[] } {
    if (dMax <= dMin) return { lo: 0, hi: Math.max(dMax, 1), ticks: [0] };
    const range = dMax - dMin;
    const rawStep = range / (count - 1);
    const mag = Math.pow(10, Math.floor(Math.log10(rawStep)));
    const norm = rawStep / mag;
    const step = norm <= 1 ? mag : norm <= 2 ? 2 * mag : norm <= 5 ? 5 * mag : 10 * mag;
    const lo = Math.floor(dMin / step) * step;
    const hi = Math.ceil(dMax / step) * step;
    const ticks: number[] = [];
    for (let v = lo; v <= hi + step * 0.001; v += step) ticks.push(Math.round(v));
    return { lo, hi, ticks };
  }

  function logFrac(v: number, maxV: number): number {
    if (maxV <= 0) return 0;
    return Math.log1p(v) / Math.log1p(maxV);
  }

  const scatterXNiceTicks = $derived(() => ({ lo: 0, hi: 100, ticks: [0, 25, 50, 75, 100] }));
  const chartQx = $derived(() => CP.l + (50 / 100) * CIW);

  const scatterYMax = $derived(() => Math.max(...allSorted.map(t => t.periodVolume), 1));

  const chartData = $derived(() => {
    const all = allSorted;
    const maxVol = scatterYMax();
    const xHi = scatterXNiceTicks().hi;
    return all.map(t => {
      const lf = logFrac(t.periodVolume, maxVol);
      const x = CP.l + (t.positive_pct / Math.max(xHi, 1)) * CIW;
      const y = CP.t + CIH - lf * CIH;
      const r = 7 + lf * 8;
      const tier = t.positive_pct > 60 ? 'good' : t.positive_pct >= 40 ? 'mixed' : 'critical';
      const color = tier === 'good' ? '#059669' : tier === 'mixed' ? '#4A90E2' : '#DC2626';
      const fillColor = tier === 'good' ? 'rgba(5,150,105,0.16)' : tier === 'mixed' ? 'rgba(74,144,226,0.14)' : 'rgba(220,38,38,0.16)';
      return { ...t, x, y, r, tier, color, fillColor };
    });
  });

  const yTicks = $derived(() => {
    const maxV = scatterYMax();
    const candidates = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000];
    const chosen = candidates.filter(v => v <= maxV);
    if (!chosen.length || chosen[chosen.length - 1] < maxV * 0.5) chosen.push(Math.round(maxV));
    return chosen.map(v => ({ v, y: CP.t + CIH - logFrac(v, maxV) * CIH }));
  });

  // Sentiment label for a card
  function sentLabel(t: typeof top3[0]) {
    if (t.positive_pct > 60) return 'Positive';
    if (t.positive_pct >= 40) return 'Mixed';
    return 'Critical';
  }
  function sentClass(t: typeof top3[0]) {
    if (t.positive_pct > 60) return 'sent-good';
    if (t.positive_pct >= 40) return 'sent-mixed';
    return 'sent-crit';
  }

</script>

<PageHeader
  title="Recommendations"
  subtitle="Top product improvements ranked by feedback impact and sentiment signal."
>
  <div class="date-picker-wrap">
    <button class="date-btn" onclick={() => showDateMenu = !showDateMenu}>
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="4" width="18" height="18" rx="2"/>
        <line x1="16" y1="2" x2="16" y2="6"/>
        <line x1="8" y1="2" x2="8" y2="6"/>
        <line x1="3" y1="10" x2="21" y2="10"/>
      </svg>
      {selectedOpt.label}
      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="6 9 12 15 18 9"/>
      </svg>
    </button>
    {#if showDateMenu}
      <button type="button" class="overlay" onclick={() => showDateMenu = false} aria-label="Close date menu"></button>
      <div class="date-menu glass-sm">
        {#each DATE_OPTS as opt}
          <button
            class="date-opt"
            class:selected={dateRange === opt.value}
            onclick={() => { dateRange = opt.value; showDateMenu = false; }}
          >{opt.label}</button>
        {/each}
      </div>
    {/if}
  </div>
</PageHeader>

<main class="page-container">
  <!-- ── Top 3 summary cards ──────────────────────────── -->
  <section class="summary-row">
    {#each top3 as t, i (t.cluster_id)}
      <div class="glass summary-card fade-in-up" style="animation-delay:{i * 60}ms">
        <div class="sc-header">
          <span class="sc-rank">#{i + 1}</span>
          <span class="sc-sent {sentClass(t)}">{sentLabel(t)}</span>
        </div>
        <h3 class="sc-name">{t.name}</h3>
        <div class="sc-bar-wrap">
          <div class="sc-bar">
            <div class="sc-fill" style="width:{t.positive_pct}%"></div>
          </div>
          <span class="sc-pct">{t.positive_pct}%</span>
        </div>
        <p class="sc-vol">{t.periodVolume.toLocaleString()} responses in period</p>

        <p class="sc-issues">
          <span class="sc-chip">Key issues</span>
          <span class="sc-issues-text">{t.description}</span>
        </p>
      </div>
    {/each}
  </section>

  <!-- ── View toggle ───────────────────────────────────── -->
  <div class="view-toggle fade-in-up" style="animation-delay:200ms">
    <button class="vtab" class:active={viewMode === 'cards'} onclick={() => viewMode = 'cards'}>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
        <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
      </svg>
      Topics
    </button>
    <button class="vtab" class:active={viewMode === 'chart'} onclick={() => viewMode = 'chart'}>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="8" cy="16" r="2"/><circle cx="16" cy="8" r="2"/><circle cx="20" cy="18" r="2"/>
        <circle cx="4" cy="10" r="2"/>
      </svg>
      Chart
    </button>
  </div>

  <!-- ── Topics list ───────────────────────────────────── -->
  {#if viewMode === 'cards'}
    <div class="topics-list">
      {#each allSorted as t, i (t.cluster_id)}
        <div class="glass topic-card fade-in-up" class:tag-open={openTagDropdown === t.cluster_id} style="animation-delay:{i * 35}ms">
          <div class="topic-top">
            <div class="topic-info">
              <h3 class="topic-name"><a class="topic-link" href={`/feedback?cluster=${t.cluster_id}`}>{t.name}</a></h3>
              <p class="topic-desc">{t.description}</p>
            </div>
            <div class="topic-count">
              <span class="count-num">{t.periodVolume.toLocaleString()}</span>
              <span class="count-label">comments</span>
              <a class="topic-open" href={`/feedback?cluster=${t.cluster_id}`}>Open</a>
            </div>
          </div>

          <!-- Tags row -->
          <div class="tags-row">
            {#each ($topicTagsStore[t.cluster_id] ?? []) as tag}
              <span class="tag-chip">
                {tag}
                <button class="tag-x" onclick={() => removeTag(t.cluster_id, tag)} aria-label="Remove tag">
                  <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
              </span>
            {/each}

            <div class="tag-trigger">
              <button
                class="add-tag-btn"
                onclick={(e) => { e.stopPropagation(); openTagDropdown = openTagDropdown === t.cluster_id ? null : t.cluster_id; }}
              >
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                Tag
              </button>

              {#if openTagDropdown === t.cluster_id}
                <button type="button" class="overlay overlay-z50" onclick={() => openTagDropdown = null} aria-label="Close tag menu"></button>
                <div class="tag-dropdown glass" role="dialog" aria-label="Add tag">
                  <div class="tag-presets">
                    {#each PRESET_TAGS as pt}
                      <button
                        class="tag-preset"
                        class:preset-active={($topicTagsStore[t.cluster_id] ?? []).includes(pt)}
                        onclick={() => toggleTag(t.cluster_id, pt)}
                      >{pt}</button>
                    {/each}
                  </div>
                  <div class="tag-custom-row">
                    <input
                      class="tag-custom-input"
                      type="text"
                      placeholder="Custom tag…"
                      bind:value={customTagInput}
                      onkeydown={(e) => { if (e.key === 'Enter') handleAddCustom(t.cluster_id); }}
                    />
                    <button class="tag-add-btn" onclick={() => handleAddCustom(t.cluster_id)}>Add</button>
                  </div>
                </div>
              {/if}
            </div>
          </div>
        </div>
      {/each}
    </div>

  <!-- ── Chart view ────────────────────────────────────── -->
  {:else}
    <div class="glass chart-card fade-in-up" style="animation-delay:80ms">
      <div class="chart-header">
        <div>
          <p class="section-title">Sentiment vs. Impact</p>
          <p class="chart-sub">Each bubble = one theme · size = priority score</p>
        </div>
        <button class="print-btn" onclick={() => window.print()}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/>
          </svg>
          Print
        </button>
      </div>

      <svg viewBox="0 0 {CW} {CH}" class="scatter-svg" aria-hidden="true">
        <!-- Zone backgrounds -->
        <rect x={CP.l} y={CP.t} width={chartQx() - CP.l} height={CIH} fill="rgba(220,38,38,0.04)" rx="4"/>
        <rect x={chartQx()} y={CP.t} width={CP.l + CIW - chartQx()} height={CIH} fill="rgba(5,150,105,0.04)" rx="4"/>

        <!-- Center divider -->
        <line x1={chartQx()} y1={CP.t} x2={chartQx()} y2={CP.t + CIH}
              stroke="rgba(15,23,42,0.12)" stroke-width="1" stroke-dasharray="4,4"/>

        <!-- Y-axis grid + labels -->
        {#each yTicks() as tick}
          <line x1={CP.l} y1={tick.y} x2={CP.l + CIW} y2={tick.y}
                stroke="rgba(15,23,42,0.06)" stroke-width="1"/>
          <text x={CP.l - 6} y={tick.y + 4} font-size="9" fill="rgba(15,23,42,0.35)" text-anchor="end">
            {tick.v > 999 ? (tick.v / 1000).toFixed(1) + 'k' : tick.v}
          </text>
        {/each}

        <!-- X-axis ticks + labels -->
        {#each scatterXNiceTicks().ticks as pct (pct)}
          {@const xpos = CP.l + (pct / Math.max(scatterXNiceTicks().hi, 1)) * CIW}
          <line x1={xpos} y1={CP.t + CIH} x2={xpos} y2={CP.t + CIH + 5}
                stroke="rgba(15,23,42,0.18)" stroke-width="1"/>
          <text x={xpos} y={CP.t + CIH + 18} font-size="9" fill="rgba(15,23,42,0.40)"
                text-anchor="middle">{pct}%</text>
        {/each}

        <!-- X-axis title -->
        <text x={CP.l + CIW / 2} y={CH - 6} font-size="9.5" fill="rgba(15,23,42,0.40)"
              text-anchor="middle">Positive Sentiment %</text>

        <!-- Y-axis title -->
        <text x={14} y={CP.t + CIH / 2} font-size="9.5" fill="rgba(15,23,42,0.40)"
              text-anchor="middle" transform="rotate(-90 14 {CP.t + CIH / 2})">Volume</text>

        <!-- Bubbles -->
        {#each chartData() as item (item.cluster_id)}
          <g class="chart-bubble" role="img" aria-label="{item.name}: {item.periodVolume} responses">
            <circle
              cx={item.x} cy={item.y} r={item.r}
              fill={item.fillColor}
              stroke={item.color}
              stroke-width="1.5"
            />
            <text x={item.x} y={item.y - item.r - 4} font-size="8.5"
                  fill={item.color}
                  text-anchor="middle" font-weight="600">{item.name.split(' ')[0]}</text>
          </g>
        {/each}
      </svg>

      <!-- Legend -->
      <div class="chart-legend">
        <span class="leg">
          <span class="leg-dot" style="background:rgba(5,150,105,0.18);border:1.5px solid #059669;"></span>
          High Sentiment
        </span>
        <span class="leg">
          <span class="leg-dot" style="background:rgba(74,144,226,0.18);border:1.5px solid #4A90E2;"></span>
          Mixed
        </span>
        <span class="leg">
          <span class="leg-dot" style="background:rgba(220,38,38,0.18);border:1.5px solid #DC2626;"></span>
          Needs Attention
        </span>
        <span class="leg-note">Bubble size = priority score</span>
      </div>
    </div>
  {/if}

</main>

<style>
  main { padding-top: 0; padding-bottom: 72px; }

  /* Date picker */
  .date-picker-wrap { position: relative; }
  .date-btn {
    display:flex; align-items:center; gap:7px;
    padding:8px 14px; font-size:.82rem; font-weight:600; color:var(--text-muted);
    background:#fff; border:1px solid rgba(15,23,42,0.12); border-radius:var(--radius-sm);
    cursor:pointer; transition:background var(--transition), color var(--transition), border-color var(--transition);
  }
  .date-btn:hover { background:#F7F8FA; color:var(--text); border-color:rgba(15,23,42,0.18); }
  .date-menu {
    position:absolute; top:calc(100% + 6px); right:0; z-index:51;
    padding:6px; min-width:140px;
  }
  .date-opt {
    display:block; width:100%; text-align:left;
    padding:8px 12px; font-size:.82rem; font-weight:500; color:var(--text-muted);
    background:transparent; border:none; border-radius:6px; cursor:pointer;
    transition:background var(--transition), color var(--transition);
  }
  .date-opt:hover { background:rgba(74,144,226,0.10); color:var(--navy); }
  .date-opt.selected { color:var(--navy); font-weight:700; background:rgba(74,144,226,0.10); }
  .overlay {
    position: fixed;
    inset: 0;
    z-index: 49;
    border: none;
    background: transparent;
    padding: 0;
    margin: 0;
  }
  .overlay-z50 { z-index:50; }

  /* Summary cards */
  .summary-row {
    display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin-bottom:18px;
  }
  @media (max-width:700px) { .summary-row { grid-template-columns:1fr; } }

  .summary-card { padding:20px 22px; }
  .sc-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:10px; }
  .sc-rank { font-size:.7rem; font-weight:800; color:var(--text-muted); text-transform:uppercase; letter-spacing:.06em; }
  .sc-sent { font-size:.7rem; font-weight:700; padding:2px 8px; border-radius:6px; }
  .sent-good  { background:rgba(5,150,105,.10); color:#059669; }
  .sent-mixed { background:rgba(74,144,226,.12); color:#1A5FAF; }
  .sent-crit  { background:rgba(220,38,38,.10);  color:#DC2626; }
  .sc-name { font-size:.95rem; font-weight:700; color:var(--text); margin-bottom:12px; line-height:1.3; }
  .sc-bar-wrap { display:flex; align-items:center; gap:8px; margin-bottom:8px; }
  .sc-bar { flex:1; height:5px; background:rgba(15,23,42,.07); border-radius:6px; overflow:hidden; }
  .sc-fill { height:100%; background:linear-gradient(90deg,var(--blue-light),var(--navy)); border-radius:6px; }
  .sc-pct { font-size:.75rem; font-weight:700; color:var(--text-muted); flex-shrink:0; }
  .sc-vol { font-size:.73rem; color:var(--text-subtle); margin-bottom:10px; }
  .sc-issues {
    font-size:.74rem;
    line-height:1.42;
    color:var(--text-muted);
    display:flex;
    align-items:flex-start;
    gap:6px;
    margin-bottom:8px;
  }
  .sc-chip {
    display:inline-flex;
    align-items:center;
    justify-content:center;
    min-width:52px;
    padding:2px 8px;
    border-radius:999px;
    font-size:.63rem;
    font-weight:700;
    text-transform:uppercase;
    letter-spacing:.04em;
    flex-shrink:0;
    margin-top:1px;
    background:rgba(27,58,107,.10);
    color:var(--navy);
  }
  .sc-issues-text { color:var(--text); }

  /* View toggle */
  .view-toggle {
    display:inline-flex; gap:3px; background:rgba(15,23,42,.05); border-radius:8px;
    padding:3px; margin-bottom:16px;
  }
  .vtab {
    display:flex; align-items:center; gap:6px;
    padding:6px 14px; font-size:.8rem; font-weight:500; color:var(--text-muted);
    background:transparent; border:none; border-radius:6px; cursor:pointer;
    transition:background var(--transition), color var(--transition);
  }
  .vtab.active {
    background:#fff; color:var(--text); font-weight:700;
    border: 1px solid rgba(15,23,42,0.10);
  }

  /* Topics list */
  .topics-list { display:flex; flex-direction:column; gap:10px; }

  .topic-card { padding:18px 20px; }
  .topic-card.tag-open { z-index: 5; }

  .topic-top {
    display:flex; align-items:flex-start; justify-content:space-between; gap:16px; margin-bottom:12px;
  }
  .topic-info { flex:1; min-width:0; }
  .topic-name { font-size:.95rem; font-weight:700; color:var(--text); margin-bottom:4px; }
  .topic-link { color:inherit; text-decoration:none; }
  .topic-link:hover { color:var(--navy); text-decoration:underline; text-underline-offset:2px; }
  .topic-desc { font-size:.81rem; color:var(--text-muted); line-height:1.5; }

  .topic-count { flex-shrink:0; text-align:right; }
  .count-num { display:block; font-size:1.3rem; font-weight:800; color:var(--navy); letter-spacing:-.02em; }
  .count-label { font-size:.68rem; color:var(--text-subtle); text-transform:uppercase; letter-spacing:.04em; font-weight:600; }
  .topic-open {
    display:inline-flex; margin-top:4px;
    font-size:.72rem; font-weight:600; color:var(--navy);
    text-decoration:none;
  }
  .topic-open:hover { color:var(--blue); }

  /* Tags */
  .tags-row { display:flex; align-items:center; gap:6px; flex-wrap:wrap; }

  .tag-chip {
    display:inline-flex; align-items:center; gap:4px;
    padding:3px 8px; background:rgba(27,58,107,.09); color:var(--navy);
    border-radius:6px; font-size:.72rem; font-weight:600;
  }
  .tag-x {
    display:flex; align-items:center; background:none; border:none; cursor:pointer;
    color:inherit; opacity:.6; padding:0; line-height:1;
  }
  .tag-x:hover { opacity:1; }

  .tag-trigger { position:relative; }

  .add-tag-btn {
    display:inline-flex; align-items:center; gap:4px;
    padding:3px 9px; font-size:.72rem; font-weight:600; color:var(--text-muted);
    background:rgba(15,23,42,.05); border:1px dashed rgba(27,58,107,.18);
    border-radius:6px; cursor:pointer;
    transition:background var(--transition), color var(--transition), border-color var(--transition);
  }
  .add-tag-btn:hover { background:rgba(74,144,226,.10); color:var(--navy); border-color:rgba(74,144,226,.30); }

  .tag-dropdown {
    position:absolute; top:calc(100% + 6px); left:0; z-index:51;
    padding:10px; min-width:220px;
  }
  .tag-presets { display:flex; flex-wrap:wrap; gap:5px; margin-bottom:8px; }
  .tag-preset {
    padding:3px 9px; font-size:.72rem; font-weight:500; color:var(--text-muted);
    background:rgba(15,23,42,.05); border:1px solid transparent;
    border-radius:6px; cursor:pointer; transition:all var(--transition);
  }
  .tag-preset:hover { background:rgba(74,144,226,.10); color:var(--navy); }
  .tag-preset.preset-active { background:rgba(27,58,107,.10); color:var(--navy); border-color:rgba(27,58,107,.20); font-weight:700; }

  .tag-custom-row { display:flex; gap:6px; }
  .tag-custom-input {
    flex:1; padding:6px 10px; font-size:.78rem;
    background:#fff; border:1px solid rgba(15,23,42,.13);
    border-radius:var(--radius-sm); outline:none; width:auto;
    transition:border-color var(--transition);
  }
  .tag-custom-input:focus { border-color:var(--blue); }
  .tag-add-btn {
    padding:6px 12px; font-size:.78rem; font-weight:600; color:#fff;
    background:var(--navy); border:none; border-radius:var(--radius-sm); cursor:pointer;
    transition:background var(--transition);
  }
  .tag-add-btn:hover { background:#142d5a; }

  /* Chart */
  .chart-card { padding:22px 24px 18px; }
  .chart-header { display:flex; align-items:flex-start; justify-content:space-between; margin-bottom:14px; }
  .chart-sub { font-size:.76rem; color:var(--text-muted); margin-top:2px; }
  .scatter-svg { width:100%; height:auto; display:block; overflow:visible; }
  .chart-bubble { cursor:default; }
  .chart-bubble circle { transition:r 0.2s ease, opacity 0.2s ease; }
  .chart-bubble:hover circle { opacity:0.85; }

  .chart-legend {
    display:flex; gap:18px; flex-wrap:wrap; align-items:center;
    margin-top:12px; padding-top:12px; border-top:1px solid rgba(15,23,42,.06);
  }
  .leg { display:flex; align-items:center; gap:6px; font-size:.73rem; color:var(--text-muted); }
  .leg-dot { width:12px; height:12px; border-radius:4px; flex-shrink:0; }
  .leg-note { font-size:.70rem; color:var(--text-subtle); margin-left:auto; }

  /* Print button */
  .print-btn {
    display:flex; align-items:center; gap:6px;
    padding:6px 14px; font-size:.78rem; font-weight:600; color:var(--text-muted);
    background:#fff; border:1px solid rgba(15,23,42,0.12); border-radius:var(--radius-sm);
    cursor:pointer; flex-shrink:0;
    transition:background var(--transition), color var(--transition), border-color var(--transition);
  }
  .print-btn:hover { background:#F7F8FA; color:var(--text); border-color:rgba(15,23,42,0.20); }

  @media print {
    :global(.sidebar),
    :global(.topbar),
    :global(.page-header-wrap) { display: none !important; }
    :global(.app-content) { margin: 0 !important; padding: 0 !important; }
    :global(body) { background: white !important; }
    .summary-row,
    .view-toggle,
    .topics-list,
    .print-btn { display: none !important; }
    .chart-card {
      box-shadow: none !important;
      border: 1px solid rgba(15,23,42,0.15) !important;
      break-inside: avoid;
    }
  }
</style>
