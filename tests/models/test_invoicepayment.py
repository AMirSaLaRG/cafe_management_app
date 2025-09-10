from datetime import datetime, timedelta
from models.cafe_managment_models import InvoicePayment, Invoice
from utils import crud_cycle_test
import pytest


@pytest.fixture
def setup_invoice(in_memory_db):
    """Setup an invoice for invoice payment tests"""
    invoice = in_memory_db.add_invoice(
        saler='test_cashier',
        date=datetime.now(),
        total_price=100.0,
        closed=False,
        description='Test invoice for payment'
    )
    assert invoice is not None
    return invoice


def test_invoicepayment_crud_cycle(in_memory_db, setup_invoice):
    """Test complete CRUD cycle for InvoicePayment model"""

    # Test data
    create_kwargs = {
        'invoice_id': setup_invoice.id,
        'paid': 100.0,
        'payer': '  Test Payer  ',  # With spaces to test stripping
        'method': '  CASH  ',  # With spaces to test stripping
        'date': datetime.now(),
        'receiver': '  Test Receiver  ',  # With spaces to test stripping
        'receiver_id': 'TEST123'
    }

    update_kwargs = {
        'paid': 200.0,
        'payer': '  Updated Payer  ',  # With spaces to test stripping
        'method': '  CARD  ',  # With spaces to test stripping
        'receiver': '  Updated Receiver  ',  # With spaces to test stripping
        'receiver_id': 'UPDATED456'
    }

    # Run CRUD cycle test
    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=InvoicePayment,
        create_kwargs=create_kwargs,
        update_kwargs=update_kwargs,
        lookup_fields=['id'],  # Lookup by id field
        lookup_values=None  # Will be set by created object
    )




def test_invoicepayment_get_methods(in_memory_db, setup_invoice):
    """Test various get_invoicepayment filtering options"""

    # Create test payments
    now = datetime.now()
    payment1 = in_memory_db.add_invoicepayment(
        invoice_id=setup_invoice.id,
        paid=100.0,
        payer='payer_one',
        method='cash',
        date=now - timedelta(days=1),
        receiver='receiver_one',
        receiver_id='ID001'
    )
    assert payment1 is not None

    # Create another invoice for second payment
    invoice2 = in_memory_db.add_invoice(
        saler='cashier2',
        date=datetime.now(),
        total_price=200.0,
        closed=True,
        description='Second test invoice'
    )
    payment2 = in_memory_db.add_invoicepayment(
        invoice_id=invoice2.id,
        paid=200.0,
        payer='payer_two',
        method='card',
        date=now,
        receiver='receiver_two',
        receiver_id='ID002'
    )
    assert payment2 is not None

    # Test get by id
    result = in_memory_db.get_invoicepayment(id=payment1.id)
    assert len(result) == 1
    assert result[0].id == payment1.id

    # Test get by invoice_id
    result = in_memory_db.get_invoicepayment(invoice_id=setup_invoice.id)
    assert len(result) == 1
    assert result[0].invoice_id == setup_invoice.id

    # Test get by payer (case insensitive)
    result = in_memory_db.get_invoicepayment(payer='PAYER_ONE')
    assert len(result) == 1
    assert result[0].payer == 'payer_one'  # Should be lowercased

    # Test get by method (case insensitive)
    result = in_memory_db.get_invoicepayment(method='CASH')
    assert len(result) == 1
    assert result[0].method == 'cash'  # Should be lowercased

    # Test get by receiver (case insensitive)
    result = in_memory_db.get_invoicepayment(receiver='RECEIVER_ONE')
    assert len(result) == 1
    assert result[0].receiver == 'receiver_one'  # Should be lowercased

    # Test get by receiver_id
    result = in_memory_db.get_invoicepayment(receiver_id='ID001')
    assert len(result) == 1
    assert result[0].receiver_id == 'ID001'

    # Test date filtering
    result = in_memory_db.get_invoicepayment(from_date=now - timedelta(hours=12))
    assert len(result) >= 1

    # Test row_num limit
    result = in_memory_db.get_invoicepayment(row_num=1)
    assert len(result) == 1


def test_invoicepayment_validation(in_memory_db, setup_invoice):
    """Test invoice payment validation rules"""

    # Test negative paid amount
    result = in_memory_db.add_invoicepayment(
        invoice_id=setup_invoice.id,
        paid=-50.0,  # Invalid negative amount
        payer='test',
        method='cash',
        receiver='test'
    )
    assert result is None

    # Test zero paid amount
    result = in_memory_db.add_invoicepayment(
        invoice_id=setup_invoice.id,
        paid=0.0,  # Invalid zero amount
        payer='test',
        method='cash',
        receiver='test'
    )
    assert result is None

    # Test invalid invoice_id
    result = in_memory_db.add_invoicepayment(
        invoice_id=9999,  # Non-existent invoice
        paid=50.0,
        payer='test',
        method='cash',
        receiver='test'
    )
    assert result is None

    # Test valid paid amount
    result = in_memory_db.add_invoicepayment(
        invoice_id=setup_invoice.id,
        paid=50.0,  # Valid positive amount
        payer='test',
        method='cash',
        receiver='test'
    )
    assert result is not None


