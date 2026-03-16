<script lang="ts">
  import { flip } from 'svelte/animate';
  import { themes, monthlyTrends, getTrend } from '$lib/data';
  import PageHeader from '$lib/components/PageHeader.svelte';

  // ── Time range types ─────────────────────────────────────────
  type TimeRange = 'week' | 'month' | 'quarter' | 'year';
  type InfoMode  = 'volume' | 'sentiment' | 'priority' | 'channel';
  type ChartType = 'line' | 'bar';

  let timeRange  = $state<TimeRange>('month');
  let infoMode   = $state<InfoMode>('volume');
  let chartType  = $state<ChartType>('line');
  let showCal    = $state(false);

  // Calendar: start/end month index into monthlyTrends
  let calStart = $state(0);
  let calEnd   = $state(monthlyTrends.length - 1);
  let calPickingEnd = $state(false);

  // Comparison cluster selection (max 3)
  let compIds = $state<number[]>([0, 1, 8]);
  const PALETTE = ['#1B3A6B', '#DC2626', '#4A90E2', '#059669', '#7C3AED'];

  function toggleComp(cid: number) {
    if (compIds.includes(cid)) {
      if (compIds.length > 1) compIds = compIds.filter(c => c !== cid);
    } else {
      if (compIds.length < 5) compIds = [...compIds, cid];
    }
  }

  // ── Build data points for current view ───────────────────────
  const rawData = $derived(monthlyTrends.slice(calStart, calEnd + 1));

  // Aggregate into quarters from rawData
  function buildQuarters(data: typeof monthlyTrends) {
    const out: { label: string; vols: number[] }[] = [];
    for (let i = 0; i < data.length; i += 3) {
      const chunk = data.slice(i, i + 3);
      const label = 'Q' + (Math.floor(i / 3) + 1) + ' ' + chunk[0].month.split(' ')[1];
      const vols = Array(10).fill(0).map((_, c) => chunk.reduce((s, m) => s + m.volumes[c], 0));
      out.push({ label, vols });
    }
    return out;
  }

  // Aggregate into calendar years from rawData
  function buildYears(data: typeof monthlyTrends) {
    const groups = new Map<string, number[]>();
    for (const m of data) {
      const year = m.month.split(' ')[1];
      if (!groups.has(year)) groups.set(year, Array(10).fill(0));
      const acc = groups.get(year)!;
      m.volumes.forEach((v, i) => { acc[i] += v; });
    }
    return Array.from(groups.entries()).map(([label, vols]) => ({ label, vols }));
  }

  // Simulate weekly from monthly (interpolate 4 points per month)
  function buildWeeks(data: typeof monthlyTrends) {
    const out: { label: string; vols: number[] }[] = [];
    data.forEach((m, mi) => {
      const next = data[mi + 1] ?? m;
      for (let w = 0; w < 4; w++) {
        const t = w / 4;
        const vols = m.volumes.map((v, c) => Math.round(v / 4 + (next.volumes[c] - v) * t / 4));
        out.push({ label: `${m.month_short} W${w + 1}`, vols });
      }
    });
    return out.slice(0, 24); // max 24 weeks shown
  }

  // Derive display points based on timeRange
  const displayPoints = $derived(() => {
    switch (timeRange) {
      case 'quarter': {
        const qs = buildQuarters(rawData);
        return qs.map(q => ({ label: q.label, vols: q.vols }));
      }
      case 'year': {
        return buildYears(rawData);
      }
      case 'week': {
        const wks = buildWeeks(rawData);
        return wks.map(w => ({ label: w.label, vols: w.vols }));
      }
      default: // month
        return rawData.map(m => ({ label: m.month_short, vols: m.volumes }));
    }
  });

  // ── Chart geometry ───────────────────────────────────────────
  const W = 700; const H = 200;
  const PAD = { t: 16, r: 24, b: 32, l: 44 };
  const IW = W - PAD.l - PAD.r;
  const IH = H - PAD.t - PAD.b;

  const CHANNEL_SPLIT = [
    { label: 'App Review', weight: 0.28 },
    { label: 'Support Ticket', weight: 0.24 },
    { label: 'Social Media', weight: 0.26 },
    { label: 'Beta Testing', weight: 0.22 },
  ] as const;

  const compData = $derived(() => {
    const points = displayPoints();

    if (infoMode === 'sentiment') {
      return [
        {
          cid: 100,
          label: 'Positive',
          vals: points.map((p) =>
            Math.round(themes.reduce((sum, t) => sum + p.vols[t.cluster_id] * (t.positive_pct / 100), 0))
          ),
          stroke: '#059669',
        },
        {
          cid: 101,
          label: 'Needs Attention',
          vals: points.map((p) =>
            Math.round(themes.reduce((sum, t) => sum + p.vols[t.cluster_id] * (t.negative_pct / 100), 0))
          ),
          stroke: '#DC2626',
        },
      ];
    }

    if (infoMode === 'priority') {
      const topPriority = [...themes]
        .filter((t) => t.roadmap_id)
        .sort((a, b) => b.priority_score - a.priority_score)
        .slice(0, 3);

      return topPriority.map((t, idx) => ({
        cid: t.cluster_id,
        label: t.name.split(' ').slice(0, 2).join(' '),
        vals: points.map((p) => Math.round(p.vols[t.cluster_id] * (t.priority_score / 100))),
        stroke: PALETTE[idx % PALETTE.length],
      }));
    }

    if (infoMode === 'channel') {
      const totals = points.map((p) => p.vols.reduce((sum, v) => sum + v, 0));
      return CHANNEL_SPLIT.map((c, idx) => ({
        cid: 200 + idx,
        label: c.label,
        vals: totals.map((t) => Math.round(t * c.weight)),
        stroke: PALETTE[idx % PALETTE.length],
      }));
    }

    return compIds.map((cid, idx) => ({
      cid,
      label: themes.find((t) => t.cluster_id === cid)!.name.split(' ').slice(0, 2).join(' '),
      vals: points.map((p) => p.vols[cid]),
      stroke: PALETTE[idx % PALETTE.length],
    }));
  });

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

  const allVals = $derived(() => compData().flatMap((d) => d.vals));
  const lineTickData = $derived(() => {
    const vals = allVals();
    if (!vals.length) return { lo: 0, hi: 100, ticks: [0, 25, 50, 75, 100] };
    return niceLineTicks(0, Math.max(...vals), 5);
  });
  const yMin = $derived(() => lineTickData().lo);
  const yMax = $derived(() => lineTickData().hi);
  const pts = $derived(() => displayPoints());
  const barW = $derived(() => (pts().length > 1 ? (IW / pts().length) * 0.55 : 40));

  function xp(i: number) {
    if (pts().length <= 1) return PAD.l + IW / 2;
    return PAD.l + (i / (pts().length - 1)) * IW;
  }
  function yp(v: number) { return PAD.t + IH - ((v - yMin()) / Math.max(yMax() - yMin(), 1)) * IH; }

  function linePath(vals: number[]) {
    return vals.map((v, i) => `${i===0?'M':'L'}${xp(i).toFixed(1)},${yp(v).toFixed(1)}`).join(' ');
  }
  function areaPath(vals: number[]) {
    const b = PAD.t + IH;
    if (vals.length < 2) return '';
    const pts2 = vals.map((v, i) => `${xp(i).toFixed(1)},${yp(v).toFixed(1)}`).join(' L');
    return `M${xp(0).toFixed(1)},${b} L${pts2} L${xp(vals.length-1).toFixed(1)},${b} Z`;
  }

  const yTicks = $derived(() => lineTickData().ticks.map((v) => ({ v, y: yp(v) })));

  // ── Info mode data ───────────────────────────────────────────
  type MoverItem = { name: string; value: string; sub: string; isGood: boolean };

  const moverData = $derived((): MoverItem[] => {
    switch (infoMode) {
      case 'volume':
        return [...themes]
          .map(t => ({ ...t, trend: getTrend(t.cluster_id) }))
          .sort((a, b) => Math.abs(b.trend) - Math.abs(a.trend))
          .slice(0, 6)
          .map(t => ({
            name: t.name, isGood: t.trend >= 0,
            value: (t.trend >= 0 ? '+' : '') + t.trend + '%',
            sub: t.volume.toLocaleString() + ' responses',
          }));
      case 'sentiment':
        return [...themes]
          .sort((a, b) => b.negative_pct - a.negative_pct)
          .slice(0, 6)
          .map(t => ({
            name: t.name, isGood: t.positive_pct >= 55,
            value: t.positive_pct + '%',
            sub: t.negative_pct + '% negative',
          }));
      case 'priority':
        return [...themes]
          .filter(t => t.roadmap_id)
          .sort((a, b) => b.priority_score - a.priority_score)
          .map(t => ({
            name: t.name, isGood: t.priority_score < 60,
            value: String(t.priority_score),
            sub: (t.roadmap_id ?? 'Unassigned') + ' · ' + t.volume.toLocaleString() + ' resp.',
          }));
      case 'channel':
        const channelData = [
          { name: 'App Review',     pct: 28, count: 5600 },
          { name: 'Support Ticket', pct: 24, count: 4800 },
          { name: 'Social Media',   pct: 26, count: 5200 },
          { name: 'Beta Testing',   pct: 22, count: 4400 },
        ];
        return channelData.map(c => ({
          name: c.name, isGood: true,
          value: c.pct + '%',
          sub: c.count.toLocaleString() + ' total',
        }));
    }
  });

  // ── Calendar helpers ─────────────────────────────────────────
  function calClick(i: number) {
    if (!calPickingEnd) {
      calStart = i; calEnd = i; calPickingEnd = true;
    } else {
      if (i < calStart) { calEnd = calStart; calStart = i; }
      else calEnd = i;
      calPickingEnd = false;
      showCal = false;
    }
  }

  const rangeLabel = $derived(
    calStart === 0 && calEnd === monthlyTrends.length - 1
      ? 'All time'
      : monthlyTrends[calStart].month + ' – ' + monthlyTrends[calEnd].month
  );

  // ── Hover state ──────────────────────────────────────────────
  let trendHover = $state<number | null>(null);

  const trendBands = $derived(
    pts().map((_, i) => {
      const left  = i === 0              ? PAD.l     : (xp(i - 1) + xp(i)) / 2;
      const right = i === pts().length - 1 ? W - PAD.r : (xp(i) + xp(i + 1)) / 2;
      return { idx: i, left, width: right - left };
    })
  );

  const trendHoverData = $derived(
    trendHover !== null && trendHover < pts().length
      ? {
          idx:   trendHover,
          label: pts()[trendHover].label,
          x:     xp(trendHover),
          rows:  compData().map(d => ({ label: d.label, color: d.stroke, value: d.vals[trendHover!] ?? 0 })),
        }
      : null
  );

  const trendTooltipPos = $derived(
    trendHoverData !== null && compData().length > 0
      ? (() => {
          const xPct = ((trendHoverData.x - PAD.l) / IW) * 100;
          const avgY = compData().reduce((s, d) => s + yp(d.vals[trendHoverData.idx] ?? 0), 0) / compData().length;
          const yPct = (avgY / H) * 100;
          return { xPct, yPct };
        })()
      : null
  );

  function tipXTranslate(pct: number): string {
    if (pct < 12) return '0%';
    if (pct > 88) return '-100%';
    return '-50%';
  }

