from datetime import datetime
from models.cafe_managment_models import Equipment


def test_equipment_crud_cycle(in_memory_db):
    """Test CRUD operations for Equipment model"""

    # Test data
    create_kwargs = {
        'name': 'Test Coffee Machine',
        'category': 'Beverage Equipment',
        'number': 2,
        'purchase_date': datetime(2024, 1, 15),
        'purchase_price': 2500.0,
        'payer': 'company account',
        'in_use': True,
        'expire_date': datetime(2026, 1, 15),
        'monthly_depreciation': 83.33,
        'description': 'Main coffee brewing machine'
    }

    update_kwargs = {
        'number': 3,
        'in_use': False,
        'description': 'Updated description'
    }

    # Use the generic CRUD test
    from utils import crud_cycle_test

    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=Equipment,
        create_kwargs=create_kwargs,
        update_kwargs=update_kwargs,
        lookup_fields=['name'],
        lookup_values=['Test Coffee Machine']
    )


def test_equipment_validation_errors(in_memory_db):
    """Test that invalid data is rejected"""

    # Test negative purchase price
    result = in_memory_db.add_equipment(
        name='Test Machine',
        purchase_price=-100.0
    )
    assert result is None

    # Test negative monthly depreciation
    result = in_memory_db.add_equipment(
        name='Test Machine',
        monthly_depreciation=-50.0
    )
    assert result is None

    # Test zero or negative number
    result = in_memory_db.add_equipment(
        name='Test Machine',
        number=0
    )
    assert result is None

    result = in_memory_db.add_equipment(
        name='Test Machine',
        number=-1
    )
    assert result is None


def test_equipment_string_processing(in_memory_db):
    """Test that string fields are properly processed"""

    equipment = in_memory_db.add_equipment(
        name='  TEST Machine  ',
        category='  Beverage Equipment  ',
        payer='  Company Account  '
    )

    assert equipment is not None
    assert equipment.name == 'test machine'
    assert equipment.category == 'beverage equipment'
    assert equipment.payer == 'company account'


def test_equipment_get_filters(in_memory_db):
    """Test various filter combinations for get_equipment"""

    # Create multiple equipment records
    eq1 = in_memory_db.add_equipment(
        name='Coffee Grinder',
        category='Preparation',
        payer='store budget',
        in_use=True,
        purchase_date=datetime(2024, 1, 1)
    )
    assert eq1 is not None

    eq2 = in_memory_db.add_equipment(
        name='Espresso Machine',
        category='Beverage',
        payer='company account',
        in_use=False,
        purchase_date=datetime(2024, 2, 1)
    )
    assert eq2 is not None

    eq3 = in_memory_db.add_equipment(
        name='Refrigerator',
        category='Storage',
        payer='store budget',
        in_use=True,
        purchase_date=datetime(2024, 3, 1)
    )
    assert eq3 is not None

    # Test various filter combinations
    # Get all
    all_equipment = in_memory_db.get_equipment()
    assert len(all_equipment) == 3

    # Filter by name
    coffee_equipment = in_memory_db.get_equipment(name='coffee grinder')
    assert len(coffee_equipment) == 1
    assert coffee_equipment[0].name == 'coffee grinder'

    # Filter by category
    beverage_equipment = in_memory_db.get_equipment(category='beverage')
    assert len(beverage_equipment) == 1
    assert beverage_equipment[0].category == 'beverage'

    # Filter by payer
    store_equipment = in_memory_db.get_equipment(payer='store budget')
    assert len(store_equipment) == 2

    # Filter by in_use status
    active_equipment = in_memory_db.get_equipment(in_use=True)
    assert len(active_equipment) == 2

    inactive_equipment = in_memory_db.get_equipment(in_use=False)
    assert len(inactive_equipment) == 1

    # Filter by date range (purchase date)
    jan_equipment = in_memory_db.get_equipment(
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 1, 31)
    )
    assert len(jan_equipment) == 1

    # Test row limit
    limited = in_memory_db.get_equipment(row_num=2)
    assert len(limited) == 2


def test_equipment_date_expire_filter(in_memory_db):
    """Test the date_expire filter functionality"""

    # Create equipment with expire dates
    eq1 = in_memory_db.add_equipment(
        name='Equipment 1',
        expire_date=datetime(2024, 6, 1)
    )
    eq2 = in_memory_db.add_equipment(
        name='Equipment 2',
        expire_date=datetime(2024, 12, 1)
    )

    # Test expire date filtering
    mid_year_expire = in_memory_db.get_equipment(
        date_expire=True,
        from_date=datetime(2024, 5, 1),
        to_date=datetime(2024, 7, 1)
    )
    assert len(mid_year_expire) == 0 #noting get expire in this time

    # Test purchase date filtering (date_expire=False)
    # Note: This test requires equipment with purchase dates
    eq3 = in_memory_db.add_equipment(
        name='Equipment 3',
        purchase_date=datetime(2024, 3, 1)
    )

    q1_purchases = in_memory_db.get_equipment(
        date_expire=False,
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 3, 31)
    )
    assert len(q1_purchases) >= 1


def test_equipment_edit_and_delete(in_memory_db):
    """Test specific edit and delete functionality"""

    # Create equipment
    equipment = in_memory_db.add_equipment(
        name='Test Equipment',
        number=1,
        purchase_price=1000.0
    )
    assert equipment is not None

    # Test edit
    equipment.number = 2
    equipment.purchase_price = 1200.0
    equipment.description = 'Updated equipment'

    updated = in_memory_db.edit_equipment(equipment)
    assert updated is not None
    assert updated.number == 2
    assert updated.purchase_price == 1200.0
    assert updated.description == 'Updated equipment'

    # Test delete
    deleted = in_memory_db.delete_equipment(updated)
    assert deleted is True

    # Verify deletion
    result = in_memory_db.get_equipment(id=equipment.id)
    assert len(result) == 0


def test_equipment_edit_without_id(in_memory_db):
    """Test that edit fails without ID"""

    equipment = Equipment(name='Test Equipment')
    # equipment.id is None

    result = in_memory_db.edit_equipment(equipment)
    assert result is None


def test_equipment_delete_nonexistent(in_memory_db):
    """Test deleting non-existent equipment"""

    equipment = Equipment(name='Non-existent')
    equipment.id = 9999  # Non-existent ID

    result = in_memory_db.delete_equipment(equipment)
    assert result is False