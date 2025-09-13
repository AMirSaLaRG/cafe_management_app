from datetime import datetime, timedelta
from typing import Optional


from models.dbhandler import DBHandler
from models.cafe_managment_models import Supplier, Order, Ship, OrderDetail

class SupplierService:
    def __init__(self, db_handler: DBHandler):
        self.db = db_handler

    #Missing Status: There's no status for "partially approved" or "pending inspection".
    def _check_status_detail(self, order_id, item_id):
        the_check_detail_fetch = self.db.get_orderdetail(order_id=order_id, inventory_id=item_id)
        if not the_check_detail_fetch:
            return False
        the_check_detail = the_check_detail_fetch[0]
        status = None
        #order = approve : completed
        if the_check_detail.numbers_of_box_approved and the_check_detail.numbers_of_box_approved == the_check_detail.boxes_ordered:
            status = "completed"
        else:
            if the_check_detail.numbers_of_box_received is not None:
                if the_check_detail.numbers_of_box_rejected and the_check_detail.numbers_of_box_rejected > 0:
                    status = "rejected"
                elif the_check_detail.boxes_ordered > the_check_detail.numbers_of_box_received:
                    status = "shortage"
                elif the_check_detail.boxes_ordered == the_check_detail.numbers_of_box_received:
                    status = "received"


        if status:
            the_check_detail.status = status
            return bool(self.db.edit_orderdetail(the_check_detail))
        return True






    def create_order(self, supplier_id,
                     buyer:str,
                     payer:str,
                     order_date=None,
                     description=None) -> bool:
        return bool(self.db.add_order(supplier_id=supplier_id,
                          buyer=buyer,
                          payer=payer,
                          date=order_date,
                          description=description,
                          status="Opened"))

    def get_open_orders(self):
        return self.db.get_order(status="Opened")

    def close_order(self, order_id: int) -> bool:
        """Close an order and update its status"""
        order = self.db.get_order(id=order_id)
        if not order:
            return False
        order[0].status = "Closed"
        return bool(self.db.edit_order(order[0]))

    def get_order_details(self, order_id: int) -> list[OrderDetail]:
        """Get all details for a specific order"""
        return self.db.get_orderdetail(order_id=order_id)

    def update_order_total_price(self, order_id: int) -> bool:
        """Recalculate and update the total price of an order"""
        order_details = self.db.get_orderdetail(order_id=order_id)
        if not order_details:
            return False

        total_cost = 0
        total_discount = 0

        for detail in order_details:
            if detail.box_price and detail.boxes_ordered:
                total_cost += (detail.box_price * detail.boxes_ordered)
            if detail.overall_discount:
                total_discount += detail.overall_discount
        total = total_cost - total_discount
        order = self.db.get_order(id=order_id)
        if order:
            order[0].total_price = total
            return bool(self.db.edit_order(order[0]))
        return False

    def add_item_to_order(self,
                          order_id:int,
                          inventory_id:int,
                          num_box_ordered:float,
                          box_amount: float = None,
                          box_price: float = None,
                          expected_delivery_date:Optional[datetime] = None,
                          overall_discount: Optional[float] = None,
                          ) ->bool:


        exist = self.db.get_orderdetail(order_id=order_id, inventory_id=inventory_id)
        if exist:
            order_detail = exist[0]
            if box_amount and order_detail.box_amount == box_amount:
                ordered_boxes = order_detail.boxes_ordered or 0
                the_current_price = order_detail.box_price or 0
                box_price = box_price or 0
                overall_discounted = order_detail.overall_discount or 0
                overall_discount = overall_discount or 0

                order_detail.boxes_ordered = ordered_boxes + num_box_ordered
                order_detail.overall_discount = overall_discounted + overall_discount
                order_detail.box_price = the_current_price + box_price

                return bool(self.db.edit_orderdetail(order_detail))



        return bool(self.db.add_orderdetail(inventory_id=inventory_id,
                                order_id=order_id,
                                boxes_ordered=num_box_ordered,
                                expected_delivery_date=expected_delivery_date,
                                box_amount=box_amount,
                                box_price=box_price,
                                overall_discount=overall_discount,))


    def receive_order(self,
                      order_id:int,
                      inventory_id:int,
                      receiver_name:str,
                      number_of_box_received:float,
                      ship_id:Optional[int]=None,
                      date:Optional[datetime]=None) -> bool:

        if date is None:
            date = datetime.now()
        order_detail_fetch = self.db.get_orderdetail(order_id=order_id, inventory_id=inventory_id)
        if not order_detail_fetch:
            return False


        the_order_detail = order_detail_fetch[0]

        received_before = the_order_detail.numbers_of_box_received or 0
        receiver_before = the_order_detail.receiver or ""

        the_order_detail.numbers_of_box_received = received_before + number_of_box_received
        the_order_detail.receiver = f'{receiver_before} {receiver_name}'
        the_order_detail.actual_delivery_date = date
        if ship_id is not None:
            the_order_detail.ship_id = ship_id
        if not self.db.edit_orderdetail(the_order_detail):
            return False
        self._check_status_detail(the_order_detail.order_id, the_order_detail.inventory_id)
        return True

    def inspect_received_order(self,
                               order_id:int,
                               inventory_id:int,
                               approved: float,
                               rejected: float,
                               replace_rejected: float) -> bool:
        order_detail_fetch = self.db.get_orderdetail(order_id=order_id, inventory_id=inventory_id)
        if not order_detail_fetch:
            return False
        the_order_detail = order_detail_fetch[0]
        approved_before = the_order_detail.numbers_of_box_approved or 0
        rejected_before = the_order_detail.numbers_of_box_rejected or 0


        the_order_detail.numbers_of_box_approved = approved_before + approved
        the_order_detail.numbers_of_box_rejected = rejected_before + rejected - replace_rejected

        if not self.db.edit_orderdetail(the_order_detail):
            return False
        self._check_status_detail(the_order_detail.order_id, the_order_detail.inventory_id)
        return True
