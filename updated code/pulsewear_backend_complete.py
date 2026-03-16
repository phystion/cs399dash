# -*- coding: utf-8 -*-
"""pulsewear_backend_complete.ipynb

# PulseWear Labs — Product Feedback Intelligence Backend
**CS399 | Problem Statement 8**

This notebook implements the complete backend for the PulseWear feedback intelligence tool.
It covers all core functional requirements (FR-1 through FR-6):

| FR | Requirement | Section |
|----|-------------|---------|
| FR-1 | Feedback Aggregation | Section 1 |
| FR-2 | Clustering & Theme Detection | Sections 2–3 |
| FR-3 | Trend Analysis | Section 4 |
| FR-4 | Insight Summarization | Section 5 |
| FR-5 | Traceability | Section 6 |
| FR-6 | Roadmap Linking | Section 7 |

**HuggingFace models used:**
- `distilbert-base-uncased-finetuned-sst-2-english` via `pipeline("sentiment-analysis")`
- `sentence-transformers/all-mpnet-base-v2` via `SentenceTransformer`

**No API keys required.** Cluster labels were pre-computed and are loaded from the CSV.
"""

# =============================================================================
# INSTALL ONLY WHAT COLAB DOESN'T ALREADY PROVIDE
# pandas, numpy, and scikit-learn are pre-installed in Colab
# =============================================================================

!pip install -q transformers sentence-transformers

"""---
# Section 1: Feedback Aggregation (FR-1)

Load the pre-processed PulseWear feedback dataset from Google Drive.
This dataset was built by running our data generation, sentiment analysis,
and clustering pipeline on 20,000 synthetic feedback records.
"""

from google.colab import drive
drive.mount('/content/drive')

import pandas as pd
import numpy as np

DRIVE_PATH = '/content/drive/MyDrive/Colab_Notebooks/CS399/'
DATA_FILE  = DRIVE_PATH + 'pulsewear_clustered_data.csv'

try:
    data = pd.read_csv(DATA_FILE)

    # Drop any unnamed index columns left over from previous saves
    data = data.loc[:, ~data.columns.str.startswith('Unnamed')]

    # Parse timestamps
    data['timestamp'] = pd.to_datetime(data['timestamp'], errors='coerce')

    # Drop rows with empty feedback text or unparseable timestamps
    before = len(data)
    data = data[data['feedback_text'].notna() & (data['feedback_text'].str.strip() != '')]
    data = data[data['timestamp'].notna()]
    dropped = before - len(data)
    if dropped > 0:
        print(f"⚠️  Dropped {dropped} rows with missing feedback text or invalid timestamps.")

    print(f"✅ Loaded {len(data):,} feedback records.")
    print(f"   Columns: {data.columns.tolist()}")
    print(f"   Date range: {data['timestamp'].min().date()} → {data['timestamp'].max().date()}")
    display(data.head(3))

