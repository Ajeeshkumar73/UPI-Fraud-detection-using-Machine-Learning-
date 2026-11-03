from django.core.management.base import BaseCommand
from users.models import User
from beneficiaries.models import Beneficiary
from transactions.models import Transaction
from fraud_detection.models import FraudDetection, RiskAnalysis, OTPVerification
from alerts.models import FraudAlert
from ml.predict import FraudPredictionService

class Command(BaseCommand):
    help = 'Seeds initial superuser, test user, beneficiaries, and sample transactions'

    def handle(self, *args, **options):
        self.stdout.write("--> Seeding demo users and transactions...")

        # 1. Admin User
        admin, created = User.objects.get_or_create(username='admin', defaults={
            'email': 'admin@upifraud.local',
            'full_name': 'System Administrator',
            'role': 'ADMIN',
            'is_staff': True,
            'is_superuser': True
        })
        if created:
            admin.set_password('Admin@12345')
            admin.save()
            self.stdout.write(self.style.SUCCESS("Created admin user: admin / Admin@12345"))

        # 2. Demo Normal User
        user, created = User.objects.get_or_create(username='demo_user', defaults={
            'email': 'user@upifraud.local',
            'full_name': 'Ajeesh Kumar',
            'role': 'USER'
        })
        if created:
            user.set_password('User@12345')
            user.save()
            self.stdout.write(self.style.SUCCESS("Created demo user: demo_user / User@12345"))

        # 3. Beneficiaries
        b1, _ = Beneficiary.objects.get_or_create(user=user, upi_id='rahul@okicici', defaults={
            'beneficiary_name': 'Rahul Sharma',
            'bank_name': 'ICICI Bank',
            'account_reference': 'ICIC00010293'
        })
        b2, _ = Beneficiary.objects.get_or_create(user=user, upi_id='amazon@apl', defaults={
            'beneficiary_name': 'Amazon Pay Retail',
            'bank_name': 'HDFC Bank',
            'account_reference': 'HDFC00049281'
        })
        b3, _ = Beneficiary.objects.get_or_create(user=user, upi_id='travel_booking@sbi', defaults={
            'beneficiary_name': 'Global Travel Agency',
            'bank_name': 'State Bank of India',
            'account_reference': 'SBI000928172'
        })

        # 4. Sample Transactions evaluated with ML model
        ml_service = FraudPredictionService()

        sample_cases = [
            {
                'txn_id': 'TXN_109281',
                'beneficiary': b1,
                'amount': 450.00,
                'type': 'P2P',
                'merchant': 'Services',
                'device': 'Mobile',
                'location': 'Mumbai',
                'ip_flag': 0,
                'prev_fraud': 0,
                'daily_cnt': 2,
                'avg_7d': 500.00,
                'failed_7d': 0,
                'distance': 2.5,
                'auth': 'PIN'
            },
            {
                'txn_id': 'TXN_291048',
                'beneficiary': b2,
                'amount': 2499.00,
                'type': 'Online',
                'merchant': 'Electronics',
                'device': 'Mobile',
                'location': 'Mumbai',
                'ip_flag': 0,
                'prev_fraud': 0,
                'daily_cnt': 4,
                'avg_7d': 800.00,
                'failed_7d': 1,
                'distance': 15.0,
                'auth': 'Biometric'
            },
            {
                'txn_id': 'TXN_992014',
                'beneficiary': b3,
                'amount': 85000.00,
                'type': 'Merchant',
                'merchant': 'Travel',
                'device': 'Laptop',
                'location': 'Sydney',
                'ip_flag': 1,
                'prev_fraud': 1,
                'daily_cnt': 18,
                'avg_7d': 450.00,
                'failed_7d': 4,
                'distance': 1200.0,
                'auth': 'Password'
            }
        ]

        for case in sample_cases:
            txn, txn_created = Transaction.objects.get_or_create(transaction_id=case['txn_id'], defaults={
                'user': user,
                'beneficiary': case['beneficiary'],
                'beneficiary_name': case['beneficiary'].beneficiary_name,
                'upi_id': case['beneficiary'].upi_id,
                'amount': case['amount'],
                'transaction_type': case['type'],
                'merchant_category': case['merchant'],
                'device_type': case['device'],
                'location': case['location'],
                'ip_address_flag': case['ip_flag'],
                'previous_fraudulent_activity': case['prev_fraud'],
                'daily_transaction_count': case['daily_cnt'],
                'avg_transaction_amount_7d': case['avg_7d'],
                'failed_transaction_count_7d': case['failed_7d'],
                'transaction_distance': case['distance'],
                'authentication_method': case['auth'],
                'status': 'PENDING'
            })

            if txn_created:
                ml_res = ml_service.predict({
                    'transaction_amount': case['amount'],
                    'transaction_type': case['type'],
                    'account_balance': 50000.00,
                    'device_type': case['device'],
                    'location': case['location'],
                    'merchant_category': case['merchant'],
                    'ip_address_flag': case['ip_flag'],
                    'previous_fraudulent_activity': case['prev_fraud'],
                    'daily_transaction_count': case['daily_cnt'],
                    'avg_transaction_amount_7d': case['avg_7d'],
                    'failed_transaction_count_7d': case['failed_7d'],
                    'card_type': 'Debit',
                    'card_age': 365,
                    'transaction_distance': case['distance'],
                    'authentication_method': case['auth'],
                    'is_weekend': 0
                })

                action = ml_res['recommended_action']
                score = ml_res['risk_score']
                level = ml_res['risk_level']

                FraudDetection.objects.create(
                    transaction=txn,
                    prediction_result=ml_res['prediction'],
                    fraud_probability=ml_res['fraud_probability'],
                    risk_score=score,
                    risk_level=level,
                    model_name=ml_res['model_name']
                )

                RiskAnalysis.objects.create(
                    transaction=txn,
                    risk_score=score,
                    risk_category=level,
                    risk_factors=ml_res['risk_factors']
                )

                if action == 'APPROVED':
                    txn.status = 'APPROVED'
                elif action == 'OTP_REQUIRED':
                    txn.status = 'OTP_REQUIRED'
                    OTPVerification.objects.create(transaction=txn, otp_code='123456', verification_status='PENDING')
                elif action == 'BLOCKED':
                    txn.status = 'BLOCKED'
                    FraudAlert.objects.create(
                        transaction=txn,
                        user=user,
                        alert_type='HIGH_RISK_TRANSACTION_BLOCKED',
                        alert_message=f"Transaction {case['txn_id']} blocked due to high risk score {score}/100.",
                        risk_score=score
                    )
                txn.save()

        self.stdout.write(self.style.SUCCESS("--> Seeding finished successfully."))
