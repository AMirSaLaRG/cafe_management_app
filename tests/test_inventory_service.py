from datetime import datetime, timedelta

from services import inventory_service
from services.inventory_service import InventoryService
import pytest


@pytest.fixture
def setup_menu_inventory(in_memory_db):
    sup1 = in_memory_db.add_supplier('Supplier 1', load_time_days=1)
    sup2 = in_memory_db.add_supplier('Supplier 2', load_time_days=2)
    menu = in_memory_db.add_menu(name='latte', size='L')
    menu2 = in_memory_db.add_menu(name='monster', size='L')
    inv1 = in_memory_db.add_inventory(name='coffee', unit='gr',  safety_stock=50, daily_usage=50, current_supplier=sup1.id)
    inv2 = in_memory_db.add_inventory(name='milk', unit='L', safety_stock=2, daily_usage=2, current_supplier=sup1.id)
    inv3 = in_memory_db.add_inventory(name='straw', unit='unit',  safety_stock=1, daily_usage=1, current_supplier=sup1.id)


    base_stock_record1 = in_memory_db.add_inventorystockrecord(inventory_id=inv1.id, manual_report=100)
    base_stock_record2 = in_memory_db.add_inventorystockrecord(inventory_id=inv2.id, manual_report=6)
    base_stock_record3 = in_memory_db.add_inventorystockrecord(inventory_id=inv3.id, manual_report=10)
    r1 = in_memory_db.add_recipe(inv1.id, menu.id, inventory_item_amount_usage=11)
    r2 = in_memory_db.add_recipe(inv2.id, menu.id, inventory_item_amount_usage=0.4)
    r3 = in_memory_db.add_recipe(inv3.id, menu.id, inventory_item_amount_usage=1)
    r4 = in_memory_db.add_recipe(inv1.id, menu2.id, inventory_item_amount_usage=50)
    r5 = in_memory_db.add_recipe(inv2.id, menu2.id, inventory_item_amount_usage=3)
    r6 = in_memory_db.add_recipe(inv3.id, menu2.id, inventory_item_amount_usage=1000)

    service = InventoryService(in_memory_db)
    test1 = service._calculate_inventory(inv1.id)
    test2 = service._calculate_inventory(inv2.id)
    test3 = service._calculate_inventory(inv3.id)
    assert test1 and test2 and test3

    return {"menu": menu, 'menu2': menu2, "inv1": inv1, "inv2":inv2, "inv3":inv3, 'sup1':sup1, 'sup2':sup2}

def test_inventory_check_menu(in_memory_db, setup_menu_inventory):
    service = InventoryService(in_memory_db)
    # test1=service._calculate_inventory(setup_menu_inventory['inv1'].id)
    # test2=service._calculate_inventory(setup_menu_inventory['inv2'].id)
    # test3=service._calculate_inventory(setup_menu_inventory['inv3'].id)
    # assert test1 and test2 and test3
    test4 = service._calculate_inventory(999999)
    assert test4 is False

    result, missing_items =service.check_stock_for_menu(menu_id=setup_menu_inventory['menu'].id, quantity=10)
    assert result is False
    assert 'coffee' in missing_items
    assert missing_items['coffee'] > 0

    result, missing_items =service.check_stock_for_menu(menu_id=setup_menu_inventory['menu'].id)
    assert result is True

    result, missing_items =service.check_stock_for_menu(menu_id=setup_menu_inventory['menu2'].id)
    assert result is False
    assert set(missing_items.keys()) == { 'straw'}

def test_deduct_stock_menu(in_memory_db, setup_menu_inventory):
    service = InventoryService(in_memory_db)

    deduct1 = service.deduct_stock_by_menu(menu_id=setup_menu_inventory['menu'].id, quantity=2)
    assert deduct1 is True

    deduct2 = service.deduct_stock_by_menu(menu_id=setup_menu_inventory['menu'].id,
                                           quantity=1,
                                           category='sells',
                                           foreign_id=11,
                                           date=datetime.now(),
                                           description="test Description for this"
                                           )
    assert deduct2 is True


    stock_before_fail1 = in_memory_db.get_inventory(id=setup_menu_inventory['inv1'].id)[0].current_stock
    stock_before_fail2 = in_memory_db.get_inventory(id=setup_menu_inventory['inv2'].id)[0].current_stock
    stock_before_fail3 = in_memory_db.get_inventory(id=setup_menu_inventory['inv3'].id)[0].current_stock

    deduct3 = service.deduct_stock_by_menu(menu_id=setup_menu_inventory['menu2'].id, quantity=2)
    assert deduct3 is False

    stock_after_fail1 = in_memory_db.get_inventory(id=setup_menu_inventory['inv1'].id)[0].current_stock
    stock_after_fail2 = in_memory_db.get_inventory(id=setup_menu_inventory['inv2'].id)[0].current_stock
    stock_after_fail3 = in_memory_db.get_inventory(id=setup_menu_inventory['inv3'].id)[0].current_stock

    assert stock_before_fail1 == stock_after_fail1
    assert stock_before_fail2 == stock_after_fail2
    assert stock_before_fail3 == stock_after_fail3

