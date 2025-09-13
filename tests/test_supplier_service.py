from datetime import datetime, timedelta
import pytest

from services.supplier_service import SupplierService
from models.cafe_managment_models import Supplier, Order, OrderDetail, Ship
from tests.conftest import in_memory_db


@pytest.fixture
def supplier_service(in_memory_db):
    """Fixture to provide a SupplierService instance"""
    return SupplierService(in_memory_db)


@pytest.fixture
def test_supplier(in_memory_db):
    """Fixture to create a test supplier"""
    return in_memory_db.add_supplier(
        name="Test Supplier",
        contact_channel="email",
        contact_address="test@supplier.com",
        load_time_hr=24
    )


@pytest.fixture
def test_inventory(in_memory_db):
    """Fixture to create test inventory items"""
    inv1 = in_memory_db.add_inventory(
        name="coffee beans",
        unit="kg",
        current_stock=10.0,
        current_price=50000.0
    )
    inv2 = in_memory_db.add_inventory(
        name="milk",
        unit="liter",
        current_stock=20.0,
        current_price=20000.0
    )
    return inv1, inv2


def test_create_order(supplier_service, test_supplier):
    """Test creating a new order"""
    result = supplier_service.create_order(
        supplier_id=test_supplier.id,
        buyer="John Doe",
        payer="Company Account",
        description="Test order creation"
    )

    assert result is True

    # Verify the order was created
    orders = supplier_service.db.get_order()
    assert len(orders) == 1
    assert orders[0].supplier_id == test_supplier.id
    assert orders[0].buyer == "john doe"  # Lowercase due to processing
    assert orders[0].status == "opened"


def test_get_open_orders(supplier_service, test_supplier):
    """Test retrieving open orders"""
    # Create multiple orders
    supplier_service.create_order(
        supplier_id=test_supplier.id,
        buyer="Buyer 1",
        payer="Payer 1"
    )
    supplier_service.create_order(
        supplier_id=test_supplier.id,
        buyer="Buyer 2",
        payer="Payer 2"
    )

    open_orders = supplier_service.get_open_orders()
    assert len(open_orders) == 2
    assert all(order.status == "opened" for order in open_orders)


def test_close_order(supplier_service, test_supplier):
    """Test closing an order"""
    # Create an order first
    supplier_service.create_order(
        supplier_id=test_supplier.id,
        buyer="Test Buyer",
        payer="Test Payer"
    )

    order = supplier_service.db.get_order()[0]
    result = supplier_service.close_order(order.id)

    assert result is True

    # Verify order is closed
    updated_order = supplier_service.db.get_order(id=order.id)[0]
    assert updated_order.status == "closed"


def test_add_item_to_order(supplier_service, test_supplier, test_inventory):
    """Test adding items to an order"""
    # Create an order first
    supplier_service.create_order(
        supplier_id=test_supplier.id,
        buyer="Test Buyer",
        payer="Test Payer"
    )

    order = supplier_service.db.get_order()[0]
    coffee_beans, milk = test_inventory

    # Add items to order
    result1 = supplier_service.add_item_to_order(
        order_id=order.id,
        inventory_id=coffee_beans.id,
        num_box_ordered=5.0,
        box_price=45000.0,
        box_amount=1.0
    )

    result2 = supplier_service.add_item_to_order(
        order_id=order.id,
        inventory_id=milk.id,
        num_box_ordered=10.0,
        box_price=18000.0,
        box_amount=1.0
    )

    assert result1 is True
    assert result2 is True

    # Verify order details were added
    order_details = supplier_service.get_order_details(order.id)
    assert len(order_details) == 2
    assert any(detail.inventory_id == coffee_beans.id for detail in order_details)
    assert any(detail.inventory_id == milk.id for detail in order_details)


