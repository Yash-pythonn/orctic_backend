"""
Custom JWT authentication for MongoDB User model.
Directly using MongoDB collections.
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import AnonymousUser
from users.utils import find_user_by_id


class MongoUser:
    """
    Custom user class for MongoDB authentication.
    Compatible with Django REST Framework.
    """
    def __init__(self, user_doc):
        self.user_id = str(user_doc.get('_id'))
        self.id = self.user_id
        self.email = user_doc.get('email', '')
        self.user_type = user_doc.get('user_type', 'customer')
        self.email_verified = user_doc.get('email_verified', False)
        self.is_authenticated = True
        self.is_active = user_doc.get('is_active', True)
        self.is_anonymous = False
    
    def get(self, key, default=None):
        """Dict-like get method for compatibility."""
        return getattr(self, key, default)
    
    def __getitem__(self, key):
        """Dict-like access."""
        return getattr(self, key, None)
    
    def __str__(self):
        return self.email or self.user_id


class MongoDBJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that works directly with MongoDB.
    """
    
    def get_user(self, validated_token):
        """
        Attempts to find and return a user using the given validated token.
        Directly queries MongoDB.
        """
        try:
            user_id = validated_token.get('user_id')
            
            if not user_id:
                return AnonymousUser()
            
            # Find user directly from MongoDB
            user_doc = find_user_by_id(user_id)
            
            if not user_doc or not user_doc.get('is_active', True):
                return AnonymousUser()
            
            # Return a MongoUser object with is_authenticated attribute
            return MongoUser(user_doc)
            
        except Exception as e:
            return AnonymousUser()

