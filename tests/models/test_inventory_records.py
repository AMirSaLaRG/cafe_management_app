import logging
from datetime import datetime, timedelta

from tests.utils import crud_cycle_test
from models.cafe_managment_models import InventoryStockRecord

def test_inventory_records_curd_cycle(in_memory_db):
    """Test full CRUD cycle for Menu using  exact utility function"""
    inventory_item = in_memory_db.add_inventory(
        name="Test Item",
        unit="kg",
        current_stock=100,
        price_per_unit=10.0
    )
    assert inventory_item is not None
    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=InventoryStockRecord,
        create_kwargs={
            "inventory_id": inventory_item.id,
            "change_amount": -101.1,
            "auto_calculated_amount":130,
            "manual_report":100,
            "date":datetime.now(),
            "description":"kheyli ajibe"

        },
        update_kwargs={
            "manual_report":50,
            "date":datetime.now(),
            "description":"kheyli ajibe - 2vommn bar eshtebahe mohasebati"
        },
        lookup_fields=['inventory_id'],
        lookup_values=[inventory_item.id]


    )

def test_inventorystockrecord_crud_cycle(in_memory_db):
    """Test happy path using crud_cycle_test"""
    inventory_item = in_memory_db.add_inventory(
        name="Test Item",
        unit="kg",
        current_stock=100,
        price_per_unit=10.0
    )
    assert inventory_item is not None
    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=InventoryStockRecord,
        create_kwargs={
            "inventory_id": 1,
            "change_amount": -10.5,
            "description": "Initial record"
        },
        update_kwargs={
            "change_amount": -15.2,
            "description": "Updated record"
        },
        lookup_fields=['inventory_id'],
        lookup_values=[1]
    )


def test_inventory_records_date_range_filtering(in_memory_db):
    """Test adding multiple records and filtering by date range"""
    # Create test inventory item
    inventory_item = in_memory_db.add_inventory(
        name="Date Range Test Item",
        unit="kg",
        current_stock=100,
        price_per_unit=5.0
    )
    assert inventory_item is not None

    # Add 10 records with dates spanning 30 days (days 0, 3, 6, 9, 12, 15, 18, 21, 24, 27)
    base_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=15)
    for i in range(10):
        record_date = base_date + timedelta(days=i*3)
        in_memory_db.add_inventorystockrecord(
            inventory_id=inventory_item.id,
            change_amount=-10 + i*5,
            date=record_date,
            description=f"Test record {i+1}"
        )

    # Define our date range (should catch records for days 9,12,15,18 - 4 records)
    from_date = base_date + timedelta(days=9)
    to_date = base_date + timedelta(days=18)  # Changed from 21 to 18 to get exactly 4 records

    # Get records in date range
    records = in_memory_db.get_inventorystockrecord(
        inventory_id=inventory_item.id,
        from_date=from_date,
        to_date=to_date
    )

    # Debug output to see what dates we actually got
    for i, record in enumerate(records):
        logging.info(f"Record {i+1}: {record.date}")

    # Verify we got the expected records
    assert len(records) == 4, f"Expected 4 records, got {len(records)}"
    for record in records:
        assert from_date <= record.date <= to_date

    # Verify ordering is descending (newest first)
    for i in range(len(records)-1):
        assert records[i].date >= records[i+1].date


def test_inventory_records_get_all_with_date_range(in_memory_db):
    """Test getting all records within date range with last=False"""
    # Create test inventory item
    inventory_item = in_memory_db.add_inventory(
        name="Date Range Test Item",
        unit="kg",
        current_stock=100,
        price_per_unit=5.0
    )
    assert inventory_item is not None

    # Create test records across 30 days (every 3 days)
    base_date = datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    ) - timedelta(days=15)

    test_records = []
    for i in range(10):  # Days 0, 3, 6, 9, 12, 15, 18, 21, 24, 27
        record_date = base_date + timedelta(days=i * 3)
        record = in_memory_db.add_inventorystockrecord(
            inventory_id=inventory_item.id,
            change_amount=10 + i * 5,
            date=record_date,
            description=f"Record day {i * 3}"
        )
        test_records.append(record)

    # Define date range covering days 6-18 (should get 5 records)
    from_date = base_date + timedelta(days=6)
    to_date = base_date + timedelta(days=18)

    # Test last=False with date range
    records = in_memory_db.get_inventorystockrecord(
        inventory_id=inventory_item.id,
        from_date=from_date,
        to_date=to_date
    )

    # Verify results
    assert len(records) == 5, f"Expected 5 records, got {len(records)}"

    # Check all returned records are within date range
    for record in records:
        assert from_date <= record.date <= to_date

    # Verify we got the exact expected records (days 6,9,12,15,18)
    expected_days = {6, 9, 12, 15, 18}
    actual_days = {(r.date - base_date).days for r in records}
    assert actual_days == expected_days

    # Verify descending order (newest first)
    assert all(
        records[i].date >= records[i + 1].date
        for i in range(len(records) - 1)
    )

    # Verify all records exist in our test data
    assert all(r.id in {tr.id for tr in test_records} for r in records)

def test_inventory_records_get_all_records(in_memory_db):
    """Test getting all records without date range filtering"""
    # Create test inventory item
    inventory_item = in_memory_db.add_inventory(
        name="All Records Test Item",
        unit="kg",
        current_stock=100,
        price_per_unit=5.0
    )
    assert inventory_item is not None

    # Create test records across 30 days (every 3 days)
    base_date = datetime.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    ) - timedelta(days=15)

    test_records = []
    for i in range(10):  # Days 0, 3, 6, 9, 12, 15, 18, 21, 24, 27
        record_date = base_date + timedelta(days=i * 3)
        record = in_memory_db.add_inventorystockrecord(
            inventory_id=inventory_item.id,
            change_amount=10 + i * 5,
            date=record_date,
            description=f"Record day {i * 3}"
        )
        test_records.append(record)

    # Test last=False without date range
    records = in_memory_db.get_inventorystockrecord(
        inventory_id=inventory_item.id,
    )

    # Verify results
    assert len(records) == 10, f"Expected all 10 records, got {len(records)}"

    # Verify we got all the test records
    assert {r.id for r in records} == {tr.id for tr in test_records}

    # Verify descending order (newest first)
    assert all(
        records[i].date >= records[i + 1].date
        for i in range(len(records) - 1)
    )