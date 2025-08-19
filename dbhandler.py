from typing import Optional, List, Tuple, Union

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
                 category:Optional[str]=None,
                 current_price:Optional[float]=None,
                 value_added_tax:Optional[float]=None,
                 serving:bool=True,
                 description:Optional[str]=None,
                 ) -> Optional[Menu]:
        """ adding new menu item name + size must be unique"""
        if current_price is not None and current_price < 0:
            logging.error("Price cannot be negative")
            return None
        if value_added_tax is not None and not (0 <= value_added_tax <= 1):
            logging.error("VAT must be between 0-1")
            return None
        with self.Session() as session:
            try:

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


    #--inventory record--
    def add_inventoryrecord(self,
                 inventory_id:int,
                 sold_amount:Optional[float]=None,
                 other_used_amount:Optional[float]=None,
                 supplied_amount:Optional[float]=None,
                 auto_calculated_amount:Optional[float]=None,
                 manual_report:Optional[float]=None,
                 date:datetime=None,
                 description:Optional[str]=None,
                 ) -> Optional[InventoryRecord]:
        """ adding new inventory record item """
        if sold_amount is not None and sold_amount < 0:
            logging.error("sold_amount: value cant be negative")
            return None
        if other_used_amount is not None and other_used_amount < 0:
            logging.error("other_used_amount: value cant be negative")
            return None
        if supplied_amount is not None and supplied_amount < 0:
            logging.error("supplied_amount: value cant be negative")
            return None
        if auto_calculated_amount is not None and auto_calculated_amount < 0:
            logging.error("auto_calculated_amount: value cant be negative")
            return None
        if manual_report is not None and manual_report < 0:
            logging.error("manual_report: value cant be negative")
            return None

        with self.Session() as session:
            try:
                if not session.get(Inventory, inventory_id):
                    logging.error(f"Inventory ID {inventory_id} not found")
                    session.rollback()
                    return None

                date = date if date is not None else datetime.now()

                new_record = InventoryRecord(
                    inventory_id=inventory_id,
                    sold_amount=sold_amount,
                    other_used_amount=other_used_amount,
                    supplied_amount=supplied_amount,
                    auto_calculated_amount=auto_calculated_amount,
                    manual_report=manual_report,
                    date=date,
                    description=description,
                )
                session.add(new_record)
                session.commit()
                session.refresh(new_record)
                logging.info("inventory record added successfully")
                return new_record
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to add inventory record item to the database: {e}")
                return None

    def get_inventoryrecord(
            self,
            inventory_id: int,
            last: bool = True,
            from_date: Optional[datetime] = None,
            to_date: Optional[datetime] = None
    ) -> Union[Optional[InventoryRecord], List[InventoryRecord]]:
        """Get inventory record(s) for an inventory item

        Args:
            inventory_id: Inventory item ID to filter by
            last: If True, returns only the most recent record
                  If False, returns all records (optionally filtered by date range)
            from_date: Optional start date for filtering records
            to_date: Optional end date for filtering records

        Returns:
            - If last=True: Single InventoryRecord or None
            - If last=False: List of InventoryRecords (may be empty)
        """

        with (self.Session() as session):
            try:
                query = session.query(InventoryRecord).filter_by(
                    inventory_id=inventory_id
                )

                if from_date:
                    query = query.filter(InventoryRecord.date >= from_date)
                if to_date:
                    query = query.filter(InventoryRecord.date <= to_date)

                query = query.order_by(InventoryRecord.date.desc())

                if last:
                    # Get single most recent record
                    record: Optional[InventoryRecord] = query.first()
                    if record:
                        logging.info(f"Found last record from {record.date}")
                        return record
                    logging.warning(f"No records found for inventory ID {inventory_id}")
                    return None
                else:
                    # Get all matching records
                    records = query.all()
                    logging.info(f"Found {len(records)} records for inventory ID {inventory_id}")
                    return records
            except Exception as e:
                session.rollback()
                logging.error(f"Error fetching records for inventory {inventory_id}: {str(e)}")
                return None if last else []

    def edit_inventoryrecord(self, inventory_record:InventoryRecord) -> Optional[InventoryRecord]:
        """
        Updates an existing inventory record in the database.

        Args:
            inventory_record: The InventoryRecord object with updated values.
                             Must have a valid ID for existing records.

        Returns:
            The updated InventoryRecord if successful, None on error.
        """

        if not inventory_record.id:
            logging.error("Cannot edit inventory record without a valid ID.")
            return None
        with self.Session() as session:
            try:
                existing = session.get(InventoryRecord, inventory_record.id)
                if not existing:
                    logging.error(f"No inventory record found with ID: {inventory_record.id}")
                    return None
                merged_record  = session.merge(inventory_record)
                session.commit()
                session.refresh(merged_record )
                logging.info(f"Successfully updated inventory record with id: {inventory_record.id}")
                return merged_record
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to update inventory record with id: {inventory_record.id}: {e}")
                return None

    def delete_inventoryrecord(self, id: int) -> bool:
        """
        Deletes an inventory record by ID.
        Returns True if deleted, False otherwise.
        """
        with self.Session() as session:
            try:
                record = session.get(InventoryRecord, id)
                if not record:
                    logging.warning(f"No inventory record found with id: {id}")
                    return False
                session.delete(record)
                session.commit()
                logging.info(f"Deleted inventory record with id: {id}")
                return True
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete inventory record {id}: {e}")
                return False




    #--EstimatedMenuPriceRecord--
    def add_estimatedmenupricerecord(self,
                 menu_id:int,
                 sales_forecast:Optional[int]=None,
                 estimated_indirect_costs:Optional[float]=None,
                 direct_cost:Optional[float]=None,
                 profit:Optional[float]=None,
                 estimated_price:Optional[float]=None,
                 manual_price:Optional[float]=None,
                 from_date:Optional[datetime]=None,
                 estimated_to_date:Optional[datetime]=None,

                 description:Optional[str]=None,
                 ) -> Optional[EstimatedMenuPriceRecord]:
        """ adding new estimate of price item """

        if sales_forecast is not None and sales_forecast < 0:
            logging.error("sales_forecast: value cant be negative")
            return None
        if estimated_indirect_costs is not None and estimated_indirect_costs < 0:
            logging.error("estimated_indirect_costs: value cant be negative")
            return None
        if direct_cost is not None and direct_cost < 0:
            logging.error("direct_cost: value cant be negative")
            return None
        if profit is not None and profit < 0:
            logging.warning("profit: value should not be negative")
            return None
        if estimated_price is not None and estimated_price < 0:
            logging.error("estimated_price: value cant be negative")
            return None
        if manual_price is not None and manual_price < 0:
            logging.error("manual_price: value cant be negative")
            return None

        if estimated_to_date and from_date and estimated_to_date < from_date:
            logging.error("estimated_to_date must be after from_date")
            return None
        from_date = from_date if from_date is not None else datetime.now()
        with self.Session() as session:
            try:
                if not session.get(Menu, menu_id):
                    logging.error(f"Menu ID {menu_id} not found")
                    session.rollback()
                    return None

                new_record = EstimatedMenuPriceRecord(
                    menu_id=menu_id,
                    sales_forecast=sales_forecast,
                    estimated_indirect_costs=estimated_indirect_costs,
                    direct_cost=direct_cost,
                    profit=profit,
                    estimated_price=estimated_price,
                    manual_price=manual_price,
                    from_date=from_date,
                    estimated_to_date=estimated_to_date,
                    description=description,
                )
                session.add(new_record)
                session.commit()
                session.refresh(new_record)
                logging.info("price estimation record added successfully")
                return new_record
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to add price estimation record item to the database: {e}")
                return None

    def get_estimatedmenupricerecord(
            self,
            menu_id: int,
            last: bool = True,
            from_date: Optional[datetime] = None,
            to_date: Optional[datetime] = None
    ) -> Union[Optional[EstimatedMenuPriceRecord], List[EstimatedMenuPriceRecord]]:
        """Get price estimation record(s) for an inventory item

        Args:
            menu_id: menu item ID to filter by
            last: If True, returns only the most recent record
                  If False, returns all records (optionally filtered by date range)
            from_date: Optional start date for filtering records
            to_date: Optional end date for filtering records

        Returns:
            - If last=True: Single EstimatedMenuPriceRecord or None
            - If last=False: List of EstimatedMenuPriceRecord (may be empty)
        """

        with (self.Session() as session):
            try:
                query = session.query(EstimatedMenuPriceRecord).filter_by(
                    menu_id=menu_id
                )

                if from_date:
                    query = query.filter(EstimatedMenuPriceRecord.from_date >= from_date)
                if to_date:
                    query = query.filter(EstimatedMenuPriceRecord.from_date <= to_date)

                query = query.order_by(EstimatedMenuPriceRecord.from_date.desc())

                if last:
                    # Get single most recent record
                    record: Optional[EstimatedMenuPriceRecord] = query.first()
                    if record:
                        logging.info(f"Found last record from {record.from_date}")
                        return record
                    logging.warning(f"No records found for menu ID {menu_id}")
                    return None
                else:
                    # Get all matching records
                    records = query.all()
                    logging.info(f"Found {len(records)} records for menu ID {menu_id}")
                    return records
            except Exception as e:
                session.rollback()
                logging.error(f"Error fetching records for menu {menu_id}: {str(e)}")
                return None if last else []

    def edit_estimatedmenupricerecord(self, price_estimation_record:EstimatedMenuPriceRecord) -> Optional[EstimatedMenuPriceRecord]:
        """
        Updates an existing price estimation record in the database.

        Args:
            price_estimation_record: The EstimatedMenuPriceRecord object with updated values.
                             Must have a valid ID for existing records.

        Returns:
            The updated EstimatedMenuPriceRecord if successful, None on error.
        """

        if not price_estimation_record.id:
            logging.error("Cannot edit inventory record without a valid ID.")
            return None
        with self.Session() as session:
            try:
                existing = session.get(EstimatedMenuPriceRecord, price_estimation_record.id)
                if not existing:
                    logging.error(f"No price estimation record found with ID: {price_estimation_record.id}")
                    return None
                merged_record  = session.merge(price_estimation_record)
                session.commit()
                session.refresh(merged_record )
                logging.info(f"Successfully updated price estimation record with id: {price_estimation_record.id}")
                return merged_record
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to update price estimation record with id: {price_estimation_record.id}: {e}")
                return None

    def delete_estimatedmenupricerecord(self, id: int) -> bool:
        """
        Deletes a price estimation record by ID.
        Returns True if deleted, False otherwise.
        """
        with self.Session() as session:
            try:
                record = session.get(EstimatedMenuPriceRecord, id)
                if not record:
                    logging.warning(f"No price estimation record found with id: {id}")
                    return False
                session.delete(record)
                session.commit()
                logging.info(f"Deleted price estimation record with id: {id}")
                return True
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete price estimation record {id}: {e}")
                return False




db = DbHandler()

