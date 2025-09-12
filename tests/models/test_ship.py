import pytest
from datetime import datetime
from models.dbhandler import DBHandler
from models.cafe_managment_models import Ship
from utils import crud_cycle_test


def test_ship_crud_cycle(in_memory_db: DBHandler):
    """Test complete CRUD cycle for Ship using the utility function"""
    # Test data
    create_kwargs = {
        'shipper': 'Test Shipper Company',
        'shipper_contact': 'test@shipper.com',
        'price': 45.75,
        'receiver': 'Test Receiver Name',
        'payer': 'Test Payer Company',
        'shipped_date': datetime(2024, 1, 15, 10, 30),
        'received_date': datetime(2024, 1, 16, 14, 0),
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
        lookup_fields=['shipper'],
        lookup_values=['Test Shipper Company']
    )


def test_add_ship_success(in_memory_db: DBHandler):
    """Test successfully adding a ship record"""
    # Now add ship
    shipped_date = datetime.now()
    received_date = datetime.now()
    ship = in_memory_db.add_ship(
        shipper="Test Shipper",
        shipper_contact="contact@test.com",
        price=25.50,
        receiver="Test Receiver",
        payer="Test Payer",
        shipped_date=shipped_date,
        received_date=received_date,
        description="Test shipment"
    )

    assert ship is not None
    assert ship.shipper == "test shipper"  # Should be lowercased
    assert ship.shipper_contact == "contact@test.com"
    assert ship.price == 25.50
    assert ship.receiver == "test receiver"
    assert ship.payer == "test payer"
    assert ship.shipped_date == shipped_date
    assert ship.received_date == received_date
    assert ship.description == "Test shipment"


def test_add_ship_minimal_data(in_memory_db: DBHandler):
    """Test adding ship with minimal required data"""
    ship = in_memory_db.add_ship(shipper="Minimal Shipper")

    assert ship is not None
    assert ship.shipper == "minimal shipper"
    assert ship.price is None
    assert ship.shipped_date is None
    assert ship.received_date is None


def test_get_ship_by_shipper(in_memory_db: DBHandler):
    """Test retrieving ships by shipper name"""
    in_memory_db.add_ship(shipper="Fast Shipping")
    in_memory_db.add_ship(shipper="Slow Shipping")
    in_memory_db.add_ship(shipper="Fast Shipping")  # Same shipper

    # Test case-insensitive search
    fast_ships = in_memory_db.get_ship(shipper="FAST SHIPPING")
    assert len(fast_ships) == 2
    assert all(ship.shipper == "fast shipping" for ship in fast_ships)

    slow_ships = in_memory_db.get_ship(shipper="slow shipping")
    assert len(slow_ships) == 1


def test_get_ship_by_date_range(in_memory_db: DBHandler):
    """Test retrieving ships by date range"""
    dates = [
        datetime(2024, 1, 1),
        datetime(2024, 1, 15),
        datetime(2024, 2, 1),
        datetime(2024, 2, 15)
    ]

    for i, date in enumerate(dates):
        in_memory_db.add_ship(shipper=f"Shipper {i}", shipped_date=date)

    # Get ships from January 2024
    jan_ships = in_memory_db.get_ship(
        from_date_shipped=datetime(2024, 1, 1),
        to_date_shipped=datetime(2024, 1, 31)
    )
    assert len(jan_ships) == 2

    # Get ships from February 2024
    feb_ships = in_memory_db.get_ship(
        from_date_shipped=datetime(2024, 2, 1),
        to_date_shipped=datetime(2024, 2, 28)
    )
    assert len(feb_ships) == 2


def test_get_ship_by_received_date_range(in_memory_db: DBHandler):
    """Test retrieving ships by received date range"""
    dates = [
        datetime(2024, 3, 1),
        datetime(2024, 3, 15),
        datetime(2024, 4, 1),
        datetime(2024, 4, 15)
    ]

    for i, date in enumerate(dates):
        in_memory_db.add_ship(shipper=f"Shipper {i}", received_date=date)

    # Get ships received in March 2024
    mar_ships = in_memory_db.get_ship(
        from_date_received=datetime(2024, 3, 1),
        to_date_received=datetime(2024, 3, 31)
    )
    assert len(mar_ships) == 2

    # Get ships received in April 2024
    apr_ships = in_memory_db.get_ship(
        from_date_received=datetime(2024, 4, 1),
        to_date_received=datetime(2024, 4, 30)
    )
    assert len(apr_ships) == 2


def test_get_ship_multiple_filters(in_memory_db: DBHandler):
    """Test retrieving ships with multiple filters"""
    # Add test ships
    in_memory_db.add_ship(
        shipper="Express Shipping",
        receiver="Warehouse A",
        payer="Company X",
        shipped_date=datetime(2024, 3, 10)
    )

    in_memory_db.add_ship(
        shipper="Express Shipping",
        receiver="Warehouse B",
        payer="Company Y",
        shipped_date=datetime(2024, 3, 15)
    )

    in_memory_db.add_ship(
        shipper="Standard Shipping",
        receiver="Warehouse A",
        payer="Company X",
        shipped_date=datetime(2024, 3, 20)
    )

    # Test combined filters
    filtered_ships = in_memory_db.get_ship(
        shipper="express shipping",
        receiver="warehouse a",
        payer="company x"
    )
    assert len(filtered_ships) == 1
    assert filtered_ships[0].shipper == "express shipping"
    assert filtered_ships[0].receiver == "warehouse a"
    assert filtered_ships[0].payer == "company x"


