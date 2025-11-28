"""
Serializers for user authentication and management.
"""
from rest_framework import serializers
from users.utils import USER_TYPES, validate_email, find_user_by_email


class UserRegistrationSerializer(serializers.Serializer):
    """Serializer for user registration."""
    name = serializers.CharField(max_length=255, required=True)
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, min_length=8, required=True)
    confirm_password = serializers.CharField(write_only=True, min_length=8, required=True)
    user_type = serializers.ChoiceField(
        choices=USER_TYPES,
        default='customer',
        required=False
    )
    mobile = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
    def validate_email(self, value):
        """Validate email format and uniqueness."""
        email = value.lower().strip()
        if not validate_email(email):
            raise serializers.ValidationError("Invalid email format.")
        
        # Check if email already exists in MongoDB
        existing_user = find_user_by_email(email)
        if existing_user:
            raise serializers.ValidationError("Email already registered.")
        
        return email
    
    def validate(self, data):
        """Validate password confirmation."""
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })
        return data


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    
    def validate_email(self, value):
        """Normalize email."""
        return value.lower().strip()


class UserProfileSerializer(serializers.Serializer):
    """Serializer for user profile."""
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=255, required=False)
    email = serializers.EmailField(read_only=True)
    user_type = serializers.ChoiceField(choices=USER_TYPES, required=False)
    email_verified = serializers.BooleanField(read_only=True)
    mobile = serializers.CharField(max_length=20, required=False, allow_blank=True)
    is_active = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password."""
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, min_length=8, required=True)
    confirm_password = serializers.CharField(write_only=True, min_length=8, required=True)
    
    def validate(self, data):
        """Validate password confirmation."""
        if data.get('new_password') != data.get('confirm_password'):
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })
        return data


class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for forgot password request."""
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Normalize email."""
        return value.lower().strip()


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for resetting password."""
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(write_only=True, min_length=8, required=True)
    confirm_password = serializers.CharField(write_only=True, min_length=8, required=True)
    
    def validate(self, data):
        """Validate password confirmation."""
        if data.get('new_password') != data.get('confirm_password'):
            raise serializers.ValidationError({
                "confirm_password": "Passwords do not match."
            })
        return data


class VerifyEmailSerializer(serializers.Serializer):
    """Serializer for email verification."""
    token = serializers.CharField(required=True)


class LoginResponseSerializer(serializers.Serializer):
    """Serializer for login response."""
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    user = UserProfileSerializer()


class AdminVerifyEmailSerializer(serializers.Serializer):
    """Serializer for admin-triggered email verification."""
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Normalize email."""
        return value.lower().strip()

