from datetime import datetime
from models.dbhandler import DBHandler
from models.cafe_managment_models import Ship
from utils import crud_cycle_test


def test_ship_crud_cycle(in_memory_db: DBHandler):
    """Test complete CRUD cycle for Ship using the utility function"""
    # First create prerequisite data
    supplier = in_memory_db.add_supplier(
        name="CRUD Test Supplier",
        contact_channel="phone",
        contact_address="123-456-7890"
    )
    assert supplier is not None

    order = in_memory_db.add_order(
        supplier_id=supplier.id,
        buyer="crud_test_buyer",
        payer="crud_test_payer"
    )
    assert order is not None

    # Test data
    create_kwargs = {
        'order_id': order.id,
        'shipper': 'Test Shipper Company',
        'price': 45.75,
        'receiver': 'Test Receiver Name',
        'payer': 'Test Payer Company',
        'date': datetime(2024, 1, 15, 10, 30),
        'description': 'Test shipment description'
    }

    update_kwargs = {
        'price': 50.25,
        'shipper': 'Updated Shipper',
        'description': 'Updated description'
    }

    # Run CRUD cycle test
    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=Ship,
        create_kwargs=create_kwargs,
        update_kwargs=update_kwargs,
        lookup_fields=['order_id', 'shipper'],
        lookup_values=[order.id, 'Test Shipper Company']
    )


def test_add_ship_success(in_memory_db: DBHandler):
    """Test successfully adding a ship record"""
    # First create a supplier and order
    supplier = in_memory_db.add_supplier(
        name="Test Supplier",
        contact_channel="email",
        contact_address="supplier@test.com"
    )
    assert supplier is not None

    order = in_memory_db.add_order(
        supplier_id=supplier.id,
        buyer="test buyer",
        payer="test payer"
    )
    assert order is not None

    # Now add ship
    ship_date = datetime.now()
    ship = in_memory_db.add_ship(
        order_id=order.id,
        shipper="Test Shipper",
        price=25.50,
        receiver="Test Receiver",
        payer="Test Payer",
        date=ship_date,
        description="Test shipment"
    )

    assert ship is not None
    assert ship.order_id == order.id
    assert ship.shipper == "test shipper"  # Should be lowercased
    assert ship.price == 25.50
    assert ship.receiver == "test receiver"
    assert ship.payer == "test payer"
    assert ship.date == ship_date
    assert ship.description == "Test shipment"


def test_add_ship_nonexistent_order(in_memory_db: DBHandler):
    """Test adding ship with non-existent order ID"""
    ship = in_memory_db.add_ship(
        order_id=999,  # Non-existent order ID
        shipper="Test Shipper"
    )

    assert ship is None


def test_add_ship_minimal_data(in_memory_db: DBHandler):
    """Test adding ship with minimal required data"""
    # Create prerequisite data
    supplier = in_memory_db.add_supplier(name="Minimal Supplier")
    assert supplier is not None

    order = in_memory_db.add_order(supplier_id=supplier.id, buyer="minimal")
    assert order is not None

    ship = in_memory_db.add_ship(order_id=order.id)

    assert ship is not None
    assert ship.order_id == order.id
    assert ship.shipper is None
    assert ship.price is None
    assert ship.date is not None  # Should be auto-set to current datetime


def test_get_ship_by_order_id(in_memory_db: DBHandler):
    """Test retrieving ships by order ID"""
    # Setup test data
    supplier = in_memory_db.add_supplier(name="Filter Supplier")
    order1 = in_memory_db.add_order(supplier_id=supplier.id, buyer="order1")
    order2 = in_memory_db.add_order(supplier_id=supplier.id, buyer="order2")

    # Add ships for different orders
    ship1 = in_memory_db.add_ship(order_id=order1.id, shipper="Shipper A")
    ship2 = in_memory_db.add_ship(order_id=order2.id, shipper="Shipper B")
    ship3 = in_memory_db.add_ship(order_id=order1.id, shipper="Shipper C")  # Same order as ship1

    assert ship1 is not None
    assert ship2 is not None
    assert ship3 is not None

    # Get ships for order1
    order1_ships = in_memory_db.get_ship(order_id=order1.id)
    assert len(order1_ships) == 2
    assert all(ship.order_id == order1.id for ship in order1_ships)

    # Get ships for order2
    order2_ships = in_memory_db.get_ship(order_id=order2.id)
    assert len(order2_ships) == 1
    assert order2_ships[0].order_id == order2.id


def test_get_ship_by_shipper(in_memory_db: DBHandler):
    """Test retrieving ships by shipper name"""
    supplier = in_memory_db.add_supplier(name="Shipper Test Supplier")
    order = in_memory_db.add_order(supplier_id=supplier.id, buyer="shipper_test")

    in_memory_db.add_ship(order_id=order.id, shipper="Fast Shipping")
    in_memory_db.add_ship(order_id=order.id, shipper="Slow Shipping")
    in_memory_db.add_ship(order_id=order.id, shipper="Fast Shipping")  # Same shipper

    # Test case-insensitive search
    fast_ships = in_memory_db.get_ship(shipper="FAST SHIPPING")
    assert len(fast_ships) == 2
    assert all(ship.shipper == "fast shipping" for ship in fast_ships)

    slow_ships = in_memory_db.get_ship(shipper="slow shipping")
    assert len(slow_ships) == 1


