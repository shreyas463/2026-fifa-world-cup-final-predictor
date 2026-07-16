# Final Report — 2026 FIFA World Cup Winner Predictor

*Methodology, results, limitations, and the predicted winner.*

---

## 1. Objective

Estimate, as calibrated probabilities, how far each of the 48 teams in the 2026
FIFA World Cup is likely to progress — culminating in each nation's probability
of winning the tournament — and expose those estimates through an interactive
web application.

## 2. Data

Live match-feed scraping is deliberately **not** used, so the project is fully
reproducible and runs offline. Instead the system uses:

- **A curated 2026 field** (`backend/wc2026/data/teams.py`): 48 nations with Elo
  rating, recent-form index, squad valuation, World Cup titles and appearances,
  and host status. Attacking / defensive goal rates are derived from strength
  and form. FIFA-style ranks come from the Elo ordering; the group draw is a
  deterministic, pot-based snake draft with the three hosts (USA, Mexico,
  Canada) seeded as group heads.
- **A reproducible synthetic match history** (`ml/dataset.py`): a long timeline
  of international matches whose outcomes are sampled from each team's *latent*
  strength via a Poisson generative process, with Elo, form and goal rates
  updated after every match.

> Swapping in a real results feed (e.g. an international-match CSV) only requires
> replacing `ml/dataset.py`; the feature engineering, models, engine and API are
> unchanged.

## 3. Avoiding data leakage

Every feature row is built **only from pre-match, observable statistics** — the
Elo, rolling form and rolling goal rates that were known *before* kickoff.
Rolling state is updated strictly *after* the result is recorded, so no
post-match information can leak into the features. The **same** `build_feature_row`
function is used during training and at live inference, guaranteeing identical
inputs in both phases.

## 4. Exploratory data analysis

Running `python -m wc2026.ml.eda` over 3,360 generated matches shows:

- **Outcome balance:** ~39% home/A win, ~24% draw, ~37% away/B win — realistic
  for international football.
- **~1.4 goals** per team per match; host advantage lifts the host win rate from
  ~40% (neutral) to ~51%.
- **Feature correlation with outcome:** `elo_diff` (+0.26) is the strongest
  signal, followed by `home_advantage` (+0.23) and `form_diff` (+0.15).
- **Win rate scales monotonically with the Elo gap:** from ~23% (>150 Elo behind)
  to ~60% (>150 Elo ahead) — confirming the feature set carries real signal.

## 5. Features

| Feature | Meaning |
|---------|---------|
| `elo_diff` | Elo(A) − Elo(B) |
| `form_diff` | recent-form(A) − recent-form(B) |
| `attack_a`, `defense_a` | A's goals-scored / goals-conceded rates |
| `attack_b`, `defense_b` | B's goals-scored / goals-conceded rates |
| `attack_vs_defense` | net attacking edge of A over B |
| `home_advantage` | +1 A host, −1 B host, 0 neutral |

## 6. Models & evaluation

Three classifiers plus a Poisson baseline were trained on a 75/25 train/test
split and evaluated with proper scoring rules. The best model is chosen by
log-loss.

| Model | Accuracy | Log-loss | ROC-AUC | Brier |
|-------|:-------:|:--------:|:-------:|:-----:|
| **Logistic Regression** ⭐ | **0.494** | **1.026** | **0.626** | **0.614** |
| Random Forest | 0.485 | 1.041 | 0.595 | 0.626 |
| Gradient Boosting | 0.469 | 1.068 | 0.579 | 0.644 |
| Poisson (baseline) | 0.469 | 1.072 | 0.600 | 0.644 |

Full report (precision, recall, F1, confusion matrix, feature importance and a
calibration curve) is served at `/api/model-metrics` and visualised on the
**Model Insights** page.

**Reading the numbers:** predicting a three-way result *including draws* is hard
— strong bookmaker models sit around 50–55% accuracy, so ~49% with well-ranked,
reasonably-calibrated probabilities (ROC-AUC 0.63) is a sound result. Elo
difference and host advantage are, correctly, the dominant learned features.

## 7. Match prediction & tournament simulation

- **Match engine** (`engine/match.py`): the trained classifier produces
  win/draw/loss probabilities; a **Poisson scoreline model** (`engine/poisson.py`)
  produces expected goals and the most-likely scoreline, plus head-to-head,
  form/ranking comparison and the key factors driving the call.
- **Monte Carlo simulation** (`engine/simulate.py`): plays the full 2026 format —
  12 groups of 4 (single round-robin) → top 2 of each group + 8 best
  third-placed teams → single-elimination R32 → R16 → QF → SF → Final with a
  penalty tiebreak — thousands of times, aggregating each team's probability of
  reaching every stage. 5,000 simulations run in ~2–3 seconds.

## 8. Results — the predicted winner 🏆

From **5,000 Monte Carlo simulations** of the tournament:

| # | Team | Win title | Reach final | Reach semis | Advance from group |
|---|------|:--------:|:-----------:|:-----------:|:------------------:|
| 1 | 🇦🇷 **Argentina** | **22.2%** | 35.0% | 51.5% | 99.6% |
| 2 | 🇫🇷 France | 20.1% | 33.1% | 49.5% | 99.4% |
| 3 | 🇪🇸 Spain | 18.1% | 30.2% | 47.9% | 99.2% |
| 4 | 🇧🇷 Brazil | 9.4% | 18.4% | 33.9% | 98.0% |
| 5 | 🏴 England | 6.7% | 15.0% | 29.3% | 97.2% |
| 6 | 🇵🇹 Portugal | 5.9% | 13.2% | 27.0% | 96.6% |
| 7 | 🇳🇱 Netherlands | 4.3% | 10.9% | 24.1% | 95.9% |
| 8 | 🇩🇪 Germany | 3.6% | 9.4% | 21.1% | 94.5% |

> ### Predicted champion: 🇦🇷 **Argentina** — ~22% championship probability
>
> The top three (Argentina, France, Spain) are separated by only a few points
> and together account for ~60% of simulated titles, reflecting genuine
> uncertainty at the top rather than a runaway favourite.

*(Exact percentages vary slightly with the random seed and the size of the
Monte Carlo run; the canonical API uses 5,000 simulations.)*

## 9. Limitations

- Trained on a **synthetic, generatively-sampled** history, not live match feeds.
- The 2026 field is a **projection** — qualification, groups and squads will
  change before the tournament.
- The model **cannot** capture injuries, red cards, tactical setups, morale, or
  penalty-shootout variance beyond a simple Elo-weighted coin flip.
- The knockout bracket uses a representative seeded slotting, not FIFA's exact
  published R32 pairing table.
- All outputs are **probability-based estimates, not guarantees.**

## 10. Reproducibility

```bash
cd backend
python -m wc2026.ml.eda      # EDA
python -m wc2026.ml.train    # retrain + re-evaluate (writes artifacts/)
python -m wc2026.engine.simulate   # standalone simulation sanity check
```

Randomness is fully seeded (`numpy.random.default_rng`), so every run reproduces
the same dataset, metrics and canonical predictions.
