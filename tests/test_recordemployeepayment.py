import pytest
from datetime import datetime, time, timedelta
from typing import Dict, Any, Optional
from dbhandler import DbHandler
from cafe_managment_models import RecordEmployeePayment, Personal
from utils import crud_cycle_test


class TestRecordEmployeePayment:
    """Test cases for RecordEmployeePayment CRUD operations"""

    @pytest.fixture
    def create_personal(self, in_memory_db: DbHandler) -> Personal:
        """Create a personal record for testing"""
        personal_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'position': 'manager',
            'active': True
        }
        personal = in_memory_db.add_personal(**personal_data)
        assert personal is not None
        return personal

    @pytest.fixture
    def create_kwargs(self, create_personal: Personal) -> Dict[str, Any]:
        """Create kwargs for RecordEmployeePayment"""
        return {
            'personal_id': create_personal.id,
            'from_date': datetime(2024, 1, 1),
            'to_date': datetime(2024, 1, 31),
            'payment': 2500.0,
            'insurance': 200.0,
            'work_hr': 160.0,
            'extra_hr': 10.0,
            'extra_expenses': 50.0,
            'description': 'Monthly salary payment'
        }

    @pytest.fixture
    def update_kwargs(self) -> Dict[str, Any]:
        """Update kwargs for RecordEmployeePayment"""
        return {
            'payment': 2600.0,
            'insurance': 220.0,
            'work_hr': 165.0,
            'extra_hr': 15.0,
            'extra_expenses': 60.0,
            'description': 'Updated monthly salary with bonus'
        }

    def test_crud_cycle_recordemployeepayment(self, in_memory_db: DbHandler,
                                              create_kwargs: Dict[str, Any],
                                              update_kwargs: Dict[str, Any]):
        """Test complete CRUD cycle for RecordEmployeePayment"""
        crud_cycle_test(
            db_handler=in_memory_db,
            model_class=RecordEmployeePayment,
            create_kwargs=create_kwargs,
            update_kwargs=update_kwargs,
            lookup_fields=['personal_id', 'from_date'],
            lookup_values=[create_kwargs['personal_id'], create_kwargs['from_date']]
        )

    def test_add_recordemployeepayment_invalid_personal_id(self, in_memory_db: DbHandler):
        """Test adding RecordEmployeePayment with invalid personal_id"""
        invalid_data = {
            'personal_id': 9999,  # Non-existent personal ID
            'from_date': datetime(2024, 1, 1),
            'to_date': datetime(2024, 1, 31),
            'payment': 2500.0
        }

        result = in_memory_db.add_recordemployeepayment(**invalid_data)
        assert result is None

    def test_add_recordemployeepayment_negative_values(self, in_memory_db: DbHandler, create_personal: Personal):
        """Test adding RecordEmployeePayment with negative values"""
        negative_data = {
            'personal_id': create_personal.id,
            'from_date': datetime(2024, 1, 1),
            'to_date': datetime(2024, 1, 31),
            'payment': -100.0,  # Negative value
            'work_hr': 160.0
        }

        result = in_memory_db.add_recordemployeepayment(**negative_data)
        assert result is None

    def test_add_recordemployeepayment_invalid_dates(self, in_memory_db: DbHandler, create_personal: Personal):
        """Test adding RecordEmployeePayment with invalid date range"""
        invalid_date_data = {
            'personal_id': create_personal.id,
            'from_date': datetime(2024, 2, 1),  # Later than to_date
            'to_date': datetime(2024, 1, 31),  # Earlier than from_date
            'payment': 2500.0
        }

        result = in_memory_db.add_recordemployeepayment(**invalid_date_data)
        assert result is None

    def test_get_recordemployeepayment_by_personal_id(self, in_memory_db: DbHandler, create_kwargs: Dict[str, Any]):
        """Test getting RecordEmployeePayment by personal_id"""
        # Create the record
        record = in_memory_db.add_recordemployeepayment(**create_kwargs)
        assert record is not None

        # Get by personal_id
        results = in_memory_db.get_recordemployeepayment(personal_id=create_kwargs['personal_id'])
        assert len(results) == 1
        assert results[0].personal_id == create_kwargs['personal_id']
        assert results[0].payment == create_kwargs['payment']

    def test_get_recordemployeepayment_by_date_range(self, in_memory_db: DbHandler, create_kwargs: Dict[str, Any]):
        """Test getting RecordEmployeePayment by date range"""
        # Create the record
        record = in_memory_db.add_recordemployeepayment(**create_kwargs)
        assert record is not None

        # Get by date range
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 2, 1)
        results = in_memory_db.get_recordemployeepayment(
            personal_id=create_kwargs['personal_id'],
            from_date=start_date,
            to_date=end_date
        )

        assert len(results) == 1
        assert results[0].from_date == create_kwargs['from_date']

    def test_get_recordemployeepayment_by_id(self, in_memory_db: DbHandler, create_kwargs: Dict[str, Any]):
        """Test getting RecordEmployeePayment by ID"""
        # Create the record
        record = in_memory_db.add_recordemployeepayment(**create_kwargs)
        assert record is not None

        # Get by ID
        results = in_memory_db.get_recordemployeepayment(id=record.id)
        assert len(results) == 1
        assert results[0].id == record.id

    def test_time_overlap_prevention(self, in_memory_db: DbHandler, create_personal: Personal):
        """Test that overlapping time periods are prevented"""
        # Create first record
        record1_data = {
            'personal_id': create_personal.id,
            'from_date': datetime(2024, 1, 1),
            'to_date': datetime(2024, 1, 15),
            'payment': 1250.0
        }

        record1 = in_memory_db.add_recordemployeepayment(**record1_data)
        assert record1 is not None

        # Try to create overlapping record
        record2_data = {
            'personal_id': create_personal.id,
            'from_date': datetime(2024, 1, 10),  # Overlaps with record1
            'to_date': datetime(2024, 1, 20),  # Overlaps with record1
            'payment': 1300.0
        }

        record2 = in_memory_db.add_recordemployeepayment(**record2_data)
        assert record2 is None  # Should be prevented

    def test_non_overlapping_records_allowed(self, in_memory_db: DbHandler, create_personal: Personal):
        """Test that non-overlapping records are allowed"""
        # Create first record
        record1_data = {
            'personal_id': create_personal.id,
            'from_date': datetime(2024, 1, 1),
            'to_date': datetime(2024, 1, 15),
            'payment': 1250.0
        }

        record1 = in_memory_db.add_recordemployeepayment(**record1_data)
        assert record1 is not None

        # Create non-overlapping record
        record2_data = {
            'personal_id': create_personal.id,
            'from_date': datetime(2024, 2, 1),  # After record1
            'to_date': datetime(2024, 2, 15),  # After record1
            'payment': 1300.0
        }

        record2 = in_memory_db.add_recordemployeepayment(**record2_data)
        assert record2 is not None  # Should be allowed

    def test_edit_recordemployeepayment_time_overlap_prevention(self, in_memory_db: DbHandler,
                                                                create_personal: Personal):
        """Test that editing to create time overlap is prevented"""
        # Create first record
        record1_data = {
            'personal_id': create_personal.id,
            'from_date': datetime(2024, 1, 1),
            'to_date': datetime(2024, 1, 15),
            'payment': 1250.0
        }

        record1 = in_memory_db.add_recordemployeepayment(**record1_data)
        assert record1 is not None

        # Create second record (non-overlapping initially)
        record2_data = {
            'personal_id': create_personal.id,
            'from_date': datetime(2024, 2, 1),
            'to_date': datetime(2024, 2, 15),
            'payment': 1300.0
        }

        record2 = in_memory_db.add_recordemployeepayment(**record2_data)
        assert record2 is not None

        # Try to edit second record to overlap with first
        record2.from_date = datetime(2024, 1, 10)  # Now overlaps with record1
        record2.to_date = datetime(2024, 1, 20)  # Now overlaps with record1

        updated = in_memory_db.edit_recordemployeepayment(record2)
        assert updated is None  # Should be prevented


if __name__ == "__main__":
    pytest.main([__file__, "-v"])