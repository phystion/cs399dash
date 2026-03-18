"""
PulseWear Labs — FastAPI Backend
================================
Serves endpoints for the SvelteKit dashboard.

Endpoints:
  POST /sentiment          — DistilBERT sentiment analysis
  GET  /themes             — all clusters with stats (count derived from CSV)
  GET  /trends             — monthly pivot data (Mar 2024 – Feb 2025)
  GET  /feedback/{cluster} — raw feedback quotes for a cluster
  GET  /roadmap            — priority-scored roadmap initiatives
  POST /chat               — rule-based feedback intelligence chat
  GET  /chat/models        — engine info

Start:
  pip install -r requirements.txt
  uvicorn main:app --reload --port 8000
"""

import os
import math
import json
import re
import pandas as pd
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

# ── Optional: HuggingFace sentiment model ───────────────────────────────────
# Loads lazily on first /sentiment call to avoid slow startup
_sentiment_pipeline = None

def get_sentiment_pipeline():
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        from transformers import pipeline
        _sentiment_pipeline = pipeline("sentiment-analysis")
    return _sentiment_pipeline

# ── App setup ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="PulseWear Feedback Intelligence API",
    version="1.0.0",
    description="Backend for PulseWear Labs feedback dashboard (CS399)",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load CSV ─────────────────────────────────────────────────────────────────
CSV_PATH = Path(__file__).parent.parent / "data generation excel" / "Data" / "pulsewear_clustered_data.csv"

def load_data() -> pd.DataFrame:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV not found at: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df

try:
    DATA = load_data()
    print(f"[PulseWear] Loaded {len(DATA):,} rows from {CSV_PATH.name}")
    # Build cluster name lookup from cluster_description column
    if "cluster_description" in DATA.columns:
        _desc_map = (
            DATA.groupby("cluster_label")["cluster_description"]
            .first().to_dict()
        )
        CLUSTER_NAMES: dict[int, str] = {
            int(cid): str(desc).split(".")[0].strip() if pd.notna(desc) else f"Cluster {int(cid)}"
            for cid, desc in _desc_map.items()
        }
    else:
        CLUSTER_NAMES = {}
except Exception as e:
    DATA = None
    CLUSTER_NAMES = {}
    print(f"[PulseWear] WARNING: Could not load CSV — {e}")

# ── Roadmap mapping (read from roadmap_config.json if present) ───────────────
_ROADMAP_CFG_PATH = Path(__file__).parent / "roadmap_config.json"
try:
    with open(_ROADMAP_CFG_PATH, encoding="utf-8") as _f:
        _raw = json.load(_f)
    ROADMAP: dict[int, dict] = {int(k): v for k, v in _raw.items() if v is not None}
    print(f"[PulseWear] Loaded roadmap_config.json — {len(ROADMAP)} entries")
except FileNotFoundError:
    ROADMAP = {}
    print("[PulseWear] No roadmap_config.json — roadmap fields will be null")

# ── Rule-based chat engine ────────────────────────────────────────────────────

