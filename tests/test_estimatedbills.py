import pytest
from models.cafe_managment_models import *
from tests.utils import crud_cycle_test
from datetime import datetime


@pytest.fixture
def setup_test_data(in_memory_db):
    """Setup fixture with test data for EstimatedBills tests"""
    # No need to setup other models since EstimatedBills is standalone
    return in_memory_db


def test_estimatedbills_basic_crud(in_memory_db, setup_test_data):
    """Test basic CRUD operations for EstimatedBills"""
    create_kwargs = {
        "name": "Rent Payment",
        "category": "rent",
        "from_date": datetime(2024, 1, 1),
        "to_date": datetime(2024, 12, 31),
        "cost": 1500.0,
        "description": "Monthly rent payment"
    }

    update_kwargs = {
        "cost": 1600.0,
        "description": "Updated rent payment with increase"
    }

    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=EstimatedBills,
        create_kwargs=create_kwargs,
        update_kwargs=update_kwargs,
        lookup_fields=['name', 'category'],
        lookup_values=['rent payment', 'rent']
    )


def test_estimatedbills_multiple_categories(in_memory_db, setup_test_data):
    """Test creating bills in different categories with same dates"""
    # Electricity bill
    electricity = in_memory_db.add_estimatedbills(
        name="Electricity",
        category="utilities",
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 12, 31),
        cost=200.0
    )
    assert electricity is not None

    # Internet bill - same dates, different category (should work)
    internet = in_memory_db.add_estimatedbills(
        name="Internet",
        category="services",
        from_date=datetime(2024, 1, 1),  # Same dates
        to_date=datetime(2024, 12, 31),  # Same dates
        cost=100.0
    )
    assert internet is not None  # Should work - different category


def test_estimatedbills_time_overlap_prevention(in_memory_db, setup_test_data):
    """Test that time overlaps are prevented within same category"""
    # First bill
    bill1 = in_memory_db.add_estimatedbills(
        name="Rent Q1",
        category="rent",
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 3, 31),
        cost=1500.0
    )
    assert bill1 is not None

    # Overlapping bill - same category (should fail)
    bill2 = in_memory_db.add_estimatedbills(
        name="Rent Q2",
        category="rent",  # Same category
        from_date=datetime(2024, 3, 15),  # Overlaps with Q1
        to_date=datetime(2024, 6, 30),
        cost=1500.0
    )
    assert bill2 is None  # Should fail due to time overlap


def test_estimatedbills_no_overlap_different_categories(in_memory_db, setup_test_data):
    """Test that different categories can have overlapping dates"""
    # Rent bill
    rent = in_memory_db.add_estimatedbills(
        name="Rent",
        category="rent",
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 12, 31),
        cost=1500.0
    )
    assert rent is not None

    # Utilities bill - same dates, different category (should work)
    utilities = in_memory_db.add_estimatedbills(
        name="Utilities",
        category="utilities",  # Different category
        from_date=datetime(2024, 1, 1),  # Same dates
        to_date=datetime(2024, 12, 31),  # Same dates
        cost=300.0
    )
    assert utilities is not None  # Should work - different category


def test_estimatedbills_invalid_inputs(in_memory_db, setup_test_data):
    """Test validation for invalid inputs"""
    # Negative cost
    bill1 = in_memory_db.add_estimatedbills(
        name="Test Bill",
        category="test",
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 12, 31),
        cost=-100.0  # Invalid negative cost
    )
    assert bill1 is None

    # from_date after to_date
    bill2 = in_memory_db.add_estimatedbills(
        name="Test Bill",
        category="test",
        from_date=datetime(2024, 12, 31),  # After to_date
        to_date=datetime(2024, 1, 1),  # Before from_date
        cost=100.0
    )
    assert bill2 is None


def test_estimatedbills_filtering(in_memory_db, setup_test_data):
    """Test filtering functionality"""
    # Create test bills
    bills_data = [
        {"name": "Rent Jan-Mar", "category": "rent", "from_date": datetime(2024, 1, 1),
         "to_date": datetime(2024, 3, 31), "cost": 1500},
        {"name": "Rent Apr-Jun", "category": "rent", "from_date": datetime(2024, 4, 1),
         "to_date": datetime(2024, 6, 30), "cost": 1500},
        {"name": "Electricity", "category": "utilities", "from_date": datetime(2024, 1, 1),
         "to_date": datetime(2024, 12, 31), "cost": 200},
    ]

    for data in bills_data:
        bill = in_memory_db.add_estimatedbills(**data)
        assert bill is not None

    # Test filtering by category
    rent_bills = in_memory_db.get_estimatedbills(category="rent")
    assert len(rent_bills) == 2
    # Test filtering by date range

    q1_bills = in_memory_db.get_estimatedbills(
        from_date=datetime(2024, 1, 1),
        # to_date=datetime(2024, 3, 31)
    )
    assert len(q1_bills) == 3  # Rent Jan-Mar + Electricity (spans entire year)

    # Test filtering by name
    electricity_bills = in_memory_db.get_estimatedbills(name="electricity")
    assert len(electricity_bills) == 1


def test_estimatedbills_string_processing(in_memory_db, setup_test_data):
    """Test that string fields are properly processed (lowercase, strip)"""
    create_kwargs = {
        "name": "  ELECTRICITY BILL  ",  # With spaces and uppercase
        "category": "  UTILITIES  ",  # With spaces and uppercase
        "from_date": datetime(2024, 1, 1),
        "to_date": datetime(2024, 12, 31),
        "cost": 200.0
    }

    update_kwargs = {
        "name": "  UPDATED ELECTRICITY  ",
        "category": "  UPDATED UTILITIES  "
    }

    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=EstimatedBills,
        create_kwargs=create_kwargs,
        update_kwargs=update_kwargs,
        lookup_fields=['name', 'category'],
        lookup_values=['electricity bill', 'utilities']  # Should match processed strings
    )


def test_estimatedbills_without_cost(in_memory_db, setup_test_data):
    """Test creating bills without cost (should be allowed since cost is Optional)"""
    bill = in_memory_db.add_estimatedbills(
        name="Miscellaneous",
        category="other",
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 12, 31),
        cost=None,  # No cost provided
        description="Miscellaneous expenses"
    )
    assert bill is not None
    assert bill.cost is None


def test_estimatedbills_case_insensitive_lookup(in_memory_db, setup_test_data):
    """Test that lookups are case-insensitive due to string processing"""
    bill = in_memory_db.add_estimatedbills(
        name="Internet Bill",
        category="Services",
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 12, 31),
        cost=100.0
    )
    assert bill is not None

    # Should find with different case
    found = in_memory_db.get_estimatedbills(name="INTERNET BILL", category="services")
    assert len(found) == 1
    assert found[0].id == bill.id