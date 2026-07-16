"""Train match-outcome models on REAL international results (martj42 dataset),
using a chronological train / validation / test split so accuracy is measured
the honest way — fit on the past, tested on the most recent matches.

Also caches each 2026 team's current Elo / form / goals (+ head-to-head) so the
API runs without the raw dataset.

Run:  python -m wc2026.ml.train
Outputs (backend/artifacts/):  model.joblib · metrics.json · current_form.json
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ..engine.poisson import outcome_probs
from .elo_features import FEATURE_NAMES, replay, snapshot
from .history import load_results

ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "artifacts"
CLASS_LABELS = ["Home win", "Draw", "Away win"]
VAL_START = pd.Timestamp("2021-01-01")
TEST_START = pd.Timestamp("2023-06-01")


def _roster() -> list[str]:
    from ..data.teams import load_teams  # local import avoids a load-order cycle
    return [t.name for t in load_teams()]


def _brier(y, proba):
    onehot = np.eye(proba.shape[1])[y]
    return float(np.mean(np.sum((proba - onehot) ** 2, axis=1)))


def _evaluate(y, proba):
    preds = proba.argmax(axis=1)
    return {
        "accuracy": round(float(accuracy_score(y, preds)), 4),
        "log_loss": round(float(log_loss(y, proba, labels=[0, 1, 2])), 4),
        "precision": round(float(precision_score(y, preds, average="macro", zero_division=0)), 4),
        "recall": round(float(recall_score(y, preds, average="macro", zero_division=0)), 4),
        "f1": round(float(f1_score(y, preds, average="macro", zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y, proba, multi_class="ovr", average="macro")), 4),
        "brier": round(_brier(y, proba), 4),
    }


def _poisson_proba(X):
    idx = {n: i for i, n in enumerate(FEATURE_NAMES)}
    out = []
    for row in X:
        diff = row[idx["elo_diff"]] + 100.0 * row[idx["home_advantage"]]
        lam_a = 1.35 * np.exp(0.5 * diff / 400.0)
        lam_b = 1.35 * np.exp(-0.5 * diff / 400.0)
        out.append(outcome_probs(min(lam_a, 6), min(lam_b, 6)))
    return np.asarray(out)


def _calibration(y, proba, n_bins=10):
    p, yb = proba[:, 0], (y == 0).astype(int)
    edges = np.linspace(0, 1, n_bins + 1)
    curve = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (p >= lo) & (p < hi) if hi < 1 else (p >= lo) & (p <= hi)
        if mask.sum() >= 10:
            curve.append({"predicted": round(float(p[mask].mean()), 3),
                          "observed": round(float(yb[mask].mean()), 3), "count": int(mask.sum())})
    return curve


def train() -> dict:
    X, y, dates, r = replay()

    tr = dates < VAL_START
    va = (dates >= VAL_START) & (dates < TEST_START)
    te = dates >= TEST_START
    X_tr, y_tr = X[tr], y[tr]
    X_va, y_va = X[va], y[va]
    X_te, y_te = X[te], y[te]

    models = {
        "Logistic Regression": Pipeline([("scale", StandardScaler()),
                                         ("clf", LogisticRegression(max_iter=3000, C=0.5))]),
        "Random Forest": RandomForestClassifier(n_estimators=400, max_depth=9,
                                                min_samples_leaf=30, random_state=7, n_jobs=-1),
        "Gradient Boosting": GradientBoostingClassifier(n_estimators=250, max_depth=3,
                                                        learning_rate=0.05, subsample=0.9, random_state=7),
    }
    comparison, val_ll, fitted = {}, {}, {}
    for name, model in models.items():
        model.fit(X_tr, y_tr)
        comparison[name] = _evaluate(y_te, model.predict_proba(X_te))
        val_ll[name] = _evaluate(y_va, model.predict_proba(X_va))["log_loss"]
        fitted[name] = model
    comparison["Poisson (baseline)"] = _evaluate(y_te, _poisson_proba(X_te))

    best_name = min(fitted, key=lambda n: val_ll[n])
    best = fitted[best_name]
    proba_te = best.predict_proba(X_te)
    train_eval = _evaluate(y_tr, best.predict_proba(X_tr))
    overfit = {"train_accuracy": train_eval["accuracy"], "test_accuracy": comparison[best_name]["accuracy"],
               "accuracy_gap": round(train_eval["accuracy"] - comparison[best_name]["accuracy"], 4),
               "train_log_loss": train_eval["log_loss"], "test_log_loss": comparison[best_name]["log_loss"]}

    if hasattr(best, "feature_importances_"):
        imp = best.feature_importances_
    elif isinstance(best, Pipeline):
        coef = np.abs(best.named_steps["clf"].coef_).mean(axis=0)
        imp = coef / coef.sum()
    else:
        imp = np.ones(len(FEATURE_NAMES)) / len(FEATURE_NAMES)
    importance = sorted(({"feature": f, "importance": round(float(v), 4)}
                         for f, v in zip(FEATURE_NAMES, imp)), key=lambda d: -d["importance"])
    cm = confusion_matrix(y_te, proba_te.argmax(axis=1), labels=[0, 1, 2]).tolist()

    full = load_results(played_only=True)
    metrics = {
        "best_model": best_name,
        "metrics": comparison[best_name],
        "model_comparison": comparison,
        "validation_log_loss": {k: round(v, 4) for k, v in val_ll.items()},
        "overfitting_check": overfit,
        "confusion_matrix": {"labels": CLASS_LABELS, "matrix": cm},
        "feature_importance": importance,
        "calibration_curve": _calibration(y_te, proba_te),
        "training": {
            "n_matches": int(len(X)), "n_train": int(tr.sum()),
            "n_validation": int(va.sum()), "n_test": int(te.sum()),
            "features": FEATURE_NAMES, "class_labels": CLASS_LABELS,
            "history_span": f"{full.date.min().date()} to {full.date.max().date()}",
            "total_internationals": int(len(full)),
            "split": "chronological — train <2021, validation 2021–mid-2023, test mid-2023 onward",
        },
        "data_sources": [
            "Real international results 1872–2026 — martj42/international_results (49k+ matches)",
            "World-Football-style Elo replayed over the full history (importance & margin weighted)",
            "Real FIFA ranking points (July 2026) & World Cup pedigree — data/teams.py",
            "Fan sentiment (curated, pluggable to X API) applied as a current-context adjustment",
        ],
        "limitations": [
            "Injuries/availability & fan sentiment are current-context adjustments, not historical features.",
            "Three-way outcome (incl. draws) is inherently hard — strong models sit ~50-55% accuracy.",
            "Elo cannot see red cards, in-game tactics or shootout variance directly.",
            "Probabilities are calibrated estimates, not guarantees.",
        ],
    }

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": best, "features": FEATURE_NAMES, "class_labels": CLASS_LABELS,
                 "name": best_name}, ARTIFACT_DIR / "model.joblib")
    (ARTIFACT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))
    snap = snapshot(r, _roster(), as_of=str(full.date.max().date()))
    (ARTIFACT_DIR / "current_form.json").write_text(json.dumps(snap, indent=2))

    # Rebuild the real-bracket cache with fresh Elo + the just-trained model.
    from ..data import teams as teams_mod
    from ..data.wc2026 import build_bracket, has_raw, save_cache
    from ..engine.match import _load_model, predict_match
    teams_mod._current_form.cache_clear()
    _load_model.cache_clear()
    if has_raw():
        save_cache(build_bracket(teams_mod.load_teams(), predict_match))
    return metrics


if __name__ == "__main__":
    m = train()
    t = m["training"]
    print(f"Best model (validation-selected): {m['best_model']}")
    print(f"Trained on {t['total_internationals']:,} real internationals ({t['history_span']})")
    print(f"Split: {t['n_train']:,} train / {t['n_validation']:,} val / {t['n_test']:,} test\n")
    for name, mm in m["model_comparison"].items():
        print(f"  {name:22s} acc={mm['accuracy']:.3f} logloss={mm['log_loss']:.3f} auc={mm['roc_auc']:.3f}")
    o = m["overfitting_check"]
    print(f"\nOverfitting — train {o['train_accuracy']:.3f} vs test {o['test_accuracy']:.3f} (gap {o['accuracy_gap']:+.3f})")
