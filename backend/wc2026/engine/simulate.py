"""Monte Carlo simulation of the 48-team 2026 World Cup.

Format modelled:
  * 12 groups of 4, single round-robin
  * top 2 of each group + 8 best third-placed teams -> Round of 32
  * single-elimination R32 -> R16 -> QF -> SF -> Final (penalty tiebreak)

`run_monte_carlo` aggregates each team's probability of reaching every stage.
`simulate_once` returns one full random realisation for the simulator page.
`predicted_bracket` returns the deterministic favourites bracket for /api/bracket.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..data.teams import Team, groups_map, load_teams
from .poisson import GOAL_SPREAD_K, LEAGUE_AVG_GOALS, expected_goals

STAGES = ["r32", "r16", "qf", "sf", "final", "winner"]
KO_ROUND_NAMES = ["Round of 32", "Round of 16", "Quarterfinals", "Semifinals", "Final"]


@dataclass
class _T:
    id: int
    elo: float
    attack: float
    defense: float
    host: bool


def _index(teams: list[Team]) -> dict[int, _T]:
    return {t.id: _T(t.id, float(t.elo), t.attack, t.defense, t.host) for t in teams}


def _standard_bracket(n: int) -> list[int]:
    """Seed-slot order so seed 1 and seed 2 can only meet in the final."""
    order = [0]
    m = 1
    while m < n:
        m *= 2
        order = [x for pair in ((s, m - 1 - s) for s in order) for x in pair]
    return order


def _sim_goals(rng, a: _T, b: _T, home_adv: int) -> tuple[int, int]:
    lam_a, lam_b = expected_goals(a.elo, b.elo, home_adv, a.attack, a.defense, b.attack, b.defense)
    return int(rng.poisson(lam_a)), int(rng.poisson(lam_b))


def _pen_winner(rng, a: _T, b: _T) -> int:
    p_a = 1.0 / (1.0 + 10 ** ((b.elo - a.elo) / 400.0))
    return a.id if rng.random() < p_a else b.id


def _ko_result(rng, a: _T, b: _T) -> tuple[int, int, int, bool]:
    ga, gb = _sim_goals(rng, a, b, 0)
    if ga > gb:
        return a.id, ga, gb, False
    if gb > ga:
        return b.id, ga, gb, False
    return _pen_winner(rng, a, b), ga, gb, True


# ---------------------------------------------------------------------------
# Group stage
# ---------------------------------------------------------------------------

def _play_group(rng, ids: list[int], idx: dict[int, _T]):
    """Round-robin; return standings sorted best-first with points/GD/GF."""
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
    ranked = sorted(
        ids,
        key=lambda i: (stat[i]["pts"], stat[i]["gf"] - stat[i]["ga"], stat[i]["gf"], idx[i].elo),
        reverse=True,
    )
    return ranked, stat


def _qualifiers(rng, group_ids: dict[str, list[int]], idx):
    """Return the 32 qualifiers seeded strongest-first, plus per-group standings."""
    winners, runners, thirds = [], [], []
    standings = {}
    for g, ids in group_ids.items():
        ranked, stat = _play_group(rng, ids, idx)
        standings[g] = [{"id": i, **stat[i], "gd": stat[i]["gf"] - stat[i]["ga"]} for i in ranked]
        winners.append((ranked[0], stat[ranked[0]], True))
        runners.append((ranked[1], stat[ranked[1]], True))
        thirds.append((ranked[2], stat[ranked[2]], False))

    thirds.sort(key=lambda e: (e[1]["pts"], e[1]["gf"] - e[1]["ga"], e[1]["gf"], idx[e[0]].elo),
                reverse=True)
    best_thirds = thirds[:8]

    pool = winners + runners + best_thirds
    # Seed: group winners first, then by points / GD / GF / Elo.
    pool.sort(key=lambda e: (e[2], e[1]["pts"], e[1]["gf"] - e[1]["ga"], e[1]["gf"], idx[e[0]].elo),
              reverse=True)
    seeded_ids = [e[0] for e in pool]
    return seeded_ids, standings


def _seed_to_bracket(seeded_ids: list[int]) -> list[int]:
    order = _standard_bracket(len(seeded_ids))
    return [seeded_ids[s] for s in order]


# ---------------------------------------------------------------------------
# Monte Carlo aggregation
# ---------------------------------------------------------------------------

def run_monte_carlo(n: int = 2000, seed: int = 2026, teams: list[Team] | None = None) -> dict:
    teams = teams or load_teams()
    idx = _index(teams)
    group_ids = {g: [t.id for t in members] for g, members in groups_map(teams).items()}
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


# ---------------------------------------------------------------------------
# Single realisation (for the simulator page)
# ---------------------------------------------------------------------------

def _team_dict(t: Team) -> dict:
    return {"id": t.id, "name": t.name, "flag": t.flag, "group": t.group}


def simulate_once(seed: int | None = None, teams: list[Team] | None = None) -> dict:
    teams = teams or load_teams()
    tmap = {t.id: t for t in teams}
    idx = _index(teams)
    group_ids = {g: [t.id for t in members] for g, members in groups_map(teams).items()}
    rng = np.random.default_rng(seed)

    seeded, standings = _qualifiers(rng, group_ids, idx)

    # Build readable group standings
    group_view = {}
    for g, rows in standings.items():
        group_view[g] = [
            {**_team_dict(tmap[r["id"]]), "points": r["pts"], "gf": r["gf"],
             "ga": r["ga"], "gd": r["gd"], "qualified": r["id"] in set(seeded)}
            for r in rows
        ]

    bracket = _seed_to_bracket(seeded)
    rounds = []
    current = bracket
    for name in KO_ROUND_NAMES:
        matches, winners = [], []
        for k in range(0, len(current), 2):
            a, b = idx[current[k]], idx[current[k + 1]]
            w, ga, gb, pens = _ko_result(rng, a, b)
            matches.append({
                "round": name,
                "team_a": _team_dict(tmap[a.id]), "team_b": _team_dict(tmap[b.id]),
                "score_a": ga, "score_b": gb, "penalties": pens,
                "winner_id": w,
            })
            winners.append(w)
        rounds.append({"name": name, "matches": matches})
        current = winners

    champion = tmap[current[0]]
    return {
        "seed": seed,
        "groups": group_view,
        "knockout": rounds,
        "champion": tmap and champion.to_dict(),
    }


def predicted_bracket(teams: list[Team] | None = None) -> dict:
    """Deterministic 'chalk' bracket where the favourite (higher Elo) advances."""
    teams = teams or load_teams()
    tmap = {t.id: t for t in teams}
    idx = _index(teams)
    group_ids = {g: [t.id for t in members] for g, members in groups_map(teams).items()}

    # Deterministic group order by Elo; top 2 + best-Elo thirds qualify.
    winners, runners, thirds = [], [], []
    group_view = {}
    for g, ids in group_ids.items():
        ranked = sorted(ids, key=lambda i: -idx[i].elo)
        group_view[g] = [{**_team_dict(tmap[i]),
                          "qualified": True if idx[i] else True} for i in ranked]
        winners.append((ranked[0], True)); runners.append((ranked[1], True))
        thirds.append((ranked[2], False))
    thirds.sort(key=lambda e: -idx[e[0]].elo)
    pool = winners + runners + thirds[:8]
    pool.sort(key=lambda e: (e[1], idx[e[0]].elo), reverse=True)
    seeded = [e[0] for e in pool]
    # mark qualified in group_view
    qset = set(seeded)
    for g in group_view:
        for row in group_view[g]:
            row["qualified"] = row["id"] in qset

    bracket = _seed_to_bracket(seeded)
    rounds = []
    current = bracket
    for name in KO_ROUND_NAMES:
        matches, winners2 = [], []
        for k in range(0, len(current), 2):
            a, b = idx[current[k]], idx[current[k + 1]]
            w = a.id if a.elo >= b.elo else b.id
            matches.append({"round": name, "team_a": _team_dict(tmap[a.id]),
                            "team_b": _team_dict(tmap[b.id]), "winner_id": w})
            winners2.append(w)
        rounds.append({"name": name, "matches": matches})
        current = winners2

    return {"groups": group_view, "knockout": rounds,
            "champion": tmap[current[0]].to_dict()}


if __name__ == "__main__":
    import time
    t0 = time.time()
    res = run_monte_carlo(n=1000)
    dt = time.time() - t0
    ranked = sorted(res["probabilities"].items(), key=lambda kv: -kv[1]["winner"])
    names = {t.id: t.name for t in load_teams()}
    print(f"{1000} sims in {dt:.1f}s\nTop 10 title favourites:")
    for tid, p in ranked[:10]:
        print(f"  {names[tid]:14s} win={p['winner']*100:5.1f}%  final={p['final']*100:5.1f}%  "
              f"advance={p['group_advance']*100:5.1f}%")
