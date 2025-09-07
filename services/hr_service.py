from typing import Optional
from datetime import datetime, time
from models.dbhandler import DBHandler
from models.cafe_managment_models import *


class HRService:
    def __init__(self, db_handler: DBHandler):
        self.db = db_handler

    #___________Personal CRUD (add/deactivate)__________
    def new_personal(self,
                     f_name: str,
                     l_name:str,
                     n_code:str,
                     email:str,
                     phone:str,
                     address:str,
                     position: str,
                     monthly_hr: float,
                     monthly_payment: float,
                     start_date: Optional[datetime] = None) -> bool:
        added = self.db.add_personal(first_name=f_name, last_name=l_name,
                                      nationality_code=n_code, email=email,
                                      phone=phone, address=address,
                                      position=position, monthly_hr=monthly_hr,
                                      monthly_payment=monthly_payment, hire_date=start_date, active=True)
        return True if added else False

    def update_personal(self,
                     personal_id: int,
                     f_name: Optional[str] = None,
                     l_name:Optional[str] = None,
                     n_code:Optional[str] = None,
                     email:Optional[str] = None,
                     phone:Optional[str] = None,
                     address:Optional[str] = None,
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
                       monthly_salary:float,
                       regular_worked_hr:float,
                       direct_payed:float,
                       insurance_payed:Optional[float],
                       indirect_payed:Optional[float] = None,
                       extra_worked_hr:Optional[float] = None,
                       extra_expenses:Optional[float] = None,
                       description:Optional[str]=None
                       ) -> bool:
        return bool(self.db.add_recordemployeepayment(
            personal_id=personal_id,
            from_date=from_date,
            to_date=to_date,
            monthly_salary=monthly_salary,
            payment=direct_payed,
            indirect_payment=indirect_payed,
            insurance=insurance_payed,
            work_hr=regular_worked_hr,
            extra_hr=extra_worked_hr,
            extra_expenses=extra_expenses,
            description=description,
        ))

    # __________Shift assignment & schedule retrieval____
    def get_shift_schedule(self, personal_id: int,
                           from_date: datetime,
                           to_date: datetime) -> list[Shift]:
        shift_in_that_range = self.db.get_shift(from_date=from_date,
                                                to_date=to_date)
        personal_shifts_assigned = []
        for shift in shift_in_that_range:
            if getattr(shift, "assignments", None):
                if shift.assignments.personal_id == personal_id:
                    personal_shifts_assigned.append(shift)
        return personal_shifts_assigned


    def create_shift(self, date: datetime, from_hr: time, to_hr: time, name: str,
                     lunch_payment: float = 0, service_payment: float = 0,
                     extra_payment: float = 0, description: str = "") -> Optional[Shift]:
        """Create a new shift"""
        return self.db.add_shift(
            date=date, from_hr=from_hr, to_hr=to_hr, name=name,
            lunch_payment=lunch_payment, service_payment=service_payment,
            extra_payment=extra_payment, description=description
        )

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


