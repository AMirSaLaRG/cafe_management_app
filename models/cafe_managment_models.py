from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey, DateTime, TIMESTAMP, \
    Time
from sqlalchemy.orm import declarative_base, relationship
from eralchemy import render_er
from datetime import datetime, timezone

Base = declarative_base()
#done
class Inventory(Base):
    __tablename__ = 'inventory'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    unit = Column(String(50))
    current_stock = Column(Float)
    current_price = Column(Float)
    current_supplier = Column(ForeignKey('supplier.id'))
    daily_usage = Column(Float)
    safety_stock = Column(Float)
    category = Column(String(255))
    price_per_unit = Column(Float)


    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))


    supplier = relationship("Supplier", back_populates="inventory_item", lazy="joined")
    recipes = relationship("Recipe", back_populates="inventory_item")
    supply_record = relationship("SupplyRecord", back_populates="inventory_item")
    usage_records = relationship("InventoryUsage", back_populates="inventory_item")
    records = relationship("InventoryStockRecord", back_populates="inventory_item")

#done
class InventoryStockRecord(Base):
    __tablename__ = "inventory_record"

    id = Column(Integer, primary_key=True)
    inventory_id = Column(ForeignKey('inventory.id'))
    category = Column(String)
    foreign_id = Column(Integer)
    date = Column(TIMESTAMP)
    change_amount = Column(Float)
    auto_calculated_amount = Column(Float)
    manual_report = Column(Float)
    reporter = Column(String)
    description = Column(String(500))
    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    inventory_item = relationship("Inventory", back_populates="records")
#done
class Menu(Base):
    __tablename__ = 'menu'

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    size = Column(String, nullable=False, default='m')
    category = Column(String)
    current_price = Column(Float)
    suggested_price = Column(Float)
    value_added_tax = Column(Float)
    serving = Column(Boolean, default=True)
    description = Column(String(500))

    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))


    recipe = relationship('Recipe', back_populates='menu_item', lazy="joined")
    sales = relationship("Sales", back_populates="menu_item")
    usage_record = relationship("MenuUsage", back_populates="menu_item")
    estimated_price_records = relationship("EstimatedMenuPriceRecord" , back_populates="menu_item")
    forecast = relationship("SalesForecast", back_populates="menu_item")



#done
class EstimatedMenuPriceRecord(Base):
    __tablename__ = "estimated_menu_price_record"

    id =Column(Integer, primary_key=True)
    menu_id = Column(ForeignKey("menu.id"), index=True)
    sales_forecast = Column(Integer)
    estimated_indirect_costs = Column(Float)
    direct_cost = Column(Float)
    profit_margin = Column(Float)

    category = Column(String)
    estimated_price = Column(Float)
    manual_price = Column(Float)
    from_date = Column(DateTime, nullable=False, index=True)

    description = Column(String(500))

    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))


    menu_item = relationship("Menu", back_populates="estimated_price_records")



#done
class Recipe(Base):
    __tablename__ = "recipe"

    inventory_id = Column(ForeignKey('inventory.id'), primary_key=True)
    menu_id = Column(ForeignKey("menu.id"), primary_key=True)
    inventory_item_amount_usage = Column(Float)
    writer = Column(String(100))
    description = Column(String(500))
    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    menu_item = relationship("Menu", back_populates='recipe', lazy="joined")
    inventory_item = relationship("Inventory", back_populates="recipes", lazy="joined")

#_______________THIS TABLES CAN ADD ITEM TO MY INVENTORY__________________________
class Supplier(Base):
    __tablename__ = "supplier"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    load_time_days = Column(Integer)
    contact_channel = Column(String)
    contact_address = Column(String)
    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    inventory_item = relationship("Inventory", back_populates="supplier", lazy="joined")
    orders = relationship("Order", back_populates="supplier")

#Done
class Order(Base):
    __tablename__ = "order"

    id = Column(Integer, primary_key=True)
    supplier_id = Column(ForeignKey('supplier.id'))
    date = Column(DateTime)
    buyer= Column(String, nullable=False)
    payer = Column(String)
    description = Column(String(500))
    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))


    supplier = relationship("Supplier", back_populates="orders", lazy="joined")
    ship = relationship("Ship", back_populates="order", lazy="joined")

#done
class Ship(Base):
    __tablename__ = 'ship'

    id = Column(Integer, primary_key=True)
    order_id = Column(ForeignKey('order.id'))
    shipper = Column(String)
    price = Column(Float)
    receiver = Column(String)
    payer = Column(String)
    date = Column(DateTime)
    description = Column(String(500))

    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    supply_record = relationship("SupplyRecord", back_populates="ship")
    order = relationship("Order", back_populates="ship")
