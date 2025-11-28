"""
URL routing for category APIs.
"""
from django.urls import path

from categories import views


app_name = 'categories'

urlpatterns = [
    path('', views.list_categories, name='list-categories'),
    path('create/', views.create_category, name='create-category'),
    path('get/', views.get_category, name='get-category'),
    path('update/', views.update_category, name='update-category'),
    path('delete/', views.delete_category, name='delete-category'),
]


