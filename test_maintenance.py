
import os
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "manufacturing_production_quality_test"
)

from datetime import datetime, timedelta

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
                    maintenances,
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

    assert response.status_code in [200, 201], (
        response.text
    )

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

    assert login_response.status_code == 200, (
        login_response.text
    )

    return {
        "id": user_id,
        "token": login_response.json()[
            "access_token"
        ],
        "email": email,
    }


def create_admin():
    return create_user(
        role="Super Admin",
        email=(
            f"admin_{uuid4().hex[:8]}"
            "@example.com"
        ),
    )


def create_maintenance_engineer():
    return create_user(
        role="Maintenance Engineer",
        email=(
            f"engineer_{uuid4().hex[:8]}"
            "@example.com"
        ),
    )


def create_worker():
    return create_user(
        role="Worker",
        email=(
            f"worker_{uuid4().hex[:8]}"
            "@example.com"
        ),
    )


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def create_plant(token):
    code = (
        f"PLT-{uuid4().hex[:6].upper()}"
    )

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

    assert response.status_code == 201, (
        response.text
    )

    return response.json()


def create_production_line(
    token,
    plant_id,
):
    code = (
        f"LINE-{uuid4().hex[:6].upper()}"
    )

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

    assert response.status_code == 201, (
        response.text
    )

    return response.json()


def create_machine(
    token,
    production_line_id,
):
    machine_code = (
        f"MCH-{uuid4().hex[:6].upper()}"
    )

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

    assert response.status_code == 201, (
        response.text
    )

    return response.json()


def setup_machine():
    admin = create_admin()

    plant = create_plant(
        admin["token"]
    )

    line = create_production_line(
        admin["token"],
        plant["id"],
    )

    machine = create_machine(
        admin["token"],
        line["id"],
    )

    return (
        admin,
        plant,
        line,
        machine,
    )


def maintenance_payload(
    machine_id,
    maintenance_type="Preventive",
    scheduled_date=None,
    next_due_date=None,
):
    if scheduled_date is None:
        scheduled_date = (
            datetime.utcnow()
            + timedelta(days=1)
        )

    if next_due_date is None:
        next_due_date = (
            scheduled_date
            + timedelta(days=30)
        )

    return {
        "maintenance_number": (
            f"PM-{uuid4().hex[:8].upper()}"
        ),
        "machine_id": machine_id,
        "maintenance_type": (
            maintenance_type
        ),
        "maintenance_status": "Scheduled",
        "scheduled_date": (
            scheduled_date.isoformat()
        ),
        "next_due_date": (
            next_due_date.isoformat()
        ),
        "maintenance_description": (
            "Routine machine maintenance"
        ),
        "maintenance_cost": 2500,
        "spare_parts_used": [
            {
                "part_name": "Bearing",
                "quantity": 2,
                "unit_cost": 750,
            }
        ],
    }


def test_create_maintenance():
    cleanup_database()

    (
        admin,
        _,
        _,
        machine,
    ) = setup_machine()

    response = client.post(
        "/api/v1/maintenance",
        headers=auth_headers(
            admin["token"]
        ),
        json=maintenance_payload(
            machine["id"]
        ),
    )

    assert response.status_code == 201, (
        response.text
    )

    data = response.json()

    assert data["machine_id"] == machine["id"]
    assert data["maintenance_type"] == (
        "Preventive"
    )
    assert data["maintenance_status"] == (
        "Scheduled"
    )
    assert float(
        data["maintenance_cost"]
    ) == 2500


