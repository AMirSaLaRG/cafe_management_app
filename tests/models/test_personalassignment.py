from sqlalchemy.orm import joinedload

from models.cafe_managment_models import *
from tests.utils import crud_cycle_test
from datetime import datetime, time
import pytest


def test_personalassignment_basic_crud(in_memory_db):
    """Test basic CRUD operations for PersonalAssignment"""
    # First create required entities
    personal = in_memory_db.add_personal(
        first_name="John",
        last_name="Doe",
        position="Barista"
    )
    assert personal is not None

    position = in_memory_db.add_targetpositionandsalary(
        position="Senior Barista",
        category="full-time",
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 12, 31),
        monthly_hr=160,
        monthly_payment=2500.0
    )
    assert position is not None

    shift = in_memory_db.add_shift(
        date=datetime(2024, 1, 15),
        from_hr=datetime.strptime("08:00", "%H:%M").time(),
        to_hr=datetime.strptime("16:00", "%H:%M").time(),
        name="Morning Shift"
    )
    assert shift is not None

    create_kwargs = {
        "personal_id": personal.id,
        "position_id": position.id,
        "shift_id": shift.id,
        "active": True
    }

    update_kwargs = {
        "active": False,
        "shift_id": None  # Remove shift assignment
    }

    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=PersonalAssignment,
        create_kwargs=create_kwargs,
        update_kwargs=update_kwargs,
        lookup_fields=['personal_id', 'position_id'],
        lookup_values=[personal.id, position.id]
    )


def test_personalassignment_without_shift(in_memory_db):
    """Test creating assignment without a shift (should be allowed)"""
    personal = in_memory_db.add_personal(
        first_name="Jane",
        last_name="Smith",
        position="Manager"
    )
    assert personal is not None

    position = in_memory_db.add_targetpositionandsalary(
        position="Manager",
        category="full-time",
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 12, 31),
        monthly_hr=160,
        monthly_payment=3500.0
    )
    assert position is not None

    assignment = in_memory_db.add_personalassignment(
        personal_id=personal.id,
        position_id=position.id,
        shift_id=None,  # No shift assigned
        active=True
    )

    assert assignment is not None
    assert assignment.shift_id is None
    assert assignment.active is True


def test_personalassignment_nonexistent_entities(in_memory_db):
    """Test assignment with non-existent entities should fail"""
    # Try with non-existent personal
    assignment1 = in_memory_db.add_personalassignment(
        personal_id=999,  # Doesn't exist
        position_id=1,
        active=True
    )
    assert assignment1 is None

    # Try with non-existent position
    personal = in_memory_db.add_personal(
        first_name="Test",
        last_name="User",
        position="Test"
    )
    assert personal is not None

    assignment2 = in_memory_db.add_personalassignment(
        personal_id=personal.id,
        position_id=999,  # Doesn't exist
        active=True
    )
    assert assignment2 is None

    # Try with non-existent shift
    assignment3 = in_memory_db.add_personalassignment(
        personal_id=personal.id,
        position_id=1,
        shift_id=999,  # Doesn't exist
        active=True
    )
    assert assignment3 is None


def test_personalassignment_duplicate_prevention(in_memory_db):
    """Test that duplicate assignments are prevented"""
    personal = in_memory_db.add_personal(
        first_name="Alice",
        last_name="Johnson",
        position="Barista"
    )
    assert personal is not None

    position = in_memory_db.add_targetpositionandsalary(
        position="Barista",
        category="full-time",
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 12, 31),
        monthly_hr=160,
        monthly_payment=2000.0
    )
    assert position is not None

    # First assignment
    assignment1 = in_memory_db.add_personalassignment(
        personal_id=personal.id,
        position_id=position.id,
        active=True
    )
    assert assignment1 is not None

    # Try duplicate assignment
    assignment2 = in_memory_db.add_personalassignment(
        personal_id=personal.id,
        position_id=position.id,  # Same combination
        active=False
    )
    assert assignment2 is None  # Should fail due to duplicate


