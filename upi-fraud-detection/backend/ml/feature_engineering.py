import pandas as pd
import numpy as np

KEY_MAPPING = {
    'transaction_amount': 'Transaction_Amount',
    'transaction_type': 'Transaction_Type',
    'account_balance': 'Account_Balance',
    'device_type': 'Device_Type',
    'location': 'Location',
    'merchant_category': 'Merchant_Category',
    'ip_address_flag': 'IP_Address_Flag',
    'previous_fraudulent_activity': 'Previous_Fraudulent_Activity',
    'daily_transaction_count': 'Daily_Transaction_Count',
    'avg_transaction_amount_7d': 'Avg_Transaction_Amount_7d',
    'failed_transaction_count_7d': 'Failed_Transaction_Count_7d',
    'card_type': 'Card_Type',
    'card_age': 'Card_Age',
    'transaction_distance': 'Transaction_Distance',
    'authentication_method': 'Authentication_Method',
    'is_weekend': 'Is_Weekend',
    'risk_score': 'Risk_Score',
    'timestamp': 'Timestamp'
}

def extract_features(df_input: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms raw input DataFrame into engineered features for model training and prediction.
    Does NOT use Fraud_Label or target variable.
    """
    df = df_input.copy()

    # Normalize column names if lowercase API keys were supplied
    new_cols = {}
    for col in df.columns:
        col_lower = col.lower()
        if col_lower in KEY_MAPPING:
            new_cols[col] = KEY_MAPPING[col_lower]
    if new_cols:
        df.rename(columns=new_cols, inplace=True)
    
    # 1. Parse Timestamp to datetime
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
        df['transaction_hour'] = df['Timestamp'].dt.hour.fillna(12).astype(int)
        df['transaction_day'] = df['Timestamp'].dt.day.fillna(15).astype(int)
        df['transaction_month'] = df['Timestamp'].dt.month.fillna(6).astype(int)
        df['transaction_day_of_week'] = df['Timestamp'].dt.dayofweek.fillna(0).astype(int)
        df['is_night_transaction'] = df['transaction_hour'].apply(lambda h: 1 if (h >= 23 or h <= 5) else 0)
    else:
        df['transaction_hour'] = 12
        df['transaction_day'] = 15
        df['transaction_month'] = 6
        df['transaction_day_of_week'] = 0
        df['is_night_transaction'] = 0

    # Ensure numeric columns are floats/ints
    num_cols = [
        'Transaction_Amount', 'Account_Balance', 'Daily_Transaction_Count',
        'Avg_Transaction_Amount_7d', 'Failed_Transaction_Count_7d', 'Card_Age',
        'Transaction_Distance', 'IP_Address_Flag', 'Previous_Fraudulent_Activity',
        'Is_Weekend', 'Risk_Score'
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        else:
            df[col] = 0.0

    # Ensure categorical columns exist and are string type
    cat_cols = ['Transaction_Type', 'Device_Type', 'Location', 'Merchant_Category', 'Card_Type', 'Authentication_Method']
    defaults = {
        'Transaction_Type': 'Online',
        'Device_Type': 'Mobile',
        'Location': 'Mumbai',
        'Merchant_Category': 'Retail',
        'Card_Type': 'Debit',
        'Authentication_Method': 'PIN'
    }
    for col in cat_cols:
        if col not in df.columns or df[col].isnull().all():
            df[col] = defaults.get(col, 'Unknown')
        df[col] = df[col].astype(str)

    # 2. Behavioral Features
    amount = df['Transaction_Amount']
    avg_7d = df['Avg_Transaction_Amount_7d']
    daily_cnt = df['Daily_Transaction_Count']
    failed_7d = df['Failed_Transaction_Count_7d']
    acc_bal = df['Account_Balance']
    distance = df['Transaction_Distance']
    
    df['amount_vs_7d_average'] = amount / (avg_7d + 1.0)
    df['transaction_frequency_score'] = daily_cnt / 24.0
    df['failed_transaction_ratio'] = failed_7d / (daily_cnt + 1.0)
    df['balance_after_transaction'] = acc_bal - amount
    df['unusual_amount_flag'] = (df['amount_vs_7d_average'] > 2.5).astype(int)
    df['unusual_distance_flag'] = (distance > 300.0).astype(int)
    df['suspicious_ip_flag'] = (df['IP_Address_Flag'] == 1).astype(int)
    df['previous_fraud_flag'] = (df['Previous_Fraudulent_Activity'] == 1).astype(int)
    
    return df
