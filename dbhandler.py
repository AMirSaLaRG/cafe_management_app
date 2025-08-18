from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging
from cafe_managment_models import *

logging.basicConfig(filename='app.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class DbHandler:
    """
    add - get - edit - delete _tablename
    """

    def __init__(self, db_url="sqlite:///cafe.db", engine=None, session_factory=None):
        if engine:
            self.engine = engine
        else:
            self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)

        if session_factory:
            self.Session = session_factory
        else:
            self.Session = sessionmaker(bind=self.engine)


    #--inventory--
    def add_inventory(self, name:str,
                      unit:Optional[str]=None,
                      current_stock:Optional[float]=None,
                      price_per_unit:Optional[float]=None,
                      initial_value:Optional[float]=None,
                      date_of_initial_value:Optional[datetime]=None):
        with self.Session() as session:
            try:
                # The timestamp column in your model is "date_of_initial_value".
                # SQLAlchemy handles the conversion from a Python datetime object to TIMESTAMP.
                new_item = Inventory(
                    name=name.strip().lower(),
                    unit=unit,
                    current_stock=current_stock,
                    price_per_unit=price_per_unit,
                    initial_value=initial_value,
                    date_of_initial_value=date_of_initial_value
                )
                session.add(new_item)
                session.commit()
                session.refresh(new_item)
                logging.info("Inventory added successfully")
                return new_item
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to add inventory item to the database: {e}")
                return None

    def get_inventory(self, name:str) -> Optional[Inventory]:
        """find an inventory by name"""

        with self.Session() as session:
            try:
                the_item = session.query(Inventory).filter_by(name=name.strip().lower()).first()
                if the_item:
                    logging.info(f"Found inventory item with name: {name}")
                    return the_item
                logging.warning(f"No inventory item found with name: {name}")
                return None
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to find inventory item with the name: {name}")
                return None


    def edit_inventory(self, inventory:Inventory) -> Optional[Inventory]:
        """
        Updates an existing inventory item in the database.

        This function uses session.merge() to update an object based on its primary key.
        If the object doesn't have an ID, it will be inserted.

        Args:
            inventory: The Inventory object with the updated values. It must have
                       a valid primary key (id) to update an existing record.

        Returns:
            The updated Inventory object after it has been committed, or None
            if an error occurred.
        """

        if not inventory.id:
            logging.error("Cannot edit inventory item without a valid ID.")
            return None
        with self.Session() as session:
            existing = session.get(Inventory, inventory.id)
            if not existing:
                logging.error(f"No inventory item found with ID: {inventory.id}")
                return None
            try:
                merged_inventory = session.merge(inventory)
                session.commit()
                session.refresh(merged_inventory)
                logging.info(f"Successfully updated inventory item with id: {inventory.id}")
                return merged_inventory
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to update inventory item with id: {inventory.id}: {e}")
                return None

    def delete_inventory(self, inventory_id: int) -> bool:
        """
        Deletes an inventory item by ID.
        Returns True if deleted, False otherwise.
        """
        with self.Session() as session:
            try:
                item = session.get(Inventory, inventory_id)
                if not item:
                    logging.warning(f"No inventory item found with id: {inventory_id}")
                    return False
                session.delete(item)
                session.commit()
                logging.info(f"Deleted inventory item with id: {inventory_id}")
                return True
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete inventory item {inventory_id}: {e}")
                return False


    #--menu--
    def add_menu(self,
                 name:str,
                 size:Optional[str],
                 category:str="M",
                 current_price:Optional[float]=None,
                 value_added_tax:Optional[float]=None,
                 serving:bool=True,
                 description:Optional[str]=None,
                 ) -> Optional[Menu]:
        """ adding new menu item name + size must be unique"""
        with self.Session() as session:
            try:
                if current_price is not None and current_price < 0:
                    raise ValueError("Price cannot be negative")
                if value_added_tax is not None and not (0 <= value_added_tax <= 1):
                    raise ValueError("VAT must be between 0-1")
                # The timestamp column in your model is "date_of_initial_value".
                # SQLAlchemy handles the conversion from a Python datetime object to TIMESTAMP.
                existing = session.query(Menu).filter_by(
                    name=name.strip().lower(),
                    size=size.strip().lower()
                ).first()
                if existing:
                    logging.warning(f"Menu item already exists: {name} ({size})")
                    return None


                new_item = Menu(
                    name=name.strip().lower(),
                    size=size.strip().lower(),
                    category=category,
                    current_price=current_price,
                    value_added_tax=value_added_tax,
                    serving=serving,
                    description=description
                )
                session.add(new_item)
                session.commit()
                session.refresh(new_item)
                logging.info(f"Successfully added menu item with name: {name} size:{size}")
                return new_item
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to add menu item to the database: {e}")
                return None

    def get_menu(self, name:str, size:str="M") -> Optional[Menu]:
        """find a menu by name and size
        Args:
        name: Menu item name (case-insensitive)
        size: If provided, searches for exact name+size match.
              If None, returns first item matching name.

        Returns:
            Menu object if found, None otherwise
        """

        with (self.Session() as session):
            try:

                the_item: Optional[Menu] = session.query(Menu).filter_by(
                    name=name.strip().lower(),
                    size=size.strip().lower()
                ).first()


                if the_item:
                    logging.info(f"Found menu item with name: {name} size: {size}")
                    return the_item

                check = session.query(Menu).filter_by(name=name.strip().lower()).all()
                if check:
                    sizes = [item.size for item in check]
                    logging.warning(f"Found menu item with name: {name} sizes: {sizes}, there is not any {size}")
                    return None
                logging.warning(f"No inventory item found with name: {name} size: {size}")
                return None
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to find inventory item with the name: {name}")
                return None

    def edit_menu(self, menu:Menu) -> Optional[Menu]:
        """
        Updates an existing menu item in the database.

        This function uses session.merge() to update an object based on its primary key.
        If the object doesn't have an ID, it will be inserted.

        Args:
            menu: The menu object with the updated values. It must have
                       a valid primary key (id) to update an existing record.

        Returns:
            The updated menu object after it has been committed, or None
            if an error occurred.
        """

        if not menu.id:
            logging.error("Cannot edit menu item without a valid ID.")
            return None
        with self.Session() as session:
            try:
                existing = session.get(Menu, menu.id)
                if not existing:
                    logging.error(f"No menu item found with ID: {menu.id}")
                    return None
                merged_menu = session.merge(menu)
                session.commit()
                session.refresh(merged_menu)
                logging.info(f"Successfully updated inventory item with id: {menu.id}")
                return merged_menu
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to update inventory item with id: {menu.id}: {e}")
                return None

    def delete_menu(self, menu_id: int) -> bool:
        """
        Deletes an menu item by ID.
        Returns True if deleted, False otherwise.
        """
        with self.Session() as session:
            try:
                item = session.get(Menu, menu_id)
                if not item:
                    logging.warning(f"No inventory item found with id: {menu_id}")
                    return False
                session.delete(item)
                session.commit()
                logging.info(f"Deleted menu item with id: {menu_id}")
                return True
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete menu item {menu_id}: {e}")
                return False


db = DbHandler()