def test_personalassignment_filtering(in_memory_db):
    """Test filtering functionality"""
    # Create test data
    personal1 = in_memory_db.add_personal(first_name="John", last_name="Doe", position="Barista")
    personal2 = in_memory_db.add_personal(first_name="Jane", last_name="Smith", position="Manager")

    position1 = in_memory_db.add_targetpositionandsalary(
        position="Barista", category="full-time",
        from_date=datetime(2024, 1, 1), to_date=datetime(2024, 12, 31)
    )
    position2 = in_memory_db.add_targetpositionandsalary(
        position="Manager", category="full-time",
        from_date=datetime(2024, 1, 1), to_date=datetime(2024, 12, 31)
    )

    shift1 = in_memory_db.add_shift(
        date=datetime(2024, 1, 15),
        from_hr=time(8, 0),  # Use time() constructor instead of strptime
        to_hr=time(16, 0)
    )
    shift2 = in_memory_db.add_shift(
        date=datetime(2024, 1, 15),
        from_hr=time(16, 0),
        to_hr=time(23, 59)  # Changed from "24:00" to valid time
    )

    # Create assignments
    assignments_data = [
        {"personal_id": personal1.id, "position_id": position1.id, "shift_id": shift1.id, "active": True},
        {"personal_id": personal1.id, "position_id": position2.id, "shift_id": None, "active": False},
        {"personal_id": personal2.id, "position_id": position2.id, "shift_id": shift2.id, "active": True},
        {"personal_id": personal2.id, "position_id": position1.id, "shift_id": shift1.id, "active": False},
    ]

    for data in assignments_data:
        assignment = in_memory_db.add_personalassignment(**data)
        assert assignment is not None

    # Test filtering by personal_id
    john_assignments = in_memory_db.get_personalassignment(personal_id=personal1.id)
    assert len(john_assignments) == 2

    # Test filtering by position_id
    barista_assignments = in_memory_db.get_personalassignment(position_id=position1.id)
    assert len(barista_assignments) == 2

    # Test filtering by shift_id
    shift1_assignments = in_memory_db.get_personalassignment(shift_id=shift1.id)
    assert len(shift1_assignments) == 2

    # Test filtering by active status
    active_assignments = in_memory_db.get_personalassignment(active=True)
    assert len(active_assignments) == 2

    inactive_assignments = in_memory_db.get_personalassignment(active=False)
    assert len(inactive_assignments) == 2

def test_personalassignment_edit_validation(in_memory_db):
    """Test validation during edit operations"""
    personal = in_memory_db.add_personal(first_name="Test", last_name="User", position="Test")
    position1 = in_memory_db.add_targetpositionandsalary(
        position="Position1", category="test",
        from_date=datetime(2024, 1, 1), to_date=datetime(2024, 12, 31)
    )
    position2 = in_memory_db.add_targetpositionandsalary(
        position="Position2", category="test",
        from_date=datetime(2024, 1, 1), to_date=datetime(2024, 12, 31)
    )

    # Create assignment
    assignment = in_memory_db.add_personalassignment(
        personal_id=personal.id,
        position_id=position1.id,
        active=True
    )
    assert assignment is not None

    # Try to edit with non-existent shift
    assignment.shift_id = 999
    updated = in_memory_db.edit_personalassignment(assignment)
    assert updated is None  # Should fail due to non-existent shift


def test_personalassignment_delete(in_memory_db):
    """Test deletion functionality"""
    personal = in_memory_db.add_personal(first_name="Delete", last_name="Test", position="Test")
    position = in_memory_db.add_targetpositionandsalary(
        position="TestPosition", category="test",
        from_date=datetime(2024, 1, 1), to_date=datetime(2024, 12, 31)
    )

    assignment = in_memory_db.add_personalassignment(
        personal_id=personal.id,
        position_id=position.id,
        active=True
    )
    assert assignment is not None

    # Verify assignment exists
    assignments = in_memory_db.get_personalassignment(
        personal_id=personal.id,
        position_id=position.id
    )
    assert len(assignments) == 1

    # Delete assignment
    result = in_memory_db.delete_personalassignment(assignment)
    assert result is True

    # Verify assignment is gone
    assignments = in_memory_db.get_personalassignment(
        personal_id=personal.id,
        position_id=position.id
    )
    assert len(assignments) == 0


def test_personalassignment_relationships(in_memory_db):
    """Test that relationships work correctly"""
    personal = in_memory_db.add_personal(
        first_name="Relationship",
        last_name="Test",
        position="Tester"
    )
    position = in_memory_db.add_targetpositionandsalary(
        position="Tester",
        category="test",
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 12, 31)
    )
    shift = in_memory_db.add_shift(
        date=datetime(2024, 1, 15),
        from_hr=datetime.strptime("09:00", "%H:%M").time(),
        to_hr=datetime.strptime("17:00", "%H:%M").time()
    )

    assignment = in_memory_db.add_personalassignment(
        personal_id=personal.id,
        position_id=position.id,
        shift_id=shift.id,
        active=True
    )
    assert assignment is not None

    # Test that relationships are accessible
    with in_memory_db.Session() as session:
        full_assignment = session.query(PersonalAssignment).options(
            joinedload(PersonalAssignment.personal),
            joinedload(PersonalAssignment.position),
            joinedload(PersonalAssignment.shift)
        ).filter_by(personal_id=personal.id, position_id=position.id).first()

        assert full_assignment is not None
        assert full_assignment.personal.first_name == "relationship"
        assert full_assignment.position.position == "tester"
        assert full_assignment.shift is not None


