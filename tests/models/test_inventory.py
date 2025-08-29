from models.cafe_managment_models import Inventory
from tests.utils import crud_cycle_test


def test_inventory_crud_cycle(in_memory_db):
    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=Inventory,
        create_kwargs={"name": "Honey", "unit": "kg", "current_stock": 2.0, "safety_stock": 300},
        update_kwargs={"current_stock": 5.0, "unit": "kilogram", "safety_stock":0},
        lookup_fields=["name", 'id'],  # for Inventory, we often fetch by name
        lookup_values=["honey", 1]
    )