def test_deduct_stock_inventory(in_memory_db, setup_menu_inventory):
    service = InventoryService(in_memory_db)

    stock_before = in_memory_db.get_inventory(id=setup_menu_inventory['inv1'].id)[0].current_stock
    deduct1 = service.deduct_stock_by_inventory_item(inventory_item_id=setup_menu_inventory['inv1'].id, quantity=1500)
    assert deduct1 is False
    stock_after = in_memory_db.get_inventory(id=setup_menu_inventory['inv1'].id)[0].current_stock
    assert stock_before == stock_after


    stock_before = in_memory_db.get_inventory(id=setup_menu_inventory['inv1'].id)[0].current_stock
    deduct2 = service.deduct_stock_by_inventory_item(inventory_item_id=setup_menu_inventory['inv1'].id, quantity=4)
    assert deduct2 is True
    stock_after = in_memory_db.get_inventory(id=setup_menu_inventory['inv1'].id)[0].current_stock
    assert stock_before == stock_after +4

    stock_before = in_memory_db.get_inventory(id=setup_menu_inventory['inv1'].id)[0].current_stock
    deduct3 = service.deduct_stock_by_inventory_item(inventory_item_id=setup_menu_inventory['inv1'].id,
                                                     quantity=1,
                                                     category='sells',
                                                     foreign_id=11,
                                                     date=datetime.now(),
                                                     description="test Description for this")
    assert deduct3 is True
    stock_after = in_memory_db.get_inventory(id=setup_menu_inventory['inv1'].id)[0].current_stock
    assert stock_before == stock_after +1

def test_restock(in_memory_db, setup_menu_inventory):
    service = InventoryService(in_memory_db)

    stock_before1 = in_memory_db.get_inventory(id=setup_menu_inventory['inv1'].id)[0].current_stock
    stock_before2 = in_memory_db.get_inventory(id=setup_menu_inventory['inv2'].id)[0].current_stock
    stock_before3 = in_memory_db.get_inventory(id=setup_menu_inventory['inv3'].id)[0].current_stock

    deduct1 = service.deduct_stock_by_menu(menu_id=setup_menu_inventory['menu'].id, quantity=2)
    assert deduct1 is True
    restock = service.restock_by_menu(menu_id=setup_menu_inventory['menu'].id, quantity=2)
    assert restock is True

    stock_after1 = in_memory_db.get_inventory(id=setup_menu_inventory['inv1'].id)[0].current_stock
    stock_after2 = in_memory_db.get_inventory(id=setup_menu_inventory['inv2'].id)[0].current_stock
    stock_after3 = in_memory_db.get_inventory(id=setup_menu_inventory['inv3'].id)[0].current_stock

    assert stock_before1 == stock_after1
    assert stock_before2 == stock_after2
    assert stock_before3 == stock_after3

    stock_before1 = in_memory_db.get_inventory(id=setup_menu_inventory['inv1'].id)[0].current_stock
    stock_before2 = in_memory_db.get_inventory(id=setup_menu_inventory['inv2'].id)[0].current_stock
    stock_before3 = in_memory_db.get_inventory(id=setup_menu_inventory['inv3'].id)[0].current_stock

    deduct1 = service.deduct_stock_by_menu(menu_id=setup_menu_inventory['menu'].id, quantity=2)
    assert deduct1 is True
    restock = service.restock_by_menu(menu_id=setup_menu_inventory['menu'].id, quantity=3)
    assert restock is True

    stock_after1 = in_memory_db.get_inventory(id=setup_menu_inventory['inv1'].id)[0].current_stock
    stock_after2 = in_memory_db.get_inventory(id=setup_menu_inventory['inv2'].id)[0].current_stock
    stock_after3 = in_memory_db.get_inventory(id=setup_menu_inventory['inv3'].id)[0].current_stock

    assert stock_before1 != stock_after1
    assert stock_before2 != stock_after2
    assert stock_before3 != stock_after3


    stock_before1 = in_memory_db.get_inventory(id=setup_menu_inventory['inv1'].id)[0].current_stock

    deduct1 = service.deduct_stock_by_inventory_item(inventory_item_id=setup_menu_inventory['inv1'].id, quantity=10)
    assert deduct1 is True
    restock = service.restock_by_inventory_item(inventory_item_id=setup_menu_inventory['inv1'].id, quantity=10)
    assert restock is True

    stock_after1 = in_memory_db.get_inventory(id=setup_menu_inventory['inv1'].id)[0].current_stock

    assert stock_before1 == stock_after1



    stock_before1 = in_memory_db.get_inventory(id=setup_menu_inventory['inv1'].id)[0].current_stock

    deduct1 = service.deduct_stock_by_inventory_item(inventory_item_id=setup_menu_inventory['inv1'].id, quantity=25)
    assert deduct1 is True
    midle = in_memory_db.get_inventory(id=setup_menu_inventory['inv1'].id)[0].current_stock
    restock = service.restock_by_inventory_item(inventory_item_id=setup_menu_inventory['inv1'].id, quantity=50)
    assert restock is True
    end = in_memory_db.get_inventory(id=setup_menu_inventory['inv1'].id)[0].current_stock

    stock_after1 = in_memory_db.get_inventory(id=setup_menu_inventory['inv1'].id)[0].current_stock

    assert stock_before1 == stock_after1 - 25


