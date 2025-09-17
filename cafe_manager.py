# cafe_manager.py

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

from typing import Optional, List
from datetime import datetime


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

            available_items.append({
                "item": item,
                "max_to_make": number_available
            })
            print(item)

        return available_items


    def add_menu_item(self, name, size, category, value_added_tax, description=None):
        return self.menu.add_menu_item(name=name,
                                        size=size,
                                        category=category,
                                        value_added_tax=value_added_tax,
                                        description=description)