import os

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

    db.execute(
        text(
            """
            TRUNCATE TABLE
                products,
                auth_tokens,
                users
            RESTART IDENTITY CASCADE
            """
        )
    )

    db.commit()
    db.close()


def create_user(
    email: str,
    role: UserRole,
    password: str = "Password@123",
):
    db = SessionLocal()

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

    db.close()

    return user


def login(email: str, password: str = "Password@123"):
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
        "Authorization": f"Bearer {token}"
    }


def create_admin():
    create_user(
        "admin@test.com",
        UserRole.SUPER_ADMIN,
    )

    return login("admin@test.com")


def create_product(
    token: str,
    name: str = "Steel Component",
    category: str = "Metal",
    sku: str = "SKU-001",
):
    response = client.post(
        "/api/v1/products",
        json={
            "name": name,
            "category": category,
            "sku": sku,
            "unit_of_measurement": "Piece",
            "status": "Active",
            "standard_production_time": 60,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 201

    return response.json()


def test_create_product():
    token = create_admin()

    response = client.post(
        "/api/v1/products",
        json={
            "name": "Steel Component",
            "category": "Metal",
            "sku": "SKU-001",
            "unit_of_measurement": "Piece",
            "status": "Active",
            "standard_production_time": 60,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Steel Component"
    assert data["category"] == "Metal"
    assert data["sku"] == "SKU-001"
    assert data["unit_of_measurement"] == "Piece"
    assert data["status"] == "Active"
    assert data["standard_production_time"] == 60


def test_create_product_without_authentication():
    response = client.post(
        "/api/v1/products",
        json={
            "name": "Steel Component",
            "category": "Metal",
            "sku": "SKU-001",
            "unit_of_measurement": "Piece",
            "status": "Active",
            "standard_production_time": 60,
        },
    )

    assert response.status_code == 401


def test_worker_cannot_create_product():
    create_user(
        "worker@test.com",
        UserRole.WORKER,
    )

    token = login("worker@test.com")

    response = client.post(
        "/api/v1/products",
        json={
            "name": "Steel Component",
            "category": "Metal",
            "sku": "SKU-001",
            "unit_of_measurement": "Piece",
            "status": "Active",
            "standard_production_time": 60,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 403


def test_plant_manager_can_create_product():
    create_user(
        "manager@test.com",
        UserRole.PLANT_MANAGER,
    )

    token = login("manager@test.com")

    response = client.post(
        "/api/v1/products",
        json={
            "name": "Steel Component",
            "category": "Metal",
            "sku": "SKU-001",
            "unit_of_measurement": "Piece",
            "status": "Active",
            "standard_production_time": 60,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 201


def test_production_manager_can_create_product():
    create_user(
        "manager@test.com",
        UserRole.PRODUCTION_MANAGER,
    )

    token = login("manager@test.com")

    response = client.post(
        "/api/v1/products",
        json={
            "name": "Steel Component",
            "category": "Metal",
            "sku": "SKU-001",
            "unit_of_measurement": "Piece",
            "status": "Active",
            "standard_production_time": 60,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 201


def test_duplicate_product_sku():
    token = create_admin()

    create_product(token)

    response = client.post(
        "/api/v1/products",
        json={
            "name": "Another Component",
            "category": "Metal",
            "sku": "SKU-001",
            "unit_of_measurement": "Piece",
            "status": "Active",
            "standard_production_time": 90,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 409


def test_get_product_details():
    token = create_admin()

    product = create_product(token)

    response = client.get(
        f"/api/v1/products/{product['id']}",
        headers=auth_header(token),
    )

    assert response.status_code == 200
    assert response.json()["sku"] == "SKU-001"


def test_get_nonexistent_product():
    token = create_admin()

    response = client.get(
        "/api/v1/products/99999",
        headers=auth_header(token),
    )

    assert response.status_code == 404


def test_list_products():
    token = create_admin()

    create_product(
        token,
        sku="SKU-001",
    )

    create_product(
        token,
        name="Plastic Component",
        category="Plastic",
        sku="SKU-002",
    )

    response = client.get(
        "/api/v1/products",
        headers=auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_update_product():
    token = create_admin()

    product = create_product(token)

    response = client.put(
        f"/api/v1/products/{product['id']}",
        json={
            "name": "Updated Steel Component",
            "category": "Updated Metal",
            "sku": "SKU-001",
            "unit_of_measurement": "Kg",
            "status": "Active",
            "standard_production_time": 120,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Updated Steel Component"
    assert data["category"] == "Updated Metal"
    assert data["unit_of_measurement"] == "Kg"
    assert data["standard_production_time"] == 120


def test_update_product_sku():
    token = create_admin()

    product = create_product(token)

    response = client.put(
        f"/api/v1/products/{product['id']}",
        json={
            "sku": "SKU-UPDATED",
        },
        headers=auth_header(token),
    )

    assert response.status_code == 200
    assert response.json()["sku"] == "SKU-UPDATED"


def test_duplicate_sku_on_update_rejected():
    token = create_admin()

    create_product(
        token,
        sku="SKU-001",
    )

    product = create_product(
        token,
        name="Second Product",
        sku="SKU-002",
    )

    response = client.put(
        f"/api/v1/products/{product['id']}",
        json={
            "sku": "SKU-001",
        },
        headers=auth_header(token),
    )

    assert response.status_code == 409


def test_worker_cannot_update_product():
    admin_token = create_admin()

    product = create_product(admin_token)

    create_user(
        "worker@test.com",
        UserRole.WORKER,
    )

    worker_token = login("worker@test.com")

    response = client.put(
        f"/api/v1/products/{product['id']}",
        json={
            "name": "Unauthorized Update",
        },
        headers=auth_header(worker_token),
    )

    assert response.status_code == 403


def test_update_product_status():
    token = create_admin()

    product = create_product(token)

    response = client.patch(
        f"/api/v1/products/{product['id']}/status",
        params={
            "status_value": "Inactive",
        },
        headers=auth_header(token),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Inactive"


def test_discontinue_product():
    token = create_admin()

    product = create_product(token)

    response = client.patch(
        f"/api/v1/products/{product['id']}/status",
        params={
            "status_value": "Discontinued",
        },
        headers=auth_header(token),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Discontinued"


def test_search_products_by_name():
    token = create_admin()

    create_product(
        token,
        name="Premium Steel",
        sku="STEEL-001",
    )

    create_product(
        token,
        name="Plastic Cover",
        category="Plastic",
        sku="PLASTIC-001",
    )

    response = client.get(
        "/api/v1/products",
        params={
            "search": "Steel",
        },
        headers=auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["name"] == "Premium Steel"


def test_search_products_by_sku():
    token = create_admin()

    create_product(
        token,
        sku="STEEL-001",
    )

    create_product(
        token,
        name="Plastic Product",
        sku="PLASTIC-001",
    )

    response = client.get(
        "/api/v1/products",
        params={
            "search": "STEEL-001",
        },
        headers=auth_header(token),
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_search_products_by_category():
    token = create_admin()

    create_product(
        token,
        category="Metal",
        sku="METAL-001",
    )

    create_product(
        token,
        name="Plastic Product",
        category="Plastic",
        sku="PLASTIC-001",
    )

    response = client.get(
        "/api/v1/products",
        params={
            "search": "Metal",
        },
        headers=auth_header(token),
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_filter_by_category():
    token = create_admin()

    create_product(
        token,
        category="Metal",
        sku="METAL-001",
    )

    create_product(
        token,
        name="Plastic Product",
        category="Plastic",
        sku="PLASTIC-001",
    )

    response = client.get(
        "/api/v1/products",
        params={
            "category": "Metal",
        },
        headers=auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["category"] == "Metal"


def test_filter_by_status():
    token = create_admin()

    product = create_product(
        token,
        sku="SKU-001",
    )

    client.patch(
        f"/api/v1/products/{product['id']}/status",
        params={
            "status_value": "Inactive",
        },
        headers=auth_header(token),
    )

    create_product(
        token,
        name="Active Product",
        sku="SKU-002",
    )

    response = client.get(
        "/api/v1/products",
        params={
            "status_value": "Inactive",
        },
        headers=auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["status"] == "Inactive"


def test_filter_by_category_and_status():
    token = create_admin()

    product = create_product(
        token,
        category="Metal",
        sku="METAL-001",
    )

    client.patch(
        f"/api/v1/products/{product['id']}/status",
        params={
            "status_value": "Inactive",
        },
        headers=auth_header(token),
    )

    create_product(
        token,
        name="Active Metal",
        category="Metal",
        sku="METAL-002",
    )

    response = client.get(
        "/api/v1/products",
        params={
            "category": "Metal",
            "status_value": "Inactive",
        },
        headers=auth_header(token),
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_pagination():
    token = create_admin()

    for index in range(1, 6):
        create_product(
            token,
            name=f"Product {index}",
            sku=f"SKU-{index:03d}",
        )

    response = client.get(
        "/api/v1/products",
        params={
            "page": 1,
            "page_size": 2,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total_pages"] == 3


def test_pagination_second_page():
    token = create_admin()

    for index in range(1, 6):
        create_product(
            token,
            name=f"Product {index}",
            sku=f"SKU-{index:03d}",
        )

    response = client.get(
        "/api/v1/products",
        params={
            "page": 2,
            "page_size": 2,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["page"] == 2
    assert len(data["items"]) == 2


def test_delete_product():
    token = create_admin()

    product = create_product(token)

    response = client.delete(
        f"/api/v1/products/{product['id']}",
        headers=auth_header(token),
    )

    assert response.status_code == 204

    response = client.get(
        f"/api/v1/products/{product['id']}",
        headers=auth_header(token),
    )

    assert response.status_code == 404


def test_worker_cannot_delete_product():
    admin_token = create_admin()

    product = create_product(admin_token)

    create_user(
        "worker@test.com",
        UserRole.WORKER,
    )

    worker_token = login("worker@test.com")

    response = client.delete(
        f"/api/v1/products/{product['id']}",
        headers=auth_header(worker_token),
    )

    assert response.status_code == 403


def test_negative_production_time_rejected():
    token = create_admin()

    response = client.post(
        "/api/v1/products",
        json={
            "name": "Invalid Product",
            "category": "Metal",
            "sku": "INVALID-001",
            "unit_of_measurement": "Piece",
            "status": "Active",
            "standard_production_time": -10,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 422


def test_zero_production_time_rejected():
    token = create_admin()

    response = client.post(
        "/api/v1/products",
        json={
            "name": "Invalid Product",
            "category": "Metal",
            "sku": "INVALID-002",
            "unit_of_measurement": "Piece",
            "status": "Active",
            "standard_production_time": 0,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 422


def test_invalid_product_status_rejected():
    token = create_admin()

    response = client.post(
        "/api/v1/products",
        json={
            "name": "Invalid Product",
            "category": "Metal",
            "sku": "INVALID-003",
            "unit_of_measurement": "Piece",
            "status": "WrongStatus",
            "standard_production_time": 60,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 422