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
                    defects,
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


def create_user(
    role="Worker",
    email=None,
):
    if email is None:
        email = (
            f"user_{uuid4().hex[:8]}"
            "@example.com"
        )

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Test@12345",
            "full_name": "Test User",
        },
    )

    assert response.status_code in [
        200,
        201,
    ], response.text

    user_id = response.json()["id"]

    db = SessionLocal()

    try:
        user = db.get(
            User,
            user_id,
        )

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

    assert login_response.status_code == 200

    return {
        "id": user_id,
        "token": login_response.json()[
            "access_token"
        ],
    }


def create_admin():
    return create_user(
        role="Super Admin"
    )


def create_quality_manager():
    return create_user(
        role="Quality Manager"
    )


def create_production_manager():
    return create_user(
        role="Production Manager"
    )


def create_production_supervisor():
    return create_user(
        role="Production Supervisor"
    )


def create_worker():
    return create_user(
        role="Worker"
    )


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}"
    }


def create_plant(token):
    response = client.post(
        "/api/v1/plants",
        headers=auth_headers(token),
        json={
            "name": "Main Plant",
            "code": (
                f"PLT-{uuid4().hex[:6].upper()}"
            ),
            "address": "Industrial Area",
            "city": "Tirupati",
            "state": "Andhra Pradesh",
            "production_capacity": 10000,
            "status": "Active",
        },
    )

    assert response.status_code == 201

    return response.json()


def create_line(
    token,
    plant_id,
):
    response = client.post(
        "/api/v1/production-lines",
        headers=auth_headers(token),
        json={
            "name": "Assembly Line",
            "code": (
                f"LINE-{uuid4().hex[:6].upper()}"
            ),
            "plant_id": plant_id,
            "production_capacity": 5000,
            "status": "Active",
        },
    )

    assert response.status_code == 201

    return response.json()


def create_product(token):
    response = client.post(
        "/api/v1/products",
        headers=auth_headers(token),
        json={
            "name": "Test Product",
            "code": (
                f"PRD-{uuid4().hex[:6].upper()}"
            ),
            "category": "Finished Goods",
            "sku": (
                f"SKU-{uuid4().hex[:8].upper()}"
            ),
            "unit_of_measurement": "Piece",
            "standard_production_time": 60,
            "status": "Active",
        },
    )

    assert response.status_code == 201

    return response.json()


def create_machine(
    token,
    production_line_id,
):
    response = client.post(
        "/api/v1/machines",
        headers=auth_headers(token),
        json={
            "name": "Assembly Machine",
            "machine_code": (
                f"MCH-{uuid4().hex[:6].upper()}"
            ),
            "machine_type": "Assembly",
            "production_line_id": (
                production_line_id
            ),
            "installation_date": "2025-01-01",
            "status": "Idle",
        },
    )

    assert response.status_code == 201

    return response.json()


def create_order(
    token,
    product_id,
    production_line_id,
    supervisor_id,
):
    response = client.post(
        "/api/v1/production-orders",
        headers=auth_headers(token),
        json={
            "order_number": (
                f"ORD-{uuid4().hex[:8].upper()}"
            ),
            "product_id": product_id,
            "production_line_id": (
                production_line_id
            ),
            "quantity": 1000,
            "target_date": "2026-12-31",
            "supervisor_id": supervisor_id,
            "priority": "High",
            "status": "Draft",
        },
    )

    assert response.status_code == 201

    return response.json()


def create_batch(
    token,
    order_id,
    line_id,
    machine_id,
    supervisor_id,
):
    response = client.post(
        "/api/v1/production-batches",
        headers=auth_headers(token),
        json={
            "batch_number": (
                f"BATCH-{uuid4().hex[:8].upper()}"
            ),
            "production_order_id": order_id,
            "production_line_id": line_id,
            "machine_id": machine_id,
            "supervisor_id": supervisor_id,
            "planned_quantity": 500,
            "status": "Planned",
        },
    )

    assert response.status_code == 201

    return response.json()


