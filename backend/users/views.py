import random
from datetime import timedelta
from rest_framework import status, views, permissions, generics
from rest_framework.response import Response
from django.contrib.auth import login, logout
from django.utils import timezone
from users.models import User, LoginHistory, AuditLog, PasswordResetOTP
from users.serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer, AuditLogSerializer,
    ForgotPasswordRequestSerializer, ForgotPasswordResetSerializer
)

class RegisterView(views.APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            AuditLog.objects.create(user=user, action='USER_REGISTER', description=f'Registered user {user.username}')
            return Response({
                'message': 'Registration successful',
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        first_err = serializer.errors.get('non_field_errors') or list(serializer.errors.values())[0]
        err_msg = first_err[0] if isinstance(first_err, list) else str(first_err)
        return Response({'error': err_msg, 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            
            # Log login history
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
            user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown Device')
            LoginHistory.objects.create(user=user, ip_address=ip, device_info=user_agent[:250])
            AuditLog.objects.create(user=user, action='USER_LOGIN', description=f'User {user.username} logged in')

            return Response({
                'message': 'Login successful',
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        first_err = serializer.errors.get('non_field_errors') or list(serializer.errors.values())[0]
        err_msg = first_err[0] if isinstance(first_err, list) else str(first_err)
        return Response({'error': err_msg, 'details': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(views.APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        if request.user.is_authenticated:
            AuditLog.objects.create(user=request.user, action='USER_LOGOUT', description=f'User {request.user.username} logged out')
        logout(request)
        return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)

class ProfileView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(UserSerializer(request.user).data)

class AdminUserListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserSerializer

class AdminUserToggleActiveView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            user.is_active = not user.is_active
            user.save()
            AuditLog.objects.create(user=request.user if request.user.is_authenticated else None, 
                                     action='USER_TOGGLE_ACTIVE', 
                                     description=f'User {user.username} is_active set to {user.is_active}')
            return Response({'message': f'User active status updated to {user.is_active}', 'user': UserSerializer(user).data})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class AuditLogListView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    queryset = AuditLog.objects.all().order_by('-timestamp')
    serializer_class = AuditLogSerializer

class ForgotPasswordRequestOTPView(views.APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = ForgotPasswordRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data['username']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': f'No user account found with username "{username}"'}, status=status.HTTP_404_NOT_FOUND)

        # Invalidate previous unused OTPs
        PasswordResetOTP.objects.filter(user=user, is_used=False).update(is_used=True)

        # Generate 6-digit OTP code
        otp_code = f"{random.randint(100000, 999999):06d}"
        PasswordResetOTP.objects.create(user=user, otp_code=otp_code)

        # Print OTP to terminal output
        print("\n" + "=" * 60)
        print(f" [FORGOT PASSWORD OTP DISPATCH]")
        print(f" Username : {user.username}")
        print(f" OTP Code : {otp_code}")
        print(f" Time     : {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60 + "\n", flush=True)

        return Response({
            'message': 'OTP generated successfully! Please check your server terminal to view the OTP code.',
            'username': user.username
        }, status=status.HTTP_200_OK)

class ForgotPasswordResetView(views.APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = ForgotPasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            # Format validation error message
            first_err = list(serializer.errors.values())[0]
            err_msg = first_err[0] if isinstance(first_err, list) else str(first_err)
            return Response({'error': err_msg}, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data['username']
        otp_code = serializer.validated_data['otp_code']
        new_password = serializer.validated_data['new_password']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'User account not found'}, status=status.HTTP_404_NOT_FOUND)

        ten_minutes_ago = timezone.now() - timedelta(minutes=10)
        otp_record = PasswordResetOTP.objects.filter(
            user=user,
            otp_code=otp_code,
            is_used=False,
            created_at__gte=ten_minutes_ago
        ).first()

        if not otp_record:
            return Response({'error': 'Invalid or expired OTP code. Please check terminal or request a new OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        # Reset user password
        user.set_password(new_password)
        user.save()

        # Mark OTP as used
        otp_record.is_used = True
        otp_record.save()

        # Audit Log
        AuditLog.objects.create(
            user=user,
            action='USER_PASSWORD_RESET',
            description=f'Password reset successfully via terminal OTP for user {user.username}'
        )

        return Response({
            'message': 'Password has been reset successfully. You can now log in with your new password.'
        }, status=status.HTTP_200_OK)


