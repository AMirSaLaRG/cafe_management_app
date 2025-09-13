import pytest
from datetime import datetime
from models.cafe_managment_models import OrderDetail, Order, Ship, Inventory
from utils import crud_cycle_test


@pytest.fixture
def setup_test_data(in_memory_db):
    """Setup required test data for order detail tests"""
    # Create a supplier first
    supplier = in_memory_db.add_supplier(
        name='Test Supplier',
        load_time_hr=24,
        contact_channel='email',
        contact_address='supplier@test.com'
    )
    assert supplier is not None

    # Create an order
    order = in_memory_db.add_order(
        supplier_id=supplier.id,
        date=datetime.now(),
        buyer='test_buyer',
        payer='test_payer',
        real_load_time_hr=48,
        total_price=100.0,
        status='ordered',
        description='Test order'
    )
    assert order is not None

    # Create a ship
    ship = in_memory_db.add_ship(
        shipper='Test Shipper',
        shipper_contact='shipper@test.com',
        price=20.0,
        receiver='test_receiver',
        payer='test_payer',
        shipped_date=datetime.now(),
        received_date=datetime.now(),
        description='Test shipment'
    )
    assert ship is not None

    # Create an inventory item
    inventory = in_memory_db.add_inventory(
        name='Test Coffee Beans',
        unit='kg',
        current_stock=10.0,
        current_price=15.0,
        current_supplier=supplier.id,
        daily_usage=1.0,
        safety_stock=5.0,
        category='coffee',
        price_per_unit=15.0
    )
    assert inventory is not None

    return {
        'order_id': order.id,
        'ship_id': ship.id,
        'inventory_id': inventory.id,
        'order': order,
        'ship': ship,
        'inventory': inventory,
        'supplier': supplier
    }


def test_orderdetail_crud_cycle(in_memory_db, setup_test_data):
    """Test complete CRUD cycle for OrderDetail model"""

    # Test data
    create_kwargs = {
        'inventory_id': setup_test_data['inventory_id'],
        'order_id': setup_test_data['order_id'],
        'ship_id': setup_test_data['ship_id'],
        'box_amount': 1.0,
        'box_price': 15.0,
        'overall_discount': 1.0,
        'boxes_ordered': 5.0,
        'numbers_of_box_shipped': 5.0,
        'numbers_of_box_received': 5.0,
        'numbers_of_box_approved': 4.5,
        'numbers_of_box_rejected': 0.5,
        'expected_delivery_date': datetime.now(),
        'actual_delivery_date': datetime.now(),
        'description': 'Test order detail'
    }

    update_kwargs = {
        'box_amount': 1.5,
        'box_price': 16.0,
        'overall_discount': 2.0,
        'boxes_ordered': 6.0,
        'numbers_of_box_shipped': 6.0,
        'numbers_of_box_received': 5.5,
        'numbers_of_box_approved': 5.0,
        'numbers_of_box_rejected': 0.5,
        'expected_delivery_date': datetime.now(),
        'actual_delivery_date': datetime.now(),
        'description': 'Updated order detail'
    }

    # Run CRUD cycle test - OrderDetail uses simple id primary key
    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=OrderDetail,
        create_kwargs=create_kwargs,
        update_kwargs=update_kwargs,
        lookup_fields=['id'],  # Simple id lookup
        lookup_values=None  # Will be set by the created object
    )


