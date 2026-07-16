"""Export every API response as static JSON so the frontend can run as a fully
static site (e.g. GitHub Pages) with no backend.

Writes to frontend/public/data/. Run:  python -m scripts.export_static
"""
from __future__ import annotations

import json
from pathlib import Path

from wc2026.api.service import get_state
from wc2026.engine.match import predict_match
from wc2026.engine.simulate import simulate_once

OUT = Path(__file__).resolve().parents[2] / "frontend" / "public" / "data"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    st = get_state()

    def dump(name, obj):
        (OUT / f"{name}.json").write_text(json.dumps(obj, separators=(",", ":")))
        print(f"  {name}.json ({(OUT / f'{name}.json').stat().st_size // 1024} KB)")

    dump("teams", [st.team_summary(t) for t in st.teams])
    dump("details", {str(t.id): st.team_detail(t) for t in st.teams})
    board = st.leaderboard()
    dump("predictions", {"leaderboard": board, "favourite": board[0]})
    dump("bracket", st.bracket)
    dump("metrics", st.metrics)
    table = st.sentiment_table()
    dump("sentiment", {"sentiment": table,
                       "most_positive": max(table, key=lambda r: r["positivity"]),
                       "most_buzz": table[0],
                       "source": "Curated social-media snapshot (pluggable to a live X API); not a live scrape."})

    # All ordered pairwise match predictions (for predict-match + comparison).
    matches = {}
    for a in st.teams:
        for b in st.teams:
            if a.id != b.id:
                matches[f"{a.id}-{b.id}"] = predict_match(a, b, neutral=True)
    dump("matches", matches)

    # A handful of sample single-run tournaments for the simulator.
    samples = [simulate_once(seed=s, teams=st.teams) for s in range(1, 13)]
    dump("sims", {"aggregate": board, "samples": samples})

    print(f"\nExported static data to {OUT}")


if __name__ == "__main__":
    main()
