from http.client import responses

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from models.dbhandler import DBHandler
from cafe_manager import CafeManager




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
    try:
        data = request.data
        success = cafe_manager.menu.add_menu_item(
            name=data['name'],
            size=data['size'],
            category=data['category'],
            value_added_tax=data['value_added_tax'],
            description=data.get('description', None),

        )
        return Response({'success': success})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)