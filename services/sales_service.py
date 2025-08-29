

class SalesService:
    def __init__(self):
        self.db = None

    #Full sale flow (invoice, sales record, stock deduction)
    def process_sale(self, menu_id, quantity, discount, payment_infor):
        pass

    #undo sale & restock
    def cancel_sale(self, menu_id, invoice_id):
        pass

    def create_invoice(self, payment_id, saler, total_price):
        pass

    def add_payment(self, amount, payer, method, receiver):
        pass

    def get_sales_report(self, from_date, to_date):
        pass

    def top_selling_items(self, limit=5):
        pass