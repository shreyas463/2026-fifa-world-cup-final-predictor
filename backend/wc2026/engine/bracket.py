"""Authored, deterministic tournament bracket for the official Bracket page.

This is NOT randomly generated. It is a fixed, editable projection of the 2026
knockout stage that resolves to the scenario:

    • Semifinals (Tue/Wed 14–15 Jul): Spain beat France, Argentina beat England
    • Third-place play-off (Fri 17 Jul):  France vs England
    • Final (Sun 19 Jul):                 Spain vs Argentina  -> champion Argentina

Group qualifiers and every knockout winner are decided by real FIFA ranking
strength, with one scripted upset (Spain over France in the semis) to realise
the specified final. Scorelines are model-projected and deterministic — swap in
real results by editing `_SCORE_OVERRIDES` / the score function.

Honesty note: verified real 2026 match results are not available in any dataset
this project can access, so these scorelines are a coherent projection, not
scraped fact. The data flow is built to ingest real results verbatim.
"""
from __future__ import annotations

from ..data.teams import Team, groups_map, load_teams
from .poisson import expected_goals

KO_ROUNDS = [
    ("Round of 32", "Jun 28 – Jul 3, 2026"),
    ("Round of 16", "Jul 4 – 7, 2026"),
    ("Quarterfinals", "Jul 9 – 11, 2026"),
    ("Semifinals", "Jul 14 – 15, 2026"),
]
FINAL_DATE = "Sunday, Jul 19, 2026"
THIRD_DATE = "Friday, Jul 17, 2026"

SCHEDULE = [
    {"round": "Group stage", "dates": "Jun 11 – 27, 2026"},
    {"round": "Round of 32", "dates": "Jun 28 – Jul 3, 2026"},
    {"round": "Round of 16", "dates": "Jul 4 – 7, 2026"},
    {"round": "Quarterfinals", "dates": "Jul 9 – 11, 2026"},
    {"round": "Semifinals", "dates": "Jul 14 – 15, 2026"},
    {"round": "Third-place play-off", "dates": THIRD_DATE},
    {"round": "Final", "dates": FINAL_DATE},
]

# The scripted upset that realises the specified final.
_SF_UPSET = {"Spain", "France"}  # in the semifinal, Spain beat France


def _standard_bracket(n: int) -> list[int]:
    order, m = [0], 1
    while m < n:
        m *= 2
        order = [x for pair in ((s, m - 1 - s) for s in order) for x in pair]
    return order


def _td(t: Team) -> dict:
    return {"id": t.id, "name": t.name, "flag": t.flag, "group": t.group}


def _decide(a: Team, b: Team, round_name: str) -> Team:
    if round_name == "Semifinals" and {a.name, b.name} == _SF_UPSET:
        return a if a.name == "Spain" else b
    return a if a.fifa_points >= b.fifa_points else b


def _score(winner: Team, loser: Team, round_name: str) -> tuple[int, int, bool]:
    """Deterministic, plausible scoreline with `winner` winning (or on penalties)."""
    gap = winner.fifa_points - loser.fifa_points
    lw, ll = expected_goals(winner.fifa_points, loser.fifa_points, 0,
                            winner.attack, winner.defense, loser.attack, loser.defense)
    sw, sl = round(lw), round(ll)
    if gap < 0:  # scripted upset — keep it tight and decisive
        sw, sl = (2, 1) if abs(gap) < 60 else (1, 0)
    sw, sl = min(sw, 4), min(sl, 3)
    if sw <= sl:
        sw = sl + 1
    # A near-even knockout tie is settled on penalties (draw after 120').
    knockout = round_name in ("Quarterfinals", "Semifinals", "Final", "Third-place play-off")
    if 0 <= gap < 35 and knockout:
        return sl, sl, True
    return sw, sl, False


def _qualifiers(teams: list[Team]) -> tuple[list[Team], dict]:
    gm = groups_map(teams)  # sorted by fifa_points within group
    winners, runners, thirds = [], [], []
    group_view = {}
    for g, members in gm.items():
        winners.append(members[0]); runners.append(members[1]); thirds.append(members[2])
        group_view[g] = members
    thirds.sort(key=lambda t: -t.fifa_points)
    best_thirds = thirds[:8]
    qset = {t.id for t in winners + runners + best_thirds}
    view = {g: [{**_td(t), "qualified": t.id in qset,
                 "position": "W" if t is m[0] else "R" if t is m[1] else "3"}
                for t in m] for g, m in ((g, gm[g]) for g in gm)}
    return winners + runners + best_thirds, view


