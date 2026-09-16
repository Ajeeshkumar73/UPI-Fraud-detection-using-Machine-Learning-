from django.db import models
from transactions.models import Transaction

class FraudDetection(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='fraud_detection')
    prediction_result = models.CharField(max_length=20) # Fraud / Genuine
    fraud_probability = models.FloatField()
    risk_score = models.FloatField() # 0 - 100
    risk_level = models.CharField(max_length=20) # Low / Medium / High
    model_name = models.CharField(max_length=100, default='Random Forest')
    model_version = models.CharField(max_length=20, default='1.0.0')
    detection_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction.transaction_id} -> {self.risk_level} Risk ({self.risk_score})"

class RiskAnalysis(models.Model):
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='risk_analysis')
    risk_score = models.FloatField()
    risk_category = models.CharField(max_length=20)
    risk_factors = models.JSONField(default=list)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class OTPVerification(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Verification'),
        ('VERIFIED', 'Verified Successfully'),
        ('EXPIRED', 'Expired'),
    )
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='otp_verification')
    otp_code = models.CharField(max_length=10)
    verification_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    generated_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"OTP for {self.transaction.transaction_id}: {self.verification_status}"
