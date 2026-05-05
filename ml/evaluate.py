import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, classification_report,
    confusion_matrix
)
import warnings

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

def evaluate_model(model, X_test, y_test, name):
    """Evaluate a model and return a metrics dictionary."""
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else y_pred

    metrics = {
        "model": name,
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_prob)), 4),
        "report": classification_report(y_test, y_pred),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist()
    }
    return metrics

def compute_feature_importance(model, feature_names):
    """
    Extract feature importances.
    If it's a CalibratedClassifierCV or StackingClassifier, try to find an underlying tree/linear model.
    """
    importances = []
    
    # Try to extract base estimator if it's CalibratedClassifierCV
    if hasattr(model, 'calibrated_classifiers_'):
        base_model = model.calibrated_classifiers_[0].estimator
    else:
        base_model = model

    # If it's a StackingClassifier, get the random forest estimator
    if hasattr(base_model, 'named_estimators_'):
        if 'rf' in base_model.named_estimators_:
            base_model = base_model.named_estimators_['rf']
        elif 'xgb' in base_model.named_estimators_:
            base_model = base_model.named_estimators_['xgb']

    if hasattr(base_model, "feature_importances_"):
        vals = base_model.feature_importances_
        importances = sorted(
            zip(feature_names, vals.tolist()),
            key=lambda x: x[1], reverse=True
        )
    elif hasattr(base_model, "coef_"):
        vals = np.abs(base_model.coef_[0])
        importances = sorted(
            zip(feature_names, vals.tolist()),
            key=lambda x: x[1], reverse=True
        )

    return [{"feature": f, "importance": round(float(v), 6)} for f, v in importances]

def get_shap_explainer(model, X_train):
    """
    Returns a SHAP explainer for the given model if possible.
    KernelExplainer is used as fallback, but it's slow, so we prefer TreeExplainer on the base model.
    """
    if not SHAP_AVAILABLE:
        return None
        
    # Try to extract base estimator
    if hasattr(model, 'calibrated_classifiers_'):
        base_model = model.calibrated_classifiers_[0].estimator
    else:
        base_model = model

    if hasattr(base_model, 'named_estimators_'):
        if 'rf' in base_model.named_estimators_:
            base_model = base_model.named_estimators_['rf']

    try:
        # Use TreeExplainer for trees
        if hasattr(base_model, "feature_importances_"):
            explainer = shap.TreeExplainer(base_model)
            return explainer
        # Linear models
        elif hasattr(base_model, "coef_"):
            explainer = shap.LinearExplainer(base_model, X_train)
            return explainer
    except Exception as e:
        warnings.warn(f"Could not create SHAP explainer: {e}")
        
    return None
