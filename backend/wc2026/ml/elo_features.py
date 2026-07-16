"""Replay the real match history to produce (a) leakage-free training data and
(b) each team's current Elo / form / goal rates.

A World-Football-style Elo is updated after every match (importance- and
margin-weighted, with home advantage). For each match we emit a feature row
built ONLY from the pre-match state, then update — so nothing leaks.
"""
from __future__ import annotations

from collections import defaultdict, deque

import numpy as np
import pandas as pd

from .history import load_results

FEATURE_NAMES = ["elo_diff", "form_diff", "gf_diff", "ga_diff", "h2h_diff", "home_advantage"]

BASE_ELO = 1500.0
HOME_ADV_ELO = 100.0
FORM_WINDOW = 10
GF_ALPHA = 0.25
H2H_WINDOW = 5


def _importance(tournament: str) -> float:
    # World-Football-Elo-style K weights (kept moderate so ratings stay in the
    # realistic ~1400-2100 band rather than drifting high for elite teams).
    t = str(tournament).lower()
    if "friendly" in t:
        return 12.0
    if "qualification" in t:
        return 22.0
    if "fifa world cup" in t:
        return 36.0
    if any(k in t for k in ("euro", "copa", "cup of nations", "asian cup", "gold cup",
                            "nations league", "confederations")):
        return 28.0
    return 18.0


def _goal_mult(margin: int) -> float:
    if margin <= 1:
        return 1.0
    if margin == 2:
        return 1.5
    return (11 + margin) / 8.0


class _Replay:
    def __init__(self):
        self.elo = defaultdict(lambda: BASE_ELO)
        self.results = defaultdict(lambda: deque(maxlen=FORM_WINDOW))
        self.gf = defaultdict(lambda: 1.3)
        self.ga = defaultdict(lambda: 1.3)
        self.h2h = defaultdict(lambda: deque(maxlen=H2H_WINDOW))
        self.h2h_games = defaultdict(lambda: deque(maxlen=H2H_WINDOW))
        self.matches = defaultdict(int)

    def form(self, t: str) -> float:
        d = self.results[t]
        return round(sum(d) / (3 * len(d)) * 100.0, 1) if d else 55.0

    def state(self, t: str) -> dict:
        return {"elo": round(self.elo[t], 1), "form": self.form(t),
                "gf": round(self.gf[t], 2), "ga": round(self.ga[t], 2),
                "matches": self.matches[t]}

    def feature_row(self, home: str, away: str, neutral: bool) -> list[float]:
        pair = tuple(sorted((home, away)))
        h2h = self.h2h[pair]
        h2h_diff = (float(np.mean(h2h)) * (1 if home < away else -1)) if h2h else 0.0
        return [
            self.elo[home] - self.elo[away],
            self.form(home) - self.form(away),
            self.gf[home] - self.gf[away],
            self.ga[home] - self.ga[away],
            h2h_diff,
            0.0 if neutral else 1.0,
        ]

    def update(self, home, away, hs, as_, neutral, tournament, year=0):
        adv = 0.0 if neutral else HOME_ADV_ELO
        we = 1.0 / (1.0 + 10 ** (-(self.elo[home] - self.elo[away] + adv) / 400.0))
        w = 1.0 if hs > as_ else 0.5 if hs == as_ else 0.0
        k = _importance(tournament) * _goal_mult(abs(hs - as_))
        delta = k * (w - we)
        self.elo[home] += delta
        self.elo[away] -= delta
        pts_h, pts_a = (3, 0) if hs > as_ else (1, 1) if hs == as_ else (0, 3)
        self.results[home].append(pts_h)
        self.results[away].append(pts_a)
        self.gf[home] = (1 - GF_ALPHA) * self.gf[home] + GF_ALPHA * hs
        self.ga[home] = (1 - GF_ALPHA) * self.ga[home] + GF_ALPHA * as_
        self.gf[away] = (1 - GF_ALPHA) * self.gf[away] + GF_ALPHA * as_
        self.ga[away] = (1 - GF_ALPHA) * self.ga[away] + GF_ALPHA * hs
        pair = tuple(sorted((home, away)))
        self.h2h[pair].append((hs - as_) if home < away else (as_ - hs))
        self.h2h_games[pair].append((year, home, away, hs, as_))
        self.matches[home] += 1
        self.matches[away] += 1


def replay(min_year: int = 1990):
    """Return (X, y, dates, replay). Training rows use matches from `min_year`
    on (older data still warms up Elo but is noisy/low-information)."""
    df = load_results(played_only=True)
    r = _Replay()
    X, y, dates = [], [], []
    for row in df.itertuples(index=False):
        hs, as_ = int(row.home_score), int(row.away_score)
        if row.date.year >= min_year:
            X.append(r.feature_row(row.home_team, row.away_team, row.neutral))
            y.append(0 if hs > as_ else 1 if hs == as_ else 2)
            dates.append(row.date)
        r.update(row.home_team, row.away_team, hs, as_, row.neutral, row.tournament, row.date.year)
    return np.asarray(X, float), np.asarray(y, int), pd.to_datetime(dates), r


def snapshot(r: "_Replay", roster: list[str], as_of: str = "") -> dict:
    """Current per-team state, mean head-to-head, and recent H2H scorelines."""
    rs = set(roster)
    teams = {name: r.state(name) for name in roster}
    h2h, h2h_games = {}, {}
    for pair, dq in r.h2h.items():
        if pair[0] in rs and pair[1] in rs and dq:
            h2h[f"{pair[0]}|{pair[1]}"] = round(float(np.mean(dq)), 2)
            games = r.h2h_games[pair]
            h2h_games[f"{pair[0]}|{pair[1]}"] = [
                {"year": int(yr), "home": hm, "away": aw, "hs": int(hs), "as": int(as_)}
                for (yr, hm, aw, hs, as_) in games
            ]
    return {"as_of": as_of, "teams": teams, "h2h": h2h, "h2h_games": h2h_games}


def build_inference_row(a: dict, b: dict, h2h_diff: float, home_advantage: int) -> list[float]:
    """Feature row (A perspective) from two team-state dicts, matching FEATURE_NAMES."""
    return [
        a["elo"] - b["elo"],
        a["form"] - b["form"],
        a["gf"] - b["gf"],
        a["ga"] - b["ga"],
        h2h_diff,
        float(home_advantage),
    ]


if __name__ == "__main__":
    X, y, dates, r = replay()
    states = {t: r.state(t) for t in r.elo}
    print(f"training rows: {len(X):,}  ({dates.min().date()} .. {dates.max().date()})")
    top = sorted(states.items(), key=lambda kv: -kv[1]["elo"])[:12]
    print("\nCurrent Elo leaders (real history):")
    for t, s in top:
        print(f"  {t:16s} elo={s['elo']:.0f}  form={s['form']:.0f}  gf={s['gf']:.2f} ga={s['ga']:.2f}")
