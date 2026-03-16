<script lang="ts">
  import { themes } from '$lib/data';
  import { topicTagsStore, toggleTag, addCustomTag, removeTag, PRESET_TAGS } from '$lib/tagStore';
  import PageHeader from '$lib/components/PageHeader.svelte';

  // ── Sentiment filter ─────────────────────────────────────────
  type SentFilter = 'all' | 'positive' | 'negative' | 'mixed';
  let sentFilter = $state<SentFilter>('all');

  const SENT_FILTERS: { value: SentFilter; label: string }[] = [
    { value: 'all',      label: 'All'      },
    { value: 'positive', label: 'Positive' },
    { value: 'negative', label: 'Negative' },
    { value: 'mixed',    label: 'Mixed'    },
  ];

  // ── Sort state ───────────────────────────────────────────────
  type SortKey = 'rank' | 'sentiment' | 'comments';
  let sortKey = $state<SortKey>('rank');
  let sortDir = $state<'asc' | 'desc'>('desc');

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      sortDir = sortDir === 'desc' ? 'asc' : 'desc';
    } else {
      sortKey = key;
      sortDir = 'desc';
    }
  }

  function sortIcon(key: SortKey) {
    if (sortKey !== key) return '';
    return sortDir === 'desc' ? '▼' : '▲';
  }

  function rowRank(index: number, total: number) {
    return sortDir === 'desc' ? index + 1 : total - index;
  }

  // ── Filtered + sorted data ───────────────────────────────────
  const filteredSorted = $derived(() => {
    let items = themes.filter(t => {
      if (sentFilter === 'positive') return t.positive_pct >= 60;
      if (sentFilter === 'negative') return t.positive_pct < 45;
      if (sentFilter === 'mixed')    return t.positive_pct >= 45 && t.positive_pct < 60;
      return true;
    });

    items = [...items].sort((a, b) => {
      let diff = 0;
      if (sortKey === 'rank')      diff = b.priority_score - a.priority_score;
      if (sortKey === 'sentiment') diff = b.positive_pct   - a.positive_pct;
      if (sortKey === 'comments')  diff = b.volume         - a.volume;
      return sortDir === 'desc' ? diff : -diff;
    });

    return items;
  });

  // ── Tags ─────────────────────────────────────────────────────
  let openTagDropdown = $state<number | null>(null);
  let customTagInput  = $state('');

  function handleAddCustom(cid: number) {
    addCustomTag(cid, customTagInput);
    customTagInput = '';
  }

  // ── Sentiment display helpers ────────────────────────────────
  function sentLabel(t: typeof themes[0]) {
    if (t.positive_pct >= 60) return 'Positive';
    if (t.positive_pct >= 45) return 'Mixed';
    return 'Negative';
  }
  function sentClass(t: typeof themes[0]) {
    if (t.positive_pct >= 60) return 'pos';
    if (t.positive_pct >= 45) return 'mixed';
    return 'neg';
  }
</script>

<PageHeader
  title="Theme Analysis"
  subtitle="10 feedback clusters ranked by volume and sentiment — spot which themes need immediate attention."
>
  <div class="record-count">
    <span class="rc-num">{filteredSorted().length}</span>
    <span class="rc-label">themes</span>
  </div>
</PageHeader>

