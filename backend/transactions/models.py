from django.db import models
from django.conf import settings
from beneficiaries.models import Beneficiary

class Transaction(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('APPROVED_AFTER_OTP', 'Approved after OTP'),
        ('OTP_REQUIRED', 'OTP Verification Required'),
        ('BLOCKED', 'Blocked Fraudulent'),
    )

    transaction_id = models.CharField(max_length=50, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    beneficiary_name = models.CharField(max_length=150)
    upi_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=50, default='Online')
    timestamp = models.DateTimeField(auto_now_add=True)
    account_balance = models.DecimalField(max_digits=12, decimal_places=2, default=50000.00)
    device_type = models.CharField(max_length=50, default='Mobile')
    location = models.CharField(max_length=100, default='Mumbai')
    merchant_category = models.CharField(max_length=50, default='Retail')
    ip_address_flag = models.IntegerField(default=0)
    previous_fraudulent_activity = models.IntegerField(default=0)
    daily_transaction_count = models.IntegerField(default=1)
    avg_transaction_amount_7d = models.DecimalField(max_digits=12, decimal_places=2, default=500.00)
    failed_transaction_count_7d = models.IntegerField(default=0)
    card_type = models.CharField(max_length=50, default='Debit')
    card_age = models.IntegerField(default=365)
    transaction_distance = models.DecimalField(max_digits=10, decimal_places=2, default=5.00)
    authentication_method = models.CharField(max_length=50, default='PIN')
    is_weekend = models.IntegerField(default=0)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING')

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.transaction_id} - INR {self.amount} ({self.status})"
