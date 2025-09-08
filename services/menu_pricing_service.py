from datetime import datetime, timedelta, time
from typing import Optional

from models.dbhandler import DBHandler
from models.cafe_managment_models import Inventory, Menu, Recipe


class MenuPriceService:
    def __init__(self, db_handler: DBHandler):
        self.db = db_handler


    def _calculate_suggested_price(self, direct_cost: float, indirect_cost: float,
                              sales_forecast: int, profit_margin: float) -> Optional[float]:
        """the calculation of the estimated price to suggest it"""
        if not sales_forecast:
            return None
        if not indirect_cost:
            indirect_cost = 0
        if profit_margin < 0:
            return None
        indirect_cost = indirect_cost / sales_forecast
        direct_cost = direct_cost
        suggested_price = (indirect_cost + direct_cost ) * (1 + profit_margin)
        return suggested_price



    def _time_difference_to_float_hr(self, start:time, end:time)->float:
        today = datetime.today().date()
        dt_start = datetime.combine(today, start)
        dt_end = datetime.combine(today, end)

        if dt_end < dt_start:
            dt_end += timedelta(days=1)

        delta = dt_end - dt_start
        return delta.total_seconds() / 3600

    def _time_to_float_hr(self, time_obj: time) -> float:
        """Convert time object to float hours"""
        if not time_obj:
            return 0.0
        return time_obj.hour + time_obj.minute / 60.0 + time_obj.second / 3600.0

    #todo this looks like shit
    def _get_estimated_labor_cost(self, from_date, to_date):
        """this estimates the price of labor in shifts"""
        shifts = self.db.get_shift(from_date=from_date, to_date=to_date)
        total_labor_cost = 0

        for shift  in shifts:
            if not shift :
                continue

            # Get all labor assignments for this shift
            labor_assignments = self.db.get_estimatedlabor(shift_id=shift.id)
            for labor in labor_assignments:
                if not labor:
                    continue

                # Get the position details
                positions = self.db.get_targetpositionandsalary(id=labor.position_id)
                if not positions:
                    continue

                position = positions[0]

                # Calculate shift duration in hours
                shift_duration = self._time_difference_to_float_hr(shift.from_hr, shift.to_hr)

                # Calculate regular hours (total hours minus overtime)
                regular_hours = max(0, shift_duration - self._time_to_float_hr(labor.extra_hr))

                # Calculate overtime hours
                overtime_hours = self._time_to_float_hr(labor.extra_hr)

                # Calculate hourly rate
                if position.monthly_hr and position.monthly_hr > 0:
                    hourly_rate = position.monthly_payment / position.monthly_hr if position.monthly_payment else 0
                else:
                    hourly_rate = 0

                # Calculate overtime rate
                overtime_rate = position.extra_hr_payment if position.extra_hr_payment else hourly_rate * 1.4  # Default 1.4x for overtime

                # Normal payment for regular hours
                normal_payment = regular_hours * hourly_rate * labor.number

                # Overtime payment
                overtime_payment = overtime_hours * overtime_rate * labor.number

                # Insurance (daily pro-rata)
                daily_insurance = (position.monthly_insurance
                                   / 30) * labor.number if position.monthly_insurance else 0

                # Extra payments from shift
                extra_payment = shift.extra_payment if shift.extra_payment else 0

                # Sum for this labor assignment
                total_labor_cost += normal_payment + overtime_payment + daily_insurance + extra_payment

        return total_labor_cost




    #_____________________________menu price updaters______________________________________________
    def _add_new_estimated_record_update_menu_suggestion(self,
                                                         only_menu_id:Optional[int]=None,
                                                         direct_cost:Optional[float]=None,
                                                         indirect_cost:Optional[float]=None,
                                                         sales_forecast:Optional[int]=None,
                                                         profit_margin:Optional[float]=None,
                                                         manual_price:Optional[float]=None,
                                                         category:Optional[str]=None,
                                                         description:Optional[str]=None) -> bool:
        """add suggested price to menu and create new estimated menu price"""
        menu_ids = []
        if only_menu_id :
            menu_ids.append(only_menu_id)
        else:
            menu = self.db.get_menu()
            for item in menu:
                menu_ids.append(item.id)

        for menu_id in menu_ids:
            latest_item_records = self.db.get_estimatedmenupricerecord(menu_id=menu_id, row_num=1)
            if not latest_item_records:
                the_record = None
            else:
                the_record = latest_item_records[0]

            last_direct_cost = the_record.direct_cost if the_record else 0
            last_indirect_cost = the_record.estimated_indirect_costs if the_record else 0
            last_sales_forecast = the_record.sales_forecast if the_record else 0
            last_profit_margin = the_record.profit_margin if the_record else 0
            last_manual_price = the_record.manual_price if the_record else 0

            direct_cost = direct_cost if direct_cost else last_direct_cost
            indirect_cost = indirect_cost if indirect_cost else last_indirect_cost
            sales_forecast = sales_forecast if sales_forecast else last_sales_forecast
            profit_margin = profit_margin if profit_margin else last_profit_margin
            manual_price = manual_price if manual_price else last_manual_price

            suggested_price = self._calculate_suggested_price(direct_cost, indirect_cost, sales_forecast, profit_margin)
            if not suggested_price:
                suggested_price = None


            new_record =  self.db.add_estimatedmenupricerecord(menu_id=menu_id,
                                                               direct_cost=direct_cost,
                                                               estimated_indirect_costs=indirect_cost,
                                                               sales_forecast=sales_forecast,
                                                               profit_margin=profit_margin,
                                                               manual_price=manual_price,
                                                               description=description,
                                                               category=category,
                                                               estimated_price=suggested_price
                                                               )
            if new_record:
                update_menu_list = self.db.get_menu(id=menu_id)
                if update_menu_list:
                    update_menu = update_menu_list[0]
                else:
                    print("not in menu")
                    continue
                update_menu.current_price = manual_price


                if suggested_price:
                    update_menu.suggested_price = suggested_price
                    print("updated menu Suggested price")
                else:
                    print("Could not update menu suggested price")


                self.db.edit_menu(update_menu)


        return True


    #_____________________________direct cost changes updates______________________________________________

    def calculate_update_direct_cost(self, menu_ids:list[int],
                                     category:Optional[str]=None,
                                     description:Optional[str]=None)->bool:
        if not menu_ids:
            return False

        menu_ids = list(set(menu_ids))

        menu_get_list = self.db.get_menu(id=menu_ids)
        if not menu_get_list:
            return False

        for menu_item in menu_get_list:
            recipe_list = menu_item.recipe
            new_price = 0
            for recipe in recipe_list:
                usage = recipe.inventory_item_amount_usage
                price_unit = recipe.inventory_item.price_per_unit if recipe.inventory_item.price_per_unit else 0
                new_price += usage * price_unit

            self._add_new_estimated_record_update_menu_suggestion(only_menu_id=menu_item.id,
                                                                  direct_cost=new_price,
                                                                  category=category,
                                                                  description=description)

        return True



    #this should get triggered each time rent, bills, equipment, or shifts get changes, or when new item get add to menu but this time should not update all
    #then should generate new record
    def calculate_indirect_cost(self, year=datetime.today().year, num_year=1, category:str = None)-> bool | float:
        """calculate the indirect costs"""
        start_date = datetime(year=year, month=1, day=1)
        end_date = datetime(year=year + num_year - 1, month=12, day=31)

        list_of_rents = self.db.get_rent(from_date=start_date, to_date=end_date)
        cost_rent = sum(r.rent + ((r.mortgage if r.mortgage else 0) * (r.mortgage_percentage_to_rent if r.mortgage_percentage_to_rent else 0)) for r in list_of_rents if r)


        list_of_bills = self.db.get_estimatedbills(from_date=start_date, to_date=end_date)
        cost_bills = sum(b.cost for b in list_of_bills if b)


        list_equipment_depreciation = self.db.get_equipment(expire_from_date=start_date, purchase_to_date=end_date)
        cost_equipment_depreciation = sum(e.monthly_depreciation for e in list_equipment_depreciation if e)


        payment_labor = self._get_estimated_labor_cost(start_date, end_date)


        indirect_price_overall = cost_rent + cost_bills + payment_labor + cost_equipment_depreciation
        if indirect_price_overall<= 0:
            return False
        if self._add_new_estimated_record_update_menu_suggestion(indirect_cost=indirect_price_overall, category=category):

            return indirect_price_overall
        return False


    #_____________________________menu manual changes updates______________________________________________

    def calculate_manual_price_change(self, menu_item_id, new_manual_price:float, category:Optional[str]="Manual Price Change")-> bool:
        """calculate the manual price change"""


        if self._add_new_estimated_record_update_menu_suggestion(only_menu_id=menu_item_id, manual_price=new_manual_price, category=category):
            return True
        return False


    #_____________________________direct cost changes updates______________________________________________
    def inventory_price_change_update_menu_item_direct_prices(self, inventory_id:int) -> bool:
        inventory_item_get_list = self.db.get_inventory(id=inventory_id, with_recipe=True)
        if not inventory_item_get_list:
            return False
        inventory_item = inventory_item_get_list[0]
        menu_recipe_ids = [the_recipe.menu_id for the_recipe in inventory_item.recipes]
        if not menu_recipe_ids:
            return False

        result = self.calculate_update_direct_cost(menu_ids=menu_recipe_ids, category="Inventory Changed", description=f"Inventory price change for {inventory_item.name}")

        return result
    # _____________________________indirect cost changes updates______________________________________________
    #IN BAKHSHE INDIRECT COST
    def labor_change_update_on_menu_price_record(self) -> bool:
        result = self.calculate_indirect_cost(category='Labor Changed')
        return result
    def rent_change_update_on_menu_price_record(self) -> bool:
        result = self.calculate_indirect_cost(category='Rent Changed')
        return result
    def equipment_change_update_on_menu_price_record(self) -> bool:
        result = self.calculate_indirect_cost(category='Equipment Changed')
        return result
    def bills_change_update_on_menu_price_record(self) -> bool:
        result = self.calculate_indirect_cost(category='Bills Changed')
        return result

    # _____________________________forecast changes updates______________________________________________
    def calculate_forecast(self,year=datetime.today().year, num_year=1, category:Optional[str] = "Forecast Changed")-> bool:
        start_date = datetime(year=year, month=1, day=1)
        end_date = datetime(year=year + num_year, month=1, day=1)

        list_of_forecasts = self.db.get_salesforecast(from_date=start_date, to_date=end_date)
        number_of_sales_forecasted = sum(sf.sell_number for sf in list_of_forecasts if list_of_forecasts)

        if self._add_new_estimated_record_update_menu_suggestion(sales_forecast=number_of_sales_forecasted, category=category):

            return True
        return False

