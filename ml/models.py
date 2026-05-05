import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, StackingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import cross_val_score, StratifiedKFold
import optuna

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    from imblearn.over_sampling import SMOTE
    SMOTE_AVAILABLE = True
except ImportError:
    SMOTE_AVAILABLE = False

def apply_smote(X_train, y_train):
    """Apply SMOTE to handle class imbalance."""
    if SMOTE_AVAILABLE:
        smote = SMOTE(random_state=42)
        X_res, y_res = smote.fit_resample(X_train, y_train)
        return X_res, y_res
    return X_train, y_train

def optimize_hyperparameters(X, y, n_trials=10):
    """Use Optuna to optimize Random Forest hyperparameters as an example."""
    def objective(trial):
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 100, 300),
            'max_depth': trial.suggest_int('max_depth', 3, 10),
            'min_samples_split': trial.suggest_int('min_samples_split', 2, 10),
            'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 5)
        }
        
        clf = RandomForestClassifier(**params, random_state=42, n_jobs=-1, class_weight='balanced')
        cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
        scores = cross_val_score(clf, X, y, cv=cv, scoring='roc_auc')
        return scores.mean()

    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=n_trials)
    
    return study.best_params

def get_best_models(X_train, y_train, use_optuna=True):
    """
    Returns a dictionary of models to evaluate, including a calibrated stacking ensemble.
    """
    scale_pos = 1
    if len(y_train) > 0:
        scale_pos = max(1, int(np.sum(y_train == 0) / max(1, np.sum(y_train == 1))))
        
    models = {
        "Logistic Regression": LogisticRegression(
            C=0.1, max_iter=1000, class_weight="balanced", random_state=42
        ),
    }
    
    rf_params = {'n_estimators': 200, 'max_depth': 8, 'min_samples_leaf': 5}
    if use_optuna:
        print("  Running Optuna to optimize Random Forest...")
        try:
            rf_params = optimize_hyperparameters(X_train, y_train, n_trials=10)
            print(f"  Optuna best RF params: {rf_params}")
        except Exception as e:
            print(f"  Optuna failed, using default params. Error: {e}")
            
    rf = RandomForestClassifier(**rf_params, class_weight="balanced", random_state=42, n_jobs=-1)
    models["Random Forest"] = rf
    
    estimators = [('rf', rf), ('lr', models["Logistic Regression"])]

    if XGBOOST_AVAILABLE:
        xgb = XGBClassifier(
            n_estimators=200, max_depth=5, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            scale_pos_weight=scale_pos,
            eval_metric="logloss", random_state=42, n_jobs=-1
        )
        models["XGBoost"] = xgb
        estimators.append(('xgb', xgb))

    # Stacking Classifier
    stacking = StackingClassifier(
        estimators=estimators,
        final_estimator=LogisticRegression(C=0.1, random_state=42)
    )
    
    # Calibrated Classifier for well-calibrated probabilities
    calibrated_stacking = CalibratedClassifierCV(stacking, cv=3, method='sigmoid')
    models["Stacking Ensemble (Calibrated)"] = calibrated_stacking
    
    return models
