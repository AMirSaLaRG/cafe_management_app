from csv import excel
from http.client import responses
from typing import Optional
from datetime import time
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from models.dbhandler import DBHandler
from cafe_manager import CafeManager
from models.cafe_managment_models import *




db_handler = DBHandler()
cafe_manager = CafeManager(db_handler)
# Create your views here.

def parse_date_string(date_str: str):
    """Convert string to datetime object"""
    if isinstance(date_str, datetime):
        return date_str

    if date_str is None:
        return None

    try:
        # Handle various date formats
        formats = ['%Y/%m/%d', '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y%m%d']

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        raise ValueError(f"Unsupported date format: {date_str}")
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid date format: {date_str}") from e


def parse_time_string(time_str: str):
    """Convert string to time object"""
    if isinstance(time_str, time):
        return time_str

    if time_str is None:
        return None

    try:
        # Handle various time formats
        if ':' in time_str:
            # Format: "HH:MM" or "HH:MM:SS"
            parts = time_str.split(':')
            if len(parts) == 2:
                return time(int(parts[0]), int(parts[1]))
            elif len(parts) == 3:
                return time(int(parts[0]), int(parts[1]), int(parts[2]))
        else:
            # Format: "8" (just hours) or "800" (HHMM)
            if len(time_str) <= 2:
                return time(int(time_str), 0)
            else:
                # Handle "800" as 8:00, "1630" as 16:30
                hours = int(time_str[:-2]) if len(time_str) > 2 else int(time_str)
                minutes = int(time_str[-2:]) if len(time_str) > 2 else 0
                return time(hours, minutes)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid time format: {time_str}") from e



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
        kwargs = clear_kwargs(
            data=request.data,
            float_fields={"value_added_tax", "price", "profit_margin"},
            datetime_fields={"sales_forecast_from_date", "sales_forecast_to_date"},
            int_fields={"forecast_number" "id"},
        )
        menu_item, estimation = cafe_manager.create_new_menu_item(
            **kwargs
        )
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
        if 'active' in params and params['active'] == "all":
            f = "all"

        data = cafe_manager.serialization_personal(f = f)
        if data:
            return Response({'success': True, 'personal': data}, status=200)

        else:
            return Response({'success': False, 'error': 'Could not get personal info'}, status=500)

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)

@api_view(['POST'])
def add_personal_info(request):
    data = request.data
    personal_info_kwargs = {}
    required_fields = {
        'f_name', 'l_name', 'n_code', 'email', 'phone',
        'address', 'position', 'monthly_hr', 'monthly_payment'
    }
    float_fields = {
        'monthly_hr', 'monthly_payment'
    }
    for key, value in data.items():
        if value == "" or value is None:
            value = None
        else:
            if key in float_fields:
                value = float(value)

        personal_info_kwargs[key] = value

    try:
        missing_fields = required_fields - set(personal_info_kwargs.keys())
        if missing_fields:
            return Response({'success': False, 'error': 'need more info for add new personal'}, status=400)

        new_personal = cafe_manager.add_new_personal(**personal_info_kwargs)
        if new_personal:
            return Response({'success': True})
        else:
            return Response({'success': False, 'error': 'Could not add new personal'}, status=500)
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)

@api_view(['POST'])
def edit_personal_info(request):
    data = request.data
    personal_info_kwargs = {}
    required_fields = {
        'personal_id'
    }
    float_fields = {
        'monthly_hr', 'monthly_payment'
    }

    for key, value in data.items():
        if value == "" or value is None:
            value = None
        else:
            if key in float_fields:
                value = float(value)

        personal_info_kwargs[key] = value

    try:
        missing_fields = required_fields - set(personal_info_kwargs.keys())
        if missing_fields:
            return Response({'success': False, 'error': 'need personal id'}, status=400)

        update = cafe_manager.edit_info_personal(**personal_info_kwargs)
        if update:
            return Response({'success': True})
        else:
            return Response({'success': False, 'error': 'Could not update personal info'}, status=500)
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)








