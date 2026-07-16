"""Train and compare several match-outcome models, evaluate them with proper
scoring rules, and persist the best model plus a metrics report.

Run:  python -m wc2026.ml.train
Outputs (backend/artifacts/):
  model.joblib     best calibrated classifier + metadata
  metrics.json     full evaluation report consumed by /api/model-metrics
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ..engine.poisson import expected_goals, outcome_probs
from .dataset import build_training_data
from .features import FEATURE_NAMES, HOME_ADV_ELO

ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "artifacts"
CLASS_LABELS = ["A win", "Draw", "B win"]


def _multiclass_brier(y_true: np.ndarray, proba: np.ndarray) -> float:
    onehot = np.eye(proba.shape[1])[y_true]
    return float(np.mean(np.sum((proba - onehot) ** 2, axis=1)))


def _evaluate(y_true: np.ndarray, proba: np.ndarray) -> dict:
    preds = proba.argmax(axis=1)
    return {
        "accuracy": round(float(accuracy_score(y_true, preds)), 4),
        "log_loss": round(float(log_loss(y_true, proba, labels=[0, 1, 2])), 4),
        "precision": round(float(precision_score(y_true, preds, average="macro", zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, preds, average="macro", zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, preds, average="macro", zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, proba, multi_class="ovr", average="macro")), 4),
        "brier": round(_multiclass_brier(y_true, proba), 4),
    }


def _poisson_proba(X: np.ndarray) -> np.ndarray:
    """Analytic Poisson baseline scored from the same feature rows."""
    idx = {n: i for i, n in enumerate(FEATURE_NAMES)}
    out = []
    for row in X:
        lam_a, lam_b = expected_goals(
            elo_a=row[idx["elo_diff"]], elo_b=0.0,
            home_advantage=int(round(row[idx["home_advantage"]])),
            attack_a=row[idx["attack_a"]], defense_a=row[idx["defense_a"]],
            attack_b=row[idx["attack_b"]], defense_b=row[idx["defense_b"]],
        )
        out.append(outcome_probs(lam_a, lam_b))
    return np.asarray(out)


def _calibration(y_true: np.ndarray, proba: np.ndarray, n_bins: int = 10) -> list[dict]:
    """Reliability of P(A win) as a one-vs-rest binary problem."""
    p = proba[:, 0]
    y = (y_true == 0).astype(int)
    edges = np.linspace(0, 1, n_bins + 1)
    curve = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (p >= lo) & (p < hi) if hi < 1 else (p >= lo) & (p <= hi)
        if mask.sum() >= 5:
            curve.append({
                "predicted": round(float(p[mask].mean()), 3),
                "observed": round(float(y[mask].mean()), 3),
                "count": int(mask.sum()),
            })
    return curve


def train() -> dict:
    X, y, _, _, feat_names = build_training_data()
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=7, stratify=y)

    models = {
        "Logistic Regression": Pipeline([
            ("scale", StandardScaler()),
            ("clf", LogisticRegression(max_iter=2000, C=1.0)),
        ]),
        "Random Forest": RandomForestClassifier(
            n_estimators=300, max_depth=9, min_samples_leaf=12, random_state=7, n_jobs=-1),
        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=250, max_depth=3, learning_rate=0.05, random_state=7),
    }

    comparison = {}
    fitted = {}
    for name, model in models.items():
        model.fit(X_tr, y_tr)
        proba = model.predict_proba(X_te)
        comparison[name] = _evaluate(y_te, proba)
        fitted[name] = model

    # Poisson analytic baseline (no fitting required).
    comparison["Poisson (baseline)"] = _evaluate(y_te, _poisson_proba(X_te))

    # Pick the best fitted classifier by log loss (a proper scoring rule).
    best_name = min(fitted, key=lambda n: comparison[n]["log_loss"])
    best_model = fitted[best_name]
    best_proba = best_model.predict_proba(X_te)

    # Feature importance (tree models expose it; else use |LR coefficients|).
    if hasattr(best_model, "feature_importances_"):
        imp = best_model.feature_importances_
    elif isinstance(best_model, Pipeline):
        coef = np.abs(best_model.named_steps["clf"].coef_).mean(axis=0)
        imp = coef / coef.sum()
    else:
        imp = np.ones(len(feat_names)) / len(feat_names)
    importance = sorted(
        ({"feature": f, "importance": round(float(v), 4)} for f, v in zip(feat_names, imp)),
        key=lambda d: -d["importance"],
    )

    cm = confusion_matrix(y_te, best_proba.argmax(axis=1), labels=[0, 1, 2]).tolist()

    metrics = {
        "best_model": best_name,
        "metrics": comparison[best_name],
        "model_comparison": comparison,
        "confusion_matrix": {"labels": CLASS_LABELS, "matrix": cm},
        "feature_importance": importance,
        "calibration_curve": _calibration(y_te, best_proba),
        "training": {
            "n_matches": int(len(X)),
            "n_train": int(len(X_tr)),
            "n_test": int(len(X_te)),
            "features": feat_names,
            "class_labels": CLASS_LABELS,
        },
        "data_sources": [
            "Curated 2026 field: Elo ratings, recent form, squad valuations, World Cup pedigree",
            "Reproducible synthetic match history generated from latent team strengths",
        ],
        "limitations": [
            "Trained on a synthetic, generatively-sampled history — not live match feeds.",
            "The 2026 field is a projection; qualification and squads will change.",
            "Cannot model injuries, red cards, tactics, penalty-shootout variance or morale.",
            "Probabilities are calibrated estimates, not guarantees.",
        ],
    }

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"model": best_model, "features": feat_names, "home_adv_elo": HOME_ADV_ELO,
         "class_labels": CLASS_LABELS, "name": best_name},
        ARTIFACT_DIR / "model.joblib",
    )
    (ARTIFACT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    m = train()
    print(f"Best model: {m['best_model']}")
    for name, mm in m["model_comparison"].items():
        print(f"  {name:22s} acc={mm['accuracy']:.3f} logloss={mm['log_loss']:.3f} "
              f"auc={mm['roc_auc']:.3f} brier={mm['brier']:.3f}")
    print(f"\nSaved model + metrics to {ARTIFACT_DIR}")
