
import pytest
import time as t
from datetime import datetime, time, timedelta
from decimal import Decimal
from services.hr_service import HRService
from models.cafe_managment_models import *


class TestHRService:
    def test_personal_crud(self, in_memory_db):

        """Test updating menu item attributes"""
        service = HRService(in_memory_db)

        test1= service.new_personal(f_name="Mr Test",
                             l_name="testi number ONE $",
                             n_code="0014492847298723",
                             email='testingemail@hotmail.com',
                             phone="+989121111111111",
                             address="test address street testing and house number",
                             position="Waiter",
                             monthly_hr=182,
                             monthly_payment=15000000,
                             start_date=datetime(2026, 1, 1))

        assert test1


        test2= service.new_personal(f_name="1",
                             l_name="testi number ONE $",
                             n_code="0014492847298723",
                             email='testingemail@hotmail.com',
                             phone="+989121111111111",
                             address="test address street testing and house number",
                             position="Waiter",
                             monthly_hr=182,
                             monthly_payment=15000000,
                             start_date=datetime(2026, 1, 1))

        assert test2 is False

        test3 = service.new_personal(f_name="Mr Test",
                                     l_name="testi number ONE $",
                                     n_code="001111111113",
                                     email='testingemail@hotmail.com',
                                     phone="+989121111111111",
                                     address="test address street testing and house number",
                                     position="Barista",
                                     monthly_hr=182,
                                     monthly_payment=0,
                                     start_date=datetime(2026, 1, 1))

        assert test3
        assert len(in_memory_db.get_personal()) == 2

        personal_ids = [personal.id for personal in in_memory_db.get_personal()]

        personal1 = in_memory_db.get_personal(id=1)[0]
        personal2 = in_memory_db.get_personal(id=2)[0]

        p1 = service.get_employee(1)
        p2 = service.get_employee(2)

        assert personal1.id == p1.id
        assert personal2.id == p2.id
        assert personal1.active == True
        assert personal2.active == True
        assert personal1.id != p2.id

        all_employees = service.list_employees()
        all_employees_id = [personal.id for personal in all_employees]

        assert all_employees_id == personal_ids


        test_4 = service.deactivate_personal(personal_id=p1.id)
        assert test_4

        all_employees_2 = service.list_employees()
        all_employees_id_2 = [personal.id for personal in all_employees_2]
        assert len(all_employees_id_2) == 1
        assert all_employees_id_2[0] == p2.id

        test_5 = service.deactivate_personal(personal_id=p1.id, active=True)
        assert test_5

        all_employees_3 = service.list_employees()
        all_employees_id_3 = [personal.id for personal in all_employees_3]
        assert len(all_employees_id_3) == 2


        p2 = service.get_employee(2)

        assert p2.monthly_payment == 0

        service.update_personal(personal_id=p2.id, monthly_payment=10000000)

        p2 = service.get_employee(2)

        assert p2.monthly_payment == 10000000

        p1 = service.get_employee(1)
        p2 = service.get_employee(2)


        test_5 = service.update_personal(personal_id=p2.id, n_code=p1.nationality_code)

        p1 = service.get_employee(1)
        p2 = service.get_employee(2)

        assert test_5 is False
        assert p1.nationality_code != p2.nationality_code

    def test_record_payment(self, in_memory_db):
        service = HRService(in_memory_db)

        john = in_memory_db.add_personal(first_name="John", last_name="Doe")

        test_1 = service.record_payment(personal_id=john.id,
                                        from_date=datetime(2025, 1, 1),
                                        to_date=datetime(2025, 2, 1),
                                        monthly_salary=0,
                                        regular_worked_hr=144,
                                        direct_payed=10000,
                                        insurance_payed=0,
                                        extra_worked_hr=100,
                                        extra_expenses=500000,
                                        indirect_payed=43000,
                                        description="gosale")

        assert test_1

        # check = in_memory_db.get_recordemployeepayment()
        # print('checking')

    def time_h_m_creator(self, time:str):
        time_obj = datetime.strptime(time, "%H:%M").time()
        return time_obj
    def test_create_new_shift(self, in_memory_db):
        service = HRService(in_memory_db)

        test_1 = service.create_shift(date=datetime.now(),
                             from_hr=self.time_h_m_creator('13:20'),
                             to_hr=self.time_h_m_creator('23:30'),
                             name='shift asr',
                             )

        assert test_1



        test_2 = service.create_shift(date=datetime.now(),
                                      from_hr=self.time_h_m_creator('13:20'),
                                      to_hr=self.time_h_m_creator('23:30'),
                                      name='shift asr', extra_payment=300,
                                      description="vasssap"
                                      )

        assert test_2



    def test_create_new_shift_failure(self, in_memory_db):
        service = HRService(in_memory_db)

        test_2 = service.create_shift(date=datetime.now(),
                                      from_hr="10",
                                      to_hr="24",
                                      name='shift asr', extra_payment=300,
                                      description="vasssap"
                                      )

        assert test_2 is None

    def test_get_remove_shift_schedule(self, in_memory_db):
        service = HRService(in_memory_db)

        checking = []

        john = in_memory_db.add_personal(first_name="John", last_name="Doe")

        barista = in_memory_db.add_targetpositionandsalary("barista",
                                                           datetime(2024, 1, 1),
                                                           datetime(2025, 1, 1))

        for i in range(10):
            hr = i * 8
            date = datetime(2024, 1, 1) + timedelta(hours=hr)
            from_hr = (i * 8) % 24
            to_hr = (i * 8 + 8) % 24
            name = f"shift {i+1}"
            checking.append((from_hr, to_hr))

            the_shif =in_memory_db.add_shift(date=date,
                                   from_hr=self.time_h_m_creator(f'{from_hr}:00'),
                                   to_hr=self.time_h_m_creator(f'{to_hr}:00'),
                                   name=name)

            if i %3 == 0:
                in_memory_db.add_personalassignment(personal_id=john.id, shift_id=the_shif.id, position_id=barista.id)


        test_1 = service.get_shift_schedule(personal_id=john.id,
                                   from_date=datetime(2024, 1, 1),
                                   to_date=datetime(2024, 6, 1))

        assert len(test_1) == 4



        test_2 = service.get_shift_schedule(personal_id=john.id,
                                   from_date=datetime(2024, 1, 1),
                                   to_date=datetime(2024, 1, 2))

        assert len(test_2) == 2

        test_3 = service.remove_shift_assignment(john.id, test_2[1].id)

        assert test_3

        test_4 = service.get_shift_schedule(personal_id=john.id,
                                            from_date=datetime(2024, 1, 1),
                                            to_date=datetime(2024, 1, 2))

        assert len(test_4) == 1

        test_5 = service.get_employee_shifts(john.id)
        assert len(test_5) == 3

        a = in_memory_db.get_shift()
        b = in_memory_db.get_estimatedlabor()
        c = in_memory_db.get_targetpositionandsalary()
        d = in_memory_db.get_personalassignment()
        print("chicking")


    # def time_h_m_creator(self, time_str: str):
    #     """Helper method to create time objects from string"""
    #     return datetime.strptime(time_str, "%H:%M").time()

    def test_comprehensive_personal_management(self, in_memory_db):
        """Test comprehensive personal management with multiple employees and scenarios"""
        service = HRService(in_memory_db)

        # Create multiple employees with different positions
        employees_data = [
            {
                "f_name": "Alice", "l_name": "Johnson", "n_code": "0012345678901",
                "email": "alice@cafe.com", "phone": "+989121234567",
                "address": "123 Main St", "position": "Manager",
                "monthly_hr": 176, "monthly_payment": 25000000,
                "start_date": datetime(2024, 1, 15)
            },
            {
                "f_name": "Bob", "l_name": "Smith", "n_code": "0012345678902",
                "email": "bob@cafe.com", "phone": "+989121234568",
                "address": "456 Oak Ave", "position": "Barista",
                "monthly_hr": 160, "monthly_payment": 12000000,
                "start_date": datetime(2024, 2, 1)
            },
            {
                "f_name": "Charlie", "l_name": "Brown", "n_code": "0012345678903",
                "email": "charlie@cafe.com", "phone": "+989121234569",
                "address": "789 Pine Rd", "position": "Waiter",
                "monthly_hr": 150, "monthly_payment": 10000000,
                "start_date": datetime(2024, 2, 15)
            },
            {
                "f_name": "Diana", "l_name": "Prince", "n_code": "0012345678904",
                "email": "diana@cafe.com", "phone": "+989121234570",
                "address": "321 Cedar Ln", "position": "Cashier",
                "monthly_hr": 140, "monthly_payment": 9000000,
                "start_date": datetime(2024, 3, 1)
            }
        ]

        # Add all employees
        employee_ids = []
        for emp_data in employees_data:
            result = service.new_personal(**emp_data)
            assert result
            employee_ids.append(len(employee_ids) + 1)  # Assuming sequential IDs

        # Verify all employees were added
        all_employees = service.list_employees()
        assert len(all_employees) == 4

        # Test deactivation/reactivation
        assert service.deactivate_personal(employee_ids[2])  # Deactivate Charlie
        active_employees = service.list_employees(active_only=True)
        assert len(active_employees) == 3

        assert service.deactivate_personal(employee_ids[2], active=True)  # Reactivate
        active_employees = service.list_employees(active_only=True)
        assert len(active_employees) == 4

        # Test bulk updates
        updates = {
            "monthly_payment": 11000000,  # Give everyone a raise
            "monthly_hr": 170  # Increase hours
        }

        for emp_id in employee_ids:
            assert service.update_personal(emp_id, **updates)

        # Verify updates
        for emp_id in employee_ids:
            employee = service.get_employee(emp_id)
            assert employee.monthly_payment == 11000000
            assert employee.monthly_hr == 170

    def test_comprehensive_payment_records(self, in_memory_db):
        """Test comprehensive payment recording with various scenarios"""
        service = HRService(in_memory_db)

        # Create employees
        manager = in_memory_db.add_personal(
            first_name="Manager", last_name="Test",
            nationality_code="001111111111", position="Manager",
            monthly_payment=20000000, monthly_hr=176
        )

        barista = in_memory_db.add_personal(
            first_name="Barista", last_name="Test",
            nationality_code="001111111112", position="Barista",
            monthly_payment=12000000, monthly_hr=160
        )

        # Record various payment scenarios
        payment_scenarios = [
            # Regular full month
            {
                "personal_id": manager.id,
                "from_date": datetime(2024, 1, 1),
                "to_date": datetime(2024, 1, 31),
                "monthly_salary": 20000000,
                "regular_worked_hr": 176,
                "direct_payed": 20000000,
                "insurance_payed": 1000000,
                "description": "Regular January salary"
            },
            # Partial month with overtime
            {
                "personal_id": barista.id,
                "from_date": datetime(2024, 1, 15),
                "to_date": datetime(2024, 1, 31),
                "monthly_salary": 6000000,  # Half month
                "regular_worked_hr": 80,
                "direct_payed": 6000000,
                "insurance_payed": 500000,
                "extra_worked_hr": 20,
                "extra_expenses": 500000,
                "indirect_payed": 1000000,
                "description": "January partial with overtime"
            },
            # Month with bonuses
            {
                "personal_id": manager.id,
                "from_date": datetime(2024, 2, 1),
                "to_date": datetime(2024, 2, 29),
                "monthly_salary": 20000000,
                "regular_worked_hr": 176,
                "direct_payed": 25000000,  # Includes bonus
                "insurance_payed": 1000000,
                "extra_expenses": 2000000,
                "description": "February with performance bonus"
            }
        ]

        # Record all payments
        for payment in payment_scenarios:
            assert service.record_payment(**payment)

        # Verify payments were recorded
        manager_payments = in_memory_db.get_recordemployeepayment(personal_id=manager.id)
        barista_payments = in_memory_db.get_recordemployeepayment(personal_id=barista.id)

        assert len(manager_payments) == 2
        assert len(barista_payments) == 1

        # Verify payment amounts
        total_manager_payments = sum(p.payment for p in manager_payments)
        assert total_manager_payments == 45000000  # 20M + 25M

    def test_comprehensive_shift_management(self, in_memory_db):
        """Test comprehensive shift management with multiple scenarios"""
        service = HRService(in_memory_db)

        # Create positions
        positions = [
            in_memory_db.add_targetpositionandsalary(
                "Manager", datetime(2024, 1, 1), datetime(2024, 12, 31),
                monthly_hr=176, monthly_payment=20000000, extra_hr_payment=150000
            ),
            in_memory_db.add_targetpositionandsalary(
                "Barista", datetime(2024, 1, 1), datetime(2024, 12, 31),
                monthly_hr=160, monthly_payment=12000000, extra_hr_payment=100000
            ),
            in_memory_db.add_targetpositionandsalary(
                "Waiter", datetime(2024, 1, 1), datetime(2024, 12, 31),
                monthly_hr=150, monthly_payment=10000000, extra_hr_payment=80000
            )
        ]

        # Create employees
        employees = [
            in_memory_db.add_personal(first_name="Manager", last_name="One", position="Manager"),
            in_memory_db.add_personal(first_name="Barista", last_name="One", position="Barista"),
            in_memory_db.add_personal(first_name="Waiter", last_name="One", position="Waiter"),
            in_memory_db.add_personal(first_name="Barista", last_name="Two", position="Barista")
        ]

        # Create shifts for a week
        week_shifts = []
        for day in range(7):  # 7 days of shifts
            date = datetime(2024, 3, 10 + day)  # Starting March 10th

            # Morning shift
            morning_shift = service.create_shift(
                date=date,
                from_hr=self.time_h_m_creator('08:00'),
                to_hr=self.time_h_m_creator('16:00'),
                name=f"Morning Shift Day {day + 1}",
                lunch_payment=50000,
                service_payment=20000
            )
            week_shifts.append(morning_shift)

            # Evening shift
            evening_shift = service.create_shift(
                date=date,
                from_hr=self.time_h_m_creator('16:00'),
                to_hr=self.time_h_m_creator('00:00'),
                name=f"Evening Shift Day {day + 1}",
                lunch_payment=50000,
                service_payment=30000,
                extra_payment=100000
            )
            week_shifts.append(evening_shift)

        # Assign employees to shifts (complex schedule)
        assignments = [
            # Manager works Monday-Friday morning
            (employees[0].id, week_shifts[0].id, positions[0].id),  # Mon morning
            (employees[0].id, week_shifts[2].id, positions[0].id),  # Tue morning
            (employees[0].id, week_shifts[4].id, positions[0].id),  # Wed morning
            (employees[0].id, week_shifts[6].id, positions[0].id),  # Thu morning
            (employees[0].id, week_shifts[8].id, positions[0].id),  # Fri morning

            # Barista One works all evening shifts
            (employees[1].id, week_shifts[1].id, positions[1].id),  # Mon evening
            (employees[1].id, week_shifts[3].id, positions[1].id),  # Tue evening
            (employees[1].id, week_shifts[5].id, positions[1].id),  # Wed evening
            (employees[1].id, week_shifts[7].id, positions[1].id),  # Thu evening
            (employees[1].id, week_shifts[9].id, positions[1].id),  # Fri evening
            (employees[1].id, week_shifts[11].id, positions[1].id),  # Sat evening
            (employees[1].id, week_shifts[13].id, positions[1].id),  # Sun evening

            # Barista Two works weekend mornings
            (employees[3].id, week_shifts[10].id, positions[1].id),  # Sat morning
            (employees[3].id, week_shifts[12].id, positions[1].id),  # Sun morning

            # Waiter works all shifts except Sunday
            (employees[2].id, week_shifts[0].id, positions[2].id),  # Mon morning
            (employees[2].id, week_shifts[1].id, positions[2].id),  # Mon evening
            (employees[2].id, week_shifts[2].id, positions[2].id),  # Tue morning
            (employees[2].id, week_shifts[3].id, positions[2].id),  # Tue evening
            (employees[2].id, week_shifts[4].id, positions[2].id),  # Wed morning
            (employees[2].id, week_shifts[5].id, positions[2].id),  # Wed evening
            (employees[2].id, week_shifts[6].id, positions[2].id),  # Thu morning
            (employees[2].id, week_shifts[7].id, positions[2].id),  # Thu evening
            (employees[2].id, week_shifts[8].id, positions[2].id),  # Fri morning
            (employees[2].id, week_shifts[9].id, positions[2].id),  # Fri evening
            (employees[2].id, week_shifts[10].id, positions[2].id),  # Sat morning
            (employees[2].id, week_shifts[11].id, positions[2].id),  # Sat evening
        ]

        # Make all assignments
        for emp_id, shift_id, pos_id in assignments:
            assert service.assign_shift(emp_id, shift_id, pos_id)

        # Verify assignments
        manager_shifts = service.get_employee_shifts(employees[0].id)
        assert len(manager_shifts) == 5  # Mon-Fri morning

        barista1_shifts = service.get_employee_shifts(employees[1].id)
        assert len(barista1_shifts) == 7  # All evening shifts

        waiter_shifts = service.get_employee_shifts(employees[2].id)
        assert len(waiter_shifts) == 12  # All shifts except Sunday

        # Test removing assignments
        assert service.remove_shift_assignment(employees[2].id, week_shifts[0].id)
        updated_waiter_shifts = service.get_employee_shifts(employees[2].id)
        assert len(updated_waiter_shifts) == 11

    def test_work_record_comprehensive(self, in_memory_db):
        """Test comprehensive work record management"""
        service = HRService(in_memory_db)

        # Create employee
        employee = in_memory_db.add_personal(
            first_name="Work", last_name="Recorder",
            nationality_code="001999999999", position="Tester"
        )

        # Add multiple work records for different scenarios
        work_records = [
            # Regular 8-hour shift
            {
                "personal_id": employee.id,
                "from_date": datetime(2024, 1, 1, 8, 0),
                "to_date": datetime(2024, 1, 1, 16, 0),
                "worked_hr": 8.0,
                "lunch": 50000,
                "service": 20000,
                "description": "Regular Monday shift"
            },
            # Overtime shift
            {
                "personal_id": employee.id,
                "from_date": datetime(2024, 1, 2, 8, 0),
                "to_date": datetime(2024, 1, 2, 18, 0),
                "worked_hr": 10.0,
                "lunch": 50000,
                "service": 30000,
                "extra_payment": 150000,
                "description": "Tuesday with 2h overtime"
            },
            # Weekend shift with premium
            {
                "personal_id": employee.id,
                "from_date": datetime(2024, 1, 6, 10, 0),  # Saturday
                "to_date": datetime(2024, 1, 6, 18, 0),
                "worked_hr": 8.0,
                "lunch": 60000,
                "service": 40000,
                "extra_payment": 200000,
                "description": "Weekend premium shift"
            },
            # Night shift
            {
                "personal_id": employee.id,
                "from_date": datetime(2024, 1, 3, 22, 0),
                "to_date": datetime(2024, 1, 4, 6, 0),
                "worked_hr": 8.0,
                "lunch": 70000,
                "service": 50000,
                "extra_payment": 250000,
                "description": "Night shift differential"
            }
        ]

        # Add all work records
        for record in work_records:
            assert service.add_work_record(**record)

        # Verify records were added
        records = in_memory_db.get_workshiftrecord(personal_id=employee.id)
        assert len(records) == 4

        # Test editing a record
        first_record = records[-1]
        check = in_memory_db.get_workshiftrecord()
        times = [(i.from_date, i.to_date) for i in check]
        test = service.edit_work_record(
            record_id=first_record.id,
            from_date=datetime(2024, 1, 1, 9, 0),  # Start 1 hour later
            to_date=datetime(2024, 1, 1, 17, 0),  # End 1 hour later
            lunch=60000,  # Increase lunch payment
            description="Updated Monday shift"
        )

        assert test

        # Verify edit
        updated_record = in_memory_db.get_workshiftrecord(id=first_record.id)[0]
        assert updated_record.worked_hr == 8.0  # Should still be 8 hours
        assert updated_record.lunch_payed == 60000

    def test_target_position_management(self, in_memory_db):
        """Test comprehensive target position management"""
        service = HRService(in_memory_db)

        # Create multiple target positions
        positions = [
            {
                "name": "Senior Manager",
                "category": "Management",
                "monthly_hr": 176,
                "monthly_payment": 30000000,
                "over_time_payment_hr": 200000,
                "monthly_insurance": 1500000,
                "start_date": datetime(2024, 1, 1),
                "end_date": datetime(2024, 12, 31)
            },
            {
                "name": "Junior Barista",
                "category": "Production",
                "monthly_hr": 140,
                "monthly_payment": 8000000,
                "over_time_payment_hr": 80000,
                "monthly_insurance": 800000,
                "start_date": datetime(2024, 1, 1),
                "end_date": datetime(2024, 6, 30)  # 6-month contract
            },
            {
                "name": "Head Chef",
                "category": "Kitchen",
                "monthly_hr": 180,
                "monthly_payment": 25000000,
                "over_time_payment_hr": 180000,
                "monthly_insurance": 2000000,
                "start_date": datetime(2024, 3, 1),  # Starting later
                "end_date": datetime(2024, 12, 31)
            }
        ]

        # Add all positions
        for pos in positions:
            assert service.add_target_position(**pos)

        # Verify positions were added
        all_positions = in_memory_db.get_targetpositionandsalary()
        assert len(all_positions) == 3

        # Test updating a position
        junior_barista = all_positions[1]  # Second position
        assert service.update_target_position(
            position_id=junior_barista.id,
            monthly_payment=9000000,  # Give raise
            monthly_hr=150,  # Increase hours
            end_date=datetime(2024, 12, 31)  # Extend contract
        )

        # Verify update
        updated_position = in_memory_db.get_targetpositionandsalary(id=junior_barista.id)[0]
        assert updated_position.monthly_payment == 9000000
        assert updated_position.monthly_hr == 150

    def test_estimation_labor_management(self, in_memory_db):
        """Test labor estimation functionality"""
        service = HRService(in_memory_db)

        # Create positions
        positions = [
            in_memory_db.add_targetpositionandsalary(
                "Manager", datetime(2024, 1, 1), datetime(2024, 12, 31),
                monthly_hr=176, monthly_payment=20000000
            ),
            in_memory_db.add_targetpositionandsalary(
                "Barista", datetime(2024, 1, 1), datetime(2024, 12, 31),
                monthly_hr=160, monthly_payment=12000000
            ),
            in_memory_db.add_targetpositionandsalary(
                "Waiter", datetime(2024, 1, 1), datetime(2024, 12, 31),
                monthly_hr=150, monthly_payment=10000000
            )
        ]

        # Create shifts
        shifts = []
        for i in range(5):  # 5 days of shifts
            shift = service.create_shift(
                date=datetime(2024, 4, 1 + i),
                from_hr=self.time_h_m_creator('08:00'),
                to_hr=self.time_h_m_creator('16:00'),
                name=f"Shift Day {i + 1}"
            )
            shifts.append(shift)

        # Add labor estimations for each shift
        labor_estimations = [
            # Shift 1: 1 Manager, 2 Baristas, 3 Waiters
            ([positions[0].id, positions[1].id, positions[1].id,
              positions[2].id, positions[2].id, positions[2].id], shifts[0].id, "01:30"),

            # Shift 2: 1 Manager, 1 Barista, 2 Waiters
            ([positions[0].id, positions[1].id,
              positions[2].id, positions[2].id], shifts[1].id, "00:45"),

            # Shift 3: 2 Baristas, 2 Waiters (no manager)
            ([positions[1].id, positions[1].id,
              positions[2].id, positions[2].id], shifts[2].id, "00:30"),

            # Shift 4: Weekend - more staff
            ([positions[0].id, positions[1].id, positions[1].id, positions[1].id,
              positions[2].id, positions[2].id, positions[2].id], shifts[3].id, "02:00"),

            # Shift 5: Minimum staff
            ([positions[1].id, positions[2].id], shifts[4].id, "00:15")
        ]

        # Add all labor estimations
        for position_ids, shift_id, extra_hr in labor_estimations:
            assert service.add_estimation_labor(position_ids, shift_id, extra_hr)

        # Verify estimations were added
        all_estimations = in_memory_db.get_estimatedlabor()
        assert len(all_estimations) == sum(len(list(set(ids))) for ids, _, _ in labor_estimations)

        # Verify specific estimation
        shift1_estimations = in_memory_db.get_estimatedlabor(shift_id=shifts[0].id)
        person_in_shift = sum(r.number for r in shift1_estimations)
        assert person_in_shift == 6  # 1 Manager + 2 Baristas + 3 Waiters

        # Count positions per shift
        manager_count = sum(e.number for e in shift1_estimations if e.position_id == positions[0].id)
        barista_count = sum(e.number  for e in shift1_estimations if e.position_id == positions[1].id)
        waiter_count = sum(e.number  for e in shift1_estimations if e.position_id == positions[2].id)

        assert manager_count == 1
        assert barista_count == 2
        assert waiter_count == 3

    def test_edge_cases_and_error_handling(self, in_memory_db):
        """Test edge cases and error handling"""
        service = HRService(in_memory_db)

        # Test with non-existent employee
        assert not service.record_payment(
            personal_id=999,  # Non-existent ID
            from_date=datetime(2024, 1, 1),
            to_date=datetime(2024, 1, 31),
            monthly_salary=10000000,
            regular_worked_hr=160,
            direct_payed=10000000,
            insurance_payed=500000
        )

        # Test with invalid date range
        employee = in_memory_db.add_personal(
            first_name="Test", last_name="Edge", position="Tester"
        )

        assert not service.record_payment(
            personal_id=employee.id,
            from_date=datetime(2024, 1, 31),  # Start after end
            to_date=datetime(2024, 1, 1),
            monthly_salary=10000000,
            regular_worked_hr=160,
            direct_payed=10000000,
            insurance_payed=500000
        )

        # Test with negative values
        assert not service.record_payment(
            personal_id=employee.id,
            from_date=datetime(2024, 1, 1),
            to_date=datetime(2024, 1, 31),
            monthly_salary=-10000000,  # Negative salary
            regular_worked_hr=160,
            direct_payed=10000000,
            insurance_payed=500000
        )

        # Test work record with invalid time range
        assert not service.add_work_record(
            personal_id=employee.id,
            from_date=datetime(2024, 1, 1, 18, 0),  # Start after end
            to_date=datetime(2024, 1, 1, 8, 0),
            worked_hr=8.0
        )

    def test_performance_with_large_datasets(self, in_memory_db):
        """Test performance with larger datasets"""
        service = HRService(in_memory_db)

        # Create 50 employees
        for i in range(50):
            service.new_personal(
                f_name=f"Employee{i:02d}",
                l_name="Performance",
                n_code=f"0012345678{i:03d}",
                email=f"employee{i:02d}@cafe.com",
                phone=f"+989121234{i:04d}",
                address=f"{i} Test Street",
                position="Staff",
                monthly_hr=160,
                monthly_payment=10000000 + (i * 100000),  # Varying salaries
                start_date=datetime(2024, 1, 1)
            )

        # Create 100 shifts over a month
        shifts = []
        for day in range(30):  # 30 days
            for shift_num in range(3):  # 3 shifts per day
                shift = service.create_shift(
                    date=datetime(2024, 4, day + 1),
                    from_hr=self.time_h_m_creator(f'{(8 + shift_num * 8) % 24}:00'),
                    to_hr=self.time_h_m_creator(f'{(16 + shift_num * 8) % 24}:00'),
                    name=f"Shift {day + 1}-{shift_num + 1}"
                )
                shifts.append(shift)

        # Verify we can handle large datasets
        all_employees = service.list_employees()
        assert len(all_employees) == 50

        all_shifts = in_memory_db.get_shift()
        assert len(all_shifts) == 90  # 30 days * 3 shifts

        # Test filtering performance
        import time
        start_time = time.time()

        april_shifts = in_memory_db.get_shift(
            from_date=datetime(2024, 4, 1),
            to_date=datetime(2024, 4, 30)
        )

        end_time = time.time()
        assert len(april_shifts) == 90
        assert end_time - start_time < 1.0  # Should be fast


# Run the tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])