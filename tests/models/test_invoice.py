from datetime import datetime, timedelta
from models.cafe_managment_models import Invoice
from utils import crud_cycle_test


def test_invoice_crud_cycle(in_memory_db):
    """Test complete CRUD cycle for Invoice model"""

    # First create a required InvoicePayment for foreign key constraint
    payment = in_memory_db.add_invoicepayment(
        payed=100.0,
        payer="test payer",
        method="cash",
        date=datetime.now(),
        receiver="test receiver",
        receiver_id="123"
    )
    assert payment is not None

    # Test data
    create_kwargs = {
        'pay_id': payment.id,
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

    # Create test payments first
    payment1 = in_memory_db.add_invoicepayment(
        payed=100.0, payer="payer1", method="cash", date=datetime.now(), receiver="rec1", receiver_id="1"
    )
    payment2 = in_memory_db.add_invoicepayment(
        payed=200.0, payer="payer2", method="card", date=datetime.now(), receiver="rec2", receiver_id="2"
    )

    # Create test invoices
    now = datetime.now()
    invoice1 = in_memory_db.add_invoice(
        pay_id=payment1.id,
        saler='saler_one',
        date=now - timedelta(days=1),
        total_price=100.0,
        closed=False,
        description='First invoice'
    )
    assert invoice1 is not None

    invoice2 = in_memory_db.add_invoice(
        pay_id=payment2.id,
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

    # Test get by pay_id
    result = in_memory_db.get_invoice(pay_id=payment2.id)
    assert len(result) == 1
    assert result[0].pay_id == payment2.id

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

    # Create test payment
    payment = in_memory_db.add_invoicepayment(
        payed=100.0, payer="test", method="cash", date=datetime.now(), receiver="test", receiver_id="1"
    )

    # Test negative total_price
    result = in_memory_db.add_invoice(
        pay_id=payment.id,
        saler='test',
        total_price=-50.0,  # Invalid negative price
        closed=False
    )
    assert result is None

    # Test zero total_price
    result = in_memory_db.add_invoice(
        pay_id=payment.id,
        saler='test',
        total_price=0.0,  # Invalid zero price
        closed=False
    )
    assert result is None

    # Test valid total_price
    result = in_memory_db.add_invoice(
        pay_id=payment.id,
        saler='test',
        total_price=50.0,  # Valid positive price
        closed=False
    )
    assert result is not None


def test_invoice_string_processing(in_memory_db):
    """Test that string fields are properly processed"""

    payment = in_memory_db.add_invoicepayment(
        payed=100.0, payer="test", method="cash", date=datetime.now(), receiver="test", receiver_id="1"
    )

    # Test with spaces and mixed case
    invoice = in_memory_db.add_invoice(
        pay_id=payment.id,
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


def test_invoice_with_none_pay_id(in_memory_db):
    """Test invoice creation with None pay_id"""

    # Should allow None pay_id (based on your method signature)
    invoice = in_memory_db.add_invoice(
        pay_id=None,  # No payment associated
        saler='standalone',
        total_price=100.0,
        closed=False
    )
    assert invoice is not None
    assert invoice.pay_id is None


def test_invoice_nonexistent_pay_id(in_memory_db):
    """Test invoice creation with non-existent pay_id"""

    # Try to create invoice with non-existent payment ID
    invoice = in_memory_db.add_invoice(
        pay_id=9999,  # Non-existent payment
        saler='test',
        total_price=100.0,
        closed=False
    )
    assert invoice is None  # Should fail due to foreign key constraint


def test_invoice_delete_nonexistent(in_memory_db):
    """Test deleting non-existent invoice"""

    # Create a mock invoice object with non-existent ID
    class MockInvoice:
        id = 9999

    result = in_memory_db.delete_invoice(MockInvoice())
    assert result is False  # Should return False for non-existent invoice


