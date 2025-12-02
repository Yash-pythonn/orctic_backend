"""
Utility helpers for product APIs interacting with MongoDB.
"""
import re
import secrets
from datetime import datetime
from typing import Optional, Sequence

from bson import ObjectId
from bson.regex import Regex
from django.utils.text import slugify

from categories import utils as category_utils
from qtratic.mongodb import get_mongo_collection


def get_products_collection():
    """Return MongoDB collection for products."""

    return get_mongo_collection('products')


def normalize_product_name(name: Optional[str]) -> str:
    """Normalize product name by trimming and collapsing whitespace."""

    return re.sub(r'\s+', ' ', (name or '').strip())


def product_exists_by_name(name: str, exclude_id: Optional[str] = None) -> bool:
    """Check if a product with the provided name exists."""

    if not name:
        return False

    query = {'name_lower': name.lower()}
    if exclude_id:
        try:
            query['_id'] = {'$ne': ObjectId(exclude_id)}
        except Exception:
            pass

    return get_products_collection().find_one(query) is not None


def product_exists_by_slug(slug: str, exclude_id: Optional[str] = None) -> bool:
    """Check if a slug already exists."""

    if not slug:
        return False

    query = {'slug': slug}
    if exclude_id:
        try:
            query['_id'] = {'$ne': ObjectId(exclude_id)}
        except Exception:
            pass

    return get_products_collection().find_one(query) is not None


def generate_unique_slug(name: str, exclude_id: Optional[str] = None) -> str:
    """Generate unique slug from name."""

    base_slug = slugify(name) or secrets.token_hex(4)
    slug = base_slug
    counter = 1
    collection = get_products_collection()

    query = {'slug': slug}
    if exclude_id:
        try:
            query['_id'] = {'$ne': ObjectId(exclude_id)}
        except Exception:
            pass

    while collection.find_one(query):
        slug = f"{base_slug}-{counter}"
        query['slug'] = slug
        counter += 1

    return slug


def find_product_by_id(product_id: str):
    """Fetch a product by its ID."""

    try:
        object_id = ObjectId(product_id)
    except Exception:
        return None

    return get_products_collection().find_one({'_id': object_id})


def product_to_dict(product_doc):
    """Serialize Mongo product document into API-friendly dict."""

    if not product_doc:
        return None

    category_snapshot = product_doc.get('category_snapshot') or {}
    category_id = product_doc.get('category_id')
    return {
        'id': str(product_doc.get('_id')),
        'name': product_doc.get('name', ''),
        'slug': product_doc.get('slug', ''),
        'description': product_doc.get('description', ''),
        'price': product_doc.get('price') or {},
        'offer': product_doc.get('offer'),
        'image': product_doc.get('image'),
        'key_highlights': product_doc.get('key_highlights', []),
        'highlights': product_doc.get('highlights', []),
        'quantity': product_doc.get('quantity', 0),
        'category': category_snapshot,
        'category_id': _stringify_object_id(category_id),
        'product_tag_line': product_doc.get('product_tag_line', ''),
        'created_by': _stringify_object_id(product_doc.get('created_by')),
        'created_at': product_doc.get('created_at'),
        'updated_at': product_doc.get('updated_at'),
    }


def build_product_document(data, user_id: Optional[str] = None, category_doc=None):
    """Create Mongo document for new product."""

    now = datetime.utcnow()
    normalized_name = normalize_product_name(data.get('name'))
    category_doc = category_doc or _resolve_category_doc(data.get('category_id'))
    document = {
        'name': normalized_name,
        'name_lower': normalized_name.lower(),
        'slug': data.get('slug') or generate_unique_slug(normalized_name),
        'description': data.get('description') or '',
        'price': _normalize_price(data.get('price')),
        'offer': _normalize_offer(data.get('offer')),
        'image': data.get('image'),
        'key_highlights': _normalize_highlights(data.get('key_highlights')),
        'highlights': _normalize_highlights(data.get('highlights')),
        'quantity': int(data.get('quantity', 0)),
        'category_id': category_doc.get('_id') if category_doc else None,
        'category_snapshot': _build_category_snapshot(category_doc),
        'product_tag_line': data.get('product_tag_line') or '',
        'created_at': now,
        'updated_at': now,
    }

    if user_id:
        try:
            document['created_by'] = ObjectId(user_id)
        except Exception:
            document['created_by'] = user_id

    return document


