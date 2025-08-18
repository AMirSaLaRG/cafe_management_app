from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey, DateTime, TIMESTAMP, \
    Time
from sqlalchemy.orm import declarative_base, relationship
from eralchemy import render_er

Base = declarative_base()

class Inventory(Base):
    __tablename__ = 'inventory'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    unit = Column(String(50))
    current_stock = Column(Float)  # Auto-updated by system
    category = Column(String(255))
    price_per_unit = Column(Float)
    initial_value = Column(Float)
    date_of_initial_value = Column(Date)

    recipes = relationship("Recipe", back_populates="inventory_item")
    supply_record = relationship("SupplyRecord", back_populates="inventory_item")
    usage_records = relationship("InventoryUsage", back_populates="inventory_item")
    records = relationship("InventoryRecord", back_populates="inventory_item")


class InventoryRecord(Base):
    __tablename__ = "inventory_record"

    id = Column(Integer, primary_key=True)
    inventory_id = Column(ForeignKey('inventory.id'))
    sold_amount = Column(Float)
    other_used_amount = Column(Float)
    supplied_amount = Column(Float)
    auto_calculated_amount = Column(Float)
    manual_report = Column(Float)
    date = Column(TIMESTAMP)
    description = Column(String(500))

    inventory_item = relationship("Inventory", back_populates="records")

class Menu(Base):
    __tablename__ = 'menu'

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    size = Column(String, nullable=False, default='m')
    category = Column(String)
    current_price = Column(Float)
    value_added_tax = Column(Float)
    serving = Column(Boolean, default=True)
    description = Column(String(500))

    recipe = relationship('Recipe', back_populates='menu_item')
    sales = relationship("Sales", back_populates="menu_item")
    usage_record = relationship("MenuUsage", back_populates="menu_item")
    records = relationship("EstimatedMenuPriceRecord" , back_populates="menu_item")
    forecast = relationship("SalesForecast", back_populates="menu_item")

class EstimatedMenuPriceRecord(Base):
    __tablename__ = "estimated_menu_price_record"

    id =Column(Integer, primary_key=True)
    menu_id = Column(ForeignKey("menu.id"))
    sales_forcast = Column(Integer)
    estimated_indirect_costs = Column(Float)
    direct_cost = Column(Float)
    profit = Column(Float)

    estimated_price = Column(Float)
    manual_price = Column(Float)
    from_date = Column(Date)
    estimated_to_date = Column(Date)

    description = Column(String(500))

    menu_item = relationship("Menu", back_populates="records")




class Recipe(Base):
    __tablename__ = "recipe"

    inventory_id = Column(ForeignKey('inventory.id'), primary_key=True)
    menu_id = Column(ForeignKey("menu.id"), primary_key=True)
    inventory_item_amount_usage = Column(Float)
    writer = Column(String(100))
    recipe_note = Column(String(500))

    menu_item = relationship("Menu", back_populates='recipe')
    inventory_item = relationship("Inventory", back_populates="recipes")

#_______________THIS TABLES CAN ADD ITEM TO MY INVENTORY__________________________
class Supplier(Base):
    __tablename__ = "supplier"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    contact_channel = Column(String)
    contact_address = Column(String)

    orders = relationship("Order", back_populates="supplier")


class Order(Base):
    __tablename__ = "order"

    id = Column(Integer, primary_key=True)
    supplier_id = Column(ForeignKey('supplier.id'))
    date = Column(DateTime)
    buyer= Column(String)
    payer = Column(String)
    description = Column(String(500))

    supplier = relationship("Supplier", back_populates="orders")
    ship = relationship("Ship", back_populates="order")
    supply_record = relationship("SupplyRecord", back_populates="order")

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

    order = relationship("Order", back_populates="ship")

class SupplyRecord(Base):
    __tablename__ = "supply_record"

    inventory_item_id = Column(ForeignKey('inventory.id'), primary_key=True)
    order_id = Column(ForeignKey('order.id'), primary_key=True)
    box_amount = Column(Float)
    box_price = Column(Float)
    box_discount = Column(Float)
    num_of_box = Column(Float)
    description = Column(String(500))

    inventory_item = relationship("Inventory", back_populates="supply_record")
    order = relationship("Order", back_populates="supply_record")
#_______________THIS TABLES CAN DEDUCT ITEM FROM MY INVENTORY__________________________

class Invoice(Base):
    __tablename__ = 'invoice'

    id = Column(Integer, primary_key=True)
    saler = Column(String)
    date = Column(DateTime)
    payment_method = Column(String)
    description = Column(String(500))

    sales = relationship("Sales", back_populates="invoice")

class Sales(Base):
    __tablename__ = 'sales'
    menu_id = Column(ForeignKey("menu.id"), primary_key=True)
    invoice_id = Column(ForeignKey('invoice.id'), primary_key=True)
    number = Column(Integer)
    discount = Column(Float)
    payment = Column(Float)

    menu_item = relationship("Menu", back_populates="sales")
    invoice = relationship("Invoice", back_populates="sales")

class Usage(Base):
    __tablename__ = 'usage'

    id = Column(Integer, primary_key=True)
    used_by = Column(String)
    date = Column(DateTime)
    category_of_use = Column(String)
    description = Column(String(500))

    inventory_usage = relationship("InventoryUsage", back_populates="usage")
    menu_usage = relationship("MenuUsage", back_populates="usage")

