<script lang="ts">
  import { goto } from '$app/navigation';
  import { monthlyTrends as staticTrends, themes as staticThemes, type MonthlyDataPoint } from '$lib/data';
  import PageHeader from '$lib/components/PageHeader.svelte';

  let { data } = $props();
  const themes = $derived(data.themes ?? staticThemes);
  const monthlyTrends = $derived(data.monthlyTrends ?? staticTrends);

  type RangeKey = '30d' | '90d' | '180d' | '365d' | 'all';

  const RANGE_PRESETS: { key: RangeKey; label: string; months?: number }[] = [
    { key: '30d',  label: 'Last 30 days',  months: 1  },
    { key: '90d',  label: 'Last 90 days',  months: 3  },
    { key: '180d', label: 'Last 180 days', months: 6  },
    { key: '365d', label: 'Last 365 days', months: 12 },
    { key: 'all',  label: 'Lifetime'                  },
  ];

  // ── Nice Y-axis tick computation ──────────────────────────
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

  let rangeKey      = $state<RangeKey>('90d');
  let showRangeMenu = $state(false);
  let lineHover     = $state<number | null>(null);
  let bubbleHover     = $state<number | null>(null);
  let bubbleSelected  = $state<number | null>(null);
  let legendHover     = $state<string | null>(null);
  let legendSelected  = $state<string | null>(null);
  let mounted       = $state(false);
  let sentHover = $state<'positive' | 'negative' | null>(null);
  let countDisplay     = $state(0);
  let headerDisplay    = $state(0);
  let headerAnimDone   = $state(false);
  let viewportWidth = $state(0);

  type MetricKey = 'sentiment' | 'volume';

  const isMobileViewport = $derived(() => viewportWidth > 0 && viewportWidth <= 640);
  const isStackedControlsViewport = $derived(() => viewportWidth > 0 && viewportWidth <= 640);

  const METRICS: { key: MetricKey; label: string; color: string }[] = [
    { key: 'volume',    label: 'Responses', color: '#4A90E2' },
    { key: 'sentiment', label: 'Sentiment', color: '#059669' },
  ];

  let metricKey = $state<MetricKey>('volume');
  $effect(() => {
    const t = setTimeout(() => { mounted = true; }, 100);
    return () => clearTimeout(t);
  });

  const periodMonths = $derived(() => {
    const preset = RANGE_PRESETS.find((p) => p.key === rangeKey)!;
    if (!preset.months) return monthlyTrends;
    return monthlyTrends.slice(-preset.months);
  });

  const trendMonths = $derived(() => {
    if (periodMonths().length === 1 && monthlyTrends.length > 1) return monthlyTrends.slice(-2);
    return periodMonths();
  });

  const rangeLabel    = $derived(() => RANGE_PRESETS.find((p) => p.key === rangeKey)!.label);
  const rangeDateText = $derived(() => {
    const m = periodMonths();
    if (!m.length) return '';
    return m.length === 1 ? m[0].month : `${m[0].month} – ${m[m.length - 1].month}`;
  });

  interface ChartPoint { label: string; xLabel: string; volumes: number[]; }
  const useDailyInterp = $derived(() => rangeKey === '30d' || rangeKey === '90d');

  const chartPoints = $derived((): ChartPoint[] => {
    const months = trendMonths();
    if (!useDailyInterp() || months.length < 2) {
      return months.map((m) => ({ label: m.month, xLabel: m.month_short, volumes: m.volumes }));
    }
    const DAYS = 30; const pts: ChartPoint[] = [];
    for (let mi = 0; mi < months.length - 1; mi++) {
      const mA = months[mi]; const mB = months[mi + 1];
      const yr = mA.month.split(' ')[1];
      for (let d = 0; d < DAYS; d++) {
        const frac = d / DAYS;
        pts.push({
          label: `${mA.month_short} ${d + 1}, ${yr}`,
          xLabel: d === 0 ? mA.month_short : d === 14 ? '15' : '',
          volumes: mA.volumes.map((v, ci) => Math.round(v + (mB.volumes[ci] - v) * frac)),
        });
      }
    }
    const last = months[months.length - 1];
    pts.push({ label: `${last.month_short} 30, ${last.month.split(' ')[1]}`, xLabel: last.month_short, volumes: last.volumes });
    return pts;
  });

  const periodThemeMetrics = $derived(() =>
    themes.map((t) => ({ ...t, periodVolume: periodMonths().reduce((s, m) => s + m.volumes[t.cluster_id], 0) }))
  );

  const overallVolume   = $derived(() => periodThemeMetrics().reduce((s, t) => s + t.periodVolume, 0));
  const overallPositive = $derived(() => Math.round(periodThemeMetrics().reduce((s, t) => s + t.periodVolume * (t.positive_pct / 100), 0)));
  const overallNegative = $derived(() => Math.max(0, overallVolume() - overallPositive()));
  const posPct          = $derived(() => Math.round((overallPositive() / Math.max(overallVolume(), 1)) * 100));
  const negPct          = $derived(() => Math.round((overallNegative() / Math.max(overallVolume(), 1)) * 100));

  // Ring count — no animation, always shows live value
  $effect(() => { countDisplay = overallVolume(); });

  // Header stat count-up — runs only on initial load
  let headerHasAnimated = false;
  $effect(() => {
    const target = activeTabData().curr;
    if (headerHasAnimated) {
      headerDisplay = target;
      return;
    }
    let cancelled = false; let startTime: number | null = null;
    function step(ts: number) {
      if (cancelled) return;
      if (startTime === null) startTime = ts;
      const p = Math.min((ts - startTime) / 1600, 1);
      // Two-phase: cubic ease-in for bulk (slow→fast), then explicit slow count for last ~20 integers (fast→slow)
      const SLOW_LAST = 20;
      const fastTarget = Math.max(0, target - SLOW_LAST);
      const SPLIT = 0.70;
      if (p < SPLIT) {
        const q = p / SPLIT;
        headerDisplay = Math.floor(q ** 3 * fastTarget);
      } else {
        const q = (p - SPLIT) / (1 - SPLIT);
        const eased = 1 - (1 - q) ** 2;
        headerDisplay = Math.round(fastTarget + eased * SLOW_LAST);
      }
      if (p < 1) requestAnimationFrame(step);
      else { headerHasAnimated = true; headerAnimDone = true; }
    }
    requestAnimationFrame(step);
    return () => { cancelled = true; };
  });

  // Ring animation
  const RING_R = 80;
  const RING_C = +(2 * Math.PI * RING_R).toFixed(2);
  const ringDashOffset = $derived(() =>
    mounted ? RING_C * (1 - overallPositive() / Math.max(overallVolume(), 1)) : RING_C
  );

  const daysLabel = $derived(() => {
    if (rangeKey === '30d') return '30 days';
    if (rangeKey === '90d') return '90 days';
    if (rangeKey === '180d') return '180 days';
    if (rangeKey === '365d') return '365 days';
    return 'all time';
  });

  const prevPeriodMonths = $derived(() => {
    const preset = RANGE_PRESETS.find(p => p.key === rangeKey)!;
    if (!preset.months) return [] as MonthlyDataPoint[];
    const start = Math.max(0, monthlyTrends.length - preset.months * 2);
    const end   = Math.max(0, monthlyTrends.length - preset.months);
    return monthlyTrends.slice(start, end);
  });

  function computeMetricForMonths(months: MonthlyDataPoint[], metric: MetricKey): number {
    if (!months.length) return 0;
    const total = months.reduce((s, m) => s + themes.reduce((ts, t) => ts + m.volumes[t.cluster_id], 0), 0);
    const pos   = months.reduce((s, m) => s + themes.reduce((ts, t) => ts + m.volumes[t.cluster_id] * (t.positive_pct / 100), 0), 0);
    if (metric === 'volume') return Math.round(total);
    return Math.round(pos);
  }

  const metricTabData = $derived(() =>
    METRICS.map(m => {
      const curr = computeMetricForMonths(periodMonths(), m.key);
      const prev = prevPeriodMonths().length
        ? computeMetricForMonths(prevPeriodMonths(), m.key) : null;
      const pctChange = (prev !== null && prev > 0)
        ? Math.round(((curr - prev) / prev) * 100) : null;
      const displayColor = pctChange === null ? m.color
        : pctChange > 0 ? '#059669'
        : pctChange < 0 ? '#DC2626'
        : '#6B7280';
      return { ...m, curr, pctChange, displayColor };
    })
  );

  const activeTabData = $derived(() => metricTabData().find(m => m.key === metricKey)!);

  function fmtMetric(val: number, _key: MetricKey): string {
    return val.toLocaleString();
  }

  const lineSeries = $derived(() => {
    const m = activeTabData();
    const vals = chartPoints().map(p => {
      const total = themes.reduce((s, t) => s + p.volumes[t.cluster_id], 0);
      if (m.key === 'sentiment') {
        return Math.round(themes.reduce((s, t) => s + p.volumes[t.cluster_id] * (t.positive_pct / 100), 0));
      } else {
        return total;
      }
    });
    return [{ id: 101, label: m.label, color: m.displayColor, vals }];
  });

  const statDescription = $derived(() => {
    const data   = activeTabData();
    const period = daysLabel();
    let base: string;
    if (metricKey === 'sentiment')
      base = `${fmtMetric(data.curr, 'sentiment')} positive responses over the last ${period}`;
    else
      base = `${fmtMetric(data.curr, 'volume')} total responses over the last ${period}`;
    return `${base}.`;
  });

  function lineGeom() {
    if (viewportWidth > 0 && viewportWidth <= 640) {
      const pad = { t: 18, r: 18, b: 52, l: 42 };
      const w = 780;
      const h = 420;
      return { w, h, pad, innerW: w - pad.l - pad.r, innerH: h - pad.t - pad.b };
    }

    if (viewportWidth > 0 && viewportWidth <= 900) {
      const pad = { t: 16, r: 18, b: 46, l: 46 };
      const w = 780;
      const h = 320;
      return { w, h, pad, innerW: w - pad.l - pad.r, innerH: h - pad.t - pad.b };
    }

    if (viewportWidth > 0 && viewportWidth <= 1180) {
      const pad = { t: 16, r: 18, b: 44, l: 46 };
      const w = 780;
      const h = 300;
      return { w, h, pad, innerW: w - pad.l - pad.r, innerH: h - pad.t - pad.b };
    }

    const pad = { t: 14, r: 18, b: 36, l: 48 };
    const w = 780;
    const h = 260;
    return { w, h, pad, innerW: w - pad.l - pad.r, innerH: h - pad.t - pad.b };
  }

  function lineTextSize(kind: 'axis' | 'tick') {
    if (viewportWidth > 0 && viewportWidth <= 640) return kind === 'axis' ? 16 : 15;
    if (viewportWidth > 0 && viewportWidth <= 1180) return kind === 'axis' ? 14 : 13;
    return kind === 'axis' ? 11.5 : 10.5;
  }

  const allLineVals = $derived(() => lineSeries().flatMap((s) => s.vals));
  const lineTickData = $derived(() => {
    const vals = allLineVals();
    if (!vals.length) return { lo: 0, hi: 100, ticks: [0, 25, 50, 75, 100] };
    return niceLineTicks(0, Math.max(...vals), 5);
  });
  const yMin = $derived(() => lineTickData().lo);
  const yMax = $derived(() => lineTickData().hi);

  function xAt(i: number) {
    const geom = lineGeom();
    return geom.pad.l + (i / Math.max(chartPoints().length - 1, 1)) * geom.innerW;
  }
  function yAt(v: number)  {
    const geom = lineGeom();
    return geom.pad.t + geom.innerH - ((v - yMin()) / Math.max(yMax() - yMin(), 1)) * geom.innerH;
  }
  function fmtY(v: number) {
    return v >= 1000 ? (v / 1000).toFixed(1).replace(/\.0$/, '') + 'k' : Math.round(v).toString();
  }
  function linePath(vals: number[]) {
    return vals.map((v, i) => `${i === 0 ? 'M' : 'L'}${xAt(i).toFixed(1)},${yAt(v).toFixed(1)}`).join(' ');
  }
  function areaPath(vals: number[]) {
    if (vals.length < 2) return '';
    const geom = lineGeom();
    const base = geom.pad.t + geom.innerH;
    return `${linePath(vals)} L${xAt(vals.length - 1).toFixed(1)},${base.toFixed(1)} L${xAt(0).toFixed(1)},${base.toFixed(1)} Z`;
  }

  const yTicks = $derived(() =>
    lineTickData().ticks.map((v) => ({ v, y: yAt(v) }))
  );

  const lineBands = $derived(() =>
    chartPoints().map((_, i) => {
      const geom = lineGeom();
      const left  = i === 0 ? geom.pad.l : (xAt(i - 1) + xAt(i)) / 2;
      const right = i === chartPoints().length - 1 ? geom.w - geom.pad.r : (xAt(i) + xAt(i + 1)) / 2;
      return { idx: i, left, width: right - left };
    })
  );

  const lineHoverData = $derived(() => {
    if (lineHover === null) return null;
    const idx = Math.max(0, Math.min(lineHover, chartPoints().length - 1));
    return {
      idx, label: chartPoints()[idx].label, x: xAt(idx),
      rows: lineSeries().map((s) => ({ label: s.label, color: s.color, value: s.vals[idx] })),
    };
  });

  const lineTooltipPos = $derived(() => {
    if (!lineHoverData()) return null;
    const geom = lineGeom();
    const idx  = lineHoverData()!.idx;
    const xPct = (lineHoverData()!.x - geom.pad.l) / geom.innerW * 100;
    const yPct = yAt(lineSeries()[0].vals[idx]) / geom.h * 100;
    return { xPct, yPct };
  });

  function tipXTranslate(pct: number): string {
    if (pct < 12) return '0%';
    if (pct > 88) return '-100%';
    return '-50%';
  }

  // ── Scatter bubble chart: Sentiment % vs Volume ──────────
  function scatterGeom() {
    if (viewportWidth > 0 && viewportWidth <= 640) {
      const pad = { t: 52, r: 20, b: 84, l: 46 };
      const w = 720;
      const h = 494;
      return { w, h, pad, innerW: w - pad.l - pad.r, innerH: h - pad.t - pad.b };
    }

    if (viewportWidth > 0 && viewportWidth <= 900) {
      const pad = { t: 54, r: 26, b: 76, l: 54 };
      const w = 720;
      const h = 434;
      return { w, h, pad, innerW: w - pad.l - pad.r, innerH: h - pad.t - pad.b };
    }

    if (viewportWidth > 0 && viewportWidth <= 1180) {
      const pad = { t: 54, r: 28, b: 72, l: 56 };
      const w = 720;
      const h = 414;
      return { w, h, pad, innerW: w - pad.l - pad.r, innerH: h - pad.t - pad.b };
    }

    const pad = { t: 56, r: 32, b: 68, l: 62 };
    const w = 720;
    const h = 384;
    return { w, h, pad, innerW: w - pad.l - pad.r, innerH: h - pad.t - pad.b };
  }

  function scatterTextSize(kind: 'axis' | 'tick' | 'quadrant' | 'bubble') {
    if (viewportWidth > 0 && viewportWidth <= 640) {
      if (kind === 'axis') return 16;
      if (kind === 'tick') return 15;
      if (kind === 'quadrant') return 13;
      return 13.5;
    }

    if (viewportWidth > 0 && viewportWidth <= 1180) {
      if (kind === 'axis') return 14;
      if (kind === 'tick') return 13;
      if (kind === 'quadrant') return 11.5;
      return 12;
    }

    if (kind === 'axis') return 11.5;
    if (kind === 'tick') return 10.5;
    if (kind === 'quadrant') return 9.5;
    return 10;
  }

  // Fixed 0–100 scale so the 50% divider always lands at the visual center
  const scatterXNiceTicks = $derived(() => ({ lo: 0, hi: 100, ticks: [0, 25, 50, 75, 100] }));

  // Log-scale helper: fraction of chart height for a given value
  function logFrac(v: number, maxV: number): number {
    if (maxV <= 0) return 0;
    return Math.log1p(v) / Math.log1p(maxV);
  }

  const scatterYMax = $derived(() =>
    Math.max(...periodThemeMetrics().map((t) => t.periodVolume), 1)
  );

  const scatterYTicks = $derived(() => {
    const maxV = scatterYMax();
    const geom = scatterGeom();
    // Pick ~5 log-friendly tick values within range
    const candidates = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000];
    const chosen = candidates.filter(v => v <= maxV);
    if (!chosen.length || chosen[chosen.length - 1] < maxV * 0.5) chosen.push(Math.round(maxV));
    return chosen.map(v => ({ v, y: geom.pad.t + geom.innerH - logFrac(v, maxV) * geom.innerH }));
  });

  const scatterData = $derived(() => {
    const base = periodThemeMetrics();
    const maxVol = Math.max(...base.map((t) => t.periodVolume), 1);
    const xMax = scatterXNiceTicks().hi;
    const geom = scatterGeom();
    const MIN_R = 10; const MAX_R = 28;
    const raw = base.map((t) => {
      const lf = logFrac(t.periodVolume, maxVol);
      const r  = MIN_R + lf * (MAX_R - MIN_R);
      const cx = geom.pad.l + (t.positive_pct / Math.max(xMax, 1)) * geom.innerW;
      const cy = geom.pad.t + geom.innerH - lf * geom.innerH;
      const tier = t.positive_pct > 60 ? 'good' : t.positive_pct >= 40 ? 'mixed' : 'critical';
      const color    = tier === 'good' ? '#059669' : tier === 'mixed' ? '#4A90E2' : '#DC2626';
      const fillOpac = tier === 'good' ? 0.16       : tier === 'mixed' ? 0.14       : 0.13;
      return { ...t, r, cx, cy, color, fillOpac, tier, shortName: t.name.split(' ')[0] };
    });
    // Separate overlapping bubbles that share the same cx
    const JITTER = 22;
    const xGroups = new Map<number, typeof raw>();
    for (const b of raw) {
      const key = Math.round(b.cx);
      if (!xGroups.has(key)) xGroups.set(key, []);
      xGroups.get(key)!.push(b);
    }
    return raw.map((b) => {
      const group = xGroups.get(Math.round(b.cx))!;
      if (group.length < 2) return b;
      const idx = group.indexOf(b);
      const offset = (idx - (group.length - 1) / 2) * JITTER;
      return { ...b, cy: b.cy + offset };
    });
  });

  // Quadrant midpoint lines
  const qx = $derived(() => {
    const geom = scatterGeom();
    return geom.pad.l + (50 / Math.max(scatterXNiceTicks().hi, 1)) * geom.innerW;
  });
  const qy = $derived(() => {
    const geom = scatterGeom();
    return geom.pad.t + geom.innerH * 0.5;
  }); // 50% volume


  function bubbleOpacity(i: number): number {
    const tier = scatterData()[i]?.tier;
    if (bubbleSelected !== null) return bubbleSelected === i ? 1 : 0;
    if (legendSelected !== null) return tier === legendSelected ? 1 : 0;
    if (legendHover    !== null) return tier === legendHover    ? 1 : 0.15;
    if (bubbleHover    !== null) return bubbleHover === i       ? 1 : 0.15;
    return 1;
  }

  function openCluster(clusterId: number) {
    goto(`/feedback?cluster=${clusterId}`);
  }
