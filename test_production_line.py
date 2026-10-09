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
                "TRUNCATE TABLE production_lines, plants, "
                "auth_tokens, users "
                "RESTART IDENTITY CASCADE"
            )
        )


def create_user(
    role: str,
    prefix: str,
    password: str = "Password@12345",
):
    email = unique_email(prefix)

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": f"Test {prefix}",
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 201

    user_id = response.json()["id"]

    with SessionLocal() as db:
        db.execute(
            text(
                "UPDATE users "
                "SET role = :role "
                "WHERE id = :user_id"
            ),
            {
                "role": role,
                "user_id": user_id,
            },
        )
        db.commit()

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200

    return {
        "id": user_id,
        "email": email,
        "token": login_response.json()["access_token"],
    }


def create_super_admin():
    return create_user(
        role="SUPER_ADMIN",
        prefix="admin",
        password="Admin@12345",
    )


def create_plant_manager():
    return create_user(
        role="PLANT_MANAGER",
        prefix="plantmanager",
        password="Manager@12345",
    )


def create_production_manager():
    return create_user(
        role="PRODUCTION_MANAGER",
        prefix="productionmanager",
        password="Production@12345",
    )


def create_supervisor():
    return create_user(
        role="PRODUCTION_SUPERVISOR",
        prefix="supervisor",
        password="Supervisor@12345",
    )


def create_worker():
    return create_user(
        role="WORKER",
        prefix="worker",
        password="Worker@12345",
    )


