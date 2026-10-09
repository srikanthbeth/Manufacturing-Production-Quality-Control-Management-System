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
                    downtimes,
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


def create_worker():
    return create_user(
        role="Worker",
        email=(
            f"worker_{uuid4().hex[:8]}"
            "@example.com"
        ),
    )


def create_production_manager():
    return create_user(
        role="Production Manager",
        email=(
            f"manager_{uuid4().hex[:8]}"
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


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}"
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


def downtime_payload(
    machine_id,
    production_line_id,
    responsible_person_id,
    category="Machine Breakdown",
    reason="Machine stopped unexpectedly",
    start_time=None,
    end_time="AUTO",
):
    if start_time is None:
        start_time = (
            datetime.utcnow()
            - timedelta(hours=2)
        )

    if end_time == "AUTO":
        end_time = (
            start_time
            + timedelta(minutes=60)
        )

    return {
        "downtime_number": (
            f"DT-{uuid4().hex[:8].upper()}"
        ),
        "machine_id": machine_id,
        "production_line_id": (
            production_line_id
        ),
        "responsible_person_id": (
            responsible_person_id
        ),
        "category": category,
        "reason": reason,
        "start_time": (
            start_time.isoformat()
        ),
        "end_time": (
            end_time.isoformat()
            if end_time is not None
            else None
        ),
    }


def test_create_downtime():
    cleanup_database()

    (
        admin,
        _,
        line,
        machine,
    ) = setup_machine()

    payload = downtime_payload(
        machine["id"],
        line["id"],
        admin["id"],
    )

    response = client.post(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 201, (
        response.text
    )

    data = response.json()

    assert data["machine_id"] == (
        machine["id"]
    )

    assert data["production_line_id"] == (
        line["id"]
    )

    assert data[
        "responsible_person_id"
    ] == admin["id"]

    assert data["category"] == (
        "Machine Breakdown"
    )

    assert float(
        data["duration_minutes"]
    ) == 60


def test_create_material_shortage_downtime():
    cleanup_database()

    (
        admin,
        _,
        line,
        machine,
    ) = setup_machine()

    payload = downtime_payload(
        machine["id"],
        line["id"],
        admin["id"],
        category="Material Shortage",
    )

    payload["reason"] = (
        "Raw material unavailable"
    )

    response = client.post(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 201, (
        response.text
    )

    assert response.json()["category"] == (
        "Material Shortage"
    )


def test_create_quality_issue_downtime():
    cleanup_database()

    (
        admin,
        _,
        line,
        machine,
    ) = setup_machine()

    payload = downtime_payload(
        machine["id"],
        line["id"],
        admin["id"],
        category="Quality Issue",
    )

    response = client.post(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 201, (
        response.text
    )

    assert response.json()["category"] == (
        "Quality Issue"
    )


def test_create_power_failure_downtime():
    cleanup_database()

    (
        admin,
        _,
        line,
        machine,
    ) = setup_machine()

    payload = downtime_payload(
        machine["id"],
        line["id"],
        admin["id"],
        category="Power Failure",
    )

    response = client.post(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 201, (
        response.text
    )

    assert response.json()["category"] == (
        "Power Failure"
    )


def test_create_maintenance_downtime():
    cleanup_database()

    (
        admin,
        _,
        line,
        machine,
    ) = setup_machine()

    payload = downtime_payload(
        machine["id"],
        line["id"],
        admin["id"],
        category="Maintenance",
    )

    response = client.post(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 201, (
        response.text
    )

    assert response.json()["category"] == (
        "Maintenance"
    )


def test_create_operator_issue_downtime():
    cleanup_database()

    (
        admin,
        _,
        line,
        machine,
    ) = setup_machine()

    payload = downtime_payload(
        machine["id"],
        line["id"],
        admin["id"],
        category="Operator Issue",
    )

    response = client.post(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 201, (
        response.text
    )

    assert response.json()["category"] == (
        "Operator Issue"
    )


def test_get_downtime():
    cleanup_database()

    (
        admin,
        _,
        line,
        machine,
    ) = setup_machine()

    payload = downtime_payload(
        machine["id"],
        line["id"],
        admin["id"],
    )

    create_response = client.post(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert create_response.status_code == 201

    downtime_id = (
        create_response.json()["id"]
    )

    response = client.get(
        f"/api/v1/downtime/{downtime_id}",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == downtime_id


def test_list_downtime():
    cleanup_database()

    (
        admin,
        _,
        line,
        machine,
    ) = setup_machine()

    for _ in range(3):
        payload = downtime_payload(
            machine["id"],
            line["id"],
            admin["id"],
        )

        response = client.post(
            "/api/v1/downtime",
            headers=auth_headers(
                admin["token"]
            ),
            json=payload,
        )

        assert response.status_code == 201

    response = client.get(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert data["page"] == 1


def test_search_downtime():
    cleanup_database()

    (
        admin,
        _,
        line,
        machine,
    ) = setup_machine()

    payload = downtime_payload(
        machine["id"],
        line["id"],
        admin["id"],
        reason="Motor overheating issue",
    )

    response = client.post(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 201

    response = client.get(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        params={
            "search": "overheating"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1


def test_filter_by_category():
    cleanup_database()

    (
        admin,
        _,
        line,
        machine,
    ) = setup_machine()

    categories = [
        "Machine Breakdown",
        "Material Shortage",
    ]

    for category in categories:
        payload = downtime_payload(
            machine["id"],
            line["id"],
            admin["id"],
            category=category,
        )

        response = client.post(
            "/api/v1/downtime",
            headers=auth_headers(
                admin["token"]
            ),
            json=payload,
        )

        assert response.status_code == 201

    response = client.get(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        params={
            "category": "Material Shortage"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1

    assert data["items"][0]["category"] == (
        "Material Shortage"
    )


def test_filter_by_machine():
    cleanup_database()

    (
        admin,
        _,
        line,
        machine,
    ) = setup_machine()

    payload = downtime_payload(
        machine["id"],
        line["id"],
        admin["id"],
    )

    response = client.post(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 201

    response = client.get(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        params={
            "machine_id": machine["id"]
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1

    assert data["items"][0][
        "machine_id"
    ] == machine["id"]


def test_filter_by_production_line():
    cleanup_database()

    (
        admin,
        _,
        line,
        machine,
    ) = setup_machine()

    payload = downtime_payload(
        machine["id"],
        line["id"],
        admin["id"],
    )

    response = client.post(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 201

    response = client.get(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        params={
            "production_line_id": line["id"]
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1

    assert data["items"][0][
        "production_line_id"
    ] == line["id"]


def test_filter_by_responsible_person():
    cleanup_database()

    (
        admin,
        _,
        line,
        machine,
    ) = setup_machine()

    payload = downtime_payload(
        machine["id"],
        line["id"],
        admin["id"],
    )

    response = client.post(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 201

    response = client.get(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        params={
            "responsible_person_id": admin["id"]
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1

    assert data["items"][0][
        "responsible_person_id"
    ] == admin["id"]


def test_update_downtime():
    cleanup_database()

    (
        admin,
        _,
        line,
        machine,
    ) = setup_machine()

    start_time = (
        datetime.utcnow()
        - timedelta(hours=3)
    )

    end_time = (
        start_time
        + timedelta(minutes=30)
    )

    payload = downtime_payload(
        machine["id"],
        line["id"],
        admin["id"],
        start_time=start_time,
        end_time=end_time,
    )

    create_response = client.post(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert create_response.status_code == 201

    downtime_id = (
        create_response.json()["id"]
    )

    new_end_time = (
        start_time
        + timedelta(minutes=90)
    )

    response = client.put(
        f"/api/v1/downtime/{downtime_id}",
        headers=auth_headers(
            admin["token"]
        ),
        json={
            "category": "Maintenance",
            "reason": "Scheduled maintenance",
            "end_time": (
                new_end_time.isoformat()
            ),
        },
    )

    assert response.status_code == 200, (
        response.text
    )

    data = response.json()

    assert data["category"] == (
        "Maintenance"
    )

    assert data["reason"] == (
        "Scheduled maintenance"
    )

    assert float(
        data["duration_minutes"]
    ) == 90


def test_delete_downtime():
    cleanup_database()

    (
        admin,
        _,
        line,
        machine,
    ) = setup_machine()

    payload = downtime_payload(
        machine["id"],
        line["id"],
        admin["id"],
    )

    create_response = client.post(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert create_response.status_code == 201

    downtime_id = (
        create_response.json()["id"]
    )

    response = client.delete(
        f"/api/v1/downtime/{downtime_id}",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 204

    response = client.get(
        f"/api/v1/downtime/{downtime_id}",
        headers=auth_headers(
            admin["token"]
        ),
    )

    assert response.status_code == 404


def test_missing_auth_rejected():
    cleanup_database()

    response = client.get(
        "/api/v1/downtime"
    )

    assert response.status_code == 401


def test_worker_cannot_create_downtime():
    cleanup_database()

    (
        admin,
        _,
        line,
        machine,
    ) = setup_machine()

    worker = create_worker()

    payload = downtime_payload(
        machine["id"],
        line["id"],
        admin["id"],
    )

    response = client.post(
        "/api/v1/downtime",
        headers=auth_headers(
            worker["token"]
        ),
        json=payload,
    )

    assert response.status_code == 403


def test_production_manager_can_create_downtime():
    cleanup_database()

    (
        admin,
        _,
        line,
        machine,
    ) = setup_machine()

    manager = create_production_manager()

    payload = downtime_payload(
        machine["id"],
        line["id"],
        manager["id"],
    )

    response = client.post(
        "/api/v1/downtime",
        headers=auth_headers(
            manager["token"]
        ),
        json=payload,
    )

    assert response.status_code == 201, (
        response.text
    )


def test_maintenance_engineer_can_create_downtime():
    cleanup_database()

    (
        admin,
        _,
        line,
        machine,
    ) = setup_machine()

    engineer = create_maintenance_engineer()

    payload = downtime_payload(
        machine["id"],
        line["id"],
        engineer["id"],
        category="Maintenance",
    )

    response = client.post(
        "/api/v1/downtime",
        headers=auth_headers(
            engineer["token"]
        ),
        json=payload,
    )

    assert response.status_code == 201, (
        response.text
    )

    assert response.json()["category"] == (
        "Maintenance"
    )


def test_duplicate_downtime_number_rejected():
    cleanup_database()

    (
        admin,
        _,
        line,
        machine,
    ) = setup_machine()

    downtime_number = (
        f"DT-DUP-{uuid4().hex[:8].upper()}"
    )

    payload = downtime_payload(
        machine["id"],
        line["id"],
        admin["id"],
    )

    payload["downtime_number"] = (
        downtime_number
    )

    response = client.post(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 201

    response = client.post(
        "/api/v1/downtime",
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

    payload = downtime_payload(
        machine_id=999999,
        production_line_id=999999,
        responsible_person_id=admin["id"],
    )

    response = client.post(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 404

    assert "machine not found" in (
        response.text.lower()
    )


def test_invalid_production_line_rejected():
    cleanup_database()

    (
        admin,
        _,
        line,
        machine,
    ) = setup_machine()

    payload = downtime_payload(
        machine["id"],
        production_line_id=999999,
        responsible_person_id=admin["id"],
    )

    response = client.post(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 404

    assert "production line not found" in (
        response.text.lower()
    )


def test_invalid_responsible_person_rejected():
    cleanup_database()

    (
        admin,
        _,
        line,
        machine,
    ) = setup_machine()

    payload = downtime_payload(
        machine["id"],
        line["id"],
        responsible_person_id=999999,
    )

    response = client.post(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 404

    assert "responsible person not found" in (
        response.text.lower()
    )


def test_end_time_before_start_time_rejected():
    cleanup_database()

    (
        admin,
        _,
        line,
        machine,
    ) = setup_machine()

    start_time = datetime.utcnow()

    end_time = (
        start_time
        - timedelta(minutes=30)
    )

    payload = downtime_payload(
        machine["id"],
        line["id"],
        admin["id"],
        start_time=start_time,
        end_time=end_time,
    )

    response = client.post(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 400

    assert "end time must be after" in (
        response.text.lower()
    )


def test_machine_production_line_mismatch_rejected():
    cleanup_database()

    (
        admin,
        plant,
        line,
        machine,
    ) = setup_machine()

    second_line_response = client.post(
        "/api/v1/production-lines",
        headers=auth_headers(
            admin["token"]
        ),
        json={
            "name": "Second Assembly Line",
            "code": (
                f"LINE-{uuid4().hex[:6].upper()}"
            ),
            "plant_id": plant["id"],
            "production_capacity": 3000,
            "status": "Active",
        },
    )

    assert (
        second_line_response.status_code
        == 201
    ), second_line_response.text

    second_line = (
        second_line_response.json()
    )

    payload = downtime_payload(
        machine["id"],
        second_line["id"],
        admin["id"],
    )

    response = client.post(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 400

    assert "does not belong" in (
        response.text.lower()
    )


def test_downtime_percentage():
    cleanup_database()

    (
        admin,
        _,
        line,
        machine,
    ) = setup_machine()

    period_start = (
        datetime.utcnow()
        - timedelta(hours=4)
    )

    period_end = (
        period_start
        + timedelta(hours=4)
    )

    downtime_start = (
        period_start
        + timedelta(hours=1)
    )

    downtime_end = (
        downtime_start
        + timedelta(hours=1)
    )

    payload = downtime_payload(
        machine["id"],
        line["id"],
        admin["id"],
        start_time=downtime_start,
        end_time=downtime_end,
    )

    response = client.post(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 201

    response = client.get(
        "/api/v1/downtime/percentage",
        headers=auth_headers(
            admin["token"]
        ),
        params={
            "machine_id": machine["id"],
            "start_time": (
                period_start.isoformat()
            ),
            "end_time": (
                period_end.isoformat()
            ),
        },
    )

    assert response.status_code == 200, (
        response.text
    )

    data = response.json()

    assert data["machine_id"] == (
        machine["id"]
    )

    assert float(
        data["total_available_minutes"]
    ) == 240

    assert float(
        data["total_downtime_minutes"]
    ) == 60

    assert float(
        data["downtime_percentage"]
    ) == 25


def test_downtime_percentage_multiple_records():
    cleanup_database()

    (
        admin,
        _,
        line,
        machine,
    ) = setup_machine()

    period_start = (
        datetime.utcnow()
        - timedelta(hours=8)
    )

    period_end = (
        period_start
        + timedelta(hours=8)
    )

    first_start = (
        period_start
        + timedelta(hours=1)
    )

    first_end = (
        first_start
        + timedelta(minutes=60)
    )

    second_start = (
        period_start
        + timedelta(hours=4)
    )

    second_end = (
        second_start
        + timedelta(minutes=120)
    )

    first_payload = downtime_payload(
        machine["id"],
        line["id"],
        admin["id"],
        start_time=first_start,
        end_time=first_end,
    )

    second_payload = downtime_payload(
        machine["id"],
        line["id"],
        admin["id"],
        category="Maintenance",
        start_time=second_start,
        end_time=second_end,
    )

    response = client.post(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        json=first_payload,
    )

    assert response.status_code == 201

    response = client.post(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        json=second_payload,
    )

    assert response.status_code == 201

    response = client.get(
        "/api/v1/downtime/percentage",
        headers=auth_headers(
            admin["token"]
        ),
        params={
            "machine_id": machine["id"],
            "start_time": (
                period_start.isoformat()
            ),
            "end_time": (
                period_end.isoformat()
            ),
        },
    )

    assert response.status_code == 200, (
        response.text
    )

    data = response.json()

    assert float(
        data["total_available_minutes"]
    ) == 480

    assert float(
        data["total_downtime_minutes"]
    ) == 180

    assert float(
        data["downtime_percentage"]
    ) == 37.5


def test_open_downtime_duration_is_zero():
    cleanup_database()

    (
        admin,
        _,
        line,
        machine,
    ) = setup_machine()

    start_time = (
        datetime.utcnow()
        - timedelta(hours=1)
    )

    payload = downtime_payload(
        machine_id=machine["id"],
        production_line_id=line["id"],
        responsible_person_id=admin["id"],
        category="Machine Breakdown",
        reason="Machine is currently down",
        start_time=start_time,
        end_time=None,
    )

    assert payload["end_time"] is None

    response = client.post(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        json=payload,
    )

    assert response.status_code == 201, (
        response.text
    )

    data = response.json()

    assert data["end_time"] is None

    assert float(
        data["duration_minutes"]
    ) == 0.0


def test_pagination():
    cleanup_database()

    (
        admin,
        _,
        line,
        machine,
    ) = setup_machine()

    for _ in range(5):
        payload = downtime_payload(
            machine["id"],
            line["id"],
            admin["id"],
        )

        response = client.post(
            "/api/v1/downtime",
            headers=auth_headers(
                admin["token"]
            ),
            json=payload,
        )

        assert response.status_code == 201

    response = client.get(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        params={
            "page": 2,
            "limit": 2,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 5
    assert data["page"] == 2
    assert data["limit"] == 2
    assert len(data["items"]) == 2
    assert data["pages"] == 3


def test_invalid_page_rejected():
    cleanup_database()

    admin = create_admin()

    response = client.get(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        params={
            "page": 0,
        },
    )

    assert response.status_code == 422


def test_invalid_limit_rejected():
    cleanup_database()

    admin = create_admin()

    response = client.get(
        "/api/v1/downtime",
        headers=auth_headers(
            admin["token"]
        ),
        params={
            "limit": 101,
        },
    )

    assert response.status_code == 422