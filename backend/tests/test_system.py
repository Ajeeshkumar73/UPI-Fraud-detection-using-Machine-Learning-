import os
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.conf import settings

from ml.feature_engineering import extract_features
from ml.predict import FraudPredictionService
from beneficiaries.models import Beneficiary
from transactions.models import Transaction
from fraud_detection.models import FraudDetection, OTPVerification
from alerts.models import FraudAlert
from investigations.models import FraudInvestigation

User = get_user_model()

class SystemIntegrationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='TestPassword123!',
            email='test@upifraud.local',
            full_name='Test User'
        )
        self.admin = User.objects.create_user(
            username='testadmin',
            password='AdminPassword123!',
            email='admin@upifraud.local',
            role='ADMIN'
        )
        self.beneficiary = Beneficiary.objects.create(
            user=self.user,
            beneficiary_name='Test Merchant',
            upi_id='merchant@okicici',
            bank_name='HDFC Bank'
        )

    def test_01_dataset_exists(self):
        csv_path = os.path.join(settings.BASE_DIR, 'ml', 'dataset', 'synthetic_fraud_dataset.csv')
        self.assertTrue(os.path.exists(csv_path), "Kaggle synthetic fraud dataset CSV file should exist.")

    def test_02_feature_engineering(self):
        import pandas as pd
        sample_df = pd.DataFrame([{
            'Transaction_Amount': 15000,
            'Transaction_Type': 'Online',
            'Account_Balance': 50000,
            'Device_Type': 'Mobile',
            'Location': 'Mumbai',
            'Merchant_Category': 'Retail',
            'IP_Address_Flag': 0,
            'Previous_Fraudulent_Activity': 0,
            'Daily_Transaction_Count': 5,
            'Avg_Transaction_Amount_7d': 750,
            'Failed_Transaction_Count_7d': 0,
            'Card_Type': 'Debit',
            'Card_Age': 24,
            'Transaction_Distance': 5,
            'Authentication_Method': 'PIN',
            'Is_Weekend': 0
        }])
        df_feats = extract_features(sample_df)
        self.assertIn('amount_vs_7d_average', df_feats.columns)
        self.assertIn('is_night_transaction', df_feats.columns)
        self.assertNotIn('Fraud_Label', df_feats.columns)

    def test_03_ml_prediction_service(self):
        service = FraudPredictionService()
        sample_input = {
            'transaction_amount': 2500,
            'transaction_type': 'Online',
            'account_balance': 15000,
            'device_type': 'Mobile',
            'location': 'Kerala',
            'merchant_category': 'Retail',
            'ip_address_flag': 0,
            'previous_fraudulent_activity': 0,
            'daily_transaction_count': 5,
            'avg_transaction_amount_7d': 750,
            'failed_transaction_count_7d': 0,
            'card_type': 'Debit',
            'card_age': 24,
            'transaction_distance': 5,
            'authentication_method': 'PIN',
            'is_weekend': 0
        }
        res = service.predict(sample_input)
        self.assertIn('prediction', res)
        self.assertIn('fraud_probability', res)
        self.assertIn('risk_score', res)
        self.assertIn('risk_level', res)
        self.assertIn('recommended_action', res)
        self.assertIn('risk_factors', res)
        self.assertGreaterEqual(res['risk_score'], 0.0)
        self.assertLessEqual(res['risk_score'], 100.0)

    def test_04_user_authentication_api(self):
        # Test Login
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'TestPassword123!'
        }, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['username'], 'testuser')

    def test_05_transaction_creation_and_decision_engine(self):
        self.client.force_login(self.user)
        # Create a low-risk transaction
        payload = {
            'beneficiary_name': 'Test Merchant',
            'upi_id': 'merchant@okicici',
            'amount': 250.00,
            'transaction_type': 'P2P',
            'merchant_category': 'Services',
            'device_type': 'Mobile',
            'location': 'Mumbai',
            'avg_transaction_amount_7d': 500.00,
            'failed_transaction_count_7d': 0,
            'transaction_distance': 2.0,
            'ip_address_flag': 0,
            'previous_fraudulent_activity': 0
        }
        res = self.client.post('/api/transactions/', payload, content_type='application/json')
        self.assertEqual(res.status_code, 201)
        txn_data = res.data
        self.assertIn('transaction_id', txn_data)
        self.assertIn('status', txn_data)
        self.assertIn('fraud_detection', txn_data)

    def test_06_otp_verification_flow(self):
        txn = Transaction.objects.create(
            transaction_id='TXN_OTP_TEST',
            user=self.user,
            beneficiary_name='OTP Test Merchant',
            upi_id='test@otp',
            amount=5000.00,
            status='OTP_REQUIRED'
        )
        OTPVerification.objects.create(
            transaction=txn,
            otp_code='123456',
            verification_status='PENDING'
        )

        res = self.client.post('/api/otp/verify/', {
            'transaction_id': 'TXN_OTP_TEST',
            'otp_code': '123456'
        }, content_type='application/json')

        self.assertEqual(res.status_code, 200)
        txn.refresh_from_db()
        self.assertEqual(txn.status, 'APPROVED_AFTER_OTP')

    def test_07_admin_investigation_api(self):
        txn = Transaction.objects.create(
            transaction_id='TXN_HIGH_RISK_TEST',
            user=self.user,
            beneficiary_name='Suspicious Merchant',
            upi_id='suspicious@upi',
            amount=99000.00,
            status='BLOCKED'
        )
        self.client.force_login(self.admin)
        res = self.client.post('/api/admin/investigations/', {
            'transaction_id': 'TXN_HIGH_RISK_TEST',
            'investigation_status': 'Confirmed Fraud',
            'remarks': 'Audited by security team'
        }, content_type='application/json')

        self.assertEqual(res.status_code, 200)
        inv = FraudInvestigation.objects.get(transaction=txn)
        self.assertEqual(inv.investigation_status, 'Confirmed Fraud')
