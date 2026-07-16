# Final Report — 2026 FIFA World Cup Winner Predictor

*Methodology, results, limitations, and the predicted winner.*

---

## 1. Objective

Estimate, as calibrated probabilities, how far each of the 48 teams in the 2026
FIFA World Cup is likely to progress — trained on **real historical match
results** and reported against the **real recorded 2026 tournament**.

## 2. Data

- **Match history:** [martj42/international_results](https://github.com/martj42/international_results)
  — **49,518 real internationals, 1872–2026** (results.csv + shootouts.csv). This
  dataset also contains the recorded 2026 World Cup (104 matches), through the
  semifinals.
- **2026 field & draw:** the real Final Draw (5 Dec 2025), 48 teams, groups A–L.
- **FIFA ranking points** (July 2026) and **World Cup pedigree** — real; eight
  lower-ranked qualifiers use best-estimate points (flagged in `data/teams.py`).
- **Fan sentiment** (positivity, buzz, momentum) — curated snapshot behind a
  pluggable `SentimentProvider`; **squad availability** — injury/fitness proxy.

## 3. Elo replay & feature engineering

Every match in history is replayed into a **World-Football-style Elo** —
importance-weighted (World Cup > continental > qualifier > friendly) and
goal-margin-weighted, with a home-advantage term. Ratings settle in a realistic
band (top sides ≈ 2050–2160).

Six **leakage-free** features are built from *pre-match* state only, then state
is updated after the result:

| Feature | Meaning |
|---------|---------|
| `elo_diff` | home Elo − away Elo |
| `form_diff` | recent-form difference (last-10 points) |
| `gf_diff` / `ga_diff` | rolling goals-for / goals-against difference |
| `h2h_diff` | recent head-to-head goal difference |
| `home_advantage` | 1 at home, 0 at a neutral venue |

The **same** `build_inference_row()` runs at prediction time. Signals absent from
match history — **squad availability (injuries)** and **fan sentiment** — are
applied as small, documented adjustments to each side's effective Elo, so the
model still "considers" them without fabricating historical values.

## 4. Training, validation & testing (chronological)

The honest way to test a match model is on the **future**: fit on the past, test
on the most recent games. Split by date:

- **Train:** before 2021 — 26,607 matches
- **Validation:** 2021 → mid-2023 — 2,311 matches (model selection)
- **Test:** mid-2023 → 2026 — 3,482 matches (held out)

| Model | Accuracy | Log-loss | ROC-AUC | Brier |
|-------|:-------:|:--------:|:-------:|:-----:|
| **Logistic Regression** ⭐ | **0.606** | **0.863** | 0.744 | 0.507 |
| Random Forest | 0.605 | 0.866 | 0.746 | 0.508 |
| Gradient Boosting | 0.606 | 0.863 | 0.745 | 0.507 |
| Poisson (baseline) | 0.607 | 0.894 | 0.740 | 0.523 |

**Overfitting check:** train accuracy **0.582** vs test **0.606** (gap
**−0.024** — the test set is, if anything, slightly *easier*; the model is not
memorising). Precision 0.40 / recall 0.51 / F1 0.44 (macro, three classes).

**Feature importance:** `elo_diff` (0.50) ≫ `ga_diff` (0.16) ≈ `home_advantage`
(0.13) ≈ `h2h_diff` (0.12) > `form_diff` (0.06) > `gf_diff` (0.03).

Training on real history lifted three-way accuracy from ~0.49 (synthetic) to
**~0.61** on real held-out internationals — strong for an outcome that includes
draws (sharp bookmaker models sit ~50–55%).

## 5. Match prediction & simulation

- **Match engine:** the real-trained classifier gives win/draw/loss; a Poisson
  model gives expected goals + scoreline; the UI shows **real past meetings**
  (from the dataset) and the key factors driving the call.
- **Monte Carlo:** plays the full 48-team format (12 groups → best-32 →
  knockouts, penalty tiebreaks) thousands of times on real Elo strengths.

## 6. The bracket — real results, predicted finale

The Bracket page is built from the **actual recorded 2026 results**:

- **Group stage → semifinals:** real scorelines for all 30 knockout matches
  (penalty shootouts resolved from shootouts.csv). Examples: Spain 3-0 Austria,
  Germany 1-1 Paraguay (Paraguay on pens), France 0-2 Spain (SF).
- **Final (Sun 19 Jul) & third-place (Sat 18 Jul):** genuinely **unplayed** as of
  the snapshot → the model predicts **🇪🇸 Spain 1-0 🇦🇷 Argentina** (Spain 48% /
  draw 26% / Argentina 26%) and **🇫🇷 France** over 🏴 England for third.

## 7. Results — the predicted winner 🏆

From **5,000 Monte Carlo simulations** on the real Elo-replayed strengths:

| # | Team | Win title | Reach final | Advance from group |
|---|------|:--------:|:-----------:|:------------------:|
| 1 | 🇪🇸 **Spain** | **40.9%** | 53.7% | 99.9% |
| 2 | 🇦🇷 Argentina | 20.2% | 35.2% | 99.7% |
| 3 | 🇫🇷 France | 9.7% | 19.2% | 99.3% |
| 4 | 🇨🇴 Colombia | 5.5% | 12.8% | 95.8% |
| 5 | 🇵🇹 Portugal | 3.6% | 9.5% | 96.1% |
| 6 | 🇧🇷 Brazil | 3.4% | 9.7% | 97.3% |

> ### Predicted champion: 🇪🇸 **Spain** — ~41%
>
> Spain carries the highest real Elo in the field and, in the recorded data, has
> already won its semifinal 2-0 over France. The model makes them a clear
> favourite over Argentina for the unplayed final.

## 8. Limitations

- Injuries/availability and fan sentiment are **current-context adjustments**,
  not historical features.
- Eight lower-ranked qualifiers use **best-estimate** FIFA points.
- A dominant Elo leader compounds over a single-elimination bracket, so the
  favourite's title odds sit high; single matches carry more variance than any
  model captures.
- No modelling of red cards, in-game tactics or shootout skill directly.
- **All outputs are probability-based estimates, not guarantees.**

## 9. Reproducibility

```bash
cd backend
git clone https://github.com/martj42/international_results.git data_raw   # raw data
python -m wc2026.ml.eda            # EDA on real matches
python -m wc2026.ml.train          # Elo replay + train (writes artifacts/)
python -m wc2026.ml.elo_features   # current Elo leaders
```

Deterministic given the dataset snapshot; the committed artifacts let the API run
without the raw data.
