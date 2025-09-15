from datetime import datetime
from models.dbhandler import DBHandler
from models.cafe_managment_models import Sales, Invoice, InvoicePayment, Menu


class SalesService:
    def __init__(self, db_handler: DBHandler):
        self.db = db_handler

    def _update_invoice_price(self, invoice_id):
        the_invoice = self.db.get_invoice(id=invoice_id)[0]
        full_price = sum(sales.price for sales in the_invoice.sales)
        full_discount = sum(sales.discount for sales in the_invoice.sales)
        the_invoice.total_price = full_price - full_discount
        return bool(self.db.edit_invoice(the_invoice))

    def _calculate_invoice_remain(self, invoice_id):
        the_invoice = self.db.get_invoice(id=invoice_id)[0]
        all_payments = the_invoice.payments
        all_paid = sum(p.paid for p in all_payments)
        all_tips = sum(p.tip for p in all_payments)
        return the_invoice.total_price + all_tips - all_paid
    #Full sale flow (invoice, sales record, stock deduction)

    def process_sale(self,
                     menu_item:Menu,
                     quantity,
                     discount,
                     price=None,
                     invoice_id = None,
                     description=None,
                     time=None,
                     saler=None):

        if time is None:
            time = datetime.now()

        if invoice_id is None:
            order_invoice = self.db.add_invoice(saler=saler,
                                date=time,
                                closed=False,
                                description=f'Order: {description}',)
            invoice_id = order_invoice.id
        if price is None:
            current_price = menu_item.current_price
            price = (current_price * quantity)

        if self.db.add_sales(menu_id=menu_item.id,
                          invoice_id=invoice_id,
                          number=quantity,
                          discount=discount,
                          price=price,) is None:
            return False

        self._update_invoice_price(invoice_id)
        return True





    #undo sale & restock
    def cancel_sale(self, menu_id, invoice_id, quantity=None, discount=None, price=None):
        sales = self.db.get_sales(menu_id=menu_id, invoice_id=invoice_id)
        if not sales:
            return False  # Nothing to cancel
        total_number_ordered = sum(s.number for s in sales)
        price_per_item = sum(s.price for s in sales) / total_number_ordered
        discount_per_item = sum(s.discount for s in sales) / total_number_ordered

        success = True

        if quantity is None:
            for sale in sales:
                if not self.db.delete_sales(sale):
                    success = False
        elif quantity > 0:

            for sale in sales:

                if quantity <= 0:
                    break
                if sale.number <= quantity:
                    if not self.db.delete_sales(sale):
                        success = False
                    quantity -= sale.number
                else:
                    sale.number -= quantity
                    if discount is None:
                        discount = discount_per_item * sale.number
                    sale.discount = discount

                    if price is None:
                        price = price_per_item * sale.number
                    sale.price = price
                    if not self.db.edit_sales(sale):
                        success = False
                    quantity = 0

        self._update_invoice_price(invoice_id)
        return success

    def change_sale(self, menu_id, invoice_id, id=None, discount=None, number=None, price=None, description=None):
        success = True

        if id:
            the_sales = self.db.get_sales(id=id)
            if not the_sales:
                return False
            the_sale = the_sales[0]
        else:
            the_sales = self.db.get_sales(menu_id=menu_id, invoice_id=invoice_id)
            if not the_sales:
                return False
            the_sale = the_sales[0]

        if number:
            the_sale.number = number
        if discount:
            the_sale.discount = discount
        if price:
            the_sale.price = price
        if description:
            the_sale.description = description

        updated_sale = self.db.edit_sales(the_sale)
        self._update_invoice_price(the_sale.invoice_id)

        if not updated_sale:
            return False



    def add_payment(self,
                    amount,
                    payer,
                    method,
                    receiver,
                    invoice_id,
                    remain_as_tip=False,
                    tip=None,
                    receiver_id=None,
                    date=None):

        success = True
        if date is None:
            date = datetime.now()
        the_payment = self.db.add_invoicepayment(invoice_id=invoice_id,
                                   paid=amount,
                                   tip=tip,
                                   payer=payer,
                                   method=method,
                                   receiver=receiver,
                                   receiver_id=receiver_id,
                                   date=date)
        if not the_payment:
            return False

        remain = self._calculate_invoice_remain(invoice_id)

        if remain < 0 and remain_as_tip:
            the_payment.tip = (the_payment.tip or 0) + abs(remain)
            self.db.edit_invoicepayment(the_payment)
            remain = 0

        if remain == 0:
            the_invoice = self.db.get_invoice(id=invoice_id)[0]
            the_invoice.closed = True
            self.db.edit_invoice(the_invoice)

        return True

