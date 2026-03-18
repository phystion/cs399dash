"""
export_to_json.py — One-time script to export CSV data to static JSON files.

Run from the backend/ directory:
    python export_to_json.py

Outputs to pulsewear-dashboard/src/lib/:
    themes.json   — cluster objects with stats (count derived from CSV)
    trends.json   — monthly data points
    feedback.json — 30 pre-sampled quotes per cluster
    roadmap.json  — roadmap-linked clusters (requires roadmap_config.json)

Optional: create backend/roadmap_config.json to attach roadmap IDs/statuses:
    {
      "0": {"id": "PWL-ROAD-01", "status": "Active"},
      "1": {"id": "PWL-ROAD-02", "status": "Active"}
    }
    Clusters not listed will have null roadmap_id/status.
    If the file does not exist, roadmap.json is not written.
"""

import json
import sys
from pathlib import Path

try:
    import pandas as pd
    import numpy as np
except ImportError:
    sys.exit("Install pandas and numpy: pip install pandas numpy")

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR        = Path(__file__).parent
CSV_PATH          = SCRIPT_DIR.parent / "data generation excel" / "Data" / "pulsewear_clustered_data.csv"
OUT_DIR           = SCRIPT_DIR.parent / "pulsewear-dashboard" / "src" / "lib"
ROADMAP_CFG_PATH  = SCRIPT_DIR / "roadmap_config.json"

def priority_score(neg_pct: float, volume: int) -> int:
    return min(100, round((neg_pct * 0.6) + (min(volume, 2500) / 2500 * 40)))


