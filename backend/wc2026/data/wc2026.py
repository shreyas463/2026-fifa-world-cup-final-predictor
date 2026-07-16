"""Build the 2026 World Cup bracket from the REAL recorded results in the
martj42 dataset.

Every played match (group stage through the semifinals) uses the actual
scoreline and winner (penalty shootouts resolved from shootouts.csv). The final
and third-place play-off are, as of the data snapshot, genuinely UNPLAYED — so
those two are filled by the model as clearly-flagged predictions.

The built bracket is cached to artifacts/bracket_2026.json so the API runs
without the raw dataset present.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from ..ml.history import RESULTS, load_results, load_shootouts

ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "artifacts"
CACHE = ARTIFACT_DIR / "bracket_2026.json"

ROUND_BOUNDS = [
    ("Round of 32", "2026-06-28", "2026-07-03", "Jun 28 – Jul 3, 2026"),
    ("Round of 16", "2026-07-04", "2026-07-07", "Jul 4 – 7, 2026"),
    ("Quarterfinals", "2026-07-09", "2026-07-11", "Jul 9 – 11, 2026"),
    ("Semifinals", "2026-07-14", "2026-07-15", "Jul 14 – 15, 2026"),
]
THIRD_DATE = "Saturday, Jul 18, 2026"
FINAL_DATE = "Sunday, Jul 19, 2026"
SCHEDULE = [
    {"round": "Group stage", "dates": "Jun 11 – 27, 2026"},
    *[{"round": r, "dates": d} for r, _, _, d in ROUND_BOUNDS],
    {"round": "Third-place play-off", "dates": THIRD_DATE},
    {"round": "Final", "dates": FINAL_DATE},
]


def _td(t) -> dict:
    return {"id": t.id, "name": t.name, "flag": t.flag, "group": t.group}


def _winner_name(hm, aw, hs, as_, shootouts, date):
    if pd.isna(hs) or pd.isna(as_):
        return None
    if hs > as_:
        return hm
    if as_ > hs:
        return aw
    return shootouts.get((date.date(), frozenset({hm, aw})))


def _group_standings(teams, group_matches, by_name):
    """Real group standings from the 72 group matches -> qualified flags."""
    stat = {t.name: {"pts": 0, "gf": 0, "ga": 0} for t in teams}
    for m in group_matches.itertuples(index=False):
        h, a, hs, as_ = m.home_team, m.away_team, int(m.home_score), int(m.away_score)
        if h not in stat or a not in stat:
            continue
        stat[h]["gf"] += hs; stat[h]["ga"] += as_
        stat[a]["gf"] += as_; stat[a]["ga"] += hs
        if hs > as_:
            stat[h]["pts"] += 3
        elif as_ > hs:
            stat[a]["pts"] += 3
        else:
            stat[h]["pts"] += 1; stat[a]["pts"] += 1

    groups: dict[str, list] = {}
    for t in teams:
        groups.setdefault(t.group, []).append(t)
    thirds = []
    ranked_groups = {}
    for g, members in groups.items():
        rows = sorted(members, key=lambda t: (stat[t.name]["pts"],
                      stat[t.name]["gf"] - stat[t.name]["ga"], stat[t.name]["gf"]), reverse=True)
        ranked_groups[g] = rows
        thirds.append(rows[2])
    thirds.sort(key=lambda t: (stat[t.name]["pts"], stat[t.name]["gf"] - stat[t.name]["ga"],
                               stat[t.name]["gf"]), reverse=True)
    best_thirds = {t.name for t in thirds[:8]}

    view = {}
    for g, rows in sorted(ranked_groups.items()):
        view[g] = []
        for pos, t in enumerate(rows):
            qualified = pos < 2 or t.name in best_thirds
            view[g].append({**_td(t), "points": stat[t.name]["pts"],
                            "gf": stat[t.name]["gf"], "ga": stat[t.name]["ga"],
                            "qualified": qualified, "position": "W" if pos == 0 else "R" if pos == 1 else "3"})
    return view


def build_bracket(teams, predict_fn) -> dict:
    df = load_results(played_only=False)
    wc = df[(df["tournament"] == "FIFA World Cup") & (df["date"] >= pd.Timestamp("2026-06-01"))].copy()
    shootouts = load_shootouts()
    by_name = {t.name: t for t in teams}

    group_matches = wc[wc["date"] < pd.Timestamp("2026-06-28")]
    group_view = _group_standings(teams, group_matches, by_name)

    # Collect knockout matches per round with real winners.
    ko = wc[wc["date"] >= pd.Timestamp("2026-06-28")]
    rounds_raw = {}
    for name, lo, hi, _ in ROUND_BOUNDS:
        sel = ko[(ko["date"] >= pd.Timestamp(lo)) & (ko["date"] <= pd.Timestamp(hi))]
        rounds_raw[name] = list(sel.itertuples(index=False))

    def match_obj(m, round_name, predicted=False):
        hm, aw = m.home_team, m.away_team
        played = not (pd.isna(m.home_score) or pd.isna(m.away_score))
        pens = played and int(m.home_score) == int(m.away_score)
        wname = _winner_name(hm, aw, m.home_score, m.away_score, shootouts, m.date)
        obj = {"round": round_name, "team_a": _td(by_name[hm]), "team_b": _td(by_name[aw]),
               "score_a": None if not played else int(m.home_score),
               "score_b": None if not played else int(m.away_score),
               "penalties": pens, "played": played, "predicted": predicted,
               "winner_id": by_name[wname].id if wname else None}
        return obj, wname

    # Reconstruct the bracket tree by linking winners across rounds.
    level_names = [r[0] for r in ROUND_BOUNDS]  # R32, R16, QF, SF
    winners_by_round = {}
    for name in level_names:
        wins = {}
        for m in rounds_raw[name]:
            _, w = match_obj(m, name)
            if w:
                wins[w] = m
        winners_by_round[name] = wins

    def feeder(level_idx, team):
        for m in rounds_raw[level_names[level_idx]]:
            _, w = match_obj(m, level_names[level_idx])
            if w == team:
                return m
        return None

    ordered = {name: [] for name in level_names}

    def walk(m, level_idx):
        obj, _ = match_obj(m, level_names[level_idx])
        ordered[level_names[level_idx]].append(obj)
        if level_idx == 0:
            return
        for team in (m.home_team, m.away_team):
            fm = feeder(level_idx - 1, team)
            if fm is not None:
                walk(fm, level_idx - 1)

    for sf in rounds_raw["Semifinals"]:
        walk(sf, len(level_names) - 1)

    knockout = [{"name": name, "dates": dates, "matches": ordered[name]}
                for name, _, _, dates in ROUND_BOUNDS]

    # Finalists = SF winners; third-place contestants = SF losers.
    sf_objs = [match_obj(m, "Semifinals")[0] for m in rounds_raw["Semifinals"]]
    finalists = [by_name[o["team_a"]["name"]] if o["winner_id"] == o["team_a"]["id"]
                 else by_name[o["team_b"]["name"]] for o in sf_objs]
    sf_losers = [by_name[o["team_b"]["name"]] if o["winner_id"] == o["team_a"]["id"]
                 else by_name[o["team_a"]["name"]] for o in sf_objs]

    final = _predicted_match(finalists[0], finalists[1], "Final", FINAL_DATE, predict_fn)
    third = _predicted_match(sf_losers[0], sf_losers[1], "Third-place play-off", THIRD_DATE, predict_fn)

    champ = by_name[final["team_a"]["name"]] if final["winner_id"] == final["team_a"]["id"] else by_name[final["team_b"]["name"]]
    runner = by_name[final["team_b"]["name"]] if final["winner_id"] == final["team_a"]["id"] else by_name[final["team_a"]["name"]]
    third_team = by_name[third["team_a"]["name"]] if third["winner_id"] == third["team_a"]["id"] else by_name[third["team_b"]["name"]]

    return {
        "is_projection": False,
        "results_source": "Real recorded results (martj42 dataset); final & third-place are model predictions (unplayed).",
        "as_of": "2026-07-15",
        "schedule": SCHEDULE,
        "groups": group_view,
        "knockout": knockout,
        "final": final,
        "third_place": third,
        "champion": {**champ.to_dict(), "predicted": True},
        "runner_up": _td(runner),
        "third": _td(third_team),
    }


def _predicted_match(a, b, round_name, dates, predict_fn) -> dict:
    pred = predict_fn(a, b, neutral=True)
    p = pred["probabilities"]
    a_wins = p["team_a_win"] >= p["team_b_win"]
    sa, sb = pred["predicted_score"]["team_a"], pred["predicted_score"]["team_b"]
    if sa == sb:  # ensure a decisive projected winner
        sa, sb = (sa + 1, sb) if a_wins else (sa, sb + 1)
    return {"round": round_name, "dates": dates, "team_a": _td(a), "team_b": _td(b),
            "score_a": sa, "score_b": sb, "penalties": False, "played": False, "predicted": True,
            "winner_id": a.id if a_wins else b.id,
            "win_probabilities": {"team_a": round(p["team_a_win"], 3), "draw": round(p["draw"], 3),
                                  "team_b": round(p["team_b_win"], 3)}}


def has_raw() -> bool:
    return RESULTS.exists()


def save_cache(bracket: dict) -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(bracket, indent=2))


def load_cache() -> dict | None:
    return json.loads(CACHE.read_text()) if CACHE.exists() else None
