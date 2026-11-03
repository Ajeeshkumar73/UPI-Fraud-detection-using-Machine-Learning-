import random
import string
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from django.db.models import Q

from transactions.models import Transaction
from transactions.serializers import TransactionSerializer
from fraud_detection.models import FraudDetection, RiskAnalysis, OTPVerification
from alerts.models import FraudAlert
from users.models import User, AuditLog
from ml.predict import FraudPredictionService

def generate_txn_id():
    digits = ''.join(random.choices(string.digits, k=6))
    return f"TXN_{digits}"

class TransactionListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = TransactionSerializer

    def get_queryset(self):
        queryset = Transaction.objects.all().order_by('-timestamp')
        
        # Filter by user if not admin
        user = self.request.user
        if user.is_authenticated and getattr(user, 'role', 'USER') != 'ADMIN':
            queryset = queryset.filter(user=user)

        # Filters
        search = self.request.query_params.get('search', None)
        risk_level = self.request.query_params.get('risk_level', None)
        status_param = self.request.query_params.get('status', None)
        fraud = self.request.query_params.get('fraud', None)
        tx_type = self.request.query_params.get('transaction_type', None)

        if search:
            queryset = queryset.filter(
                Q(transaction_id__icontains=search) |
                Q(beneficiary_name__icontains=search) |
                Q(upi_id__icontains=search) |
                Q(location__icontains=search)
            )
        if risk_level:
            queryset = queryset.filter(fraud_detection__risk_level__iexact=risk_level)
        if status_param:
            queryset = queryset.filter(status__iexact=status_param)
        if fraud is not None:
            if fraud.lower() == 'true':
                queryset = queryset.filter(fraud_detection__prediction_result='Fraud')
            elif fraud.lower() == 'false':
                queryset = queryset.filter(fraud_detection__prediction_result='Genuine')
        if tx_type:
            queryset = queryset.filter(transaction_type__iexact=tx_type)

        return queryset

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        
        # User handling
        user = request.user if request.user.is_authenticated else None
        if not user:
            user = User.objects.filter(username='demo_user').first()
            if not user:
                user = User.objects.create_user(username='demo_user', email='demo@upifraud.local', full_name='Demo User')

        txn_id = generate_txn_id()
        
        # Build transaction object instance
        amount = float(data.get('amount', 500.00))
        txn = Transaction.objects.create(
            transaction_id=txn_id,
            user=user,
            beneficiary_name=data.get('beneficiary_name', 'Demo Merchant'),
            upi_id=data.get('upi_id', 'merchant@upi'),
            amount=amount,
            transaction_type=data.get('transaction_type', 'Online'),
            account_balance=float(data.get('account_balance', 50000.00)),
            device_type=data.get('device_type', 'Mobile'),
            location=data.get('location', 'Mumbai'),
            merchant_category=data.get('merchant_category', 'Retail'),
            ip_address_flag=int(data.get('ip_address_flag', 0)),
            previous_fraudulent_activity=int(data.get('previous_fraudulent_activity', 0)),
            daily_transaction_count=int(data.get('daily_transaction_count', 1)),
            avg_transaction_amount_7d=float(data.get('avg_transaction_amount_7d', 500.00)),
            failed_transaction_count_7d=int(data.get('failed_transaction_count_7d', 0)),
            card_type=data.get('card_type', 'Debit'),
            card_age=int(data.get('card_age', 365)),
            transaction_distance=float(data.get('transaction_distance', 5.00)),
            authentication_method=data.get('authentication_method', 'PIN'),
            is_weekend=int(data.get('is_weekend', 0)),
            status='PENDING'
        )

        # Run ML Fraud Inference
        ml_service = FraudPredictionService()
        ml_input = {
            'transaction_amount': amount,
            'transaction_type': txn.transaction_type,
            'account_balance': float(txn.account_balance),
            'device_type': txn.device_type,
            'location': txn.location,
            'merchant_category': txn.merchant_category,
            'ip_address_flag': txn.ip_address_flag,
            'previous_fraudulent_activity': txn.previous_fraudulent_activity,
            'daily_transaction_count': txn.daily_transaction_count,
            'avg_transaction_amount_7d': float(txn.avg_transaction_amount_7d),
            'failed_transaction_count_7d': txn.failed_transaction_count_7d,
            'card_type': txn.card_type,
            'card_age': txn.card_age,
            'transaction_distance': float(txn.transaction_distance),
            'authentication_method': txn.authentication_method,
            'is_weekend': txn.is_weekend
        }
        ml_res = ml_service.predict(ml_input)

        prediction_result = ml_res['prediction']
        fraud_prob = ml_res['fraud_probability']
        risk_score = ml_res['risk_score']
        risk_level = ml_res['risk_level']
        recommended_action = ml_res['recommended_action']
        risk_factors = ml_res['risk_factors']

        # Save Fraud Detection Record
        fd = FraudDetection.objects.create(
            transaction=txn,
            prediction_result=prediction_result,
            fraud_probability=fraud_prob,
            risk_score=risk_score,
            risk_level=risk_level,
            model_name=ml_res['model_name'],
            model_version='1.0.0'
        )

        # Save Risk Analysis Record
        RiskAnalysis.objects.create(
            transaction=txn,
            risk_score=risk_score,
            risk_category=risk_level,
            risk_factors=risk_factors,
            remarks=f"ML decision: {recommended_action}"
        )

        # Decision Engine Logic
        demo_otp = None
        if recommended_action == 'APPROVED':
            txn.status = 'APPROVED'
            txn.save()
        elif recommended_action == 'OTP_REQUIRED':
            txn.status = 'OTP_REQUIRED'
            txn.save()
            demo_otp = "123456"
            OTPVerification.objects.create(
                transaction=txn,
                otp_code=demo_otp,
                verification_status='PENDING'
            )
        elif recommended_action == 'BLOCKED':
            txn.status = 'BLOCKED'
            txn.save()
            # Create Fraud Alert
            FraudAlert.objects.create(
                transaction=txn,
                user=user,
                alert_type='HIGH_RISK_TRANSACTION_BLOCKED',
                alert_message=f"Transaction {txn.transaction_id} of INR {txn.amount} blocked due to High Fraud Risk Score ({risk_score}/100).",
                risk_score=risk_score,
                alert_status='New'
            )

        AuditLog.objects.create(
            user=user,
            action='TRANSACTION_SIMULATED',
            description=f"Transaction {txn.transaction_id} evaluated with risk score {risk_score} ({risk_level}) -> Status: {txn.status}"
        )

        serializer = self.get_serializer(txn)
        resp_data = serializer.data
        if demo_otp:
            resp_data['demo_otp'] = demo_otp

        return Response(resp_data, status=status.HTTP_201_CREATED)

class TransactionDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
