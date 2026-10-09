
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "manufacturing_production_quality_test"
)

from fastapi.testclient import TestClient
from sqlalchemy import text

from database import Base, SessionLocal, engine
from main import app

from models import (
    User,
    Plant,
    ProductionLine,
    Product,
    Machine,
    ProductionOrder,
    ProductionBatch,
    Worker,
    WorkerBatchAssignment,
)


client = TestClient(app)

Base.metadata.create_all(bind=engine)


def cleanup_database():
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                TRUNCATE TABLE
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


def create_user(
    email=None,
    password="Test@12345",
    role=None,
):
    if email is None:
        email = f"user_{uuid4().hex[:8]}@example.com"

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Test User",
        },
    )

    assert response.status_code in [200, 201], response.text

    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        assert user is not None

        if role is not None:
            user.role = role
            db.commit()
            db.refresh(user)

        user_id = user.id

    finally:
        db.close()

    return {
        "email": email,
        "password": password,
        "user_id": user_id,
    }


def login(email, password):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200, response.text

    return response.json()["access_token"]


def auth_header(token):
    return {
        "Authorization": f"Bearer {token}"
    }


def create_admin():
    from core.enums import UserRole

    user = create_user(
        role=UserRole.SUPER_ADMIN
    )

    token = login(
        user["email"],
        user["password"],
    )

    return {
        **user,
        "token": token,
    }


def create_worker_user():
    from core.enums import UserRole

    user = create_user(
        role=UserRole.WORKER
    )

    token = login(
        user["email"],
        user["password"],
    )

    return {
        **user,
        "token": token,
    }


def create_production_manager():
    from core.enums import UserRole

    user = create_user(
        role=UserRole.PRODUCTION_MANAGER
    )

    token = login(
        user["email"],
        user["password"],
    )

    return {
        **user,
        "token": token,
    }


def create_supervisor():
    from core.enums import UserRole

    user = create_user(
        role=UserRole.PRODUCTION_SUPERVISOR
    )

    token = login(
        user["email"],
        user["password"],
    )

    return {
        **user,
        "token": token,
    }


