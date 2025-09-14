from datetime import datetime, timedelta
from typing import Optional
from dateutil.relativedelta import relativedelta

from models.cafe_managment_models import EstimatedBills, Rent, Bills
from models.dbhandler import DBHandler


class BillsRent:
    def __init__(self, db_handler: DBHandler):
        self.db = db_handler


    #crud the estimate bills and get a time range (year) as indirect cost estimation
    def new_bill_estimated(self,
                      name:str,
                      category:str,
                      cost:float,
                      from_date:datetime,
                      to_date:datetime,
                      description:str=None) -> Optional[EstimatedBills]:

        return self.db.add_estimatedbills(
            name=name,
            category=category,
            cost=cost,
            from_date=from_date,
            to_date=to_date,
            description=description,
        )

    def find_bill_estimated(self, id:int)->Optional[EstimatedBills]:
        the_bill = self.db.get_estimatedbills(id=id)

        if the_bill:
            return the_bill[0]
        return None

    def find_bills_estimated(self, **filters) -> list[EstimatedBills]:
        return self.db.get_estimatedbills(**filters)

    def update_bill_estimated(self, estimated_bill_id, **kwargs) ->Optional[EstimatedBills]:
        the_bill = self.find_bill_estimated(estimated_bill_id)
        if not the_bill:
            return None
        for key, value in kwargs.items():
            if hasattr(the_bill, key):
                setattr(the_bill, key, value)

        return self.db.edit_estimatedbills(the_bill)

    def delete_bill_estimated(self, estimated_bill_id: int) -> bool:
        the_bill = self.find_bill_estimated(estimated_bill_id)
        if not the_bill:
            return False
        return self.db.delete_estimatedbills(the_bill)

    def create_a_range_of_bills(self,
                                category: str,
                                name: str,
                                year: int,
                                average_estimated_cost: float,
                                month: int = 1,
                                day: int = 1,
                                interval_months: int = 1,
                                number_of_periods: int = 12,
                                delete_overlap_bills: bool = False) -> bool:

        start_date = datetime(year, month, day)
        end_date = start_date + relativedelta(months=(interval_months * number_of_periods))

        # Check overlaps
        overlapping_bills = self.db.get_estimatedbills(
            name=name,
            from_date=start_date,
            to_date=end_date
        )

        if overlapping_bills and not delete_overlap_bills:
            return False

        # Delete overlaps if requested
        for bill in overlapping_bills or []:
            if not self.db.delete_estimatedbills(bill):
                return False

        # Create bills for each period
        current_date = start_date
        for _ in range(number_of_periods):
            next_date = current_date + relativedelta(months=interval_months)

            if not self.new_bill_estimated(
                    name=name,
                    category=category,
                    cost=average_estimated_cost,
                    from_date=current_date,
                    to_date=next_date,
                    description="Created as Range",
            ):
                return False

            current_date = next_date

        return True

    #crud the rent and get a time range (year) as indirect cost estimation

    def new_rent(self,
                 name: str,
                 rent: float,
                 mortgage: float,
                 mortgage_percentage_to_rent: float,
                 from_date: datetime,
                 to_date: datetime,
                 payer: str = None,
                 description: str = None) -> Optional[Rent]:
        return self.db.add_rent(
            name=name,
            rent=rent,
            mortgage=mortgage,
            mortgage_percentage_to_rent=mortgage_percentage_to_rent,
            from_date=from_date,
            to_date=to_date,
            payer=payer,
            description=description,
        )

    def find_rent(self, id: int) -> Optional[Rent]:
        rents = self.db.get_rent(id=id)
        return rents[0] if rents else None

    def find_rents(self, **filters) -> list[Rent]:
        return self.db.get_rent(**filters)

    def update_rent(self, rent_id: int, **kwargs) -> Optional[Rent]:
        the_rent = self.find_rent(rent_id)
        if not the_rent:
            return None

        for key, value in kwargs.items():
            if hasattr(the_rent, key):
                setattr(the_rent, key, value)

        return self.db.edit_rent(the_rent)

    def delete_the_rent(self, rent_id: int) -> bool:
        the_rent = self.find_rent(rent_id)
        if not the_rent:
            return False
        return self.db.delete_rent(the_rent)

    def create_a_range_of_rent(self,
                                name_place: str,
                                rent: float,
                                mortgage: float,
                                percentage_m_to_r: float,
                                year:int,
                                month: int = 1,
                                day: int = 1,
                                payer: str = None,
                                interval_months: int = 1,
                                number_of_periods: int = 12,
                                description: str = None,

                                ) -> bool:

        start_date = datetime(year, month, day)
        end_date = start_date + relativedelta(months=(interval_months * number_of_periods))


        # Create bills for each period
        current_date = start_date
        for _ in range(number_of_periods):
            next_date = current_date + relativedelta(months=interval_months)

            if not self.db.add_rent(
                    name=name_place,
                    rent=rent,
                    mortgage=mortgage,
                    mortgage_percentage_to_rent=percentage_m_to_r,
                    payer=payer,
                    from_date=current_date,
                    to_date=next_date,
                    description=description,
            ):
                return False

            current_date = next_date

        return True

    def pay_rent(self, rent_id:int, payer:str, description:str = None) ->bool:
        rent = self.find_rent(rent_id)
        if rent:
            rent.payer = payer
            if description:
                rent.description = description
            if self.db.edit_rent(rent):
                return True
        return False
    #crud the bills
    def new_bill(self,
                 name:str,
                 category:str,
                 from_date:datetime,
                 to_date:datetime,
                 cost:float,
                 payer:str,
                 description:str=None) -> Optional[Bills]:

        return self.db.add_bills(
            name=name,
            category=category,
            from_date=from_date,
            to_date=to_date,
            cost=cost,
            payer=payer,
            description=description,
        )

    def find_bill(self, id: int) -> Optional[Bills]:
        bills = self.db.get_bills(id=id)
        return bills[0] if bills else None

    def find_bills(self, **filters) -> list[Bills]:
        return self.db.get_bills(**filters)

    def update_bill(self, bill_id: int, **kwargs) -> Optional[Bills]:
        the_bill = self.find_bill(bill_id)
        if not the_bill:
            return None

        for key, value in kwargs.items():
            if hasattr(the_bill, key):
                setattr(the_bill, key, value)

        return self.db.edit_bills(the_bill)

    def delete_bill(self, bill_id: int) -> bool:
        the_bill = self.find_bill(bill_id)
        if not the_bill:
            return False
        return self.db.delete_bills(the_bill)