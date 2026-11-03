# AI-Powered UPI Fraud Detection System

Production-grade **AI-Powered UPI Fraud Detection System** prototype as a full-stack web application. The platform uses machine learning (XGBoost, Random Forest, Logistic Regression) trained on the Kaggle **Fraud Detection Transactions Dataset** (50,000 records, 21 features) to evaluate real-time transaction risk, auto-classify risk levels (Low, Medium, High), trigger OTP verification or transaction blocking, generate fraud alerts, and provide administrative fraud investigation and model monitoring tools.

> **Important Notice**: The Kaggle dataset used in this project is synthetic and is used for academic/prototype fraud detection. The system simulates UPI payment workflows for academic and prototyping purposes without connecting to real banking networks or payment gateways.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Key Features](#key-features)
3. [System Architecture](#system-architecture)
4. [Technology Stack](#technology-stack)
5. [Dataset Information & Source](#dataset-information--source)
6. [Machine Learning Workflow](#machine-learning-workflow)
7. [Database Design](#database-design)
8. [API Endpoints](#api-endpoints)
9. [Installation & Setup](#installation--setup)
10. [Dataset Placement](#dataset-placement)
11. [Model Training Command](#model-training-command)
12. [Running the Application](#running-the-application)
13. [Automated Testing](#automated-testing)
14. [Limitations](#limitations)
15. [Future Enhancements](#future-enhancements)

---

## Project Overview
Digital payments via UPI (Unified Payments Interface) require instant fraud protection. This platform evaluates every simulated UPI transaction request using trained machine learning models, generating a dynamic Risk Score (0 to 100) and classifying it into three risk levels:
- **Low Risk (0–29)**: Transaction is automatically `APPROVED`.
- **Medium Risk (30–64)**: Transaction requires `OTP_REQUIRED` (simulated 6-digit OTP verification).
- **High Risk (65–100)**: Transaction is automatically `BLOCKED` and triggers an urgent Fraud Alert.

---

## Key Features

### User Features
- **User Authentication**: Secure registration and login with role-based access.
- **Beneficiary Management**: CRUD operations for adding trusted UPI beneficiaries with auto-fill during transactions.
- **UPI Transaction Simulation**: Send money interface with real-time pre-analysis ("Analyze Transaction" button).
- **OTP Verification Simulation**: Interactive modal for Medium risk transactions (Displays demo OTP `123456`).
- **Fraud Alerts**: Notifications for high risk blocked transactions.
- **Transaction History & Details**: Deep inspection page featuring behavioral metrics and explainable risk factors.

### Administrator Features
- **Executive Admin Dashboard**: Real-time stats on total users, transactions, fraud rate %, and volume.
- **User Management**: Search and toggle user account activation status.
- **Transaction Monitoring**: Filter transactions by risk level, decision status, and location.
- **Fraud Investigation Workbench**: Audit flagged transactions and record auditor verdicts ("Confirmed Fraud", "Mark Genuine", "Under Investigation").
- **ML Model Performance Dashboard**: Displays dataset stats, 3-model comparison metrics (Logistic Regression, Random Forest, XGBoost), feature importances, ROC curves, and confusion matrix.
- **Security Audit Logs**: Track user logins, transaction evaluations, and system actions.

---

## System Architecture

```text
HTML5 / CSS3 / JavaScript (Tailwind CSS)
                 │
                 │ REST API (JSON)
                 ▼
     Django REST Framework (DRF)
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
  SQLite     Django ORM   ML Service (FraudPredictionService)
Database       Models         │
                              ├── Preprocessor Pipeline (OneHotEncoder + StandardScaler)
                              └── Trained Classifiers (Random Forest / XGBoost / Logistic Regression)
```

---

## Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+ Modules), Tailwind CSS, Chart.js, Lucide Icons.
- **Backend**: Python 3.13, Django 5.x, Django REST Framework, SQLite Database, CORS Headers.
- **Machine Learning**: Scikit-Learn, XGBoost, Pandas, NumPy, Joblib, Matplotlib.

---

## Dataset Information & Source

- **Dataset Name**: Fraud Detection Transactions Dataset
- **Kaggle URL**: [https://www.kaggle.com/datasets/samayashar/fraud-detection-transactions-dataset](https://www.kaggle.com/datasets/samayashar/fraud-detection-transactions-dataset)
- **Dataset Specs**: 50,000 transaction records, 21 features.
- **Target Column**: `Fraud_Label` (`0` = Not Fraud, `1` = Fraud)
- **Features**: `Transaction_ID`, `User_ID`, `Transaction_Amount`, `Transaction_Type`, `Timestamp`, `Account_Balance`, `Device_Type`, `Location`, `Merchant_Category`, `IP_Address_Flag`, `Previous_Fraudulent_Activity`, `Daily_Transaction_Count`, `Avg_Transaction_Amount_7d`, `Failed_Transaction_Count_7d`, `Card_Type`, `Card_Age`, `Transaction_Distance`, `Authentication_Method`, `Risk_Score`, `Is_Weekend`, `Fraud_Label`.

---

## Machine Learning Workflow

1. **Preprocessing**: Parse timestamps into temporal features (`transaction_hour`, `is_night_transaction`). Encode categorical features (`Transaction_Type`, `Device_Type`, `Location`, `Merchant_Category`, `Card_Type`, `Authentication_Method`) with `OneHotEncoder(handle_unknown='ignore')`. Scale numeric features with `StandardScaler`.
2. **Data Leakage Prevention**: Split dataset 80/20 into train/test sets using stratification BEFORE fitting transformers.
3. **Model Training & Comparison**:
   - Model 1: Logistic Regression (`class_weight='balanced'`)
   - Model 2: Random Forest Classifier (`n_estimators=100`, `class_weight='balanced'`)
   - Model 3: XGBoost Classifier (`scale_pos_weight` tuned)
4. **Model Selection**: Select best performing model based primary on F1-score, Recall, and PR-AUC.
5. **Artifact Output**: Save `fraud_model.pkl`, `preprocessor.pkl`, and `model_metadata.json`.

---

## Database Design

- `User`: Custom Django user model (`role`: USER / ADMIN).
- `Beneficiary`: Beneficiary name, UPI ID, Bank name, account reference.
- `Transaction`: Full transaction record with amounts, location, device, and status (`APPROVED`, `APPROVED_AFTER_OTP`, `OTP_REQUIRED`, `BLOCKED`).
- `FraudDetection`: OneToOne relation storing ML prediction label, probability, risk score, and risk level.
- `RiskAnalysis`: OneToOne relation storing explainable risk factors.
- `OTPVerification`: OTP code, status, and verification timestamp.
- `FraudAlert`: High risk alert messages.
- `FraudInvestigation`: Admin investigation status ("Confirmed Fraud", "Mark Genuine").
- `AuditLog`: Security action logging.

---

## API Endpoints

### Authentication
- `POST /api/auth/register/` - Register new user account
- `POST /api/auth/login/` - User/Admin authentication
- `POST /api/auth/logout/` - Session logout
- `GET /api/auth/profile/` - Retrieve authenticated user profile

### Beneficiaries & Transactions
- `GET /api/beneficiaries/` - List user beneficiaries
- `POST /api/beneficiaries/` - Create beneficiary
- `GET /api/transactions/` - List transactions (filters: `search`, `risk_level`, `status`)
- `POST /api/transactions/` - Create transaction & evaluate ML prediction
- `GET /api/transactions/{id}/` - Transaction deep detail view

### Fraud & OTP
- `POST /api/fraud/predict/` - Standalone ML pre-analysis
- `POST /api/otp/verify/` - Verify 6-digit OTP

### Admin APIs
- `GET /api/admin/dashboard/` - High-level system statistics
- `GET /api/admin/users/` - User list & management
- `POST /api/admin/users/{id}/toggle-active/` - Activate/deactivate user
- `GET /api/admin/analytics/` - Chart analytics data
- `GET /api/admin/model-performance/` - Dataset stats, model metrics, ROC/PR points
- `POST /api/admin/investigations/` - Update fraud investigation verdict

---

## Installation & Setup

### Prerequisites
- Python 3.10+
- Pip package manager

### 1. Clone Project & Set Up Environment
```bash
cd upi-fraud-detection/backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## Dataset Placement
Ensure `synthetic_fraud_dataset.csv` is located at:
`upi-fraud-detection/dataset/synthetic_fraud_dataset.csv`
and
`upi-fraud-detection/backend/ml/dataset/synthetic_fraud_dataset.csv`

Validate dataset using management command:
```bash
python manage.py import_fraud_dataset
```

---

## Model Training Command
Train and compare Logistic Regression, Random Forest, and XGBoost:
```bash
python manage.py train_fraud_model
```
This generates saved model artifacts in `backend/ml/models/`.

---

## Running the Application

### 1. Run Migrations & Seed Demo Data
```bash
python manage.py migrate
python manage.py seed_demo_data
```

### 2. Start Django Backend Server
```bash
python manage.py runserver
```
Backend runs at `http://127.0.0.1:8000/`.

### 3. Open Frontend Interface
Open `http://127.0.0.1:8000/` in your browser. The Django backend serves the full-stack HTML frontend templates directly.

### Demo Login Credentials
- **Admin Account**: `admin` / `Admin@12345`
- **Demo User Account**: `demo_user` / `User@12345`

---

## Automated Testing
Run Django unit and integration test suite:
```bash
python manage.py test tests
```

---

## Limitations
- **Synthetic Data**: Dataset values are synthetically generated and do not represent actual commercial bank transactions.
- **Simulated OTP**: OTP codes are generated in-memory (`123456`) for demonstration and do not send real SMS messages via telecom APIs.
- **Non-Financial Sandbox**: Money transfers are simulated numbers stored in SQLite.

---

## Future Enhancements
- Integration of real SMS gateway APIs (Twilio / Fast2SMS).
- Biometric WebAuthn authentication support.
- SHAP / LIME graph visualization in admin model dashboard.
