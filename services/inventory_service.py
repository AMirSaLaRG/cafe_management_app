from typing import Optional
from datetime import datetime

from models.dbhandler import DBHandler
from models.cafe_managment_models import *

class InventoryService:
    def __init__(self, db_handler:DBHandler):
        self.db = db_handler

    def _calculate_inventory(self, inventory_item_id: int):
        """
        Recalculates the stock amount for an inventory item.
        Uses the latest manual report as base and sums subsequent changes.
        """

        # Step 1: Get latest manual report
        latest_manual_report = self.db.get_inventorystockrecord(
            inventory_id=inventory_item_id,
            latest_check=True
        )

        if latest_manual_report:
            last_report: InventoryStockRecord = latest_manual_report[0]
            base_amount = last_report.manual_report or 0
            from_time = last_report.date
        else:
            base_amount = 0
            from_time = None

        # Step 2: Get all subsequent stock changes
        calculating_amounts = self.db.get_inventorystockrecord(
            from_date=from_time,
            inventory_id=inventory_item_id
        )

        # Step 3: Exclude manual report itself if included
        if latest_manual_report:
            calculating_amounts = [item for item in calculating_amounts if item.id != last_report.id]

        # Step 4: Sum all change_amounts
        total_changes = sum(item.change_amount for item in calculating_amounts)

        # Step 5: Final stock
        final_stock = base_amount + total_changes

        # Step 6: Update inventory
        fetch_inventory_items = self.db.get_inventory(id=inventory_item_id)
        if fetch_inventory_items:
            inventory_item: Inventory = fetch_inventory_items[0]
            inventory_item.current_stock = final_stock
            self.db.edit_inventory(inventory_item)
            return True
        else:
            return False



    def _correct_failed_group_attempt(self, the_ids:list[int]) -> Optional[bool]:
        for record_id in the_ids:
            if record_id is not None:
                corrupt_record = self.db.get_inventorystockrecord(id=record_id)[0]
                if not self.db.delete_inventorystockrecord(corrupt_record):
                    return False
        return True




    #todo date should removed i think
    #check if it is possible to make this item
    def check_stock_for_menu(self, menu_id:int, quantity:float=1, date:datetime=None) -> tuple[bool, dict[str, float]]:
        """
        Check if a menu item can be prepared given the current inventory stock.

        For each ingredient in the menu's recipe, compares the required amount
        (inventory_item_amount_usage * quantity) with the current stock.
        If any ingredient is insufficient, records the missing amount.

        Args:
            menu_id (int): The ID of the menu item to check.
            quantity (float, optional): Number of menu items to prepare. Defaults to 1.

        Returns:
            tuple[bool, dict[str, float]]:
                - bool: True if all ingredients are sufficient, False if any are missing.
                - dict[str, float]: Mapping of inventory item names to missing amounts
                  (empty if all ingredients are sufficient).
        """

        is_satisfied = True
        missing_items = {}
        list_menu_items = self.db.get_menu(id = menu_id, with_recipe=True)
        if list_menu_items:
            menu_item:Menu = list_menu_items[0]
            menu_recipe = menu_item.recipe
            for used_item in menu_recipe:
                inventory_item = used_item.inventory_item
                amount = used_item.inventory_item_amount_usage
                amount_needed = amount * quantity
                current_stock = inventory_item.current_stock or 0
                if current_stock < amount_needed:
                    is_satisfied = False
                    missing_items[inventory_item.name] = amount_needed - inventory_item.current_stock

        else:
            is_satisfied = False

        return is_satisfied, missing_items
    #check if it is possible to make this item
    def check_stock_for_inventory(self, inventory_id:int, quantity:float, date:datetime=None) -> tuple[bool, dict[str, float]]:
        is_satisfied = True
        missing_amount = {}

        inventory_item = self.db.get_inventory(id=inventory_id)
        if inventory_item:
            item = inventory_item[0]
            amount = item.current_stock
            amount_needed = quantity
            if amount < amount_needed:
                is_satisfied = False
                missing_amount[item.name] = (amount_needed - amount)
        else:
            is_satisfied = False

        return is_satisfied, missing_amount

    #reduce ingredients after a sale or menu usage
    def deduct_stock_by_menu(self, menu_id: int,
                             quantity:float,
                             category:str=None,
                             foreign_id: int = None,
                             date:datetime=None,
                             description:str=None,
                             ) -> bool:
        satisfied, items = self.check_stock_for_menu(menu_id=menu_id, quantity=quantity)
        if not satisfied:
            return False
        ids = []
        menu_item: Menu = self.db.get_menu(id=menu_id, with_recipe=True)[0]
        menu_recipe = menu_item.recipe
        for used_item in menu_recipe:
            inventory_item: Inventory = used_item.inventory_item
            amount = used_item.inventory_item_amount_usage
            amount_change = -(amount * quantity)
            new = self.db.add_inventorystockrecord(inventory_id=inventory_item.id,
                                                   change_amount=amount_change,
                                                   category=category,
                                                   foreign_id=foreign_id,
                                                   date=date or datetime.now(),
                                                   description=description)
            ids.append(new.id)
        if None in ids:
            if self._correct_failed_group_attempt(ids):
                return False
        for used_item in menu_recipe:
            inventory_id = used_item.inventory_id
            self._calculate_inventory(inventory_item_id=inventory_id)
        return True

    def deduct_stock_by_inventory_item(self, inventory_item_id:int,
                                       quantity: float,
                                       category: str = None,
                                       date: datetime = None,
                                       description: str = None,
                                       foreign_id: int = None) -> bool:

        satisfied, missing = self.check_stock_for_inventory(inventory_id=inventory_item_id, quantity=quantity)
        if not satisfied:
            return False

        changed_amount = -quantity
        new: Optional[InventoryStockRecord] = self.db.add_inventorystockrecord(inventory_id=inventory_item_id,
                                               change_amount=changed_amount,
                                               category=category,
                                               foreign_id=foreign_id,
                                               date=date or datetime.now(),
                                               description=description)

        if new:
            self._calculate_inventory(inventory_item_id=inventory_item_id)
            return True

        return False


    def restock_by_menu(self, menu_id: int,
                             quantity:float,
                             category:str=None,
                             foreign_id: int = None,
                             date:datetime=None,
                             description:str=None,
                             ) -> bool:

        ids = []
        menu_item: Menu = self.db.get_menu(id=menu_id, with_recipe=True)[0]
        menu_recipe = menu_item.recipe
        for used_item in menu_recipe:
            inventory_item: Inventory = used_item.inventory_item
            amount = used_item.inventory_item_amount_usage
            amount_change = (amount * quantity)
            new = self.db.add_inventorystockrecord(inventory_id=inventory_item.id,
                                                   change_amount=amount_change,
                                                   category=category,
                                                   foreign_id=foreign_id,
                                                   date=date or datetime.now(),
                                                   description=description)
            ids.append(new.id)
        if None in ids:
            if self._correct_failed_group_attempt(ids):
                return False
        for used_item in menu_recipe:
            inventory_id = used_item.inventory_id
            self._calculate_inventory(inventory_item_id=inventory_id)
        return True

    def restock_by_inventory_item(self, inventory_item_id:int,
                                       quantity: float,
                                       category: str = None,
                                       date: datetime = None,
                                       description: str = None,
                                       foreign_id: int = None) -> bool:

        changed_amount = quantity
        new: Optional[InventoryStockRecord] = self.db.add_inventorystockrecord(inventory_id=inventory_item_id,
                                               change_amount=changed_amount,
                                               category=category,
                                               foreign_id=foreign_id,
                                               date=date or datetime.now(),
                                               description=description)

        if new:
            self._calculate_inventory(inventory_item_id=inventory_item_id)
            return True

        return False


    #manual correction after check
    def manual_report(self,inventory_id:int,
                      amount:float,
                      reporter:str,
                      date:Optional[datetime]=None,
                      reason:Optional[str] = None,
                      foreign_id:Optional[int]=None) -> bool:
        if date is None:
            date = datetime.now()

        recorded = self.db.add_inventorystockrecord(inventory_id=inventory_id,
                                         category="Manual Check",
                                         foreign_id=foreign_id,
                                         date=date,
                                         manual_report=amount,
                                         reporter=reporter,
                                         description=reason)
        if recorded is None:
            return False

        self._calculate_inventory(inventory_item_id=inventory_id)
        return True

    #see where stock went
    def get_usage_report(self, inventory_id, from_date, to_date):
        pass

    #returns items blow threshold
    def low_stock_alerts(self):
        pass

    #Predict future needs based on
    def forecast_inventory(self, menu_id, days=7):
        pass