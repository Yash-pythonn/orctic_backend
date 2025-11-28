"""
API views for user authentication and management.
Directly using MongoDB collections.
"""
from datetime import datetime, timedelta
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.permissions import IsEmailVerified
from rest_framework_simplejwt.tokens import RefreshToken
from bson import ObjectId

from users.utils import (
    validate_email,
    hash_password,
    verify_password,
    generate_token,
    get_users_collection,
    find_user_by_email,
    find_user_by_id,
    find_user_by_reset_token,
    find_user_by_verification_token,
    user_to_dict,
    USER_TYPES,
)
from users.serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    VerifyEmailSerializer,
    AdminVerifyEmailSerializer,
)
from users.email_service import (
    send_email_verification,
    send_password_reset_email,
    send_email_verification_confirmation,
    send_password_reset_confirmation,
)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register a new user."""
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        collection = get_users_collection()
        name = serializer.validated_data['name']
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user_type = serializer.validated_data.get('user_type', 'customer')
        mobile = serializer.validated_data.get('mobile', '')
        
        # Check if email already exists
        existing_user = find_user_by_email(email)
        if existing_user:
            return Response(
                {'error': 'Email already registered.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create new user document
        now = datetime.utcnow()
        user_doc = {
            'name': name,
            'email': email.lower().strip(),
            'password_hash': hash_password(password),
            'user_type': user_type,
            'email_verified': False,
            'email_verification_token': generate_token(),
            'mobile': mobile,
            'is_active': True,
            'created_at': now,
            'updated_at': now,
            'reset_password_token': '',
            'reset_password_expires': None,
        }
        
        # Insert user into MongoDB
        result = collection.insert_one(user_doc)
        user_doc['_id'] = result.inserted_id
        
        # Send email verification email
        verification_token = user_doc.get('email_verification_token')
        try:
            send_email_verification(
                user_email=user_doc['email'],
                user_name=user_doc['name'],
                verification_token=verification_token
            )
        except Exception as e:
            print(f"Failed to send verification email: {e}")
            # Continue even if email fails
        
        # Generate JWT tokens
        refresh = RefreshToken()
        refresh['user_id'] = str(user_doc['_id'])
        refresh['email'] = user_doc['email']
        
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Prepare response
        user_data = user_to_dict(user_doc)
        
        response_data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user_data,
            'message': 'User registered successfully. Please check your email to verify your account.',
            'email_verified': False,
            'verification_required': True,
            'note': 'Verification email has been sent. Please verify your email before accessing protected endpoints.'
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Login user and return JWT tokens."""
    serializer = UserLoginSerializer(data=request.data)
    
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        # Find user in MongoDB
        user_doc = find_user_by_email(email)
        
        if not user_doc:
            return Response(
                {'error': 'Invalid email or password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Verify password
        password_hash = user_doc.get('password_hash', '')
        if not verify_password(password, password_hash):
            return Response(
                {'error': 'Invalid email or password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if user is active
        if not user_doc.get('is_active', True):
            return Response(
                {'error': 'Account is deactivated.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if email is verified
        email_verified = user_doc.get('email_verified', False)
        if not email_verified:
            return Response(
                {
                    'error': 'Email not verified. Please verify your email before accessing the system.',
                    'email_verified': False,
                    'verification_required': True
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate JWT tokens
        refresh = RefreshToken()
        refresh['user_id'] = str(user_doc['_id'])
        refresh['email'] = user_doc['email']
        
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Prepare response
        user_data = user_to_dict(user_doc)
        
        response_data = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user_data,
            'message': 'Login successful.'
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsEmailVerified])
def get_profile(request):
    """Get current user profile."""
    user_id = getattr(request.user, 'user_id', None)
    
    if not user_id:
        return Response(
            {'error': 'User not found in token.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Find user in MongoDB
    user_doc = find_user_by_id(user_id)
    
    if not user_doc:
        return Response(
            {'error': 'User not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    user_data = user_to_dict(user_doc)
    
    return Response(user_data, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsEmailVerified])
def update_profile(request):
    """Update user profile."""
    user_id = getattr(request.user, 'user_id', None)
    
    if not user_id:
        return Response(
            {'error': 'User not found in token.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Find user in MongoDB
    user_doc = find_user_by_id(user_id)
    
    if not user_doc:
        return Response(
            {'error': 'User not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = UserProfileSerializer(data=request.data, partial=True)
    
    if serializer.is_valid():
        collection = get_users_collection()
        update_data = {}
        
        # Update allowed fields
        if 'name' in serializer.validated_data:
            update_data['name'] = serializer.validated_data['name']
        if 'user_type' in serializer.validated_data:
            update_data['user_type'] = serializer.validated_data['user_type']
        if 'mobile' in serializer.validated_data:
            update_data['mobile'] = serializer.validated_data['mobile']
        
        if update_data:
            update_data['updated_at'] = datetime.utcnow()
            collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': update_data}
            )
            
            # Get updated user
            user_doc = find_user_by_id(user_id)
        
        user_data = user_to_dict(user_doc)
        
        return Response({
            'user': user_data,
            'message': 'Profile updated successfully.'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsEmailVerified])
def change_password(request):
    """Change user password."""
    user_id = getattr(request.user, 'user_id', None)
    
    if not user_id:
        return Response(
            {'error': 'User not found in token.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Find user in MongoDB
    user_doc = find_user_by_id(user_id)
    
    if not user_doc:
        return Response(
            {'error': 'User not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = ChangePasswordSerializer(data=request.data)
    
    if serializer.is_valid():
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']
        
        # Verify old password
        password_hash = user_doc.get('password_hash', '')
        if not verify_password(old_password, password_hash):
            return Response(
                {'error': 'Current password is incorrect.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update password in MongoDB
        collection = get_users_collection()
        collection.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$set': {
                    'password_hash': hash_password(new_password),
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        return Response({
            'message': 'Password changed successfully.'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    """Request password reset."""
    serializer = ForgotPasswordSerializer(data=request.data)
    
    if serializer.is_valid():
        email = serializer.validated_data['email']
        user_doc = find_user_by_email(email)
        
        if user_doc:
            # Generate reset token and update in MongoDB
            collection = get_users_collection()
            reset_token = generate_token()
            reset_expires = datetime.utcnow() + timedelta(hours=24)
            
            collection.update_one(
                {'_id': user_doc['_id']},
                {
                    '$set': {
                        'reset_password_token': reset_token,
                        'reset_password_expires': reset_expires,
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            # Send password reset email
            try:
                send_password_reset_email(
                    user_email=user_doc['email'],
                    user_name=user_doc.get('name', 'User'),
                    reset_token=reset_token
                )
            except Exception as e:
                print(f"Failed to send password reset email: {e}")
                # Continue even if email fails
        
        # Always return success to prevent email enumeration
        return Response({
            'message': 'If the email exists, a password reset link has been sent to your email.'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """Reset password using token."""
    serializer = ResetPasswordSerializer(data=request.data)
    
    if serializer.is_valid():
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        # Find user by reset token in MongoDB
        user_doc = find_user_by_reset_token(token)
        
        if not user_doc:
            return Response(
                {'error': 'Invalid or expired reset token.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update password in MongoDB
        collection = get_users_collection()
        collection.update_one(
            {'_id': user_doc['_id']},
            {
                '$set': {
                    'password_hash': hash_password(new_password),
                    'reset_password_token': '',
                    'reset_password_expires': None,
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        # Send password reset confirmation email
        try:
            send_password_reset_confirmation(
                user_email=user_doc['email'],
                user_name=user_doc.get('name', 'User')
            )
        except Exception as e:
            print(f"Failed to send password reset confirmation email: {e}")
            # Continue even if email fails
        
        return Response({
            'message': 'Password reset successfully. A confirmation email has been sent.'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """Verify user email using token."""
    serializer = VerifyEmailSerializer(data=request.data)
    
    if serializer.is_valid():
        token = serializer.validated_data['token']
        
        # Find user by verification token in MongoDB
        user_doc = find_user_by_verification_token(token)
        
        if not user_doc:
            return Response(
                {'error': 'Invalid verification token.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if user_doc.get('email_verified', False):
            return Response({
                'message': 'Email already verified.'
            }, status=status.HTTP_200_OK)
        
        # Mark email as verified in MongoDB
        collection = get_users_collection()
        collection.update_one(
            {'_id': user_doc['_id']},
            {
                '$set': {
                    'email_verified': True,
                    'email_verification_token': '',
                    'updated_at': datetime.utcnow()
                }
            }
        )
        
        # Send email verification confirmation
        try:
            send_email_verification_confirmation(
                user_email=user_doc['email'],
                user_name=user_doc.get('name', 'User')
            )
        except Exception as e:
            print(f"Failed to send verification confirmation email: {e}")
            # Continue even if email fails
        
        return Response({
            'message': 'Email verified successfully. You can now access all protected endpoints. A confirmation email has been sent.',
            'email_verified': True,
            'verification_required': False
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def admin_verify_email(request):
    """Admin-triggered resend of verification email (no token needed)."""
    serializer = AdminVerifyEmailSerializer(data=request.data)

    if serializer.is_valid():
        email = serializer.validated_data['email']
        
        user_doc = find_user_by_email(email)
        if not user_doc:
            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if user_doc.get('email_verified', False):
            return Response({
                'message': 'Email already verified.'
            }, status=status.HTTP_200_OK)

        # generate new token
        verification_token = generate_token()
        collection = get_users_collection()
        collection.update_one(
            {'_id': user_doc['_id']},
            {
                '$set': {
                    'email_verification_token': verification_token,
                    'updated_at': datetime.utcnow()
                }
            }
        )

        try:
            send_email_verification(
                user_email=user_doc['email'],
                user_name=user_doc.get('name', 'User'),
                verification_token=verification_token
            )
        except Exception as e:
            print(f"Failed to send admin-triggered verification email: {e}")
            return Response(
                {
                    'error': 'Failed to send verification email. Check email configuration.',
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            'message': 'Verification email sent successfully.',
            'email_verified': False,
            'verification_required': True
        }, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """Refresh access token using refresh token."""
    refresh_token_str = request.data.get('refresh_token')
    
    if not refresh_token_str:
        return Response(
            {'error': 'Refresh token is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        refresh = RefreshToken(refresh_token_str)
        access_token = str(refresh.access_token)
        
        return Response({
            'access_token': access_token,
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {'error': 'Invalid refresh token.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