def test_manual_check(in_memory_db, setup_menu_inventory):
    service = InventoryService(in_memory_db)

    stock_before1 = in_memory_db.get_inventory(id=setup_menu_inventory['inv1'].id)[0].current_stock
    report1 =service.manual_report(setup_menu_inventory['inv1'].id, -200, "Mr_test")
    assert report1 is False

    stock_after1 = in_memory_db.get_inventory(id=setup_menu_inventory['inv1'].id)[0].current_stock

    assert stock_after1 == stock_before1

    stock_before1 = in_memory_db.get_inventory(id=setup_menu_inventory['inv1'].id)[0].current_stock
    report1 =service.manual_report(setup_menu_inventory['inv1'].id, 500.0005, "Mr_test")
    assert report1 is True

    stock_after1 = in_memory_db.get_inventory(id=setup_menu_inventory['inv1'].id)[0].current_stock

    assert stock_after1 == 500.0005

    stock_before1 = in_memory_db.get_inventory(id=setup_menu_inventory['inv1'].id)[0].current_stock
    report1 =service.manual_report(setup_menu_inventory['inv1'].id, 0,
                                   "Mr_test", date=datetime.now(),
                                   foreign_id=12345,
                                   reason="All Ex")
    assert report1 is True

    stock_after1 = in_memory_db.get_inventory(id=setup_menu_inventory['inv1'].id)[0].current_stock

    assert stock_after1 == 0

def test_inventory_alerts(in_memory_db, setup_menu_inventory):
    service = InventoryService(in_memory_db)

    test1= service.low_stock_alerts()
    assert test1 is not {setup_menu_inventory['inv3'].name: setup_menu_inventory['inv3'].current_stock}




def test_add_inventory_item(in_memory_db, setup_menu_inventory):
    service = InventoryService(in_memory_db)

    from services.inventory_service import INITIATE_STOCK_CATEGORY

    test1 = service.create_new_inventory_item( item_name="Sibzamini",
                                  unit="kg",
                                  category="pishghza",
                                  person_who_added="Mr: test",
                                  current_supplier_id= setup_menu_inventory["sup1"].id,
                                  daily_usage = 5.43,
                                  safety_stock=10,
                                  price_per_unit=105.500,
                                  current_stock=100)
    assert test1

    check1 = in_memory_db.get_inventorystockrecord(description=INITIATE_STOCK_CATEGORY)
    assert check1
    assert check1[0].manual_report == 100

    check2 = in_memory_db.get_inventory(name="SIBzaMINI")[0]
    assert check2.unit == "kg"
    assert check2.category == "pishghza"
    assert check2.price_per_unit == 105.500
    assert check2.current_stock == 100

def test_one_parameter_changers_daily_usage(in_memory_db, setup_menu_inventory):
    service = InventoryService(in_memory_db)
    the_inventory_id = setup_menu_inventory["inv1"].id

    test1 = service.change_daily_usage(the_inventory_id, 0)
    assert test1

    check1 = in_memory_db.get_inventory(id=the_inventory_id)
    assert check1
    assert check1[0].daily_usage == 0

    test1 = service.change_daily_usage(the_inventory_id, 1500)
    assert test1

    check1 = in_memory_db.get_inventory(id=the_inventory_id)
    assert check1
    assert check1[0].daily_usage == 1500


    test1 = service.change_daily_usage(the_inventory_id, -1)
    assert test1 is False

    check1 = in_memory_db.get_inventory(id=the_inventory_id)
    assert check1
    assert check1[0].daily_usage == 1500

def test_one_parameter_changers_supplier(in_memory_db, setup_menu_inventory):
    service = InventoryService(in_memory_db)
    the_inventory_id = setup_menu_inventory["inv1"].id

    test1 = service.change_supplier(the_inventory_id, 2)
    assert test1

    check1 = in_memory_db.get_inventory(id=the_inventory_id)
    assert check1
    assert check1[0].current_supplier == 2

    test1 = service.change_supplier(the_inventory_id, 1)
    assert test1

    check1 = in_memory_db.get_inventory(id=the_inventory_id)
    assert check1
    assert check1[0].current_supplier == 1

    test1 = service.change_supplier(the_inventory_id, 3)
    assert test1 is False

    check1 = in_memory_db.get_inventory(id=the_inventory_id)
    assert check1
    assert check1[0].current_supplier == 1


