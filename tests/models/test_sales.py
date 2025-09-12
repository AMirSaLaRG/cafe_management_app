import pytest
from datetime import datetime
from models.cafe_managment_models import Sales, Invoice, InvoicePayment, Menu
from utils import crud_cycle_test


@pytest.fixture
def setup_test_data(in_memory_db):
    """Setup required test data for sales tests"""
    # Create a menu item first
    menu = in_memory_db.add_menu(
        name='Test Coffee',
        size='medium',
        category='drinks',
        current_price=5.99,
        value_added_tax=0.08,
        serving=True
    )
    assert menu is not None

    # Create an invoice first
    invoice = in_memory_db.add_invoice(
        saler='test_cashier',
        date=datetime.now(),
        total_price=50.0,
        closed=False,
        description='Test invoice'
    )
    assert invoice is not None

    # Create an invoice payment linked to the invoice
    payment = in_memory_db.add_invoicepayment(
        invoice_id=invoice.id,
        paid=50.0,
        payer='test_customer',
        method='cash',
        date=datetime.now(),
        receiver='test_cafe',
        receiver_id='CAFE001'
    )
    assert payment is not None

    return {
        'menu_id': menu.id,
        'invoice_id': invoice.id,
        'menu': menu,
        'invoice': invoice,
        'payment': payment
    }


def test_sales_crud_cycle(in_memory_db, setup_test_data):
    """Test complete CRUD cycle for Sales model"""

    # Test data
    create_kwargs = {
        'menu_id': setup_test_data['menu_id'],
        'invoice_id': setup_test_data['invoice_id'],
        'number': 2,
        'discount': 1.0,
        'price': 11.98,  # 2 * 5.99
        'description': 'Test sale of 2 coffees'
    }

    update_kwargs = {
        'number': 3,
        'discount': 2.0,
        'price': 15.97,  # 3 * 5.99 - 2.0 discount
        'description': 'Updated sale of 3 coffees'
    }

    # Run CRUD cycle test - Sales now uses simple id primary key
    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=Sales,
        create_kwargs=create_kwargs,
        update_kwargs=update_kwargs,
        lookup_fields=['id'],  # Simple id lookup
        lookup_values=None  # Will be set by the created object
    )


def test_sales_get_methods(in_memory_db, setup_test_data):
    """Test various get_sales filtering options"""

    # Create test sales
    sale1 = in_memory_db.add_sales(
        menu_id=setup_test_data['menu_id'],
        invoice_id=setup_test_data['invoice_id'],
        number=1,
        discount=0.5,
        price=5.49,  # 5.99 - 0.5
        description='First sale'
    )
    assert sale1 is not None

    # Create another invoice and sale for different filtering
    invoice2 = in_memory_db.add_invoice(
        saler='cashier2',
        date=datetime.now(),
        total_price=25.0,
        closed=True
    )
    sale2 = in_memory_db.add_sales(
        menu_id=setup_test_data['menu_id'],
        invoice_id=invoice2.id,
        number=2,
        discount=1.0,
        price=10.98,  # 2 * 5.99 - 1.0
        description='Second sale'
    )
    assert sale2 is not None

    # Test get by menu_id
    result = in_memory_db.get_sales(menu_id=setup_test_data['menu_id'])
    assert len(result) == 2
    assert all(sale.menu_id == setup_test_data['menu_id'] for sale in result)

    # Test get by invoice_id
    result = in_memory_db.get_sales(invoice_id=setup_test_data['invoice_id'])
    assert len(result) == 1
    assert result[0].invoice_id == setup_test_data['invoice_id']

    # Test get by id
    result = in_memory_db.get_sales(id=sale1.id)
    assert len(result) == 1
    assert result[0].id == sale1.id

    # Test row_num limit
    result = in_memory_db.get_sales(row_num=1)
    assert len(result) == 1


def test_sales_validation(in_memory_db, setup_test_data):
    """Test sales validation rules"""

    # Test negative number
    result = in_memory_db.add_sales(
        menu_id=setup_test_data['menu_id'],
        invoice_id=setup_test_data['invoice_id'],
        number=-1,  # Invalid negative number
        price=5.99
    )
    assert result is None

    # Test zero number
    result = in_memory_db.add_sales(
        menu_id=setup_test_data['menu_id'],
        invoice_id=setup_test_data['invoice_id'],
        number=0,  # Invalid zero number
        price=5.99
    )
    assert result is None

    # Test negative price
    result = in_memory_db.add_sales(
        menu_id=setup_test_data['menu_id'],
        invoice_id=setup_test_data['invoice_id'],
        number=1,
        price=-5.99  # Invalid negative price
    )
    assert result is None

    # Test negative discount
    result = in_memory_db.add_sales(
        menu_id=setup_test_data['menu_id'],
        invoice_id=setup_test_data['invoice_id'],
        number=1,
        discount=-1.0,  # Invalid negative discount
        price=5.99
    )
    assert result is None

    # Test valid values
    result = in_memory_db.add_sales(
        menu_id=setup_test_data['menu_id'],
        invoice_id=setup_test_data['invoice_id'],
        number=1,
        discount=0.5,  # Valid discount
        price=5.49  # Valid price
    )
    assert result is not None