def test_get_ship_by_id(in_memory_db: DBHandler):
    """Test retrieving ship by ID"""
    ship1 = in_memory_db.add_ship(shipper="Ship 1")
    ship2 = in_memory_db.add_ship(shipper="Ship 2")

    assert ship1 is not None
    assert ship2 is not None

    # Get by ID
    result1 = in_memory_db.get_ship(id=ship1.id)
    assert len(result1) == 1
    assert result1[0].id == ship1.id
    assert result1[0].shipper == "ship 1"

    result2 = in_memory_db.get_ship(id=ship2.id)
    assert len(result2) == 1
    assert result2[0].id == ship2.id
    assert result2[0].shipper == "ship 2"


def test_edit_ship_success(in_memory_db: DBHandler):
    """Test successfully editing a ship record"""
    ship = in_memory_db.add_ship(
        shipper="Original Shipper",
        price=30.00,
        description="Original description"
    )
    assert ship is not None

    # Modify the ship object
    ship.shipper = "Updated Shipper"
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
    fake_ship = Ship(id=999, shipper="fake")  # Non-existent ship

    result = in_memory_db.edit_ship(fake_ship)
    assert result is None


def test_delete_ship_success(in_memory_db: DBHandler):
    """Test successfully deleting a ship record"""
    ship = in_memory_db.add_ship(shipper="Delete Test Shipper")
    assert ship is not None

    # Delete the ship
    delete_result = in_memory_db.delete_ship(ship)
    assert delete_result is True

    # Verify it's gone
    remaining_ships = in_memory_db.get_ship(id=ship.id)
    assert len(remaining_ships) == 0


def test_delete_ship_nonexistent(in_memory_db: DBHandler):
    """Test deleting a non-existent ship record"""
    fake_ship = Ship(id=999, shipper="fake")  # Non-existent ship

    delete_result = in_memory_db.delete_ship(fake_ship)
    assert delete_result is False


def test_get_ship_ordering(in_memory_db: DBHandler):
    """Test that ships are returned in correct order (most recent first)"""
    # Add ships with different dates
    dates = [
        datetime(2024, 1, 1),
        datetime(2024, 1, 3),
        datetime(2024, 1, 2)
    ]

    for i, date in enumerate(dates):
        in_memory_db.add_ship(shipper=f"Shipper {i}", shipped_date=date)

    # Get all ships - should be ordered by shipped_date descending
    all_ships = in_memory_db.get_ship()
    assert len(all_ships) == 3

    # Check ordering: most recent first
    assert all_ships[0].shipped_date == datetime(2024, 1, 3)
    assert all_ships[1].shipped_date == datetime(2024, 1, 2)
    assert all_ships[2].shipped_date == datetime(2024, 1, 1)


def test_get_ship_row_limit(in_memory_db: DBHandler):
    """Test limiting the number of returned ships"""
    # Add multiple ships
    for i in range(5):
        in_memory_db.add_ship(shipper=f"Shipper {i}")

    # Test different limits
    limited_2 = in_memory_db.get_ship(row_num=2)
    assert len(limited_2) == 2

    limited_3 = in_memory_db.get_ship(row_num=3)
    assert len(limited_3) == 3

    # Test getting all
    all_ships = in_memory_db.get_ship()
    assert len(all_ships) == 5


def test_ship_string_fields_lowercased(in_memory_db: DBHandler):
    """Test that string fields are properly lowercased and stripped"""
    ship = in_memory_db.add_ship(
        shipper="  TEST Shipper  ",
        receiver="  Test Receiver  ",
        payer="  Test Payer  ",
        shipper_contact="  contact@test.com  "
    )

    assert ship is not None
    assert ship.shipper == "test shipper"
    assert ship.receiver == "test receiver"
    assert ship.payer == "test payer"
    assert ship.shipper_contact == "  contact@test.com  "


def test_get_ship_by_shipper_contact(in_memory_db: DBHandler):
    """Test retrieving ships by shipper contact"""
    in_memory_db.add_ship(shipper="Shipper A", shipper_contact="contact@a.com")
    in_memory_db.add_ship(shipper="Shipper B", shipper_contact="contact@b.com")
    in_memory_db.add_ship(shipper="Shipper C", shipper_contact="contact@a.com")  # Same contact

    # Test getting by shipper contact
    contact_a_ships = in_memory_db.get_ship(shipper_contact="contact@a.com")
    assert len(contact_a_ships) == 2
    assert all(ship.shipper_contact == "contact@a.com" for ship in contact_a_ships)

    contact_b_ships = in_memory_db.get_ship(shipper_contact="contact@b.com")
    assert len(contact_b_ships) == 1
    assert contact_b_ships[0].shipper_contact == "contact@b.com"