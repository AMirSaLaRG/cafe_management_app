

from models.cafe_managment_models import Supplier
from tests.utils import crud_cycle_test


def test_supplier_crud_cycle(in_memory_db):
    """Test full CRUD cycle for Supplier using utility function"""
    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=Supplier,
        create_kwargs={
            "name": "Test Supplier Inc.",
            "contact_channel": "email",
            "contact_address": "test@supplier.com"
        },
        update_kwargs={
            "contact_channel": "phone",
            "contact_address": "+1234567890"
        },
        lookup_fields=['name'],
        lookup_values=['test supplier inc.']  # Lowercase due to your implementation
    )


def test_supplier_case_insensitive_lookup(in_memory_db):
    """Test that supplier lookup is case-insensitive"""
    # Add supplier with mixed case
    supplier = in_memory_db.add_supplier(
        name="Awesome Supplier LLC",
        contact_channel="email",
        contact_address="contact@awesome.com"
    )
    assert supplier is not None

    # Test various case lookups (should all work)
    test_cases = [
        "awesome supplier llc",
        "Awesome Supplier LLC",
        "AWESOME SUPPLIER LLC",
        "   awesome supplier llc   ",
    ]

    for test_name in test_cases:
        found = in_memory_db.get_supplier(name = test_name)
        assert found != []
        assert found[0].name == "awesome supplier llc"  # Stored lowercase
        assert found[0].id == supplier.id


def test_supplier_duplicate_name(in_memory_db):
    """Test behavior with duplicate supplier names"""
    # Add first supplier
    supplier1 = in_memory_db.add_supplier(
        name="Duplicate Supplier",
        contact_channel="email"
    )
    assert supplier1 is not None

    # Try to add duplicate (should work since no unique constraint in your code)
    supplier2 = in_memory_db.add_supplier(
        name="duplicate supplier",  # Lowercase variant
        contact_channel="phone"
    )
    assert supplier2 is None


def test_supplier_edit_nonexistent(in_memory_db):
    """Test editing non-existent supplier"""
    # Create supplier object without saving to DB
    fake_supplier = Supplier(
        name="Fake Supplier",
        contact_channel="none"
    )
    fake_supplier.id = 9999  # Non-existent ID

    result = in_memory_db.edit_supplier(fake_supplier)
    assert result is None  # Should return None for non-existent


def test_supplier_delete_nonexistent(in_memory_db):
    """Test deleting non-existent supplier"""
    # Create supplier object without saving to DB
    fake_supplier = Supplier(
        name="Fake Supplier",
        contact_channel="none"
    )
    fake_supplier.id = 9999  # Non-existent ID

    result = in_memory_db.delete_supplier(fake_supplier)
    assert result is False  # Should return False for non-existent


def test_supplier_empty_name(in_memory_db):
    """Test behavior with empty/whitespace names"""
    # Test empty string
    supplier = in_memory_db.add_supplier(name="", contact_channel="test")
    assert supplier is not None
    assert supplier.name == ""  # Empty string is stored

    # Test whitespace only
    supplier2 = in_memory_db.add_supplier(name="   ", contact_channel="test")
    assert supplier2 is None


def test_supplier_get_all_functionality(in_memory_db):
    """Test getting multiple suppliers"""
    # Add multiple suppliers
    suppliers = []
    for i in range(3):
        supplier = in_memory_db.add_supplier(
            name=f"Supplier {i}",
            contact_channel=f"channel_{i}"
        )
        assert supplier is not None
        suppliers.append(supplier)

    # Verify we can retrieve each one
    for i, expected_supplier in enumerate(suppliers):
        found = in_memory_db.get_supplier(name =f"supplier {i}")
        assert found != []
        assert found[0].id == expected_supplier.id
        assert found[0].name == f"supplier {i}"  # Lowercase


def test_supplier_null_values(in_memory_db):
    """Test supplier with None values"""
    supplier = in_memory_db.add_supplier(
        name="Null Supplier",

    )
    assert supplier is not None
    assert supplier.contact_channel is None
    assert supplier.contact_address is None

    found = in_memory_db.get_supplier(name = "Null Supplier")
    assert found != []
    assert found[0].contact_channel is None
    assert found[0].contact_address is None