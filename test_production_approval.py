import os
from datetime import date, timedelta
from uuid import uuid4

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://postgres:Srik8499@localhost:5433/"
    "manufacturing_production_quality_test"
)

from fastapi.testclient import TestClient
from sqlalchemy import select

from main import app
from database import SessionLocal
from models.user import User
from core.enums import AccountStatus, UserRole
from core.security import hash_password


client = TestClient(app)


PASSWORD = "Test@12345"
ADMIN_EMAIL = "admin@manufacturing.com"
ADMIN_PASSWORD = "Admin@12345"


def unique_email(prefix):
    return f"{prefix}_{uuid4().hex[:8]}@example.com"


def register_user(
    email,
    full_name,
):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": full_name,
            "email": email,
            "password": PASSWORD,
        },
    )

    assert response.status_code in (200, 201), response.text

    return response.json()


def login_user(
    email,
    password=PASSWORD,
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


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}",
    }


def create_worker():
    email = unique_email("worker")

    register_user(
        email=email,
        full_name="Test Worker",
    )

    token = login_user(email)

    return {
        "email": email,
        "token": token,
    }


def create_role_user(
    role,
    prefix,
    full_name,
):
    email = unique_email(prefix)

    db = SessionLocal()

    try:
        existing_user = db.scalar(
            select(User).where(
                User.email == email
            )
        )

        if existing_user:
            user = existing_user
        else:
            user = User(
                full_name=full_name,
                email=email,
                password_hash=hash_password(
                    PASSWORD
                ),
                role=role,
                status=AccountStatus.ACTIVE,
            )

            db.add(user)
            db.commit()
            db.refresh(user)

        user_id = user.id

    finally:
        db.close()

    token = login_user(email)

    return {
        "id": user_id,
        "email": email,
        "token": token,
    }


def create_production_manager():
    return create_role_user(
        role=UserRole.PRODUCTION_MANAGER,
        prefix="production_manager",
        full_name="Test Production Manager",
    )


def create_production_supervisor():
    return create_role_user(
        role=UserRole.PRODUCTION_SUPERVISOR,
        prefix="production_supervisor",
        full_name="Test Production Supervisor",
    )


def create_quality_manager():
    return create_role_user(
        role=UserRole.QUALITY_MANAGER,
        prefix="quality_manager",
        full_name="Test Quality Manager",
    )


def create_store_manager():
    return create_role_user(
        role=UserRole.STORE_MANAGER,
        prefix="store_manager",
        full_name="Test Store Manager",
    )


def get_current_user(token):
    response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers(token),
    )

    assert response.status_code == 200, response.text

    return response.json()

def get_seeded_admin_token():
    db = SessionLocal()

    try:
        admin = db.scalar(
            select(User).where(
                User.email == ADMIN_EMAIL
            )
        )

        if not admin:
            admin = User(
                full_name="Manufacturing Super Admin",
                email=ADMIN_EMAIL,
                password_hash=hash_password(
                    ADMIN_PASSWORD
                ),
                role=UserRole.SUPER_ADMIN,
                status=AccountStatus.ACTIVE,
            )

            db.add(admin)
            db.commit()
            db.refresh(admin)

        else:
            admin.password_hash = hash_password(
                ADMIN_PASSWORD
            )
            admin.role = UserRole.SUPER_ADMIN
            admin.status = AccountStatus.ACTIVE

            db.commit()

    finally:
        db.close()

    token = login_user(
        ADMIN_EMAIL,
        ADMIN_PASSWORD,
    )

    return token
def create_plant(admin_token):
    payload = {
        "name": f"Workflow Plant {uuid4().hex[:8]}",
        "code": f"WP-{uuid4().hex[:8].upper()}",
        "address": "Workflow Test Address",
        "city": "Tirupati",
        "state": "Andhra Pradesh",
        "production_capacity": 1000,
    }

    response = client.post(
        "/api/v1/plants",
        json=payload,
        headers=auth_headers(admin_token),
    )

    assert response.status_code in (200, 201), response.text

    return response.json()

