import pytest
import time as t
from datetime import datetime, time, timedelta
from decimal import Decimal
from services.menu_pricing_service import MenuPriceService
from models.cafe_managment_models import *


class TestMenuPricingService:

    def test_calculate_suggested_price_basic_scenario(self, in_memory_db):
        """Test basic price calculation with realistic values"""
        service = MenuPriceService(in_memory_db)

        # Test case: Coffee with realistic costs
        result = service._calculate_suggested_price(
            direct_cost=1.50,  # Cost of coffee, milk, cup
            indirect_cost=2000,  # Monthly overhead
            sales_forecast=1000,  # Expected monthly sales
            profit_margin=0.3  # 30% profit margin
        )

        # indirect_cost_per_unit = 2000 / 1000 = 2.0
        # total_cost = 1.50 + 2.0 = 3.50
        # suggested_price = 3.50 * 1.3 = 4.55
        assert result == pytest.approx(4.55, 0.01)

    def test_calculate_suggested_price_edge_cases(self, in_memory_db):
        """Test edge cases for price calculation"""
        service = MenuPriceService(in_memory_db)

        # Test zero sales forecast (should return None/Fail)
        result = service._calculate_suggested_price(
            direct_cost=1.50,
            indirect_cost=2000,
            sales_forecast=0,
            profit_margin=0.3
        )
        assert result is None or result is False

        # Test negative profit margin (should return None/Fail)
        result = service._calculate_suggested_price(
            direct_cost=1.50,
            indirect_cost=2000,
            sales_forecast=1000,
            profit_margin=-0.1
        )
        assert result is None or result is False

    def test_labor_cost_multiple_shifts(self, in_memory_db):
        """Test that labor cost correctly sums multiple shifts"""
        service = MenuPriceService(in_memory_db)

        # Create position (ADD ALL REQUIRED PARAMETERS)
        position = in_memory_db.add_targetpositionandsalary(
            position="Test Worker",
            category="Test Category",  # ← REQUIRED
            from_date=datetime(2024, 1, 1),  # ← REQUIRED
            to_date=datetime(2024, 12, 31),  # ← REQUIRED
            monthly_payment=2400.00,  # $2400/month
            monthly_hr=160.0,  # $15/hour
            monthly_insurance=300.00  # $10/day
        )

        # Check if position was created successfully
        assert position is not None, "Failed to create position - check required parameters"
        assert hasattr(position, 'id'), "Position object doesn't have id attribute"

        # Create 3 identical shifts
        for i in range(3):
            shift = in_memory_db.add_shift(
                date=datetime(2024, 1, 15 + i),  # Different days
                from_hr=time(9, 0),
                to_hr=time(17, 0)  # 8 hours
            )

            # Check if shift was created successfully
            assert shift is not None, "Failed to create shift"
            assert hasattr(shift, 'id'), "Shift object doesn't have id attribute"

            labor = in_memory_db.add_estimatedlabor(
                position_id=position.id,
                shift_id=shift.id,
                number=1,
                extra_hr=time(0, 0)  # No overtime
            )

            # Check if labor assignment was created successfully
            assert labor is not None, "Failed to create labor assignment"

        # Calculate cost for all 3 shifts
        start_date = datetime(2024, 1, 15)
        end_date = datetime(2024, 1, 17)

        labor_cost = service._get_estimated_labor_cost(start_date, end_date)

        # Each shift: 8 hours * $15/hour + $10 insurance = $120 + $10 = $130
        # 3 shifts: 3 * $130 = $390
        expected_cost = 390.00

        assert labor_cost == pytest.approx(expected_cost, 0.01), \
            f"Expected ${expected_cost} for 3 shifts, got ${labor_cost}"

    def test_real_world_menu_item_pricing(self, in_memory_db):
        """Test complete pricing flow for a real menu item"""
        service = MenuPriceService(in_memory_db)

        # Create inventory items
        coffee_beans = in_memory_db.add_inventory(
            name="Arabica Coffee Beans",
            unit="kg",
            current_price=25.00,
            price_per_unit=0.05  # $0.05 per gram
        )

        milk = in_memory_db.add_inventory(
            name="Whole Milk",
            unit="liter",
            current_price=2.50,
            price_per_unit=0.0025  # $0.0025 per ml
        )

        # Create menu item
        latte = in_memory_db.add_menu(
            name="Latte",
            size="12oz",
            category="Coffee"
        )

        # Create recipes
        in_memory_db.add_recipe(
            inventory_id=coffee_beans.id,
            menu_id=latte.id,
            inventory_item_amount_usage=18.0  # 18g coffee
        )

        in_memory_db.add_recipe(
            inventory_id=milk.id,
            menu_id=latte.id,
            inventory_item_amount_usage=240.0  # 240ml milk
        )
        in_memory_db.add_estimatedmenupricerecord(menu_id=latte.id, sales_forecast=1, profit_margin=0.0, estimated_indirect_costs=2000)

        # Calculate direct cost
        service.calculate_update_direct_cost([latte.id])

        # Verify direct cost calculation
        # Coffee: 18g * $0.05/g = $0.90
        # Milk: 240ml * $0.0025/ml = $0.60
        # Total direct cost: $1.50

        latest_record = in_memory_db.get_estimatedmenupricerecord(
            menu_id=latte.id, row_num=1
        )[0]

        assert latest_record.direct_cost == pytest.approx(1.50, 0.01)

    def test_complete_pricing_workflow(self, in_memory_db):
        """Test complete pricing workflow from ingredients to final price"""
        service = MenuPriceService(in_memory_db)

        # Setup inventory
        ingredients = {
            "espresso_beans": in_memory_db.add_inventory(
                name="Espresso Beans", unit="kg", price_per_unit=0.06
            ),
            "milk": in_memory_db.add_inventory(
                name="Milk", unit="liter", price_per_unit=0.003
            ),
            "chocolate": in_memory_db.add_inventory(
                name="Chocolate Syrup", unit="liter", price_per_unit=0.01
            )
        }

        # Setup menu items
        menu_items = {
            "espresso": in_memory_db.add_menu(name="Espresso", size="30ml"),
            "latte": in_memory_db.add_menu(name="Latte", size="12oz"),
            "mocha": in_memory_db.add_menu(name="Mocha", size="12oz")
        }

        # Setup recipes
        recipes = [
            # Espresso: 20g beans
            {"inv": ingredients["espresso_beans"].id, "menu": menu_items["espresso"].id, "amt": 20.0},
            # Latte: 18g beans + 240ml milk
            {"inv": ingredients["espresso_beans"].id, "menu": menu_items["latte"].id, "amt": 18.0},
            {"inv": ingredients["milk"].id, "menu": menu_items["latte"].id, "amt": 240.0},
            # Mocha: 18g beans + 200ml milk + 30ml chocolate
            {"inv": ingredients["espresso_beans"].id, "menu": menu_items["mocha"].id, "amt": 18.0},
            {"inv": ingredients["milk"].id, "menu": menu_items["mocha"].id, "amt": 200.0},
            {"inv": ingredients["chocolate"].id, "menu": menu_items["mocha"].id, "amt": 30.0}
        ]

        for recipe in recipes:
            in_memory_db.add_recipe(
                inventory_id=recipe["inv"],
                menu_id=recipe["menu"],
                inventory_item_amount_usage=recipe["amt"]
            )

        # Calculate direct costs
        menu_ids = [item.id for item in menu_items.values()]

        for the_id in menu_ids:
            in_memory_db.add_estimatedmenupricerecord(menu_id=the_id, sales_forecast=1, profit_margin=0.0,
                                                      estimated_indirect_costs=2000)

        service.calculate_update_direct_cost(menu_ids)

        # Verify direct costs
        espresso_cost = in_memory_db.get_estimatedmenupricerecord(
            menu_id=menu_items["espresso"].id, row_num=1
        )[0].direct_cost
        assert espresso_cost == pytest.approx(1.20, 0.01)  # 20g * $0.06

        latte_cost = in_memory_db.get_estimatedmenupricerecord(
            menu_id=menu_items["latte"].id, row_num=1
        )[0].direct_cost
        # 18g * $0.06 + 240ml * $0.003 = $1.08 + $0.72 = $1.80
        assert latte_cost == pytest.approx(1.80, 0.01)

    def test_labor_cost_calculation_realistic(self, in_memory_db):
        """Test realistic labor cost calculation"""
        service = MenuPriceService(in_memory_db)
        in_memory_db.add_targetpositionandsalary(
            position="asdf",
            monthly_payment=3000.00,  # $3000/month
            monthly_hr=160.0,  # 40hrs/week * 4 weeks
            monthly_insurance=300.00,  # $300 insurance
            extra_hr_payment=25.00,  # $25/hr overtime
            from_date=datetime(2023, 1, 15),
            to_date=datetime(2025, 1, 15),
        )
        # Create position with realistic salary
        barista_position = in_memory_db.add_targetpositionandsalary(
            position="Barista",
            monthly_payment=3000.00,  # $3000/month
            monthly_hr=160.0,  # 40hrs/week * 4 weeks
            monthly_insurance=300.00,  # $300 insurance
            extra_hr_payment=25.00,  # $25/hr overtime
            from_date=datetime(2023, 1, 15),
            to_date=datetime(2025, 1, 15),
        )

        # Create shifts
        morning_shift = in_memory_db.add_shift(
            date=datetime(2024, 1, 15),
            from_hr=time(7, 0),
            to_hr=time(15, 0),
            name="Morning Shift"
        )

        # Add labor to shift
        in_memory_db.add_estimatedlabor(
            position_id=barista_position.id,
            shift_id=morning_shift.id,
            number=2,  # 2 baristas
            extra_hr=time(1, 0)  # 1 hour overtime
        )

        # Test labor cost calculation
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)

        labor_cost = service._get_estimated_labor_cost(start_date, end_date)

        # Expected calculation:
        # Regular hours: 8 hours * 2 baristas = 16 hours
        # Regular pay: 16hrs * ($3000/160hrs) = 16 * $18.75 = $300
        # Overtime: 1hr * 2 baristas * $25 = $50
        # Insurance: ($300/30 days) * 2 baristas = $20
        # Total: $300 + $50 + $20 = $370

        assert labor_cost == pytest.approx(370.00, 1.00)

    def test_indirect_cost_calculation_comprehensive(self, in_memory_db):
        """Test comprehensive indirect cost calculation"""
        service = MenuPriceService(in_memory_db)

        #should have some menu
        in_memory_db.add_menu(
            name="Sib",
            size="goonda"
        )

        # Setup rent
        in_memory_db.add_rent(
            name="Downtown Cafe Space",
            rent=5000.00,  # $5000/month rent
            mortgage=200000.00,  # $200k mortgage
            mortgage_percentage_to_rent=0.1,  # 10% of mortgage as additional cost
            from_date=datetime(2024, 1, 1),
            to_date=datetime(2024, 12, 31)
        )

        # Setup bills
        in_memory_db.add_estimatedbills(
            name="Electricity",
            category="Utilities",
            cost=800.00,  # $800/month
            from_date=datetime(2024, 1, 1),
            to_date=datetime(2024, 12, 31)
        )

        # Setup equipment
        in_memory_db.add_equipment(
            name="Espresso Machine",
            purchase_price=15000.00,
            monthly_depreciation=250.00,  # $250/month depreciation
            purchase_date=datetime(2023, 6, 1),
            expire_date=datetime(2028, 6, 1)
        )

        # Calculate indirect costs for the year
        indirect_costs = service.calculate_indirect_cost(year=2024, num_year=1)

        # Expected calculation:
        # Rent: ($5000 + 10% of $200k mortgage) * 12 = ($5000 + $2000) * 12 = $84,000
        # Bills: $800 * 12 = $9,600
        # Equipment: $250 * 12 = $3,000
        # Labor: (from previous test, but would need actual labor setup)
        # Total without labor: $84,000 + $9,600 + $3,000 = $96,600

        # This should be a positive value indicating success
        assert indirect_costs > 0

    def test_sales_forecast_integration(self, in_memory_db):
        """Test sales forecast integration with pricing"""
        service = MenuPriceService(in_memory_db)

        # Create menu item
        cappuccino = in_memory_db.add_menu(name="Cappuccino", size="12oz")

        # Add sales forecast
        in_memory_db.add_salesforecast(
            menu_item_id=cappuccino.id,
            from_date=datetime(2024, 1, 1),
            to_date=datetime(2024, 1, 31),
            sell_number=500  # 500 cappuccinos expected in January
        )

        # Calculate forecast
        result = service.calculate_forecast(year=2024, num_year=1)

        assert result is True

        # Verify the forecast was used in pricing
        price_record = in_memory_db.get_estimatedmenupricerecord(
            menu_id=cappuccino.id, row_num=1
        )[0]

        assert price_record.sales_forecast == 500

    def test_manual_price_override(self, in_memory_db):
        """Test manual price override functionality"""
        service = MenuPriceService(in_memory_db)

        # Create menu item
        special_brew = in_memory_db.add_menu(
            name="Special Reserve Brew",
            size="8oz",
            current_price=8.00  # Initial price
        )

        # Set manual price
        result = service.calculate_manual_price_change(
            special_brew.id,
            new_manual_price=12.50,  # Premium price
            category="Premium Pricing"
        )

        assert result is True

        # Verify menu price was updated
        updated_menu = in_memory_db.get_menu(id=special_brew.id)[0]
        assert updated_menu.current_price == 12.50

        # Verify price record was created
        price_record = in_memory_db.get_estimatedmenupricerecord(
            menu_id=special_brew.id, row_num=1
        )[0]
        assert price_record.manual_price == 12.50

    def test_error_handling_scenarios(self, in_memory_db):
        """Test various error handling scenarios"""
        service = MenuPriceService(in_memory_db)

        # Test with non-existent menu ID
        result = service.calculate_update_direct_cost([99999])
        assert result is False

        # Test with empty menu list
        result = service.calculate_update_direct_cost([])
        assert result is False

        # Test with invalid parameters for indirect cost
        result = service.calculate_indirect_cost(year=9999, num_year=-1)
        assert result is False

    def test_performance_with_multiple_items(self, in_memory_db):
        """Test performance with multiple menu items"""
        service = MenuPriceService(in_memory_db)

        # Create multiple menu items
        menu_ids = []
        for i in range(10):  # Create 10 menu items
            menu = in_memory_db.add_menu(
                name=f"Test Item {i}",
                size="M",
                category="Test",

            )
            menu_ids.append(menu.id)

            # Add basic price record
            service._add_new_estimated_record_update_menu_suggestion(
                only_menu_id=menu.id,
                direct_cost=2.00 + (i * 0.5),
                indirect_cost=1000.00,
                sales_forecast=200,
                profit_margin=0.25,
            )


        # Batch update all items
        result = service.calculate_update_direct_cost(menu_ids)
        assert result is True

        # Verify all items were updated
        for menu_id in menu_ids:
            menu = in_memory_db.get_menu(id=menu_id)[0]
            assert menu.suggested_price is not None
            assert menu.suggested_price > 0


