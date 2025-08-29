from services.inventory_service import InventoryService


def test_inventory_check_menu(in_memory_db):
    test_menu_item = in_memory_db.add_menu(
                            name='latter',
                            size='L'
                        )
    assert test_menu_item is not None

    test_inventory_item1 = in_memory_db.add_inventory(
        name='coffee',
        unit="gr",
        current_stock=100,
        safety_stock=50,
    )
    assert test_inventory_item1 is not None


    test_inventory_item2 = in_memory_db.add_inventory(
        name='milk',
        unit="Litter",
        current_stock=6,
        safety_stock=2,
    )
    assert test_inventory_item2 is not None


    test_inventory_item3 = in_memory_db.add_inventory(
        name='straw',
        unit="unit",
        current_stock=10,
        safety_stock=1,
    )
    assert test_inventory_item3 is not None

    test_recipe1 = in_memory_db.add_recipe(
        test_inventory_item1.id,
        test_menu_item.id,
        inventory_item_amount_usage=10)
    assert test_recipe1 is not None

    test_recipe2 = in_memory_db.add_recipe(
        test_inventory_item2.id,
        test_menu_item.id,
        inventory_item_amount_usage=0.4)
    assert test_recipe2 is not None

    test_recipe3 = in_memory_db.add_recipe(
        test_inventory_item3.id,
        test_menu_item.id,
        inventory_item_amount_usage=1)
    assert test_recipe3 is not None


    service = InventoryService(in_memory_db)
    service.check_stock(menu_id=test_menu_item.id, quantity=10)