#___shipment____
    def add_shipment(self,
                     shipper:str,
                     shipper_contact:str,
                     price: Optional[float] = None,
                     receiver: Optional[str] = None,
                     payer: Optional[str] = None,
                     shipped_date: Optional[datetime] = None,
                     received_date: Optional[datetime] = None,
                     description: Optional[str] = None) -> Optional[Ship]:
        """Add a new shipment record"""
        if shipped_date is None:
            shipped_date = datetime.now()
        return self.db.add_ship(
            shipper=shipper,
            shipper_contact=shipper_contact,
            price=price,
            receiver=receiver,
            payer=payer,
            shipped_date=shipped_date,
            received_date=received_date,
            description=description
        )

    def get_shipments(self,
                      id: Optional[int] = None,
                      shipper: Optional[str] = None,
                      receiver: Optional[str] = None,
                      from_date_shipped: Optional[datetime] = None,
                      to_date_shipped: Optional[datetime] = None,
                      from_date_received: Optional[datetime] = None,
                      to_date_received: Optional[datetime] = None,
                      ) -> list[Ship]:
        """Get shipments with optional filters"""
        return self.db.get_ship(
            id=id,
            shipper=shipper,
            receiver=receiver,
            from_date_shipped=from_date_shipped,
            to_date_shipped=to_date_shipped,
            from_date_received=from_date_received,
            to_date_received=to_date_received,
        )
    #____ supplier _____

    def add_a_supplier(self, name: str,
                       contact_channel: str,
                       contact_address: str,
                       load_time_hr: int) -> bool:
        return bool(self.db.add_supplier(name,
                             contact_channel=contact_channel,
                             contact_address=contact_address,
                             load_time_hr=load_time_hr))

    def get_suppliers(self, id:Optional[int]=None, name:Optional[str]=None) -> Optional[list[Supplier]]:
        fetch = self.db.get_supplier(id=id, name=name)
        if not fetch:
            return []
        return fetch

    def update_supplier_lead_time(self, supplier_id: int, new_lead_time: int) -> bool:
        """Update a supplier's lead time"""
        supplier = self.db.get_supplier(id=supplier_id)
        if not supplier:
            return False
        supplier[0].load_time_hr = new_lead_time
        return bool(self.db.edit_supplier(supplier[0]))

    def get_supplier_orders(self, supplier_id: int, status: Optional[str] = None) -> list[Order]:
        """Get all orders for a specific supplier"""
        return self.db.get_order(supplier_id=supplier_id, status=status)