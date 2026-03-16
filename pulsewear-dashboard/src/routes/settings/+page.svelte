<script lang="ts">
  import { browser } from '$app/environment';
  import { onMount } from 'svelte';
  import PageHeader from '$lib/components/PageHeader.svelte';
  import { accountProfile } from '$lib/data';

  type LandingPage = '/' | '/recommendations' | '/analysis' | '/roadmap';
  type DigestFrequency = 'daily' | 'weekly' | 'monthly';
  type RetentionWindow = '30d' | '90d' | '180d' | '365d';

  interface WorkspaceSettings {
    workspaceName: string;
    landingPage: LandingPage;
    digestFrequency: DigestFrequency;
    autoTagging: boolean;
    anomalyAlerts: boolean;
    roadmapDigest: boolean;
    includeBetaFeedback: boolean;
    retentionWindow: RetentionWindow;
    slackChannel: string;
    apiBaseUrl: string;
  }

  const STORAGE_KEY = 'pulsewear-settings';

  function createDefaults(): WorkspaceSettings {
    return {
      workspaceName: 'PulseWear Labs',
      landingPage: '/recommendations',
      digestFrequency: 'weekly',
      autoTagging: true,
      anomalyAlerts: true,
      roadmapDigest: true,
      includeBetaFeedback: true,
      retentionWindow: '90d',
      slackChannel: '#feedback-intel',
      apiBaseUrl: 'http://127.0.0.1:8000'
    };
  }

  let settings = $state<WorkspaceSettings>(createDefaults());
  let lastSaved = $state<string | null>(null);
  let saveNote = $state('Settings are stored in this browser.');

  onMount(() => {
    if (!browser) return;
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;

    try {
      settings = { ...createDefaults(), ...JSON.parse(raw) };
      saveNote = 'Loaded saved workspace settings.';
    } catch {
      saveNote = 'Saved settings were invalid. Using defaults.';
    }
  });

  function saveSettings() {
    if (!browser) return;
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...settings }));
    lastSaved = new Date().toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' });
    saveNote = 'Workspace settings saved.';
  }

  function resetSettings() {
    settings = createDefaults();
    saveNote = 'Defaults restored. Save to keep them.';
  }
</script>

<PageHeader title="Settings">
  <button class="btn-ghost" onclick={resetSettings}>Reset</button>
  <button class="btn-primary" onclick={saveSettings}>Save</button>
</PageHeader>

