<script lang="ts">
  import { roadmapItems as staticRoadmap } from '$lib/data';
  import PageHeader from '$lib/components/PageHeader.svelte';

  let { data } = $props();
  const roadmapItems = $derived(data.roadmapItems ?? staticRoadmap);

  type SortKey = 'priority_score' | 'volume' | 'positive_pct' | 'status';
  let sortKey = $state<SortKey>('priority_score');
  let sortAsc  = $state(false);

  const STATUS_RANK: Record<string, number> = {
    Active: 4,
    'Under Review': 3,
    Planned: 2,
    Backlog: 1,
  };

  const sorted = $derived(
    [...roadmapItems].sort((a, b) => {
      const diff = sortKey === 'status'
        ? (STATUS_RANK[a.status] ?? 0) - (STATUS_RANK[b.status] ?? 0)
        : a[sortKey] - b[sortKey];
      return sortAsc ? diff : -diff;
    })
  );

  function toggleSort(key: SortKey) {
    if (sortKey === key) sortAsc = !sortAsc;
    else { sortKey = key; sortAsc = false; }
  }

  function statusClass(s: string) {
    if (s === 'Active')       return 'badge-positive';
    if (s === 'Planned')      return 'badge-blue';
    if (s === 'Under Review') return 'badge-warning';
    return 'badge-gray';
  }

  function priorityClass(score: number) {
    if (score >= 80) return 'prio-critical';
    if (score >= 60) return 'prio-high';
    if (score >= 40) return 'prio-medium';
    return 'prio-low';
  }

  function priorityLabel(score: number) {
    if (score >= 80) return 'Critical';
    if (score >= 60) return 'High';
    if (score >= 40) return 'Medium';
    return 'Low';
  }

  // Stats
  const totalVolume    = $derived(roadmapItems.reduce((s, r) => s + r.volume, 0));
  const avgSentiment   = $derived(Math.round(roadmapItems.reduce((s, r) => s + r.positive_pct, 0) / Math.max(roadmapItems.length, 1)));
  const criticalCount  = $derived(roadmapItems.filter(r => r.priority_score >= 80).length);
</script>

<PageHeader
  title="Roadmap Priorities"
  subtitle="8 feedback-driven product initiatives ranked by priority score, tied directly to the highest-impact customer themes."
/>

