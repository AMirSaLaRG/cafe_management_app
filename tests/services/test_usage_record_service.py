import pytest
from datetime import datetime, timedelta
from services.usage_record_service import OtherUsageService
from models.cafe_managment_models import Usage, InventoryUsage, MenuUsage
from models.dbhandler import DBHandler


class TestOtherUsageService:
    def test_create_usage_record(self, in_memory_db):
        """Test creating a new usage record"""
        service = OtherUsageService(in_memory_db)

        # Create a new usage record
        usage = service.new_usage_record(
            used_by="staff_member",
            category="cleaning",
            date=datetime(2024, 1, 15, 10, 30),
            description="Daily cleaning supplies usage"
        )

        assert usage is not None
        assert usage.used_by == "staff_member"
        assert usage.category == "cleaning"
        assert usage.date == datetime(2024, 1, 15, 10, 30)
        assert usage.description == "Daily cleaning supplies usage"

    def test_get_usage_by_id(self, in_memory_db):
        """Test finding usage record by ID"""
        service = OtherUsageService(in_memory_db)

        # First create usage record
        created_usage = service.new_usage_record(
            used_by="manager",
            category="maintenance",
            date=datetime(2024, 1, 16, 14, 0)
        )

        # Now find it
        found_usage = service.get_usage_by_id(created_usage.id)

        assert found_usage is not None
        assert found_usage.id == created_usage.id
        assert found_usage.used_by == "manager"
        assert found_usage.category == "maintenance"

    def test_get_usage_records_with_filters(self, in_memory_db):
        """Test finding usage records with various filters"""
        service = OtherUsageService(in_memory_db)

        # Create multiple usage records
        cleaning_usage = service.new_usage_record(
            used_by="staff_a",
            category="cleaning",
            date=datetime(2024, 1, 15, 9, 0),
            description="Morning cleaning"
        )

        maintenance_usage = service.new_usage_record(
            used_by="manager",
            category="maintenance",
            date=datetime(2024, 1, 16, 14, 0),
            description="Equipment maintenance"
        )

        another_cleaning = service.new_usage_record(
            used_by="staff_b",
            category="cleaning",
            date=datetime(2024, 1, 17, 17, 0),
            description="Evening cleaning"
        )

        # Find by category
        cleaning_records = service.get_usage_records(category="cleaning")
        assert len(cleaning_records) == 2

        # Find by used_by
        manager_records = service.get_usage_records(used_by="manager")
        assert len(manager_records) == 1
        assert manager_records[0].category == "maintenance"

        # Find by date range
        jan_16_records = service.get_usage_records(
            from_date=datetime(2024, 1, 16),
            to_date=datetime(2024, 1, 16, 23, 59, 59)
        )
        assert len(jan_16_records) == 1
        assert jan_16_records[0].used_by == "manager"

    def test_update_usage_record(self, in_memory_db):
        """Test updating usage record information"""
        service = OtherUsageService(in_memory_db)

        # Create usage record
        usage = service.new_usage_record(
            used_by="staff",
            category="cleaning",
            date=datetime(2024, 1, 15),
            description="Initial description"
        )

        # Update it
        updated_usage = service.update_usage_record(
            usage,
            used_by="updated_staff",
            category="updated_category",
            description="Updated description"
        )

        assert updated_usage is not None
        assert updated_usage.used_by == "updated_staff"
        assert updated_usage.category == "updated_category"
        assert updated_usage.description == "Updated description"

    def test_delete_usage_record(self, in_memory_db):
        """Test deleting a usage record"""
        service = OtherUsageService(in_memory_db)

        # Create usage record
        usage = service.new_usage_record(
            used_by="staff",
            category="cleaning",
            date=datetime(2024, 1, 15)
        )

        # Delete it
        result = service.delete_usage_record(usage)
        assert result == True

        # Verify it's gone
        found_usage = service.get_usage_by_id(usage.id)
        assert found_usage is None

    def test_add_inventory_usage(self, in_memory_db):
        """Test adding inventory usage to a usage record"""
        service = OtherUsageService(in_memory_db)

        # First create a usage record
        usage = service.new_usage_record(
            used_by="staff",
            category="cleaning",
            date=datetime(2024, 1, 15)
        )

        # Add inventory usage (assuming inventory item with ID 1 exists)
        inventory_usage = service.add_inventory_usage(
            inventory_item_id=1,
            usage_id=usage.id,
            amount=2.5
        )

        assert inventory_usage is not None
        assert inventory_usage.inventory_item_id == 1
        assert inventory_usage.usage_id == usage.id
        assert inventory_usage.amount == 2.5

    def test_get_inventory_usage(self, in_memory_db):
        """Test retrieving inventory usage records"""
        service = OtherUsageService(in_memory_db)

        # Create usage record and inventory usage
        usage = service.new_usage_record(
            used_by="staff",
            category="cleaning",
            date=datetime(2024, 1, 15)
        )

        service.add_inventory_usage(
            inventory_item_id=1,
            usage_id=usage.id,
            amount=2.5
        )

        service.add_inventory_usage(
            inventory_item_id=2,
            usage_id=usage.id,
            amount=1.0
        )

        # Get all inventory usage for this usage record
        inventory_usages = service.get_inventory_usage(usage_id=usage.id)
        assert len(inventory_usages) == 2

        # Get inventory usage for specific item
        item_usages = service.get_inventory_usage(inventory_item_id=1)
        assert len(item_usages) == 1
        assert item_usages[0].amount == 2.5

    def test_update_inventory_usage(self, in_memory_db):
        """Test updating inventory usage amount"""
        service = OtherUsageService(in_memory_db)

        in_memory_db.add_inventory(name="inventory_item")

        # Create usage record and inventory usage
        usage = service.new_usage_record(
            used_by="staff",
            category="cleaning",
            date=datetime(2024, 1, 15)
        )

        inventory_usage = service.add_inventory_usage(
            inventory_item_id=1,
            usage_id=usage.id,
            amount=2.5
        )

        # Update the amount
        updated_inventory_usage = service.update_inventory_usage(
            inventory_usage,
            amount=3.0
        )

        assert updated_inventory_usage is not None
        assert updated_inventory_usage.amount == 3.0

    def test_delete_inventory_usage(self, in_memory_db):
        """Test deleting inventory usage record"""
        service = OtherUsageService(in_memory_db)

        # Create usage record and inventory usage
        usage = service.new_usage_record(
            used_by="staff",
            category="cleaning",
            date=datetime(2024, 1, 15)
        )

        inventory_usage = service.add_inventory_usage(
            inventory_item_id=1,
            usage_id=usage.id,
            amount=2.5
        )

        # Delete it
        result = service.delete_inventory_usage(inventory_usage)
        assert result == True

    def test_add_menu_usage(self, in_memory_db):
        """Test adding menu usage to a usage record"""
        service = OtherUsageService(in_memory_db)

        # First create a usage record
        usage = service.new_usage_record(
            used_by="staff",
            category="tasting",
            date=datetime(2024, 1, 15)
        )

        # Add menu usage (assuming menu item with ID 1 exists)
        menu_usage = service.add_menu_usage(
            menu_id=1,
            usage_id=usage.id,
            amount=1
        )

        assert menu_usage is not None
        assert menu_usage.menu_id == 1
        assert menu_usage.usage_id == usage.id
        assert menu_usage.amount == 1

    def test_real_world_scenario_daily_operations(self, in_memory_db):
        """Test a real-world scenario: daily operations usage tracking"""
        service = OtherUsageService(in_memory_db)

        # Morning cleaning routine
        morning_cleaning = service.new_usage_record(
            used_by="opening_staff",
            category="cleaning",
            date=datetime(2024, 1, 15, 8, 0),
            description="Morning opening cleaning routine"
        )

        # Add cleaning supplies used
        service.add_inventory_usage(
            inventory_item_id=101,  # Cleaning solution
            usage_id=morning_cleaning.id,
            amount=0.5
        )

        service.add_inventory_usage(
            inventory_item_id=102,  # Paper towels
            usage_id=morning_cleaning.id,
            amount=10
        )

        # Mid-day maintenance
        equipment_maintenance = service.new_usage_record(
            used_by="technician",
            category="maintenance",
            date=datetime(2024, 1, 15, 14, 0),
            description="Espresso machine maintenance"
        )

        service.add_inventory_usage(
            inventory_item_id=201,  # Machine cleaner
            usage_id=equipment_maintenance.id,
            amount=0.2
        )

        # Evening staff tasting session
        tasting_session = service.new_usage_record(
            used_by="all_staff",
            category="training",
            date=datetime(2024, 1, 15, 17, 0),
            description="New menu item tasting"
        )

        service.add_menu_usage(
            menu_id=5,  # New coffee blend
            usage_id=tasting_session.id,
            amount=4  # 4 cups tasted
        )

        service.add_menu_usage(
            menu_id=8,  # New pastry
            usage_id=tasting_session.id,
            amount=2  # 2 pastries tasted
        )

        # Verify all records were created
        daily_records = service.get_usage_records(
            from_date=datetime(2024, 1, 15),
            to_date=datetime(2024, 1, 15, 23, 59, 59)
        )
        assert len(daily_records) == 3

        # Verify inventory usage totals
        cleaning_inventory = service.get_inventory_usage(usage_id=morning_cleaning.id)
        assert len(cleaning_inventory) == 2

        # Verify menu usage
        tasting_menu = service.get_menu_usage(usage_id=tasting_session.id)
        assert len(tasting_menu) == 2
        total_tasted = sum(mu.amount for mu in tasting_menu)
        assert total_tasted == 6

    def test_real_world_scenario_waste_tracking(self, in_memory_db):
        """Test waste tracking scenario"""
        service = OtherUsageService(in_memory_db)

        # Daily waste recording
        waste_records = []
        for day in range(1, 8):  # One week of waste tracking
            waste_record = service.new_usage_record(
                used_by="closing_staff",
                category="waste",
                date=datetime(2024, 1, day, 22, 0),
                description=f"End of day waste - Day {day}"
            )
            waste_records.append(waste_record)

            # Record wasted items
            service.add_menu_usage(
                menu_id=3,  # Baked goods
                usage_id=waste_record.id,
                amount=day * 2  # Increasing waste for demo
            )

            service.add_menu_usage(
                menu_id=5,  # Coffee
                usage_id=waste_record.id,
                amount=day * 0.5
            )

        # Analyze weekly waste
        weekly_waste = service.get_usage_records(
            category="waste",
            from_date=datetime(2024, 1, 1),
            to_date=datetime(2024, 1, 7, 23, 59, 59)
        )
        assert len(weekly_waste) == 7

        # Calculate total waste
        total_waste = 0
        for waste_record in weekly_waste:
            menu_waste = service.get_menu_usage(usage_id=waste_record.id)
            total_waste += sum(mw.amount for mw in menu_waste)

        assert total_waste > 0

    def test_real_world_scenario_comprehensive_usage(self, in_memory_db):
        """Test comprehensive usage tracking across multiple categories"""
        service = OtherUsageService(in_memory_db)

        # Create usage records for different purposes
        categories = {
            "cleaning": ["daily_clean", "deep_clean", "sanitizing"],
            "maintenance": ["equipment", "furniture", "plumbing"],
            "training": ["new_staff", "menu_tasting", "barista_skills"],
            "waste": ["food", "beverage", "packaging"],
            "testing": ["quality_control", "new_recipes", "customer_feedback"]
        }

        records_created = []
        for category, sub_categories in categories.items():
            for sub_category in sub_categories:
                record = service.new_usage_record(
                    used_by="various_staff",
                    category=category,
                    date=datetime(2024, 1, 15),
                    description=f"{sub_category} {category}"
                )
                records_created.append(record)

                # Add some inventory usage for each record
                if category in ["cleaning", "maintenance"]:
                    service.add_inventory_usage(
                        inventory_item_id=1,
                        usage_id=record.id,
                        amount=1.0
                    )

                # Add some menu usage for each record
                if category in ["training", "waste", "testing"]:
                    service.add_menu_usage(
                        menu_id=1,
                        usage_id=record.id,
                        amount=1
                    )

        # Verify all records were created
        all_records = service.get_usage_records(
            from_date=datetime(2024, 1, 15),
            to_date=datetime(2024, 1, 15, 23, 59, 59)
        )
        assert len(all_records) == len(records_created)

        # Test category-based filtering
        for category in categories.keys():
            category_records = service.get_usage_records(category=category)
            assert len(category_records) == len(categories[category])

        # Test comprehensive search capabilities
        training_records = service.get_usage_records(
            category="training",
            used_by="various_staff"
        )
        assert len(training_records) == 3

    def test_error_handling_edge_cases(self, in_memory_db):
        """Test error handling and edge cases"""
        service = OtherUsageService(in_memory_db)

        # Test with None values
        usage = service.new_usage_record(
            used_by=None,
            category=None,
            date=datetime(2024, 1, 15)
        )
        assert usage is not None

        # Test updating non-existent record
        non_existent_usage = Usage(id=9999, used_by="test", category="test", date=datetime.now())
        result = service.update_usage_record(non_existent_usage, used_by="updated")
        assert result is None

        # Test deleting non-existent record
        result = service.delete_usage_record(non_existent_usage)
        assert result == False

    def test_usage_record_lifecycle(self, in_memory_db):
        """Test complete lifecycle of usage records"""
        service = OtherUsageService(in_memory_db)

        # Create
        usage = service.new_usage_record(
            used_by="test_staff",
            category="test_category",
            date=datetime(2024, 1, 15),
            description="Initial record"
        )

        # Read
        found_usage = service.get_usage_by_id(usage.id)
        assert found_usage is not None

        # Update
        updated_usage = service.update_usage_record(
            usage,
            used_by="updated_staff",
            description="Updated record"
        )
        assert updated_usage.used_by == "updated_staff"

        # Add related records
        inventory_usage = service.add_inventory_usage(
            inventory_item_id=1,
            usage_id=usage.id,
            amount=5.0
        )
        assert inventory_usage is not None

        menu_usage = service.add_menu_usage(
            menu_id=1,
            usage_id=usage.id,
            amount=3
        )
        assert menu_usage is not None

        # Verify relationships
        related_inventory = service.get_inventory_usage(usage_id=usage.id)
        assert len(related_inventory) == 1

        related_menu = service.get_menu_usage(usage_id=usage.id)
        assert len(related_menu) == 1

        # Delete
        result = service.delete_usage_record(usage)
        #it is not cascaded so it should avoid getting delete while has child
        assert result == False

        # Verify deletion cascades (or related records are handled appropriately)
        # This depends on your database configuration
        remaining_inventory = service.get_inventory_usage(usage_id=usage.id)
        remaining_menu = service.get_menu_usage(usage_id=usage.id)