def main():
    print(f"Reading CSV: {CSV_PATH}")
    if not CSV_PATH.exists():
        sys.exit(f"CSV not found: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    print(f"Loaded {len(df):,} rows. Columns: {list(df.columns)}")

    # ── Derive cluster IDs from data ──────────────────────────────────────────
    cluster_ids = sorted(df["cluster_label"].dropna().unique().astype(int).tolist())
    print(f"  Found {len(cluster_ids)} clusters: {cluster_ids}")

    # ── Load optional roadmap config ──────────────────────────────────────────
    roadmap_cfg: dict[int, dict] = {}
    if ROADMAP_CFG_PATH.exists():
        with open(ROADMAP_CFG_PATH, encoding="utf-8") as f:
            raw = json.load(f)
        roadmap_cfg = {int(k): v for k, v in raw.items() if v is not None}
        print(f"  roadmap_config.json loaded — {len(roadmap_cfg)} entries")
    else:
        print(f"  roadmap_config.json not found — roadmap fields will be null")

    # ── themes.json ───────────────────────────────────────────────────────────
    themes = []
    for cid in cluster_ids:
        sub = df[df["cluster_label"] == cid]
        if len(sub) == 0:
            continue
        total     = len(sub)
        pos_count = (sub["sentiment_label"] == "POSITIVE").sum()
        pos_pct   = round(int(pos_count) / total * 100)
        neg_pct   = 100 - pos_pct
        avg_score = round(float(sub["sentiment_score"].mean()), 4)
        desc      = str(sub["cluster_description"].iloc[0]) if "cluster_description" in sub.columns else ""
        # Derive name: first sentence of description, or fallback
        name      = desc.split(".")[0].strip() if desc else f"Cluster {cid}"
        rm        = roadmap_cfg.get(cid)

        themes.append({
            "cluster_id":    cid,
            "name":          name,
            "description":   desc,
            "volume":        total,
            "positive_pct":  pos_pct,
            "negative_pct":  neg_pct,
            "avg_score":     avg_score,
            "priority_score": priority_score(neg_pct, total),
            "roadmap_id":    rm["id"]     if rm else None,
            "status":        rm["status"] if rm else None,
        })

    write_json(OUT_DIR / "themes.json", themes)
    print(f"  themes.json — {len(themes)} clusters")

    # ── Volume imbalance check ────────────────────────────────────────────────
    volumes = sorted([t["volume"] for t in themes])
    if len(volumes) >= 2:
        mid = len(volumes) // 2
        median_vol = (volumes[mid - 1] + volumes[mid]) / 2 if len(volumes) % 2 == 0 else volumes[mid]
        lo_thresh = median_vol * 0.3
        hi_thresh = median_vol * 3.0
        outliers = [t for t in themes if t["volume"] < lo_thresh or t["volume"] > hi_thresh]
        if outliers:
            print(f"\n  WARNING: {len(outliers)} cluster(s) have volumes outside 0.3x–3x of median ({median_vol:.0f}):")
            for t in outliers:
                ratio = t["volume"] / median_vol
                print(f"    Cluster {t['cluster_id']} ({t['name']!r}): {t['volume']} rows ({ratio:.1f}x median)")
            print("  Check cluster_label assignment in the CSV — badly imbalanced clusters may indicate a data generation or clustering issue.")
        else:
            print(f"  Volume balance OK: all clusters within 0.3x–3x of median ({median_vol:.0f})")

    # ── trends.json ───────────────────────────────────────────────────────────
    df2 = df.dropna(subset=["timestamp"]).copy()
    df2["month_key"] = df2["timestamp"].dt.to_period("M")
    periods = sorted(df2["month_key"].unique())

    # Exclude partial months (fewer than 500 entries — normal months have ~3300)
    months = []
    for p in periods:
        mdf  = df2[df2["month_key"] == p]
        if len(mdf) < 500:
            continue
        vols = [int((mdf["cluster_label"] == c).sum()) for c in cluster_ids]
        months.append({
            "month":       p.strftime("%b %Y"),
            "month_short": p.strftime("%b"),
            "volumes":     vols,
        })

    write_json(OUT_DIR / "trends.json", months)
    print(f"  trends.json — {len(months)} months")

    # ── feedback.json ─────────────────────────────────────────────────────────
    feedback: dict[str, list] = {}
    for cid in cluster_ids:
        sub    = df[df["cluster_label"] == cid]
        sample = sub.sample(n=min(30, len(sub)), random_state=42)
        quotes = []
        for _, row in sample.iterrows():
            ts = str(row["timestamp"])[:10] if pd.notna(row["timestamp"]) else ""
            quotes.append({
                "feedback_id": str(row.get("feedback_id", "")),
                "text":        str(row["feedback_text"]),
                "sentiment":   str(row["sentiment_label"]),
                "score":       round(float(row["sentiment_score"]), 4),
                "channel":     str(row.get("channel", "")),
                "platform":    str(row.get("platform", "")),
                "timestamp":   ts,
            })
        feedback[str(cid)] = quotes

    write_json(OUT_DIR / "feedback.json", feedback)
    total_q = sum(len(v) for v in feedback.values())
    print(f"  feedback.json — {total_q} quotes across {len(cluster_ids)} clusters")

    # ── roadmap.json (only if roadmap_config.json exists) ────────────────────
    if not roadmap_cfg:
        print("  roadmap.json — skipped (no roadmap_config.json)")
    else:
        # Build a name lookup from themes data
        name_lookup = {t["cluster_id"]: t["name"] for t in themes}
        roadmap_items = []
        for cid, rm in roadmap_cfg.items():
            sub     = df[df["cluster_label"] == cid]
            total   = len(sub)
            if total == 0:
                continue
            pos_pct = round((sub["sentiment_label"] == "POSITIVE").sum() / total * 100)
            neg_pct = 100 - pos_pct

            roadmap_items.append({
                "roadmap_id":    rm["id"],
                "cluster_id":    cid,
                "theme_name":    name_lookup.get(cid, f"Cluster {cid}"),
                "volume":        total,
                "positive_pct":  pos_pct,
                "negative_pct":  neg_pct,
                "priority_score": priority_score(neg_pct, total),
                "status":        rm["status"],
            })

        roadmap_items.sort(key=lambda x: -x["priority_score"])
        write_json(OUT_DIR / "roadmap.json", roadmap_items)
        print(f"  roadmap.json — {len(roadmap_items)} items")

    print("\nDone. All JSON files written to:", OUT_DIR)


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
