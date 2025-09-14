import pytest
from models.cafe_managment_models import *
from tests.utils import crud_cycle_test
from datetime import datetime


@pytest.fixture
def setup_test_data(in_memory_db):
    """Setup fixture with test data for Bills tests"""
    return in_memory_db


def test_bills_basic_crud(in_memory_db, setup_test_data):
    """Test basic CRUD operations for Bills"""
    create_kwargs = {
        "name": "Rent Payment",
        "category": "rent",
        "from_date": datetime(2024, 1, 1),
        "to_date": datetime(2024, 12, 31),
        "cost": 1500.0,
        "payer": "Company ABC",
        "description": "Monthly rent payment"
    }

    update_kwargs = {
        "cost": 1600.0,
        "payer": "Updated Company",
        "description": "Updated rent payment with increase"
    }

    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=Bills,
        create_kwargs=create_kwargs,
        update_kwargs=update_kwargs,
        lookup_fields=['name', 'category', 'payer'],
        lookup_values=['rent payment', 'rent', 'company abc']
    )


def test_bills_time_overlap_prevention(in_memory_db, setup_test_data):
    """Test that time overlaps are prevented for same name bills"""
    # First bill
    bill1 = in_memory_db.add_bills(
        name="Rent Q1",
        category="rent",
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 3, 31),
        cost=1500.0,
        payer="Landlord"
    )
    assert bill1 is not None

    # Overlapping bill - same name (should fail)
    bill2 = in_memory_db.add_bills(
        name="Rent Q1",  # Same name
        category="rent",
        from_date=datetime(2024, 3, 15),  # Overlaps with Q1
        to_date=datetime(2024, 6, 30),
        cost=1500.0,
        payer="Landlord"
    )
    assert bill2 is None  # Should fail due to time overlap with same name


def test_bills_no_overlap_different_names(in_memory_db, setup_test_data):
    """Test that different names can have overlapping dates"""
    # Rent bill
    rent = in_memory_db.add_bills(
        name="Rent Payment",
        category="rent",
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 12, 31),
        cost=1500.0,
        payer="Company A"
    )
    assert rent is not None

    # Utilities bill - same dates, different name (should work)
    utilities = in_memory_db.add_bills(
        name="Utilities Payment",  # Different name
        category="utilities",
        from_date=datetime(2024, 1, 1),  # Same dates
        to_date=datetime(2024, 12, 31),  # Same dates
        cost=300.0,
        payer="Company B"
    )
    assert utilities is not None  # Should work - different name


def test_bills_invalid_inputs(in_memory_db, setup_test_data):
    """Test validation for invalid inputs"""
    # Negative cost
    bill1 = in_memory_db.add_bills(
        name="Test Bill",
        category="test",
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 12, 31),
        cost=-100.0,  # Invalid negative cost
        payer="Test Payer"
    )
    assert bill1 is None

    # from_date after to_date
    bill2 = in_memory_db.add_bills(
        name="Test Bill",
        category="test",
        from_date=datetime(2024, 12, 31),  # After to_date
        to_date=datetime(2024, 1, 1),  # Before from_date
        cost=100.0,
        payer="Test Payer"
    )
    assert bill2 is None


def test_bills_filtering(in_memory_db, setup_test_data):
    """Test filtering functionality"""
    # Create test bills
    bills_data = [
        {"name": "Rent Jan-Mar", "category": "rent", "from_date": datetime(2024, 1, 1),
         "to_date": datetime(2024, 3, 31), "cost": 1500, "payer": "Landlord A"},
        {"name": "Rent Apr-Jun", "category": "rent", "from_date": datetime(2024, 4, 1),
         "to_date": datetime(2024, 6, 30), "cost": 1500, "payer": "Landlord A"},
        {"name": "Electricity", "category": "utilities", "from_date": datetime(2024, 1, 1),
         "to_date": datetime(2024, 12, 31), "cost": 200, "payer": "Power Company"},
    ]

    for data in bills_data:
        bill = in_memory_db.add_bills(**data)
        assert bill is not None

    # Test filtering by category
    rent_bills = in_memory_db.get_bills(category="rent")
    assert len(rent_bills) == 2

    # Test filtering by payer
    landlord_bills = in_memory_db.get_bills(payer="landlord a")
    assert len(landlord_bills) == 2

    # Test filtering by date range
    q1_bills = in_memory_db.get_bills(from_date=datetime(2024, 1, 1))
    assert len(q1_bills) == 3


def test_bills_string_processing(in_memory_db, setup_test_data):
    """Test that string fields are properly processed (lowercase, strip)"""
    create_kwargs = {
        "name": "  ELECTRICITY BILL  ",  # With spaces and uppercase
        "category": "  UTILITIES  ",  # With spaces and uppercase
        "payer": "  POWER COMPANY  ",  # With spaces and uppercase
        "from_date": datetime(2024, 1, 1),
        "to_date": datetime(2024, 12, 31),
        "cost": 200.0
    }

    update_kwargs = {
        "name": "  UPDATED ELECTRICITY  ",
        "category": "  UPDATED UTILITIES  ",
        "payer": "  UPDATED POWER CO  "
    }

    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=Bills,
        create_kwargs=create_kwargs,
        update_kwargs=update_kwargs,
        lookup_fields=['name', 'category', 'payer'],
        lookup_values=['electricity bill', 'utilities', 'power company']
    )


def test_bills_without_optional_fields(in_memory_db, setup_test_data):
    """Test creating bills without optional fields"""
    bill = in_memory_db.add_bills(
        name="Miscellaneous",
        category="other",
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 12, 31),
        cost=None,  # No cost provided
        payer=None,  # No payer provided
        description="Miscellaneous expenses"
    )
    assert bill is not None
    assert bill.cost is None
    assert bill.payer is None


def test_bills_case_insensitive_lookup(in_memory_db, setup_test_data):
    """Test that lookups are case-insensitive due to string processing"""
    bill = in_memory_db.add_bills(
        name="Internet Bill",
        category="Services",
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 12, 31),
        cost=100.0,
        payer="ISP Company"
    )
    assert bill is not None

    # Should find with different case
    found = in_memory_db.get_bills(
        name="INTERNET BILL",
        category="services",
        payer="isp company"
    )
    assert len(found) == 1
    assert found[0].id == bill.id


def test_bills_edit_with_overlap_check(in_memory_db, setup_test_data):
    """Test editing bills with overlap checking"""
    # Create initial bills
    bill1 = in_memory_db.add_bills(
        name="Bill A",
        category="test",
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 3, 31),
        cost=100.0,
        payer="Test"
    )
    assert bill1 is not None

    bill2 = in_memory_db.add_bills(
        name="Bill B",
        category="test",
        from_date=datetime(2024, 4, 1),
        to_date=datetime(2024, 6, 30),
        cost=100.0,
        payer="Test"
    )
    assert bill2 is not None

    # Try to edit bill2 to overlap with bill1 (should fail)
    bill2.name = "Bill A"  # Change to same name as bill1
    bill2.from_date = datetime(2024, 3, 15)  # Overlap with bill1

    result = in_memory_db.edit_bills(bill2)
    assert result is None  # Should fail due to overlap