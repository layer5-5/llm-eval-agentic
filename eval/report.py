#!/usr/bin/env python3
"""Generate aggregate report from all eval JSON logs."""

import json
import os
import sys
from collections import defaultdict


def load_runs(log_dir: str) -> list[dict]:
    """Load all JSON run files from the log directory."""
    runs = []
    for fname in os.listdir(log_dir):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(log_dir, fname)
        try:
            with open(path) as f:
                data = json.load(f)
            # Must have required fields
            if "model" in data and "mode" in data and "total_tokens" in data:
                data["_file"] = fname
                runs.append(data)
        except (json.JSONDecodeError, KeyError):
            continue
    return runs


def model_label(model: str) -> str:
    """Extract a short label from a model name like openrouter/google/gemini-2.5-flash."""
    # Strip openrouter/ prefix and provider, keep the model name
    parts = model.split("/")
    return parts[-1] if parts else model


def pretty_label(label: str) -> str:
    """Make model labels more readable."""
    return label.replace("-", " ").replace("_", " ").title()


def generate_report(log_dir: str):
    runs = load_runs(log_dir)
    if not runs:
        print("No eval runs found.")
        return

    # Group by (model, mode)
    grouped = defaultdict(list)
    for r in runs:
        label = r.get("label", model_label(r["model"]))
        grouped[(label, r["mode"])].append(r)

    # Collect all labels and modes
    all_labels = sorted(set(label for label, _ in grouped))
    modes = ["bash", "mcp"]

    # Print header
    print()
    print("=" * 100)
    print("  EVALUATION REPORT")
    print("=" * 100)
    print()

    # Per-mode table
    header = (
        f"  {'Model':<28} {'Mode':<6} {'Runs':>4} {'Wins':>4} {'Win%':>5}"
        f" {'Avg Tok':>8} {'Min Tok':>8} {'Max Tok':>8} {'Avg Turns':>10}"
    )
    print(header)
    print("  " + "-" * (len(header) - 2))

    for label in all_labels:
        for mode in modes:
            key = (label, mode)
            if key not in grouped:
                continue
            entries = grouped[key]
            n = len(entries)
            wins = sum(1 for e in entries if e["won"])
            win_pct = (wins / n * 100) if n else 0
            tokens = [e["total_tokens"] for e in entries]
            avg_tok = sum(tokens) / n
            min_tok = min(tokens)
            max_tok = max(tokens)
            turns = [e["turns"] for e in entries]
            avg_turns = sum(turns) / n

            print(
                f"  {label:<28} {mode:<6} {n:>4} {wins:>4} {win_pct:>4.0f}%"
                f" {avg_tok:>8.0f} {min_tok:>8} {max_tok:>8} {avg_turns:>10.1f}"
            )
        print()

    # Summary stats
    total_runs = len(runs)
    total_wins = sum(1 for r in runs if r["won"])
    total_tokens = sum(r["total_tokens"] for r in runs)
    print("  " + "-" * (len(header) - 2))
    print(f"  Total runs: {total_runs}   Total wins: {total_wins}   Total tokens: {total_tokens:,}")

    # Leaderboard: best avg tokens among winners only
    print()
    print("  LEADERBOARD (avg tokens to win, winners only)")
    print("  " + "-" * 50)

    leaderboard = []
    for (label, mode), entries in grouped.items():
        winners = [e for e in entries if e["won"]]
        if not winners:
            continue
        avg = sum(e["total_tokens"] for e in winners) / len(winners)
        leaderboard.append((avg, label, mode, len(winners)))

    leaderboard.sort()
    for i, (avg, label, mode, n) in enumerate(leaderboard, 1):
        print(f"  {i}. {label:<28} {mode:<6} {avg:>8.0f} avg tokens  ({n} wins)")

    print()


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(script_dir, "logs")

    if not os.path.isdir(log_dir):
        print(f"ERROR: Log directory not found: {log_dir}")
        sys.exit(1)

    generate_report(log_dir)


if __name__ == "__main__":
    main()
