import pytest
from datetime import datetime, timedelta
from cafe_managment_models import InvoicePayment
from utils import crud_cycle_test


def test_invoicepayment_crud_cycle(in_memory_db):
    """Test complete CRUD cycle for InvoicePayment model"""

    # Test data
    create_kwargs = {
        'payed': 100.0,
        'payer': '  Test Payer  ',  # With spaces to test stripping
        'method': '  CASH  ',  # With spaces to test stripping
        'date': datetime.now(),
        'receiver': '  Test Receiver  ',  # With spaces to test stripping
        'receiver_id': 'TEST123'
    }

    update_kwargs = {
        'payed': 200.0,
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
        lookup_fields=['payer'],  # Lookup by payer field
        lookup_values=[create_kwargs['payer']]  # Use original payer value for lookup
    )


def test_invoicepayment_get_methods(in_memory_db):
    """Test various get_invoicepayment filtering options"""

    # Create test payments
    now = datetime.now()
    payment1 = in_memory_db.add_invoicepayment(
        payed=100.0,
        payer='payer_one',
        method='cash',
        date=now - timedelta(days=1),
        receiver='receiver_one',
        receiver_id='ID001'
    )
    assert payment1 is not None

    payment2 = in_memory_db.add_invoicepayment(
        payed=200.0,
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

    # Test get by payer (case insensitive)
    result = in_memory_db.get_invoicepayment(payer='PAYER_ONE')
    assert len(result) == 1
    assert result[0].payer == 'payer_one'  # Should be lowercased

    # Test get by method (case insensitive)
    result = in_memory_db.get_invoicepayment(method='CASH')
    assert len(result) == 1
    assert result[0].method == 'cash'  # Should be lowercased

    # Test get by receiver (case insensitive)
    result = in_memory_db.get_invoicepayment(receiver='RECEIVER_TWO')
    assert len(result) == 1
    assert result[0].receiver == 'receiver_two'  # Should be lowercased

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


def test_invoicepayment_validation(in_memory_db):
    """Test invoice payment validation rules"""

    # Test negative payed amount
    result = in_memory_db.add_invoicepayment(
        payed=-50.0,  # Invalid negative amount
        payer='test',
        method='cash',
        receiver='test'
    )
    assert result is None

    # Test zero payed amount
    result = in_memory_db.add_invoicepayment(
        payed=0.0,  # Invalid zero amount
        payer='test',
        method='cash',
        receiver='test'
    )
    assert result is None

    # Test valid payed amount
    result = in_memory_db.add_invoicepayment(
        payed=50.0,  # Valid positive amount
        payer='test',
        method='cash',
        receiver='test'
    )
    assert result is not None


def test_invoicepayment_string_processing(in_memory_db):
    """Test that string fields are properly processed"""

    # Test with spaces and mixed case
    payment = in_memory_db.add_invoicepayment(
        payed=100.0,
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


def test_invoicepayment_optional_fields(in_memory_db):
    """Test invoice payment creation with optional fields as None"""

    # Should allow None for optional fields
    payment = in_memory_db.add_invoicepayment(
        payed=100.0,
        payer=None,  # Optional field
        method=None,  # Optional field
        receiver=None,  # Optional field
        receiver_id=None  # Optional field
    )
    assert payment is not None
    assert payment.payer is None
    assert payment.method is None
    assert payment.receiver is None
    assert payment.receiver_id is None


def test_invoicepayment_delete_nonexistent(in_memory_db):
    """Test deleting non-existent invoice payment"""

    # Create a mock payment object with non-existent ID
    class MockInvoicePayment:
        id = 9999

    result = in_memory_db.delete_invoicepayment(MockInvoicePayment())
    assert result is False  # Should return False for non-existent payment


def test_invoicepayment_date_auto_assignment(in_memory_db):
    """Test that date is automatically assigned if not provided"""

    payment = in_memory_db.add_invoicepayment(
        payed=100.0,
        payer='test',
        method='cash',
        receiver='test'
        # date not provided - should be auto-assigned
    )
    assert payment is not None
    assert payment.date is not None
    assert isinstance(payment.date, datetime)


def test_invoicepayment_multiple_filters(in_memory_db):
    """Test combining multiple filters in get_invoicepayment"""

    # Create test payments
    payment1 = in_memory_db.add_invoicepayment(
        payed=100.0,
        payer='john_doe',
        method='cash',
        receiver='company_a',
        receiver_id='COMP_A'
    )

    payment2 = in_memory_db.add_invoicepayment(
        payed=200.0,
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

    # Test non-matching combined filters
    result = in_memory_db.get_invoicepayment(
        payer='john_doe',
        method='card'  # Doesn't exist with this combination
    )
    assert len(result) == 0