import pytest
from datetime import datetime
from cafe_managment_models import InventoryUsage, Inventory, Usage
from utils import crud_cycle_test


@pytest.fixture
def setup_inventory_usage_data(in_memory_db):
    """Setup required test data for inventory usage tests"""
    # Create an inventory item first
    inventory = in_memory_db.add_inventory(
        name='Test Coffee Beans',
        category='coffee',
        unit='kg',
        current_stock=10.0,
        price_per_unit=15.99
    )
    assert inventory is not None

    # Create a usage record
    usage = in_memory_db.add_usage(
        used_by='test_chef',
        category='brewing',
        description='Test coffee brewing usage'
    )
    assert usage is not None

    return {
        'inventory_id': inventory.id,
        'usage_id': usage.id,
        'inventory': inventory,
        'usage': usage
    }


def test_inventoryusage_crud_cycle(in_memory_db, setup_inventory_usage_data):
    """Test complete CRUD cycle for InventoryUsage model"""

    # Test data
    create_kwargs = {
        'inventory_item_id': setup_inventory_usage_data['inventory_id'],
        'usage_id': setup_inventory_usage_data['usage_id'],
        'amount': 2.5
    }

    update_kwargs = {
        'amount': 3.0
    }

    # Run CRUD cycle test - InventoryUsage uses composite key
    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=InventoryUsage,
        create_kwargs=create_kwargs,
        update_kwargs=update_kwargs,
        lookup_fields=['inventory_item_id', 'usage_id'],  # Composite key lookup
        lookup_values=[setup_inventory_usage_data['inventory_id'], setup_inventory_usage_data['usage_id']]
    )


def test_inventoryusage_get_methods(in_memory_db, setup_inventory_usage_data):
    """Test various get_inventoryusage filtering options"""

    # Create test inventory usage records
    usage1 = in_memory_db.add_inventoryusage(
        inventory_item_id=setup_inventory_usage_data['inventory_id'],
        usage_id=setup_inventory_usage_data['usage_id'],
        amount=2.5
    )
    assert usage1 is not None

    # Create another usage and inventory usage for different filtering
    usage2 = in_memory_db.add_usage(
        used_by='test_barista',
        category='cleaning',
        description='Test cleaning usage'
    )
    usage3 = in_memory_db.add_inventoryusage(
        inventory_item_id=setup_inventory_usage_data['inventory_id'],
        usage_id=usage2.id,
        amount=1.0
    )
    assert usage3 is not None

    # Test get by inventory_item_id
    result = in_memory_db.get_inventoryusage(
        inventory_item_id=setup_inventory_usage_data['inventory_id']
    )
    assert len(result) == 2
    assert all(usage.inventory_item_id == setup_inventory_usage_data['inventory_id'] for usage in result)

    # Test get by usage_id
    result = in_memory_db.get_inventoryusage(
        usage_id=setup_inventory_usage_data['usage_id']
    )
    assert len(result) == 1
    assert result[0].usage_id == setup_inventory_usage_data['usage_id']

    # Test get by both inventory_item_id and usage_id
    result = in_memory_db.get_inventoryusage(
        inventory_item_id=setup_inventory_usage_data['inventory_id'],
        usage_id=setup_inventory_usage_data['usage_id']
    )
    assert len(result) == 1
    assert result[0].inventory_item_id == setup_inventory_usage_data['inventory_id']
    assert result[0].usage_id == setup_inventory_usage_data['usage_id']

    # Test row_num limit
    result = in_memory_db.get_inventoryusage(row_num=1)
    assert len(result) == 1


def test_inventoryusage_validation(in_memory_db, setup_inventory_usage_data):
    """Test inventory usage validation rules"""

    # Test negative amount
    result = in_memory_db.add_inventoryusage(
        inventory_item_id=setup_inventory_usage_data['inventory_id'],
        usage_id=setup_inventory_usage_data['usage_id'],
        amount=-1.0  # Invalid negative amount
    )
    assert result is None

    # Test zero amount
    result = in_memory_db.add_inventoryusage(
        inventory_item_id=setup_inventory_usage_data['inventory_id'],
        usage_id=setup_inventory_usage_data['usage_id'],
        amount=0.0  # Invalid zero amount
    )
    assert result is None

    # Test valid amount
    result = in_memory_db.add_inventoryusage(
        inventory_item_id=setup_inventory_usage_data['inventory_id'],
        usage_id=setup_inventory_usage_data['usage_id'],
        amount=2.5  # Valid positive amount
    )
    assert result is not None


def test_inventoryusage_foreign_key_validation(in_memory_db, setup_inventory_usage_data):
    """Test inventory usage foreign key validation in edit"""

    # Create a valid inventory usage first
    inventory_usage = in_memory_db.add_inventoryusage(
        inventory_item_id=setup_inventory_usage_data['inventory_id'],
        usage_id=setup_inventory_usage_data['usage_id'],
        amount=2.5
    )
    assert inventory_usage is not None

    # Test edit with non-existent inventory ID
    inventory_usage.inventory_item_id = 9999
    result = in_memory_db.edit_inventoryusage(inventory_usage)
    assert result is None  # Should fail due to non-existent inventory

    # Test edit with non-existent usage ID
    inventory_usage.inventory_item_id = setup_inventory_usage_data['inventory_id']
    inventory_usage.usage_id = 9999
    result = in_memory_db.edit_inventoryusage(inventory_usage)
    assert result is None  # Should fail due to non-existent usage


def test_inventoryusage_composite_key_operations(in_memory_db, setup_inventory_usage_data):
    """Test operations with composite primary key"""

    # Create an inventory usage
    inventory_usage = in_memory_db.add_inventoryusage(
        inventory_item_id=setup_inventory_usage_data['inventory_id'],
        usage_id=setup_inventory_usage_data['usage_id'],
        amount=2.5
    )
    assert inventory_usage is not None

    # Test edit with composite key
    inventory_usage.amount = 3.0
    updated = in_memory_db.edit_inventoryusage(inventory_usage)
    assert updated is not None
    assert updated.amount == 3.0

    # Test delete with composite key
    result = in_memory_db.delete_inventoryusage(inventory_usage)
    assert result is True

    # Verify deletion
    result = in_memory_db.get_inventoryusage(
        inventory_item_id=setup_inventory_usage_data['inventory_id'],
        usage_id=setup_inventory_usage_data['usage_id']
    )
    assert len(result) == 0


def test_inventoryusage_optional_amount(in_memory_db, setup_inventory_usage_data):
    """Test inventory usage with optional amount as None"""

    # Should allow None for amount
    inventory_usage = in_memory_db.add_inventoryusage(
        inventory_item_id=setup_inventory_usage_data['inventory_id'],
        usage_id=setup_inventory_usage_data['usage_id'],
        # amount is optional
    )
    assert inventory_usage is not None
    assert inventory_usage.amount is None


def test_inventoryusage_delete_nonexistent(in_memory_db):
    """Test deleting non-existent inventory usage record"""

    # Create a mock inventory usage object with non-existent composite key
    class MockInventoryUsage:
        inventory_item_id = 9999
        usage_id = 9999

    result = in_memory_db.delete_inventoryusage(MockInventoryUsage())
    assert result is False  # Should return False for non-existent record


def test_inventoryusage_edit_nonexistent(in_memory_db):
    """Test editing non-existent inventory usage record"""

    # Create a mock inventory usage object with non-existent composite key
    class MockInventoryUsage:
        inventory_item_id = 9999
        usage_id = 9999
        amount = 2.5

    result = in_memory_db.edit_inventoryusage(MockInventoryUsage())
    assert result is None  # Should return None for non-existent record