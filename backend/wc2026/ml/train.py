"""Train and compare match-outcome models with a proper train / validation /
test protocol, pick the best on validation, and report held-out test metrics
plus an overfitting check.

Run:  python -m wc2026.ml.train
Outputs (backend/artifacts/):  model.joblib · metrics.json
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
from .features import FEATURE_NAMES, HOME_ADV_RATING

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
    idx = {n: i for i, n in enumerate(FEATURE_NAMES)}
    out = []
    for row in X:
        lam_a, lam_b = expected_goals(
            rating_a=row[idx["rating_diff"]], rating_b=0.0,
            home_advantage=int(round(row[idx["home_advantage"]])),
            attack_a=row[idx["attack_a"]], defense_a=row[idx["defense_a"]],
            attack_b=row[idx["attack_b"]], defense_b=row[idx["defense_b"]],
        )
        out.append(outcome_probs(lam_a, lam_b))
    return np.asarray(out)


def _calibration(y_true: np.ndarray, proba: np.ndarray, n_bins: int = 10) -> list[dict]:
    p, y = proba[:, 0], (y_true == 0).astype(int)
    edges = np.linspace(0, 1, n_bins + 1)
    curve = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (p >= lo) & (p < hi) if hi < 1 else (p >= lo) & (p <= hi)
        if mask.sum() >= 5:
            curve.append({"predicted": round(float(p[mask].mean()), 3),
                          "observed": round(float(y[mask].mean()), 3),
                          "count": int(mask.sum())})
    return curve


def train() -> dict:
    X, y, _, _, feat_names = build_training_data()

    # 60 / 20 / 20 train / validation / test split (stratified).
    X_tr, X_tmp, y_tr, y_tmp = train_test_split(X, y, test_size=0.40, random_state=7, stratify=y)
    X_val, X_te, y_val, y_te = train_test_split(X_tmp, y_tmp, test_size=0.50, random_state=7, stratify=y_tmp)

    models = {
        "Logistic Regression": Pipeline([
            ("scale", StandardScaler()),
            ("clf", LogisticRegression(max_iter=3000, C=0.5)),
        ]),
        "Random Forest": RandomForestClassifier(
            n_estimators=350, max_depth=8, min_samples_leaf=20, random_state=7, n_jobs=-1),
        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=200, max_depth=3, learning_rate=0.04, subsample=0.9, random_state=7),
    }

    comparison, val_scores, fitted = {}, {}, {}
    for name, model in models.items():
        model.fit(X_tr, y_tr)
        comparison[name] = _evaluate(y_te, model.predict_proba(X_te))         # held-out test
        val_scores[name] = _evaluate(y_val, model.predict_proba(X_val))["log_loss"]
        fitted[name] = model
    comparison["Poisson (baseline)"] = _evaluate(y_te, _poisson_proba(X_te))

    # Model selection on VALIDATION log-loss (never the test set).
    best_name = min(fitted, key=lambda n: val_scores[n])
    best_model = fitted[best_name]
    best_proba_te = best_model.predict_proba(X_te)

    # Overfitting check: train vs test gap for the chosen model.
    train_eval = _evaluate(y_tr, best_model.predict_proba(X_tr))
    overfit = {
        "train_accuracy": train_eval["accuracy"],
        "test_accuracy": comparison[best_name]["accuracy"],
        "accuracy_gap": round(train_eval["accuracy"] - comparison[best_name]["accuracy"], 4),
        "train_log_loss": train_eval["log_loss"],
        "test_log_loss": comparison[best_name]["log_loss"],
    }

    if hasattr(best_model, "feature_importances_"):
        imp = best_model.feature_importances_
    elif isinstance(best_model, Pipeline):
        coef = np.abs(best_model.named_steps["clf"].coef_).mean(axis=0)
        imp = coef / coef.sum()
    else:
        imp = np.ones(len(feat_names)) / len(feat_names)
    importance = sorted(({"feature": f, "importance": round(float(v), 4)}
                         for f, v in zip(feat_names, imp)), key=lambda d: -d["importance"])

    cm = confusion_matrix(y_te, best_proba_te.argmax(axis=1), labels=[0, 1, 2]).tolist()

    metrics = {
        "best_model": best_name,
        "metrics": comparison[best_name],
        "model_comparison": comparison,
        "validation_log_loss": {k: round(v, 4) for k, v in val_scores.items()},
        "overfitting_check": overfit,
        "confusion_matrix": {"labels": CLASS_LABELS, "matrix": cm},
        "feature_importance": importance,
        "calibration_curve": _calibration(y_te, best_proba_te),
        "training": {
            "n_matches": int(len(X)), "n_train": int(len(X_tr)),
            "n_validation": int(len(X_val)), "n_test": int(len(X_te)),
            "features": feat_names, "class_labels": CLASS_LABELS,
        },
        "data_sources": [
            "Real 2026 Final Draw (5 Dec 2025) — FIFA.com / Wikipedia",
            "Real FIFA/Coca-Cola Men's World Ranking points (July 2026 snapshot)",
            "World Cup titles & appearances — historical record",
            "Fan sentiment — social-media positivity/buzz (curated, pluggable to X API)",
            "Reproducible synthetic match history sampled from latent team strengths",
        ],
        "limitations": [
            "Trained on a synthetic, generatively-sampled history — not live match feeds.",
            "Eight lower-ranked qualifiers use best-estimate FIFA points (outside the public top-60).",
            "Availability (injuries) and fan sentiment are curated snapshots, not live feeds.",
            "Cannot model red cards, in-game tactics or penalty-shootout variance directly.",
            "Probabilities are calibrated estimates, not guarantees.",
        ],
    }

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": best_model, "features": feat_names,
                 "home_adv_rating": HOME_ADV_RATING, "class_labels": CLASS_LABELS,
                 "name": best_name}, ARTIFACT_DIR / "model.joblib")
    (ARTIFACT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    m = train()
    print(f"Best model (by validation log-loss): {m['best_model']}\n")
    for name, mm in m["model_comparison"].items():
        print(f"  {name:22s} acc={mm['accuracy']:.3f} logloss={mm['log_loss']:.3f} "
              f"auc={mm['roc_auc']:.3f} brier={mm['brier']:.3f}")
    o = m["overfitting_check"]
    print(f"\nOverfitting check — train acc {o['train_accuracy']:.3f} vs test "
          f"{o['test_accuracy']:.3f} (gap {o['accuracy_gap']:+.3f})")
    print(f"Saved model + metrics to {ARTIFACT_DIR}")
