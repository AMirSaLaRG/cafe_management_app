from typing import Optional
from datetime import datetime, timedelta

from models.dbhandler import DBHandler
from models.cafe_managment_models import Inventory, Menu, InventoryStockRecord

INITIATE_STOCK_CATEGORY = "Initiate Stock"

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
        total_changes = sum(item.change_amount for item in calculating_amounts if item.change_amount is not None)

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
    def check_stock_for_menu(self, menu_item:Menu, quantity:float=1, date:datetime=None) -> tuple[bool, dict[str, float]]:
        """
        Check if a menu item can be prepared given the current inventory stock.

        For each ingredient in the menu's recipe, compares the required amount
        (inventory_item_amount_usage * quantity) with the current stock.
        If any ingredient is insufficient, records the missing amount.

        Args:
            menu_id (int): the Menu object.
            quantity (float, optional): Number of menu items to prepare. Defaults to 1.

        Returns:
            tuple[bool, dict[str, float]]:
                - bool: True if all ingredients are sufficient, False if any are missing.
                - dict[str, float]: Mapping of inventory item names to missing amounts
                  (empty if all ingredients are sufficient).
        """

        is_satisfied = True
        missing_items = {}

        menu_item:Menu = menu_item
        menu_recipe = menu_item.recipe
        for used_item in menu_recipe:
            inventory_item = used_item.inventory_item
            amount = used_item.inventory_item_amount_usage
            amount_needed = amount * quantity
            current_stock = inventory_item.current_stock or 0
            if current_stock < amount_needed:
                is_satisfied = False
                missing_items[inventory_item.name] = amount_needed - current_stock



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
    def deduct_stock_by_menu(self, menu_item:Menu,
                             quantity:float,
                             category:str=None,
                             foreign_id: int = None,
                             date:datetime=None,
                             description:str=None,
                             ) -> bool:
        satisfied, items = self.check_stock_for_menu(menu_item=menu_item, quantity=quantity)
        if not satisfied:
            return False
        ids = []
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


    def restock_by_menu(self, menu_item: Menu,
                             quantity:float,
                             category:str=None,
                             foreign_id: int = None,
                             date:datetime=None,
                             description:str=None,
                             ) -> bool:

        ids = []
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


    #returns items blow threshold
    def low_stock_alerts(self, item_list:Optional[list[Inventory]] = None) -> dict[str, float]:
        alert_dict = {}

        if item_list is None:
            all_inventory = self.db.get_inventory()
            for inventory_item in all_inventory:
                current_stock = inventory_item.current_stock or 0
                safety_stock = inventory_item.safety_stock or 0
                the_supplier = inventory_item.supplier
                load_time_hr = the_supplier.load_time_hr or 0
                daily_usage = inventory_item.daily_usage or 0

                load_time_day = load_time_hr / 24
                load_time_day = round(load_time_day) + 1
                threshold = safety_stock + (load_time_day * daily_usage)
                if current_stock <= threshold:
                    alert_dict[inventory_item.name] = current_stock
        else:
            for inventory_item in item_list:
                current_stock = inventory_item.current_stock
                safety_stock = inventory_item.safety_stock
                load_time_day = inventory_item.current_supplier.load_time_day
                daily_usage = inventory_item.daily_usage

                threshold = safety_stock + (load_time_day * daily_usage)
                if current_stock <= threshold:
                    alert_dict[inventory_item.name] = current_stock


        return alert_dict


    #see where stock went
    def get_inventory_stock_report(self, inventory_id:int, from_date: datetime=None, to_date: datetime=None) -> list[InventoryStockRecord]:
        return self.db.get_inventorystockrecord(inventory_id=inventory_id, from_date=from_date, to_date=to_date)


    #do not handle gaps
    #Predict future needs based on
    def forecast_inventory(self, inventory_id, days=7) -> dict[str, float]:
        """
        this function forecast the amount for item in days
        :param
         inventory_id: id of item
         days: days to forecast

        :return: a list with name and stock value of it after that many days
        """

        item = self.db.get_inventory(id=inventory_id)[0]
        daily_usage = item.daily_usage

        usage_after_days = daily_usage * days
        current_stock = item.current_stock

        difference = current_stock - usage_after_days

        return {item.name: difference}



    def create_new_inventory_item(self,
                                  item_name:str,
                                  unit:str,
                                  category:str,
                                  person_who_added:str,
                                  current_supplier_id: int = None,
                                  daily_usage:float = None,
                                  safety_stock:float=None,
                                  price_per_unit:float=None,
                                  current_stock:float=0):


        # name unit category is basic of an inventory item to add to inventory model
        # next check if there is daily_usage and safety_stock and price_per_unit and current_supplier_id is there
        # all of top items will add to inventory

        new_item = self.db.add_inventory(name=item_name, unit=unit, category=category,
                              current_supplier=current_supplier_id, price_per_unit=price_per_unit,
                              daily_usage=daily_usage, safety_stock=safety_stock,
                                         )
        if new_item is None:
            return False
        # if there is a current_stock we should add restock_by_inventory_item request
        if self.manual_report(inventory_id=new_item.id,
                              amount=current_stock,
                              reporter=person_who_added,
                              reason=INITIATE_STOCK_CATEGORY, ):
            return True


        return False

    def change_daily_usage(self, inventory_id:int, new_daily_usage:float) -> bool:
        search_list = self.db.get_inventory(id=inventory_id)
        if search_list and new_daily_usage>=0:
            the_item = search_list[0]
            the_item.daily_usage = new_daily_usage
            approve = self.db.edit_inventory(the_item)
            if approve:
                return True

        return False


    def change_supplier(self, inventory_id:int, supplier_id:int) -> bool:
        search_list = self.db.get_inventory(id=inventory_id)
        if search_list and self.db.get_supplier(id=supplier_id):
            the_item = search_list[0]
            the_item.current_supplier = supplier_id
            approve = self.db.edit_inventory(the_item)
            if approve:
                return True

        return False

    def change_safety_stock(self, inventory_id:int, new_safety_stock:float) -> bool:
        search_list = self.db.get_inventory(id=inventory_id)
        if search_list and new_safety_stock>=0:
            the_item = search_list[0]
            the_item.safety_stock = new_safety_stock
            approve = self.db.edit_inventory(the_item)
            if approve:
                return True

        return False

    def set_current_price(self, inventory_id:int, current_price:float):
        search_list = self.db.get_inventory(id=inventory_id)
        if search_list and current_price>=0:
            the_item = search_list[0]
            the_item.current_price = current_price
            approve = self.db.edit_inventory(the_item)
            if approve:
                return True

        return False