def test_orderdetail_get_methods(in_memory_db, setup_test_data):
    """Test various get_orderdetail filtering options"""

    # Create test order details
    detail1 = in_memory_db.add_orderdetail(
        inventory_id=setup_test_data['inventory_id'],
        order_id=setup_test_data['order_id'],
        ship_id=setup_test_data['ship_id'],
        boxes_ordered=5.0,
        numbers_of_box_shipped=5.0,
        numbers_of_box_received=5.0,
        description='First order detail'
    )
    assert detail1 is not None

    # Create another order for different filtering
    order2 = in_memory_db.add_order(
        supplier_id=setup_test_data['supplier'].id,
        date=datetime.now(),
        buyer='test_buyer2',
        status='shipped'
    )
    detail2 = in_memory_db.add_orderdetail(
        inventory_id=setup_test_data['inventory_id'],
        order_id=order2.id,
        boxes_ordered=3.0,
        numbers_of_box_shipped=3.0,
        numbers_of_box_received=2.5,
        numbers_of_box_rejected=0.5,
        description='Second order detail with rejection'
    )
    assert detail2 is not None

    # Test get by order_id
    result = in_memory_db.get_orderdetail(order_id=setup_test_data['order_id'])
    assert len(result) == 1
    assert all(detail.order_id == setup_test_data['order_id'] for detail in result)

    # Test get by inventory_id
    result = in_memory_db.get_orderdetail(inventory_id=setup_test_data['inventory_id'])
    assert len(result) == 2
    assert all(detail.inventory_id == setup_test_data['inventory_id'] for detail in result)

    # Test get by ship_id
    result = in_memory_db.get_orderdetail(ship_id=setup_test_data['ship_id'])
    assert len(result) == 1
    assert result[0].ship_id == setup_test_data['ship_id']

    # Test get by id
    result = in_memory_db.get_orderdetail(id=detail1.id)
    assert len(result) == 1
    assert result[0].id == detail1.id

    # Test has_reject filter
    result = in_memory_db.get_orderdetail(has_reject=True)
    assert len(result) >= 1
    assert any(detail.numbers_of_box_rejected is not None and detail.numbers_of_box_rejected > 0
               for detail in result)

    # Test row_num limit
    result = in_memory_db.get_orderdetail(row_num=1)
    assert len(result) == 1


def test_orderdetail_validation(in_memory_db, setup_test_data):
    """Test order detail validation rules"""

    # Test negative box_amount
    result = in_memory_db.add_orderdetail(
        inventory_id=setup_test_data['inventory_id'],
        order_id=setup_test_data['order_id'],
        box_amount=-1.0,  # Invalid negative value
        boxes_ordered=5.0
    )
    assert result is None

    # Test negative box_price
    result = in_memory_db.add_orderdetail(
        inventory_id=setup_test_data['inventory_id'],
        order_id=setup_test_data['order_id'],
        box_price=-15.0,  # Invalid negative value
        boxes_ordered=5.0
    )
    assert result is None

    # Test negative box_discount
    result = in_memory_db.add_orderdetail(
        inventory_id=setup_test_data['inventory_id'],
        order_id=setup_test_data['order_id'],
        overall_discount=-1.0,  # Invalid negative value
        boxes_ordered=5.0
    )
    assert result is None

    # Test negative boxes_ordered
    result = in_memory_db.add_orderdetail(
        inventory_id=setup_test_data['inventory_id'],
        order_id=setup_test_data['order_id'],
        boxes_ordered=-5.0  # Invalid negative value
    )
    assert result is None

    # Test valid values
    result = in_memory_db.add_orderdetail(
        inventory_id=setup_test_data['inventory_id'],
        order_id=setup_test_data['order_id'],
        boxes_ordered=5.0,  # Valid value
        box_price=15.0,     # Valid value
        overall_discount=1.0    # Valid value
    )
    assert result is not None


def test_orderdetail_foreign_key_validation(in_memory_db, setup_test_data):
    """Test order detail foreign key validation"""

    # Test non-existent inventory_id
    result = in_memory_db.add_orderdetail(
        inventory_id=9999,  # Non-existent inventory
        order_id=setup_test_data['order_id'],
        boxes_ordered=5.0
    )
    assert result is None

    # Test non-existent order_id
    result = in_memory_db.add_orderdetail(
        inventory_id=setup_test_data['inventory_id'],
        order_id=9999,  # Non-existent order
        boxes_ordered=5.0
    )
    assert result is None

    # Test non-existent ship_id
    result = in_memory_db.add_orderdetail(
        inventory_id=setup_test_data['inventory_id'],
        order_id=setup_test_data['order_id'],
        ship_id=9999,  # Non-existent ship
        boxes_ordered=5.0
    )
    assert result is None

    # Test valid foreign keys
    result = in_memory_db.add_orderdetail(
        inventory_id=setup_test_data['inventory_id'],
        order_id=setup_test_data['order_id'],
        ship_id=setup_test_data['ship_id'],
        boxes_ordered=5.0
    )
    assert result is not None