#done
class SupplyRecord(Base):
    __tablename__ = "supply_record"

    id = Column(Integer, primary_key=True)
    inventory_item_id = Column(ForeignKey('inventory.id'), nullable=False)
    ship_id = Column(ForeignKey('ship.id'), nullable=False)
    price = Column(Float)
    box_amount = Column(Float)
    box_price = Column(Float)
    box_discount = Column(Float)
    num_of_box = Column(Float)
    description = Column(String(500))

    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))


    inventory_item = relationship("Inventory", back_populates="supply_record")
    ship = relationship("Ship", back_populates="supply_record", lazy="joined")
#_______________THIS TABLES CAN DEDUCT ITEM FROM MY INVENTORY__________________________

#done
class InvoicePayment(Base):
    __tablename__ = 'invoice_payment'

    id = Column(Integer, primary_key=True)
    payed = Column(Float)
    payer = Column(String)
    method = Column(String)
    date = Column(DateTime)
    receiver = Column(String)
    receiver_id = Column(String)

    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))


    invoice = relationship("Invoice", back_populates="payment")
#done
class Invoice(Base):
    __tablename__ = 'invoice'

    id = Column(Integer, primary_key=True)
    pay_id = Column(ForeignKey('invoice_payment.id'))
    saler = Column(String)
    date = Column(DateTime)
    total_price = Column(Float)
    closed = Column(Boolean, nullable=False)
    description = Column(String(500))

    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))


    sales = relationship("Sales", back_populates="invoice")
    payment = relationship("InvoicePayment", back_populates="invoice")

#done
class Sales(Base):
    __tablename__ = 'sales'

    menu_id = Column(ForeignKey("menu.id"), primary_key=True)
    invoice_id = Column(ForeignKey('invoice.id'), primary_key=True)
    number = Column(Integer)
    discount = Column(Float)
    price = Column(Float)
    description = Column(String(500))

    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))



    menu_item = relationship("Menu", back_populates="sales")
    invoice = relationship("Invoice", back_populates="sales")

#done
class Usage(Base):
    __tablename__ = 'usage'

    id = Column(Integer, primary_key=True)
    used_by = Column(String)
    date = Column(DateTime)
    category = Column(String)
    description = Column(String(500))

    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))


    inventory_usage = relationship("InventoryUsage", back_populates="usage")
    menu_usage = relationship("MenuUsage", back_populates="usage")
#done
class InventoryUsage(Base):
    __tablename__ = "inventory_usage"

    inventory_item_id = Column(ForeignKey('inventory.id'), primary_key=True)
    usage_id = Column(ForeignKey("usage.id"), primary_key=True)
    amount = Column(Float)

    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))


    inventory_item = relationship("Inventory", back_populates="usage_records")
    usage = relationship("Usage", back_populates="inventory_usage")
#done
class MenuUsage(Base):
    __tablename__ = "menu_usage"

    menu_id = Column(ForeignKey("menu.id"), primary_key=True)
    usage_id = Column(ForeignKey("usage.id"), primary_key=True)
    amount = Column(Float)

    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))


    menu_item= relationship("Menu", back_populates="usage_record")
    usage = relationship("Usage", back_populates="menu_usage")



#_______________THIS TABLES WE TRY TO ESTIMATE HOW THINK WILL BE FROM EXP TO GET PREDICT INDIRECT COSTS __________________________
#done
class SalesForecast(Base):
    __tablename__ = "sales_forecast"

    id = Column(Integer, primary_key=True)
    menu_item_id = Column(ForeignKey("menu.id"))

    from_date = Column(DateTime)
    to_date = Column(DateTime)

    sell_number = Column(Integer)

    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))


    menu_item = relationship("Menu", back_populates="forecast")

#CLEANING AS WELL
#done
class EstimatedBills(Base):
    __tablename__ = "estimated_bills"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    category = Column(String)
    cost = Column(Float)
    from_date = Column(DateTime)
    to_date = Column(DateTime)
    description = Column(String(500))

    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))

#done
class TargetPositionAndSalary(Base):
    __tablename__ = "target_position_and_salary"

    id = Column(Integer, primary_key=True)
    position = Column(String, nullable=False)
    category = Column(String)
    from_date = Column(DateTime)
    to_date = Column(DateTime)
    monthly_hr = Column(Float)
    monthly_payment = Column(Float)
    monthly_insurance = Column(Float)
    extra_hr_payment = Column(Float)

    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    labor = relationship("EstimatedLabor", back_populates="position")



