from datetime import datetime, timedelta
from models.cafe_managment_models import Usage
from utils import crud_cycle_test


def test_usage_crud_cycle(in_memory_db):
    """Test complete CRUD cycle for Usage model"""

    # Test data
    create_kwargs = {
        'used_by': '  Test User  ',  # With spaces to test stripping
        'date': datetime.now(),
        'category': '  Test Category  ',  # With spaces to test stripping
        'description': 'Test usage description'
    }

    update_kwargs = {
        'used_by': '  Updated User  ',  # With spaces to test stripping
        'category': '  Updated Category  ',  # With spaces to test stripping
        'description': 'Updated usage description'
    }

    # Run CRUD cycle test
    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=Usage,
        create_kwargs=create_kwargs,
        update_kwargs=update_kwargs,
        lookup_fields=['used_by'],  # Lookup by used_by field
        lookup_values=[create_kwargs['used_by']]  # Use original used_by value for lookup
    )


def test_usage_get_methods(in_memory_db):
    """Test various get_usage filtering options"""

    # Create test usage records
    now = datetime.now()
    usage1 = in_memory_db.add_usage(
        used_by='user_one',
        date=now - timedelta(days=1),
        category='category_a',
        description='First usage'
    )
    assert usage1 is not None

    usage2 = in_memory_db.add_usage(
        used_by='user_two',
        date=now,
        category='category_b',
        description='Second usage'
    )
    assert usage2 is not None

    # Test get by id
    result = in_memory_db.get_usage(id=usage1.id)
    assert len(result) == 1
    assert result[0].id == usage1.id

    # Test get by used_by (case insensitive)
    result = in_memory_db.get_usage(used_by='USER_ONE')
    assert len(result) == 1
    assert result[0].used_by == 'user_one'  # Should be lowercased

    # Test get by category (case insensitive)
    result = in_memory_db.get_usage(category='CATEGORY_A')
    assert len(result) == 1
    assert result[0].category == 'category_a'  # Should be lowercased

    # Test date filtering
    result = in_memory_db.get_usage(from_date=now - timedelta(hours=12))
    assert len(result) >= 1

    # Test row_num limit
    result = in_memory_db.get_usage(row_num=1)
    assert len(result) == 1


def test_usage_string_processing(in_memory_db):
    """Test that string fields are properly processed"""

    # Test with spaces and mixed case
    usage = in_memory_db.add_usage(
        used_by='  MixedCase User  ',  # Should be stripped and lowercased
        category='  MixedCase Category  ',  # Should be stripped and lowercased
        description='Test description'
    )
    assert usage is not None
    assert usage.used_by == 'mixedcase user'  # Should be processed
    assert usage.category == 'mixedcase category'  # Should be processed

    # Test edit with string processing
    usage.used_by = '  UPDATED User  '
    usage.category = '  UPDATED Category  '
    updated = in_memory_db.edit_usage(usage)
    assert updated is not None
    assert updated.used_by == 'updated user'  # Should be processed
    assert updated.category == 'updated category'  # Should be processed


def test_usage_optional_fields(in_memory_db):
    """Test usage creation with optional fields as None"""

    # Should allow None for optional fields
    usage = in_memory_db.add_usage(
        used_by='test_user',
        # category, description are optional
    )
    assert usage is not None
    assert usage.used_by == 'test_user'
    assert usage.category is None
    assert usage.description is None


def test_usage_date_auto_assignment(in_memory_db):
    """Test that date is automatically assigned if not provided"""

    usage = in_memory_db.add_usage(
        used_by='test_user',
        category='test_category'
        # date not provided - should be auto-assigned
    )
    assert usage is not None
    assert usage.date is not None
    assert isinstance(usage.date, datetime)


def test_usage_delete_nonexistent(in_memory_db):
    """Test deleting non-existent usage record"""

    # Create a mock usage object with non-existent ID
    class MockUsage:
        id = 9999

    result = in_memory_db.delete_usage(MockUsage())
    assert result is False  # Should return False for non-existent usage


def test_usage_edit_nonexistent(in_memory_db):
    """Test editing non-existent usage record"""

    # Create a mock usage object with non-existent ID
    class MockUsage:
        id = 9999
        used_by = 'test_user'
        category = 'test_category'

    result = in_memory_db.edit_usage(MockUsage())
    assert result is None  # Should return None for non-existent usage


def test_usage_multiple_filters(in_memory_db):
    """Test combining multiple filters in get_usage"""

    # Create test usage records
    usage1 = in_memory_db.add_usage(
        used_by='john_doe',
        category='cleaning',
        description='Cleaning supplies'
    )

    usage2 = in_memory_db.add_usage(
        used_by='jane_smith',
        category='maintenance',
        description='Maintenance tools'
    )

    # Test combined filters
    result = in_memory_db.get_usage(
        used_by='john_doe',
        category='cleaning'
    )
    assert len(result) == 1
    assert result[0].id == usage1.id

    # Test non-matching combined filters
    result = in_memory_db.get_usage(
        used_by='john_doe',
        category='maintenance'  # Doesn't exist with this combination
    )
    assert len(result) == 0