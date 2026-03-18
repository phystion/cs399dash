<script lang="ts">
  import { themes as staticThemes, sampleFeedback, type FeedbackItem } from '$lib/data';
  import { API_BASE } from '$lib/api';
  import PageHeader from '$lib/components/PageHeader.svelte';
  import { page } from '$app/stores';

  let { data } = $props();
  const themes = $derived(data.themes ?? staticThemes);

  // Cluster from URL ?cluster=N, default to first
  const urlCluster = $derived(() => {
    const p = $page.url.searchParams.get('cluster');
    const n = p !== null ? parseInt(p) : null;
    return (n !== null && !isNaN(n) && themes.find(t => t.cluster_id === n)) ? n : 0;
  });

  let selectedCid = $state(0);

  $effect(() => {
    selectedCid = urlCluster();
  });

  // Update URL param when selection changes (no navigation, just push state)
  function selectCluster(cid: number) {
    selectedCid = cid;
    const url = new URL(window.location.href);
    url.searchParams.set('cluster', String(cid));
    window.history.replaceState({}, '', url.toString());
  }

  const selectedTheme = $derived(themes.find(t => t.cluster_id === selectedCid)!);

  // Live feedback from API, falling back to pre-sampled static JSON
  let liveFeedback = $state<FeedbackItem[] | null>(null);
  let feedbackLoading = $state(false);

  $effect(() => {
    const cid = selectedCid;
    liveFeedback = null;
    feedbackLoading = true;
    fetch(`${API_BASE}/feedback/${cid}?limit=30`)
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(body => { if (selectedCid === cid) liveFeedback = body.feedback; })
      .catch(() => { /* silently fall back to static */ })
      .finally(() => { if (selectedCid === cid) feedbackLoading = false; });
  });

  const feedbackItems = $derived<FeedbackItem[]>(liveFeedback ?? sampleFeedback[selectedCid] ?? []);

  // Filter state
  type SentFilter = 'all' | 'POSITIVE' | 'NEGATIVE';
  type ChanFilter = 'all' | 'App Review' | 'Support Ticket' | 'Social Media' | 'Beta Testing';

  let sentFilter = $state<SentFilter>('all');
  let chanFilter = $state<ChanFilter>('all');

  const displayFiltered = $derived(feedbackItems.filter(f => {
    if (sentFilter !== 'all' && f.sentiment !== sentFilter) return false;
    if (chanFilter !== 'all' && f.channel !== chanFilter) return false;
    return true;
  }));

  const posCount = $derived(feedbackItems.filter(f => f.sentiment === 'POSITIVE').length);
  const negCount = $derived(feedbackItems.filter(f => f.sentiment === 'NEGATIVE').length);

  const channels = ['all', 'App Review', 'Support Ticket', 'Social Media', 'Beta Testing'] as const;
</script>

<PageHeader
  title="Feedback Explorer"
  subtitle="Browse raw customer quotes by theme, sentiment, and channel."
/>

