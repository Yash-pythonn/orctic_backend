"""
URL routing for product APIs.
"""
from django.urls import path

from products import views


app_name = 'products'


urlpatterns = [
    path('', views.list_products, name='list-products'),
    path('create/', views.create_product, name='create-product'),
    path('get/', views.get_product, name='get-product'),
    path('update/', views.update_product, name='update-product'),
    path('delete/', views.delete_product, name='delete-product'),
]

