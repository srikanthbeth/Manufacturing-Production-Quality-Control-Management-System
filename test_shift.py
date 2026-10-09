
import os
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "manufacturing_production_quality_test"
)

from fastapi.testclient import TestClient
from sqlalchemy import text

from database import Base, SessionLocal, engine
from main import app
from models.user import User


Base.metadata.create_all(bind=engine)

client = TestClient(app)


def cleanup_database():
    db = SessionLocal()

    try:
        db.execute(
            text(
                """
                TRUNCATE TABLE
                    shift_machine_usage,
                    shift_production_outputs,
                    shift_workers,
                    shifts,
                    worker_batch_assignments,
                    workers,
                    production_batches,
                    production_orders,
                    machines,
                    bom_items,
                    boms,
                    material_transactions,
                    raw_materials,
                    products,
                    production_lines,
                    plants,
                    auth_tokens,
                    users
                RESTART IDENTITY CASCADE
                """
            )
        )

        db.commit()

    finally:
        db.close()


def create_user(role="Worker", email=None):
    if email is None:
        email = f"user_{uuid4().hex[:8]}@example.com"

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Test@12345",
            "full_name": "Test User",
        },
    )

    assert response.status_code in [200, 201], response.text

    user_id = response.json()["id"]

    db = SessionLocal()

    try:
        user = db.get(User, user_id)

        assert user is not None

        user.role = role

        db.commit()

    finally:
        db.close()

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "Test@12345",
        },
    )

    assert login_response.status_code == 200, login_response.text

    return {
        "id": user_id,
        "token": login_response.json()["access_token"],
        "email": email,
    }


def create_admin():
    return create_user(
        role="Super Admin",
        email=f"admin_{uuid4().hex[:8]}@example.com",
    )


def create_production_manager():
    return create_user(
        role="Production Manager",
        email=f"manager_{uuid4().hex[:8]}@example.com",
    )


def create_production_supervisor():
    return create_user(
        role="Production Supervisor",
        email=f"supervisor_{uuid4().hex[:8]}@example.com",
    )


