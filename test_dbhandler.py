from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cafe_managment_models import *
from dbhandler import DbHandler

@pytest.fixture(scope='function')
def in_memory_db():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    db_handler = DbHandler(engine=engine, session_factory=Session)


    yield db_handler

    Base.metadata.drop_all(engine)


# Test the add_inventory function
def test_add_inventory_item(in_memory_db):
    # Prepare test data
    name = "Coffee Beans"
    unit = "gr"
    current_stock = 10.0
    price_per_unit = 15.0
    initial_value = 150.0
    date_of_initial_value = datetime.now()

    # Call the function you are testing
    new_item = in_memory_db.add_inventory(
        name=name,
        unit=unit,
        current_stock=current_stock,
        price_per_unit=price_per_unit,
        initial_value=initial_value,
        date_of_initial_value=date_of_initial_value
    )

    # Assert that the function returned a valid object
    assert new_item is not None
    assert new_item.id is not None
    assert new_item.name == name.lower().strip()


def test_add_inventory_with_missing_data(in_memory_db):
    # Test adding an item with only the required field
    new_item = in_memory_db.add_inventory(name="Sugar")
    # Assert that the item was created successfully and has an ID
    assert new_item is not None
    assert new_item.id is not None
    assert new_item.name == "Sugar".lower().strip()

    # Assert that the optional fields are set to their defaults (or None)
    assert new_item.unit is None


def test_get_inventory_success(in_memory_db):
    # Add an item to the test database
    db_handler = in_memory_db
    added_item = in_memory_db.add_inventory(name="Sugar")
    # Try to retrieve the item using your new function
    found_item = db_handler.get_inventory(name="Sugar")
    # Assert that the item was found and its attributes match
    assert found_item is not None
    assert found_item.name == added_item.name
    assert found_item.id == added_item.id


def test_get_inventory_not_found(in_memory_db):
    # Try to get an item that doesn't exist
    result = in_memory_db.get_inventory("Nonexistent")
    assert result is None

def test_edit_inventory_success(in_memory_db):
    # Add an item first
    item = in_memory_db.add_inventory(name="Milk", unit="L", current_stock=5.0)
    assert item is not None

    # Change some fields
    item.current_stock = 8.0
    item.unit = "liters"

    updated_item = in_memory_db.edit_inventory(item)

    assert updated_item is not None
    assert updated_item.id == item.id
    assert updated_item.current_stock == 8.0
    assert updated_item.unit == "liters"


def test_edit_inventory_no_id(in_memory_db):
    from cafe_managment_models import Inventory
    # Create an inventory object manually without ID
    fake_item = Inventory(name="Ghost", unit="none")
    result = in_memory_db.edit_inventory(fake_item)
    assert result is None


def test_delete_inventory_success(in_memory_db):
    # Add an item to delete
    item = in_memory_db.add_inventory(name="Tea", unit="gr")
    assert item is not None

    deleted = in_memory_db.delete_inventory(item.id)
    assert deleted is True

    # Verify it’s gone
    found = in_memory_db.get_inventory("Tea")
    assert found is None


def test_delete_inventory_not_found(in_memory_db):
    # Try deleting a non-existent ID
    deleted = in_memory_db.delete_inventory(9999)
    assert deleted is False

def test_full_crud_cycle(in_memory_db):
    # --- CREATE ---
    item = in_memory_db.add_inventory(name="Honey", unit="kg", current_stock=2.0)
    assert item is not None
    assert item.id is not None
    assert item.name == "honey"  # stored lowercase

    # --- READ ---
    fetched = in_memory_db.get_inventory("Honey")
    assert fetched is not None
    assert fetched.id == item.id
    assert fetched.current_stock == 2.0

    # --- UPDATE ---
    fetched.current_stock = 5.0
    fetched.unit = "kilogram"
    updated = in_memory_db.edit_inventory(fetched)
    assert updated is not None
    assert updated.current_stock == 5.0
    assert updated.unit == "kilogram"

    # Re-fetch to double check persistence
    refetched = in_memory_db.get_inventory("honey")
    assert refetched.current_stock == 5.0
    assert refetched.unit == "kilogram"

    # --- DELETE ---
    deleted = in_memory_db.delete_inventory(updated.id)
    assert deleted is True

    # Verify it’s gone
    gone = in_memory_db.get_inventory("Honey")
    assert gone is None

"""
The only improvement I’d suggest:

If you add more models later (e.g. Orders, Staff, etc.), you might not want to duplicate the test_full_crud_cycle style for every one. Instead, you could use pytest parametrize to run the same CRUD test on multiple models.

Would you like me to show you how to parameterize the CRUD cycle test so it works for any model you add later?
"""