class Shift(Base):
    __tablename__ = "shift"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime)
    from_hr = Column(Time)
    to_hr = Column(Time)
    name = Column(String)
    lunch_payment = Column(Float)
    service_payment = Column(Float)
    extra_payment = Column(Float)
    description = Column(String(500))

    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))


    labor = relationship("EstimatedLabor", back_populates="shift", lazy="joined")

class EstimatedLabor(Base):
    __tablename__ = "estimated_labor"
    position_id = Column(ForeignKey("target_position_and_salary.id"), primary_key=True)
    shift_id = Column(ForeignKey("shift.id"), primary_key=True)
    number = Column(Integer)
    extra_hr = Column(Time)

    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))


    position = relationship("TargetPositionAndSalary", back_populates="labor", lazy="joined")
    shift = relationship("Shift", back_populates="labor", lazy="joined")

#_______________THIS TABLES HELPS TO FORECAST INDIRECT COSTS BUT THEY ARE CONSTANT MOSTLY SO HELPS RECORD AS WELL__________________________

class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    number = Column(Integer)
    category = Column(String)
    purchase_date = Column(DateTime)
    purchase_price = Column(Float)
    payer = Column(String)
    in_use= Column(Boolean)
    expire_date = Column(DateTime)
    monthly_depreciation = Column(Float)
    description = Column(String(500))


    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Rent(Base):
    __tablename__ = "rent"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    rent = Column(Float)
    mortgage = Column(Float)
    mortgage_percentage_to_rent = Column(Float)
    from_date = Column(DateTime)
    to_date = Column(DateTime)
    payer = Column(String)
    description = Column(String(500))

    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))

#_____________ THIS TABLES HELP RECORD AND SEE WHAT REALITY LOOKS LIKE _________________________

#Cleaning should be in this
class Bills(Base):
    __tablename__ = 'bills'

    id = Column(Integer, primary_key=True)
    name=Column(String)
    from_date = Column(DateTime)
    to_date = Column(DateTime)
    cost = Column(Float)
    payer = Column(String)
    description=Column(String)

    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))


#_____________personal worked shifts and payment record_______________________


class Personal(Base):
    __tablename__ = "personal"

    id = Column(Integer, primary_key=True)
    first_name = Column(String(250))
    last_name = Column(String(250))
    nationality_code = Column(String(20), unique=True)
    email= Column(String(250))
    phone =  Column(String(30))
    address = Column(String(300))
    hire_date = Column(DateTime)
    position = Column(String(250))
    monthly_hr = Column(Float)
    monthly_payment = Column(Float)
    active = Column(Boolean)
    description = Column(String(300))

    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))


    payments = relationship("RecordEmployeePayment", back_populates="personal")
    shift_record = relationship("WorkShiftRecord", back_populates="personal")
    assignments = relationship("PersonalAssignment", back_populates="personal")


class PersonalAssignment(Base):
    __tablename__ = "personal_assignment"

    personal_id = Column(ForeignKey("personal.id"), primary_key=True)
    position_id = Column(ForeignKey("target_position_and_salary.id"), primary_key=True)
    shift_id = Column(ForeignKey("shift.id"))
    active = Column(Boolean, default=True)

    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    personal = relationship("Personal", back_populates="assignments")
    position = relationship("TargetPositionAndSalary")
    shift = relationship("Shift")

class WorkShiftRecord(Base):
    __tablename__ = "working_shift_record"

    id = Column(Integer, primary_key=True)
    personal_id = Column(ForeignKey("personal.id"))
    date = Column(DateTime)
    start_hr = Column(Time)
    end_hr = Column(Time)
    worked_hr = Column(Float)
    lunch_payed = Column(Float)
    service_payed = Column(Float)
    extra_payed = Column(Float)
    description = Column(String(500))

    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))


    personal = relationship("Personal", back_populates="shift_record")


class RecordEmployeePayment(Base):
    __tablename__ = "record_employee_payment"

    id = Column(Integer, primary_key=True)
    personal_id = Column(ForeignKey("personal.id"))
    from_date = Column(DateTime)
    to_date = Column(DateTime)
    payment = Column(Float)
    insurance = Column(Float)
    work_hr = Column(Float)
    extra_hr = Column(Float)
    extra_expenses = Column(Float)
    description = Column(String)

    time_create = Column(DateTime, default=lambda: datetime.now(timezone.utc))


    personal = relationship("Personal", back_populates="payments")



render_er(Base, 'erd_from_sqlalchemy.png')
