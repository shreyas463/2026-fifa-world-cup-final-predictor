"""Load and normalise the real international-match history.

Data: martj42/international_results (results.csv + shootouts.csv), ~49k matches
from 1872 to date. Cloned into backend/data_raw/ (see README). If the raw data
is absent, callers fall back to cached artifacts.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data_raw"
RESULTS = DATA_DIR / "results.csv"
SHOOTOUTS = DATA_DIR / "shootouts.csv"

# Dataset spelling -> the roster spelling used in data/teams.py.
DATASET_TO_ROSTER = {
    "United States": "USA",
    "Curaçao": "Curacao",
}
# roster spelling -> dataset spelling (for look-ups)
ROSTER_TO_DATASET = {v: k for k, v in DATASET_TO_ROSTER.items()}


def has_data() -> bool:
    return RESULTS.exists()


def _normalise(name: str) -> str:
    return DATASET_TO_ROSTER.get(name, name)


def load_results(played_only: bool = True) -> pd.DataFrame:
    """Return the match history with normalised names and outcome labels."""
    df = pd.read_csv(RESULTS, parse_dates=["date"])
    df["home_team"] = df["home_team"].map(_normalise)
    df["away_team"] = df["away_team"].map(_normalise)
    df["neutral"] = df["neutral"].astype(str).str.upper().eq("TRUE")
    if played_only:
        df = df.dropna(subset=["home_score", "away_score"]).copy()
    df["home_score"] = pd.to_numeric(df["home_score"], errors="coerce")
    df["away_score"] = pd.to_numeric(df["away_score"], errors="coerce")
    df = df.sort_values("date").reset_index(drop=True)
    return df


def load_shootouts() -> dict[tuple, str]:
    """Map (date, {teams}) -> penalty-shootout winner (roster spelling)."""
    if not SHOOTOUTS.exists():
        return {}
    s = pd.read_csv(SHOOTOUTS, parse_dates=["date"])
    out = {}
    for _, r in s.iterrows():
        key = (r["date"].date(), frozenset({_normalise(r["home_team"]), _normalise(r["away_team"])}))
        out[key] = _normalise(r["winner"])
    return out
