import pytest
from cafe_managment_models import *
from tests.utils import crud_cycle_test
from datetime import datetime, timedelta


def test_targetpositionandsalary_basic_crud(in_memory_db):
    """Test basic CRUD operations for TargetPositionAndSalary"""
    create_kwargs = {
        "position": "Senior Barista",
        "category": "full-time",
        "from_date": datetime(2024, 1, 1),
        "to_date": datetime(2024, 12, 31),
        "monthly_hr": 160,
        "monthly_payment": 2500.0,
        "monthly_insurance": 200.0,
        "extra_hr_payment": 25.0
    }

    update_kwargs = {
        "monthly_payment": 2600.0,
        "extra_hr_payment": 30.0
    }

    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=TargetPositionAndSalary,
        create_kwargs=create_kwargs,
        update_kwargs=update_kwargs,
        lookup_fields=['position', 'category'],
        lookup_values=['senior barista', 'full-time']
    )


def test_targetpositionandsalary_with_zero_insurance(in_memory_db):
    """Test creating position with zero insurance (should be allowed)"""
    position = in_memory_db.add_targetpositionandsalary(
        position="Intern-barista",
        category="staff",
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 12, 31),
        monthly_hr=80,
        monthly_payment=1000.0,
        monthly_insurance=0.0,  # Zero should be allowed
        extra_hr_payment=15.0
    )
    assert position is not None
    assert position.monthly_insurance == 0.0


def test_targetpositionandsalary_time_overlap_prevention(in_memory_db):
    """Test that time overlaps are prevented for same position"""
    # First position
    position1 = in_memory_db.add_targetpositionandsalary(
        position="Barista",
        category="full-time",
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 6, 30),
        monthly_hr=160,
        monthly_payment=2000.0
    )
    assert position1 is not None

    # Overlapping position - same position (should fail)
    position2 = in_memory_db.add_targetpositionandsalary(
        position="Barista",  # Same position
        category="full-time",
        from_date=datetime(2024, 3, 1),  # Overlaps with first
        to_date=datetime(2024, 9, 30),
        monthly_hr=160,
        monthly_payment=2100.0
    )
    assert position2 is None  # Should fail due to time overlap


def test_targetpositionandsalary_different_positions_same_dates(in_memory_db):
    """Test that different positions can have same dates"""
    # Barista position
    barista = in_memory_db.add_targetpositionandsalary(
        position="Barista",
        category="full-time",
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 12, 31),
        monthly_hr=160,
        monthly_payment=2000.0
    )
    assert barista is not None

    # Manager position - same dates, different position (should work)
    manager = in_memory_db.add_targetpositionandsalary(
        position="Manager",  # Different position
        category="full-time",
        from_date=datetime(2024, 1, 1),  # Same dates
        to_date=datetime(2024, 12, 31),  # Same dates
        monthly_hr=160,
        monthly_payment=3500.0
    )
    assert manager is not None  # Should work - different position


def test_targetpositionandsalary_negative_values(in_memory_db):
    """Test validation for negative values"""
    # Negative monthly payment
    position1 = in_memory_db.add_targetpositionandsalary(
        position="Test Position",
        category="test",
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 12, 31),
        monthly_payment=-1000.0  # Invalid negative
    )
    assert position1 is None

    # Negative insurance
    position2 = in_memory_db.add_targetpositionandsalary(
        position="Test Position",
        category="test",
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 12, 31),
        monthly_insurance=-100.0  # Invalid negative
    )
    assert position2 is None


def test_targetpositionandsalary_string_processing(in_memory_db):
    """Test that string fields are properly processed (lowercase, strip)"""
    create_kwargs = {
        "position": "  SENIOR BARISTA  ",  # With spaces and uppercase
        "category": "  FULL-TIME  ",  # With spaces and uppercase
        "from_date": datetime(2024, 1, 1),
        "to_date": datetime(2024, 12, 31),
        "monthly_hr": 160,
        "monthly_payment": 2500.0
    }

    update_kwargs = {
        "position": "  LEAD BARISTA  ",
        "category": "  PART-TIME  "
    }

    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=TargetPositionAndSalary,
        create_kwargs=create_kwargs,
        update_kwargs=update_kwargs,
        lookup_fields=['position', 'category'],
        lookup_values=['senior barista', 'full-time']  # Should match processed strings
    )


def test_targetpositionandsalary_filtering(in_memory_db):
    """Test filtering functionality"""
    # Create test positions
    positions_data = [
        {"position": "Barista", "category": "full-time", "from_date": datetime(2024, 1, 1),
         "to_date": datetime(2024, 6, 30)},
        {"position": "Barista", "category": "part-time", "from_date": datetime(2024, 7, 1),
         "to_date": datetime(2024, 12, 31)},
        {"position": "Manager", "category": "full-time", "from_date": datetime(2024, 1, 1),
         "to_date": datetime(2024, 12, 31)},
        {"position": "Trainee", "category": "part-time", "from_date": datetime(2024, 4, 15),  # ✅ Starts in Q2
         "to_date": datetime(2024, 12, 31)},
        {"position": "Supervisor", "category": "full-time", "from_date": datetime(2024, 6, 1),  # ✅ Starts in Q2
         "to_date": datetime(2024, 12, 31)},
    ]



    for data in positions_data:
        position = in_memory_db.add_targetpositionandsalary(
            **data,
            monthly_hr=160,
            monthly_payment=2000.0
        )
        assert position is not None


    # Test filtering by position
    barista_positions = in_memory_db.get_targetpositionandsalary(position="barista")
    assert len(barista_positions) == 2

    # Test filtering by category
    full_time_positions = in_memory_db.get_targetpositionandsalary(category="full-time")
    assert len(full_time_positions) == 3

    # Test filtering by date range
    q2_positions = in_memory_db.get_targetpositionandsalary(
        from_date=datetime(2024, 4, 1),
        to_date=datetime(2024, 6, 30)
    )
    assert len(q2_positions) == 2