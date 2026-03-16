<script lang="ts">
  import type { Snippet } from 'svelte';

  interface Props {
    title: string;
    children?: Snippet;
    /* kept for back-compat but no longer rendered */
    eyebrow?: string;
    subtitle?: string;
    meta?: string;
  }

  let { title, children }: Props = $props();
</script>

<div class="page-header-wrap">
  <div class="header-inner">
    <div class="header-row">
      <h1 class="page-title">{title}</h1>
      {#if children}
        <div class="header-actions">
          {@render children()}
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .page-header-wrap {
    margin-bottom: 24px;
  }

  .header-inner {
    max-width: 1280px;
    margin: 0 auto;
    padding: 20px 28px 18px;
    border-bottom: 1px solid rgba(15,23,42,0.10);
  }

  .header-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 24px;
    min-height: 36px;
  }

  .header-actions {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .page-title {
    font-size: 1.22rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.025em;
  }

  @media (max-width: 680px) {
    .header-row {
      flex-direction: column;
      align-items: flex-start;
      gap: 10px;
    }

    .header-actions {
      align-self: stretch;
    }
  }
</style>