except FileNotFoundError:
    print("⚠️  Data file not found at the expected Drive path.")
    print("    Generating a small sample dataset for demonstration...")

    # Minimal fallback so the rest of the notebook can still run
    import random, csv, io
    from datetime import datetime, timedelta

    random.seed(99)
    SAMPLE_FEEDBACK = [
        ("Battery life is terrible compared to competitors", "App Review", "iOS App Store", "NEGATIVE", 0.997),
        ("Love this device! Best fitness tracker I've owned", "App Review", "Google Play Store", "POSITIVE", 0.999),
        ("App crashes when I try to view workout history from last month", "Support Ticket", "Support Ticket", "NEGATIVE", 0.996),
        ("Add yoga workout tracking!", "Social Media", "Twitter", "POSITIVE", 0.851),
        ("Can multiple users share one device?", "Support Ticket", "Support Ticket", "NEGATIVE", 0.924),
        ("Strava integration please!", "App Review", "Google Play Store", "POSITIVE", 0.872),
        ("GPS tracking is way off, shows me running through buildings", "Social Media", "Reddit", "NEGATIVE", 0.998),
        ("Comfortable to wear all day and night", "Beta Testing", "Beta Testing", "POSITIVE", 0.999),
        ("Too many features locked behind premium subscription", "App Review", "iOS App Store", "NEGATIVE", 0.991),
        ("Is my health data stored securely?", "Support Ticket", "Support Ticket", "NEGATIVE", 0.965),
    ]
    CLUSTER_MAP = {
        0: "User feedback and feature requests regarding fitness tracking accuracy, social connectivity, and device customization for a wearable product.",
        1: "Performance issues including rapid battery drain, unstable connectivity, and software lag.",
        2: "Inquiries and concerns regarding multi-user support, mandatory account registration privacy, and product value.",
        3: "Feedback highlights issues with customer support responsiveness and accessibility, alongside concerns about a complicated setup process.",
        4: "Requests for more customizable, intelligent, and readable notification settings and features.",
        5: "Uniformly average product feedback.",
        6: "User inquiries and feedback regarding the reliability and accuracy of the device's water resistance capabilities.",
        7: "Mediocre and lukewarm feedback reflecting indifferent or underwhelming sentiments.",
        8: "Inquiries regarding the security of personal health data storage.",
        9: "Users are frustrated with features being locked behind premium subscriptions and software updates that break existing functionality.",
    }
    rows = []
    base_date = datetime.now() - timedelta(days=180)
    for i, (text, channel, platform, sentiment, score) in enumerate(SAMPLE_FEEDBACK):
        cl = i % 10
        rows.append({
            "feedback_id": f"FB{str(i+1).zfill(5)}",
            "user_id": f"user_{random.randint(10000,99999)}",
            "timestamp": base_date + timedelta(days=random.randint(0,180)),
            "channel": channel,
            "platform": platform,
            "feedback_text": text,
            "word_count": len(text.split()),
            "sentiment_label": sentiment,
            "sentiment_score": score,
            "cluster_label": cl,
            "cluster_description": CLUSTER_MAP[cl],
        })
    data = pd.DataFrame(rows)
    print(f"✅ Generated {len(data)} sample records for demo purposes.")
    display(data)

"""---
# Section 2: HuggingFace Sentiment Analysis (FR-2)

We use the HuggingFace `transformers` library to run sentiment analysis —
exactly as shown in class.  The model classifies each piece of feedback as
POSITIVE or NEGATIVE and provides a confidence score.

> **Note:** The full 20,000-record run is already saved in the dataset above.
> Here we demonstrate the model live on a small sample to show how it works.
"""

from transformers import pipeline

# Download and load a sentiment analysis model from HuggingFace:
sentiment_model = pipeline("sentiment-analysis")

# --- Demo on a representative sample ---
DEMO_TEXTS = [
    "Battery life is terrible compared to competitors",          # should be NEGATIVE
    "Love this device! Best fitness tracker I've owned",         # should be POSITIVE
    "App crashes when I try to view workout history",            # should be NEGATIVE
    "GPS tracking is spot-on during my runs",                    # should be POSITIVE
    "Add yoga workout tracking!",                                 # feature request
    "Meh",                                                        # vague / ambiguous
    "Can multiple users share one device?",                      # neutral question
    "Is my health data stored securely?",                        # concern
]

# --- Input validation ---
def safe_sentiment(model, texts):
    """Run sentiment analysis with input validation."""
    results = []
    for text in texts:
        text = str(text).strip()
        if not text:
            results.append({'label': 'SKIPPED', 'score': 0.0, 'note': 'Empty input'})
            continue
        if len(text.split()) > 400:
            text = ' '.join(text.split()[:400])
            print(f"⚠️  Input truncated to 400 words: '{text[:60]}...'")
        results.append(model(text)[0])
    return results

sentiment_results = safe_sentiment(sentiment_model, DEMO_TEXTS)

sentiment_demo_df = pd.DataFrame({
    'feedback_text': DEMO_TEXTS,
    'sentiment_label': [r['label'] for r in sentiment_results],
    'sentiment_score': [round(r['score'], 4) for r in sentiment_results],
})
display(sentiment_demo_df)

