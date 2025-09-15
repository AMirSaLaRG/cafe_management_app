from datetime import datetime
from typing import Optional, List, Union

from models.cafe_managment_models import Usage, InventoryUsage, MenuUsage
from models.dbhandler import DBHandler


class OtherUsageService:
    def __init__(self, db_handler: DBHandler):
        self.db = db_handler

    def new_usage_record(self, used_by: str, category: str, date: datetime, description: str = None) -> Optional[Usage]:
        """Create a new usage record"""
        return self.db.add_usage(
            used_by=used_by,
            date=date,
            category=category,
            description=description,
        )

    def get_usage_by_id(self, id: int) -> Optional[Usage]:
        """Get usage record by ID"""
        results = self.db.get_usage(id=id)
        return results[0] if results else None

    def get_usage_records(self,
                          used_by: Optional[str] = None,
                          category: Optional[str] = None,
                          from_date: Optional[datetime] = None,
                          to_date: Optional[datetime] = None,
                          row_num: Optional[int] = None) -> List[Usage]:
        """Get usage records with optional filters"""
        return self.db.get_usage(
            used_by=used_by,
            category=category,
            from_date=from_date,
            to_date=to_date,
            row_num=row_num
        )

    def update_usage_record(self, usage: Usage, **kwargs) -> Optional[Usage]:
        """Update an existing usage record"""
        # Update the usage object with provided kwargs
        for key, value in kwargs.items():
            if hasattr(usage, key):
                setattr(usage, key, value)

        return self.db.edit_usage(usage)

    def delete_usage_record(self, usage: Usage) -> bool:
        """Delete a usage record"""
        return self.db.delete_usage(usage)

    def add_inventory_usage(self,
                            inventory_item_id: int,
                            usage_id: int,
                            amount: float) -> Optional[InventoryUsage]:
        """Add inventory usage to a usage record"""
        return self.db.add_inventoryusage(
            inventory_item_id=inventory_item_id,
            usage_id=usage_id,
            amount=amount
        )

    def get_inventory_usage(self,
                            inventory_item_id: Optional[int] = None,
                            usage_id: Optional[int] = None) -> List[InventoryUsage]:
        """Get inventory usage records"""
        return self.db.get_inventoryusage(
            inventory_item_id=inventory_item_id,
            usage_id=usage_id
        )

    def update_inventory_usage(self, inventory_usage: InventoryUsage, amount: float) -> Optional[InventoryUsage]:
        """Update inventory usage amount"""
        inventory_usage.amount = amount
        return self.db.edit_inventoryusage(inventory_usage)

    def delete_inventory_usage(self, inventory_usage: InventoryUsage) -> bool:
        """Delete inventory usage record"""
        return self.db.delete_inventoryusage(inventory_usage)

    def add_menu_usage(self,
                       menu_id: int,
                       usage_id: int,
                       amount: float) -> Optional[MenuUsage]:
        """Add menu usage to a usage record"""
        return self.db.add_menuusage(
            menu_id=menu_id,
            usage_id=usage_id,
            amount=amount
        )

    def get_menu_usage(self,
                       menu_id: Optional[int] = None,
                       usage_id: Optional[int] = None) -> List[MenuUsage]:
        """Get menu usage records"""
        return self.db.get_menuusage(
            menu_id=menu_id,
            usage_id=usage_id
        )

    def update_menu_usage(self, menu_usage: MenuUsage, amount: float) -> Optional[MenuUsage]:
        """Update menu usage amount"""
        menu_usage.amount = amount
        return self.db.edit_menuusage(menu_usage)

    def delete_menu_usage(self, menu_usage: MenuUsage) -> bool:
        """Delete menu usage record"""
        return self.db.delete_menuusage(menu_usage)


