from django.db import models
from django.conf import settings

class Beneficiary(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='beneficiaries')
    beneficiary_name = models.CharField(max_length=150)
    upi_id = models.CharField(max_length=100)
    bank_name = models.CharField(max_length=100, default='State Bank of India')
    account_reference = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.beneficiary_name} ({self.upi_id})"
