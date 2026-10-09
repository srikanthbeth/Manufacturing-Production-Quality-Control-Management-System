import os
from datetime import datetime, date

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "manufacturing_production_quality_test"
)

from fastapi.testclient import TestClient
from sqlalchemy import text

from database import Base, SessionLocal, engine
from main import app


client = TestClient(app)


def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def create_admin():
    email = "reports_admin@example.com"
    password = "Admin@12345"

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Reports Admin",
            "email": email,
            "password": password,
        },
    )

    assert response.status_code in [200, 201], response.text

    db = SessionLocal()

    try:
        db.execute(
            text(
                """
                UPDATE users
                SET role = :role
                WHERE email = :email
                """
            ),
            {
                "role": "SUPER_ADMIN",
                "email": email,
            },
        )
        db.commit()

        user_id = db.execute(
            text(
                """
                SELECT id
                FROM users
                WHERE email = :email
                """
            ),
            {"email": email},
        ).scalar_one()

    finally:
        db.close()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200, response.text

    token = response.json()["access_token"]

    return token, user_id


def get_enum_value(db, enum_type_name, preferred_values):
    values = db.execute(
        text(
            """
            SELECT unnest(enum_range(NULL::<enum_type>))
            """.replace("<enum_type>", enum_type_name)
        )
    ).scalars().all()

    for preferred in preferred_values:
        if preferred in values:
            return preferred

    if values:
        return values[0]

    raise AssertionError(
        f"No values found for PostgreSQL enum: {enum_type_name}"
    )


