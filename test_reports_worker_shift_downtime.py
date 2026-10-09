from datetime import datetime, time, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import text

from database import SessionLocal
from main import app


client = TestClient(app)


def create_admin():
    email = "reports_advanced_admin@example.com"

    db = SessionLocal()

    try:
        user_id = db.execute(
            text(
                """
                SELECT id
                FROM users
                WHERE email = :email
                """
            ),
            {"email": email},
        ).scalar()

        if user_id is None:
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "full_name": "Reports Advanced Admin",
                    "email": email,
                    "password": "Admin@12345",
                },
            )

            assert response.status_code in [200, 201], response.text

        db.commit()

    finally:
        db.close()

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

    finally:
        db.close()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "Admin@12345",
        },
    )

    assert response.status_code == 200, response.text

    return response.json()["access_token"]


def create_worker_user():
    email = "report_worker@example.com"

    db = SessionLocal()

    try:
        user_id = db.execute(
            text(
                """
                SELECT id
                FROM users
                WHERE email = :email
                """
            ),
            {"email": email},
        ).scalar()

        if user_id is None:
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "full_name": "Report Worker",
                    "email": email,
                    "password": "Worker@12345",
                },
            )

            assert response.status_code in [200, 201], response.text

        db.commit()

    finally:
        db.close()

    return {
        "email": email,
        "password": "Worker@12345",
        "full_name": "Report Worker",
    }


def get_user_id(email):
    db = SessionLocal()

    try:
        return db.execute(
            text(
                """
                SELECT id
                FROM users
                WHERE email = :email
                """
            ),
            {"email": email},
        ).scalar()

    finally:
        db.close()


def create_worker_record():
    worker_user = create_worker_user()

    user_id = get_user_id(worker_user["email"])

    db = SessionLocal()

    try:
        existing = db.execute(
            text(
                """
                SELECT id
                FROM workers
                WHERE user_id = :user_id
                """
            ),
            {"user_id": user_id},
        ).scalar()

        if existing:
            return existing, user_id

        worker_id = db.execute(
            text(
                """
                INSERT INTO workers (
                    user_id,
                    employee_code,
                    skill,
                    department,
                    shift,
                    status
                )
                VALUES (
                    :user_id,
                    :employee_code,
                    :skill,
                    :department,
                    :shift,
                    :status
                )
                RETURNING id
                """
            ),
            {
                "user_id": user_id,
                "employee_code": "RPT-W-001",
                "skill": "Production",
                "department": "Manufacturing",
                "shift": "Morning",
                "status": "Active",
            },
        ).scalar()

        db.commit()

        return worker_id, user_id

    finally:
        db.close()


def create_shift():
    db = SessionLocal()

    try:
        existing = db.execute(
            text(
                """
                SELECT id
                FROM shifts
                WHERE name = :name
                """
            ),
            {"name": "Report Morning Shift"},
        ).scalar()

        if existing:
            return existing

        shift_id = db.execute(
            text(
                """
                INSERT INTO shifts (
                    name,
                    start_time,
                    end_time,
                    description,
                    is_active
                )
                VALUES (
                    :name,
                    :start_time,
                    :end_time,
                    :description,
                    :is_active
                )
                RETURNING id
                """
            ),
            {
                "name": "Report Morning Shift",
                "start_time": time(8, 0),
                "end_time": time(16, 0),
                "description": "Report test shift",
                "is_active": True,
            },
        ).scalar()

        db.commit()

        return shift_id

    finally:
        db.close()


