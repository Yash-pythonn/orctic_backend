"""
Utility functions for user authentication and management.
"""
import re
import bcrypt
import secrets
import string
from datetime import datetime
from qtratic.mongodb import get_mongo_collection
from bson import ObjectId

# User types
USER_TYPES = [
    ('customer', 'Customer'),
    ('admin', 'Admin'),
    ('vendor', 'Vendor'),
]


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except:
        return False


def generate_token(length: int = 32) -> str:
    """Generate random token for email verification or password reset."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def get_users_collection():
    """Get users collection."""
    return get_mongo_collection('users')


def find_user_by_email(email: str):
    """Find user by email from MongoDB."""
    collection = get_users_collection()
    return collection.find_one({'email': email.lower().strip()})


def find_user_by_id(user_id: str):
    """Find user by ID from MongoDB."""
    collection = get_users_collection()
    try:
        return collection.find_one({'_id': ObjectId(user_id)})
    except:
        return None


def find_user_by_reset_token(token: str):
    """Find user by reset password token."""
    collection = get_users_collection()
    return collection.find_one({
        'reset_password_token': token,
        'reset_password_expires': {'$gt': datetime.utcnow()}
    })


def find_user_by_verification_token(token: str):
    """Find user by email verification token."""
    collection = get_users_collection()
    return collection.find_one({'email_verification_token': token})


def user_to_dict(user_doc):
    """Convert MongoDB user document to dictionary (excluding sensitive fields)."""
    if not user_doc:
        return None
    
    return {
        'id': str(user_doc.get('_id')),
        'name': user_doc.get('name', ''),
        'email': user_doc.get('email', ''),
        'user_type': user_doc.get('user_type', 'customer'),
        'email_verified': user_doc.get('email_verified', False),
        'mobile': user_doc.get('mobile', ''),
        'is_active': user_doc.get('is_active', True),
        'created_at': user_doc.get('created_at'),
        'updated_at': user_doc.get('updated_at'),
    }