<main class="page-container">
  <div class="main-grid">
    <!-- ── Theme selector sidebar ──────────────────── -->
    <aside class="themes-sidebar">
      <div class="glass sidebar-card fade-in-up">
        <p class="sidebar-label">Themes</p>
        <div class="theme-list">
          {#each themes as t (t.cluster_id)}
            <button
              class="theme-btn"
              class:active={selectedCid === t.cluster_id}
              onclick={() => selectCluster(t.cluster_id)}
            >
              <div class="tb-info">
                <span class="tb-name">{t.name}</span>
                <span class="tb-vol">{t.volume.toLocaleString()} resp.</span>
              </div>
              <div class="tb-right">
                {#if t.roadmap_id}
                  <span class="badge badge-blue" style="font-size:.62rem">{t.roadmap_id}</span>
                {:else}
                  <span class="badge badge-gray" style="font-size:.62rem">—</span>
                {/if}
                <span
                  class="tb-sent"
                  class:tb-pos={t.positive_pct > 60}
                  class:tb-neg={t.positive_pct < 40}
                >{t.positive_pct}%</span>
              </div>
            </button>
          {/each}
        </div>
      </div>
    </aside>

    <!-- ── Feedback panel ──────────────────────────── -->
    <div class="feedback-col">

      <!-- Theme header card -->
      <div class="glass theme-header-card fade-in-up">
        <div class="th-top">
          <div>
            <div class="th-badges">
              {#if selectedTheme.roadmap_id}
                <span class="badge badge-indigo">{selectedTheme.roadmap_id}</span>
              {:else}
                <span class="badge badge-gray">Unassigned</span>
              {/if}
              <span class="badge badge-blue">Cluster {selectedTheme.cluster_id}</span>
            </div>
            <h2 class="th-name">{selectedTheme.name}</h2>
            <p class="th-desc">{selectedTheme.description}</p>
          </div>
        </div>

        <!-- Mini stats -->
        <div class="th-stats">
          <div class="th-stat">
            <span class="stat-val">{selectedTheme.volume.toLocaleString()}</span>
            <span class="stat-label">Total Responses</span>
          </div>
          <div class="th-stat">
            <span class="stat-val pos">{selectedTheme.positive_pct}%</span>
            <span class="stat-label">Positive</span>
          </div>
          <div class="th-stat">
            <span class="stat-val neg">{selectedTheme.negative_pct}%</span>
            <span class="stat-label">Negative</span>
          </div>
          <div class="th-stat">
            <span class="stat-val">{selectedTheme.priority_score}</span>
            <span class="stat-label">Priority Score</span>
          </div>
        </div>

        <!-- Sentiment bar -->
        <div class="th-bar">
          <div class="th-bar-fill" style="width:{selectedTheme.positive_pct}%"></div>
        </div>
      </div>

      <!-- Filters -->
      <div class="glass filters-card fade-in-up" style="animation-delay:60ms">
        <div class="filters-row">
          <div class="filter-group">
            <span class="filter-label">Sentiment</span>
            <div class="filter-tabs">
              {#each ['all', 'POSITIVE', 'NEGATIVE'] as s}
                <button
                  class="ftab"
                  class:active={sentFilter === s}
                  onclick={() => sentFilter = s as SentFilter}
                >{s === 'all' ? 'All' : s === 'POSITIVE' ? 'Positive' : 'Negative'}</button>
              {/each}
            </div>
          </div>
          <div class="filter-group">
            <span class="filter-label">Channel</span>
            <div class="filter-tabs">
              {#each channels as ch}
                <button
                  class="ftab"
                  class:active={chanFilter === ch}
                  onclick={() => chanFilter = ch as ChanFilter}
                >{ch === 'all' ? 'All' : ch}</button>
              {/each}
            </div>
          </div>
        </div>
        <div class="filter-meta">
          <span>{displayFiltered.length} quotes · {posCount} pos / {negCount} neg</span>
        </div>
      </div>

      <!-- Quote cards -->
      {#if displayFiltered.length === 0}
        <div class="glass empty-state fade-in-up">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="rgba(15,23,42,0.18)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          <p>No quotes match these filters</p>
        </div>
      {:else}
        <div class="quotes-list">
          {#each displayFiltered as item, i (i)}
            <div class="glass quote-card fade-in-up" style="animation-delay:{i*40}ms" class:quote-pos={item.sentiment==='POSITIVE'} class:quote-neg={item.sentiment==='NEGATIVE'}>
              <div class="quote-header">
                <span class="quote-sent" class:qs-pos={item.sentiment==='POSITIVE'} class:qs-neg={item.sentiment==='NEGATIVE'}>
                  {item.sentiment === 'POSITIVE' ? 'Positive' : 'Negative'}
                </span>
                <span class="quote-channel">{item.channel}</span>
              </div>
              <p class="quote-text">"{item.text}"</p>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</main>

<style>
  main { padding-top: 0; padding-bottom: 72px; }

  .main-grid { display:grid; grid-template-columns:280px 1fr; gap:20px; align-items:start; }
  @media (max-width:960px) { .main-grid { grid-template-columns:1fr; } }

  /* Sidebar */
  .sidebar-card { padding:16px; }
  .sidebar-label { font-size:.72rem; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:.05em; margin-bottom:10px; display:block; }
  .theme-list { display:flex; flex-direction:column; gap:3px; }
  .theme-btn {
    display:flex; align-items:center; justify-content:space-between; gap:8px;
    width:100%; padding:9px 10px;
    background:transparent; border:1px solid transparent;
    border-radius:var(--radius-sm); cursor:pointer; text-align:left;
    transition:background var(--transition), border-color var(--transition);
  }
  .theme-btn:hover { background:rgba(255,255,255,.55); }
  .theme-btn.active { background:rgba(27,58,107,.08); border-color:rgba(27,58,107,.20); }
  .tb-info { display:flex; flex-direction:column; gap:2px; flex:1; min-width:0; }
  .tb-name { font-size:.8rem; font-weight:600; color:var(--text); }
  .tb-vol  { font-size:.7rem; color:var(--text-muted); }
  .tb-right { display:flex; flex-direction:column; align-items:flex-end; gap:3px; flex-shrink:0; }
  .tb-sent { font-size:.74rem; font-weight:700; color:var(--text-muted); }
  .tb-pos { color:#059669; }
  .tb-neg { color:#DC2626; }

  /* Feedback col */
  .feedback-col { display:flex; flex-direction:column; gap:14px; }

  /* Theme header */
  .theme-header-card { padding:20px 22px; }
  .th-top { margin-bottom:14px; }
  .th-badges { display:flex; gap:6px; margin-bottom:8px; flex-wrap:wrap; }
  .th-name { font-size:1.2rem; font-weight:800; color:var(--text); margin-bottom:4px; letter-spacing:-.015em; }
  .th-desc { font-size:.82rem; color:var(--text-muted); line-height:1.5; }
  .th-stats { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:12px; }
  @media (max-width:600px) { .th-stats { grid-template-columns:repeat(2,1fr); } }
  .th-stat { display:flex; flex-direction:column; gap:2px; }
  .stat-val { font-size:1.2rem; font-weight:800; color:var(--navy); letter-spacing:-.02em; }
  .stat-val.pos { color:#059669; }
  .stat-val.neg { color:#DC2626; }
  .stat-label { font-size:.69rem; color:var(--text-muted); text-transform:uppercase; letter-spacing:.04em; font-weight:600; }
  .th-bar { height:4px; background:rgba(15,23,42,.07); border-radius:6px; overflow:hidden; }
  .th-bar-fill { height:100%; background:linear-gradient(90deg,var(--blue-light),var(--navy)); border-radius:6px; transition:width .7s var(--ease); }

  /* Filters */
  .filters-card { padding:14px 18px; }
  .filters-row { display:flex; flex-wrap:wrap; gap:16px; margin-bottom:10px; }
  .filter-group { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
  .filter-label { font-size:.72rem; font-weight:600; color:var(--text-muted); text-transform:uppercase; letter-spacing:.04em; flex-shrink:0; }
  .filter-tabs { display:flex; gap:4px; }
  .ftab {
    padding:4px 10px; font-size:.74rem; font-weight:500; color:var(--text-muted);
    background:rgba(15,23,42,.05); border:1px solid transparent;
    border-radius:6px; cursor:pointer; transition:all var(--transition);
  }
  .ftab.active { background:rgba(27,58,107,.10); color:var(--navy); border-color:rgba(27,58,107,.20); font-weight:700; }
  .ftab:hover:not(.active) { background:rgba(15,23,42,.09); color:var(--text); }
  .filter-meta { display:flex; align-items:center; gap:10px; font-size:.74rem; color:var(--text-muted); }

  /* Empty state */
  .empty-state { padding:36px 24px; display:flex; flex-direction:column; align-items:center; gap:12px; text-align:center; }
  .empty-state p { font-size:.85rem; color:var(--text-muted); }

  /* Quotes */
  .quotes-list { display:flex; flex-direction:column; gap:10px; }
  .quote-card { padding:16px 20px; border-left:3px solid transparent; }
  .quote-card.quote-pos { border-left-color:rgba(5,150,105,.35); }
  .quote-card.quote-neg { border-left-color:rgba(220,38,38,.35); }
  .quote-header { display:flex; align-items:center; gap:8px; margin-bottom:8px; }
  .quote-sent { font-size:.68rem; font-weight:700; padding:2px 8px; border-radius:6px; }
  .qs-pos { background:rgba(5,150,105,.10); color:#059669; }
  .qs-neg { background:rgba(220,38,38,.10); color:#DC2626; }
  .quote-channel { font-size:.71rem; color:var(--text-subtle); }
  .quote-text { font-size:.875rem; color:var(--text); line-height:1.55; font-style:italic; }
</style>
