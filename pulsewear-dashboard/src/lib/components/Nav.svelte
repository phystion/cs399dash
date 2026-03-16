<script lang="ts">
  type Page = 'dashboard' | 'sentiment' | 'trends' | 'roadmap' | 'feedback';

  interface Props { activePage: Page; }
  let { activePage }: Props = $props();

  const links: { label: string; href: string; page: Page }[] = [
    { label: 'Dashboard', href: '/',          page: 'dashboard' },
    { label: 'Sentiment', href: '/sentiment', page: 'sentiment' },
    { label: 'Trends',    href: '/trends',    page: 'trends'    },
    { label: 'Roadmap',   href: '/roadmap',   page: 'roadmap'   },
    { label: 'Feedback',  href: '/feedback',  page: 'feedback'  },
  ];
</script>

<nav class="nav">
  <div class="nav-inner">
    <a href="/" class="wordmark" aria-label="PulseWear home">
      <svg width="26" height="26" viewBox="0 0 26 26" fill="none" aria-hidden="true">
        <circle cx="13" cy="13" r="12" stroke="url(#ng)" stroke-width="1.8"/>
        <polyline points="3,13 7,13 9,7 11,19 14,9 16,17 18,13 23,13"
          stroke="url(#ng)" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
        <defs>
          <linearGradient id="ng" x1="0" y1="0" x2="26" y2="26" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stop-color="#4A90E2"/>
            <stop offset="100%" stop-color="#1B3A6B"/>
          </linearGradient>
        </defs>
      </svg>
      <span class="brand-name">PulseWear</span>
      <span class="brand-sub">Labs</span>
    </a>

    <ul class="nav-links" role="list">
      {#each links as link (link.page)}
        <li>
          <a
            href={link.href}
            class="nav-link"
            class:active={activePage === link.page}
            aria-current={activePage === link.page ? 'page' : undefined}
          >
            {link.label}
          </a>
        </li>
      {/each}
    </ul>
  </div>
</nav>

<style>
  .nav {
    position: fixed;
    top: 0; left: 0; right: 0;
    height: var(--nav-height);
    z-index: 100;
    background: #FFFFFF;
    border-bottom: 1px solid rgba(15,23,42,0.09);
    box-shadow: none;
  }

  .nav-inner {
    max-width: 1280px;
    margin: 0 auto;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 28px;
  }

  .wordmark {
    display: flex;
    align-items: center;
    gap: 9px;
    text-decoration: none;
    flex-shrink: 0;
  }

  .brand-name {
    font-size: 1.05rem;
    font-weight: 800;
    color: var(--text);
    letter-spacing: -0.02em;
  }

  .brand-sub {
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--text-muted);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-top: 1px;
  }

  .nav-links {
    display: flex;
    align-items: center;
    gap: 2px;
    list-style: none;
  }

  .nav-link {
    position: relative;
    padding: 7px 14px;
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-muted);
    text-decoration: none;
    border-radius: var(--radius-sm);
    transition: color var(--transition), background var(--transition);
  }

  .nav-link:hover {
    color: var(--text);
    background: rgba(255,255,255,0.70);
  }

  .nav-link.active {
    color: var(--navy);
    font-weight: 700;
    background: rgba(74,144,226,0.12);
  }

  .nav-link.active::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 14px;
    right: 14px;
    height: 2px;
    border-radius: 2px 2px 0 0;
    background: linear-gradient(90deg, #4A90E2, #1B3A6B);
  }
</style>