def create_machine():
    db = SessionLocal()

    try:
        machine_code = "RPT-M-001"

        existing_machine = db.execute(
            text(
                """
                SELECT id
                FROM machines
                WHERE machine_code = :machine_code
                LIMIT 1
                """
            ),
            {"machine_code": machine_code},
        ).fetchone()

        if existing_machine:
            return existing_machine[0]

        production_line = db.execute(
            text(
                """
                SELECT id
                FROM production_lines
                LIMIT 1
                """
            )
        ).fetchone()

        if not production_line:
            plant = db.execute(
                text(
                    """
                    SELECT id
                    FROM plants
                    LIMIT 1
                    """
                )
            ).fetchone()

            if not plant:
                raise AssertionError(
                    "No plant exists in the test database. "
                    "A plant is required before creating a production line."
                )

            existing_line = db.execute(
                text(
                    """
                    SELECT id
                    FROM production_lines
                    WHERE code = :line_code
                    LIMIT 1
                    """
                ),
                {"line_code": "RPT-LINE-001"},
            ).fetchone()

            if existing_line:
                production_line_id = existing_line[0]

            else:
                production_line_id = db.execute(
                    text(
                        """
                        INSERT INTO production_lines (
                            name,
                            code,
                            production_capacity,
                            plant_id,
                            status,
                            supervisor_id,
                            created_at,
                            updated_at
                        )
                        VALUES (
                            :name,
                            :code,
                            :production_capacity,
                            :plant_id,
                            :status,
                            :supervisor_id,
                            NOW(),
                            NOW()
                        )
                        RETURNING id
                        """
                    ),
                    {
                        "name": "Reports Test Production Line",
                        "code": "RPT-LINE-001",
                        "production_capacity": 1000,
                        "plant_id": plant[0],
                        "status": "ACTIVE",
                        "supervisor_id": None,
                    },
                ).scalar_one()

                db.commit()

        else:
            production_line_id = production_line[0]

        machine_id = db.execute(
            text(
                """
                INSERT INTO machines (
                    machine_code,
                    machine_type,
                    production_line_id,
                    installation_date,
                    status,
                    operating_hours,
                    created_at,
                    updated_at
                )
                VALUES (
                    :machine_code,
                    :machine_type,
                    :production_line_id,
                    CURRENT_DATE,
                    :status,
                    :operating_hours,
                    NOW(),
                    NOW()
                )
                RETURNING id
                """
            ),
            {
                "machine_code": machine_code,
                "machine_type": "Production Machine",
                "production_line_id": production_line_id,
                "status": "RUNNING",
                "operating_hours": 100,
            },
        ).scalar_one()

        db.commit()

        return machine_id

    finally:
        db.close()


def create_production_batch(supervisor_id, machine_id):
    db = SessionLocal()

    try:
        production_line_id = db.execute(
            text(
                """
                SELECT production_line_id
                FROM machines
                WHERE id = :machine_id
                LIMIT 1
                """
            ),
            {"machine_id": machine_id},
        ).scalar()

        if production_line_id is None:
            raise AssertionError(
                "A production line is required for the report test."
            )

        product_id = db.execute(
            text(
                """
                SELECT id
                FROM products
                ORDER BY id
                LIMIT 1
                """
            )
        ).scalar()

        if product_id is None:
            product_id = db.execute(
                text(
                    """
                    INSERT INTO products (
                        name,
                        category,
                        sku,
                        unit_of_measurement,
                        status,
                        standard_production_time,
                        created_at,
                        updated_at
                    )
                    VALUES (
                        :name,
                        :category,
                        :sku,
                        :unit_of_measurement,
                        :status,
                        :standard_production_time,
                        NOW(),
                        NOW()
                    )
                    RETURNING id
                    """
                ),
                {
                    "name": "Reports Test Product",
                    "category": "Finished Goods",
                    "sku": "RPT-PROD-001",
                    "unit_of_measurement": "UNIT",
                    "status": "ACTIVE",
                    "standard_production_time": 1.0,
                },
            ).scalar_one()

            db.commit()

        production_order_id = db.execute(
            text(
                """
                SELECT id
                FROM production_orders
                WHERE order_number = :order_number
                LIMIT 1
                """
            ),
            {"order_number": "RPT-ORD-001"},
        ).scalar()

        if production_order_id is None:
            production_order_id = db.execute(
                text(
                    """
                    INSERT INTO production_orders (
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
                    VALUES (
                        :order_number,
                        :product_id,
                        :quantity,
                        CURRENT_DATE,
                        :production_line_id,
                        :priority,
                        :supervisor_id,
                        :status,
                        NOW(),
                        NOW()
                    )
                    RETURNING id
                    """
                ),
                {
                    "order_number": "RPT-ORD-001",
                    "product_id": product_id,
                    "quantity": 100,
                    "production_line_id": production_line_id,
                    "priority": "HIGH",
                    "supervisor_id": supervisor_id,
                    "status": "COMPLETED",
                },
            ).scalar_one()

            db.commit()

        else:
            db.execute(
                text(
                    """
                    UPDATE production_orders
                    SET
                        status = :status,
                        updated_at = NOW()
                    WHERE id = :production_order_id
                    """
                ),
                {
                    "status": "COMPLETED",
                    "production_order_id": production_order_id,
                },
            )

            db.commit()

        existing_batch = db.execute(
            text(
                """
                SELECT id
                FROM production_batches
                WHERE batch_number = :batch_number
                LIMIT 1
                """
            ),
            {"batch_number": "RPT-BATCH-001"},
        ).scalar()

        if existing_batch:
            db.execute(
                text(
                    """
                    UPDATE production_batches
                    SET
                        production_order_id = :production_order_id,
                        produced_quantity = :produced_quantity,
                        rejected_quantity = :rejected_quantity,
                        completion_percentage = :completion_percentage,
                        rejection_percentage = :rejection_percentage,
                        production_efficiency = :production_efficiency,
                        end_time = :end_time,
                        updated_at = NOW()
                    WHERE id = :batch_id
                    """
                ),
                {
                    "production_order_id": production_order_id,
                    "produced_quantity": 100,
                    "rejected_quantity": 10,
                    "completion_percentage": 100.0,
                    "rejection_percentage": 10.0,
                    "production_efficiency": 90.0,
                    "end_time": datetime.now(timezone.utc),
                    "batch_id": existing_batch,
                },
            )

            db.commit()

            return existing_batch

        start_time = datetime.now(timezone.utc) - timedelta(hours=2)
        end_time = datetime.now(timezone.utc)

        batch_id = db.execute(
            text(
                """
                INSERT INTO production_batches (
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
                VALUES (
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
                    NOW(),
                    NOW()
                )
                RETURNING id
                """
            ),
            {
                "batch_number": "RPT-BATCH-001",
                "production_order_id": production_order_id,
                "planned_quantity": 100,
                "produced_quantity": 100,
                "rejected_quantity": 10,
                "start_time": start_time,
                "end_time": end_time,
                "production_line_id": production_line_id,
                "machine_id": machine_id,
                "supervisor_id": supervisor_id,
                "completion_percentage": 100.0,
                "rejection_percentage": 10.0,
                "production_efficiency": 90.0,
            },
        ).scalar_one()

        db.commit()

        return batch_id

    finally:
        db.close()


