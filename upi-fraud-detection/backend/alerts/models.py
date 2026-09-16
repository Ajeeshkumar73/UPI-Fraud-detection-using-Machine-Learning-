from django.db import models
from django.conf import settings
from transactions.models import Transaction

class FraudAlert(models.Model):
    STATUS_CHOICES = (
        ('New', 'New Alert'),
        ('Viewed', 'Viewed'),
        ('Investigating', 'Under Investigation'),
        ('Resolved', 'Resolved'),
    )
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='alerts')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=50, default='High Fraud Risk Detected')
    alert_message = models.TextField()
    risk_score = models.FloatField()
    alert_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='New')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Alert {self.id} for {self.transaction.transaction_id} ({self.alert_status})"
