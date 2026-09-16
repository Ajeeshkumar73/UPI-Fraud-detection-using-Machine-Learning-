import os
import json
import joblib
import pandas as pd
import numpy as np

from ml.feature_engineering import extract_features

class FraudPredictionService:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(FraudPredictionService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, models_dir=None):
        if self._initialized:
            return

        if models_dir is None:
            models_dir = os.path.join(os.path.dirname(__file__), 'models')

        self.models_dir = models_dir
        self.model_path = os.path.join(models_dir, 'fraud_model.pkl')
        self.preprocessor_path = os.path.join(models_dir, 'preprocessor.pkl')
        self.metadata_path = os.path.join(models_dir, 'model_metadata.json')

        self.model = None
        self.preprocessor = None
        self.metadata = None

        self.load_artifacts()
        self._initialized = True

    def load_artifacts(self):
        """Loads serialized model, preprocessor, and metadata."""
        if os.path.exists(self.model_path) and os.path.exists(self.preprocessor_path):
            self.model = joblib.load(self.model_path)
            self.preprocessor = joblib.load(self.preprocessor_path)
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, 'r') as f:
                    self.metadata = json.load(f)
            print(f"--> [FraudPredictionService] Loaded model: {self.metadata.get('selected_model', 'Unknown') if self.metadata else 'Loaded'}")
        else:
            print("--> [FraudPredictionService] WARNING: Artifacts not found. Please run train_fraud_model command.")

    def predict(self, transaction_data: dict) -> dict:
        """
        Input dictionary representing a transaction record.
        Returns prediction details including probability, score, risk level, action, and explanation.
        """
        if self.model is None or self.preprocessor is None:
            self.load_artifacts()
            if self.model is None or self.preprocessor is None:
                raise RuntimeError("ML Model not trained or missing model artifacts. Run python manage.py train_fraud_model first.")

        df_input = pd.DataFrame([transaction_data])
        df_engineered = extract_features(df_input)

        feature_cols = self.metadata.get('feature_names', None) if self.metadata else None
        if feature_cols:
            for col in feature_cols:
                if col not in df_engineered.columns:
                    df_engineered[col] = 0
            df_features = df_engineered[feature_cols]
        else:
            drop_cols = ['Fraud_Label', 'Transaction_ID', 'User_ID', 'Timestamp']
            feature_cols = [c for c in df_engineered.columns if c not in drop_cols]
            df_features = df_engineered[feature_cols]

        X_trans = self.preprocessor.transform(df_features)

        prob_array = self.model.predict_proba(X_trans)
        fraud_probability = float(prob_array[0][1])
        prediction_label = "Fraud" if fraud_probability >= 0.50 else "Genuine"

        risk_score = round(fraud_probability * 100, 2)

        if risk_score < 30.0:
            risk_level = "Low"
            recommended_action = "APPROVED"
        elif risk_score < 65.0:
            risk_level = "Medium"
            recommended_action = "OTP_REQUIRED"
        else:
            risk_level = "High"
            recommended_action = "BLOCKED"

        risk_factors = []
        amount = float(transaction_data.get('transaction_amount', transaction_data.get('Transaction_Amount', 0)))
        avg_7d = float(transaction_data.get('avg_transaction_amount_7d', transaction_data.get('Avg_Transaction_Amount_7d', 1)))
        prev_fraud = int(transaction_data.get('previous_fraudulent_activity', transaction_data.get('Previous_Fraudulent_Activity', 0)))
        failed_7d = int(transaction_data.get('failed_transaction_count_7d', transaction_data.get('Failed_Transaction_Count_7d', 0)))
        ip_flag = int(transaction_data.get('ip_address_flag', transaction_data.get('IP_Address_Flag', 0)))
        distance = float(transaction_data.get('transaction_distance', transaction_data.get('Transaction_Distance', 0)))
        daily_cnt = int(transaction_data.get('daily_transaction_count', transaction_data.get('Daily_Transaction_Count', 0)))
        is_night = int(df_engineered['is_night_transaction'].iloc[0]) if 'is_night_transaction' in df_engineered else 0

        if prev_fraud == 1:
            risk_factors.append("Previous Fraudulent Activity Detected on Account")
        if ip_flag == 1:
            risk_factors.append("Suspicious / Anomaly IP Address Flagged")
        if avg_7d > 0 and (amount / avg_7d) > 2.5:
            risk_factors.append(f"Unusual Transaction Amount (INR {amount:,.2f} is >2.5x of 7-day average INR {avg_7d:,.2f})")
        if failed_7d >= 2:
            risk_factors.append(f"Multiple Failed Transactions ({failed_7d} failed in last 7 days)")
        if distance > 300:
            risk_factors.append(f"Unusually High Transaction Distance ({distance:.1f} km)")
        if daily_cnt > 15:
            risk_factors.append(f"Elevated Daily Transaction Frequency ({daily_cnt} transactions today)")
        if is_night == 1:
            risk_factors.append("Off-Hours / Late Night Transaction Activity")

        if not risk_factors:
            if risk_level == "Low":
                risk_factors.append("Normal Transaction Behavioral Profile")
            else:
                risk_factors.append("Elevated Statistical Anomaly Score Detected by Machine Learning Model")

        return {
            "prediction": prediction_label,
            "fraud_probability": round(fraud_probability, 4),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "recommended_action": recommended_action,
            "risk_factors": risk_factors,
            "model_name": self.metadata.get('selected_model', 'XGBoost') if self.metadata else 'Trained Model'
        }
