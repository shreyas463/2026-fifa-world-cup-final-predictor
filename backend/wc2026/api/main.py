"""FastAPI application exposing the World Cup prediction API."""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ..engine.match import predict_match
from ..engine.simulate import run_monte_carlo, simulate_once
from .service import get_state

app = FastAPI(
    title="2026 FIFA World Cup Winner Predictor API",
    description="Match predictions, tournament simulations and model metrics for the 2026 World Cup.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DISCLAIMER = (
    "All figures are probability-based statistical estimates, not guaranteed outcomes. "
    "Real results are affected by injuries, squad changes, tactics, red cards, penalties "
    "and other unpredictable events."
)


class MatchRequest(BaseModel):
    team_a_id: int = Field(..., ge=1, le=48)
    team_b_id: int = Field(..., ge=1, le=48)
    neutral: bool = True


class SimulateRequest(BaseModel):
    simulations: int = Field(1000, ge=1, le=20000)
    seed: int | None = None


@app.get("/api/health")
def health():
    st = get_state()
    return {"status": "ok", "teams": len(st.teams), "model": st.metrics.get("best_model")}


@app.get("/api/teams")
def teams(
    q: str | None = Query(None, description="search by team name"),
    group: str | None = None,
    confederation: str | None = None,
):
    st = get_state()
    rows = [st.team_summary(t) for t in st.teams]
    if q:
        rows = [r for r in rows if q.lower() in r["name"].lower()]
    if group:
        rows = [r for r in rows if r["group"].upper() == group.upper()]
    if confederation:
        rows = [r for r in rows if r["confederation"].lower() == confederation.lower()]
    rows.sort(key=lambda r: -r["win_probability"])
    return {"count": len(rows), "teams": rows, "disclaimer": DISCLAIMER}


@app.get("/api/teams/{team_id}")
def team_detail(team_id: int):
    st = get_state()
    t = st.by_id.get(team_id)
    if not t:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
    return {"team": st.team_detail(t), "disclaimer": DISCLAIMER}


@app.get("/api/predictions")
def predictions():
    st = get_state()
    board = st.leaderboard()
    return {
        "leaderboard": board,
        "favourite": board[0],
        "simulations": 5000,
        "disclaimer": DISCLAIMER,
    }


@app.post("/api/predict-match")
def predict(req: MatchRequest):
    st = get_state()
    a, b = st.by_id.get(req.team_a_id), st.by_id.get(req.team_b_id)
    if not a or not b:
        raise HTTPException(status_code=404, detail="One or both teams not found")
    if a.id == b.id:
        raise HTTPException(status_code=400, detail="Pick two different teams")
    return {"prediction": predict_match(a, b, neutral=req.neutral), "disclaimer": DISCLAIMER}


@app.post("/api/simulate-tournament")
def simulate(req: SimulateRequest):
    st = get_state()
    if req.simulations == 1:
        return {"mode": "single", "simulation": simulate_once(seed=req.seed, teams=st.teams),
                "disclaimer": DISCLAIMER}
    result = run_monte_carlo(n=req.simulations, seed=req.seed or 2026, teams=st.teams)
    probs = result["probabilities"]
    table = []
    for t in st.teams:
        p = probs[t.id]
        table.append({**t.to_dict(), "probabilities": p, "win_probability": p["winner"]})
    table.sort(key=lambda r: -r["win_probability"])
    return {
        "mode": "aggregate",
        "simulations": result["n"],
        "results": table,
        "sample_bracket": simulate_once(seed=req.seed, teams=st.teams),
        "disclaimer": DISCLAIMER,
    }


@app.get("/api/bracket")
def bracket():
    st = get_state()
    return {"bracket": st.bracket, "disclaimer": DISCLAIMER}


@app.get("/api/sentiment")
def sentiment():
    st = get_state()
    table = st.sentiment_table()
    return {
        "sentiment": table,
        "most_positive": max(table, key=lambda r: r["positivity"]),
        "most_buzz": table[0],
        "source": "Curated social-media snapshot (pluggable to a live X API); not a live scrape.",
        "disclaimer": DISCLAIMER,
    }


@app.get("/api/model-metrics")
def model_metrics():
    st = get_state()
    return {"metrics": st.metrics, "disclaimer": DISCLAIMER}


@app.get("/api/team-comparison")
def team_comparison(
    team_a: int = Query(..., ge=1, le=48),
    team_b: int = Query(..., ge=1, le=48),
):
    st = get_state()
    a, b = st.by_id.get(team_a), st.by_id.get(team_b)
    if not a or not b:
        raise HTTPException(status_code=404, detail="One or both teams not found")
    if a.id == b.id:
        raise HTTPException(status_code=400, detail="Pick two different teams")
    match = predict_match(a, b, neutral=True)
    return {
        "team_a": st.team_detail(a),
        "team_b": st.team_detail(b),
        "attribute_labels": st.team_detail(a)["attribute_labels"],
        "head_to_head": match["head_to_head"],
        "match_preview": match["probabilities"],
        "disclaimer": DISCLAIMER,
    }


@app.get("/")
def root():
    return {"name": "2026 FIFA World Cup Winner Predictor API", "docs": "/docs",
            "disclaimer": DISCLAIMER}