class InventoryUsage(Base):
    __tablename__ = "inventory_usage"

    inventory_item_id = Column(ForeignKey('inventory.id'), primary_key=True)
    usage_id = Column(ForeignKey("usage.id"), primary_key=True)
    amount = Column(Float)

    inventory_item = relationship("Inventory", back_populates="usage_records")
    usage = relationship("Usage", back_populates="inventory_usage")

class MenuUsage(Base):
    __tablename__ = "menu_usage"

    menu_id = Column(ForeignKey("menu.id"), primary_key=True)
    usage_id = Column(ForeignKey("usage.id"), primary_key=True)
    amount = Column(Float)

    menu_item= relationship("Menu", back_populates="usage_record")
    usage = relationship("Usage", back_populates="menu_usage")



#_______________THIS TABLES WE TRY TO ESTIMATE HOW THINK WILL BE FROM EXP TO GET PREDICT INDIRECT COSTS __________________________

class SalesForecast(Base):
    __tablename__ = "sales_forecast"

    id = Column(Integer, primary_key=True)
    menu_item_id = Column(ForeignKey("menu.id"))

    from_date = Column(Date)
    to_date = Column(Date)

    sell_number = Column(Integer)

    menu_item = relationship("Menu", back_populates="forecast")

#CLEANING AS WELL
class EstimatedBills(Base):
    __tablename__ = "estimated_bills"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    cost = Column(Float)
    from_date = Column(Date)
    to_date = Column(Date)
    description = Column(String(500))

class TargetPositionAndSalary(Base):
    __tablename__ = "target_position_and_salary"

    id = Column(Integer, primary_key=True)
    position = Column(String(250), nullable=False)
    from_date = Column(Date)
    to_date = Column(Date)
    monthly_hr = Column(Integer)
    monthly_payment = Column(Float)
    monthly_insurance = Column(Float)
    extra_hr_payment = Column(Float)

    shifts = relationship("Shift", back_populates="target_position")


class Shift(Base):
    __tablename__ = "shift"

    id = Column(Integer, primary_key=True)
    target_position_id = Column(ForeignKey("target_position_and_salary.id"))
    date = Column(Date)
    from_hr = Column(Time)
    to_hr = Column(Time)
    name = Column(String)
    lunch_payment = Column(Float)
    service_payment = Column(Float)
    extra_payment = Column(Float)
    description = Column(String(500))

    target_position = relationship("TargetPositionAndSalary", back_populates="shifts")
    shift_record = relationship("WorkShiftRecord", back_populates="shift")


#_______________THIS TABLES HELPS TO FORECAST INDIRECT COSTS BUT THEY ARE CONSTANT MOSTLY SO HELPS RECORD AS WELL__________________________

class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    category = Column(String)
    purchase_date = Column(Date)
    perche_price = Column(Float)
    payer = Column(String)
    in_use= Column(Boolean)
    expire_date = Column(Date)
    monthly_depreciation = Column(Float)
    description = Column(String(500))

class Rent(Base):
    __tablename__ = "rent"

    id = Column(Integer, primary_key=True)
    rent = Column(Float)
    mortgage = Column(Float)
    mortgage_percentage_to_rent = Column(Float)
    from_date = Column(Date)
    to_date = Column(Date)
    payer = Column(String)
    description = Column(String(500))

#_____________ THIS TABLES HELP RECORD AND SEE WHAT REALITY LOOKS LIKE _________________________

#Cleaning should be in this
class Bills(Base):
    __tablename__ = 'bills'

    id = Column(Integer, primary_key=True)
    name=Column(String)
    from_date = Column(Date)
    to_date = Column(Date)
    cost = Column(Float)
    payer = Column(String)
    description=Column(String)

#_____________personal worked shifts and payment record_______________________


class Personal(Base):
    __tablename__ = "personal"

    id = Column(Integer, primary_key=True)
    first_name = Column(String(250))
    last_name = Column(String(250))
    nationality_code = Column(String(20))
    email= Column(String(250))
    phone =  Column(String(30))
    address = Column(String(300))
    hire_date = Column(Date)
    position = Column(String(250))
    active = Column(Boolean)
    description = Column(String(300))

    payments = relationship("RecordEmployeePayment", back_populates="personal")
    shift_record = relationship("WorkShiftRecord", back_populates="personal")
class WorkShiftRecord(Base):
    __tablename__ = "working_shift_record"

    id = Column(Integer, primary_key=True)
    shift_id = Column(ForeignKey("shift.id"))
    personal_id = Column(ForeignKey("personal.id"))
    start_hr = Column(Time)
    end_hr = Column(Time)
    worked_hr = Column(Float)
    lunch_payed = Column(Float)
    service_payed = Column(Float)
    extra_payed = Column(Float)
    description = Column(String(500))

    shift = relationship("Shift", back_populates="shift_record")
    personal = relationship("Personal", back_populates="shift_record")


class RecordEmployeePayment(Base):
    __tablename__ = "record_employee_payment"

    id = Column(Integer, primary_key=True)
    personal_id = Column(ForeignKey("personal.id"))
    from_date = Column(Date)
    to_date = Column(Date)
    payment = Column(Float)
    insurance = Column(Float)
    work_hr = Column(Float)
    extra_hr = Column(Float)
    extra_expenses = Column(Float)

    personal = relationship("Personal", back_populates="payments")



# render_er(Base, 'erd_from_sqlalchemy.png')
