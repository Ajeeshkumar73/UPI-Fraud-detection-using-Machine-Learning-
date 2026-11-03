from rest_framework import serializers
from alerts.models import FraudAlert

class FraudAlertSerializer(serializers.ModelSerializer):
    transaction_id = serializers.CharField(source='transaction.transaction_id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = FraudAlert
        fields = ['id', 'transaction', 'transaction_id', 'user', 'username', 'alert_type', 'alert_message', 'risk_score', 'alert_status', 'created_at']
        read_only_fields = ['id', 'created_at']
