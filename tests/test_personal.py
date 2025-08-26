import pytest
from datetime import datetime
from dbhandler import DbHandler
from cafe_managment_models import Personal
from utils import crud_cycle_test

@pytest.fixture(scope="module")
def db_handler():
    # Use in-memory SQLite for tests
    handler = DbHandler("sqlite:///:memory:")
    return handler

def test_personal_crud_cycle(db_handler):
    create_kwargs = {
        "first_name": "John",
        "last_name": "Doe",
        "nationality_code": "ABC123",
        "email": "john@example.com",
        "phone": "123456789",
        "address": "123 Main St",
        "hire_date": datetime(2023, 1, 1),
        "position": "Barista",
        "active": True,
        "description": "Test employee"
    }

    update_kwargs = {
        "first_name": "Jane",
        "last_name": "Smith",
        "position": "Manager",
        "active": False,
        "description": "Updated employee"
    }

    crud_cycle_test(
        db_handler=db_handler,
        model_class=Personal,
        create_kwargs=create_kwargs,
        update_kwargs=update_kwargs,
        lookup_fields=["nationality_code"],
        lookup_values=["ABC123"]
    )

def test_duplicate_nationality_code_fails(db_handler):
    """Should not allow two personals with the same nationality_code"""
    p1 = db_handler.add_personal(
        first_name="John",
        last_name="Doe",
        nationality_code="XYZ999"
    )
    assert p1 is not None

    # try adding duplicate
    p2 = db_handler.add_personal(
        first_name="Jane",
        last_name="Doe",
        nationality_code="XYZ999"
    )
    assert p2 is None  # should fail because unique constraint

def test_missing_required_fields(db_handler):
    """Nationality code is required (unique + important identifier)"""
    p = db_handler.add_personal(
        first_name="Alice",
        last_name="Smith"
        # nationality_code is missing
    )
    assert p is not None  # should not fail

def test_update_nonexistent_personal(db_handler):
    """Editing a Personal with a non-existent ID should return None"""
    fake = Personal(
        id=999,  # doesn't exist in DB
        first_name="Ghost",
        last_name="User",
        nationality_code="GHOST999"
    )
    updated = db_handler.edit_personal(fake)
    assert updated is None

def test_delete_nonexistent_personal(db_handler):
    """Deleting a Personal that does not exist should return False"""
    fake = Personal(
        id=999,
        first_name="Ghost",
        last_name="User",
        nationality_code="GHOST999"
    )
    deleted = db_handler.delete_personal(fake)
    assert deleted is False

def test_filter_by_active_flag(db_handler):
    """Ensure filtering by active works"""
    db_handler.add_personal(
        first_name="Active",
        last_name="User",
        nationality_code="ACTIVE123",
        active=True
    )
    db_handler.add_personal(
        first_name="Inactive",
        last_name="User",
        nationality_code="INACTIVE123",
        active=False
    )
    actives = db_handler.get_personal(active=True)
    inactives = db_handler.get_personal(active=False)

    assert all(p.active for p in actives)
    assert all(p.active is False for p in inactives)