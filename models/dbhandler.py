from typing import Optional, List, cast

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import time
import logging
from models.cafe_managment_models import *

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
                      category:Optional[str] = None,
                      unit:Optional[str]=None,
                      current_stock:Optional[float]=None,
                      price_per_unit:Optional[float]=None,
                      ):

        if name:
            name = name.lower().strip()
        if category:
            category = category.lower().strip()
        if unit:
            unit = unit.lower().strip()
        with self.Session() as session:
            try:
                # The timestamp column in your model is "date_of_initial_value".
                # SQLAlchemy handles the conversion from a Python datetime object to TIMESTAMP.
                new_item = Inventory(
                    name=name,
                    unit=unit,
                    category=category,
                    current_stock=current_stock,
                    price_per_unit=price_per_unit,

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

    def get_inventory(self,
                      id: Optional[int]=None,
                      name:Optional[str]=None,
                      row_num:Optional[int]=None) -> list[Inventory]:
        """Find inventory item(s) with optional filters

        Args:
            id: id of item to find
            name: Inventory item name (case-insensitive)
            row_num: Maximum number of records to return

        Returns:
            List of Inventory objects (empty list if no matches found)
        """

        with self.Session() as session:
            try:
                query = session.query(Inventory).order_by(Inventory.time_create.desc())
                if id:
                    query = query.filter_by(id=id)
                if name:
                    lookup_name = name.strip().lower()
                    query = query.filter_by(name=lookup_name)
                if row_num:
                    query = query.limit(row_num)

                result = query.all()
                logging.info(f"Found {len(result)} inventory items")
                return cast(List[Inventory], result)
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to find inventory item(s): {e}")
                return []


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
        fields_to_process = ['name', "category", "unit"]
        for field in fields_to_process:
            value = getattr(inventory, field, None)
            if isinstance(value, str):
                setattr(inventory, field, value.strip().lower())

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

    def delete_inventory(self, inventory: Inventory) -> bool:
        """
        Deletes an inventory item by ID.
        Returns True if deleted, False otherwise.
        """
        with self.Session() as session:
            try:
                item = session.get(Inventory, inventory.id)
                if not item:
                    logging.warning(f"No inventory item found with id: {inventory.id}")
                    return False
                session.delete(item)
                session.commit()
                logging.info(f"Deleted inventory item with id: {inventory.id}")
                return True
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete inventory item {inventory.id}: {e}")
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
        if not name:
            logging.error("Menu item name is required")
            return None

        if current_price is not None and current_price < 0:
            logging.error("Price cannot be negative")
            return None
        if value_added_tax is not None and not (0 <= value_added_tax <= 1):
            logging.error("VAT must be between 0-1")
            return None
        if name:
            name = name.strip().lower()
        if size:
            size = size.strip().lower()
        if category:
            category = category.strip().lower()

        with self.Session() as session:
            try:

                # The timestamp column in your model is "date_of_initial_value".
                # SQLAlchemy handles the conversion from a Python datetime object to TIMESTAMP.
                existing = session.query(Menu).filter_by(
                    name=name,
                    size=size
                ).first()
                if existing:
                    logging.warning(f"Menu item already exists: {name} ({size})")
                    return None


                new_item = Menu(
                    name=name,
                    size=size,
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

    def get_menu(self,
                 id:Optional[int]=None,
                 name:Optional[str]=None,
                 size:Optional[str]=None,
                 row_num:Optional[int]=None) -> list[Menu]:
        """Get menu items with optional filters

        Args:
            id: get the item by its id
            name: Menu item name (case-insensitive)
            size: If provided, searches for exact name+size match
            row_num: Maximum number of records to return

        Returns:
            List of Menu objects (empty list if no matches found or error occurs)
        """

        with (self.Session() as session):
            try:
                query = session.query(Menu).order_by(Menu.time_create.desc())
                if id:
                    query = query.filter_by(id=id)
                if name:
                    lookup_name = name.strip().lower()
                    query = query.filter_by(name=lookup_name)

                if size:
                    lookup_size = size.strip().lower()
                    query = query.filter_by(size=lookup_size)

                if row_num:
                    query = query.limit(row_num)

                result = query.all()
                logging.info(f"Found {len(result)} menu items")
                return cast(list[Menu], result)

            except Exception as e:
                session.rollback()
                logging.error(f"Failed to find menu item")
                return []

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

        fields_to_process = ['name', "size", "category"]
        for field in fields_to_process:
            value = getattr(menu, field, None)
            if isinstance(value, str):
                setattr(menu, field, value.strip().lower())

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

    def delete_menu(self, menu: Menu) -> bool:
        """
        Deletes an object Menu.
        Returns True if deleted, False otherwise.
        """
        with self.Session() as session:
            try:
                item = session.get(Menu, menu.id)
                if not item:
                    logging.warning(f"No inventory item found with id: {menu.id}")
                    return False
                session.delete(item)
                session.commit()
                logging.info(f"Deleted menu item with id: {menu.id}")
                return True
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete menu item {menu.id}: {e}")
                return False


    #--InventoryStockRecord--
    def add_inventorystockrecord(self,
                 inventory_id:int,
                 change_amount:float,
                 category:str = None,
                 auto_calculated_amount:Optional[float]=None,
                 manual_report:Optional[float]=None,
                 date:datetime=None,
                 description:Optional[str]=None,
                 ) -> Optional[InventoryStockRecord]:
        """ adding new inventory record item """

        if manual_report is not None and manual_report < 0:
            logging.error("manual_report: value cant be negative")
            return None

        if category is not None:
            category = category.strip().lower()

        with self.Session() as session:
            try:
                if not session.get(Inventory, inventory_id):
                    logging.error(f"Inventory ID {inventory_id} not found")
                    session.rollback()
                    return None

                date = date if date is not None else datetime.now()

                new_record = InventoryStockRecord(
                    inventory_id=inventory_id,
                    category=category,
                    change_amount=change_amount,
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

    def get_inventorystockrecord(
            self,
            id:Optional[int]=None,
            inventory_id: Optional[int]=None,
            category: Optional[str]=None,
            from_date: Optional[datetime] = None,
            to_date: Optional[datetime] = None,
            row_num: Optional[int]=None,
    ) ->List[InventoryStockRecord]:
        """Get inventory record(s) for inventory items

        Args:
            id: inventory record id
            inventory_id: Inventory ID to filter by (None for all inventories)
            from_date: Optional start date for filtering records
            to_date: Optional end date for filtering records
            row_num: Maximum number of records to return

        Returns:
            List of InventoryRecord objects (empty list if no matches found or error occurs)
        """
        if category is not None:
            category = category.strip().lower()
        with (self.Session() as session):
            try:
                query = session.query(InventoryStockRecord).order_by(InventoryStockRecord.date.desc())

                if id:
                    query = query.filter_by(id=id)
                if inventory_id:
                    query = query.filter_by(inventory_id=inventory_id)
                if category:
                    query = query.filter_by(category=category)
                if from_date:
                    query = query.filter(InventoryStockRecord.date >= from_date)
                if to_date:
                    query = query.filter(InventoryStockRecord.date <= to_date)
                if row_num:
                    query = query.limit(row_num)

                result = query.all()
                logging.info(f"Found {len(result)} inventory records")
                return cast(List[InventoryStockRecord], result)

            except Exception as e:
                session.rollback()
                logging.error(f"Error fetching records for inventory: {str(e)}")
                return []

    def edit_inventorystockrecord(self, inventory_record:InventoryStockRecord) -> Optional[InventoryStockRecord]:
        """
        Updates an existing inventory record in the database.

        Args:
            inventory_record: The inventorystockrecord object with updated values.
                             Must have a valid ID for existing records.

        Returns:
            The updated inventorystockrecord if successful, None on error.
        """


        if not inventory_record.id:
            logging.error("Cannot edit inventory record without a valid ID.")
            return None
        with self.Session() as session:
            try:
                existing = session.get(InventoryStockRecord, inventory_record.id)
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

    def delete_inventorystockrecord(self, inventory_record: InventoryStockRecord) -> bool:
        """
        Deletes an inventory record by ID.
        Returns True if deleted, False otherwise.
        """
        with self.Session() as session:
            try:
                record = session.get(InventoryStockRecord, inventory_record.id)
                if not record:
                    logging.warning(f"No inventory record found with id: {inventory_record.id}")
                    return False
                session.delete(record)
                session.commit()
                logging.info(f"Deleted inventory record with id: {inventory_record.id}")
                return True
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete inventory record {inventory_record.id}: {e}")
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
            id: Optional[int]=None,
            menu_id: Optional[int] = None,
            from_date: Optional[datetime] = None,
            to_date: Optional[datetime] = None,
            row_num: Optional[int] = None,
    ) -> list[EstimatedMenuPriceRecord]:
        """Get price estimation records for menu items

        Args:
            id: get estimated menu price record by its id
            menu_id: menu item ID to filter by (None for all menus)
            from_date: Optional start date for filtering records
            to_date: Optional end date for filtering records
            row_num: maximum number of records to return

        Returns:
            List of EstimatedMenuPriceRecord objects (empty list if no matches found)
        """

        with (self.Session() as session):
            try:

                query = session.query(EstimatedMenuPriceRecord).order_by(EstimatedMenuPriceRecord.from_date.desc())
                if id:
                    query = query.filter_by(id=id)
                if menu_id:
                    query = query.filter_by(menu_id=menu_id)
                if from_date:
                    query = query.filter(EstimatedMenuPriceRecord.from_date >= from_date)
                if to_date:
                    query = query.filter(EstimatedMenuPriceRecord.from_date <= to_date)
                if row_num:
                    query = query.limit(row_num)

                result = query.all()
                logging.info(f"Found {len(result)} price estimation records")
                return cast(List[EstimatedMenuPriceRecord], result)


            except Exception as e:
                session.rollback()
                logging.error(f"Error fetching records for menu: {str(e)}")
                return []

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

    def delete_estimatedmenupricerecord(self, price_estimation_record: EstimatedMenuPriceRecord) -> bool:
        """
        Deletes a price estimation record by ID.
        Returns True if deleted, False otherwise.
        """
        with self.Session() as session:
            try:
                record = session.get(EstimatedMenuPriceRecord, price_estimation_record.id)
                if not record:
                    logging.warning(f"No price estimation record found with id: {price_estimation_record.id}")
                    return False
                session.delete(record)
                session.commit()
                logging.info(f"Deleted price estimation record with id: {price_estimation_record.id}")
                return True
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete price estimation record {price_estimation_record.id}: {e}")
                return False




    #--Recipe--
    def add_recipe(self,
                 inventory_id:int,
                 menu_id:int,
                 inventory_item_amount_usage:Optional[float]=None,
                 writer:Optional[str]=None,
                 description:Optional[str]=None,
                 ) -> Optional[Recipe]:
        """ adding new recipe  """

        if inventory_item_amount_usage is not None and inventory_item_amount_usage < 0:
            logging.error("inventory_item_amount_usage: value cant be negative")
            return None
        if writer:
            writer = writer.lower().strip()
        with self.Session() as session:
            try:
                if not session.get(Menu, menu_id):
                    logging.error(f"Menu ID {menu_id} not found")
                    session.rollback()
                    return None
                if not session.get(Inventory, inventory_id):
                    logging.error(f"Inventory ID {menu_id} not found")
                    session.rollback()
                    return None

                new_record = Recipe(
                    inventory_id=inventory_id,
                    menu_id=menu_id,
                    inventory_item_amount_usage=inventory_item_amount_usage,
                    writer=writer,
                    description=description,
                )
                session.add(new_record)
                session.commit()
                session.refresh(new_record)
                logging.info("Recipe added successfully")
                return new_record
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to add recipe to the database: {e}")
                return None

    def get_recipe(
            self,
            inventory_id: Optional[int]=None,
            menu_id: Optional[int]=None,
            row_num: Optional[int]=None,
    ) -> list[Recipe]:
        """Get recipes can be filtered by inventory_id, menu_id, or both

        Args:
            inventory_id: Filter by inventory item ID
            menu_id: Filter by menu item ID
            row_num: return at most by row number

        Returns:
            List of Recipes (empty list if no matches found or error occurs)
        """

        with (self.Session() as session):
                try:
                    query = session.query(Recipe).order_by(Recipe.time_create.desc())
                    if inventory_id:
                        query = query.filter_by(inventory_id=inventory_id)
                    if menu_id:
                        query = query.filter_by(menu_id=menu_id)
                    if row_num:
                        query = query.limit(row_num)

                    result = query.all()
                    logging.info(f"Found {len(result)} recipes")
                    return cast(list[Recipe], result)

                except Exception as e:
                    session.rollback()
                    logging.error(f"Error fetching recipe : {str(e)}")
                    return []





    def edit_recipe(self, recipe:Recipe) -> Optional[Recipe]:
        """
        Updates an existing recipe in the database.

        Args:
            recipe: The Recipe object with updated values.
                             Must have valid inventory_id and menu_id for existing records.

        Returns:
            The updated Recipe if successful, None on error.
        """

        fields_to_process = ['writer']
        for field in fields_to_process:
            value = getattr(recipe, field, None)
            if isinstance(value, str):
                setattr(recipe, field, value.strip().lower())


        if not recipe.inventory_id or not recipe.menu_id:
            logging.error("Cannot edit recipe without a valid ID (inventory, menu).")
            return None


        with self.Session() as session:
            try:
                existing = session.get(Recipe, (recipe.inventory_id, recipe.menu_id))
                if not existing:
                    logging.info(f"No recipe found with ID: {(recipe.inventory_id, recipe.menu_id)} ")
                    return None
                merged_record  = session.merge(recipe)
                session.commit()
                session.refresh(merged_record )
                logging.info(f"Successfully updated recipe with ids: {(recipe.inventory_id, recipe.menu_id)}")
                return merged_record
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to update recipe with ids: {(recipe.inventory_id, recipe.menu_id)}: {e}")
                return None

    def delete_recipe(self, recipe:Recipe) -> bool:
        """
        Deletes a recipe by inventory_id and menu_id.
        Returns True if deleted, False otherwise.
        """
        if not recipe.inventory_id or not recipe.menu_id:
            logging.error("Cannot edit recipe without a valid ID (inventory, menu).")
            return False
        with self.Session() as session:

            try:
                record_to_delete = session.get(Recipe, (recipe.inventory_id, recipe.menu_id))
                if record_to_delete:
                    session.delete(record_to_delete)
                    session.commit()
                    logging.info(f"Deleted recipe with id: {(recipe.inventory_id, recipe.menu_id)}")
                    return True
                else:
                    logging.warning(f"Recipe with ids {(recipe.inventory_id, recipe.menu_id)} not found for deletion.")
                    return False
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete recipe {(recipe.inventory_id, recipe.menu_id)}: {e}")
                return False


    #--Supplier--
    def add_supplier(self,
                 name:str,
                 contact_channel:Optional[str]=None,
                 contact_address:Optional[str]=None,
                 ) -> Optional[Supplier]:
        """ adding new supplier  """
        if name:
            name = name.strip().lower()

        if contact_channel:
            contact_channel = contact_channel.strip().lower()

        with self.Session() as session:
            try:
                supplier = Supplier(
                    name=name,
                    contact_channel=contact_channel,
                    contact_address=contact_address,
                )
                session.add(supplier)
                session.commit()
                session.refresh(supplier)
                logging.info("Supplier added successfully")
                return supplier
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to add supplier to the database: {e}")
                return None

    def get_supplier(
            self,
            id: Optional[int] = None,
            name:Optional[str] = None,
            row_num: Optional[int]=None,
    ) -> list[Supplier]:
        """can filter supplier by name can make number of supplier returns,
        Returns:
            Supplier object or None on error.
        """


        with self.Session() as session:
                try:
                    query = session.query(Supplier).order_by(Supplier.time_create.desc())
                    if id:
                        query = query.filter_by(id=id)
                    if name:
                        lookup_name = name.lower().strip()
                        query = query.filter_by(name = lookup_name)
                    if row_num:
                        query = query.limit(row_num)
                    result = query.all()
                    logging.info(f"Found {len(result)} suppliers")
                    return cast(List[Supplier], result)

                except Exception as e:
                    session.rollback()
                    logging.error(f"Error fetching supplier {lookup_name}: {str(e)}")
                return []

    def edit_supplier(self, supplier:Supplier) -> Optional[Supplier]:
        """
        Updates an existing supplier in the database.

        Args:
            supplier: The Supplier object with updated values.
                             Must have valid id for existing supplier.

        Returns:
            The updated supplier if successful, None on error.
        """
        fields_to_process = ['name', "contact_channel" ]
        for field in fields_to_process:
            value = getattr(supplier, field, None)
            if isinstance(value, str):
                setattr(supplier, field, value.strip().lower())
        if not supplier.id:
            logging.error("Cannot edit supplier without a valid ID.")
            return None
        with self.Session() as session:
            try:
                existing = session.get(Supplier, supplier.id)
                if not existing:
                    logging.info(f"No supplier found with ID: {supplier.id} ")
                    return None
                merged_supplier  = session.merge(supplier)
                session.commit()
                session.refresh(merged_supplier )
                logging.info(f"Successfully updated supplier with ids: {supplier.id}")
                return merged_supplier
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to update supplier with ids: {supplier.id}: {e}")
                return None

    def delete_supplier(self, supplier:Supplier) -> bool:
        """
        Deletes a supplier .
        Returns True if deleted, False otherwise.
        """

        with self.Session() as session:

            try:
                the_supplier = session.get(Supplier, supplier.id)
                if the_supplier:
                    session.delete(the_supplier)
                    session.commit()
                    logging.info(f"Deleted supplier with id: {supplier.id}")
                    return True
                else:
                    logging.warning(f"supplier with ids {supplier.id} not found for deletion.")
                    return False
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete supplier {supplier.id}: {e}")
                return False



    #--order--
    def add_order(self,
                     supplier_id:int,
                     date:Optional[datetime]=None,
                     buyer:Optional[str]=None,
                     payer:Optional[str]=None,
                     description:Optional[str]=None,
                 ) -> Optional[Order]:
        """ adding new supplier  """
        if date is None:
            date = datetime.now()

        if buyer:
            buyer = buyer.strip().lower()
        if payer:
            payer = payer.strip().lower()

        with self.Session() as session:
            try:
                if supplier_id:
                    check = session.get(Supplier, supplier_id)
                    if not check:
                        logging.info(f"No supplier found with supplier id: {supplier_id}")
                        return None

                new_order = Order(
                    supplier_id=supplier_id,
                    date=date,
                    buyer=buyer,
                    payer=payer,
                    description=description,
                )
                session.add(new_order)
                session.commit()
                session.refresh(new_order)
                logging.info("Order added successfully")
                return new_order
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to add order to the database: {e}")
                return None

    def get_order(
            self,
            id: Optional[int] = None,
            buyer: Optional[str] = None,
            payer: Optional[str]=None,
            supplier:Optional[str]=None,
            from_date: Optional[datetime]=None,
            to_date: Optional[datetime]=None,
            row_num: Optional[int]=None,

    ) -> list[Order]:
        """Get orders with optional filters

        Args:
            id: Filter by id
            buyer: Filter by buyer name (case-insensitive)
            payer: Filter by payer name (case-insensitive)
            supplier: Filter by supplier name
            from_date: Filter orders from this date
            to_date: Filter orders to this date
            row_num: number of data you want to get if not give back all

        Returns:
            List of matching orders (empty list if no matches or no filters provided)
        """


        with self.Session() as session:
                try:
                    query = session.query(Order).order_by(Order.date.desc())

                    if id:
                        query = query.filter_by(id=id)
                    if buyer:
                        lookup_buyer = buyer.lower().strip()
                        query = query.filter_by(buyer=lookup_buyer)

                    if payer:
                        lookup_payer = payer.lower().strip()
                        query = query.filter_by(payer=lookup_payer)
                    if supplier:
                        lookup_supplier = supplier.lower().strip()
                        the_supplier = session.query(Supplier).filter_by(name = lookup_supplier).first()
                        if the_supplier:
                            supplier_id = the_supplier.id
                            query = query.filter_by(supplier_id=supplier_id)
                        else:
                            logging.info(f"No supplier found with name: {supplier}")
                            return []
                    if from_date:
                        query = query.filter(Order.date >= from_date)
                    if to_date:
                        query = query.filter(Order.date <= to_date)

                    if row_num:
                        query = query.limit(row_num)

                    result = query.all()
                    logging.info(f"Found {len(result)} orders")

                    return cast(List[Order], result)

                except Exception as e:
                    session.rollback()
                    logging.error(f"Error fetching orders: {str(e)}")
                    return []

    def edit_order(self, order:Order) -> Optional[Order]:
        """
        Updates an existing order in the database.

        Args:
            order: The Order object with updated values.
                             Must have valid id for existing order.

        Returns:
            The updated supplier if successful, None on error.
        """

        fields_to_process = ['buyer', "payer"]
        for field in fields_to_process:
            value = getattr(order, field, None)
            if isinstance(value, str):
                setattr(order, field, value.strip().lower())
        if not order.id:
            logging.error("Cannot edit order without a valid ID.")
            return None
        with self.Session() as session:
            try:
                existing = session.get(Order, order.id)
                if not existing:
                    logging.info(f"No order found with ID: {order.id} ")
                    return None
                merged_order  = session.merge(order)
                session.commit()
                session.refresh(merged_order )
                logging.info(f"Successfully updated order with ids: {order.id}")
                return merged_order
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to update order with ids: {order.id}: {e}")
                return None

    def delete_order(self, order:Order) -> bool:
        """
        Deletes a order .
        Returns True if deleted, False otherwise.
        """

        with self.Session() as session:

            try:
                the_order = session.get(Order, order.id)
                if the_order:
                    session.delete(the_order)
                    session.commit()
                    logging.info(f"Deleted order with id: {order.id}")
                    return True
                else:
                    logging.warning(f"order with ids {order.id} not found for deletion.")
                    return False
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete order {order.id}: {e}")
                return False



    #--ship--
    def add_ship(self,
                     order_id:int,
                     shipper:Optional[str]=None,
                     price:Optional[float]=None,
                     receiver:Optional[str]=None,
                     payer:Optional[str]=None,
                     date:Optional[datetime]=None,
                     description:Optional[str]=None,
                 ) -> Optional[Ship]:
        """ adding new supplier  """
        if date is None:
            date = datetime.now()
        if shipper:
            shipper = shipper.strip().lower()
        if payer:
            payer = payer.strip().lower()
        if receiver:
            receiver = receiver.strip().lower()

        with self.Session() as session:
            try:
                if order_id:
                    check = session.get(Order, order_id)
                    if not check:
                        logging.info(f"No order found with order id: {order_id}")
                        return None

                new_ship = Ship(
                    order_id=order_id,
                    shipper=shipper,
                    price=price,
                    receiver=receiver,
                    payer=payer,
                    date=date,
                    description=description,
                )
                session.add(new_ship)
                session.commit()
                session.refresh(new_ship)
                logging.info("ship added successfully")
                return new_ship
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to add ship to the database: {e}")
                return None

    def get_ship(
            self,
            id:Optional[int]=None,
            order_id: Optional[int] = None,
            shipper: Optional[str]=None,
            receiver:Optional[str]=None,
            payer: Optional[str]=None,
            from_date: Optional[datetime]=None,
            to_date: Optional[datetime]=None,
            row_num: Optional[int]=None,

    ) -> list[Ship]:
        """Get ship with optional filters

        Args:
            id: get by id
            order_id: filter by order id
            shipper: Filter by shipper name (case-insensitive)
            payer: Filter by payer name (case-insensitive)
            receiver: Filter by receiver name (case-insensitive)
            from_date: Filter ships from this date
            to_date: Filter ships to this date
            row_num: number of data you want to get if not give back all

        Returns:
            List of matching ships (empty list if no matches or no filters provided)
        """

        with self.Session() as session:
                try:
                    query = session.query(Ship).order_by(Ship.date.desc())

                    if id:
                        query= query.filter_by(id = id)

                    if order_id:
                        check = session.get(Order, order_id)
                        if not check:
                            logging.info(f"No order found with order_id: {order_id}")
                            return []
                        query = query.filter_by(order_id=order_id)

                    if shipper:
                        shipper = shipper.strip().lower()
                        query = query.filter_by(shipper=shipper)

                    if receiver:
                        receiver = receiver.strip().lower()
                        query = query.filter_by(receiver=receiver)

                    if payer:
                        payer = payer.strip().lower()
                        query = query.filter_by(payer=payer)

                    if from_date:
                        query = query.filter(Ship.date >= from_date)
                    if to_date:
                        query = query.filter(Ship.date <= to_date)

                    if row_num:
                        query = query.limit(row_num)

                    result = query.all()
                    logging.info(f"Found {len(result)} ship")

                    return cast(List[Ship], result)
                except Exception as e:
                    session.rollback()
                    logging.error(f"Error fetching ship: {str(e)}")
                    return []

    def edit_ship(self, ship:Ship) -> Optional[Ship]:
        """
        Updates an existing ship in the database.

        Args:
            ship: The Ship object with updated values.
                             Must have valid id for existing Ship.

        Returns:
            The updated ship if successful, None on error.
        """
        fields_to_process = ['shipper', "receiver", "payer"]
        for field in fields_to_process:
            value = getattr(ship, field, None)
            if isinstance(value, str):
                setattr(ship, field, value.strip().lower())
        if not ship.id:
            logging.error("Cannot edit ship without a valid ID.")
            return None
        with self.Session() as session:
            try:
                existing = session.get(Ship, ship.id)
                if not existing:
                    logging.info(f"No ship found with ID: {ship.id} ")
                    return None
                merged_ship  = session.merge(ship)
                session.commit()
                session.refresh(merged_ship )
                logging.info(f"Successfully updated ship with ids: {ship.id}")
                return merged_ship
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to update ship with ids: {ship.id}: {e}")
                return None

    def delete_ship(self, ship:Ship) -> bool:
        """
        Deletes a ship .
        Returns True if deleted, False otherwise.
        """

        with self.Session() as session:

            try:
                the_ship = session.get(Ship, ship.id)
                if the_ship:
                    session.delete(the_ship)
                    session.commit()
                    logging.info(f"Deleted ship with id: {ship.id}")
                    return True
                else:
                    logging.warning(f"ship with ids {ship.id} not found for deletion.")
                    return False
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete ship {ship.id}: {e}")
                return False




    #--SupplyRecord--

    def add_supplyrecord(self,
                     inventory_item_id:int,
                     ship_id:int,
                     price:Optional[float]=None,
                     box_amount:Optional[float]=None,
                     box_price:Optional[float]=None,
                     box_discount:Optional[float]=None,
                     num_of_box:Optional[float]=None,
                     description:Optional[str]=None,
                 ) -> Optional[SupplyRecord]:
        """ adding new supplyrecord  """
        if not ship_id or not inventory_item_id:
            logging.error("Cannot add supplyrecord without valid ship_id or inventory_item_id")
            return None

        if price is not None and price < 0:
            logging.error("Cannot add supplyrecord with negative price")
            return None
        if box_amount is not None and box_amount < 0:
            logging.error("Cannot add supplyrecord with negative box_amount")
            return None
        if box_price is not None and box_price < 0:
            logging.error("Cannot add supplyrecord with negative box_price")
            return None
        if box_discount is not None and box_discount < 0:
            logging.error("Cannot add supplyrecord with negative box_discount")
            return None
        if num_of_box is not None and num_of_box < 0:
            logging.error("Cannot add supplyrecord with negative num_of_box")
            return None


        with self.Session() as session:
            try:
                if ship_id:
                    check = session.get(Ship, ship_id)
                    if not check:
                        logging.info(f"No ship found with ship id: {ship_id}")
                        return None
                if inventory_item_id:
                    check = session.get(Inventory, inventory_item_id)
                    if not check:
                        logging.info(f"No inventory item found with order id: {inventory_item_id}")
                        return None

                new_supply_record = SupplyRecord(
                    inventory_item_id=inventory_item_id,
                    ship_id=ship_id,
                    price=price,
                    box_amount=box_amount,
                    box_price=box_price,
                    box_discount=box_discount,
                    num_of_box=num_of_box,
                    description=description
                )
                session.add(new_supply_record)
                session.commit()
                session.refresh(new_supply_record)
                logging.info("supply record added successfully")
                return new_supply_record
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to add supply record to the database: {e}")
                return None

    def get_supplyrecord(
            self,
            id:Optional[int] = None,
            inventory_item_id: Optional[int] = None,
            ship_id: Optional[int] = None,
            row_num: Optional[int]=None,

    ) -> list[SupplyRecord]:
        """Get supply record with optional filters

        Args:
            id: filter by record id
            inventory_item_id: filter by inventory id
            ship_id: filter by ship id
            row_num: number of data you want to get if not give back all

        Returns:
            List of matching supply records (empty list if no matches or no filters provided)
        """
        with self.Session() as session:
                try:
                    query = session.query(SupplyRecord).order_by(SupplyRecord.time_create.desc())

                    if id:
                        query = query.filter_by(id=id)
                    if inventory_item_id:
                        check = session.get(Inventory, inventory_item_id)
                        if not check:
                            logging.info(f"No item in inventory with inventory_item_id: {inventory_item_id}")
                            return []
                        query = query.filter_by(inventory_item_id=inventory_item_id)

                    if ship_id:
                        check = session.get(Ship, ship_id)
                        if not check:
                            logging.info(f"No ship found with ship_id: {ship_id}")
                            return []
                        query = query.filter_by(ship_id=ship_id)

                    if row_num:
                        query = query.limit(row_num)

                    result = query.all()
                    logging.info(f"Found {len(result)} supply records")

                    return cast(List[SupplyRecord], result)

                except Exception as e:
                    session.rollback()
                    logging.error(f"Error fetching supply records: {str(e)}")
                    return []


    def edit_supplyrecord(self, supply_record:SupplyRecord) -> Optional[SupplyRecord]:
        """
        Updates an existing supply record in the database.

        Args:
            supply_record: The SupplyRecord object with updated values.
                         Must have valid id.

        Returns:
            The updated SupplyRecord if successful, None on error.
        """



        if not supply_record.id:
            logging.info("No supply record id")
            return None
        if not supply_record.inventory_item_id or not supply_record.ship_id:
            logging.error("Cannot edit supply record without inventory item id and ship id.")
            return None
        with self.Session() as session:
            try:
                existing = session.get(SupplyRecord, supply_record.id)
                if not existing:
                    logging.info(f"No supply record found with ID: {supply_record.id} ")
                    return None
                merged_supply_record  = session.merge(supply_record)
                session.commit()
                session.refresh(merged_supply_record )
                logging.info(f"Successfully updated supply record with ids: {supply_record.id}")
                return merged_supply_record
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to update supply record with ids: {supply_record.id}: {e}")
                return None

    def delete_supplyrecord(self, supply_record:SupplyRecord) -> bool:
        """
        Deletes a supply record.
        Returns True if deleted, False otherwise.
        """

        if not supply_record.id:
            logging.error("Cannot delete supply record without id.")
            return False

        if not supply_record.inventory_item_id or not supply_record.ship_id:
            logging.error("Cannot edit supply record without id.")
            return False

        with self.Session() as session:

            try:
                the_supply_record = session.get(SupplyRecord, supply_record.id)
                if the_supply_record:
                    session.delete(the_supply_record)
                    session.commit()
                    logging.info(f"Deleted supply record with id: {supply_record.id}")
                    return True
                else:
                    logging.warning(f"supply record with id {supply_record.id} not found for deletion.")
                    return False
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete supply record {supply_record.id}: {e}")
                return False




    #--InvoicePayment--

    def add_invoicepayment(self,
                    payed: Optional[float] = None,
                    payer: Optional[str] = None,
                    method: Optional[str] = None,
                    date: Optional[datetime] = None,
                    receiver: Optional[str] = None,
                    receiver_id: Optional[str] = None,
                    ) -> Optional[InvoicePayment]:

        """ adding new invoice  payment"""
        if payed is not None and payed <= 0:
            logging.error("Total payed must be greater than 0.")
            return None

        if payer:
            payer = payer.lower().strip()
        if method:
            method = method.lower().strip()
        if receiver:
            receiver = receiver.lower().strip()



        if not date:
            date = datetime.now()

        with self.Session() as session:
            try:


                new_invoice_payment = InvoicePayment(
                    payed=payed,
                    payer=payer,
                    method=method,
                    date=date,
                    receiver=receiver,
                    receiver_id=receiver_id,

                )
                session.add(new_invoice_payment)
                session.commit()
                session.refresh(new_invoice_payment)
                logging.info("invoice payment added successfully")
                return new_invoice_payment
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to add invoice payment to the database: {e}")
                return None

    def get_invoicepayment(
            self,
            id: Optional[int] = None,
            payer: Optional[str] = None,
            method: Optional[str] = None,
            receiver: Optional[str] = None,
            receiver_id: Optional[str] = None,
            from_date: Optional[datetime] = None,
            to_date: Optional[datetime] = None,
            row_num: Optional[int] = None,

    ) -> list[InvoicePayment]:
        """Get invoice payment with optional filters



        Returns:
            List of matching InvoicePayment (empty list if no matches or no filters provided)
        """
        with self.Session() as session:
                try:
                    query = session.query(InvoicePayment).order_by(InvoicePayment.date.desc())
                    if id:
                        query = query.filter_by(id=id)

                    if payer:
                        payer = payer.lower().strip()
                        query = query.filter_by(payer=payer)

                    if method:
                        method = method.lower().strip()
                        query = query.filter_by(method=method)

                    if receiver:
                        receiver = receiver.lower().strip()
                        query = query.filter_by(receiver=receiver)

                    if receiver_id:
                        query = query.filter_by(receiver_id=receiver_id)

                    if from_date:
                        query = query.filter(InvoicePayment.date >= from_date)
                        
                    if to_date:
                        query = query.filter(InvoicePayment.date <= to_date)

                    if row_num:
                        query = query.limit(row_num)

                    result = query.all()
                    logging.info(f"Found {len(result)} invoice payment")

                    return cast(List[InvoicePayment], result)

                except Exception as e:
                    session.rollback()
                    logging.error(f"Error fetching invoice payment(s): {str(e)}")
                    return []


    def edit_invoicepayment(self, invoice_payment:InvoicePayment) -> Optional[InvoicePayment]:
        """
        Updates an existing invoice payment in the database.

        Args:
            invoice_payment: The InvoicePayment object with updated values.
                         Must have valid id.

        Returns:
            The updated InvoicePayment if successful, None on error.
        """
        fields_to_process = ['payer', "method", "receiver"]
        for field in fields_to_process:
            value = getattr(invoice_payment, field, None)
            if isinstance(value, str):
                setattr(invoice_payment, field, value.strip().lower())
        if not invoice_payment.id:
            logging.info("No invoice payment id")
            return None

        with self.Session() as session:
            try:
                existing = session.get(InvoicePayment, invoice_payment.id)
                if not existing:
                    logging.info(f"No invoice payment found with ID: {invoice_payment.id} ")
                    return None
                merged_invoice_payment  = session.merge(invoice_payment)
                session.commit()
                session.refresh(merged_invoice_payment )
                logging.info(f"Successfully updated invoice payment with ids: {invoice_payment.id}")
                return merged_invoice_payment
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to update invoice payment with ids: {invoice_payment.id}: {e}")
                return None

    def delete_invoicepayment(self, invoice_payment:InvoicePayment) -> bool:
        """
        Deletes an invoice payment in the database.
        Returns True if deleted, False otherwise.
        """

        if not invoice_payment.id:
            logging.error("Cannot delete invoice payment without invoice id.")
            return False

        with self.Session() as session:

            try:
                the_invoice_payment = session.get(InvoicePayment, invoice_payment.id)
                if the_invoice_payment:
                    session.delete(the_invoice_payment)
                    session.commit()
                    logging.info(f"Deleted invoice payment with id: {invoice_payment.id}")
                    return True
                else:
                    logging.warning(f"invoice payment with id {invoice_payment.id} not found for deletion.")
                    return False
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete invoice payment {invoice_payment.id}: {e}")
                return False


    #--Invoice--

    def add_invoice(self,
                    pay_id: Optional[int] = None,
                    saler: Optional[str] = None,
                    date: Optional[datetime] = None,
                    total_price: Optional[float] = None,
                    closed: bool = False,
                    description: Optional[str] = None,
                    ) -> Optional[Invoice]:

        """ adding new invoice  """
        if total_price is not None and total_price <= 0:
            logging.error("Total price must be greater than 0.")
            return None

        if saler:
            saler = saler.lower().strip()

        #todo this look problematic just wrote it here to check others
        if not date:
            date = datetime.now()

        with self.Session() as session:
            try:
                if pay_id:
                    check = session.get(InvoicePayment, pay_id)
                    if not check:
                        logging.info(f"No payment found with pay id: {pay_id}")
                        return None

                new_invoice = Invoice(
                    pay_id=pay_id,
                    saler=saler,
                    date=date,
                    total_price=total_price,
                    closed=closed,
                    description=description,

                )
                session.add(new_invoice)
                session.commit()
                session.refresh(new_invoice)
                logging.info("invoice added successfully")
                return new_invoice
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to add invoice to the database: {e}")
                return None

    def get_invoice(
            self,
            id: Optional[int] = None,
            saler: Optional[str] = None,
            pay_id: Optional[int] = None,
            closed:Optional[bool] = None,
            from_date: Optional[datetime] = None,
            to_date: Optional[datetime] = None,
            row_num: Optional[int] = None,

    ) -> list[Invoice]:
        """Get invoice with optional filters



        Returns:
            List of matching invoices (empty list if no matches or no filters provided)
        """
        with self.Session() as session:
                try:
                    query = session.query(Invoice).order_by(Invoice.date.desc())
                    if id:
                        query = query.filter_by(id=id)
                    if closed is not None:
                        query = query.filter_by(closed=closed)

                    if pay_id:
                        check = session.get(InvoicePayment, pay_id)
                        if not check:
                            logging.info(f"No ship found with pay_id: {pay_id}")
                            return []
                        query = query.filter_by(pay_id=pay_id)

                    if saler:
                        saler = saler.lower().strip()
                        query = query.filter_by(saler=saler)

                    if from_date:
                        query = query.filter(Invoice.date >= from_date)

                    if to_date:
                        query = query.filter(Invoice.date <= to_date)

                    if row_num:
                        query = query.limit(row_num)

                    result = query.all()
                    logging.info(f"Found {len(result)} invoices")

                    return cast(List[Invoice], result)

                except Exception as e:
                    session.rollback()
                    logging.error(f"Error fetching invoice(s): {str(e)}")
                    return []


    def edit_invoice(self, invoice:Invoice) -> Optional[Invoice]:
        """
        Updates an existing invoice in the database.

        Args:
            invoice: The Invoice object with updated values.
                         Must have valid id.

        Returns:
            The updated invoice if successful, None on error.
        """
        fields_to_process = ['saler']
        for field in fields_to_process:
            value = getattr(invoice, field, None)
            if isinstance(value, str):
                setattr(invoice, field, value.strip().lower())
        if not invoice.id:
            logging.info("No invoice id")
            return None

        with self.Session() as session:
            try:
                existing = session.get(Invoice, invoice.id)
                if not existing:
                    logging.info(f"No invoice found with ID: {invoice.id} ")
                    return None
                merged_invoice  = session.merge(invoice)
                session.commit()
                session.refresh(merged_invoice )
                logging.info(f"Successfully updated invoice with ids: {invoice.id}")
                return merged_invoice
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to update invoice with ids: {invoice.id}: {e}")
                return None

    def delete_invoice(self, invoice:Invoice) -> bool:
        """
        Deletes a invoice.
        Returns True if deleted, False otherwise.
        """

        if not invoice.id:
            logging.error("Cannot delete supply record without invoice id.")
            return False

        with self.Session() as session:

            try:
                the_invoice = session.get(Invoice, invoice.id)
                if the_invoice:
                    session.delete(the_invoice)
                    session.commit()
                    logging.info(f"Deleted invoice with id: {invoice.id}")
                    return True
                else:
                    logging.warning(f"invoice with id {invoice.id} not found for deletion.")
                    return False
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete invoice {invoice.id}: {e}")
                return False


    #--sales--

    def add_sales(self,
                    menu_id: Optional[int] = None,
                    invoice_id: Optional[int] = None,
                    number: Optional[int] = None,
                    discount: Optional[float] = None,
                    price: Optional[float] = None,
                    description: Optional[str] = None,
                    ) -> Optional[Sales]:

        """ adding new sales  """
        if number is not None and number <= 0:
            logging.error("Total number must be greater than 0.")
            return None
        if price is not None and price <= 0:
            logging.error("Total price must be greater than 0.")
            return None
        if discount is not None and discount < 0:
            logging.error("Discount cannot be negative.")
            return None


        with self.Session() as session:
            try:
                if menu_id:
                    check = session.get(Menu, menu_id)
                    if not check:
                        logging.info(f"No menu item found with menu id: {menu_id}")
                        return None
                if invoice_id:
                    check = session.get(Invoice, invoice_id)
                    if not check:
                        logging.info(f"No invoice found with invoice id: {invoice_id}")
                        return None

                new_sales = Sales(
                    menu_id=menu_id,
                    invoice_id=invoice_id,
                    number=number,
                    discount=discount,
                    price=price,
                    description=description,

                )
                session.add(new_sales)
                session.commit()
                session.refresh(new_sales)
                logging.info("sales added successfully")
                return new_sales
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to add sales to the database: {e}")
                return None

    def get_sales(
            self,
            menu_id: Optional[int] = None,
            invoice_id: Optional[int] = None,
            row_num: Optional[int] = None,

    ) -> list[Sales]:
        """Get sales with optional filters



        Returns:
            List of matching Sales (empty list if no matches or no filters provided)
        """
        with self.Session() as session:
                try:
                    query = session.query(Sales).order_by(Sales.time_create.desc())
                    if menu_id:
                        query = query.filter_by(menu_id=menu_id)
                    if invoice_id:
                        query = query.filter_by(invoice_id=invoice_id)

                    if row_num:
                        query = query.limit(row_num)

                    result = query.all()
                    logging.info(f"Found {len(result)} sales")

                    return cast(List[Sales], result)

                except Exception as e:
                    session.rollback()
                    logging.error(f"Error fetching sales: {str(e)}")
                    return []


    def edit_sales(self, sales:Sales) -> Optional[Sales]:
        """
        Updates an existing sale in the database.

        Args:
            sales: The Sales object with updated values.
                         Must have valid id.

        Returns:
            The updated Sales if successful, None on error.
        """
        # fields_to_process = ['saler']
        # for field in fields_to_process:
        #     value = getattr(invoice, field, None)
        #     if isinstance(value, str):
        #         setattr(invoice, field, value.strip().lower())



        if not sales.menu_id or not sales.invoice_id:
            logging.info("No valid ids")
            return None

        key = (sales.menu_id, sales.invoice_id)

        with self.Session() as session:
            try:
                existing = session.get(Sales, key)
                if not existing:
                    logging.info(f"No sales found with IDs: {key} ")
                    return None
                merged_sales  = session.merge(sales)
                session.commit()
                session.refresh(merged_sales )
                logging.info(f"Successfully updated sales with ids: {key}")
                return merged_sales
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to update sales with ids: {key}: {e}")
                return None

    def delete_sales(self, sales:Sales) -> bool:
        """
        Deletes a sales.
        Returns True if deleted, False otherwise.
        """

        if not sales.menu_id or not sales.invoice_id:
            logging.error("Cannot delete sales record without  menu_id and invoice_id.")
            return False
        key = (sales.menu_id, sales.invoice_id)

        with self.Session() as session:

            try:
                the_sales = session.get(Sales, key)
                if the_sales:
                    session.delete(the_sales)
                    session.commit()
                    logging.info(f"Deleted sales with ids: {key}")
                    return True
                else:
                    logging.warning(f"sales with ids {key} not found for deletion.")
                    return False
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete sales {key}: {e}")
                return False




    #--Usage--

    def add_usage(self,
                    used_by: Optional[str] = None,
                    date: Optional[datetime] = None,
                    category: Optional[str] = None,
                    description: Optional[str] = None,
                    ) -> Optional[Usage]:

        """ adding new usage  """
        #todo if used_by should be if used_by is not None
        if used_by is not None:
            used_by = used_by.lower().strip()

        if category is not None:
            category = category.lower().strip()

        if date is None:
            date = datetime.now()



        with self.Session() as session:
            try:

                new_usage = Usage(
                    used_by=used_by,
                    date=date,
                    category=category,
                    description=description,
                )
                session.add(new_usage)
                session.commit()
                session.refresh(new_usage)
                logging.info("usage added successfully")
                return new_usage
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to add usage to the database: {e}")
                return None

    def get_usage(
            self,
            id: Optional[int] = None,
            used_by: Optional[str] = None,
            category: Optional[str] = None,
            from_date: Optional[datetime] = None,
            to_date: Optional[datetime] = None,
            row_num: Optional[int] = None,

    ) -> list[Usage]:
        """Get usage with optional filters



        Returns:
            List of matching usages (empty list if no matches or no filters provided)
        """
        if used_by is not None:
            used_by = used_by.lower().strip()

        if category is not None:
            category = category.lower().strip()
        with self.Session() as session:
                try:
                    query = session.query(Usage).order_by(Usage.date.desc())
                    if id:
                        query = query.filter_by(id=id)

                    if used_by:
                        query = query.filter_by(used_by=used_by)

                    if category:
                        query = query.filter_by(category=category)

                    if from_date:
                        query = query.filter(Usage.date >= from_date)

                    if to_date:
                        query = query.filter(Usage.date <= to_date)

                    if row_num:
                        query = query.limit(row_num)

                    result = query.all()
                    logging.info(f"Found {len(result)} usage(s)")

                    return cast(List[Usage], result)

                except Exception as e:
                    session.rollback()
                    logging.error(f"Error fetching usage: {str(e)}")
                    return []


    def edit_usage(self, usage:Usage) -> Optional[Usage]:
        """
        Updates an existing usage in the database.

        Args:
            usage: The Usage object with updated values.
                         Must have valid id.

        Returns:
            The updated Usage if successful, None on error.
        """
        fields_to_process = ['used_by', "category"]
        for field in fields_to_process:
            value = getattr(usage, field, None)
            if isinstance(value, str):
                setattr(usage, field, value.strip().lower())



        if not usage.id:
            logging.info("No valid id")
            return None

        with self.Session() as session:
            try:
                existing = session.get(Usage, usage.id)
                if not existing:
                    logging.info(f"No usage found with IDs: {usage.id} ")
                    return None
                merged_usage  = session.merge(usage)
                session.commit()
                session.refresh(merged_usage )
                logging.info(f"Successfully updated usage with ids: {usage.id}")
                return merged_usage
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to update usage with ids: {usage.id}: {e}")
                return None

    def delete_usage(self, usage:Usage) -> bool:
        """
        Deletes a usage.
        Returns True if deleted, False otherwise.
        """

        if not usage.id:
            logging.error("Cannot delete usage record without ID.")
            return False

        with self.Session() as session:

            try:
                the_usage = session.get(Usage, usage.id)
                if the_usage:
                    session.delete(the_usage)
                    session.commit()
                    logging.info(f"Deleted usage with ids: {usage.id}")
                    return True
                else:
                    logging.warning(f"usage with ids {usage.id} not found for deletion.")
                    return False
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete usage {usage.id}: {e}")
                return False




    #--InventoryUsage--

    def add_inventoryusage(self,
                    inventory_item_id:int ,
                    usage_id:int ,
                    amount: Optional[int] = None,

                    ) -> Optional[InventoryUsage]:

        """ adding new InventoryUsage  """
        if amount is not None and amount <= 0:
            logging.error("Total amount must be greater than 0.")
            return None



        with self.Session() as session:
            try:

                new_inventory_usage = InventoryUsage(
                    inventory_item_id=inventory_item_id,
                    usage_id=usage_id,
                    amount=amount,
                )
                session.add(new_inventory_usage)
                session.commit()
                session.refresh(new_inventory_usage)
                logging.info("inventory usage added successfully")
                return new_inventory_usage
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to add inventory usage to the database: {e}")
                return None

    def get_inventoryusage(
            self,
            inventory_item_id: Optional[int] = None,
            usage_id: Optional[int] = None,
            row_num: Optional[int] = None,
    ) -> list[InventoryUsage]:
        """Get inventory_usage with optional filters



        Returns:
            List of matching InventoryUsage (empty list if no matches or no filters provided)
        """

        with self.Session() as session:
                try:
                    query = session.query(InventoryUsage).order_by(InventoryUsage.time_create.desc())

                    if inventory_item_id:
                        query = query.filter_by(inventory_item_id=inventory_item_id)

                    if usage_id:
                        query = query.filter_by(usage_id=usage_id)

                    if row_num:
                        query = query.limit(row_num)

                    result = query.all()
                    logging.info(f"Found {len(result)} inventory_usage(s)")

                    return cast(List[InventoryUsage], result)

                except Exception as e:
                    session.rollback()
                    logging.error(f"Error fetching inventory_usage: {str(e)}")
                    return []


    def edit_inventoryusage(self, inventory_usage:InventoryUsage) -> Optional[InventoryUsage]:
        """
        Updates an existing inventory_usage in the database.

        Args:
            inventory_usage: The Usage object with updated values.
                         Must have valid id.

        Returns:
            The updated InventoryUsage if successful, None on error.
        """

        # fields_to_process = ['used_by', "category"]
        # for field in fields_to_process:
        #     value = getattr(usage, field, None)
        #     if isinstance(value, str):
        #         setattr(usage, field, value.strip().lower())

        if not inventory_usage.inventory_item_id or not inventory_usage.usage_id:
            logging.error("Cannot update inventory usage record without inventory_item_id and usage_id.")
            return None

        with self.Session() as session:
            try:

                inventory_exists = session.get(Inventory, inventory_usage.inventory_item_id)
                if not inventory_exists:
                    logging.info(f"No inventory item found with IDs: {inventory_usage.inventory_item_id} ")
                    return None

                usage_exists = session.get(Usage, inventory_usage.usage_id)
                if not usage_exists:
                    logging.info(f"No usage record found with IDs: {inventory_usage.usage_id} ")
                    return None

                merged_inventory_usage  = session.merge(inventory_usage)
                session.commit()
                session.refresh(merged_inventory_usage )
                logging.info(f"Successfully updated inventory usage")
                return merged_inventory_usage
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to update inventory usage : {e}")
                return None

    def delete_inventoryusage(self, inventory_usage:InventoryUsage) -> bool:
        """
        Deletes a InventoryUsage.
        Returns True if deleted, False otherwise.
        """

        if not inventory_usage.inventory_item_id or not inventory_usage.usage_id:
            logging.error("Cannot delete inventory usage record without ID.")
            return False

        key = (inventory_usage.inventory_item_id, inventory_usage.usage_id)
        with self.Session() as session:

            try:
                the_inventory_usage = session.get(InventoryUsage, key)
                if the_inventory_usage:
                    session.delete(the_inventory_usage)
                    session.commit()
                    logging.info(f"Deleted inventory usage with ids: {key}")
                    return True
                else:
                    logging.warning(f"inventory usage with ids {key} not found for deletion.")
                    return False
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete inventory usage {key}: {e}")
                return False




    #--MenuUsage--

    def add_menuusage(self,
                    menu_id:int ,
                    usage_id:int ,
                    amount: Optional[int] = None,

                    ) -> Optional[MenuUsage]:

        """ adding new MenuUsage  """
        if amount is not None and amount <= 0:
            logging.error("Total amount must be greater than 0.")
            return None



        with self.Session() as session:
            try:

                new_menu_usage = MenuUsage(
                    menu_id=menu_id,
                    usage_id=usage_id,
                    amount=amount,
                )
                session.add(new_menu_usage)
                session.commit()
                session.refresh(new_menu_usage)
                logging.info("menu usage added successfully")
                return new_menu_usage
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to add menu usage to the database: {e}")
                return None

    def get_menuusage(
            self,
            menu_id: Optional[int] = None,
            usage_id: Optional[int] = None,
            row_num: Optional[int] = None,
    ) -> list[MenuUsage]:
        """Get menu_usage with optional filters



        Returns:
            List of matching MenuUsage (empty list if no matches or no filters provided)
        """

        with self.Session() as session:
                try:
                    query = session.query(MenuUsage).order_by(MenuUsage.time_create.desc())

                    if menu_id:
                        query = query.filter_by(menu_id=menu_id)

                    if usage_id:
                        query = query.filter_by(usage_id=usage_id)

                    if row_num:
                        query = query.limit(row_num)

                    result = query.all()
                    logging.info(f"Found {len(result)} menu usage(s)")

                    return cast(List[MenuUsage], result)

                except Exception as e:
                    session.rollback()
                    logging.error(f"Error fetching menu usage: {str(e)}")
                    return []


    def edit_menuusage(self, menu_usage:MenuUsage) -> Optional[MenuUsage]:
        """
        Updates an existing menu_usage in the database.

        Args:
            menu_usage: The MenuUsage object with updated values.
                         Must have valid menu_id and usage_id.

        Returns:
            The updated MenuUsage if successful, None on error.
        """

        # fields_to_process = ['used_by', "category"]
        # for field in fields_to_process:
        #     value = getattr(usage, field, None)
        #     if isinstance(value, str):
        #         setattr(usage, field, value.strip().lower())

        if not menu_usage.menu_id or not menu_usage.usage_id:
            logging.error("Cannot update menu usage record without menu_id and usage_id.")
            return None

        with self.Session() as session:
            try:

                menu_exists = session.get(Menu, menu_usage.menu_id)
                if not menu_exists:
                    logging.info(f"No menu item found with IDs: {menu_usage.menu_id} ")
                    return None

                usage_exists = session.get(Usage, menu_usage.usage_id)
                if not usage_exists:
                    logging.info(f"No usage record found with IDs: {menu_usage.usage_id} ")
                    return None

                merged_menu_usage  = session.merge(menu_usage)
                session.commit()
                session.refresh(merged_menu_usage )
                logging.info(f"Successfully updated menu usage")
                return merged_menu_usage
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to update menu usage : {e}")
                return None

    def delete_menuusage(self, menu_usage:MenuUsage) -> bool:
        """
        Deletes a MenuUsage.
        Returns True if deleted, False otherwise.
        """

        if not menu_usage.menu_id or not menu_usage.usage_id:
            logging.error("Cannot delete menu usage record without ID.")
            return False

        key = (menu_usage.menu_id, menu_usage.usage_id)
        with self.Session() as session:

            try:
                the_menu_usage = session.get(MenuUsage, key)
                if the_menu_usage:
                    session.delete(the_menu_usage)
                    session.commit()
                    logging.info(f"Deleted menu usage with ids: {key}")
                    return True
                else:
                    logging.warning(f"menu usage with ids {key} not found for deletion.")
                    return False
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete menu usage {key}: {e}")
                return False




    #--SalesForecast--

    def add_salesforecast(self,
                          menu_item_id: int,
                          from_date: datetime,
                          to_date: datetime,
                          sell_number:int,
                    ) -> Optional[SalesForecast]:

        """ adding new SalesForecast  """
        if sell_number is not None and sell_number < 0:
            logging.error("Total amount can not be negative")
            return None

        if from_date >= to_date:
            logging.error("from date should be less than to_date ")
            return None



        with self.Session() as session:
            try:
                menu_check = session.get(Menu, menu_item_id)
                if not menu_check:
                    logging.info(f"No menu item found with ID: {menu_item_id}")
                    return None

                existing_overlap = session.query(SalesForecast).filter(
                    SalesForecast.menu_item_id == menu_item_id,
                    SalesForecast.from_date < to_date,
                    SalesForecast.to_date > from_date
                ).first()

                if existing_overlap:
                    logging.error(f"Time overlap with existing forecast (ID: {existing_overlap.id}) "
                                  f"from {existing_overlap.from_date} to {existing_overlap.to_date}")
                    return None


                new_sales_forecast = SalesForecast(
                    menu_item_id=menu_item_id,
                    from_date=from_date,
                    to_date=to_date,
                    sell_number=sell_number,
                )
                session.add(new_sales_forecast)
                session.commit()
                session.refresh(new_sales_forecast)
                logging.info("sales_forecast added successfully")
                return new_sales_forecast
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to add sales_forecast to the database: {e}")
                return None

    def get_salesforecast(
            self,
            id: Optional[int] = None,
            menu_item_id: Optional[int] = None,
            from_date: Optional[datetime] = None,
            to_date: Optional[datetime] = None,
            row_num: Optional[int] = None,
    ) -> list[SalesForecast]:
        """Get sales_forecast with optional filters



        Returns:
            List of matching SalesForecast (empty list if no matches or no filters provided)
        """

        with self.Session() as session:
                try:
                    query = session.query(SalesForecast).order_by(SalesForecast.from_date.desc())
                    if id:
                        query = query.filter_by(id=id)
                    if menu_item_id:
                        query = query.filter_by(menu_item_id=menu_item_id)

                    if from_date:
                        query = query.filter(SalesForecast.from_date >= from_date)

                    if to_date:
                        query = query.filter(SalesForecast.from_date <= to_date)

                    if row_num:
                        query = query.limit(row_num)

                    result = query.all()
                    logging.info(f"Found {len(result)} sales_forecast")

                    return cast(list[SalesForecast], result)

                except Exception as e:
                    session.rollback()
                    logging.error(f"Error fetching sales_forecast: {str(e)}")
                    return []


    def edit_salesforecast(self, sales_forecast:SalesForecast) -> Optional[SalesForecast]:
        """
        Updates an existing sales_forecast in the database.

        Args:
            sales_forecast: The SalesForecast object with updated values.
                         Must have valid ID.

        Returns:
    The updated SalesForecast if successful, None on error.
        """

        # fields_to_process = ['used_by', "category"]
        # for field in fields_to_process:
        #     value = getattr(usage, field, None)
        #     if isinstance(value, str):
        #         setattr(usage, field, value.strip().lower())

        if sales_forecast.from_date and sales_forecast.to_date:
            if sales_forecast.from_date >= sales_forecast.to_date:
                logging.error("from date should be less than to date ")
                return None

        with self.Session() as session:
            try:
                existing_overlap = session.query(SalesForecast).filter(
                    SalesForecast.id != sales_forecast.id,
                    SalesForecast.menu_item_id == sales_forecast.menu_item_id,
                    SalesForecast.from_date < sales_forecast.to_date,
                    SalesForecast.to_date > sales_forecast.from_date
                ).first()

                if existing_overlap:
                    logging.error(f"Time overlap with existing forecast (ID: {existing_overlap.id})")
                    return None

                menu_exists = session.get(Menu, sales_forecast.menu_item_id)
                if not menu_exists:
                    logging.info(f"No menu item found with IDs: {sales_forecast.menu_item_id} ")
                    return None


                new_sales_forecast  = session.merge(sales_forecast)
                session.commit()
                session.refresh(new_sales_forecast)
                logging.info(f"Successfully updated sales_forecast")
                return new_sales_forecast
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to update sales_forecast : {e}")
                return None

    def delete_salesforecast(self, sales_forecast:SalesForecast) -> bool:
        """
        Deletes a SalesForecast.
        Returns True if deleted, False otherwise.
        """

        if not sales_forecast.id:
            logging.error("Cannot delete sales_forecast record without ID.")
            return False

        with self.Session() as session:

            try:
                the_sales_forecast = session.get(SalesForecast, sales_forecast.id)
                if the_sales_forecast:
                    session.delete(the_sales_forecast)
                    session.commit()
                    logging.info(f"Deleted sales_forecast with ID: {sales_forecast.id}")
                    return True
                else:
                    logging.warning(f"sales_forecast with ids {sales_forecast.id} not found for deletion.")
                    return False
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete sales_forecast {sales_forecast.id}: {e}")
                return False




    #--EstimatedBills--

    def add_estimatedbills(self,
                          name: str,
                           category: str,
                          from_date: datetime,
                          to_date: datetime,
                          cost: Optional[float] = None,
                          description:Optional[str] = None,
                    ) -> Optional[EstimatedBills]:

        """ adding new EstimatedBills  """
        if cost is not None and cost < 0:
            logging.error("Total amount can not be negative")
            return None

        if from_date >= to_date:
            logging.error("from date should be less than to date ")
            return None

        if name is not None:
            name = name.lower().strip()

        if category is not None:
            category = category.lower().strip()

        with self.Session() as session:
            try:

                existing_overlap = session.query(EstimatedBills).filter(
                    EstimatedBills.category == category,
                    EstimatedBills.from_date < to_date,
                    EstimatedBills.to_date > from_date
                ).first()

                if existing_overlap:
                    logging.error(f"Time overlap with existing estimated  (ID: {existing_overlap.id}) "
                                  f"from {existing_overlap.from_date} to {existing_overlap.to_date}")
                    return None


                new_estimated_bill = EstimatedBills(
                    name=name,
                    category=category,
                    cost=cost,
                    from_date=from_date,
                    to_date=to_date,
                    description=description,
                )
                session.add(new_estimated_bill)
                session.commit()
                session.refresh(new_estimated_bill)
                logging.info("estimated_bills added successfully")
                return new_estimated_bill
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to add estimated_bills to the database: {e}")
                return None

    def get_estimatedbills(
            self,
            id: Optional[int] = None,
            name: Optional[str] = None,
            category: Optional[str] = None,
            from_date: Optional[datetime] = None,
            to_date: Optional[datetime] = None,
            row_num: Optional[int] = None,
    ) -> list[EstimatedBills]:
        """Get estimated_bills with optional filters



        Returns:
            List of matching EstimatedBills (empty list if no matches or no filters provided)
        """

        if from_date and to_date and from_date >= to_date:
            logging.error("from_date should be less than to_date")
            return []

        if name is not None:
            name = name.lower().strip()

        if category is not None:
            category = category.lower().strip()

        with self.Session() as session:
                try:
                    query = session.query(EstimatedBills).order_by(EstimatedBills.from_date.desc())
                    if id:
                        query = query.filter_by(id=id)

                    if name:
                        query = query.filter_by(name=name)

                    if category:
                        query = query.filter_by(category=category)

                    if from_date:
                        query = query.filter(EstimatedBills.from_date >= from_date)
                        a = len(query.all())

                    if to_date:
                        query = query.filter(EstimatedBills.from_date <= to_date)
                        b = query.all()

                    if row_num:
                        query = query.limit(row_num)

                    result = query.all()
                    logging.info(f"Found {len(result)} estimated_bills")

                    return cast(list[EstimatedBills], result)

                except Exception as e:
                    session.rollback()
                    logging.error(f"Error fetching estimated_bills: {str(e)}")
                    return []


    def edit_estimatedbills(self, estimated_bills:EstimatedBills) -> Optional[EstimatedBills]:
        """
        Updates an existing estimated_bills in the database.

        Args:
            estimated_bills: The EstimatedBills object with updated values.
                         Must have valid ID.

        Returns:
    The updated EstimatedBills if successful, None on error.
        """

        fields_to_process = ['name', "category"]
        for field in fields_to_process:
            value = getattr(estimated_bills, field, None)
            if isinstance(value, str):
                setattr(estimated_bills, field, value.strip().lower())

        if estimated_bills.from_date and estimated_bills.to_date:
            if estimated_bills.from_date >= estimated_bills.to_date:
                logging.error("from date should be less than to date ")
                return None

        with self.Session() as session:
            try:
                existing_overlap = session.query(EstimatedBills).filter(
                    EstimatedBills.id != estimated_bills.id,
                    EstimatedBills.category == estimated_bills.category,
                    EstimatedBills.from_date < estimated_bills.to_date,
                    EstimatedBills.to_date > estimated_bills.from_date
                ).first()

                if existing_overlap:
                    logging.error(f"Time overlap with existing estimated_bills (ID: {existing_overlap.id})")
                    return None


                new_estimated_bill  = session.merge(estimated_bills)
                session.commit()
                session.refresh(new_estimated_bill)
                logging.info(f"Successfully updated estimated_bills")
                return new_estimated_bill
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to update estimated_bills : {e}")
                return None

    def delete_estimatedbills(self, estimated_bills:EstimatedBills) -> bool:
        """
        Deletes a EstimatedBills.
        Returns True if deleted, False otherwise.
        """

        if not estimated_bills.id:
            logging.error("Cannot delete estimated_bills record without ID.")
            return False

        with self.Session() as session:

            try:
                the_estimated_bill = session.get(EstimatedBills, estimated_bills.id)
                if the_estimated_bill:
                    session.delete(the_estimated_bill)
                    session.commit()
                    logging.info(f"Deleted estimated_bills with ID: {estimated_bills.id}")
                    return True
                else:
                    logging.warning(f"estimated_bills with ID {estimated_bills.id} not found for deletion.")
                    return False
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete estimated_bills {estimated_bills.id}: {e}")
                return False





    #--TargetPositionAndSalary--

    def add_targetpositionandsalary(self,
                          position: str,
                           category: str,
                          from_date: datetime,
                          to_date: datetime,
                          monthly_hr: Optional[float] = None,
                          monthly_payment: Optional[float] = None,
                          monthly_insurance: Optional[float] = None,
                          extra_hr_payment: Optional[float] = None,
                    ) -> Optional[TargetPositionAndSalary]:

        """ adding new record to db  """

        if monthly_hr is not None and monthly_hr < 0:
            logging.error("Total amount can not be negative")
            return None

        if monthly_payment is not None and monthly_payment < 0:
            logging.error("Total amount can not be negative")
            return None

        if monthly_insurance is not None and monthly_insurance < 0:
            logging.error("Total amount can not be negative")
            return None

        if extra_hr_payment is not None and extra_hr_payment < 0:
            logging.error("Total amount can not be negative")
            return None

        if from_date >= to_date:
            logging.error("from date should be less than to date ")
            return None

        if position is not None:
            position = position.lower().strip()

        if category is not None:
            category = category.lower().strip()

        with self.Session() as session:
            try:

                existing_overlap = session.query(TargetPositionAndSalary).filter(
                    TargetPositionAndSalary.position == position,
                    TargetPositionAndSalary.from_date < to_date,
                    TargetPositionAndSalary.to_date > from_date
                ).first()

                if existing_overlap:
                    logging.error(f"Time overlap with existing position ID: {existing_overlap.id}) "
                                  f"from {existing_overlap.from_date} to {existing_overlap.to_date}")
                    return None


                new_one = TargetPositionAndSalary(
                    position=position,
                    category=category,
                    from_date=from_date,
                    to_date=to_date,
                    monthly_hr=monthly_hr,
                    monthly_payment=monthly_payment,
                    monthly_insurance=monthly_insurance,
                    extra_hr_payment=extra_hr_payment,
                )
                session.add(new_one)
                session.commit()
                session.refresh(new_one)
                logging.info("added successfully")
                return new_one
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to add TargetPositionAndSalary to the database: {e}")
                return None

    def get_targetpositionandsalary(
            self,
            id: Optional[int] = None,
            position: Optional[str] = None,
            category: Optional[str] = None,
            from_date: Optional[datetime] = None,
            to_date: Optional[datetime] = None,
            row_num: Optional[int] = None,
    ) -> list[TargetPositionAndSalary]:
        """Get with optional filters



        Returns:
            List of matching Objects (empty list if no matches or no filters provided)
        """

        if from_date and to_date and from_date >= to_date:
            logging.error("from_date should be less than to_date")
            return []

        if position is not None:
            position = position.lower().strip()

        if category is not None:
            category = category.lower().strip()

        with self.Session() as session:
                try:
                    query = session.query(TargetPositionAndSalary).order_by(TargetPositionAndSalary.from_date.desc())
                    if id:
                        query = query.filter_by(id=id)

                    if position:
                        query = query.filter_by(position=position)

                    if category:
                        query = query.filter_by(category=category)

                    if from_date:
                        query = query.filter(TargetPositionAndSalary.from_date >= from_date)
                        a=len(query.all())

                    if to_date:
                        query = query.filter(TargetPositionAndSalary.from_date <= to_date)
                        b=len(query.all())

                    if row_num:
                        query = query.limit(row_num)

                    result = query.all()
                    logging.info(f"Found {len(result)}")

                    return cast(list[TargetPositionAndSalary], result)

                except Exception as e:
                    session.rollback()
                    logging.error(f"Error fetching TargetPositionAndSalary: {str(e)}")
                    return []


    def edit_targetpositionandsalary(self,
                                     target_position_and_salary:TargetPositionAndSalary
                                     ) -> Optional[TargetPositionAndSalary]:
        """
        Updates an existing Object in the database.

        Args:
            target_position_and_salary: The TargetPositionAndSalary object with updated values.
                         Must have valid ID.

        Returns:
    The updated Object if successful, None on error.
        """

        fields_to_process = ['position', "category"]
        for field in fields_to_process:
            value = getattr(target_position_and_salary, field, None)
            if isinstance(value, str):
                setattr(target_position_and_salary, field, value.strip().lower())

        if target_position_and_salary.from_date and target_position_and_salary.to_date:
            if target_position_and_salary.from_date >= target_position_and_salary.to_date:
                logging.error("from date should be less than to date ")
                return None

        with self.Session() as session:
            try:
                existing_overlap = session.query(TargetPositionAndSalary).filter(
                    TargetPositionAndSalary.id != target_position_and_salary.id,
                    TargetPositionAndSalary.position == target_position_and_salary.position,
                    TargetPositionAndSalary.from_date < target_position_and_salary.to_date,
                    TargetPositionAndSalary.to_date > target_position_and_salary.from_date
                ).first()

                if existing_overlap:
                    logging.error(f"`Time overlap with existing (ID: {existing_overlap.id})")
                    return None


                merged  = session.merge(target_position_and_salary)
                session.commit()
                session.refresh(merged)
                logging.info(f"Successfully updated")
                return merged
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to update TargetPositionAndSalary : {e}")
                return None

    def delete_targetpositionandsalary(self, target_position_and_salary:TargetPositionAndSalary) -> bool:
        """
        Deletes a Object from the database.
        Returns True if deleted, False otherwise.
        """

        if not target_position_and_salary.id:
            logging.error("Cannot delete Object record without ID.")
            return False

        with self.Session() as session:

            try:
                obj = session.get(TargetPositionAndSalary, target_position_and_salary.id)
                if obj:
                    session.delete(obj)
                    session.commit()
                    logging.info(f"Deleted successfully")
                    return True
                else:
                    logging.warning(f"incorrect ID.")
                    return False
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete TargetPositionAndSalary {target_position_and_salary.id}: {e}")
                return False






    #--Shift--

    def add_shift(self,
                            date: datetime,
                          from_hr: time,
                          to_hr: time,
                          name: Optional[str] = None,
                          lunch_payment: Optional[float] = None,
                          service_payment: Optional[float] = None,
                          extra_payment: Optional[float] = None,
                          description: Optional[str] = None,
                    ) -> Optional[Shift]:

        """ adding new record to db  """

        if lunch_payment is not None and lunch_payment < 0:
            logging.error("Total amount can not be negative")
            return None

        if service_payment is not None and service_payment < 0:
            logging.error("Total amount can not be negative")
            return None

        if extra_payment is not None and extra_payment < 0:
            logging.error("Total amount can not be negative")
            return None

        if from_hr >= to_hr:
            logging.error("from date should be less than to time ")
            return None

        if name is not None:
            name = name.lower().strip()

        with self.Session() as session:
            try:

                # existing_overlap = session.query(Shift).filter(
                #     Shift.date == date,
                #     Shift.from_hr < to_hr,  # CORRECT - Proper overlap detection
                #     Shift.to_hr > from_hr  # CORRECT - Check if existing shift ends after new shift starts
                # ).first()
                #
                # if existing_overlap:
                #     logging.error(f"Time overlap with existing shift ID: {existing_overlap.id}) "
                #                   f"from {existing_overlap.from_hr} to {existing_overlap.to_hr}")
                #     return None


                new_one = Shift(
                    date=date,
                    from_hr=from_hr,
                    to_hr=to_hr,
                    name=name,
                    lunch_payment=lunch_payment,
                    service_payment=service_payment,
                    extra_payment=extra_payment,
                    description=description,
                )
                session.add(new_one)
                session.commit()
                session.refresh(new_one)
                logging.info("added successfully")
                return new_one
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to add Shift to the database: {e}")
                return None
    #problem datetime time hr
    def get_shift(
            self,
            id: Optional[int] = None,
            name: Optional[str] = None,
            from_date: Optional[datetime] = None,
            to_date: Optional[datetime] = None,
            date: Optional[datetime] = None,
            from_hr: Optional[time] = None,
            to_hr: Optional[time] = None,
            row_num: Optional[int] = None,
    ) -> list[Shift]:
        """Get with optional filters



        Returns:
            List of matching Objects (empty list if no matches or no filters provided)
        """

        if from_date and to_date and from_date >= to_date:
            logging.error("from_date should be less than to_date")
            return []
        if from_hr and to_hr and from_hr >= to_hr:
            logging.error("from_hr should be less than to_hr")
            return []

        if name is not None:
            name = name.lower().strip()

        with self.Session() as session:
                try:
                    query = session.query(Shift).order_by(Shift.date.desc())
                    if id:
                        query = query.filter_by(id=id)

                    if name:
                        query = query.filter_by(name=name)


                    if from_date:
                        query = query.filter(Shift.date >= from_date)

                    if to_date:
                        query = query.filter(Shift.date <= to_date)

                    if date:
                        query = query.filter(Shift.date == date)


                    if from_hr and to_hr:
                        query = query.filter(
                            Shift.from_hr < to_hr,  # Shift starts before the end of search window
                            Shift.to_hr > from_hr  # Shift ends after the start of search window
                        )


                    elif from_hr:
                        query = query.filter(Shift.from_hr >= from_hr)



                    elif to_hr:
                        query = query.filter(Shift.from_hr <= to_hr)


                    if row_num:
                        query = query.limit(row_num)

                    result = query.all()
                    logging.info(f"Found {len(result)}")

                    return cast(list[Shift], result)

                except Exception as e:
                    session.rollback()
                    logging.error(f"Error fetching Shift: {str(e)}")
                    return []


    def edit_shift(self,
                                     shift:Shift
                                     ) -> Optional[Shift]:
        """
        Updates an existing Object in the database.

        Args:
            shift: The Shift object with updated values.
                         Must have valid ID.

        Returns:
        The updated Object if successful, None on error.
        """

        fields_to_process = ['name']
        for field in fields_to_process:
            value = getattr(shift, field, None)
            if isinstance(value, str):
                setattr(shift, field, value.strip().lower())


        if shift.from_hr and shift.to_hr:
            if shift.from_hr >= shift.to_hr:
                logging.error("from hr should be less than to hr ")
                return None

        with self.Session() as session:
            try:
                # existing_overlap = session.query(Shift).filter(
                #     Shift.id != shift.id,
                #     Shift.date == shift.date,
                #     Shift.from_hr < shift.to_hr,
                #     Shift.to_hr > shift.from_hr
                # ).first()
                #
                # if existing_overlap:
                #     logging.error(f"`Time overlap with existing (ID: {existing_overlap.id})")
                #     return None


                merged  = session.merge(shift)
                session.commit()
                session.refresh(merged)
                logging.info(f"Successfully updated")
                return merged
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to update Shift : {e}")
                return None

    def delete_shift(self, shift:Shift) -> bool:
        """
        Deletes an Object from the database.
        Returns True if deleted, False otherwise.
        """

        if not shift.id:
            logging.error("Cannot delete Object record without ID.")
            return False

        with self.Session() as session:

            try:
                obj = session.get(Shift, shift.id)
                if obj:
                    session.delete(obj)
                    session.commit()
                    logging.info(f"Deleted successfully")
                    return True
                else:
                    logging.warning(f"incorrect ID.")
                    return False
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete Shift {shift.id}: {e}")
                return False





    #--EstimatedLabor--

    def add_estimatedlabor(self,
                            position_id: int,
                          shift_id: int,
                          number: int,
                    ) -> Optional[EstimatedLabor]:

        """ adding new record to db  """

        if number is not None and number < 0:
            logging.error("Total amount can not be negative")
            return None

        with self.Session() as session:
            try:
                exist_shift = session.get(Shift, shift_id)
                if not exist_shift:
                    logging.error(f"Shift {shift_id} does not exist")
                    return None
                exist = session.get(TargetPositionAndSalary, position_id)
                if not exist:
                    logging.error(f"Position  {position_id} does not exist")
                    return None

                new_one = EstimatedLabor(
                    position_id=position_id,
                    shift_id=shift_id,
                    number=number,
                )
                session.add(new_one)
                session.commit()
                session.refresh(new_one)
                logging.info("added successfully")
                return new_one
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to add EstimatedLabor  to the database: {e}")
                return None

    def get_estimatedlabor(
            self,
            position_id: Optional[int]=None,
            shift_id: Optional[int]=None,
            row_num: Optional[int] = None,
    ) -> list[EstimatedLabor]:
        """Get with optional filters
        Returns:
            List of matching Objects (empty list if no matches or no filters provided)
        """

        with self.Session() as session:
                try:
                    query = session.query(EstimatedLabor).order_by(EstimatedLabor.time_create.desc())
                    if position_id:
                        query = query.filter_by(position_id=position_id)

                    if shift_id:
                        query = query.filter_by(shift_id=shift_id)

                    if row_num:
                        query = query.limit(row_num)

                    result = query.all()
                    logging.info(f"Found {len(result)}")

                    return cast(list[EstimatedLabor], result)

                except Exception as e:
                    session.rollback()
                    logging.error(f"Error fetching EstimatedLabor: {str(e)}")
                    return []


    def edit_estimatedlabor(self,
                                     labor:EstimatedLabor
                                     ) -> Optional[EstimatedLabor]:
        """
        Updates an Object in the database.

        Args:
            labor: The EstimatedLabor object with updated values.
                         Must have valid ID.

        Returns:
        The updated EstimatedLabor  if successful, None on error.
        """
        if not labor.position_id or not labor.shift_id:
            logging.error("can update object without ids")
            return None

        key = (labor.position_id, labor.shift_id)

        with self.Session() as session:
            try:
                existing = session.get(EstimatedLabor, key)
                if not existing:
                    logging.error(f"EstimatedLabor {key} does not exist")
                    return None

                merged  = session.merge(labor)
                session.commit()
                session.refresh(merged)
                logging.info(f"Successfully updated")
                return merged
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to update EstimatedLabor : {e}")
                return None

    def delete_estimatedlabor(self, labor:EstimatedLabor) -> bool:
        """
        Deletes an Object from the database.
        Returns True if deleted, False otherwise.
        """

        if not labor.position_id or not labor.shift_id:
            logging.error("Cannot delete Object record without ID.")
            return False
        key = (labor.position_id, labor.shift_id)
        with self.Session() as session:

            try:
                obj = session.get(EstimatedLabor, key)
                if obj:
                    session.delete(obj)
                    session.commit()
                    logging.info(f"Deleted successfully")
                    return True
                else:
                    logging.warning(f"incorrect ID.")
                    return False
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete EstimatedLabor {key}: {e}")
                return False


    #--Equipment--

    def add_equipment(self,
                      name: str,
                      category: Optional[str] = None,
                      number: Optional[int] = 1,
                      purchase_date: Optional[datetime] = None,
                      purchase_price: Optional[float] = None,
                      payer: Optional[str] = None,
                      in_use: bool = True,
                      expire_date: Optional[datetime] = None,
                      monthly_depreciation: Optional[float] = None,
                      description: Optional[str] = None,
                      ) -> Optional[Equipment]:

        """ adding new record to db  """

        if purchase_price is not None and purchase_price < 0:
            logging.error("Total amount can not be negative")
            return None

        if monthly_depreciation is not None and monthly_depreciation < 0:
            logging.error("Total amount can not be negative")
            return None

        if number is not None and number <= 0:
            logging.error("Number must be greater than zero")
            return None

        name = name.lower().strip()


        if category is not None:
            category = category.lower().strip()

        if payer is not None:
            payer = payer.lower().strip()

        with self.Session() as session:
            try:

                new_one = Equipment(
                    name=name,
                    number=number,
                    category=category,
                    purchase_date=purchase_date,
                    purchase_price=purchase_price,
                    payer=payer,
                    in_use=in_use,
                    expire_date=expire_date,
                    monthly_depreciation=monthly_depreciation,
                    description=description,
                )
                session.add(new_one)
                session.commit()
                session.refresh(new_one)
                logging.info("added successfully")
                return new_one
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to add Equipment to the database: {e}")
                return None
    #problem datetime time hr
    def get_equipment(
            self,
            id: Optional[int] = None,
            name: Optional[str] = None,
            category: Optional[str] = None,
            payer: Optional[str] = None,
            from_date: Optional[datetime] = None,
            to_date: Optional[datetime] = None,
            date_expire: Optional[bool] = None,
            in_use: Optional[bool] = None,
            row_num: Optional[int] = None,
    ) -> list[Equipment]:
        """Get with optional filters
        Returns:
            List of matching Objects (empty list if no matches or no filters provided)
        """

        if from_date and to_date and from_date >= to_date:
            logging.error("from_date should be less than to_date")
            return []

        if name is not None:
            name = name.lower().strip()

        if category is not None:
            category = category.lower().strip()

        if payer is not None:
            payer = payer.lower().strip()

        with self.Session() as session:
                try:
                    query = session.query(Equipment).order_by(Equipment.time_create.desc())
                    if id:
                        query = query.filter_by(id=id)

                    if name:
                        query = query.filter_by(name=name)

                    if category:
                        query = query.filter_by(category=category)

                    if payer:
                        query = query.filter_by(payer=payer)

                    if date_expire:
                        if from_date:
                            query = query.filter(Equipment.expire_date >= from_date)

                        if to_date:
                            query = query.filter(Equipment.purchase_date <= to_date)
                    else:
                        if from_date:
                            query = query.filter(Equipment.purchase_date >= from_date)

                        if to_date:
                            query = query.filter(Equipment.purchase_date <= to_date)


                    if in_use is not None:
                        query = query.filter_by(in_use=in_use)
                    if row_num:
                        query = query.limit(row_num)

                    result = query.all()
                    logging.info(f"Found {len(result)}")

                    return cast(list[Equipment], result)

                except Exception as e:
                    session.rollback()
                    logging.error(f"Error fetching Equipment: {str(e)}")
                    return []


    def edit_equipment(self,
                                     equipment:Equipment
                                     ) -> Optional[Equipment]:
        """
        Args:
            equipment: The Equipment object with updated values.
                             Must have valid ID.

        Returns:
        The updated Equipment if successful, None on error.
        """
        if not equipment.id:
            logging.error("Cannot update equipment without ID")
            return None

        fields_to_process = ['name', "category", "payer"]
        for field in fields_to_process:
            value = getattr(equipment, field, None)
            if isinstance(value, str):
                setattr(equipment, field, value.strip().lower())

        with self.Session() as session:
            try:
                merged  = session.merge(equipment)
                session.commit()
                session.refresh(merged)
                logging.info(f"Successfully updated")
                return merged
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to update equipment : {e}")
                return None

    def delete_equipment(self, equipment:Equipment) -> bool:
        """
        Deletes an Object from the database.
        Returns True if deleted, False otherwise.
        """

        if not equipment.id:
            logging.error("Cannot delete Equipment without ID")
            return False

        with self.Session() as session:

            try:
                obj = session.get(Equipment, equipment.id)
                if obj:
                    session.delete(obj)
                    session.commit()
                    logging.info(f"Deleted equipment ID: {equipment.id}")
                    return True
                else:
                    logging.warning(f"Equipment with ID {equipment.id} not found")
                    return False
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete Equipment {equipment.id}: {e}")
                return False



    #--Rent--

    def add_rent(self,
                      name: str,
                      rent: Optional[float] = None,
                      mortgage: Optional[float] = None,
                      mortgage_percentage_to_rent: Optional[float] = None,
                      from_date: Optional[datetime] = None,
                      to_date: Optional[datetime] = None,
                      payer: Optional[str] = None,
                      description: Optional[str] = None,
                      ) -> Optional[Rent]:

        """ adding new record to db  """

        if rent is not None and rent < 0:
            logging.error("Total amount can not be negative")
            return None

        if mortgage is not None and mortgage < 0:
            logging.error("Total amount can not be negative")
            return None

        if mortgage_percentage_to_rent is not None and not 0<= mortgage_percentage_to_rent <= 1:
            logging.error("Number must be between 0 and 1")
            return None

        name = name.lower().strip()

        if payer is not None:
            payer = payer.lower().strip()

        with self.Session() as session:
            try:

                new_one = Rent(
                    name=name,
                    rent=rent,
                    mortgage=mortgage,
                    mortgage_percentage_to_rent=mortgage_percentage_to_rent,
                    from_date=from_date,
                    to_date=to_date,
                    payer=payer,
                    description=description,
                )
                session.add(new_one)
                session.commit()
                session.refresh(new_one)
                logging.info("added successfully")
                return new_one
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to add Rent to the database: {e}")
                return None

    def get_rent(
            self,
            id: Optional[int] = None,
            name: Optional[str] = None,
            payer: Optional[str] = None,
            from_date: Optional[datetime] = None,
            to_date: Optional[datetime] = None,
            row_num: Optional[int] = None,
    ) -> list[Rent]:
        """Get with optional filters
        Returns:
            List of matching Objects (empty list if no matches or no filters provided)
        """

        if from_date and to_date and from_date >= to_date:
            logging.error("from_date should be less than to_date")
            return []

        if payer is not None:
            payer = payer.lower().strip()
        if name is not None:
            name = name.lower().strip()

        with self.Session() as session:
                try:
                    query = session.query(Rent).order_by(Rent.time_create.desc())
                    if id:
                        query = query.filter_by(id=id)


                    if name:
                        query = query.filter_by(name=name)

                    if payer:
                        query = query.filter_by(payer=payer)

                    if from_date:
                        query = query.filter(Rent.from_date >= from_date)

                    if to_date:
                        query = query.filter(Rent.from_date <= to_date)

                    if row_num:
                        query = query.limit(row_num)

                    result = query.all()
                    logging.info(f"Found {len(result)}")

                    return cast(list[Rent], result)

                except Exception as e:
                    session.rollback()
                    logging.error(f"Error fetching Rent: {str(e)}")
                    return []


    def edit_rent(self,
                                     rent:Rent
                                     ) -> Optional[Rent]:
        """
        Args:
            rent: The Rent object with updated values.

        Returns:
        The updated Rent if successful, None on error.
        """
        if not rent.id:
            logging.error("Cannot update rent without ID")
            return None

        fields_to_process = ["name", "payer"]
        for field in fields_to_process:
            value = getattr(rent, field, None)
            if isinstance(value, str):
                setattr(rent, field, value.strip().lower())

        with self.Session() as session:
            try:
                merged  = session.merge(rent)
                session.commit()
                session.refresh(merged)
                logging.info(f"Successfully updated")
                return merged
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to update rent : {e}")
                return None

    def delete_rent(self, rent:Rent) -> bool:
        """
        Deletes an Object from the database.
        Returns True if deleted, False otherwise.
        """

        if not rent.id:
            logging.error("Cannot delete rent without ID")
            return False

        with self.Session() as session:

            try:
                obj = session.get(Rent, rent.id)
                if obj:
                    session.delete(obj)
                    session.commit()
                    logging.info(f"Deleted rent ID: {rent.id}")
                    return True
                else:
                    logging.warning(f"rent with ID {rent.id} not found")
                    return False
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete rent {rent.id}: {e}")
                return False




    #--Personal--

    def add_personal(self,
                      first_name: Optional[str] = None,
                      last_name: Optional[str] = None,
                      nationality_code: Optional[str] = None,
                      email: Optional[str] = None,
                      phone: Optional[str] = None,
                      address: Optional[str] = None,
                      hire_date: Optional[datetime] = None,
                      position: Optional[str] = None,
                      active: Optional[bool] = None,
                      description: Optional[str] = None,
                      ) -> Optional[Personal]:

        """ adding new record to db  """

        if first_name is not None:
            first_name = first_name.lower().strip()

        if last_name is not None:
            last_name = last_name.lower().strip()

        if position is not None:
            position = position.lower().strip()

        if nationality_code is not None:
            nationality_code = nationality_code.lower().strip()

        with self.Session() as session:
            try:

                new_one = Personal(
                    first_name=first_name,
                    last_name=last_name,
                    nationality_code=nationality_code,
                    email=email,
                    phone=phone,
                    address=address,
                    hire_date=hire_date,
                    position=position,
                    active=active,
                    description=description,
                )
                session.add(new_one)
                session.commit()
                session.refresh(new_one)
                logging.info("added successfully")
                return new_one
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to add personal to the database: {e}")
                return None

    def get_personal(
            self,
            id: Optional[int] = None,
            first_name: Optional[str] = None,
            last_name: Optional[str] = None,
            nationality_code: Optional[str] = None,
            position: Optional[str] = None,
            from_date: Optional[datetime] = None,
            to_date: Optional[datetime] = None,
            active: Optional[bool] = None,
            row_num: Optional[int] = None,
    ) -> list[Personal]:
        """Get with optional filters
        Returns:
            List of matching Objects (empty list if no matches or no filters provided)
        """

        if from_date and to_date and from_date >= to_date:
            logging.error("from_date should be less than to_date")
            return []

        if first_name is not None:
            first_name = first_name.lower().strip()

        if last_name is not None:
            last_name = last_name.lower().strip()

        if position is not None:
            position = position.lower().strip()

        if nationality_code is not None:
            nationality_code = nationality_code.lower().strip()

        with self.Session() as session:
                try:
                    query = session.query(Personal).order_by(Personal.time_create.desc())
                    if id:
                        query = query.filter_by(id=id)


                    if first_name:
                        query = query.filter_by(first_name=first_name)

                    if last_name:
                        query = query.filter_by(last_name=last_name)

                    if position:
                        query = query.filter_by(position=position)

                    if nationality_code:
                        query = query.filter_by(nationality_code=nationality_code)

                    if active is not None:
                        query = query.filter_by(active=active)

                    if from_date:
                        query = query.filter(Personal.hire_date >= from_date)

                    if to_date:
                        query = query.filter(Personal.hire_date <= to_date)

                    if row_num:
                        query = query.limit(row_num)

                    result = query.all()
                    logging.info(f"Found {len(result)}")

                    return cast(list[Personal], result)

                except Exception as e:
                    session.rollback()
                    logging.error(f"Error fetching Personal: {str(e)}")
                    return []


    def edit_personal(self,
                                     personal:Personal
                                     ) -> Optional[Personal]:
        """
        Args:
            personal: The personal object with updated values.

        Returns:
        The updated Personal if successful, None on error.
        """
        if not personal.id:
            logging.error("Cannot update personal without ID")
            return None

        fields_to_process = ["first_name", "last_name", "position", "nationality_code"]
        for field in fields_to_process:
            value = getattr(personal, field, None)
            if isinstance(value, str):
                setattr(personal, field, value.strip().lower())

        with self.Session() as session:
            try:
                existing = session.get(Personal, personal.id)
                if not existing:
                    logging.error(f"No personal found with ID: {personal.id}")
                    return None
                merged  = session.merge(personal)
                session.commit()
                session.refresh(merged)
                logging.info(f"Successfully updated")
                return merged
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to update personal : {e}")
                return None

    def delete_personal(self, personal:Personal) -> bool:
        """
        Deletes an Object from the database.
        Returns True if deleted, False otherwise.
        """

        if not personal.id:
            logging.error("Cannot delete personal without ID")
            return False

        with self.Session() as session:

            try:
                obj = session.get(Personal, personal.id)
                if obj:
                    session.delete(obj)
                    session.commit()
                    logging.info(f"Deleted personal ID: {personal.id}")
                    return True
                else:
                    logging.warning(f"personal with ID {personal.id} not found")
                    return False
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete personal {personal.id}: {e}")
                return False





    #--WorkShiftRecord--

    def add_workshiftrecord(self,
                      personal_id: int,
                      date: Optional[datetime] = None,
                      start_hr: Optional[time] = None,
                      end_hr: Optional[time] = None,
                      worked_hr: Optional[float] = None,
                      lunch_payed: Optional[float] = None,
                      service_payed: Optional[float] = None,
                      extra_payed: Optional[float] = None,
                      description: Optional[str] = None,
                      ) -> Optional[WorkShiftRecord]:

        """ adding new record to db  """

        if worked_hr is not None and worked_hr < 0:
            logging.error('Value cannot be negative')
            return None

        if lunch_payed is not None and lunch_payed < 0:
            logging.error('Value cannot be negative')
            return None

        if service_payed is not None and service_payed < 0:
            logging.error('Value cannot be negative')
            return None

        if extra_payed is not None and extra_payed < 0:
            logging.error('Value cannot be negative')
            return None

        if start_hr and end_hr and start_hr > end_hr:
            logging.error("start time can not be later than end time")
            return None


        with self.Session() as session:
            try:
                existence = session.get(Personal, personal_id)
                if not existence:
                    logging.error("This personal id does not exist")
                    return None

                over_lap = session.query(WorkShiftRecord).filter(
                    WorkShiftRecord.personal_id == personal_id,
                    WorkShiftRecord.date == date,
                    WorkShiftRecord.start_hr < end_hr,
                    WorkShiftRecord.end_hr > start_hr
                ).first()
                if over_lap:
                    logging.error("this time overlaps with other record of this person")
                    return None

                new_one = WorkShiftRecord(
                    personal_id=personal_id,
                    date=date,
                    start_hr=start_hr,
                    end_hr=end_hr,
                    worked_hr=worked_hr,
                    lunch_payed=lunch_payed,
                    service_payed=service_payed,
                    extra_payed=extra_payed,
                    description=description,

                )
                session.add(new_one)
                session.commit()
                session.refresh(new_one)
                logging.info("added successfully")
                return new_one
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to add WorkShiftRecord to the database: {e}")
                return None

    def get_workshiftrecord(
            self,
            id: Optional[int] = None,
            personal_id: Optional[int] = None,
            from_hr: Optional[time] = None,
            to_hr: Optional[time] = None,
            from_date: Optional[datetime] = None,
            to_date: Optional[datetime] = None,
            row_num: Optional[int] = None,
    ) -> list[WorkShiftRecord]:
        """Get with optional filters
        Returns:
            List of matching Objects (empty list if no matches or no filters provided)
        """

        if from_date and to_date and from_date >= to_date:
            logging.error("from_date should be less than to_date")
            return []
        if from_hr and to_hr and from_hr >= to_hr:
            logging.error("from_hr should be less than to_hr")
            return []

        with self.Session() as session:
                try:
                    query = session.query(WorkShiftRecord).order_by(WorkShiftRecord.date.desc())
                    if id:
                        query = query.filter_by(id=id)


                    if personal_id:
                        query = query.filter_by(personal_id=personal_id)


                    if from_hr:
                        query = query.filter(WorkShiftRecord.start_hr >= from_hr)

                    if to_hr:
                        query = query.filter(WorkShiftRecord.start_hr <= to_hr)

                    if from_date:
                        query = query.filter(WorkShiftRecord.date >= from_date)

                    if to_date:
                        query = query.filter(WorkShiftRecord.date <= to_date)

                    if row_num:
                        query = query.limit(row_num)

                    result = query.all()
                    logging.info(f"Found {len(result)}")

                    return cast(list[WorkShiftRecord], result)

                except Exception as e:
                    session.rollback()
                    logging.error(f"Error fetching WorkShiftRecord: {str(e)}")
                    return []


    def edit_workshiftrecord(self,
                                     working_shift_record:WorkShiftRecord
                                     ) -> Optional[WorkShiftRecord]:
        """
        Args:
            working_shift_record: The personal object with updated values.

        Returns:
        The updated WorkShiftRecord if successful, None on error.
        """
        if not working_shift_record.id:
            logging.error("Cannot update working_shift_record without ID")
            return None

        # fields_to_process = ["first_name", "last_name", "position", "nationality_code"]
        # for field in fields_to_process:
        #     value = getattr(working_shift_record, field, None)
        #     if isinstance(value, str):
        #         setattr(working_shift_record, field, value.strip().lower())

        with self.Session() as session:
            try:
                existing = session.get(WorkShiftRecord, working_shift_record.id)
                if not existing:
                    logging.error(f"No working_shift_record found with ID: {working_shift_record.id}")
                    return None
                over_lap = session.query(WorkShiftRecord).filter(
                    WorkShiftRecord.id != working_shift_record.id,
                    WorkShiftRecord.personal_id == working_shift_record.personal_id,
                    WorkShiftRecord.date == working_shift_record.date,
                    WorkShiftRecord.start_hr < working_shift_record.end_hr,
                    WorkShiftRecord.end_hr > working_shift_record.start_hr
                ).first()
                if over_lap:
                    logging.error("this time overlaps with other record of this person")
                    return None
                merged  = session.merge(working_shift_record)
                session.commit()
                session.refresh(merged)
                logging.info(f"Successfully updated")
                return merged
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to update WorkShiftRecord : {e}")
                return None

    def delete_workshiftrecord(self, working_shift_record:WorkShiftRecord) -> bool:
        """
        Deletes a WorkShiftRecord from the database.
        Returns True if deleted, False otherwise.
        """

        if not working_shift_record.id:
            logging.error("Cannot delete WorkShiftRecord without ID")
            return False

        with self.Session() as session:

            try:
                obj = session.get(WorkShiftRecord, working_shift_record.id)
                if obj:
                    session.delete(obj)
                    session.commit()
                    logging.info(f"Deleted working_shift_record ID: {working_shift_record.id}")
                    return True
                else:
                    logging.warning(f"working_shift_record with ID {working_shift_record.id} not found")
                    return False
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete working_shift_record {working_shift_record.id}: {e}")
                return False




    #--RecordEmployeePayment--

    def add_recordemployeepayment(self,
                      personal_id: int,
                      from_date: Optional[datetime] = None,
                      to_date: Optional[datetime] = None,
                      payment: Optional[float] = None,
                      insurance: Optional[float] = None,
                      work_hr: Optional[float] = None,
                      extra_hr: Optional[float] = None,
                      extra_expenses: Optional[float] = None,
                      description: Optional[str] = None,
                      ) -> Optional[RecordEmployeePayment]:

        """ adding new record to db  """

        if work_hr is not None and work_hr < 0:
            logging.error('Value cannot be negative')
            return None

        if extra_hr is not None and extra_hr < 0:
            logging.error('Value cannot be negative')
            return None

        if payment is not None and payment < 0:
            logging.error('Value cannot be negative')
            return None

        if insurance is not None and insurance < 0:
            logging.error('Value cannot be negative')
            return None

        if extra_expenses is not None and extra_expenses < 0:
            logging.error('Value cannot be negative')
            return None

        if from_date and to_date and from_date > to_date:
            logging.error("start date can not be later than end date")
            return None


        with self.Session() as session:
            try:
                existence = session.get(Personal, personal_id)
                if not existence:
                    logging.error("This personal id does not exist")
                    return None

                over_lap = session.query(RecordEmployeePayment).filter(
                    RecordEmployeePayment.personal_id == personal_id,
                    RecordEmployeePayment.from_date < to_date,
                    RecordEmployeePayment.to_date > from_date
                ).first()
                if over_lap:
                    logging.error("this time overlaps with other record of this person")
                    return None

                new_one = RecordEmployeePayment(
                    personal_id=personal_id,
                    from_date=from_date,
                    to_date=to_date,
                    payment=payment ,
                    insurance=insurance ,
                    work_hr=work_hr ,
                    extra_hr=extra_hr ,
                    extra_expenses=extra_expenses,
                    description=description,

                )
                session.add(new_one)
                session.commit()
                session.refresh(new_one)
                logging.info("added successfully")
                return new_one
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to add RecordEmployeePayment to the database: {e}")
                return None

    def get_recordemployeepayment(
            self,
            id: Optional[int] = None,
            personal_id: Optional[int] = None,
            from_date: Optional[datetime] = None,
            to_date: Optional[datetime] = None,
            row_num: Optional[int] = None,
    ) -> list[RecordEmployeePayment]:
        """Get with optional filters
        Returns:
            List of matching Objects (empty list if no matches or no filters provided)
        """

        if from_date and to_date and from_date >= to_date:
            logging.error("from_date should be less than to_date")
            return []

        with self.Session() as session:
                try:
                    query = session.query(RecordEmployeePayment).order_by(RecordEmployeePayment.time_create.desc())
                    if id:
                        query = query.filter_by(id=id)
                    if personal_id:
                        query = query.filter_by(personal_id=personal_id)

                    if from_date:
                        query = query.filter(RecordEmployeePayment.from_date >= from_date)

                    if to_date:
                        query = query.filter(RecordEmployeePayment.from_date <= to_date)

                    if row_num:
                        query = query.limit(row_num)

                    result = query.all()
                    logging.info(f"Found {len(result)}")

                    return cast(list[RecordEmployeePayment], result)

                except Exception as e:
                    session.rollback()
                    logging.error(f"Error fetching RecordEmployeePayment: {str(e)}")
                    return []


    def edit_recordemployeepayment(self,
                                     record_employee_payment:RecordEmployeePayment
                                     ) -> Optional[RecordEmployeePayment]:
        """
        Args:
            record_employee_payment: The personal object with updated values.

        Returns:
        The updated RecordEmployeePayment if successful, None on error.
        """
        if not record_employee_payment.id:
            logging.error("Cannot update record_employee_payment without ID")
            return None

        # fields_to_process = ["first_name", "last_name", "position", "nationality_code"]
        # for field in fields_to_process:
        #     value = getattr(working_shift_record, field, None)
        #     if isinstance(value, str):
        #         setattr(working_shift_record, field, value.strip().lower())

        with self.Session() as session:
            try:
                existing = session.get(RecordEmployeePayment, record_employee_payment.id)
                if not existing:
                    logging.error(f"No record_employee_payment found with ID: {record_employee_payment.id}")
                    return None
                over_lap = session.query(RecordEmployeePayment).filter(
                    RecordEmployeePayment.id != record_employee_payment.id,
                    RecordEmployeePayment.personal_id == record_employee_payment.personal_id,
                    RecordEmployeePayment.from_date < record_employee_payment.to_date,
                    RecordEmployeePayment.to_date > record_employee_payment.from_date
                ).first()
                if over_lap:
                    logging.error("this time overlaps with other record of this person")
                    return None
                merged  = session.merge(record_employee_payment)
                session.commit()
                session.refresh(merged)
                logging.info(f"Successfully updated")
                return merged
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to update RecordEmployeePayment : {e}")
                return None

    def delete_recordemployeepayment(self, record_employee_payment:RecordEmployeePayment) -> bool:
        """
        Deletes a WorkShiftRecord from the database.
        Returns True if deleted, False otherwise.
        """

        if not record_employee_payment.id:
            logging.error("Cannot delete RecordEmployeePayment without ID")
            return False

        with self.Session() as session:

            try:
                obj = session.get(RecordEmployeePayment, record_employee_payment.id)
                if obj:
                    session.delete(obj)
                    session.commit()
                    logging.info(f"Deleted record_employee_payment ID: {record_employee_payment.id}")
                    return True
                else:
                    logging.warning(f"record_employee_payment with ID {record_employee_payment.id} not found")
                    return False
            except Exception as e:
                session.rollback()
                logging.error(f"Failed to delete record_employee_payment {record_employee_payment.id}: {e}")
                return False





db = DbHandler()