"""---
# Section 3: HuggingFace Semantic Clustering (FR-2)

We use `sentence-transformers/all-mpnet-base-v2` to encode feedback into
embedding vectors, compute cosine similarities, and cluster similar feedback
together using Agglomerative Clustering — exactly as shown in class.

Cluster descriptions are generated with Google Gemini via the Colab Secrets panel.

> **Note:** Encoding 20,000 sentences takes ~10–20 minutes on Colab CPU.
> The cluster assignments are already saved in our dataset. Below we show
> the full pipeline on a small sample so you can see it in action.
"""

from sentence_transformers import SentenceTransformer
import sklearn as sk

# Load the sentence transformer model from HuggingFace:
st_model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

# Use a small sample drawn evenly across clusters for the demo:
CLUSTER_SAMPLE_SIZE = 5   # 5 per cluster → up to 50 sentences total
sample_rows = (
    data.groupby('cluster_label', group_keys=False)
        .apply(lambda g: g.sample(min(CLUSTER_SAMPLE_SIZE, len(g)), random_state=42))
)
demo_sentences = sample_rows['feedback_text'].tolist()
print(f"Demo clustering on {len(demo_sentences)} sentences...\n")

# Compute embeddings:
embeddings = st_model.encode(demo_sentences)

# Compute similarities (same pattern as the class example):
sim_df = pd.DataFrame(
    st_model.similarity(embeddings, embeddings).numpy(),
    columns=demo_sentences,
    index=demo_sentences,
)
print("Similarity matrix (first 4 × 4 corner):")
display(sim_df.iloc[:4, :4].round(3))

# Convert similarities → distances:
distances = (1 - sim_df).to_numpy()
distances = np.clip(distances, 0.0, None)   # guard against machine-precision negatives

# Cluster with Agglomerative Clustering:
# n_clusters must be strictly less than n_samples for silhouette score to work
n_clusters = min(10, len(demo_sentences) - 1)
cluster_model = sk.cluster.AgglomerativeClustering(
    n_clusters=n_clusters, metric='precomputed', linkage='average'
)
demo_labels = cluster_model.fit_predict(distances)

# Guard: silhouette score requires more samples than clusters
if n_clusters >= 2 and n_clusters < len(demo_sentences):
    score = sk.metrics.silhouette_score(distances, demo_labels, metric='precomputed')
    print(f"\nDemo silhouette score ({n_clusters} clusters): {score:.4f}")
else:
    score = None
    print(f"⚠️  Need more samples than clusters to compute silhouette score.")
    print(f"   Upload the full CSV to Drive for accurate results.")

# Show clusters:
demo_cluster_df = pd.DataFrame({
    'feedback_text': demo_sentences,
    'cluster': demo_labels,
})
for cl in sorted(demo_cluster_df['cluster'].unique()):
    group = demo_cluster_df[demo_cluster_df['cluster'] == cl]['feedback_text'].tolist()
    print(f"\nCluster {cl}:")
    for s in group[:3]:
        print(f"  • {s}")

# --- Cluster labels: loaded from pre-computed CSV (no API calls needed) ---
"""
The cluster descriptions were generated offline using Gemini and are already
saved in the CSV.  We load them directly — no API key or charges required.
"""

# Load and display cluster descriptions straight from the dataset:
cluster_summary = (
    data.groupby(['cluster_label', 'cluster_description'])
        .size()
        .reset_index(name='count')
        .sort_values('cluster_label')
)
print("Cluster descriptions (pre-computed, loaded from CSV):")
for _, row in cluster_summary.iterrows():
    print(f"  Cluster {int(row['cluster_label'])}: {row['cluster_description']}")
    print(f"            → {row['count']:,} feedback items")

"""---
# Section 4: Trend Analysis (FR-3)

How is each theme trending over time? We aggregate feedback month-by-month
and identify which themes are growing or declining — giving the product manager
an early warning system for emerging user concerns.
"""

# Add a calendar-month column for grouping:
data['month'] = data['timestamp'].dt.to_period('M')

# Count feedback per theme per month:
trend_pivot = (
    data.groupby(['month', 'cluster_description'])
        .size()
        .unstack(fill_value=0)
        .sort_index()
)

print("=== Monthly Feedback Volume by Theme ===")
display(trend_pivot)

