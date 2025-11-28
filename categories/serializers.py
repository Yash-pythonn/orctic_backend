"""
Serializers for category CRUD APIs.
"""
from rest_framework import serializers

from categories import utils


class CategoryResponseSerializer(serializers.Serializer):
    """Standard category representation."""
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=255, read_only=True)
    slug = serializers.CharField(read_only=True)
    description = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    is_active = serializers.BooleanField(read_only=True)
    category_for = serializers.ChoiceField(
        choices=tuple((value, value.title()) for value in utils.CATEGORY_FOR_CHOICES),
        read_only=True
    )
    created_by = serializers.CharField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class CategoryCreateSerializer(serializers.Serializer):
    """Payload serializer for creating categories."""
    name = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_active = serializers.BooleanField(required=False, default=True)
    category_for = serializers.ChoiceField(
        choices=tuple((value, value.title()) for value in utils.CATEGORY_FOR_CHOICES),
        required=False,
        default='other'
    )
    
    def validate_name(self, value):
        normalized = utils.normalize_category_name(value)
        if utils.category_exists_by_name(normalized):
            raise serializers.ValidationError("Category with this name already exists.")
        return normalized


class CategoryUpdateSerializer(serializers.Serializer):
    """Payload serializer for updating categories."""
    name = serializers.CharField(max_length=255, required=False)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_active = serializers.BooleanField(required=False)
    category_for = serializers.ChoiceField(
        choices=tuple((value, value.title()) for value in utils.CATEGORY_FOR_CHOICES),
        required=False
    )
    
    def validate_name(self, value):
        normalized = utils.normalize_category_name(value)
        category_id = self.context.get('category_id')
        if utils.category_exists_by_name(normalized, exclude_id=category_id):
            raise serializers.ValidationError("Category with this name already exists.")
        return normalized


class CategoryQuerySerializer(serializers.Serializer):
    """Query params for listing categories."""
    search = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
    category_for = serializers.ChoiceField(
        choices=tuple((value, value.title()) for value in utils.CATEGORY_FOR_CHOICES),
        required=False
    )
    page = serializers.IntegerField(min_value=1, required=False, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, required=False, default=20)


