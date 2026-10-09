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


client = TestClient(app)


def unique_email(prefix="user"):
    return f"{prefix}_{uuid4().hex[:8]}@test.com"


def cleanup_database():
    with engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE TABLE plants, auth_tokens, users "
                "RESTART IDENTITY CASCADE"
            )
        )


def create_super_admin():
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Test Admin",
            "email": unique_email("admin"),
            "password": "Admin@12345",
        },
    )

    assert response.status_code == 201

    user = response.json()

    with SessionLocal() as db:
        db.execute(
            text(
                "UPDATE users "
                "SET role = 'SUPER_ADMIN' "
                "WHERE id = :user_id"
            ),
            {"user_id": user["id"]},
        )
        db.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": user["email"],
            "password": "Admin@12345",
        },
    )

    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def create_worker():
    email = unique_email("worker")

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Test Worker",
            "email": email,
            "password": "Worker@12345",
        },
    )

    assert response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "Worker@12345",
        },
    )

    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def create_plant_manager():
    email = unique_email("manager")

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Test Plant Manager",
            "email": email,
            "password": "Manager@12345",
        },
    )

    assert response.status_code == 201

    user_id = response.json()["id"]

    with SessionLocal() as db:
        db.execute(
            text(
                "UPDATE users "
                "SET role = 'PLANT_MANAGER' "
                "WHERE id = :user_id"
            ),
            {"user_id": user_id},
        )
        db.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "Manager@12345",
        },
    )

    assert login_response.status_code == 200

    return {
        "id": user_id,
        "token": login_response.json()["access_token"],
    }


