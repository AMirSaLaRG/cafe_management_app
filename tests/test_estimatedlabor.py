import pytest
from datetime import datetime, time
from cafe_managment_models import EstimatedLabor, Shift, TargetPositionAndSalary
from utils import crud_cycle_test


def test_estimatedlabor_crud_cycle(in_memory_db):
    """Test CRUD operations for EstimatedLabor model"""

    # First create required dependencies
    # Create a TargetPositionAndSalary
    position = in_memory_db.add_targetpositionandsalary(
        position="test_manager",
        category="management",
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 12, 31),
        monthly_hr=160,
        monthly_payment=3000.0
    )
    assert position is not None

    # Create a Shift
    shift = in_memory_db.add_shift(
        date=datetime(2024, 1, 15),
        from_hr=time(9, 0),
        to_hr=time(17, 0),
        name="test_shift"
    )
    assert shift is not None

    # Test data
    create_kwargs = {
        'position_id': position.id,
        'shift_id': shift.id,
        'number': 2
    }

    update_kwargs = {
        'number': 3  # Update the number of employees
    }

    # Use the generic CRUD test

    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=EstimatedLabor,
        create_kwargs=create_kwargs,
        update_kwargs=update_kwargs,
        lookup_fields=['position_id', 'shift_id'],
        lookup_values=[position.id, shift.id]
    )


def test_estimatedlabor_negative_number(in_memory_db):
    """Test that negative number is rejected"""
    # Create dependencies first
    position = in_memory_db.add_targetpositionandsalary(
        position="test_position",
        category="test",
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 12, 31)
    )
    shift = in_memory_db.add_shift(
        date=datetime(2024, 1, 15),
        from_hr=time(9, 0),
        to_hr=time(17, 0)
    )

    # Try to create with negative number
    result = in_memory_db.add_estimatedlabor(
        position_id=position.id,
        shift_id=shift.id,
        number=-1
    )

    assert result is None  # Should be rejected


def test_estimatedlabor_nonexistent_dependencies(in_memory_db):
    """Test that non-existent dependencies are rejected"""
    # Try with non-existent position and shift
    result = in_memory_db.add_estimatedlabor(
        position_id=999,  # Doesn't exist
        shift_id=999,  # Doesn't exist
        number=2
    )

    assert result is None  # Should be rejected


def test_estimatedlabor_get_filters(in_memory_db):
    """Test various filter combinations for get_estimatedlabor"""
    # Create multiple records
    position1 = in_memory_db.add_targetpositionandsalary(
        position="position1",
        category="cat1",
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 12, 31)
    )
    position2 = in_memory_db.add_targetpositionandsalary(
        position="position2",
        category="cat2",
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 12, 31)
    )

    shift1 = in_memory_db.add_shift(
        date=datetime(2024, 1, 15),
        from_hr=time(9, 0),
        to_hr=time(17, 0)
    )
    shift2 = in_memory_db.add_shift(
        date=datetime(2024, 1, 16),
        from_hr=time(10, 0),
        to_hr=time(18, 0)
    )

    # Create multiple EstimatedLabor records
    el1 = in_memory_db.add_estimatedlabor(
        position_id=position1.id,
        shift_id=shift1.id,
        number=2
    )
    assert el1 is not None

    el2 = in_memory_db.add_estimatedlabor(
        position_id=position2.id,
        shift_id=shift2.id,
        number=3
    )
    assert el2 is not None

    # Test various filter combinations
    # Get all
    all_records = in_memory_db.get_estimatedlabor()
    assert len(all_records) == 2

    # Filter by position_id
    pos1_records = in_memory_db.get_estimatedlabor(position_id=position1.id)
    assert len(pos1_records) == 1
    assert pos1_records[0].position_id == position1.id

    # Filter by shift_id
    shift1_records = in_memory_db.get_estimatedlabor(shift_id=shift1.id)
    assert len(shift1_records) == 1
    assert shift1_records[0].shift_id == shift1.id

    # Filter by both
    specific_record = in_memory_db.get_estimatedlabor(
        position_id=position1.id,
        shift_id=shift1.id
    )
    assert len(specific_record) == 1
    assert specific_record[0].position_id == position1.id
    assert specific_record[0].shift_id == shift1.id