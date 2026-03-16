<script lang="ts">
  import { themes } from '$lib/data';
  import { chatPageStarters, resolveAssistantReply, type AssistantMessage } from '$lib/chat/engine';
  import PageHeader from '$lib/components/PageHeader.svelte';

  interface Message extends AssistantMessage {
    ts: string;
  }

  let messages = $state<Message[]>([]);
  let input    = $state('');
  let loading  = $state(false);
  let error    = $state<string | null>(null);
  let chatBottom: HTMLDivElement | undefined = $state();

  const starters = chatPageStarters;
  const totalRows = themes.reduce((sum, theme) => sum + theme.volume, 0);

  function scrollBottom() {
    setTimeout(() => chatBottom?.scrollIntoView({ behavior: 'smooth' }), 50);
  }

  async function send(textOverride?: string) {
    const text = (textOverride ?? input).trim();
    if (!text || loading) return;
    input   = '';
    error   = null;
    loading = true;

    const userMessage: Message = { role: 'user', content: text, ts: now() };
    const nextMessages: Message[] = [...messages, userMessage];
    messages = nextMessages;
    scrollBottom();

    try {
      const data = await resolveAssistantReply(
        nextMessages.map(({ role, content }): AssistantMessage => ({ role, content }))
      );
      const reply: string = data.reply ?? '(no reply)';
      const assistantMessage: Message = { role: 'assistant', content: reply, ts: now() };

      messages = [...nextMessages, assistantMessage];
      scrollBottom();
    } catch (e: unknown) {
      error = e instanceof Error ? e.message : String(e);
    }

    loading = false;
  }

  function useStarter(s: string) { void send(s); }
  function clearChat() { messages = []; error = null; }
  function now() { return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }); }
</script>

<PageHeader
  eyebrow="Feedback Assistant · Rule-based engine"
  title="Feedback Assistant"
  subtitle="Ask about themes, trends, priorities, and roadmap status."
  meta={`${totalRows.toLocaleString()} rows · ${themes.length} themes · No API required`}
