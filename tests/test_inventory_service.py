from datetime import datetime

from services.inventory_service import InventoryService
import pytest


@pytest.fixture
def setup_menu_inventory(in_memory_db):
    menu = in_memory_db.add_menu(name='latte', size='L')
    menu2 = in_memory_db.add_menu(name='monster', size='L')
    inv1 = in_memory_db.add_inventory(name='coffee', unit='gr',  safety_stock=50)
    inv2 = in_memory_db.add_inventory(name='milk', unit='L', safety_stock=2)
    inv3 = in_memory_db.add_inventory(name='straw', unit='unit',  safety_stock=1)


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

    return {"menu": menu, 'menu2': menu2, "inv1": inv1, "inv2":inv2, "inv3":inv3}

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
