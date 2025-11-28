"""
Utility helpers for category APIs interacting with MongoDB.
"""
import re
import secrets
from datetime import datetime
from typing import Optional

from bson import ObjectId
from bson.regex import Regex
from django.utils.text import slugify

from qtratic.mongodb import get_mongo_collection


CATEGORY_FOR_CHOICES = {'men', 'women', 'children', 'other'}


def get_categories_collection():
    """Return MongoDB collection for categories."""
    return get_mongo_collection('categories')


def normalize_category_name(name: str) -> str:
    """Trim excessive whitespace and normalize spacing."""
    normalized = re.sub(r'\s+', ' ', name or '').strip()
    return normalized


def category_exists_by_name(name: str, exclude_id: Optional[str] = None) -> bool:
    """Check if a category with the provided name exists."""
    if not name:
        return False
    
    query = {'name_lower': name.lower()}
    if exclude_id:
        try:
            query['_id'] = {'$ne': ObjectId(exclude_id)}
        except Exception:
            pass
    
    collection = get_categories_collection()
    return collection.find_one(query) is not None


def generate_unique_slug(name: str, exclude_id: Optional[str] = None) -> str:
    """Generate a slug from name ensuring uniqueness."""
    base_slug = slugify(name) or secrets.token_hex(4)
    collection = get_categories_collection()
    slug = base_slug
    counter = 1
    
    query = {'slug': slug}
    if exclude_id:
        try:
            query['_id'] = {'$ne': ObjectId(exclude_id)}
        except Exception:
            pass
    
    while collection.find_one(query):
        slug = f"{base_slug}-{counter}"
        counter += 1
        query['slug'] = slug
    
    return slug


def find_category_by_id(category_id: str):
    """Fetch a single category document by its ID."""
    try:
        object_id = ObjectId(category_id)
    except Exception:
        return None
    
    collection = get_categories_collection()
    return collection.find_one({'_id': object_id})


def category_to_dict(category_doc):
    """Serialize Mongo document into API-friendly dict."""
    print(category_doc,'category_doc')
    if not category_doc:
        return None
    return {
        'id': str(category_doc.get('_id')),
        'name': category_doc.get('name', ''),
        'slug': category_doc.get('slug', ''),
        'description': category_doc.get('description', ''),
        'is_active': category_doc.get('is_active', True),
        'category_for': category_doc.get('category_for', 'other'),
        'created_by': _stringify_object_id(category_doc.get('created_by')),
        'created_at': category_doc.get('created_at'),
        'updated_at': category_doc.get('updated_at'),
    }


def build_category_document(data, user_id: Optional[str] = None, slug: Optional[str] = None):
    """Create a Mongo document for insert operations."""
    now = datetime.utcnow()
    normalized_name = normalize_category_name(data.get('name', ''))
    document = {
        'name': normalized_name,
        'name_lower': normalized_name.lower(),
        'slug': slug or generate_unique_slug(normalized_name),
        'description': data.get('description') or '',
        'is_active': data.get('is_active', True),
        'category_for': _normalize_category_for(data.get('category_for')),
        'created_at': now,
        'updated_at': now,
    }
    
    if user_id:
        try:
            document['created_by'] = ObjectId(user_id)
        except Exception:
            document['created_by'] = user_id
    
    return document


def update_category_document(existing_doc, data):
    """Build update payload by comparing existing values."""
    updates = {}
    normalized_name = None
    if 'name' in data:
        normalized_name = normalize_category_name(data['name'])
        if normalized_name != existing_doc.get('name'):
            updates['name'] = normalized_name
            updates['name_lower'] = normalized_name.lower()
            updates['slug'] = generate_unique_slug(normalized_name, exclude_id=str(existing_doc.get('_id')))
    
    if 'description' in data:
        updates['description'] = data['description'] or ''
    
    if 'is_active' in data:
        updates['is_active'] = bool(data['is_active'])
    
    if 'category_for' in data:
        updates['category_for'] = _normalize_category_for(data['category_for'])
    
    if updates:
        updates['updated_at'] = datetime.utcnow()
    
    return updates


def build_search_filter(search: Optional[str], is_active: Optional[bool], category_for: Optional[str]):
    """Construct Mongo filter for list endpoint."""
    filters = {}
    if search:
        regex_pattern = Regex.from_native(
            re.compile(re.escape(search), re.IGNORECASE)
        )
        filters['$or'] = [
            {'name': {'$regex': regex_pattern}},
            {'description': {'$regex': regex_pattern}},
        ]
    
    if is_active is not None:
        filters['is_active'] = is_active

    if category_for:
        filters['category_for'] = _normalize_category_for(category_for)
    
    return filters


def _stringify_object_id(value):
    """Convert ObjectId to string safely."""
    if isinstance(value, ObjectId):
        return str(value)
    return value


def _normalize_category_for(value: Optional[str]) -> str:
    """Normalize category audience; fallback to 'other'."""
    if not value:
        return 'other'
    lowered = str(value).strip().lower()
    if lowered not in CATEGORY_FOR_CHOICES:
        return 'other'
    return lowered


