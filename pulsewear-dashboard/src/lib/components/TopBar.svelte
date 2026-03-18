<script lang="ts">
  import { tick } from 'svelte';
  import { page } from '$app/stores';
  import { accountProfile, roadmapItems as staticRoadmap, themes as staticThemes } from '$lib/data';
  import type { Theme, RoadmapItem } from '$lib/data';

  type SearchCategory = 'Page' | 'Theme' | 'Roadmap';

  interface SearchItem {
    label: string;
    description: string;
    href: string;
    category: SearchCategory;
    keywords: string;
  }

  interface Props {
    sidebarExpanded: boolean;
    ontoggle: () => void;
    onchatToggle: () => void;
    onchatClose: () => void;
    chatOpen?: boolean;
    themes?: Theme[];
    roadmapItems?: RoadmapItem[];
  }
  let {
    sidebarExpanded, ontoggle, onchatToggle, onchatClose, chatOpen = false,
    themes = staticThemes,
    roadmapItems = staticRoadmap,
  }: Props = $props();

  const pageItems: SearchItem[] = [
    { label: 'Dashboard', description: 'Overview of feedback volume, sentiment, and theme activity', href: '/', category: 'Page', keywords: 'home overview dashboard stats' },
    { label: 'Recommendations', description: 'Top product improvements ranked by impact and sentiment', href: '/recommendations', category: 'Page', keywords: 'recommendations actions priorities product improvements' },
    { label: 'Theme Analysis', description: 'Rank and compare customer feedback clusters', href: '/analysis', category: 'Page', keywords: 'analysis themes clusters ranking' },
    { label: 'Sentiment Analyzer', description: 'Run DistilBERT sentiment checks on new feedback text', href: '/sentiment', category: 'Page', keywords: 'sentiment analyzer distilbert nlp classify text' },
    { label: 'Trends', description: 'Track feedback movement across time windows and topics', href: '/trends', category: 'Page', keywords: 'trends charts movement time series' },
    { label: 'Roadmap Priorities', description: 'See active initiatives mapped to customer pain points', href: '/roadmap', category: 'Page', keywords: 'roadmap priorities initiatives status' },
    { label: 'Feedback Explorer', description: 'Browse raw customer quotes by theme and channel', href: '/feedback', category: 'Page', keywords: 'feedback explorer quotes customer comments' },
    { label: 'Assistant', description: 'Ask the rule-based assistant about clusters, trends, and priorities', href: '/chat', category: 'Page', keywords: 'chat assistant rule-based copilot' },
  ];

  const themeItems = $derived<SearchItem[]>(themes.map((theme) => ({
    label: theme.name,
    description: `${theme.volume.toLocaleString()} responses · ${theme.positive_pct}% positive sentiment`,
    href: `/feedback?cluster=${theme.cluster_id}`,
    category: 'Theme',
    keywords: `${theme.name} ${theme.description} cluster ${theme.cluster_id} ${theme.roadmap_id ?? ''}`,
  })));

  const roadmapSearchItems = $derived<SearchItem[]>(roadmapItems.map((item) => ({
    label: item.roadmap_id,
    description: `${item.theme_name} · ${item.status} · priority ${item.priority_score}`,
    href: `/roadmap`,
    category: 'Roadmap',
    keywords: `${item.roadmap_id} ${item.theme_name} ${item.status} roadmap initiative priority`,
  })));

  const searchItems = $derived([...pageItems, ...themeItems, ...roadmapSearchItems]);
  const suggestedSearchItems = $derived([
    ...pageItems.slice(0, 4),
    ...[...themeItems].sort((a, b) => {
      const aTheme = themes.find((theme) => theme.name === a.label);
      const bTheme = themes.find((theme) => theme.name === b.label);
      return (bTheme?.priority_score ?? 0) - (aTheme?.priority_score ?? 0);
    }).slice(0, 4),
  ]);

  const notifications = $derived([...roadmapItems]
    .filter((item) => item.priority_score >= 60)
    .sort((a, b) => b.priority_score - a.priority_score)
    .slice(0, 3)
    .map((item) => {
      const negativePct = 100 - item.positive_pct;
      return {
        ...item,
        detail: `${item.volume.toLocaleString()} responses · ${negativePct}% negative sentiment`,
        href: `/feedback?cluster=${item.cluster_id}`,
        tone:
          item.priority_score >= 80 ? 'critical' :
          item.priority_score >= 60 ? 'high' :
          item.status === 'Under Review' ? 'watch' :
          'info',
      };
    }));

  let searchOpen = $state(false);
  let notifOpen = $state(false);
  let profileOpen = $state(false);
  let searchQuery = $state('');
  let hasUnreadNotifications = $state(true);

  let searchButton: HTMLButtonElement | undefined = $state();
  let notifButton: HTMLButtonElement | undefined = $state();
  let profileButton: HTMLButtonElement | undefined = $state();
  let searchPanel: HTMLDivElement | undefined = $state();
  let notifPanel: HTMLDivElement | undefined = $state();
  let profilePanel: HTMLDivElement | undefined = $state();
  let searchInput: HTMLInputElement | undefined = $state();

  const currentPath = $derived($page.url.pathname);

  const filteredSearchItems = $derived(() => {
    const query = searchQuery.trim().toLowerCase();
    const pool = query ? searchItems : suggestedSearchItems;

    return pool
      .filter((item, index, arr) => {
        const haystack = `${item.label} ${item.description} ${item.keywords}`.toLowerCase();
        return (!query || haystack.includes(query)) && arr.findIndex((candidate) => candidate.href === item.href && candidate.label === item.label) === index;
      })
      .slice(0, 8);
  });

  async function toggleSearch() {
    const nextOpen = !searchOpen;
    searchOpen = nextOpen;
    notifOpen = false;
    profileOpen = false;
    if (nextOpen && chatOpen) onchatClose();

    if (nextOpen) {
      await tick();
      searchInput?.focus();
      searchInput?.select();
    }
  }

  function toggleNotifications() {
    const nextOpen = !notifOpen;
    notifOpen = nextOpen;
    searchOpen = false;
    profileOpen = false;
    if (nextOpen && chatOpen) onchatClose();

    if (nextOpen) {
      hasUnreadNotifications = false;
    }
  }

  function toggleProfile() {
    const nextOpen = !profileOpen;
    profileOpen = nextOpen;
    searchOpen = false;
    notifOpen = false;
    if (nextOpen && chatOpen) onchatClose();
  }

  function handleAiToggle() {
    closePanels();
    onchatToggle();
  }

  function closePanels() {
    searchOpen = false;
    notifOpen = false;
    profileOpen = false;
  }

  function clearSearch() {
    searchQuery = '';
    searchInput?.focus();
  }

  $effect(() => {
    function handleDocumentClick(event: MouseEvent) {
      const target = event.target;
      if (!(target instanceof Node)) return;

      if (searchOpen && searchPanel && searchButton && !searchPanel.contains(target) && !searchButton.contains(target)) {
        searchOpen = false;
      }

      if (notifOpen && notifPanel && notifButton && !notifPanel.contains(target) && !notifButton.contains(target)) {
        notifOpen = false;
      }

      if (profileOpen && profilePanel && profileButton && !profilePanel.contains(target) && !profileButton.contains(target)) {
        profileOpen = false;
      }
    }

    function handleDocumentKeydown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        closePanels();
        return;
      }

      const target = event.target;
      const isTyping =
        target instanceof HTMLInputElement ||
        target instanceof HTMLTextAreaElement ||
        (target instanceof HTMLElement && target.isContentEditable);

      if (!isTyping && ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k')) {
        event.preventDefault();
        toggleSearch();
      }
    }

    document.addEventListener('click', handleDocumentClick);
    document.addEventListener('keydown', handleDocumentKeydown);

    return () => {
      document.removeEventListener('click', handleDocumentClick);
      document.removeEventListener('keydown', handleDocumentKeydown);
    };
  });
