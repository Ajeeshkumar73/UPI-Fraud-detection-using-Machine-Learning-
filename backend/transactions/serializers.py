from rest_framework import serializers
from transactions.models import Transaction
from fraud_detection.models import FraudDetection, RiskAnalysis, OTPVerification

class FraudDetectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FraudDetection
        fields = ['prediction_result', 'fraud_probability', 'risk_score', 'risk_level', 'model_name', 'detection_time']

class RiskAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskAnalysis
        fields = ['risk_score', 'risk_category', 'risk_factors', 'remarks', 'created_at']

class OTPVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTPVerification
        fields = ['otp_code', 'verification_status', 'generated_at', 'verified_at']

class TransactionSerializer(serializers.ModelSerializer):
    fraud_detection = FraudDetectionSerializer(read_only=True)
    risk_analysis = RiskAnalysisSerializer(read_only=True)
    otp_verification = OTPVerificationSerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'user', 'beneficiary', 'beneficiary_name', 'upi_id',
            'amount', 'transaction_type', 'timestamp', 'account_balance', 'device_type',
            'location', 'merchant_category', 'ip_address_flag', 'previous_fraudulent_activity',
            'daily_transaction_count', 'avg_transaction_amount_7d', 'failed_transaction_count_7d',
            'card_type', 'card_age', 'transaction_distance', 'authentication_method', 'is_weekend',
            'status', 'fraud_detection', 'risk_analysis', 'otp_verification'
        ]
        read_only_fields = ['id', 'transaction_id', 'user', 'timestamp', 'status']
