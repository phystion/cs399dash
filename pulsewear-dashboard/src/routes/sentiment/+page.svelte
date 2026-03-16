<script lang="ts">
  import PageHeader from '$lib/components/PageHeader.svelte';

  let inputText = $state('');
  let loading   = $state(false);
  let result    = $state<{ label: string; score: number } | null>(null);
  let error     = $state<string | null>(null);

  interface HistoryItem { text: string; label: string; score: number; ts: string; }
  let history = $state<HistoryItem[]>([]);

  const examples = [
    { text: 'Battery is dead by 6pm. Barely usable.', label: 'Negative' },
    { text: 'Love the run tracking — comparing splits with friends is amazing!', label: 'Positive' },
    { text: 'The setup took 3 hours and two support calls.', label: 'Negative' },
    { text: 'Smart notifications are perfectly timed — not too many, not too few.', label: 'Positive' },
    { text: 'My health data was still on the device after I sold it. Unacceptable.', label: 'Negative' },
    { text: 'The ECG feature in the latest update is exceptional.', label: 'Positive' },
  ];

  async function analyze() {
    if (!inputText.trim()) return;
    loading = true; result = null; error = null;

    try {
      const res = await fetch('http://localhost:8000/sentiment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: inputText.trim() }),
        signal: AbortSignal.timeout(5000),
      });
      if (!res.ok) throw new Error(`Server ${res.status}`);
      const data = await res.json();
      result = { label: data.label, score: data.score };
    } catch {
      // Client-side heuristic fallback when backend is offline
      const t = inputText.toLowerCase();
      const neg = ['dead','bad','terrible','broken','crash','slow','fail','worst','annoying','hate','disconnect','issue','problem','bug','useless','overpriced','unacceptable','confusing','frustrat'].filter(w => t.includes(w)).length;
      const pos = ['love','great','amazing','perfect','excellent','good','awesome','impressive','fantastic','best','smooth','easy','helpful','happy','satisfied','thank','flawless','exceptional'].filter(w => t.includes(w)).length;
      const isPos = pos >= neg;
      result = { label: isPos ? 'POSITIVE' : 'NEGATIVE', score: Math.min(0.98, 0.52 + Math.abs(pos - neg) * 0.07) };
      error = 'Backend offline — heuristic fallback active. Start FastAPI for model inference.';
    }

    history = [{
      text: inputText.trim().slice(0, 90) + (inputText.length > 90 ? '…' : ''),
      label: result!.label, score: result!.score,
      ts: new Date().toLocaleTimeString(),
    }, ...history.slice(0, 9)];

    loading = false;
  }

  function useExample(text: string) { inputText = text; result = null; error = null; }
</script>

<PageHeader
  eyebrow="NLP · DistilBERT"
  title="Sentiment Analyzer"
  subtitle="Real-time sentiment classification on wearable device feedback — powered by DistilBERT fine-tuned on SST-2."
  meta="85% accuracy on golden test set · Ethan Brooks, Sr. PM"
>
  <span class="badge badge-blue">SST-2 · 85% accuracy</span>
</PageHeader>