def test_update_order_total_price(supplier_service, test_supplier, test_inventory):
    """Test updating order total price"""
    # Create order and add items
    supplier_service.create_order(
        supplier_id=test_supplier.id,
        buyer="Test Buyer",
        payer="Test Payer"
    )

    order = supplier_service.db.get_order()[0]
    coffee_beans, milk = test_inventory

    supplier_service.add_item_to_order(
        order_id=order.id,
        inventory_id=coffee_beans.id,
        num_box_ordered=2.0,
        box_price=50000.0,
        box_amount=1.0
    )

    supplier_service.add_item_to_order(
        order_id=order.id,
        inventory_id=milk.id,
        num_box_ordered=3.0,
        box_price=20000.0,
        box_amount=1.0
    )

    # Update total price
    result = supplier_service.update_order_total_price(order.id)

    assert result is True

    # Verify total price calculation
    updated_order = supplier_service.db.get_order(id=order.id)[0]
    expected_total = (2.0 * 50000.0) + (3.0 * 20000.0)
    assert updated_order.total_price == expected_total


def test_receive_order(supplier_service, test_supplier, test_inventory):
    """Test receiving an order"""
    # Create order and add item
    supplier_service.create_order(
        supplier_id=test_supplier.id,
        buyer="Test Buyer",
        payer="Test Payer"
    )

    order = supplier_service.db.get_order()[0]
    coffee_beans, _ = test_inventory

    supplier_service.add_item_to_order(
        order_id=order.id,
        inventory_id=coffee_beans.id,
        num_box_ordered=5.0,
        box_price=50000.0
    )

    # Receive the order
    result = supplier_service.receive_order(
        order_id=order.id,
        inventory_id=coffee_beans.id,
        receiver_name="Warehouse Staff",
        number_of_box_received=5.0
    )

    assert result is True

    # Verify order details were updated
    order_details = supplier_service.get_order_details(order.id)
    assert order_details[0].numbers_of_box_received == 5.0
    assert "warehouse staff" in order_details[0].receiver.lower()


def test_inspect_received_order(supplier_service, test_supplier, test_inventory):
    """Test inspecting a received order"""
    # Create order, add item, and receive it
    supplier_service.create_order(
        supplier_id=test_supplier.id,
        buyer="Test Buyer",
        payer="Test Payer"
    )

    order = supplier_service.db.get_order()[0]
    coffee_beans, _ = test_inventory

    supplier_service.add_item_to_order(
        order_id=order.id,
        inventory_id=coffee_beans.id,
        num_box_ordered=10.0,
        box_price=50000.0
    )

    supplier_service.receive_order(
        order_id=order.id,
        inventory_id=coffee_beans.id,
        receiver_name="Staff",
        number_of_box_received=10.0
    )

    # Inspect the received order
    result = supplier_service.inspect_received_order(
        order_id=order.id,
        inventory_id=coffee_beans.id,
        approved=8.0,
        rejected=2.0,
        replace_rejected=1.0
    )

    assert result is True

    # Verify inspection results
    order_details = supplier_service.get_order_details(order.id)
    assert order_details[0].numbers_of_box_approved == 8.0
    assert order_details[0].numbers_of_box_rejected == 1.0  # 2 rejected - 1 replaced = 1


def test_add_shipment(supplier_service):
    """Test adding a shipment"""
    shipment = supplier_service.add_shipment(
        shipper="Fast Shipping Co.",
        shipper_contact="contact@fastshipping.com",
        price=150000.0,
        receiver="Warehouse",
        payer="Company Account"
    )

    assert shipment is not None
    assert shipment.shipper == "fast shipping co."
    assert shipment.price == 150000.0


def test_get_shipments(supplier_service):
    """Test retrieving shipments"""
    # Add multiple shipments
    supplier_service.add_shipment(
        shipper="Shipper A",
        shipper_contact="contact@a.com",
        price=100000.0
    )

    supplier_service.add_shipment(
        shipper="Shipper B",
        shipper_contact="contact@b.com",
        price=200000.0
    )

    shipments = supplier_service.get_shipments()
    assert len(shipments) == 2
    assert any(shipment.shipper == "shipper a" for shipment in shipments)
    assert any(shipment.shipper == "shipper b" for shipment in shipments)


