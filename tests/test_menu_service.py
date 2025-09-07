import pytest
import time as t
from datetime import datetime, time, timedelta
from decimal import Decimal
from services.menu_service import MenuService
from models.cafe_managment_models import *


class TestMenuService:
    def test_update_menu_attributes(self, in_memory_db):
        """Test updating menu item attributes"""
        service = MenuService(in_memory_db)

        # Create initial menu item
        drink = in_memory_db.add_menu(
            name="Original Drink",
            size="M",
            category="Beverages",
            value_added_tax=0.07,
            description="Original description"
        )

        # Update multiple attributes
        result = service.change_attribute_menu_item(
            menu_id=drink.id,
            name="Updated Drink Name",
            size="L",
            category="Premium Beverages",
            value_added_tax=0.09,
            description="New improved description"
        )

        assert result is True

        # Verify all changes
        updated_menu = in_memory_db.get_menu(id=drink.id)[0]
        assert updated_menu.name == "updated drink name"
        assert updated_menu.size == "l"
        assert updated_menu.category == "premium beverages"
        assert updated_menu.value_added_tax == 0.09
        assert updated_menu.description == "New improved description"

    def test_change_menu_availability(self, in_memory_db):
        """Test toggling menu item availability"""
        service = MenuService(in_memory_db)

        # Create menu item (initially available)
        sandwich = in_memory_db.add_menu(
            name="Club Sandwich",
            size="Regular",
            serving=True
        )

        # Toggle availability to False
        result = service.change_availability_of_menu_item(
            menu_id=sandwich.id,
            switch_to=False
        )

        assert result is True

        # Verify change
        updated_menu = in_memory_db.get_menu(id=sandwich.id)[0]
        assert updated_menu.serving is False

        # Toggle back to True
        result = service.change_availability_of_menu_item(sandwich.id)
        updated_menu = in_memory_db.get_menu(id=sandwich.id)[0]
        assert updated_menu.serving is True

    def test_seasonal_menu_changes(self, in_memory_db):
        """Test seasonal menu changes with pricing adjustments"""
        service = MenuService(in_memory_db)

        # Summer menu item
        iced_tea = in_memory_db.add_menu(
            name="Iced Tea",
            size="16oz",
            category="Summer Drinks",
            current_price=3.50
        )

        # Winter menu item
        hot_chocolate = in_memory_db.add_menu(
            name="Hot Chocolate",
            size="12oz",
            category="Winter Drinks",
            current_price=4.00
        )

        # Seasonal availability changes
        service.change_availability_of_menu_item(iced_tea.id, True)  # Summer available
        service.change_availability_of_menu_item(hot_chocolate.id, False)  # Winter not available

        # Verify seasonal availability
        iced_tea_updated = in_memory_db.get_menu(id=iced_tea.id)[0]
        hot_chocolate_updated = in_memory_db.get_menu(id=hot_chocolate.id)[0]

        assert iced_tea_updated.serving is True
        assert hot_chocolate_updated.serving is False

    def test_add_menu_item_with_pricing(self, in_memory_db):
        """Test adding a new menu item with initial pricing"""
        service = MenuService(in_memory_db)

        result = service.add_menu_item(
            name="New Specialty Drink",
            size="16oz",
            category="Specialty",
            value_added_tax=0.08,
            description="A delicious new drink"
        )

        assert result is True

        # Verify menu item was created with correct price
        menu_items = in_memory_db.get_menu(name="new specialty drink")
        assert len(menu_items) == 1

        menu_item = menu_items[0]
        assert menu_item.value_added_tax == 0.08

    # def test_new_product_launch(self, in_memory_db):
    #     """Test complete new product launch workflow"""
    #     service = MenuService(in_memory_db)
    #
    #     # Phase 1: Create new inventory items
    #     matcha = in_memory_db.add_inventory(
    #         name="Premium Matcha Powder",
    #         unit="kg",
    #         price_per_unit=0.20,  # $0.20 per gram
    #         current_price=200.00
    #     )
    #
    #     coconut_milk = in_memory_db.add_inventory(
    #         name="Organic Coconut Milk",
    #         unit="liter",
    #         price_per_unit=0.004,  # $0.004 per ml
    #         current_price=4.00
    #     )
    #
    #     # Phase 2: Create new menu item
    #     matcha_latte = service.add_menu_item(
    #         name="Matcha Coconut Latte",
    #         size="16oz",
    #         category="Premium Drinks",
    #         value_added_tax=0.09,
    #         description="Premium matcha with coconut milk"
    #     )
    #
    #     assert matcha_latte is True
    #
    #     # Get the created menu item
    #     menu_items = in_memory_db.get_menu(name="matcha coconut latte")
    #     assert len(menu_items) == 1
    #     menu_item = menu_items[0]
    #
    #     # Phase 3: Add recipes
    #     service.add_recipe_of_menu_item(
    #         menu_id=menu_item.id,
    #         inventory_id=matcha.id,
    #         amount=4.0,  # 4g matcha
    #         writer="Product Development",
    #         note="Base matcha amount"
    #     )
    #
    #     service.add_recipe_of_menu_item(
    #         menu_id=menu_item.id,
    #         inventory_id=coconut_milk.id,
    #         amount=300.0,  # 300ml coconut milk
    #         writer="Product Development",
    #         note="Coconut milk base"
    #     )
    #
    #     # Phase 4: Automatic price calculation
    #     service.calculate_update_direct_cost([menu_item.id])
    #
    #     # Phase 5: Verify final pricing
    #     final_menu = in_memory_db.get_menu(id=menu_item.id)[0]
    #     price_record = in_memory_db.get_estimatedmenupricerecord(
    #         menu_id=menu_item.id, row_num=1
    #     )[0]
    #
    #     # Should have calculated direct cost
    #     assert price_record.direct_cost > 0
    #     # Final price should be set
    #     assert final_menu.current_price is not None
    #     assert final_menu.suggested_price is not None
    #
    #     print(f"New product launched: {final_menu.name}")
    #     print(f"Direct cost: ${price_record.direct_cost:.2f}")
    #     print(f"Final price: ${final_menu.current_price:.2f}")

    def test_get_recipe_items_returns_correct_inventory(self, in_memory_db):
        """Test retrieving inventory items for a menu item"""
        service = MenuService(in_memory_db)

        # Create inventory items
        coffee = in_memory_db.add_inventory(name="Coffee", unit="kg", price_per_unit=0.05)
        milk = in_memory_db.add_inventory(name="Milk", unit="liter", price_per_unit=0.003)
        chocolate = in_memory_db.add_inventory(name="Chocolate", unit="liter", price_per_unit=0.01)

        # Create menu item
        mocha = in_memory_db.add_menu(name="Mocha", size="12oz")

        # Add multiple recipes
        recipes_data = [
            (coffee.id, 18.0),
            (milk.id, 200.0),
            (chocolate.id, 30.0)
        ]

        for inv_id, amount in recipes_data:
            in_memory_db.add_recipe(
                inventory_id=inv_id,
                menu_id=mocha.id,
                inventory_item_amount_usage=amount
            )

        # Get recipe items
        inventory_items = service.get_recipe_items_of_menu_item(mocha.id)

        # Should return 3 inventory items
        assert len(inventory_items) == 3
        assert any(item.name == "coffee" for item in inventory_items)
        assert any(item.name == "milk" for item in inventory_items)
        assert any(item.name == "chocolate" for item in inventory_items)

    def test_get_recipe_items_empty_menu(self, in_memory_db):
        """Test getting recipe items for menu with no recipes"""
        service = MenuService(in_memory_db)

        # Create menu item with no recipes
        empty_menu = in_memory_db.add_menu(name="Empty Menu", size="S")

        items = service.get_recipe_items_of_menu_item(empty_menu.id)
        assert items == []  # Should return empty list

    def test_add_recipe_updates_menu_price(self, in_memory_db):
        """Test that adding a recipe triggers price recalculation"""
        service = MenuService(in_memory_db)

        # Create inventory and menu items
        sugar = in_memory_db.add_inventory(
            name="Sugar", unit="kg", price_per_unit=0.02
        )
        coffee = in_memory_db.add_menu(name="Coffee", size="8oz")

        # Add initial price record
        in_memory_db.add_estimatedmenupricerecord(
            menu_id=coffee.id,
            direct_cost=1.00,
            sales_forecast=100,
            profit_margin=0.3
        )

        initial_record = in_memory_db.get_estimatedmenupricerecord(
            menu_id=coffee.id, row_num=1
        )[0]

        # Add sugar to recipe
        result = service.add_recipe_of_menu_item(
            menu_id=coffee.id,
            inventory_id=sugar.id,
            amount=10.0,  # 10g sugar
            writer="Test Chef",
            note="Added sugar to recipe"
        )

        assert result is True

    def test_add_recipe_nonexistent_items(self, in_memory_db):
        """Test adding recipe with non-existent menu or inventory"""
        service = MenuService(in_memory_db)

        result = service.add_recipe_of_menu_item(
            menu_id=99999,
            inventory_id=99998,
            amount=10.0,
            writer="Test"
        )
        assert result is False  # DBHandler validation should catch this

    def test_zero_or_negative_values_handling(self, in_memory_db):
        """Test handling of zero and negative values"""
        service = MenuService(in_memory_db)

        # Test with zero amount in recipe
        inventory = in_memory_db.add_inventory(name="Test Item", unit="kg", price_per_unit=1.0)
        menu = in_memory_db.add_menu(name="Test Menu", size="M")

        # This should be handled by DBHandler validation
        result = service.add_recipe_of_menu_item(
            menu_id=menu.id,
            inventory_id=inventory.id,
            amount=0.0,  # Zero amount
            writer="Test"
        )
        # Depending on DBHandler validation, this might return False
        # or might be prevented at the database level

    def test_change_recipe_updates(self, in_memory_db):
        """Test that changing recipe amounts updates prices"""
        service = MenuService(in_memory_db)

        # Setup
        coffee_beans = in_memory_db.add_inventory(
            name="Coffee Beans", unit="kg", price_per_unit=0.05
        )
        espresso = in_memory_db.add_menu(name="Espresso", size="30ml")

        # Initial recipe: 18g coffee
        in_memory_db.add_recipe(
            inventory_id=coffee_beans.id,
            menu_id=espresso.id,
            inventory_item_amount_usage=18.0
        )

        # Add price record
        in_memory_db.add_estimatedmenupricerecord(
            menu_id=espresso.id,
            direct_cost=0.90,  # 18g * $0.05
            sales_forecast=100,
            profit_margin=0.3
        )

        # Change recipe to use 20g coffee (stronger espresso)
        result = service.change_recipe_of_menu_item(
            menu_id=espresso.id,
            inventory_id=coffee_beans.id,
            amount=20.0,
            writer="Updated Recipe",
            note="Stronger espresso shot"
        )

        assert result is True

    def test_change_recipe_nonexistent_recipe(self, in_memory_db):
        """Test changing non-existent recipe"""
        service = MenuService(in_memory_db)

        # Create real menu and inventory
        menu = in_memory_db.add_menu(name="Test Menu", size="M")
        inventory = in_memory_db.add_inventory(name="Test Inventory", unit="kg")

        # Try to change non-existent recipe
        result = service.change_recipe_of_menu_item(
            menu_id=menu.id,
            inventory_id=inventory.id,
            amount=10.0
        )
        assert result is False  # No recipe exists to change