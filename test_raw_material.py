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
from core.enums import UserRole


client = TestClient(app)


def setup_database():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        db.execute(
            text(
                "TRUNCATE TABLE "
                "material_transactions, "
                "raw_materials, "
                "production_lines, "
                "plants, "
                "products, "
                "auth_tokens, "
                "users "
                "RESTART IDENTITY CASCADE"
            )
        )
        db.commit()
    finally:
        db.close()


def create_user(
    role=UserRole.WORKER,
    email=None,
    password="Password@123",
):
    if email is None:
        email = f"{uuid4().hex}@example.com"

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": f"Test User {uuid4().hex[:6]}",
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 201, response.text

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.email == email).first()

        if role != UserRole.WORKER:
            user.role = role
            db.commit()
    finally:
        db.close()

    return {
        "email": email,
        "password": password,
    }


def login_user(email, password="Password@123"):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200, response.text

    return response.json()["access_token"]


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def create_admin():
    user = create_user(
        role=UserRole.SUPER_ADMIN,
    )

    token = login_user(
        user["email"],
        user["password"],
    )

    return {
        "token": token,
        "email": user["email"],
    }


def create_store_manager():
    user = create_user(
        role=UserRole.STORE_MANAGER,
    )

    token = login_user(
        user["email"],
        user["password"],
    )

    return {
        "token": token,
        "email": user["email"],
    }


def create_production_manager():
    user = create_user(
        role=UserRole.PRODUCTION_MANAGER,
    )

    token = login_user(
        user["email"],
        user["password"],
    )

    return {
        "token": token,
        "email": user["email"],
    }


def create_supervisor():
    user = create_user(
        role=UserRole.PRODUCTION_SUPERVISOR,
    )

    token = login_user(
        user["email"],
        user["password"],
    )

    return {
        "token": token,
        "email": user["email"],
    }


def create_worker():
    user = create_user(
        role=UserRole.WORKER,
    )

    token = login_user(
        user["email"],
        user["password"],
    )

    return {
        "token": token,
        "email": user["email"],
    }


def material_payload(**overrides):
    payload = {
        "name": "Steel Sheet",
        "material_code": f"MAT-{uuid4().hex[:8].upper()}",
        "category": "Metal",
        "unit": "kg",
        "available_quantity": 100,
        "minimum_stock_level": 20,
        "reorder_level": 10,
        "supplier_reference": "SUP-001",
        "status": "Active",
    }

    payload.update(overrides)

    return payload


def create_material(token, **overrides):
    response = client.post(
        "/api/v1/raw-materials",
        json=material_payload(**overrides),
        headers=auth_headers(token),
    )

    assert response.status_code == 201, response.text

    return response.json()


def setup_function():
    setup_database()


