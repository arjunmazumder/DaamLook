from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import LoginSerializer, RegisterSerializer, SendOTPSerializer, VerifyOTPSerializer, UserSerializer, KYCProfileSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
from .services import login_user, refresh_tokens, logout_user
from django.utils import timezone
from datetime import timedelta
from .models import OTPVerification, KYCProfile
from .utils import generate_otp, send_otp_sms
from lookup.models import Lookup
from lookup.serializers import LookupSerializer

def set_auth_cookies(response, access_token, refresh_token):
    response.set_cookie(
        key='access_token',
        value=access_token,
        httponly=True,
        secure=True,
        samesite='Lax',
        max_age=15 * 60
    )
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite='Lax',
        max_age=7 * 24 * 60 * 60
    )

class RoleListView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['Authentication & Onboarding'],
        operation_summary="Get Roles",
        operation_description="Get all active roles from the lookup table for the registration form.",
        responses={200: LookupSerializer(many=True)}
    )
    def get(self, request):
        roles = Lookup.objects.filter(is_active=True)
        serializer = LookupSerializer(roles, many=True)
        return Response({
            "status": "success",
            "message": "Roles fetched successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

class RegisterView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['Authentication & Onboarding'],
        operation_summary="User Registration",
        operation_description="Register a new user after verifying OTP. Only verified phone numbers can be registered.",
        request_body=RegisterSerializer,
        responses={201: openapi.Response('User registered successfully. OTP sent.', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status': openapi.Schema(type=openapi.TYPE_STRING, example="success"),
                'message': openapi.Schema(type=openapi.TYPE_STRING, example="Registration successful. OTP sent to phone number."),
                'data': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            }
        )), 400: 'Bad Request'}
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Auto-generate and send OTP
            otp_code = generate_otp()
            expires_at = timezone.now() + timedelta(minutes=5)
            
            OTPVerification.objects.update_or_create(
                phone_number=user.phone_number,
                defaults={
                    'otp_code': otp_code,
                    'is_verified': False,
                    'expires_at': expires_at
                }
            )
            
            send_otp_sms(user.phone_number, otp_code)
            
            response_data = {
                "status": "success",
                "message": "Registration successful. OTP sent to phone number.",
                "data": {
                    "user": UserSerializer(user).data
                }
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['Authentication & Onboarding'],
        operation_summary="User Login",
        operation_description="Login user with phone number and password. Returns an access token and sets a secure HttpOnly cookie for the refresh token.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING),
                'password': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['phone_number', 'password'],
            example={
                "phone_number": "01700000000",
                "password": "admin"
            }
        ),
        responses={200: openapi.Response('Login successful', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status': openapi.Schema(type=openapi.TYPE_STRING, example="success"),
                'message': openapi.Schema(type=openapi.TYPE_STRING, example="Login successful."),
                'data': openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access_token': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            }
        )), 400: 'Bad Request'}
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            access_token, refresh_token = login_user(user)
            
            response_data = {
                "status": "success",
                "message": "Login successful.",
                "data": {
                    "access_token": access_token,
                    "user": UserSerializer(user).data
                }
            }
            
            response = Response(response_data, status=status.HTTP_200_OK)
            set_auth_cookies(response, access_token, refresh_token)
            return response
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RefreshTokenView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['Authentication & Onboarding'],
        operation_summary="Refresh Access Token",
        operation_description="Refresh the access token using the refresh token stored in the secure HttpOnly cookie.",
        responses={200: openapi.Response('Token refreshed', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'access_token': openapi.Schema(type=openapi.TYPE_STRING)}
        )), 401: 'Unauthorized'}
    )
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({'detail': 'Refresh token missing.'}, status=status.HTTP_401_UNAUTHORIZED)
            
        access_token, new_refresh_token = refresh_tokens(refresh_token)
        if not access_token:
            return Response({'detail': 'Invalid or expired refresh token.'}, status=status.HTTP_401_UNAUTHORIZED)
            
        response = Response({'access_token': access_token}, status=status.HTTP_200_OK)
        set_auth_cookies(response, access_token, new_refresh_token)
        return response

