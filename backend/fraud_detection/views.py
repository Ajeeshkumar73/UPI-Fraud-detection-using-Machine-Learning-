from rest_framework import views, permissions, status, generics
from rest_framework.response import Response
from django.utils import timezone

from ml.predict import FraudPredictionService
from fraud_detection.models import FraudDetection, OTPVerification
from transactions.models import Transaction
from users.models import AuditLog

class FraudPredictAPIView(views.APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        """
        Standalone prediction API endpoint POST /api/fraud/predict/
        """
        data = request.data
        ml_service = FraudPredictionService()

        try:
            prediction_res = ml_service.predict(data)
            return Response(prediction_res, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class FraudHistoryListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        detections = FraudDetection.objects.select_related('transaction').order_by('-detection_time')[:100]
        data = []
        for d in detections:
            data.append({
                'id': d.id,
                'transaction_id': d.transaction.transaction_id,
                'amount': d.transaction.amount,
                'user': d.transaction.user.username if d.transaction.user else 'Unknown',
                'prediction_result': d.prediction_result,
                'fraud_probability': d.fraud_probability,
                'risk_score': d.risk_score,
                'risk_level': d.risk_level,
                'model_name': d.model_name,
                'detection_time': d.detection_time
            })
        return Response(data)

class OTPGenerateView(views.APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        transaction_id = request.data.get('transaction_id')
        try:
            txn = Transaction.objects.get(transaction_id=transaction_id)
            otp, _ = OTPVerification.objects.get_or_create(transaction=txn)
            otp.otp_code = "123456"
            otp.verification_status = 'PENDING'
            otp.save()
            return Response({
                'message': 'OTP generated successfully',
                'transaction_id': transaction_id,
                'demo_otp': '123456'
            })
        except Transaction.DoesNotExist:
            return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

class OTPVerifyView(views.APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        transaction_id = request.data.get('transaction_id')
        otp_input = request.data.get('otp_code')

        try:
            txn = Transaction.objects.get(transaction_id=transaction_id)
            otp_obj = getattr(txn, 'otp_verification', None)
            
            if not otp_obj:
                return Response({'error': 'No OTP record found for transaction'}, status=status.HTTP_400_BAD_REQUEST)

            if otp_input == otp_obj.otp_code or otp_input == '123456':
                otp_obj.verification_status = 'VERIFIED'
                otp_obj.verified_at = timezone.now()
                otp_obj.save()

                txn.status = 'APPROVED_AFTER_OTP'
                txn.save()

                AuditLog.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='OTP_VERIFIED',
                    description=f'OTP verified successfully for {transaction_id}'
                )
                return Response({'message': 'OTP Verified successfully', 'status': 'APPROVED_AFTER_OTP'})
            else:
                return Response({'error': 'Invalid OTP code'}, status=status.HTTP_400_BAD_REQUEST)
        except Transaction.DoesNotExist:
            return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)
