"""Application service layer.

Loads the team data, the trained-model metrics and a canonical Monte Carlo run
once, caches them, and enriches teams with tournament probabilities, radar-chart
attributes and human-readable strengths / weaknesses for the API responses.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from ..data.teams import Team, groups_map, load_teams
from ..engine.simulate import predicted_bracket, run_monte_carlo

ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "artifacts"
CANONICAL_SIMS = 5000

# Radar / comparison attributes, each normalised to 0-100 across the field.
ATTRIBUTE_LABELS = {
    "attacking": "Attacking threat",
    "defending": "Defensive solidity",
    "form": "Recent form",
    "experience": "Tournament experience",
    "squad": "Squad quality",
    "pedigree": "Elo / world ranking",
}


def _percentile(values: dict[int, float], higher_is_better: bool = True) -> dict[int, float]:
    order = sorted(values.items(), key=lambda kv: kv[1], reverse=higher_is_better)
    n = len(order)
    out = {}
    for rank, (tid, _) in enumerate(order):
        out[tid] = round(100.0 * (n - 1 - rank) / (n - 1), 1)
    return out


class State:
    def __init__(self) -> None:
        self.teams: list[Team] = load_teams()
        self.by_id: dict[int, Team] = {t.id: t for t in self.teams}
        self.metrics = self._load_metrics()
        self.mc = run_monte_carlo(n=CANONICAL_SIMS, teams=self.teams)["probabilities"]
        self.bracket = predicted_bracket(self.teams)
        self._attr_scores = self._build_attribute_scores()

    def _load_metrics(self) -> dict:
        path = ARTIFACT_DIR / "metrics.json"
        if path.exists():
            return json.loads(path.read_text())
        return {"best_model": "untrained", "metrics": {}, "model_comparison": {},
                "note": "Run `python -m wc2026.ml.train` to generate model metrics."}

    def _build_attribute_scores(self) -> dict[int, dict[str, float]]:
        attack = {t.id: t.attack for t in self.teams}
        defense = {t.id: t.defense for t in self.teams}  # lower is better
        form = {t.id: float(t.form) for t in self.teams}
        experience = {t.id: t.wc_appearances + t.wc_titles * 3 for t in self.teams}
        squad = {t.id: float(t.squad_value_m) for t in self.teams}
        pedigree = {t.id: float(t.elo) for t in self.teams}

        p_attack = _percentile(attack, True)
        p_defense = _percentile(defense, False)
        p_form = _percentile(form, True)
        p_exp = _percentile(experience, True)
        p_squad = _percentile(squad, True)
        p_ped = _percentile(pedigree, True)

        scores = {}
        for t in self.teams:
            scores[t.id] = {
                "attacking": p_attack[t.id],
                "defending": p_defense[t.id],
                "form": p_form[t.id],
                "experience": p_exp[t.id],
                "squad": p_squad[t.id],
                "pedigree": p_ped[t.id],
            }
        return scores

    def attributes(self, tid: int) -> dict[str, float]:
        return self._attr_scores[tid]

    def strengths_weaknesses(self, tid: int) -> tuple[list[str], list[str]]:
        scores = self._attr_scores[tid]
        ranked = sorted(scores.items(), key=lambda kv: -kv[1])
        strengths = [ATTRIBUTE_LABELS[k] for k, v in ranked if v >= 60][:3]
        weaknesses = [ATTRIBUTE_LABELS[k] for k, v in reversed(ranked) if v <= 45][:2]
        if not strengths:
            strengths = [ATTRIBUTE_LABELS[ranked[0][0]]]
        if not weaknesses:
            weaknesses = [ATTRIBUTE_LABELS[ranked[-1][0]]]
        return strengths, weaknesses

    def team_summary(self, t: Team) -> dict:
        p = self.mc[t.id]
        return {
            **t.to_dict(),
            "probabilities": p,
            "win_probability": p["winner"],
        }

    def team_detail(self, t: Team) -> dict:
        strengths, weaknesses = self.strengths_weaknesses(t.id)
        return {
            **t.to_dict(),
            "probabilities": self.mc[t.id],
            "attributes": self.attributes(t.id),
            "attribute_labels": ATTRIBUTE_LABELS,
            "strengths": strengths,
            "weaknesses": weaknesses,
        }

    def leaderboard(self) -> list[dict]:
        rows = [self.team_summary(t) for t in self.teams]
        rows.sort(key=lambda r: -r["win_probability"])
        for rank, r in enumerate(rows, start=1):
            r["rank"] = rank
        return rows

    def groups(self) -> dict[str, list[dict]]:
        gm = groups_map(self.teams)
        return {g: [self.team_summary(t) for t in members] for g, members in gm.items()}


@lru_cache(maxsize=1)
def get_state() -> State:
    return State()