def test_one_parameter_changers_safety_stock(in_memory_db, setup_menu_inventory):
    service = InventoryService(in_memory_db)
    the_inventory_id = setup_menu_inventory["inv1"].id

    test1 = service.change_safety_stock(the_inventory_id, 0)
    assert test1

    check1 = in_memory_db.get_inventory(id=the_inventory_id)
    assert check1
    assert check1[0].safety_stock == 0

    test1 = service.change_safety_stock(the_inventory_id, 1500)
    assert test1

    check1 = in_memory_db.get_inventory(id=the_inventory_id)
    assert check1
    assert check1[0].safety_stock == 1500


    test1 = service.change_safety_stock(the_inventory_id, -1)
    assert test1 is False

    check1 = in_memory_db.get_inventory(id=the_inventory_id)
    assert check1
    assert check1[0].safety_stock == 1500


def test_one_parameter_changers_current_price(in_memory_db, setup_menu_inventory):
    service = InventoryService(in_memory_db)
    the_inventory_id = setup_menu_inventory["inv1"].id

    test1 = service.set_current_price(the_inventory_id, 0)
    assert test1

    check1 = in_memory_db.get_inventory(id=the_inventory_id)
    assert check1
    assert check1[0].current_price == 0

    test1 = service.set_current_price(the_inventory_id, 1500)
    assert test1

    check1 = in_memory_db.get_inventory(id=the_inventory_id)
    assert check1
    assert check1[0].current_price == 1500


    test1 = service.set_current_price(the_inventory_id, -1)
    assert test1 is False

    check1 = in_memory_db.get_inventory(id=the_inventory_id)
    assert check1
    assert check1[0].current_price == 1500


def test_forecast_inventory_simple_basic(in_memory_db):
    """Test basic inventory forecasting with simple daily usage"""
    service = InventoryService(in_memory_db)
    supplier = in_memory_db.add_supplier('Test Supplier')
    inventory = in_memory_db.add_inventory(
        name='test_item_simple',
        unit='kg',
        safety_stock=10,
        daily_usage=3.0,  # Set daily usage explicitly
        current_supplier=supplier.id,
        current_stock=50.0
    )

    # Test forecast - should use the manual daily_usage field
    forecast = service.forecast_inventory(inventory.id, days=10)

    # 50 current stock - (3 daily usage * 10 days) = 20 remaining
    expected_remaining = 20.0
    assert forecast[inventory.name] == expected_remaining


def test_forecast_inventory_zero_daily_usage(in_memory_db):
    """Test forecasting when daily usage is zero"""
    service = InventoryService(in_memory_db)
    supplier = in_memory_db.add_supplier('Test Supplier')
    inventory = in_memory_db.add_inventory(
        name='non_consumable_item',
        unit='units',
        safety_stock=5,
        daily_usage=0.0,  # Zero usage
        current_supplier=supplier.id,
        current_stock=100.0
    )

    # Test forecast for 30 days with zero usage
    forecast = service.forecast_inventory(inventory.id, days=30)

    # 100 current stock - (0 daily usage * 30 days) = 100 (no change)
    assert forecast[inventory.name] == 100.0


def test_forecast_inventory_negative_result_simple(in_memory_db):
    """Test forecasting when stock will be depleted (simple version)"""
    service = InventoryService(in_memory_db)
    supplier = in_memory_db.add_supplier('Test Supplier')
    inventory = in_memory_db.add_inventory(
        name='high_usage_item',
        unit='units',
        daily_usage=15.0,  # High daily usage
        current_supplier=supplier.id,
        current_stock=40.0  # Low stock
    )

    # Forecast for 5 days
    forecast = service.forecast_inventory(inventory.id, days=5)

    # 40 current stock - (15 daily usage * 5 days) = -35 (depletion)
    assert forecast[inventory.name] == -35.0


def test_forecast_inventory_default_days_parameter(in_memory_db):
    """Test forecasting with default days parameter (7 days)"""
    service = InventoryService(in_memory_db)
    supplier = in_memory_db.add_supplier('Test Supplier')
    inventory = in_memory_db.add_inventory(
        name='default_test_item',
        unit='L',
        daily_usage=4.0,
        current_supplier=supplier.id,
        current_stock=50.0
    )

    # Test with default days (should be 7)
    forecast = service.forecast_inventory(inventory.id)

    # 50 current stock - (4 daily usage * 7 days) = 22 remaining
    assert forecast[inventory.name] == 22.0