def test_add_supplier(supplier_service):
    """Test adding a new supplier"""
    result = supplier_service.add_a_supplier(
        name="New Supplier",
        contact_channel="phone",
        contact_address="+1234567890",
        load_time_hr=48
    )

    assert result is True

    # Verify supplier was added
    suppliers = supplier_service.db.get_supplier(name="new supplier")
    assert len(suppliers) == 1
    assert suppliers[0].contact_channel == "phone"
    assert suppliers[0].load_time_hr == 48


def test_get_suppliers(supplier_service, test_supplier):
    """Test retrieving suppliers"""
    suppliers = supplier_service.get_suppliers()
    assert len(suppliers) > 0
    assert any(supplier.name == "test supplier" for supplier in suppliers)


def test_update_supplier_lead_time(supplier_service, test_supplier):
    """Test updating supplier lead time"""
    result = supplier_service.update_supplier_lead_time(
        supplier_id=test_supplier.id,
        new_lead_time=72
    )

    assert result is True

    # Verify lead time was updated
    updated_supplier = supplier_service.db.get_supplier(id=test_supplier.id)[0]
    assert updated_supplier.load_time_hr == 72


def test_get_supplier_orders(supplier_service, test_supplier, in_memory_db):
    """Test retrieving orders for a specific supplier"""
    # Create orders for the test supplier
    supplier_service.create_order(
        supplier_id=test_supplier.id,
        buyer="Buyer 1",
        payer="Payer 1"
    )

    b = supplier_service.create_order(
        supplier_id=test_supplier.id,
        buyer="Buyer 2",
        payer="Payer 2"
    )

    c = in_memory_db.get_order()
    orders = supplier_service.get_supplier_orders(test_supplier.id)
    assert len(orders) == 2
    assert all(order.supplier_id == test_supplier.id for order in orders)


def test_order_status_flow(supplier_service, test_supplier, test_inventory):
    """Test the complete order status flow"""
    # Create order
    supplier_service.create_order(
        supplier_id=test_supplier.id,
        buyer="Test Buyer",
        payer="Test Payer"
    )

    order = supplier_service.db.get_order()[0]
    coffee_beans, _ = test_inventory

    # Add item
    supplier_service.add_item_to_order(
        order_id=order.id,
        inventory_id=coffee_beans.id,
        num_box_ordered=5.0,
        box_price=50000.0
    )

    # Initially should be "Opened"
    assert order.status == "opened"

    # Receive partial shipment
    supplier_service.receive_order(
        order_id=order.id,
        inventory_id=coffee_beans.id,
        receiver_name="Staff",
        number_of_box_received=3.0
    )

    # Should be "shortage" status after partial receipt
    order_details = supplier_service.get_order_details(order.id)
    assert order_details[0].status == "shortage"

    # Receive remaining items
    supplier_service.receive_order(
        order_id=order.id,
        inventory_id=coffee_beans.id,
        receiver_name="Staff",
        number_of_box_received=2.0
    )

    # Should be "received" status after full receipt
    order_details = supplier_service.get_order_details(order.id)
    assert order_details[0].status == "received"

    # Inspect and approve all items
    supplier_service.inspect_received_order(
        order_id=order.id,
        inventory_id=coffee_beans.id,
        approved=5.0,
        rejected=0.0,
        replace_rejected=0.0
    )

    # Should be "completed" status after approval
    order_details = supplier_service.get_order_details(order.id)
    assert order_details[0].status == "completed"


