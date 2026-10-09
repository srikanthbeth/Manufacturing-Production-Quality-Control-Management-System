
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
    ProductionBatch,
    ProductionOrder,
    ProductionLine,
    Product,
    Machine,
    Plant,
    User,
    AuthToken,
)

client = TestClient(app)

Base.metadata.create_all(bind=engine)


def cleanup_database():
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                TRUNCATE TABLE
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

    payload = {
        "email": email,
        "password": password,
        "full_name": "Test User",
    }

    response = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert response.status_code in [200, 201], response.text

    db = SessionLocal()

    try:
        user = db.query(User).filter(
            User.email == email
        ).first()

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

    data = response.json()

    return data["access_token"]


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


def create_worker():
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


def create_test_data():
    admin = create_admin()
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

    return {
        "admin": admin,
        "supervisor": supervisor,
        "plant": plant,
        "line": line,
        "product": product,
        "machine": machine,
        "order": order,
    }


def create_batch(
    token,
    data,
):
    response = client.post(
        "/api/v1/production-batches",
        headers=auth_header(token),
        json={
            "batch_number": (
                f"BATCH-{uuid4().hex[:8].upper()}"
            ),
            "production_order_id": data["order"]["id"],
            "planned_quantity": 1000,
            "produced_quantity": 900,
            "rejected_quantity": 50,
            "start_time": "2026-10-07T08:00:00Z",
            "end_time": "2026-10-07T16:00:00Z",
            "production_line_id": data["line"]["id"],
            "machine_id": data["machine"]["id"],
            "supervisor_id": data["supervisor"]["user_id"],
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def setup_function():
    cleanup_database()


def test_create_production_batch():
    data = create_test_data()

    batch = create_batch(
        data["admin"]["token"],
        data,
    )

    assert batch["batch_number"].startswith("BATCH-")
    assert batch["production_order_id"] == data["order"]["id"]
    assert batch["planned_quantity"] == 1000
    assert batch["produced_quantity"] == 900
    assert batch["rejected_quantity"] == 50


def test_batch_calculations():
    data = create_test_data()

    batch = create_batch(
        data["admin"]["token"],
        data,
    )

    assert batch["completion_percentage"] == 90.0
    assert batch["rejection_percentage"] == 5.56
    assert batch["production_efficiency"] == 85.0


def test_get_production_batch():
    data = create_test_data()

    batch = create_batch(
        data["admin"]["token"],
        data,
    )

    response = client.get(
        f"/api/v1/production-batches/{batch['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 200
    assert response.json()["id"] == batch["id"]


def test_list_production_batches():
    data = create_test_data()

    create_batch(
        data["admin"]["token"],
        data,
    )

    response = client.get(
        "/api/v1/production-batches",
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 200

    result = response.json()

    assert result["total"] == 1
    assert len(result["items"]) == 1


def test_search_by_batch_number():
    data = create_test_data()

    batch = create_batch(
        data["admin"]["token"],
        data,
    )

    response = client.get(
        "/api/v1/production-batches",
        params={
            "search": batch["batch_number"]
        },
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_filter_by_production_order():
    data = create_test_data()

    create_batch(
        data["admin"]["token"],
        data,
    )

    response = client.get(
        "/api/v1/production-batches",
        params={
            "production_order_id": data["order"]["id"]
        },
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_filter_by_production_line():
    data = create_test_data()

    create_batch(
        data["admin"]["token"],
        data,
    )

    response = client.get(
        "/api/v1/production-batches",
        params={
            "production_line_id": data["line"]["id"]
        },
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_filter_by_machine():
    data = create_test_data()

    create_batch(
        data["admin"]["token"],
        data,
    )

    response = client.get(
        "/api/v1/production-batches",
        params={
            "machine_id": data["machine"]["id"]
        },
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_filter_by_supervisor():
    data = create_test_data()

    create_batch(
        data["admin"]["token"],
        data,
    )

    response = client.get(
        "/api/v1/production-batches",
        params={
            "supervisor_id": data["supervisor"]["user_id"]
        },
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_pagination():
    data = create_test_data()

    create_batch(
        data["admin"]["token"],
        data,
    )

    response = client.get(
        "/api/v1/production-batches",
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


def test_duplicate_batch_number_rejected():
    data = create_test_data()

    batch_number = (
        f"BATCH-{uuid4().hex[:8].upper()}"
    )

    payload = {
        "batch_number": batch_number,
        "production_order_id": data["order"]["id"],
        "planned_quantity": 1000,
        "produced_quantity": 900,
        "rejected_quantity": 50,
        "production_line_id": data["line"]["id"],
        "machine_id": data["machine"]["id"],
        "supervisor_id": data["supervisor"]["user_id"],
    }

    first = client.post(
        "/api/v1/production-batches",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json=payload,
    )

    assert first.status_code == 201

    second = client.post(
        "/api/v1/production-batches",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json=payload,
    )

    assert second.status_code == 409


def test_worker_cannot_create_batch():
    data = create_test_data()
    worker = create_worker()

    response = client.post(
        "/api/v1/production-batches",
        headers=auth_header(
            worker["token"]
        ),
        json={
            "batch_number": (
                f"BATCH-{uuid4().hex[:8].upper()}"
            ),
            "production_order_id": data["order"]["id"],
            "planned_quantity": 1000,
            "produced_quantity": 0,
            "rejected_quantity": 0,
            "production_line_id": data["line"]["id"],
            "machine_id": data["machine"]["id"],
            "supervisor_id": data["supervisor"]["user_id"],
        },
    )

    assert response.status_code == 403


def test_missing_auth_rejected():
    create_test_data()

    response = client.get(
        "/api/v1/production-batches"
    )

    assert response.status_code == 401


def test_nonexistent_batch():
    admin = create_admin()

    response = client.get(
        "/api/v1/production-batches/999999",
        headers=auth_header(
            admin["token"]
        ),
    )

    assert response.status_code == 404


def test_negative_planned_quantity_rejected():
    data = create_test_data()

    response = client.post(
        "/api/v1/production-batches",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json={
            "batch_number": (
                f"BATCH-{uuid4().hex[:8].upper()}"
            ),
            "production_order_id": data["order"]["id"],
            "planned_quantity": -100,
            "produced_quantity": 0,
            "rejected_quantity": 0,
            "production_line_id": data["line"]["id"],
            "machine_id": data["machine"]["id"],
            "supervisor_id": data["supervisor"]["user_id"],
        },
    )

    assert response.status_code == 422


def test_rejected_quantity_cannot_exceed_produced():
    data = create_test_data()

    response = client.post(
        "/api/v1/production-batches",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json={
            "batch_number": (
                f"BATCH-{uuid4().hex[:8].upper()}"
            ),
            "production_order_id": data["order"]["id"],
            "planned_quantity": 1000,
            "produced_quantity": 100,
            "rejected_quantity": 150,
            "production_line_id": data["line"]["id"],
            "machine_id": data["machine"]["id"],
            "supervisor_id": data["supervisor"]["user_id"],
        },
    )

    assert response.status_code == 400


def test_invalid_time_range_rejected():
    data = create_test_data()

    response = client.post(
        "/api/v1/production-batches",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json={
            "batch_number": (
                f"BATCH-{uuid4().hex[:8].upper()}"
            ),
            "production_order_id": data["order"]["id"],
            "planned_quantity": 1000,
            "produced_quantity": 0,
            "rejected_quantity": 0,
            "start_time": "2026-10-07T16:00:00Z",
            "end_time": "2026-10-07T08:00:00Z",
            "production_line_id": data["line"]["id"],
            "machine_id": data["machine"]["id"],
            "supervisor_id": data["supervisor"]["user_id"],
        },
    )

    assert response.status_code == 400


def test_machine_from_different_line_rejected():
    data = create_test_data()

    response = client.post(
        "/api/v1/production-batches",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json={
            "batch_number": (
                f"BATCH-{uuid4().hex[:8].upper()}"
            ),
            "production_order_id": data["order"]["id"],
            "planned_quantity": 1000,
            "produced_quantity": 0,
            "rejected_quantity": 0,
            "production_line_id": data["line"]["id"] + 999,
            "machine_id": data["machine"]["id"],
            "supervisor_id": data["supervisor"]["user_id"],
        },
    )

    assert response.status_code == 404


def test_invalid_machine_rejected():
    data = create_test_data()

    response = client.post(
        "/api/v1/production-batches",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json={
            "batch_number": (
                f"BATCH-{uuid4().hex[:8].upper()}"
            ),
            "production_order_id": data["order"]["id"],
            "planned_quantity": 1000,
            "produced_quantity": 0,
            "rejected_quantity": 0,
            "production_line_id": data["line"]["id"],
            "machine_id": 999999,
            "supervisor_id": data["supervisor"]["user_id"],
        },
    )

    assert response.status_code == 404


def test_invalid_supervisor_rejected():
    data = create_test_data()
    worker = create_worker()

    response = client.post(
        "/api/v1/production-batches",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json={
            "batch_number": (
                f"BATCH-{uuid4().hex[:8].upper()}"
            ),
            "production_order_id": data["order"]["id"],
            "planned_quantity": 1000,
            "produced_quantity": 0,
            "rejected_quantity": 0,
            "production_line_id": data["line"]["id"],
            "machine_id": data["machine"]["id"],
            "supervisor_id": worker["user_id"],
        },
    )

    assert response.status_code == 400


def test_production_manager_can_create_batch():
    data = create_test_data()
    manager = create_production_manager()

    batch = create_batch(
        manager["token"],
        data,
    )

    assert batch["production_order_id"] == data["order"]["id"]


def test_production_supervisor_can_create_batch():
    data = create_test_data()

    batch = create_batch(
        data["supervisor"]["token"],
        data,
    )

    assert batch["supervisor_id"] == (
        data["supervisor"]["user_id"]
    )


def test_update_produced_quantity():
    data = create_test_data()

    batch = create_batch(
        data["admin"]["token"],
        data,
    )

    response = client.put(
        f"/api/v1/production-batches/{batch['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json={
            "produced_quantity": 950,
            "rejected_quantity": 50,
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["produced_quantity"] == 950
    assert result["rejected_quantity"] == 50
    assert result["completion_percentage"] == 95.0
    assert result["rejection_percentage"] == 5.26
    assert result["production_efficiency"] == 90.0


def test_update_planned_quantity():
    data = create_test_data()

    batch = create_batch(
        data["admin"]["token"],
        data,
    )

    response = client.put(
        f"/api/v1/production-batches/{batch['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json={
            "planned_quantity": 1200,
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["planned_quantity"] == 1200
    assert result["completion_percentage"] == 75.0


def test_zero_produced_quantity():
    data = create_test_data()

    response = client.post(
        "/api/v1/production-batches",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json={
            "batch_number": (
                f"BATCH-{uuid4().hex[:8].upper()}"
            ),
            "production_order_id": data["order"]["id"],
            "planned_quantity": 1000,
            "produced_quantity": 0,
            "rejected_quantity": 0,
            "production_line_id": data["line"]["id"],
            "machine_id": data["machine"]["id"],
            "supervisor_id": data["supervisor"]["user_id"],
        },
    )

    assert response.status_code == 201

    result = response.json()

    assert result["completion_percentage"] == 0.0
    assert result["rejection_percentage"] == 0.0
    assert result["production_efficiency"] == 0.0


def test_update_rejected_quantity():
    data = create_test_data()

    batch = create_batch(
        data["admin"]["token"],
        data,
    )

    response = client.put(
        f"/api/v1/production-batches/{batch['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json={
            "rejected_quantity": 100,
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["rejected_quantity"] == 100
    assert result["rejection_percentage"] == 11.11
    assert result["production_efficiency"] == 80.0


def test_update_times():
    data = create_test_data()

    batch = create_batch(
        data["admin"]["token"],
        data,
    )

    response = client.put(
        f"/api/v1/production-batches/{batch['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json={
            "start_time": "2026-10-07T07:00:00Z",
            "end_time": "2026-10-07T17:00:00Z",
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["start_time"] is not None
    assert result["end_time"] is not None


def test_delete_production_batch():
    data = create_test_data()

    batch = create_batch(
        data["admin"]["token"],
        data,
    )

    response = client.delete(
        f"/api/v1/production-batches/{batch['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert response.status_code in [200, 204]

    get_response = client.get(
        f"/api/v1/production-batches/{batch['id']}",
        headers=auth_header(
            data["admin"]["token"]
        ),
    )

    assert get_response.status_code == 404


def test_worker_cannot_update_batch():
    data = create_test_data()

    batch = create_batch(
        data["admin"]["token"],
        data,
    )

    worker = create_worker()

    response = client.put(
        f"/api/v1/production-batches/{batch['id']}",
        headers=auth_header(
            worker["token"]
        ),
        json={
            "produced_quantity": 950,
        },
    )

    assert response.status_code == 403


def test_worker_cannot_delete_batch():
    data = create_test_data()

    batch = create_batch(
        data["admin"]["token"],
        data,
    )

    worker = create_worker()

    response = client.delete(
        f"/api/v1/production-batches/{batch['id']}",
        headers=auth_header(
            worker["token"]
        ),
    )

    assert response.status_code == 403


def test_completed_production_order_cannot_create_batch():
    data = create_test_data()

    db = SessionLocal()

    try:
        order = db.get(
            ProductionOrder,
            data["order"]["id"],
        )

        from core.enums import ProductionOrderStatus

        order.status = ProductionOrderStatus.COMPLETED
        db.commit()

    finally:
        db.close()

    response = client.post(
        "/api/v1/production-batches",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json={
            "batch_number": (
                f"BATCH-{uuid4().hex[:8].upper()}"
            ),
            "production_order_id": data["order"]["id"],
            "planned_quantity": 1000,
            "produced_quantity": 0,
            "rejected_quantity": 0,
            "production_line_id": data["line"]["id"],
            "machine_id": data["machine"]["id"],
            "supervisor_id": data["supervisor"]["user_id"],
        },
    )

    assert response.status_code == 400


def test_cancelled_production_order_cannot_create_batch():
    data = create_test_data()

    db = SessionLocal()

    try:
        order = db.get(
            ProductionOrder,
            data["order"]["id"],
        )

        from core.enums import ProductionOrderStatus

        order.status = ProductionOrderStatus.CANCELLED
        db.commit()

    finally:
        db.close()

    response = client.post(
        "/api/v1/production-batches",
        headers=auth_header(
            data["admin"]["token"]
        ),
        json={
            "batch_number": (
                f"BATCH-{uuid4().hex[:8].upper()}"
            ),
            "production_order_id": data["order"]["id"],
            "planned_quantity": 1000,
            "produced_quantity": 0,
            "rejected_quantity": 0,
            "production_line_id": data["line"]["id"],
            "machine_id": data["machine"]["id"],
            "supervisor_id": data["supervisor"]["user_id"],
        },
    )

    assert response.status_code == 400