def create_test_production_order_and_batch(db, user_id):
    now = datetime.utcnow()

    plant_status = get_enum_value(
        db,
        "plant_status",
        [
            "ACTIVE",
            "Active",
            "active",
        ],
    )

    line_status = get_enum_value(
        db,
        "production_line_status",
        [
            "ACTIVE",
            "Active",
            "active",
        ],
    )

    order_status = get_enum_value(
        db,
        "production_order_status",
        [
            "COMPLETED",
            "Completed",
            "completed",
        ],
    )

    priority = get_enum_value(
        db,
        "production_order_priority",
        [
            "MEDIUM",
            "Medium",
            "medium",
            "NORMAL",
            "Normal",
            "normal",
            "HIGH",
            "High",
            "high",
            "LOW",
            "Low",
            "low",
        ],
    )

    product_status = get_enum_value(
        db,
        "product_status",
        [
            "ACTIVE",
            "Active",
            "active",
        ],
    )

    machine_status = get_enum_value(
        db,
        "machine_status",
        [
            "RUNNING",
            "Running",
            "running",
            "IDLE",
            "Idle",
            "idle",
        ],
    )

    plant_result = db.execute(
        text(
            """
            INSERT INTO plants
            (
                name,
                code,
                address,
                city,
                state,
                country,
                production_capacity,
                status,
                created_at,
                updated_at
            )
            VALUES
            (
                :name,
                :code,
                :address,
                :city,
                :state,
                :country,
                :production_capacity,
                :status,
                :created_at,
                :updated_at
            )
            RETURNING id
            """
        ),
        {
            "name": "Report Plant",
            "code": "RPT-PLANT-001",
            "address": "Industrial Area",
            "city": "Tirupati",
            "state": "Andhra Pradesh",
            "country": "India",
            "production_capacity": 50000,
            "status": plant_status,
            "created_at": now,
            "updated_at": now,
        },
    )

    plant_id = plant_result.scalar_one()

    line_result = db.execute(
        text(
            """
            INSERT INTO production_lines
            (
                name,
                code,
                production_capacity,
                plant_id,
                status,
                supervisor_id,
                created_at,
                updated_at
            )
            VALUES
            (
                :name,
                :code,
                :production_capacity,
                :plant_id,
                :status,
                :supervisor_id,
                :created_at,
                :updated_at
            )
            RETURNING id
            """
        ),
        {
            "name": "Report Production Line",
            "code": "RPT-LINE-001",
            "production_capacity": 5000,
            "plant_id": plant_id,
            "status": line_status,
            "supervisor_id": user_id,
            "created_at": now,
            "updated_at": now,
        },
    )

    line_id = line_result.scalar_one()

    machine_result = db.execute(
        text(
            """
            INSERT INTO machines
            (
                machine_code,
                machine_type,
                production_line_id,
                installation_date,
                status,
                operating_hours,
                created_at,
                updated_at
            )
            VALUES
            (
                :machine_code,
                :machine_type,
                :production_line_id,
                :installation_date,
                :status,
                :operating_hours,
                :created_at,
                :updated_at
            )
            RETURNING id
            """
        ),
        {
            "machine_code": "RPT-MACHINE-001",
            "machine_type": "Production Machine",
            "production_line_id": line_id,
            "installation_date": date.today(),
            "status": machine_status,
            "operating_hours": 100,
            "created_at": now,
            "updated_at": now,
        },
    )

    machine_id = machine_result.scalar_one()

    product_result = db.execute(
        text(
            """
            INSERT INTO products
            (
                name,
                category,
                sku,
                unit_of_measurement,
                status,
                standard_production_time,
                created_at,
                updated_at
            )
            VALUES
            (
                :name,
                :category,
                :sku,
                :unit_of_measurement,
                :status,
                :standard_production_time,
                :created_at,
                :updated_at
            )
            RETURNING id
            """
        ),
        {
            "name": "Report Product",
            "category": "Finished Goods",
            "sku": "RPT-SKU-001",
            "unit_of_measurement": "pcs",
            "status": product_status,
            "standard_production_time": 60,
            "created_at": now,
            "updated_at": now,
        },
    )

    product_id = product_result.scalar_one()

    order_result = db.execute(
        text(
            """
            INSERT INTO production_orders
            (
                order_number,
                product_id,
                quantity,
                target_date,
                production_line_id,
                priority,
                supervisor_id,
                status,
                created_at,
                updated_at
            )
            VALUES
            (
                :order_number,
                :product_id,
                :quantity,
                :target_date,
                :production_line_id,
                :priority,
                :supervisor_id,
                :status,
                :created_at,
                :updated_at
            )
            RETURNING id
            """
        ),
        {
            "order_number": "RPT-ORDER-001",
            "product_id": product_id,
            "quantity": 1000,
            "target_date": date.today(),
            "production_line_id": line_id,
            "priority": priority,
            "supervisor_id": user_id,
            "status": order_status,
            "created_at": now,
            "updated_at": now,
        },
    )

    production_order_id = order_result.scalar_one()

    batch_result = db.execute(
        text(
            """
            INSERT INTO production_batches
            (
                batch_number,
                production_order_id,
                planned_quantity,
                produced_quantity,
                rejected_quantity,
                start_time,
                end_time,
                production_line_id,
                machine_id,
                supervisor_id,
                completion_percentage,
                rejection_percentage,
                production_efficiency,
                created_at,
                updated_at
            )
            VALUES
            (
                :batch_number,
                :production_order_id,
                :planned_quantity,
                :produced_quantity,
                :rejected_quantity,
                :start_time,
                :end_time,
                :production_line_id,
                :machine_id,
                :supervisor_id,
                :completion_percentage,
                :rejection_percentage,
                :production_efficiency,
                :created_at,
                :updated_at
            )
            RETURNING id
            """
        ),
        {
            "batch_number": "RPT-BATCH-001",
            "production_order_id": production_order_id,
            "planned_quantity": 1000,
            "produced_quantity": 900,
            "rejected_quantity": 100,
            "start_time": now,
            "end_time": now,
            "production_line_id": line_id,
            "machine_id": machine_id,
            "supervisor_id": user_id,
            "completion_percentage": 100,
            "rejection_percentage": 10,
            "production_efficiency": 90,
            "created_at": now,
            "updated_at": now,
        },
    )

    batch_id = batch_result.scalar_one()

    db.commit()

    return {
        "plant_id": plant_id,
        "line_id": line_id,
        "machine_id": machine_id,
        "product_id": product_id,
        "production_order_id": production_order_id,
        "batch_id": batch_id,
    }