<main class="page-container">
  <div class="main-grid">
    <div class="left-col">

      <!-- Input -->
      <div class="glass input-card fade-in-up">
        <p class="card-label">Feedback Text</p>
        <textarea
          rows="5"
          placeholder="Paste or type user feedback here…"
          bind:value={inputText}
          onkeydown={(e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) analyze(); }}
        ></textarea>
        <div class="input-footer">
          <span class="char-hint">{inputText.length} chars · Ctrl+Enter to analyze</span>
          <button
            class="btn-primary"
            onclick={analyze}
            disabled={loading || !inputText.trim()}
          >
            {#if loading}
              <svg class="spin" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>Analyzing…
            {:else}
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>Analyze
            {/if}
          </button>
        </div>
      </div>

      <!-- Result -->
      {#if result}
        <div class="glass result-card fade-in-up" class:pos={result.label === 'POSITIVE'} class:neg={result.label === 'NEGATIVE'}>
          <div class="result-row">
            <span class="result-label">{result.label}</span>
            <span class="result-score">{(result.score * 100).toFixed(1)}% confidence</span>
          </div>
          <div class="conf-track">
            <div class="conf-fill" style="width:{result.score * 100}%"></div>
          </div>
          {#if error}<p class="offline-note">{error}</p>{/if}
        </div>
      {/if}

      <!-- Examples -->
      <div class="glass examples-card fade-in-up" style="animation-delay:60ms">
        <p class="card-label" style="margin-bottom:12px">Quick Examples</p>
        <div class="examples-list">
          {#each examples as ex}
            <button class="ex-btn" onclick={() => useExample(ex.text)}>
              <span class="ex-tag" class:ex-pos={ex.label==='Positive'} class:ex-neg={ex.label==='Negative'}>{ex.label}</span>
              <span class="ex-text">{ex.text}</span>
            </button>
          {/each}
        </div>
      </div>
    </div>

    <!-- History + info -->
    <aside class="right-col">
      <div class="glass history-card fade-in-up" style="animation-delay:80ms">
        <div class="history-hdr">
          <p class="section-title">Analysis History</p>
          {#if history.length > 0}
            <button class="btn-ghost" onclick={() => history = []}>Clear</button>
          {/if}
        </div>
        {#if history.length === 0}
          <div class="history-empty">
            <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="rgba(15,23,42,0.18)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>
            <p>No analyses yet</p>
          </div>
        {:else}
          <div class="history-list">
            {#each history as item, i (i)}
              <div class="h-item fade-in-up" style="animation-delay:{i*25}ms">
                <div class="h-top">
                  <span class="h-badge" class:h-pos={item.label==='POSITIVE'} class:h-neg={item.label==='NEGATIVE'}>{item.label}</span>
                  <span class="h-ts">{item.ts}</span>
                </div>
                <p class="h-text">{item.text}</p>
                <span class="h-score">{(item.score*100).toFixed(1)}% confidence</span>
              </div>
            {/each}
          </div>
        {/if}
      </div>

      <div class="glass info-card fade-in-up" style="animation-delay:120ms">
        <p class="section-title" style="margin-bottom:10px">Model Info</p>
        <p class="info-text">Sends text to FastAPI running <strong>DistilBERT</strong> via HuggingFace Transformers. Trained on SST-2, achieves <strong>85% accuracy</strong> on PulseWear golden test set of 20 labeled samples.</p>
        <div class="info-tags">
          <span class="badge badge-blue">DistilBERT-base-uncased</span>
          <span class="badge badge-indigo">SST-2</span>
        </div>
      </div>
    </aside>
  </div>
</main>

<style>
  main { padding-top: 0; padding-bottom: 72px; }

  .main-grid { display:grid; grid-template-columns:1fr 300px; gap:20px; align-items:start; }
  @media (max-width:960px) { .main-grid { grid-template-columns:1fr; } }
  .left-col  { display:flex; flex-direction:column; gap:16px; }
  .right-col { display:flex; flex-direction:column; gap:16px; }

  /* Input */
  .input-card { padding:22px; display:flex; flex-direction:column; gap:14px; }
  .card-label { font-size:.77rem; font-weight:600; color:var(--text-muted); text-transform:uppercase; letter-spacing:.05em; }
  .input-footer { display:flex; align-items:center; justify-content:space-between; }
  .char-hint { font-size:.73rem; color:var(--text-subtle); }
  @keyframes spin { to { transform:rotate(360deg); } }
  .spin { animation:spin .8s linear infinite; }

  /* Result */
  .result-card { padding:20px 22px; }
  .result-card.pos { border-color:rgba(5,150,105,.28); background:rgba(5,150,105,.05); }
  .result-card.neg { border-color:rgba(220,38,38,.28);  background:rgba(220,38,38,.05);  }
  .result-row { display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; }
  .result-label { font-size:1.4rem; font-weight:800; letter-spacing:-.02em; }
  .pos .result-label { color:#059669; }
  .neg .result-label { color:#DC2626; }
  .result-score { font-size:.82rem; color:var(--text-muted); }
  .conf-track { height:6px; background:rgba(15,23,42,.08); border-radius:6px; overflow:hidden; }
  .conf-fill { height:100%; border-radius:6px; transition:width .6s var(--ease); }
  .pos .conf-fill { background:#059669; }
  .neg .conf-fill { background:#DC2626; }
  .offline-note { font-size:.73rem; color:var(--text-muted); margin-top:10px; font-style:italic; }

  /* Examples */
  .examples-card { padding:20px 22px; }
  .examples-list { display:flex; flex-direction:column; gap:7px; }
  .ex-btn { display:flex; align-items:flex-start; gap:10px; padding:10px 12px; background:rgba(255,255,255,.50); border:1px solid rgba(15,23,42,.07); border-radius:var(--radius-sm); cursor:pointer; text-align:left; transition:background var(--transition); }
  .ex-btn:hover { background:rgba(255,255,255,.82); }
  .ex-tag { font-size:.64rem; font-weight:700; padding:2px 7px; border-radius:6px; flex-shrink:0; margin-top:1px; }
  .ex-pos { background:rgba(5,150,105,.10); color:#059669; }
  .ex-neg { background:rgba(220,38,38,.10); color:#DC2626; }
  .ex-text { font-size:.82rem; color:var(--text); line-height:1.4; }

  /* History */
  .history-card { padding:20px; }
  .history-hdr { display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; }
  .history-empty { display:flex; flex-direction:column; align-items:center; gap:10px; padding:30px 0; }
  .history-empty p { font-size:.82rem; color:var(--text-subtle); }
  .history-list { display:flex; flex-direction:column; gap:2px; }
  .h-item { padding:9px 6px; border-bottom:1px solid rgba(15,23,42,.05); display:flex; flex-direction:column; gap:3px; }
  .h-item:last-child { border-bottom:none; }
  .h-top { display:flex; align-items:center; justify-content:space-between; }
  .h-badge { font-size:.66rem; font-weight:700; padding:2px 7px; border-radius:6px; }
  .h-pos { background:rgba(5,150,105,.10); color:#059669; }
  .h-neg { background:rgba(220,38,38,.10); color:#DC2626; }
  .h-ts { font-size:.68rem; color:var(--text-subtle); }
  .h-text { font-size:.79rem; color:var(--text); line-height:1.35; }
  .h-score { font-size:.69rem; color:var(--text-muted); }

  /* Info */
  .info-card { padding:18px 20px; }
  .info-text { font-size:.81rem; color:var(--text-muted); line-height:1.55; margin-bottom:12px; }
  .info-tags { display:flex; gap:7px; flex-wrap:wrap; }
</style>
