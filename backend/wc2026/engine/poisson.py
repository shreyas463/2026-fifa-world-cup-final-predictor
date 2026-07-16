"""Poisson scoreline model — turns two expected-goal rates into outcome
probabilities and a most-likely scoreline. Shared by the trainer (as a
baseline model) and the live match-prediction engine.
"""
from __future__ import annotations

import numpy as np

LEAGUE_AVG_GOALS = 1.35
GOAL_SPREAD_K = 0.55
MAX_GOALS = 10
HOME_ADV_RATING = 100.0  # Elo-point bump for the home/host side


def expected_goals(rating_a: float, rating_b: float, home_advantage: int = 0,
                   attack_a: float = LEAGUE_AVG_GOALS, defense_a: float = LEAGUE_AVG_GOALS,
                   attack_b: float = LEAGUE_AVG_GOALS, defense_b: float = LEAGUE_AVG_GOALS
                   ) -> tuple[float, float]:
    """Blend a ranking-based expectation with each side's attack/defense profile."""
    eff = (rating_a - rating_b) + 2.0 * HOME_ADV_RATING * home_advantage
    diff = eff / 400.0
    base_a = LEAGUE_AVG_GOALS * np.exp(GOAL_SPREAD_K * diff)
    base_b = LEAGUE_AVG_GOALS * np.exp(-GOAL_SPREAD_K * diff)
    # Nudge toward attack-vs-defense matchup (Dixon-Coles flavour).
    lam_a = base_a * (attack_a / LEAGUE_AVG_GOALS) ** 0.5 * (defense_b / LEAGUE_AVG_GOALS) ** 0.5
    lam_b = base_b * (attack_b / LEAGUE_AVG_GOALS) ** 0.5 * (defense_a / LEAGUE_AVG_GOALS) ** 0.5
    return float(np.clip(lam_a, 0.15, 6.0)), float(np.clip(lam_b, 0.15, 6.0))


def _poisson_pmf(lam: float, k: np.ndarray) -> np.ndarray:
    from math import lgamma
    logp = k * np.log(lam) - lam - np.array([lgamma(int(v) + 1) for v in k])
    return np.exp(logp)


def score_matrix(lam_a: float, lam_b: float) -> np.ndarray:
    ks = np.arange(0, MAX_GOALS + 1)
    pa = _poisson_pmf(lam_a, ks)
    pb = _poisson_pmf(lam_b, ks)
    return np.outer(pa, pb)


def outcome_probs(lam_a: float, lam_b: float) -> tuple[float, float, float]:
    """Return (P(A win), P(draw), P(B win))."""
    m = score_matrix(lam_a, lam_b)
    p_a = float(np.tril(m, -1).sum())   # a goals > b goals
    p_draw = float(np.trace(m))
    p_b = float(np.triu(m, 1).sum())
    total = p_a + p_draw + p_b
    return p_a / total, p_draw / total, p_b / total


def most_likely_score(lam_a: float, lam_b: float) -> tuple[int, int]:
    m = score_matrix(lam_a, lam_b)
    i, j = np.unravel_index(int(np.argmax(m)), m.shape)
    return int(i), int(j)