def test_reports_require_authentication():
    reset_database()

    endpoints = [
        "/api/v1/reports/daily-production",
        "/api/v1/reports/monthly-production",
        "/api/v1/reports/machine-performance",
        "/api/v1/reports/product-production",
        "/api/v1/reports/quality",
        "/api/v1/reports/defects",
        "/api/v1/reports/material-consumption",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)

        assert response.status_code == 401, (
            f"{endpoint} returned {response.status_code}: "
            f"{response.text}"
        )


def test_daily_production_report_empty():
    reset_database()

    token, _ = create_admin()

    response = client.get(
        "/api/v1/reports/daily-production",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_monthly_production_report_empty():
    reset_database()

    token, _ = create_admin()

    response = client.get(
        "/api/v1/reports/monthly-production",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_machine_performance_report_empty():
    reset_database()

    token, _ = create_admin()

    response = client.get(
        "/api/v1/reports/machine-performance",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_product_production_report_empty():
    reset_database()

    token, _ = create_admin()

    response = client.get(
        "/api/v1/reports/product-production",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_quality_report_empty():
    reset_database()

    token, _ = create_admin()

    response = client.get(
        "/api/v1/reports/quality",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_inspections"] == 0
    assert data["passed_inspections"] == 0
    assert data["failed_inspections"] == 0
    assert data["pending_inspections"] == 0
    assert data["pass_percentage"] == 0
    assert data["fail_percentage"] == 0


def test_defect_report_empty():
    reset_database()

    token, _ = create_admin()

    response = client.get(
        "/api/v1/reports/defects",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_material_consumption_report_empty():
    reset_database()

    token, _ = create_admin()

    response = client.get(
        "/api/v1/reports/material-consumption",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_quality_report_with_data():
    reset_database()

    token, user_id = create_admin()

    db = SessionLocal()

    try:
        test_data = create_test_production_order_and_batch(
            db,
            user_id,
        )

        now = datetime.utcnow()

        db.execute(
            text(
                """
                INSERT INTO quality_inspections
                (
                    inspection_number,
                    inspection_type,
                    inspector_id,
                    production_batch_id,
                    inspection_date,
                    parameters,
                    expected_value,
                    actual_value,
                    result,
                    remarks,
                    created_at,
                    updated_at
                )
                VALUES
                (
                    :inspection_number,
                    :inspection_type,
                    :inspector_id,
                    :production_batch_id,
                    :inspection_date,
                    :parameters,
                    :expected_value,
                    :actual_value,
                    :result,
                    :remarks,
                    :created_at,
                    :updated_at
                )
                """
            ),
            {
                "inspection_number": "RPT-INSP-001",
                "inspection_type": "Final",
                "inspector_id": user_id,
                "production_batch_id": test_data["batch_id"],
                "inspection_date": date.today(),
                "parameters": "Dimension",
                "expected_value": "100",
                "actual_value": "100",
                "result": "Pass",
                "remarks": "Passed inspection",
                "created_at": now,
                "updated_at": now,
            },
        )

        db.execute(
            text(
                """
                INSERT INTO quality_inspections
                (
                    inspection_number,
                    inspection_type,
                    inspector_id,
                    production_batch_id,
                    inspection_date,
                    parameters,
                    expected_value,
                    actual_value,
                    result,
                    remarks,
                    created_at,
                    updated_at
                )
                VALUES
                (
                    :inspection_number,
                    :inspection_type,
                    :inspector_id,
                    :production_batch_id,
                    :inspection_date,
                    :parameters,
                    :expected_value,
                    :actual_value,
                    :result,
                    :remarks,
                    :created_at,
                    :updated_at
                )
                """
            ),
            {
                "inspection_number": "RPT-INSP-002",
                "inspection_type": "Final",
                "inspector_id": user_id,
                "production_batch_id": test_data["batch_id"],
                "inspection_date": date.today(),
                "parameters": "Dimension",
                "expected_value": "100",
                "actual_value": "95",
                "result": "Fail",
                "remarks": "Failed inspection",
                "created_at": now,
                "updated_at": now,
            },
        )

        db.execute(
            text(
                """
                INSERT INTO quality_inspections
                (
                    inspection_number,
                    inspection_type,
                    inspector_id,
                    production_batch_id,
                    inspection_date,
                    parameters,
                    expected_value,
                    actual_value,
                    result,
                    remarks,
                    created_at,
                    updated_at
                )
                VALUES
                (
                    :inspection_number,
                    :inspection_type,
                    :inspector_id,
                    :production_batch_id,
                    :inspection_date,
                    :parameters,
                    :expected_value,
                    :actual_value,
                    :result,
                    :remarks,
                    :created_at,
                    :updated_at
                )
                """
            ),
            {
                "inspection_number": "RPT-INSP-003",
                "inspection_type": "Final",
                "inspector_id": user_id,
                "production_batch_id": test_data["batch_id"],
                "inspection_date": date.today(),
                "parameters": "Dimension",
                "expected_value": "100",
                "actual_value": "100",
                "result": "Pending",
                "remarks": "Pending inspection",
                "created_at": now,
                "updated_at": now,
            },
        )

        db.commit()

    finally:
        db.close()

    response = client.get(
        "/api/v1/reports/quality",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_inspections"] == 3
    assert data["passed_inspections"] == 1
    assert data["failed_inspections"] == 1
    assert data["pending_inspections"] == 1
    assert data["pass_percentage"] == 33.33
    assert data["fail_percentage"] == 33.33


def test_defect_report_with_data():
    reset_database()

    token, user_id = create_admin()

    db = SessionLocal()

    try:
        test_data = create_test_production_order_and_batch(
            db,
            user_id,
        )

        now = datetime.utcnow()

        db.execute(
            text(
                """
                INSERT INTO defects
                (
                    defect_number,
                    defect_type,
                    severity,
                    production_batch_id,
                    product_id,
                    quantity_affected,
                    root_cause,
                    corrective_action,
                    resolution_status,
                    created_at,
                    updated_at
                )
                VALUES
                (
                    :defect_number,
                    :defect_type,
                    :severity,
                    :production_batch_id,
                    :product_id,
                    :quantity_affected,
                    :root_cause,
                    :corrective_action,
                    :resolution_status,
                    :created_at,
                    :updated_at
                )
                """
            ),
            {
                "defect_number": "RPT-DEF-001",
                "defect_type": "Dimension Error",
                "severity": "High",
                "production_batch_id": test_data["batch_id"],
                "product_id": test_data["product_id"],
                "quantity_affected": 10,
                "root_cause": "Machine calibration",
                "corrective_action": "Recalibration",
                "resolution_status": "Resolved",
                "created_at": now,
                "updated_at": now,
            },
        )

        db.execute(
            text(
                """
                INSERT INTO defects
                (
                    defect_number,
                    defect_type,
                    severity,
                    production_batch_id,
                    product_id,
                    quantity_affected,
                    root_cause,
                    corrective_action,
                    resolution_status,
                    created_at,
                    updated_at
                )
                VALUES
                (
                    :defect_number,
                    :defect_type,
                    :severity,
                    :production_batch_id,
                    :product_id,
                    :quantity_affected,
                    :root_cause,
                    :corrective_action,
                    :resolution_status,
                    :created_at,
                    :updated_at
                )
                """
            ),
            {
                "defect_number": "RPT-DEF-002",
                "defect_type": "Dimension Error",
                "severity": "High",
                "production_batch_id": test_data["batch_id"],
                "product_id": test_data["product_id"],
                "quantity_affected": 5,
                "root_cause": "Machine calibration",
                "corrective_action": "Pending",
                "resolution_status": "Open",
                "created_at": now,
                "updated_at": now,
            },
        )

        db.commit()

    finally:
        db.close()

    response = client.get(
        "/api/v1/reports/defects",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    report = data[0]

    assert report["defect_type"] == "Dimension Error"
    assert report["severity"] == "High"
    assert report["defect_count"] == 2
    assert report["quantity_affected"] == 15
    assert report["resolved_defects"] == 1
    assert report["open_defects"] == 1


def test_material_consumption_report_with_data():
    reset_database()

    token, user_id = create_admin()

    db = SessionLocal()

    try:
        material_status = get_enum_value(
            db,
            "material_status",
            [
                "ACTIVE",
                "Active",
                "active",
            ],
        )

        now = datetime.utcnow()

        material_result = db.execute(
            text(
                """
                INSERT INTO raw_materials
                (
                    name,
                    material_code,
                    category,
                    unit,
                    available_quantity,
                    minimum_stock_level,
                    reorder_level,
                    supplier_reference,
                    status,
                    created_at,
                    updated_at
                )
                VALUES
                (
                    :name,
                    :material_code,
                    :category,
                    :unit,
                    :available_quantity,
                    :minimum_stock_level,
                    :reorder_level,
                    :supplier_reference,
                    :status,
                    :created_at,
                    :updated_at
                )
                RETURNING id
                """
            ),
            {
                "name": "Report Material",
                "material_code": "RPT-MAT-001",
                "category": "Raw Material",
                "unit": "kg",
                "available_quantity": 300,
                "minimum_stock_level": 100,
                "reorder_level": 200,
                "supplier_reference": "RPT-SUP-001",
                "status": material_status,
                "created_at": now,
                "updated_at": now,
            },
        )

        material_id = material_result.scalar_one()

        db.execute(
            text(
                """
                INSERT INTO inventory_movements
                (
                    transaction_number,
                    raw_material_id,
                    movement_type,
                    quantity,
                    stock_before,
                    stock_after,
                    reference_number,
                    reason,
                    created_by_id,
                    created_at
                )
                VALUES
                (
                    :transaction_number,
                    :raw_material_id,
                    :movement_type,
                    :quantity,
                    :stock_before,
                    :stock_after,
                    :reference_number,
                    :reason,
                    :created_by_id,
                    :created_at
                )
                """
            ),
            {
                "transaction_number": "RPT-INV-001",
                "raw_material_id": material_id,
                "movement_type": "Stock In",
                "quantity": 500,
                "stock_before": 0,
                "stock_after": 500,
                "reference_number": "RPT-REF-001",
                "reason": "Purchase",
                "created_by_id": user_id,
                "created_at": now,
            },
        )

        db.execute(
            text(
                """
                INSERT INTO inventory_movements
                (
                    transaction_number,
                    raw_material_id,
                    movement_type,
                    quantity,
                    stock_before,
                    stock_after,
                    reference_number,
                    reason,
                    created_by_id,
                    created_at
                )
                VALUES
                (
                    :transaction_number,
                    :raw_material_id,
                    :movement_type,
                    :quantity,
                    :stock_before,
                    :stock_after,
                    :reference_number,
                    :reason,
                    :created_by_id,
                    :created_at
                )
                """
            ),
            {
                "transaction_number": "RPT-INV-002",
                "raw_material_id": material_id,
                "movement_type": "Stock Out",
                "quantity": 200,
                "stock_before": 500,
                "stock_after": 300,
                "reference_number": "RPT-REF-002",
                "reason": "Production consumption",
                "created_by_id": user_id,
                "created_at": now,
            },
        )

        db.commit()

    finally:
        db.close()

    response = client.get(
        "/api/v1/reports/material-consumption",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1

    report = data[0]

    assert report["material_id"] == material_id
    assert report["material_name"] == "Report Material"
    assert report["material_code"] == "RPT-MAT-001"
    assert report["stock_in"] == 500
    assert report["stock_out"] == 200
    assert report["consumption"] == 200
    assert report["current_stock"] == 300
    assert report["minimum_stock_level"] == 100
    assert report["reorder_level"] == 200
    assert report["stock_status"] == "Normal"