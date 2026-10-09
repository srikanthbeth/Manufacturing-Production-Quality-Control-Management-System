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
from core.security import hash_password
from core.enums import UserRole, AccountStatus


client = TestClient(app)


def setup_function():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        db.execute(
            text(
                """
                TRUNCATE TABLE
                    bom_items,
                    boms,
                    material_transactions,
                    raw_materials,
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


def create_user(
    email: str,
    role: UserRole,
    password: str = "Password@123",
):
    db = SessionLocal()

    try:
        user = User(
            full_name=f"Test {role.value}",
            email=email,
            password_hash=hash_password(password),
            role=role,
            status=AccountStatus.ACTIVE,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    finally:
        db.close()


def login(
    email: str,
    password: str = "Password@123",
):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200, response.text

    return response.json()["access_token"]


def auth_header(token: str):
    return {
        "Authorization": f"Bearer {token}",
    }


def create_admin():
    email = f"admin-{uuid4().hex[:8]}@test.com"

    create_user(
        email,
        UserRole.SUPER_ADMIN,
    )

    return login(email)


def create_worker():
    email = f"worker-{uuid4().hex[:8]}@test.com"

    create_user(
        email,
        UserRole.WORKER,
    )

    return login(email)


def create_plant_manager():
    email = f"plant-manager-{uuid4().hex[:8]}@test.com"

    create_user(
        email,
        UserRole.PLANT_MANAGER,
    )

    return login(email)


def create_production_manager():
    email = f"production-manager-{uuid4().hex[:8]}@test.com"

    create_user(
        email,
        UserRole.PRODUCTION_MANAGER,
    )

    return login(email)


def product_payload(**overrides):
    payload = {
        "name": "Steel Component",
        "category": "Metal",
        "sku": f"SKU-{uuid4().hex[:8].upper()}",
        "unit_of_measurement": "Piece",
        "status": "Active",
        "standard_production_time": 60,
    }

    payload.update(overrides)

    return payload


def create_product(
    token: str,
    **overrides,
):
    response = client.post(
        "/api/v1/products",
        json=product_payload(**overrides),
        headers=auth_header(token),
    )

    assert response.status_code == 201, response.text

    return response.json()


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


def create_material(
    token: str,
    **overrides,
):
    response = client.post(
        "/api/v1/raw-materials",
        json=material_payload(**overrides),
        headers=auth_header(token),
    )

    assert response.status_code == 201, response.text

    return response.json()


def bom_payload(
    product_id: int,
    material_id: int,
    **overrides,
):
    payload = {
        "product_id": product_id,
        "version": 1,
        "description": "Standard manufacturing BOM",
        "is_active": False,
        "items": [
            {
                "material_id": material_id,
                "quantity_required": 2.5,
            }
        ],
    }

    payload.update(overrides)

    return payload


def create_bom(
    token: str,
    product_id: int,
    material_id: int,
    **overrides,
):
    response = client.post(
        "/api/v1/boms",
        json=bom_payload(
            product_id,
            material_id,
            **overrides,
        ),
        headers=auth_header(token),
    )

    assert response.status_code == 201, response.text

    return response.json()


def test_create_bom():
    token = create_admin()

    product = create_product(token)
    material = create_material(token)

    response = client.post(
        "/api/v1/boms",
        json=bom_payload(
            product["id"],
            material["id"],
        ),
        headers=auth_header(token),
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["product_id"] == product["id"]
    assert data["version"] == 1
    assert data["description"] == "Standard manufacturing BOM"
    assert data["is_active"] is False
    assert len(data["items"]) == 1
    assert data["items"][0]["material_id"] == material["id"]
    assert data["items"][0]["quantity_required"] == 2.5


def test_create_bom_without_authentication():
    product_token = create_admin()

    product = create_product(product_token)
    material = create_material(product_token)

    response = client.post(
        "/api/v1/boms",
        json=bom_payload(
            product["id"],
            material["id"],
        ),
    )

    assert response.status_code in [401, 403]


def test_worker_cannot_create_bom():
    admin_token = create_admin()

    product = create_product(admin_token)
    material = create_material(admin_token)

    worker_token = create_worker()

    response = client.post(
        "/api/v1/boms",
        json=bom_payload(
            product["id"],
            material["id"],
        ),
        headers=auth_header(worker_token),
    )

    assert response.status_code == 403


def test_plant_manager_can_create_bom():
    admin_token = create_admin()

    product = create_product(admin_token)
    material = create_material(admin_token)

    manager_token = create_plant_manager()

    response = client.post(
        "/api/v1/boms",
        json=bom_payload(
            product["id"],
            material["id"],
        ),
        headers=auth_header(manager_token),
    )

    assert response.status_code == 201, response.text


def test_production_manager_can_create_bom():
    admin_token = create_admin()

    product = create_product(admin_token)
    material = create_material(admin_token)

    manager_token = create_production_manager()

    response = client.post(
        "/api/v1/boms",
        json=bom_payload(
            product["id"],
            material["id"],
        ),
        headers=auth_header(manager_token),
    )

    assert response.status_code == 201, response.text


def test_create_bom_with_multiple_materials():
    token = create_admin()

    product = create_product(token)

    material_1 = create_material(
        token,
        name="Steel Sheet",
    )

    material_2 = create_material(
        token,
        name="Copper Wire",
        category="Electrical",
        unit="meter",
    )

    response = client.post(
        "/api/v1/boms",
        json={
            "product_id": product["id"],
            "version": 1,
            "description": "Multi-material BOM",
            "is_active": False,
            "items": [
                {
                    "material_id": material_1["id"],
                    "quantity_required": 2.5,
                },
                {
                    "material_id": material_2["id"],
                    "quantity_required": 4.0,
                },
            ],
        },
        headers=auth_header(token),
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert len(data["items"]) == 2

    material_ids = {
        item["material_id"]
        for item in data["items"]
    }

    assert material_1["id"] in material_ids
    assert material_2["id"] in material_ids


def test_duplicate_material_in_same_bom_rejected():
    token = create_admin()

    product = create_product(token)
    material = create_material(token)

    response = client.post(
        "/api/v1/boms",
        json={
            "product_id": product["id"],
            "version": 1,
            "description": "Duplicate material test",
            "is_active": False,
            "items": [
                {
                    "material_id": material["id"],
                    "quantity_required": 2.0,
                },
                {
                    "material_id": material["id"],
                    "quantity_required": 3.0,
                },
            ],
        },
        headers=auth_header(token),
    )

    assert response.status_code == 400


def test_zero_material_quantity_rejected():
    token = create_admin()

    product = create_product(token)
    material = create_material(token)

    response = client.post(
        "/api/v1/boms",
        json=bom_payload(
            product["id"],
            material["id"],
            items=[
                {
                    "material_id": material["id"],
                    "quantity_required": 0,
                }
            ],
        ),
        headers=auth_header(token),
    )

    assert response.status_code == 422


def test_negative_material_quantity_rejected():
    token = create_admin()

    product = create_product(token)
    material = create_material(token)

    response = client.post(
        "/api/v1/boms",
        json=bom_payload(
            product["id"],
            material["id"],
            items=[
                {
                    "material_id": material["id"],
                    "quantity_required": -2,
                }
            ],
        ),
        headers=auth_header(token),
    )

    assert response.status_code == 422


def test_nonexistent_product_rejected():
    token = create_admin()

    material = create_material(token)

    response = client.post(
        "/api/v1/boms",
        json=bom_payload(
            999999,
            material["id"],
        ),
        headers=auth_header(token),
    )

    assert response.status_code == 404


def test_nonexistent_material_rejected():
    token = create_admin()

    product = create_product(token)

    response = client.post(
        "/api/v1/boms",
        json=bom_payload(
            product["id"],
            999999,
        ),
        headers=auth_header(token),
    )

    assert response.status_code == 404


def test_duplicate_bom_version_rejected():
    token = create_admin()

    product = create_product(token)
    material_1 = create_material(token)
    material_2 = create_material(
        token,
        name="Copper Wire",
        category="Electrical",
    )

    create_bom(
        token,
        product["id"],
        material_1["id"],
        version=1,
    )

    response = client.post(
        "/api/v1/boms",
        json=bom_payload(
            product["id"],
            material_2["id"],
            version=1,
        ),
        headers=auth_header(token),
    )

    assert response.status_code == 409


def test_get_bom():
    token = create_admin()

    product = create_product(token)
    material = create_material(token)

    bom = create_bom(
        token,
        product["id"],
        material["id"],
    )

    response = client.get(
        f"/api/v1/boms/{bom['id']}",
        headers=auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == bom["id"]
    assert data["product_id"] == product["id"]
    assert len(data["items"]) == 1


def test_get_nonexistent_bom():
    token = create_admin()

    response = client.get(
        "/api/v1/boms/999999",
        headers=auth_header(token),
    )

    assert response.status_code == 404


def test_list_boms():
    token = create_admin()

    product_1 = create_product(
        token,
        sku="SKU-001",
    )

    product_2 = create_product(
        token,
        name="Plastic Component",
        category="Plastic",
        sku="SKU-002",
    )

    material_1 = create_material(token)
    material_2 = create_material(
        token,
        name="Plastic Material",
        category="Plastic",
    )

    create_bom(
        token,
        product_1["id"],
        material_1["id"],
        version=1,
    )

    create_bom(
        token,
        product_2["id"],
        material_2["id"],
        version=1,
    )

    response = client.get(
        "/api/v1/boms",
        headers=auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2


def test_list_boms_by_product():
    token = create_admin()

    product_1 = create_product(
        token,
        sku="SKU-001",
    )

    product_2 = create_product(
        token,
        name="Second Product",
        sku="SKU-002",
    )

    material_1 = create_material(token)
    material_2 = create_material(
        token,
        name="Copper",
        category="Electrical",
    )

    create_bom(
        token,
        product_1["id"],
        material_1["id"],
        version=1,
    )

    create_bom(
        token,
        product_1["id"],
        material_2["id"],
        version=2,
    )

    create_bom(
        token,
        product_2["id"],
        material_1["id"],
        version=1,
    )

    response = client.get(
        f"/api/v1/boms/product/{product_1['id']}",
        headers=auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2

    versions = {
        item["version"]
        for item in data
    }

    assert versions == {1, 2}


def test_filter_boms_by_active_status():
    token = create_admin()

    product = create_product(token)

    material_1 = create_material(token)
    material_2 = create_material(
        token,
        name="Copper",
        category="Electrical",
    )

    create_bom(
        token,
        product["id"],
        material_1["id"],
        version=1,
        is_active=False,
    )

    create_bom(
        token,
        product["id"],
        material_2["id"],
        version=2,
        is_active=True,
    )

    response = client.get(
        "/api/v1/boms",
        params={
            "is_active": True,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["is_active"] is True
    assert data[0]["version"] == 2


def test_update_bom():
    token = create_admin()

    product = create_product(token)
    material = create_material(token)

    bom = create_bom(
        token,
        product["id"],
        material["id"],
        version=1,
    )

    response = client.put(
        f"/api/v1/boms/{bom['id']}",
        json={
            "version": 2,
            "description": "Updated BOM version",
        },
        headers=auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["version"] == 2
    assert data["description"] == "Updated BOM version"


def test_add_material_to_bom():
    token = create_admin()

    product = create_product(token)

    material_1 = create_material(token)
    material_2 = create_material(
        token,
        name="Copper Wire",
        category="Electrical",
    )

    bom = create_bom(
        token,
        product["id"],
        material_1["id"],
    )

    response = client.post(
        f"/api/v1/boms/{bom['id']}/items",
        json={
            "material_id": material_2["id"],
            "quantity_required": 3.5,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["bom_id"] == bom["id"]
    assert data["material_id"] == material_2["id"]
    assert data["quantity_required"] == 3.5


def test_duplicate_material_addition_rejected():
    token = create_admin()

    product = create_product(token)
    material = create_material(token)

    bom = create_bom(
        token,
        product["id"],
        material["id"],
    )

    response = client.post(
        f"/api/v1/boms/{bom['id']}/items",
        json={
            "material_id": material["id"],
            "quantity_required": 5,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 409


def test_update_bom_item_quantity():
    token = create_admin()

    product = create_product(token)
    material = create_material(token)

    bom = create_bom(
        token,
        product["id"],
        material["id"],
    )

    item_id = bom["items"][0]["id"]

    response = client.put(
        f"/api/v1/boms/{bom['id']}/items/{item_id}",
        json={
            "quantity_required": 8.5,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["quantity_required"] == 8.5


def test_remove_bom_item():
    token = create_admin()

    product = create_product(token)

    material_1 = create_material(token)
    material_2 = create_material(
        token,
        name="Copper",
        category="Electrical",
    )

    bom = create_bom(
        token,
        product["id"],
        material_1["id"],
        items=[
            {
                "material_id": material_1["id"],
                "quantity_required": 2,
            },
            {
                "material_id": material_2["id"],
                "quantity_required": 3,
            },
        ],
    )

    item_id = bom["items"][0]["id"]

    response = client.delete(
        f"/api/v1/boms/{bom['id']}/items/{item_id}",
        headers=auth_header(token),
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/api/v1/boms/{bom['id']}",
        headers=auth_header(token),
    )

    assert get_response.status_code == 200

    data = get_response.json()

    assert len(data["items"]) == 1
    assert data["items"][0]["material_id"] == material_2["id"]


def test_activate_bom():
    token = create_admin()

    product = create_product(token)
    material = create_material(token)

    bom = create_bom(
        token,
        product["id"],
        material["id"],
        is_active=False,
    )

    response = client.post(
        f"/api/v1/boms/{bom['id']}/activate",
        headers=auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["is_active"] is True


def test_only_one_active_bom_per_product():
    token = create_admin()

    product = create_product(token)

    material_1 = create_material(token)
    material_2 = create_material(
        token,
        name="Copper",
        category="Electrical",
    )

    bom_1 = create_bom(
        token,
        product["id"],
        material_1["id"],
        version=1,
        is_active=True,
    )

    bom_2 = create_bom(
        token,
        product["id"],
        material_2["id"],
        version=2,
        is_active=False,
    )

    response = client.post(
        f"/api/v1/boms/{bom_2['id']}/activate",
        headers=auth_header(token),
    )

    assert response.status_code == 200

    assert response.json()["is_active"] is True

    old_bom = client.get(
        f"/api/v1/boms/{bom_1['id']}",
        headers=auth_header(token),
    )

    assert old_bom.status_code == 200
    assert old_bom.json()["is_active"] is False


def test_create_active_bom_deactivates_previous_active_bom():
    token = create_admin()

    product = create_product(token)

    material_1 = create_material(token)
    material_2 = create_material(
        token,
        name="Aluminium",
        category="Metal",
    )

    bom_1 = create_bom(
        token,
        product["id"],
        material_1["id"],
        version=1,
        is_active=True,
    )

    bom_2 = create_bom(
        token,
        product["id"],
        material_2["id"],
        version=2,
        is_active=True,
    )

    old_bom = client.get(
        f"/api/v1/boms/{bom_1['id']}",
        headers=auth_header(token),
    )

    assert old_bom.status_code == 200
    assert old_bom.json()["is_active"] is False

    new_bom = client.get(
        f"/api/v1/boms/{bom_2['id']}",
        headers=auth_header(token),
    )

    assert new_bom.status_code == 200
    assert new_bom.json()["is_active"] is True


def test_deactivate_bom():
    token = create_admin()

    product = create_product(token)
    material = create_material(token)

    bom = create_bom(
        token,
        product["id"],
        material["id"],
        is_active=True,
    )

    response = client.post(
        f"/api/v1/boms/{bom['id']}/deactivate",
        headers=auth_header(token),
    )

    assert response.status_code == 200

    assert response.json()["is_active"] is False


def test_active_bom_cannot_be_modified():
    token = create_admin()

    product = create_product(token)
    material_1 = create_material(token)
    material_2 = create_material(
        token,
        name="Copper",
        category="Electrical",
    )

    bom = create_bom(
        token,
        product["id"],
        material_1["id"],
        is_active=True,
    )

    response = client.post(
        f"/api/v1/boms/{bom['id']}/items",
        json={
            "material_id": material_2["id"],
            "quantity_required": 2,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 400


def test_worker_cannot_update_bom():
    admin_token = create_admin()

    product = create_product(admin_token)
    material = create_material(admin_token)

    bom = create_bom(
        admin_token,
        product["id"],
        material["id"],
    )

    worker_token = create_worker()

    response = client.put(
        f"/api/v1/boms/{bom['id']}",
        json={
            "description": "Unauthorized update",
        },
        headers=auth_header(worker_token),
    )

    assert response.status_code == 403


def test_worker_cannot_delete_bom():
    admin_token = create_admin()

    product = create_product(admin_token)
    material = create_material(admin_token)

    bom = create_bom(
        admin_token,
        product["id"],
        material["id"],
    )

    worker_token = create_worker()

    response = client.delete(
        f"/api/v1/boms/{bom['id']}",
        headers=auth_header(worker_token),
    )

    assert response.status_code == 403


def test_active_bom_cannot_be_deleted():
    token = create_admin()

    product = create_product(token)
    material = create_material(token)

    bom = create_bom(
        token,
        product["id"],
        material["id"],
        is_active=True,
    )

    response = client.delete(
        f"/api/v1/boms/{bom['id']}",
        headers=auth_header(token),
    )

    assert response.status_code == 400


def test_delete_inactive_bom():
    token = create_admin()

    product = create_product(token)
    material = create_material(token)

    bom = create_bom(
        token,
        product["id"],
        material["id"],
        is_active=False,
    )

    response = client.delete(
        f"/api/v1/boms/{bom['id']}",
        headers=auth_header(token),
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/api/v1/boms/{bom['id']}",
        headers=auth_header(token),
    )

    assert get_response.status_code == 404


def test_authenticated_worker_can_view_bom():
    admin_token = create_admin()

    product = create_product(admin_token)
    material = create_material(admin_token)

    bom = create_bom(
        admin_token,
        product["id"],
        material["id"],
    )

    worker_token = create_worker()

    response = client.get(
        f"/api/v1/boms/{bom['id']}",
        headers=auth_header(worker_token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == bom["id"]


def test_bom_list_requires_authentication():
    response = client.get(
        "/api/v1/boms",
    )

    assert response.status_code in [401, 403]


def test_bom_update_duplicate_version_rejected():
    token = create_admin()

    product = create_product(token)

    material_1 = create_material(token)
    material_2 = create_material(
        token,
        name="Copper",
        category="Electrical",
    )

    bom_1 = create_bom(
        token,
        product["id"],
        material_1["id"],
        version=1,
    )

    bom_2 = create_bom(
        token,
        product["id"],
        material_2["id"],
        version=2,
    )

    response = client.put(
        f"/api/v1/boms/{bom_2['id']}",
        json={
            "version": 1,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 409

    get_response = client.get(
        f"/api/v1/boms/{bom_1['id']}",
        headers=auth_header(token),
    )

    assert get_response.status_code == 200