# Hardcoded cluster data (matches CSV-derived values)
CLUSTER_DATA = {
    0: {"name": "Fitness Tracking & Customization",       "vol": 7843, "pos": 36, "neg": 64, "priority": 78, "roadmap_id": "PWL-ROAD-01", "status": "Active",       "topics": "fitness tracking accuracy, social connectivity, avatar customization, device customization"},
    1: {"name": "Battery, Connectivity & Lag",            "vol": 4202, "pos": 10, "neg": 90, "priority": 94, "roadmap_id": "PWL-ROAD-02", "status": "Active",       "topics": "battery drain, Bluetooth instability, software lag, sync failures"},
    2: {"name": "Privacy & Multi-User Support",           "vol":  869, "pos": 19, "neg": 81, "priority": 63, "roadmap_id": "PWL-ROAD-03", "status": "Planned",      "topics": "multi-user support, account registration privacy, data sharing controls, product value"},
    3: {"name": "Support & Setup Experience",             "vol":  811, "pos": 24, "neg": 76, "priority": 59, "roadmap_id": "PWL-ROAD-04", "status": "Active",       "topics": "customer support responsiveness, onboarding flow, pairing issues, setup documentation"},
    4: {"name": "Notification Settings",                  "vol": 2135, "pos": 31, "neg": 69, "priority": 76, "roadmap_id": "PWL-ROAD-05", "status": "Under Review", "topics": "push notification timing, alert customization, do-not-disturb, smart reminders"},
    5: {"name": "Average Product Feedback",               "vol":  232, "pos":  0, "neg": 100,"priority": 64, "roadmap_id": None,          "status": None,           "topics": "uniformly average ratings, lukewarm general satisfaction, calls for incremental improvement"},
    6: {"name": "Water Resistance Reliability",           "vol":  496, "pos": 34, "neg": 66, "priority": 48, "roadmap_id": "PWL-ROAD-06", "status": "Backlog",      "topics": "swim tracking, waterproof rating accuracy, physical durability, strap comfort"},
    7: {"name": "Mixed & Neutral Sentiment",              "vol": 2925, "pos": 68, "neg": 32, "priority": 59, "roadmap_id": None,          "status": None,           "topics": "mediocre and lukewarm feedback, indifferent or underwhelming sentiments"},
    8: {"name": "Health Data Security",                   "vol":  105, "pos":  0, "neg": 100,"priority": 62, "roadmap_id": "PWL-ROAD-07", "status": "Active",       "topics": "health data encryption, HIPAA concerns, third-party data sharing, account security"},
    9: {"name": "Subscriptions & Update Regressions",     "vol":  382, "pos": 46, "neg": 54, "priority": 39, "roadmap_id": "PWL-ROAD-08", "status": "Planned",      "topics": "premium subscription value, firmware update regressions, new feature requests, OS compatibility"},
}

def _cluster_detail(cid: int) -> tuple[str, list[str]]:
    c = CLUSTER_DATA[cid]
    rm = f"{c['roadmap_id']} ({c['status']})" if c['roadmap_id'] else "no roadmap item"
    reply = (
        f"Cluster {cid} — {c['name']}: {c['vol']:,} entries, {c['pos']}% positive / {c['neg']}% negative, "
        f"priority score {c['priority']}/100. Roadmap: {rm}. "
        f"Key topics: {c['topics']}."
    )
    sources = [f"cluster:{cid}"]
    if c['roadmap_id']:
        sources.append(c['roadmap_id'])
    return reply, sources


