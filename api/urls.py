from django.urls import path
from . import views


urlpatterns = [
    path('menu/', views.menu_items, name='menu-items'),
    path('menu/crete/', views.create_menu_item, name='crete-menu-item'),
    path('menu/edit/', views.edit_menu_item, name='edit_menu_item'),
]

