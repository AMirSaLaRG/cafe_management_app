import pytest
from datetime import datetime
from cafe_managment_models import Recipe, Inventory, Menu
from utils import crud_cycle_test


# The 'in_memory_db' fixture is provided by conftest.py
# It sets up a new in-memory SQLite database for each test function.

@pytest.fixture
def setup_recipe_dependencies(in_memory_db):
    """
    Fixture to set up required Inventory and Menu items for recipe tests.
    Recipes have a composite primary key that depends on these items.
    """
    # Create a new inventory item
    inventory_data = {
        "name": "coffee beans",
        "unit": "g",
        "current_stock": 1000.0,
        "price_per_unit": 0.05
    }
    inventory_item = in_memory_db.add_inventory(**inventory_data)
    assert inventory_item is not None

    # Create a new menu item
    menu_data = {
        "name": "latte",
        "size": "M",
        "current_price": 4.50,
        "category": "coffee"
    }
    menu_item = in_memory_db.add_menu(**menu_data)
    assert menu_item is not None

    # Return the created items' IDs for use in tests
    return inventory_item.id, menu_item.id


def test_add_recipe(in_memory_db, setup_recipe_dependencies):
    """
    Test the add_recipe function.
    """
    inventory_id, menu_id = setup_recipe_dependencies

    # Create the recipe
    recipe_data = {
        "inventory_id": inventory_id,
        "menu_id": menu_id,
        "inventory_item_amount_usage": 15.0,
        "writer": "John Doe",
        "description": "Standard recipe"
    }
    new_recipe = in_memory_db.add_recipe(**recipe_data)

    # Assert that the recipe was added successfully
    assert new_recipe is not None
    assert new_recipe.inventory_id == inventory_id
    assert new_recipe.menu_id == menu_id
    assert new_recipe.inventory_item_amount_usage == 15.0

    # Test adding a duplicate recipe (should fail)
    duplicate_recipe = in_memory_db.add_recipe(**recipe_data)
    assert duplicate_recipe is None


def test_get_recipe(in_memory_db, setup_recipe_dependencies):
    """
    Test the get_recipe function with various lookup methods.
    """
    inventory_id, menu_id = setup_recipe_dependencies

    # Add a recipe to the database first
    in_memory_db.add_recipe(
        inventory_id=inventory_id,
        menu_id=menu_id,
        inventory_item_amount_usage=20.0
    )

    # Test getting a single recipe with both IDs
    retrieved_recipe = in_memory_db.get_recipe(
        inventory_id=inventory_id,
        menu_id=menu_id
    )
    assert retrieved_recipe != []
    assert isinstance(retrieved_recipe[0], Recipe)
    assert retrieved_recipe[0].inventory_id == inventory_id
    assert retrieved_recipe[0].menu_id == menu_id

    # Test getting recipes with only inventory_id
    retrieved_recipes_by_inv = in_memory_db.get_recipe(inventory_id=inventory_id)
    assert retrieved_recipes_by_inv is not None
    assert isinstance(retrieved_recipes_by_inv, list)
    assert len(retrieved_recipes_by_inv) == 1
    assert retrieved_recipes_by_inv[0].inventory_id == inventory_id

    # Test getting recipes with only menu_id
    retrieved_recipes_by_menu = in_memory_db.get_recipe(menu_id=menu_id)
    assert retrieved_recipes_by_menu is not None
    assert isinstance(retrieved_recipes_by_menu, list)
    assert len(retrieved_recipes_by_menu) == 1
    assert retrieved_recipes_by_menu[0].menu_id == menu_id

    # Test no IDs provided (should not return empty)
    no_id_recipe = in_memory_db.get_recipe()
    assert no_id_recipe != []

    # Test with non-existent IDs (should return None or empty list)
    non_existent_recipe = in_memory_db.get_recipe(inventory_id=999, menu_id=999)
    assert non_existent_recipe == []

    non_existent_list = in_memory_db.get_recipe(inventory_id=999)
    assert non_existent_list == []


def test_edit_recipe(in_memory_db, setup_recipe_dependencies):
    """
    Test the edit_recipe function.
    """
    inventory_id, menu_id = setup_recipe_dependencies

    # Add a recipe
    recipe_to_edit = in_memory_db.add_recipe(
        inventory_id=inventory_id,
        menu_id=menu_id,
        inventory_item_amount_usage=20.0
    )
    assert recipe_to_edit is not None

    # Modify the object
    recipe_to_edit.inventory_item_amount_usage = 25.0
    recipe_to_edit.description = "Updated note"

    # Edit the recipe in the database
    edited_recipe = in_memory_db.edit_recipe(recipe_to_edit)

    # Assert that the changes were saved
    assert edited_recipe is not None
    assert edited_recipe.inventory_item_amount_usage == 25.0
    assert edited_recipe.description == "Updated note"


def test_delete_recipe(in_memory_db, setup_recipe_dependencies):
    """
    Test the delete_recipe function.
    """
    inventory_id, menu_id = setup_recipe_dependencies

    # Add a recipe to delete
    recipe_to_delete = in_memory_db.add_recipe(
        inventory_id=inventory_id,
        menu_id=menu_id,
        inventory_item_amount_usage=10.0
    )
    assert recipe_to_delete is not None

    # Delete the recipe
    deleted_status = in_memory_db.delete_recipe(
        recipe_to_delete)
    assert deleted_status is True

    # Verify that it's gone
    gone_recipe = in_memory_db.get_recipe(
        inventory_id=inventory_id,
        menu_id=menu_id
    )
    assert gone_recipe == []

    # Test deleting a non-existent recipe (should return False)
    non_existent_delete = in_memory_db.delete_recipe(
        recipe_to_delete
    )
    assert non_existent_delete is False


def test_crud_cycle_recipe(in_memory_db, setup_recipe_dependencies):
    """
    Test the full CRUD cycle for the Recipe model using the generic utility function.
    """
    inventory_id, menu_id = setup_recipe_dependencies

    # Define the data for the CRUD cycle
    create_kwargs = {
        "inventory_id": inventory_id,
        "menu_id": menu_id,
        "inventory_item_amount_usage": 12.0,
        "writer": "Jane Smith"
    }
    update_kwargs = {
        "inventory_item_amount_usage": 15.0,
        "description": "Test note"
    }
    # For a composite key, we need to pass the lookup values manually
    lookup_fields = ["inventory_id", "menu_id"]
    lookup_values = [inventory_id, menu_id]

    # Run the generic CRUD test
    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=Recipe,
        create_kwargs=create_kwargs,
        update_kwargs=update_kwargs,
        lookup_fields=lookup_fields,
        lookup_values=lookup_values
    )