@api_view(['GET'])
def get_shift_planning(request):
    try:
        data = cafe_manager.serialization_shifts_plan()
        if data:
            return Response(data['success': True, 'personal': data], status=200)
        else:
            return Response({'success': False, 'error': 'Could not get shift planning info'}, status=500)

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
def create_one_shift(request):
    data = request.data
    kwargs_the_shift = {}
    float_fields = {"lunch_payment", "service_payment", "extra_payment"}
    datetime_fields = {'date'}
    time_fields = {'from_hr', "to_hr"}
    try:
        for key, value in data.items():
            if value == "" or value is None:
                value = None

            else:
                if key in float_fields:
                    value = float(value)

                if key in datetime_fields:
                    value = parse_date_string(value)

                if key in time_fields:
                    value = parse_time_string(value)

            kwargs_the_shift[key] = value
        added = cafe_manager.create_the_shift(**kwargs_the_shift)
        if added:
            return Response({'success': True})
        else:
            return Response({'success': False, 'error': 'Could not add new shift'}, status=500)

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
def create_routine_shift(request):
    data = request.data
    kwargs_the_shift = {}
    float_fields = {"lunch_payment", "service_payment", "extra_payment"}
    int_fields = {'continue_days'}
    datetime_fields = {'from_date'}
    time_fields = {'from_hr_1', "to_hr_1",
                   'from_hr_2', "to_hr_2",
                   'from_hr_3', "to_hr_3",
                   'from_hr_4', "to_hr_4",
                   'from_hr_5', "to_hr_5",
                   'from_hr_6', "to_hr_6",}
    try:
        for key, value in data.items():
            if value == "" or value is None:
                value = None

            else:
                if key in float_fields:
                    value = float(value)
                if key in int_fields:
                    value = int(value)
                if key in datetime_fields:
                    value = parse_date_string(value)

                if key in time_fields:
                    value = parse_time_string(value)

            kwargs_the_shift[key] = value
        added = cafe_manager.create_routine_shifts(**kwargs_the_shift)
        if added:
            return Response({'success': True})
        else:
            return Response({'success': False, 'error': 'Could not add new shifts'}, status=500)

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['POST'])
def create_edit_target_salary(request):
    data = request.data
    kwargs_the_target = {}
    float_fields = {"monthly_hr", "monthly_payment", "monthly_insurance", "extra_hr_payment"}
    datetime_fields = {'from_date', "to_date"}
    int_fields = {'id'}


    try:
        for key, value in data.items():
            if value == "" or value is None:
                value = None

            else:
                if key in float_fields:
                    value = float(value)
                if key in datetime_fields:
                    value = parse_date_string(value)

            kwargs_the_target[key] = value
        added = cafe_manager.add_edit_target_salary(**kwargs_the_target)
        if added:
            return Response({'success': True})
        else:
            return Response({'success': False, 'error': 'Could not add new target salary'}, status=500)

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(['GET'])
def get_target_salary(request):
    try:
        data = cafe_manager.get_target_salary()
        if data:
            return Response({'success': True, 'target_salary_info': data}, status=200)
        else:
            return Response({'success': False, 'error': 'Could not get target salary info'}, status=500)

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


#add edit get bills
@api_view(["POST"])
def add_edit_bill(request):
    try:
        the_kwargs = clear_kwargs(request.data,
                                  float_fields={"cost"},
                                  datetime_fields={'from_date', "to_date"},
                                  int_fields={'id'})
        added = cafe_manager.add_edit_bill(**the_kwargs)
        if added:
            return Response({'success': True})
        else:
            return Response({'success': False, 'error': 'Could not add new bill'}, status=500)

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)

@api_view(["GET"])
def get_bills(request):
    try:
        data = cafe_manager.get_bills()
        if data:
            return Response({'success': True, 'bills': data}, status=200)
        else:
            return Response({'success': False, 'error': 'Could not get bills info'}, status=500)

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)
#add edit get estimated bills update indirect cost
@api_view(["POST"])
def add_edit_estimated_bill(request):
    try:
        the_kwargs = clear_kwargs(request.data,
                                  float_fields={"cost"},
                                  datetime_fields={'from_date', "to_date"},
                                  int_fields={'id'})
        added = cafe_manager.add_edit_estimated_bill(**the_kwargs)
        if added:
            return Response({'success': True})
        else:
            return Response({'success': False, 'error': 'Could not add new estimated bill'}, status=500)

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)