def test_sales_foreign_key_validation(in_memory_db, setup_test_data):
    """Test sales foreign key validation"""

    # Test non-existent menu_id
    result = in_memory_db.add_sales(
        menu_id=9999,  # Non-existent menu
        invoice_id=setup_test_data['invoice_id'],
        number=1,
        price=5.99
    )
    assert result is None

    # Test non-existent invoice_id
    result = in_memory_db.add_sales(
        menu_id=setup_test_data['menu_id'],
        invoice_id=9999,  # Non-existent invoice
        number=1,
        price=5.99
    )
    assert result is None

    # Test valid foreign keys
    result = in_memory_db.add_sales(
        menu_id=setup_test_data['menu_id'],
        invoice_id=setup_test_data['invoice_id'],
        number=1,
        price=5.99
    )
    assert result is not None


def test_sales_simple_key_operations(in_memory_db, setup_test_data):
    """Test operations with simple primary key"""

    # Create a sale
    sale = in_memory_db.add_sales(
        menu_id=setup_test_data['menu_id'],
        invoice_id=setup_test_data['invoice_id'],
        number=1,
        price=5.99
    )
    assert sale is not None

    # Test edit with simple key
    sale.number = 2
    sale.price = 11.98
    updated = in_memory_db.edit_sales(sale)
    assert updated is not None
    assert updated.number == 2
    assert updated.price == 11.98

    # Test delete with simple key
    result = in_memory_db.delete_sales(sale)
    assert result is True

    # Verify deletion
    result = in_memory_db.get_sales(id=sale.id)
    assert len(result) == 0


def test_sales_delete_nonexistent(in_memory_db):
    """Test deleting non-existent sales record"""

    # Create a mock sales object with non-existent id
    class MockSales:
        id = 999999
        menu_id = 9999
        invoice_id = 9999

    result = in_memory_db.delete_sales(MockSales())
    assert result is False  # Should return False for non-existent sales


def test_sales_edit_nonexistent(in_memory_db):
    """Test editing non-existent sales record"""

    # Create a mock sales object with non-existent id
    class MockSales:
        id = 99999
        menu_id = 9999
        invoice_id = 9999
        number = 1
        price = 5.99

    result = in_memory_db.edit_sales(MockSales())
    assert result is None  # Should return None for non-existent sales


def test_sales_without_optional_fields(in_memory_db, setup_test_data):
    """Test sales creation without optional fields"""

    # Should allow None for optional fields
    sale = in_memory_db.add_sales(
        menu_id=setup_test_data['menu_id'],
        invoice_id=setup_test_data['invoice_id'],
        number=1,
        price=5.99,
        # discount, description are optional
    )
    assert sale is not None
    assert sale.discount is None
    assert sale.description is None


def test_sales_invoice_relationship(in_memory_db, setup_test_data):
    """Test that sales are properly linked to invoices"""

    # Create a sale
    sale = in_memory_db.add_sales(
        menu_id=setup_test_data['menu_id'],
        invoice_id=setup_test_data['invoice_id'],
        number=2,
        price=11.98
    )
    assert sale is not None

    # Verify the relationship
    invoice = in_memory_db.get_invoice(id=setup_test_data['invoice_id'])
    assert len(invoice) == 1
    assert invoice[0].id == setup_test_data['invoice_id']


def test_sales_menu_relationship(in_memory_db, setup_test_data):
    """Test that sales are properly linked to menu items"""

    # Create a sale
    sale = in_memory_db.add_sales(
        menu_id=setup_test_data['menu_id'],
        invoice_id=setup_test_data['invoice_id'],
        number=1,
        price=5.99
    )
    assert sale is not None

    # Verify the relationship
    menu = in_memory_db.get_menu(id=setup_test_data['menu_id'])
    assert len(menu) == 1
    assert menu[0].id == setup_test_data['menu_id']