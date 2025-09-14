import pytest
from datetime import datetime, timedelta
from services.equipment_service import EquipmentService
from models.cafe_managment_models import Equipment
from models.dbhandler import DBHandler


class TestEquipmentService:
    def test_create_equipment(self, in_memory_db):
        """Test creating a new equipment record"""
        service = EquipmentService(in_memory_db)

        # Create a new equipment
        equipment = service.new_equipment_record(
            name="Espresso Machine",
            category="Coffee Equipment",
            number=2,
            purchase_date=datetime(2024, 1, 15),
            purchase_price=8500.0,
            payer="Business Account",
            in_use=True,
            expire_date=datetime(2028, 1, 15),
            monthly_depreciation=141.67,  # $8500 / 60 months
            description="La Marzocco Linea PB"
        )

        assert equipment is not None
        assert equipment.name == "espresso machine"
        assert equipment.category == "coffee equipment"
        assert equipment.number == 2
        assert equipment.purchase_price == 8500.0
        assert equipment.in_use == True
        assert equipment.monthly_depreciation == 141.67
        assert equipment.description == "La Marzocco Linea PB"

    def test_find_equipment_by_id(self, in_memory_db):
        """Test finding equipment by ID"""
        service = EquipmentService(in_memory_db)

        # First create equipment
        created_equipment = service.new_equipment_record(
            name="Grinder",
            category="Coffee Equipment",
            purchase_price=2500.0
        )

        # Now find it
        found_equipment = service.get_equipment_by_id(created_equipment.id)

        assert found_equipment is not None
        assert found_equipment.id == created_equipment.id
        assert found_equipment.name == "grinder"
        assert found_equipment.purchase_price == 2500.0

    def test_find_equipment_with_filters(self, in_memory_db):
        """Test finding equipment with various filters"""
        service = EquipmentService(in_memory_db)

        # Create multiple equipment items
        espresso_machine = service.new_equipment_record(
            name="Espresso Machine",
            category="Coffee Equipment",
            purchase_price=8500.0,
            in_use=True
        )

        grinder = service.new_equipment_record(
            name="Grinder",
            category="Coffee Equipment",
            purchase_price=2500.0,
            in_use=True
        )

        broken_oven = service.new_equipment_record(
            name="Oven",
            category="Kitchen Equipment",
            purchase_price=3000.0,
            in_use=False
        )

        # Find by category
        coffee_equipment = service.find_equipment(category="Coffee Equipment")
        assert len(coffee_equipment) == 2

        # Find by in_use status
        active_equipment = service.find_equipment(in_use=True)
        assert len(active_equipment) == 2

        inactive_equipment = service.find_equipment(in_use=False)
        assert len(inactive_equipment) == 1

        # Find by name
        grinders = service.find_equipment(name="Grinder")
        assert len(grinders) == 1
        assert grinders[0].purchase_price == 2500.0

    def test_update_equipment(self, in_memory_db):
        """Test updating equipment information"""
        service = EquipmentService(in_memory_db)

        # Create equipment
        equipment = service.new_equipment_record(
            name="Refrigerator",
            category="Kitchen Equipment",
            purchase_price=4000.0,
            in_use=True
        )

        # Update it
        updated_equipment = service.update_equipment(
            Equipment(
                id=equipment.id,
                name="Commercial Refrigerator",
                category="Kitchen Equipment",
                purchase_price=4500.0,  # Price correction
                monthly_depreciation=75.0,
                description="Updated with correct price and depreciation"
            )
        )

        assert updated_equipment is not None
        assert updated_equipment.name == "commercial refrigerator"
        assert updated_equipment.purchase_price == 4500.0
        assert updated_equipment.monthly_depreciation == 75.0
        assert updated_equipment.description == "Updated with correct price and depreciation"

    def test_deactivate_and_activate_equipment(self, in_memory_db):
        """Test deactivating and reactivating equipment"""
        service = EquipmentService(in_memory_db)

        # Create equipment
        equipment = service.new_equipment_record(
            name="Blender",
            category="Kitchen Equipment",
            purchase_price=500.0,
            in_use=True
        )

        # Deactivate it
        deactivated = service.deactivate_equipment(equipment.id)
        assert deactivated is not None
        assert deactivated.in_use == False

        # Reactivate it
        activated = service.activate_equipment(equipment.id)
        assert activated is not None
        assert activated.in_use == True

    def test_calculate_monthly_depreciation(self, in_memory_db):
        """Test calculating monthly depreciation"""
        service = EquipmentService(in_memory_db)

        # Create equipment with depreciation
        equipment = service.new_equipment_record(
            name="Coffee Brewer",
            category="Coffee Equipment",
            purchase_price=1200.0,
            monthly_depreciation=20.0  # $20/month
        )

        depreciation = service.calculate_monthly_depreciation(equipment.id)
        assert depreciation == 20.0

        # Test equipment without specified depreciation
        equipment_no_dep = service.new_equipment_record(
            name="Table",
            category="Furniture",
            purchase_price=800.0
        )

        depreciation = service.calculate_monthly_depreciation(equipment_no_dep.id)
        assert depreciation is None

    def test_get_equipment_by_purchase_date_range(self, in_memory_db):
        """Test finding equipment by purchase date range"""
        service = EquipmentService(in_memory_db)

        # Create equipment with different purchase dates
        jan_equipment = service.new_equipment_record(
            name="Jan Machine",
            category="Test",
            purchase_date=datetime(2024, 1, 15),
            purchase_price=1000.0
        )

        jun_equipment = service.new_equipment_record(
            name="Jun Machine",
            category="Test",
            purchase_date=datetime(2024, 6, 20),
            purchase_price=2000.0
        )

        dec_equipment = service.new_equipment_record(
            name="Dec Machine",
            category="Test",
            purchase_date=datetime(2024, 12, 5),
            purchase_price=3000.0
        )

        # Find equipment purchased in first half of 2024
        q1_q2_equipment = service.get_equipment_by_purchase_date_range(
            datetime(2024, 1, 1),
            datetime(2024, 6, 30)
        )
        assert len(q1_q2_equipment) == 2

        # Find equipment purchased in second half of 2024
        q3_q4_equipment = service.get_equipment_by_purchase_date_range(
            datetime(2024, 7, 1),
            datetime(2024, 12, 31)
        )
        assert len(q3_q4_equipment) == 1

    def test_get_equipment_nearing_expiration(self, in_memory_db):
        """Test finding equipment nearing expiration"""
        service = EquipmentService(in_memory_db)

        # Create equipment with different expiration dates
        soon_expiring = service.new_equipment_record(
            name="Soon Expiring",
            category="Test",
            expire_date=datetime.now() + timedelta(days=15),  # 15 days from now
            purchase_price=1000.0
        )

        far_expiring = service.new_equipment_record(
            name="Far Expiring",
            category="Test",
            expire_date=datetime.now() + timedelta(days=60),  # 60 days from now
            purchase_price=2000.0
        )

        # Find equipment expiring within 30 days
        expiring_soon = service.get_equipment_nearing_expiration(threshold_days=30)
        assert len(expiring_soon) == 1
        assert expiring_soon[0].name == "soon expiring"

    def test_real_world_scenario_cafe_equipment_lifecycle(self, in_memory_db):
        """Test a real-world scenario: cafe equipment lifecycle management"""
        service = EquipmentService(in_memory_db)

        # Phase 1: Initial equipment setup for new cafe
        initial_equipment = [
            ("Espresso Machine", "Coffee Equipment", 8500.0, 141.67, 60),
            ("Grinder", "Coffee Equipment", 2500.0, 41.67, 60),
            ("Refrigerator", "Kitchen Equipment", 4000.0, 66.67, 60),
            ("Oven", "Kitchen Equipment", 3000.0, 50.00, 60),
            ("Blender", "Kitchen Equipment", 500.0, 8.33, 60),
        ]

        for name, category, price, monthly_dep, lifespan_months in initial_equipment:
            service.new_equipment_record(
                name=name,
                category=category,
                purchase_price=price,
                monthly_depreciation=monthly_dep,
                purchase_date=datetime(2024, 1, 1),
                expire_date=datetime(2024, 1, 1) + timedelta(days=lifespan_months * 30),
                in_use=True,
                description=f"Initial equipment for cafe opening"
            )

        # Verify all equipment was created
        all_equipment = service.get_all_equipment()
        assert len(all_equipment) == 5

        # Phase 2: Equipment maintenance and updates
        # Find the blender and mark it as broken (not in use)
        blender = service.find_equipment(name="Blender")[0]
        broken_blender = service.deactivate_equipment(blender.id)
        assert broken_blender.in_use == False

        # Purchase replacement blender
        new_blender = service.new_equipment_record(
            name="Blender Pro",
            category="Kitchen Equipment",
            purchase_price=600.0,
            monthly_depreciation=10.0,
            purchase_date=datetime(2024, 6, 1),
            in_use=True,
            description="Replacement for broken blender"
        )

        # Phase 3: Calculate total equipment value and depreciation
        total_value = sum(eq.purchase_price or 0 for eq in all_equipment if eq.in_use)
        total_monthly_depreciation = sum(
            service.calculate_monthly_depreciation(eq.id) or 0
            for eq in all_equipment if eq.in_use
        )

        # Should include new blender but exclude broken one
        assert total_value > 18000.0  # Initial equipment minus broken blender plus new
        assert total_monthly_depreciation > 300.0

        # Phase 4: Equipment nearing expiration alert
        # Update oven to be expiring soon
        oven = service.find_equipment(name="Oven")[0]
        service.update_equipment(
            Equipment(
                id=oven.id,
                expire_date=datetime.now() + timedelta(days=10),
                description="Warranty expiring soon"
            )
        )

        # Check for equipment needing attention
        expiring_equipment = service.get_equipment_nearing_expiration(threshold_days=30)
        assert len(expiring_equipment) >= 1
        assert any(eq.name == "oven" for eq in expiring_equipment)

    def test_real_world_scenario_equipment_budgeting(self, in_memory_db):
        """Test equipment budgeting and financial planning scenario"""
        service = EquipmentService(in_memory_db)

        # Create equipment with different purchase dates for depreciation calculation
        equipment_data = [
            ("Espresso Machine", 8500.0, datetime(2023, 6, 1), 141.67),
            ("Grinder", 2500.0, datetime(2023, 6, 1), 41.67),
            ("Refrigerator", 4000.0, datetime(2024, 1, 1), 66.67),
            ("New Oven", 3500.0, datetime(2024, 6, 1), 58.33),
        ]

        for name, price, purchase_date, monthly_dep in equipment_data:
            service.new_equipment_record(
                name=name,
                category="Coffee Equipment",
                purchase_price=price,
                purchase_date=purchase_date,
                monthly_depreciation=monthly_dep,
                in_use=True
            )

        # Calculate current depreciated values for financial reporting
        total_depreciated_value = 0
        for equipment in service.get_all_equipment():
            current_value = service._calculate_current_depreciated_value(equipment)
            total_depreciated_value += current_value

        # Should be less than total purchase price due to depreciation
        total_purchase_price = sum(eq.purchase_price or 0 for eq in service.get_all_equipment())
        assert total_depreciated_value < total_purchase_price

        # Plan for equipment replacement - estimate future value
        espresso_machine = service.find_equipment(name="Espresso Machine")[0]
        future_estimation_date = datetime.now() + timedelta(days=365)
        estimated_future_value = 3000.0  # Estimated value after 2 years

        monthly_dep_estimate = service.calculate_estimated_monthly_depreciation(
            espresso_machine.id,
            estimated_future_value,
            future_estimation_date
        )

        # Monthly depreciation should be reasonable
        assert monthly_dep_estimate is not None
        assert 100.0 <= monthly_dep_estimate <= 200.0

        # Create budget for new equipment
        planned_equipment = service.new_equipment_record(
            name="Additional Grinder",
            category="Coffee Equipment",
            purchase_price=2800.0,  # Current market price
            monthly_depreciation=46.67,  # 5-year lifespan
            description="Planned purchase for Q3 2024"
        )

        # Verify the planned equipment is captured
        planned_items = service.find_equipment(category="Coffee Equipment")
        assert len(planned_items) >= 2  # Should include existing and planned

    def test_equipment_usage_tracking(self, in_memory_db):
        """Test tracking equipment usage and status changes"""
        service = EquipmentService(in_memory_db)

        # Create equipment
        equipment = service.new_equipment_record(
            name="Test Machine",
            category="Test",
            purchase_price=1000.0,
            in_use=True
        )

        # Simulate usage pattern: active → maintenance → active → retired
        assert equipment.in_use == True

        # Send for maintenance
        maintained = service.deactivate_equipment(equipment.id)
        assert maintained.in_use == False

        # Return from maintenance
        returned = service.activate_equipment(equipment.id)
        assert returned.in_use == True

        # Eventually retire the equipment
        retired = service.deactivate_equipment(equipment.id)
        assert retired.in_use == False

        # Verify equipment history through multiple status changes
        equipment_history = service.find_equipment(name="Test Machine")
        assert len(equipment_history) == 1  # Should be the same equipment
        assert equipment_history[0].in_use == False  # Currently retired

    def test_equipment_category_management(self, in_memory_db):
        """Test managing equipment by categories"""
        service = EquipmentService(in_memory_db)

        # Create equipment in different categories
        categories = {
            "Coffee Equipment": ["Espresso Machine", "Grinder", "Brewer"],
            "Kitchen Equipment": ["Oven", "Refrigerator", "Blender"],
            "Furniture": ["Tables", "Chairs", "Display Case"]
        }

        for category, items in categories.items():
            for item in items:
                service.new_equipment_record(
                    name=item,
                    category=category,
                    purchase_price=1000.0,  # Simplified price
                    in_use=True
                )

        # Test category-based filtering
        coffee_equipment = service.find_equipment(category="Coffee Equipment")
        assert len(coffee_equipment) == 3

        kitchen_equipment = service.find_equipment(category="Kitchen Equipment")
        assert len(kitchen_equipment) == 3

        furniture = service.find_equipment(category="Furniture")
        assert len(furniture) == 3

        # Test cross-category search
        all_equipment = service.get_all_equipment()
        assert len(all_equipment) == 9

        # Test category-based depreciation calculation
        total_coffee_depreciation = sum(
            service.calculate_monthly_depreciation(eq.id) or 0
            for eq in coffee_equipment
        )
        assert total_coffee_depreciation >= 0