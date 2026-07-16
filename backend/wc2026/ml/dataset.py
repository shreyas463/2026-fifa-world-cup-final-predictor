"""Reproducible, leakage-free synthetic match history for model training.

We simulate a long timeline of international matches. Each match outcome is
drawn from teams' *latent* strengths, while the feature row is built only from
each team's *rolling, pre-match* statistics (Elo, form, goal rates) that were
knowable before kickoff. Because rolling stats are updated only after the
result is generated, no post-match information ever leaks into the features.
"""
from __future__ import annotations

import numpy as np

from ..data.teams import load_teams
from .features import FEATURE_NAMES, TeamStats, build_feature_row, HOME_ADV_ELO

LEAGUE_AVG_GOALS = 1.35
GOAL_SPREAD_K = 0.55   # how sharply Elo gap maps onto expected goals
ELO_K = 24.0           # Elo update factor
FORM_WINDOW = 10


class _RollingTeam:
    def __init__(self, true_elo: float):
        self.true_elo = true_elo
        # Observed Elo starts near the truth but is noisy, so features are imperfect.
        self.elo = true_elo
        self.results: list[int] = []      # points from last matches (3/1/0)
        self.gf = LEAGUE_AVG_GOALS        # EMA goals for
        self.ga = LEAGUE_AVG_GOALS        # EMA goals against

    @property
    def form(self) -> float:
        if not self.results:
            return 60.0
        ppg = sum(self.results) / len(self.results)
        return round(ppg / 3.0 * 100.0, 1)

    def stats(self) -> TeamStats:
        return TeamStats(elo=self.elo, form=self.form, attack=self.gf, defense=self.ga)

    def update(self, gf: int, ga: int, points: int):
        self.results.append(points)
        if len(self.results) > FORM_WINDOW:
            self.results.pop(0)
        self.gf = 0.75 * self.gf + 0.25 * gf
        self.ga = 0.75 * self.ga + 0.25 * ga


def _expected_goals(elo_a: float, elo_b: float) -> tuple[float, float]:
    diff = (elo_a - elo_b) / 400.0
    lam_a = LEAGUE_AVG_GOALS * np.exp(GOAL_SPREAD_K * diff)
    lam_b = LEAGUE_AVG_GOALS * np.exp(-GOAL_SPREAD_K * diff)
    return lam_a, lam_b


def build_training_data(rounds: int = 140, seed: int = 42):
    """Return (X, y, goals_a, goals_b, feature_names).

    y: 0 = A win, 1 = draw, 2 = B win (from A's perspective).
    """
    rng = np.random.default_rng(seed)
    teams = load_teams()
    roll = {t.id: _RollingTeam(float(t.elo) + rng.normal(0, 25)) for t in teams}
    ids = [t.id for t in teams]

    X, y, ga_list, gb_list = [], [], [], []

    for _ in range(rounds):
        rng.shuffle(ids)
        for i in range(0, len(ids) - 1, 2):
            ta, tb = roll[ids[i]], roll[ids[i + 1]]
            # Randomly assign venue: home A, home B, or neutral.
            venue = rng.integers(-1, 2)  # -1 B home, 0 neutral, 1 A home
            adv = HOME_ADV_ELO * venue

            lam_a, lam_b = _expected_goals(ta.true_elo + adv, tb.true_elo - adv)
            gf_a = int(rng.poisson(lam_a))
            gf_b = int(rng.poisson(lam_b))

            # Feature row is built from PRE-match rolling stats only.
            row = build_feature_row(ta.stats(), tb.stats(), home_advantage=int(venue))
            X.append(row)
            if gf_a > gf_b:
                label, pa, pb = 0, 3, 0
            elif gf_a == gf_b:
                label, pa, pb = 1, 1, 1
            else:
                label, pa, pb = 2, 0, 3
            y.append(label)
            ga_list.append(gf_a)
            gb_list.append(gf_b)

            # Update observed Elo and rolling stats AFTER recording features.
            exp_a = 1.0 / (1.0 + 10 ** ((tb.elo - ta.elo) / 400.0))
            score_a = 1.0 if label == 0 else (0.5 if label == 1 else 0.0)
            ta.elo += ELO_K * (score_a - exp_a)
            tb.elo += ELO_K * ((1 - score_a) - (1 - exp_a))
            ta.update(gf_a, gf_b, pa)
            tb.update(gf_b, gf_a, pb)

    return (
        np.asarray(X, dtype=float),
        np.asarray(y, dtype=int),
        np.asarray(ga_list, dtype=int),
        np.asarray(gb_list, dtype=int),
        list(FEATURE_NAMES),
    )
