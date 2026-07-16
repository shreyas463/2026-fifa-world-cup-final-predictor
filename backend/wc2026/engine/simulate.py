"""Monte Carlo simulation of the 48-team 2026 World Cup.

Format: 12 groups of 4 (round-robin) -> top 2 + 8 best third-placed -> single-
elimination R32 -> R16 -> QF -> SF -> Final (penalty tiebreak). Used for the
Simulator page's random runs and for the stage-probability leaderboard.

(The official Bracket page uses the authored, deterministic bracket in
`engine.bracket`, not these random realisations.)
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..data.teams import Team, groups_map, load_teams

STAGES = ["r32", "r16", "qf", "sf", "final", "winner"]
KO_ROUND_NAMES = ["Round of 32", "Round of 16", "Quarterfinals", "Semifinals", "Final"]

LEAGUE_AVG_GOALS = 1.35
GOAL_SPREAD_K = 0.55
HOME_ADV = 65.0


@dataclass
class _T:
    id: int
    rating: float
    attack: float
    defense: float
    host: bool


def _index(teams: list[Team]) -> dict[int, _T]:
    return {t.id: _T(t.id, float(t.fifa_points), t.attack, t.defense, t.host) for t in teams}


def _standard_bracket(n: int) -> list[int]:
    order, m = [0], 1
    while m < n:
        m *= 2
        order = [x for pair in ((s, m - 1 - s) for s in order) for x in pair]
    return order


def _sim_goals(rng, a: _T, b: _T, home_adv: int) -> tuple[int, int]:
    diff = ((a.rating - b.rating) + 2.0 * HOME_ADV * home_adv) / 400.0
    lam_a = LEAGUE_AVG_GOALS * np.exp(GOAL_SPREAD_K * diff) * (a.attack / LEAGUE_AVG_GOALS) ** 0.5 * (b.defense / LEAGUE_AVG_GOALS) ** 0.5
    lam_b = LEAGUE_AVG_GOALS * np.exp(-GOAL_SPREAD_K * diff) * (b.attack / LEAGUE_AVG_GOALS) ** 0.5 * (a.defense / LEAGUE_AVG_GOALS) ** 0.5
    return int(rng.poisson(min(lam_a, 6))), int(rng.poisson(min(lam_b, 6)))


def _pen_winner(rng, a: _T, b: _T) -> int:
    p_a = 1.0 / (1.0 + 10 ** ((b.rating - a.rating) / 400.0))
    return a.id if rng.random() < p_a else b.id


def _ko_result(rng, a: _T, b: _T) -> tuple[int, int, int, bool]:
    ga, gb = _sim_goals(rng, a, b, 0)
    if ga > gb:
        return a.id, ga, gb, False
    if gb > ga:
        return b.id, ga, gb, False
    return _pen_winner(rng, a, b), ga, gb, True


def _play_group(rng, ids: list[int], idx: dict[int, _T]):
    stat = {i: {"pts": 0, "gf": 0, "ga": 0} for i in ids}
    for x in range(len(ids)):
        for y in range(x + 1, len(ids)):
            a, b = idx[ids[x]], idx[ids[y]]
            ga, gb = _sim_goals(rng, a, b, 0)
            stat[a.id]["gf"] += ga; stat[a.id]["ga"] += gb
            stat[b.id]["gf"] += gb; stat[b.id]["ga"] += ga
            if ga > gb:
                stat[a.id]["pts"] += 3
            elif gb > ga:
                stat[b.id]["pts"] += 3
            else:
                stat[a.id]["pts"] += 1; stat[b.id]["pts"] += 1
    ranked = sorted(ids, key=lambda i: (stat[i]["pts"], stat[i]["gf"] - stat[i]["ga"],
                                        stat[i]["gf"], idx[i].rating), reverse=True)
    return ranked, stat


def _qualifiers(rng, group_ids, idx):
    winners, runners, thirds, standings = [], [], [], {}
    for g, ids in group_ids.items():
        ranked, stat = _play_group(rng, ids, idx)
        standings[g] = [{"id": i, **stat[i], "gd": stat[i]["gf"] - stat[i]["ga"]} for i in ranked]
        winners.append((ranked[0], stat[ranked[0]], True))
        runners.append((ranked[1], stat[ranked[1]], True))
        thirds.append((ranked[2], stat[ranked[2]], False))
    thirds.sort(key=lambda e: (e[1]["pts"], e[1]["gf"] - e[1]["ga"], e[1]["gf"], idx[e[0]].rating), reverse=True)
    pool = winners + runners + thirds[:8]
    pool.sort(key=lambda e: (e[2], e[1]["pts"], e[1]["gf"] - e[1]["ga"], e[1]["gf"], idx[e[0]].rating), reverse=True)
    return [e[0] for e in pool], standings


def _seed_to_bracket(seeded_ids: list[int]) -> list[int]:
    return [seeded_ids[s] for s in _standard_bracket(len(seeded_ids))]


def run_monte_carlo(n: int = 2000, seed: int = 2026, teams: list[Team] | None = None) -> dict:
    teams = teams or load_teams()
    idx = _index(teams)
    group_ids = {g: [t.id for t in m] for g, m in groups_map(teams).items()}
    rng = np.random.default_rng(seed)
    counts = {t.id: {s: 0 for s in STAGES} for t in teams}

    for _ in range(n):
        seeded, _ = _qualifiers(rng, group_ids, idx)
        for i in seeded:
            counts[i]["r32"] += 1
        bracket = _seed_to_bracket(seeded)
        for stage in ["r16", "qf", "sf", "final", "winner"]:
            winners = []
            for k in range(0, len(bracket), 2):
                w, _, _, _ = _ko_result(rng, idx[bracket[k]], idx[bracket[k + 1]])
                counts[w][stage] += 1
                winners.append(w)
            bracket = winners

    probs = {}
    for i, c in counts.items():
        probs[i] = {s: round(c[s] / n, 4) for s in STAGES}
        probs[i]["group_advance"] = probs[i]["r32"]
    return {"n": n, "probabilities": probs}


def _team_dict(t: Team) -> dict:
    return {"id": t.id, "name": t.name, "flag": t.flag, "group": t.group}


def simulate_once(seed: int | None = None, teams: list[Team] | None = None) -> dict:
    teams = teams or load_teams()
    tmap = {t.id: t for t in teams}
    idx = _index(teams)
    group_ids = {g: [t.id for t in m] for g, m in groups_map(teams).items()}
    rng = np.random.default_rng(seed)

    seeded, standings = _qualifiers(rng, group_ids, idx)
    qset = set(seeded)
    group_view = {g: [{**_team_dict(tmap[r["id"]]), "points": r["pts"], "gf": r["gf"],
                       "ga": r["ga"], "gd": r["gd"], "qualified": r["id"] in qset}
                      for r in rows] for g, rows in standings.items()}

    bracket = _seed_to_bracket(seeded)
    rounds, current = [], bracket
    for name in KO_ROUND_NAMES:
        matches, winners = [], []
        for k in range(0, len(current), 2):
            a, b = idx[current[k]], idx[current[k + 1]]
            w, ga, gb, pens = _ko_result(rng, a, b)
            matches.append({"round": name, "team_a": _team_dict(tmap[a.id]),
                            "team_b": _team_dict(tmap[b.id]), "score_a": ga, "score_b": gb,
                            "penalties": pens, "winner_id": w})
            winners.append(w)
        rounds.append({"name": name, "matches": matches})
        current = winners

    return {"seed": seed, "groups": group_view, "knockout": rounds,
            "champion": tmap[current[0]].to_dict()}


if __name__ == "__main__":
    import time
    t0 = time.time()
    res = run_monte_carlo(n=2000)
    names = {t.id: t.name for t in load_teams()}
    ranked = sorted(res["probabilities"].items(), key=lambda kv: -kv[1]["winner"])
    print(f"2000 sims in {time.time()-t0:.1f}s · Top 8 title favourites:")
    for tid, p in ranked[:8]:
        print(f"  {names[tid]:14s} win={p['winner']*100:5.1f}%  final={p['final']*100:5.1f}%  "
              f"advance={p['group_advance']*100:5.1f}%")
