from datetime import datetime, timedelta
from models.cafe_managment_models import Invoice, Sales, InvoicePayment
from utils import crud_cycle_test


def test_invoice_crud_cycle(in_memory_db):
    """Test complete CRUD cycle for Invoice model"""

    # Test data - no pay_id needed anymore
    create_kwargs = {
        'saler': '  Test Saler  ',  # With spaces to test stripping
        'date': datetime.now(),
        'total_price': 150.0,
        'closed': False,
        'description': 'Test invoice description'
    }

    update_kwargs = {
        'saler': '  Updated Saler  ',  # With spaces to test stripping
        'total_price': 200.0,
        'closed': True,
        'description': 'Updated description'
    }

    # Run CRUD cycle test
    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=Invoice,
        create_kwargs=create_kwargs,
        update_kwargs=update_kwargs,
        lookup_fields=['saler'],  # Lookup by saler field
        lookup_values=[create_kwargs['saler']]  # Use original saler value for lookup
    )


def test_invoice_get_methods(in_memory_db):
    """Test various get_invoice filtering options"""

    # Create test invoices
    now = datetime.now()
    invoice1 = in_memory_db.add_invoice(
        saler='saler_one',
        date=now - timedelta(days=1),
        total_price=100.0,
        closed=False,
        description='First invoice'
    )
    assert invoice1 is not None

    invoice2 = in_memory_db.add_invoice(
        saler='saler_two',
        date=now,
        total_price=200.0,
        closed=True,
        description='Second invoice'
    )
    assert invoice2 is not None

    # Test get by id
    result = in_memory_db.get_invoice(id=invoice1.id)
    assert len(result) == 1
    assert result[0].id == invoice1.id

    # Test get by saler (case insensitive)
    result = in_memory_db.get_invoice(saler='SALER_ONE')
    assert len(result) == 1
    assert result[0].saler == 'saler_one'  # Should be lowercased

    # Test get by closed status
    result = in_memory_db.get_invoice(closed=True)
    assert len(result) == 1
    assert result[0].closed == True

    result = in_memory_db.get_invoice(closed=False)
    assert len(result) == 1
    assert result[0].closed == False

    # Test date filtering
    result = in_memory_db.get_invoice(from_date=now - timedelta(hours=12))
    assert len(result) >= 1

    # Test row_num limit
    result = in_memory_db.get_invoice(row_num=1)
    assert len(result) == 1


def test_invoice_validation(in_memory_db):
    """Test invoice validation rules"""

    # Test negative total_price
    result = in_memory_db.add_invoice(
        saler='test',
        total_price=-50.0,  # Invalid negative price
        closed=False
    )
    assert result is None

    # Test zero total_price
    result = in_memory_db.add_invoice(
        saler='test',
        total_price=0.0,  # Invalid zero price
        closed=False
    )
    assert result is None

    # Test valid total_price
    result = in_memory_db.add_invoice(
        saler='test',
        total_price=50.0,  # Valid positive price
        closed=False
    )
    assert result is not None


def test_invoice_string_processing(in_memory_db):
    """Test that string fields are properly processed"""

    # Test with spaces and mixed case
    invoice = in_memory_db.add_invoice(
        saler='  MixedCase Saler  ',  # Should be stripped and lowercased
        total_price=100.0,
        closed=False
    )
    assert invoice is not None
    assert invoice.saler == 'mixedcase saler'  # Should be processed

    # Test edit with string processing
    invoice.saler = '  UPDATED Saler  '
    updated = in_memory_db.edit_invoice(invoice)
    assert updated is not None
    assert updated.saler == 'updated saler'  # Should be processed


def test_invoice_relationships(in_memory_db):
    """Test Invoice relationships with Sales and InvoicePayment"""

    # Create an invoice first
    invoice = in_memory_db.add_invoice(
        saler='test_saler',
        total_price=150.0,
        closed=False
    )
    assert invoice is not None

    # Create a menu item for sales
    menu_item = in_memory_db.add_menu(
        name='test_coffee',
        size='medium',
        current_price=5.0
    )
    assert menu_item is not None

    # Add sales to the invoice
    sales = in_memory_db.add_sales(
        menu_id=menu_item.id,
        invoice_id=invoice.id,
        number=3,
        price=15.0
    )
    assert sales is not None

    # Add payment to the invoice
    payment = in_memory_db.add_invoicepayment(
        invoice_id=invoice.id,
        paid=150.0,
        payer='test_customer',
        method='cash'
    )
    assert payment is not None

    # Test that relationships work correctly
    # Get invoice with relationships loaded
    invoices = in_memory_db.get_invoice(id=invoice.id)
    assert len(invoices) == 1

    fetched_invoice = invoices[0]

    # Check sales relationship
    assert len(fetched_invoice.sales) == 1
    assert fetched_invoice.sales[0].menu_id == menu_item.id
    assert fetched_invoice.sales[0].price == 15.0

    # Check payments relationship
    assert len(fetched_invoice.payments) == 1
    assert fetched_invoice.payments[0].payer == 'test_customer'
    assert fetched_invoice.payments[0].paid == 150.0


def test_invoice_without_relationships(in_memory_db):
    """Test invoice creation without any sales or payments"""

    # Should be able to create invoice without any sales or payments
    invoice = in_memory_db.add_invoice(
        saler='standalone_saler',
        total_price=100.0,
        closed=False
    )
    assert invoice is not None

    # Verify it has empty relationships
    invoices = in_memory_db.get_invoice(id=invoice.id)
    assert len(invoices) == 1
    assert len(invoices[0].sales) == 0
    assert len(invoices[0].payments) == 0


def test_invoice_delete_cascading(in_memory_db):
    """Test what happens when invoice is deleted (cascading behavior)"""

    # Create invoice with sales and payments
    invoice = in_memory_db.add_invoice(
        saler='cascade_test',
        total_price=200.0,
        closed=False
    )
    assert invoice is not None

    # Create menu item
    menu_item = in_memory_db.add_menu(
        name='cascade_item',
        size='small',
        current_price=10.0
    )
    assert menu_item is not None

    # Add sales
    sales = in_memory_db.add_sales(
        menu_id=menu_item.id,
        invoice_id=invoice.id,
        number=2,
        price=20.0
    )
    assert sales is not None

    # Add payment
    payment = in_memory_db.add_invoicepayment(
        invoice_id=invoice.id,
        paid=200.0,
        payer='cascade_customer',
        method='card'
    )
    assert payment is not None

    # Delete the invoice
    result = in_memory_db.delete_invoice(invoice)
    # should not be able to delete because there is payment for it
    assert result is False

    # Check that sales and payments are also deleted (depending on cascade settings)
    # This depends on your database cascade settings
    remaining_sales = in_memory_db.get_sales(invoice_id=invoice.id)
    remaining_payments = in_memory_db.get_invoicepayment(id=invoice.id)

    # Depending on your cascade configuration, these might be empty or might still exist
    # You'll need to adjust this assertion based on your actual cascade behavior
    print(f"Remaining sales: {len(remaining_sales)}")
    print(f"Remaining payments: {len(remaining_payments)}")


def test_invoice_nonexistent_delete(in_memory_db):
    """Test deleting non-existent invoice"""

    # Create a mock invoice object with non-existent ID
    class MockInvoice:
        id = 9999

    result = in_memory_db.delete_invoice(MockInvoice())
    assert result is False  # Should return False for non-existent invoice