</script>

<PageHeader
  title="Trend Analysis"
  subtitle="Volume, sentiment, and priority signals over time across wearable device feedback themes."
/>

<main class="page-container">
  <!-- ── Controls bar ─────────────────────────────── -->
  <div class="glass controls-bar fade-in-up">
    <!-- Time range -->
    <div class="ctrl-group">
      <span class="ctrl-label">Range</span>
      <div class="ctrl-tabs">
        {#each (['week','month','quarter','year'] as TimeRange[]) as tr}
          <button class="ctab" class:active={timeRange===tr} onclick={()=>timeRange=tr}>
            {tr.charAt(0).toUpperCase()+tr.slice(1)}
          </button>
        {/each}
      </div>
    </div>

    <!-- Calendar date picker -->
    <div class="ctrl-group" style="position:relative">
      <span class="ctrl-label">Period</span>
      <button class="cal-btn" onclick={()=>showCal=!showCal}>
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
        {rangeLabel}
      </button>
      {#if showCal}
        <div class="cal-popup glass" role="dialog" aria-label="Select date range">
          <p class="cal-hint">{calPickingEnd ? 'Click end month' : 'Click start month'}</p>
          <div class="cal-grid">
            {#each monthlyTrends as m, i}
              <button
                class="cal-cell"
                class:cal-in={i >= calStart && i <= calEnd}
                class:cal-edge={i === calStart || i === calEnd}
                onclick={() => calClick(i)}
              >{m.month_short}<span class="cal-yr">{m.month.split(' ')[1].slice(2)}</span></button>
            {/each}
          </div>
          <button class="cal-reset" onclick={() => { calStart=0; calEnd=monthlyTrends.length-1; showCal=false; calPickingEnd=false; }}>Reset to all time</button>
        </div>
      {/if}
    </div>

    <!-- Chart type -->
    <div class="ctrl-group">
      <span class="ctrl-label">Style</span>
      <div class="ctrl-tabs">
        {#each (['line','bar'] as ChartType[]) as ct}
          <button class="ctab" class:active={chartType===ct} onclick={()=>chartType=ct}>
            {ct.charAt(0).toUpperCase()+ct.slice(1)}
          </button>
        {/each}
      </div>
    </div>

    <!-- Info mode -->
    <div class="ctrl-group">
      <span class="ctrl-label">View</span>
      <div class="ctrl-tabs">
        {#each (['volume','sentiment','priority','channel'] as InfoMode[]) as m}
          <button class="ctab" class:active={infoMode===m} onclick={()=>infoMode=m}>
            {m.charAt(0).toUpperCase()+m.slice(1)}
          </button>
        {/each}
      </div>
    </div>
  </div>

  <!-- ── Main chart ─────────────────────────────── -->
  <div class="glass chart-card fade-in-up" style="animation-delay:60ms">
    <div class="chart-top">
      <div>
        <p class="section-title">
          {infoMode === 'volume' ? 'Volume Over Time' :
           infoMode === 'sentiment' ? 'Sentiment Trend' :
           infoMode === 'priority' ? 'Priority by Theme' : 'Channel Volume'}
        </p>
        <p class="chart-sub">{rangeLabel} · {pts().length} {timeRange === 'week' ? 'weeks' : timeRange === 'quarter' ? 'quarters' : timeRange === 'year' ? 'years' : 'months'}</p>
      </div>
      <div class="chart-top-right">
        <div class="chart-legend">
          {#each compData() as d}
            <span class="legend-item">
              <span class="legend-dot" style="background:{d.stroke};"></span>{d.label}
            </span>
          {/each}
        </div>
        <button class="print-btn" onclick={() => window.print()}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/>
          </svg>
          Print
        </button>
      </div>
    </div>

    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div class="chart-svg-wrap" onmouseleave={() => trendHover = null}>
      {#if pts().length >= 1}
        <svg viewBox="0 0 {W} {H}" class="chart-svg" aria-hidden="true">
          <defs>
            {#each compData() as d}
              <linearGradient id="cg{d.cid}" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%"   stop-color={d.stroke} stop-opacity="0.18"/>
                <stop offset="100%" stop-color={d.stroke} stop-opacity="0"/>
              </linearGradient>
            {/each}
          </defs>

          {#each yTicks() as tick}
            <line x1={PAD.l} y1={tick.y} x2={W-PAD.r} y2={tick.y} stroke="rgba(15,23,42,.07)" stroke-width="1"/>
            <text x={PAD.l-6} y={tick.y+4} font-size="9.5" fill="rgba(15,23,42,.32)" text-anchor="end">{Math.round(tick.v)}</text>
          {/each}

          {#each pts() as p, i}
            {#if i % Math.max(1, Math.floor(pts().length / 8)) === 0}
              <text x={xp(i)} y={H-4} font-size="9.5" fill="rgba(15,23,42,.38)" text-anchor="middle">{p.label}</text>
            {/if}
          {/each}

          {#each compData() as d}
            {#if chartType === 'bar'}
              {#each d.vals as v, i}
                {@const bx = xp(i) - barW() / 2}
                {@const bh = yp(yMin()) - yp(v)}
                <rect x={bx} y={yp(v)} width={barW()} height={bh} fill={d.stroke} opacity="0.7" rx="2"/>
              {/each}
            {:else}
              <path d={areaPath(d.vals)} fill="url(#cg{d.cid})"/>
              <path d={linePath(d.vals)} stroke={d.stroke} stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
              <circle cx={xp(d.vals.length-1)} cy={yp(d.vals[d.vals.length-1])} r="3.5" fill={d.stroke} stroke="#fff" stroke-width="1.5"/>
            {/if}
          {/each}

          {#if trendHoverData && chartType !== 'bar'}
            <line x1={trendHoverData.x} y1={PAD.t} x2={trendHoverData.x} y2={H - PAD.b} stroke="rgba(27,58,107,.24)" stroke-width="1" stroke-dasharray="3 3"/>
            {#each compData() as d}
              <circle cx={trendHoverData.x} cy={yp(d.vals[trendHoverData.idx])} r="4" fill={d.stroke} stroke="#fff" stroke-width="1.5"/>
            {/each}
          {/if}

          {#each trendBands as b}
            <!-- svelte-ignore a11y_no_static_element_interactions -->
            <rect x={b.left} y={PAD.t} width={b.width} height={IH} fill="transparent" onmouseenter={() => trendHover = b.idx}/>
          {/each}
        </svg>

        {#if trendHoverData && trendTooltipPos}
          <div class="chart-tip" style="left:{trendTooltipPos.xPct}%; top:{trendTooltipPos.yPct}%; transform:translate({tipXTranslate(trendTooltipPos.xPct)}, calc(-100% - 10px))">
            <div class="tip-head">{trendHoverData.label}</div>
            {#each trendHoverData.rows as row}
              <div class="tip-row">
                <span class="tip-dot" style="background:{row.color}"></span>
                <span class="tip-label">{row.label}</span>
                <span class="tip-val">{row.value}</span>
              </div>
            {/each}
          </div>
        {/if}
      {:else}
        <p class="single-pt-note">Select a wider date range to see a chart</p>
      {/if}
    </div>

    <!-- Theme toggles -->
    {#if infoMode === 'volume'}
      <div class="theme-toggles">
        {#each themes as t (t.cluster_id)}
          <button
            class="toggle-btn"
            class:active={compIds.includes(t.cluster_id)}
            onclick={() => toggleComp(t.cluster_id)}
          >{t.name.split(' ').slice(0,2).join(' ')}</button>
        {/each}
      </div>
    {/if}
  </div>

  <!-- ── Info panel ─────────────────────────────── -->
  <div class="glass info-panel fade-in-up" style="animation-delay:120ms">
    <div class="info-top">
      <p class="section-title">
        {infoMode === 'volume' ? 'Volume Movers' :
         infoMode === 'sentiment' ? 'Sentiment Overview' :
         infoMode === 'priority' ? 'Priority Ranking' : 'Channel Breakdown'}
      </p>
    </div>
    <div class="info-grid">
      {#each moverData() as item, i (item.name)}
        <div class="info-item fade-in-up" style="animation-delay:{i*30}ms" animate:flip={{ duration: 320 }}>
          <div class="ii-top">
            <span class="ii-name">{item.name}</span>
            <span class="ii-value" class:ii-good={item.isGood} class:ii-bad={!item.isGood}>{item.value}</span>
          </div>
          <span class="ii-sub">{item.sub}</span>
        </div>
      {/each}
    </div>
  </div>

  <!-- ── Monthly data table ────────────────────── -->
  {#if timeRange !== 'year'}
    <div class="glass table-card fade-in-up" style="animation-delay:160ms">
      <p class="section-title" style="margin-bottom:16px">Data Table</p>
      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th>Period</th>
              {#each themes.filter(t=>t.roadmap_id).slice(0,5) as t}
                <th>{t.name.split(' ')[0]}</th>
              {/each}
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            {#each pts() as row}
              {@const rThemes = themes.filter(t=>t.roadmap_id).slice(0,5)}
              {@const total = rThemes.reduce((s,t) => s + row.vols[t.cluster_id], 0)}
              <tr>
                <td class="month-cell">{row.label}</td>
                {#each rThemes as t}
                  <td>{row.vols[t.cluster_id]}</td>
                {/each}
                <td class="total-cell">{total}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  {/if}
</main>

<style>
  main { padding-top: 0; padding-bottom: 72px; }

  /* Controls bar */
  .controls-bar {
    display: flex; flex-wrap: wrap; align-items: center; gap: 20px;
    padding: 14px 20px; margin-bottom: 16px;
  }
  .ctrl-group { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
  .ctrl-label { font-size:.7rem; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:.05em; flex-shrink:0; }
  .ctrl-tabs { display:flex; gap:3px; background:rgba(15,23,42,.05); border-radius:6px; padding:2px; }
  .ctab { padding:4px 11px; font-size:.75rem; font-weight:500; color:var(--text-muted); background:transparent; border:none; border-radius:4px; cursor:pointer; transition:background var(--transition),color var(--transition); white-space:nowrap; }
  .ctab.active { background:#fff; color:var(--text); font-weight:700; border: 1px solid rgba(15,23,42,0.10); }

  /* Calendar button */
  .cal-btn {
    display:flex; align-items:center; gap:6px;
    padding:5px 12px; font-size:.77rem; font-weight:600; color:var(--text-muted);
    background:rgba(255,255,255,.55); border:1px solid rgba(15,23,42,.10);
    border-radius:var(--radius-sm); cursor:pointer;
    transition:background var(--transition),color var(--transition);
  }
  .cal-btn:hover { background:rgba(255,255,255,.80); color:var(--text); }

  /* Calendar popup */
  .cal-popup {
    position:absolute; top:calc(100% + 6px); left:0; z-index:200;
    padding:14px 16px; min-width:240px;
    box-shadow: none;
  }
  .cal-hint { font-size:.72rem; color:var(--text-muted); margin-bottom:10px; font-weight:600; text-transform:uppercase; letter-spacing:.04em; }
  .cal-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:4px; margin-bottom:10px; }
  .cal-cell {
    display:flex; flex-direction:column; align-items:center; padding:5px 4px;
    font-size:.75rem; font-weight:500; color:var(--text-muted);
    background:transparent; border:1px solid transparent; border-radius:6px;
    cursor:pointer; transition:background var(--transition),color var(--transition);
  }
  .cal-yr { font-size:.6rem; color:var(--text-subtle); }
  .cal-cell:hover { background:rgba(27,58,107,.08); color:var(--navy); }
  .cal-cell.cal-in { background:rgba(27,58,107,.08); color:var(--navy); }
  .cal-cell.cal-edge { background:var(--navy); color:#fff; font-weight:700; }
  .cal-cell.cal-edge .cal-yr { color:rgba(255,255,255,.7); }
  .cal-reset { font-size:.72rem; color:var(--text-muted); background:none; border:none; cursor:pointer; text-decoration:underline; padding:0; }
  .cal-reset:hover { color:var(--navy); }

  /* Chart */
  .chart-svg-wrap { position: relative; }
  .chart-tip {
    position: absolute;
    min-width: 172px;
    background: rgba(255,255,255,0.97);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(27,58,107,0.14);
    border-radius: var(--radius-lg);
    padding: 10px 12px;
    box-shadow: 0 8px 28px rgba(27,58,107,0.16), 0 1px 4px rgba(27,58,107,0.08);
    pointer-events: none;
    z-index: 200;
  }
  .tip-head {
    font-size: .73rem; font-weight: 700; color: var(--navy);
    margin-bottom: 7px; padding-bottom: 6px;
    border-bottom: 1px solid rgba(27,58,107,0.09);
    letter-spacing: -.01em;
  }
  .tip-row { display:flex; align-items:center; gap:7px; font-size:.72rem; margin-top:4px; }
  .tip-dot { width:7px; height:7px; border-radius:2px; flex-shrink:0; }
  .tip-label { flex:1; color:var(--text-muted); }
  .tip-val { font-weight:700; color:var(--text); font-size:.74rem; }

  .chart-card { padding:22px 24px 18px; margin-bottom:16px; }
  .chart-top { display:flex; align-items:flex-start; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-bottom:16px; }
  .chart-sub { font-size:.76rem; color:var(--text-muted); margin-top:2px; }
  .chart-legend { display:flex; gap:14px; flex-wrap:wrap; align-items:center; }
  .legend-item { display:flex; align-items:center; gap:5px; font-size:.72rem; color:var(--text-muted); }
  .legend-dot { width:8px; height:8px; border-radius:3px; flex-shrink:0; }
  .chart-svg { width:100%; height:auto; display:block; overflow:visible; }
  .single-pt-note { font-size:.82rem; color:var(--text-subtle); padding:20px 0; text-align:center; }

  .theme-toggles { display:flex; flex-wrap:wrap; gap:6px; margin-top:14px; padding-top:12px; border-top:1px solid rgba(15,23,42,.07); }
  .toggle-btn { padding:4px 11px; font-size:.72rem; font-weight:500; color:var(--text-muted); background:rgba(15,23,42,.05); border:1px solid transparent; border-radius:6px; cursor:pointer; transition:all var(--transition); }
  .toggle-btn.active { background:rgba(27,58,107,.10); color:var(--navy); border-color:rgba(27,58,107,.22); font-weight:700; }
  .toggle-btn:hover:not(.active) { background:rgba(15,23,42,.09); color:var(--text); }

  /* Info panel */
  .info-panel { padding:20px 22px; margin-bottom:16px; }
  .info-top { margin-bottom:14px; }
  .info-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }
  @media (max-width:700px) { .info-grid { grid-template-columns:repeat(2,1fr); } }
  @media (max-width:460px) { .info-grid { grid-template-columns:1fr; } }
  .info-item { background:rgba(255,255,255,.50); border:1px solid rgba(15,23,42,.06); border-radius:var(--radius); padding:12px 14px; }
  .ii-top { display:flex; align-items:center; justify-content:space-between; margin-bottom:4px; }
  .ii-name { font-size:.78rem; font-weight:600; color:var(--text); }
  .ii-value { font-size:.82rem; font-weight:800; flex-shrink:0; }
  .ii-good { color:#059669; }
  .ii-bad  { color:#DC2626; }
  .ii-sub  { font-size:.71rem; color:var(--text-muted); }

  /* Table */
  .table-card { padding:22px 24px; }
  .table-scroll { overflow-x:auto; }
  .data-table { width:100%; border-collapse:collapse; font-size:.82rem; }
  .data-table th { padding:8px 12px; text-align:left; font-size:.71rem; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:.04em; border-bottom:2px solid rgba(15,23,42,.08); white-space:nowrap; }
  .data-table td { padding:9px 12px; border-bottom:1px solid rgba(15,23,42,.055); color:var(--text); }
  .data-table tr:last-child td { border-bottom:none; }
  .data-table tr:hover td { background:rgba(255,255,255,.40); }
  .month-cell { font-weight:600; white-space:nowrap; }
  .total-cell { font-weight:700; color:var(--navy); }

  .chart-top-right { display:flex; align-items:center; gap:12px; }

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
    .controls-bar,
    .info-panel,
    .table-card,
    .print-btn { display: none !important; }
    .chart-card {
      box-shadow: none !important;
      border: 1px solid rgba(15,23,42,0.15) !important;
      break-inside: avoid;
    }
  }
</style>
