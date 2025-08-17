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

db = DbHandler()

