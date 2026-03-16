"""
PulseWear Feedback Intelligence — API Test Suite
=================================================
Tests every endpoint with multiple scenarios.
Requires the FastAPI server to be running on port 8000.

Usage:
  python test_scenarios.py
  python test_scenarios.py --base-url http://localhost:8000
  python test_scenarios.py --verbose
"""

import sys
import json
import argparse
import requests
from dataclasses import dataclass, field
from typing import Any

# ── Colors ───────────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def ok(msg):   print(f"  {GREEN}✓{RESET} {msg}")
def fail(msg): print(f"  {RED}✗{RESET} {msg}")
def info(msg): print(f"  {CYAN}·{RESET} {msg}")
def header(msg): print(f"\n{BOLD}{msg}{RESET}")
def dim(msg):  print(f"  {DIM}{msg}{RESET}")

# ── Test result tracking ─────────────────────────────────────────────────────
@dataclass
class Results:
    passed: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)

    def record(self, success: bool, name: str, detail: str = ""):
        if success:
            self.passed += 1
            ok(name)
        else:
            self.failed += 1
            self.errors.append(f"{name}: {detail}")
            fail(f"{name} — {detail}")

    def summary(self):
        total = self.passed + self.failed
        header("─" * 50)
        if self.failed == 0:
            print(f"{GREEN}{BOLD}  All {total} tests passed!{RESET}")
        else:
            print(f"{BOLD}  {self.passed}/{total} passed  ·  {RED}{self.failed} failed{RESET}")
            for e in self.errors:
                print(f"  {RED}→ {e}{RESET}")
        return self.failed == 0


R = Results()

# ── Helpers ───────────────────────────────────────────────────────────────────
def get(url, params=None, verbose=False) -> tuple[int, Any]:
    try:
        r = requests.get(url, params=params, timeout=10)
        if verbose:
            dim(f"GET {url}  →  {r.status_code}")
        return r.status_code, r.json() if r.headers.get("content-type","").startswith("application/json") else {}
    except requests.ConnectionError:
        return 0, {}
    except Exception as e:
        return -1, {"error": str(e)}

def post(url, body, verbose=False) -> tuple[int, Any]:
    try:
        r = requests.post(url, json=body, timeout=15)
        if verbose:
            dim(f"POST {url}  →  {r.status_code}")
        return r.status_code, r.json() if r.headers.get("content-type","").startswith("application/json") else {}
    except requests.ConnectionError:
        return 0, {}
    except Exception as e:
        return -1, {"error": str(e)}


# ── Test suites ───────────────────────────────────────────────────────────────

def test_root(base: str, verbose: bool):
    header("1 / ROOT")
    code, data = get(f"{base}/", verbose=verbose)
    R.record(code == 200, "GET / returns 200")
    R.record(isinstance(data.get("rows_loaded"), int), "rows_loaded is an integer",
             f"got: {data.get('rows_loaded')}")
    if verbose and "rows_loaded" in data:
        info(f"rows_loaded = {data['rows_loaded']:,}")


def test_sentiment(base: str, verbose: bool):
    header("2 / SENTIMENT  (POST /sentiment)")

    # Positive examples
    positive_cases = [
        "Love the run tracking — comparing splits with friends is amazing!",
        "The ECG feature in the latest update is exceptional.",
        "Smart notifications are perfectly timed — not too many, not too few.",
        "The 5ATM waterproof rating held up during lap swimming. Impressed.",
        "Support team resolved my issue in one call — very satisfied.",
    ]

    # Negative examples
    negative_cases = [
        "Battery is dead by 6pm every day. Barely usable.",
        "GPS drops out constantly on my morning run.",
        "My health data was still on the device after I sold it. Unacceptable.",
        "Took 3 hours and two support calls to pair the device. Terrible.",
        "Every firmware update introduces two new bugs. QA needs work.",
    ]

    # Edge cases
    edge_cases = [
        ("Empty text", {"text": ""}),
        ("Very long text", {"text": "bad " * 200}),
        ("Numbers only", {"text": "12345 67890"}),
        ("Single word positive", {"text": "amazing"}),
        ("Single word negative", {"text": "broken"}),
    ]

    print(f"\n  {DIM}Positive samples:{RESET}")
    for text in positive_cases:
        code, data = post(f"{base}/sentiment", {"text": text}, verbose=verbose)
        if code == 200:
            label = data.get("label", "?")
            score = data.get("score", 0)
            correct = label == "POSITIVE"
            R.record(correct, f'"{text[:45]}…" → {label} ({score:.0%})',
                     f"expected POSITIVE, got {label}")
        else:
            R.record(False, f'"{text[:45]}…"', f"HTTP {code}")

    print(f"\n  {DIM}Negative samples:{RESET}")
    for text in negative_cases:
        code, data = post(f"{base}/sentiment", {"text": text}, verbose=verbose)
        if code == 200:
            label = data.get("label", "?")
            score = data.get("score", 0)
            correct = label == "NEGATIVE"
            R.record(correct, f'"{text[:45]}…" → {label} ({score:.0%})',
                     f"expected NEGATIVE, got {label}")
        else:
            R.record(False, f'"{text[:45]}…"', f"HTTP {code}")

    print(f"\n  {DIM}Edge cases:{RESET}")
    for name, body in edge_cases:
        code, data = post(f"{base}/sentiment", body, verbose=verbose)
        if name == "Empty text":
            R.record(code == 400, f"{name} returns 400", f"got {code}")
        else:
            R.record(code in (200, 400, 422), f"{name} handled gracefully", f"got {code}")


