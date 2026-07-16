"""Single-match prediction engine.

Combines the trained classifier (win/draw/loss) with the Poisson scoreline model
(expected goals + most-likely score) and the supporting context the frontend
shows: head-to-head, form/ranking comparison and the key factors — now including
squad availability and social-media sentiment.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np

from ..data.teams import Team
from ..ml.features import TeamStats, build_feature_row, team_experience
from .poisson import expected_goals, most_likely_score, outcome_probs

ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "artifacts"


@lru_cache(maxsize=1)
def _load_model():
    path = ARTIFACT_DIR / "model.joblib"
    return joblib.load(path) if path.exists() else None


def _stats(t: Team) -> TeamStats:
    return TeamStats(
        rating=float(t.fifa_points), form=float(t.form), attack=t.attack, defense=t.defense,
        experience=team_experience(t.wc_titles, t.wc_appearances), squad=float(t.squad_value_m),
        availability=float(t.availability), sentiment=float(t.sentiment),
    )


def _home_advantage(a: Team, b: Team, neutral: bool) -> int:
    if neutral:
        return 0
    if a.host and not b.host:
        return 1
    if b.host and not a.host:
        return -1
    return 0


def _head_to_head(a: Team, b: Team, n: int = 5) -> tuple[list[dict], float]:
    """Deterministic, reproducible synthetic H2H history keyed on the pairing.

    Returns the recent results and the mean goal difference (A perspective).
    """
    rng = np.random.default_rng(min(a.id, b.id) * 1000 + max(a.id, b.id))
    lam_a, lam_b = expected_goals(a.fifa_points, b.fifa_points, 0, a.attack, a.defense, b.attack, b.defense)
    out, diffs = [], []
    for year in (2024, 2023, 2022, 2021, 2019):
        ga, gb = int(rng.poisson(lam_a)), int(rng.poisson(lam_b))
        out.append({"year": year, "team_a": a.name, "team_b": b.name, "score_a": ga, "score_b": gb})
        diffs.append(ga - gb)
    return out, float(np.mean(diffs))


def _key_factors(a: Team, b: Team, home_adv: int) -> list[dict]:
    factors = [
        ("FIFA ranking edge", a.fifa_points - b.fifa_points,
         f"{a.name} {a.fifa_points:.0f} vs {b.name} {b.fifa_points:.0f}", 300.0),
        ("Recent form", a.form - b.form, f"form {a.form} vs {b.form}", 40.0),
        ("Attack vs defence", (a.attack - b.defense) - (b.attack - a.defense),
         "net attacking edge (xG)", 1.5),
        ("Squad availability", a.availability - b.availability,
         f"fitness {a.availability} vs {b.availability}", 15.0),
        ("Fan sentiment", a.sentiment - b.sentiment,
         f"positivity {a.sentiment:.0f} vs {b.sentiment:.0f}", 25.0),
        ("World Cup pedigree",
         team_experience(a.wc_titles, a.wc_appearances) - team_experience(b.wc_titles, b.wc_appearances),
         f"{a.wc_titles} titles / {a.wc_appearances} apps vs {b.wc_titles} / {b.wc_appearances}", 20.0),
    ]
    out = []
    for name, gap, detail, scale in factors:
        if abs(gap) < 1e-9:
            continue
        out.append({"factor": name, "favours": a.name if gap > 0 else b.name,
                    "detail": detail, "weight": round(min(1.0, abs(gap) / scale), 2)})
    if home_adv != 0:
        out.append({"factor": "Host advantage", "favours": a.name if home_adv > 0 else b.name,
                    "detail": "playing on home soil", "weight": 0.4})
    return sorted(out, key=lambda f: -f["weight"])


def predict_match(a: Team, b: Team, neutral: bool = True) -> dict:
    home_adv = _home_advantage(a, b, neutral)
    h2h_list, h2h_diff = _head_to_head(a, b)
    row = build_feature_row(_stats(a), _stats(b), home_advantage=home_adv, h2h=h2h_diff)

    bundle = _load_model()
    if bundle is not None:
        proba = bundle["model"].predict_proba([row])[0]
        p_a, p_draw, p_b = float(proba[0]), float(proba[1]), float(proba[2])
        source = bundle["name"]
    else:
        lam_a, lam_b = expected_goals(a.fifa_points, b.fifa_points, home_adv, a.attack, a.defense, b.attack, b.defense)
        p_a, p_draw, p_b = outcome_probs(lam_a, lam_b)
        source = "Poisson (untrained fallback)"

    lam_a, lam_b = expected_goals(a.fifa_points, b.fifa_points, home_adv, a.attack, a.defense, b.attack, b.defense)
    sa, sb = most_likely_score(lam_a, lam_b)

    return {
        "team_a": a.to_dict(), "team_b": b.to_dict(), "neutral_venue": neutral,
        "probabilities": {"team_a_win": round(p_a, 4), "draw": round(p_draw, 4), "team_b_win": round(p_b, 4)},
        "expected_goals": {"team_a": round(lam_a, 2), "team_b": round(lam_b, 2)},
        "predicted_score": {"team_a": sa, "team_b": sb},
        "head_to_head": h2h_list,
        "form_comparison": {"team_a": a.form, "team_b": b.form},
        "ranking_comparison": {"team_a": a.fifa_rank, "team_b": b.fifa_rank},
        "key_factors": _key_factors(a, b, home_adv),
        "model": source,
    }
