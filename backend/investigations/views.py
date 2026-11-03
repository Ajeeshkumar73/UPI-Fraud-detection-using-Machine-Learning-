from rest_framework import serializers, generics, permissions, status, views
from rest_framework.response import Response
from investigations.models import FraudInvestigation
from transactions.models import Transaction
from users.models import AuditLog

class FraudInvestigationSerializer(serializers.ModelSerializer):
    transaction_id = serializers.CharField(source='transaction.transaction_id', read_only=True)
    investigator_name = serializers.CharField(source='investigated_by.username', read_only=True, default='Admin')

    class Meta:
        model = FraudInvestigation
        fields = ['id', 'transaction', 'transaction_id', 'investigated_by', 'investigator_name', 'investigation_status', 'final_result', 'remarks', 'investigation_date']
        read_only_fields = ['id', 'investigation_date']

class InvestigationListCreateView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        investigations = FraudInvestigation.objects.all().order_by('-investigation_date')
        return Response(FraudInvestigationSerializer(investigations, many=True).data)

    def post(self, request):
        txn_id = request.data.get('transaction_id')
        status_choice = request.data.get('investigation_status', 'Under Investigation')
        remarks = request.data.get('remarks', '')

        try:
            txn = Transaction.objects.get(transaction_id=txn_id)
        except Transaction.DoesNotExist:
            try:
                txn = Transaction.objects.get(pk=txn_id)
            except (Transaction.DoesNotExist, ValueError):
                return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user if request.user.is_authenticated else None
        investigation, created = FraudInvestigation.objects.get_or_create(transaction=txn)
        investigation.investigation_status = status_choice
        investigation.final_result = status_choice
        investigation.remarks = remarks
        if user:
            investigation.investigated_by = user
        investigation.save()

        AuditLog.objects.create(
            user=user,
            action='FRAUD_INVESTIGATION_UPDATE',
            description=f'Investigation updated for transaction {txn.transaction_id} to status {status_choice}'
        )

        return Response({
            'message': 'Investigation record updated',
            'investigation': FraudInvestigationSerializer(investigation).data
        }, status=status.HTTP_200_OK)
