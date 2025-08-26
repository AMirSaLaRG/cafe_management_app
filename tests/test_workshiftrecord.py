import pytest
from datetime import datetime, time, timedelta
from cafe_managment_models import Personal, WorkShiftRecord
from utils import crud_cycle_test

def test_crud_cycle_personal(in_memory_db):
    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=Personal,
        create_kwargs=dict(
            first_name="Alice",
            last_name="Smith",
            nationality_code="N123",
            email="alice@example.com",
            phone="12345",
            address="Street 1",
            hire_date=datetime(2023, 5, 1),
            position="Manager",
            active=True,
            description="First test employee"
        ),
        update_kwargs=dict(
            first_name="Alicia",
            last_name="Smithy",
            position="senior manager",
            description="Updated desc"
        ),
        lookup_fields=["first_name", "last_name"],
        lookup_values=["Alice", "Smith"]
    )

def test_crud_cycle_workshiftrecord(in_memory_db):
    # First create a Personal (because WorkShiftRecord requires a valid personal_id)
    personal = in_memory_db.add_personal(
        first_name="Tester",
        last_name="One",
        nationality_code="T999",
        email="tester@example.com",
        phone="555-123",
        address="Somewhere",
        hire_date=datetime(2023, 1, 1),
        position="Cashier",
        active=True,
        description="Sample employee"
    )

    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=WorkShiftRecord,
        create_kwargs=dict(
            personal_id=personal.id,
            date=datetime(2023, 6, 1),
            start_hr=time(9, 0),
            end_hr=time(17, 0),
            worked_hr=8.0,
            lunch_payed=1.0,
            service_payed=2.0,
            extra_payed=0.0,
            description="Regular shift"
        ),
        update_kwargs=dict(
            end_hr=time(18, 0),
            worked_hr=9.0,
            description="Extended shift"
        ),
        lookup_fields=["from_date", "personal_id"],
        lookup_values=[datetime(2023, 6, 1), personal.id]
    )


# Test data
@pytest.fixture
def personal_data():
    return {
        'first_name': 'John',
        'last_name': 'Doe',
        'position': 'waiter',
        'nationality_code': '1234567890'
    }


@pytest.fixture
def workshift_create_data():
    now = datetime.now()
    return {
        'personal_id': 1,  # Will be set after creating personal
        'date': datetime(now.year, now.month, now.day),
        'start_hr': time(9, 0),
        'end_hr': time(17, 0),
        'worked_hr': 8.0,
        'lunch_payed': 1.0,
        'service_payed': 0.5,
        'extra_payed': 0.0,
        'description': 'Regular shift'
    }


@pytest.fixture
def workshift_update_data():
    return {
        'worked_hr': 7.5,
        'lunch_payed': 1.5,
        'service_payed': 1.0,
        'description': 'Updated shift details'
    }


class TestWorkShiftRecord:
    def test_crud_cycle(self, in_memory_db, personal_data, workshift_create_data, workshift_update_data):
        # First create a personal record to reference
        personal = in_memory_db.add_personal(**personal_data)
        assert personal is not None
        workshift_create_data['personal_id'] = personal.id

        # Test the CRUD cycle
        crud_cycle_test(
            db_handler=in_memory_db,
            model_class=WorkShiftRecord,
            create_kwargs=workshift_create_data,
            update_kwargs=workshift_update_data,
            lookup_fields=['personal_id', 'from_date'],
            lookup_values=[personal.id, workshift_create_data['date']]
        )

    def test_time_validation(self, in_memory_db, personal_data, workshift_create_data):
        # Create personal record
        personal = in_memory_db.add_personal(**personal_data)
        assert personal is not None

        # Test start time after end time
        invalid_data = workshift_create_data.copy()
        invalid_data['personal_id'] = personal.id
        invalid_data['start_hr'] = time(18, 0)
        invalid_data['end_hr'] = time(9, 0)

        result = in_memory_db.add_workshiftrecord(**invalid_data)
        assert result is None

    def test_time_overlap_prevention(self, in_memory_db, personal_data, workshift_create_data):
        # Create personal record
        personal = in_memory_db.add_personal(**personal_data)
        assert personal is not None

        # Create first shift
        shift1_data = workshift_create_data.copy()
        shift1_data['personal_id'] = personal.id
        shift1 = in_memory_db.add_workshiftrecord(**shift1_data)
        assert shift1 is not None

        # Try to create overlapping shift
        shift2_data = workshift_create_data.copy()
        shift2_data['personal_id'] = personal.id
        shift2_data['start_hr'] = time(14, 0)
        shift2_data['end_hr'] = time(19, 0)

        result = in_memory_db.add_workshiftrecord(**shift2_data)
        assert result is None

    def test_negative_values_validation(self, in_memory_db, personal_data, workshift_create_data):
        # Create personal record
        personal = in_memory_db.add_personal(**personal_data)
        assert personal is not None

        # Test negative worked hours
        invalid_data = workshift_create_data.copy()
        invalid_data['personal_id'] = personal.id
        invalid_data['worked_hr'] = -5.0

        result = in_memory_db.add_workshiftrecord(**invalid_data)
        assert result is None

    def test_get_with_filters(self, in_memory_db, personal_data, workshift_create_data):
        # Create personal record
        personal = in_memory_db.add_personal(**personal_data)
        assert personal is not None

        # Create shift record
        shift_data = workshift_create_data.copy()
        shift_data['personal_id'] = personal.id
        shift = in_memory_db.add_workshiftrecord(**shift_data)
        assert shift is not None

        # Test get by ID
        result = in_memory_db.get_workshiftrecord(id=shift.id)
        assert len(result) == 1
        assert result[0].id == shift.id

        # Test get by personal_id
        result = in_memory_db.get_workshiftrecord(personal_id=personal.id)
        assert len(result) == 1
        assert result[0].personal_id == personal.id

        # Test get by time range
        from_time = time(8, 0)
        to_time = time(18, 0)
        result = in_memory_db.get_workshiftrecord(from_hr=from_time, to_hr=to_time)
        assert len(result) == 1

        # Test get by date range
        from_date = datetime.now() - timedelta(days=1)
        to_date = datetime.now() + timedelta(days=1)
        result = in_memory_db.get_workshiftrecord(from_date=from_date, to_date=to_date)
        assert len(result) == 1

    def test_nonexistent_personal_id(self, in_memory_db, workshift_create_data):
        # Try to create shift with non-existent personal ID
        invalid_data = workshift_create_data.copy()
        invalid_data['personal_id'] = 999  # Non-existent ID

        result = in_memory_db.add_workshiftrecord(**invalid_data)
        assert result is None