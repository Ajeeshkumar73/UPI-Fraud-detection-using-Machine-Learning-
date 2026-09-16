from django.db import models
from django.conf import settings
from transactions.models import Transaction

class FraudInvestigation(models.Model):
    STATUS_CHOICES = (
        ('Under Investigation', 'Under Investigation'),
        ('Marked Genuine', 'Marked Genuine'),
        ('Confirmed Fraud', 'Confirmed Fraud'),
        ('Resolved', 'Resolved'),
    )
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='investigations')
    investigated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    investigation_status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Under Investigation')
    final_result = models.CharField(max_length=50, blank=True)
    remarks = models.TextField(blank=True)
    investigation_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-investigation_date']

    def __str__(self):
        return f"Investigation on {self.transaction.transaction_id}: {self.investigation_status}"