def _match_intent(text: str, history: list[dict]) -> tuple[str, list[str], Optional[int]]:
    """
    Match user text to an intent and return (reply, sources, last_cluster_id).
    history is the list of prior messages as dicts with 'role' and 'content'.
    last_cluster is carried forward for follow-up resolution.
    """
    t = text.lower()

    # Resolve "that cluster" / "it" / "that one" using last mentioned cluster in history
    last_cluster: Optional[int] = None
    for msg in reversed(history):
        if msg["role"] == "assistant":
            for cid in CLUSTER_DATA:
                if f"cluster {cid}" in msg["content"].lower() or CLUSTER_DATA[cid]["name"].lower() in msg["content"].lower():
                    last_cluster = cid
                    break
            if last_cluster is not None:
                break

    follow_up_triggers = re.search(r"\b(that cluster|that one|tell me more|more about it|what about that|elaborate)\b", t)
    if follow_up_triggers and last_cluster is not None:
        reply, sources = _cluster_detail(last_cluster)
        return "Following up on the previous cluster — " + reply, sources, last_cluster

    # Intent 21: greeting
    if re.search(r"^\s*(hello|hi|hey|howdy|good (morning|afternoon|evening))[!.,]?\s*$", t):
        return (
            "Hello, Ethan. I'm your PulseWear feedback intelligence assistant. "
            "I have full context on all 10 feedback clusters, 20,000 entries, and roadmap status. "
            "What would you like to explore?",
            ["summary"],
            None,
        )

    # Intent 20: help / capabilities
    if re.search(r"\b(help|what can you do|capabilities|commands|what do you know)\b", t):
        return (
            "I can answer questions about the PulseWear feedback dataset. Try asking:\n"
            "- Top priorities / urgent issues\n"
            "- Battery, security, support, fitness, notifications, water resistance, premium, multi-user\n"
            "- Dataset summary / overview\n"
            "- Best / worst sentiment clusters\n"
            "- Roadmap status\n"
            "- Monthly trends\n"
            "- Channel breakdown\n"
            "- Actionable recommendations\n"
            "- Draft a Jira ticket\n"
            "- Compare clusters",
            ["summary"],
            None,
        )

    # Intent 1: top issues / priorities
    if re.search(r"\b(top (issue|issues|problem|problems|priority|priorities)|focus|urgent|most critical|highest priority|what to fix|what should we fix)\b", t):
        return (
            "Top 3 priorities by urgency score:\n"
            "1. Battery, Connectivity & Lag (score 94, 90% negative) — PWL-ROAD-02 Active\n"
            "2. Fitness Tracking & Customization (score 78, 64% negative) — PWL-ROAD-01 Active\n"
            "3. Notification Settings (score 76, 69% negative) — PWL-ROAD-05 Under Review\n"
            "Battery, Connectivity & Lag is the highest-priority item with 9 in 10 users dissatisfied.",
            ["cluster:1", "cluster:0", "cluster:4", "summary"],
            None,
        )

    # Intent 2: battery / connectivity
    if re.search(r"\b(battery|bluetooth|gps|sync|connectivity|connection|charging|drain)\b", t):
        reply, sources = _cluster_detail(1)
        return reply, sources, 1

    # Intent 8: security / health data
    if re.search(r"\b(security|encryption|hipaa|health data|data breach|account security|third.party sharing)\b", t):
        reply, sources = _cluster_detail(8)
        return reply, sources, 8

    # Intent 4: support / setup / onboarding
    if re.search(r"\b(support|setup|onboarding|pairing|documentation|response time|customer service)\b", t):
        reply, sources = _cluster_detail(3)
        return reply, sources, 3

    # Intent 5: fitness / social
    if re.search(r"\b(fitness|social|workout|community|challenge|avatar|exercise|tracking)\b", t):
        reply, sources = _cluster_detail(0)
        return reply, sources, 0

    # Intent 6: notifications / alerts
    if re.search(r"\b(notification|alert|reminder|do.not.disturb|push notification)\b", t):
        reply, sources = _cluster_detail(4)
        return reply, sources, 4

    # Intent 7: water / durability
    if re.search(r"\b(water|swim|waterproof|durability|durable|strap|physical|resistant)\b", t):
        reply, sources = _cluster_detail(6)
        return reply, sources, 6

    # Intent 9: premium / firmware / subscription
    if re.search(r"\b(premium|subscription|firmware|update|os compatibility|new feature)\b", t):
        reply, sources = _cluster_detail(9)
        return reply, sources, 9

    # Intent 3: privacy (multi-user — distinct from data security)
    if re.search(r"\b(multi.user|family|sharing|privacy setting|profile)\b", t):
        reply, sources = _cluster_detail(2)
        return reply, sources, 2

    # Intent 10: general / neutral feedback clusters 5 & 7
    if re.search(r"\b(general feedback|average feedback|neutral|cluster 5|cluster 7)\b", t):
        c5, c7 = CLUSTER_DATA[5], CLUSTER_DATA[7]
        return (
            f"There are two unlinked feedback clusters with no roadmap items.\n"
            f"Cluster 5 ({c5['name']}): {c5['vol']:,} entries, {c5['pos']}% positive, priority {c5['priority']}.\n"
            f"Cluster 7 ({c7['name']}): {c7['vol']:,} entries, {c7['pos']}% positive, priority {c7['priority']}.\n"
            "Cluster 7 is largely neutral/positive; Cluster 5 shows uniformly average sentiment with no clear actionable signal.",
            ["cluster:5", "cluster:7"],
            None,
        )

    # Intent 11: summary / overview / dataset
    if re.search(r"\b(summary|overview|total|dataset|how many|all clusters|entire dataset|big picture)\b", t):
        return (
            "Dataset: 20,000 feedback entries. "
            "Overall sentiment: 33% positive, 67% negative. "
            "Channels: App Review 28%, Social Media 26%, Support Ticket 24%, Beta Testing 22%. "
            "10 semantic clusters, top priority is Battery, Connectivity & Lag (score 94), lowest is Subscriptions & Update Regressions (score 39).",
            ["summary"],
            None,
        )

    # Intent 12: positive / best clusters
    if re.search(r"\b(positive|best|happiest|most satisfied|highest satisfaction|top rated)\b", t):
        return (
            "The three most positive clusters are:\n"
            "1. Mixed & Neutral Sentiment — 68% positive (2,925 entries)\n"
            "2. Subscriptions & Update Regressions — 46% positive (382 entries)\n"
            "3. Fitness Tracking & Customization — 36% positive (7,843 entries)\n"
            "Mixed & Neutral Sentiment is the only cluster with majority-positive feedback.",
            ["cluster:7", "cluster:9", "cluster:0"],
            None,
        )

    # Intent 13: negative / worst clusters
    if re.search(r"\b(negative|worst|unhappiest|most dissatisfied|most complaints|critical|unhappy)\b", t):
        return (
            "The three most negative clusters are:\n"
            "1. Battery, Connectivity & Lag — 90% negative (4,202 entries)\n"
            "2. Average Product Feedback — 100% negative (232 entries)\n"
            "3. Health Data Security — 100% negative (105 entries)\n"
            "Battery, Connectivity & Lag has both the highest volume and worst sentiment — the loudest pain point by far.",
            ["cluster:1", "cluster:5", "cluster:8"],
            None,
        )

    # Intent 14: roadmap
    if re.search(r"\b(roadmap|planned|backlog|under review|active item|initiative)\b", t):
        return (
            "Roadmap status across 8 initiatives:\n"
            "Active (4): PWL-ROAD-01 Fitness Tracking, PWL-ROAD-02 Battery & Lag, PWL-ROAD-04 Support & Setup, PWL-ROAD-07 Health Data Security\n"
            "Planned (2): PWL-ROAD-03 Privacy & Multi-User, PWL-ROAD-08 Subscriptions & Updates\n"
            "Under Review (1): PWL-ROAD-05 Notification Settings\n"
            "Backlog (1): PWL-ROAD-06 Water Resistance\n"
            "Clusters 5 and 7 have no roadmap items.",
            ["roadmap"],
            None,
        )

    # Intent 15: trends / monthly
    if re.search(r"\b(trend|monthly|over time|month.over.month|growing|declining|trajectory)\b", t):
        return (
            "Data spans Mar 2024 – Feb 2025 (12 months). "
            "Battery & Connectivity and Data Security & Health have grown month-over-month, indicating worsening user experience in those areas. "
            "Fitness & Social volume peaked in Dec 2024, likely driven by holiday activations. "
            "Overall feedback volume has a slight uplift across all clusters through the year.",
            ["trends", "cluster:1", "cluster:8", "cluster:0"],
            None,
        )

    # Intent 16: channels
    if re.search(r"\b(channel|app review|social media|support ticket|beta test|distribution)\b", t):
        return (
            "Feedback channel breakdown (20,000 total entries):\n"
            "- App Review: 28% (5,600 entries)\n"
            "- Social Media: 26% (5,200 entries)\n"
            "- Support Ticket: 24% (4,800 entries)\n"
            "- Beta Testing: 22% (4,400 entries)\n"
            "App reviews are the largest source, but support tickets tend to carry the most critical negative sentiment.",
            ["summary", "channel"],
            None,
        )

    # Intent 17: recommendations / actions / next steps
    if re.search(r"\b(recommend|what should (i|we|ethan)|action|next step|suggest|what to do|prioritize)\b", t):
        return (
            "Based on the data, three immediate recommendations:\n"
            "1. Fix battery drain and connectivity lag — 90% negative, 4,202 entries, Active (PWL-ROAD-02). Highest priority in the dataset; nearly every user is dissatisfied.\n"
            "2. Improve fitness tracking accuracy and social features — 64% negative, 7,843 entries, Active (PWL-ROAD-01). Largest volume cluster; even small sentiment gains have major impact.\n"
            "3. Improve notification customization — 69% negative, 2,135 entries, Under Review (PWL-ROAD-05). High negative rate needs to move from Under Review to Active.",
            ["cluster:1", "cluster:0", "cluster:4"],
            None,
        )

    # Intent 18: jira / ticket draft
    if re.search(r"\b(jira|ticket|draft|create (a )?ticket|write (a )?ticket)\b", t):
        return (
            "Draft Jira ticket for top issue:\n\n"
            "Title: [PWL-ROAD-02] Resolve Battery Drain and Connectivity Lag\n\n"
            "Description:\n"
            "User feedback analysis (20,000 entries) identifies Battery, Connectivity & Lag as the highest-priority cluster with a score of 94/100. "
            "Of 4,202 entries in this cluster, 90% are negative, covering battery drain during workouts, Bluetooth instability, software lag, and sync errors. "
            "This represents the single largest source of user dissatisfaction across the PulseWear platform.\n\n"
            "Acceptance Criteria:\n"
            "- Battery drain rate reduced by measurable % under active tracking\n"
            "- Bluetooth reconnect time < 3s after interruption\n"
            "- Software lag eliminated in core app flows\n"
            "- Cluster 1 negative sentiment drops below 70% in next feedback cycle",
            ["cluster:1", "PWL-ROAD-02"],
            1,
        )

    # Intent 19: compare clusters
    if re.search(r"\b(compare|comparison|versus|vs\.?|which is better|difference between)\b", t):
        # Try to detect two cluster names or numbers in the query
        mentioned = [cid for cid in CLUSTER_DATA if CLUSTER_DATA[cid]["name"].lower().split("(")[0].strip() in t or f"cluster {cid}" in t]
        if len(mentioned) >= 2:
            a, b = mentioned[0], mentioned[1]
            ca, cb = CLUSTER_DATA[a], CLUSTER_DATA[b]
            return (
                f"Comparing clusters:\n"
                f"- {ca['name']}: {ca['vol']:,} entries, {ca['pos']}% positive, priority {ca['priority']}, roadmap {ca['roadmap_id'] or 'none'} ({ca['status'] or 'N/A'})\n"
                f"- {cb['name']}: {cb['vol']:,} entries, {cb['pos']}% positive, priority {cb['priority']}, roadmap {cb['roadmap_id'] or 'none'} ({cb['status'] or 'N/A'})\n"
                f"{'Cluster ' + str(a) + ' has higher priority.' if ca['priority'] > cb['priority'] else 'Cluster ' + str(b) + ' has higher priority.'}",
                [f"cluster:{a}", f"cluster:{b}"],
                None,
            )
        # Default comparison: Battery vs Fitness (top two by priority)
        ca, cb = CLUSTER_DATA[1], CLUSTER_DATA[0]
        return (
            "Comparing the two highest-priority clusters:\n"
            f"- {ca['name']}: {ca['vol']:,} entries, {ca['pos']}% positive, priority {ca['priority']}, PWL-ROAD-02 Active\n"
            f"- {cb['name']}: {cb['vol']:,} entries, {cb['pos']}% positive, priority {cb['priority']}, PWL-ROAD-01 Active\n"
            "Battery, Connectivity & Lag has the worst sentiment; Fitness Tracking & Customization has the largest volume — both need active attention.",
            ["cluster:1", "cluster:0"],
            None,
        )

    # Fallback
    return (
        "I can answer questions about the 10 feedback clusters, sentiment trends, roadmap status, and priorities. "
        "Try asking about battery issues, data security, top priorities, or the data overview. "
        "Type 'help' to see all available topics.",
        [],
        None,
    )

