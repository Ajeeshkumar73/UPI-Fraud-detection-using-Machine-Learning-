import os
import json
from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.db.models import Count, Sum, Q

from users.models import User
from transactions.models import Transaction
from fraud_detection.models import FraudDetection
from alerts.models import FraudAlert

class AdminDashboardStatsView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        total_users = User.objects.count()
        total_txns = Transaction.objects.count()
        
        fraud_txns = FraudDetection.objects.filter(prediction_result='Fraud').count()
        genuine_txns = FraudDetection.objects.filter(prediction_result='Genuine').count()
        
        blocked_txns = Transaction.objects.filter(status='BLOCKED').count()
        otp_txns = Transaction.objects.filter(status__in=['OTP_REQUIRED', 'APPROVED_AFTER_OTP']).count()
        high_risk_txns = FraudDetection.objects.filter(risk_level='High').count()
        medium_risk_txns = FraudDetection.objects.filter(risk_level='Medium').count()
        low_risk_txns = FraudDetection.objects.filter(risk_level='Low').count()

        total_value_agg = Transaction.objects.aggregate(total=Sum('amount'))['total'] or 0.0
        avg_amount = (total_value_agg / total_txns) if total_txns > 0 else 0.0

        fraud_rate = round((fraud_txns / total_txns * 100), 2) if total_txns > 0 else 0.0

        return Response({
            'total_users': total_users,
            'total_transactions': total_txns,
            'fraudulent_transactions': fraud_txns,
            'genuine_transactions': genuine_txns,
            'blocked_transactions': blocked_txns,
            'otp_transactions': otp_txns,
            'high_risk_transactions': high_risk_txns,
            'medium_risk_transactions': medium_risk_txns,
            'low_risk_transactions': low_risk_txns,
            'fraud_rate': fraud_rate,
            'total_transaction_value': round(float(total_value_agg), 2),
            'average_transaction_amount': round(float(avg_amount), 2)
        })

class AdminAnalyticsView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Fraud by Device Type
        by_device = Transaction.objects.values('device_type').annotate(
            total=Count('id'),
            fraud_count=Count('id', filter=Q(fraud_detection__prediction_result='Fraud'))
        )
        
        # Fraud by Location
        by_location = Transaction.objects.values('location').annotate(
            total=Count('id'),
            fraud_count=Count('id', filter=Q(fraud_detection__prediction_result='Fraud'))
        )[:10]

        # Fraud by Merchant Category
        by_merchant = Transaction.objects.values('merchant_category').annotate(
            total=Count('id'),
            fraud_count=Count('id', filter=Q(fraud_detection__prediction_result='Fraud'))
        )

        # Fraud by Authentication Method
        by_auth = Transaction.objects.values('authentication_method').annotate(
            total=Count('id'),
            fraud_count=Count('id', filter=Q(fraud_detection__prediction_result='Fraud'))
        )

        # Risk level distribution
        risk_dist = [
            {'level': 'Low Risk', 'count': FraudDetection.objects.filter(risk_level='Low').count()},
            {'level': 'Medium Risk', 'count': FraudDetection.objects.filter(risk_level='Medium').count()},
            {'level': 'High Risk', 'count': FraudDetection.objects.filter(risk_level='High').count()},
        ]

        return Response({
            'by_device': list(by_device),
            'by_location': list(by_location),
            'by_merchant': list(by_merchant),
            'by_auth': list(by_auth),
            'risk_distribution': risk_dist
        })

class MLModelPerformanceView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        metadata_path = os.path.join(os.path.dirname(__file__), '..', 'ml', 'models', 'model_metadata.json')
        if not os.path.exists(metadata_path):
            return Response({'error': 'ML Metadata not found. Run python manage.py train_fraud_model first.'}, status=status.HTTP_404_NOT_FOUND)

        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        return Response(metadata)
