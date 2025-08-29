

class HRService:
    def __init__(self):
        self.db = None

    def add_employee(self, personal_data):
        pass

    def deactivate_employee(self, employee_id):
        pass
    #shift id should be foreign key
    def assign_shift(self, employee_id, shift_id, date):
        pass
    def get_shift_schedule(self, employee_id, from_date, to_date):
        pass

    def record_payment(self, employee_id, from_date, to_date, amount, extras):
        pass
    def labor_cost_repot(self, from_date, to_date):
        pass
