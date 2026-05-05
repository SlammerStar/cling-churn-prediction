"""
predictor.py
============
Handles loading model artifacts and making predictions using the ml pipeline.
"""

import pickle
import json
import numpy as np
import pandas as pd
from pathlib import Path
import os
import sys

# Add ml/ to path so we can import features
ROOT_DIR = Path(__file__).parent.parent
ML_DIR = ROOT_DIR / "ml"
sys.path.insert(0, str(ML_DIR))

from features import apply_feature_engineering, preprocess_data

MODEL_DIR = ML_DIR / "artifacts"
_artifacts = None
_meta = None

def load_artifacts():
    """Load model artifacts (cached after first call)."""
    global _artifacts, _meta
    if _artifacts is None:
        pkl_path = MODEL_DIR / "model_artifacts.pkl"
        meta_path = MODEL_DIR / "model_meta.json"

        if not pkl_path.exists():
            raise FileNotFoundError(
                f"Model not found at {pkl_path}. Run ml/train.py first."
            )

        with open(pkl_path, "rb") as f:
            _artifacts = pickle.load(f)

        with open(meta_path, "r") as f:
            _meta = json.load(f)

    return _artifacts, _meta

def predict_single(input_data: dict) -> dict:
    """
    Make a churn prediction for a single customer.
    """
    artifacts, meta = load_artifacts()
    model = artifacts["model"]

    df = pd.DataFrame([input_data])
    df = apply_feature_engineering(df)
    
    X_scaled, _ = preprocess_data(df, is_training=False, artifacts=artifacts)
    
    prob = float(model.predict_proba(X_scaled)[0][1])
    prediction = int(prob >= 0.5)

    # Risk level
    if prob < 0.30:
        risk = "Low"
        risk_color = "#22c55e"
    elif prob < 0.60:
        risk = "Medium"
        risk_color = "#f59e0b"
    else:
        risk = "High"
        risk_color = "#ef4444"

    importances = meta.get("feature_importances", [])

    return {
        "churn": prediction,
        "probability": round(prob * 100, 1),
        "risk_level": risk,
        "risk_color": risk_color,
        "top_features": importances[:8],
        "model_used": meta.get("best_model", "Unknown"),
    }

def predict_batch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Make predictions for a batch of customers from a DataFrame.
    """
    artifacts, meta = load_artifacts()
    model = artifacts["model"]

    work = df.copy()
    
    # Drop target if present
    for col in ["Churn", "churn"]:
        if col in work.columns:
            work.drop(columns=[col], inplace=True)

    # Apply same processing
    work_feat = apply_feature_engineering(work)
    X_scaled, _ = preprocess_data(work_feat, is_training=False, artifacts=artifacts)

    probs = model.predict_proba(X_scaled)[:, 1]
    preds = (probs >= 0.5).astype(int)

    result = df.copy()
    result["ChurnPrediction"] = preds
    result["ChurnProbability"] = (probs * 100).round(1)
    result["RiskLevel"] = pd.cut(
        probs,
        bins=[-0.01, 0.30, 0.60, 1.01],
        labels=["Low", "Medium", "High"]
    )
    return result

def get_model_stats() -> dict:
    """Return model performance stats for the dashboard."""
    try:
        _, meta = load_artifacts()
        results = meta.get("all_results", [])
        best_name = meta.get("best_model", "")
        best = next((r for r in results if r["model"] == best_name), {})
        return {
            "best_model": best_name,
            "accuracy": best.get("accuracy", 0),
            "precision": best.get("precision", 0),
            "recall": best.get("recall", 0),
            "f1": best.get("f1", 0),
            "roc_auc": best.get("roc_auc", 0),
            "cv_auc": best.get("cv_auc_mean", 0),
            "all_models": results,
            "feature_importances": meta.get("feature_importances", []),
            "churn_rate": meta.get("churn_rate", 0),
            "n_samples": meta.get("n_samples", 0),
        }
    except Exception:
        return {}
