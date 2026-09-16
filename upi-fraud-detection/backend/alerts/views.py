from rest_framework import views, permissions, status, generics
from rest_framework.response import Response
from alerts.models import FraudAlert
from alerts.serializers import FraudAlertSerializer

class AlertListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = FraudAlertSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and getattr(user, 'role', 'USER') != 'ADMIN':
            return FraudAlert.objects.filter(user=user)
        return FraudAlert.objects.all()

class AlertStatusUpdateView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def put(self, request, pk):
        try:
            alert = FraudAlert.objects.get(pk=pk)
            new_status = request.data.get('status', 'Viewed')
            alert.alert_status = new_status
            alert.save()
            return Response({'message': f'Alert status updated to {new_status}', 'alert': FraudAlertSerializer(alert).data})
        except FraudAlert.DoesNotExist:
            return Response({'error': 'Alert not found'}, status=status.HTTP_404_NOT_FOUND)
