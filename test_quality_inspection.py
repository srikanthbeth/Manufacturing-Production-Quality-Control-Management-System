import os
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "manufacturing_production_quality_test"
)

from datetime import datetime

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
                    quality_inspections,
                    production_batches,
                    production_orders,
                    machines,
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


def create_quality_manager():
    return create_user(
        role="Quality Manager",
        email=f"quality_{uuid4().hex[:8]}@example.com",
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
            "supervisor_id": supervisor_id,
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

    return (
        admin,
        plant,
        line,
        product,
        order,
        batch,
        supervisor,
    )


def create_quality_inspection(
    token,
    inspector_id,
    production_batch_id,
    inspection_type="Final Product Inspection",
    result="Pass",
):
    inspection_number = (
        f"QI-{uuid4().hex[:8].upper()}"
    )

    response = client.post(
        "/api/v1/quality-inspections",
        headers=auth_headers(token),
        json={
            "inspection_number": inspection_number,
            "inspection_type": inspection_type,
            "inspector_id": inspector_id,
            "production_batch_id": production_batch_id,
            "inspection_date": datetime.now().isoformat(),
            "parameters": "Product dimensions",
            "expected_value": "100 mm",
            "actual_value": "100 mm",
            "result": result,
            "remarks": "Inspection completed",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def test_create_quality_inspection():
    cleanup_database()

    admin, _, _, _, _, batch, _ = setup_batch()

    inspector = create_quality_manager()

    inspection = create_quality_inspection(
        admin["token"],
        inspector["id"],
        batch["id"],
    )

    assert inspection["inspection_number"].startswith("QI-")
    assert inspection["inspection_type"] == (
        "Final Product Inspection"
    )
    assert inspection["inspector_id"] == inspector["id"]
    assert inspection["production_batch_id"] == batch["id"]
    assert inspection["result"] == "Pass"


def test_create_incoming_material_inspection():
    cleanup_database()

    admin, _, _, _, _, batch, _ = setup_batch()

    inspector = create_quality_manager()

    inspection = create_quality_inspection(
        admin["token"],
        inspector["id"],
        batch["id"],
        "Incoming Material Inspection",
    )

    assert inspection["inspection_type"] == (
        "Incoming Material Inspection"
    )


def test_create_in_process_inspection():
    cleanup_database()

    admin, _, _, _, _, batch, _ = setup_batch()

    inspector = create_quality_manager()

    inspection = create_quality_inspection(
        admin["token"],
        inspector["id"],
        batch["id"],
        "In-Process Inspection",
    )

    assert inspection["inspection_type"] == (
        "In-Process Inspection"
    )


def test_get_quality_inspection():
    cleanup_database()

    admin, _, _, _, _, batch, _ = setup_batch()

    inspector = create_quality_manager()

    inspection = create_quality_inspection(
        admin["token"],
        inspector["id"],
        batch["id"],
    )

    response = client.get(
        f"/api/v1/quality-inspections/{inspection['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200
    assert response.json()["id"] == inspection["id"]


def test_list_quality_inspections():
    cleanup_database()

    admin, _, _, _, _, batch, _ = setup_batch()

    inspector = create_quality_manager()

    create_quality_inspection(
        admin["token"],
        inspector["id"],
        batch["id"],
    )

    response = client.get(
        "/api/v1/quality-inspections",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    assert data["page"] == 1


def test_search_quality_inspection():
    cleanup_database()

    admin, _, _, _, _, batch, _ = setup_batch()

    inspector = create_quality_manager()

    inspection = create_quality_inspection(
        admin["token"],
        inspector["id"],
        batch["id"],
    )

    response = client.get(
        "/api/v1/quality-inspections",
        headers=auth_headers(admin["token"]),
        params={
            "search": inspection["inspection_number"]
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1
    assert any(
        item["id"] == inspection["id"]
        for item in data["items"]
    )


def test_filter_by_inspection_type():
    cleanup_database()

    admin, _, _, _, _, batch, _ = setup_batch()

    inspector = create_quality_manager()

    create_quality_inspection(
        admin["token"],
        inspector["id"],
        batch["id"],
        "Incoming Material Inspection",
    )

    create_quality_inspection(
        admin["token"],
        inspector["id"],
        batch["id"],
        "Final Product Inspection",
    )

    response = client.get(
        "/api/v1/quality-inspections",
        headers=auth_headers(admin["token"]),
        params={
            "inspection_type": (
                "Incoming Material Inspection"
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1

    for item in data["items"]:
        assert item["inspection_type"] == (
            "Incoming Material Inspection"
        )


def test_filter_by_result():
    cleanup_database()

    admin, _, _, _, _, batch, _ = setup_batch()

    inspector = create_quality_manager()

    create_quality_inspection(
        admin["token"],
        inspector["id"],
        batch["id"],
        result="Pass",
    )

    create_quality_inspection(
        admin["token"],
        inspector["id"],
        batch["id"],
        result="Fail",
    )

    response = client.get(
        "/api/v1/quality-inspections",
        headers=auth_headers(admin["token"]),
        params={
            "result": "Fail"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1

    for item in data["items"]:
        assert item["result"] == "Fail"


def test_filter_by_batch():
    cleanup_database()

    admin, _, _, _, _, batch, _ = setup_batch()

    inspector = create_quality_manager()

    inspection = create_quality_inspection(
        admin["token"],
        inspector["id"],
        batch["id"],
    )

    response = client.get(
        "/api/v1/quality-inspections",
        headers=auth_headers(admin["token"]),
        params={
            "production_batch_id": batch["id"]
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1
    assert any(
        item["id"] == inspection["id"]
        for item in data["items"]
    )


def test_filter_by_inspector():
    cleanup_database()

    admin, _, _, _, _, batch, _ = setup_batch()

    inspector = create_quality_manager()

    inspection = create_quality_inspection(
        admin["token"],
        inspector["id"],
        batch["id"],
    )

    response = client.get(
        "/api/v1/quality-inspections",
        headers=auth_headers(admin["token"]),
        params={
            "inspector_id": inspector["id"]
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1
    assert any(
        item["id"] == inspection["id"]
        for item in data["items"]
    )


def test_pagination():
    cleanup_database()

    admin, _, _, _, _, batch, _ = setup_batch()

    inspector = create_quality_manager()

    for _ in range(3):
        create_quality_inspection(
            admin["token"],
            inspector["id"],
            batch["id"],
        )

    response = client.get(
        "/api/v1/quality-inspections",
        headers=auth_headers(admin["token"]),
        params={
            "page": 1,
            "limit": 2,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 1
    assert data["limit"] == 2
    assert len(data["items"]) <= 2
    assert data["total"] >= 3


def test_duplicate_inspection_number_rejected():
    cleanup_database()

    admin, _, _, _, _, batch, _ = setup_batch()

    inspector = create_quality_manager()

    inspection_number = (
        f"QI-{uuid4().hex[:8].upper()}"
    )

    payload = {
        "inspection_number": inspection_number,
        "inspection_type": "Final Product Inspection",
        "inspector_id": inspector["id"],
        "production_batch_id": batch["id"],
        "inspection_date": datetime.now().isoformat(),
        "parameters": "Product dimensions",
        "expected_value": "100 mm",
        "actual_value": "100 mm",
        "result": "Pass",
        "remarks": "First inspection",
    }

    response = client.post(
        "/api/v1/quality-inspections",
        headers=auth_headers(admin["token"]),
        json=payload,
    )

    assert response.status_code == 201, response.text

    response = client.post(
        "/api/v1/quality-inspections",
        headers=auth_headers(admin["token"]),
        json=payload,
    )

    assert response.status_code == 400
    assert "already exists" in response.text.lower()


def test_invalid_inspection_type_rejected():
    cleanup_database()

    admin, _, _, _, _, batch, _ = setup_batch()

    inspector = create_quality_manager()

    response = client.post(
        "/api/v1/quality-inspections",
        headers=auth_headers(admin["token"]),
        json={
            "inspection_number": (
                f"QI-{uuid4().hex[:8].upper()}"
            ),
            "inspection_type": "Invalid Inspection",
            "inspector_id": inspector["id"],
            "production_batch_id": batch["id"],
            "inspection_date": datetime.now().isoformat(),
            "parameters": "Product dimensions",
            "expected_value": "100 mm",
            "actual_value": "100 mm",
            "result": "Pass",
            "remarks": "Test",
        },
    )

    assert response.status_code == 422


def test_invalid_result_rejected():
    cleanup_database()

    admin, _, _, _, _, batch, _ = setup_batch()

    inspector = create_quality_manager()

    response = client.post(
        "/api/v1/quality-inspections",
        headers=auth_headers(admin["token"]),
        json={
            "inspection_number": (
                f"QI-{uuid4().hex[:8].upper()}"
            ),
            "inspection_type": "Final Product Inspection",
            "inspector_id": inspector["id"],
            "production_batch_id": batch["id"],
            "inspection_date": datetime.now().isoformat(),
            "parameters": "Product dimensions",
            "expected_value": "100 mm",
            "actual_value": "100 mm",
            "result": "Invalid",
            "remarks": "Test",
        },
    )

    assert response.status_code == 422


def test_invalid_inspector_rejected():
    cleanup_database()

    admin, _, _, _, _, batch, _ = setup_batch()

    response = client.post(
        "/api/v1/quality-inspections",
        headers=auth_headers(admin["token"]),
        json={
            "inspection_number": (
                f"QI-{uuid4().hex[:8].upper()}"
            ),
            "inspection_type": "Final Product Inspection",
            "inspector_id": 999999,
            "production_batch_id": batch["id"],
            "inspection_date": datetime.now().isoformat(),
            "parameters": "Product dimensions",
            "expected_value": "100 mm",
            "actual_value": "100 mm",
            "result": "Pass",
            "remarks": "Test",
        },
    )

    assert response.status_code == 404


def test_invalid_batch_rejected():
    cleanup_database()

    admin = create_admin()
    inspector = create_quality_manager()

    response = client.post(
        "/api/v1/quality-inspections",
        headers=auth_headers(admin["token"]),
        json={
            "inspection_number": (
                f"QI-{uuid4().hex[:8].upper()}"
            ),
            "inspection_type": "Final Product Inspection",
            "inspector_id": inspector["id"],
            "production_batch_id": 999999,
            "inspection_date": datetime.now().isoformat(),
            "parameters": "Product dimensions",
            "expected_value": "100 mm",
            "actual_value": "100 mm",
            "result": "Pass",
            "remarks": "Test",
        },
    )

    assert response.status_code == 404


def test_missing_auth_rejected():
    cleanup_database()

    response = client.get(
        "/api/v1/quality-inspections"
    )

    assert response.status_code == 401


def test_worker_cannot_create_inspection():
    cleanup_database()

    admin, _, _, _, _, batch, _ = setup_batch()

    worker = create_worker_user()

    response = client.post(
        "/api/v1/quality-inspections",
        headers=auth_headers(worker["token"]),
        json={
            "inspection_number": (
                f"QI-{uuid4().hex[:8].upper()}"
            ),
            "inspection_type": "Final Product Inspection",
            "inspector_id": worker["id"],
            "production_batch_id": batch["id"],
            "inspection_date": datetime.now().isoformat(),
            "parameters": "Product dimensions",
            "expected_value": "100 mm",
            "actual_value": "100 mm",
            "result": "Pass",
            "remarks": "Test",
        },
    )

    assert response.status_code == 403


def test_quality_manager_can_create_inspection():
    cleanup_database()

    admin, _, _, _, _, batch, _ = setup_batch()

    quality_manager = create_quality_manager()

    inspection = create_quality_inspection(
        quality_manager["token"],
        quality_manager["id"],
        batch["id"],
    )

    assert inspection["inspector_id"] == (
        quality_manager["id"]
    )


def test_production_manager_can_view_inspections():
    cleanup_database()

    admin, _, _, _, _, batch, _ = setup_batch()

    inspector = create_quality_manager()

    inspection = create_quality_inspection(
        admin["token"],
        inspector["id"],
        batch["id"],
    )

    production_manager = create_production_manager()

    response = client.get(
        f"/api/v1/quality-inspections/{inspection['id']}",
        headers=auth_headers(
            production_manager["token"]
        ),
    )

    assert response.status_code == 200
    assert response.json()["id"] == inspection["id"]


def test_production_supervisor_can_view_inspections():
    cleanup_database()

    admin, _, _, _, _, batch, _ = setup_batch()

    inspector = create_quality_manager()

    inspection = create_quality_inspection(
        admin["token"],
        inspector["id"],
        batch["id"],
    )

    supervisor = create_production_supervisor()

    response = client.get(
        f"/api/v1/quality-inspections/{inspection['id']}",
        headers=auth_headers(
            supervisor["token"]
        ),
    )

    assert response.status_code == 200


def test_worker_cannot_view_inspections():
    cleanup_database()

    admin, _, _, _, _, batch, _ = setup_batch()

    inspector = create_quality_manager()

    inspection = create_quality_inspection(
        admin["token"],
        inspector["id"],
        batch["id"],
    )

    worker = create_worker_user()

    response = client.get(
        f"/api/v1/quality-inspections/{inspection['id']}",
        headers=auth_headers(worker["token"]),
    )

    assert response.status_code == 403


def test_update_quality_inspection():
    cleanup_database()

    admin, _, _, _, _, batch, _ = setup_batch()

    inspector = create_quality_manager()

    inspection = create_quality_inspection(
        admin["token"],
        inspector["id"],
        batch["id"],
    )

    response = client.put(
        f"/api/v1/quality-inspections/{inspection['id']}",
        headers=auth_headers(admin["token"]),
        json={
            "actual_value": "101 mm",
            "result": "Fail",
            "remarks": "Dimension outside tolerance",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["actual_value"] == "101 mm"
    assert data["result"] == "Fail"
    assert data["remarks"] == (
        "Dimension outside tolerance"
    )


def test_quality_manager_can_update_inspection():
    cleanup_database()

    admin, _, _, _, _, batch, _ = setup_batch()

    inspector = create_quality_manager()

    inspection = create_quality_inspection(
        admin["token"],
        inspector["id"],
        batch["id"],
    )

    response = client.put(
        f"/api/v1/quality-inspections/{inspection['id']}",
        headers=auth_headers(
            inspector["token"]
        ),
        json={
            "result": "Fail",
        },
    )

    assert response.status_code == 200
    assert response.json()["result"] == "Fail"


def test_worker_cannot_update_inspection():
    cleanup_database()

    admin, _, _, _, _, batch, _ = setup_batch()

    inspector = create_quality_manager()

    inspection = create_quality_inspection(
        admin["token"],
        inspector["id"],
        batch["id"],
    )

    worker = create_worker_user()

    response = client.put(
        f"/api/v1/quality-inspections/{inspection['id']}",
        headers=auth_headers(worker["token"]),
        json={
            "result": "Fail",
        },
    )

    assert response.status_code == 403


def test_quality_inspection_not_found():
    cleanup_database()

    admin = create_admin()

    response = client.get(
        "/api/v1/quality-inspections/999999",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 404


def test_delete_quality_inspection():
    cleanup_database()

    admin, _, _, _, _, batch, _ = setup_batch()

    inspector = create_quality_manager()

    inspection = create_quality_inspection(
        admin["token"],
        inspector["id"],
        batch["id"],
    )

    response = client.delete(
        f"/api/v1/quality-inspections/{inspection['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 204

    response = client.get(
        f"/api/v1/quality-inspections/{inspection['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 404


def test_worker_cannot_delete_inspection():
    cleanup_database()

    admin, _, _, _, _, batch, _ = setup_batch()

    inspector = create_quality_manager()

    inspection = create_quality_inspection(
        admin["token"],
        inspector["id"],
        batch["id"],
    )

    worker = create_worker_user()

    response = client.delete(
        f"/api/v1/quality-inspections/{inspection['id']}",
        headers=auth_headers(worker["token"]),
    )

    assert response.status_code == 403


def test_invalid_page_rejected():
    cleanup_database()

    admin = create_admin()

    response = client.get(
        "/api/v1/quality-inspections",
        headers=auth_headers(admin["token"]),
        params={
            "page": 0,
        },
    )

    assert response.status_code == 422


def test_invalid_limit_rejected():
    cleanup_database()

    admin = create_admin()

    response = client.get(
        "/api/v1/quality-inspections",
        headers=auth_headers(admin["token"]),
        params={
            "limit": 101,
        },
    )

    assert response.status_code == 422