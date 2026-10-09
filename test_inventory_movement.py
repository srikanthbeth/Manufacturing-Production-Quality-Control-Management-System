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
                    inventory_movements,
                    raw_materials,
                    production_lines,
                    plants,
                    products,
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


def create_store_manager():
    return create_user(
        role="Store Manager",
        email=f"store_{uuid4().hex[:8]}@example.com",
    )


def create_production_manager():
    return create_user(
        role="Production Manager",
        email=f"manager_{uuid4().hex[:8]}@example.com",
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


def create_raw_material(token, plant_id):
    material_code = f"MAT-{uuid4().hex[:6].upper()}"

    response = client.post(
        "/api/v1/raw-materials",
        headers=auth_headers(token),
        json={
            "name": "Steel Sheet",
            "material_code": material_code,
            "category": "Metal",
            "unit": "Kg",
            "available_quantity": 1000,
            "minimum_stock_level": 200,
            "reorder_level": 100,
            "supplier_reference": "SUP-001",
            "status": "Active",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_inventory_movement(
    token,
    raw_material_id,
    movement_type="Raw Material Receipt",
    quantity=100,
    reference_number=None,
    reason=None,
):
    payload = {
        "raw_material_id": raw_material_id,
        "movement_type": movement_type,
        "quantity": quantity,
    }

    if reference_number is not None:
        payload["reference_number"] = reference_number

    if reason is not None:
        payload["reason"] = reason

    response = client.post(
        "/api/v1/inventory-movements",
        headers=auth_headers(token),
        json=payload,
    )

    assert response.status_code == 201, response.text

    return response.json()


def setup_inventory():
    cleanup_database()

    admin = create_admin()

    store_manager = create_store_manager()

    production_manager = create_production_manager()

    worker = create_worker_user()

    plant = create_plant(
        admin["token"]
    )

    material = create_raw_material(
        admin["token"],
        plant["id"],
    )

    return (
        admin,
        store_manager,
        production_manager,
        worker,
        material,
    )


def test_create_raw_material_receipt():
    admin, _, _, _, material = setup_inventory()

    movement = create_inventory_movement(
        admin["token"],
        material["id"],
        "Raw Material Receipt",
        100,
    )

    assert movement["raw_material_id"] == material["id"]
    assert movement["movement_type"] == "Raw Material Receipt"
    assert float(movement["quantity"]) == 100


def test_create_material_consumption():
    admin, _, _, _, material = setup_inventory()

    movement = create_inventory_movement(
        admin["token"],
        material["id"],
        "Material Consumption",
        100,
    )

    assert movement["raw_material_id"] == material["id"]
    assert movement["movement_type"] == "Material Consumption"
    assert float(movement["quantity"]) == 100


def test_create_finished_goods_production():
    admin, _, _, _, material = setup_inventory()

    movement = create_inventory_movement(
        admin["token"],
        material["id"],
        "Finished Goods Production",
        100,
    )

    assert movement["raw_material_id"] == material["id"]
    assert movement["movement_type"] == "Finished Goods Production"
    assert float(movement["quantity"]) == 100


def test_create_rejected_goods():
    admin, _, _, _, material = setup_inventory()

    movement = create_inventory_movement(
        admin["token"],
        material["id"],
        "Rejected Goods",
        100,
    )

    assert movement["raw_material_id"] == material["id"]
    assert movement["movement_type"] == "Rejected Goods"
    assert float(movement["quantity"]) == 100


def test_create_stock_adjustment():
    admin, _, _, _, material = setup_inventory()

    movement = create_inventory_movement(
        admin["token"],
        material["id"],
        "Stock Adjustment",
        100,
    )

    assert movement["raw_material_id"] == material["id"]
    assert movement["movement_type"] == "Stock Adjustment"
    assert float(movement["quantity"]) == 100


def test_get_inventory_movement():
    admin, _, _, _, material = setup_inventory()

    movement = create_inventory_movement(
        admin["token"],
        material["id"],
    )

    response = client.get(
        f"/api/v1/inventory-movements/{movement['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == movement["id"]
    assert data["transaction_number"] == movement["transaction_number"]


def test_get_nonexistent_inventory_movement():
    admin, _, _, _, _ = setup_inventory()

    response = client.get(
        "/api/v1/inventory-movements/999999",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 404


def test_list_inventory_movements():
    admin, _, _, _, material = setup_inventory()

    create_inventory_movement(
        admin["token"],
        material["id"],
    )

    response = client.get(
        "/api/v1/inventory-movements",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1
    assert len(data["items"]) >= 1
    assert data["page"] == 1


def test_search_inventory_movement():
    admin, _, _, _, material = setup_inventory()

    movement = create_inventory_movement(
        admin["token"],
        material["id"],
        reference_number="PO-SEARCH-001",
    )

    response = client.get(
        "/api/v1/inventory-movements",
        headers=auth_headers(admin["token"]),
        params={
            "search": movement["transaction_number"]
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1

    assert any(
        item["id"] == movement["id"]
        for item in data["items"]
    )


def test_filter_by_movement_type():
    admin, _, _, _, material = setup_inventory()

    create_inventory_movement(
        admin["token"],
        material["id"],
        "Raw Material Receipt",
    )

    create_inventory_movement(
        admin["token"],
        material["id"],
        "Material Consumption",
        50,
    )

    response = client.get(
        "/api/v1/inventory-movements",
        headers=auth_headers(admin["token"]),
        params={
            "movement_type": "Material Consumption"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1

    for item in data["items"]:
        assert item["movement_type"] == "Material Consumption"


def test_filter_by_raw_material():
    admin, _, _, _, material = setup_inventory()

    movement = create_inventory_movement(
        admin["token"],
        material["id"],
    )

    response = client.get(
        "/api/v1/inventory-movements",
        headers=auth_headers(admin["token"]),
        params={
            "raw_material_id": material["id"]
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] >= 1

    assert any(
        item["id"] == movement["id"]
        for item in data["items"]
    )


def test_pagination():
    admin, _, _, _, material = setup_inventory()

    for _ in range(3):
        create_inventory_movement(
            admin["token"],
            material["id"],
        )

    response = client.get(
        "/api/v1/inventory-movements",
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


def test_stock_updated_after_receipt():
    admin, _, _, _, material = setup_inventory()

    initial_stock = float(material["available_quantity"])

    movement = create_inventory_movement(
        admin["token"],
        material["id"],
        "Raw Material Receipt",
        100,
    )

    assert float(movement["stock_before"]) == initial_stock
    assert float(movement["stock_after"]) == initial_stock + 100

    response = client.get(
        f"/api/v1/inventory-movements/stock/{material['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert float(data["available_quantity"]) == initial_stock + 100


def test_stock_updated_after_consumption():
    admin, _, _, _, material = setup_inventory()

    initial_stock = float(material["available_quantity"])

    movement = create_inventory_movement(
        admin["token"],
        material["id"],
        "Material Consumption",
        100,
    )

    assert float(movement["stock_before"]) == initial_stock
    assert float(movement["stock_after"]) == initial_stock - 100

    response = client.get(
        f"/api/v1/inventory-movements/stock/{material['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert float(data["available_quantity"]) == initial_stock - 100


def test_stock_status_available():
    admin, _, _, _, material = setup_inventory()

    response = client.get(
        f"/api/v1/inventory-movements/stock/{material['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["stock_status"] == "Available"


def test_stock_status_reorder_required():
    admin, _, _, _, material = setup_inventory()

    current_stock = float(material["available_quantity"])
    reorder_level = float(material["reorder_level"])

    quantity = current_stock - reorder_level

    if quantity <= 0:
        quantity = 1

    create_inventory_movement(
        admin["token"],
        material["id"],
        "Material Consumption",
        quantity,
    )

    response = client.get(
        f"/api/v1/inventory-movements/stock/{material['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["stock_status"] in [
        "Reorder Required",
        "Below Minimum Level",
        "Out of Stock",
    ]


def test_stock_status_out_of_stock():
    admin, _, _, _, material = setup_inventory()

    current_stock = float(material["available_quantity"])

    create_inventory_movement(
        admin["token"],
        material["id"],
        "Material Consumption",
        current_stock,
    )

    response = client.get(
        f"/api/v1/inventory-movements/stock/{material['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["stock_status"] == "Out of Stock"
    assert float(data["available_quantity"]) == 0


def test_insufficient_stock_rejected():
    admin, _, _, _, material = setup_inventory()

    current_stock = float(material["available_quantity"])

    response = client.post(
        "/api/v1/inventory-movements",
        headers=auth_headers(admin["token"]),
        json={
            "raw_material_id": material["id"],
            "movement_type": "Material Consumption",
            "quantity": current_stock + 1000,
        },
    )

    assert response.status_code == 400
    assert "Insufficient available stock" in response.text


def test_invalid_raw_material_rejected():
    admin, _, _, _, _ = setup_inventory()

    response = client.post(
        "/api/v1/inventory-movements",
        headers=auth_headers(admin["token"]),
        json={
            "raw_material_id": 999999,
            "movement_type": "Raw Material Receipt",
            "quantity": 100,
        },
    )

    assert response.status_code == 404


def test_zero_quantity_rejected():
    admin, _, _, _, material = setup_inventory()

    response = client.post(
        "/api/v1/inventory-movements",
        headers=auth_headers(admin["token"]),
        json={
            "raw_material_id": material["id"],
            "movement_type": "Raw Material Receipt",
            "quantity": 0,
        },
    )

    assert response.status_code == 422


def test_negative_quantity_rejected():
    admin, _, _, _, material = setup_inventory()

    response = client.post(
        "/api/v1/inventory-movements",
        headers=auth_headers(admin["token"]),
        json={
            "raw_material_id": material["id"],
            "movement_type": "Raw Material Receipt",
            "quantity": -10,
        },
    )

    assert response.status_code == 422


def test_missing_auth():
    cleanup_database()

    response = client.get(
        "/api/v1/inventory-movements"
    )

    assert response.status_code == 401


def test_worker_cannot_create_inventory_movement():
    admin, _, _, worker, material = setup_inventory()

    response = client.post(
        "/api/v1/inventory-movements",
        headers=auth_headers(worker["token"]),
        json={
            "raw_material_id": material["id"],
            "movement_type": "Raw Material Receipt",
            "quantity": 100,
        },
    )

    assert response.status_code == 403


def test_production_manager_can_create_inventory_movement():
    admin, _, production_manager, _, material = (
        setup_inventory()
    )

    movement = create_inventory_movement(
        production_manager["token"],
        material["id"],
        "Raw Material Receipt",
        100,
    )

    assert movement["raw_material_id"] == material["id"]


def test_store_manager_can_create_inventory_movement():
    admin, store_manager, _, _, material = (
        setup_inventory()
    )

    movement = create_inventory_movement(
        store_manager["token"],
        material["id"],
        "Raw Material Receipt",
        100,
    )

    assert movement["raw_material_id"] == material["id"]


def test_transaction_number_generated():
    admin, _, _, _, material = setup_inventory()

    movement = create_inventory_movement(
        admin["token"],
        material["id"],
    )

    assert movement["transaction_number"]
    assert movement["transaction_number"].startswith("INV-")


def test_transaction_history():
    admin, _, _, _, material = setup_inventory()

    create_inventory_movement(
        admin["token"],
        material["id"],
        "Raw Material Receipt",
        100,
    )

    create_inventory_movement(
        admin["token"],
        material["id"],
        "Material Consumption",
        50,
    )

    response = client.get(
        f"/api/v1/inventory-movements/history/{material['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["raw_material_id"] == material["id"]
    assert data["total_transactions"] == 2
    assert float(data["total_receipts"]) == 100
    assert float(data["total_consumption"]) == 50


def test_transaction_history_keeps_all_records():
    admin, _, _, _, material = setup_inventory()

    for _ in range(5):
        create_inventory_movement(
            admin["token"],
            material["id"],
            "Raw Material Receipt",
            10,
        )

    response = client.get(
        f"/api/v1/inventory-movements/history/{material['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_transactions"] == 5
    assert float(data["total_receipts"]) == 50


def test_reference_number_saved():
    admin, _, _, _, material = setup_inventory()

    movement = create_inventory_movement(
        admin["token"],
        material["id"],
        reference_number="PO-2026-001",
    )

    assert movement["reference_number"] == "PO-2026-001"


def test_reason_saved():
    admin, _, _, _, material = setup_inventory()

    movement = create_inventory_movement(
        admin["token"],
        material["id"],
        reason="Monthly stock receipt",
    )

    assert movement["reason"] == "Monthly stock receipt"


def test_stock_before_and_after_are_recorded():
    admin, _, _, _, material = setup_inventory()

    movement = create_inventory_movement(
        admin["token"],
        material["id"],
        "Raw Material Receipt",
        100,
    )

    assert movement["stock_before"] is not None
    assert movement["stock_after"] is not None

    assert (
        float(movement["stock_after"])
        == float(movement["stock_before"]) + 100
    )


def test_multiple_movements_maintain_transaction_history():
    admin, _, _, _, material = setup_inventory()

    first = create_inventory_movement(
        admin["token"],
        material["id"],
        "Raw Material Receipt",
        100,
    )

    second = create_inventory_movement(
        admin["token"],
        material["id"],
        "Material Consumption",
        30,
    )

    third = create_inventory_movement(
        admin["token"],
        material["id"],
        "Stock Adjustment",
        20,
    )

    response = client.get(
        f"/api/v1/inventory-movements/history/{material['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_transactions"] == 3

    assert float(data["total_receipts"]) == 100
    assert float(data["total_consumption"]) == 30
    assert float(data["total_adjustments"]) == 20

    assert first["transaction_number"] != second["transaction_number"]
    assert second["transaction_number"] != third["transaction_number"]
    assert first["transaction_number"] != third["transaction_number"]