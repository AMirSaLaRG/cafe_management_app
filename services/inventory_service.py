from models.dbhandler import DBHandler

class InventoryService:
    def __init__(self, db_handler:DBHandler = DBHandler()):
        self.db = db_handler

    #check if it is possible to make this item
    def check_stock(self, menu_id, quantity):
        pass

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