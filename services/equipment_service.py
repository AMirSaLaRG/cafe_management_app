from models.cafe_managment_models import Equipment
from models.dbhandler import DBHandler
from typing import Optional, List
from datetime import datetime, timedelta


class EquipmentService:
    def __init__(self, db_handler: DBHandler):
        self.db = db_handler

    def new_equipment_record(self,
                      name: str,
                      category: str,
                      number: int = 1,
                      purchase_date: Optional[datetime] = None,
                      purchase_price: Optional[float] = None,
                      payer: Optional[str] = None,
                      in_use: bool = True,
                      expire_date: Optional[datetime] = None,
                      monthly_depreciation: Optional[float] = None,
                      description: Optional[str] = None) -> Optional[Equipment]:
        """Add new equipment to the system"""
        return self.db.add_equipment(
            name=name,
            category=category,
            number=number,
            purchase_date=purchase_date,
            purchase_price=purchase_price,
            payer=payer,
            in_use=in_use,
            expire_date=expire_date,
            monthly_depreciation=monthly_depreciation,
            description=description
        )

    def update_equipment(self, equipment: Equipment) -> Optional[Equipment]:
        """Update existing equipment information"""
        return self.db.edit_equipment(equipment)

    def remove_equipment(self, equipment_id: int) -> bool:
        """Permanently delete equipment from the system"""
        equipment = Equipment(id=equipment_id)
        return self.db.delete_equipment(equipment)

    def get_equipment_by_id(self, equipment_id: int) -> Optional[Equipment]:
        """Get specific equipment by ID"""
        results = self.db.get_equipment(id=equipment_id)
        return results[0] if results else None

    def find_equipment(self,
                       name: Optional[str] = None,
                       category: Optional[str] = None,
                       in_use: Optional[bool] = None,
                       row_num: Optional[int] = None) -> List[Equipment]:
        """Search for equipment with various filters"""
        return self.db.get_equipment(
            name=name,
            category=category,
            in_use=in_use,
            row_num=row_num
        )

    def get_all_equipment(self, row_num: Optional[int] = None) -> List[Equipment]:
        """Get all equipment in the system"""
        return self.db.get_equipment(row_num=row_num)

    def deactivate_equipment(self, equipment_id: int) -> Optional[Equipment]:
        """Mark equipment as not in use"""
        equipment = self.get_equipment_by_id(equipment_id)
        if equipment:
            equipment.in_use = False
            return self.update_equipment(equipment)
        return None

    def activate_equipment(self, equipment_id: int) -> Optional[Equipment]:
        """Mark equipment as in use"""
        equipment = self.get_equipment_by_id(equipment_id)
        if equipment:
            equipment.in_use = True
            return self.update_equipment(equipment)
        return None

    def calculate_monthly_depreciation(self, equipment_id: int) -> Optional[float]:
        """Calculate or retrieve monthly depreciation for equipment"""
        equipment = self.get_equipment_by_id(equipment_id)
        if equipment and equipment.monthly_depreciation:
            return equipment.monthly_depreciation

        # You could add custom depreciation calculation logic here
        # For example, based on purchase price and expected lifespan
        return None

    def calculate_estimated_monthly_depreciation(self, equipment_id: int,
                                                 estimated_price: float,
                                                 estimation_date: datetime) -> Optional[float]:
        """
        Calculate monthly depreciation based on current depreciated value vs estimated future value.

        Args:
            equipment_id: ID of the equipment to calculate depreciation for
            estimated_price: Estimated future value of the equipment
            estimation_date: Date when this estimated value is expected

        Returns:
            Monthly depreciation amount based on the estimation, or None if calculation fails
        """
        # Get current equipment details
        equipment = self.get_equipment_by_id(equipment_id)
        if not equipment:
            return None

        # Calculate current depreciated value
        current_value = self._calculate_current_depreciated_value(equipment)
        if current_value <= 0:
            return None

        # Calculate time difference in months
        current_date = datetime.now()
        months_diff = (estimation_date.year - current_date.year) * 12 + (estimation_date.month - current_date.month)

        # Ensure we have a positive time period
        if months_diff <= 0:
            return None

        # Calculate monthly depreciation
        total_depreciation = current_value - estimated_price
        if months_diff == 0:
            return None

        monthly_depreciation = total_depreciation / months_diff

        # Return only positive depreciation (equipment shouldn't appreciate in this context)
        return max(monthly_depreciation, 0)

    def _calculate_current_depreciated_value(self, equipment: Equipment) -> float:
        """
        Calculate the current depreciated value of equipment based on purchase price
        and elapsed time using monthly depreciation rate.
        """
        if not equipment.purchase_price or not equipment.purchase_date:
            return equipment.purchase_price or 0

        # Calculate elapsed months since purchase
        current_date = datetime.now()
        elapsed_months = (current_date.year - equipment.purchase_date.year) * 12 + \
                         (current_date.month - equipment.purchase_date.month)

        # Use provided monthly depreciation if available
        if equipment.monthly_depreciation:
            depreciated_amount = equipment.monthly_depreciation * elapsed_months
            return max(equipment.purchase_price - depreciated_amount, 0)

        # Fallback: calculate based on useful life assumption (5 years default)
        useful_life_months = 60  # 5 years
        monthly_depreciation_rate = equipment.purchase_price / useful_life_months
        depreciated_amount = monthly_depreciation_rate * elapsed_months
        return max(equipment.purchase_price - depreciated_amount, 0)

    def get_equipment_by_purchase_date_range(self,
                                             start_date: datetime,
                                             end_date: datetime) -> List[Equipment]:
        """Get equipment purchased within a date range"""
        return self.db.get_equipment(
            purchase_from_date=start_date,
            purchase_to_date=end_date
        )

    def get_equipment_nearing_expiration(self,
                                         threshold_days: int = 30) -> List[Equipment]:
        """Get equipment that will expire within the threshold days"""
        from datetime import datetime, timedelta
        threshold_date = datetime.now() + timedelta(days=threshold_days)
        return self.db.get_equipment(
            expire_to_date=threshold_date
        )