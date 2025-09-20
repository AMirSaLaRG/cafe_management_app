from django.urls import path
from . import views


urlpatterns = [
    path('menu/', views.menu_items, name='menu-items'),
    path('menu/create/', views.create_menu_item, name='crete-menu-item'),
    path('menu/edit/', views.edit_menu_item, name='edit-menu-item'),
    path('inventory/', views.inventory_items, name='inventory-items'),
    path('inventory/create/', views.create_inventory_item, name='crete-inventory-item'),

]

