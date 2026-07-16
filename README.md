# 🏆 2026 FIFA World Cup Winner Predictor

A full-stack machine-learning application that rates all 48 nations of the 2026
FIFA World Cup, predicts individual matches, and runs thousands of Monte Carlo
tournament simulations to estimate every team's probability of reaching each
round — and lifting the trophy.

> ⚠️ **Disclaimer** — All figures are probability-based statistical estimates,
> not guaranteed outcomes. Real results are affected by injuries, squad changes,
> tactics, red cards, penalties and other unpredictable events.

---

## ✨ Features

| Page | What it does |
|------|--------------|
| **Home** | Predicted champion, title probability, top-5 favourites |
| **Team Predictions** | Search / filter / sort all 48 teams; per-team round-by-round probabilities, strengths & weaknesses, radar profile |
| **Match Predictor** | Win / draw / loss probabilities, expected goals, predicted score, head-to-head, key factors for any two teams |
| **Tournament Simulator** | Run 1–20,000 Monte Carlo simulations; group standings + interactive knockout bracket |
| **Bracket** | The most-likely tournament bracket, group stage → final; click any match for details |
| **Team Comparison** | Two teams side-by-side with a radar chart and metric-by-metric table |
| **Leaderboard** | Every nation ranked by championship probability |
| **Model Insights** | Accuracy, log-loss, precision/recall/F1, ROC-AUC, Brier, confusion matrix, feature importance, calibration curve, model comparison |

## 🧱 Architecture

```
2026-fifa-world-cup-final-predictor/
├── backend/                      # Python · FastAPI · scikit-learn
│   ├── wc2026/
│   │   ├── data/teams.py         # 48-team field + deterministic group draw
│   │   ├── ml/
│   │   │   ├── features.py       # shared, leakage-free feature engineering
│   │   │   ├── dataset.py        # reproducible synthetic match history
│   │   │   ├── eda.py            # exploratory data analysis
│   │   │   └── train.py          # train + evaluate + save best model
│   │   ├── engine/
│   │   │   ├── poisson.py        # Poisson scoreline model
│   │   │   ├── match.py          # single-match prediction engine
│   │   │   └── simulate.py       # Monte Carlo tournament simulation
│   │   └── api/
│   │       ├── service.py        # caching + team enrichment
│   │       └── main.py           # FastAPI REST endpoints
│   ├── artifacts/                # model.joblib + metrics.json (generated)
│   └── requirements.txt
├── frontend/                     # React · TypeScript · Tailwind · Recharts
│   └── src/{pages,components}/
├── REPORT.md                     # methodology, results, limitations, winner
└── README.md
```

## 🚀 Getting started

### 1. Backend (Python 3.10+)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m wc2026.ml.eda        # (optional) exploratory data analysis
python -m wc2026.ml.train      # train models -> backend/artifacts/
uvicorn wc2026.api.main:app --reload --port 8000
```

The API is now at **http://localhost:8000** (interactive docs at `/docs`).

### 2. Frontend (Node 18+)

```bash
cd frontend
npm install
npm run dev                    # http://localhost:5173  (proxies /api -> :8000)
```

Open **http://localhost:5173**. For a production build: `npm run build`.
To point at a non-local API, set `VITE_API_URL` (see `.env.example`).

## 🔌 API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/api/teams` | All teams (supports `?q=`, `?group=`, `?confederation=`) |
| `GET`  | `/api/teams/{id}` | Detailed stats + predictions for one team |
| `GET`  | `/api/predictions` | Championship leaderboard + favourite |
| `POST` | `/api/predict-match` | `{team_a_id, team_b_id, neutral}` → result probabilities |
| `POST` | `/api/simulate-tournament` | `{simulations, seed?}` → single bracket or aggregate probabilities |
| `GET`  | `/api/bracket` | Most-likely predicted bracket |
| `GET`  | `/api/model-metrics` | Full model evaluation report |
| `GET`  | `/api/team-comparison?team_a=&team_b=` | Side-by-side comparison |
| `GET`  | `/api/health` | Service + model status |

## 🧪 How the prediction works

1. **Data** — a curated snapshot of the 48-team field (Elo, recent form, squad
   valuation, World Cup pedigree) drives derived attacking / defensive rates.
2. **Feature engineering** — Elo difference, form difference, attack/defence
   profiles and host advantage, built by a single function shared between
   training and inference so the model always sees identical inputs.
3. **Training** — Logistic Regression, Random Forest and Gradient Boosting are
   trained on a **reproducible, leakage-free synthetic match history** and
   compared against a Poisson baseline. The best model (by log-loss) is saved.
4. **Match engine** — the trained classifier gives win/draw/loss probabilities;
   a Poisson scoreline model gives expected goals and the most-likely score.
5. **Simulation** — a Monte Carlo engine plays the full 48-team format (12 groups
   of 4 → best-32 → knockouts) thousands of times to estimate each team's
   probability of reaching every round.

> **On the data:** live match-feed scraping is intentionally not used, so the
> project runs fully offline and reproducibly. The synthetic history is sampled
> from latent team strengths; swapping in a real results feed only requires
> replacing `ml/dataset.py`. See [`REPORT.md`](REPORT.md) for full methodology.

## 📄 License / attribution

Educational project. Not affiliated with or endorsed by FIFA. Team flags are
Unicode emoji. See [`REPORT.md`](REPORT.md) for the methodology and results.
