"""Exploratory data analysis over the REAL international-match history.

Prints outcome balance, home advantage, feature-vs-outcome correlations and
win-rate by Elo gap — the evidence that justifies the feature set.

Run:  python -m wc2026.ml.eda
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .elo_features import FEATURE_NAMES, replay
from .history import load_results


def run_eda() -> pd.DataFrame:
    full = load_results(played_only=True)
    X, y, dates, _ = replay()
    df = pd.DataFrame(X, columns=FEATURE_NAMES)
    df["result"] = y  # 0 home win, 1 draw, 2 away win

    print("=" * 66)
    print("EXPLORATORY DATA ANALYSIS — real international results (martj42)")
    print("=" * 66)
    print(f"\nTotal internationals on record: {len(full):,} "
          f"({full.date.min().date()} .. {full.date.max().date()})")
    print(f"Training rows (1990+): {len(df):,}")

    labels = {0: "Home win", 1: "Draw", 2: "Away win"}
    print("\nOutcome balance:")
    for k, v in df["result"].value_counts().sort_index().items():
        print(f"  {labels[k]:10s} {v:6d}  ({v / len(df) * 100:4.1f}%)")

    home_games = df[df.home_advantage == 1]
    neutral = df[df.home_advantage == 0]
    print(f"\nHome win rate (home venue): {(home_games.result == 0).mean() * 100:4.1f}%")
    print(f"Home win rate (neutral):    {(neutral.result == 0).mean() * 100:4.1f}%")

    outcome_score = np.where(y == 0, 1.0, np.where(y == 1, 0.0, -1.0))
    print("\nFeature correlation with outcome (home perspective):")
    corr = {c: np.corrcoef(df[c], outcome_score)[0, 1] for c in FEATURE_NAMES}
    for c, v in sorted(corr.items(), key=lambda kv: -abs(kv[1])):
        print(f"  {c:16s} {v:+.3f} {'█' * int(abs(v) * 40)}")

    print("\nHome win rate by Elo advantage:")
    buckets = pd.cut(df["elo_diff"], [-2000, -200, -75, 75, 200, 2000],
                     labels=["<-200", "-200..-75", "-75..75", "75..200", ">200"])
    for band, rate in df.groupby(buckets, observed=True)["result"].apply(lambda s: (s == 0).mean()).items():
        print(f"  Elo diff {str(band):11s} -> {rate * 100:4.1f}% home wins")

    print("\nInsight: real Elo difference is the dominant signal, reinforced by")
    print("recent form, goal rates and a clear home-venue advantage.")
    return df


if __name__ == "__main__":
    run_eda()