def test_themes(base: str, verbose: bool):
    header("3 / THEMES  (GET /themes)")
    code, data = get(f"{base}/themes", verbose=verbose)
    R.record(code == 200, "GET /themes returns 200")
    themes = data.get("themes", [])
    R.record(len(themes) == 10, f"Returns 10 clusters (got {len(themes)})")
    if themes:
        t = themes[0]
        R.record("cluster_id"    in t, "cluster_id field present")
        R.record("name"          in t, "name field present")
        R.record("volume"        in t, "volume field present")
        R.record("positive_pct"  in t, "positive_pct field present")
        R.record("priority_score"in t, "priority_score field present")
        R.record("roadmap_id"    in t, "roadmap_id field present")

        # Verify volume totals make sense
        total_vol = sum(t["volume"] for t in themes)
        R.record(15000 <= total_vol <= 25000, f"Total volume {total_vol:,} is within expected range")

        if verbose:
            info("Top themes by volume:")
            for t in sorted(themes, key=lambda x: -x["volume"])[:3]:
                info(f"  Cluster {t['cluster_id']}: {t['name'][:35]} — {t['volume']:,} resp, "
                     f"{t['positive_pct']}% pos")


def test_trends(base: str, verbose: bool):
    header("4 / TRENDS  (GET /trends)")
    code, data = get(f"{base}/trends", verbose=verbose)
    R.record(code == 200, "GET /trends returns 200")
    months = data.get("months", [])
    R.record(len(months) >= 6, f"Returns at least 6 months (got {len(months)})")
    if months:
        m = months[0]
        R.record("month"   in m, "month field present")
        R.record("volumes" in m, "volumes array present")
        R.record(len(m.get("volumes", [])) == 10, "volumes has 10 entries (one per cluster)")

        # Verify no negative volumes
        all_vols = [v for month in months for v in month.get("volumes", [])]
        R.record(all(v >= 0 for v in all_vols), "All volume values are non-negative")

        if verbose:
            info(f"First month: {m['month']}  →  total = {sum(m['volumes']):,}")
            info(f"Last  month: {months[-1]['month']}  →  total = {sum(months[-1]['volumes']):,}")


def test_feedback(base: str, verbose: bool):
    header("5 / FEEDBACK  (GET /feedback/{cluster_id})")

    for cid in range(10):
        code, data = get(f"{base}/feedback/{cid}", verbose=verbose)
        R.record(code == 200, f"Cluster {cid} ({data.get('name','?')[:25]}) returns 200",
                 f"HTTP {code}")
        if code == 200:
            items = data.get("feedback", [])
            R.record(len(items) > 0, f"  Cluster {cid} has feedback items", "empty list")
            if items and verbose:
                info(f"  Cluster {cid}: {data['total']:,} total → sample: \"{items[0]['text'][:60]}…\"")

    # Sentiment filter
    code, data = get(f"{base}/feedback/1", params={"sentiment": "NEGATIVE"}, verbose=verbose)
    R.record(code == 200, "Cluster 1 filtered by NEGATIVE returns 200")
    if code == 200:
        items = data.get("feedback", [])
        all_neg = all(i["sentiment"] == "NEGATIVE" for i in items)
        R.record(all_neg, "All returned items are NEGATIVE sentiment",
                 f"{sum(1 for i in items if i['sentiment']!='NEGATIVE')} non-negative found")

    # Limit param
    code, data = get(f"{base}/feedback/0", params={"limit": 5}, verbose=verbose)
    R.record(code == 200, "limit=5 returns 200")
    if code == 200:
        R.record(len(data.get("feedback", [])) <= 5, "Respects limit=5 param")

    # Invalid cluster
    code, _ = get(f"{base}/feedback/99", verbose=verbose)
    R.record(code == 404, "Cluster 99 returns 404")


def test_roadmap(base: str, verbose: bool):
    header("6 / ROADMAP  (GET /roadmap)")
    code, data = get(f"{base}/roadmap", verbose=verbose)
    R.record(code == 200, "GET /roadmap returns 200")
    items = data.get("roadmap", [])
    R.record(len(items) == 8, f"Returns 8 initiatives (got {len(items)})")
    if items:
        i = items[0]
        R.record("roadmap_id"     in i, "roadmap_id field present")
        R.record("priority_score" in i, "priority_score field present")
        R.record("status"         in i, "status field present")

        # Verify sorted by priority descending
        scores = [x["priority_score"] for x in items]
        R.record(scores == sorted(scores, reverse=True), "Items sorted by priority desc")

        if verbose:
            info("Top 3 priority initiatives:")
            for it in items[:3]:
                info(f"  {it['roadmap_id']} — {it['theme_name'][:30]} — priority {it['priority_score']}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="PulseWear API test runner")
    parser.add_argument("--base-url", default="http://localhost:8000",
                        help="FastAPI base URL (default: http://localhost:8000)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show request details and sample data")
    parser.add_argument("--skip-sentiment", action="store_true",
                        help="Skip sentiment tests (slow, requires model download)")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    print(f"\n{BOLD}PulseWear API Test Suite{RESET}")
    print(f"{DIM}Target: {base}{RESET}")

    # Check server is up
    code, _ = get(f"{base}/", verbose=False)
    if code == 0:
        print(f"\n{RED}{BOLD}Cannot connect to {base}{RESET}")
        print(f"Start the server with:{YELLOW}  uvicorn main:app --reload --port 8000{RESET}")
        sys.exit(1)

    test_root(base, args.verbose)
    test_themes(base, args.verbose)
    test_trends(base, args.verbose)
    test_feedback(base, args.verbose)
    test_roadmap(base, args.verbose)

    if not args.skip_sentiment:
        test_sentiment(base, args.verbose)
    else:
        print(f"\n{YELLOW}  Sentiment tests skipped (--skip-sentiment){RESET}")

    success = R.summary()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
