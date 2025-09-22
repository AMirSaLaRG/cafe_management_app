from django.urls import path
from . import views


urlpatterns = [
    path('menu/', views.menu_items, name='menu-items'),
    path('menu/create/', views.create_menu_item, name='crete-menu-item'),
    path('menu/edit/', views.edit_menu_item, name='edit-menu-item'),
    path('inventory/', views.inventory_items, name='inventory-items'),
    path('inventory/create/', views.create_inventory_item, name='crete-inventory-item'),
    path('inventory/edit/', views.edit_inventory_item, name='edit-inventory-item'),
    path('recipe/add/', views.add_new_recipe, name='add-recipe-record'),
    path('recipe/edit/', views.update_remove_recipe, name='update-remove-recipe'),

]