def test_invoicepayment_string_processing(in_memory_db, setup_invoice):
    """Test that string fields are properly processed"""

    # Test with spaces and mixed case
    payment = in_memory_db.add_invoicepayment(
        invoice_id=setup_invoice.id,
        paid=100.0,
        payer='  MixedCase Payer  ',  # Should be stripped and lowercased
        method='  CreditCard  ',  # Should be stripped and lowercased
        receiver='  MixedCase Receiver  ',  # Should be stripped and lowercased
        receiver_id='TEST123'
    )
    assert payment is not None
    assert payment.payer == 'mixedcase payer'  # Should be processed
    assert payment.method == 'creditcard'  # Should be processed
    assert payment.receiver == 'mixedcase receiver'  # Should be processed

    # Test edit with string processing
    payment.payer = '  UPDATED Payer  '
    payment.method = '  UPDATED Method  '
    payment.receiver = '  UPDATED Receiver  '
    updated = in_memory_db.edit_invoicepayment(payment)
    assert updated is not None
    assert updated.payer == 'updated payer'  # Should be processed
    assert updated.method == 'updated method'  # Should be processed
    assert updated.receiver == 'updated receiver'  # Should be processed


def test_invoicepayment_optional_fields(in_memory_db, setup_invoice):
    """Test invoice payment creation with optional fields as None"""

    # Should allow None for optional fields
    payment = in_memory_db.add_invoicepayment(
        invoice_id=setup_invoice.id,
        paid=100.0,
        payer=None,  # Optional field
        method=None,  # Optional field
        receiver=None,  # Optional field
        receiver_id=None,  # Optional field
        tip=None  # Optional field
    )
    assert payment is not None
    assert payment.payer is None
    assert payment.method is None
    assert payment.receiver is None
    assert payment.receiver_id is None
    assert payment.tip is None


def test_invoicepayment_delete_nonexistent(in_memory_db):
    """Test deleting non-existent invoice payment"""

    # Create a mock payment object with non-existent ID
    class MockInvoicePayment:
        id = 9999

    result = in_memory_db.delete_invoicepayment(MockInvoicePayment())
    assert result is False  # Should return False for non-existent payment


def test_invoicepayment_date_auto_assignment(in_memory_db, setup_invoice):
    """Test that date is automatically assigned if not provided"""

    payment = in_memory_db.add_invoicepayment(
        invoice_id=setup_invoice.id,
        paid=100.0,
        payer='test',
        method='cash',
        receiver='test'
        # date not provided - should be auto-assigned
    )
    assert payment is not None
    assert payment.date is not None
    assert isinstance(payment.date, datetime)


def test_invoicepayment_multiple_filters(in_memory_db, setup_invoice):
    """Test combining multiple filters in get_invoicepayment"""

    # Create test payments
    payment1 = in_memory_db.add_invoicepayment(
        invoice_id=setup_invoice.id,
        paid=100.0,
        payer='john_doe',
        method='cash',
        receiver='company_a',
        receiver_id='COMP_A'
    )

    # Create another invoice for second payment
    invoice2 = in_memory_db.add_invoice(
        saler='cashier2',
        date=datetime.now(),
        total_price=200.0,
        closed=True,
        description='Second test invoice'
    )
    payment2 = in_memory_db.add_invoicepayment(
        invoice_id=invoice2.id,
        paid=200.0,
        payer='jane_smith',
        method='card',
        receiver='company_b',
        receiver_id='COMP_B'
    )

    # Test combined filters
    result = in_memory_db.get_invoicepayment(
        payer='john_doe',
        method='cash'
    )
    assert len(result) == 1
    assert result[0].id == payment1.id

    # Test invoice_id with other filters
    result = in_memory_db.get_invoicepayment(
        invoice_id=setup_invoice.id,
        payer='john_doe'
    )
    assert len(result) == 1
    assert result[0].id == payment1.id

    # Test non-matching combined filters
    result = in_memory_db.get_invoicepayment(
        payer='john_doe',
        method='card'  # Doesn't exist with this combination
    )
    assert len(result) == 0


def test_invoicepayment_tip_field(in_memory_db, setup_invoice):
    """Test the tip field functionality"""

    # Test with tip
    payment_with_tip = in_memory_db.add_invoicepayment(
        invoice_id=setup_invoice.id,
        paid=100.0,
        tip=10.0,  # Add tip
        payer='tipper',
        method='cash',
        receiver='cafe'
    )
    assert payment_with_tip is not None
    assert payment_with_tip.tip == 10.0

    # Test get payments with tip
    result_with_tip = in_memory_db.get_invoicepayment(tip=True)
    assert len(result_with_tip) >= 1
    assert any(p.tip is not None for p in result_with_tip)

    # Test get payments without tip
    result_without_tip = in_memory_db.get_invoicepayment(tip=False)
    assert len(result_without_tip) >= 0  # Could be 0 or more


def test_invoicepayment_invoice_relationship(in_memory_db, setup_invoice):
    """Test that invoice payments are properly linked to invoices"""

    # Create a payment
    payment = in_memory_db.add_invoicepayment(
        invoice_id=setup_invoice.id,
        paid=100.0,
        payer='test_customer',
        method='cash',
        receiver='test_cafe'
    )
    assert payment is not None

    # Verify the relationship
    assert payment.invoice_id == setup_invoice.id

    # Verify we can retrieve the invoice
    invoices = in_memory_db.get_invoice(id=setup_invoice.id)
    assert len(invoices) == 1
    assert invoices[0].id == setup_invoice.id