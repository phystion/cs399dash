<script lang="ts">
  import { popupStarters, resolveAssistantReply, type AssistantMessage } from '$lib/chat/engine';

  interface Message extends AssistantMessage {
    ts: string;
  }

  interface Props {
    open: boolean;
    onclose: () => void;
  }

  let { open, onclose }: Props = $props();

  let messages = $state<Message[]>([]);
  let input    = $state('');
  let loading  = $state(false);
  let error    = $state<string | null>(null);
  let chatBottom: HTMLDivElement | undefined = $state();

  const starters = popupStarters;

  function now() {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

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

  function useStarter(s: string) {
    void send(s);
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }
</script>

{#if open}
  <div class="chat-panel" role="dialog" aria-label="Feedback assistant">
    <!-- Header -->
    <div class="panel-header">
      <div class="header-left">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
        </svg>
        <span class="panel-title">Assistant</span>
      </div>
      <button class="close-btn" onclick={onclose} aria-label="Close assistant">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
             stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="18" y1="6" x2="6" y2="18"/>
          <line x1="6" y1="6" x2="18" y2="18"/>
        </svg>
      </button>
    </div>

    <!-- Messages area -->
    <div class="messages-area">
      {#if messages.length === 0}
        <div class="empty-state">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none"
               stroke="rgba(74,144,226,0.4)" stroke-width="1.4"
               stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          <p class="empty-text">Ask about feedback</p>
        </div>
      {:else}
        <div class="messages-list">
          {#each messages as msg, i (i)}
            <div class="msg" class:user={msg.role === 'user'} class:assistant={msg.role === 'assistant'}>
              <div class="msg-meta">
                <span class="msg-role">{msg.role === 'user' ? 'You' : 'Assistant'}</span>
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

    <!-- Error bar -->
    {#if error}
      <div class="error-bar">{error}</div>
    {/if}

    <!-- Input area -->
    <div class="input-area">
      <!-- Starter chips -->
      <div class="chips-row">
        {#each starters as s (s)}
          <button class="chip" onclick={() => useStarter(s)} disabled={loading}>{s}</button>
        {/each}
      </div>

      <div class="input-row">
        <textarea
          rows="2"
          placeholder="Ask about themes or priorities…"
          bind:value={input}
          disabled={loading}
          onkeydown={handleKeydown}
        ></textarea>
        <button class="send-btn" onclick={() => void send()} disabled={loading || !input.trim()} aria-label="Send">
          {#if loading}
            <svg class="spin" width="13" height="13" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2.5">
              <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
            </svg>
          {:else}
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                 stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"/>
              <polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
          {/if}
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  @keyframes panel-in {
    from { opacity: 0; transform: translateY(-8px) scale(0.98); }
    to   { opacity: 1; transform: none; }
  }

  .chat-panel {
    position: fixed;
    top: calc(var(--topbar-height) + 8px);
    right: 16px;
    width: 380px;
    height: 520px;
    z-index: 200;
    background: rgba(255, 255, 255, 0.92);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(15, 23, 42, 0.10);
    border-radius: 10px;
    box-shadow: 0 8px 40px rgba(15, 23, 42, 0.14);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    animation: panel-in 0.18s ease both;
  }

  /* ── Header ─────────────────────────────────────────────── */
  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 11px 14px;
    border-bottom: 1px solid rgba(15, 23, 42, 0.08);
    flex-shrink: 0;
    background: rgba(255, 255, 255, 0.60);
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 7px;
    color: var(--navy);
  }

  .panel-title {
    font-size: 0.80rem;
    font-weight: 700;
    color: var(--navy);
    letter-spacing: 0.01em;
  }

  .close-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 26px;
    height: 26px;
    border: none;
    background: transparent;
    color: var(--text-muted);
    cursor: pointer;
    border-radius: 5px;
    transition: background 0.13s ease, color 0.13s ease;
    flex-shrink: 0;
  }

  .close-btn:hover {
    background: rgba(15, 23, 42, 0.07);
    color: var(--navy);
  }

  /* ── Messages area ───────────────────────────────────────── */
  .messages-area {
    flex: 1;
    overflow-y: auto;
    padding: 14px;
    display: flex;
    flex-direction: column;
  }

  .empty-state {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 9px;
    text-align: center;
  }

  .empty-text {
    font-size: 0.80rem;
    color: var(--text-muted);
    font-weight: 500;
    margin: 0;
  }

  /* ── Message bubbles ─────────────────────────────────────── */
  .messages-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .msg {
    display: flex;
    flex-direction: column;
    gap: 3px;
  }

  .msg.user      { align-items: flex-end; }
  .msg.assistant { align-items: flex-start; }

  .msg-meta {
    display: flex;
    align-items: center;
    gap: 5px;
  }

  .msg-role {
    font-size: 0.63rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
  }

  .msg-ts {
    font-size: 0.63rem;
    color: var(--text-subtle, rgba(15,23,42,0.35));
  }

  .msg-bubble {
    max-width: 86%;
    padding: 8px 11px;
    border-radius: 6px;
    line-height: 1.5;
  }

  .user .msg-bubble {
    background: linear-gradient(135deg, var(--blue) 0%, #1B3A6B 100%);
    color: #fff;
    border-bottom-right-radius: 2px;
  }

  .assistant .msg-bubble {
    background: rgba(255, 255, 255, 0.72);
    border: 1px solid rgba(15, 23, 42, 0.08);
    color: var(--text);
    border-bottom-left-radius: 2px;
  }

  .msg-text {
    font-size: 0.82rem;
    white-space: pre-wrap;
    word-break: break-word;
    margin: 0;
  }

  /* ── Typing dots ─────────────────────────────────────────── */
  .typing-dots {
    display: flex;
    gap: 4px;
    align-items: center;
    padding: 2px 0;
  }

  .typing-dots span {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background: var(--text-muted);
    animation: dot-bounce 1.2s ease-in-out infinite;
  }

  .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
  .typing-dots span:nth-child(3) { animation-delay: 0.4s; }

  @keyframes dot-bounce {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
    30%            { transform: translateY(-4px); opacity: 1; }
  }

  /* ── Error bar ───────────────────────────────────────────── */
  .error-bar {
    margin: 0 14px 8px;
    padding: 8px 11px;
    background: rgba(220, 38, 38, 0.08);
    border: 1px solid rgba(220, 38, 38, 0.20);
    border-radius: 4px;
    font-size: 0.74rem;
    color: #DC2626;
    line-height: 1.45;
    flex-shrink: 0;
  }

  /* ── Input area ──────────────────────────────────────────── */
  .input-area {
    flex-shrink: 0;
    border-top: 1px solid rgba(15, 23, 42, 0.08);
    padding: 10px 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    background: rgba(255, 255, 255, 0.50);
  }

  /* Starter chips */
  .chips-row {
    display: flex;
    gap: 5px;
    flex-wrap: wrap;
  }

  .chip {
    padding: 4px 9px;
    border: 1px solid rgba(74, 144, 226, 0.30);
    border-radius: 20px;
    background: rgba(74, 144, 226, 0.07);
    color: var(--navy);
    font-size: 0.72rem;
    font-family: inherit;
    cursor: pointer;
    transition: background 0.13s ease, border-color 0.13s ease;
    white-space: nowrap;
    line-height: 1.3;
  }

  .chip:hover:not(:disabled) {
    background: rgba(74, 144, 226, 0.15);
    border-color: rgba(74, 144, 226, 0.50);
  }

  .chip:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  /* Text input + send */
  .input-row {
    display: flex;
    gap: 7px;
    align-items: flex-end;
  }

  textarea {
    flex: 1;
    resize: none;
    border: 1px solid rgba(15, 23, 42, 0.12);
    border-radius: 5px;
    padding: 7px 10px;
    font-family: inherit;
    font-size: 0.80rem;
    color: var(--text);
    background: rgba(255, 255, 255, 0.80);
    line-height: 1.45;
    outline: none;
    transition: border-color 0.13s ease;
  }

  textarea:focus {
    border-color: rgba(74, 144, 226, 0.50);
  }

  textarea:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .send-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    flex-shrink: 0;
    border: none;
    border-radius: 5px;
    background: linear-gradient(135deg, var(--blue) 0%, #1B3A6B 100%);
    color: #fff;
    cursor: pointer;
    transition: opacity 0.13s ease;
  }

  .send-btn:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }

  .send-btn:not(:disabled):hover {
    opacity: 0.88;
  }

  @keyframes spin { to { transform: rotate(360deg); } }
  .spin { animation: spin 0.8s linear infinite; }
</style>
