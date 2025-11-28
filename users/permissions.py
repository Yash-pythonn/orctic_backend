"""
Custom permissions for user authentication.
"""
from rest_framework import permissions
from users.utils import find_user_by_id


class IsEmailVerified(permissions.BasePermission):
    """
    Permission class that checks if user's email is verified.
    Users must verify their email before accessing protected endpoints.
    """
    
    message = 'Email not verified. Please verify your email before accessing this resource.'
    
    def has_permission(self, request, view):
        """
        Check if the user's email is verified.
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Get user_id from request.user
        user_id = getattr(request.user, 'user_id', None)
        if not user_id:
            return False
        
        # Find user in MongoDB and check email_verified status
        user_doc = find_user_by_id(user_id)
        if not user_doc:
            return False
        
        # Check if email is verified
        email_verified = user_doc.get('email_verified', False)
        return email_verified
    
    def has_object_permission(self, request, view, obj):
        """
        Check if the user's email is verified for object-level permissions.
        """
        return self.has_permission(request, view)