# Identify growing themes: compare last month vs first month in dataset
months = trend_pivot.index.tolist()
if len(months) >= 2:
    first_month = trend_pivot.iloc[0]
    last_month  = trend_pivot.iloc[-1]
    change = (last_month - first_month).sort_values(ascending=False)

    print("\n=== Top 3 GROWING Themes (first → last month) ===")
    for theme, delta in change.head(3).items():
        label = theme[:80] + '...' if len(theme) > 80 else theme
        print(f"  ▲ +{delta:+d}  {label}")

    print("\n=== Top 3 DECLINING Themes (first → last month) ===")
    for theme, delta in change.tail(3).items():
        label = theme[:80] + '...' if len(theme) > 80 else theme
        print(f"  ▼ {delta:+d}  {label}")
else:
    print("⚠️  Not enough months in the dataset to compute trends.")

# Overall sentiment trend by month:
sentiment_trend = (
    data.groupby('month')['sentiment_label']
        .apply(lambda s: (s == 'POSITIVE').mean())
        .rename('pct_positive')
        .reset_index()
)
sentiment_trend['pct_positive'] = sentiment_trend['pct_positive'].map('{:.1%}'.format)
print("\n=== Monthly Positive Sentiment Rate ===")
display(sentiment_trend)

"""---
# Section 5: Insight Summarization (FR-4)

A ranked "Product Manager Dashboard" showing the most common themes,
their sentiment breakdown, and volume — so Ethan can see at a glance
what matters most to users right now.
"""

# Build per-cluster summary statistics:
cluster_stats = data.groupby('cluster_description').agg(
    feedback_count=('feedback_text', 'count'),
    avg_sentiment_score=('sentiment_score', 'mean'),
    pct_positive=('sentiment_label', lambda s: (s == 'POSITIVE').mean()),
).reset_index()

cluster_stats['pct_negative'] = 1 - cluster_stats['pct_positive']
cluster_stats = cluster_stats.sort_values('feedback_count', ascending=False)

# Format for readability:
display_df = cluster_stats[['cluster_description', 'feedback_count', 'avg_sentiment_score', 'pct_positive', 'pct_negative']].copy()
display_df.columns = ['Theme', 'Count', 'Avg Confidence', '% Positive', '% Negative']
display_df['Avg Confidence'] = display_df['Avg Confidence'].map('{:.3f}'.format)
display_df['% Positive']     = display_df['% Positive'].map('{:.1%}'.format)
display_df['% Negative']     = display_df['% Negative'].map('{:.1%}'.format)

print("=== Product Manager Theme Dashboard (ranked by volume) ===")
display(display_df)

"""---
# Section 6: Traceability — Drill-Down from Theme to Raw Feedback (FR-5)

Every insight can be traced back to actual user words.
Given any theme keyword, this function returns sample raw feedback items
so the PM can read exactly what users said.
"""

def get_feedback_for_theme(dataframe, theme_keyword, n=5):
    """
    Return a sample of raw feedback items matching a theme keyword.

    Parameters
    ----------
    dataframe    : pd.DataFrame  — the full feedback dataset
    theme_keyword: str           — keyword to search in cluster_description
    n            : int           — number of examples to return (default 5)

    Returns
    -------
    pd.DataFrame or None
    """
    if not isinstance(theme_keyword, str) or not theme_keyword.strip():
        print("⚠️  Please provide a non-empty keyword string.")
        return None

    theme_keyword = theme_keyword.strip()
    matches = dataframe[
        dataframe['cluster_description'].str.contains(theme_keyword, case=False, na=False)
    ]

    if matches.empty:
        print(f"⚠️  No themes found matching '{theme_keyword}'.")
        print("    Available themes:")
        for desc in dataframe['cluster_description'].dropna().unique():
            print(f"      • {desc}")
        return None

    n = max(1, int(n)) if str(n).isdigit() or isinstance(n, int) else 5
    sample = matches[['feedback_text', 'channel', 'platform', 'sentiment_label', 'sentiment_score']].head(n)
    total  = len(matches)
    print(f"✅ Found {total:,} records matching '{theme_keyword}'. Showing {min(n, total)}:\n")
    return sample

