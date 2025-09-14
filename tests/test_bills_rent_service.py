import pytest
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from services.bills_rent_service import BillsRent
from models.cafe_managment_models import EstimatedBills, Rent, Bills
from models.dbhandler import DBHandler


class TestBillsRentService:
    def test_create_estimated_bill(self, in_memory_db):
        """Test creating a new estimated bill"""
        service = BillsRent(in_memory_db)

        # Create a new estimated bill
        from_date = datetime(2024, 1, 1)
        to_date = datetime(2024, 12, 31)

        bill = service.new_bill_estimated(
            name="Electricity",
            category="Utilities",
            cost=250.0,
            from_date=from_date,
            to_date=to_date,
            description="Monthly electricity bill estimate"
        )

        assert bill is not None
        assert bill.name == "electricity"
        assert bill.category == "utilities"
        assert bill.cost == 250.0
        assert bill.from_date == from_date
        assert bill.to_date == to_date
        assert bill.description == "Monthly electricity bill estimate"

    def test_find_estimated_bill(self, in_memory_db):
        """Test finding an estimated bill by ID"""
        service = BillsRent(in_memory_db)

        # First create a bill
        from_date = datetime(2024, 1, 1)
        to_date = datetime(2024, 12, 31)

        created_bill = service.new_bill_estimated(
            name="Water",
            category="Utilities",
            cost=150.0,
            from_date=from_date,
            to_date=to_date
        )

        # Now find it
        found_bill = service.find_bill_estimated(created_bill.id)

        assert found_bill is not None
        assert found_bill.id == created_bill.id
        assert found_bill.name == "water"
        assert found_bill.cost == 150.0

    def test_find_estimated_bills_with_filters(self, in_memory_db):
        """Test finding estimated bills with filters"""
        service = BillsRent(in_memory_db)

        # Create multiple bills
        jan_to_jun = service.new_bill_estimated(
            name="Internet",
            category="Services",
            cost=80.0,
            from_date=datetime(2024, 1, 1),
            to_date=datetime(2024, 6, 30)
        )

        jul_to_dec = service.new_bill_estimated(
            name="Internet",
            category="Services",
            cost=85.0,  # Price increased
            from_date=datetime(2024, 7, 1),
            to_date=datetime(2024, 12, 31)
        )

        # Find bills by name
        internet_bills = service.find_bills_estimated(name="Internet")
        assert len(internet_bills) == 2

        # Find bills by category
        utility_bills = service.find_bills_estimated(category="Services")
        assert len(utility_bills) == 2

        # Find bills within date range
        mid_year_bills = service.find_bills_estimated(
            from_date=datetime(2024, 4, 1),
            to_date=datetime(2024, 9, 30)
        )
        assert len(mid_year_bills) == 2  # Both bills cover part of this range

    def test_update_estimated_bill(self, in_memory_db):
        """Test updating an estimated bill"""
        service = BillsRent(in_memory_db)

        # Create a bill
        bill = service.new_bill_estimated(
            name="Insurance",
            category="Business",
            cost=300.0,
            from_date=datetime(2024, 1, 1),
            to_date=datetime(2024, 12, 31)
        )

        # Update it
        updated_bill = service.update_bill_estimated(
            bill.id,
            cost=350.0,  # Price increased
            description="Updated with new premium"
        )

        assert updated_bill is not None
        assert updated_bill.cost == 350.0
        assert updated_bill.description == "Updated with new premium"

        # Verify the update persisted
        retrieved_bill = service.find_bill_estimated(bill.id)
        assert retrieved_bill.cost == 350.0

    def test_delete_estimated_bill(self, in_memory_db):
        """Test deleting an estimated bill"""
        service = BillsRent(in_memory_db)

        # Create a bill
        bill = service.new_bill_estimated(
            name="Cleaning Service",
            category="Services",
            cost=200.0,
            from_date=datetime(2024, 1, 1),
            to_date=datetime(2024, 12, 31)
        )

        # Delete it
        result = service.delete_bill_estimated(bill.id)
        assert result is True

        # Verify it's gone
        deleted_bill = service.find_bill_estimated(bill.id)
        assert deleted_bill is None

    def test_create_range_of_bills(self, in_memory_db):
        """Test creating a range of estimated bills"""
        service = BillsRent(in_memory_db)

        # Create monthly bills for a year
        result = service.create_a_range_of_bills(
            category="Utilities",
            name="Electricity",
            year=2024,
            average_estimated_cost=250.0,
            month=1,
            day=1,
            interval_months=1,
            number_of_periods=12
        )

        assert result is True

        # Verify all 12 bills were created
        electricity_bills = service.find_bills_estimated(name="Electricity")
        assert len(electricity_bills) == 12

        # Verify they cover the correct date ranges

        for i, bill in enumerate(electricity_bills):
            expected_from = datetime(2024, 12-i, 1)
            if i == 0:
                expected_to = datetime(2025, 1, 1)
            else:
                expected_to = datetime(2024, 13-i, 1)
            assert bill.from_date == expected_from
            assert bill.to_date == expected_to
            assert bill.cost == 250.0

    def test_create_rent(self, in_memory_db):
        """Test creating a new rent record"""
        service = BillsRent(in_memory_db)

        # Create a new rent record
        from_date = datetime(2024, 1, 1)
        to_date = datetime(2024, 12, 31)

        rent = service.new_rent(
            name="Main Cafe Location",
            rent=3000.0,
            mortgage=1500.0,
            mortgage_percentage_to_rent=0.5,
            from_date=from_date,
            to_date=to_date,
            payer="Business Account",
            description="Prime location downtown"
        )

        assert rent is not None
        assert rent.name == "main cafe location"
        assert rent.rent == 3000.0
        assert rent.mortgage == 1500.0
        assert rent.mortgage_percentage_to_rent == 0.5
        assert rent.from_date == from_date
        assert rent.to_date == to_date
        assert rent.payer == "business account"
        assert rent.description == "Prime location downtown"

    def test_find_rent(self, in_memory_db):
        """Test finding a rent record by ID"""
        service = BillsRent(in_memory_db)

        # First create a rent record
        created_rent = service.new_rent(
            name="Storage Unit",
            rent=500.0,
            mortgage=0.0,
            mortgage_percentage_to_rent=0.0,
            from_date=datetime(2024, 1, 1),
            to_date=datetime(2024, 12, 31)
        )

        # Now find it
        found_rent = service.find_rent(created_rent.id)

        assert found_rent is not None
        assert found_rent.id == created_rent.id
        assert found_rent.name == "storage unit"
        assert found_rent.rent == 500.0

    def test_update_rent(self, in_memory_db):
        """Test updating a rent record"""
        service = BillsRent(in_memory_db)

        # Create a rent record
        rent = service.new_rent(
            name="Main Location",
            rent=3000.0,
            mortgage=1500.0,
            mortgage_percentage_to_rent=0.5,
            from_date=datetime(2024, 1, 1),
            to_date=datetime(2024, 12, 31)
        )

        # Update it
        updated_rent = service.update_rent(
            rent.id,
            rent=3200.0,  # Rent increased
            mortgage=1600.0,  # Mortgage increased
            description="Annual rent increase"
        )

        assert updated_rent is not None
        assert updated_rent.rent == 3200.0
        assert updated_rent.mortgage == 1600.0
        assert updated_rent.mortgage_percentage_to_rent == 0.5  # Should remain unchanged
        assert updated_rent.description == "Annual rent increase"

    def test_pay_rent(self, in_memory_db):
        """Test marking rent as paid"""
        service = BillsRent(in_memory_db)

        # Create a rent record
        rent = service.new_rent(
            name="Main Location",
            rent=3000.0,
            mortgage=1500.0,
            mortgage_percentage_to_rent=0.5,
            from_date=datetime(2024, 1, 1),
            to_date=datetime(2024, 1, 31)
        )

        # Initially no payer
        assert rent.payer is None

        # Mark as paid
        result = service.pay_rent(
            rent.id,
            payer="Business Account",
            description="Paid via bank transfer"
        )

        assert result is True

        # Verify payment was recorded
        paid_rent = service.find_rent(rent.id)
        assert paid_rent.payer == "business account"
        assert paid_rent.description == "Paid via bank transfer"

    def test_create_range_of_rent(self, in_memory_db):
        """Test creating a range of rent records"""
        service = BillsRent(in_memory_db)

        # Create monthly rent records for a year
        result = service.create_a_range_of_rent(
            name_place="Main Cafe",
            rent=3000.0,
            mortgage=1500.0,
            percentage_m_to_r=0.5,
            year=2024,
            month=1,
            day=1,
            payer="Business Account",
            interval_months=1,
            number_of_periods=12,
            description="Monthly rent payments"
        )

        assert result is True

        # Verify all 12 rent records were created
        rent_records = service.find_rents(name="Main Cafe")
        assert len(rent_records) == 12

        # Verify they cover the correct date ranges
        for i, rent in enumerate(rent_records):
            expected_from = datetime(2024, 12 - i, 1)
            if i == 0:
                expected_to = datetime(2025, 1, 1)
            else:
                expected_to = datetime(2024, 13 - i, 1)
            assert rent.from_date == expected_from
            assert rent.to_date == expected_to
            assert rent.rent == 3000.0
            assert rent.mortgage == 1500.0
            assert rent.mortgage_percentage_to_rent == 0.5

    def test_create_actual_bill(self, in_memory_db):
        """Test creating a new actual bill"""
        service = BillsRent(in_memory_db)

        # Create a new actual bill
        from_date = datetime(2024, 1, 1)
        to_date = datetime(2024, 1, 31)

        bill = service.new_bill(
            name="January Electricity",
            category="Utilities",
            from_date=from_date,
            to_date=to_date,
            cost=275.50,
            payer="Business Account",
            description="Actual bill for January"
        )

        assert bill is not None
        assert bill.name == "january electricity"
        assert bill.category == "utilities"
        assert bill.cost == 275.50
        assert bill.from_date == from_date
        assert bill.to_date == to_date
        assert bill.payer == "business account"
        assert bill.description == "Actual bill for January"

    def test_find_actual_bill(self, in_memory_db):
        """Test finding an actual bill by ID"""
        service = BillsRent(in_memory_db)

        # First create a bill
        created_bill = service.new_bill(
            name="Water Bill",
            category="Utilities",
            from_date=datetime(2024, 1, 1),
            to_date=datetime(2024, 1, 31),
            cost=120.0,
            payer="Business Account"
        )

        # Now find it
        found_bill = service.find_bill(created_bill.id)

        assert found_bill is not None
        assert found_bill.id == created_bill.id
        assert found_bill.name == "water bill"
        assert found_bill.cost == 120.0

    def test_update_actual_bill(self, in_memory_db):
        """Test updating an actual bill"""
        service = BillsRent(in_memory_db)

        # Create a bill
        bill = service.new_bill(
            name="Internet Bill",
            category="Services",
            from_date=datetime(2024, 1, 1),
            to_date=datetime(2024, 1, 31),
            cost=85.0,
            payer="Business Account"
        )

        # Update it
        updated_bill = service.update_bill(
            bill.id,
            cost=82.50,  # Corrected amount
            payer="Owner Personal",  # Changed payer
            description="Applied loyalty discount"
        )

        assert updated_bill is not None
        assert updated_bill.cost == 82.50
        assert updated_bill.payer == "owner personal"
        assert updated_bill.description == "Applied loyalty discount"

    def test_delete_actual_bill(self, in_memory_db):
        """Test deleting an actual bill"""
        service = BillsRent(in_memory_db)

        # Create a bill
        bill = service.new_bill(
            name="Cleaning Service",
            category="Services",
            from_date=datetime(2024, 1, 1),
            to_date=datetime(2024, 1, 31),
            cost=200.0,
            payer="Business Account"
        )

        # Delete it
        result = service.delete_bill(bill.id)
        assert result is True

        # Verify it's gone
        deleted_bill = service.find_bill(bill.id)
        assert deleted_bill is None

    def test_real_world_scenario_annual_budgeting(self, in_memory_db):
        """Test a real-world scenario: annual budgeting for expenses"""
        service = BillsRent(in_memory_db)

        # Create estimated bills for annual budgeting
        expenses = [
            ("Electricity", "Utilities", 3000.0),  # $250/month
            ("Water", "Utilities", 1200.0),  # $100/month
            ("Internet", "Services", 960.0),  # $80/month
            ("Insurance", "Business", 3600.0),  # $300/month
            ("Cleaning", "Services", 2400.0),  # $200/month
        ]

        for name, category, annual_cost in expenses:
            service.new_bill_estimated(
                name=name,
                category=category,
                cost=annual_cost,
                from_date=datetime(2024, 1, 1),
                to_date=datetime(2024, 12, 31),
                description=f"Annual estimate for {name}"
            )

        # Verify all estimates were created
        estimated_bills = service.find_bills_estimated()
        assert len(estimated_bills) == 5

        # Create monthly rent records
        service.create_a_range_of_rent(
            name_place="Main Cafe",
            rent=3000.0,
            mortgage=1500.0,
            percentage_m_to_r=0.5,
            year=2024,
            interval_months=1,
            number_of_periods=12,
            payer="Business Account",
            description="Monthly rent"
        )

        # Verify rent records were created
        rent_records = service.find_rents()
        assert len(rent_records) == 12

        # Record some actual bills for Q1
        actual_bills = [
            ("January Electricity", "Utilities", 275.50, datetime(2024, 1, 1), datetime(2024, 1, 31)),
            ("February Electricity", "Utilities", 285.25, datetime(2024, 2, 1), datetime(2024, 2, 29)),
            ("March Electricity", "Utilities", 260.75, datetime(2024, 3, 1), datetime(2024, 3, 31)),
            ("Q1 Insurance", "Business", 900.00, datetime(2024, 1, 1), datetime(2024, 3, 31)),
        ]

        for name, category, cost, from_date, to_date in actual_bills:
            service.new_bill(
                name=name,
                category=category,
                from_date=from_date,
                to_date=to_date,
                cost=cost,
                payer="Business Account",
                description=f"Actual bill for {name}"
            )

        # Verify actual bills were created
        actual_bills = service.find_bills()
        assert len(actual_bills) == 4

        # Update an estimate based on actual spending
        electricity_estimates = service.find_bills_estimated(name="Electricity")
        assert len(electricity_estimates) == 1

        # Calculate average monthly electricity cost from actuals
        electricity_actuals = service.find_bills(category="Utilities")
        total_electricity = sum(bill.cost for bill in electricity_actuals)
        avg_monthly = total_electricity / 3  # 3 months of data

        # Update the annual estimate
        service.update_bill_estimated(
            electricity_estimates[0].id,
            cost=avg_monthly * 12,  # Project annual cost based on 3 months
            description=f"Updated based on Q1 actuals (avg: ${avg_monthly:.2f}/month)"
        )

        # Verify the update
        updated_estimate = service.find_bill_estimated(electricity_estimates[0].id)
        expected_annual = (275.50 + 285.25 + 260.75) / 3 * 12
        assert updated_estimate.cost == pytest.approx(expected_annual, 0.01)

    def test_real_world_scenario_rent_variation(self, in_memory_db):
        """Test a real-world scenario: rent variation with mortgage changes"""
        service = BillsRent(in_memory_db)

        # Create rent records with increasing mortgage payments
        base_rent = 3000.0
        base_mortgage = 1500.0

        for month in range(1, 13)[::-1]:
            # Mortgage increases slightly each month
            current_mortgage = base_mortgage * (1 + (month - 1) * 0.01)  # 1% increase monthly
            mortgage_percentage = current_mortgage / base_rent

            service.new_rent(
                name="Main Cafe",
                rent=base_rent,
                mortgage=current_mortgage,
                mortgage_percentage_to_rent=mortgage_percentage,
                from_date=datetime(2024, month, 1),
                to_date=datetime(2024, month + 1, 1) if month < 12 else datetime(2025, 1, 1),
                payer="Business Account",
                description=f"Rent for {datetime(2024, month, 1).strftime('%B %Y')}"
            )

        # Verify all rent records were created
        rent_records = service.find_rents(name="Main Cafe")
        assert len(rent_records) == 12

        # Check that mortgage increases as expected
        for i, rent in enumerate(rent_records):
            expected_mortgage = base_mortgage * (1 + i * 0.01)
            assert rent.mortgage == pytest.approx(expected_mortgage, 0.01)
            assert rent.mortgage_percentage_to_rent == pytest.approx(expected_mortgage / base_rent, 0.01)

        # Update the rent for the second half of the year due to lease renewal
        july_to_dec_rents = service.find_rents(
            from_date=datetime(2024, 7, 1),
            to_date=datetime(2024, 12, 31)
        )

        new_rent = 3200.0  # Rent increase
        for rent in july_to_dec_rents:
            service.update_rent(
                rent.id,
                rent=new_rent,
                mortgage_percentage_to_rent=rent.mortgage / new_rent,
                description="Updated for lease renewal"
            )

        # Verify the updates
        updated_rents = service.find_rents(
            from_date=datetime(2024, 7, 1),
            to_date=datetime(2024, 12, 31)
        )

        for rent in updated_rents:
            assert rent.rent == 3200.0
            assert rent.mortgage_percentage_to_rent == pytest.approx(rent.mortgage / 3200.0, 0.01)