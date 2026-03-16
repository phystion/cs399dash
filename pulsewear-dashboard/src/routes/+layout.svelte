<script lang="ts">
  import '../app.css';
  import Sidebar from '$lib/components/Sidebar.svelte';
  import TopBar from '$lib/components/TopBar.svelte';
  import ChatPanel from '$lib/components/ChatPanel.svelte';
  import type { Snippet } from 'svelte';

  let { children }: { children: Snippet } = $props();
  let sidebarExpanded = $state(false);
  let chatOpen = $state(false);
</script>

<TopBar
  {sidebarExpanded}
  ontoggle={() => sidebarExpanded = !sidebarExpanded}
  onchatToggle={() => chatOpen = !chatOpen}
  onchatClose={() => chatOpen = false}
  {chatOpen}
/>

<div class="app-shell">
  <Sidebar expanded={sidebarExpanded} />

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

  @media (max-width: 860px) {
    .app-content {
      margin-left: 0;
    }
    .app-content.shifted {
      margin-left: 0;
    }
  }
</style>
