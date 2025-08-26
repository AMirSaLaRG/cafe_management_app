import pytest
from datetime import datetime
from cafe_managment_models import Rent


def test_rent_crud_cycle(in_memory_db):
    """Test CRUD operations for Rent model"""

    # Test data
    create_kwargs = {
        "name": "Venty",
        'rent': 2000.0,
        'mortgage': 1500.0,
        'mortgage_percentage_to_rent': 0.75,
        'from_date': datetime(2024, 1, 1),
        'to_date': datetime(2024, 12, 31),
        'payer': 'Company Account',
        'description': 'Monthly store rental'
    }

    update_kwargs = {
        'rent': 2200.0,
        'mortgage_percentage_to_rent': 0.8,
        'description': 'Updated rental agreement'
    }

    # Use the generic CRUD test
    from utils import crud_cycle_test

    crud_cycle_test(
        db_handler=in_memory_db,
        model_class=Rent,
        create_kwargs=create_kwargs,
        update_kwargs=update_kwargs,
        lookup_fields=['payer'],
        lookup_values=['company account']  # Should be processed to lowercase
    )


def test_rent_validation_errors(in_memory_db):
    """Test that invalid data is rejected"""

    # Test negative rent
    result = in_memory_db.add_rent(rent=-1000.0, name='test')
    assert result is None

    # Test negative mortgage
    result = in_memory_db.add_rent(mortgage=-500.0, name='test2')
    assert result is None

    # Test mortgage percentage out of range
    result = in_memory_db.add_rent(mortgage_percentage_to_rent=1.5, name='test3')  # > 1
    assert result is None

    result = in_memory_db.add_rent(mortgage_percentage_to_rent=-0.5, name='test4')  # < 0
    assert result is None


def test_rent_string_processing(in_memory_db):
    """Test that string fields are properly processed"""

    rent = in_memory_db.add_rent(
        name='test',
        rent=2000.0,
        payer='  Company Account  '
    )

    assert rent is not None
    assert rent.payer == 'company account'  # Should be processed to lowercase


def test_rent_get_filters(in_memory_db):
    """Test various filter combinations for get_rent"""

    # Create multiple rent records
    rent1 = in_memory_db.add_rent(
        name='test',
        rent=2000.0,
        payer='company account',
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 6, 30)
    )
    assert rent1 is not None

    rent2 = in_memory_db.add_rent(
        name='test2',
        rent=1800.0,
        payer='store budget',
        from_date=datetime(2024, 7, 1),
        to_date=datetime(2024, 12, 31)
    )
    assert rent2 is not None

    rent3 = in_memory_db.add_rent(
        name='test3',
        rent=2500.0,
        payer='company account',
        from_date=datetime(2025, 1, 1),
        to_date=datetime(2025, 12, 31)
    )
    assert rent3 is not None

    # Test various filter combinations
    # Get all
    all_rents = in_memory_db.get_rent()
    assert len(all_rents) == 3

    # Filter by payer
    company_rents = in_memory_db.get_rent(payer='company account')
    assert len(company_rents) == 2

    store_rents = in_memory_db.get_rent(payer='store budget')
    assert len(store_rents) == 1

    # Filter by date range (from_date)
    year_2024_rents = in_memory_db.get_rent(
        from_date=datetime(2024, 1, 1),
        to_date=datetime(2024, 12, 31)
    )
    assert len(year_2024_rents) == 2

    # Filter by specific from_date
    mid_year_rents = in_memory_db.get_rent(
        from_date=datetime(2024, 6, 1),
        to_date=datetime(2024, 8, 1)
    )
    assert len(mid_year_rents) == 1

    # Test row limit
    limited = in_memory_db.get_rent(row_num=2)
    assert len(limited) == 2


def test_rent_date_validation(in_memory_db):
    """Test date validation in get_rent"""

    # Test invalid date range
    result = in_memory_db.get_rent(
        from_date=datetime(2024, 12, 31),
        to_date=datetime(2024, 1, 1)  # from_date > to_date
    )
    assert result == []  # Should return empty list due to validation error


def test_rent_edit_and_delete(in_memory_db):
    """Test specific edit and delete functionality"""

    # Create rent
    rent = in_memory_db.add_rent(
        name='test',
        rent=2000.0,
        mortgage=1500.0,
        payer='Company Account'
    )
    assert rent is not None

    # Test edit
    rent.rent = 2200.0
    rent.mortgage_percentage_to_rent = 0.8
    rent.payer = 'Updated Account'

    updated = in_memory_db.edit_rent(rent)
    assert updated is not None
    assert updated.rent == 2200.0
    assert updated.mortgage_percentage_to_rent == 0.8
    assert updated.payer == 'updated account'  # Should be processed to lowercase

    # Test delete
    deleted = in_memory_db.delete_rent(updated)
    assert deleted is True

    # Verify deletion
    result = in_memory_db.get_rent(id=rent.id)
    assert len(result) == 0


def test_rent_edit_without_id(in_memory_db):
    """Test that edit fails without ID"""

    rent = Rent(rent=2000.0)
    # rent.id is None

    result = in_memory_db.edit_rent(rent)
    assert result is None


def test_rent_delete_nonexistent(in_memory_db):
    """Test deleting non-existent rent"""

    rent = Rent(rent=2000.0)
    rent.id = 9999  # Non-existent ID

    result = in_memory_db.delete_rent(rent)
    assert result is False


def test_rent_optional_parameters(in_memory_db):
    """Test that optional parameters work correctly"""

    # Test with minimal parameters
    rent1 = in_memory_db.add_rent(rent=2000.0, name='test')
    assert rent1 is not None
    assert rent1.rent == 2000.0
    assert rent1.mortgage_percentage_to_rent == 1  # Default value

    # Test with all parameters None except required
    rent2 = in_memory_db.add_rent(
        name='test2',
        rent=1800.0,
        mortgage=None,
        mortgage_percentage_to_rent=None,
        from_date=None,
        to_date=None,
        payer=None,
        description=None
    )
    assert rent2 is not None