# ── Pydantic models ───────────────────────────────────────────────────────────
class SentimentRequest(BaseModel):
    text: str

class ChatMessage(BaseModel):
    role: str     # "user" | "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    rows = len(DATA) if DATA is not None else 0
    return {
        "service": "PulseWear Feedback Intelligence API",
        "version": "1.0.0",
        "rows_loaded": rows,
        "endpoints": ["/sentiment", "/themes", "/trends", "/feedback/{cluster_id}", "/roadmap"],
    }


@app.post("/sentiment")
def analyze_sentiment(req: SentimentRequest):
    """
    Run DistilBERT sentiment analysis on a single text.
    Returns: { label: 'POSITIVE'|'NEGATIVE', score: float }
    """
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="text must not be empty")

    try:
        pipe = get_sentiment_pipeline()
        result = pipe(text[:512])[0]  # truncate to model max
        return {
            "label": result["label"],    # 'POSITIVE' or 'NEGATIVE'
            "score": round(result["score"], 4),
            "text":  text[:120],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model error: {str(e)}")


@app.get("/themes")
def get_themes():
    """
    Return all clusters with volume, sentiment, and roadmap data.
    Cluster count is derived from unique values in cluster_label column.
    """
    if DATA is None:
        raise HTTPException(status_code=503, detail="Data not loaded")

    cluster_ids = sorted(DATA["cluster_label"].dropna().unique().astype(int).tolist())
    themes = []
    for cid in cluster_ids:
        subset = DATA[DATA["cluster_label"] == cid]
        if len(subset) == 0:
            continue
        total      = len(subset)
        pos_count  = (subset["sentiment_label"] == "POSITIVE").sum()
        pos_pct    = round(pos_count / total * 100)
        neg_pct    = 100 - pos_pct
        avg_score  = round(float(subset["sentiment_score"].mean()), 4)
        description = str(subset["cluster_description"].iloc[0]) if "cluster_description" in subset.columns else ""
        name = description.split(".")[0].strip() if description else f"Cluster {cid}"
        rm = ROADMAP.get(cid)

        # Priority score: weighted by volume and negative sentiment
        priority = min(100, round((neg_pct * 0.6) + (min(total, 2500) / 2500 * 40)))

        themes.append({
            "cluster_id":    cid,
            "name":          name,
            "description":   description,
            "volume":        total,
            "positive_pct":  pos_pct,
            "negative_pct":  neg_pct,
            "avg_score":     avg_score,
            "roadmap_id":    rm["id"] if rm else None,
            "status":        rm["status"] if rm else None,
            "priority_score": priority,
        })

    return {"themes": sorted(themes, key=lambda t: -t["volume"])}


@app.get("/trends")
def get_trends():
    """
    Monthly feedback volume per cluster.
    Returns array of { month, month_short, volumes: [N values, one per cluster] }
    Cluster count is derived from unique values in cluster_label column.
    """
    if DATA is None:
        raise HTTPException(status_code=503, detail="Data not loaded")

    cluster_ids = sorted(DATA["cluster_label"].dropna().unique().astype(int).tolist())
    df = DATA.dropna(subset=["timestamp"]).copy()
    df["month_key"] = df["timestamp"].dt.to_period("M")

    periods = sorted(df["month_key"].unique())
    result = []
    for p in periods:
        month_df = df[df["month_key"] == p]
        vols = [int((month_df["cluster_label"] == c).sum()) for c in cluster_ids]
        result.append({
            "month":       p.strftime("%b %Y"),
            "month_short": p.strftime("%b"),
            "volumes":     vols,
        })

    return {"months": result, "total_periods": len(result)}


@app.get("/feedback/{cluster_id}")
def get_feedback(cluster_id: int, limit: int = 20, sentiment: str = "all"):
    """
    Return raw feedback quotes for a given cluster.
    Optional ?sentiment=POSITIVE|NEGATIVE|all
    Optional ?limit=N (default 20, max 100)
    """
    if DATA is None:
        raise HTTPException(status_code=503, detail="Data not loaded")
    if cluster_id < 0 or cluster_id > 9:
        raise HTTPException(status_code=404, detail="cluster_id must be 0–9")

    limit = min(limit, 100)
    subset = DATA[DATA["cluster_label"] == cluster_id].copy()

    if sentiment.upper() in ("POSITIVE", "NEGATIVE"):
        subset = subset[subset["sentiment_label"] == sentiment.upper()]

    sample = subset.sample(n=min(limit, len(subset)), random_state=42)

    feedback = [
        {
            "feedback_id": row.get("feedback_id", ""),
            "text":        row["feedback_text"],
            "sentiment":   row["sentiment_label"],
            "score":       round(float(row["sentiment_score"]), 4),
            "channel":     row.get("channel", ""),
            "platform":    row.get("platform", ""),
            "timestamp":   str(row["timestamp"])[:10] if pd.notna(row["timestamp"]) else "",
        }
        for _, row in sample.iterrows()
    ]

    return {
        "cluster_id":   cluster_id,
        "name":         CLUSTER_NAMES.get(cluster_id, f"Cluster {cluster_id}"),
        "total":        len(subset),
        "returned":     len(feedback),
        "feedback":     feedback,
    }


@app.post("/chat")
def chat(req: ChatRequest):
    """
    Rule-based feedback intelligence chat. Matches user intent against ~25
    patterns and returns data-precise answers about the PulseWear dataset.
    Supports multi-turn context (follow-up questions about the last cluster).
    """
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty")

    last_user = next(
        (m.content for m in reversed(req.messages) if m.role == "user"), ""
    )
    if not last_user.strip():
        raise HTTPException(status_code=400, detail="No user message found")

    history = [{"role": m.role, "content": m.content} for m in req.messages[:-1]]
    reply, sources, _ = _match_intent(last_user, history)
    return {"reply": reply, "sources": sources}


@app.get("/chat/models")
def list_chat_models():
    """Return engine info for the rule-based chat system."""
    return {"models": ["rule-based"], "current": "rule-based", "type": "rule-based"}


@app.get("/roadmap")
def get_roadmap():
    """
    Return all roadmap-linked themes with priority scores.
    """
    if DATA is None:
        raise HTTPException(status_code=503, detail="Data not loaded")

    items = []
    for cid, rm in ROADMAP.items():
        if rm is None:
            continue
        subset    = DATA[DATA["cluster_label"] == cid]
        total     = len(subset)
        pos_pct   = round((subset["sentiment_label"] == "POSITIVE").sum() / max(total, 1) * 100)
        neg_pct   = 100 - pos_pct
        priority  = min(100, round((neg_pct * 0.6) + (min(total, 2500) / 2500 * 40)))

        items.append({
            "roadmap_id":     rm["id"],
            "cluster_id":     cid,
            "theme_name":     CLUSTER_NAMES.get(cid, f"Cluster {cid}"),
            "volume":         total,
            "positive_pct":   pos_pct,
            "negative_pct":   neg_pct,
            "priority_score": priority,
            "status":         rm["status"],
        })

    return {"roadmap": sorted(items, key=lambda x: -x["priority_score"])}