<main class="page-container">
  <!-- ── Summary row ────────────────────────────────── -->
  <div class="summary-row fade-in-up">
    <div class="glass summary-card">
      <p class="sum-label">Initiatives</p>
      <p class="sum-value">{roadmapItems.length}</p>
    </div>
    <div class="glass summary-card">
      <p class="sum-label">Feedback Covered</p>
      <p class="sum-value">{totalVolume.toLocaleString()}</p>
    </div>
    <div class="glass summary-card">
      <p class="sum-label">Avg Sentiment</p>
      <p class="sum-value">{avgSentiment}%</p>
    </div>
    <div class="glass summary-card">
      <p class="sum-label">Critical Issues</p>
      <p class="sum-value critical">{criticalCount}</p>
    </div>
  </div>

  <!-- ── Priority table ─────────────────────────────── -->
  <div class="glass table-card fade-in-up" style="animation-delay:80ms">
    <div class="table-header">
      <p class="section-title">All Initiatives</p>
      <p class="sort-hint">Click column headers to sort</p>
    </div>

    <div class="table-scroll">
      <table class="data-table">
        <thead>
          <tr>
            <th>Initiative</th>
            <th>Theme</th>
            <th>
              <button class="sort-btn" class:active={sortKey==='volume'} onclick={() => toggleSort('volume')}>
                Volume {sortKey==='volume' ? (sortAsc?'▲':'▼') : ''}
              </button>
            </th>
            <th>
              <button class="sort-btn" class:active={sortKey==='positive_pct'} onclick={() => toggleSort('positive_pct')}>
                Sentiment {sortKey==='positive_pct' ? (sortAsc?'▲':'▼') : ''}
              </button>
            </th>
            <th>
              <button class="sort-btn" class:active={sortKey==='priority_score'} onclick={() => toggleSort('priority_score')}>
                Priority {sortKey==='priority_score' ? (sortAsc?'▲':'▼') : ''}
              </button>
            </th>
            <th>
              <button class="sort-btn" class:active={sortKey==='status'} onclick={() => toggleSort('status')}>
                Status {sortKey==='status' ? (sortAsc?'▲':'▼') : ''}
              </button>
            </th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {#each sorted as item, i (item.roadmap_id)}
            <tr class="data-row fade-in-up" style="animation-delay:{i*30}ms">
              <td><span class="badge badge-indigo">{item.roadmap_id}</span></td>
              <td>
                <div class="theme-cell">
                  <span class="theme-name">{item.theme_name}</span>
                </div>
              </td>
              <td class="num-cell">{item.volume.toLocaleString()}</td>
              <td>
                <div class="sentiment-cell">
                  <div class="sent-track">
                    <div class="sent-fill" style="width:{item.positive_pct}%"></div>
                  </div>
                  <span class="sent-pct" class:sent-good={item.positive_pct>=60} class:sent-bad={item.positive_pct<45}>
                    {item.positive_pct}%
                  </span>
                </div>
              </td>
              <td>
                <div class="prio-cell">
                  <span class="prio-score {priorityClass(item.priority_score)}">{item.priority_score}</span>
                  <span class="prio-label">{priorityLabel(item.priority_score)}</span>
                </div>
              </td>
              <td><span class="badge {statusClass(item.status)}">{item.status}</span></td>
              <td>
                <a href="/feedback?cluster={item.cluster_id}" class="action-link">
                  View feedback
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
                </a>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>

  <!-- ── Priority legend ────────────────────────────── -->
  <div class="glass legend-card fade-in-up" style="animation-delay:140ms">
    <p class="section-title" style="margin-bottom:12px">Priority Score Guide</p>
    <div class="legend-row">
      <span class="prio-score prio-critical" style="min-width:36px;text-align:center">80+</span>
      <span class="legend-desc">Critical — immediate PM attention required, high negative sentiment</span>
    </div>
    <div class="legend-row">
      <span class="prio-score prio-high" style="min-width:36px;text-align:center">60–79</span>
      <span class="legend-desc">High — plan for next sprint, significant user pain</span>
    </div>
    <div class="legend-row">
      <span class="prio-score prio-medium" style="min-width:36px;text-align:center">40–59</span>
      <span class="legend-desc">Medium — schedule in upcoming roadmap cycle</span>
    </div>
    <div class="legend-row">
      <span class="prio-score prio-low" style="min-width:36px;text-align:center">&lt;40</span>
      <span class="legend-desc">Low — monitor, defer to backlog</span>
    </div>
  </div>
</main>

<style>
  main { padding-top: 0; padding-bottom: 72px; }

  /* Summary */
  .summary-row { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:20px; }
  @media (max-width:700px) { .summary-row { grid-template-columns:repeat(2,1fr); } }
  .summary-card { padding:16px 18px; }
  .sum-label { font-size:.72rem; font-weight:600; color:var(--text-muted); text-transform:uppercase; letter-spacing:.05em; margin-bottom:6px; }
  .sum-value { font-size:1.7rem; font-weight:800; color:var(--navy); letter-spacing:-.03em; }
  .sum-value.critical { color:#DC2626; }

  /* Table */
  .table-card { padding:22px 24px; margin-bottom:16px; }
  .table-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:16px; }
  .sort-hint { font-size:.73rem; color:var(--text-subtle); }
  .table-scroll { overflow-x:auto; }
  .data-table { width:100%; border-collapse:collapse; font-size:.83rem; }
  .data-table th { padding:9px 14px; text-align:left; font-size:.71rem; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:.04em; border-bottom:2px solid rgba(15,23,42,.08); white-space:nowrap; }
  .data-table td { padding:12px 14px; border-bottom:1px solid rgba(15,23,42,.055); vertical-align:middle; }
  .data-table tr:last-child td { border-bottom:none; }
  .data-row:hover td { background:rgba(255,255,255,.45); }

  .sort-btn { background:none; border:none; font:inherit; font-size:.71rem; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:.04em; cursor:pointer; padding:0; transition:color var(--transition); }
  .sort-btn.active { color:var(--navy); }

  .theme-cell { display:flex; flex-direction:column; gap:2px; }
  .theme-name { font-weight:600; color:var(--text); font-size:.83rem; }
  .num-cell { font-weight:600; color:var(--text); }

  /* Sentiment */
  .sentiment-cell { display:flex; align-items:center; gap:8px; min-width:120px; }
  .sent-track { flex:1; height:5px; background:rgba(15,23,42,.07); border-radius:6px; overflow:hidden; }
  .sent-fill { height:100%; border-radius:6px; background:linear-gradient(90deg,var(--blue-light),var(--navy)); }
  .sent-pct { font-size:.78rem; font-weight:700; flex-shrink:0; color:var(--text-muted); }
  .sent-good { color:#059669; }
  .sent-bad  { color:#DC2626; }

  /* Priority */
  .prio-cell { display:flex; align-items:center; gap:8px; }
  .prio-score { font-size:.8rem; font-weight:800; padding:3px 8px; border-radius:6px; }
  .prio-critical { background:rgba(220,38,38,.10); color:#DC2626; }
  .prio-high     { background:rgba(217,119,6,.10);  color:#D97706; }
  .prio-medium   { background:rgba(74,144,226,.15);  color:#1A5FAF; }
  .prio-low      { background:rgba(15,23,42,.06);   color:var(--text-muted); }
  .prio-label { font-size:.72rem; color:var(--text-muted); }

  /* Action */
  .action-link { display:inline-flex; align-items:center; gap:4px; font-size:.78rem; font-weight:600; color:var(--navy); text-decoration:none; transition:color var(--transition); }
  .action-link:hover { color:var(--blue); }

  /* Legend */
  .legend-card { padding:18px 22px; }
  .legend-row { display:flex; align-items:center; gap:12px; padding:7px 0; border-bottom:1px solid rgba(15,23,42,.05); }
  .legend-row:last-child { border-bottom:none; }
  .legend-desc { font-size:.81rem; color:var(--text-muted); }
</style>