class LogoutView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['Authentication & Onboarding'],
        operation_summary="User Logout",
        operation_description="Logout the user by blacklisting the refresh token and clearing the secure HttpOnly cookie.",
        responses={200: openapi.Response('Successfully logged out', openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}
        ))}
    )
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            logout_user(refresh_token)
            
        response = Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['Authentication & Onboarding'],
        operation_summary="Forgot Password - Send OTP",
        request_body=ForgotPasswordSerializer,
        responses={200: 'OTP sent', 404: 'User not found'}
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            try:
                user = User.objects.get(phone_number=phone_number)
                
                # Delete existing unverified OTPs for this number
                OTPVerification.objects.filter(phone_number=phone_number).delete()
                
                otp_code = generate_otp()
                OTPVerification.objects.create(phone_number=phone_number, otp_code=otp_code)
                
                # Send SMS
                success = send_otp_sms(phone_number, otp_code)
                if success:
                    return Response({'status': 'success', 'message': 'OTP sent successfully for password reset.'}, status=status.HTTP_200_OK)
                else:
                    return Response({'status': 'error', 'message': 'Failed to send OTP.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
            except User.DoesNotExist:
                return Response({'status': 'error', 'message': 'No account found with this phone number.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['Authentication & Onboarding'],
        operation_summary="Reset Password with OTP",
        request_body=ResetPasswordSerializer,
        responses={200: 'Password reset successful', 400: 'Invalid OTP or passwords do not match'}
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            otp_code = serializer.validated_data['otp_code']
            new_password = serializer.validated_data['new_password']
            
            try:
                # Find the latest OTP verification for this phone number
                otp_record = OTPVerification.objects.filter(
                    phone_number=phone_number
                ).order_by('-id').first()
                
                if not otp_record or otp_record.otp_code != otp_code:
                    return Response({'status': 'error', 'message': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)
                    
                # Find user and reset password
                try:
                    user = User.objects.get(phone_number=phone_number)
                    user.set_password(new_password)
                    user.save()
                    
                    # Mark OTP as verified or delete it
                    otp_record.is_verified = True
                    otp_record.save()
                    
                    return Response({'status': 'success', 'message': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)
                except User.DoesNotExist:
                    return Response({'status': 'error', 'message': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
                    
            except Exception as e:
                 return Response({'status': 'error', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SendOTPView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['Authentication & Onboarding'],
        operation_summary="Send/Resend OTP",
        operation_description="Send a 6-digit OTP to the provided phone number for verification before registration. Re-sending to the same number updates the OTP.",
        request_body=SendOTPSerializer,
        responses={200: 'OTP Sent successfully', 400: 'Bad Request'}
    )
    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            
            otp_code = generate_otp()
            expires_at = timezone.now() + timedelta(minutes=5)
            
            otp_record, created = OTPVerification.objects.update_or_create(
                phone_number=phone_number,
                defaults={
                    'otp_code': otp_code,
                    'is_verified': False,
                    'expires_at': expires_at
                }
            )
            
            send_otp_sms(phone_number, otp_code)
            
            return Response({'detail': 'OTP sent successfully.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        tags=['Authentication & Onboarding'],
        operation_summary="Verify OTP",
        operation_description="Verify the 6-digit OTP sent to the phone number. Returns an access token if user is approved.",
        request_body=VerifyOTPSerializer,
        responses={200: 'OTP Verified successfully', 400: 'Invalid or expired OTP'}
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            otp_code = serializer.validated_data['otp_code']
            
            try:
                otp_record = OTPVerification.objects.get(phone_number=phone_number)
            except OTPVerification.DoesNotExist:
                return Response({'detail': 'OTP record not found. Please request a new OTP.'}, status=status.HTTP_404_NOT_FOUND)
                
            if otp_record.is_expired():
                return Response({'detail': 'OTP has expired.'}, status=status.HTTP_400_BAD_REQUEST)
                
            if otp_record.otp_code != otp_code:
                return Response({'detail': 'Invalid OTP code.'}, status=status.HTTP_400_BAD_REQUEST)
                
            otp_record.is_verified = True
            otp_record.save()
            
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(phone_number=phone_number)
                user.is_phone_verified = True
                user.save()
                
                if user.is_approved:
                    access_token, refresh_token = login_user(user)
                    response_data = {
                        "status": "success",
                        "message": "Phone number verified and login successful.",
                        "data": {
                            "access_token": access_token,
                            "user": UserSerializer(user).data
                        }
                    }
                    response = Response(response_data, status=status.HTTP_200_OK)
                    set_auth_cookies(response, access_token, refresh_token)
                    return response
                else:
                    return Response({
                        "status": "success",
                        "message": "Phone number verified successfully. Account is pending admin approval."
                    }, status=status.HTTP_200_OK)
                    
            except User.DoesNotExist:
                # If user doesn't exist yet, just verify OTP (might not happen with new flow)
                return Response({'detail': 'Phone number verified successfully.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class KYCProfileView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Users'],
        operation_summary="Get KYC Profile",
        responses={200: KYCProfileSerializer()}
    )
    def get(self, request):
        try:
            profile = KYCProfile.objects.get(user=request.user)
            serializer = KYCProfileSerializer(profile)
            return Response(serializer.data)
        except KYCProfile.DoesNotExist:
            return Response({'detail': 'KYC profile not found.'}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        tags=['Users'],
        operation_summary="Submit KYC Profile",
        request_body=KYCProfileSerializer,
        responses={201: KYCProfileSerializer(), 400: 'Bad Request'}
    )
    def post(self, request):
        if hasattr(request.user, 'kyc_profile'):
            return Response({'detail': 'KYC profile already exists. Use PUT/PATCH to update.'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = KYCProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=['Users'],
        operation_summary="Update KYC Profile",
        request_body=KYCProfileSerializer,
        responses={200: KYCProfileSerializer()}
    )
    def put(self, request):
        try:
            profile = KYCProfile.objects.get(user=request.user)
        except KYCProfile.DoesNotExist:
            return Response({'detail': 'KYC profile not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = KYCProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(status='PENDING') # Reset status on update
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=['Users'],
        operation_summary="Partial Update KYC Profile",
        request_body=KYCProfileSerializer,
        responses={200: KYCProfileSerializer()}
    )
    def patch(self, request):
        return self.put(request)

    @swagger_auto_schema(
        tags=['Users'],
        operation_summary="Delete KYC Profile",
        responses={204: 'No Content'}
    )
    def delete(self, request):
        try:
            profile = KYCProfile.objects.get(user=request.user)
            profile.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except KYCProfile.DoesNotExist:
            return Response({'detail': 'KYC profile not found.'}, status=status.HTTP_404_NOT_FOUND)