>
  <span class="badge badge-blue">rule-based</span>
  {#if messages.length > 0}
    <button class="btn-ghost" onclick={clearChat}>Clear chat</button>
  {/if}
</PageHeader>

<main class="page-container">
  <div class="chat-layout">

    <!-- Chat window -->
    <div class="chat-col">

      <!-- Messages -->
      <div class="glass chat-box">
        {#if messages.length === 0}
          <div class="empty-state">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="rgba(74,144,226,0.4)" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            <p class="empty-title">Ask about your feedback data</p>
          </div>
        {:else}
          <div class="messages-list">
            {#each messages as msg, i (i)}
              <div class="msg" class:user={msg.role === 'user'} class:assistant={msg.role === 'assistant'}>
                <div class="msg-meta">
                  <span class="msg-role">{msg.role === 'user' ? 'Ethan' : 'Assistant'}</span>
                  <span class="msg-ts">{msg.ts}</span>
                </div>
                <div class="msg-bubble">
                  <p class="msg-text">{msg.content}</p>
                </div>
              </div>
            {/each}
            {#if loading}
              <div class="msg assistant">
                <div class="msg-meta">
                  <span class="msg-role">Assistant</span>
                </div>
                <div class="msg-bubble">
                  <span class="typing-dots">
                    <span></span><span></span><span></span>
                  </span>
                </div>
              </div>
            {/if}
            <div bind:this={chatBottom}></div>
          </div>
        {/if}
      </div>

      {#if error}
        <div class="error-bar">{error}</div>
      {/if}

      <!-- Input -->
      <div class="glass input-wrap">
        <textarea
          rows="3"
          placeholder="Ask about themes, trends, priorities, or request a summary…"
          bind:value={input}
          disabled={loading}
          onkeydown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); } }}
        ></textarea>
        <div class="input-footer">
          <span class="hint">Enter to send · Shift+Enter for newline</span>
          <button class="btn-primary" onclick={() => void send()} disabled={loading || !input.trim()}>
            {#if loading}
              <svg class="spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
              Thinking…
            {:else}
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
              Send
            {/if}
          </button>
        </div>
      </div>
    </div>

    <!-- Sidebar: starters -->
    <aside class="side-col">

      <div class="glass starters-card fade-in-up">
        <p class="card-label">Starter Prompts</p>
        <div class="starters-list">
          {#each starters as s}
            <button class="starter-btn" onclick={() => useStarter(s)} disabled={loading}>
              {s}
            </button>
          {/each}
        </div>
      </div>

    </aside>
  </div>
</main>

<style>
  main { padding-top: 0; padding-bottom: 72px; }

  .chat-layout {
    display: grid;
    grid-template-columns: 1fr 280px;
    gap: 20px;
    align-items: start;
  }
  @media (max-width: 900px) { .chat-layout { grid-template-columns: 1fr; } }

  .chat-col  { display: flex; flex-direction: column; gap: 12px; }
  .side-col  { display: flex; flex-direction: column; gap: 14px; }

  /* Chat box */
  .chat-box {
    min-height: 420px;
    max-height: 560px;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
  }

  .empty-state {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 10px;
    padding: 40px 20px;
    text-align: center;
  }
  .empty-title { font-size: .92rem; font-weight: 600; color: var(--text); }

  /* Messages */
  .messages-list { display: flex; flex-direction: column; gap: 14px; }

  .msg { display: flex; flex-direction: column; gap: 4px; }
  .msg.user      { align-items: flex-end; }
  .msg.assistant { align-items: flex-start; }

  .msg-meta  { display: flex; align-items: center; gap: 6px; }
  .msg-role  { font-size: .66rem; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; color: var(--text-muted); }
  .msg-ts    { font-size: .66rem; color: var(--text-subtle); }

  .msg-bubble {
    max-width: 82%;
    padding: 10px 14px;
    border-radius: var(--radius-lg);
    line-height: 1.55;
  }

  .user .msg-bubble {
    background: linear-gradient(135deg, var(--blue) 0%, #1B3A6B 100%);
    color: #fff;
    border-bottom-right-radius: 3px;
  }

  .assistant .msg-bubble {
    background: rgba(255,255,255,0.72);
    border: 1px solid rgba(15,23,42,.08);
    color: var(--text);
    border-bottom-left-radius: 3px;
  }

  .msg-text { font-size: .85rem; white-space: pre-wrap; word-break: break-word; margin: 0; }

  /* Typing dots */
  .typing-dots { display: flex; gap: 4px; align-items: center; padding: 2px 0; }
  .typing-dots span {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--text-muted);
    animation: dot-bounce 1.2s ease-in-out infinite;
  }
  .typing-dots span:nth-child(2) { animation-delay: .2s; }
  .typing-dots span:nth-child(3) { animation-delay: .4s; }
  @keyframes dot-bounce {
    0%, 60%, 100% { transform: translateY(0); opacity: .5; }
    30%            { transform: translateY(-5px); opacity: 1; }
  }

  /* Error */
  .error-bar {
    padding: 10px 14px;
    background: rgba(220,38,38,.08);
    border: 1px solid rgba(220,38,38,.20);
    border-radius: var(--radius-sm);
    font-size: .78rem;
    color: #DC2626;
    line-height: 1.45;
  }

  /* Input */
  .input-wrap { padding: 16px 18px; display: flex; flex-direction: column; gap: 10px; }
  .input-footer { display: flex; align-items: center; justify-content: space-between; }
  .hint { font-size: .71rem; color: var(--text-subtle); }

  @keyframes spin { to { transform: rotate(360deg); } }
  .spin { animation: spin .8s linear infinite; }

  /* Sidebar cards */
  .card-label {
    font-size: .73rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .05em; color: var(--text-muted); margin-bottom: 12px;
  }

  .starters-card { padding: 18px; }
  .starters-list { display: flex; flex-direction: column; gap: 6px; }
  .starter-btn {
    text-align: left; padding: 9px 11px;
    background: rgba(255,255,255,.50);
    border: 1px solid rgba(15,23,42,.07);
    border-radius: var(--radius-sm);
    font-size: .78rem; color: var(--text);
    cursor: pointer; line-height: 1.4;
    transition: background var(--transition);
  }
  .starter-btn:hover:not(:disabled) { background: rgba(255,255,255,.85); }
  .starter-btn:disabled { opacity: .5; cursor: not-allowed; }
</style>
