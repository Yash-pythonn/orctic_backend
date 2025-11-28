"""
Category API views implemented similar to users API patterns.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from categories.serializers import (
    CategoryCreateSerializer,
    CategoryQuerySerializer,
    CategoryResponseSerializer,
    CategoryUpdateSerializer,
)
from categories import utils
from users.permissions import IsEmailVerified


def _error_response(detail, data=None, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR):
    """Unified error payload."""
    payload = {
        'status': "ERROR",
        'detail': detail,
        'data': data,
    }
    return Response(payload, status=status_code)


def _require_admin_user(request):
    """Simple helper to restrict write actions to admin users."""
    user = getattr(request, 'user', None)
    if not user or not getattr(user, 'email_verified', False):
        return False
    return getattr(user, 'user_type', '').lower() == 'admin'


@api_view(['GET'])
@permission_classes([AllowAny])
def list_categories(request):
    """List categories with pagination and search filters."""

    search = request.GET.get("search")
    is_active = request.GET.get('is_active',True)
    category_for = request.GET.get('category_for','')
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
  
    filters = utils.build_search_filter(
        search=search,
        is_active=is_active,
        category_for=category_for,
    )
    try:
        collection = utils.get_categories_collection()
        total = collection.count_documents(filters or {})
        skip = (page - 1) * page_size

        cursor = (
            collection.find(filters or {})
            .sort('created_at', -1)
            .skip(skip)
            .limit(page_size)
        )
        results = [utils.category_to_dict(doc) for doc in cursor]
    except Exception as exc:
        return _error_response(
            detail='Failed to fetch categories',
            data=str(exc),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    response_payload = {
        "status":"SUCCESS",
        'results': results,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total': total,
            'pages': (total + page_size - 1) // page_size if page_size else 1,
        }
    }
    
    return Response(response_payload, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsEmailVerified])
def create_category(request):
    """Create a new category; restricted to admin users."""
    if not _require_admin_user(request):
        return _error_response(
                detail='Admin privileges are required to manage categories.',
                status_code=status.HTTP_403_FORBIDDEN
            )
    
    serializer = CategoryCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        document = utils.build_category_document(
            data=serializer.validated_data,
            user_id=getattr(request.user, 'user_id', None)
        )
        collection = utils.get_categories_collection()
        result = collection.insert_one(document)
        document['_id'] = result.inserted_id
    except Exception as exc:
        return _error_response(
            detail='Failed to create category',
            data=str(exc),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    response_data = CategoryResponseSerializer(utils.category_to_dict(document)).data
    return Response(
        {'category': response_data, 'message': 'Category created successfully.','status': "SUCCESS"},
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_category(request):
    """Retrieve single category by ID (path param `category_id`)."""
    category_id = request.GET.get("category_id")
    if not category_id:
        return _error_response(
            detail='Failed to fetch parameters',
            data={'missing': 'category_id'},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        category_doc = utils.find_category_by_id(category_id)
    except Exception as exc:
        return _error_response(
            detail='Failed to fetch category',
            data={'error': str(exc)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    if not category_doc:
        return Response({'error': 'Category not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    response_data = CategoryResponseSerializer(utils.category_to_dict(category_doc)).data
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsEmailVerified])
def update_category(request):
    """Update category fields addressed by path param `category_id`."""
    if not _require_admin_user(request):
        return Response(
            {'error': 'Admin privileges are required to manage categories.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    category_id = request.GET.get("category_id")
    if not category_id:
        return _error_response(
            detail='Failed to fetch parameters',
            data={'missing': 'category_id'},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    existing_doc = utils.find_category_by_id(category_id)
    if not existing_doc:
        return Response({'error': 'Category not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = CategoryUpdateSerializer(
        data=request.data,
        partial=True,
        context={'category_id': category_id}
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    update_payload = utils.update_category_document(existing_doc, serializer.validated_data)
    if not update_payload:
        response_data = CategoryResponseSerializer(utils.category_to_dict(existing_doc)).data
        return Response(
            {'category': response_data, 'message': 'No changes detected.'},
            status=status.HTTP_200_OK
        )
    
    try:
        collection = utils.get_categories_collection()
        collection.update_one({'_id': existing_doc['_id']}, {'$set': update_payload})
        updated_doc = utils.find_category_by_id(category_id)
    except Exception as exc:
        return _error_response(
            detail='Failed to update category',
            data={'error': str(exc)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    response_data = CategoryResponseSerializer(utils.category_to_dict(updated_doc)).data
    return Response(
        {'category': response_data, 'message': 'Category updated successfully.'},
        status=status.HTTP_200_OK
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsEmailVerified])
def delete_category(request):
    """Delete a category document referenced by path param `category_id`."""
    if not _require_admin_user(request):
        return Response(
            {'error': 'Admin privileges are required to manage categories.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    category_id = request.GET.get("category_id")
    if not category_id:
        return _error_response(
            detail='Failed to fetch parameters',
            data={'missing': 'category_id'},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    category_doc = utils.find_category_by_id(category_id)
    if not category_doc:
        return Response({'error': 'Category not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    try:
        collection = utils.get_categories_collection()
        collection.delete_one({'_id': category_doc['_id']})
    except Exception as exc:
        return _error_response(
            detail='Failed to delete category',
            data={'error': str(exc)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return Response(
        {'message': 'Category deleted successfully.'},
        status=status.HTTP_200_OK
    )


