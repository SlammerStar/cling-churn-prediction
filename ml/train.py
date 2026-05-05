import os
import json
import pickle
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold

from features import load_data, apply_feature_engineering, preprocess_data
from models import apply_smote, get_best_models
from evaluate import evaluate_model, compute_feature_importance

MODEL_DIR = Path(__file__).parent / "artifacts"
DATA_DIR = Path(__file__).parent / "data"
DATA_FILE = DATA_DIR / "WA_Fn-UseC_-Telco-Customer-Churn.csv"

def train_and_save():
    print("=" * 60)
    print("  CLING CHURN PREDICTION — TRAINING PIPELINE")
    print("=" * 60)

    # 1. Load Data
    print("\n[1/5] Loading real Telco Customer Churn dataset...")
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset not found at {DATA_FILE}. Please download it first.")
    
    df = load_data(DATA_FILE)
    print(f"      Samples: {len(df)} | Columns: {len(df.columns)}")

    # 2. Feature Engineering & Preprocessing
    print("\n[2/5] Applying advanced feature engineering...")
    df = apply_feature_engineering(df)
    
    print("      Preprocessing data (encoding, scaling)...")
    X, y, feature_names, encoders, scaler = preprocess_data(df, is_training=True)
    print(f"      Features generated: {len(feature_names)}")

    # 3. Splitting and SMOTE
    print("\n[3/5] Train/Test Split & SMOTE Balancing...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=42
    )
    print(f"      Train distribution before SMOTE: 0: {sum(y_train==0)}, 1: {sum(y_train==1)}")
    
    X_train_res, y_train_res = apply_smote(X_train, y_train)
    print(f"      Train distribution after SMOTE: 0: {sum(y_train_res==0)}, 1: {sum(y_train_res==1)}")

    # 4. Training Models
    print("\n[4/5] Training models & tuning hyperparameters...")
    candidates = get_best_models(X_train_res, y_train_res, use_optuna=True)
    
    results = []
    best_model = None
    best_auc = 0.0
    best_name = ""

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    for name, model in candidates.items():
        print(f"  Training {name}...")
        model.fit(X_train_res, y_train_res)
        metrics = evaluate_model(model, X_test, y_test, name)

        # Cross-val AUC
        cv_scores = cross_val_score(model, X_train_res, y_train_res, cv=cv, scoring="roc_auc", n_jobs=-1)
        metrics["cv_auc_mean"] = round(float(cv_scores.mean()), 4)
        metrics["cv_auc_std"] = round(float(cv_scores.std()), 4)
        results.append(metrics)

        print(f"    AUC={metrics['roc_auc']:.4f}  F1={metrics['f1']:.4f}  CV-AUC={metrics['cv_auc_mean']:.4f}")

        if metrics["roc_auc"] > best_auc:
            best_auc = metrics["roc_auc"]
            best_model = model
            best_name = name

    print(f"\n✅ Best model: {best_name} (AUC={best_auc:.4f})")

    # 5. Feature importances and Artifacts
    print("\n[5/5] Extracting feature importances & saving artifacts...")
    importance_list = compute_feature_importance(best_model, feature_names)

    MODEL_DIR.mkdir(exist_ok=True, parents=True)

    artifacts = {
        "model": best_model,
        "scaler": scaler,
        "encoders": encoders,
        "feature_names": feature_names,
        "best_model_name": best_name,
        "X_train_sample": X_train_res[:100] # Save a small sample for SHAP explainers later if needed
    }
    
    with open(MODEL_DIR / "model_artifacts.pkl", "wb") as f:
        pickle.dump(artifacts, f)

    meta = {
        "best_model": best_name,
        "feature_names": feature_names,
        "feature_importances": importance_list[:15],
        "all_results": results,
        "churn_rate": float(y.mean()),
        "n_samples": len(df),
    }
    
    with open(MODEL_DIR / "model_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\n✅ Artifacts saved to {MODEL_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    train_and_save()