<main class="page-container">
  <!-- ── Sentiment filter bar ─────────────────────────────── -->
  <div class="glass-sm filter-bar fade-in-up">
    <span class="filter-label">Sentiment</span>
    <div class="filter-tabs">
      {#each SENT_FILTERS as sf}
        <button
          class="ftab"
          class:active={sentFilter === sf.value}
          onclick={() => sentFilter = sf.value}
        >{sf.label}</button>
      {/each}
    </div>
  </div>

  <!-- ── Analysis table ───────────────────────────────────── -->
  <div class="glass table-card fade-in-up" style="animation-delay:60ms">
    <div class="table-scroll">
      <table class="analysis-table">
        <thead>
          <tr>
            <th class="col-tags">Tags</th>
            <th class="col-rank">
              <button class="sort-btn" class:active={sortKey==='rank'} onclick={() => toggleSort('rank')}>
                Rank {sortIcon('rank')}
              </button>
            </th>
            <th class="col-topic">Topic</th>
            <th class="col-sent">
              <button class="sort-btn" class:active={sortKey==='sentiment'} onclick={() => toggleSort('sentiment')}>
                Sentiment {sortIcon('sentiment')}
              </button>
            </th>
            <th class="col-comments">
              <button class="sort-btn" class:active={sortKey==='comments'} onclick={() => toggleSort('comments')}>
                Comments {sortIcon('comments')}
              </button>
            </th>
          </tr>
        </thead>
        <tbody>
          {#each filteredSorted() as t, i (t.cluster_id)}
            <tr class="data-row fade-in-up" style="animation-delay:{i * 28}ms">

              <!-- Tags column -->
              <td class="col-tags">
                <div class="tag-cell">
                  {#each ($topicTagsStore[t.cluster_id] ?? []) as tag}
                    <span class="tag-chip-sm">{tag}</span>
                  {/each}
                  <div class="tag-trigger">
                    <button
                      class="add-tag-icon"
                      onclick={(e) => { e.stopPropagation(); openTagDropdown = openTagDropdown === t.cluster_id ? null : t.cluster_id; }}
                      aria-label="Add tag"
                      title="Add tag"
                    >
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                           stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/>
                        <line x1="7" y1="7" x2="7.01" y2="7"/>
                      </svg>
                    </button>

                    {#if openTagDropdown === t.cluster_id}
                      <button type="button" class="overlay" onclick={() => openTagDropdown = null} aria-label="Close tag menu"></button>
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
                        {#each ($topicTagsStore[t.cluster_id] ?? []) as tag}
                          <button class="tag-existing" onclick={() => removeTag(t.cluster_id, tag)}>
                            {tag} ×
                          </button>
                        {/each}
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
              </td>

              <!-- Rank -->
              <td class="col-rank">
                <span class="rank-badge">{rowRank(i, filteredSorted().length)}</span>
              </td>

              <!-- Topic + preview -->
              <td class="col-topic">
                <div class="topic-cell">
                  <span class="topic-name">{t.name}</span>
                  <span class="topic-preview">{t.description.length > 85 ? t.description.slice(0, 85) + '…' : t.description}</span>
                </div>
              </td>

              <!-- Sentiment -->
              <td class="col-sent">
                <div class="sent-cell">
                  <div class="sent-bar-wrap">
                    <div class="sent-bar">
                      <div class="sent-fill" style="width:{t.positive_pct}%"></div>
                    </div>
                  </div>
                  <span class="sent-badge sent-{sentClass(t)}">{sentLabel(t)}</span>
                </div>
              </td>

              <!-- Comments -->
              <td class="col-comments">
                <span class="comment-num">{t.volume.toLocaleString()}</span>
              </td>
            </tr>
          {/each}

          {#if filteredSorted().length === 0}
            <tr>
              <td colspan="5" class="empty-row">No topics match this filter.</td>
            </tr>
          {/if}
        </tbody>
      </table>
    </div>
  </div>

</main>

<style>
  main { padding-top: 0; padding-bottom: 72px; }

  .record-count { text-align:right; flex-shrink:0; }
  .rc-num { display:block; font-size:2rem; font-weight:800; color:var(--navy); letter-spacing:-.04em; line-height:1; }
  .rc-label { font-size:.72rem; color:var(--text-subtle); text-transform:uppercase; letter-spacing:.05em; font-weight:600; }

  /* Filter bar */
  .filter-bar {
    display:flex; align-items:center; gap:12px; padding:10px 16px;
    margin-bottom:14px; border-radius:var(--radius);
  }
  .filter-label { font-size:.72rem; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:.05em; flex-shrink:0; }
  .filter-tabs { display:flex; gap:4px; }
  .ftab {
    padding:5px 12px; font-size:.78rem; font-weight:500; color:var(--text-muted);
    background:transparent; border:1px solid transparent; border-radius:6px; cursor:pointer;
    transition:all var(--transition);
  }
  .ftab:hover { background:rgba(27,58,107,.06); color:var(--text); }
  .ftab.active { background:rgba(27,58,107,.10); color:var(--navy); border-color:rgba(27,58,107,.20); font-weight:700; }

  /* Table */
  .table-card { padding:0; overflow:hidden; }
  .table-scroll { overflow-x:auto; }
  .analysis-table { width:100%; border-collapse:collapse; font-size:.84rem; }

  .analysis-table thead th {
    padding:12px 14px; text-align:left; font-size:.70rem; font-weight:700;
    color:var(--text-muted); text-transform:uppercase; letter-spacing:.04em;
    border-bottom:1px solid rgba(27,58,107,.09); white-space:nowrap;
    background:rgba(255,255,255,.40);
  }

  .analysis-table tbody td {
    padding:13px 14px; border-bottom:1px solid rgba(27,58,107,.055); vertical-align:middle;
  }
  .data-row:last-child td { border-bottom:none; }
  .data-row:hover td { background:rgba(255,255,255,.50); }

  /* Sort button */
  .sort-btn {
    background:none; border:none; font:inherit; font-size:.70rem; font-weight:700;
    color:var(--text-muted); text-transform:uppercase; letter-spacing:.04em;
    cursor:pointer; padding:0; transition:color var(--transition); white-space:nowrap;
  }
  .sort-btn:hover, .sort-btn.active { color:var(--navy); }

  /* Column widths */
  .col-tags     { width:120px; min-width:90px; }
  .col-rank     { width:64px; text-align:center; }
  .col-topic    { min-width:200px; }
  .col-sent     { width:180px; min-width:150px; }
  .col-comments { width:100px; text-align:right; white-space:nowrap; }

  /* Tags cell */
  .tag-cell { display:flex; align-items:center; gap:4px; flex-wrap:wrap; }
  .tag-chip-sm {
    display:inline-flex; align-items:center;
    padding:2px 7px; background:rgba(27,58,107,.09); color:var(--navy);
    border-radius:6px; font-size:.66rem; font-weight:600; white-space:nowrap;
  }

  .tag-trigger { position:relative; flex-shrink:0; }

  .add-tag-icon {
    display:flex; align-items:center; justify-content:center;
    width:26px; height:26px; border-radius:7px;
    color:var(--text-subtle); background:transparent; border:1px solid rgba(27,58,107,.12);
    cursor:pointer; transition:all var(--transition);
  }
  .add-tag-icon:hover { background:rgba(74,144,226,.10); color:var(--navy); border-color:rgba(74,144,226,.30); }

  /* Tag dropdown */
  .overlay {
    position: fixed;
    inset: 0;
    z-index: 49;
    border: none;
    background: transparent;
    padding: 0;
    margin: 0;
  }
  .tag-dropdown {
    position:absolute; top:calc(100% + 4px); left:0; z-index:51;
    padding:10px; min-width:210px; border-radius:var(--radius);
  }
  .tag-presets { display:flex; flex-wrap:wrap; gap:5px; margin-bottom:8px; }
  .tag-preset {
    padding:3px 9px; font-size:.71rem; font-weight:500; color:var(--text-muted);
    background:rgba(15,23,42,.05); border:1px solid transparent;
    border-radius:6px; cursor:pointer; transition:all var(--transition);
  }
  .tag-preset:hover { background:rgba(74,144,226,.10); color:var(--navy); }
  .tag-preset.preset-active { background:rgba(27,58,107,.10); color:var(--navy); border-color:rgba(27,58,107,.20); font-weight:700; }
  .tag-existing {
    display:inline-flex; align-items:center; gap:4px;
    padding:2px 7px; font-size:.70rem; font-weight:500;
    background:rgba(27,58,107,.09); color:var(--navy); border-radius:6px;
    border:none; cursor:pointer; margin:0 3px 5px 0;
    transition:background var(--transition);
  }
  .tag-existing:hover { background:rgba(220,38,38,.10); color:#DC2626; }
  .tag-custom-row { display:flex; gap:6px; margin-top:8px; }
  .tag-custom-input {
    flex:1; padding:5px 9px; font-size:.77rem;
    background:#fff; border:1px solid rgba(15,23,42,.13);
    border-radius:var(--radius-sm); outline:none; width:auto;
    transition:border-color var(--transition);
  }
  .tag-custom-input:focus { border-color:var(--blue); }
  .tag-add-btn {
    padding:5px 10px; font-size:.77rem; font-weight:600; color:#fff;
    background:var(--navy); border:none; border-radius:var(--radius-sm); cursor:pointer;
    transition:background var(--transition);
  }
  .tag-add-btn:hover { background:#142d5a; }

  /* Rank */
  .rank-badge {
    display:inline-flex; align-items:center; justify-content:center;
    width:26px; height:26px; border-radius:6px;
    background:rgba(27,58,107,.07); font-size:.75rem; font-weight:800;
    color:var(--text-muted);
  }

  /* Topic cell */
  .topic-cell { display:flex; flex-direction:column; gap:3px; }
  .topic-name { font-size:.87rem; font-weight:700; color:var(--text); }
  .topic-preview { font-size:.76rem; color:var(--text-muted); line-height:1.4; }

  /* Sentiment cell */
  .sent-cell { display:flex; flex-direction:column; gap:5px; }
  .sent-bar-wrap { display:flex; align-items:center; gap:8px; }
  .sent-bar { flex:1; height:4px; background:rgba(15,23,42,.07); border-radius:6px; overflow:hidden; max-width:100px; }
  .sent-fill { height:100%; background:linear-gradient(90deg,var(--blue-light),var(--navy)); border-radius:6px; }

  .sent-badge { display:inline-block; font-size:.68rem; font-weight:700; padding:2px 7px; border-radius:6px; }
  .sent-pos  { background:rgba(5,150,105,.10);  color:#059669; }
  .sent-neg  { background:rgba(220,38,38,.10);  color:#DC2626; }
  .sent-mixed{ background:rgba(74,144,226,.12); color:#1A5FAF; }

  /* Comments */
  .comment-num { font-size:.88rem; font-weight:700; color:var(--text); }

  /* Empty */
  .empty-row { text-align:center; padding:36px; color:var(--text-subtle); font-size:.85rem; }
</style>