def create_production_line(
    admin_token,
    plant_id,
):
    payload = {
        "name": f"Workflow Line {uuid4().hex[:8]}",
        "code": f"WL-{uuid4().hex[:8].upper()}",
        "plant_id": plant_id,
        "production_capacity": 500,
    }

    response = client.post(
        "/api/v1/production-lines",
        json=payload,
        headers=auth_headers(admin_token),
    )

    assert response.status_code in (200, 201), response.text

    return response.json()

def create_product(admin_token):
    unique_value = uuid4().hex[:8].upper()

    payload = {
        "name": f"Workflow Product {unique_value}",
        "code": f"WP-{unique_value}",
        "description": "Workflow test product",
        "category": "Finished Goods",
        "sku": f"SKU-{unique_value}",
        "unit_of_measurement": "PCS",
        "standard_production_time": 60,
    }

    response = client.post(
        "/api/v1/products",
        json=payload,
        headers=auth_headers(admin_token),
    )

    assert response.status_code in (200, 201), response.text

    return response.json()

def create_production_order(
    manager_token,
    product_id,
    production_line_id,
    supervisor_id,
):
    payload = {
        "order_number": (
            f"WO-{uuid4().hex[:10].upper()}"
        ),
        "product_id": product_id,
        "quantity": 100,
        "target_date": (
            date.today() + timedelta(days=7)
        ).isoformat(),
        "production_line_id": production_line_id,
        "priority": "Medium",
        "supervisor_id": supervisor_id,
    }

    response = client.post(
        "/api/v1/production-orders",
        json=payload,
        headers=auth_headers(manager_token),
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_workflow_order():
    admin_token = get_seeded_admin_token()

    manager = create_production_manager()
    supervisor = create_production_supervisor()

    manager_user = get_current_user(
        manager["token"]
    )

    supervisor_user = get_current_user(
        supervisor["token"]
    )

    plant = create_plant(admin_token)

    line = create_production_line(
        admin_token,
        plant["id"],
    )

    product = create_product(
        admin_token,
    )

    order = create_production_order(
        manager_token=manager["token"],
        product_id=product["id"],
        production_line_id=line["id"],
        supervisor_id=supervisor_user["id"],
    )

    return {
        "admin_token": admin_token,
        "manager": manager,
        "manager_user": manager_user,
        "supervisor": supervisor,
        "supervisor_user": supervisor_user,
        "plant": plant,
        "line": line,
        "product": product,
        "order": order,
    }


def prepare_until_supervisor_approved(data):
    order_id = data["order"]["id"]

    response = client.post(
        f"/api/v1/production-orders/{order_id}/workflow/"
        "supervisor-approve",
        json={
            "comment": "Supervisor approved",
        },
        headers=auth_headers(
            data["supervisor"]["token"]
        ),
    )

    assert response.status_code == 200, response.text

    return response.json()


def prepare_until_material_checked(data):
    prepare_until_supervisor_approved(data)

    store_manager = create_store_manager()

    order_id = data["order"]["id"]

    response = client.post(
        f"/api/v1/production-orders/{order_id}/workflow/"
        "material-check",
        json={
            "comment": "Materials available",
        },
        headers=auth_headers(
            store_manager["token"]
        ),
    )

    assert response.status_code == 200, response.text

    data["store_manager"] = store_manager

    return response.json()


def prepare_until_production_started(data):
    prepare_until_material_checked(data)

    order_id = data["order"]["id"]

    response = client.post(
        f"/api/v1/production-orders/{order_id}/workflow/start",
        headers=auth_headers(
            data["manager"]["token"]
        ),
    )

    assert response.status_code == 200, response.text

    return response.json()


def prepare_until_quality_inspected(data):
    prepare_until_production_started(data)

    quality_manager = create_quality_manager()

    order_id = data["order"]["id"]

    response = client.post(
        f"/api/v1/production-orders/{order_id}/workflow/"
        "quality-inspection",
        json={
            "comment": "Quality inspection passed",
        },
        headers=auth_headers(
            quality_manager["token"]
        ),
    )

    assert response.status_code == 200, response.text

    data["quality_manager"] = quality_manager

    return response.json()


def prepare_until_manager_approval(data):
    prepare_until_quality_inspected(data)

    order_id = data["order"]["id"]

    response = client.post(
        f"/api/v1/production-orders/{order_id}/workflow/complete",
        headers=auth_headers(
            data["manager"]["token"]
        ),
    )

    assert response.status_code == 200, response.text

    return response.json()


def test_workflow_created_on_first_access():
    data = create_workflow_order()

    order_id = data["order"]["id"]

    response = client.get(
        f"/api/v1/production-orders/{order_id}/workflow",
        headers=auth_headers(
            data["manager"]["token"]
        ),
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert body["production_order_id"] == order_id

    assert body["workflow_status"] == (
        "Pending Supervisor Review"
    )


def test_supervisor_can_approve_order():
    data = create_workflow_order()

    body = prepare_until_supervisor_approved(
        data
    )

    assert body["workflow_status"] == (
        "Supervisor Approved"
    )

    assert body["supervisor_id"] == (
        data["supervisor_user"]["id"]
    )

    order_response = client.get(
        f"/api/v1/production-orders/"
        f"{data['order']['id']}",
        headers=auth_headers(
            data["manager"]["token"]
        ),
    )

    assert order_response.status_code == 200

    assert order_response.json()["status"] == "Scheduled"


def test_worker_cannot_approve_supervisor_review():
    data = create_workflow_order()

    worker = create_worker()

    order_id = data["order"]["id"]

    response = client.post(
        f"/api/v1/production-orders/{order_id}/workflow/"
        "supervisor-approve",
        json={
            "comment": "Unauthorized",
        },
        headers=auth_headers(
            worker["token"]
        ),
    )

    assert response.status_code == 403


def test_invalid_material_check_before_supervisor_approval():
    data = create_workflow_order()

    store_manager = create_store_manager()

    order_id = data["order"]["id"]

    response = client.post(
        f"/api/v1/production-orders/{order_id}/workflow/"
        "material-check",
        json={
            "comment": "Checking material",
        },
        headers=auth_headers(
            store_manager["token"]
        ),
    )

    assert response.status_code == 400

    assert "Invalid workflow transition" in (
        response.json()["detail"]
    )


def test_material_check_after_supervisor_approval():
    data = create_workflow_order()

    body = prepare_until_material_checked(
        data
    )

    assert body["workflow_status"] == (
        "Material Checked"
    )


def test_cannot_start_before_material_check():
    data = create_workflow_order()

    order_id = data["order"]["id"]

    response = client.post(
        f"/api/v1/production-orders/{order_id}/workflow/start",
        headers=auth_headers(
            data["manager"]["token"]
        ),
    )

    assert response.status_code == 400

    assert "Invalid workflow transition" in (
        response.json()["detail"]
    )


def test_production_can_start_after_material_check():
    data = create_workflow_order()

    body = prepare_until_production_started(
        data
    )

    assert body["workflow_status"] == (
        "Production Started"
    )

    order_response = client.get(
        f"/api/v1/production-orders/"
        f"{data['order']['id']}",
        headers=auth_headers(
            data["manager"]["token"]
        ),
    )

    assert order_response.status_code == 200

    assert order_response.json()["status"] == (
        "In Progress"
    )


def test_cannot_complete_before_quality_inspection():
    data = create_workflow_order()

    prepare_until_production_started(
        data
    )

    order_id = data["order"]["id"]

    response = client.post(
        f"/api/v1/production-orders/{order_id}/workflow/complete",
        headers=auth_headers(
            data["manager"]["token"]
        ),
    )

    assert response.status_code == 400

    assert "Invalid workflow transition" in (
        response.json()["detail"]
    )


def test_quality_inspection_moves_workflow_forward():
    data = create_workflow_order()

    body = prepare_until_quality_inspected(
        data
    )

    assert body["workflow_status"] == (
        "Quality Inspected"
    )

    assert body["quality_inspected_by_id"] == (
        get_current_user(
            data["quality_manager"]["token"]
        )["id"]
    )


def test_quality_inspection_requires_quality_role():
    data = create_workflow_order()

    prepare_until_production_started(
        data
    )

    order_id = data["order"]["id"]

    response = client.post(
        f"/api/v1/production-orders/{order_id}/workflow/"
        "quality-inspection",
        json={
            "comment": "Unauthorized inspection",
        },
        headers=auth_headers(
            data["manager"]["token"]
        ),
    )

    assert response.status_code == 403


def test_complete_production_after_quality_inspection():
    data = create_workflow_order()

    body = prepare_until_manager_approval(
        data
    )

    assert body["workflow_status"] == (
        "Pending Manager Approval"
    )

    order_response = client.get(
        f"/api/v1/production-orders/"
        f"{data['order']['id']}",
        headers=auth_headers(
            data["manager"]["token"]
        ),
    )

    assert order_response.status_code == 200

    assert order_response.json()["status"] == (
        "Completed"
    )


def test_manager_can_approve_completed_production():
    data = create_workflow_order()

    prepare_until_manager_approval(
        data
    )

    order_id = data["order"]["id"]

    response = client.post(
        f"/api/v1/production-orders/{order_id}/workflow/"
        "manager-approve",
        json={
            "comment": "Final production approved",
        },
        headers=auth_headers(
            data["manager"]["token"]
        ),
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert body["workflow_status"] == (
        "Manager Approved"
    )

    assert body["manager_id"] == (
        data["manager_user"]["id"]
    )


def test_worker_cannot_manager_approve():
    data = create_workflow_order()

    worker = create_worker()

    order_id = data["order"]["id"]

    response = client.post(
        f"/api/v1/production-orders/{order_id}/workflow/"
        "manager-approve",
        json={},
        headers=auth_headers(
            worker["token"]
        ),
    )

    assert response.status_code == 403


def test_manager_cannot_approve_before_completion():
    data = create_workflow_order()

    order_id = data["order"]["id"]

    response = client.post(
        f"/api/v1/production-orders/{order_id}/workflow/"
        "manager-approve",
        json={
            "comment": "Premature approval",
        },
        headers=auth_headers(
            data["manager"]["token"]
        ),
    )

    assert response.status_code == 400

    assert "Invalid workflow transition" in (
        response.json()["detail"]
    )


def test_supervisor_can_reject_order():
    data = create_workflow_order()

    order_id = data["order"]["id"]

    response = client.post(
        f"/api/v1/production-orders/{order_id}/workflow/"
        "supervisor-reject",
        json={
            "comment": "Production information incomplete",
        },
        headers=auth_headers(
            data["supervisor"]["token"]
        ),
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert body["workflow_status"] == (
        "Supervisor Rejected"
    )

    assert body["supervisor_comment"] == (
        "Production information incomplete"
    )


def test_manager_can_reject_after_completion():
    data = create_workflow_order()

    prepare_until_manager_approval(
        data
    )

    order_id = data["order"]["id"]

    response = client.post(
        f"/api/v1/production-orders/{order_id}/workflow/"
        "manager-reject",
        json={
            "comment": "Final approval rejected",
        },
        headers=auth_headers(
            data["manager"]["token"]
        ),
    )

    assert response.status_code == 200, response.text

    assert response.json()["workflow_status"] == (
        "Manager Rejected"
    )


def test_invalid_transition_after_supervisor_approval():
    data = create_workflow_order()

    prepare_until_supervisor_approved(
        data
    )

    order_id = data["order"]["id"]

    response = client.post(
        f"/api/v1/production-orders/{order_id}/workflow/"
        "supervisor-approve",
        json={},
        headers=auth_headers(
            data["supervisor"]["token"]
        ),
    )

    assert response.status_code == 400

    assert "Invalid workflow transition" in (
        response.json()["detail"]
    )


def test_workflow_requires_authentication():
    data = create_workflow_order()

    order_id = data["order"]["id"]

    response = client.get(
        f"/api/v1/production-orders/{order_id}/workflow"
    )

    assert response.status_code == 401


def test_workflow_nonexistent_order_returns_404():
    admin_token = get_seeded_admin_token()

    response = client.get(
        "/api/v1/production-orders/999999/workflow",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 404

    assert response.json()["detail"] == (
        "Production order not found"
    )