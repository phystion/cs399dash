<script lang="ts">
  import { page } from '$app/stores';
  import { accountProfile } from '$lib/data';

  interface Props {
    expanded: boolean;
  }

  let { expanded }: Props = $props();

  const currentPath = $derived($page.url.pathname);
</script>

<aside class="sidebar" class:expanded aria-label="Main navigation">
  <div class="logo-area">
    <a
      href="/settings"
      class="account-trigger"
      class:active={currentPath.startsWith('/settings')}
      aria-label={`Open account page for ${accountProfile.name}`}
      aria-current={currentPath.startsWith('/settings') ? 'page' : undefined}
      data-tooltip="Account"
    >
      <div class="account-avatar" aria-hidden="true">{accountProfile.initials}</div>
      <div class="account-info">
        <span class="account-label">Your Account</span>
        <span class="account-name">{accountProfile.name}</span>
      </div>
    </a>
  </div>

  <div class="sidebar-divider"></div>

  <nav class="sidebar-nav" aria-label="Pages">
    <a
      href="/"
      class="nav-item"
      class:active={currentPath === '/'}
      data-tooltip="Dashboard"
      aria-label="Dashboard"
    >
      <svg class="nav-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2"/>
        <path d="M7 16l3-4 3 3 3-5"/>
      </svg>
      <span class="nav-label">Dashboard</span>
    </a>

    <a
      href="/recommendations"
      class="nav-item"
      class:active={currentPath.startsWith('/recommendations')}
      data-tooltip="Recommendations"
      aria-label="Recommendations"
    >
      <svg class="nav-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="9"/>
        <circle cx="12" cy="12" r="4.5"/>
        <circle cx="12" cy="12" r="1" fill="currentColor" stroke="none"/>
      </svg>
      <span class="nav-label">Recommendations</span>
    </a>

    <a
      href="/analysis"
      class="nav-item"
      class:active={currentPath.startsWith('/analysis')}
      data-tooltip="Analysis"
      aria-label="Analysis"
    >
      <svg class="nav-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
        <polyline points="16 7 22 7 22 13"/>
      </svg>
      <span class="nav-label">Analysis</span>
    </a>

    <a
      href="/sentiment"
      class="nav-item"
      class:active={currentPath.startsWith('/sentiment')}
      data-tooltip="Sentiment"
      aria-label="Sentiment"
    >
      <svg class="nav-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="9"/>
        <circle cx="9" cy="10" r="1"/>
        <circle cx="15" cy="10" r="1"/>
        <path d="M8.5 14.5s1.5 2 3.5 2 3.5-2 3.5-2"/>
      </svg>
      <span class="nav-label">Sentiment</span>
    </a>

    <a
      href="/trends"
      class="nav-item"
      class:active={currentPath.startsWith('/trends')}
      data-tooltip="Trends"
      aria-label="Trends"
    >
      <svg class="nav-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 3v18h18"/>
        <path d="m7 14 4-4 3 3 4-6"/>
      </svg>
      <span class="nav-label">Trends</span>
    </a>

    <a
      href="/roadmap"
      class="nav-item"
      class:active={currentPath.startsWith('/roadmap')}
      data-tooltip="Roadmap"
      aria-label="Roadmap"
    >
      <svg class="nav-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <path d="M3 21V5"/>
        <path d="M5 6h11l-2 4 2 4H5"/>
      </svg>
      <span class="nav-label">Roadmap</span>
    </a>

    <a
      href="/feedback"
      class="nav-item"
      class:active={currentPath.startsWith('/feedback')}
      data-tooltip="Feedback"
      aria-label="Feedback"
    >
      <svg class="nav-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 11.5a8.5 8.5 0 0 1-8.5 8.5c-1.7 0-3.29-.5-4.62-1.35L3 20l1.35-4.88A8.46 8.46 0 0 1 3.5 11.5 8.5 8.5 0 1 1 21 11.5z"/>
      </svg>
      <span class="nav-label">Feedback</span>
    </a>

    <a
      href="/chat"
      class="nav-item"
      class:active={currentPath.startsWith('/chat')}
      data-tooltip="Assistant"
      aria-label="Assistant"
    >
      <svg class="nav-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 2a10 10 0 0 1 7.39 16.74L21 22l-3.26-1.61A10 10 0 1 1 12 2z"/>
        <path d="M8 10h.01M12 10h.01M16 10h.01" stroke-width="2.5" stroke-linecap="round"/>
      </svg>
      <span class="nav-label">Assistant</span>
    </a>
  </nav>

  <div class="sidebar-bottom">
    <a
      href="/settings"
      class="nav-item"
      class:active={currentPath.startsWith('/settings')}
      data-tooltip="Settings"
      aria-label="Settings"
    >
      <svg class="nav-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor"
        stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="3"/>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
      </svg>
      <span class="nav-label">Settings</span>
    </a>
  </div>
</aside>

