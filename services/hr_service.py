from typing import Optional
from datetime import datetime, time, timedelta
from models.dbhandler import DBHandler
from models.cafe_managment_models import *

def str_to_time_object_hr_min(the_time:str):
    the_time_object = datetime.strptime(the_time, '%H:%M').time()
    return the_time_object


def get_hours_diff(start_time, end_time):
    """Calculate difference in hours as float"""
    if not start_time or not end_time:
        return 0.0

    time_diff = end_time - start_time
    hours_diff = time_diff.total_seconds() / 3600
    return hours_diff

def time_difference_to_float_hr(self, start:time, end:time)->float:
    today = datetime.today().date()
    dt_start = datetime.combine(today, start)
    dt_end = datetime.combine(today, end)

    if dt_end < dt_start:
        dt_end += timedelta(days=1)

    delta = dt_end - dt_start
    return delta.total_seconds() / 3600

def time_to_float_hr(self, time_obj: time) -> float:
    """Convert time object to float hours"""
    if not time_obj:
        return 0.0
    return time_obj.hour + time_obj.minute / 60.0 + time_obj.second / 3600.0

class HRService:
    def __init__(self, db_handler: DBHandler):
        self.db = db_handler

    #___________Personal CRUD (add/deactivate)__________
    def new_personal(self,
                     f_name: str,
                     l_name: str,
                     n_code: str,
                     email: str,
                     phone: str,
                     address: str,
                     position: str,
                     monthly_hr: float,
                     monthly_payment: float,
                     start_date: Optional[datetime] = None) -> Personal:
        added = self.db.add_personal(first_name=f_name, last_name=l_name,
                                     nationality_code=n_code, email=email,
                                     phone=phone, address=address,
                                     position=position, monthly_hr=monthly_hr,
                                     monthly_payment=monthly_payment, hire_date=start_date, active=True)
        return added

    def update_personal(self,
                        personal_id: int,
                        f_name: Optional[str] = None,
                        l_name: Optional[str] = None,
                        n_code: Optional[str] = None,
                        email: Optional[str] = None,
                        phone: Optional[str] = None,
                        address: Optional[str] = None,
                        position: Optional[str] = None,
                        monthly_hr: Optional[float] = None,
                        monthly_payment: Optional[float] = None,
                        start_date: Optional[datetime] = None) -> bool:

        emp_fetch = self.db.get_personal(id=personal_id)

        if emp_fetch:
            emp = emp_fetch[0]
        else:
            return False

        if f_name is not None:
            emp.first_name = f_name
        if l_name is not None:
            emp.last_name = l_name
        if n_code is not None:
            emp.nationality_code = n_code
        if phone is not None:
            emp.phone = phone
        if email is not None:
            emp.email = email
        if address is not None:
            emp.address = address
        if position is not None:
            emp.position = position
        if monthly_hr is not None:
            emp.monthly_hr = monthly_hr
        if monthly_payment is not None:
            emp.monthly_payment = monthly_payment
        if start_date is not None:
            emp.hire_date = start_date

        return bool(self.db.edit_personal(emp))

    def deactivate_personal(self, personal_id: int, active=False) -> bool:
        employees = self.db.get_personal(id=personal_id)
        if not employees:
            return False
        emp = employees[0]
        emp.active = active
        if self.db.edit_personal(emp):
            return True
        return False

    def get_employee(self, personal_id: int) -> Optional[Personal]:
        employees = self.db.get_personal(id=personal_id)
        return employees[0] if employees else None

    def list_employees(self, active_only: bool = True) -> list[Personal]:
        return self.db.get_personal(active=active_only)

    #_________Payroll (recording payments)___________
    def record_payment(self, personal_id: int,
                       from_date: datetime,
                       to_date: datetime,
                       monthly_salary: float,
                       regular_worked_hr: float,
                       direct_paid: float,
                       insurance_paid: Optional[float],
                       indirect_paid: Optional[float] = None,
                       extra_worked_hr: Optional[float] = None,
                       extra_expenses: Optional[float] = None,
                       description: Optional[str] = None
                       ) -> bool:
        return bool(self.db.add_recordemployeepayment(
            personal_id=personal_id,
            from_date=from_date,
            to_date=to_date,
            monthly_salary=monthly_salary,
            payment=direct_paid,
            indirect_payment=indirect_paid,
            insurance=insurance_paid,
            work_hr=regular_worked_hr,
            extra_hr=extra_worked_hr,
            extra_expenses=extra_expenses,
            description=description,
        ))
    #_________record work (recording work)___________
    def add_work_record(self,
                        personal_id,
                        from_date:datetime,
                        to_date:datetime,
                        worked_hr:Optional[float]=None,
                        lunch:Optional[float] = 0,
                        service:Optional[float] = 0,
                        extra_payment:Optional[float] = 0,
                        description:Optional[str] = None) -> bool:

        if worked_hr is None:
            worked_hr = get_hours_diff(from_date, to_date)

        return bool(self.db.add_workshiftrecord(personal_id=personal_id,
                                    from_date=from_date,
                                    to_date=to_date,
                                    worked_hr=worked_hr,
                                    lunch_paid=lunch,
                                    service_paid=service,
                                    extra_paid=extra_payment,
                                    description=description))

    def edit_work_record(self,
                         record_id: int,
                         from_date: Optional[datetime] = None,
                         to_date: Optional[datetime] = None,
                         worked_hr: Optional[float] = None,
                         lunch: Optional[float] = None,
                         service: Optional[float] = None,
                         extra_payment: Optional[float] = None,
                         description: Optional[str] = None) -> bool:


        # First, get the existing record
        records = self.db.get_workshiftrecord(id=record_id)
        if not records:
            return False

        record = records[0]

        # Calculate worked hours if both from_date and to_date are provided
        if from_date is not None and to_date is not None:
            if from_date > to_date:
                return False
            record.worked_hr = get_hours_diff(from_date, to_date)
            record.from_date = from_date
            record.to_date = to_date
        elif from_date is not None:
            record.from_date = from_date
            if record.to_date and from_date > record.to_date:
                return False
            if record.to_date:
                record.worked_hr = get_hours_diff(from_date, record.to_date)
        elif to_date is not None:
            record.to_date = to_date
            if record.from_date and record.from_date > to_date:
                return False
            if record.from_date:
                record.worked_hr = get_hours_diff(record.from_date, to_date)

        # Update other fields if provided
        if worked_hr is not None:
            if worked_hr < 0:
                return False
            record.worked_hr = worked_hr

        if lunch is not None:
            if lunch < 0:
                return False
            record.lunch_paid = lunch

        if service is not None:
            if service < 0:
                return False
            record.service_paid = service

        if extra_payment is not None:
            if extra_payment < 0:
                return False
            record.extra_paid = extra_payment

        if description is not None:
            record.description = description

        # Save the changes
        updated_record = self.db.edit_workshiftrecord(record)
        return bool(updated_record)

    # __________Shift assignment & schedule retrieval____

    def create_shift(self, date: datetime, from_hr: time, to_hr: time, name: str=None,
                     lunch_payment: float = None, service_payment: float = None,
                     extra_payment: float = None, description: str = "") -> Optional[Shift]:
        """Create a new shift"""
        if lunch_payment is None:
            lunch_payment = 0
        if service_payment is None:
            service_payment = 0
        if extra_payment is None:
            extra_payment = 0
        return self.db.add_shift(
            date=date, from_hr=from_hr, to_hr=to_hr, name=name,
            lunch_payment=lunch_payment, service_payment=service_payment,
            extra_payment=extra_payment, description=description
        )
    def create_shift_routine(self,
                             list_tuple_start_end_daily: list[tuple[time, time]],
                             continue_days:int,
                             from_date:datetime=None,
                             name=None,
                             lunch_payment=None,
                             service_payment=None,
                             extra_payment=None,
                             description=None):
        date_range = []
        main_list = []
        if from_date is None:
            from_date = datetime.now()
        target_date = from_date + timedelta(days=continue_days)

        while from_date <= target_date:
            date_range.append(from_date)
            from_date += timedelta(days=1)

        for date in date_range:
            for tuple_start_end_daily in list_tuple_start_end_daily:
                main_tuple = (date, tuple_start_end_daily[0], tuple_start_end_daily[1])
                main_list.append(main_tuple)

        if self.db.add_routine_shift(main_list,
                                  name=name,
                                  lunch_payment=lunch_payment,
                                  service_payment=service_payment,
                                  extra_payment=extra_payment,
                                  description=description):
            return True
        return None

    def get_shift_schedule(self, personal_id: int,
                           from_date: datetime,
                           to_date: datetime) -> list[Shift]:
        shift_in_that_range = self.db.get_shift(from_date=from_date,
                                                to_date=to_date)
        personal_shifts_assigned = []
        for shift in shift_in_that_range:
            if getattr(shift, "assignments", None):
                for personal_assigned in shift.assignments:
                    if personal_assigned.personal_id == personal_id:
                        personal_shifts_assigned.append(shift)
        return personal_shifts_assigned

    def assign_shift(self, employee_id: int, shift_id: int, position_id: int) -> bool:
        return bool(self.db.add_personalassignment(personal_id=employee_id,
                                                   shift_id=shift_id,
                                                   position_id=position_id
                                                   ))

    def remove_shift_assignment(self, employee_id: int, shift_id: int) -> bool:
        """Remove an employee from a shift"""
        assignments = self.db.get_personalassignment(
            personal_id=employee_id,
            shift_id=shift_id
        )

        if assignments:
            return self.db.delete_personalassignment(assignments[0])
        return False

    def get_employee_shifts(self, employee_id: int,
                            from_date: Optional[datetime] = None,
                            to_date: Optional[datetime] = None) -> list[Shift]:
        """Get all shifts assigned to a specific employee"""
        assignments = self.db.get_personalassignment(personal_id=employee_id)

        shift_ids = [assignment.shift_id for assignment in assignments]
        if not shift_ids:
            return []

        # Get the actual shift objects
        shifts = self.db.get_shift(id=shift_ids)

        # Filter by date range if provided
        if from_date and to_date:
            shifts = [shift for shift in shifts if from_date <= shift.date <= to_date]

        return shifts

