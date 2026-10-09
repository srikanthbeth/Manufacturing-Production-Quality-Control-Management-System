import os
from datetime import date
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "manufacturing_production_quality_test"
)

from fastapi.testclient import TestClient
from sqlalchemy import text

from database import Base, SessionLocal, engine
from main import app
from core.enums import AccountStatus, UserRole
from core.security import hash_password
from models.user import User


client = TestClient(app)

Base.metadata.create_all(bind=engine)


def setup_function():
    db = SessionLocal()

    db.execute(
        text(
            """
            TRUNCATE TABLE
                machines,
                production_lines,
                plants,
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
        "Authorization": f"Bearer {token}"
    }


def create_admin():
    create_user(
        "admin@test.com",
        UserRole.SUPER_ADMIN,
    )

    return login("admin@test.com")


def create_worker():
    create_user(
        "worker@test.com",
        UserRole.WORKER,
    )

    return login("worker@test.com")


def create_production_line(
    token: str,
    line_code: str | None = None,
):
    if line_code is None:
        line_code = f"LINE-{uuid4().hex[:8]}"

    plant_code = f"PLANT-{uuid4().hex[:8]}"

    response = client.post(
        "/api/v1/plants",
        json={
            "name": "Main Manufacturing Plant",
            "code": plant_code,
            "status": "Active",
            "address": "Industrial Area",
            "city": "Tirupati",
            
            "state": "Andhra Pradesh",
            "production_capacity": 1000,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 201, response.text

    plant_id = response.json()["id"]

    response = client.post(
        "/api/v1/production-lines",
        json={
            "name": "Assembly Line",
            "code": line_code,
            "production_capacity": 500,
            "plant_id": plant_id,
            "status": "Active",
        },
        headers=auth_header(token),
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_machine(
    token: str,
    production_line_id: int,
    machine_code: str | None = None,
    status: str = "Idle",
):
    if machine_code is None:
        machine_code = f"MCH-{uuid4().hex[:8]}"

    response = client.post(
        "/api/v1/machines",
        json={
            "machine_code": machine_code,
            "machine_type": "CNC Machine",
            "production_line_id": production_line_id,
            "installation_date": "2026-01-15",
            "status": status,
            "operating_hours": 100.5,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 201, response.text

    return response.json()


def test_create_machine():
    token = create_admin()

    line = create_production_line(token)

    response = client.post(
        "/api/v1/machines",
        json={
            "machine_code": "MCH-001",
            "machine_type": "CNC Machine",
            "production_line_id": line["id"],
            "installation_date": "2026-01-15",
            "status": "Idle",
            "operating_hours": 100,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 201
    data = response.json()

    assert data["machine_code"] == "MCH-001"
    assert data["machine_type"] == "CNC Machine"
    assert data["production_line_id"] == line["id"]
    assert data["status"] == "Idle"
    assert data["operating_hours"] == 100


def test_create_machine_without_authentication():
    token = create_admin()

    line = create_production_line(token)

    response = client.post(
        "/api/v1/machines",
        json={
            "machine_code": "MCH-002",
            "machine_type": "Lathe",
            "production_line_id": line["id"],
            "installation_date": "2026-01-15",
            "status": "Idle",
            "operating_hours": 0,
        },
    )

    assert response.status_code == 401


def test_worker_cannot_create_machine():
    admin_token = create_admin()
    line = create_production_line(admin_token)

    worker_token = create_worker()

    response = client.post(
        "/api/v1/machines",
        json={
            "machine_code": "MCH-003",
            "machine_type": "Lathe",
            "production_line_id": line["id"],
            "installation_date": "2026-01-15",
            "status": "Idle",
            "operating_hours": 0,
        },
        headers=auth_header(worker_token),
    )

    assert response.status_code == 403


def test_maintenance_engineer_can_create_machine():
    admin_token = create_admin()
    line = create_production_line(admin_token)

    create_user(
        "maintenance@test.com",
        UserRole.MAINTENANCE_ENGINEER,
    )

    token = login("maintenance@test.com")

    response = client.post(
        "/api/v1/machines",
        json={
            "machine_code": "MCH-004",
            "machine_type": "Hydraulic Press",
            "production_line_id": line["id"],
            "installation_date": "2026-02-01",
            "status": "Running",
            "operating_hours": 250,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 201


def test_duplicate_machine_code_rejected():
    token = create_admin()
    line = create_production_line(token)

    create_machine(
        token,
        line["id"],
        "MCH-DUP",
    )

    response = client.post(
        "/api/v1/machines",
        json={
            "machine_code": "MCH-DUP",
            "machine_type": "Lathe",
            "production_line_id": line["id"],
            "installation_date": "2026-01-15",
            "status": "Idle",
            "operating_hours": 0,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 409


def test_nonexistent_production_line_rejected():
    token = create_admin()

    response = client.post(
        "/api/v1/machines",
        json={
            "machine_code": "MCH-005",
            "machine_type": "Lathe",
            "production_line_id": 99999,
            "installation_date": "2026-01-15",
            "status": "Idle",
            "operating_hours": 0,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 404


def test_negative_operating_hours_rejected():
    token = create_admin()
    line = create_production_line(token)

    response = client.post(
        "/api/v1/machines",
        json={
            "machine_code": "MCH-006",
            "machine_type": "Lathe",
            "production_line_id": line["id"],
            "installation_date": "2026-01-15",
            "status": "Idle",
            "operating_hours": -10,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 422


def test_get_machine():
    token = create_admin()
    line = create_production_line(token)

    machine = create_machine(
        token,
        line["id"],
    )

    response = client.get(
        f"/api/v1/machines/{machine['id']}",
        headers=auth_header(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == machine["id"]


def test_get_nonexistent_machine():
    token = create_admin()

    response = client.get(
        "/api/v1/machines/99999",
        headers=auth_header(token),
    )

    assert response.status_code == 404


def test_list_machines():
    token = create_admin()
    line = create_production_line(token)

    create_machine(
        token,
        line["id"],
        "MCH-101",
    )

    create_machine(
        token,
        line["id"],
        "MCH-102",
    )

    response = client.get(
        "/api/v1/machines",
        headers=auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_search_machines():
    token = create_admin()
    line = create_production_line(token)

    create_machine(
        token,
        line["id"],
        "CNC-SEARCH-001",
    )

    response = client.get(
        "/api/v1/machines?search=CNC-SEARCH",
        headers=auth_header(token),
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_filter_machines_by_status():
    token = create_admin()
    line = create_production_line(token)

    create_machine(
        token,
        line["id"],
        "MCH-RUN",
        "Running",
    )

    create_machine(
        token,
        line["id"],
        "MCH-IDLE",
        "Idle",
    )

    response = client.get(
        "/api/v1/machines?machine_status=Running",
        headers=auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["status"] == "Running"


def test_filter_machines_by_production_line():
    token = create_admin()

    line1 = create_production_line(
        token,
        "LINE-001",
    )

    line2 = create_production_line(
        token,
        "LINE-002",
    )

    create_machine(
        token,
        line1["id"],
        "MCH-LINE-1",
    )

    create_machine(
        token,
        line2["id"],
        "MCH-LINE-2",
    )

    response = client.get(
        f"/api/v1/machines?production_line_id={line1['id']}",
        headers=auth_header(token),
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_pagination():
    token = create_admin()
    line = create_production_line(token)

    for index in range(5):
        create_machine(
            token,
            line["id"],
            f"MCH-PAGE-{index}",
        )

    response = client.get(
        "/api/v1/machines?page=1&page_size=2",
        headers=auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) == 2


def test_update_machine():
    token = create_admin()
    line = create_production_line(token)

    machine = create_machine(
        token,
        line["id"],
    )

    response = client.put(
        f"/api/v1/machines/{machine['id']}",
        json={
            "machine_type": "Advanced CNC Machine",
            "operating_hours": 500,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["machine_type"] == "Advanced CNC Machine"
    assert data["operating_hours"] == 500


def test_update_machine_production_line():
    token = create_admin()

    line1 = create_production_line(
        token,
        "LINE-101",
    )

    line2 = create_production_line(
        token,
        "LINE-102",
    )

    machine = create_machine(
        token,
        line1["id"],
    )

    response = client.put(
        f"/api/v1/machines/{machine['id']}",
        json={
            "production_line_id": line2["id"],
        },
        headers=auth_header(token),
    )

    assert response.status_code == 200
    assert response.json()["production_line_id"] == line2["id"]


def test_worker_cannot_update_machine():
    admin_token = create_admin()
    line = create_production_line(admin_token)

    machine = create_machine(
        admin_token,
        line["id"],
    )

    worker_token = create_worker()

    response = client.put(
        f"/api/v1/machines/{machine['id']}",
        json={
            "machine_type": "Unauthorized Update",
        },
        headers=auth_header(worker_token),
    )

    assert response.status_code == 403


def test_update_machine_status():
    token = create_admin()
    line = create_production_line(token)

    machine = create_machine(
        token,
        line["id"],
    )

    response = client.patch(
        f"/api/v1/machines/{machine['id']}/status",
        json={
            "status": "Running",
        },
        headers=auth_header(token),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Running"


def test_all_machine_statuses():
    token = create_admin()
    line = create_production_line(token)

    statuses = [
        "Running",
        "Idle",
        "Maintenance",
        "Breakdown",
        "Decommissioned",
    ]

    for index, machine_status in enumerate(statuses):
        machine = create_machine(
            token,
            line["id"],
            f"MCH-STATUS-{index}",
            machine_status,
        )

        assert machine["status"] == machine_status


def test_decommissioned_machine_cannot_be_reactivated():
    token = create_admin()
    line = create_production_line(token)

    machine = create_machine(
        token,
        line["id"],
        status="Decommissioned",
    )

    response = client.patch(
        f"/api/v1/machines/{machine['id']}/status",
        json={
            "status": "Running",
        },
        headers=auth_header(token),
    )

    assert response.status_code == 400


def test_decommissioned_machine_cannot_be_modified():
    token = create_admin()
    line = create_production_line(token)

    machine = create_machine(
        token,
        line["id"],
        status="Decommissioned",
    )

    response = client.put(
        f"/api/v1/machines/{machine['id']}",
        json={
            "machine_type": "Updated Machine",
        },
        headers=auth_header(token),
    )

    assert response.status_code == 400


def test_worker_can_view_machine():
    admin_token = create_admin()
    line = create_production_line(admin_token)

    machine = create_machine(
        admin_token,
        line["id"],
    )

    worker_token = create_worker()

    response = client.get(
        f"/api/v1/machines/{machine['id']}",
        headers=auth_header(worker_token),
    )

    assert response.status_code == 200


def test_machine_list_requires_authentication():
    response = client.get(
        "/api/v1/machines"
    )

    assert response.status_code == 401


def test_worker_cannot_delete_machine():
    admin_token = create_admin()
    line = create_production_line(admin_token)

    machine = create_machine(
        admin_token,
        line["id"],
        status="Decommissioned",
    )

    worker_token = create_worker()

    response = client.delete(
        f"/api/v1/machines/{machine['id']}",
        headers=auth_header(worker_token),
    )

    assert response.status_code == 403


def test_non_decommissioned_machine_cannot_be_deleted():
    token = create_admin()
    line = create_production_line(token)

    machine = create_machine(
        token,
        line["id"],
        status="Idle",
    )

    response = client.delete(
        f"/api/v1/machines/{machine['id']}",
        headers=auth_header(token),
    )

    assert response.status_code == 400


def test_delete_decommissioned_machine():
    token = create_admin()
    line = create_production_line(token)

    machine = create_machine(
        token,
        line["id"],
        status="Decommissioned",
    )

    response = client.delete(
        f"/api/v1/machines/{machine['id']}",
        headers=auth_header(token),
    )

    assert response.status_code == 204

    response = client.get(
        f"/api/v1/machines/{machine['id']}",
        headers=auth_header(token),
    )

    assert response.status_code == 404


def test_get_machines_by_production_line():
    token = create_admin()
    line = create_production_line(token)

    create_machine(
        token,
        line["id"],
        "MCH-LINE-A",
    )

    create_machine(
        token,
        line["id"],
        "MCH-LINE-B",
    )

    response = client.get(
        f"/api/v1/machines/production-line/{line['id']}",
        headers=auth_header(token),
    )

    assert response.status_code == 200
    assert len(response.json()) == 2