def test_get_ship_by_date_range(in_memory_db: DBHandler):
    """Test retrieving ships by date range"""
    supplier = in_memory_db.add_supplier(name="Date Test Supplier")
    order = in_memory_db.add_order(supplier_id=supplier.id, buyer="date_test")

    dates = [
        datetime(2024, 1, 1),
        datetime(2024, 1, 15),
        datetime(2024, 2, 1),
        datetime(2024, 2, 15)
    ]

    for i, date in enumerate(dates):
        in_memory_db.add_ship(order_id=order.id, shipper=f"Shipper {i}", date=date)

    # Get ships from January 2024
    jan_ships = in_memory_db.get_ship(
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 1, 31)
    )
    assert len(jan_ships) == 2

    # Get ships from February 2024
    feb_ships = in_memory_db.get_ship(
        from_date=datetime(2024, 2, 1),
        to_date=datetime(2024, 2, 28)
    )
    assert len(feb_ships) == 2


def test_get_ship_multiple_filters(in_memory_db: DBHandler):
    """Test retrieving ships with multiple filters"""
    supplier = in_memory_db.add_supplier(name="Multi Filter Supplier")
    order = in_memory_db.add_order(supplier_id=supplier.id, buyer="multi_test")

    # Add test ships
    in_memory_db.add_ship(
        order_id=order.id,
        shipper="Express Shipping",
        receiver="Warehouse A",
        payer="Company X",
        date=datetime(2024, 3, 10)
    )

    in_memory_db.add_ship(
        order_id=order.id,
        shipper="Express Shipping",
        receiver="Warehouse B",
        payer="Company Y",
        date=datetime(2024, 3, 15)
    )

    in_memory_db.add_ship(
        order_id=order.id,
        shipper="Standard Shipping",
        receiver="Warehouse A",
        payer="Company X",
        date=datetime(2024, 3, 20)
    )
    #
    all = in_memory_db.get_ship()
    a = []
    for one in all:
        a.append(one.shipper)
    # Test combined filters
    filtered_ships = in_memory_db.get_ship(
        shipper="express shipping",
        receiver="warehouse a",
        payer="company x"
    )
    assert len(filtered_ships) == 1
    assert filtered_ships[0].shipper == "express shipping"
    assert filtered_ships[0].receiver == "warehouse a"


def test_edit_ship_success(in_memory_db: DBHandler):
    """Test successfully editing a ship record"""
    supplier = in_memory_db.add_supplier(name="Edit Test Supplier")
    order = in_memory_db.add_order(supplier_id=supplier.id, buyer="edit_test")

    ship = in_memory_db.add_ship(
        order_id=order.id,
        shipper="Original Shipper",
        price=30.00,
        description="Original description"
    )
    assert ship is not None

    # Modify the ship object
    ship.shipper = "Updated Shipper".lower().strip()
    ship.price = 35.50
    ship.description = "Updated description"

    # Edit the ship
    updated_ship = in_memory_db.edit_ship(ship)
    assert updated_ship is not None
    assert updated_ship.shipper == "updated shipper"
    assert updated_ship.price == 35.50
    assert updated_ship.description == "Updated description"
    assert updated_ship.id == ship.id  # ID should remain the same


def test_edit_ship_nonexistent(in_memory_db: DBHandler):
    """Test editing a non-existent ship record"""
    fake_ship = Ship(id=999, order_id=999)  # Non-existent ship

    result = in_memory_db.edit_ship(fake_ship)
    assert result is None


def test_delete_ship_success(in_memory_db: DBHandler):
    """Test successfully deleting a ship record"""
    supplier = in_memory_db.add_supplier(name="Delete Test Supplier")
    order = in_memory_db.add_order(supplier_id=supplier.id, buyer="delete_test")

    ship = in_memory_db.add_ship(
        order_id=order.id,
        shipper="Delete Test Shipper"
    )
    assert ship is not None

    # Delete the ship
    delete_result = in_memory_db.delete_ship(ship)
    assert delete_result is True

    # Verify it's gone
    remaining_ships = in_memory_db.get_ship(order_id=order.id)
    assert len(remaining_ships) == 0


def test_delete_ship_nonexistent(in_memory_db: DBHandler):
    """Test deleting a non-existent ship record"""
    fake_ship = Ship(id=999, order_id=999)  # Non-existent ship

    delete_result = in_memory_db.delete_ship(fake_ship)
    assert delete_result is False


def test_get_ship_ordering(in_memory_db: DBHandler):
    """Test that ships are returned in correct order (most recent first)"""
    supplier = in_memory_db.add_supplier(name="Order Test Supplier")
    order = in_memory_db.add_order(supplier_id=supplier.id, buyer="order_test")

    # Add ships with different dates
    dates = [
        datetime(2024, 1, 1),
        datetime(2024, 1, 3),
        datetime(2024, 1, 2)
    ]

    for i, date in enumerate(dates):
        in_memory_db.add_ship(order_id=order.id, shipper=f"Shipper {i}", date=date)

    # Get all ships - should be ordered by date descending
    all_ships = in_memory_db.get_ship(order_id=order.id)
    assert len(all_ships) == 3

    # Check ordering: most recent first
    assert all_ships[0].date == datetime(2024, 1, 3)
    assert all_ships[1].date == datetime(2024, 1, 2)
    assert all_ships[2].date == datetime(2024, 1, 1)


def test_get_ship_row_limit(in_memory_db: DBHandler):
    """Test limiting the number of returned ships"""
    supplier = in_memory_db.add_supplier(name="Limit Test Supplier")
    order = in_memory_db.add_order(supplier_id=supplier.id, buyer="limit_test")

    # Add multiple ships
    for i in range(5):
        in_memory_db.add_ship(order_id=order.id, shipper=f"Shipper {i}")

    # Test different limits
    limited_2 = in_memory_db.get_ship(order_id=order.id, row_num=2)
    assert len(limited_2) == 2

    limited_3 = in_memory_db.get_ship(order_id=order.id, row_num=3)
    assert len(limited_3) == 3

    # Test getting all
    all_ships = in_memory_db.get_ship(order_id=order.id)
    assert len(all_ships) == 5