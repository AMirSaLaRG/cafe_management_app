from models.dbhandler import DBHandler
from models.cafe_managment_models import *

class InventoryService:
    def __init__(self, db_handler:DBHandler):
        self.db = db_handler

    #check if it is possible to make this item
    def check_stock(self, menu_id, quantity=1):
        satisfied = True
        note_missing_items = ""
        menu_item: Menu = self.db.get_menu(id = menu_id, with_recipe=True)[0]
        menu_recipe = menu_item.recipe
        for used_item in menu_recipe:
            inventory_item = used_item.inventory_item
            amount = used_item.inventory_item_amount_usage
            if (inventory_item.current_stock * quantity)< (amount * quantity):
                satisfied = False
                note_missing_items = f"\n{inventory_item.name} have {(inventory_item.quantity * quantity)} need {(amount * quantity)}"
        if note_missing_items:
            note = f"Can not provide {quantity} x {menu_item.name}  item. {note_missing_items}"
            print(note)
        else:
            note = "Available"

        return satisfied




    #reduce ingredients after a sale or menu usage
    def deduct_stock(self, menu_id, quantity):
        pass

    #add back stock after supply
    def restock_item(self, inventory_id, quantity):
        pass
    #manual correction after check
    def adjust_stock(self,inventory_id, new_amount, reason):
        pass

    #record usage link them together
    def log_usage(self, inventory_id, usage_id, quantity):
        pass

    #see where stock went
    def get_usage_report(self, inventory_id, from_date, to_date):
        pass
    #add supplyrecord update inventory current_stock logs inventorystockrecord
    def process_supply(self, ship_id, supplies):
        pass
    #returns items blow threshold
    def low_stock_alerts(self, threshold=5):
        pass

    #Predict future needs based on
    def forecast_inventory(self, menu_id, days=7):
        pass