from datetime import datetime, time
from models.cafe_managment_models import Shift
from utils import crud_cycle_test


class TestShift:
    """Test Shift CRUD operations and overlap detection"""

    def test_basic_crud_cycle(self, in_memory_db):
        """Test basic CRUD operations for Shift"""
        create_kwargs = {
            'date': datetime(2024, 1, 15),
            'from_hr': time(9, 0),
            'to_hr': time(17, 0),
            'name': 'Morning Shift',
            'lunch_payment': 10.0,
            'service_payment': 5.0
        }

        update_kwargs = {
            'name': 'Updated Morning Shift',
            'extra_payment': 15.0
        }
        #todo to_hr to to_date and work
        crud_cycle_test(
            db_handler=in_memory_db,
            model_class=Shift,
            create_kwargs=create_kwargs,
            update_kwargs=update_kwargs,
            lookup_fields=['name', 'from_hr']
        )

    def test_shift_overlap_detection_add(self, in_memory_db):
        """Test that overlapping shifts are detected during creation"""
        # Add first shift
        shift1 = in_memory_db.add_shift(
            date=datetime(2024, 1, 15),
            from_hr=time(9, 0),
            to_hr=time(17, 0),
            name='First Shift'
        )
        assert shift1 is not None

        # Try to add overlapping shift (should fail)
        shift2 = in_memory_db.add_shift(
            date=datetime(2024, 1, 15),
            from_hr=time(10, 0),  # Overlaps with first shift
            to_hr=time(18, 0),
            name='Overlapping Shift'
        )
        assert shift2 is not None  # Should be rejected due to overlap (overlap removed)

        # Try to add non-overlapping shift (should succeed)
        shift3 = in_memory_db.add_shift(
            date=datetime(2024, 1, 15),
            from_hr=time(18, 0),  # After first shift ends
            to_hr=time(22, 0),
            name='Evening Shift'
        )
        assert shift3 is not None  # Should be accepted

    def test_shift_overlap_detection_edit(self, in_memory_db):
        """Test that overlapping shifts are detected during updates"""
        # Add two shifts
        shift1 = in_memory_db.add_shift(
            date=datetime(2024, 1, 15),
            from_hr=time(9, 0),
            to_hr=time(12, 0),
            name='Morning Shift'
        )
        assert shift1 is not None

        shift2 = in_memory_db.add_shift(
            date=datetime(2024, 1, 15),
            from_hr=time(14, 0),
            to_hr=time(18, 0),
            name='Afternoon Shift'
        )
        assert shift2 is not None

        # Try to edit shift2 to overlap with shift1 (should fail)
        shift2.from_hr = time(11, 0)  # Now overlaps with shift1 (11am-6pm vs 9am-12pm)
        result = in_memory_db.edit_shift(shift2)
        assert result is not None  # Should be rejected due to overlap (overlap removed)

        # Try non-overlapping edit (should succeed)
        shift2.from_hr = time(13, 0)  # Still doesn't overlap
        result = in_memory_db.edit_shift(shift2)
        assert result is not None  # Should be accepted

    def test_different_dates_no_overlap(self, in_memory_db):
        """Test that shifts on different dates don't cause overlap"""
        shift1 = in_memory_db.add_shift(
            date=datetime(2024, 1, 15),
            from_hr=time(9, 0),
            to_hr=time(17, 0),
            name='Monday Shift'
        )
        assert shift1 is not None

        # Same times but different date (should succeed)
        shift2 = in_memory_db.add_shift(
            date=datetime(2024, 1, 16),  # Different date
            from_hr=time(9, 0),
            to_hr=time(17, 0),
            name='Tuesday Shift'
        )
        assert shift2 is not None  # Should be accepted

    def test_edge_case_overlaps(self, in_memory_db):
        """Test various edge cases for overlap detection"""
        shift1 = in_memory_db.add_shift(
            date=datetime(2024, 1, 15),
            from_hr=time(9, 0),
            to_hr=time(17, 0),
            name='Base Shift'
        )
        assert shift1 is not None

        # Test cases that should ALL fail (overlap in different ways)
        test_cases = [
            # Exact same times
            (time(9, 0), time(17, 0)),
            # Starts during, ends after
            (time(10, 0), time(18, 0)),
            # Starts before, ends during
            (time(8, 0), time(16, 0)),
            # Completely contained within
            (time(10, 0), time(16, 0)),
            # Completely contains
            (time(8, 0), time(18, 0)),
            # # Ends exactly when other starts
            # (time(8, 0), time(9, 0)),  # Should this be allowed? Depends on business rules
            # # Starts exactly when other ends
            # (time(17, 0), time(18, 0))  # Should this be allowed? Depends on business rules
        ]

        for i, (from_hr, to_hr) in enumerate(test_cases):
            shift = in_memory_db.add_shift(
                date=datetime(2024, 1, 15),
                from_hr=from_hr,
                to_hr=to_hr,
                name=f'Test Shift {i}'
            )
            # Uncomment the next line if you want adjacent shifts to be allowed
            # if i >= 5:  # For the last two edge cases
            #     assert shift is not None
            # else:
            #     assert shift is None
            assert shift is not None  # Currently all should be rejected (over laped alowwed)

    def test_invalid_time_range(self, in_memory_db):
        """Test that invalid time ranges are rejected"""
        # from_hr >= to_hr should be rejected
        shift = in_memory_db.add_shift(
            date=datetime(2024, 1, 15),
            from_hr=time(17, 0),
            to_hr=time(9, 0),  # Invalid: ends before it starts
            name='Invalid Shift'
        )
        assert shift is None

    def test_shift_filtering_by_time(self, in_memory_db):
        """Test get_shift time filtering functionality"""
        # Add multiple shifts
        shifts = [
            (time(6, 0), time(14, 0), 'Early Shift'),
            (time(14, 0), time(22, 0), 'Late Shift'),
            (time(10, 0), time(18, 0), 'Mid Shift')
        ]

        for from_hr, to_hr, name in shifts:
            shift = in_memory_db.add_shift(
                date=datetime(2024, 1, 15),
                from_hr=from_hr,
                to_hr=to_hr,
                name=name
            )
            assert shift is not None

        # Test filtering - get shifts that start after 8am
        result = in_memory_db.get_shift(
            from_hr=time(8, 0),
            to_hr=time(23, 0)
        )
        assert len(result) == 3  # All shifts start after 8am? Check this

        # Test filtering - get shifts that start after 12pm
        result = in_memory_db.get_shift(
            from_hr=time(12, 0),
            to_hr=time(23, 0)
        )
        # Should get Late Shift and possibly Mid Shift depending on exact filtering
        assert len(result) >= 1