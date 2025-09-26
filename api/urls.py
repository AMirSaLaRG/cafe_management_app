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
    path('suppliers/', views.get_suppliers, name='get-suppliers-info'),
    path('suppliers/create/', views.add_new_supplier, name='add-suppliers-new'),
    path('suppliers/edit/', views.editing_the_supplier, name='edit-suppliers-info'),
    path('order/', views.get_order_details, name='get-order-detailed'),
    path('order/add', views.add_order_detailed, name='add-order-detailed'),
    path('order/shipped', views.update_shipment_info, name='update-order-shipment'),
    path('order/approve', views.checked_shipment_info, name='approve-received-shipment'),

]

