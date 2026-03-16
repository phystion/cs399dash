<script lang="ts">
  import { onMount } from 'svelte';

  interface Props {
    label: string;
    value: number;
    suffix?: string;
    accentColor?: string;
    icon?: string; // SVG path d attribute
    trend?: number; // percent change, e.g. +5 or -3
    delay?: number;
    active?: boolean;
    onclick?: () => void;
  }

  let {
    label,
    value,
    suffix = '',
    accentColor = '#1B3A6B',
    trend,
    delay = 0,
    active = false,
    onclick,
  }: Props = $props();

  let displayed = $state(0);

  onMount(() => {
    const DURATION = 900;
    const STEPS = 60;
    const intervalMs = DURATION / STEPS;

    const t = setTimeout(() => {
      let step = 0;
      const ticker = setInterval(() => {
        step++;
        const p = step / STEPS;
        const eased = 1 - Math.pow(1 - p, 3);
        displayed = Math.round(eased * value);
        if (step >= STEPS) { displayed = value; clearInterval(ticker); }
      }, intervalMs);
    }, delay);

    return () => clearTimeout(t);
  });
</script>

<button
  type="button"
  class="glass stat-card fade-in-up"
  class:is-active={active}
  style="--accent: {accentColor}; animation-delay: {delay}ms;"
  onclick={onclick}
  disabled={!onclick}
>
  <div class="top-row">
    <span class="label">{label}</span>
    {#if trend !== undefined}
      <span class="trend" class:up={trend >= 0} class:down={trend < 0}>
        {trend >= 0 ? '+' : ''}{trend}%
      </span>
    {/if}
  </div>
  <div class="value-row">
    <span class="value">{displayed.toLocaleString()}{suffix}</span>
  </div>
  <div class="accent-line"></div>
</button>

<style>
  .stat-card {
    appearance: none;
    text-align: left;
    padding: 22px 24px 20px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    position: relative;
    overflow: hidden;
    cursor: pointer;
    transition: border-color var(--transition);
  }

  .stat-card:disabled {
    cursor: default;
  }

  .stat-card:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 2px;
  }

  .stat-card:hover {
    border-color: rgba(15, 23, 42, 0.18);
  }

  .stat-card.is-active {
    border-color: var(--accent);
  }

  .top-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .label {
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }

  .trend {
    font-size: 0.75rem;
    font-weight: 700;
    padding: 2px 7px;
    border-radius: 6px;
  }

  .trend.up {
    color: var(--positive);
    background: var(--positive-bg);
  }

  .trend.down {
    color: var(--negative);
    background: var(--negative-bg);
  }

  .value-row { display: flex; align-items: baseline; gap: 4px; }

  .value {
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    line-height: 1;
    color: var(--accent);
  }

  /* Colored bottom accent line */
  .accent-line {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--accent);
    opacity: 0.6;
    border-radius: 0 0 var(--radius-lg) var(--radius-lg);
    transition: opacity var(--transition);
  }

  .is-active .accent-line {
    opacity: 1;
  }
</style>