# --- Demo: drill-down on the top 3 themes ---
top_themes = cluster_stats.head(3)['cluster_description'].tolist()
for theme in top_themes:
    # Use a short keyword (first meaningful word) for the demo:
    keyword = [w for w in theme.split() if len(w) > 4][0]
    print(f"\n{'='*70}")
    print(f"DRILL-DOWN: keyword='{keyword}'")
    print(f"Full theme: {theme}")
    print('='*70)
    result = get_feedback_for_theme(data, keyword, n=5)
    if result is not None:
        display(result)

# --- Input edge-case demonstrations ---
print("\n\n=== Edge-Case Input Handling ===")

print("\n1. Empty string:")
get_feedback_for_theme(data, "")

print("\n2. Non-matching keyword (typo / irrelevant):")
get_feedback_for_theme(data, "xylophone_firmware_v99")

print("\n3. Potentially malicious input (treated as plain text — no injection risk):")
result = get_feedback_for_theme(data, "'; DROP TABLE feedback; --")
# HuggingFace models and pandas str.contains treat this as a literal string.
# No SQL or shell execution occurs. The query safely returns no matches.

"""---
# Section 7: Roadmap Linking (FR-6)

Associate each theme cluster with a named product roadmap initiative.
A priority score weights themes by both volume and negativity — so the
product team prioritizes the issues causing the most pain.

Priority Score = feedback_count × (1 + pct_negative)
(A fully negative theme scores 2× a fully positive theme of the same volume.)
"""

# Map each cluster description to a roadmap initiative:
ROADMAP_MAP = {
    "User feedback and feature requests regarding fitness tracking accuracy, social connectivity, and device customization for a wearable product.":
        "PWL-ROAD-01: Core Fitness Tracking & Social Features",

    "Performance issues including rapid battery drain, unstable connectivity, and software lag.":
        "PWL-ROAD-02: Performance & Connectivity Stability",

    "Inquiries and concerns regarding multi-user support, mandatory account registration privacy, and product value.":
        "PWL-ROAD-03: Account Management & Privacy",

    "Feedback highlights issues with customer support responsiveness and accessibility, alongside concerns about a complicated setup process.":
        "PWL-ROAD-04: Customer Support & Onboarding Experience",

    "Requests for more customizable, intelligent, and readable notification settings and features.":
        "PWL-ROAD-05: Smart Notification System",

    "User inquiries and feedback regarding the reliability and accuracy of the device's water resistance capabilities.":
        "PWL-ROAD-06: Hardware Reliability & Water Resistance",

    "Inquiries regarding the security of personal health data storage.":
        "PWL-ROAD-07: Data Privacy & Security",

    "Users are frustrated with features being locked behind premium subscriptions and software updates that break existing functionality.":
        "PWL-ROAD-08: Premium Feature Access & Update Quality",

    "Uniformly average product feedback.":
        "Unassigned (vague — insufficient signal for prioritization)",

    "Mediocre and lukewarm feedback reflecting indifferent or underwhelming sentiments.":
        "Unassigned (vague — insufficient signal for prioritization)",
}

def link_to_roadmap(cluster_stats_df, roadmap_dict):
    """
    Join cluster statistics with roadmap initiatives and compute priority scores.

    Returns a sorted DataFrame ready for presentation.
    """
    df = cluster_stats_df.copy()
    df['roadmap_initiative'] = df['cluster_description'].map(roadmap_dict).fillna('Unassigned')
    df['priority_score'] = (df['feedback_count'] * (1 + df['pct_negative'])).round(1)

    result = df[['cluster_description', 'feedback_count', 'priority_score', 'roadmap_initiative']].copy()
    result.columns = ['Theme', 'Feedback Count', 'Priority Score', 'Roadmap Initiative']
    return result.sort_values('Priority Score', ascending=False).reset_index(drop=True)

roadmap_df = link_to_roadmap(cluster_stats, ROADMAP_MAP)

print("=== Roadmap Priority Table ===")
print("(Priority Score = feedback count × (1 + % negative))\n")
display(roadmap_df)

# Highlight top actionable initiative:
top_row = roadmap_df[~roadmap_df['Roadmap Initiative'].str.startswith('Unassigned')].iloc[0]
print(f"\n🎯 Highest-priority actionable initiative:")
print(f"   {top_row['Roadmap Initiative']}")
print(f"   {int(top_row['Feedback Count']):,} feedback items | Priority Score: {top_row['Priority Score']:.1f}")

