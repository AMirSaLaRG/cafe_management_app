from cafe_manager import CafeManager




def test_get_menu_available(in_memory_db):
    cafe_manager = CafeManager(in_memory_db)

    in_memory_db.add_menu(name="test1", category="cat test", size="Gonde")

    test1 = cafe_manager.get_menu_with_availability()
    print(test1)

def test_add_menu_item(in_memory_db):
    cafe_manager = CafeManager(in_memory_db)


    test = cafe_manager.add_menu_item(name="test1",
                               category="cat test",
                               size="Gonde",
                               value_added_tax=0.1,)

    assert test

    test2 = cafe_manager.get_menu_with_availability()

    assert test2

