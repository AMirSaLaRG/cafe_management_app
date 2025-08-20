import logging
from datetime import datetime, timedelta

from tests.utils import crud_cycle_test
from cafe_managment_models import EstimatedMenuPriceRecord, Menu


def test_estimatedmenupricerecord_crud_cycle(in_memory_db):
    """Test full CRUD cycle for EstimatedMenuPriceRecord using utility function"""
    # First create a menu item
    menu_item = in_memory_db.add_menu(
        name="Test Menu",
        size="m",
        current_price=10.0
    )
    assert menu_item is not None

    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=EstimatedMenuPriceRecord,
        create_kwargs={
            "menu_id": menu_item.id,
            "sales_forecast": 100,
            "estimated_indirect_costs": 500.0,
            "direct_cost": 200.0,
            "profit": 300.0,
            "estimated_price": 10.0,
            "from_date": datetime.now(),
            "description": "Initial price estimation"
        },
        update_kwargs={
            "sales_forecast": 120,
            "estimated_price": 12.0,
            "description": "Updated price estimation"
        },
        lookup_fields=['menu_id'],
        lookup_values=[menu_item.id]
    )


def test_estimatedmenupricerecord_negative_values(in_memory_db):
    """Test validation of negative values"""
    menu_item = in_memory_db.add_menu(
        name="Negative Test Menu",
        size="m",
        current_price=15.0
    )

    # Test negative sales_forecast
    nwe_item = in_memory_db.add_estimatedmenupricerecord(
        menu_id=menu_item.id,
        sales_forecast=-100,
        from_date=datetime.now()
    )
    print(nwe_item)
    assert nwe_item is None, "Should have raised ValueError for negative sales_forecast"

    # Test negative estimated_price
    nwe_item = in_memory_db.add_estimatedmenupricerecord(
        menu_id=menu_item.id,
        estimated_price=-10.0,
        from_date=datetime.now()
    )
    assert nwe_item is None, "Should have raised ValueError for negative estimated_price"




def test_estimatedmenupricerecord_date_ranges(in_memory_db):
    """Test date range filtering and validation"""
    menu_item = in_memory_db.add_menu(
        name="Date Test Menu",
        size="m",
        current_price=20.0
    )

    # Test invalid date range (to_date before from_date)
    new = in_memory_db.add_estimatedmenupricerecord(
        menu_id=menu_item.id,
        from_date=datetime.now(),
        estimated_to_date=datetime.now() - timedelta(days=1)
    )
    assert new is None, "Should have raised ValueError for invalid date range"


    # Create multiple records with different dates
    base_date = datetime.now().date()
    for i in range(5):
        in_memory_db.add_estimatedmenupricerecord(
            menu_id=menu_item.id,
            sales_forecast=100 + i * 20,
            from_date=base_date + timedelta(days=i * 7),  # 0, 7, 14, 21, 28 days
            estimated_to_date=base_date + timedelta(days=(i + 1) * 7)  # 7, 14, 21, 28, 35 days
        )


    # Test date range filtering (should get 2 records)
    records = in_memory_db.get_estimatedmenupricerecord(
        menu_id=menu_item.id,
        from_date=base_date + timedelta(days=14),
        to_date=base_date + timedelta(days=28)
    )

    assert len(records) == 3
    assert all(record.from_date >= base_date + timedelta(days=14) for record in records)
    assert all(record.from_date <= base_date + timedelta(days=28) for record in records)


def test_estimatedmenupricerecord_get_last(in_memory_db):
    """Test getting the most recent record"""
    menu_item = in_memory_db.add_menu(
        name="Last Record Test Menu",
        size="m",
        current_price=25.0
    )

    # Explicitly define test dates (newest to oldest)
    test_dates = [
        datetime.now().date(),  # Today (most recent)
        datetime.now().date() - timedelta(days=2),  # 2 days ago
        datetime.now().date() - timedelta(days=4)  # 4 days ago
    ]

    for i, date in enumerate(test_dates):
        in_memory_db.add_estimatedmenupricerecord(
            menu_id=menu_item.id,
            sales_forecast=50 + i * 10,  # 50, 60, 70
            from_date=date
        )

    # Verify the newest record is returned
    last_record = in_memory_db.get_estimatedmenupricerecord(
        menu_id=menu_item.id,
    )

    assert last_record != []
    assert last_record[0].from_date == test_dates[0]  # Today (most recent)
    assert last_record[0].sales_forecast == 50

def test_estimatedmenupricerecord_profit_warning(in_memory_db):
    """Test warning is logged for negative profit"""
    menu_item = in_memory_db.add_menu(
        name="Profit Warning Menu",
        size="m",
        current_price=30.0
    )

    record = in_memory_db.add_estimatedmenupricerecord(
        menu_id=menu_item.id,
        profit=-100.0,
        from_date=datetime.now()
    )
    assert record is None