@api_view(["GET"])
def get_estimated_bills(request):
    try:
        data = cafe_manager.get_estimated_bills()
        if data:
            return Response({'success': True, 'estimate_bills': data}, status=200)
        else:
            return Response({'success': False, 'error': 'Could not get bills info'}, status=500)

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)

#add edit get rent update indirect cost
@api_view(["POST"])
def add_edit_rent(request):
    try:
        the_kwargs = clear_kwargs(request.data,
                                  float_fields={"rent", "mortgage", "mortgage_percentage_to_rent"},
                                  datetime_fields={'from_date', "to_date"},
                                  int_fields={'id'})
        added = cafe_manager.add_edit_rent(**the_kwargs)
        if added:
            return Response({'success': True})
        else:
            return Response({'success': False, 'error': 'Could not add new rent'}, status=500)

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(["GET"])
def fetch_rent(request):
    try:
        data = cafe_manager.get_the_rent()
        if data:
            return Response({'success': True, 'rent_info': data}, status=200)
        else:
            return Response({'success': False, 'error': 'Could not get rent info'}, status=500)

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


#add edit get equipment update indirect cost
@api_view(["POST"])
def add_edit_equipment(request):
    try:
        the_kwargs = clear_kwargs(request.data,
                                  float_fields={"purchase_price", "monthly_depreciation"},
                                  datetime_fields={'purchase_date', "expire_date"},
                                  int_fields={'id', "number"},
                                  bool_fields={"in_use"})
        added = cafe_manager.add_edit_equipment(**the_kwargs)
        if added:
            return Response({'success': True})
        else:
            return Response({'success': False, 'error': 'Could not add new rent'}, status=500)

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


@api_view(["GET"])
def fetch_equipment(request):
    try:
        data = cafe_manager.get_the_equipments()
        if data:
            return Response({'success': True, 'bills': data}, status=200)
        else:
            return Response({'success': False, 'error': 'Could not get rent info'}, status=500)

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


#process sell deduct inventory creat invoic get invoice payments
@api_view(["POST"])
def add_new_sale(request):
    try:
        kwargs = clear_kwargs(
            data = request.data,
            float_fields={"price", "discount"},
            datetime_fields={"date"},
            int_fields={ "quantity", "menu_id", "invoice_id"},
            )
        added = cafe_manager.add_new_sale(**kwargs)
        if added:
            return Response({'success': True})
        else:
            return Response({'success': False, 'error': 'Could not add new sale'}, status=500)

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)
@api_view(["POST"])
def add_invoice_payment(request):
    try:
        kwargs = clear_kwargs(
            data = request.data,
            float_fields={"paid", "tip"},
            datetime_fields={"date"},
            int_fields={"invoice_id"},
            bool_fields={"remain_as_tip"}
            )
        added = cafe_manager.add_new_invoice_pay(**kwargs)
        if added:
            return Response({'success': True})
        else:
            return Response({'success': False, 'error': 'Could not add new payment'}, status=500)

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)
@api_view(["GET"])
def get_invoices_info(request):
    try:
        data = cafe_manager.get_the_invoices_info()
        if data:
            return Response({'success': True, 'invoices_info': data}, status=200)
        else:
            return Response({'success': False, 'error': 'Could not get invoice info'}, status=500)

    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=500)


#process usage deduct inventory















def clear_kwargs(data,
                 float_fields: Optional[set[str]] = None,
                 datetime_fields: Optional[set[str]] = None,
                 int_fields: Optional[set[str]] = None,
                 bool_fields: Optional[set[str]] = None):
    kwargs_the_target = {}
    for key, value in data.items():
        if value == "" or value is None:
            value = None

        else:
            if int_fields is not None and key in int_fields:
                value = int(value)
            if float_fields is not None and key in float_fields:
                value = float(value)
            if datetime_fields is not None and key in datetime_fields:
                value = parse_date_string(value)
            if bool_fields is not None and key in bool_fields:
                if value in {"1", "True", "true"}:
                    value = True
                elif value in {"0", "False", "false"}:
                    value = False





        kwargs_the_target[key] = value
    return kwargs_the_target