#_______________estimate positions & salary & labor_______________________

    def add_estimation_labor(self, position_ids: list[int], shift_id:int, extra_hr:str = "00:00") -> bool:
        """Add an estimation labor"""

        clean_position_ids = list(set(position_ids))

        for position_id in clean_position_ids:
            if not self.db.add_estimatedlabor(position_id=position_id,
                                              shift_id=shift_id,
                                              number=position_ids.count(position_id),
                                              extra_hr=str_to_time_object_hr_min(extra_hr)):
                return False

        return True

    def add_target_position(self,
                            position:str,
                            category:str,
                            monthly_hr:float,
                            monthly_payment:float,
                            extra_hr_payment:float,
                            monthly_insurance:float,
                            from_date:datetime = None,
                            to_date:datetime = None) -> bool:
        """Add a target position"""

        year = datetime.now().year

        if from_date is None:
            if to_date:
                year = to_date.year
            from_date = datetime(year=year, month=1, day=1)
            year = from_date.year

        if to_date is None:
            to_date = datetime(year=year, month=12, day=31)

        return bool(self.db.add_targetpositionandsalary(position=position,
                                            from_date=from_date,
                                            to_date=to_date,
                                            category=category,
                                            monthly_hr=monthly_hr,
                                            monthly_payment=monthly_payment,
                                            monthly_insurance=monthly_insurance,
                                            extra_hr_payment=extra_hr_payment))

    def update_target_position(self,
                               position_id:int,
                            name: Optional[str] = None,
                            category: Optional[str] = None,
                            monthly_hr: Optional[float] = None,
                            monthly_payment: Optional[float] = None,
                            over_time_payment_hr: Optional[float] = None,
                            monthly_insurance: Optional[float] = None,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> bool:
        """Add a target position"""


        target_fetch = self.db.get_targetpositionandsalary(id=position_id)

        if not target_fetch:
            return False
        target = target_fetch[0]

        if name is not None:
            target.position = name

        if category is not None:
            target.category = category

        if monthly_hr is not None:
            target.monthly_hr = monthly_hr

        if monthly_payment is not None:
            target.monthly_payment = monthly_payment

        if over_time_payment_hr is not None:
            target.extra_hr_payment  = over_time_payment_hr

        if monthly_insurance is not None:
            target.monthly_insurance = monthly_insurance

        if start_date is not None:
            target.from_date = start_date

        if end_date is not None:
            target.to_date = end_date

        return bool(self.db.edit_targetpositionandsalary(target))

#____________________indirect cost estimate____________________________