def test_orderdetail_simple_key_operations(in_memory_db, setup_test_data):
    """Test operations with simple primary key"""

    # Create an order detail
    detail = in_memory_db.add_orderdetail(
        inventory_id=setup_test_data['inventory_id'],
        order_id=setup_test_data['order_id'],
        boxes_ordered=5.0,
        numbers_of_box_shipped=5.0,
        numbers_of_box_received=5.0
    )
    assert detail is not None

    # Test edit with simple key
    detail.boxes_ordered = 6.0
    detail.numbers_of_box_received = 5.5
    updated = in_memory_db.edit_orderdetail(detail)
    assert updated is not None
    assert updated.boxes_ordered == 6.0
    assert updated.numbers_of_box_received == 5.5

    # Test delete with simple key
    result = in_memory_db.delete_orderdetail(detail)
    assert result is True

    # Verify deletion
    result = in_memory_db.get_orderdetail(id=detail.id)
    assert len(result) == 0


def test_orderdetail_delete_nonexistent(in_memory_db):
    """Test deleting non-existent order detail record"""

    # Create a mock order detail object with non-existent id
    class MockOrderDetail:
        id = 999999
        inventory_id = 9999
        order_id = 9999

    result = in_memory_db.delete_orderdetail(MockOrderDetail())
    assert result is False  # Should return False for non-existent order detail


def test_orderdetail_edit_nonexistent(in_memory_db):
    """Test editing non-existent order detail record"""

    # Create a mock order detail object with non-existent id
    class MockOrderDetail:
        id = 99999
        inventory_id = 9999
        order_id = 9999
        boxes_ordered = 5.0

    result = in_memory_db.edit_orderdetail(MockOrderDetail())
    assert result is None  # Should return None for non-existent order detail


def test_orderdetail_without_optional_fields(in_memory_db, setup_test_data):
    """Test order detail creation without optional fields"""

    # Should allow None for optional fields
    detail = in_memory_db.add_orderdetail(
        inventory_id=setup_test_data['inventory_id'],
        order_id=setup_test_data['order_id'],
        boxes_ordered=5.0,
        # ship_id, box_amount, box_price, etc. are optional
    )
    assert detail is not None
    assert detail.ship_id is None
    assert detail.box_amount is None
    assert detail.box_price is None


def test_orderdetail_order_relationship(in_memory_db, setup_test_data):
    """Test that order details are properly linked to orders"""

    # Create an order detail
    detail = in_memory_db.add_orderdetail(
        inventory_id=setup_test_data['inventory_id'],
        order_id=setup_test_data['order_id'],
        boxes_ordered=5.0
    )
    assert detail is not None

    # Verify the relationship
    order = in_memory_db.get_order(id=setup_test_data['order_id'])
    assert len(order) == 1
    assert order[0].id == setup_test_data['order_id']


def test_orderdetail_inventory_relationship(in_memory_db, setup_test_data):
    """Test that order details are properly linked to inventory items"""

    # Create an order detail
    detail = in_memory_db.add_orderdetail(
        inventory_id=setup_test_data['inventory_id'],
        order_id=setup_test_data['order_id'],
        boxes_ordered=5.0
    )
    assert detail is not None

    # Verify the relationship
    inventory = in_memory_db.get_inventory(id=setup_test_data['inventory_id'])
    assert len(inventory) == 1
    assert inventory[0].id == setup_test_data['inventory_id']


def test_orderdetail_ship_relationship(in_memory_db, setup_test_data):
    """Test that order details are properly linked to ships"""

    # Create an order detail with ship
    detail = in_memory_db.add_orderdetail(
        inventory_id=setup_test_data['inventory_id'],
        order_id=setup_test_data['order_id'],
        ship_id=setup_test_data['ship_id'],
        boxes_ordered=5.0
    )
    assert detail is not None

    # Verify the relationship
    ship = in_memory_db.get_ship(id=setup_test_data['ship_id'])
    assert len(ship) == 1
    assert ship[0].id == setup_test_data['ship_id']