def test_receive_order_with_shipment(supplier_service, test_supplier, test_inventory):
    """Test receiving an order with shipment information"""
    # Create a shipment first
    shipment = supplier_service.add_shipment(
        shipper="Test Shipper",
        shipper_contact="test@shipper.com",
        price=100000.0
    )

    # Create order and add item
    supplier_service.create_order(
        supplier_id=test_supplier.id,
        buyer="Test Buyer",
        payer="Test Payer"
    )

    order = supplier_service.db.get_order()[0]
    coffee_beans, _ = test_inventory

    supplier_service.add_item_to_order(
        order_id=order.id,
        inventory_id=coffee_beans.id,
        num_box_ordered=5.0,
        box_price=50000.0
    )

    # Receive order with shipment ID
    result = supplier_service.receive_order(
        order_id=order.id,
        inventory_id=coffee_beans.id,
        receiver_name="Staff",
        number_of_box_received=5.0,
        ship_id=shipment.id
    )

    assert result is True

    # Verify shipment was linked
    order_details = supplier_service.get_order_details(order.id)
    assert order_details[0].ship_id == shipment.id


def test_order_with_discount(supplier_service, test_supplier, test_inventory):
    """Test order with discount applied"""
    supplier_service.create_order(
        supplier_id=test_supplier.id,
        buyer="Test Buyer",
        payer="Test Payer"
    )

    order = supplier_service.db.get_order()[0]
    coffee_beans, _ = test_inventory

    # Add item with discount
    supplier_service.add_item_to_order(
        order_id=order.id,
        inventory_id=coffee_beans.id,
        num_box_ordered=10.0,
        box_price=50000.0,
        overall_discount=5000.0  # 5000 discount per box
    )

    # Update total price to include discount
    supplier_service.update_order_total_price(order.id)

    updated_order = supplier_service.db.get_order(id=order.id)[0]
    expected_total = (10.0 * 50000.0) - 5000.0 # Price after discount
    assert updated_order.total_price == expected_total


def test_error_cases(supplier_service, test_supplier):
    """Test various error cases"""
    # Try to create order with non-existent supplier
    result = supplier_service.create_order(
        supplier_id=999,  # Non-existent ID
        buyer="Test",
        payer="Test"
    )
    assert result is False

    # Try to close non-existent order
    result = supplier_service.close_order(999)
    assert result is False

    # Try to get details of non-existent order
    details = supplier_service.get_order_details(999)
    assert len(details) == 0

    # Try to update total price of non-existent order
    result = supplier_service.update_order_total_price(999)
    assert result is False


def test_complex_shipment_with_rejection_and_replacement(supplier_service, test_supplier, test_inventory):
    """Test complex scenario with rejection, replacement shipments, and different receivers"""
    # Create order
    supplier_service.create_order(
        supplier_id=test_supplier.id,
        buyer="Test Buyer",
        payer="Test Payer"
    )

    order = supplier_service.db.get_order()[0]
    coffee_beans, _ = test_inventory

    # Add item to order
    supplier_service.add_item_to_order(
        order_id=order.id,
        inventory_id=coffee_beans.id,
        num_box_ordered=10.0,
        box_price=50000.0
    )

    # First shipment - receive 8 boxes with first receiver
    result1 = supplier_service.receive_order(
        order_id=order.id,
        inventory_id=coffee_beans.id,
        receiver_name="John Smith",  # First receiver
        number_of_box_received=8.0
    )
    assert result1 is True

    # Inspect first shipment - reject 2 boxes (6 approved, 2 rejected)
    result2 = supplier_service.inspect_received_order(
        order_id=order.id,
        inventory_id=coffee_beans.id,
        approved=6.0,
        rejected=2.0,
        replace_rejected=0.0
    )
    assert result2 is True

    # Check status after first inspection (should be shortage + rejected)
    order_details = supplier_service.get_order_details(order.id)
    assert order_details[0].numbers_of_box_received == 8.0
    assert order_details[0].numbers_of_box_approved == 6.0
    assert order_details[0].numbers_of_box_rejected == 2.0
    assert "john smith" in order_details[0].receiver.lower()

    # Second shipment - receive replacement boxes with different receiver
    result3 = supplier_service.receive_order(
        order_id=order.id,
        inventory_id=coffee_beans.id,
        receiver_name="Maria Garcia",  # Different receiver
        number_of_box_received=4.0  # 2 replacements + 2 extra
    )
    assert result3 is True

    # Inspect second shipment - approve all 4 boxes, replace the 2 rejected ones
    result4 = supplier_service.inspect_received_order(
        order_id=order.id,
        inventory_id=coffee_beans.id,
        approved=4.0,
        rejected=0.0,
        replace_rejected=2.0  # Replace the 2 previously rejected boxes
    )
    assert result4 is True

    # Final verification
    order_details = supplier_service.get_order_details(order.id)
    assert order_details[0].numbers_of_box_received == 12.0  # 8 + 4
    assert order_details[0].numbers_of_box_approved == 10.0  # 6 + 4
    assert order_details[0].numbers_of_box_rejected == 0.0  # 2 - 2 (replaced)

    # Verify both receivers are recorded
    receiver_info = order_details[0].receiver.lower()
    assert "john smith" in receiver_info
    assert "maria garcia" in receiver_info

    # Verify status is completed (all ordered items approved)
    assert order_details[0].status == "completed"