def setup_data():
    admin = create_admin()

    plant = create_plant(
        admin["token"]
    )

    line = create_line(
        admin["token"],
        plant["id"],
    )

    product = create_product(
        admin["token"]
    )

    supervisor = create_production_supervisor()

    order = create_order(
        admin["token"],
        product["id"],
        line["id"],
        supervisor["id"],
    )

    machine = create_machine(
        admin["token"],
        line["id"],
    )

    batch = create_batch(
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


def create_defect(
    token,
    batch_id,
    product_id,
    severity="Minor",
    resolution_status="Open",
):
    response = client.post(
        "/api/v1/defects",
        headers=auth_headers(token),
        json={
            "defect_number": (
                f"DEF-{uuid4().hex[:8].upper()}"
            ),
            "defect_type": "Dimensional Defect",
            "severity": severity,
            "production_batch_id": batch_id,
            "product_id": product_id,
            "quantity_affected": 5,
            "root_cause": (
                "Incorrect machine calibration"
            ),
            "corrective_action": (
                "Recalibrate machine"
            ),
            "resolution_status": (
                resolution_status
            ),
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def test_create_defect():
    cleanup_database()

    (
        admin,
        _,
        _,
        product,
        _,
        batch,
        _,
    ) = setup_data()

    defect = create_defect(
        admin["token"],
        batch["id"],
        product["id"],
    )

    assert defect["defect_number"].startswith(
        "DEF-"
    )
    assert defect["severity"] == "Minor"
    assert defect["quantity_affected"] == 5
    assert defect["resolution_status"] == "Open"


def test_create_major_defect():
    cleanup_database()

    (
        admin,
        _,
        _,
        product,
        _,
        batch,
        _,
    ) = setup_data()

    defect = create_defect(
        admin["token"],
        batch["id"],
        product["id"],
        severity="Major",
    )

    assert defect["severity"] == "Major"


def test_create_critical_defect():
    cleanup_database()

    (
        admin,
        _,
        _,
        product,
        _,
        batch,
        _,
    ) = setup_data()

    defect = create_defect(
        admin["token"],
        batch["id"],
        product["id"],
        severity="Critical",
    )

    assert defect["severity"] == "Critical"


def test_get_defect():
    cleanup_database()

    (
        admin,
        _,
        _,
        product,
        _,
        batch,
        _,
    ) = setup_data()

    defect = create_defect(
        admin["token"],
        batch["id"],
        product["id"],
    )

    response = client.get(
        f"/api/v1/defects/{defect['id']}",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 200
    assert response.json()["id"] == defect["id"]


def test_list_defects():
    cleanup_database()

    (
        admin,
        _,
        _,
        product,
        _,
        batch,
        _,
    ) = setup_data()

    create_defect(
        admin["token"],
        batch["id"],
        product["id"],
    )

    response = client.get(
        "/api/v1/defects",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1
    assert len(data["items"]) >= 1


def test_search_defect():
    cleanup_database()

    (
        admin,
        _,
        _,
        product,
        _,
        batch,
        _,
    ) = setup_data()

    defect = create_defect(
        admin["token"],
        batch["id"],
        product["id"],
    )

    response = client.get(
        "/api/v1/defects",
        headers=auth_headers(
            admin["token"]
        ),
        params={
            "search": defect[
                "defect_number"
            ]
        },
    )

    assert response.status_code == 200

    assert any(
        item["id"] == defect["id"]
        for item in response.json()["items"]
    )


def test_filter_by_severity():
    cleanup_database()

    (
        admin,
        _,
        _,
        product,
        _,
        batch,
        _,
    ) = setup_data()

    create_defect(
        admin["token"],
        batch["id"],
        product["id"],
        severity="Critical",
    )

    response = client.get(
        "/api/v1/defects",
        headers=auth_headers(
            admin["token"]
        ),
        params={
            "severity": "Critical"
        },
    )

    assert response.status_code == 200

    for item in response.json()["items"]:
        assert item["severity"] == "Critical"


def test_filter_by_resolution_status():
    cleanup_database()

    (
        admin,
        _,
        _,
        product,
        _,
        batch,
        _,
    ) = setup_data()

    create_defect(
        admin["token"],
        batch["id"],
        product["id"],
        resolution_status="Resolved",
    )

    response = client.get(
        "/api/v1/defects",
        headers=auth_headers(
            admin["token"]
        ),
        params={
            "resolution_status": "Resolved"
        },
    )

    assert response.status_code == 200

    for item in response.json()["items"]:
        assert item["resolution_status"] == (
            "Resolved"
        )


def test_filter_by_batch():
    cleanup_database()

    (
        admin,
        _,
        _,
        product,
        _,
        batch,
        _,
    ) = setup_data()

    defect = create_defect(
        admin["token"],
        batch["id"],
        product["id"],
    )

    response = client.get(
        "/api/v1/defects",
        headers=auth_headers(
            admin["token"]
        ),
        params={
            "production_batch_id": batch["id"]
        },
    )

    assert response.status_code == 200

    assert any(
        item["id"] == defect["id"]
        for item in response.json()["items"]
    )


def test_filter_by_product():
    cleanup_database()

    (
        admin,
        _,
        _,
        product,
        _,
        batch,
        _,
    ) = setup_data()

    defect = create_defect(
        admin["token"],
        batch["id"],
        product["id"],
    )

    response = client.get(
        "/api/v1/defects",
        headers=auth_headers(
            admin["token"]
        ),
        params={
            "product_id": product["id"]
        },
    )

    assert response.status_code == 200

    assert any(
        item["id"] == defect["id"]
        for item in response.json()["items"]
    )


def test_pagination():
    cleanup_database()

    (
        admin,
        _,
        _,
        product,
        _,
        batch,
        _,
    ) = setup_data()

    for _ in range(3):
        create_defect(
            admin["token"],
            batch["id"],
            product["id"],
        )

    response = client.get(
        "/api/v1/defects",
        headers=auth_headers(
            admin["token"]
        ),
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


def test_duplicate_defect_number_rejected():
    cleanup_database()

    (
        admin,
        _,
        _,
        product,
        _,
        batch,
        _,
    ) = setup_data()

    defect_number = (
        f"DEF-{uuid4().hex[:8].upper()}"
    )

    payload = {
        "defect_number": defect_number,
        "defect_type": "Crack",
        "severity": "Major",
        "production_batch_id": batch["id"],
        "product_id": product["id"],
        "quantity_affected": 10,
        "root_cause": "Material issue",
        "corrective_action": "Replace material",
        "resolution_status": "Open",
    }

    response = client.post(
        "/api/v1/defects",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 201

    response = client.post(
        "/api/v1/defects",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 400


def test_invalid_severity_rejected():
    cleanup_database()

    (
        admin,
        _,
        _,
        product,
        _,
        batch,
        _,
    ) = setup_data()

    response = client.post(
        "/api/v1/defects",
        headers=auth_headers(
            admin["token"]
        ),
        json={
            "defect_number": (
                f"DEF-{uuid4().hex[:8].upper()}"
            ),
            "defect_type": "Crack",
            "severity": "Invalid",
            "production_batch_id": batch["id"],
            "product_id": product["id"],
            "quantity_affected": 5,
            "root_cause": "Material issue",
            "resolution_status": "Open",
        },
    )

    assert response.status_code == 422


def test_invalid_resolution_status_rejected():
    cleanup_database()

    (
        admin,
        _,
        _,
        product,
        _,
        batch,
        _,
    ) = setup_data()

    response = client.post(
        "/api/v1/defects",
        headers=auth_headers(
            admin["token"]
        ),
        json={
            "defect_number": (
                f"DEF-{uuid4().hex[:8].upper()}"
            ),
            "defect_type": "Crack",
            "severity": "Major",
            "production_batch_id": batch["id"],
            "product_id": product["id"],
            "quantity_affected": 5,
            "root_cause": "Material issue",
            "resolution_status": "Invalid",
        },
    )

    assert response.status_code == 422


def test_invalid_quantity_rejected():
    cleanup_database()

    (
        admin,
        _,
        _,
        product,
        _,
        batch,
        _,
    ) = setup_data()

    response = client.post(
        "/api/v1/defects",
        headers=auth_headers(
            admin["token"]
        ),
        json={
            "defect_number": (
                f"DEF-{uuid4().hex[:8].upper()}"
            ),
            "defect_type": "Crack",
            "severity": "Major",
            "production_batch_id": batch["id"],
            "product_id": product["id"],
            "quantity_affected": 0,
            "root_cause": "Material issue",
            "resolution_status": "Open",
        },
    )

    assert response.status_code == 422


def test_invalid_batch_rejected():
    cleanup_database()

    admin = create_admin()
    product = create_product(
        admin["token"]
    )

    response = client.post(
        "/api/v1/defects",
        headers=auth_headers(
            admin["token"]
        ),
        json={
            "defect_number": (
                f"DEF-{uuid4().hex[:8].upper()}"
            ),
            "defect_type": "Crack",
            "severity": "Major",
            "production_batch_id": 999999,
            "product_id": product["id"],
            "quantity_affected": 5,
            "root_cause": "Material issue",
            "resolution_status": "Open",
        },
    )

    assert response.status_code == 404


def test_invalid_product_rejected():
    cleanup_database()

    (
        admin,
        _,
        _,
        _,
        _,
        batch,
        _,
    ) = setup_data()

    response = client.post(
        "/api/v1/defects",
        headers=auth_headers(
            admin["token"]
        ),
        json={
            "defect_number": (
                f"DEF-{uuid4().hex[:8].upper()}"
            ),
            "defect_type": "Crack",
            "severity": "Major",
            "production_batch_id": batch["id"],
            "product_id": 999999,
            "quantity_affected": 5,
            "root_cause": "Material issue",
            "resolution_status": "Open",
        },
    )

    assert response.status_code == 404


def test_missing_auth_rejected():
    cleanup_database()

    response = client.get(
        "/api/v1/defects"
    )

    assert response.status_code == 401


def test_worker_cannot_create_defect():
    cleanup_database()

    (
        admin,
        _,
        _,
        product,
        _,
        batch,
        _,
    ) = setup_data()

    worker = create_worker()

    response = client.post(
        "/api/v1/defects",
        headers=auth_headers(
            worker["token"]
        ),
        json={
            "defect_number": (
                f"DEF-{uuid4().hex[:8].upper()}"
            ),
            "defect_type": "Crack",
            "severity": "Major",
            "production_batch_id": batch["id"],
            "product_id": product["id"],
            "quantity_affected": 5,
            "root_cause": "Material issue",
            "resolution_status": "Open",
        },
    )

    assert response.status_code == 403


def test_quality_manager_can_create_defect():
    cleanup_database()

    (
        admin,
        _,
        _,
        product,
        _,
        batch,
        _,
    ) = setup_data()

    manager = create_quality_manager()

    defect = create_defect(
        manager["token"],
        batch["id"],
        product["id"],
    )

    assert defect["id"] > 0


def test_production_manager_can_view_defect():
    cleanup_database()

    (
        admin,
        _,
        _,
        product,
        _,
        batch,
        _,
    ) = setup_data()

    defect = create_defect(
        admin["token"],
        batch["id"],
        product["id"],
    )

    manager = create_production_manager()

    response = client.get(
        f"/api/v1/defects/{defect['id']}",
        headers=auth_headers(
            manager["token"]
        ),
    )

    assert response.status_code == 200


def test_production_supervisor_can_view_defect():
    cleanup_database()

    (
        admin,
        _,
        _,
        product,
        _,
        batch,
        _,
    ) = setup_data()

    defect = create_defect(
        admin["token"],
        batch["id"],
        product["id"],
    )

    supervisor = create_production_supervisor()

    response = client.get(
        f"/api/v1/defects/{defect['id']}",
        headers=auth_headers(
            supervisor["token"]
        ),
    )

    assert response.status_code == 200


def test_worker_cannot_view_defect():
    cleanup_database()

    (
        admin,
        _,
        _,
        product,
        _,
        batch,
        _,
    ) = setup_data()

    defect = create_defect(
        admin["token"],
        batch["id"],
        product["id"],
    )

    worker = create_worker()

    response = client.get(
        f"/api/v1/defects/{defect['id']}",
        headers=auth_headers(
            worker["token"]
        ),
    )

    assert response.status_code == 403


def test_update_defect():
    cleanup_database()

    (
        admin,
        _,
        _,
        product,
        _,
        batch,
        _,
    ) = setup_data()

    defect = create_defect(
        admin["token"],
        batch["id"],
        product["id"],
    )

    response = client.put(
        f"/api/v1/defects/{defect['id']}",
        headers=auth_headers(
            admin["token"]
        ),
        json={
            "severity": "Critical",
            "quantity_affected": 20,
            "resolution_status": "In Progress",
            "corrective_action": (
                "Replace affected components"
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["severity"] == "Critical"
    assert data["quantity_affected"] == 20
    assert data["resolution_status"] == (
        "In Progress"
    )


def test_quality_manager_can_update_defect():
    cleanup_database()

    (
        admin,
        _,
        _,
        product,
        _,
        batch,
        _,
    ) = setup_data()

    defect = create_defect(
        admin["token"],
        batch["id"],
        product["id"],
    )

    manager = create_quality_manager()

    response = client.put(
        f"/api/v1/defects/{defect['id']}",
        headers=auth_headers(
            manager["token"]
        ),
        json={
            "resolution_status": "Resolved"
        },
    )

    assert response.status_code == 200
    assert response.json()[
        "resolution_status"
    ] == "Resolved"


def test_worker_cannot_update_defect():
    cleanup_database()

    (
        admin,
        _,
        _,
        product,
        _,
        batch,
        _,
    ) = setup_data()

    defect = create_defect(
        admin["token"],
        batch["id"],
        product["id"],
    )

    worker = create_worker()

    response = client.put(
        f"/api/v1/defects/{defect['id']}",
        headers=auth_headers(
            worker["token"]
        ),
        json={
            "severity": "Critical"
        },
    )

    assert response.status_code == 403


def test_defect_not_found():
    cleanup_database()

    admin = create_admin()

    response = client.get(
        "/api/v1/defects/999999",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 404


def test_delete_defect():
    cleanup_database()

    (
        admin,
        _,
        _,
        product,
        _,
        batch,
        _,
    ) = setup_data()

    defect = create_defect(
        admin["token"],
        batch["id"],
        product["id"],
    )

    response = client.delete(
        f"/api/v1/defects/{defect['id']}",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 204

    response = client.get(
        f"/api/v1/defects/{defect['id']}",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 404


def test_worker_cannot_delete_defect():
    cleanup_database()

    (
        admin,
        _,
        _,
        product,
        _,
        batch,
        _,
    ) = setup_data()

    defect = create_defect(
        admin["token"],
        batch["id"],
        product["id"],
    )

    worker = create_worker()

    response = client.delete(
        f"/api/v1/defects/{defect['id']}",
        headers=auth_headers(
            worker["token"]
        ),
    )

    assert response.status_code == 403


def test_invalid_page_rejected():
    cleanup_database()

    admin = create_admin()

    response = client.get(
        "/api/v1/defects",
        headers=auth_headers(
            admin["token"]
        ),
        params={
            "page": 0
        },
    )

    assert response.status_code == 422


def test_invalid_limit_rejected():
    cleanup_database()

    admin = create_admin()

    response = client.get(
        "/api/v1/defects",
        headers=auth_headers(
            admin["token"]
        ),
        params={
            "limit": 101
        },
    )

    assert response.status_code == 422