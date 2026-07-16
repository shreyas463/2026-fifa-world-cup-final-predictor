"""Single-match prediction engine.

Uses the classifier trained on real historical results (features: real Elo,
form, goal rates, head-to-head, home advantage). Injuries/availability and fan
sentiment — which aren't in the historical record — are applied as a small,
documented adjustment to each side's effective Elo so the model still "considers"
them, exactly as requested. A Poisson model supplies expected goals + scoreline.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np

from ..data.teams import Team, head_to_head_diff, head_to_head_games
from ..ml.elo_features import build_inference_row
from .poisson import expected_goals, most_likely_score, outcome_probs

ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "artifacts"

# Current-context adjustments (Elo points) for signals absent from match history.
# Deliberately small — these are nuance nudges, not primary drivers.
AVAIL_W = 2.0    # per point of squad availability above/below 90 (injuries)
SENT_W = 0.5     # per point of fan sentiment above/below 63


@lru_cache(maxsize=1)
def _load_model():
    path = ARTIFACT_DIR / "model.joblib"
    return joblib.load(path) if path.exists() else None


def effective_elo(t: Team) -> float:
    """Real Elo nudged by current injuries/availability and fan sentiment."""
    return t.elo + AVAIL_W * (t.availability - 90) + SENT_W * (t.sentiment - 63)


def _home_advantage(a: Team, b: Team, neutral: bool) -> int:
    if neutral:
        return 0
    if a.host and not b.host:
        return 1
    if b.host and not a.host:
        return -1
    return 0


def _state(t: Team) -> dict:
    return {"elo": effective_elo(t), "form": float(t.form), "gf": t.attack, "ga": t.defense}


def _key_factors(a: Team, b: Team, home_adv: int) -> list[dict]:
    factors = [
        ("Elo rating edge", a.elo - b.elo, f"{a.name} {a.elo:.0f} vs {b.name} {b.elo:.0f}", 250.0),
        ("Recent form", a.form - b.form, f"form {a.form} vs {b.form}", 40.0),
        ("Goal-scoring rate", a.attack - b.attack, f"{a.attack:.2f} vs {b.attack:.2f} per game", 1.2),
        ("Head-to-head", head_to_head_diff(a.name, b.name), "recent meetings goal diff", 2.0),
        ("Squad availability", a.availability - b.availability, f"fitness {a.availability} vs {b.availability}", 15.0),
        ("Fan sentiment", a.sentiment - b.sentiment, f"positivity {a.sentiment:.0f} vs {b.sentiment:.0f}", 25.0),
    ]
    out = []
    for name, gap, detail, scale in factors:
        if abs(gap) < 1e-9:
            continue
        out.append({"factor": name, "favours": a.name if gap > 0 else b.name,
                    "detail": detail, "weight": round(min(1.0, abs(gap) / scale), 2)})
    if home_adv:
        out.append({"factor": "Host advantage", "favours": a.name if home_adv > 0 else b.name,
                    "detail": "playing on home soil", "weight": 0.4})
    return sorted(out, key=lambda f: -f["weight"])


def predict_match(a: Team, b: Team, neutral: bool = True) -> dict:
    home_adv = _home_advantage(a, b, neutral)
    h2h_diff = head_to_head_diff(a.name, b.name)
    row = build_inference_row(_state(a), _state(b), h2h_diff, home_adv)

    bundle = _load_model()
    ea, eb = effective_elo(a), effective_elo(b)
    if bundle is not None:
        proba = bundle["model"].predict_proba([row])[0]
        p_a, p_draw, p_b = float(proba[0]), float(proba[1]), float(proba[2])
        source = f"{bundle['name']} (trained on real internationals)"
    else:
        lam_a, lam_b = expected_goals(ea, eb, home_adv, a.attack, a.defense, b.attack, b.defense)
        p_a, p_draw, p_b = outcome_probs(lam_a, lam_b)
        source = "Poisson (untrained fallback)"

    lam_a, lam_b = expected_goals(ea, eb, home_adv, a.attack, a.defense, b.attack, b.defense)
    sa, sb = most_likely_score(lam_a, lam_b)

    h2h_games = head_to_head_games(a.name, b.name)
    return {
        "team_a": a.to_dict(), "team_b": b.to_dict(), "neutral_venue": neutral,
        "probabilities": {"team_a_win": round(p_a, 4), "draw": round(p_draw, 4), "team_b_win": round(p_b, 4)},
        "expected_goals": {"team_a": round(lam_a, 2), "team_b": round(lam_b, 2)},
        "predicted_score": {"team_a": sa, "team_b": sb},
        "head_to_head": h2h_games,
        "head_to_head_note": "Real past meetings" if h2h_games else "No recent meetings on record",
        "form_comparison": {"team_a": a.form, "team_b": b.form},
        "ranking_comparison": {"team_a": a.fifa_rank, "team_b": b.fifa_rank},
        "key_factors": _key_factors(a, b, home_adv),
        "model": source,
    }
