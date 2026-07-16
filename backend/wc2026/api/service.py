"""Application service layer.

Loads teams, model metrics, a canonical Monte Carlo run, the authored bracket
and fan-sentiment once, caches them, and enriches teams with tournament
probabilities, radar attributes, strengths/weaknesses and sentiment.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from ..data.sentiment import get_provider
from ..data.teams import Team, groups_map, load_teams
from ..engine.bracket import authored_bracket
from ..engine.simulate import run_monte_carlo

ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "artifacts"
CANONICAL_SIMS = 5000

ATTRIBUTE_LABELS = {
    "attacking": "Attacking threat",
    "defending": "Defensive solidity",
    "form": "Recent form",
    "experience": "Tournament experience",
    "squad": "Squad quality",
    "pedigree": "FIFA ranking",
    "sentiment": "Fan sentiment",
}


def _percentile(values: dict[int, float], higher_is_better: bool = True) -> dict[int, float]:
    order = sorted(values.items(), key=lambda kv: kv[1], reverse=higher_is_better)
    n = len(order)
    return {tid: round(100.0 * (n - 1 - rank) / (n - 1), 1) for rank, (tid, _) in enumerate(order)}


class State:
    def __init__(self) -> None:
        self.teams: list[Team] = load_teams()
        self.by_id: dict[int, Team] = {t.id: t for t in self.teams}
        self.metrics = self._load_metrics()
        self.mc = run_monte_carlo(n=CANONICAL_SIMS, teams=self.teams)["probabilities"]
        self.bracket = authored_bracket(self.teams)
        self.sentiment = get_provider().all()
        self._attr_scores = self._build_attribute_scores()

    def _load_metrics(self) -> dict:
        path = ARTIFACT_DIR / "metrics.json"
        if path.exists():
            return json.loads(path.read_text())
        return {"best_model": "untrained", "metrics": {}, "model_comparison": {},
                "note": "Run `python -m wc2026.ml.train` to generate model metrics."}

    def _build_attribute_scores(self) -> dict[int, dict[str, float]]:
        p_attack = _percentile({t.id: t.attack for t in self.teams}, True)
        p_defense = _percentile({t.id: t.defense for t in self.teams}, False)  # lower is better
        p_form = _percentile({t.id: float(t.form) for t in self.teams}, True)
        p_exp = _percentile({t.id: t.wc_appearances + t.wc_titles * 3 for t in self.teams}, True)
        p_squad = _percentile({t.id: float(t.squad_value_m) for t in self.teams}, True)
        p_ped = _percentile({t.id: float(t.fifa_points) for t in self.teams}, True)
        p_sent = _percentile({t.id: float(t.sentiment) for t in self.teams}, True)
        return {t.id: {"attacking": p_attack[t.id], "defending": p_defense[t.id],
                       "form": p_form[t.id], "experience": p_exp[t.id], "squad": p_squad[t.id],
                       "pedigree": p_ped[t.id], "sentiment": p_sent[t.id]} for t in self.teams}

    def attributes(self, tid: int) -> dict[str, float]:
        return self._attr_scores[tid]

    def strengths_weaknesses(self, tid: int) -> tuple[list[str], list[str]]:
        ranked = sorted(self._attr_scores[tid].items(), key=lambda kv: -kv[1])
        strengths = [ATTRIBUTE_LABELS[k] for k, v in ranked if v >= 60][:3]
        weaknesses = [ATTRIBUTE_LABELS[k] for k, v in reversed(ranked) if v <= 45][:2]
        return (strengths or [ATTRIBUTE_LABELS[ranked[0][0]]],
                weaknesses or [ATTRIBUTE_LABELS[ranked[-1][0]]])

    def sentiment_of(self, name: str) -> dict:
        s = self.sentiment.get(name)
        return s.to_dict() if s else {"team": name, "positivity": 60, "buzz": 35,
                                      "trend": 0, "sample_posts": 0, "mood": "cautious", "momentum": "steady"}

    def team_summary(self, t: Team) -> dict:
        p = self.mc[t.id]
        return {**t.to_dict(), "probabilities": p, "win_probability": p["winner"],
                "sentiment_detail": self.sentiment_of(t.name)}

    def team_detail(self, t: Team) -> dict:
        strengths, weaknesses = self.strengths_weaknesses(t.id)
        return {**t.to_dict(), "probabilities": self.mc[t.id], "attributes": self.attributes(t.id),
                "attribute_labels": ATTRIBUTE_LABELS, "strengths": strengths, "weaknesses": weaknesses,
                "sentiment_detail": self.sentiment_of(t.name)}

    def leaderboard(self) -> list[dict]:
        rows = sorted((self.team_summary(t) for t in self.teams), key=lambda r: -r["win_probability"])
        for rank, r in enumerate(rows, start=1):
            r["rank"] = rank
        return rows

    def sentiment_table(self) -> list[dict]:
        rows = []
        for t in self.teams:
            s = self.sentiment_of(t.name)
            rows.append({"id": t.id, "name": t.name, "flag": t.flag, "group": t.group,
                         "win_probability": self.mc[t.id]["winner"], **s})
        rows.sort(key=lambda r: -r["buzz"])
        return rows

    def groups(self) -> dict[str, list[dict]]:
        return {g: [self.team_summary(t) for t in m] for g, m in groups_map(self.teams).items()}


@lru_cache(maxsize=1)
def get_state() -> State:
    return State()
