import pytest
from datetime import datetime
from models.dbhandler import DbHandler
from models.cafe_managment_models import SupplyRecord
from utils import crud_cycle_test


class TestSupplyRecord:
    """Test suite for SupplyRecord CRUD operations"""

    @pytest.fixture(autouse=True)
    def setup(self, in_memory_db: DbHandler):
        self.db = in_memory_db

        # Create prerequisite entities
        self.supplier = self.db.add_supplier(
            name="Test Supplier",
            contact_channel="email",
            contact_address="supplier@test.com"
        )
        assert self.supplier is not None

        self.order = self.db.add_order(
            supplier_id=self.supplier.id,
            date=datetime.now(),
            buyer="test_buyer",
            payer="test_payer"
        )
        assert self.order is not None

        self.ship = self.db.add_ship(
            order_id=self.order.id,
            shipper="test_shipper",
            price=50.0,
            receiver="test_receiver",
            payer="test_payer"
        )
        assert self.ship is not None

        self.inventory = self.db.add_inventory(
            name="Test Inventory Item",
            unit="kg",
            current_stock=100.0,
            category="test_category",
            price_per_unit=10.0
        )
        assert self.inventory is not None

    def test_crud_cycle_supplyrecord(self, in_memory_db: DbHandler):
        """Test complete CRUD cycle for SupplyRecord"""

        create_kwargs = {
            "inventory_item_id": self.inventory.id,
            "ship_id": self.ship.id,
            "price": 100.0,
            "box_amount": 10.0,
            "box_price": 90.0,
            "box_discount": 5.0,
            "num_of_box": 2.0,
            "description": "Test supply record"
        }

        update_kwargs = {
            "price": 120.0,
            "box_discount": 10.0,
            "description": "Updated test supply record"
        }

        # Use the generic CRUD test utility
        crud_cycle_test(
            db_handler=in_memory_db,
            model_class=SupplyRecord,
            create_kwargs=create_kwargs,
            update_kwargs=update_kwargs,
            lookup_fields=["inventory_item_id", "ship_id"],
            lookup_values=[self.inventory.id, self.ship.id]
        )

    def test_add_supplyrecord_with_negative_values(self, in_memory_db: DbHandler):
        """Test that negative values are rejected"""

        # Test negative price
        result = self.db.add_supplyrecord(
            inventory_item_id=self.inventory.id,
            ship_id=self.ship.id,
            price=-10.0
        )
        assert result is None

        # Test negative box_amount
        result = self.db.add_supplyrecord(
            inventory_item_id=self.inventory.id,
            ship_id=self.ship.id,
            box_amount=-5.0
        )
        assert result is None

        # Test negative box_price
        result = self.db.add_supplyrecord(
            inventory_item_id=self.inventory.id,
            ship_id=self.ship.id,
            box_price=-20.0
        )
        assert result is None

        # Test negative box_discount
        result = self.db.add_supplyrecord(
            inventory_item_id=self.inventory.id,
            ship_id=self.ship.id,
            box_discount=-3.0
        )
        assert result is None

        # Test negative num_of_box
        result = self.db.add_supplyrecord(
            inventory_item_id=self.inventory.id,
            ship_id=self.ship.id,
            num_of_box=-1.0
        )
        assert result is None

    def test_add_supplyrecord_without_required_fields(self, in_memory_db: DbHandler):
        """Test that missing required fields are rejected"""

        # Test without inventory_item_id
        result = self.db.add_supplyrecord(
            inventory_item_id= None,
            ship_id=self.ship.id,
            price=100.0
        )
        assert result is None

        # Test without ship_id
        result = self.db.add_supplyrecord(
            inventory_item_id=self.inventory.id,
            ship_id=None,
            price=100.0
        )
        assert result is None

    def test_add_supplyrecord_with_nonexistent_references(self, in_memory_db: DbHandler):
        """Test that references to non-existent entities are rejected"""

        # Test with non-existent inventory item
        result = self.db.add_supplyrecord(
            inventory_item_id=9999,  # Non-existent ID
            ship_id=self.ship.id,
            price=100.0
        )
        assert result is None

        # Test with non-existent ship
        result = self.db.add_supplyrecord(
            inventory_item_id=self.inventory.id,
            ship_id=9999,  # Non-existent ID
            price=100.0
        )
        assert result is None

    def test_get_supplyrecord_with_filters(self, in_memory_db: DbHandler):
        """Test filtering supply records"""

        # Create test supply record
        supply_record = self.db.add_supplyrecord(
            inventory_item_id=self.inventory.id,
            ship_id=self.ship.id,
            price=100.0,
            description="Test record for filtering"
        )
        assert supply_record is not None

        # Test filter by inventory_item_id
        results = self.db.get_supplyrecord(inventory_item_id=self.inventory.id)
        assert len(results) == 1
        assert results[0].inventory_item_id == self.inventory.id

        # Test filter by ship_id
        results = self.db.get_supplyrecord(ship_id=self.ship.id)
        assert len(results) == 1
        assert results[0].ship_id == self.ship.id

        # Test filter by both inventory_item_id and ship_id
        results = self.db.get_supplyrecord(
            inventory_item_id=self.inventory.id,
            ship_id=self.ship.id
        )
        assert len(results) == 1

        # Test filter with non-existent values
        results = self.db.get_supplyrecord(inventory_item_id=9999)
        assert len(results) == 0

        results = self.db.get_supplyrecord(ship_id=9999)
        assert len(results) == 0

    def test_get_supplyrecord_with_row_limit(self, in_memory_db: DbHandler):
        """Test row limit functionality"""

        # Create multiple supply records
        for i in range(3):
            supply_record = self.db.add_supplyrecord(
                inventory_item_id=self.inventory.id,
                ship_id=self.ship.id,
                price=100.0 + i,
                description=f"Test record {i}"
            )
            assert supply_record is not None

        # Test without limit
        results = self.db.get_supplyrecord()
        assert len(results) == 3

        # Test with limit
        results = self.db.get_supplyrecord(row_num=2)
        assert len(results) == 2

    def test_edit_supplyrecord(self, in_memory_db: DbHandler):
        """Test editing supply record"""

        # Create supply record
        supply_record = self.db.add_supplyrecord(
            inventory_item_id=self.inventory.id,
            ship_id=self.ship.id,
            price=100.0,
            box_amount=10.0,
            description="Original description"
        )
        assert supply_record is not None

        # Modify and update
        supply_record.price = 150.0
        supply_record.box_amount = 15.0
        supply_record.description = "Updated description"

        updated = self.db.edit_supplyrecord(supply_record)
        assert updated is not None
        assert updated.price == 150.0
        assert updated.box_amount == 15.0
        assert updated.description == "Updated description"

    def test_delete_supplyrecord(self, in_memory_db: DbHandler):
        """Test deleting supply record"""

        # Create supply record
        supply_record = self.db.add_supplyrecord(
            inventory_item_id=self.inventory.id,
            ship_id=self.ship.id,
            price=100.0
        )
        assert supply_record is not None

        # Verify it exists
        results = self.db.get_supplyrecord(
            inventory_item_id=self.inventory.id,
            ship_id=self.ship.id
        )
        assert len(results) == 1

        # Delete it
        deleted = self.db.delete_supplyrecord(supply_record)
        assert deleted is True

        # Verify it's gone
        results = self.db.get_supplyrecord(
            inventory_item_id=self.inventory.id,
            ship_id=self.ship.id
        )
        assert len(results) == 0

    def test_delete_nonexistent_supplyrecord(self, in_memory_db: DbHandler):
        """Test deleting non-existent supply record"""

        # Create a supply record object with non-existent IDs
        fake_supply_record = SupplyRecord()
        fake_supply_record.inventory_item_id = 9999
        fake_supply_record.ship_id = 9999

        # Try to delete it
        deleted = self.db.delete_supplyrecord(fake_supply_record)
        assert deleted is False