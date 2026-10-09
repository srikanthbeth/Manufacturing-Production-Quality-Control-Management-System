from fastapi import FastAPI

from routes.auth import router as auth_router
from routes.plant import router as plant_router
from routes.production_line import router as production_line_router
from routes.product import router as product_router
from routes.raw_material import router as raw_material_router
from routes.bom import router as bom_router
from routes.machine import router as machine_router
from routes.production_order import (
    router as production_order_router,
)
from routes.production_batch import (
    router as production_batch_router,
)

from routes.workers import router as workers_router
from routes.shifts import router as shifts_router
from routes.quality_inspection import router as quality_inspection_router
from routes.defect import router as defect_router
from routes.maintenance import router as maintenance_router
from routes.downtime import router as downtime_router
from routes.inventory_movement import (
    router as inventory_movement_router,
)
from routes.production_approval import router as production_approval_router
from routes.dashboard import router as dashboard_router
from routes.reports import router as reports_router
from routes.audit_logs import router as audit_logs_router



app = FastAPI(
    title="Manufacturing Production & Quality Control Management System",
    description=(
        "Advanced FastAPI backend for manufacturing production, "
        "quality, inventory, machines, maintenance and "
        "operational analytics."
    ),
    version="1.0.0",
)


app.include_router(auth_router)
app.include_router(plant_router)
app.include_router(production_line_router)
app.include_router(product_router)
app.include_router(raw_material_router)
app.include_router(bom_router)
app.include_router(machine_router)
app.include_router(production_order_router)
app.include_router(production_batch_router)
app.include_router(workers_router)
app.include_router(shifts_router)
app.include_router(quality_inspection_router)
app.include_router(defect_router)
app.include_router(
    maintenance_router
)
app.include_router(downtime_router)
app.include_router(
    inventory_movement_router
)
app.include_router(production_approval_router)
app.include_router(dashboard_router)
app.include_router(reports_router)
app.include_router(audit_logs_router)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "manufacturing-production-quality",
    }