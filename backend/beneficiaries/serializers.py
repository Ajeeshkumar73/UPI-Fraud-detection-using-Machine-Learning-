from rest_framework import serializers
from beneficiaries.models import Beneficiary

class BeneficiarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Beneficiary
        fields = ['id', 'user', 'beneficiary_name', 'upi_id', 'bank_name', 'account_reference', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