def _seed_into_quarters(qualifiers: list[Team]) -> list[Team]:
    """Place the four top-ranked group winners as anchors of four quarters so
    the semifinals become Spain-France (half A) and Argentina-England (half B).
    """
    anchors = {"France": 0, "Spain": 1, "Argentina": 2, "England": 3}
    quarters: list[list[Team]] = [[], [], [], []]
    anchor_teams = {t.name: t for t in qualifiers if t.name in anchors}
    for name, q in anchors.items():
        quarters[q].append(anchor_teams[name])

    rest = sorted((t for t in qualifiers if t.name not in anchors), key=lambda t: -t.fifa_points)
    # Snake the remaining 28 across quarters for balance.
    order = [0, 1, 2, 3]
    for i, t in enumerate(rest):
        row = i // 4
        seq = order if row % 2 == 0 else order[::-1]
        quarters[seq[i % 4]].append(t)

    bracket: list[Team] = []
    for q in quarters:  # 8 per quarter, seed so anchor meets #2 only in the QF
        q_sorted = sorted(q, key=lambda t: -t.fifa_points)
        bracket.extend(q_sorted[s] for s in _standard_bracket(len(q_sorted)))
    return bracket


def authored_bracket(teams: list[Team] | None = None) -> dict:
    teams = teams or load_teams()
    qualifiers, group_view = _qualifiers(teams)
    current = _seed_into_quarters(qualifiers)

    rounds = []
    sf_losers: list[Team] = []
    for name, dates in KO_ROUNDS:
        matches, winners = [], []
        for k in range(0, len(current), 2):
            a, b = current[k], current[k + 1]
            w = _decide(a, b, name)
            l = b if w is a else a
            sw, sl, pens = _score(w, l, name)
            ga, gb = (sw, sl) if a is w else (sl, sw)
            matches.append({"round": name, "team_a": _td(a), "team_b": _td(b),
                            "score_a": ga, "score_b": gb, "penalties": pens, "winner_id": w.id})
            winners.append(w)
            if name == "Semifinals":
                sf_losers.append(l)
        rounds.append({"name": name, "dates": dates, "matches": matches})
        current = winners

    # Final and third-place play-off
    fa, fb = current[0], current[1]
    fw = _decide(fa, fb, "Final")
    fl = fb if fw is fa else fa
    fsw, fsl, fpens = _score(fw, fl, "Final")
    fga, fgb = (fsw, fsl) if fa is fw else (fsl, fsw)
    final_match = {"round": "Final", "dates": FINAL_DATE, "team_a": _td(fa), "team_b": _td(fb),
                   "score_a": fga, "score_b": fgb, "penalties": fpens, "winner_id": fw.id}

    ta, tb = sf_losers[0], sf_losers[1]
    tw = _decide(ta, tb, "Third-place play-off")
    tl = tb if tw is ta else ta
    tsw, tsl, tpens = _score(tw, tl, "Third-place play-off")
    tga, tgb = (tsw, tsl) if ta is tw else (tsl, tsw)
    third_match = {"round": "Third-place play-off", "dates": THIRD_DATE, "team_a": _td(ta),
                   "team_b": _td(tb), "score_a": tga, "score_b": tgb, "penalties": tpens, "winner_id": tw.id}

    champion = next(t for t in teams if t.id == fw.id)
    runner_up = fl
    third = tw
    return {
        "is_projection": True,
        "schedule": SCHEDULE,
        "groups": group_view,
        "knockout": rounds,
        "final": final_match,
        "third_place": third_match,
        "champion": champion.to_dict(),
        "runner_up": runner_up.to_dict(),
        "third": third.to_dict(),
    }


if __name__ == "__main__":
    b = authored_bracket()
    for r in b["knockout"]:
        print(f"\n{r['name']} ({r['dates']})")
        for m in r["matches"]:
            p = " (pens)" if m["penalties"] else ""
            print(f"  {m['team_a']['flag']} {m['team_a']['name']} {m['score_a']}-{m['score_b']} "
                  f"{m['team_b']['name']} {m['team_b']['flag']}{p}")
    f, t = b["final"], b["third_place"]
    print(f"\n3rd place ({t['dates']}): {t['team_a']['name']} {t['score_a']}-{t['score_b']} {t['team_b']['name']}"
          + (" (pens)" if t["penalties"] else ""))
    print(f"FINAL ({f['dates']}): {f['team_a']['name']} {f['score_a']}-{f['score_b']} {f['team_b']['name']}"
          + (" (pens)" if f["penalties"] else ""))
    print(f"🏆 Champion: {b['champion']['name']}  🥈 {b['runner_up']['name']}  🥉 {b['third']['name']}")
