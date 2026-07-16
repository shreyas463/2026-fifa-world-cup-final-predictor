"""Reproducible, leakage-free synthetic match history for model training.

Match outcomes are sampled from each team's *latent* strength — a blend of real
FIFA ranking points, squad availability, fan sentiment and World Cup pedigree —
while feature rows are built only from *rolling, pre-match* statistics (observed
rating, form, goal rates, head-to-head). Rolling stats update only after the
result is generated, so no post-match information leaks into the features.
"""
from __future__ import annotations

import numpy as np

from ..data.teams import load_teams
from .features import (
    FEATURE_NAMES,
    HOME_ADV_RATING,
    TeamStats,
    build_feature_row,
    team_experience,
)

LEAGUE_AVG_GOALS = 1.35
GOAL_SPREAD_K = 0.55
RATING_K = 24.0
FORM_WINDOW = 10
H2H_WINDOW = 5


class _RollingTeam:
    def __init__(self, t):
        # Static, real attributes (fixed across the timeline)
        self.experience = team_experience(t.wc_titles, t.wc_appearances)
        self.squad = float(t.squad_value_m)
        self.availability = float(t.availability)
        self.sentiment = float(t.sentiment)
        # Latent "true" strength drives outcomes; observed rating is noisy.
        self.latent = (
            float(t.fifa_points)
            + 2.5 * (self.availability - 88)
            + 1.2 * (self.sentiment - 63)
            + 0.4 * (self.experience - 10)
        )
        self.rating = float(t.fifa_points)  # observed, updated after each match
        self.results: list[int] = []
        self.gf = t.attack
        self.ga = t.defense

    @property
    def form(self) -> float:
        if not self.results:
            return 60.0
        return round(sum(self.results) / len(self.results) / 3.0 * 100.0, 1)

    def stats(self) -> TeamStats:
        return TeamStats(
            rating=self.rating, form=self.form, attack=self.gf, defense=self.ga,
            experience=self.experience, squad=self.squad,
            availability=self.availability, sentiment=self.sentiment,
        )

    def update(self, gf: int, ga: int, points: int):
        self.results.append(points)
        if len(self.results) > FORM_WINDOW:
            self.results.pop(0)
        self.gf = 0.75 * self.gf + 0.25 * gf
        self.ga = 0.75 * self.ga + 0.25 * ga


def _expected_goals(r_a: float, r_b: float) -> tuple[float, float]:
    diff = (r_a - r_b) / 400.0
    return (LEAGUE_AVG_GOALS * np.exp(GOAL_SPREAD_K * diff),
            LEAGUE_AVG_GOALS * np.exp(-GOAL_SPREAD_K * diff))


def build_training_data(rounds: int = 160, seed: int = 42):
    """Return (X, y, goals_a, goals_b, feature_names).

    y: 0 = A win, 1 = draw, 2 = B win (from A's perspective).
    """
    rng = np.random.default_rng(seed)
    teams = load_teams()
    roll = {t.id: _RollingTeam(t) for t in teams}
    for rt, t in zip(roll.values(), teams):
        rt.rating = float(t.fifa_points) + rng.normal(0, 25)
    ids = [t.id for t in teams]
    h2h: dict[tuple[int, int], list[int]] = {}

    X, y, ga_list, gb_list = [], [], [], []

    for _ in range(rounds):
        rng.shuffle(ids)
        for i in range(0, len(ids) - 1, 2):
            ida, idb = ids[i], ids[i + 1]
            ta, tb = roll[ida], roll[idb]
            venue = int(rng.integers(-1, 2))  # -1 B home, 0 neutral, 1 A home
            adv = HOME_ADV_RATING * venue

            lam_a, lam_b = _expected_goals(ta.latent + adv, tb.latent - adv)
            gf_a, gf_b = int(rng.poisson(lam_a)), int(rng.poisson(lam_b))

            # Head-to-head goal diff (A perspective) from PRIOR meetings only.
            key = (min(ida, idb), max(ida, idb))
            prev = h2h.get(key, [])
            sign = 1 if ida < idb else -1
            h2h_diff = float(np.mean(prev)) * sign if prev else 0.0

            row = build_feature_row(ta.stats(), tb.stats(), home_advantage=venue, h2h=h2h_diff)
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

            # Update observed rating, rolling form/goals and H2H AFTER recording features.
            exp_a = 1.0 / (1.0 + 10 ** ((tb.rating - ta.rating) / 400.0))
            score_a = 1.0 if label == 0 else (0.5 if label == 1 else 0.0)
            ta.rating += RATING_K * (score_a - exp_a)
            tb.rating += RATING_K * ((1 - score_a) - (1 - exp_a))
            ta.update(gf_a, gf_b, pa)
            tb.update(gf_b, gf_a, pb)
            store = h2h.setdefault(key, [])
            store.append((gf_a - gf_b) * sign)  # stored in low-id perspective
            if len(store) > H2H_WINDOW:
                store.pop(0)

    return (np.asarray(X, float), np.asarray(y, int),
            np.asarray(ga_list, int), np.asarray(gb_list, int), list(FEATURE_NAMES))