def create_plant(admin_token):
    code = f"PLANT-{uuid4().hex[:8].upper()}"

    response = client.post(
        "/api/v1/plants",
        headers=auth_header(admin_token),
        json={
            "name": "Main Manufacturing Plant",
            "code": code,
            "status": "Active",
            "address": "Industrial Area",
            "city": "Tirupati",
            "state": "Andhra Pradesh",
            "production_capacity": 1000,
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_production_line(
    admin_token,
    plant_id,
):
    code = f"LINE-{uuid4().hex[:8].upper()}"

    response = client.post(
        "/api/v1/production-lines",
        headers=auth_header(admin_token),
        json={
            "name": "Assembly Line",
            "code": code,
            "production_capacity": 500,
            "plant_id": plant_id,
            "status": "Active",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_product(admin_token):
    sku = f"SKU-{uuid4().hex[:8].upper()}"

    response = client.post(
        "/api/v1/products",
        headers=auth_header(admin_token),
        json={
            "name": "Manufacturing Product",
            "category": "Finished Goods",
            "sku": sku,
            "unit_of_measurement": "Pieces",
            "status": "Active",
            "standard_production_time": 60,
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_machine(
    admin_token,
    production_line_id,
):
    machine_code = (
        f"MACHINE-{uuid4().hex[:8].upper()}"
    )

    response = client.post(
        "/api/v1/machines",
        headers=auth_header(admin_token),
        json={
            "machine_code": machine_code,
            "machine_type": "Assembly Machine",
            "production_line_id": production_line_id,
            "installation_date": "2025-01-01",
            "status": "Idle",
            "operating_hours": 100,
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_production_order(
    admin_token,
    product_id,
    production_line_id,
    supervisor_id,
):
    order_number = (
        f"ORDER-{uuid4().hex[:8].upper()}"
    )

    target_date = (
        datetime.now(timezone.utc)
        + timedelta(days=7)
    ).date().isoformat()

    response = client.post(
        "/api/v1/production-orders",
        headers=auth_header(admin_token),
        json={
            "order_number": order_number,
            "product_id": product_id,
            "quantity": 1000,
            "target_date": target_date,
            "production_line_id": production_line_id,
            "priority": "Medium",
            "supervisor_id": supervisor_id,
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_production_batch(
    admin_token,
    production_order_id,
    production_line_id,
    machine_id,
    supervisor_id,
):
    batch_number = (
        f"BATCH-{uuid4().hex[:8].upper()}"
    )

    response = client.post(
        "/api/v1/production-batches",
        headers=auth_header(admin_token),
        json={
            "batch_number": batch_number,
            "production_order_id": production_order_id,
            "planned_quantity": 1000,
            "produced_quantity": 900,
            "rejected_quantity": 50,
            "start_time": "2026-10-07T08:00:00Z",
            "end_time": "2026-10-07T16:00:00Z",
            "production_line_id": production_line_id,
            "machine_id": machine_id,
            "supervisor_id": supervisor_id,
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_test_data():
    admin = create_admin()

    worker_user = create_worker_user()

    supervisor = create_supervisor()

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

    machine = create_machine(
        admin["token"],
        line["id"],
    )

    order = create_production_order(
        admin["token"],
        product["id"],
        line["id"],
        supervisor["user_id"],
    )

    batch = create_production_batch(
        admin["token"],
        order["id"],
        line["id"],
        machine["id"],
        supervisor["user_id"],
    )

    return {
        "admin": admin,
        "worker_user": worker_user,
        "supervisor": supervisor,
        "plant": plant,
        "line": line,
        "product": product,
        "machine": machine,
        "order": order,
        "batch": batch,
    }


def create_worker_profile(
    token,
    user_id,
    production_line_id=None,
    employee_code=None,
):
    if employee_code is None:
        employee_code = (
            f"EMP-{uuid4().hex[:8].upper()}"
        )

    response = client.post(
        "/api/v1/workers",
        headers=auth_header(token),
        json={
            "user_id": user_id,
            "employee_code": employee_code,
            "skill": "Assembly",
            "department": "Production",
            "shift": "Morning",
            "production_line_id": production_line_id,
            "status": "Active",
            "profile_description": "Assembly worker",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def setup_function():
    cleanup_database()


def test_create_worker():
    data = create_test_data()

    worker = create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    assert worker["id"] > 0
    assert worker["user_id"] == data["worker_user"]["user_id"]
    assert worker["employee_code"].startswith("EMP-")
    assert worker["skill"] == "Assembly"
    assert worker["department"] == "Production"
    assert worker["shift"] == "Morning"
    assert worker["production_line_id"] == data["line"]["id"]
    assert worker["status"] == "Active"


def test_get_worker():
    data = create_test_data()

    worker = create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    response = client.get(
        f"/api/v1/workers/{worker['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 200
    assert response.json()["id"] == worker["id"]


def test_list_workers():
    data = create_test_data()

    create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    response = client.get(
        "/api/v1/workers",
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 200

    result = response.json()

    assert result["total"] == 1
    assert len(result["items"]) == 1


def test_search_worker_by_employee_code():
    data = create_test_data()

    worker = create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    response = client.get(
        "/api/v1/workers",
        params={
            "search": worker["employee_code"]
        },
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_search_worker_by_skill():
    data = create_test_data()

    create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    response = client.get(
        "/api/v1/workers",
        params={
            "search": "Assembly"
        },
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_filter_by_department():
    data = create_test_data()

    create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    response = client.get(
        "/api/v1/workers",
        params={
            "department": "Production"
        },
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_filter_by_shift():
    data = create_test_data()

    create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    response = client.get(
        "/api/v1/workers",
        params={
            "shift": "Morning"
        },
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_filter_by_status():
    data = create_test_data()

    create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    response = client.get(
        "/api/v1/workers",
        params={
            "status": "Active"
        },
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_filter_by_production_line():
    data = create_test_data()

    create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    response = client.get(
        "/api/v1/workers",
        params={
            "production_line_id": data["line"]["id"]
        },
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_pagination():
    data = create_test_data()

    create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    response = client.get(
        "/api/v1/workers",
        params={
            "page": 1,
            "page_size": 1,
        },
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 200

    result = response.json()

    assert result["page"] == 1
    assert result["page_size"] == 1
    assert len(result["items"]) == 1


def test_duplicate_employee_code_rejected():
    data = create_test_data()

    employee_code = (
        f"EMP-{uuid4().hex[:8].upper()}"
    )

    first = create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
        employee_code,
    )

    assert first["employee_code"] == employee_code

    second_user = create_worker_user()

    response = client.post(
        "/api/v1/workers",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json={
            "user_id": second_user["user_id"],
            "employee_code": employee_code,
            "skill": "Welding",
            "department": "Production",
            "shift": "Evening",
            "production_line_id": data["line"]["id"],
            "status": "Active",
        },
    )

    assert response.status_code == 409


def test_duplicate_worker_profile_rejected():
    data = create_test_data()

    create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    response = client.post(
        "/api/v1/workers",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json={
            "user_id": data["worker_user"]["user_id"],
            "employee_code": (
                f"EMP-{uuid4().hex[:8].upper()}"
            ),
            "skill": "Welding",
            "department": "Production",
            "shift": "Evening",
            "production_line_id": data["line"]["id"],
            "status": "Active",
        },
    )

    assert response.status_code == 409


def test_invalid_user_rejected():
    data = create_test_data()

    response = client.post(
        "/api/v1/workers",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json={
            "user_id": 999999,
            "employee_code": (
                f"EMP-{uuid4().hex[:8].upper()}"
            ),
            "skill": "Assembly",
            "department": "Production",
            "shift": "Morning",
            "production_line_id": data["line"]["id"],
            "status": "Active",
        },
    )

    assert response.status_code == 404


def test_invalid_production_line_rejected():
    data = create_test_data()

    response = client.post(
        "/api/v1/workers",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json={
            "user_id": data["worker_user"]["user_id"],
            "employee_code": (
                f"EMP-{uuid4().hex[:8].upper()}"
            ),
            "skill": "Assembly",
            "department": "Production",
            "shift": "Morning",
            "production_line_id": 999999,
            "status": "Active",
        },
    )

    assert response.status_code == 404


def test_invalid_shift_rejected():
    data = create_test_data()

    response = client.post(
        "/api/v1/workers",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json={
            "user_id": data["worker_user"]["user_id"],
            "employee_code": (
                f"EMP-{uuid4().hex[:8].upper()}"
            ),
            "skill": "Assembly",
            "department": "Production",
            "shift": "Invalid Shift",
            "production_line_id": data["line"]["id"],
            "status": "Active",
        },
    )

    assert response.status_code == 400


def test_invalid_worker_status_rejected():
    data = create_test_data()

    response = client.post(
        "/api/v1/workers",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json={
            "user_id": data["worker_user"]["user_id"],
            "employee_code": (
                f"EMP-{uuid4().hex[:8].upper()}"
            ),
            "skill": "Assembly",
            "department": "Production",
            "shift": "Morning",
            "production_line_id": data["line"]["id"],
            "status": "Invalid Status",
        },
    )

    assert response.status_code == 400


def test_missing_auth_rejected():
    response = client.get(
        "/api/v1/workers"
    )

    assert response.status_code == 401


def test_worker_role_cannot_create_worker_profile():
    data = create_test_data()

    another_user = create_worker_user()

    response = client.post(
        "/api/v1/workers",
        headers=auth_header(
            data["worker_user"]["token"]
        ),
        json={
            "user_id": another_user["user_id"],
            "employee_code": (
                f"EMP-{uuid4().hex[:8].upper()}"
            ),
            "skill": "Assembly",
            "department": "Production",
            "shift": "Morning",
            "production_line_id": data["line"]["id"],
            "status": "Active",
        },
    )

    assert response.status_code == 403


def test_production_manager_can_create_worker():
    data = create_test_data()

    manager = create_production_manager()
    another_user = create_worker_user()

    worker = create_worker_profile(
        manager["token"],
        another_user["user_id"],
        data["line"]["id"],
    )

    assert worker["user_id"] == another_user["user_id"]


def test_production_supervisor_can_create_worker():
    data = create_test_data()

    another_user = create_worker_user()

    worker = create_worker_profile(
        data["supervisor"]["token"],
        another_user["user_id"],
        data["line"]["id"],
    )

    assert worker["user_id"] == another_user["user_id"]


def test_update_worker_skill():
    data = create_test_data()

    worker = create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    response = client.put(
        f"/api/v1/workers/{worker['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json={
            "skill": "Advanced Welding"
        },
    )

    assert response.status_code == 200
    assert response.json()["skill"] == "Advanced Welding"


def test_update_worker_department():
    data = create_test_data()

    worker = create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    response = client.put(
        f"/api/v1/workers/{worker['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json={
            "department": "Quality"
        },
    )

    assert response.status_code == 200
    assert response.json()["department"] == "Quality"


def test_update_worker_shift():
    data = create_test_data()

    worker = create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    response = client.put(
        f"/api/v1/workers/{worker['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json={
            "shift": "Night"
        },
    )

    assert response.status_code == 200
    assert response.json()["shift"] == "Night"


def test_update_worker_status():
    data = create_test_data()

    worker = create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    response = client.put(
        f"/api/v1/workers/{worker['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json={
            "status": "On Leave"
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "On Leave"


def test_update_worker_production_line():
    data = create_test_data()

    worker = create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    second_line = create_production_line(
        data["admin"]["token"],
        data["plant"]["id"],
    )

    response = client.put(
        f"/api/v1/workers/{worker['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json={
            "production_line_id": second_line["id"]
        },
    )

    assert response.status_code == 200
    assert (
        response.json()["production_line_id"]
        == second_line["id"]
    )


def test_update_employee_code():
    data = create_test_data()

    worker = create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    new_code = (
        f"EMP-{uuid4().hex[:8].upper()}"
    )

    response = client.put(
        f"/api/v1/workers/{worker['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json={
            "employee_code": new_code
        },
    )

    assert response.status_code == 200
    assert response.json()["employee_code"] == new_code


def test_worker_not_found():
    data = create_test_data()

    response = client.get(
        "/api/v1/workers/999999",
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 404


def test_delete_worker():
    data = create_test_data()

    worker = create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    response = client.delete(
        f"/api/v1/workers/{worker['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/api/v1/workers/{worker['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert get_response.status_code == 404


def test_worker_can_be_assigned_to_batch():
    data = create_test_data()

    worker = create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    response = client.post(
        f"/api/v1/workers/{worker['id']}/batches/"
        f"{data['batch']['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 201

    result = response.json()

    assert result["worker_id"] == worker["id"]
    assert (
        result["production_batch_id"]
        == data["batch"]["id"]
    )


def test_duplicate_worker_batch_assignment_rejected():
    data = create_test_data()

    worker = create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    first = client.post(
        f"/api/v1/workers/{worker['id']}/batches/"
        f"{data['batch']['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert first.status_code == 201

    second = client.post(
        f"/api/v1/workers/{worker['id']}/batches/"
        f"{data['batch']['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert second.status_code == 409


def test_inactive_worker_cannot_be_assigned_to_batch():
    data = create_test_data()

    worker = create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    update_response = client.put(
        f"/api/v1/workers/{worker['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json={
            "status": "Inactive"
        },
    )

    assert update_response.status_code == 200

    response = client.post(
        f"/api/v1/workers/{worker['id']}/batches/"
        f"{data['batch']['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 400


def test_worker_from_different_line_cannot_be_assigned():
    data = create_test_data()

    second_line = create_production_line(
        data["admin"]["token"],
        data["plant"]["id"],
    )

    worker = create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        second_line["id"],
    )

    response = client.post(
        f"/api/v1/workers/{worker['id']}/batches/"
        f"{data['batch']['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 400


def test_invalid_batch_assignment_rejected():
    data = create_test_data()

    worker = create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    response = client.post(
        f"/api/v1/workers/{worker['id']}/batches/999999",
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 404


def test_invalid_worker_assignment_rejected():
    data = create_test_data()

    response = client.post(
        f"/api/v1/workers/999999/batches/"
        f"{data['batch']['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 404


def test_get_batch_workers():
    data = create_test_data()

    worker = create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    assignment = client.post(
        f"/api/v1/workers/{worker['id']}/batches/"
        f"{data['batch']['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert assignment.status_code == 201

    response = client.get(
        f"/api/v1/workers/batch/{data['batch']['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 200

    result = response.json()

    assert len(result) == 1
    assert result[0]["worker_id"] == worker["id"]
    assert (
        result[0]["production_batch_id"]
        == data["batch"]["id"]
    )


def test_get_worker_batches():
    data = create_test_data()

    worker = create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    assignment = client.post(
        f"/api/v1/workers/{worker['id']}/batches/"
        f"{data['batch']['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert assignment.status_code == 201

    response = client.get(
        f"/api/v1/workers/{worker['id']}/batches",
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 200

    result = response.json()

    assert len(result) == 1
    assert result[0]["worker_id"] == worker["id"]


def test_remove_worker_from_batch():
    data = create_test_data()

    worker = create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    assignment = client.post(
        f"/api/v1/workers/{worker['id']}/batches/"
        f"{data['batch']['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert assignment.status_code == 201

    response = client.delete(
        f"/api/v1/workers/{worker['id']}/batches/"
        f"{data['batch']['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 204


def test_remove_nonexistent_worker_assignment():
    data = create_test_data()

    worker = create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    response = client.delete(
        f"/api/v1/workers/{worker['id']}/batches/"
        f"{data['batch']['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 404


def test_worker_cannot_delete_worker_profile():
    data = create_test_data()

    worker = create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    response = client.delete(
        f"/api/v1/workers/{worker['id']}",
        headers=auth_header(
            data["worker_user"]["token"]
        ),
    )

    assert response.status_code == 403


def test_worker_cannot_update_worker_profile():
    data = create_test_data()

    worker = create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    response = client.put(
        f"/api/v1/workers/{worker['id']}",
        headers=auth_header(
            data["worker_user"]["token"]
        ),
        json={
            "skill": "Unauthorized Skill"
        },
    )

    assert response.status_code == 403


def test_worker_can_view_worker_list():
    data = create_test_data()

    create_worker_profile(
        data["admin"]["token"],
        data["worker_user"]["user_id"],
        data["line"]["id"],
    )

    response = client.get(
        "/api/v1/workers",
        headers=auth_header(
            data["worker_user"]["token"]
        ),
    )

    assert response.status_code == 200


def test_invalid_worker_page_size_rejected():
    data = create_test_data()

    response = client.get(
        "/api/v1/workers",
        params={
            "page": 1,
            "page_size": 101,
        },
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 422

