from fastapi.testclient import TestClient
from sqlalchemy import text

from database import SessionLocal
from main import app


client = TestClient(app)


def create_admin():
    email = "audit_level20_admin@example.com"
    password = "Admin@12345"

    db = SessionLocal()

    try:
        user_id = db.execute(
            text(
                """
                SELECT id
                FROM users
                WHERE email = :email
                """
            ),
            {"email": email},
        ).scalar()

        if user_id is None:
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "full_name": "Audit Level 20 Admin",
                    "email": email,
                    "password": password,
                },
            )

            assert response.status_code in [200, 201], response.text

        db.commit()

        db.execute(
            text(
                """
                UPDATE users
                SET role = 'SUPER_ADMIN'
                WHERE email = :email
                """
            ),
            {"email": email},
        )

        db.commit()

    finally:
        db.close()

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200, response.text

    return response.json()["access_token"]


def test_audit_logs_requires_authentication():
    response = client.get(
        "/api/v1/audit-logs"
    )

    assert response.status_code in [401, 403]


def test_audit_logs_empty():
    token = create_admin()

    response = client.get(
        "/api/v1/audit-logs",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_audit_log():
    token = create_admin()

    db = SessionLocal()

    try:
        user_id = db.execute(
            text(
                """
                SELECT id
                FROM users
                WHERE email = :email
                """
            ),
            {
                "email": "audit_level20_admin@example.com"
            },
        ).scalar()

        db.execute(
            text(
                """
                INSERT INTO audit_logs (
                    user_id,
                    action,
                    entity,
                    entity_id,
                    previous_value,
                    new_value
                )
                VALUES (
                    :user_id,
                    :action,
                    :entity,
                    :entity_id,
                    CAST(:previous_value AS jsonb),
                    CAST(:new_value AS jsonb)
                )
                """
            ),
            {
                "user_id": user_id,
                "action": "CREATE",
                "entity": "ProductionOrder",
                "entity_id": 99999,
                "previous_value": "null",
                "new_value": '{"status": "DRAFT"}',
            },
        )

        db.commit()

    finally:
        db.close()

    response = client.get(
        "/api/v1/audit-logs",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    audit = next(
        item
        for item in data
        if item["entity"] == "ProductionOrder"
        and item["entity_id"] == 99999
    )

    assert audit["action"] == "CREATE"
    assert audit["previous_value"] is None
    assert audit["new_value"]["status"] == "DRAFT"


def test_get_audit_log_by_id():
    token = create_admin()

    db = SessionLocal()

    try:
        audit_id = db.execute(
            text(
                """
                SELECT id
                FROM audit_logs
                ORDER BY id DESC
                LIMIT 1
                """
            )
        ).scalar()

    finally:
        db.close()

    assert audit_id is not None

    response = client.get(
        f"/api/v1/audit-logs/{audit_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == audit_id


def test_filter_audit_logs_by_action():
    token = create_admin()

    response = client.get(
        "/api/v1/audit-logs",
        params={
            "action": "CREATE",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    for item in data:
        assert item["action"] == "CREATE"


def test_filter_audit_logs_by_entity():
    token = create_admin()

    response = client.get(
        "/api/v1/audit-logs",
        params={
            "entity": "ProductionOrder",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    for item in data:
        assert item["entity"] == "ProductionOrder"


def test_get_audit_logs_by_user():
    token = create_admin()

    db = SessionLocal()

    try:
        user_id = db.execute(
            text(
                """
                SELECT id
                FROM users
                WHERE email = :email
                """
            ),
            {
                "email": "audit_level20_admin@example.com"
            },
        ).scalar()

    finally:
        db.close()

    response = client.get(
        f"/api/v1/audit-logs/user/{user_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    for item in data:
        assert item["user_id"] == user_id


def test_get_audit_logs_by_entity():
    token = create_admin()

    response = client.get(
        "/api/v1/audit-logs/entity/ProductionOrder/99999",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    for item in data:
        assert item["entity"] == "ProductionOrder"
        assert item["entity_id"] == 99999