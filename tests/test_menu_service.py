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

    def test_delete_nonexistent_menu_item(self, in_memory_db):
        """Test deleting a menu item that doesn't exist"""
        service = MenuService(in_memory_db)

        # Try to delete non-existent menu item
        result = service.delete_menu_item(99999)
        assert result is False  # Should return False for non-existent items

    def test_get_nonexistent_menu_item(self, in_memory_db):
        """Test retrieving a menu item that doesn't exist"""
        service = MenuService(in_memory_db)

        # Try to get non-existent menu item
        result = service.get_menu_item(99999)
        assert result is None  # Should return None for non-existent items

    def test_search_menu_items_multiple_criteria(self, in_memory_db):
        """Test searching menu items with multiple criteria"""
        service = MenuService(in_memory_db)

        # Create test data
        in_memory_db.add_menu(name="CofFe", size="M", category="Beverages", serving=True)
        in_memory_db.add_menu(name="Test Tea", size="L", category="Beverages", serving=False)
        in_memory_db.add_menu(name="Test Sandwich", size="Regular", category="Food", serving=True)

        # Search with multiple criteria
        results = service.search_menu_items(name="coffe", category="beverages", serving=True)
        assert len(results) == 1
        assert results[0].name == "coffe"

    def test_list_all_menu_items(self, in_memory_db):
        """Test listing all menu items"""
        service = MenuService(in_memory_db)

        # Clear any existing items
        existing_items = service.list_menu_items()
        for item in existing_items:
            service.delete_menu_item(item.id)

        # Add test items
        in_memory_db.add_menu(name="Item 1", size="S", category="Test")
        in_memory_db.add_menu(name="Item 2", size="M", category="Test")
        in_memory_db.add_menu(name="Item 3", size="L", category="Test")

        # List all items
        results = service.list_menu_items()
        assert len(results) == 3

    def test_remove_nonexistent_recipe_item(self, in_memory_db):
        """Test removing a recipe item that doesn't exist"""
        service = MenuService(in_memory_db)

        # Create menu and inventory items
        menu = in_memory_db.add_menu(name="Test Menu", size="M")
        inventory = in_memory_db.add_inventory(name="Test Inventory", unit="kg")

        # Try to remove non-existent recipe
        result = service.remove_recipe_item(menu.id, inventory.id)
        assert result is False  # Should return False

    def test_clear_recipe_empty_menu(self, in_memory_db):
        """Test clearing recipes from a menu with no recipes"""
        service = MenuService(in_memory_db)

        # Create menu with no recipes
        menu = in_memory_db.add_menu(name="Empty Menu", size="M")

        # Clear recipes (should succeed even with no recipes)
        result = service.clear_recipe(menu.id)
        assert result is True

    def test_clear_recipe_with_existing_recipes(self, in_memory_db):
        """Test clearing recipes from a menu with existing recipes"""
        service = MenuService(in_memory_db)

        # Create menu and inventory
        menu = in_memory_db.add_menu(name="Test Menu", size="M")
        inventory1 = in_memory_db.add_inventory(name="Ingredient 1", unit="kg")
        inventory2 = in_memory_db.add_inventory(name="Ingredient 2", unit="kg")

        # Add recipes
        in_memory_db.add_recipe(menu_id=menu.id, inventory_id=inventory1.id, inventory_item_amount_usage=10.0)
        in_memory_db.add_recipe(menu_id=menu.id, inventory_id=inventory2.id, inventory_item_amount_usage=5.0)

        # Verify recipes exist
        recipes_before = service.get_recipe_items_of_menu_item(menu.id)
        assert len(recipes_before) == 2

        # Clear recipes
        result = service.clear_recipe(menu.id)
        assert result is True

        # Verify recipes are gone
        recipes_after = service.get_recipe_items_of_menu_item(menu.id)
        assert len(recipes_after) == 0

    def test_clone_menu_item_with_recipes(self, in_memory_db):
        """Test cloning a menu item with its recipes"""
        service = MenuService(in_memory_db)

        # Create original menu item with recipes
        menu = in_memory_db.add_menu(
            name="Original Drink",
            size="M",
            category="Beverages",
            value_added_tax=0.07,
            current_price=5.99,
            serving=True,
            description="Original description"
        )

        # Add ingredients
        ingredient1 = in_memory_db.add_inventory(name="Ingredient A", unit="kg")
        ingredient2 = in_memory_db.add_inventory(name="Ingredient B", unit="ml")

        # Add recipes
        in_memory_db.add_recipe(
            menu_id=menu.id,
            inventory_id=ingredient1.id,
            inventory_item_amount_usage=10.0,
            writer="Chef",
            description="Primary ingredient"
        )

        in_memory_db.add_recipe(
            menu_id=menu.id,
            inventory_id=ingredient2.id,
            inventory_item_amount_usage=50.0,
            writer="Chef",
            description="Secondary ingredient"
        )

        # Clone the menu item
        cloned_menu = service.clone_menu_item(menu.id, "Cloned Drink")
        assert cloned_menu is not None
        assert cloned_menu.name == "cloned drink"
        assert cloned_menu.size == "m"
        assert cloned_menu.category == "beverages"
        assert cloned_menu.value_added_tax == 0.07
        assert cloned_menu.description == "Original description"

        # Verify recipes were copied
        cloned_recipes = service.get_recipe_items_of_menu_item(cloned_menu.id)
        assert len(cloned_recipes) == 2

    def test_clone_nonexistent_menu_item(self, in_memory_db):
        """Test cloning a menu item that doesn't exist"""
        service = MenuService(in_memory_db)

        result = service.clone_menu_item(99999, "New Name")
        assert result is None  # Should return None for non-existent items

    def test_edge_case_names_and_categories(self, in_memory_db):
        """Test handling of edge cases with names and categories"""
        service = MenuService(in_memory_db)

        # Test with empty strings
        result1 = service.add_menu_item(
            name="",  # Empty name
            size="M",
            category="Test",
            value_added_tax=0.07
        )
        assert result1 is False  # Should fail validation

        # Test with very long names
        long_name = "A" * 200  # Within 255 character limit
        result2 = service.add_menu_item(
            name=long_name,
            size="M",
            category="Test",
            value_added_tax=0.07
        )
        assert result2 is True

        # Test with special characters
        result3 = service.add_menu_item(
            name="Café Latte & Mocha",
            size="M",
            category="Beverages@Special",
            value_added_tax=0.07
        )
        assert result3 is True

    def test_recipe_management_comprehensive(self, in_memory_db):
        """Comprehensive test of recipe management functionality"""
        service = MenuService(in_memory_db)

        # Setup
        menu = in_memory_db.add_menu(name="Test Drink", size="M")
        ingredients = []
        for i in range(5):
            ingredient = in_memory_db.add_inventory(name=f"Ingredient {i}", unit="kg")
            ingredients.append(ingredient)

        # Add multiple recipes
        for i, ingredient in enumerate(ingredients):
            result = service.add_recipe_of_menu_item(
                menu_id=menu.id,
                inventory_id=ingredient.id,
                amount=(i + 1) * 10.0,  # 10, 20, 30, 40, 50
                writer=f"Chef {i}",
                note=f"Note {i}"
            )
            assert result is True

        # Verify all recipes were added
        recipe_items = service.get_recipe_items_of_menu_item(menu.id)
        assert len(recipe_items) == 5

        # Update one recipe
        result = service.change_recipe_of_menu_item(
            menu_id=menu.id,
            inventory_id=ingredients[0].id,
            amount=15.0,  # Update from 10 to 15
            writer="Updated Chef",
            note="Updated note"
        )
        assert result is True

        # Remove one recipe
        result = service.remove_recipe_item(menu.id, ingredients[1].id)
        assert result is True

        # Verify updated count
        recipe_items = service.get_recipe_items_of_menu_item(menu.id)
        assert len(recipe_items) == 4

        # Clear all recipes
        result = service.clear_recipe(menu.id)
        assert result is True

        # Verify all recipes are gone
        recipe_items = service.get_recipe_items_of_menu_item(menu.id)
        assert len(recipe_items) == 0