from datetime import datetime, timedelta
from typing import Optional


from models.dbhandler import DBHandler
from models.cafe_managment_models import Supplier, Order, Ship, OrderDetail
#todo ship or receives can should be many to many but now is one to many
class SupplierService:
    def __init__(self, db_handler: DBHandler):
        self.db = db_handler

    def _check_status_order(self, order_id):
        try:
            the_order = self.db.get_order(id=order_id)[0]
        except:
            return None
        detail_stat = [item.status for item in the_order.order_details]
        if len(detail_stat) == len(set(detail_stat)):
            the_order.status = detail_stat[0]
            self.db.edit_order(the_order)



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

                elif the_check_detail.boxes_ordered < the_check_detail.numbers_of_box_received:
                    status = "overage"

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
                     description=None) -> Optional[OrderDetail]:
        return self.db.add_order(supplier_id=supplier_id,
                          buyer=buyer,
                          payer=payer,
                          date=order_date,
                          description=description,
                          status="Opened")

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
                          inventory_id:int,
                          num_box_ordered:float,
                          order_id:Optional[int] = None,
                          supplier_id:Optional[int] = None,
                          buyer:Optional[str] = None,
                          payer:Optional[str] = None,
                          order_date:Optional[datetime] = None,
                          order_description:Optional[str] = None,
                          box_amount: float = None,
                          box_price: float = None,
                          overall_discount: Optional[float] = None,
                          expected_delivery_date:Optional[datetime] = None,
                          shipper_id:Optional[int] = None,
                          shipper_name:Optional[str] = None,
                          shipper_contact:Optional[str] = None,
                          shipper_price:Optional[float] = None,
                          shipper_payer:Optional[str] = None,
                          ) :
        created_ship = None
        created_order = None
        if not order_id:
            created_order = self.create_order(supplier_id,
                                              buyer,
                                              payer,
                                              order_date,
                                              order_description)
            order_id = created_order.id

        if not order_id:
            return None

        if shipper_id or shipper_name:
            if not shipper_id:
                created_ship = self.add_shipment(
                    shipper_name,
                    shipper_contact,
                    shipper_price,
                    shipper_payer,
                )
                shipper_id = created_ship.id
        if not shipper_id:
            if created_order:
                self.db.delete_order(created_order)
            return None

        order_detail = self.db.add_orderdetail(inventory_id=inventory_id,
                                               order_id=order_id,
                                               ship_id=shipper_id,
                                               boxes_ordered=num_box_ordered,
                                               expected_delivery_date=expected_delivery_date,
                                               box_amount=box_amount,
                                               box_price=box_price,
                                               overall_discount=overall_discount, )


        if not order_detail:
            if created_order:
                self.db.delete_order(created_order)
            if created_ship:
                self.db.delete_ship(created_ship)
            return None


        self.update_order_total_price(order_id)
        return True




    def receive_order(self,
                      order_id:int,
                      inventory_id:int,
                      receiver_name:str,
                      number_of_box_received:float = 0,
                      number_of_box_shipped:float = 0,
                      ship_id:Optional[int]=None,
                      date:Optional[datetime]=None) -> bool:

        if date is None:
            date = datetime.now()
        order_detail_fetch = self.db.get_orderdetail(order_id=order_id, inventory_id=inventory_id)
        if not order_detail_fetch:
            return False


        the_order_detail = order_detail_fetch[0]
        ship_id = the_order_detail.ship_id
        ship = self.get_shipments(ship_id)[0]
        ship.receiver = receiver_name
        self.db.edit_ship(ship)

        received_before = the_order_detail.numbers_of_box_received or 0
        shipped_before = the_order_detail.numbers_of_box_shipped or 0

        the_order_detail.numbers_of_box_received = received_before + number_of_box_received
        the_order_detail.numbers_of_box_shipped = shipped_before + number_of_box_shipped
        the_order_detail.actual_delivery_date = date
        if ship_id is not None:
            the_order_detail.ship_id = ship_id
        if not self.db.edit_orderdetail(the_order_detail):
            return False
        self._check_status_detail(the_order_detail.order_id, the_order_detail.inventory_id)
        self._check_status_order(order_id)
        return True

    def inspect_received_order(self,
                               order_id:int,
                               inventory_id:int,
                               approved: float,
                               rejected: float,
                               approver: str,
                               replace_rejected: float = None,
                               description: str = None) -> bool:
        order_detail_fetch = self.db.get_orderdetail(order_id=order_id, inventory_id=inventory_id)
        if not order_detail_fetch:
            return False
        the_order_detail = order_detail_fetch[0]
        approved_before = the_order_detail.numbers_of_box_approved or 0
        rejected_before = the_order_detail.numbers_of_box_rejected or 0
        if not replace_rejected:
            replace_rejected = 0
        if not approved:
            approved = 0
        if not rejected:
            rejected = 0

        if approved:
            the_order_detail.numbers_of_box_approved = approved_before + approved
        if replace_rejected:
            the_order_detail.numbers_of_box_rejected = rejected_before + rejected - replace_rejected
        the_order_detail.approver = approver
        if description:
            the_order_detail.description = description
        if not self.db.edit_orderdetail(the_order_detail):
            return False
        self._check_status_detail(the_order_detail.order_id, the_order_detail.inventory_id)
        self._check_status_order(order_id)
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



    def get_supplier_orders(self, supplier_id: int, status: Optional[str] = None) -> list[Order]:
        """Get all orders for a specific supplier"""
        return self.db.get_order(supplier_id=supplier_id, status=status)