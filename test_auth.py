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


def unique_email():
    return f"user_{uuid4().hex[:10]}@example.com"


def cleanup_database():
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                TRUNCATE TABLE auth_tokens, users
                RESTART IDENTITY CASCADE
                """
            )
        )


def setup_module():
    Base.metadata.create_all(bind=engine)
    cleanup_database()


def teardown_module():
    cleanup_database()


def register_user(
    email=None,
    password="Password@123",
):
    if email is None:
        email = unique_email()

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Test Worker",
            "email": email,
            "password": password,
        },
    )

    return response


def login_user(
    email,
    password="Password@123",
):
    return client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )


def test_register_user():
    response = register_user()

    assert response.status_code == 201

    data = response.json()

    assert data["full_name"] == "Test Worker"
    assert data["role"] == "Worker"
    assert data["status"] == "Active"


def test_public_registration_cannot_select_admin_role():
    email = unique_email()

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Attempted Admin",
            "email": email,
            "password": "Password@123",
            "role": "Super Admin",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["role"] == "Worker"


def test_duplicate_email():
    email = unique_email()

    first = register_user(email)

    assert first.status_code == 201

    second = register_user(email)

    assert second.status_code == 409
    assert second.json()["detail"] == "Email already registered"


def test_login_success():
    email = unique_email()

    register_user(email)

    response = login_user(email)

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_invalid_password():
    email = unique_email()

    register_user(email)

    response = login_user(
        email,
        "WrongPassword@123",
    )

    assert response.status_code == 401


def test_current_user():
    email = unique_email()

    register_user(email)

    login_response = login_user(email)

    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == email
    assert data["role"] == "Worker"


def test_missing_authentication():
    response = client.get(
        "/api/v1/auth/me"
    )

    assert response.status_code == 401


def test_invalid_access_token():
    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": "Bearer invalid-token"
        },
    )

    assert response.status_code == 401


def test_refresh_token():
    email = unique_email()

    register_user(email)

    login_response = login_user(email)

    refresh_token = login_response.json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data

    assert data["refresh_token"] != refresh_token


def test_old_refresh_token_cannot_be_reused():
    email = unique_email()

    register_user(email)

    login_response = login_user(email)

    old_refresh_token = login_response.json()["refresh_token"]

    first_refresh = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": old_refresh_token
        },
    )

    assert first_refresh.status_code == 200

    second_refresh = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": old_refresh_token
        },
    )

    assert second_refresh.status_code == 401


def test_invalid_refresh_token():
    response = client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": "invalid-refresh-token"
        },
    )

    assert response.status_code == 401


def test_logout():
    email = unique_email()

    register_user(email)

    login_response = login_user(email)

    access_token = login_response.json()["access_token"]
    refresh_token = login_response.json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/logout",
        json={
            "refresh_token": refresh_token
        },
        headers={
            "Authorization": f"Bearer {access_token}"
        },
    )

    assert response.status_code == 200

    assert response.json()["message"] == "Successfully logged out"


def test_password_reset_request():
    email = unique_email()

    register_user(email)

    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={
            "email": email
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == (
        "Password reset request created"
    )

    assert "reset_token" in data


def test_password_reset_unknown_email():
    response = client.post(
        "/api/v1/auth/password-reset/request",
        json={
            "email": "doesnotexist@example.com"
        },
    )

    assert response.status_code == 200

    assert response.json()["message"] == (
        "If the email exists, a password reset request has been created"
    )


def test_super_admin_rbac():
    db = SessionLocal()

    try:
        from models.user import User
        from core.enums import AccountStatus, UserRole
        from core.security import hash_password

        email = unique_email()

        admin = User(
            full_name="Super Admin",
            email=email,
            password_hash=hash_password(
                "AdminPassword@123"
            ),
            role=UserRole.SUPER_ADMIN,
            status=AccountStatus.ACTIVE,
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        admin_id = admin.id

    finally:
        db.close()

    login_response = login_user(
        email,
        "AdminPassword@123",
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    worker_response = register_user()

    worker_id = worker_response.json()["id"]

    response = client.patch(
        f"/api/v1/auth/users/{worker_id}/deactivate",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Inactive"


def test_worker_cannot_deactivate_user():
    email = unique_email()

    register_user(email)

    login_response = login_user(email)

    token = login_response.json()["access_token"]

    another_user = register_user()

    user_id = another_user.json()["id"]

    response = client.patch(
        f"/api/v1/auth/users/{user_id}/deactivate",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 403


def test_inactive_user_cannot_login():
    email = unique_email()

    register_response = register_user(email)

    user_id = register_response.json()["id"]

    db = SessionLocal()

    try:
        from models.user import User
        from core.enums import AccountStatus

        user = db.get(User, user_id)

        user.status = AccountStatus.INACTIVE

        db.commit()

    finally:
        db.close()

    response = login_user(email)

    assert response.status_code == 403


def test_inactive_user_cannot_access_me():
    email = unique_email()

    register_user(email)

    login_response = login_user(email)

    token = login_response.json()["access_token"]

    db = SessionLocal()

    try:
        from models.user import User
        from core.enums import AccountStatus

        user = db.query(User).filter(
            User.email == email
        ).first()

        user.status = AccountStatus.INACTIVE

        db.commit()

    finally:
        db.close()

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 403