def test_create_breakdown_maintenance():
    cleanup_database()

    (
        admin,
        _,
        _,
        machine,
    ) = setup_machine()

    payload = maintenance_payload(
        machine["id"],
        maintenance_type="Breakdown",
    )

    payload["issue_description"] = (
        "Machine stopped unexpectedly"
    )

    response = client.post(
        "/api/v1/maintenance",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 201, (
        response.text
    )

    assert response.json()[
        "maintenance_type"
    ] == "Breakdown"


def test_get_maintenance():
    cleanup_database()

    (
        admin,
        _,
        _,
        machine,
    ) = setup_machine()

    create_response = client.post(
        "/api/v1/maintenance",
        headers=auth_headers(
            admin["token"]
        ),
        json=maintenance_payload(
            machine["id"]
        ),
    )

    assert create_response.status_code == 201

    maintenance_id = (
        create_response.json()["id"]
    )

    response = client.get(
        f"/api/v1/maintenance/{maintenance_id}",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 200

    assert response.json()["id"] == (
        maintenance_id
    )


def test_list_maintenance():
    cleanup_database()

    (
        admin,
        _,
        _,
        machine,
    ) = setup_machine()

    for _ in range(3):
        response = client.post(
            "/api/v1/maintenance",
            headers=auth_headers(
                admin["token"]
            ),
            json=maintenance_payload(
                machine["id"]
            ),
        )

        assert response.status_code == 201

    response = client.get(
        "/api/v1/maintenance",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert data["page"] == 1


def test_search_maintenance():
    cleanup_database()

    (
        admin,
        _,
        _,
        machine,
    ) = setup_machine()

    payload = maintenance_payload(
        machine["id"]
    )

    payload["maintenance_description"] = (
        "Monthly motor inspection"
    )

    response = client.post(
        "/api/v1/maintenance",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 201

    response = client.get(
        "/api/v1/maintenance",
        headers=auth_headers(
            admin["token"]
        ),
        params={
            "search": "motor",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1


def test_filter_by_type():
    cleanup_database()

    (
        admin,
        _,
        _,
        machine,
    ) = setup_machine()

    response = client.post(
        "/api/v1/maintenance",
        headers=auth_headers(
            admin["token"]
        ),
        json=maintenance_payload(
            machine["id"],
            maintenance_type="Preventive",
        ),
    )

    assert response.status_code == 201

    response = client.post(
        "/api/v1/maintenance",
        headers=auth_headers(
            admin["token"]
        ),
        json=maintenance_payload(
            machine["id"],
            maintenance_type="Breakdown",
        ),
    )

    assert response.status_code == 201

    response = client.get(
        "/api/v1/maintenance",
        headers=auth_headers(
            admin["token"]
        ),
        params={
            "maintenance_type": "Breakdown",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1

    for item in data["items"]:
        assert item["maintenance_type"] == (
            "Breakdown"
        )


def test_filter_by_machine():
    cleanup_database()

    (
        admin,
        _,
        _,
        machine,
    ) = setup_machine()

    response = client.post(
        "/api/v1/maintenance",
        headers=auth_headers(
            admin["token"]
        ),
        json=maintenance_payload(
            machine["id"]
        ),
    )

    assert response.status_code == 201

    response = client.get(
        "/api/v1/maintenance",
        headers=auth_headers(
            admin["token"]
        ),
        params={
            "machine_id": machine["id"],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1

    assert data["items"][0][
        "machine_id"
    ] == machine["id"]


def test_update_maintenance():
    cleanup_database()

    (
        admin,
        _,
        _,
        machine,
    ) = setup_machine()

    create_response = client.post(
        "/api/v1/maintenance",
        headers=auth_headers(
            admin["token"]
        ),
        json=maintenance_payload(
            machine["id"]
        ),
    )

    assert create_response.status_code == 201

    maintenance_id = (
        create_response.json()["id"]
    )

    completed_date = (
        datetime.utcnow()
        + timedelta(hours=2)
    )

    response = client.put(
        f"/api/v1/maintenance/{maintenance_id}",
        headers=auth_headers(
            admin["token"]
        ),
        json={
            "maintenance_status": "Completed",
            "completed_date": (
                completed_date.isoformat()
            ),
            "maintenance_cost": 3500,
        },
    )

    assert response.status_code == 200, (
        response.text
    )

    data = response.json()

    assert data["maintenance_status"] == (
        "Completed"
    )

    assert float(
        data["maintenance_cost"]
    ) == 3500


def test_delete_maintenance():
    cleanup_database()

    (
        admin,
        _,
        _,
        machine,
    ) = setup_machine()

    create_response = client.post(
        "/api/v1/maintenance",
        headers=auth_headers(
            admin["token"]
        ),
        json=maintenance_payload(
            machine["id"]
        ),
    )

    assert create_response.status_code == 201

    maintenance_id = (
        create_response.json()["id"]
    )

    response = client.delete(
        f"/api/v1/maintenance/{maintenance_id}",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 204

    response = client.get(
        f"/api/v1/maintenance/{maintenance_id}",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 404


def test_missing_auth_rejected():
    cleanup_database()

    response = client.get(
        "/api/v1/maintenance"
    )

    assert response.status_code == 401


def test_worker_cannot_create_maintenance():
    cleanup_database()

    (
        admin,
        _,
        _,
        machine,
    ) = setup_machine()

    worker = create_worker()

    response = client.post(
        "/api/v1/maintenance",
        headers=auth_headers(
            worker["token"]
        ),
        json=maintenance_payload(
            machine["id"]
        ),
    )

    assert response.status_code == 403


def test_maintenance_engineer_can_create():
    cleanup_database()

    (
        admin,
        _,
        _,
        machine,
    ) = setup_machine()

    engineer = create_maintenance_engineer()

    response = client.post(
        "/api/v1/maintenance",
        headers=auth_headers(
            engineer["token"]
        ),
        json=maintenance_payload(
            machine["id"]
        ),
    )

    assert response.status_code == 201, (
        response.text
    )

    assert response.json()[
        "maintenance_type"
    ] == "Preventive"


def test_due_maintenance_alert():
    cleanup_database()

    (
        admin,
        _,
        _,
        machine,
    ) = setup_machine()

    past_date = (
        datetime.utcnow()
        - timedelta(days=1)
    )

    payload = maintenance_payload(
        machine["id"],
        scheduled_date=past_date,
        next_due_date=past_date,
    )

    payload["maintenance_number"] = (
        f"PM-DUE-{uuid4().hex[:8].upper()}"
    )

    response = client.post(
        "/api/v1/maintenance",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 201, (
        response.text
    )

    response = client.get(
        "/api/v1/maintenance/alerts/due",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 200, (
        response.text
    )

    data = response.json()

    assert data["total"] >= 1

    assert any(
        item["maintenance_number"]
        == payload["maintenance_number"]
        for item in data["items"]
    )


def test_duplicate_maintenance_number_rejected():
    cleanup_database()

    (
        admin,
        _,
        _,
        machine,
    ) = setup_machine()

    maintenance_number = (
        f"PM-DUP-{uuid4().hex[:8].upper()}"
    )

    payload = maintenance_payload(
        machine["id"]
    )

    payload["maintenance_number"] = (
        maintenance_number
    )

    response = client.post(
        "/api/v1/maintenance",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 201

    response = client.post(
        "/api/v1/maintenance",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 400

    assert "already exists" in (
        response.text.lower()
    )


def test_invalid_machine_rejected():
    cleanup_database()

    admin = create_admin()

    payload = maintenance_payload(
        machine_id=999999
    )

    response = client.post(
        "/api/v1/maintenance",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 404

    assert "machine not found" in (
        response.text.lower()
    )


def test_completed_date_before_scheduled_date_rejected():
    cleanup_database()

    (
        admin,
        _,
        _,
        machine,
    ) = setup_machine()

    scheduled_date = (
        datetime.utcnow()
        + timedelta(days=2)
    )

    completed_date = datetime.utcnow()

    payload = maintenance_payload(
        machine["id"],
        scheduled_date=scheduled_date,
    )

    payload["completed_date"] = (
        completed_date.isoformat()
    )

    response = client.post(
        "/api/v1/maintenance",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 400

    assert (
        "completed date cannot be before"
        in response.text.lower()
    )


def test_filter_by_status():
    cleanup_database()

    (
        admin,
        _,
        _,
        machine,
    ) = setup_machine()

    scheduled_payload = maintenance_payload(
        machine["id"]
    )

    completed_scheduled_date = (
        datetime.utcnow()
        - timedelta(days=1)
    )

    completed_payload = maintenance_payload(
        machine["id"],
        scheduled_date=(
            completed_scheduled_date
        ),
        next_due_date=(
            completed_scheduled_date
            + timedelta(days=30)
        ),
    )

    completed_payload[
        "maintenance_status"
    ] = "Completed"

    completed_payload[
        "completed_date"
    ] = datetime.utcnow().isoformat()

    response = client.post(
        "/api/v1/maintenance",
        headers=auth_headers(
            admin["token"]
        ),
        json=scheduled_payload,
    )

    assert response.status_code == 201, (
        response.text
    )

    response = client.post(
        "/api/v1/maintenance",
        headers=auth_headers(
            admin["token"]
        ),
        json=completed_payload,
    )

    assert response.status_code == 201, (
        response.text
    )

    response = client.get(
        "/api/v1/maintenance",
        headers=auth_headers(
            admin["token"]
        ),
        params={
            "maintenance_status": "Completed",
        },
    )

    assert response.status_code == 200, (
        response.text
    )

    data = response.json()

    assert data["total"] == 1

    for item in data["items"]:
        assert item["maintenance_status"] == (
            "Completed"
        )

