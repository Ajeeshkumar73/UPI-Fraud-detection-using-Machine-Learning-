import os
import json
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

from ml.feature_engineering import extract_features
from ml.evaluate import evaluate_model_performance

def train_and_evaluate_models(dataset_path=None, output_dir=None):
    if dataset_path is None:
        dataset_path = os.path.join(os.path.dirname(__file__), 'dataset', 'synthetic_fraud_dataset.csv')
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), 'models')

    os.makedirs(output_dir, exist_ok=True)

    print(f"--> Loading dataset from: {dataset_path}")
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset file not found at {dataset_path}")

    raw_df = pd.read_csv(dataset_path)
    print(f"--> Raw Dataset Shape: {raw_df.shape}")

    # Clean & Extract Features
    df = extract_features(raw_df)

    if 'Fraud_Label' not in df.columns:
        raise ValueError("Target column 'Fraud_Label' missing from dataset.")

    y = df['Fraud_Label'].astype(int)
    
    # Feature columns exclusion (ID, target, timestamp)
    drop_cols = ['Fraud_Label', 'Transaction_ID', 'User_ID', 'Timestamp']
    feature_cols = [c for c in df.columns if c not in drop_cols]
    
    X = df[feature_cols]

    # Identify categorical & numeric columns
    cat_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()
    num_cols = X.select_dtypes(include=['int64', 'float64', 'int32', 'float32']).columns.tolist()

    print(f"--> Total Features: {len(feature_cols)} (Categorical: {len(cat_cols)}, Numeric: {len(num_cols)})")

    # Data Leakage Prevention: Split BEFORE fitting scalers/encoders
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    print(f"--> Train set size: {len(X_train)}, Test set size: {len(X_test)}")
    fraud_count = int(y.sum())
    genuine_count = int(len(y) - fraud_count)
    fraud_pct = round((fraud_count / len(y)) * 100, 2)

    # Preprocessing Pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), num_cols),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_cols)
        ]
    )

    print("--> Fitting preprocessor on X_train...")
    X_train_trans = preprocessor.fit_transform(X_train)
    X_test_trans = preprocessor.transform(X_test)

    # Extract transformed feature names
    cat_encoder = preprocessor.named_transformers_['cat']
    encoded_cat_names = cat_encoder.get_feature_names_out(cat_cols).tolist() if cat_cols else []
    all_feature_names = num_cols + encoded_cat_names

    # Define candidate models
    pos_weight = (len(y_train) - sum(y_train)) / max(1, sum(y_train))

    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000, class_weight='balanced', random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=12, class_weight='balanced', random_state=42),
        "XGBoost": XGBClassifier(n_estimators=100, max_depth=6, learning_rate=0.1, scale_pos_weight=pos_weight, random_state=42, eval_metric='logloss')
    }

    results = {}
    trained_model_objects = {}

    print("--> Training & Evaluating Models...")
    for model_name, model_obj in models.items():
        print(f"    - Training {model_name}...")
        model_obj.fit(X_train_trans, y_train)
        y_pred = model_obj.predict(X_test_trans)
        y_prob = model_obj.predict_proba(X_test_trans)[:, 1]

        eval_res = evaluate_model_performance(y_test, y_pred, y_prob)
        results[model_name] = eval_res
        trained_model_objects[model_name] = model_obj
        print(f"      [{model_name}] F1: {eval_res['f1']} | Recall: {eval_res['recall']} | ROC-AUC: {eval_res['roc_auc']} | PR-AUC: {eval_res['pr_auc']}")

    # Model Selection: Best based on F1 score primary, PR-AUC secondary
    best_model_name = max(results.keys(), key=lambda k: (results[k]['f1'], results[k]['pr_auc'], results[k]['recall']))
    best_model_obj = trained_model_objects[best_model_name]
    best_metrics = results[best_model_name]

    print(f"\n==========================================")
    print(f" SELECTED PRODUCTION MODEL: {best_model_name}")
    print(f" Precision : {best_metrics['precision']}")
    print(f" Recall    : {best_metrics['recall']}")
    print(f" F1-Score  : {best_metrics['f1']}")
    print(f" ROC-AUC   : {best_metrics['roc_auc']}")
    print(f" PR-AUC    : {best_metrics['pr_auc']}")
    print(f"==========================================\n")

    # Feature Importance computation for best model
    feature_importances = []
    if hasattr(best_model_obj, 'feature_importances_'):
        importances = best_model_obj.feature_importances_
    elif hasattr(best_model_obj, 'coef_'):
        importances = np.abs(best_model_obj.coef_[0])
    else:
        importances = np.ones(len(all_feature_names))

    # Sort feature importances
    sorted_idx = np.argsort(importances)[::-1]
    top_n = min(20, len(all_feature_names))
    for i in range(top_n):
        idx = sorted_idx[i]
        feature_importances.append({
            "feature": all_feature_names[idx],
            "importance": round(float(importances[idx]), 4)
        })

    # Save artifacts
    model_path = os.path.join(output_dir, 'fraud_model.pkl')
    preprocessor_path = os.path.join(output_dir, 'preprocessor.pkl')
    metadata_path = os.path.join(output_dir, 'model_metadata.json')

    joblib.dump(best_model_obj, model_path)
    joblib.dump(preprocessor, preprocessor_path)

    metadata = {
        "dataset_name": "synthetic_fraud_dataset.csv",
        "total_records": len(df),
        "fraud_count": fraud_count,
        "genuine_count": genuine_count,
        "fraud_percentage": fraud_pct,
        "total_features": len(feature_cols),
        "selected_model": best_model_name,
        "feature_names": feature_cols,
        "all_transformed_feature_names": all_feature_names,
        "categorical_columns": cat_cols,
        "numeric_columns": num_cols,
        "model_comparison": results,
        "feature_importance": feature_importances
    }

    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"--> Artifacts saved successfully to {output_dir}")
    return metadata

if __name__ == '__main__':
    train_and_evaluate_models()
