from http.client import responses
from typing import Optional

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from models.dbhandler import DBHandler
from cafe_manager import CafeManager
from models.cafe_managment_models import *




db_handler = DBHandler()
cafe_manager = CafeManager(db_handler)
# Create your views here.



@api_view(['GET'])
def menu_items(request):
    try:
        items = cafe_manager.get_menu_with_availability()
        return Response({'success': True, 'items': items})
    except Exception as e:
        return Response({'success': False, 'error': str(e), status: 500})

@api_view(['POST'])
def create_menu_item(request):
    #todo check recipe items
    try:
        data = request.data
        print(data)
        menu_item, estimation = cafe_manager.create_new_menu_item(
            user_name=data['user_name'],
            name=data['name'],
            size=data['size'],
            category=data['category'],
            value_added_tax= float(data['value_added_tax']) if data['value_added_tax'] !="" else None,
            recipe_items= data['recipe_items'],
            price=float(data['price']) if data['price']!="" else None,
            profit_margin=float(data['profit_margin']),
            description=data['description'],
            forecast_number = int(data['forecast_number']) if data["forecast_number"]!= "" else None,
            sales_forecast_from_date= data['sales_forecast_from_date'],
            sales_forecast_to_date = data['sales_forecast_to_date'],
        )
        print(estimation)
        if menu_item:
            if not estimation.estimated_price:
                price_report = "Not enough data"
            else:
                price_report = estimation.estimated_price
        else:
            price_report = "This Item Already Exist in Menu"

        return Response({'success': bool(menu_item), "estimated_price":price_report})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
def edit_menu_item(request):
    menu_updatables_list = ['name', 'size', 'category', 'value_added_tax', 'description', 'serving', 'price',
                            'profit_margin', 'price_change_category']
    float_list = ["price", "value_added_tax", "profit_margin"]
    menu_change_kwargs = {}
    try:
        data = request.data
        if 'menu_id' not in data:
            return Response({'success': False, 'error': 'menu_id is required'}, status=400)
        for key, value in data.items():
            if key in menu_updatables_list:
                if value == "" or value is None:
                    menu_change_kwargs[key] = None
                else:
                    if key in float_list:
                        try:
                            menu_change_kwargs[key] = float(value)
                        except (ValueError, TypeError):
                            return Response({'success': False, 'error': f'Invalid {key} value'}, status=400)
                    elif key == 'serving':
                        if value in ('1', 1, True, 'true'):
                            menu_change_kwargs[key] = True
                        elif value in ('0', 0, False, 'false'):
                            menu_change_kwargs[key] = False
                        else:
                            menu_change_kwargs[key] = None
                    else:
                        menu_change_kwargs[key] = value

        if not menu_change_kwargs:
            return Response({'success': False, 'error': 'No valid fields provided'}, status=400)

        applied_changes = cafe_manager.update_menu_item(menu_id=int(data['menu_id']), **menu_change_kwargs)
        return Response({'success': applied_changes})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
def inventory_items(request):
    try:
        items = cafe_manager.get_and_format_inventory()
        print(items)
        return Response({'success': True, 'items': items})
    except Exception as e:
        return Response({'success': False, 'error': str(e), status: 500})


@api_view(['POST'])
def create_inventory_item(request):
    data = request.data
    inventory_kwargs = {}
    # required_fields = ["item_name", "unit", "category", "person_who_added"]
    float_fields = ['current_stock', 'price_per_unit', 'safety_stock', 'daily_usage']
    int_fields = ['current_supplier_id']
    try:
        for key, value in data.items():
            if value == "" or value is None:
                value = None
            else:
                if key in float_fields:
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        return Response({'success': False, 'error': f'Invalid {key} value'}, status=400)
                if key in int_fields:
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        return Response({'success': False, 'error': f'Invalid {key} value'}, status=400)

            inventory_kwargs[key] = value

        try:
            added_item = cafe_manager.inventory.create_new_inventory_item(**inventory_kwargs)

            return Response({'success': added_item})

        except TypeError as e:
            return Response({'success': False, 'error': str(e)}, status=400)

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)

@api_view(['POST'])
def edit_inventory_item(request):
    float_fields = ['current_stock', 'price_per_unit', 'safety_stock', 'daily_usage']
    int_fields = ['current_supplier_id']
    not_available_fields = []
    inventory_change_kwargs = {}
    try:
        data = request.data
        if 'id' not in data:
            return Response({'success': False, 'error': 'menu_id is required'}, status=400)
        if 'user_name' not in data:
            return Response({'success': False, 'error': 'user_name is required'}, status=400)

        for key, value in data.items():
            if value == "" or value is None or value in not_available_fields:
                value = None
            else:
                if key in float_fields:
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        return Response({'success': False, 'error': f'Invalid {key} value'}, status=400)
                elif key in int_fields:
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        return Response({'success': False, 'error': f'Invalid {key} value'}, status=400)

            inventory_change_kwargs[key] = value

        if not inventory_change_kwargs:
            return Response({'success': False, 'error': 'No valid fields provided'}, status=400)

        applied_changes = cafe_manager.inventory.update_inventory_item(**inventory_change_kwargs)
        return Response({'success': applied_changes})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)
