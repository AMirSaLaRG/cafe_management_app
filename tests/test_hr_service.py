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
