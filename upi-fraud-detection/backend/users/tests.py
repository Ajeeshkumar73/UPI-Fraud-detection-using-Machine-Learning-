from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User, PasswordResetOTP

class ForgotPasswordAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='OldPassword@123',
            email='test@example.com'
        )

    def test_request_otp_success(self):
        response = self.client.post('/api/auth/forgot-password/request-otp/', {'username': 'testuser'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('OTP generated successfully', response.data['message'])
        otp_record = PasswordResetOTP.objects.filter(user=self.user, is_used=False).first()
        self.assertIsNotNone(otp_record)
        self.assertEqual(len(otp_record.otp_code), 6)

    def test_request_otp_user_not_found(self):
        response = self.client.post('/api/auth/forgot-password/request-otp/', {'username': 'nonexistent'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_reset_password_success(self):
        # Generate OTP
        self.client.post('/api/auth/forgot-password/request-otp/', {'username': 'testuser'})
        otp_record = PasswordResetOTP.objects.get(user=self.user, is_used=False)

        # Reset Password
        reset_res = self.client.post('/api/auth/forgot-password/reset/', {
            'username': 'testuser',
            'otp_code': otp_record.otp_code,
            'new_password': 'NewSecurePassword@123'
        })
        self.assertEqual(reset_res.status_code, status.HTTP_200_OK)

        # Verify password updated
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewSecurePassword@123'))

        # Verify OTP marked as used
        otp_record.refresh_from_db()
        self.assertTrue(otp_record.is_used)

    def test_reset_password_invalid_otp(self):
        self.client.post('/api/auth/forgot-password/request-otp/', {'username': 'testuser'})
        reset_res = self.client.post('/api/auth/forgot-password/reset/', {
            'username': 'testuser',
            'otp_code': '000000',
            'new_password': 'NewSecurePassword@123'
        })
        self.assertEqual(reset_res.status_code, status.HTTP_400_BAD_REQUEST)