def create_plant(token, code=None):
    if code is None:
        code = f"PLANT-{uuid4().hex[:6].upper()}"

    response = client.post(
        "/api/v1/plants",
        json={
            "name": f"Manufacturing Plant {uuid4().hex[:6]}",
            "code": code,
            "address": "Industrial Area",
            "city": "Tirupati",
            "state": "Andhra Pradesh",
            "country": "India",
            "production_capacity": 50000,
            "status": "Active",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 201

    return response.json()


def create_production_line(
    token,
    plant_id,
    supervisor_id=None,
    name=None,
    code=None,
    capacity=5000,
    line_status="Active",
):
    if name is None:
        name = f"Production Line {uuid4().hex[:6]}"

    if code is None:
        code = f"LINE-{uuid4().hex[:6].upper()}"

    payload = {
        "name": name,
        "code": code,
        "production_capacity": capacity,
        "plant_id": plant_id,
        "status": line_status,
    }

    if supervisor_id is not None:
        payload["supervisor_id"] = supervisor_id

    response = client.post(
        "/api/v1/production-lines",
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


def test_create_production_line():
    admin = create_super_admin()

    plant = create_plant(admin["token"])

    response = client.post(
        "/api/v1/production-lines",
        json={
            "name": "Assembly Line 1",
            "code": "LINE-001",
            "production_capacity": 5000,
            "plant_id": plant["id"],
            "status": "Active",
        },
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Assembly Line 1"
    assert data["code"] == "LINE-001"
    assert data["production_capacity"] == 5000
    assert data["plant_id"] == plant["id"]
    assert data["status"] == "Active"


def test_create_production_line_without_authentication():
    response = client.post(
        "/api/v1/production-lines",
        json={
            "name": "Unauthorized Line",
            "code": "LINE-UNAUTH",
            "production_capacity": 5000,
            "plant_id": 1,
            "status": "Active",
        },
    )

    assert response.status_code == 401


def test_worker_cannot_create_production_line():
    admin = create_super_admin()

    plant = create_plant(admin["token"])

    worker = create_worker()

    response = client.post(
        "/api/v1/production-lines",
        json={
            "name": "Worker Line",
            "code": "LINE-WORKER",
            "production_capacity": 5000,
            "plant_id": plant["id"],
            "status": "Active",
        },
        headers={
            "Authorization": f"Bearer {worker['token']}"
        },
    )

    assert response.status_code == 403


def test_plant_manager_can_create_production_line():
    admin = create_super_admin()

    plant = create_plant(admin["token"])

    manager = create_plant_manager()

    response = client.post(
        "/api/v1/production-lines",
        json={
            "name": "Manager Line",
            "code": "LINE-MANAGER",
            "production_capacity": 5000,
            "plant_id": plant["id"],
            "status": "Active",
        },
        headers={
            "Authorization": f"Bearer {manager['token']}"
        },
    )

    assert response.status_code == 201


def test_production_manager_can_create_production_line():
    admin = create_super_admin()

    plant = create_plant(admin["token"])

    manager = create_production_manager()

    response = client.post(
        "/api/v1/production-lines",
        json={
            "name": "Production Manager Line",
            "code": "LINE-PM",
            "production_capacity": 6000,
            "plant_id": plant["id"],
            "status": "Active",
        },
        headers={
            "Authorization": f"Bearer {manager['token']}"
        },
    )

    assert response.status_code == 201


def test_duplicate_line_code():
    admin = create_super_admin()

    plant = create_plant(admin["token"])

    create_production_line(
        admin["token"],
        plant["id"],
        code="LINE-DUPLICATE",
    )

    response = client.post(
        "/api/v1/production-lines",
        json={
            "name": "Duplicate Line",
            "code": "LINE-DUPLICATE",
            "production_capacity": 7000,
            "plant_id": plant["id"],
            "status": "Active",
        },
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 409


def test_get_production_line_details():
    admin = create_super_admin()

    plant = create_plant(admin["token"])

    line = create_production_line(
        admin["token"],
        plant["id"],
    )

    response = client.get(
        f"/api/v1/production-lines/{line['id']}",
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == line["id"]
    assert data["name"] == line["name"]
    assert data["code"] == line["code"]
    assert data["plant_id"] == plant["id"]


def test_get_nonexistent_production_line():
    admin = create_super_admin()

    response = client.get(
        "/api/v1/production-lines/999999",
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 404


def test_list_production_lines():
    admin = create_super_admin()

    plant = create_plant(admin["token"])

    create_production_line(
        admin["token"],
        plant["id"],
    )

    create_production_line(
        admin["token"],
        plant["id"],
    )

    create_production_line(
        admin["token"],
        plant["id"],
    )

    response = client.get(
        "/api/v1/production-lines",
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total_pages"] == 1


def test_update_production_line():
    admin = create_super_admin()

    plant = create_plant(admin["token"])

    line = create_production_line(
        admin["token"],
        plant["id"],
    )

    response = client.put(
        f"/api/v1/production-lines/{line['id']}",
        json={
            "name": "Updated Assembly Line",
            "production_capacity": 12000,
        },
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Updated Assembly Line"
    assert data["production_capacity"] == 12000


def test_update_production_line_plant():
    admin = create_super_admin()

    plant_one = create_plant(admin["token"])

    plant_two = create_plant(admin["token"])

    line = create_production_line(
        admin["token"],
        plant_one["id"],
    )

    response = client.put(
        f"/api/v1/production-lines/{line['id']}",
        json={
            "plant_id": plant_two["id"],
        },
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    assert response.json()["plant_id"] == plant_two["id"]


def test_plant_manager_can_update_line():
    admin = create_super_admin()

    plant = create_plant(admin["token"])

    manager = create_plant_manager()

    line = create_production_line(
        admin["token"],
        plant["id"],
    )

    response = client.put(
        f"/api/v1/production-lines/{line['id']}",
        json={
            "name": "Plant Manager Updated Line",
        },
        headers={
            "Authorization": f"Bearer {manager['token']}"
        },
    )

    assert response.status_code == 200

    assert (
        response.json()["name"]
        == "Plant Manager Updated Line"
    )


def test_production_manager_can_update_line():
    admin = create_super_admin()

    plant = create_plant(admin["token"])

    manager = create_production_manager()

    line = create_production_line(
        admin["token"],
        plant["id"],
    )

    response = client.put(
        f"/api/v1/production-lines/{line['id']}",
        json={
            "name": "Production Manager Updated Line",
        },
        headers={
            "Authorization": f"Bearer {manager['token']}"
        },
    )

    assert response.status_code == 200


def test_worker_cannot_update_line():
    admin = create_super_admin()

    plant = create_plant(admin["token"])

    line = create_production_line(
        admin["token"],
        plant["id"],
    )

    worker = create_worker()

    response = client.put(
        f"/api/v1/production-lines/{line['id']}",
        json={
            "name": "Unauthorized Update",
        },
        headers={
            "Authorization": f"Bearer {worker['token']}"
        },
    )

    assert response.status_code == 403


def test_update_line_status():
    admin = create_super_admin()

    plant = create_plant(admin["token"])

    line = create_production_line(
        admin["token"],
        plant["id"],
    )

    for line_status in [
        "Maintenance",
        "Inactive",
        "Active",
    ]:
        response = client.patch(
            f"/api/v1/production-lines/{line['id']}/status",
            params={
                "status_value": line_status
            },
            headers={
                "Authorization": f"Bearer {admin['token']}"
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == line_status


def test_assign_supervisor():
    admin = create_super_admin()

    plant = create_plant(admin["token"])

    supervisor = create_supervisor()

    line = create_production_line(
        admin["token"],
        plant["id"],
    )

    response = client.patch(
        f"/api/v1/production-lines/"
        f"{line['id']}/supervisor/{supervisor['id']}",
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["supervisor_id"] == supervisor["id"]


def test_create_line_with_supervisor():
    admin = create_super_admin()

    plant = create_plant(admin["token"])

    supervisor = create_supervisor()

    line = create_production_line(
        admin["token"],
        plant["id"],
        supervisor_id=supervisor["id"],
    )

    assert line["supervisor_id"] == supervisor["id"]


def test_invalid_supervisor_role():
    admin = create_super_admin()

    plant = create_plant(admin["token"])

    worker = create_worker()

    response = client.post(
        "/api/v1/production-lines",
        json={
            "name": "Invalid Supervisor Line",
            "code": "LINE-INVALID-SUP",
            "production_capacity": 5000,
            "plant_id": plant["id"],
            "status": "Active",
            "supervisor_id": worker["id"],
        },
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 400


def test_remove_supervisor():
    admin = create_super_admin()

    plant = create_plant(admin["token"])

    supervisor = create_supervisor()

    line = create_production_line(
        admin["token"],
        plant["id"],
        supervisor_id=supervisor["id"],
    )

    response = client.delete(
        f"/api/v1/production-lines/"
        f"{line['id']}/supervisor",
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    assert response.json()["supervisor_id"] is None


def test_search_production_lines():
    admin = create_super_admin()

    plant = create_plant(admin["token"])

    create_production_line(
        admin["token"],
        plant["id"],
        name="Assembly Department",
        code="ASSEMBLY-001",
    )

    create_production_line(
        admin["token"],
        plant["id"],
        name="Packaging Department",
        code="PACKAGING-001",
    )

    create_production_line(
        admin["token"],
        plant["id"],
        name="Quality Department",
        code="QUALITY-001",
    )

    response = client.get(
        "/api/v1/production-lines",
        params={
            "search": "Assembly"
        },
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["name"] == "Assembly Department"


def test_search_by_line_code():
    admin = create_super_admin()

    plant = create_plant(admin["token"])

    create_production_line(
        admin["token"],
        plant["id"],
        name="Assembly Department",
        code="ASSEMBLY-001",
    )

    create_production_line(
        admin["token"],
        plant["id"],
        name="Packaging Department",
        code="PACKAGING-001",
    )

    response = client.get(
        "/api/v1/production-lines",
        params={
            "search": "PACKAGING-001"
        },
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["code"] == "PACKAGING-001"


def test_filter_by_plant():
    admin = create_super_admin()

    plant_one = create_plant(admin["token"])

    plant_two = create_plant(admin["token"])

    create_production_line(
        admin["token"],
        plant_one["id"],
    )

    create_production_line(
        admin["token"],
        plant_one["id"],
    )

    create_production_line(
        admin["token"],
        plant_two["id"],
    )

    response = client.get(
        "/api/v1/production-lines",
        params={
            "plant_id": plant_one["id"]
        },
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2

    for item in data["items"]:
        assert item["plant_id"] == plant_one["id"]


def test_filter_by_status():
    admin = create_super_admin()

    plant = create_plant(admin["token"])

    create_production_line(
        admin["token"],
        plant["id"],
        line_status="Active",
    )

    create_production_line(
        admin["token"],
        plant["id"],
        line_status="Maintenance",
    )

    create_production_line(
        admin["token"],
        plant["id"],
        line_status="Inactive",
    )

    response = client.get(
        "/api/v1/production-lines",
        params={
            "status_value": "Maintenance"
        },
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["status"] == "Maintenance"


def test_filter_by_plant_and_status():
    admin = create_super_admin()

    plant_one = create_plant(admin["token"])

    plant_two = create_plant(admin["token"])

    create_production_line(
        admin["token"],
        plant_one["id"],
        line_status="Active",
    )

    create_production_line(
        admin["token"],
        plant_one["id"],
        line_status="Maintenance",
    )

    create_production_line(
        admin["token"],
        plant_two["id"],
        line_status="Maintenance",
    )

    response = client.get(
        "/api/v1/production-lines",
        params={
            "plant_id": plant_one["id"],
            "status_value": "Maintenance",
        },
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["plant_id"] == plant_one["id"]
    assert data["items"][0]["status"] == "Maintenance"


def test_pagination():
    admin = create_super_admin()

    plant = create_plant(admin["token"])

    for _ in range(5):
        create_production_line(
            admin["token"],
            plant["id"],
        )

    response = client.get(
        "/api/v1/production-lines",
        params={
            "page": 1,
            "page_size": 2,
        },
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total_pages"] == 3


def test_pagination_second_page():
    admin = create_super_admin()

    plant = create_plant(admin["token"])

    for _ in range(5):
        create_production_line(
            admin["token"],
            plant["id"],
        )

    response = client.get(
        "/api/v1/production-lines",
        params={
            "page": 2,
            "page_size": 2,
        },
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["page"] == 2
    assert data["total_pages"] == 3


def test_delete_production_line():
    admin = create_super_admin()

    plant = create_plant(admin["token"])

    line = create_production_line(
        admin["token"],
        plant["id"],
    )

    response = client.delete(
        f"/api/v1/production-lines/{line['id']}",
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 200

    assert (
        response.json()["message"]
        == "Production line deleted successfully"
    )

    response = client.get(
        f"/api/v1/production-lines/{line['id']}",
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 404


def test_negative_capacity_rejected():
    admin = create_super_admin()

    plant = create_plant(admin["token"])

    response = client.post(
        "/api/v1/production-lines",
        json={
            "name": "Invalid Capacity Line",
            "code": "LINE-NEGATIVE",
            "production_capacity": -100,
            "plant_id": plant["id"],
            "status": "Active",
        },
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 422


def test_invalid_status_rejected():
    admin = create_super_admin()

    plant = create_plant(admin["token"])

    response = client.post(
        "/api/v1/production-lines",
        json={
            "name": "Invalid Status Line",
            "code": "LINE-STATUS",
            "production_capacity": 5000,
            "plant_id": plant["id"],
            "status": "Running",
        },
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 422


def test_invalid_plant_rejected():
    admin = create_super_admin()

    response = client.post(
        "/api/v1/production-lines",
        json={
            "name": "Invalid Plant Line",
            "code": "LINE-PLANT",
            "production_capacity": 5000,
            "plant_id": 999999,
            "status": "Active",
        },
        headers={
            "Authorization": f"Bearer {admin['token']}"
        },
    )

    assert response.status_code == 404