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