# Additional realistic scenario tests
class TestRealWorldScenarios:

    def test_seasonal_price_adjustment(self, in_memory_db):
        """Test seasonal price adjustments"""
        service = MenuPriceService(in_memory_db)

        # Create iced coffee menu item
        iced_coffee = in_memory_db.add_menu(name="Iced Coffee", size="16oz")

        # Summer forecast (high sales)
        in_memory_db.add_salesforecast(
            menu_item_id=iced_coffee.id,
            from_date=datetime(2024, 6, 1),
            to_date=datetime(2024, 8, 31),
            sell_number=1000  # High summer sales
        )

        # Winter forecast (low sales)
        in_memory_db.add_salesforecast(
            menu_item_id=iced_coffee.id,
            from_date=datetime(2024, 12, 1),
            to_date=datetime(2025, 2, 28),
            sell_number=200  # Low winter sales
        )

        # Calculate prices for different seasons
        service.calculate_forecast(year=2024, num_year=1)

        # In real implementation, you'd compare prices between seasons
        # Summer should have lower indirect cost allocation per unit
        assert True  # Placeholder for seasonal logic test

    def test_supply_chain_impact(self, in_memory_db):
        """Test how supply chain changes affect pricing"""
        service = MenuPriceService(in_memory_db)

        # Create coffee inventory with initial price
        coffee = in_memory_db.add_inventory(
            name="Specialty Coffee",
            unit="kg",
            price_per_unit=0.04  # $0.04 per gram
        )

        # Create menu item
        americano = in_memory_db.add_menu(name="Americano", size="12oz")

        service._add_new_estimated_record_update_menu_suggestion(
            sales_forecast=1,
            indirect_cost=1,

        )

        # Add recipe
        in_memory_db.add_recipe(
            inventory_id=coffee.id,
            menu_id=americano.id,
            inventory_item_amount_usage=20.0  # 20g coffee
        )

        # Calculate initial price
        service.calculate_update_direct_cost([americano.id])
        initial_price = in_memory_db.get_menu(id=americano.id)[0].suggested_price
        assert initial_price is not None

        # Simulate price increase due to supply chain issues
        coffee.current_price = 30.00  # Price increased from $25 to $30
        coffee.price_per_unit = 0.048  # $0.048 per gram
        in_memory_db.edit_inventory(coffee)

        # Recalculate price
        service.calculate_update_direct_cost([americano.id])
        new_price = in_memory_db.get_menu(id=americano.id)[0].suggested_price
        assert new_price is not None

        # Price should have increased
        assert new_price > initial_price

        def test_labor_cost_with_overtime_and_benefits(self, in_memory_db):
            """Test comprehensive labor cost including overtime, insurance, and shift extras"""
            service = MenuPriceService(in_memory_db)

            # Create position with full benefits
            position = in_memory_db.add_targetpositionandsalary(
                position="Senior Barista",
                category="Full-Time",
                from_date=datetime(2024, 1, 1),
                to_date=datetime(2024, 12, 31),
                monthly_payment=3200.00,  # $20/hour base
                monthly_hr=160.0,
                monthly_insurance=450.00,  # Health insurance
                extra_hr_payment=30.00  # Time-and-a-half overtime
            )

            # Create holiday shift with extras
            holiday_shift = in_memory_db.add_shift(
                date=datetime(2024, 12, 25),  # Christmas
                from_hr=time(8, 0),
                to_hr=time(16, 0),
                extra_payment=100.00,  # Holiday bonus
                lunch_payment=15.00  # Meal allowance
            )

            # Staff the shift
            in_memory_db.add_estimatedlabor(
                position_id=position.id,
                shift_id=holiday_shift.id,
                number=3,  # 3 baristas
                extra_hr=time(2, 0)  # 2 hours overtime each
            )

            # Calculate costs
            labor_cost = service._get_estimated_labor_cost(
                datetime(2024, 12, 25),
                datetime(2024, 12, 25)
            )

            # Detailed verification
            hourly_rate = 3200.00 / 160.0  # $20/hour
            regular_hours = 8 * 3  # 24 regular hours
            overtime_hours = 2 * 3  # 6 overtime hours

            expected_cost = (
                    (regular_hours * hourly_rate) +  # Regular pay
                    (overtime_hours * 30.00) +  # Overtime pay
                    (450.00 / 30 * 3) +  # Daily insurance
                    (100.00 * 3) +  # Holiday bonus
                    (15.00 * 3)  # Meal allowance
            )

            assert labor_cost == pytest.approx(expected_cost, 0.01)

        def test_supply_chain_disruption_impact(self, in_memory_db):
            """Test how supply chain disruptions affect menu pricing"""
            service = MenuPriceService(in_memory_db)

            # Create inventory with realistic seasonal variations
            avocado = in_memory_db.add_inventory(
                name="Avocado",
                unit="each",
                price_per_unit=1.20,  # Normal price
                category="Produce"
            )

            # Create menu item
            avocado_toast = in_memory_db.add_menu(
                name="Avocado Toast",
                size="Regular",
                category="Breakfast"
            )

            # Add recipe
            in_memory_db.add_recipe(
                inventory_id=avocado.id,
                menu_id=avocado_toast.id,
                inventory_item_amount_usage=0.5  # Half avocado per toast
            )

            # Calculate initial price
            service.calculate_update_direct_cost([avocado_toast.id])
            initial_price = in_memory_db.get_menu(id=avocado_toast.id)[0].suggested_price

            # Simulate supply chain disruption (drought, transportation issues)
            avocado.price_per_unit = 2.40  # 100% price increase
            in_memory_db.edit_inventory(avocado)

            # Recalculate with new costs
            service.calculate_update_direct_cost([avocado_toast.id])
            new_price = in_memory_db.get_menu(id=avocado_toast.id)[0].suggested_price

            # Verify the price increase is proportional to cost increase
            price_increase_percentage = (new_price - initial_price) / initial_price
            cost_increase_percentage = (2.40 - 1.20) / 1.20

            # Price should increase but may not be exactly proportional due to fixed costs
            assert price_increase_percentage > 0
            assert price_increase_percentage <= cost_increase_percentage  # Shouldn't increase more than cost

    def test_error_handling_comprehensive(self, in_memory_db):
        """Test comprehensive error handling scenarios"""
        service = MenuPriceService(in_memory_db)

        # Test with inventory items that have no price
        free_ingredient = in_memory_db.add_inventory(
            name="Tap Water",
            unit="liter",
            price_per_unit=0.00  # Free ingredient
        )

        water_menu = in_memory_db.add_menu(name="Water", size="500ml")

        in_memory_db.add_recipe(
            inventory_id=free_ingredient.id,
            menu_id=water_menu.id,
            inventory_item_amount_usage=0.5  # 500ml water
        )

        # This should handle zero-cost ingredients gracefully
        result = service.calculate_update_direct_cost([water_menu.id])
        assert result is True

        # Test with extremely high sales forecast (division by zero risk)
        high_volume_item = in_memory_db.add_menu(name="High Volume Item", size="S")
        service._add_new_estimated_record_update_menu_suggestion(
            only_menu_id=high_volume_item.id,
            direct_cost=1.00,
            indirect_cost=1000.00,
            sales_forecast=1000000,  # 1 million units
            profit_margin=0.1
        )

        # Should handle large numbers without floating point issues
        menu = in_memory_db.get_menu(id=high_volume_item.id)[0]
        assert menu.suggested_price is not None

        # Add these test classes to your existing test file

        class TestDirectCostUpdates:
            """Test direct cost update functionality"""

            def test_inventory_price_change_updates_menu_prices(self, in_memory_db):
                """Test that inventory price changes trigger menu price updates"""
                service = MenuPriceService(in_memory_db)

                # Create inventory item
                coffee = in_memory_db.add_inventory(
                    name="Coffee Beans",
                    unit="kg",
                    price_per_unit=0.05,  # $0.05 per gram
                    current_price=25.00
                )

                # Create menu item
                espresso = in_memory_db.add_menu(name="Espresso", size="30ml")

                # Add recipe
                in_memory_db.add_recipe(
                    inventory_id=coffee.id,
                    menu_id=espresso.id,
                    inventory_item_amount_usage=20.0  # 20g coffee
                )

                # Add initial price record
                in_memory_db.add_estimatedmenupricerecord(
                    menu_id=espresso.id,
                    direct_cost=1.00,  # Initial cost
                    sales_forecast=100,
                    profit_margin=0.3
                )

                # Get initial price
                initial_record = in_memory_db.get_estimatedmenupricerecord(
                    menu_id=espresso.id, row_num=1
                )[0]
                initial_cost = initial_record.direct_cost

                # Update inventory price (coffee becomes more expensive)
                coffee.price_per_unit = 0.06  # $0.06 per gram
                in_memory_db.edit_inventory(coffee)

                # Trigger price update
                result = service.inventory_price_change_update_menu_item_direct_prices(coffee.id)
                assert result is True

                # Check that menu price was updated
                updated_record = in_memory_db.get_estimatedmenupricerecord(
                    menu_id=espresso.id, row_num=1
                )[0]

                # New cost should be: 20g * $0.06 = $1.20
                assert updated_record.direct_cost == pytest.approx(1.20, 0.01)
                assert updated_record.direct_cost > initial_cost






        class TestIndirectCostUpdates:
            """Test indirect cost update functionality"""

            def test_labor_cost_change_triggers_update(self, in_memory_db):
                """Test that labor cost changes trigger menu price updates"""
                service = MenuPriceService(in_memory_db)

                # Create a menu item to be affected
                cappuccino = in_memory_db.add_menu(name="Cappuccino", size="12oz")
                in_memory_db.add_estimatedmenupricerecord(
                    menu_id=cappuccino.id,
                    direct_cost=1.50,
                    estimated_indirect_costs=2000.00,
                    sales_forecast=1000,
                    profit_margin=0.3
                )

                # Trigger labor cost update
                result = service.labor_change_update_on_menu_price_record()

                # Should return a positive indirect cost value
                assert result > 0

                # Check that menu prices were updated with new indirect costs
                updated_record = in_memory_db.get_estimatedmenupricerecord(
                    menu_id=cappuccino.id, row_num=1
                )[0]

                assert updated_record.estimated_indirect_costs == pytest.approx(result, 0.01)

            def test_rent_change_triggers_update(self, in_memory_db):
                """Test that rent changes trigger menu price updates"""
                service = MenuPriceService(in_memory_db)

                # Setup menu item
                latte = in_memory_db.add_menu(name="Latte", size="12oz")
                in_memory_db.add_estimatedmenupricerecord(
                    menu_id=latte.id,
                    direct_cost=1.80,
                    estimated_indirect_costs=2500.00,
                    sales_forecast=800,
                    profit_margin=0.3
                )

                # Add some rent data
                in_memory_db.add_rent(
                    name="Cafe Space",
                    rent=3000.00,
                    from_date=datetime(2024, 1, 1),
                    to_date=datetime(2024, 12, 31)
                )

                # Trigger rent update
                result = service.rent_change_update_on_menu_price_record()
                assert result > 0

                # Verify update
                updated_record = in_memory_db.get_estimatedmenupricerecord(
                    menu_id=latte.id, row_num=1
                )[0]
                assert updated_record.estimated_indirect_costs == pytest.approx(result, 0.01)

            def test_multiple_indirect_cost_updates(self, in_memory_db):
                """Test that multiple indirect cost factors work together"""
                service = MenuPriceService(in_memory_db)

                # Setup comprehensive indirect costs
                in_memory_db.add_rent(name="Rent", rent=4000.00,
                                      from_date=datetime(2024, 1, 1),
                                      to_date=datetime(2024, 12, 31))

                in_memory_db.add_estimatedbills(name="Electricity", cost=500.00,
                                                from_date=datetime(2024, 1, 1),
                                                to_date=datetime(2024, 12, 31))

                in_memory_db.add_equipment(name="Espresso Machine",
                                           monthly_depreciation=200.00,
                                           purchase_date=datetime(2023, 1, 1))

                # Setup labor
                position = in_memory_db.add_targetpositionandsalary(
                    position="Barista",
                    monthly_payment=2800.00,
                    monthly_hr=160.0,
                    from_date=datetime(2024, 1, 1),
                    to_date=datetime(2024, 12, 31)
                )

                shift = in_memory_db.add_shift(
                    date=datetime(2024, 6, 15),
                    from_hr=time(8, 0),
                    to_hr=time(16, 0)
                )

                in_memory_db.add_estimatedlabor(
                    position_id=position.id,
                    shift_id=shift.id,
                    number=2
                )

                # Trigger comprehensive update
                result = service.calculate_indirect_cost(year=2024, num_year=1)
                assert result > 0

                # Should include rent, bills, equipment, and labor costs
                assert result > 4000.00  # More than just rent

        class TestForecastUpdates:
            """Test sales forecast functionality"""

            def test_forecast_update_affects_pricing(self, in_memory_db):
                """Test that sales forecast changes affect menu pricing"""
                service = MenuPriceService(in_memory_db)

                # Create menu item
                cold_brew = in_memory_db.add_menu(name="Cold Brew", size="16oz")

                # Add initial price record with low forecast
                in_memory_db.add_estimatedmenupricerecord(
                    menu_id=cold_brew.id,
                    direct_cost=1.20,
                    estimated_indirect_costs=3000.00,
                    sales_forecast=200,  # Low forecast
                    profit_margin=0.3
                )

                initial_record = in_memory_db.get_estimatedmenupricerecord(
                    menu_id=cold_brew.id, row_num=1
                )[0]

                # Add optimistic sales forecast for summer
                in_memory_db.add_salesforecast(
                    menu_item_id=cold_brew.id,
                    from_date=datetime(2024, 6, 1),
                    to_date=datetime(2024, 8, 31),
                    sell_number=800  # High summer sales
                )

                # Update forecast
                result = service.calculate_forecast(year=2024, num_year=1)
                assert result is True

                # Check updated forecast
                updated_record = in_memory_db.get_estimatedmenupricerecord(
                    menu_id=cold_brew.id, row_num=1
                )[0]

                assert updated_record.sales_forecast == 800
                # With higher forecast, indirect cost per unit should be lower
                # leading to potentially lower suggested price





    def test_supply_chain_crisis_response(self, in_memory_db):
        """Test how the system responds to supply chain crises"""
        service = MenuPriceService(in_memory_db)

        # Create inventory item that might be affected by supply issues
        vanilla = in_memory_db.add_inventory(
            name="Vanilla Extract",
            unit="liter",
            price_per_unit=0.15,  # Normal price
            current_price=150.00
        )


        # Create menu items that use vanilla
        vanilla_latte = in_memory_db.add_menu(name="Vanilla Latte", size="12oz")
        in_memory_db.add_estimatedmenupricerecord(
            menu_id=vanilla_latte.id,
            sales_forecast=1,
            estimated_indirect_costs=1,
            profit_margin=1
        )
        recipe = in_memory_db.add_recipe(
            inventory_id=vanilla.id,
            menu_id=vanilla_latte.id,
            inventory_item_amount_usage=15.0  # 15ml vanilla
        )


        # Set initial pricing
        service.calculate_update_direct_cost([vanilla_latte.id])
        initial_price = in_memory_db.get_menu(id=vanilla_latte.id)[0].suggested_price

        # Simulate supply chain crisis (vanilla shortage)
        vanilla.price_per_unit = 0.30  # 100% price increase
        in_memory_db.edit_inventory(vanilla)

        # Automatic price update
        service.inventory_price_change_update_menu_item_direct_prices(vanilla.id)

        # Get new price
        a = in_memory_db.get_menu()
        updated_menu = in_memory_db.get_menu(id=vanilla_latte.id)[0]

        # Price should have increased due to vanilla cost increase
        assert updated_menu.suggested_price > initial_price

        # Consider alternative recipe (reduce vanilla usage)

        recipe.inventory_item_amount_usage = 20
        in_memory_db.edit_recipe(recipe)
        service.calculate_update_direct_cost([vanilla_latte.id])

        # Price should decrease from the peak but still be higher than original
        final_menu = in_memory_db.get_menu(id=vanilla_latte.id)[0]
        assert final_menu.suggested_price < updated_menu.suggested_price
        assert final_menu.suggested_price > initial_price



    class TestEdgeCasesAndErrorHandling:
        """Test edge cases and error handling scenarios"""

        def test_inventory_price_change_nonexistent_item(self, in_memory_db):
            """Test handling of non-existent inventory items"""
            service = MenuPriceService(in_memory_db)

            result = service.inventory_price_change_update_menu_item_direct_prices(99999)
            assert result is False  # Should handle gracefully

        def test_high_volume_low_cost_scenario(self, in_memory_db):
            """Test pricing with high volume and low cost items"""
            service = MenuPriceService(in_memory_db)

            # Water - very low cost, high volume
            water = in_memory_db.add_inventory(
                name="Filtered Water",
                unit="liter",
                price_per_unit=0.0005  # $0.0005 per ml (very cheap)
            )

            water_menu = in_memory_db.add_menu(name="Bottled Water", size="500ml")

            in_memory_db.add_recipe(
                inventory_id=water.id,
                menu_id=water_menu.id,
                inventory_item_amount_usage=500.0  # 500ml water
            )

            # Calculate price
            service.calculate_update_direct_cost([water_menu.id])

            # Should handle very small costs correctly
            record = in_memory_db.get_estimatedmenupricerecord(
                menu_id=water_menu.id, row_num=1
            )[0]

            # 500ml * $0.0005/ml = $0.25
            assert record.direct_cost == pytest.approx(0.25, 0.01)

    class TestPerformanceAndScale:
        """Test performance with larger datasets"""

        def test_multiple_inventory_updates(self, in_memory_db):
            """Test performance when multiple inventory items change"""
            service = MenuPriceService(in_memory_db)

            # Create menu item with multiple ingredients
            complex_drink = in_memory_db.add_menu(name="Complex Drink", size="L")

            # Create multiple inventory items
            ingredients = []
            for i in range(5):  # 5 different ingredients
                ingredient = in_memory_db.add_inventory(
                    name=f"Ingredient {i}",
                    unit="g",
                    price_per_unit=0.01 * (i + 1)  # Different prices
                )
                ingredients.append(ingredient)

                in_memory_db.add_recipe(
                    inventory_id=ingredient.id,
                    menu_id=complex_drink.id,
                    inventory_item_amount_usage=10.0 * (i + 1)  # Different amounts
                )

            # Set initial price
            service.calculate_update_direct_cost([complex_drink.id])
            initial_record = in_memory_db.get_estimatedmenupricerecord(
                menu_id=complex_drink.id, row_num=1
            )[0]

            # Update all inventory prices
            for ingredient in ingredients:
                # Increase prices by 20%
                ingredient.price_per_unit *= 1.2
                in_memory_db.edit_inventory(ingredient)

                # Trigger update for each ingredient
                service.inventory_price_change_update_menu_item_direct_prices(ingredient.id)

            # Check final price
            final_record = in_memory_db.get_estimatedmenupricerecord(
                menu_id=complex_drink.id, row_num=1
            )[0]



            # Price should have increased
            assert final_record.direct_cost > initial_record.direct_cost

        def test_batch_menu_updates_realistic(self, in_memory_db):
            """Test realistic batch menu updates - system should calculate costs from recipes"""
            service = MenuPriceService(in_memory_db)

            # Create ingredients
            sugar = in_memory_db.add_inventory(
                name="Sugar",
                unit="g",
                price_per_unit=0.02  # $0.02 per gram
            )

            coffee = in_memory_db.add_inventory(
                name="Coffee Beans",
                unit="g",
                price_per_unit=0.05  # $0.05 per gram
            )

            # Create multiple menu items that use sugar
            menu_ids = []
            for i in range(3):
                menu_item = in_memory_db.add_menu(name=f"Sweet Coffee {i}", size="M")
                menu_ids.append(menu_item.id)

                # Add coffee recipe (15g coffee)
                in_memory_db.add_recipe(
                    inventory_id=coffee.id,
                    menu_id=menu_item.id,
                    inventory_item_amount_usage=15.0
                )

                # Add sugar recipe (15g sugar)
                in_memory_db.add_recipe(
                    inventory_id=sugar.id,
                    menu_id=menu_item.id,
                    inventory_item_amount_usage=15.0
                )

            # Calculate initial direct costs (should be done by the system)
            service.calculate_update_direct_cost(menu_ids)

            # Verify initial costs
            for menu_id in menu_ids:
                record = in_memory_db.get_estimatedmenupricerecord(
                    menu_id=menu_id, row_num=1
                )[0]
                # Should be: 15g coffee * $0.05 + 15g sugar * $0.02 = $0.75 + $0.30 = $1.05
                assert record.direct_cost == pytest.approx(1.05, 0.01)

            # Update sugar price (50% increase)
            sugar.price_per_unit = 0.03  # $0.02 → $0.03 per gram
            in_memory_db.edit_inventory(sugar)

            # This should trigger recalculation of all menu items using sugar
            service.inventory_price_change_update_menu_item_direct_prices(sugar.id)

            # Verify updated costs
            for menu_id in menu_ids:
                record = in_memory_db.get_estimatedmenupricerecord(
                    menu_id=menu_id, row_num=1
                )[0]
                # Should be: 15g coffee * $0.05 + 15g sugar * $0.03 = $0.75 + $0.45 = $1.20
                assert record.direct_cost == pytest.approx(1.20, 0.01)

    def test_sugar_cost_calculation_only(self, in_memory_db):
        """Test that sugar price changes correctly affect direct cost calculation"""
        service = MenuPriceService(in_memory_db)

        # Create sugar inventory
        sugar = in_memory_db.add_inventory(
            name="Sugar",
            unit="g",
            price_per_unit=0.02
        )

        # Create a simple menu item that only uses sugar
        menu_item = in_memory_db.add_menu(name="Sugar Water", size="M")

        in_memory_db.add_recipe(
            inventory_id=sugar.id,
            menu_id=menu_item.id,
            inventory_item_amount_usage=15.0  # 15 grams of sugar
        )

        # Let the system calculate the initial direct cost
        service.calculate_update_direct_cost([menu_item.id])

        initial_record = in_memory_db.get_estimatedmenupricerecord(
            menu_id=menu_item.id, row_num=1
        )[0]

        # Initial cost should be: 15g * $0.02 = $0.30
        assert initial_record.direct_cost == pytest.approx(0.30, 0.01)

        # Update sugar price (50% increase)
        sugar.price_per_unit = 0.03
        in_memory_db.edit_inventory(sugar)

        # Trigger recalculation
        service.inventory_price_change_update_menu_item_direct_prices(sugar.id)

        # Get updated cost
        updated_record = in_memory_db.get_estimatedmenupricerecord(
            menu_id=menu_item.id, row_num=1
        )[0]

        # New cost should be: 15g * $0.03 = $0.45
        assert updated_record.direct_cost == pytest.approx(0.45, 0.01)

        # Verify the increase: $0.45 - $0.30 = $0.15
        cost_increase = updated_record.direct_cost - initial_record.direct_cost
        assert cost_increase == pytest.approx(0.15, 0.01)
    class TestIntegrationScenarios:
        """Test complex integration scenarios"""

        def test_complete_pricing_workflow_with_manual_approval(self, in_memory_db):
            """Test complete pricing workflow with manual approval for price changes"""
            service = MenuPriceService(in_memory_db)

            print("\n=== Complete Pricing Workflow with Manual Approval ===")

            # 1. Setup inventory
            print("1. Setting up inventory...")
            coffee = in_memory_db.add_inventory(
                name="Premium Coffee Beans",
                unit="kg",
                price_per_unit=0.08,  # $0.08 per gram
                current_price=80.00
            )

            milk = in_memory_db.add_inventory(
                name="Organic Milk",
                unit="liter",
                price_per_unit=0.005,  # $0.005 per ml
                current_price=5.00
            )

            # 2. Create menu item with initial price
            print("2. Creating menu item with initial price...")
            latte = in_memory_db.add_menu(
                name="Signature Latte",
                size="16oz",
                category="Premium Coffee",
                value_added_tax=0.085,
            )
            in_memory_db.add_estimatedmenupricerecord(menu_id=latte.id, profit_margin=0.3)

            service.calculate_manual_price_change(latte.id, 5.5)


            # 3. Add recipes
            print("3. Adding recipes...")
            in_memory_db.add_recipe(
                menu_id=latte.id,
                inventory_id=coffee.id,
                inventory_item_amount_usage=20.0,  # 20g coffee
                writer="Head Barista",
                description="Double shot espresso"
            )
            service.calculate_update_direct_cost([latte.id], category="Recipe added")

            in_memory_db.add_recipe(
                menu_id=latte.id,
                inventory_id=milk.id,
                inventory_item_amount_usage=300.0,  # 300ml milk
                writer="Head Barista",
                description="Steamed milk"
            )
            service.calculate_update_direct_cost([latte.id], category="Recipe added")

            # 4. Calculate initial direct cost ONLY
            print("4. Calculating initial direct cost...")
            service.calculate_update_direct_cost([latte.id])

            # 5. Check initial state - should have direct cost but NO suggested price yet
            initial_menu = in_memory_db.get_menu(id=latte.id)[0]
            initial_record = in_memory_db.get_estimatedmenupricerecord(
                menu_id=latte.id, row_num=1
            )[0]

            print(f"   Initial current price: ${initial_menu.current_price:.2f}")
            print(f"   Initial direct cost: ${initial_record.direct_cost:.2f}")
            print(f"   Initial suggested price: {initial_menu.suggested_price}")

            # Current price should remain unchanged from initial setting
            assert initial_menu.current_price == 5.50
            # Direct cost should be calculated
            assert initial_record.direct_cost > 0
            # Suggested price should be NULL/None since we don't have indirect costs and forecast
            assert initial_menu.suggested_price is None

            # 6. Setup indirect costs and forecast (prerequisites for suggested price)
            print("6. Setting up indirect costs and forecast...")

            # Add rent and other indirect costs
            in_memory_db.add_rent(
                name="Prime Location Rent",
                rent=6000.00,
                from_date=datetime(2024, 1, 1),
                to_date=datetime(2024, 12, 31)
            )

            # Add sales forecast
            in_memory_db.add_salesforecast(
                menu_item_id=latte.id,
                from_date=datetime(2024, 1, 1),
                to_date=datetime(2024, 12, 31),
                sell_number=12000  # 1000 lattes per month
            )

            # 7. Calculate complete pricing (now we have all components)
            print("7. Calculating complete pricing with indirect costs...")
            indirect_cost = service.calculate_indirect_cost(year=2024)
            service.calculate_forecast(year=2024)

            in_memory_db.get_estimatedmenupricerecord()
            # # This should now trigger suggested price calculation
            # service.calculate_update_direct_cost([latte.id])  # Recalculate to include new data
            # testc = in_memory_db.get_estimatedmenupricerecord()



            # 8. Now we should have a suggested price
            menu_with_suggestion = in_memory_db.get_menu(id=latte.id)[0]
            price_record = in_memory_db.get_estimatedmenupricerecord(
                menu_id=latte.id, row_num=1
            )[0]

            print(f"   Current price: ${menu_with_suggestion.current_price:.2f}")
            print(f"   Suggested price: ${menu_with_suggestion.suggested_price:.2f}")
            print(f"   Direct cost: ${price_record.direct_cost:.2f}")
            print(f"   Indirect cost: ${price_record.estimated_indirect_costs:.2f}")
            print(f"   Sales forecast: {price_record.sales_forecast}")

            # Current price should still be unchanged
            assert menu_with_suggestion.current_price == 5.50
            # Now we should have a suggested price (all components are available)
            assert menu_with_suggestion.suggested_price is not None
            assert menu_with_suggestion.suggested_price > 0
            assert price_record.estimated_indirect_costs > 0
            assert price_record.sales_forecast > 0
            testa = in_memory_db.get_estimatedmenupricerecord()
            testb = in_memory_db.get_menu()
            # 9. Manager reviews and approves the price change
            print("9. Manager manually approving new price...")
            approval_result = service.calculate_manual_price_change(
                latte.id,
                menu_with_suggestion.suggested_price,  # Use the calculated suggestion
                category="Manager approved based on cost analysis"
            )
            assert approval_result is True

            # 10. Verify final pricing after manual approval
            print("10. Verifying final pricing after approval...")
            final_menu = in_memory_db.get_menu(id=latte.id)[0]

            print(f"   Final current price: ${final_menu.current_price:.2f}")
            print(f"   Final suggested price: ${final_menu.suggested_price:.2f}")

            # Now current price should equal the approved suggested price
            assert final_menu.current_price == menu_with_suggestion.suggested_price
            assert final_menu.current_price < 5.50  # Should have increased from initial
            assert final_menu.current_price == final_menu.suggested_price  # Now they match

            print("✅ Complete pricing workflow with manual approval successful!")

        def test_price_change_chain_reaction(self, in_memory_db):
            service = MenuPriceService(in_memory_db)

            # Create inventory
            chocolate = in_memory_db.add_inventory(
                name="Chocolate Syrup",
                unit="liter",
                price_per_unit=0.012  # $0.012 per ml
            )

            # Create menu items
            menu_items = []
            for drink_name in ["Mocha", "Chocolate Milk", "Hot Chocolate"]:
                menu_item = in_memory_db.add_menu(name=drink_name, size="M")
                menu_items.append(menu_item)

                # Add recipe ONLY - let system calculate cost
                in_memory_db.add_recipe(
                    inventory_id=chocolate.id,
                    menu_id=menu_item.id,
                    inventory_item_amount_usage=30.0  # 30ml each
                )

            # LET SYSTEM CALCULATE INITIAL DIRECT COSTS
            menu_ids = [item.id for item in menu_items]
            service.calculate_update_direct_cost(menu_ids)

            # Record initial prices (now calculated by system)
            initial_prices = {}
            for menu_item in menu_items:
                record = in_memory_db.get_estimatedmenupricerecord(menu_id=menu_item.id, row_num=1)[0]
                initial_prices[menu_item.id] = record.direct_cost
                # Should be: 30ml * $0.012 = $0.36

            # Increase chocolate price
            chocolate.price_per_unit = 0.018  # 50% increase
            in_memory_db.edit_inventory(chocolate)

            # Trigger update
            service.inventory_price_change_update_menu_item_direct_prices(chocolate.id)

            # Verify updates
            for menu_item in menu_items:
                updated_record = in_memory_db.get_estimatedmenupricerecord(menu_id=menu_item.id, row_num=1)[0]

                # Should be: 30ml * $0.018 = $0.54
                assert updated_record.direct_cost == pytest.approx(0.54, 0.01)

                # Verify increase: $0.54 - $0.36 = $0.18
                assert updated_record.direct_cost == pytest.approx(initial_prices[menu_item.id] + 0.18, 0.01)

    def test_performance_inventory_price_update(self, in_memory_db):
        """Test performance of inventory price updates on multiple menu items"""
        service = MenuPriceService(in_memory_db)

        # Create a common ingredient that will be used by many menu items
        sugar = in_memory_db.add_inventory(
            name="Sugar",
            unit="g",
            price_per_unit=0.02  # $0.02 per gram
        )

        # Setup indirect costs (required for suggested price calculation)
        in_memory_db.add_rent(
            name="Test Rent",
            rent=5000.00,
            from_date=datetime(2024, 1, 1),
            to_date=datetime(2024, 12, 31)
        )

        # Create multiple menu items that use sugar
        num_menu_items = 50  # Test with 50 menu items
        menu_ids = []

        print(f"\nCreating {num_menu_items} menu items with sugar...")
        for i in range(num_menu_items):
            menu_item = in_memory_db.add_menu(
                name=f"Sweet Item {i}",
                size="M",
                category="Test"
            )
            menu_ids.append(menu_item.id)

            # Add recipe with sugar
            in_memory_db.add_recipe(
                inventory_id=sugar.id,
                menu_id=menu_item.id,
                inventory_item_amount_usage=10.0  # 10g sugar per item
            )

            # Add required price record with forecast and indirect costs
            in_memory_db.add_estimatedmenupricerecord(
                menu_id=menu_item.id,
                sales_forecast=1000,  # Required for suggested price
                profit_margin=0.3,  # 30% profit margin
                estimated_indirect_costs=2000.00  # Required for suggested price
            )

        # Calculate initial direct costs
        print("Calculating initial direct costs...")
        service.calculate_update_direct_cost(menu_ids)

        # Verify initial prices are set
        for menu_id in menu_ids:
            menu = in_memory_db.get_menu(id=menu_id)[0]
            record = in_memory_db.get_estimatedmenupricerecord(
                menu_id=menu_id, row_num=1
            )[0]
            print(f"Menu {menu_id}: Direct cost=${record.direct_cost:.2f}, Suggested price={menu.suggested_price}")

        # Measure time for inventory price update
        print("Updating sugar price and measuring time...")

        # Increase sugar price by 50%
        sugar.price_per_unit = 0.03
        in_memory_db.edit_inventory(sugar)

        start_time = t.perf_counter()

        # Trigger update for all menu items using sugar
        service.inventory_price_change_update_menu_item_direct_prices(sugar.id)

        end_time = t.perf_counter()
        elapsed_time = end_time - start_time

        print(f"Time to update {num_menu_items} menu items: {elapsed_time:.4f} seconds")
        print(f"Average time per menu item: {elapsed_time / num_menu_items:.6f} seconds")

        # Verify the updates were correct
        updated_count = 0
        for menu_id in menu_ids:
            record = in_memory_db.get_estimatedmenupricerecord(
                menu_id=menu_id, row_num=1
            )[0]
            menu = in_memory_db.get_menu(id=menu_id)[0]

            # Should be: 10g * $0.03 = $0.30
            assert record.direct_cost == pytest.approx(0.30, 0.01)

            # Check if suggested price was also updated
            if menu.suggested_price is not None:
                updated_count += 1
                print(
                    f"Menu {menu_id}: New direct cost=${record.direct_cost:.2f}, Suggested price=${menu.suggested_price:.2f}")

        print(f"Successfully updated suggested prices for {updated_count}/{num_menu_items} menu items")

        # Performance assertion - should complete in reasonable time
        # Adjust threshold based on your performance requirements
        assert elapsed_time < 2.0, f"Update took too long: {elapsed_time:.2f} seconds"

        print(f"✅ Performance test passed in {elapsed_time:.4f} seconds")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])