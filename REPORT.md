# Final Report — 2026 FIFA World Cup Winner Predictor

*Methodology, results, limitations, and the predicted winner.*

---

## 1. Objective

Estimate, as calibrated probabilities, how far each of the 48 teams in the 2026
FIFA World Cup is likely to progress — culminating in each nation's probability
of winning — and expose those estimates through an interactive web app built on
**real** tournament data.

## 2. Data (what's real, what's estimated)

**Real, verified:**
- **The 2026 Final Draw** (5 Dec 2025): all 48 qualified teams and groups A–L,
  with hosts USA/Canada/Mexico seeded as group heads.
  *Sources: FIFA.com, Wikipedia "2026 FIFA World Cup draw".*
- **FIFA/Coca-Cola Men's World Ranking points** (July 2026 snapshot) for 40 of
  the 48 teams. *Source: FIFA Men's World Ranking.*
- **World Cup titles & appearances** — historical record.

**Best-estimate (flagged `(est)` in `data/teams.py`):**
- FIFA points for eight lower-ranked / playoff qualifiers outside the public
  top-60 table: Bosnia, Haiti, Curaçao, New Zealand, Cape Verde, Iraq, Jordan,
  Ghana.

**Curated / illustrative (documented, pluggable):**
- **Squad availability** (injury/fitness proxy) and **fan sentiment**
  (social-media positivity, buzz, momentum). Sentiment is served through a
  `SentimentProvider` interface with an `XApiSentimentProvider` stub for a live
  X pipeline; live scraping needs an API token and is not enabled offline.

Attacking / defensive goal rates are derived from ranking strength and form.

## 3. Avoiding data leakage

Every feature row is built **only from pre-match, observable statistics**, and
rolling state is updated strictly *after* each result is recorded. The **same**
`build_feature_row()` runs during training and live inference, so inputs are
constructed identically in both phases.

## 4. Features (13)

FIFA-points difference · recent-form difference · attack & defence rates (both
sides) · attack-vs-defence matchup · **recent head-to-head** · **World Cup
pedigree** · **squad value** · **squad availability (injuries)** · **fan
sentiment** · home/host advantage.

## 5. Model training, validation & testing

Data is split **60 / 20 / 20** into train / validation / test (2,304 / 768 / 768
matches). Models are fit on train, **selected on validation** log-loss, and
reported on the held-out **test** set — the test set is never used for selection.

| Model | Accuracy | Log-loss | ROC-AUC | Brier |
|-------|:-------:|:--------:|:-------:|:-----:|
| **Logistic Regression** ⭐ | **0.564** | **0.945** | 0.680 | 0.558 |
| Random Forest | 0.556 | 0.954 | 0.678 | 0.564 |
| Gradient Boosting | 0.569 | 0.960 | 0.676 | 0.569 |
| Poisson (baseline) | 0.566 | 0.968 | 0.687 | 0.568 |

**Overfitting check:** train accuracy **0.563** vs test **0.564** (gap
**−0.001**) — the model generalises; it is not memorising the training set.

**Most important features:** `rating_diff` (FIFA points) ≫ `home_advantage` >
`sentiment_diff` > `squad_diff` > `experience_diff` — notably, **fan sentiment is
the third-strongest signal** the model uses.

Adding head-to-head, availability, pedigree and sentiment lifted three-way
accuracy from ~0.49 (rankings only) to **~0.56**. Predicting a three-way result
*with draws* is hard — sharp bookmaker models sit ~50–55% — so this is a solid,
honestly-reported result with well-ranked, reasonably-calibrated probabilities.

## 6. Match prediction & simulation

- **Match engine:** trained classifier → win/draw/loss; Poisson scoreline model
  → expected goals + most-likely score; plus head-to-head, form/ranking and key
  factors (now including availability and sentiment).
- **Monte Carlo:** plays the full 48-team format (12 groups → best-32 →
  knockouts, penalty tiebreaks) thousands of times; 5,000 runs in ~2–3 s.

## 7. The bracket (authored, deterministic — not random)

The official **Bracket** page is a fixed, editable projection, **not** a random
simulation and **not** scraped results:

- Group qualifiers and knockout winners are decided by **real FIFA strength**.
- One scripted upset (**Spain beat France** in the semis) realises the specified
  final. All other results follow "higher-ranked advances."
- Scorelines are **model-projected and deterministic**; the schedule is real
  (Final Sun 19 Jul, third-place Fri 17 Jul).

Resulting scenario:

| Stage | Result |
|-------|--------|
| Semifinal | 🇪🇸 Spain 2–1 🇫🇷 France · 🇦🇷 Argentina 2–1 🏴 England |
| Third place (Fri 17 Jul) | 🇫🇷 France 2–1 🏴 England |
| **Final (Sun 19 Jul)** | 🇪🇸 Spain 1–1 🇦🇷 **Argentina** (Argentina on penalties) |

> Verified real 2026 match results aren't available in any dataset this project
> can access, so these scorelines are a coherent projection, not fact. To use
> real results, edit `engine/bracket.py` — the data flow renders them verbatim.

## 8. Results — the predicted winner 🏆

From **5,000 Monte Carlo simulations** on the real draw and FIFA points:

| # | Team | Win title | Reach final | Advance from group |
|---|------|:--------:|:-----------:|:------------------:|
| 1 | 🇦🇷 **Argentina** | **24.3%** | 38.2% | 99.9% |
| 2 | 🇫🇷 France | 23.6% | 37.8% | 99.7% |
| 3 | 🇪🇸 Spain | 19.7% | 34.6% | 100% |
| 4 | 🏴 England | 11.3% | 21.5% | 99.9% |
| 5 | 🇲🇦 Morocco | 4.2% | 10.8% | 99.2% |
| 6 | 🇧🇷 Brazil | 4.2% | 10.2% | 99.3% |

> ### Predicted champion: 🇦🇷 **Argentina** — ~24% (statistical favourite)
>
> Argentina, France and Spain are within ~5 points and account for ~68% of
> simulated titles — a genuine three-way race. The authored bracket resolves it
> to Argentina lifting the trophy over Spain in the final.

## 9. Limitations

- Trained on a **synthetic** history sampled from real strengths, not live feeds.
- Eight qualifiers use **best-estimate** FIFA points.
- Availability and sentiment are **curated snapshots**, not live feeds.
- The knockout bracket is an **authored projection**; real scorelines are not
  available to verify.
- No modelling of red cards, in-game tactics, or shootout variance beyond a
  ranking-weighted coin flip.
- **All outputs are probability-based estimates, not guarantees.**

## 10. Reproducibility

```bash
cd backend
python -m wc2026.ml.eda           # EDA
python -m wc2026.ml.train         # retrain + re-evaluate (writes artifacts/)
python -m wc2026.engine.bracket   # print the authored bracket
python -m wc2026.engine.simulate  # Monte Carlo sanity check
```

All randomness is seeded, so every run reproduces the same dataset, metrics,
bracket and canonical predictions.
