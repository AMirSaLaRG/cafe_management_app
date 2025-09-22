from typing import Optional

from models.dbhandler import DBHandler
from models.cafe_managment_models import Inventory, Menu, Recipe, EstimatedMenuPriceRecord


class MenuService:
    def __init__(self, dbhandler: DBHandler):
        self.db = dbhandler

    def add_menu_item(self, name: str,
                      size: str,
                      category: str,
                      value_added_tax: float,
                      serving: bool = True,
                      description: str = None) -> Optional[Menu]:
        return self.db.add_menu(name=name,
                               size=size,
                               category=category,
                               value_added_tax=value_added_tax,
                               serving=serving,
                               description=description)


    def change_attribute_menu_item(self, menu_id, name: Optional[str] = None,
                                   size: Optional[str] = None,
                                   category: Optional[str] = None,
                                   value_added_tax: Optional[float] = None,
                                   description: Optional[str] = None,
                                   serving: Optional[bool] = None) -> bool:

        fetch_list = self.db.get_menu(id=menu_id)
        if not fetch_list:
            return False
        menu_item = fetch_list[0]

        if name is not None:
            menu_item.name = name
        if size is not None:
            menu_item.size = size
        if category is not None:
            menu_item.category = category
        if value_added_tax is not None:
            menu_item.value_added_tax = value_added_tax
        if description is not None:
            menu_item.description = description

        if serving is not None:
            menu_item.serving = serving

        if self.db.edit_menu(menu_item):
            return True
        return False

    def change_availability_of_menu_item(self, menu_id, switch_to:Optional[bool]=None) -> bool:
        menu_item_fetch_list = self.db.get_menu(id=menu_id)
        if not menu_item_fetch_list:
            return False
        menu_item = menu_item_fetch_list[0]
        if switch_to is None:
            switch_to = not menu_item.serving

        menu_item.serving = switch_to
        if self.db.edit_menu(menu_item):
            return True
        return False

    def delete_menu_item(self, menu_id: int) -> bool:
        menu = self.db.get_menu(id=menu_id)
        if menu:
            return self.db.delete_menu(menu[0])
        return False

    def get_menu_item(self, menu_id: int) -> Menu:
        items = self.db.get_menu(id=menu_id, with_recipe=True)
        return items[0] if items else None

    def search_menu_items(self, name: str = None, category: str = None, serving: bool = None) -> list[Menu]:
        return self.db.get_menu(name=name, category=category, serving=serving)
    def get_menu_all_available_items(self):
        return self.db.get_menu(serving=True)

    def list_menu_items(self) -> list[Menu]:
        return self.db.get_menu()

    def get_recipe_items_of_menu_item(self, menu_id:int) -> list[Inventory]:
        recipes = self.db.get_recipe(menu_id=menu_id)
        inventory_items_list = [r.inventory_item for r in recipes]
        return inventory_items_list


    def add_recipe_of_menu_item(self,
                                menu_id,
                                inventory_id,
                                amount,
                                writer,
                                note:Optional[str]=None) -> Recipe:
        return self.db.add_recipe(inventory_id=inventory_id,
                                   menu_id=menu_id,
                                   inventory_item_amount_usage=amount,
                                   writer=writer,
                                   description=note)

    def change_recipe_of_menu_item(self,
                                   menu_id,
                                   inventory_id,
                                   amount:Optional[float]=None,
                                   writer:Optional[str]=None,
                                   note:Optional[str]=None,
                                   delete:bool = False) -> bool:
        catch_recipe_list = self.db.get_recipe(menu_id=menu_id, inventory_id=inventory_id)
        if not catch_recipe_list:
            return False
        recipe = catch_recipe_list[0]

        if delete:
            if self.db.delete_recipe(recipe):
                return True
            else:
                return False

        if amount is not None:
            recipe.inventory_item_amount_usage = amount
        if writer is not None:
            recipe.writer = writer
        if note is not None:
            recipe.description = note

        if self.db.edit_recipe(recipe=recipe):
            return True
        return False

    def remove_recipe_item(self, menu_id: int, inventory_id: int) -> bool:
        recipes = self.db.get_recipe(menu_id=menu_id, inventory_id=inventory_id)
        return self.db.delete_recipe(recipes[0]) if recipes else False

    def clear_recipe(self, menu_id: int) -> bool:
        recipes = self.db.get_recipe(menu_id=menu_id)
        success = True
        for r in recipes:
            if not self.db.delete_recipe(r):
                success = False
        return success

    def clone_menu_item(self, menu_id: int, new_name: str) -> Optional[Menu]:
        menu = self.get_menu_item(menu_id)
        if not menu:
            return None
        new_menu = self.db.add_menu(
            name=new_name,
            size=menu.size,
            category=menu.category,
            value_added_tax=menu.value_added_tax,
            current_price=menu.current_price,
            serving=menu.serving,
            description=menu.description
        )
        if not new_menu:
            return None
        # Copy recipe
        for recipe in menu.recipe:
            self.add_recipe_of_menu_item(
                new_menu.id,
                recipe.inventory_id,
                recipe.inventory_item_amount_usage,
                recipe.writer,
                recipe.description
            )
        return new_menu
