"""
Product API views referencing categories.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from products import utils
from products.serializers import (
    ProductCreateSerializer,
    ProductQuerySerializer,
    ProductResponseSerializer,
    ProductUpdateSerializer,
)
from users.permissions import IsEmailVerified


def _error_response(detail, data=None, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR):
    """Unified error payload."""
    payload = {
        'status': 'ERROR',
        'detail': detail,
        'data': data,
    }
    return Response(payload, status=status_code)


def _require_admin_user(request):
    """Restrict write actions to verified admin users."""
    user = getattr(request, 'user', None)
    if not user or not getattr(user, 'email_verified', False):
        return False
    return getattr(user, 'user_type', '').lower() == 'admin'


@api_view(['GET'])
@permission_classes([AllowAny])
def list_products(request):
    """List products with pagination and filters."""
    serializer = ProductQuerySerializer(data=request.GET)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    query_params = serializer.validated_data
    filters = utils.build_search_filter(
        search=query_params.get('search'),
        category_id=query_params.get('category_id'),
        slug=query_params.get('slug'),
        offer_only=query_params.get('offer_only'),
        min_price=query_params.get('min_price'),
        max_price=query_params.get('max_price'),
    )
    page = query_params.get('page', 1)
    page_size = query_params.get('page_size', 20)

    try:
        collection = utils.get_products_collection()
        total = collection.count_documents(filters or {})
        skip = (page - 1) * page_size
        cursor = (
            collection.find(filters or {})
            .sort('created_at', -1)
            .skip(skip)
            .limit(page_size)
        )
        results = [utils.product_to_dict(doc) for doc in cursor]
    except Exception as exc:
        return _error_response(
            detail='Failed to fetch products',
            data=str(exc),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    payload = {
        'status': 'SUCCESS',
        'results': results,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total': total,
            'pages': (total + page_size - 1) // page_size if page_size else 1,
        },
    }
    return Response(payload, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsEmailVerified])
def create_product(request):
    """Create a new product linked to a category."""
    if not _require_admin_user(request):
        return _error_response(
            detail='Admin privileges are required to manage products.',
            status_code=status.HTTP_403_FORBIDDEN,
        )

    serializer = ProductCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    category_doc = serializer.get_category_doc()
    try:
        document = utils.build_product_document(
            data=serializer.validated_data,
            user_id=getattr(request.user, 'user_id', None),
            category_doc=category_doc,
        )
        collection = utils.get_products_collection()
        result = collection.insert_one(document)
        document['_id'] = result.inserted_id
    except Exception as exc:
        return _error_response(
            detail='Failed to create product',
            data=str(exc),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    response_data = ProductResponseSerializer(utils.product_to_dict(document)).data
    return Response(
        {'product': response_data, 'message': 'Product created successfully.', 'status': 'SUCCESS'},
        status=status.HTTP_201_CREATED,
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_product(request):
    """Fetch a single product by ID."""
    product_id = request.GET.get('product_id')
    if not product_id:
        return _error_response(
            detail='Failed to fetch parameters',
            data={'missing': 'product_id'},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        product_doc = utils.find_product_by_id(product_id)
    except Exception as exc:
        return _error_response(
            detail='Failed to fetch product',
            data=str(exc),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if not product_doc:
        return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

    response_data = ProductResponseSerializer(utils.product_to_dict(product_doc)).data
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsEmailVerified])
def update_product(request):
    """Update product details by ID."""
    if not _require_admin_user(request):
        return _error_response(
            detail='Admin privileges are required to manage products.',
            status_code=status.HTTP_403_FORBIDDEN,
        )

    product_id = request.GET.get('product_id')
    if not product_id:
        return _error_response(
            detail='Failed to fetch parameters',
            data={'missing': 'product_id'},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    existing_doc = utils.find_product_by_id(product_id)
    if not existing_doc:
        return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = ProductUpdateSerializer(
        data=request.data,
        partial=True,
        context={'product_id': product_id},
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    category_doc = serializer.get_category_doc()
    update_payload = utils.update_product_document(existing_doc, serializer.validated_data, category_doc)
    if not update_payload:
        response_data = ProductResponseSerializer(utils.product_to_dict(existing_doc)).data
        return Response(
            {'product': response_data, 'message': 'No changes detected.', 'status': 'SUCCESS'},
            status=status.HTTP_200_OK,
        )

    try:
        collection = utils.get_products_collection()
        collection.update_one({'_id': existing_doc['_id']}, {'$set': update_payload})
        updated_doc = utils.find_product_by_id(product_id)
    except Exception as exc:
        return _error_response(
            detail='Failed to update product',
            data=str(exc),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    response_data = ProductResponseSerializer(utils.product_to_dict(updated_doc)).data
    return Response(
        {'product': response_data, 'message': 'Product updated successfully.', 'status': 'SUCCESS'},
        status=status.HTTP_200_OK,
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsEmailVerified])
def delete_product(request):
    """Delete a product by ID."""
    if not _require_admin_user(request):
        return _error_response(
            detail='Admin privileges are required to manage products.',
            status_code=status.HTTP_403_FORBIDDEN,
        )

    product_id = request.GET.get('product_id')
    if not product_id:
        return _error_response(
            detail='Failed to fetch parameters',
            data={'missing': 'product_id'},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    product_doc = utils.find_product_by_id(product_id)
    if not product_doc:
        return Response({'error': 'Product not found.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        collection = utils.get_products_collection()
        collection.delete_one({'_id': product_doc['_id']})
    except Exception as exc:
        return _error_response(
            detail='Failed to delete product',
            data=str(exc),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response(
        {'message': 'Product deleted successfully.', 'status': 'SUCCESS'},
        status=status.HTTP_200_OK,
    )


