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
        return Response({'success': False, 'error': str(e)}, status=500)


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
        return Response({'success': False, 'error': str(e)}, status=500)


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

@api_view(['POST'])
def add_new_recipe(request):
    try:
        data = request.data
        add_recipe_kwargs = {}
        int_field = ["inventory_id", "menu_id"]
        float_field = ['amount']
        if "inventory_id" not in data or "menu_id" not in data:
            return Response({'success': False, 'error': 'menu_id and inventory_id are required'}, status=400)

        for key, value in data.items():
            if value == "" or value is None:
                value = None
            else:
                if key in float_field:
                    value = float(value)
                if key in int_field:
                    value = int(value)

            add_recipe_kwargs[key] = value
        print(add_recipe_kwargs)
        added_recipe = cafe_manager.create_new_recipe(**add_recipe_kwargs)
        return Response({'success': added_recipe})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
def update_remove_recipe(request):
    try:
        data = request.data
        float_fields = ['amount']
        update_kwargs = {}

        if 'menu_id' not in data or "inventory_id" not in data:
            return Response({'success': False, 'error': 'menu_id and inventory_id are required'}, status=400)

        for key, value in data.items():
            if value == "" or value is None:
                value = None
            else:
                if key in float_fields:
                    value = float(value)
                if key == "delete":
                    if value in (True, 'true', 1, "1"):
                        value = True
                    else:
                        value = False

            update_kwargs[key] = value

        approve_change = cafe_manager.update_remove_recipe(**update_kwargs)
        return Response({'success': approve_change})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['get'])
def get_suppliers(request):
    try:
        suppliers = cafe_manager.serialization_suppliers()
        print(suppliers)
        print(request.query_params)
        if suppliers:
            return Response({'success': True, 'suppliers': suppliers})
        else:
            return Response({'success': False, "error":'No suppliers'}, status=500)
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)

@api_view(['POST'])
def add_new_supplier(request):
    try:
        data = request.data
        add_supplier_kwargs = {}

        int_field = ['load_time_hr']
        for key, value in data.items():
            if value == "" or value is None:
                value = None
            else:
                if key in int_field:
                    value = int(value)

            add_supplier_kwargs[key] = value

        added = cafe_manager.inventory.db.add_supplier(**add_supplier_kwargs)
        if added:
            return Response({'success': True})
        else:
            return Response({'success': False, 'error': 'Could not add supplier'}, status=500)

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)

@api_view(['POST'])
def editing_the_supplier(request):
    try:
        data = request.data
        edit_supplier_kwargs = {}

        int_field = ['load_time_hr', "id"]
        for key, value in data.items():
            if value == "" or value is None:
                value = None
            else:
                if key in int_field:
                    value = int(value)

            edit_supplier_kwargs[key] = value

        added = cafe_manager.supplier_editor(**edit_supplier_kwargs)
        print(bool(added))
        if added:
            return Response({'success': True})
        else:
            return Response({'success': False, 'error': 'Could not edit supplier'}, status=500)

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)

@api_view(['GET'])
def get_order_details(request):
    try:
        require_status=None
        params = request.query_params
        if 'status' in params:
            require_status = params["status"] if params["status"] else None
        order_details = cafe_manager.get_serialization_ordes_in_detail(open_clos=require_status)
        if order_details:
            return Response({'success': True, 'orders': order_details})
        else:
            return Response({'success': False, 'error': 'Could not get orders'}, status=500)
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
def add_order_detailed(request):
    data = request.data
    add_order_detail_kwargs = {}
    int_fields = ['supplier_id', 'order_id', "supplier_id"]
    float_fields = ['box_amount', 'box_price', 'overall_discount', 'num_box_ordered', 'shipper_price']
    try:
        for key, value in data.items():
            if value == "" or value is None:
                value = None
            else:
                if key in int_fields:
                    value = int(value)
                if key in float_fields:
                    value = float(value)

            add_order_detail_kwargs[key] = value
        approved = cafe_manager.add_new_order_info(**add_order_detail_kwargs)
        if approved:
            return Response({'success': True})
        else:
            return Response({'success': False, 'error': 'Could not add order'}, status=500)
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)

@api_view(['POST'])
def update_shipment_info(request):
    data = request.data
    update_shipment_info_kwargs = {}
    int_fields = ['shipper_id', 'number_shipped', "number_received"]
    float_fields = ['price']
    try:
        for key, value in data.items():
            if value == "" or value is None:
                value = None
            else:
                if key in int_fields:
                    value = int(value)
                if key in float_fields:
                    value = float(value)
            update_shipment_info_kwargs[key] = value

        updated = cafe_manager.update_shipper_info(**update_shipment_info_kwargs)
        if updated:
            return Response({'success': True})
        else:
            return Response({'success': False, 'error': 'Could not update shipment info'}, status=500)


    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)

@api_view(['POST'])
def checked_shipment_info(request):
    data = request.data
    checked_shipment_info_kwargs = {}
    int_fields = ['approved', 'rejected', "replace_reject"]
    try:
        for key, value in data.items():
            if value == "" or value is None:
                value = None
            else:
                if key in int_fields:
                    value = int(value)

            checked_shipment_info_kwargs[key] = value


        updated = cafe_manager.checked_received_items(**checked_shipment_info_kwargs)
        if updated:
            return Response({'success': True})
        else:
            return Response({'success': False, 'error': 'Could not check shipment info'}, status=500)
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


#______________hr_______________________

@api_view(['GET'])
def get_personal_info(request):
    try:
        f = None
        params = request.query_params
        if params == "all":
            f = "all"

        cafe_manager.serialization_personal(f = f,)

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)