</script>

<header class="topbar">
  <div class="topbar-left">
    <!-- Hamburger menu -->
    <button
      class="topbar-btn menu-btn"
      onclick={ontoggle}
      aria-label="Toggle sidebar"
      aria-expanded={sidebarExpanded}
    >
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="3" y1="6" x2="21" y2="6"/>
        <line x1="3" y1="12" x2="21" y2="12"/>
        <line x1="3" y1="18" x2="21" y2="18"/>
      </svg>
    </button>

    <!-- Brand -->
    <div class="brand">
      <span class="brand-main">Feedback Management</span>
      <span class="brand-dot">·</span>
      <span class="brand-sub">PulseWear Labs</span>
    </div>
  </div>

  <div class="topbar-right">
    <!-- Feedback Assistant -->
    <button class="topbar-btn ai-btn" class:active={chatOpen} onclick={handleAiToggle} aria-label="Feedback assistant">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
           stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="11" width="18" height="10" rx="2"/>
        <path d="M9 11V7a3 3 0 0 1 6 0v4"/>
        <circle cx="9" cy="16" r="1" fill="currentColor" stroke="none"/>
        <circle cx="15" cy="16" r="1" fill="currentColor" stroke="none"/>
        <path d="M12 3v2M9.5 4.5l1 1M14.5 4.5l-1 1"/>
      </svg>
    </button>

    <!-- Search -->
    <div class="topbar-action">
      <button
        class="topbar-btn"
        class:active={searchOpen}
        bind:this={searchButton}
        onclick={toggleSearch}
        aria-label="Search"
        aria-expanded={searchOpen}
        aria-haspopup="dialog"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
      </button>

      {#if searchOpen}
        <div class="popover search-popover" bind:this={searchPanel} role="dialog" aria-label="Search dashboard">
          <div class="popover-header">
            <span class="popover-title">Search dashboard</span>
          </div>

          <div class="search-input-wrap">
            <svg class="input-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="11" cy="11" r="8"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <input
              bind:this={searchInput}
              bind:value={searchQuery}
              class="search-input"
              type="text"
              placeholder="Jump to pages, themes, roadmap IDs..."
              aria-label="Search pages, themes, and roadmap items"
            />
            {#if searchQuery}
              <button class="clear-btn" onclick={clearSearch} aria-label="Clear search">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                     stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"/>
                  <line x1="6" y1="6" x2="18" y2="18"/>
                </svg>
              </button>
            {/if}
          </div>

          <div class="search-results">
            {#if filteredSearchItems().length > 0}
              {#each filteredSearchItems() as item (item.label + item.href)}
                <a
                  class="search-result"
                  class:is-current={item.href === currentPath}
                  href={item.href}
                  onclick={closePanels}
                >
                  <div class="result-copy">
                    <span class="result-label">{item.label}</span>
                    <span class="result-description">{item.description}</span>
                  </div>
                  <span class="result-category">{item.category}</span>
                </a>
              {/each}
            {:else}
              <div class="popover-empty">
                <p>No matches for “{searchQuery.trim()}”.</p>
                <span>Try a theme like Battery, a page like Trends, or a roadmap ID.</span>
              </div>
            {/if}
          </div>
        </div>
      {/if}
    </div>

    <!-- Notifications -->
    <div class="topbar-action">
      <button
        class="topbar-btn notif-btn"
        class:active={notifOpen}
        bind:this={notifButton}
        onclick={toggleNotifications}
        aria-label="Notifications"
        aria-expanded={notifOpen}
        aria-haspopup="dialog"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
          <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
        </svg>
        {#if hasUnreadNotifications}
          <span class="notif-dot" aria-hidden="true"></span>
        {/if}
      </button>

      {#if notifOpen}
        <div class="popover notif-popover" bind:this={notifPanel} role="dialog" aria-label="Notifications">
          <div class="popover-header">
            <span class="popover-title">Alerts</span>
            <a class="popover-link" href="/roadmap" onclick={closePanels}>Open roadmap</a>
          </div>

          <div class="notif-list">
            {#each notifications as item (item.roadmap_id)}
              <a class="notif-item" href={item.href} onclick={closePanels}>
                <span class="notif-tone {item.tone}"></span>
                <div class="notif-copy">
                  <span class="notif-title">{item.theme_name}</span>
                  <span class="notif-detail">{item.detail}</span>
                  <span class="notif-meta">{item.roadmap_id} · {item.status} · priority {item.priority_score}</span>
                </div>
              </a>
            {/each}
          </div>
        </div>
      {/if}
    </div>

    <div class="topbar-sep"></div>

    <div class="topbar-action">
      <button
        class="topbar-btn profile-btn"
        class:active={profileOpen || currentPath.startsWith('/settings')}
        bind:this={profileButton}
        onclick={toggleProfile}
        aria-label={`Profile for ${accountProfile.name}`}
        aria-expanded={profileOpen}
        aria-haspopup="dialog"
      >
        <span class="avatar">{accountProfile.initials}</span>
      </button>

      {#if profileOpen}
        <div class="popover profile-popover" bind:this={profilePanel} role="dialog" aria-label="Account information">
          <div class="profile-card-header">
            <div class="profile-card-avatar">{accountProfile.initials}</div>
            <div class="profile-card-copy">
              <span class="profile-card-name">{accountProfile.name}</span>
              <span class="profile-card-role">{accountProfile.role}</span>
            </div>
          </div>

          <div class="profile-card-grid">
            <div class="profile-card-field">
              <span class="profile-card-label">Email</span>
              <span class="profile-card-value">{accountProfile.email}</span>
            </div>
            <div class="profile-card-field">
              <span class="profile-card-label">Team</span>
              <span class="profile-card-value">{accountProfile.team}</span>
            </div>
            <div class="profile-card-field">
              <span class="profile-card-label">Location</span>
              <span class="profile-card-value">{accountProfile.location}</span>
            </div>
            <div class="profile-card-field">
              <span class="profile-card-label">Access</span>
              <span class="profile-card-value">{accountProfile.plan}</span>
            </div>
          </div>

          <div class="profile-actions">
            <a class="popover-link" href="/settings" onclick={closePanels}>Open settings</a>
          </div>
        </div>
      {/if}
    </div>

  </div>
</header>

<style>
  .topbar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: var(--topbar-height);
    z-index: 150;
    background: #FFFFFF;
    border-bottom: 1px solid rgba(15, 23, 42, 0.09);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.07);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 14px 0 12px;
  }

  /* ── Left ─────────────────────────────────────────────── */
  .topbar-left {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.78rem;
    font-weight: 600;
    white-space: nowrap;
    user-select: none;
    min-width: 0;
    overflow: hidden;
  }

  .brand-main {
    color: var(--navy);
    letter-spacing: 0.01em;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .brand-dot {
    color: var(--blue);
    font-size: 0.9rem;
    line-height: 1;
  }

  .brand-sub {
    color: var(--blue);
    letter-spacing: 0.01em;
  }

  /* ── Right ────────────────────────────────────────────── */
  .topbar-right {
    display: flex;
    align-items: center;
    gap: 2px;
  }

  .topbar-action {
    position: relative;
  }

  .topbar-sep {
    width: 1px;
    height: 22px;
    background: rgba(15, 23, 42, 0.09);
    margin: 0 6px;
    flex-shrink: 0;
  }

  /* ── Buttons ──────────────────────────────────────────── */
  .topbar-btn {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    border-radius: 6px;
    border: none;
    background: transparent;
    color: var(--text-muted);
    cursor: pointer;
    font-family: inherit;
    transition: background 0.14s ease, color 0.14s ease;
    flex-shrink: 0;
  }

  /* Blue-tinted highlight — distinct from sidebar's gray */
  .topbar-btn:hover {
    background: rgba(74, 144, 226, 0.10);
    color: var(--navy);
  }

  .topbar-btn.active {
    background: rgba(74, 144, 226, 0.14);
    color: var(--navy);
  }

  .menu-btn {
    width: 36px;
    height: 36px;
  }

  /* Notification dot */
  .notif-btn { position: relative; }

  .notif-dot {
    position: absolute;
    top: 7px;
    right: 7px;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #DC2626;
    border: 1.5px solid #FFFFFF;
    pointer-events: none;
  }

  /* Assistant button — slightly distinctive */
  .ai-btn {
    color: var(--blue);
  }
  .ai-btn:hover {
    background: rgba(74, 144, 226, 0.14);
    color: var(--navy);
  }
  .ai-btn.active {
    background: rgba(74, 144, 226, 0.14);
    color: var(--navy);
  }

  /* Profile avatar */
  .profile-btn { width: 36px; height: 36px; }

  .avatar {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 26px;
    height: 26px;
    border-radius: 50%;
    background: linear-gradient(135deg, #4A90E2 0%, #1B3A6B 100%);
    color: #FFFFFF;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    pointer-events: none;
  }

  .popover {
    position: absolute;
    top: calc(100% + 10px);
    right: 0;
    width: min(360px, calc(100vw - 24px));
    background: rgba(255, 255, 255, 0.98);
    border: 1px solid rgba(15, 23, 42, 0.10);
    border-radius: 12px;
    box-shadow: 0 18px 42px rgba(15, 23, 42, 0.16);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    overflow: hidden;
  }

  .search-popover {
    width: min(380px, calc(100vw - 24px));
  }

  .notif-popover {
    width: min(312px, calc(100vw - 24px));
  }

  .profile-popover {
    width: min(308px, calc(100vw - 24px));
    padding: 16px;
  }

  .popover-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    padding: 14px 14px 12px;
    border-bottom: 1px solid rgba(15, 23, 42, 0.07);
  }

  .popover-title {
    display: block;
    font-size: 0.81rem;
    font-weight: 700;
    color: var(--navy);
  }

  .popover-subtitle {
    margin-top: 4px;
    font-size: 0.72rem;
    color: var(--text-subtle);
  }

  .popover-link {
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--blue);
    text-decoration: none;
    white-space: nowrap;
  }

  .search-input-wrap {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 14px;
    border-bottom: 1px solid rgba(15, 23, 42, 0.07);
  }

  .input-icon {
    color: var(--text-subtle);
    flex-shrink: 0;
  }

  .search-input {
    flex: 1;
    border: none;
    background: transparent;
    color: var(--text);
    font: inherit;
    font-size: 0.84rem;
    outline: none;
  }

  .search-input::placeholder {
    color: var(--text-subtle);
  }

  .clear-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    border: none;
    border-radius: 6px;
    background: rgba(15, 23, 42, 0.05);
    color: var(--text-muted);
    cursor: pointer;
  }

  .search-results,
  .notif-list {
    display: flex;
    flex-direction: column;
    padding: 8px;
  }

  .profile-card-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding-bottom: 14px;
    border-bottom: 1px solid rgba(15, 23, 42, 0.07);
  }

  .profile-card-avatar {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 42px;
    height: 42px;
    border-radius: 12px;
    background: linear-gradient(135deg, #4A90E2 0%, #1B3A6B 100%);
    color: #FFFFFF;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    flex-shrink: 0;
  }

  .profile-card-copy {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
  }

  .profile-card-name {
    font-size: 0.92rem;
    font-weight: 700;
    color: var(--navy);
  }

  .profile-card-role {
    font-size: 0.74rem;
    color: var(--text-muted);
  }

  .profile-card-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px 10px;
    padding-top: 14px;
  }

  .profile-actions {
    display: flex;
    justify-content: flex-end;
    padding-top: 14px;
    margin-top: 14px;
    border-top: 1px solid rgba(15, 23, 42, 0.07);
  }

  .profile-card-field {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
  }

  .profile-card-label {
    font-size: 0.68rem;
    font-weight: 700;
    color: var(--text-subtle);
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }

  .profile-card-value {
    font-size: 0.78rem;
    color: var(--text);
    line-height: 1.35;
    word-break: break-word;
  }

  .search-result,
  .notif-item {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    padding: 10px 10px;
    border-radius: 10px;
    text-decoration: none;
    transition: background 0.14s ease;
  }

  .search-result:hover,
  .notif-item:hover {
    background: rgba(74, 144, 226, 0.08);
  }

  .search-result.is-current {
    background: rgba(74, 144, 226, 0.12);
  }

  .result-copy,
  .notif-copy {
    display: flex;
    flex-direction: column;
    gap: 3px;
    min-width: 0;
  }

  .notif-copy {
    flex: 1;
  }

  .result-label,
  .notif-title {
    font-size: 0.82rem;
    font-weight: 700;
    color: var(--text);
  }

  .result-description,
  .notif-detail {
    font-size: 0.74rem;
    color: var(--text-muted);
    line-height: 1.35;
  }

  .result-category {
    flex-shrink: 0;
    padding: 3px 7px;
    border-radius: 999px;
    background: rgba(74, 144, 226, 0.10);
    color: var(--navy);
    font-size: 0.66rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .popover-empty {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 18px 14px 20px;
    color: var(--text-muted);
  }

  .popover-empty p {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--text);
  }

  .popover-empty span,
  .notif-meta {
    font-size: 0.72rem;
    color: var(--text-subtle);
  }

  .notif-item {
    align-items: center;
    justify-content: flex-start;
    gap: 8px;
  }

  .notif-tone {
    width: 9px;
    height: 9px;
    border-radius: 999px;
    flex-shrink: 0;
    margin-top: 3px;
  }

  .notif-tone.critical { background: #DC2626; }
  .notif-tone.high { background: #F97316; }
  .notif-tone.watch { background: #D97706; }
  .notif-tone.info { background: #4A90E2; }

  @media (max-width: 700px) {
    .brand-sub,
    .brand-dot {
      display: none;
    }

    .search-popover,
    .notif-popover,
    .profile-popover {
      right: -42px;
    }
  }

  @media (max-width: 560px) {
    .topbar {
      padding: 0 10px 0 8px;
    }

    .topbar-left {
      gap: 6px;
    }

    .topbar-right {
      gap: 0;
    }

    .topbar-sep {
      margin: 0 3px;
    }

    .brand {
      font-size: 0.72rem;
    }

    .search-popover,
    .notif-popover,
    .profile-popover {
      right: -10px;
    }

    .profile-card-grid {
      grid-template-columns: 1fr;
    }
  }

</style>