<style>
  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    width: 72px;
    z-index: 100;
    background: #FFFFFF;
    border-right: 1px solid rgba(15, 23, 42, 0.09);
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: calc(var(--topbar-height) + 10px) 0 10px;
    overflow: visible;
    transition: width 0.26s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .sidebar.expanded {
    width: 220px;
    align-items: flex-start;
  }

  .logo-area {
    width: 100%;
    padding: 0 10px;
    flex-shrink: 0;
  }

  .account-trigger {
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    padding: 0;
    background: transparent;
    border: none;
    color: inherit;
    text-decoration: none;
  }

  .account-trigger:hover .account-avatar,
  .account-trigger.active .account-avatar {
    box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.14);
  }

  .account-trigger[data-tooltip]::after {
    content: attr(data-tooltip);
    position: absolute;
    left: calc(100% + 10px);
    top: 18px;
    transform: translateY(-50%);
    background: rgba(13, 27, 46, 0.90);
    color: rgba(255, 255, 255, 0.95);
    padding: 5px 10px;
    border-radius: 6px;
    border: 1px solid rgba(255, 255, 255, 0.16);
    font-size: 0.74rem;
    font-weight: 500;
    white-space: nowrap;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.12s ease;
    z-index: 300;
  }

  .account-trigger:hover::after {
    opacity: 1;
  }

  .sidebar.expanded .account-trigger[data-tooltip]::after {
    display: none;
  }

  .account-avatar {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, #4A90E2 0%, #1B3A6B 100%);
    color: #FFFFFF;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    flex-shrink: 0;
    transition:
      width 0.26s cubic-bezier(0.4, 0, 0.2, 1),
      height 0.26s cubic-bezier(0.4, 0, 0.2, 1),
      font-size 0.26s ease,
      box-shadow 0.18s ease;
  }

  .sidebar.expanded .account-avatar {
    width: 52px;
    height: 52px;
    font-size: 0.82rem;
  }

  .account-info {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    opacity: 0;
    max-height: 0;
    overflow: hidden;
    pointer-events: none;
    transition: opacity 0.18s ease 0.1s, max-height 0.26s ease;
  }

  .sidebar.expanded .account-info {
    opacity: 1;
    max-height: 48px;
  }

  .account-label {
    font-size: 0.63rem;
    font-weight: 700;
    color: var(--text-subtle);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    white-space: nowrap;
    text-align: center;
  }

  .account-name {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--navy);
    white-space: nowrap;
    text-align: center;
  }

  .sidebar-divider {
    width: 28px;
    height: 1px;
    background: rgba(27, 58, 107, 0.10);
    margin: 8px 0 4px;
    flex-shrink: 0;
    transition: width 0.26s ease;
  }

  .sidebar.expanded .sidebar-divider {
    width: calc(100% - 20px);
    margin-left: 10px;
  }

  .sidebar-nav {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    width: 100%;
    padding: 0 10px;
    overflow-y: auto;
    overflow-x: hidden;
    scrollbar-width: none;
  }

  .sidebar-nav::-webkit-scrollbar {
    display: none;
  }

  .sidebar.expanded .sidebar-nav {
    align-items: flex-start;
  }

  .nav-item {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 52px;
    height: 42px;
    border-radius: 7px;
    color: var(--text-muted);
    text-decoration: none;
    cursor: pointer;
    border: 1px solid transparent;
    background: transparent;
    font-family: inherit;
    gap: 0;
    transition:
      background 0.15s ease,
      color 0.15s ease,
      width 0.26s cubic-bezier(0.4, 0, 0.2, 1),
      justify-content 0.1s ease,
      padding 0.26s ease;
    flex-shrink: 0;
    overflow: hidden;
    white-space: nowrap;
  }

  .sidebar.expanded .nav-item {
    width: 100%;
    justify-content: flex-start;
    padding-left: 14px;
    gap: 10px;
  }

  .nav-item:hover {
    background: rgba(15, 23, 42, 0.05);
    color: var(--text);
  }

  .nav-item.active {
    color: var(--blue);
    background: transparent;
  }

  .nav-item.active .nav-icon {
    stroke-width: 2.2;
  }

  .nav-icon {
    flex-shrink: 0;
    stroke: currentColor;
  }

  .nav-label {
    font-size: 0.83rem;
    font-weight: 500;
    color: inherit;
    opacity: 0;
    max-width: 0;
    overflow: hidden;
    pointer-events: none;
    transition: opacity 0.16s ease, max-width 0.26s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .sidebar.expanded .nav-label {
    opacity: 1;
    max-width: 140px;
  }

  .sidebar.expanded .nav-item[data-tooltip]::after {
    display: none;
  }

  .nav-item[data-tooltip]::after {
    content: attr(data-tooltip);
    position: absolute;
    left: calc(100% + 10px);
    top: 50%;
    transform: translateY(-50%);
    background: rgba(13, 27, 46, 0.90);
    color: rgba(255, 255, 255, 0.95);
    padding: 5px 10px;
    border-radius: 6px;
    border: 1px solid rgba(255, 255, 255, 0.16);
    font-size: 0.74rem;
    font-weight: 500;
    white-space: nowrap;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.12s ease;
    z-index: 300;
  }

  .nav-item[data-tooltip]:hover::after {
    opacity: 1;
  }

  .sidebar-bottom {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    width: 100%;
    padding: 0 10px 4px;
    flex-shrink: 0;
  }

  .sidebar.expanded .sidebar-bottom {
    align-items: flex-start;
  }
</style>