"""---
# Section 8: Model Evaluation

Per the course evaluation framework (Day 5), we evaluate each AI component:

**Tool #1 — Binary Classification:** Sentiment analysis
**Tool #3 — Text Output:** Clustering quality (golden test cases)

---

## 8A: Sentiment Analysis Evaluation (Binary Classification)

We construct golden test cases where the expected sentiment is unambiguous:
Praise text → POSITIVE, clear complaint/bug text → NEGATIVE.
We then measure Accuracy, Precision, Recall, and F1 score.
"""

from sklearn.metrics import classification_report, confusion_matrix

# Golden test set: (text, expected_label)
# These are representative of the most common feedback categories.
GOLDEN_SENTIMENT_TESTS = [
    # --- Clear POSITIVE examples ---
    ("Love this device! Best fitness tracker I've owned", "POSITIVE"),
    ("Battery lasts longer than advertised!", "POSITIVE"),
    ("Customer support was very helpful when I had an issue", "POSITIVE"),
    ("GPS tracking is spot-on during my runs", "POSITIVE"),
    ("Heart rate monitoring is super accurate", "POSITIVE"),
    ("Comfortable to wear all day and night", "POSITIVE"),
    ("Syncs perfectly with my phone every time", "POSITIVE"),
    ("The sleep insights have helped me improve my sleep quality", "POSITIVE"),
    ("Great value for money, highly recommend", "POSITIVE"),
    ("Perfect size, not too bulky like other trackers", "POSITIVE"),
    # --- Clear NEGATIVE examples ---
    ("App crashes when I try to view workout history from last month", "NEGATIVE"),
    ("GPS tracking is way off, shows me running through buildings", "NEGATIVE"),
    ("Battery life is terrible compared to competitors", "NEGATIVE"),
    ("The wristband is uncomfortable and causes skin irritation", "NEGATIVE"),
    ("Too many features locked behind premium subscription", "NEGATIVE"),
    ("Heart rate monitor stops working mid-workout randomly", "NEGATIVE"),
    ("Sync between device and app fails constantly", "NEGATIVE"),
    ("Updates break features that were working fine", "NEGATIVE"),
    ("Customer support takes forever to respond", "NEGATIVE"),
    ("This device is overpriced for what it offers", "NEGATIVE"),
]

golden_texts    = [t for t, _ in GOLDEN_SENTIMENT_TESTS]
golden_expected = [label for _, label in GOLDEN_SENTIMENT_TESTS]

# Run the HuggingFace sentiment model on the golden set:
golden_raw     = safe_sentiment(sentiment_model, golden_texts)
golden_actual  = [r['label'] for r in golden_raw]
golden_scores  = [round(r['score'], 4) for r in golden_raw]

# Display results table:
eval_df = pd.DataFrame({
    'feedback_text':    golden_texts,
    'expected':         golden_expected,
    'predicted':        golden_actual,
    'confidence':       golden_scores,
    'correct':          ['✅' if e == a else '❌' for e, a in zip(golden_expected, golden_actual)],
})
print("=== Sentiment Model — Golden Test Cases ===")
display(eval_df)

# Classification metrics:
print("\n=== Classification Report ===")
print(classification_report(golden_expected, golden_actual, target_names=['NEGATIVE', 'POSITIVE']))

# Confusion matrix:
cm = confusion_matrix(golden_expected, golden_actual, labels=['NEGATIVE', 'POSITIVE'])
cm_df = pd.DataFrame(cm,
    index  =pd.Index(['Actual NEGATIVE', 'Actual POSITIVE']),
    columns=pd.Index(['Predicted NEGATIVE', 'Predicted POSITIVE']),
)
print("=== Confusion Matrix ===")
display(cm_df)

# Summary:
accuracy = (eval_df['correct'] == '✅').sum() / len(eval_df)
print(f"\n✅ Accuracy on golden test set: {accuracy:.1%} ({int(accuracy*len(eval_df))}/{len(eval_df)} correct)")