def assign_worker_to_shift(shift_id, worker_id):
    db = SessionLocal()

    try:
        existing = db.execute(
            text(
                """
                SELECT id
                FROM shift_workers
                WHERE shift_id = :shift_id
                  AND worker_id = :worker_id
                """
            ),
            {
                "shift_id": shift_id,
                "worker_id": worker_id,
            },
        ).scalar()

        if existing:
            return existing

        assignment_id = db.execute(
            text(
                """
                INSERT INTO shift_workers (
                    shift_id,
                    worker_id
                )
                VALUES (
                    :shift_id,
                    :worker_id
                )
                RETURNING id
                """
            ),
            {
                "shift_id": shift_id,
                "worker_id": worker_id,
            },
        ).scalar()

        db.commit()

        return assignment_id

    finally:
        db.close()


def create_shift_output(shift_id, batch_id):
    db = SessionLocal()

    try:
        existing = db.execute(
            text(
                """
                SELECT id
                FROM shift_production_outputs
                WHERE shift_id = :shift_id
                  AND production_batch_id = :production_batch_id
                LIMIT 1
                """
            ),
            {
                "shift_id": shift_id,
                "production_batch_id": batch_id,
            },
        ).scalar()

        if existing:
            return existing

        output_id = db.execute(
            text(
                """
                INSERT INTO shift_production_outputs (
                    shift_id,
                    production_batch_id,
                    produced_quantity,
                    rejected_quantity
                )
                VALUES (
                    :shift_id,
                    :production_batch_id,
                    :produced_quantity,
                    :rejected_quantity
                )
                RETURNING id
                """
            ),
            {
                "shift_id": shift_id,
                "production_batch_id": batch_id,
                "produced_quantity": 90,
                "rejected_quantity": 10,
            },
        ).scalar()

        db.commit()

        return output_id

    finally:
        db.close()