def create_worker_user():
    return create_user(
        role="Worker",
        email=f"worker_{uuid4().hex[:8]}@example.com",
    )


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def create_shift(
    token,
    name="Morning",
    start_time="06:00:00",
    end_time="14:00:00",
):
    response = client.post(
        "/api/v1/shifts",
        headers=auth_headers(token),
        json={
            "name": name,
            "start_time": start_time,
            "end_time": end_time,
            "description": f"{name} production shift",
            "is_active": True,
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_plant(token):
    code = f"PLT-{uuid4().hex[:6].upper()}"

    response = client.post(
        "/api/v1/plants",
        headers=auth_headers(token),
        json={
            "name": "Main Manufacturing Plant",
            "code": code,
            "address": "Industrial Area",
            "city": "Tirupati",
            "state": "Andhra Pradesh",
            "production_capacity": 10000,
            "status": "Active",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_production_line(token, plant_id):
    code = f"LINE-{uuid4().hex[:6].upper()}"

    response = client.post(
        "/api/v1/production-lines",
        headers=auth_headers(token),
        json={
            "name": "Assembly Line",
            "code": code,
            "plant_id": plant_id,
            "production_capacity": 5000,
            "status": "Active",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_worker(token, user_id, production_line_id=None):
    employee_code = f"EMP-{uuid4().hex[:8].upper()}"

    response = client.post(
        "/api/v1/workers",
        headers=auth_headers(token),
        json={
            "user_id": user_id,
            "employee_code": employee_code,
            "skill": "Assembly",
            "department": "Production",
            "shift": "Morning",
            "production_line_id": production_line_id,
            "status": "Active",
            "profile_description": "Production worker",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_product(token):
    code = f"PRD-{uuid4().hex[:6].upper()}"
    sku = f"SKU-{uuid4().hex[:8].upper()}"

    response = client.post(
        "/api/v1/products",
        headers=auth_headers(token),
        json={
            "name": "Test Product",
            "code": code,
            "category": "Finished Goods",
            "sku": sku,
            "unit_of_measurement": "Piece",
            "standard_production_time": 60, 
            "status": "Active",
            
            
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_machine(token, production_line_id):
    machine_code = f"MCH-{uuid4().hex[:6].upper()}"

    response = client.post(
        "/api/v1/machines",
        headers=auth_headers(token),
        json={
            "name": "Assembly Machine",
            "machine_code": machine_code,
            "machine_type": "Assembly",
            "production_line_id": production_line_id,
            "installation_date": "2025-01-01",
            "status": "Idle",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_production_order(
    token,
    product_id,
    production_line_id,
    supervisor_id,
):
    order_number = f"ORD-{uuid4().hex[:8].upper()}"

    response = client.post(
        "/api/v1/production-orders",
        headers=auth_headers(token),
        json={
            "order_number": order_number,
            "product_id": product_id,
            "production_line_id": production_line_id,
            "quantity": 1000,
            "target_date": "2026-12-31",
            "supervisor_id":supervisor_id,
            "priority": "High",
            "status": "Draft",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_production_batch(
    token,
    production_order_id,
    production_line_id,
    machine_id,
    supervisor_id,
):
    batch_number = f"BATCH-{uuid4().hex[:8].upper()}"

    response = client.post(
        "/api/v1/production-batches",
        headers=auth_headers(token),
        json={
            "batch_number": batch_number,
            "production_order_id": production_order_id,
            "production_line_id": production_line_id,
            "machine_id": machine_id,
            "supervisor_id": supervisor_id,
            "planned_quantity": 500,
            "status": "Planned",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def setup_worker():
    admin = create_admin()

    plant = create_plant(
        admin["token"]
    )

    line = create_production_line(
        admin["token"],
        plant["id"],
    )

    worker_user = create_worker_user()

    worker = create_worker(
        admin["token"],
        worker_user["id"],
        line["id"],
    )

    return admin, plant, line, worker_user, worker


def setup_batch():
    admin = create_admin()

    plant = create_plant(
        admin["token"]
    )

    line = create_production_line(
        admin["token"],
        plant["id"],
    )

    product = create_product(
        admin["token"]
    )

    supervisor = create_production_supervisor()

    order = create_production_order(
        admin["token"],
        product["id"],
        line["id"],
        supervisor["id"],
    )

    machine = create_machine(
        admin["token"],
        line["id"],
    )

    batch = create_production_batch(
        admin["token"],
        order["id"],
        line["id"],
        machine["id"],
        supervisor["id"],
    )

    return admin, plant, line, product, order, batch


def setup_machine():
    admin = create_admin()

    plant = create_plant(
        admin["token"]
    )

    line = create_production_line(
        admin["token"],
        plant["id"],
    )

    machine = create_machine(
        admin["token"],
        line["id"],
    )

    return admin, plant, line, machine


def test_create_morning_shift():
    cleanup_database()

    admin = create_admin()

    shift = create_shift(
        admin["token"],
        "Morning",
        "06:00:00",
        "14:00:00",
    )

    assert shift["name"] == "Morning"
    assert shift["start_time"] == "06:00:00"
    assert shift["end_time"] == "14:00:00"
    assert shift["is_active"] is True


def test_create_evening_shift():
    cleanup_database()

    admin = create_admin()

    shift = create_shift(
        admin["token"],
        "Evening",
        "14:00:00",
        "22:00:00",
    )

    assert shift["name"] == "Evening"


def test_create_night_shift():
    cleanup_database()

    admin = create_admin()

    shift = create_shift(
        admin["token"],
        "Night",
        "22:00:00",
        "06:00:00",
    )

    assert shift["name"] == "Night"


def test_get_shift():
    cleanup_database()

    admin = create_admin()

    shift = create_shift(
        admin["token"]
    )

    response = client.get(
        f"/api/v1/shifts/{shift['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200
    assert response.json()["id"] == shift["id"]


def test_list_shifts():
    cleanup_database()

    admin = create_admin()

    create_shift(
        admin["token"],
        "Morning",
        "06:00:00",
        "14:00:00",
    )

    create_shift(
        admin["token"],
        "Evening",
        "14:00:00",
        "22:00:00",
    )

    response = client.get(
        "/api/v1/shifts",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_search_shift():
    cleanup_database()

    admin = create_admin()

    create_shift(
        admin["token"],
        "Morning",
        "06:00:00",
        "14:00:00",
    )

    create_shift(
        admin["token"],
        "Evening",
        "14:00:00",
        "22:00:00",
    )

    response = client.get(
        "/api/v1/shifts?search=Morning",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["name"] == "Morning"


def test_filter_active_shifts():
    cleanup_database()

    admin = create_admin()

    morning = create_shift(
        admin["token"],
        "Morning",
        "06:00:00",
        "14:00:00",
    )

    response = client.put(
        f"/api/v1/shifts/{morning['id']}",
        headers=auth_headers(admin["token"]),
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 200

    create_shift(
        admin["token"],
        "Evening",
        "14:00:00",
        "22:00:00",
    )

    response = client.get(
        "/api/v1/shifts?is_active=true",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["name"] == "Evening"


def test_pagination():
    cleanup_database()

    admin = create_admin()

    create_shift(
        admin["token"],
        "Morning",
        "06:00:00",
        "14:00:00",
    )

    create_shift(
        admin["token"],
        "Evening",
        "14:00:00",
        "22:00:00",
    )

    create_shift(
        admin["token"],
        "Night",
        "22:00:00",
        "06:00:00",
    )

    response = client.get(
        "/api/v1/shifts?page=1&page_size=2",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert len(data["items"]) == 2


def test_duplicate_shift_rejected():
    cleanup_database()

    admin = create_admin()

    create_shift(
        admin["token"],
        "Morning",
        "06:00:00",
        "14:00:00",
    )

    response = client.post(
        "/api/v1/shifts",
        headers=auth_headers(admin["token"]),
        json={
            "name": "Morning",
            "start_time": "07:00:00",
            "end_time": "15:00:00",
            "description": "Duplicate",
            "is_active": True,
        },
    )

    assert response.status_code == 409


def test_invalid_shift_name_rejected():
    cleanup_database()

    admin = create_admin()

    response = client.post(
        "/api/v1/shifts",
        headers=auth_headers(admin["token"]),
        json={
            "name": "Afternoon",
            "start_time": "10:00:00",
            "end_time": "18:00:00",
            "description": "Invalid shift",
            "is_active": True,
        },
    )

    assert response.status_code == 400


def test_same_start_end_time_rejected():
    cleanup_database()

    admin = create_admin()

    response = client.post(
        "/api/v1/shifts",
        headers=auth_headers(admin["token"]),
        json={
            "name": "Morning",
            "start_time": "06:00:00",
            "end_time": "06:00:00",
            "description": "Invalid timing",
            "is_active": True,
        },
    )

    assert response.status_code == 400


def test_missing_auth_rejected():
    cleanup_database()

    response = client.get(
        "/api/v1/shifts"
    )

    assert response.status_code == 401


def test_worker_cannot_create_shift():
    cleanup_database()

    worker = create_worker_user()

    response = client.post(
        "/api/v1/shifts",
        headers=auth_headers(worker["token"]),
        json={
            "name": "Morning",
            "start_time": "06:00:00",
            "end_time": "14:00:00",
            "description": "Worker attempt",
            "is_active": True,
        },
    )

    assert response.status_code == 403


def test_production_manager_can_create_shift():
    cleanup_database()

    manager = create_production_manager()

    shift = create_shift(
        manager["token"]
    )

    assert shift["name"] == "Morning"


def test_production_supervisor_can_create_shift():
    cleanup_database()

    supervisor = create_production_supervisor()

    shift = create_shift(
        supervisor["token"]
    )

    assert shift["name"] == "Morning"


def test_update_shift():
    cleanup_database()

    admin = create_admin()

    shift = create_shift(
        admin["token"]
    )

    response = client.put(
        f"/api/v1/shifts/{shift['id']}",
        headers=auth_headers(admin["token"]),
        json={
            "description": "Updated Morning Shift",
            "start_time": "07:00:00",
            "end_time": "15:00:00",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["description"] == "Updated Morning Shift"
    assert data["start_time"] == "07:00:00"
    assert data["end_time"] == "15:00:00"


def test_update_shift_name():
    cleanup_database()

    admin = create_admin()

    shift = create_shift(
        admin["token"]
    )

    response = client.put(
        f"/api/v1/shifts/{shift['id']}",
        headers=auth_headers(admin["token"]),
        json={
            "name": "Evening",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Evening"


def test_deactivate_shift():
    cleanup_database()

    admin = create_admin()

    shift = create_shift(
        admin["token"]
    )

    response = client.put(
        f"/api/v1/shifts/{shift['id']}",
        headers=auth_headers(admin["token"]),
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


def test_shift_not_found():
    cleanup_database()

    admin = create_admin()

    response = client.get(
        "/api/v1/shifts/999999",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 404


def test_assign_worker_to_shift():
    cleanup_database()

    admin, plant, line, worker_user, worker = setup_worker()

    shift = create_shift(
        admin["token"]
    )

    response = client.post(
        f"/api/v1/shifts/{shift['id']}/workers/{worker['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["shift_id"] == shift["id"]
    assert data["worker_id"] == worker["id"]


def test_duplicate_worker_shift_assignment_rejected():
    cleanup_database()

    admin, plant, line, worker_user, worker = setup_worker()

    shift = create_shift(
        admin["token"]
    )

    response = client.post(
        f"/api/v1/shifts/{shift['id']}/workers/{worker['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 201

    response = client.post(
        f"/api/v1/shifts/{shift['id']}/workers/{worker['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 409


def test_inactive_worker_cannot_be_assigned_to_shift():
    cleanup_database()

    admin, plant, line, worker_user, worker = setup_worker()

    db = SessionLocal()

    try:
        from models.worker import Worker

        worker_model = db.get(
            Worker,
            worker["id"],
        )

        worker_model.status = "Inactive"

        db.commit()

    finally:
        db.close()

    shift = create_shift(
        admin["token"]
    )

    response = client.post(
        f"/api/v1/shifts/{shift['id']}/workers/{worker['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 400


def test_get_shift_workers():
    cleanup_database()

    admin, plant, line, worker_user, worker = setup_worker()

    shift = create_shift(
        admin["token"]
    )

    response = client.post(
        f"/api/v1/shifts/{shift['id']}/workers/{worker['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 201

    response = client.get(
        f"/api/v1/shifts/{shift['id']}/workers",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["worker_id"] == worker["id"]


def test_get_worker_shifts():
    cleanup_database()

    admin, plant, line, worker_user, worker = setup_worker()

    shift = create_shift(
        admin["token"]
    )

    response = client.post(
        f"/api/v1/shifts/{shift['id']}/workers/{worker['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 201

    response = client.get(
        f"/api/v1/shifts/workers/{worker['id']}/shifts",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["shift_id"] == shift["id"]


def test_remove_worker_from_shift():
    cleanup_database()

    admin, plant, line, worker_user, worker = setup_worker()

    shift = create_shift(
        admin["token"]
    )

    response = client.post(
        f"/api/v1/shifts/{shift['id']}/workers/{worker['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 201

    response = client.delete(
        f"/api/v1/shifts/{shift['id']}/workers/{worker['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 204


def test_remove_nonexistent_shift_worker_rejected():
    cleanup_database()

    admin = create_admin()

    shift = create_shift(
        admin["token"]
    )

    response = client.delete(
        f"/api/v1/shifts/{shift['id']}/workers/999999",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 404


def test_assign_worker_to_inactive_shift_rejected():
    cleanup_database()

    admin, plant, line, worker_user, worker = setup_worker()

    shift = create_shift(
        admin["token"]
    )

    response = client.put(
        f"/api/v1/shifts/{shift['id']}",
        headers=auth_headers(admin["token"]),
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 200

    response = client.post(
        f"/api/v1/shifts/{shift['id']}/workers/{worker['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 400


def test_record_production_output():
    cleanup_database()

    admin, plant, line, product, order, batch = setup_batch()

    shift = create_shift(
        admin["token"]
    )

    response = client.post(
        f"/api/v1/shifts/{shift['id']}/production-output",
        headers=auth_headers(admin["token"]),
        json={
            "production_batch_id": batch["id"],
            "produced_quantity": 100,
            "rejected_quantity": 5,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["shift_id"] == shift["id"]
    assert data["production_batch_id"] == batch["id"]
    assert float(data["produced_quantity"]) == 100
    assert float(data["rejected_quantity"]) == 5


def test_get_production_output():
    cleanup_database()

    admin, plant, line, product, order, batch = setup_batch()

    shift = create_shift(
        admin["token"]
    )

    response = client.post(
        f"/api/v1/shifts/{shift['id']}/production-output",
        headers=auth_headers(admin["token"]),
        json={
            "production_batch_id": batch["id"],
            "produced_quantity": 200,
            "rejected_quantity": 10,
        },
    )

    assert response.status_code == 201

    response = client.get(
        f"/api/v1/shifts/{shift['id']}/production-output",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert float(data[0]["produced_quantity"]) == 200


def test_invalid_batch_for_production_output_rejected():
    cleanup_database()

    admin = create_admin()

    shift = create_shift(
        admin["token"]
    )

    response = client.post(
        f"/api/v1/shifts/{shift['id']}/production-output",
        headers=auth_headers(admin["token"]),
        json={
            "production_batch_id": 999999,
            "produced_quantity": 100,
            "rejected_quantity": 5,
        },
    )

    assert response.status_code == 404


def test_rejected_quantity_cannot_exceed_produced_quantity():
    cleanup_database()

    admin, plant, line, product, order, batch = setup_batch()

    shift = create_shift(
        admin["token"]
    )

    response = client.post(
        f"/api/v1/shifts/{shift['id']}/production-output",
        headers=auth_headers(admin["token"]),
        json={
            "production_batch_id": batch["id"],
            "produced_quantity": 100,
            "rejected_quantity": 150,
        },
    )

    assert response.status_code == 400


def test_record_machine_usage():
    cleanup_database()

    admin, plant, line, machine = setup_machine()

    shift = create_shift(
        admin["token"]
    )

    response = client.post(
        f"/api/v1/shifts/{shift['id']}/machine-usage",
        headers=auth_headers(admin["token"]),
        json={
            "machine_id": machine["id"],
            "usage_hours": 8,
            "downtime_hours": 1,
            "notes": "Normal operation",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["shift_id"] == shift["id"]
    assert data["machine_id"] == machine["id"]
    assert float(data["usage_hours"]) == 8
    assert float(data["downtime_hours"]) == 1


def test_get_machine_usage():
    cleanup_database()

    admin, plant, line, machine = setup_machine()

    shift = create_shift(
        admin["token"]
    )

    response = client.post(
        f"/api/v1/shifts/{shift['id']}/machine-usage",
        headers=auth_headers(admin["token"]),
        json={
            "machine_id": machine["id"],
            "usage_hours": 7,
            "downtime_hours": 1,
            "notes": "Machine usage",
        },
    )

    assert response.status_code == 201

    response = client.get(
        f"/api/v1/shifts/{shift['id']}/machine-usage",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert float(data[0]["usage_hours"]) == 7


def test_invalid_machine_for_usage_rejected():
    cleanup_database()

    admin = create_admin()

    shift = create_shift(
        admin["token"]
    )

    response = client.post(
        f"/api/v1/shifts/{shift['id']}/machine-usage",
        headers=auth_headers(admin["token"]),
        json={
            "machine_id": 999999,
            "usage_hours": 8,
            "downtime_hours": 1,
        },
    )

    assert response.status_code == 404


def test_downtime_cannot_exceed_usage():
    cleanup_database()

    admin, plant, line, machine = setup_machine()

    shift = create_shift(
        admin["token"]
    )

    response = client.post(
        f"/api/v1/shifts/{shift['id']}/machine-usage",
        headers=auth_headers(admin["token"]),
        json={
            "machine_id": machine["id"],
            "usage_hours": 4,
            "downtime_hours": 5,
        },
    )

    assert response.status_code == 400


def test_shift_performance():
    cleanup_database()

    admin, plant, line, product, order, batch = setup_batch()

    worker_user = create_worker_user()

    worker = create_worker(
        admin["token"],
        worker_user["id"],
        line["id"],
    )

    shift = create_shift(
        admin["token"]
    )

    response = client.post(
        f"/api/v1/shifts/{shift['id']}/workers/{worker['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 201

    response = client.post(
        f"/api/v1/shifts/{shift['id']}/production-output",
        headers=auth_headers(admin["token"]),
        json={
            "production_batch_id": batch["id"],
            "produced_quantity": 100,
            "rejected_quantity": 10,
        },
    )

    assert response.status_code == 201

    machine = create_machine(
        admin["token"],
        line["id"],
    )

    response = client.post(
        f"/api/v1/shifts/{shift['id']}/machine-usage",
        headers=auth_headers(admin["token"]),
        json={
            "machine_id": machine["id"],
            "usage_hours": 8,
            "downtime_hours": 1,
        },
    )

    assert response.status_code == 201

    response = client.get(
        f"/api/v1/shifts/{shift['id']}/performance",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["shift_id"] == shift["id"]
    assert data["shift_name"] == "Morning"
    assert data["worker_count"] == 1
    assert float(data["total_produced_quantity"]) == 100
    assert float(data["total_rejected_quantity"]) == 10
    assert float(data["total_machine_usage_hours"]) == 8
    assert float(data["total_machine_downtime_hours"]) == 1
    assert data["production_efficiency"] == 90.0
    assert data["output_per_worker"] == 100.0


def test_shift_performance_without_workers():
    cleanup_database()

    admin, plant, line, product, order, batch = setup_batch()

    shift = create_shift(
        admin["token"]
    )

    response = client.post(
        f"/api/v1/shifts/{shift['id']}/production-output",
        headers=auth_headers(admin["token"]),
        json={
            "production_batch_id": batch["id"],
            "produced_quantity": 100,
            "rejected_quantity": 0,
        },
    )

    assert response.status_code == 201

    response = client.get(
        f"/api/v1/shifts/{shift['id']}/performance",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["worker_count"] == 0
    assert data["production_efficiency"] == 100.0
    assert data["output_per_worker"] == 0.0


def test_worker_cannot_delete_shift():
    cleanup_database()

    admin = create_admin()

    shift = create_shift(
        admin["token"]
    )

    worker = create_worker_user()

    response = client.delete(
        f"/api/v1/shifts/{shift['id']}",
        headers=auth_headers(worker["token"]),
    )

    assert response.status_code == 403


def test_worker_cannot_update_shift():
    cleanup_database()

    admin = create_admin()

    shift = create_shift(
        admin["token"]
    )

    worker = create_worker_user()

    response = client.put(
        f"/api/v1/shifts/{shift['id']}",
        headers=auth_headers(worker["token"]),
        json={
            "description": "Unauthorized update",
        },
    )

    assert response.status_code == 403


def test_worker_can_view_shifts():
    cleanup_database()

    admin = create_admin()

    create_shift(
        admin["token"]
    )

    worker = create_worker_user()

    response = client.get(
        "/api/v1/shifts",
        headers=auth_headers(worker["token"]),
    )

    assert response.status_code == 200


def test_worker_cannot_record_production_output():
    cleanup_database()

    admin, plant, line, product, order, batch = setup_batch()

    shift = create_shift(
        admin["token"]
    )

    worker = create_worker_user()

    response = client.post(
        f"/api/v1/shifts/{shift['id']}/production-output",
        headers=auth_headers(worker["token"]),
        json={
            "production_batch_id": batch["id"],
            "produced_quantity": 100,
            "rejected_quantity": 5,
        },
    )

    assert response.status_code == 403


def test_worker_cannot_record_machine_usage():
    cleanup_database()

    admin, plant, line, machine = setup_machine()

    shift = create_shift(
        admin["token"]
    )

    worker = create_worker_user()

    response = client.post(
        f"/api/v1/shifts/{shift['id']}/machine-usage",
        headers=auth_headers(worker["token"]),
        json={
            "machine_id": machine["id"],
            "usage_hours": 8,
            "downtime_hours": 1,
        },
    )

    assert response.status_code == 403


def test_delete_shift():
    cleanup_database()

    admin = create_admin()

    shift = create_shift(
        admin["token"]
    )

    response = client.delete(
        f"/api/v1/shifts/{shift['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 204

    response = client.get(
        f"/api/v1/shifts/{shift['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 404


def test_invalid_page_size_rejected():
    cleanup_database()

    admin = create_admin()

    response = client.get(
        "/api/v1/shifts?page_size=101",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 422


def test_invalid_page_rejected():
    cleanup_database()

    admin = create_admin()

    response = client.get(
        "/api/v1/shifts?page=0",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 422
