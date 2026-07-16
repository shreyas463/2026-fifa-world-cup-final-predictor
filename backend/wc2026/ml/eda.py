"""Exploratory data analysis over the generated match dataset.

Prints the class balance, the correlation of each engineered feature with the
match result, and win/draw/loss rates bucketed by Elo gap — the analysis that
justifies the feature set used by the models.

Run:  python -m wc2026.ml.eda
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .dataset import build_training_data


def run_eda() -> pd.DataFrame:
    X, y, ga, gb, names = build_training_data()
    df = pd.DataFrame(X, columns=names)
    df["result"] = y  # 0 A win, 1 draw, 2 B win
    df["goals_a"] = ga
    df["goals_b"] = gb

    print("=" * 64)
    print("EXPLORATORY DATA ANALYSIS — synthetic international match history")
    print("=" * 64)
    print(f"\nMatches: {len(df):,}")

    counts = df["result"].value_counts().sort_index()
    labels = {0: "Team A win", 1: "Draw", 2: "Team B win"}
    print("\nOutcome balance:")
    for k, v in counts.items():
        print(f"  {labels[k]:12s} {v:5d}  ({v / len(df) * 100:4.1f}%)")

    print(f"\nAverage goals per team per match: {(ga.mean() + gb.mean()) / 2:.2f}")
    print(f"Home/host win rate boost (venue set): "
          f"{(df[df.home_advantage == 1].result == 0).mean() * 100:4.1f}% vs "
          f"{(df[df.home_advantage == 0].result == 0).mean() * 100:4.1f}% neutral")

    # Correlation of each feature with an A-favouring outcome score (+1 win .. -1 loss)
    outcome_score = np.where(y == 0, 1.0, np.where(y == 1, 0.0, -1.0))
    print("\nFeature correlation with match outcome (A perspective):")
    corr = {c: np.corrcoef(df[c], outcome_score)[0, 1] for c in names}
    for c, v in sorted(corr.items(), key=lambda kv: -abs(kv[1])):
        bar = "█" * int(abs(v) * 40)
        print(f"  {c:20s} {v:+.3f} {bar}")

    # Win rate by Elo-gap bucket
    print("\nTeam A win rate by Elo advantage:")
    buckets = pd.cut(df["elo_diff"], [-1000, -150, -50, 50, 150, 1000],
                     labels=["<-150", "-150..-50", "-50..50", "50..150", ">150"])
    table = df.groupby(buckets, observed=True)["result"].apply(lambda s: (s == 0).mean())
    for band, rate in table.items():
        print(f"  Elo diff {str(band):12s} -> {rate * 100:4.1f}% wins")

    print("\nInsight: Elo difference is the dominant signal, amplified by recent")
    print("form and host advantage — which is exactly what the models learn.")
    return df


if __name__ == "__main__":
    run_eda()
