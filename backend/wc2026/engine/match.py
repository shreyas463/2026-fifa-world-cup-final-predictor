"""Single-match prediction engine.

Combines the trained classifier (win/draw/loss probabilities) with the Poisson
scoreline model (expected goals + most-likely score) and produces the
supporting context the frontend shows: head-to-head, form/ranking comparison
and the key factors driving the prediction.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np

from ..data.teams import Team
from ..ml.features import TeamStats, build_feature_row
from .poisson import expected_goals, most_likely_score, outcome_probs

ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "artifacts"


@lru_cache(maxsize=1)
def _load_model():
    path = ARTIFACT_DIR / "model.joblib"
    if not path.exists():
        return None
    return joblib.load(path)


def _stats(t: Team) -> TeamStats:
    return TeamStats(elo=float(t.elo), form=float(t.form), attack=t.attack, defense=t.defense)


def _home_advantage(a: Team, b: Team, neutral: bool) -> int:
    if neutral:
        return 0
    if a.host and not b.host:
        return 1
    if b.host and not a.host:
        return -1
    return 0


def _head_to_head(a: Team, b: Team, n: int = 5) -> list[dict]:
    """Deterministic, reproducible synthetic H2H history keyed on the pairing."""
    seed = (min(a.id, b.id) * 1000 + max(a.id, b.id))
    rng = np.random.default_rng(seed)
    lam_a, lam_b = expected_goals(a.elo, b.elo, 0, a.attack, a.defense, b.attack, b.defense)
    out = []
    years = [2024, 2023, 2022, 2021, 2019]
    for i in range(n):
        ga, gb = int(rng.poisson(lam_a)), int(rng.poisson(lam_b))
        out.append({"year": years[i], "team_a": a.name, "team_b": b.name,
                    "score_a": ga, "score_b": gb})
    return out


def _key_factors(a: Team, b: Team, home_adv: int) -> list[dict]:
    factors = []
    elo_gap = a.elo - b.elo
    factors.append({
        "factor": "Elo rating edge",
        "favours": a.name if elo_gap >= 0 else b.name,
        "detail": f"{a.name} {a.elo} vs {b.name} {b.elo} ({elo_gap:+d})",
        "weight": round(min(1.0, abs(elo_gap) / 300.0), 2),
    })
    form_gap = a.form - b.form
    factors.append({
        "factor": "Recent form",
        "favours": a.name if form_gap >= 0 else b.name,
        "detail": f"{a.name} {a.form} vs {b.name} {b.form} ({form_gap:+.0f})",
        "weight": round(min(1.0, abs(form_gap) / 40.0), 2),
    })
    atk_gap = (a.attack - b.defense) - (b.attack - a.defense)
    factors.append({
        "factor": "Attack vs defence matchup",
        "favours": a.name if atk_gap >= 0 else b.name,
        "detail": f"net attacking edge {atk_gap:+.2f} xG",
        "weight": round(min(1.0, abs(atk_gap) / 1.5), 2),
    })
    if home_adv != 0:
        factors.append({
            "factor": "Host advantage",
            "favours": a.name if home_adv > 0 else b.name,
            "detail": "playing on home soil",
            "weight": 0.4,
        })
    return sorted(factors, key=lambda f: -f["weight"])


def predict_match(a: Team, b: Team, neutral: bool = True) -> dict:
    home_adv = _home_advantage(a, b, neutral)
    row = build_feature_row(_stats(a), _stats(b), home_advantage=home_adv)

    bundle = _load_model()
    if bundle is not None:
        proba = bundle["model"].predict_proba([row])[0]
        p_a, p_draw, p_b = float(proba[0]), float(proba[1]), float(proba[2])
        source = bundle["name"]
    else:  # graceful fallback if the model has not been trained yet
        lam_a, lam_b = expected_goals(a.elo, b.elo, home_adv, a.attack, a.defense, b.attack, b.defense)
        p_a, p_draw, p_b = outcome_probs(lam_a, lam_b)
        source = "Poisson (untrained fallback)"

    lam_a, lam_b = expected_goals(a.elo, b.elo, home_adv, a.attack, a.defense, b.attack, b.defense)
    sa, sb = most_likely_score(lam_a, lam_b)

    return {
        "team_a": a.to_dict(),
        "team_b": b.to_dict(),
        "neutral_venue": neutral,
        "probabilities": {
            "team_a_win": round(p_a, 4),
            "draw": round(p_draw, 4),
            "team_b_win": round(p_b, 4),
        },
        "expected_goals": {"team_a": round(lam_a, 2), "team_b": round(lam_b, 2)},
        "predicted_score": {"team_a": sa, "team_b": sb},
        "head_to_head": _head_to_head(a, b),
        "form_comparison": {"team_a": a.form, "team_b": b.form},
        "ranking_comparison": {"team_a": a.fifa_rank, "team_b": b.fifa_rank},
        "key_factors": _key_factors(a, b, home_adv),
        "model": source,
    }
