import pytest
from cafe_managment_models import *
from tests.utils import crud_cycle_test
from datetime import datetime, timedelta


@pytest.fixture
def setup_menu_data_salesforecast(in_memory_db):
    """Setup fixture with multiple menus for SalesForecast tests"""
    menus = []

    menu_data = [
        {"name": "Test Coffee", "size": "m", "price": 10.0, "vat": 0.1},
        {"name": "Test Tea", "size": "l", "price": 15.0, "vat": 0.1},
        {"name": "Test Cake", "size": "s", "price": 20.0, "vat": 0.2}
    ]

    for data in menu_data:
        menu = in_memory_db.add_menu(
            name=data["name"],
            size=data["size"],
            current_price=data["price"],
            value_added_tax=data["vat"],
            serving=True,
            description=f"Test {data['name']}"
        )
        assert menu is not None
        menus.append(menu)

    return menus  # Return the created menus for use in tests


def test_salesforecast_basic_crud(in_memory_db, setup_menu_data_salesforecast):
    """Test basic CRUD operations for SalesForecast"""
    menus = setup_menu_data_salesforecast
    menu_id = menus[0].id  # Use first menu's ID

    create_kwargs = {
        "menu_item_id": menu_id,
        "from_date": datetime(2024, 1, 1),
        "to_date": datetime(2024, 12, 31),
        "sell_number": 1000,
    }

    update_kwargs = {
        "sell_number": 1500,
        "to_date": datetime(2024, 6, 30),
    }

    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=SalesForecast,
        create_kwargs=create_kwargs,
        update_kwargs=update_kwargs,
        lookup_fields=['menu_item_id'],
        lookup_values=[menu_id]
    )


def test_salesforecast_multiple_forecasts_same_menu(in_memory_db, setup_menu_data_salesforecast):
    """Test creating multiple forecasts for the same menu item with non-overlapping dates"""
    menus = setup_menu_data_salesforecast
    menu_id = menus[0].id

    # First forecast
    forecast1 = in_memory_db.add_salesforecast(
        menu_item_id=menu_id,
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 3, 31),
        sell_number=500
    )
    assert forecast1 is not None

    # Second forecast (non-overlapping)
    forecast2 = in_memory_db.add_salesforecast(
        menu_item_id=menu_id,
        from_date=datetime(2024, 4, 1),
        to_date=datetime(2024, 6, 30),
        sell_number=700
    )
    assert forecast2 is not None

    # Verify both exist
    forecasts = in_memory_db.get_salesforecast(menu_item_id=menu_id)
    assert len(forecasts) == 2


def test_salesforecast_time_overlap_prevention(in_memory_db, setup_menu_data_salesforecast):
    """Test that time overlaps are properly prevented"""
    menus = setup_menu_data_salesforecast
    menu_id = menus[0].id

    # First forecast
    forecast1 = in_memory_db.add_salesforecast(
        menu_item_id=menu_id,
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 6, 30),
        sell_number=500
    )
    assert forecast1 is not None

    # Try to create overlapping forecast - should fail
    forecast2 = in_memory_db.add_salesforecast(
        menu_item_id=menu_id,
        from_date=datetime(2024, 3, 1),  # Overlaps with first forecast
        to_date=datetime(2024, 9, 30),
        sell_number=700
    )
    assert forecast2 is None  # Should be None due to time overlap


def test_salesforecast_different_menus_no_overlap(in_memory_db, setup_menu_data_salesforecast):
    """Test that forecasts for different menu items can have overlapping dates"""
    menus = setup_menu_data_salesforecast
    menu1_id, menu2_id = menus[0].id, menus[1].id

    # Forecast for first menu
    forecast1 = in_memory_db.add_salesforecast(
        menu_item_id=menu1_id,
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 6, 30),
        sell_number=500
    )
    assert forecast1 is not None

    # Forecast for second menu with same dates - should work
    forecast2 = in_memory_db.add_salesforecast(
        menu_item_id=menu2_id,
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 6, 30),
        sell_number=300
    )
    assert forecast2 is not None  # Should work - different menu


def test_salesforecast_invalid_dates(in_memory_db, setup_menu_data_salesforecast):
    """Test validation for invalid date ranges"""
    menus = setup_menu_data_salesforecast
    menu_id = menus[0].id

    # from_date after to_date - should fail
    forecast = in_memory_db.add_salesforecast(
        menu_item_id=menu_id,
        from_date=datetime(2024, 12, 31),
        to_date=datetime(2024, 1, 1),  # Invalid - from_date after to_date
        sell_number=500
    )
    assert forecast is None

    # Negative sell_number - should fail
    forecast = in_memory_db.add_salesforecast(
        menu_item_id=menu_id,
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 12, 31),
        sell_number=-100  # Invalid - negative number
    )
    assert forecast is None


def test_salesforecast_filtering(in_memory_db, setup_menu_data_salesforecast):
    """Test filtering functionality"""
    menus = setup_menu_data_salesforecast
    menu1_id, menu2_id = menus[0].id, menus[1].id

    # Create forecasts for different time periods
    dates = [
        (datetime(2024, 1, 1), datetime(2024, 3, 31)),
        (datetime(2024, 4, 1), datetime(2024, 6, 30)),
        (datetime(2024, 7, 1), datetime(2024, 9, 30)),
    ]

    for from_date, to_date in dates:
        for menu_id in [menu1_id, menu2_id]:
            forecast = in_memory_db.add_salesforecast(
                menu_item_id=menu_id,
                from_date=from_date,
                to_date=to_date,
                sell_number=100
            )
            assert forecast is not None

    # Test filtering by menu item
    menu1_forecasts = in_memory_db.get_salesforecast(menu_item_id=menu1_id)
    assert len(menu1_forecasts) == 3

    # Test filtering by date range
    q2_forecasts = in_memory_db.get_salesforecast(
        from_date=datetime(2024, 4, 1),
        to_date=datetime(2024, 6, 30)
    )
    assert len(q2_forecasts) == 2  # One for each menu

    # Test filtering by both menu and date
    menu1_q2_forecasts = in_memory_db.get_salesforecast(
        menu_item_id=menu1_id,
        from_date=datetime(2024, 4, 1),
        to_date=datetime(2024, 6, 30)
    )
    assert len(menu1_q2_forecasts) == 1