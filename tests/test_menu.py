from tests.utils import crud_cycle_test
from cafe_managment_models import Menu

def test_menu_crud_cycle(in_memory_db):
    """Test full CRUD cycle for Menu using  exact utility function"""
    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=Menu,
        create_kwargs={
            "name": "Cappuccino",
            "size": "Large",
            "category": "Coffee",
            "current_price": 4.50,
            "serving": True
        },
        update_kwargs={
            "current_price": 5.00,
            "category": "Specialty Coffee",
            "serving": False
        },
        lookup_fields=["name", "size"],  # Fields to use for lookup
        lookup_values=["cappuccino", "large"]  # Optional explicit values
    )

def test_menu_crud_without_lookup_values(in_memory_db):
    """Test using automatic lookup values from created object"""
    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=Menu,
        create_kwargs={
            "name": "Espresso",
            "size": "Small",
            "current_price": 3.00
        },
        update_kwargs={
            "description": "Strong coffee shot"
        },
        lookup_fields=["name", "size"]  # Values will be taken from created object
    )

def test_menu_multiple_lookup_fields(in_memory_db):
    """Test with multiple lookup fields"""
    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=Menu,
        create_kwargs={
            "name": "Latte",
            "size": "Medium",
            "category": "Hot",
            "value_added_tax": 0.1
        },
        update_kwargs={
            "value_added_tax": 0.15
        },
        lookup_fields=["name", "size"]
    )