def update_product_document(existing_doc, data, category_doc=None):
    """Build update payload based on provided data."""

    updates = {}
    normalized_name = None

    if 'name' in data:
        normalized_name = normalize_product_name(data.get('name'))
        if normalized_name != existing_doc.get('name'):
            updates['name'] = normalized_name
            updates['name_lower'] = normalized_name.lower()
            updates['slug'] = data.get('slug') or generate_unique_slug(
                normalized_name, exclude_id=str(existing_doc.get('_id'))
            )

    if 'slug' in data and data.get('slug'):
        updates['slug'] = data['slug']

    for field in ('description', 'image', 'product_tag_line'):
        if field in data:
            updates[field] = data.get(field) or ''

    if 'price' in data:
        updates['price'] = _normalize_price(data.get('price'))

    if 'offer' in data:
        updates['offer'] = _normalize_offer(data.get('offer'))

    if 'quantity' in data:
        updates['quantity'] = int(data.get('quantity', 0))

    if 'key_highlights' in data:
        updates['key_highlights'] = _normalize_highlights(data.get('key_highlights'))

    if 'highlights' in data:
        updates['highlights'] = _normalize_highlights(data.get('highlights'))

    if 'category_id' in data:
        category_doc = category_doc or _resolve_category_doc(data.get('category_id'))
        updates['category_id'] = category_doc.get('_id') if category_doc else None
        updates['category_snapshot'] = _build_category_snapshot(category_doc)

    if updates:
        updates['updated_at'] = datetime.utcnow()

    return updates


def build_search_filter(
    search: Optional[str],
    category_id: Optional[str],
    slug: Optional[str],
    offer_only: Optional[bool],
    min_price: Optional[float],
    max_price: Optional[float],
):
    """Construct Mongo filter for product listing."""

    filters = {}

    if search:
        regex_pattern = Regex.from_native(
            re.compile(re.escape(search), re.IGNORECASE)
        )
        filters['$or'] = [
            {'name': {'$regex': regex_pattern}},
            {'description': {'$regex': regex_pattern}},
            {'product_tag_line': {'$regex': regex_pattern}},
            {'key_highlights': {'$elemMatch': {'$regex': regex_pattern}}},
            {'highlights': {'$elemMatch': {'$regex': regex_pattern}}},
        ]

    if category_id:
        try:
            filters['category_id'] = ObjectId(category_id)
        except Exception:
            filters['category_id'] = category_id

    if slug:
        filters['slug'] = slug

    if offer_only:
        filters['offer'] = {'$ne': None}

    price_filter = {}
    if min_price is not None:
        price_filter['$gte'] = float(min_price)
    if max_price is not None:
        price_filter['$lte'] = float(max_price)
    if price_filter:
        filters['price.amount'] = price_filter

    return filters


def _build_category_snapshot(category_doc):
    if not category_doc:
        return None
    return {
        'id': str(category_doc.get('_id')),
        'name': category_doc.get('name'),
        'slug': category_doc.get('slug'),
    }


def _normalize_highlights(values: Optional[Sequence[str]]):
    if not values:
        return []
    normalized = []
    for value in values:
        text = (value or '').strip()
        if text:
            normalized.append(text)
    return normalized


def _normalize_price(price):
    if not price:
        return {'amount': 0.0, 'currency': 'USD'}
    return {
        'amount': float(price.get('amount', 0.0)),
        'currency': (price.get('currency') or 'USD').upper(),
    }


def _normalize_offer(offer):
    if not offer:
        return None
    normalized = {
        'title': (offer.get('title') or '').strip(),
        'description': offer.get('description') or '',
        'discount_percentage': float(offer.get('discount_percentage', 0)),
    }
    if not normalized['title']:
        return None
    return normalized


def _resolve_category_doc(category_id):
    if not category_id:
        return None
    return category_utils.find_category_by_id(str(category_id))


def _stringify_object_id(value):
    if isinstance(value, ObjectId):
        return str(value)
    return value
