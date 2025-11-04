# cafe_manager.py
from turtledemo.paint import switchupdown

# Import all the service classes you have created
from models.dbhandler import DBHandler
from services.bills_rent_service import BillsRent
from services.equipment_service import EquipmentService
from services.hr_service import HRService
from services.inventory_service import InventoryService
from services.menu_pricing_service import MenuPriceService
from services.menu_service import MenuService
from services.sales_service import SalesService
from services.supplier_service import SupplierService
from services.usage_record_service import OtherUsageService
from typing import Optional,Union

from datetime import datetime

from models.cafe_managment_models import *

class CafeManager:
    """
    The Facade or Orchestrator for the cafe management system.
    It provides a single, high-level interface to all the underlying services.
    """

    def __init__(self, db_handler: DBHandler):
        """Initializes all services with a single DBHandler instance."""
        self.db = db_handler

        # Instantiate each service and pass the shared DBHandler
        self.bills_rent = BillsRent(db_handler=self.db)
        self.equipment = EquipmentService(db_handler=self.db)
        self.hr = HRService(db_handler=self.db)
        self.inventory = InventoryService(db_handler=self.db)
        self.menu_pricing = MenuPriceService(db_handler=self.db)
        self.menu = MenuService(dbhandler=self.db)
        self.sales = SalesService(db_handler=self.db)
        self.supplier = SupplierService(db_handler=self.db)
        self.usage = OtherUsageService(db_handler=self.db)

    # --- Example Methods that Delegate to Services ---
    def get_menu_with_availability(self):
        """
        Calculates and returns a list of available menu items
        and the maximum number of each that can be produced. with details menu needs
        """
        # This method uses both MenuService and InventoryService
        available_items = []
        serving_menu = self.menu.get_menu_all_available_items()

        for item in serving_menu:
            available, missing_items, number_available = self.inventory.check_stock_for_menu(item)
            columns = item.__table__.columns.keys()
            clean_data = {column: getattr(item, column) for column in columns}
            clean_data['number_available'] = number_available
            if item.recipe:
                clean_data['recipes'] = [
                    {
                        'inventory_id': recipe.inventory_id,
                        'inventory_name': recipe.inventory_item.name,
                        'amount': recipe.inventory_item_amount_usage,
                        'writer': recipe.writer,
                        'description': recipe.description
                    } for recipe in item.recipe
                ]
            else:
                clean_data['recipes'] = []

            available_items.append(clean_data)

        return available_items


    def create_new_menu_item(self,user_name:str,
                             name:str,
                             size:str,
                             category:str,
                             value_added_tax:float,
                             recipe_items:list[dict[str, Union[Optional[str], float]]],
                             price:float,
                             profit_margin:float,
                             description=None,
                             forecast_number=None,
                             sales_forecast_from_date=None,
                             sales_forecast_to_date=None,

                             ):
        #add to menu model (name, size, category, value_added_tax, description, available)
        new_menu = self.menu.add_menu_item(name, size, category, value_added_tax, serving=True, description=description)
        if new_menu:
            actions = []
            try:
                #get recipe for menu as a list with dicts of {inventory_id: id, amount: amount}
                print('a')
                for item in recipe_items:
                    self.menu.add_recipe_of_menu_item(new_menu.id, item['inventory_id'], item['amount'],user_name, note=item['note'])
                #will this item change the forecast if do add to forecast model
                print('b')
                if not forecast_number:
                    forecast_number = 0
                self.sales.add_sales_forecast(new_menu.id, forecast_number, sales_forecast_from_date, sales_forecast_to_date)
                print('c')
                #need to calculate the estimated menu price data: (profit_margin, manual_price)
                self.menu_pricing.calculate_updates_new_menu_item(new_menu.id, price, profit_margin, forecast_number)
                print("d")

                latest_estimation = self.menu_pricing.get_latest_update_price(new_menu.id)
                return new_menu, latest_estimation
            except Exception as e:
                for action in actions:
                    print(action)

        return False, None

    def update_menu_item(self,
                         menu_id: int,
                         name: Optional[str] = None,
                         size:Optional[str] = None,
                         category:Optional[str] = None,
                         value_added_tax:Optional[float] = None,
                         description:Optional[str] = None,
                         serving:Optional[bool] = None,
                         price:Optional[float] = None,
                         profit_margin:Optional[float] = None,
                         price_change_category:Optional[str] = None,
                         ) -> bool:

        if not self.menu.change_attribute_menu_item(
                menu_id,
                name=name,
                size=size,
                category=category,
                value_added_tax=value_added_tax,
                description=description,
                serving=serving
        ):
            return False
        if price is not None or profit_margin is not None or price_change_category is not None:
            if not self.menu_pricing.calculate_manual_price_change(menu_id,
                                                                   price,
                                                                   profit_margin,
                                                                   price_change_category):
                return False

        return True


    def get_and_format_inventory(self):
        raw_items = self.inventory.db.get_inventory()
        formatted_items = []

        for raw_item in raw_items:
            columns = raw_item.__table__.columns.keys()
            formatted_item = {column: getattr(raw_item, column) for column in columns}
            formatted_items.append(formatted_item)

        return formatted_items


    def create_new_recipe(self, **kwargs):
        if self.menu.add_recipe_of_menu_item(**kwargs):
            if self.menu_pricing.calculate_update_direct_cost(menu_ids=[kwargs['menu_id']], category='Recipe Change'):
                return True

        return False

    def update_remove_recipe(self, **kwargs):
        if self.menu.change_recipe_of_menu_item(**kwargs):
            if 'amount' in kwargs and kwargs['amount']:
                if self.menu_pricing.calculate_update_direct_cost(menu_ids=[kwargs['menu_id']], category='Recipe Change'):
                    return True
            if 'delete' in kwargs and kwargs['delete']:
                if self.menu_pricing.calculate_update_direct_cost(menu_ids=[kwargs['menu_id']], category='Recipe Change'):
                    return True

        return False

    def serialization_suppliers(self):
        list_serialization_supplier = []
        fetch_suppliers = self.supplier.db.get_supplier()
        try:
            for supplier in fetch_suppliers:
                list_serialization_supplier.append({
                    'id': supplier.id,
                    'name': supplier.name,
                    'load_time_hr': supplier.load_time_hr,
                    'contact_channel': supplier.contact_channel,
                    'contact_address': supplier.contact_address,
                })
        except Exception as e:
            return False, e
        return list_serialization_supplier

    def supplier_editor(self, **kwargs):
        editing = Supplier()
        for key, value in kwargs.items():
            setattr(editing, key, value)
        return self.supplier.db.edit_supplier(editing)

    #todo time missing from order Important
    def get_serialization_ordes_in_detail(self, open_clos:str = None):
        if open_clos and open_clos.lower().strip() == 'open':
            open_clos = "open"
        elif open_clos and open_clos.lower().strip() == 'clos':
            open_clos = "clos"
        else:
            open_clos = None


        details = self.supplier.db.get_orderdetail(open_clos=open_clos)
        if details:
            serialization = [

            ]
            orders = {}
            for each_detail in details:
                inventory_detail = {
                                    'inventory_id': each_detail.inventory_item.id,
                                  'inventory_name': each_detail.inventory_item.name,
                                  'unit': each_detail.inventory_item.unit,
                                  'box_amount': each_detail.box_amount,
                                  'approver': each_detail.approver,
                                  'box_price': each_detail.box_price,
                                  'overall_discount': each_detail.overall_discount,
                                  'boxes_ordered': each_detail.boxes_ordered,
                                  'numbers_of_box_shipped': each_detail.numbers_of_box_shipped,
                                  'numbers_of_box_received': each_detail.numbers_of_box_received,
                                  'numbers_of_box_approved': each_detail.numbers_of_box_approved,
                                  'numbers_of_box_rejected': each_detail.numbers_of_box_rejected,
                                  'status': each_detail.status,
                                  'description': each_detail.description,
                                  'ship': {
                                      'shipper': each_detail.ship.shipper,
                                      'shipper_contact': each_detail.ship.shipper_contact,
                                      'price': each_detail.ship.price,
                                      'receiver': each_detail.ship.receiver,
                                      'payer': each_detail.ship.payer,
                                      'shipped_date': each_detail.ship.shipped_date,
                                      'received_date': each_detail.ship.received_date,
                                      'description': each_detail.ship.description,
                                  },
                                  }

                only_orders_detail = {
                    'order': {'order_id': each_detail.order_id,
                              'date': each_detail.order.date,
                              'supplier_id': each_detail.order.supplier_id,
                              'real_load_time_hr': each_detail.order.real_load_time_hr,
                              'total_price': each_detail.order.total_price,
                              'buyer': each_detail.order.buyer,
                              'payer': each_detail.order.payer,
                              "status": each_detail.order.status,
                              "description": each_detail.order.description,
                              },
                }
                if each_detail.order_id in orders:
                    orders[each_detail.order_id]['order']['inventory_detail'].append(inventory_detail)
                else:
                    orders[each_detail.order_id] = only_orders_detail
                    orders[each_detail.order_id]['order']['inventory_detail'] = [inventory_detail]

            serialization.append(orders)
            return serialization
        else:
            return None

    def add_new_order_info(self, **kwargs):
        if not self.supplier.add_item_to_order(**kwargs):
            return None

        #inventory change current price
        current_price = kwargs['box_price'] / kwargs['box_amount']
        if not self.inventory.set_current_price(kwargs['inventory_id'], current_price):
            return None
        #direct cost of menu get changed
        if not self.menu_pricing.calculate_update_direct_cost():
            pass
        return True



    def update_shipper_info(self, **kwargs):
        the_id = kwargs['id']

        try:
            the_order_detail = self.supplier.db.get_orderdetail(id=the_id)[0]
        except Exception as e:
            return None

        self.supplier.receive_order(
            the_order_detail.order_id,
            the_order_detail.inventory_id,
            receiver_name=kwargs['receiver'],
            number_of_box_received= kwargs['number_received'],
            number_of_box_shipped= kwargs['number_shipped']
        )

        if the_order_detail.ship_id:
            ship = the_order_detail.ship
            for key, value in kwargs.items():
                if hasattr(ship, key) and key != "id":
                    setattr(ship, key, value)


            return self.supplier.db.edit_ship(ship)


        else:
            the_ship_info = self.supplier.add_shipment(**kwargs)
            the_order_detail.ship_id = the_ship_info.id
            return the_ship_info

    #todo approved manfi bashe chi
    def checked_received_items(self, **kwargs):
        order_detail = self.supplier.inspect_received_order(**kwargs)
        date = datetime.now()

        if 'approved' in kwargs:
            quantity = kwargs['approved'] * order_detail.box_amount

            if kwargs['approved'] > 0:
                if not self.inventory.restock_by_inventory_item(
                    inventory_item_id=order_detail.inventory_id,
                     quantity=quantity,
                    category="Supplied",
                    date=date,
                    description=f"Mr {order_detail.approver} approved {kwargs['approved']} boxes to be usable",
                    foreign_id = order_detail.id,
                ):
                    return None
            elif kwargs['approved'] < 0:
                if not self.inventory.deduct_stock_by_inventory_item(
                    inventory_item_id=order_detail.inventory_id,
                    quantity=quantity,
                    category="deduct",
                    date=date,
                    description=f"Mr {order_detail.approver} removed approved {kwargs['approved']} boxes from usable",
                    foreign_id=order_detail.id,
                ):
                    return None
        return order_detail
    #todo check if this later may cause overload for front end
    def serialization_personal(self, f=None):
        serialization = []
        if f == "all":
            active= False
        else:
            active = True
        personal = self.hr.db.get_personal(active=active,
                                           with_shift_records=True,
                                           with_payments_records=True,
                                           with_assignments_records=True,)
        for person in personal:
            person_info = {
                'personal_id': person.id,
                'first_name': person.first_name,
                'nationality_code': person.nationality_code,
                'phone_number': person.phone,
                'email': person.email,
                'address': person.address,
                'hire_date': person.hire_date,
                'position': person.position,
                'monthly_hr': person.monthly_hr,
                'monthly_payment': person.monthly_payment,
                "active": person.active,
                "description": person.description,
            }
            persons_work_record = person.shift_record
            work_record_info = [
                {
                    "record_id": record.id,
                    "from_date": record.from_date,
                    "to_date": record.to_date,
                    "lunch": record.lunch,
                    "service": record.service,
                    "extra_payment": record.extra_payment,
                    'description': record.description,

                }
                for
                record
                in
                persons_work_record
            ]

            person_info['work_records'] = work_record_info

            person_payments_record = person.payments
            payments_info = [{
                'record_id': record.id,
                'from_date': record.from_date,
                "to_date": record.to_date,
                'monthly_salary': record.monthly_salary,
                'payment': record.payment,
                'indirect_payment': record.indirect_payment,
                'insurance': record.insurance,
                'work_hr': record.work_hr,
                'extra_hr': record.extra_hr,
                'extra_expenses': record.extra_expenses,
                'description': record.description,
            }
                             for record in
                             person_payments_record]

            person_info['payments'] = payments_info

            person_assignments = person.assignments
            assignments_info = [
                {
                    'date': record.shift.date,
                    'from_hr': record.shift.from_hr,
                    'to_hr': record.shift.to_hr,
                }
                for record in
                person_assignments
            ]
            person_info['asignments'] = assignments_info

            serialization.append(person_info)
        return serialization

    def add_new_personal(self, **kwargs):
        valid_params = [
            'f_name', 'l_name', 'n_code', 'email', 'phone',
            'address', 'position', 'monthly_hr', 'monthly_payment', 'start_date'
        ]
        new_personal_kwargs = {k: v for k, v in kwargs.items() if k in valid_params}
        return self.hr.new_personal(**new_personal_kwargs)

    def edit_info_personal(self, **kwargs):
        update = True
        update_deactive = True
        valid_params = [
            "personal_id", 'f_name', 'l_name', 'n_code', 'email', 'phone',
            'address', 'position', 'monthly_hr', 'monthly_payment', 'start_date'
        ]
        new_personal_kwargs = {k: v for k, v in kwargs.items() if k in valid_params}
        update = self.hr.update_personal(**new_personal_kwargs)

        if 'deactive' in kwargs and kwargs['deactive']:
            update_deactive = self.hr.deactivate_personal(kwargs['personal_id'])

        if update and update_deactive:
            return True
        return False



    def serialization_shifts_plan(self):
        serialization = []

        shifts = self.hr.db.get_shift()

        for shift in shifts:
            shift_ifo = {
                'shift_date': shift.date,
                'shift_id': shift.id,
                'from_hr': shift.from_hr,
                'to_hr': shift.to_hr,
                'name': shift.name,
                'description': shift.description,
                'lunch': shift.lunch,
                'service': shift.service,
                'extra_payment': shift.extra_payment,
            }

            list_labor_info = shift.labor

            shift_estimation = [ {
                'position': labor.position.position,
                'number': labor.number,
                'extra_hr': labor.extra_hr,
                'from_to_date': f"{labor.position.from_date} to {labor.position.to_date}",
                'monthly_payment': labor.position.monthly_payment,
                "monthly_hr": labor.position.monthly_hr,
                'over_time_payment_hr': labor.position.extra_hr_payment,
                'category': labor.position.category,
            }
                                for labor in
                                list_labor_info]

            shift_ifo['labor_estimation'] = shift_estimation


            assignment_list = shift.assignments

            assignment_info = [
                {
                    'name': assignment.personal.name,
                    'last_name': assignment.personal.last_name,
                    'position': assignment.position.position,

                }
                for assignment in assignment_list
            ]

            shift_ifo['assignment'] = assignment_info

            serialization.append(shift_ifo)

        return serialization

    def create_the_shift(self, **kwargs):
        update = self.hr.create_shift(**kwargs)
        self.menu_pricing.labor_change_update_on_menu_price_record()
        return self.hr.create_shift(**kwargs)

    def create_routine_shifts(self, **kwargs):
        list_hrs = []
        keys_to_remove = []
        for i in range(7):
            from_hr = f'from_hr_{i}'
            to_hr = f'to_hr_{i}'
            if from_hr in kwargs and to_hr in kwargs:
                keys_to_remove.append(from_hr)
                keys_to_remove.append(to_hr)
                if kwargs[from_hr] and kwargs[to_hr]:
                    list_hrs.append((kwargs[from_hr], kwargs[to_hr]))


        for key in keys_to_remove:
            kwargs.pop(key, None)

        return self.hr.create_shift_routine(list_hrs, **kwargs)


    def add_edit_target_salary(self, **kwargs):
        id = kwargs.get("id", None)
        updated= None
        if id:
            fetched_data = self.hr.db.get_targetpositionandsalary(id=id)[0]
            for key in kwargs:
                if hasattr(fetched_data, key):
                    setattr(fetched_data, key, kwargs[key])
            updated = self.hr.db.edit_targetpositionandsalary(fetched_data)
        else:
            updated =  self.hr.add_target_position(**kwargs)
        self.menu_pricing.labor_change_update_on_menu_price_record()
        return updated
    def get_target_salary(self):
        fetched_data = self.hr.db.get_targetpositionandsalary()
        list_data = {}



        for data in fetched_data:
            data_exist = list_data.get(data.position, None)
            if not data_exist:
                list_data[data.position] = []
            new_data = {
                'from_date': data.from_date,
                'to_date': data.to_date if data.to_date else 'current',
                'category': data.category,
                'monthly_hr': data.monthly_hr,
                'monthly_payment': data.monthly_payment,
                'monthly_insurance': data.monthly_insurance,
                'extar_hr_payment': data.extra_hr_payment,
            }
            list_data[data.position].append(new_data)



        return list_data

    def add_edit_bill(self, **kwargs):
        the_id = kwargs.get("id", None)
        if the_id:
            kwargs.pop('id')
            return self.bills_rent.update_bill(the_id, **kwargs)
        else:
            return self.bills_rent.new_bill(**kwargs)

    def get_bills(self):
        fetched_data = self.bills_rent.find_bills()
        list_data = {}

        for data in fetched_data:
            data_exist = list_data.get(data.name, None)
            if not data_exist:
                list_data[data.name] = []
            new_data = {
                'from_date': data.from_date,
                'to_date': data.to_date if data.to_date else 'current',
                'category': data.category,
                'cost': data.cost,
                'payer': data.payer,
                'description': data.description,
            }
            list_data[data.name].append(new_data)

        return list_data

    #todo update price estimated false later with front end check

    def add_edit_estimated_bill(self, **kwargs):
        the_id = kwargs.get("id", None)
        if the_id:
            kwargs.pop('id')
            update = self.bills_rent.update_bill_estimated(the_id, **kwargs)
        else:
            update = self.bills_rent.new_bill_estimated(**kwargs)

        a=self.menu_pricing.bills_change_update_on_menu_price_record()
        print(a)
        return update
    def get_estimated_bills(self):
        fetched_data = self.bills_rent.find_bills_estimated()
        list_data = {}

        for data in fetched_data:
            data_exist = list_data.get(data.name, None)
            if not data_exist:
                list_data[data.name] = []
            new_data = {
                'from_date': data.from_date,
                'to_date': data.to_date if data.to_date else 'current',
                'category': data.category,
                'cost': data.cost,
                'description': data.description,
            }
            list_data[data.name].append(new_data)

        return list_data

    def add_edit_rent(self, **kwargs):
        the_id = kwargs.get("id", None)
        if the_id:
            kwargs.pop('id')
            update = self.bills_rent.update_rent(the_id, **kwargs)
        else:
            update = self.bills_rent.new_rent(**kwargs)

        a=self.menu_pricing.rent_change_update_on_menu_price_record()
        print(a)
        return update
    def get_the_rent(self):
        fetched_data = self.bills_rent.find_rents()
        list_data = {}

        for data in fetched_data:
            data_exist = list_data.get(data.name, None)
            if not data_exist:
                list_data[data.name] = []
            new_data = {
                'from_date': data.from_date,
                'to_date': data.to_date if data.to_date else 'current',
                'rent': data.rent,
                'mortgage': data.mortgage,
                'mortgage_percentage_to_rent': data.mortgage_percentage_to_rent,
                'payer': data.payer,
                'description': data.description,
            }
            list_data[data.name].append(new_data)

        return list_data


    def add_edit_equipment(self, **kwargs):
        the_id = kwargs.get("id", None)
        if the_id:
            kwargs.pop('id')
            update = self.equipment.update_equipment(the_id, **kwargs)
        else:
            update = self.equipment.new_equipment_record(**kwargs)

        a=self.menu_pricing.equipment_change_update_on_menu_price_record()
        print(a)
        return update
    def get_the_equipments(self):
        fetched_data = self.equipment.get_all_equipment()
        list_data = {}

        for data in fetched_data:
            data_exist = list_data.get(data.category, None)
            if not data_exist:
                list_data[data.category] = []
            new_data = {
                "id": data.id,
                'name': data.name,
                'number': data.number ,
                'purchase_date': data.purchase_date,
                'expire_date': data.expire_date,
                'purchase_price': data.purchase_price,
                'monthly_depreciation': data.monthly_depreciation,
                'in_use': data.in_use,
                'description': data.description,
            }
            list_data[data.category].append(new_data)

        return list_data



