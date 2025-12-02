"""
Serializers for product CRUD APIs.
"""
from decimal import Decimal

from rest_framework import serializers

from categories import utils as category_utils
from products import utils as product_utils


class PriceSerializer(serializers.Serializer):
    """Serializer for product price object."""

    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField(max_length=3, default='USD')

    def validate_currency(self, value):
        value = (value or '').strip().upper()
        if not value:
            raise serializers.ValidationError('Currency is required.')
        if len(value) != 3:
            raise serializers.ValidationError('Currency must be a 3-letter ISO code.')
        return value

    def to_internal_value(self, data):
        internal = super().to_internal_value(data)
        amount = internal.get('amount')
        if isinstance(amount, Decimal):
            internal['amount'] = float(amount)
        return internal


class OfferSerializer(serializers.Serializer):
    """Optional offer details for a product."""

    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    discount_percentage = serializers.FloatField(required=False, min_value=0, max_value=100, default=0)


class ProductBaseSerializer(serializers.Serializer):
    """Shared fields and helpers for product serializers."""

    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    price = PriceSerializer(required=False)
    offer = OfferSerializer(required=False, allow_null=True)
    image = serializers.URLField(required=False)
    key_highlights = serializers.ListField(
        child=serializers.CharField(max_length=255), required=False, allow_empty=True
    )
    highlights = serializers.ListField(
        child=serializers.CharField(max_length=255), required=False, allow_empty=True
    )
    quantity = serializers.IntegerField(required=False, min_value=0)
    category_id = serializers.CharField(required=False)
    product_tag_line = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    slug = serializers.CharField(required=False, allow_blank=True)

    _category_doc = None

    def validate_name(self, value):
        normalized = product_utils.normalize_product_name(value)
        product_id = self.context.get('product_id')
        if product_utils.product_exists_by_name(normalized, exclude_id=product_id):
            raise serializers.ValidationError('Product with this name already exists.')
        return normalized

    def validate_slug(self, value):
        cleaned = (value or '').strip().lower()
        if not cleaned:
            return cleaned
        product_id = self.context.get('product_id')
        if product_utils.product_exists_by_slug(cleaned, exclude_id=product_id):
            raise serializers.ValidationError('Slug already in use.')
        return cleaned

    def validate_category_id(self, value):
        category_doc = category_utils.find_category_by_id(value)
        if not category_doc:
            raise serializers.ValidationError('Invalid category_id provided.')
        self._category_doc = category_doc
        return str(category_doc.get('_id'))

    def get_category_doc(self):
        return getattr(self, '_category_doc', None)


class ProductCreateSerializer(ProductBaseSerializer):
    """Serializer for creating products."""

    name = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    price = PriceSerializer(required=True)
    offer = OfferSerializer(required=False, allow_null=True)
    image = serializers.URLField(required=True)
    key_highlights = serializers.ListField(
        child=serializers.CharField(max_length=255), required=False, allow_empty=True
    )
    highlights = serializers.ListField(
        child=serializers.CharField(max_length=255), required=False, allow_empty=True
    )
    quantity = serializers.IntegerField(required=True, min_value=0)
    category_id = serializers.CharField(required=True)
    product_tag_line = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class ProductUpdateSerializer(ProductBaseSerializer):
    """Serializer for updating products."""

    pass


class ProductResponseSerializer(serializers.Serializer):
    """Standard representation for product payloads."""

    id = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    slug = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True, allow_blank=True, allow_null=True)
    price = PriceSerializer(read_only=True)
    offer = OfferSerializer(read_only=True, allow_null=True)
    image = serializers.CharField(read_only=True)
    key_highlights = serializers.ListField(child=serializers.CharField(), read_only=True)
    highlights = serializers.ListField(child=serializers.CharField(), read_only=True)
    quantity = serializers.IntegerField(read_only=True)
    category = serializers.DictField(read_only=True)
    category_id = serializers.CharField(read_only=True)
    product_tag_line = serializers.CharField(read_only=True, allow_blank=True, allow_null=True)
    created_by = serializers.CharField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class ProductQuerySerializer(serializers.Serializer):
    """Query params for listing products."""

    search = serializers.CharField(required=False, allow_blank=True)
    category_id = serializers.CharField(required=False)
    slug = serializers.CharField(required=False, allow_blank=True)
    offer_only = serializers.BooleanField(required=False)
    min_price = serializers.DecimalField(required=False, max_digits=12, decimal_places=2)
    max_price = serializers.DecimalField(required=False, max_digits=12, decimal_places=2)
    page = serializers.IntegerField(min_value=1, required=False, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, required=False, default=20)

    def validate(self, attrs):
        min_price = attrs.get('min_price')
        max_price = attrs.get('max_price')
        if isinstance(min_price, Decimal):
            attrs['min_price'] = float(min_price)
        if isinstance(max_price, Decimal):
            attrs['max_price'] = float(max_price)
        if attrs.get('min_price') is not None and attrs.get('max_price') is not None:
            if attrs['min_price'] > attrs['max_price']:
                raise serializers.ValidationError('min_price cannot be greater than max_price.')
        return attrs