def create_downtime(
    machine_id,
    production_line_id,
    responsible_person_id,
):
    db = SessionLocal()

    try:
        downtime_number = "RPT-DT-001"

        existing = db.execute(
            text(
                """
                SELECT id
                FROM downtimes
                WHERE downtime_number = :downtime_number
                LIMIT 1
                """
            ),
            {"downtime_number": downtime_number},
        ).scalar()

        if existing:
            return existing

        start_time = datetime.now(timezone.utc) - timedelta(
            minutes=120
        )

        end_time = datetime.now(timezone.utc)

        downtime_id = db.execute(
            text(
                """
                INSERT INTO downtimes (
                    downtime_number,
                    machine_id,
                    production_line_id,
                    responsible_person_id,
                    category,
                    reason,
                    start_time,
                    end_time,
                    duration_minutes,
                    created_at,
                    updated_at
                )
                VALUES (
                    :downtime_number,
                    :machine_id,
                    :production_line_id,
                    :responsible_person_id,
                    :category,
                    :reason,
                    :start_time,
                    :end_time,
                    :duration_minutes,
                    NOW(),
                    NOW()
                )
                RETURNING id
                """
            ),
            {
                "downtime_number": downtime_number,
                "machine_id": machine_id,
                "production_line_id": production_line_id,
                "responsible_person_id": responsible_person_id,
                "category": "Mechanical",
                "reason": "Routine maintenance",
                "start_time": start_time,
                "end_time": end_time,
                "duration_minutes": 120,
            },
        ).scalar_one()

        db.commit()

        return downtime_id

    finally:
        db.close()


def test_worker_performance_report_requires_authentication():
    response = client.get(
        "/api/v1/reports/worker-performance"
    )

    assert response.status_code in [401, 403]


def test_worker_performance_report_empty():
    token = create_admin()

    response = client.get(
        "/api/v1/reports/worker-performance",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_worker_performance_report_with_data():
    token = create_admin()

    worker_id, worker_user_id = create_worker_record()

    machine_id = create_machine()

    create_production_batch(
        supervisor_id=worker_user_id,
        machine_id=machine_id,
    )

    response = client.get(
        "/api/v1/reports/worker-performance",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    worker = next(
        item
        for item in data
        if item["worker_id"] == worker_id
    )

    assert worker["employee_code"] == "RPT-W-001"
    assert worker["assigned_batches"] >= 1
    assert worker["completed_batches"] >= 1
    assert worker["produced_quantity"] >= 90
    assert worker["rejected_quantity"] >= 10


def test_shift_performance_report_requires_authentication():
    response = client.get(
        "/api/v1/reports/shift-performance"
    )

    assert response.status_code in [401, 403]


def test_shift_performance_report_empty():
    token = create_admin()

    response = client.get(
        "/api/v1/reports/shift-performance",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_shift_performance_report_with_data():
    token = create_admin()

    worker_id, worker_user_id = create_worker_record()

    shift_id = create_shift()

    assign_worker_to_shift(
        shift_id=shift_id,
        worker_id=worker_id,
    )

    machine_id = create_machine()

    batch_id = create_production_batch(
        supervisor_id=worker_user_id,
        machine_id=machine_id,
    )

    create_shift_output(
        shift_id=shift_id,
        batch_id=batch_id,
    )

    response = client.get(
        "/api/v1/reports/shift-performance",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    shift = next(
        item
        for item in data
        if item["shift_id"] == shift_id
    )

    assert shift["shift_name"] == "Report Morning Shift"
    assert shift["total_workers"] >= 1
    assert shift["production_orders"] >= 1
    assert shift["completed_orders"] >= 1
    assert shift["produced_quantity"] >= 90
    assert shift["rejected_quantity"] >= 10


def test_downtime_report_requires_authentication():
    response = client.get(
        "/api/v1/reports/downtime"
    )

    assert response.status_code in [401, 403]


def test_downtime_report_empty():
    token = create_admin()

    response = client.get(
        "/api/v1/reports/downtime",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_downtime_report_with_data():
    token = create_admin()

    worker_id, worker_user_id = create_worker_record()

    machine_id = create_machine()

    db = SessionLocal()

    try:
        production_line_id = db.execute(
            text(
                """
                SELECT production_line_id
                FROM machines
                WHERE id = :machine_id
                """
            ),
            {"machine_id": machine_id},
        ).scalar()

    finally:
        db.close()

    create_downtime(
        machine_id=machine_id,
        production_line_id=production_line_id,
        responsible_person_id=worker_user_id,
    )

    response = client.get(
        "/api/v1/reports/downtime",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    machine = next(
        item
        for item in data
        if item["machine_id"] == machine_id
    )

    assert machine["machine_code"] == "RPT-M-001"
    assert machine["downtime_events"] >= 1
    assert machine["total_downtime_minutes"] >= 120
    assert machine["total_downtime_hours"] >= 2