def test_create_raw_material():
    admin = create_admin()

    response = client.post(
        "/api/v1/raw-materials",
        json=material_payload(),
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Steel Sheet"
    assert data["category"] == "Metal"
    assert data["unit"] == "kg"
    assert data["available_quantity"] == 100
    assert data["minimum_stock_level"] == 20
    assert data["reorder_level"] == 10
    assert data["status"] == "Active"


def test_create_raw_material_without_auth():
    response = client.post(
        "/api/v1/raw-materials",
        json=material_payload(),
    )

    assert response.status_code in [401, 403]


def test_worker_cannot_create_raw_material():
    worker = create_worker()

    response = client.post(
        "/api/v1/raw-materials",
        json=material_payload(),
        headers=auth_headers(worker["token"]),
    )

    assert response.status_code == 403


def test_store_manager_can_create_raw_material():
    manager = create_store_manager()

    response = client.post(
        "/api/v1/raw-materials",
        json=material_payload(),
        headers=auth_headers(manager["token"]),
    )

    assert response.status_code == 201


def test_production_manager_can_create_raw_material():
    manager = create_production_manager()

    response = client.post(
        "/api/v1/raw-materials",
        json=material_payload(),
        headers=auth_headers(manager["token"]),
    )

    assert response.status_code == 201


def test_duplicate_material_code_rejected():
    admin = create_admin()

    code = f"MAT-{uuid4().hex[:8].upper()}"

    create_material(
        admin["token"],
        material_code=code,
    )

    response = client.post(
        "/api/v1/raw-materials",
        json=material_payload(
            material_code=code,
        ),
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 409


def test_invalid_negative_available_quantity_rejected():
    admin = create_admin()

    response = client.post(
        "/api/v1/raw-materials",
        json=material_payload(
            available_quantity=-10,
        ),
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 422


def test_invalid_negative_minimum_stock_rejected():
    admin = create_admin()

    response = client.post(
        "/api/v1/raw-materials",
        json=material_payload(
            minimum_stock_level=-1,
        ),
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 422


def test_invalid_reorder_level_rejected():
    admin = create_admin()

    response = client.post(
        "/api/v1/raw-materials",
        json=material_payload(
            minimum_stock_level=10,
            reorder_level=20,
        ),
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 400


def test_get_raw_material():
    admin = create_admin()

    material = create_material(
        admin["token"],
    )

    response = client.get(
        f"/api/v1/raw-materials/{material['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200
    assert response.json()["id"] == material["id"]


def test_get_nonexistent_raw_material():
    admin = create_admin()

    response = client.get(
        "/api/v1/raw-materials/999999",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 404


def test_list_raw_materials():
    admin = create_admin()

    create_material(
        admin["token"],
        name="Steel Sheet",
        category="Metal",
    )

    create_material(
        admin["token"],
        name="Copper Wire",
        category="Electrical",
    )

    response = client.get(
        "/api/v1/raw-materials",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["page"] == 1


def test_search_raw_materials():
    admin = create_admin()

    create_material(
        admin["token"],
        name="Premium Steel",
        category="Metal",
    )

    create_material(
        admin["token"],
        name="Copper Wire",
        category="Electrical",
    )

    response = client.get(
        "/api/v1/raw-materials",
        params={
            "search": "Premium Steel",
        },
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["name"] == "Premium Steel"


def test_filter_by_category():
    admin = create_admin()

    create_material(
        admin["token"],
        category="Metal",
    )

    create_material(
        admin["token"],
        category="Plastic",
    )

    response = client.get(
        "/api/v1/raw-materials",
        params={
            "category": "Metal",
        },
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["category"] == "Metal"


def test_filter_by_status():
    admin = create_admin()

    create_material(
        admin["token"],
        status="Active",
    )

    create_material(
        admin["token"],
        status="Inactive",
    )

    response = client.get(
        "/api/v1/raw-materials",
        params={
            "status_value": "Inactive",
        },
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["status"] == "Inactive"


def test_pagination():
    admin = create_admin()

    for index in range(5):
        create_material(
            admin["token"],
            name=f"Material {index}",
        )

    response = client.get(
        "/api/v1/raw-materials",
        params={
            "page": 1,
            "page_size": 2,
        },
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total_pages"] == 3


def test_update_raw_material():
    admin = create_admin()

    material = create_material(
        admin["token"],
    )

    response = client.put(
        f"/api/v1/raw-materials/{material['id']}",
        json={
            "name": "Updated Steel Sheet",
            "category": "Updated Metal",
            "minimum_stock_level": 30,
            "reorder_level": 15,
        },
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Updated Steel Sheet"
    assert data["category"] == "Updated Metal"
    assert data["available_quantity"] == 100
    assert data["minimum_stock_level"] == 30
    assert data["reorder_level"] == 15


def test_update_raw_material_cannot_directly_change_stock():
    admin = create_admin()

    material = create_material(
        admin["token"],
    )

    response = client.put(
        f"/api/v1/raw-materials/{material['id']}",
        json={
            "available_quantity": 9999,
        },
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["available_quantity"] == 100


def test_update_raw_material_invalid_reorder_level():
    admin = create_admin()

    material = create_material(
        admin["token"],
        minimum_stock_level=20,
        reorder_level=10,
    )

    response = client.put(
        f"/api/v1/raw-materials/{material['id']}",
        json={
            "minimum_stock_level": 10,
            "reorder_level": 20,
        },
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 400


def test_update_status():
    admin = create_admin()

    material = create_material(
        admin["token"],
    )

    response = client.patch(
        f"/api/v1/raw-materials/{material['id']}/status",
        params={
            "status_value": "Inactive",
        },
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Inactive"


def test_stock_in():
    admin = create_admin()

    material = create_material(
        admin["token"],
        available_quantity=100,
    )

    response = client.post(
        f"/api/v1/raw-materials/{material['id']}/stock-in",
        json={
            "quantity": 50,
            "reason": "Supplier delivery",
        },
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["available_quantity"] == 150


def test_stock_in_creates_history():
    admin = create_admin()

    material = create_material(
        admin["token"],
        available_quantity=100,
    )

    response = client.post(
        f"/api/v1/raw-materials/{material['id']}/stock-in",
        json={
            "quantity": 50,
            "reason": "Supplier delivery",
        },
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    history = client.get(
        f"/api/v1/raw-materials/{material['id']}/history",
        headers=auth_headers(admin["token"]),
    )

    assert history.status_code == 200

    data = history.json()

    assert data["total"] == 1
    assert data["items"][0]["transaction_type"] == "Stock In"
    assert data["items"][0]["quantity"] == 50
    assert data["items"][0]["quantity_before"] == 100
    assert data["items"][0]["quantity_after"] == 150


def test_stock_out():
    admin = create_admin()

    material = create_material(
        admin["token"],
        available_quantity=100,
    )

    response = client.post(
        f"/api/v1/raw-materials/{material['id']}/stock-out",
        json={
            "quantity": 40,
            "reason": "Production usage",
        },
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["available_quantity"] == 60


def test_stock_out_insufficient_stock_rejected():
    admin = create_admin()

    material = create_material(
        admin["token"],
        available_quantity=20,
    )

    response = client.post(
        f"/api/v1/raw-materials/{material['id']}/stock-out",
        json={
            "quantity": 50,
            "reason": "Production usage",
        },
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 400


def test_stock_out_cannot_make_inventory_negative():
    admin = create_admin()

    material = create_material(
        admin["token"],
        available_quantity=10,
    )

    response = client.post(
        f"/api/v1/raw-materials/{material['id']}/stock-out",
        json={
            "quantity": 11,
        },
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 400


def test_adjustment_positive():
    admin = create_admin()

    material = create_material(
        admin["token"],
        available_quantity=100,
    )

    response = client.post(
        f"/api/v1/raw-materials/{material['id']}/adjustment",
        json={
            "quantity": 25,
            "reason": "Physical stock correction",
        },
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200
    assert response.json()["available_quantity"] == 125


def test_adjustment_negative():
    admin = create_admin()

    material = create_material(
        admin["token"],
        available_quantity=100,
    )

    response = client.post(
        f"/api/v1/raw-materials/{material['id']}/adjustment",
        json={
            "quantity": -30,
            "reason": "Damaged material",
        },
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200
    assert response.json()["available_quantity"] == 70


def test_adjustment_cannot_make_inventory_negative():
    admin = create_admin()

    material = create_material(
        admin["token"],
        available_quantity=20,
    )

    response = client.post(
        f"/api/v1/raw-materials/{material['id']}/adjustment",
        json={
            "quantity": -50,
            "reason": "Invalid adjustment",
        },
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 400


def test_worker_cannot_adjust_inventory():
    admin = create_admin()
    worker = create_worker()

    material = create_material(
        admin["token"],
    )

    response = client.post(
        f"/api/v1/raw-materials/{material['id']}/adjustment",
        json={
            "quantity": 10,
            "reason": "Unauthorized adjustment",
        },
        headers=auth_headers(worker["token"]),
    )

    assert response.status_code == 403


def test_supervisor_can_stock_in():
    admin = create_admin()
    supervisor = create_supervisor()

    material = create_material(
        admin["token"],
        available_quantity=100,
    )

    response = client.post(
        f"/api/v1/raw-materials/{material['id']}/stock-in",
        json={
            "quantity": 20,
            "reason": "Supervisor stock receipt",
        },
        headers=auth_headers(supervisor["token"]),
    )

    assert response.status_code == 200
    assert response.json()["available_quantity"] == 120


def test_supervisor_can_stock_out():
    admin = create_admin()
    supervisor = create_supervisor()

    material = create_material(
        admin["token"],
        available_quantity=100,
    )

    response = client.post(
        f"/api/v1/raw-materials/{material['id']}/stock-out",
        json={
            "quantity": 20,
            "reason": "Production issue",
        },
        headers=auth_headers(supervisor["token"]),
    )

    assert response.status_code == 200
    assert response.json()["available_quantity"] == 80


def test_inactive_material_cannot_stock_in():
    admin = create_admin()

    material = create_material(
        admin["token"],
        status="Inactive",
    )

    response = client.post(
        f"/api/v1/raw-materials/{material['id']}/stock-in",
        json={
            "quantity": 10,
        },
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 400


def test_inactive_material_cannot_stock_out():
    admin = create_admin()

    material = create_material(
        admin["token"],
        status="Inactive",
    )

    response = client.post(
        f"/api/v1/raw-materials/{material['id']}/stock-out",
        json={
            "quantity": 10,
        },
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 400


def test_material_history_pagination():
    admin = create_admin()

    material = create_material(
        admin["token"],
        available_quantity=100,
    )

    for quantity in [10, 20, 30]:
        response = client.post(
            f"/api/v1/raw-materials/{material['id']}/stock-in",
            json={
                "quantity": quantity,
                "reason": "Stock receipt",
            },
            headers=auth_headers(admin["token"]),
        )

        assert response.status_code == 200

    response = client.get(
        f"/api/v1/raw-materials/{material['id']}/history",
        params={
            "page": 1,
            "page_size": 2,
        },
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total_pages"] == 2


def test_delete_raw_material():
    admin = create_admin()

    material = create_material(
        admin["token"],
    )

    response = client.delete(
        f"/api/v1/raw-materials/{material['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/api/v1/raw-materials/{material['id']}",
        headers=auth_headers(admin["token"]),
    )

    assert get_response.status_code == 404


def test_worker_cannot_update_material():
    admin = create_admin()
    worker = create_worker()

    material = create_material(
        admin["token"],
    )

    response = client.put(
        f"/api/v1/raw-materials/{material['id']}",
        json={
            "name": "Unauthorized Update",
        },
        headers=auth_headers(worker["token"]),
    )

    assert response.status_code == 403


def test_worker_cannot_delete_material():
    admin = create_admin()
    worker = create_worker()

    material = create_material(
        admin["token"],
    )

    response = client.delete(
        f"/api/v1/raw-materials/{material['id']}",
        headers=auth_headers(worker["token"]),
    )

    assert response.status_code == 403


def test_authenticated_worker_can_view_materials():
    admin = create_admin()
    worker = create_worker()

    material = create_material(
        admin["token"],
    )

    response = client.get(
        f"/api/v1/raw-materials/{material['id']}",
        headers=auth_headers(worker["token"]),
    )

    assert response.status_code == 200
    assert response.json()["id"] == material["id"]


def test_material_history_requires_authentication():
    admin = create_admin()

    material = create_material(
        admin["token"],
    )

    response = client.get(
        f"/api/v1/raw-materials/{material['id']}/history",
    )

    assert response.status_code in [401, 403]