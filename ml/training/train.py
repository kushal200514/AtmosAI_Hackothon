"""
AtmosAI LightGBM Training Pipeline
Performs chronological train/val/test splitting, trains multi-horizon models,
computes metrics vs. persistence baseline, and persists artifacts.
"""
import os
import sys
import json
import joblib
import numpy as np
import pandas as pd

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score

from ml.preprocessing.features import FEATURE_COLUMNS, HORIZONS

def train_models(features_csv: str = None, artifacts_dir: str = None):
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    ml_root = os.path.dirname(curr_dir)

    if features_csv is None:
        features_csv = os.path.join(ml_root, "data", "bengaluru_features.csv")
    if artifacts_dir is None:
        artifacts_dir = os.path.join(ml_root, "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)

    print(f"Loading engineered dataset from {features_csv}...")
    df = pd.read_csv(features_csv)
    n_samples = len(df)
    
    # 1. Strictly Chronological Split (No random shuffling to prevent future leakage)
    train_end = int(n_samples * 0.70)
    val_end = int(n_samples * 0.85)

    df_train = df.iloc[:train_end].copy()
    df_val = df.iloc[train_end:val_end].copy()
    df_test = df.iloc[val_end:].copy()

    print(f"Dataset split chronologically:")
    print(f"  Training set:   {len(df_train)} samples ({df_train['timestamp'].iloc[0]} -> {df_train['timestamp'].iloc[-1]})")
    print(f"  Validation set: {len(df_val)} samples ({df_val['timestamp'].iloc[0]} -> {df_val['timestamp'].iloc[-1]})")
    print(f"  Test set:       {len(df_test)} samples ({df_test['timestamp'].iloc[0]} -> {df_test['timestamp'].iloc[-1]})")

    X_train = df_train[FEATURE_COLUMNS]
    X_val = df_val[FEATURE_COLUMNS]
    X_test = df_test[FEATURE_COLUMNS]

    # Persistence baseline for test set: y_hat(t+h) = y(t)
    # The current PM2.5 observation at prediction time is pm25
    y_test_persistence = df_test["pm25"].values

    all_metrics = {}
    feature_importance_all = {}

    for h in HORIZONS:
        target_col = f"target_{h}h"
        y_train = df_train[target_col]
        y_val = df_val[target_col]
        y_test = df_test[target_col]

        print(f"\n==========================================")
        print(f"Training LightGBM model for Horizon: +{h} Hours")
        print(f"==========================================")

        model = LGBMRegressor(
            n_estimators=180,
            learning_rate=0.035,
            num_leaves=24,
            max_depth=5,
            subsample=0.85,
            colsample_bytree=0.85,
            min_child_samples=15,
            random_state=42,
            verbosity=-1
        )

        model.fit(
            X_train, 
            y_train,
            eval_set=[(X_val, y_val)]
        )

        # Predictions on held-out test set
        y_pred = model.predict(X_test)

        # Compute Metrics: LightGBM vs. Persistence Baseline
        mae_lgbm = float(mean_absolute_error(y_test, y_pred))
        rmse_lgbm = float(root_mean_squared_error(y_test, y_pred))
        r2_lgbm = float(r2_score(y_test, y_pred))

        mae_persist = float(mean_absolute_error(y_test, y_test_persistence))
        rmse_persist = float(root_mean_squared_error(y_test, y_test_persistence))
        r2_persist = float(r2_score(y_test, y_test_persistence))

        mae_improvement = float(((mae_persist - mae_lgbm) / mae_persist) * 100.0)

        # Residual standard error for confidence interval estimation
        residuals = y_test - y_pred
        residual_std = float(np.std(residuals))

        print(f"Horizon +{h}h Results on Out-of-Sample Test Set:")
        print(f"  LightGBM    -> MAE: {mae_lgbm:.2f} ug/m3 | RMSE: {rmse_lgbm:.2f} | R2: {r2_lgbm:.3f}")
        print(f"  Persistence -> MAE: {mae_persist:.2f} ug/m3 | RMSE: {rmse_persist:.2f} | R2: {r2_persist:.3f}")
        print(f"  Improvement over Persistence: {mae_improvement:.1f}%")

        all_metrics[f"{h}h"] = {
            "horizon_hours": h,
            "lgbm": {
                "mae": round(mae_lgbm, 2),
                "rmse": round(rmse_lgbm, 2),
                "r2": round(r2_lgbm, 3),
                "residual_std": round(residual_std, 2)
            },
            "persistence_baseline": {
                "mae": round(mae_persist, 2),
                "rmse": round(rmse_persist, 2),
                "r2": round(r2_persist, 3)
            },
            "mae_improvement_pct": round(mae_improvement, 1)
        }

        # Feature importances
        importances = model.feature_importances_
        feature_importance_all[f"{h}h"] = {
            feat: int(imp) for feat, imp in sorted(zip(FEATURE_COLUMNS, importances), key=lambda x: x[1], reverse=True)
        }

        # Save model artifact
        model_filename = os.path.join(artifacts_dir, f"lgbm_pm25_{h}h.joblib")
        joblib.dump(model, model_filename)
        print(f"Saved model artifact -> {model_filename}")

    # Save summary metrics and feature names
    metrics_path = os.path.join(artifacts_dir, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump({
            "model_family": "LightGBM Regression",
            "model_version": "1.0.0",
            "dataset_info": {
                "location": "Bengaluru, India (12.9716, 77.5946)",
                "total_samples": n_samples,
                "train_samples": len(df_train),
                "val_samples": len(df_val),
                "test_samples": len(df_test),
                "features_count": len(FEATURE_COLUMNS)
            },
            "feature_columns": FEATURE_COLUMNS,
            "horizons": all_metrics
        }, f, indent=2)

    fi_path = os.path.join(artifacts_dir, "feature_importance.json")
    with open(fi_path, "w") as f:
        json.dump(feature_importance_all, f, indent=2)

    print(f"\nAll artifacts successfully saved to {artifacts_dir}")
    return all_metrics

if __name__ == "__main__":
    train_models()