</script>

<svelte:window bind:innerWidth={viewportWidth} />

<PageHeader
  title="Dashboard"
  subtitle="Real-time overview of user feedback trends, sentiment signals, and top themes across all channels."
/>

<!-- Dashboard header: stat centered -->
<div class="dash-header header-anim">
  <div class="dash-header-inner">

    <!-- stat centered -->
    <div class="dash-stat-wrap">
      <div class="above-stat stat-num-anim">
        <span class="above-stat-num" style="color:{activeTabData().displayColor}">
          {fmtMetric(headerDisplay, metricKey)}
        </span>
        {#if activeTabData().pctChange !== null}
          <span class="above-stat-badge"
            class:up={activeTabData().pctChange! > 0}
            class:down={activeTabData().pctChange! < 0}
            class:flat={activeTabData().pctChange === 0}
            class:visible={headerAnimDone}>
            {#if activeTabData().pctChange! > 0}
              <svg width="9" height="9" viewBox="0 0 10 10" fill="currentColor"><path d="M5 1 L9.5 9 L0.5 9 Z"/></svg>
              +{activeTabData().pctChange}%
            {:else if activeTabData().pctChange! < 0}
              <svg width="9" height="9" viewBox="0 0 10 10" fill="currentColor"><path d="M5 9 L9.5 1 L0.5 1 Z"/></svg>
              {activeTabData().pctChange}%
            {:else}
              unchanged
            {/if}
          </span>
        {/if}
      </div>
      <p class="above-stat-desc stat-desc-anim">{statDescription()}</p>
    </div>

  </div>
</div>

<main class="page-container dash-page">

  <!-- ── Hero section ──────────────────────────────────────── -->
  <div class="hero-outer fade-in-up" style="animation-delay:40ms">

    <!-- Left column: tabs floating above chart panel -->
    <div class="chart-left-col">

      <div class="chart-controls">
        {#if isStackedControlsViewport()}
          <div class="date-picker-wrap date-picker-mobile">
            <button class="date-btn date-btn-full" onclick={() => showRangeMenu = !showRangeMenu}
              aria-haspopup="menu" aria-expanded={showRangeMenu}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                   stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="4" width="18" height="18" rx="2"/>
                <line x1="16" y1="2" x2="16" y2="6"/>
                <line x1="8" y1="2" x2="8" y2="6"/>
                <line x1="3" y1="10" x2="21" y2="10"/>
              </svg>
              {rangeLabel()}
              {#if rangeDateText()}
                <span class="date-range-sub">· {rangeDateText()}</span>
              {/if}
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                   stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </button>
            {#if showRangeMenu}
              <button class="overlay" type="button" aria-label="Close date menu"
                onclick={() => showRangeMenu = false}></button>
              <div class="date-menu glass-sm" role="menu">
                {#each RANGE_PRESETS as p (p.key)}
                  <button class="date-opt" class:selected={rangeKey === p.key} role="menuitem"
                    onclick={() => { rangeKey = p.key; showRangeMenu = false; }}>
                    {p.label}
                  </button>
                {/each}
              </div>
            {/if}
          </div>
        {/if}

        <div class="chart-tab-row">
          {#each metricTabData() as m (m.key)}
            <button
              class="chart-tab"
              class:active={metricKey === m.key}
              style={metricKey === m.key ? `--tab-color:${m.displayColor}` : ''}
              onclick={() => metricKey = m.key}
            >
              <span class="ct-label">{m.label}</span>
              <div class="ct-val-row">
                <span class="ct-val">{fmtMetric(m.curr, m.key)}</span>
                {#if m.pctChange !== null}
                  <span class="ct-change" class:up={m.pctChange > 0} class:down={m.pctChange < 0} class:flat={m.pctChange === 0}>
                    {#if m.pctChange > 0}
                      <svg width="9" height="9" viewBox="0 0 10 10" fill="currentColor"><path d="M5 1 L9.5 9 L0.5 9 Z"/></svg>
                    {:else if m.pctChange < 0}
                      <svg width="9" height="9" viewBox="0 0 10 10" fill="currentColor"><path d="M5 9 L9.5 1 L0.5 1 Z"/></svg>
                    {/if}
                    {m.pctChange === 0 ? '—' : Math.abs(m.pctChange) + '%'}
                  </span>
                {/if}
              </div>
            </button>
          {/each}
        </div>

      </div>

      <div class="chart-panel glass">
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div class="trend-side" onmouseleave={() => lineHover = null}>
          <div class="line-wrap">
        <svg viewBox={`0 0 ${lineGeom().w} ${lineGeom().h}`} class="line-svg" aria-label="Positive sentiment trend">
          <defs>
            <linearGradient id="lineGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color={activeTabData().displayColor} stop-opacity="0.18"/>
              <stop offset="100%" stop-color={activeTabData().displayColor} stop-opacity="0"/>
            </linearGradient>
            <clipPath id="lineReveal">
              <rect
                x={lineGeom().pad.l}
                y={lineGeom().pad.t - 20}
                style={`width: ${mounted ? lineGeom().innerW : 0}; transition: width 1.3s cubic-bezier(0.4, 0, 0.2, 1) 0.25s`}
                height={lineGeom().innerH + 40}
              />
            </clipPath>
          </defs>
          {#each yTicks() as tick (tick.v)}
            <line x1={lineGeom().pad.l} y1={tick.y} x2={lineGeom().w - lineGeom().pad.r} y2={tick.y} class="line-grid"/>
            <text x={lineGeom().pad.l - 6} y={tick.y + 4} text-anchor="end" class="y-lab" style={`font-size:${lineTextSize('tick')}px`}>{fmtY(tick.v)}</text>
          {/each}
          {#if lineHoverData()}
            <line x1={lineHoverData()!.x} y1={lineGeom().pad.t} x2={lineHoverData()!.x} y2={lineGeom().h - lineGeom().pad.b} class="line-focus"/>
          {/if}
          {#each lineSeries() as s (s.id)}
            <path d={areaPath(s.vals)} fill="url(#lineGrad)" clip-path="url(#lineReveal)"
              style={`opacity: ${mounted ? 1 : 0}; transition: opacity 1s ease 0.25s`}/>
            <path d={linePath(s.vals)} stroke={s.color} class="series-line" clip-path="url(#lineReveal)"/>
            {#if lineHoverData()}
              <circle cx={lineHoverData()!.x} cy={yAt(s.vals[lineHoverData()!.idx])}
                r="4.8" fill={s.color} stroke="#fff" stroke-width="2"/>
            {/if}
          {/each}
          {#each chartPoints() as pt, i (pt.label)}
            {#if pt.xLabel}
              <text x={xAt(i)} y={lineGeom().h - 8} text-anchor="middle" class="month-lab" style={`font-size:${lineTextSize('axis')}px`}>{pt.xLabel}</text>
            {/if}
          {/each}
          {#each lineBands() as b (b.idx)}
            <!-- svelte-ignore a11y_no_static_element_interactions -->
            <rect x={b.left} y={lineGeom().pad.t} width={b.width} height={lineGeom().innerH}
              fill="transparent" onmouseenter={() => lineHover = b.idx}/>
          {/each}
        </svg>

        {#if lineHoverData() && lineTooltipPos()}
          <div class="chart-tip"
            style={`left:${lineTooltipPos()!.xPct}%; top:${lineTooltipPos()!.yPct}%; transform:translate(${tipXTranslate(lineTooltipPos()!.xPct)}, calc(-100% - 10px))`}>
            <div class="tip-head">{lineHoverData()!.label}</div>
            {#each lineHoverData()!.rows as row (row.label)}
              <div class="tip-row">
                <span class="tip-dot" style={`background:${row.color}`}></span>
                <span class="tip-label">{row.label}</span>
                <span class="tip-val">{fmtMetric(row.value, metricKey)}</span>
              </div>
            {/each}
          </div>
        {/if}
          </div>
        </div>
      </div>
    </div>

    <!-- Vertical divider -->
    <div class="hero-v-divider"></div>

    <!-- Right column: date picker above + sentiment card below -->
    <div class="right-col">
      {#if !isStackedControlsViewport()}
        <div class="date-picker-wrap date-picker-desktop">
          <button class="date-btn date-btn-full" onclick={() => showRangeMenu = !showRangeMenu}
            aria-haspopup="menu" aria-expanded={showRangeMenu}>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="4" width="18" height="18" rx="2"/>
              <line x1="16" y1="2" x2="16" y2="6"/>
              <line x1="8" y1="2" x2="8" y2="6"/>
              <line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
            {rangeLabel()}
            {#if rangeDateText()}
              <span class="date-range-sub">· {rangeDateText()}</span>
            {/if}
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </button>
          {#if showRangeMenu}
            <button class="overlay" type="button" aria-label="Close date menu"
              onclick={() => showRangeMenu = false}></button>
            <div class="date-menu glass-sm" role="menu">
              {#each RANGE_PRESETS as p (p.key)}
                <button class="date-opt" class:selected={rangeKey === p.key} role="menuitem"
                  onclick={() => { rangeKey = p.key; showRangeMenu = false; }}>
                  {p.label}
                </button>
              {/each}
            </div>
          {/if}
        </div>
      {/if}

      <div class="sentiment-panel glass">
      <div class="sentiment-side">
      <p class="side-label">Sentiment Split</p>

      <!-- svelte-ignore a11y_no_static_element_interactions -->
      <div class="ring-wrap" onmouseleave={() => sentHover = null}>
        <svg viewBox="0 0 220 220" class="ring-svg" aria-label="Sentiment ring">
          <defs>
            <linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stop-color="#34d399"/>
              <stop offset="100%" stop-color="#059669"/>
            </linearGradient>
          </defs>
          <!-- svelte-ignore a11y_no_static_element_interactions -->
          <circle cx="110" cy="110" r={RING_R}
            fill="none"
            stroke={sentHover === 'negative' ? 'rgba(220,38,38,0.65)' : 'rgba(220,38,38,0.28)'}
            stroke-width="16"
            stroke-linecap="round"
            stroke-dasharray={`${RING_C * negPct() / 100} ${RING_C}`}
            transform={`rotate(${-90 + posPct() * 3.6} 110 110)`}
            style="cursor:pointer; transition: stroke 0.22s ease, opacity 0.22s ease; {sentHover === 'positive' ? 'opacity:0.30' : 'opacity:1'}"
            onmouseenter={() => sentHover = 'negative'}
          />
          <!-- svelte-ignore a11y_no_static_element_interactions -->
          <circle cx="110" cy="110" r={RING_R}
            fill="none" stroke="url(#ringGrad)"
            stroke-width={sentHover === 'positive' ? 19 : 16}
            stroke-linecap="round"
            stroke-dasharray={RING_C}
            stroke-dashoffset={ringDashOffset()}
            transform="rotate(-90 110 110)"
            style="cursor:pointer; {sentHover === 'negative' ? 'opacity:0.30' : 'opacity:1'}"
            class="ring-arc"
            onmouseenter={() => sentHover = 'positive'}
          />
        </svg>
        <div class="ring-overlay">
          {#if sentHover}
            <span class="ring-count" style="color:{sentHover === 'positive' ? '#059669' : '#DC2626'}">{(sentHover === 'positive' ? overallPositive() : overallNegative()).toLocaleString()}</span>
            <span class="ring-sub">{sentHover === 'positive' ? 'positive' : 'negative'}</span>
          {:else}
            <span class="ring-count">{countDisplay.toLocaleString()}</span>
            <span class="ring-sub">total responses</span>
          {/if}
        </div>
      </div>

      <div class="sent-bars">
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div class="sent-row" class:sent-row-active={sentHover === 'positive'} onmouseenter={() => sentHover = 'positive'} onmouseleave={() => sentHover = null}>
          <span class="sent-dot pos-dot"></span>
          <span class="sent-name">Positive</span>
          <div class="sent-track">
            <div class="sent-fill sent-pos" style="width:{mounted ? posPct() : 0}%"></div>
          </div>
          <span class="sent-pct">{posPct()}%</span>
        </div>
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div class="sent-row" class:sent-row-active={sentHover === 'negative'} onmouseenter={() => sentHover = 'negative'} onmouseleave={() => sentHover = null}>
          <span class="sent-dot neg-dot"></span>
          <span class="sent-name">Negative</span>
          <div class="sent-track">
            <div class="sent-fill sent-neg" style="width:{mounted ? negPct() : 0}%"></div>
          </div>
          <span class="sent-pct">{negPct()}%</span>
        </div>
      </div>

      <p class="sent-meta">{themes.length} themes · 4 channels · {rangeLabel()}</p>
      </div>
    </div>
    </div><!-- /.right-col -->
  </div>

  <!-- ── Scatter bubble chart: Sentiment vs Impact ─────────── -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <section class="glass scatter-section fade-in-up" style="animation-delay:80ms"
    onmouseleave={() => bubbleHover = null}
    onclick={() => { bubbleSelected = null; legendSelected = null; }}>
    <div class="card-head">
      <div>
        <p class="section-title">Sentiment vs Impact</p>
        <p class="chart-sub">Each bubble = a feedback theme · X = positive sentiment · Y = volume · size = relative volume</p>
      </div>
      <div class="scatter-legend">
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <span class="sleg-item sleg-good"
          class:sleg-active={legendSelected === 'good'}
          class:sleg-inactive={legendSelected !== null && legendSelected !== 'good'}
          onmouseenter={() => legendHover = 'good'} onmouseleave={() => legendHover = null}
          onclick={(e) => { e.stopPropagation(); legendSelected = legendSelected === 'good' ? null : 'good'; bubbleSelected = null; }}
        >High Sentiment</span>
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <span class="sleg-item sleg-mixed"
          class:sleg-active={legendSelected === 'mixed'}
          class:sleg-inactive={legendSelected !== null && legendSelected !== 'mixed'}
          onmouseenter={() => legendHover = 'mixed'} onmouseleave={() => legendHover = null}
          onclick={(e) => { e.stopPropagation(); legendSelected = legendSelected === 'mixed' ? null : 'mixed'; bubbleSelected = null; }}
        >Mixed</span>
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <span class="sleg-item sleg-critical"
          class:sleg-active={legendSelected === 'critical'}
          class:sleg-inactive={legendSelected !== null && legendSelected !== 'critical'}
          onmouseenter={() => legendHover = 'critical'} onmouseleave={() => legendHover = null}
          onclick={(e) => { e.stopPropagation(); legendSelected = legendSelected === 'critical' ? null : 'critical'; bubbleSelected = null; }}
        >Needs Attention</span>
      </div>
    </div>

    <div class="scatter-wrap">
      <svg viewBox={`0 0 ${scatterGeom().w} ${scatterGeom().h}`} class="scatter-svg" aria-label="Sentiment vs impact scatter chart">
        <defs>
          {#each scatterData() as b, i (b.cluster_id)}
            <radialGradient id={`bg${i}`} cx="40%" cy="35%" r="65%">
              <stop offset="0%" stop-color={b.color} stop-opacity={b.fillOpac * 1.8}/>
              <stop offset="100%" stop-color={b.color} stop-opacity={b.fillOpac * 0.6}/>
            </radialGradient>
          {/each}
        </defs>

        <!-- Hover-reset zone: moving to empty chart area clears bubble hover -->
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <rect x={scatterGeom().pad.l} y={scatterGeom().pad.t} width={scatterGeom().innerW} height={scatterGeom().innerH} fill="transparent"
          onmouseenter={() => bubbleHover = null}/>

        <!-- Quadrant background tints -->
        <rect x={scatterGeom().pad.l} y={scatterGeom().pad.t} width={qx() - scatterGeom().pad.l} height={qy() - scatterGeom().pad.t}
          fill="rgba(220,38,38,0.03)" rx="0" pointer-events="none"/>
        <rect x={qx()} y={scatterGeom().pad.t} width={scatterGeom().pad.l + scatterGeom().innerW - qx()} height={qy() - scatterGeom().pad.t}
          fill="rgba(5,150,105,0.04)" rx="0" pointer-events="none"/>

        <!-- Grid lines -->
        {#each scatterYTicks() as tick (tick.v)}
          <line x1={scatterGeom().pad.l} y1={tick.y} x2={scatterGeom().w - scatterGeom().pad.r} y2={tick.y} class="s-grid"/>
          <text x={scatterGeom().pad.l - 7} y={tick.y + 4} text-anchor="end" class="s-axis-lab" style={`font-size:${scatterTextSize('tick')}px`}>
            {tick.v >= 1000 ? (tick.v / 1000).toFixed(1).replace(/\.0$/, '') + 'k' : Math.round(tick.v)}
          </text>
        {/each}

        <!-- X axis ticks -->
        {#each scatterXNiceTicks().ticks as pct (pct)}
          {@const xpos = scatterGeom().pad.l + (pct / Math.max(scatterXNiceTicks().hi, 1)) * scatterGeom().innerW}
          <line x1={xpos} y1={scatterGeom().pad.t + scatterGeom().innerH} x2={xpos} y2={scatterGeom().pad.t + scatterGeom().innerH + 5} class="s-tick"/>
          <text x={xpos} y={scatterGeom().h - 50} text-anchor="middle" class="s-axis-lab" style={`font-size:${scatterTextSize('tick')}px`}>{pct}%</text>
        {/each}

        <!-- Quadrant divider lines -->
        <line x1={qx()} y1={scatterGeom().pad.t} x2={qx()} y2={scatterGeom().pad.t + scatterGeom().innerH} class="q-line"/>
        <line x1={scatterGeom().pad.l} y1={qy()} x2={scatterGeom().pad.l + scatterGeom().innerW} y2={qy()} class="q-line"/>

        <!-- Axis labels -->
        <text x={scatterGeom().pad.l + scatterGeom().innerW / 2} y={scatterGeom().h - 10} text-anchor="middle" class="axis-title" style={`font-size:${scatterTextSize('axis')}px`}>
          Positive Sentiment %
        </text>
        <text x={14} y={scatterGeom().pad.t + scatterGeom().innerH / 2} text-anchor="middle"
          style={`font-size:${scatterTextSize('axis')}px`}
          transform={`rotate(-90 14 ${scatterGeom().pad.t + scatterGeom().innerH / 2})`} class="axis-title">
          Volume
        </text>

        <!-- Quadrant labels -->
        <text x={scatterGeom().pad.l + 8} y={scatterGeom().pad.t + 16} class="q-label q-danger" style={`font-size:${scatterTextSize('quadrant')}px`}>Pain Points</text>
        <text x={scatterGeom().pad.l + scatterGeom().innerW - 8} y={scatterGeom().pad.t + 16} text-anchor="end" class="q-label q-success" style={`font-size:${scatterTextSize('quadrant')}px`}>Strengths</text>
        <text x={scatterGeom().pad.l + 8} y={scatterGeom().pad.t + scatterGeom().innerH - 8} class="q-label q-muted" style={`font-size:${scatterTextSize('quadrant')}px`}>Monitor</text>
        <text x={scatterGeom().pad.l + scatterGeom().innerW - 8} y={scatterGeom().pad.t + scatterGeom().innerH - 8} text-anchor="end" class="q-label q-muted" style={`font-size:${scatterTextSize('quadrant')}px`}>Small Wins</text>

        <!-- Bubbles -->
        {#each scatterData() as b, i (b.cluster_id)}
          <!-- svelte-ignore a11y_no_static_element_interactions -->
          <g class="bubble-group"
            style={`opacity:${bubbleOpacity(i)}; transition: opacity 0.22s ease`}
            onmouseenter={() => bubbleHover = i}
            onclick={(e) => { e.stopPropagation(); openCluster(b.cluster_id); }}>
            <circle cx={b.cx} cy={b.cy} r={b.r}
              fill={`url(#bg${i})`}
              stroke={b.color}
              stroke-width={bubbleHover === i || bubbleSelected === i ? 2 : 1.2}
              stroke-opacity={bubbleHover === i || bubbleSelected === i ? 0.9 : 0.5}
              class="s-bubble"
              class:hovered={bubbleHover === i}/>
            {#if b.r >= 16}
              <text x={b.cx} y={b.cy - 4} text-anchor="middle"
                class="b-label" style={`fill:${b.color}; font-size:${scatterTextSize('bubble')}px`}>{b.shortName}</text>
              <text x={b.cx} y={b.cy + 9} text-anchor="middle" class="b-sub" style={`fill:${b.color}; font-size:${scatterTextSize('bubble') - 1.5}px`}>
                {b.positive_pct}%
              </text>
            {/if}
          </g>
        {/each}
      </svg>
    </div>


  </section>

</main>

<style>
  .dash-page { padding-top: 0; padding-bottom: 68px; }

  /* ── Brand bar ───────────────────────────────────────────── */
  .brand-bar {
    background: linear-gradient(105deg,
      rgba(255,107,157,0.06) 0%,
      rgba(168,85,247,0.05) 40%,
      rgba(251,146,60,0.04) 70%,
      transparent 100%);
    margin-bottom: 0;
  }
  .brand-bar-inner {
    max-width: 1280px; margin: 0 auto; padding: 18px 28px;
    display: flex; align-items: center; justify-content: space-between; gap: 16px;
  }
  .brand-identity { display: flex; align-items: center; gap: 10px; }

  /* Logo + glow */
  .brand-glow-wrap { position: relative; display: flex; align-items: center; justify-content: center; }
  .brand-glow {
    position: absolute; inset: -10px;
    background: radial-gradient(ellipse at center,
      rgba(168,85,247,0.22) 0%,
      rgba(255,107,157,0.12) 40%,
      transparent 70%);
    border-radius: 50%;
    filter: blur(8px);
    pointer-events: none;
  }
  .brand-icon {
    position: relative; z-index: 1;
    filter: drop-shadow(0 4px 12px rgba(168,85,247,0.30)) drop-shadow(0 1px 3px rgba(0,0,0,0.12));
    border-radius: 10px;
  }

  .brand-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .brand-wordmark { display: flex; flex-direction: column; justify-content: center; }
  .brand-name {
    font-size: 1.08rem; font-weight: 800; letter-spacing: -.03em;
    color: #7C3AED;
  }

  .brand-chip {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: .76rem; font-weight: 600; color: var(--text-muted);
    background: rgba(255,255,255,0.72); border: 1px solid rgba(15,23,42,0.09);
    border-radius: 5px; padding: 5px 10px; white-space: nowrap;
    backdrop-filter: blur(8px);
  }
  .brand-chip svg { width: 10px; height: 10px; flex-shrink: 0; }
  .brand-chip-live {
    color: #059669; background: rgba(5,150,105,0.08); border-color: rgba(5,150,105,0.22);
  }
  .live-dot {
    width: 6px; height: 6px; border-radius: 50%; background: #059669;
    animation: pulse-live 1.8s ease-in-out infinite;
  }
  @keyframes pulse-live {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.45; transform: scale(0.72); }
  }

  /* ── Page entrance animations ────────────────────────────── */
  @keyframes slideDown {
    from { opacity: 0; transform: translateY(-18px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes popIn {
    0%   { opacity: 0; transform: scale(0.88) translateY(6px); }
    70%  { transform: scale(1.03) translateY(-1px); }
    100% { opacity: 1; transform: scale(1) translateY(0); }
  }
  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .header-anim  { animation: slideDown 0.38s cubic-bezier(0.34, 1.2, 0.64, 1) both; }
  .stat-num-anim { animation: fadeUp 0.36s cubic-bezier(0.4, 0, 0.2, 1) 0.05s both; }
  .stat-desc-anim { animation: fadeUp 0.36s cubic-bezier(0.4, 0, 0.2, 1) 0.28s both; }

  /* Outline-only cards */
  .scatter-section {
    background: transparent;
    border: 1.5px solid rgba(15, 23, 42, 0.11);
    backdrop-filter: none;
  }

  /* ── Date picker ─────────────────────────────────────────── */
  .date-picker-wrap { flex-shrink: 0; position: relative; }
  .date-picker-mobile { width: 100%; }
  .date-picker-desktop { width: 100%; }
  .date-range-sub { font-size: .73rem; font-weight: 400; color: var(--text-subtle); margin-left: 2px; }

  .date-btn {
    display: flex; align-items: center; gap: 6px;
    padding: 7px 10px; font-size: .78rem; font-weight: 600;
    color: var(--text-muted); background: #FFFFFF;
    border: 1px solid rgba(15,23,42,0.12); border-radius: var(--radius-sm);
    cursor: pointer; transition: background var(--transition), color var(--transition);
    white-space: nowrap; width: 100%;
  }
  .date-btn:hover { background: #F7F8FA; color: var(--text); }

  .date-menu { position: absolute; top: calc(100% + 6px); right: 0; z-index: 51; padding: 6px; min-width: 160px; }
  .date-opt {
    display: block; width: 100%; text-align: left; padding: 8px 12px;
    font-size: .82rem; font-weight: 500; color: var(--text-muted);
    background: transparent; border: none; border-radius: var(--radius-sm); cursor: pointer;
    transition: background var(--transition), color var(--transition);
  }
  .date-opt:hover    { background: rgba(74,144,226,0.10); color: var(--navy); }
  .date-opt.selected { color: var(--navy); font-weight: 700; background: rgba(74,144,226,0.10); }
  .overlay { position: fixed; inset: 0; background: transparent; border: none; padding: 0; z-index: 49; }

  /* ── Hero outer: tabs + chart panel LEFT, sentiment RIGHT ── */
  .hero-outer {
    display: flex; align-items: stretch; gap: 14px;
    margin-bottom: 14px; position: relative; z-index: 1;
  }
  .chart-left-col {
    flex: 1; min-width: 0; display: flex; flex-direction: column;
  }
  .chart-controls {
    display: flex;
    align-items: flex-end;
    gap: 10px;
    margin-bottom: -1px;
    position: relative;
    z-index: 2;
  }
  .chart-panel {
    flex: 1;
    border-radius: 0 0 var(--radius-lg) var(--radius-lg);
    border-top: none;
  }
  .hero-v-divider { display: none; }
  .right-col {
    width: 280px; flex-shrink: 0;
    display: flex; flex-direction: column; gap: 8px;
  }
  .sentiment-panel {
    flex: 1;
    border-radius: var(--radius-lg);
    display: flex; align-items: stretch;
  }

  /* Trend side (left) */
  .trend-side { padding: 14px 20px 14px 22px; display: flex; flex-direction: column; }

  .card-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 10px; }
  .section-title { font-size: .88rem; font-weight: 700; color: var(--text); }
  .chart-sub { font-size: .72rem; color: var(--text-muted); margin-top: 2px; }

  /* ── Custom dashboard header ─────────────────────────────── */
  .dash-header { margin-bottom: 24px; }
  .dash-header-inner {
    max-width: 1280px; margin: 0 auto; padding: 20px 28px 16px;
    display: flex; flex-direction: column; gap: 0;
  }
  /* stat centered */
  .dash-stat-wrap {
    align-self: center; text-align: center;
    padding: 4px 0 4px; width: 100%;
  }
  .above-stat { display: flex; align-items: center; justify-content: center; gap: 10px; margin-bottom: 6px; }
  .above-stat-num { font-size: 4.2rem; font-weight: 800; letter-spacing: -.04em; line-height: 1; transition: color .25s; }
  .above-stat-badge {
    display: inline-flex; align-items: center; gap: 4px;
    font-size: .82rem; font-weight: 700; padding: 4px 10px;
    border-radius: var(--radius-sm); line-height: 1;
    opacity: 0;
    transform: translateY(-5px);
    transition: opacity 0.45s ease, transform 0.45s cubic-bezier(0.34, 1.2, 0.64, 1);
  }
  .above-stat-badge.visible { opacity: 1; transform: translateY(0); }
  .above-stat-badge.up   { color: #059669; background: rgba(5,150,105,0.10); }
  .above-stat-badge.down { color: #DC2626; background: rgba(220,38,38,0.09); }
  .above-stat-badge.flat { color: var(--text-subtle); background: rgba(15,23,42,0.06); }
  .above-stat-desc { font-size: 1.5rem; color: var(--text); line-height: 1.4; font-weight: 700; letter-spacing: -.02em; }

  /* ── Chart tabs — float above hero card ──────────────────── */
  .chart-tab-row {
    display: flex; gap: 4px;
    flex: 1;
    overflow: visible;
  }
  .chart-tab {
    display: flex; flex-direction: column; align-items: flex-start; gap: 3px;
    padding: 10px 18px 12px; flex: 1;
    background: #FFFFFF;
    border: 1px solid rgba(15,23,42,0.09);
    border-bottom: none;
    border-radius: var(--radius-lg) var(--radius-lg) 0 0;
    cursor: pointer;
    position: relative;
    transition: transform 0.24s cubic-bezier(0.34, 1.4, 0.64, 1),
                box-shadow 0.24s cubic-bezier(0.34, 1.4, 0.64, 1),
                border-color var(--transition);
  }
  .chart-tab:hover {
    transform: translateY(-8px);
    box-shadow: 0 -3px 10px rgba(15,23,42,0.05), 0 8px 0 0 #FFFFFF;
    border-color: rgba(15,23,42,0.13);
  }
  .chart-tab::after {
    content: '';
    position: absolute;
    bottom: -8px;
    left: -1px;
    right: -1px;
    height: 8px;
    background: transparent;
    border-left: 1px solid rgba(15,23,42,0.13);
    border-right: 1px solid rgba(15,23,42,0.13);
    opacity: 0;
    transition: opacity 0s;
  }
  .chart-tab:hover::after {
    opacity: 1;
    transition: opacity 0s;
  }
  .chart-tab.active {
    background: #FFFFFF;
    border-color: rgba(15,23,42,0.09);
    border-top: 2px solid var(--tab-color, #059669);
  }
  /* Label = section-title style (matches "Sentiment vs Impact") */
  .ct-label { font-size: .88rem; font-weight: 700; color: var(--text); letter-spacing: -.01em; }
  .chart-tab.active .ct-label { color: var(--tab-color, #059669); }
  /* Value + change = chart-sub style */
  .ct-val-row { display: flex; align-items: center; gap: 6px; }
  .ct-val { font-size: .72rem; color: var(--text-muted); font-weight: 600; }
  .ct-change { display: flex; align-items: center; gap: 2px; font-size: .68rem; font-weight: 700; }
  .ct-change.up   { color: #059669; }
  .ct-change.down { color: #DC2626; }
  .ct-change.flat { color: var(--text-subtle); }

  .line-wrap  { position: relative; flex: 1; }
  .line-svg   { width: 100%; height: auto; display: block; }
  .line-grid  { stroke: rgba(15,23,42,0.07); stroke-width: 1; }
  .line-focus { stroke: rgba(27,58,107,0.22); stroke-width: 1; stroke-dasharray: 3 3; }
  .series-line { fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; vector-effect: non-scaling-stroke; }
  .y-lab     { font-size: 9px; fill: rgba(15,23,42,0.38); font-weight: 500; }
  .month-lab { font-size: 9.5px; fill: rgba(15,23,42,0.42); font-weight: 500; }


  /* Sentiment side (right) */
  .sentiment-side { padding: 22px 22px 18px; display: flex; flex-direction: column; align-items: center; gap: 14px; width: 100%; }
  .side-label { font-size: .72rem; font-weight: 700; text-transform: uppercase; letter-spacing: .07em; color: var(--text-subtle); align-self: flex-start; margin-bottom: 4px; }

  .ring-wrap { flex-shrink: 0; align-self: center; position: relative; }
  .ring-svg  { width: 200px; height: 200px; display: block; }
  .ring-arc  { transition: stroke-dashoffset 1.4s cubic-bezier(0.34, 1.2, 0.64, 1) 0.15s, stroke-width 0.22s ease, opacity 0.22s ease; }

.sent-row { cursor: pointer; border-radius: 6px; padding: 3px 5px; margin: 0 -5px; transition: background 0.18s; }
  .sent-row:hover, .sent-row-active { background: rgba(15,23,42,0.045); }

  .ring-overlay {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    pointer-events: none;
    gap: 2px;
  }
  .ring-count { font-size: 22px; font-weight: 800; color: var(--text); letter-spacing: -0.03em; line-height: 1; }
  .ring-sub   { font-size: 10px; color: var(--text-subtle); text-transform: uppercase; letter-spacing: .06em; font-weight: 600; }

  .sent-bars { width: 100%; display: flex; flex-direction: column; gap: 8px; margin-top: 8px; align-self: center; }
  .sent-row  { display: flex; align-items: center; gap: 7px; }
  .sent-dot  { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
  .pos-dot   { background: #059669; }
  .neg-dot   { background: #DC2626; }
  .sent-name { font-size: .75rem; font-weight: 600; color: var(--text-muted); width: 54px; flex-shrink: 0; }
  .sent-track { flex: 1; height: 6px; background: rgba(15,23,42,0.07); border-radius: 3px; overflow: hidden; }
  .sent-fill  { height: 100%; border-radius: 3px; transition: width 1.2s cubic-bezier(0.34, 1.2, 0.64, 1) 0.5s; }
  .sent-pos   { background: linear-gradient(90deg, #059669, #34d399); }
  .sent-neg   { background: linear-gradient(90deg, #DC2626, #f87171); }
  .sent-pct   { font-size: .72rem; font-weight: 700; color: var(--text-muted); width: 30px; text-align: right; flex-shrink: 0; }
  .sent-meta  { font-size: .7rem; color: var(--text-subtle); font-weight: 500; text-align: center; line-height: 1.4; align-self: center; }

  /* ── Scatter chart ───────────────────────────────────────── */
  .scatter-section { padding: 20px 24px 18px; }

  .scatter-legend {
    display: flex; gap: 10px; align-items: center; flex-shrink: 0; flex-wrap: wrap;
  }
  .sleg-item {
    font-size: .7rem; font-weight: 600; padding: 3px 9px;
    border-radius: 4px; border: 1px solid; cursor: pointer;
    transition: opacity 0.18s ease, box-shadow 0.18s ease;
    user-select: none;
  }
  .sleg-good     { color: #059669; background: rgba(5,150,105,0.10); border-color: rgba(5,150,105,0.28); }
  .sleg-mixed    { color: #1A5FAF; background: rgba(74,144,226,0.10); border-color: rgba(74,144,226,0.28); }
  .sleg-critical { color: #DC2626; background: rgba(220,38,38,0.08); border-color: rgba(220,38,38,0.25); }
  .sleg-item.sleg-inactive   { filter: grayscale(1); opacity: 0.38; }

  .scatter-wrap { position: relative; }
  .scatter-svg  { width: 100%; height: auto; display: block; }

  .s-grid     { stroke: rgba(15,23,42,0.07); stroke-width: 1; pointer-events: none; }
  .s-tick     { stroke: rgba(15,23,42,0.15); stroke-width: 1; pointer-events: none; }
  .s-axis-lab { font-size: 9px; fill: rgba(15,23,42,0.40); font-weight: 500; pointer-events: none; }
  .axis-title { font-size: 10px; fill: rgba(15,23,42,0.45); font-weight: 600; letter-spacing: .02em; pointer-events: none; }

  .q-line { stroke: rgba(15,23,42,0.10); stroke-width: 1; stroke-dasharray: 4 4; pointer-events: none; }

  .q-label { font-size: 9px; font-weight: 700; letter-spacing: .04em; text-transform: uppercase; pointer-events: none; }
  .q-danger  { fill: rgba(220,38,38,0.45); }
  .q-success { fill: rgba(5,150,105,0.45); }
  .q-muted   { fill: rgba(15,23,42,0.22); }

  .bubble-group { cursor: pointer; }

  .s-bubble {
    transition: r 0.18s ease, stroke-width 0.18s ease, stroke-opacity 0.18s ease;
  }
  .s-bubble.hovered { filter: brightness(1.08) saturate(1.15); }

  .b-label { font-size: 9.5px; font-weight: 700; pointer-events: none; }
  .b-sub   { font-size: 8.5px; font-weight: 600; pointer-events: none; opacity: 0.82; }

  /* Tooltip */
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
  .b-tip { transform: translate(-50%, calc(-100% - 14px)); }
  .tip-head {
    font-size: .73rem; font-weight: 700; color: var(--navy);
    margin-bottom: 7px; padding-bottom: 6px;
    border-bottom: 1px solid rgba(27,58,107,0.09);
    letter-spacing: -.01em;
  }
  .tip-row { display: flex; align-items: center; gap: 7px; font-size: .72rem; margin-top: 4px; }
  .tip-dot  { width: 7px; height: 7px; border-radius: 2px; flex-shrink: 0; }
  .tip-label { flex: 1; color: var(--text-muted); }
  .tip-val { font-weight: 700; color: var(--text); font-size: .74rem; }

  /* ── Responsive ──────────────────────────────────────────── */
  @media (max-width: 1180px) {
    .right-col {
      width: 248px;
    }

    .sentiment-panel {
      min-width: 0;
    }

    .sentiment-side {
      padding: 18px 16px 16px;
      gap: 12px;
    }

    .ring-svg {
      width: 176px;
      height: 176px;
    }

    .sent-name {
      width: 50px;
    }
  }

  @media (max-width: 900px) {
    .dash-page {
      padding-bottom: 48px;
    }

    .dash-header {
      margin-bottom: 18px;
    }

    .dash-header-inner {
      padding: 18px 20px 14px;
    }

    .above-stat-num {
      font-size: 3.4rem;
    }

    .above-stat-desc {
      font-size: 1.2rem;
    }

    .hero-outer {
      flex-direction: column;
    }

    .chart-tab-row {
      gap: 6px;
    }

    .chart-controls {
      flex-direction: column;
      align-items: stretch;
      gap: 8px;
      margin-bottom: 8px;
    }

    .date-btn-full {
      justify-content: space-between;
      min-height: 42px;
    }

    .trend-side {
      padding: 14px 16px 16px 18px;
    }

    .right-col {
      width: 100%;
      flex-direction: column;
    }

    .date-btn-full {
      justify-content: space-between;
    }

    .sentiment-panel {
      width: 100%;
      border-radius: var(--radius-lg);
    }

    .sentiment-side {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 14px;
      padding: 22px 20px 18px;
    }

    .sent-meta {
      text-align: center;
      align-self: center;
    }

    .hero-v-divider {
      width: 100%;
      height: 1px;
    }

    .scatter-section {
      padding: 18px 18px 16px;
    }

    .card-head {
      flex-direction: column;
    }
  }

  @media (max-width: 640px) {
    .chart-controls {
      margin-bottom: 8px;
    }

    .dash-header-inner {
      padding: 16px 14px 12px;
    }

    .above-stat {
      flex-direction: column;
      gap: 6px;
      margin-bottom: 8px;
    }

    .above-stat-num {
      font-size: 2.6rem;
    }

    .above-stat-desc {
      font-size: 1rem;
    }

    .chart-tab-row {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }

    .chart-tab {
      min-width: 0;
      border-bottom: 1px solid rgba(15,23,42,0.09);
      border-radius: var(--radius-lg);
      padding: 10px 10px 11px;
    }

    .chart-tab::after {
      display: none;
    }

    .chart-tab:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 14px rgba(15, 23, 42, 0.06);
    }

    .chart-panel {
      border-top: 1px solid rgba(15, 23, 42, 0.09);
      border-radius: var(--radius-lg);
    }

    .trend-side {
      padding: 12px 12px 14px 12px;
    }

    .ct-label {
      font-size: .8rem;
    }

    .ct-val-row {
      gap: 4px;
      flex-wrap: wrap;
    }

    .ct-val {
      font-size: .68rem;
    }

    .ct-change {
      font-size: .64rem;
    }

    .sentiment-side {
      padding: 18px 14px 16px;
    }

    .ring-svg {
      width: 176px;
      height: 176px;
    }

    .sent-bars {
      margin-top: 0;
    }

    .scatter-section {
      padding: 16px 12px 14px;
    }

    .chart-tip {
      min-width: 148px;
      padding: 8px 10px;
    }
  }
</style>