def test_add_items_to_existing_open_order(supplier_service, test_supplier, test_inventory):
    """Test adding additional items to an existing open order"""
    # Create initial order
    supplier_service.create_order(
        supplier_id=test_supplier.id,
        buyer="Test Buyer",
        payer="Test Payer"
    )

    order = supplier_service.db.get_order()[0]
    coffee_beans, milk = test_inventory

    # Add first item to order
    result1 = supplier_service.add_item_to_order(
        order_id=order.id,
        inventory_id=coffee_beans.id,
        num_box_ordered=5.0,
        box_price=50000.0,
        box_amount=1.0
    )
    assert result1 is True

    # Verify initial order details
    initial_details = supplier_service.get_order_details(order.id)
    assert len(initial_details) == 1
    assert initial_details[0].inventory_id == coffee_beans.id
    assert initial_details[0].boxes_ordered == 5.0

    # Get initial total price
    supplier_service.update_order_total_price(order.id)
    initial_order = supplier_service.db.get_order(id=order.id)[0]
    initial_total = initial_order.total_price

    # Add second item to the same order
    result2 = supplier_service.add_item_to_order(
        order_id=order.id,
        inventory_id=milk.id,
        num_box_ordered=8.0,
        box_price=20000.0,
        box_amount=1.0
    )
    assert result2 is True

    # Verify both items are in the order
    updated_details = supplier_service.get_order_details(order.id)
    assert len(updated_details) == 2
    assert any(detail.inventory_id == coffee_beans.id for detail in updated_details)
    assert any(detail.inventory_id == milk.id for detail in updated_details)

    # Update and verify total price increased
    supplier_service.update_order_total_price(order.id)
    updated_order = supplier_service.db.get_order(id=order.id)[0]
    expected_total = initial_total + (8.0 * 20000.0)
    assert updated_order.total_price == expected_total

    # Add more quantity to the first item (coffee beans)
    result3 = supplier_service.add_item_to_order(
        order_id=order.id,
        inventory_id=coffee_beans.id,
        num_box_ordered=3.0,  # Additional boxes
        box_price=50000.0,
        box_amount=1.0
    )
    assert result3 is True

    # Verify the coffee beans order was updated (not duplicated)
    final_details = supplier_service.get_order_details(order.id)
    coffee_details = [d for d in final_details if d.inventory_id == coffee_beans.id]
    assert len(coffee_details) == 1  # Should not create duplicate entry
    assert coffee_details[0].boxes_ordered == 8.0  # 5 + 3

    # Verify order is still open
    assert updated_order.status == "opened"