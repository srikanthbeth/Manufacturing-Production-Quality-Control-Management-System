from enum import Enum


class UserRole(str, Enum):
    SUPER_ADMIN = "Super Admin"
    PLANT_MANAGER = "Plant Manager"
    PRODUCTION_MANAGER = "Production Manager"
    QUALITY_MANAGER = "Quality Manager"
    MAINTENANCE_ENGINEER = "Maintenance Engineer"
    STORE_MANAGER = "Store Manager"
    PRODUCTION_SUPERVISOR = "Production Supervisor"
    WORKER = "Worker"


class AccountStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"

from enum import Enum


class UserRole(str, Enum):
    SUPER_ADMIN = "Super Admin"
    PLANT_MANAGER = "Plant Manager"
    PRODUCTION_MANAGER = "Production Manager"
    QUALITY_MANAGER = "Quality Manager"
    MAINTENANCE_ENGINEER = "Maintenance Engineer"
    STORE_MANAGER = "Store Manager"
    PRODUCTION_SUPERVISOR = "Production Supervisor"
    WORKER = "Worker"


class AccountStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"


class PlantStatus(str, Enum):
    ACTIVE = "Active"
    MAINTENANCE = "Maintenance"
    TEMPORARILY_CLOSED = "Temporarily Closed"
    INACTIVE = "Inactive"

class ProductionLineStatus(str, Enum):
    ACTIVE = "Active"
    MAINTENANCE = "Maintenance"
    INACTIVE = "Inactive"

class ProductStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    DISCONTINUED = "Discontinued"

class MaterialStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    DISCONTINUED = "Discontinued"


class MaterialTransactionType(str, Enum):
    STOCK_IN = "Stock In"
    STOCK_OUT = "Stock Out"
    ADJUSTMENT = "Adjustment"

class MachineStatus(str, Enum):
    RUNNING = "Running"
    IDLE = "Idle"
    MAINTENANCE = "Maintenance"
    BREAKDOWN = "Breakdown"
    DECOMMISSIONED = "Decommissioned"

class ProductionOrderStatus(str, Enum):
    DRAFT = "Draft"
    SCHEDULED = "Scheduled"
    IN_PROGRESS = "In Progress"
    PAUSED = "Paused"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class ProductionOrderPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"