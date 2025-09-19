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
        print(f"DEBUG: Retrieved {len(items)} items")  # Add this
        print(f"DEBUG: First item: {items[0] if items else 'None'}")  # Add this
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
            value_added_tax= float(data['value_added_tax']),
            recipe_items= data['recipe_items'],
            price=float(data['price']),
            profit_margin=float(data['profit_margin']),
            description=data['description'],
            forecast_number = data['forecast_number'],
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
    menu_updatables_list = ['name', 'size', 'category', 'value_added_tax', 'description']
    try:
        data = request.data
        target_menu: Optional[Menu] = cafe_manager.menu.get_menu_item(data['id'])
        for key, value in data.items():
            #edit menu model
            menu_change_kwargs = {}
            if key in menu_updatables_list:
                if value is None:
                    menu_change_kwargs[key] = None
                elif value:
                    menu_change_kwargs[key] = value

                cafe_manager.menu.change_attribute_menu_item(target_menu.id, **menu_change_kwargs)
            #manage active
            if key == "serving":
                cafe_manager.menu.change_availability_of_menu_item(target_menu.id, switch_to=value)

            if key == "price":
                cafe_manager.menu_pricing.calculate_manual_price_change(target_menu.id, value)


        menu_item, estimation = cafe_manager.create_new_menu_item(
            user_name=data['user_name'],
            name=data['name'],
            size=data['size'],
            category=data['category'],
            value_added_tax= float(data['value_added_tax']),
            recipe_items= data['recipe_items'],
            price=float(data['price']),
            profit_margin=float(data['profit_margin']),
            description=data['description'],
            forecast_number = data['forecast_number'],
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


