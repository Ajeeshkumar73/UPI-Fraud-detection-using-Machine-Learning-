from rest_framework import serializers, viewsets, permissions
from beneficiaries.models import Beneficiary

class BeneficiarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Beneficiary
        fields = ['id', 'user', 'beneficiary_name', 'upi_id', 'bank_name', 'account_reference', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']

class BeneficiaryViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = BeneficiarySerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Beneficiary.objects.filter(user=self.request.user)
        return Beneficiary.objects.all()

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        if not user:
            # Fallback to demo user if unauthenticated demo
            from users.models import User
            user = User.objects.filter(username='demo_user').first()
            if not user:
                user = User.objects.create_user(username='demo_user', email='demo@upifraud.local', full_name='Demo User')
        serializer.save(user=user)