def create_plant(token, manager_id=None):
    payload = {
        "name": f"Manufacturing Plant {uuid4().hex[:6]}",
        "code": f"PLANT-{uuid4().hex[:6].upper()}",
        "address": "Industrial Area",
        "city": "Tirupati",
        "state": "Andhra Pradesh",
        "country": "India",
        "production_capacity": 10000,
        "status": "Active",
    }

    if manager_id is not None:
        payload["manager_id"] = manager_id

    response = client.post(
        "/api/v1/plants",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 201

    return response.json()


def setup_function():
    Base.metadata.create_all(bind=engine)
    cleanup_database()


def teardown_function():
    cleanup_database()


def test_create_plant():
    token = create_super_admin()

    response = client.post(
        "/api/v1/plants",
        json={
            "name": "Main Manufacturing Plant",
            "code": "PLANT-001",
            "address": "Industrial Area",
            "city": "Tirupati",
            "state": "Andhra Pradesh",
            "country": "India",
            "production_capacity": 10000,
            "status": "Active",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Main Manufacturing Plant"
    assert data["code"] == "PLANT-001"
    assert data["production_capacity"] == 10000
    assert data["status"] == "Active"


def test_create_plant_without_authentication():
    response = client.post(
        "/api/v1/plants",
        json={
            "name": "Unauthorized Plant",
            "code": "PLANT-002",
            "address": "Industrial Area",
            "city": "Tirupati",
            "state": "Andhra Pradesh",
            "country": "India",
            "production_capacity": 5000,
            "status": "Active",
        },
    )

    assert response.status_code == 401


def test_worker_cannot_create_plant():
    token = create_worker()

    response = client.post(
        "/api/v1/plants",
        json={
            "name": "Worker Plant",
            "code": "PLANT-003",
            "address": "Industrial Area",
            "city": "Tirupati",
            "state": "Andhra Pradesh",
            "country": "India",
            "production_capacity": 5000,
            "status": "Active",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 403


def test_duplicate_plant_code():
    token = create_super_admin()

    create_plant(
        token=token,
    )

    response = client.post(
        "/api/v1/plants",
        json={
            "name": "Second Plant",
            "code": "PLANT-DUPLICATE",
            "address": "Industrial Area",
            "city": "Tirupati",
            "state": "Andhra Pradesh",
            "country": "India",
            "production_capacity": 5000,
            "status": "Active",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 201

    response = client.post(
        "/api/v1/plants",
        json={
            "name": "Third Plant",
            "code": "PLANT-DUPLICATE",
            "address": "Another Area",
            "city": "Tirupati",
            "state": "Andhra Pradesh",
            "country": "India",
            "production_capacity": 6000,
            "status": "Active",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 409


def test_get_plant_details():
    token = create_super_admin()

    plant = create_plant(token)

    response = client.get(
        f"/api/v1/plants/{plant['id']}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == plant["id"]
    assert data["name"] == plant["name"]
    assert data["code"] == plant["code"]
    assert data["address"] == "Industrial Area"
    assert data["city"] == "Tirupati"
    assert data["production_capacity"] == 10000


def test_get_nonexistent_plant():
    token = create_super_admin()

    response = client.get(
        "/api/v1/plants/999999",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 404


def test_list_plants():
    token = create_super_admin()

    create_plant(token)
    create_plant(token)
    create_plant(token)

    response = client.get(
        "/api/v1/plants",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 3


def test_update_plant():
    token = create_super_admin()

    plant = create_plant(token)

    response = client.put(
        f"/api/v1/plants/{plant['id']}",
        json={
            "name": "Updated Manufacturing Plant",
            "address": "Updated Industrial Area",
            "city": "Chittoor",
            "state": "Andhra Pradesh",
            "country": "India",
            "production_capacity": 20000,
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Updated Manufacturing Plant"
    assert data["address"] == "Updated Industrial Area"
    assert data["city"] == "Chittoor"
    assert data["production_capacity"] == 20000


def test_plant_manager_can_update_plant():
    admin_token = create_super_admin()

    manager = create_plant_manager()

    plant = create_plant(
        token=admin_token,
        manager_id=manager["id"],
    )

    response = client.put(
        f"/api/v1/plants/{plant['id']}",
        json={
            "name": "Manager Updated Plant",
            "production_capacity": 15000,
        },
        headers={
            "Authorization": f"Bearer {manager['token']}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Manager Updated Plant"
    assert data["production_capacity"] == 15000


def test_worker_cannot_update_plant():
    admin_token = create_super_admin()

    plant = create_plant(admin_token)

    worker_token = create_worker()

    response = client.put(
        f"/api/v1/plants/{plant['id']}",
        json={
            "name": "Unauthorized Update",
        },
        headers={
            "Authorization": f"Bearer {worker_token}"
        },
    )

    assert response.status_code == 403


def test_update_plant_status():
    token = create_super_admin()

    plant = create_plant(token)

    statuses = [
        "Maintenance",
        "Temporarily Closed",
        "Inactive",
        "Active",
    ]

    for plant_status in statuses:
        response = client.patch(
            f"/api/v1/plants/{plant['id']}/status",
            params={
                "status_value": plant_status
            },
            headers={
                "Authorization": f"Bearer {token}"
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == plant_status


def test_deactivate_plant():
    token = create_super_admin()

    plant = create_plant(token)

    response = client.patch(
        f"/api/v1/plants/{plant['id']}/deactivate",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    assert response.json()["status"] == "Inactive"


def test_create_plant_with_manager():
    admin_token = create_super_admin()

    manager = create_plant_manager()

    plant = create_plant(
        token=admin_token,
        manager_id=manager["id"],
    )

    assert plant["manager_id"] == manager["id"]


def test_assign_plant_manager():
    admin_token = create_super_admin()

    manager = create_plant_manager()

    plant = create_plant(admin_token)

    response = client.patch(
        f"/api/v1/plants/{plant['id']}/manager/{manager['id']}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["manager_id"] == manager["id"]


def test_remove_plant_manager():
    admin_token = create_super_admin()

    manager = create_plant_manager()

    plant = create_plant(
        token=admin_token,
        manager_id=manager["id"],
    )

    assert plant["manager_id"] == manager["id"]

    response = client.delete(
        f"/api/v1/plants/{plant['id']}/manager",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["manager_id"] is None


def test_invalid_manager_role_cannot_be_assigned():
    admin_token = create_super_admin()

    worker_token = create_worker()

    worker_me = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {worker_token}"
        },
    )

    assert worker_me.status_code == 200

    worker_id = worker_me.json()["id"]

    plant = create_plant(admin_token)

    response = client.patch(
        f"/api/v1/plants/{plant['id']}/manager/{worker_id}",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
    )

    assert response.status_code == 400


def test_negative_production_capacity_is_rejected():
    token = create_super_admin()

    response = client.post(
        "/api/v1/plants",
        json={
            "name": "Invalid Capacity Plant",
            "code": "PLANT-INVALID",
            "address": "Industrial Area",
            "city": "Tirupati",
            "state": "Andhra Pradesh",
            "country": "India",
            "production_capacity": -100,
            "status": "Active",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 422


def test_invalid_plant_status_is_rejected():
    token = create_super_admin()

    response = client.post(
        "/api/v1/plants",
        json={
            "name": "Invalid Status Plant",
            "code": "PLANT-STATUS",
            "address": "Industrial Area",
            "city": "Tirupati",
            "state": "Andhra Pradesh",
            "country": "India",
            "production_capacity": 5000,
            "status": "Running",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 422