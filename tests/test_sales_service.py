from sqlalchemy.testing import assert_raises
import pytest

from services.sales_service import SalesService


@pytest.fixture
def menus(in_memory_db):
    menu1 = in_memory_db.add_menu(name="latte", size="large", current_price=200000)
    menu2 = in_memory_db.add_menu(name="milk shake", size="large", current_price=400000)
    menu3 = in_memory_db.add_menu(name="juice", size="small", current_price=50000)
    return menu1, menu2, menu3  # Return menus as a tuple

def test_process_sale(in_memory_db, menus):
    service = SalesService(in_memory_db)

    menu1, menu2, menu3 = menus
    # menu1 = in_memory_db.add_menu(name="latte", size="large", current_price=200000)
    # menu2 = in_memory_db.add_menu(name="milk shake", size="large", current_price=400000)
    # menu3 = in_memory_db.add_menu(name="juice", size="small", current_price=50000)
    #
    # assert menu3
    # assert menu2
    # assert menu1

    test_process_sale_1 = service.process_sale(menu1.id,
                                               10,
                                               discount=100000,
                                               description='testing dog',
                                               saler='Mr test')

    assert test_process_sale_1

    #should create an invoice
    created_invoice_test1 = in_memory_db.get_invoice()
    # a = created_invoice_test1[0].total_price
    assert created_invoice_test1[0].sales[0].id == menu1.id
    assert created_invoice_test1[0].total_price == ((menu1.current_price * 10) - 100000)

    test_process_sale_2 = service.process_sale(menu1.id,
                                               1,
                                               discount=100000,
                                               description='testing dog',
                                               saler='Mr test',
                                               invoice_id=created_invoice_test1[0].id)

    created_invoice_test1 = in_memory_db.get_invoice()
    # b=created_invoice_test1[0].total_price
    assert test_process_sale_2
    assert created_invoice_test1[0].total_price == ((menu1.current_price * 11) - 200000)
    assert len(created_invoice_test1) == 1


def test_wrong_process_sale(in_memory_db, menus):
    service = SalesService(in_memory_db)

    menu1, menu2, menu3 = menus
    #incorrect invoice id
    test_process_sale_1 = service.process_sale(menu1.id,
                                               10,
                                               discount=10000,
                                               description='testing dog',
                                               saler='Mr test',
                                               invoice_id=1)
    assert test_process_sale_1 is False

    #incorrect menu id
    test_process_sale_2 = service.process_sale(999,
                                               10,
                                               discount=10000,
                                               description='testing dog',
                                               saler='Mr test',
                                               invoice_id=1)
    assert test_process_sale_2 is False

    #what is discont be more than price
    test_process_sale_2 = service.process_sale(menu1.id,
                                               1,
                                               discount=1000000,
                                               description='testing dog',
                                               saler='Mr test',
                                               invoice_id=1)
    #ERROR:root:Total price must be greater than 0. it get catched in db handler
    assert test_process_sale_2 is False


def test_cancel_sale(in_memory_db, menus):
    service = SalesService(in_memory_db)
    menu1, menu2, menu3 = menus

    # First, process a sale to have something to cancel
    sale = service.process_sale(menu1.id, 5, discount=50000, description="test cancel", saler="Mr test")
    assert sale

    invoices = in_memory_db.get_invoice()
    assert len(invoices) == 1
    invoice_id = invoices[0].id
    assert invoices[0].total_price == (menu1.current_price * 5 - 50000)

    # Now cancel the sale
    cancel_result = service.cancel_sale(invoice_id, menu1.id, quantity=2)
    assert cancel_result

    # Fetch invoice again and check updated totals
    updated_invoice = in_memory_db.get_invoice()[0]
    assert updated_invoice.total_price == (menu1.current_price * 3 - 30000)  # remaining quantity = 3
    assert any(sale.id == menu1.id for sale in updated_invoice.sales)

def test_cancel_sale_partial(in_memory_db, menus):
    service = SalesService(in_memory_db)
    menu1, menu2, menu3 = menus

    # Process a sale of 10 items
    sale = service.process_sale(menu1.id, 10, discount=10000, description="partial cancel", saler="Mr test")
    assert sale

    invoice = in_memory_db.get_invoice()[0]
    assert invoice.total_price == (menu1.current_price * 10 - 10000)

    # Cancel 4 items
    result = service.cancel_sale(menu_id=menu1.id, invoice_id=invoice.id, quantity=4, discount=10000)
    assert result

    updated_invoice = in_memory_db.get_invoice()[0]
    # 6 items remain
    assert updated_invoice.total_price == (menu1.current_price * 6 - 10000)

# Test full cancellation
def test_cancel_sale_full(in_memory_db, menus):
    service = SalesService(in_memory_db)
    menu1, menu2, menu3 = menus

    # Process a sale of 5 items
    sale = service.process_sale(menu1.id, 5, discount=5000, description="full cancel", saler="Mr test")
    assert sale

    invoice = in_memory_db.get_invoice()[0]
    # Cancel all items
    result = service.cancel_sale(menu_id=menu1.id, invoice_id=invoice.id)
    assert result

    updated_invoice = in_memory_db.get_invoice()[0]
    # Sale should be removed
    assert all(s.id != menu1.id for s in updated_invoice.sales)

# Test canceling more than sold (should remove all)
def test_cancel_sale_over_quantity(in_memory_db, menus):
    service = SalesService(in_memory_db)
    menu1, menu2, menu3 = menus

    sale = service.process_sale(menu1.id, 3, discount=0, description="over quantity", saler="Mr test")
    assert sale

    invoice = in_memory_db.get_invoice()[0]
    # Try to cancel more than sold
    result = service.cancel_sale(menu_id=menu1.id, invoice_id=invoice.id, quantity=10)
    assert result

    updated_invoice = in_memory_db.get_invoice()[0]
    # Sale should be removed
    assert all(s.id != menu1.id for s in updated_invoice.sales)

# Test cancel when no sales exist (should return False)
def test_cancel_no_sales(in_memory_db, menus):
    service = SalesService(in_memory_db)
    menu1, menu2, menu3 = menus

    invoice = in_memory_db.get_invoice()[0] if in_memory_db.get_invoice() else None
    if invoice:
        # Make sure no sales exist for menu2
        result = service.cancel_sale(menu_id=menu2.id, invoice_id=invoice.id)
        assert result == False
    else:
        # No invoice exists, cancel should return False
        result = service.cancel_sale(menu_id=menu2.id, invoice_id=999)
        assert result == False