import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from cafe_managment_models import Order, Supplier
from tests.utils import crud_cycle_test


def test_order_crud_cycle(in_memory_db):
    """Test complete CRUD cycle for Order model"""

    # First create a supplier (required for order creation)
    supplier_data = {
        'name': 'test supplier',
        'contact_channel': 'email',
        'contact_address': 'test@supplier.com'
    }
    supplier = in_memory_db.add_supplier(**supplier_data)
    assert supplier is not None

    # Test data for order creation
    create_kwargs: Dict[str, Any] = {
        'supplier_id': supplier.id,
        'date': datetime.now(),
        'buyer': 'John Doe',
        'payer': 'Jane Smith',
        'description': 'Test order for CRUD cycle'
    }

    # Test data for order update
    update_kwargs: Dict[str, Any] = {
        'buyer': 'Updated Buyer',
        'payer': 'Updated Payer',
        'description': 'Updated test order description'
    }

    # Run CRUD cycle test
    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=Order,
        create_kwargs=create_kwargs,
        update_kwargs=update_kwargs,
        lookup_fields=['buyer', 'payer'],  # Test lookup by buyer and payer
        lookup_values=['John Doe', 'Jane Smith']
    )


def test_get_order_filters(in_memory_db):
    """Test various filter combinations for get_order"""

    # Create test supplier
    supplier = in_memory_db.add_supplier(
        name='coffee bean supplier',
        contact_channel='phone',
        contact_address='555-1234'
    )
    assert supplier is not None

    # Create test orders with different dates
    now = datetime.now()
    orders_data = [
        {
            'supplier_id': supplier.id,
            'date': now - timedelta(days=2),
            'buyer': 'buyer1',
            'payer': 'payer1',
            'description': 'Order 1'
        },
        {
            'supplier_id': supplier.id,
            'date': now - timedelta(days=1),
            'buyer': 'buyer2',
            'payer': 'payer2',
            'description': 'Order 2'
        },
        {
            'supplier_id': supplier.id,
            'date': now,
            'buyer': 'buyer3',
            'payer': 'payer3',
            'description': 'Order 3'
        }
    ]

    # Add all orders
    created_orders = []
    for order_data in orders_data:
        order = in_memory_db.add_order(**order_data)
        assert order is not None
        created_orders.append(order)

    # Test 1: Get by buyer
    buyer_orders = in_memory_db.get_order(buyer='buyer1')
    assert len(buyer_orders) == 1
    assert buyer_orders[0].buyer == 'buyer1'

    # Test 2: Get by payer
    payer_orders = in_memory_db.get_order(payer='payer2')
    assert len(payer_orders) == 1
    assert payer_orders[0].payer == 'payer2'

    # Test 3: Get by supplier name
    supplier_orders = in_memory_db.get_order(supplier='coffee bean supplier')
    assert len(supplier_orders) == 3  # Should find all orders from this supplier

    # Test 4: Get by date range
    from_date = now - timedelta(days=1)
    to_date = now
    date_orders = in_memory_db.get_order(from_date=from_date, to_date=to_date)
    assert len(date_orders) == 2  # Orders from yesterday and today

    # Test 5: Get with row limit
    limited_orders = in_memory_db.get_order(row_num=2)
    assert len(limited_orders) == 2
    # Should be ordered by date descending, so most recent first
    assert limited_orders[0].date > limited_orders[1].date

    # Test 6: Get with non-existent supplier
    non_existent = in_memory_db.get_order(supplier='non-existent supplier')
    assert non_existent == []


def test_order_edge_cases(in_memory_db):
    """Test edge cases for order functions"""

    # Create supplier
    supplier = in_memory_db.add_supplier(name='test supplier')
    assert supplier is not None

    # Test 1: Create order with minimal data
    minimal_order = in_memory_db.add_order(
        supplier_id=supplier.id,
        buyer='minimal'
    )
    assert minimal_order is not None
    assert minimal_order.buyer == 'minimal'
    assert minimal_order.payer is None

    # Test 2: Try to create order with non-existent supplier
    bad_order = in_memory_db.add_order(
        supplier_id=9999,  # Non-existent ID
        buyer='test'
    )
    assert bad_order is None

    # Test 3: Try to edit non-existent order
    fake_order = Order(id=9999, supplier_id=supplier.id, buyer='fake')
    edited = in_memory_db.edit_order(fake_order)
    assert edited is None

    # Test 4: Try to delete non-existent order
    deleted = in_memory_db.delete_order(fake_order)
    assert deleted is False


def test_order_without_filters(in_memory_db):
    """Test get_order without any filters (should return all orders)"""

    # Create supplier
    supplier = in_memory_db.add_supplier(name='bulk supplier')
    assert supplier is not None

    # Create multiple orders
    for i in range(5):
        order = in_memory_db.add_order(
            supplier_id=supplier.id,
            buyer=f'buyer_{i}',
            payer=f'payer_{i}'
        )
        assert order is not None

    # Get all orders without filters
    all_orders = in_memory_db.get_order()
    assert len(all_orders) == 5
    # Should be ordered by date descending (most recent first)
    assert all_orders[0].date >= all_orders[1].date