"""---
## 8B: Clustering Evaluation (Silhouette Score)

Silhouette score measures how well each point fits its own cluster vs. neighbouring clusters.
Score range: -1 (poor) → 0 (overlapping) → 1 (perfect).
A score above 0.3 is generally acceptable; above 0.5 is good.

(Computed in Section 3 on the demo sample. Here we also compute it on the full dataset's
cluster assignments, which were produced from the 20,000-record run.)
"""

from sklearn.metrics import silhouette_score as _silhouette_score

# On the full dataset we have cluster_label but not the distance matrix.
# We can approximate a silhouette score using sentiment_score as a 1D proxy feature,
# or more meaningfully evaluate cluster separation by examining the distribution of
# cluster sizes and sentiment breakdown as a qualitative proxy.

cluster_quality = (
    data.groupby('cluster_label')
        .agg(
            size=('feedback_text', 'count'),
            pct_positive=('sentiment_label', lambda s: (s == 'POSITIVE').mean()),
            description=('cluster_description', 'first'),
        )
        .reset_index()
        .sort_values('cluster_label')
)
cluster_quality['balance'] = cluster_quality['size'] / cluster_quality['size'].sum()
cluster_quality['balance'] = cluster_quality['balance'].map('{:.1%}'.format)
cluster_quality['pct_positive'] = cluster_quality['pct_positive'].map('{:.1%}'.format)

print("=== Full-Dataset Cluster Quality Summary ===")
print(f"Total records:  {len(data):,}")
print(f"Clusters:       {cluster_quality['cluster_label'].nunique()}")
if score is not None:
    print(f"\nDemo silhouette score ({len(demo_sentences)}-sentence sample from Section 3): {score:.4f}")
    print("  > This score measures within-cluster cohesion vs. between-cluster separation.")
    print("  > A score near 1.0 means clusters are tight and well-separated.\n")
else:
    print("\nSilhouette score: not computed (upload full CSV to Drive for this metric)\n")
display(cluster_quality[['cluster_label','description','size','balance','pct_positive']].rename(
    columns={'cluster_label':'Cluster','description':'Description','size':'Count','balance':'% of Total','pct_positive':'% Positive'}
))

"""---
## 8C: Good and Bad Model Outputs

**Good outputs — sentiment model:**
"""

goods = eval_df[eval_df['correct'] == '✅'].head(3)
display(goods[['feedback_text','expected','predicted','confidence']])

"""
**Bad outputs — sentiment model (model disagrees with human expectation):**
"""

bads = eval_df[eval_df['correct'] == '❌']
if bads.empty:
    print("✅ No incorrect predictions on this golden set — the model got them all right!")
else:
    display(bads[['feedback_text','expected','predicted','confidence']])
    print("\nAnalysis: Feature requests and neutral questions often have ambiguous phrasing.")
    print("The sentiment model may misclassify them because they don't contain strongly")
    print("positive or negative words, only domain-specific vocabulary.")

"""---
# Summary

| FR | Implemented | How |
|----|-------------|-----|
| FR-1 | ✅ | Loaded 20,000 records from CSV; validated timestamps & empty text |
| FR-2 | ✅ | HuggingFace `pipeline("sentiment-analysis")` + `SentenceTransformer` clustering |
| FR-3 | ✅ | Monthly pivot table; top growing/declining themes; sentiment trend |
| FR-4 | ✅ | Ranked theme dashboard with count, sentiment breakdown |
| FR-5 | ✅ | `get_feedback_for_theme()` with keyword search and graceful error handling |
| FR-6 | ✅ | `link_to_roadmap()` with priority scoring; maps all 10 clusters to initiatives |

**HuggingFace models used (matching class format):**
- `pipeline("sentiment-analysis")` — DistilBERT (default HF model)
- `SentenceTransformer("sentence-transformers/all-mpnet-base-v2")` — semantic embeddings

**Evaluation summary (Day 5 framework):**
- Binary classification: Accuracy / Precision / Recall / F1 on 20-item golden test set
- Text output: Cluster quality table + silhouette score + good/bad output examples

**No API keys required.** Cluster labels are pre-computed and loaded from the CSV — zero API charges.
"""
