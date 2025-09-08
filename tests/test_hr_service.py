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