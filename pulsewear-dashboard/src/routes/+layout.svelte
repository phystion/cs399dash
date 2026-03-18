<script lang="ts">
  import '../app.css';
  import Sidebar from '$lib/components/Sidebar.svelte';
  import TopBar from '$lib/components/TopBar.svelte';
  import ChatPanel from '$lib/components/ChatPanel.svelte';
  import type { Snippet } from 'svelte';

  import type { Theme, RoadmapItem, MonthlyDataPoint } from '$lib/data';
  let { children, data }: { children: Snippet; data: { themes?: Theme[]; roadmapItems?: RoadmapItem[]; monthlyTrends?: MonthlyDataPoint[] } } = $props();
  let sidebarExpanded = $state(false);
  let chatOpen = $state(false);
</script>

<TopBar
  {sidebarExpanded}
  ontoggle={() => sidebarExpanded = !sidebarExpanded}
  onchatToggle={() => chatOpen = !chatOpen}
  onchatClose={() => chatOpen = false}
  {chatOpen}
  themes={data.themes}
  roadmapItems={data.roadmapItems}
/>

<div class="app-shell">
  <Sidebar bind:expanded={sidebarExpanded} />

  {#if sidebarExpanded}
    <button
      class="app-backdrop"
      type="button"
      aria-label="Close sidebar"
      onclick={() => sidebarExpanded = false}
    ></button>
  {/if}

  <div class="app-content" class:shifted={sidebarExpanded}>
    {@render children()}
  </div>
</div>

<ChatPanel open={chatOpen} onclose={() => chatOpen = false} />

<style>
  :global(html, body) { height: 100%; }

  .app-shell {
    display: flex;
    min-height: 100vh;
    padding-top: var(--topbar-height);
    position: relative;
    isolation: isolate;
  }

  .app-content {
    flex: 1;
    min-width: 0;
    margin-left: 72px;
    transition: margin-left 0.26s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .app-content.shifted {
    margin-left: 220px;
  }

  .app-backdrop {
    display: none;
  }

  @media (max-width: 860px) {
    .app-content {
      margin-left: 0;
    }
    .app-content.shifted {
      margin-left: 0;
    }

    .app-backdrop {
      display: block;
      position: fixed;
      inset: var(--topbar-height) 0 0;
      z-index: 95;
      border: none;
      background: rgba(13, 27, 46, 0.32);
      backdrop-filter: blur(2px);
      -webkit-backdrop-filter: blur(2px);
    }
  }
</style>