<main class="page-container settings-page">
  <section class="glass profile-card fade-in-up">
    <div class="profile-hero">
      <div class="profile-avatar">{accountProfile.initials}</div>
      <div class="profile-copy">
        <p class="profile-name">{accountProfile.name}</p>
        <p class="profile-role">{accountProfile.role}</p>
      </div>
    </div>

    <div class="profile-grid">
      <div class="profile-field">
        <span class="field-label">Email</span>
        <span class="field-value">{accountProfile.email}</span>
      </div>
      <div class="profile-field">
        <span class="field-label">Team</span>
        <span class="field-value">{accountProfile.team}</span>
      </div>
      <div class="profile-field">
        <span class="field-label">Location</span>
        <span class="field-value">{accountProfile.location}</span>
      </div>
      <div class="profile-field">
        <span class="field-label">Access</span>
        <span class="field-value">{accountProfile.plan}</span>
      </div>
    </div>
  </section>

  <section class="settings-grid">
    <article class="glass panel">
      <div class="panel-head">
        <div>
          <h2 class="section-title">Workspace Preferences</h2>
          <p class="panel-copy">Default navigation and reporting behavior for this dashboard.</p>
        </div>
      </div>

      <div class="field-grid">
        <label class="field field-full">
          <span class="field-label">Workspace name</span>
          <input type="text" bind:value={settings.workspaceName} />
        </label>

        <label class="field">
          <span class="field-label">Default landing page</span>
          <select bind:value={settings.landingPage}>
            <option value="/recommendations">Recommendations</option>
            <option value="/">Dashboard</option>
            <option value="/analysis">Analysis</option>
            <option value="/roadmap">Roadmap</option>
          </select>
        </label>

        <label class="field">
          <span class="field-label">Digest frequency</span>
          <select bind:value={settings.digestFrequency}>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
        </label>

        <label class="field field-full">
          <span class="field-label">Slack channel</span>
          <input type="text" bind:value={settings.slackChannel} />
        </label>
      </div>
    </article>

    <article class="glass panel">
      <div class="panel-head">
        <div>
          <h2 class="section-title">Signal Controls</h2>
          <p class="panel-copy">Decide which automation and alerts drive the dashboard.</p>
        </div>
      </div>

      <div class="toggle-list">
        <label class="toggle-row">
          <div>
            <span class="toggle-title">Auto-tag recurring issues</span>
            <span class="toggle-copy">Apply lightweight labels when the same customer issue keeps reappearing.</span>
          </div>
          <input type="checkbox" bind:checked={settings.autoTagging} />
        </label>

        <label class="toggle-row">
          <div>
            <span class="toggle-title">Anomaly alerts</span>
            <span class="toggle-copy">Highlight sudden jumps in negative sentiment or comment volume.</span>
          </div>
          <input type="checkbox" bind:checked={settings.anomalyAlerts} />
        </label>

        <label class="toggle-row">
          <div>
            <span class="toggle-title">Roadmap digest</span>
            <span class="toggle-copy">Promote changes tied to active roadmap items into summaries.</span>
          </div>
          <input type="checkbox" bind:checked={settings.roadmapDigest} />
        </label>

        <label class="toggle-row">
          <div>
            <span class="toggle-title">Include beta feedback</span>
            <span class="toggle-copy">Blend beta comments into theme summaries and assistant answers.</span>
          </div>
          <input type="checkbox" bind:checked={settings.includeBetaFeedback} />
        </label>
      </div>
    </article>

    <article class="glass panel">
      <div class="panel-head">
        <div>
          <h2 class="section-title">Data Window</h2>
          <p class="panel-copy">Control retention and backend defaults for this workspace.</p>
        </div>
      </div>

      <div class="field-grid">
        <label class="field">
          <span class="field-label">Retention window</span>
          <select bind:value={settings.retentionWindow}>
            <option value="30d">30 days</option>
            <option value="90d">90 days</option>
            <option value="180d">180 days</option>
            <option value="365d">365 days</option>
          </select>
        </label>

        <label class="field">
          <span class="field-label">API base URL</span>
          <input type="text" bind:value={settings.apiBaseUrl} />
        </label>
      </div>
    </article>
  </section>

  <section class="status-row">
    <p class="save-note">{saveNote}</p>
    {#if lastSaved}
      <p class="save-note">Last saved {lastSaved}</p>
    {/if}
  </section>
</main>

<style>
  .settings-page {
    padding-bottom: 40px;
  }

  .settings-grid {
    display: grid;
    gap: 18px;
  }

  .settings-grid {
    grid-template-columns: 1fr 1fr;
    margin-top: 18px;
  }

  .profile-card,
  .panel {
    padding: 22px;
  }

  .profile-card {
    background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
  }

  .profile-hero {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-bottom: 20px;
  }

  .profile-avatar {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 64px;
    height: 64px;
    border-radius: 20px;
    background: linear-gradient(135deg, #4A90E2 0%, #1B3A6B 100%);
    color: #FFFFFF;
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    flex-shrink: 0;
  }

  .profile-copy {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .profile-name {
    font-size: 1.18rem;
    font-weight: 700;
    color: var(--navy);
    letter-spacing: -0.02em;
  }

  .panel-copy,
  .toggle-copy,
  .save-note {
    color: var(--text-muted);
    line-height: 1.55;
  }

  .profile-role {
    font-size: 0.9rem;
    color: var(--text-muted);
  }

  .profile-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
  }

  .profile-field {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding: 14px 16px;
    border-radius: 10px;
    background: rgba(74, 144, 226, 0.06);
  }

  .panel {
    display: flex;
    flex-direction: column;
    gap: 18px;
  }

  .field-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .field-full {
    grid-column: 1 / -1;
  }

  .field-label {
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--text);
  }

  .field-value {
    font-size: 0.88rem;
    color: var(--text);
    line-height: 1.4;
    word-break: break-word;
  }

  select {
    width: 100%;
    padding: 12px 16px;
    border: 1px solid rgba(15, 23, 42, 0.13);
    border-radius: var(--radius);
    background: #ffffff;
    color: var(--text);
    font: inherit;
  }

  .toggle-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .toggle-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 14px 16px;
    border: 1px solid rgba(15, 23, 42, 0.08);
    border-radius: var(--radius);
    background: #fbfcfe;
  }

  .toggle-title {
    display: block;
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text);
    margin-bottom: 4px;
  }

  input[type="checkbox"] {
    width: 18px;
    height: 18px;
    accent-color: var(--navy);
    flex-shrink: 0;
  }

  .status-row {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    padding: 16px 2px 0;
  }

  @media (max-width: 1100px) {
    .settings-grid {
      grid-template-columns: 1fr;
    }
  }

  @media (max-width: 760px) {
    .field-grid,
    .profile-grid {
      grid-template-columns: 1fr;
    }

    .toggle-row,
    .status-row {
      flex-direction: column;
      align-items: flex-start;
    }
  }
</style>
