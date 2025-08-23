import pytest
from datetime import datetime
from cafe_managment_models import MenuUsage, Menu, Usage
from utils import crud_cycle_test

@pytest.fixture
def setup_menu_usage_data(in_memory_db):
    """Setup required test data for menu usage tests"""
    # Create a menu item first
    menu = in_memory_db.add_menu(
        name='Test Cappuccino',
        size='medium',
        category='drinks',
        current_price=4.99,
        value_added_tax=0.08,
        serving=True
    )
    assert menu is not None

    # Create a usage record
    usage = in_memory_db.add_usage(
        used_by='test_barista',
        category='preparation',
        description='Test drink preparation usage'
    )
    assert usage is not None

    return {
        'menu_id': menu.id,
        'usage_id': usage.id,
        'menu': menu,
        'usage': usage
    }


def test_menuusage_crud_cycle(in_memory_db, setup_menu_usage_data):
    """Test complete CRUD cycle for MenuUsage model"""

    # Test data
    create_kwargs = {
        'menu_id': setup_menu_usage_data['menu_id'],
        'usage_id': setup_menu_usage_data['usage_id'],
        'amount': 5
    }

    update_kwargs = {
        'amount': 8
    }

    # Run CRUD cycle test - MenuUsage uses composite key
    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=MenuUsage,
        create_kwargs=create_kwargs,
        update_kwargs=update_kwargs,
        lookup_fields=['menu_id', 'usage_id'],  # Composite key lookup
        lookup_values=[setup_menu_usage_data['menu_id'], setup_menu_usage_data['usage_id']]
    )


def test_menuusage_get_methods(in_memory_db, setup_menu_usage_data):
    """Test various get_menuusage filtering options"""

    # Create test menu usage records
    menu_usage1 = in_memory_db.add_menuusage(
        menu_id=setup_menu_usage_data['menu_id'],
        usage_id=setup_menu_usage_data['usage_id'],
        amount=5
    )
    assert menu_usage1 is not None

    # Create another usage and menu usage for different filtering
    usage2 = in_memory_db.add_usage(
        used_by='test_waiter',
        category='serving',
        description='Test serving usage'
    )
    menu_usage2 = in_memory_db.add_menuusage(
        menu_id=setup_menu_usage_data['menu_id'],
        usage_id=usage2.id,
        amount=3
    )
    assert menu_usage2 is not None

    # Test get by menu_id
    result = in_memory_db.get_menuusage(
        menu_id=setup_menu_usage_data['menu_id']
    )
    assert len(result) == 2
    assert all(usage.menu_id == setup_menu_usage_data['menu_id'] for usage in result)

    # Test get by usage_id
    result = in_memory_db.get_menuusage(
        usage_id=setup_menu_usage_data['usage_id']
    )
    assert len(result) == 1
    assert result[0].usage_id == setup_menu_usage_data['usage_id']

    # Test get by both menu_id and usage_id
    result = in_memory_db.get_menuusage(
        menu_id=setup_menu_usage_data['menu_id'],
        usage_id=setup_menu_usage_data['usage_id']
    )
    assert len(result) == 1
    assert result[0].menu_id == setup_menu_usage_data['menu_id']
    assert result[0].usage_id == setup_menu_usage_data['usage_id']

    # Test row_num limit
    result = in_memory_db.get_menuusage(row_num=1)
    assert len(result) == 1


def test_menuusage_validation(in_memory_db, setup_menu_usage_data):
    """Test menu usage validation rules"""

    # Test negative amount
    result = in_memory_db.add_menuusage(
        menu_id=setup_menu_usage_data['menu_id'],
        usage_id=setup_menu_usage_data['usage_id'],
        amount=-2  # Invalid negative amount
    )
    assert result is None

    # Test zero amount
    result = in_memory_db.add_menuusage(
        menu_id=setup_menu_usage_data['menu_id'],
        usage_id=setup_menu_usage_data['usage_id'],
        amount=0  # Invalid zero amount
    )
    assert result is None

    # Test valid amount
    result = in_memory_db.add_menuusage(
        menu_id=setup_menu_usage_data['menu_id'],
        usage_id=setup_menu_usage_data['usage_id'],
        amount=5  # Valid positive amount
    )
    assert result is not None


def test_menuusage_foreign_key_validation(in_memory_db, setup_menu_usage_data):
    """Test menu usage foreign key validation in edit"""

    # Create a valid menu usage first
    menu_usage = in_memory_db.add_menuusage(
        menu_id=setup_menu_usage_data['menu_id'],
        usage_id=setup_menu_usage_data['usage_id'],
        amount=5
    )
    assert menu_usage is not None

    # Test edit with non-existent menu ID
    menu_usage.menu_id = 9999
    result = in_memory_db.edit_menuusage(menu_usage)
    assert result is None  # Should fail due to non-existent menu

    # Test edit with non-existent usage ID
    menu_usage.menu_id = setup_menu_usage_data['menu_id']
    menu_usage.usage_id = 9999
    result = in_memory_db.edit_menuusage(menu_usage)
    assert result is None  # Should fail due to non-existent usage


def test_menuusage_composite_key_operations(in_memory_db, setup_menu_usage_data):
    """Test operations with composite primary key"""

    # Create a menu usage
    menu_usage = in_memory_db.add_menuusage(
        menu_id=setup_menu_usage_data['menu_id'],
        usage_id=setup_menu_usage_data['usage_id'],
        amount=5
    )
    assert menu_usage is not None

    # Test edit with composite key
    menu_usage.amount = 8
    updated = in_memory_db.edit_menuusage(menu_usage)
    assert updated is not None
    assert updated.amount == 8

    # Test delete with composite key
    result = in_memory_db.delete_menuusage(menu_usage)
    assert result is True

    # Verify deletion
    result = in_memory_db.get_menuusage(
        menu_id=setup_menu_usage_data['menu_id'],
        usage_id=setup_menu_usage_data['usage_id']
    )
    assert len(result) == 0


def test_menuusage_optional_amount(in_memory_db, setup_menu_usage_data):
    """Test menu usage with optional amount as None"""

    # Should allow None for amount
    menu_usage = in_memory_db.add_menuusage(
        menu_id=setup_menu_usage_data['menu_id'],
        usage_id=setup_menu_usage_data['usage_id'],
        # amount is optional
    )
    assert menu_usage is not None
    assert menu_usage.amount is None


def test_menuusage_delete_nonexistent(in_memory_db):
    """Test deleting non-existent menu usage record"""

    # Create a mock menu usage object with non-existent composite key
    class MockMenuUsage:
        menu_id = 9999
        usage_id = 9999

    result = in_memory_db.delete_menuusage(MockMenuUsage())
    assert result is False  # Should return False for non-existent record


def test_menuusage_edit_nonexistent(in_memory_db):
    """Test editing non-existent menu usage record"""

    # Create a mock menu usage object with non-existent composite key
    class MockMenuUsage:
        menu_id = 9999
        usage_id = 9999
        amount = 5

    result = in_memory_db.edit_menuusage(MockMenuUsage())
    assert result is None  # Should return None for non-existent record