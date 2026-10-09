import os
from datetime import date, timedelta
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


def reset_database():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        db.execute(
            text(
                """
                TRUNCATE TABLE
                    production_orders,
                    machines,
                    bom_items,
                    boms,
                    material_transactions,
                    raw_materials,
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


reset_database()


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

        return user.id
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


def create_production_manager():
    email = f"manager-{uuid4().hex[:8]}@test.com"

    create_user(
        email,
        UserRole.PRODUCTION_MANAGER,
    )

    return login(email)


def create_supervisor():
    email = f"supervisor-{uuid4().hex[:8]}@test.com"

    user_id = create_user(
        email,
        UserRole.PRODUCTION_SUPERVISOR,
    )

    token = login(email)

    return {
        "id": user_id,
        "token": token,
    }


def create_plant(token: str):
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
            "production_capacity": 5000,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_production_line(token: str):
    plant = create_plant(token)

    line_code = f"LINE-{uuid4().hex[:8]}"

    response = client.post(
        "/api/v1/production-lines",
        json={
            "name": "Assembly Line",
            "code": line_code,
            "production_capacity": 1000,
            "plant_id": plant["id"],
            "status": "Active",
        },
        headers=auth_header(token),
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_product(token: str):
    sku = f"SKU-{uuid4().hex[:8]}"

    response = client.post(
        "/api/v1/products",
        json={
            "name": "Test Product",
            "category": "Finished Goods",
            "sku": sku,
            "unit_of_measurement": "Piece",
            "status": "Active",
            "standard_production_time": 60,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_production_order(
    token: str,
    product_id: int,
    production_line_id: int,
    supervisor_id: int,
    order_number: str | None = None,
    quantity: int = 1000,
    priority: str = "Medium",
):
    if order_number is None:
        order_number = f"PO-{uuid4().hex[:8]}"

    response = client.post(
        "/api/v1/production-orders",
        json={
            "order_number": order_number,
            "product_id": product_id,
            "quantity": quantity,
            "target_date": str(
                date.today() + timedelta(days=30)
            ),
            "production_line_id": production_line_id,
            "priority": priority,
            "supervisor_id": supervisor_id,
        },
        headers=auth_header(token),
    )

    assert response.status_code == 201, response.text

    return response.json()


def create_test_order():
    admin_token = create_admin()

    plant = create_plant(admin_token)

    line_response = client.post(
        "/api/v1/production-lines",
        json={
            "name": "Assembly Line",
            "code": f"LINE-{uuid4().hex[:8]}",
            "production_capacity": 1000,
            "plant_id": plant["id"],
            "status": "Active",
        },
        headers=auth_header(admin_token),
    )

    assert line_response.status_code == 201, line_response.text

    line = line_response.json()

    product = create_product(admin_token)
    supervisor = create_supervisor()

    order = create_production_order(
        admin_token,
        product["id"],
        line["id"],
        supervisor["id"],
    )

    return {
        "admin_token": admin_token,
        "line": line,
        "product": product,
        "supervisor": supervisor,
        "order": order,
    }


def test_create_production_order():
    data = create_test_order()

    order = data["order"]

    assert order["order_number"].startswith("PO-")
    assert order["product_id"] == data["product"]["id"]
    assert order["production_line_id"] == data["line"]["id"]
    assert order["supervisor_id"] == data["supervisor"]["id"]
    assert order["quantity"] == 1000
    assert order["priority"] == "Medium"
    assert order["status"] == "Draft"


def test_create_production_order_without_authentication():
    admin_token = create_admin()

    product = create_product(admin_token)
    line = create_production_line(admin_token)
    supervisor = create_supervisor()

    response = client.post(
        "/api/v1/production-orders",
        json={
            "order_number": f"PO-{uuid4().hex[:8]}",
            "product_id": product["id"],
            "quantity": 100,
            "target_date": str(
                date.today() + timedelta(days=10)
            ),
            "production_line_id": line["id"],
            "priority": "High",
            "supervisor_id": supervisor["id"],
        },
    )

    assert response.status_code == 401


def test_worker_cannot_create_production_order():
    admin_token = create_admin()

    product = create_product(admin_token)
    line = create_production_line(admin_token)
    supervisor = create_supervisor()

    worker_token = create_worker()

    response = client.post(
        "/api/v1/production-orders",
        json={
            "order_number": f"PO-{uuid4().hex[:8]}",
            "product_id": product["id"],
            "quantity": 100,
            "target_date": str(
                date.today() + timedelta(days=10)
            ),
            "production_line_id": line["id"],
            "priority": "High",
            "supervisor_id": supervisor["id"],
        },
        headers=auth_header(worker_token),
    )

    assert response.status_code == 403


def test_production_manager_can_create_order():
    admin_token = create_admin()

    product = create_product(admin_token)
    line = create_production_line(admin_token)
    supervisor = create_supervisor()

    manager_token = create_production_manager()

    response = client.post(
        "/api/v1/production-orders",
        json={
            "order_number": f"PO-{uuid4().hex[:8]}",
            "product_id": product["id"],
            "quantity": 500,
            "target_date": str(
                date.today() + timedelta(days=15)
            ),
            "production_line_id": line["id"],
            "priority": "High",
            "supervisor_id": supervisor["id"],
        },
        headers=auth_header(manager_token),
    )

    assert response.status_code == 201, response.text

    body = response.json()

    assert body["product_id"] == product["id"]
    assert body["production_line_id"] == line["id"]
    assert body["supervisor_id"] == supervisor["id"]
    assert body["quantity"] == 500
    assert body["priority"] == "High"
    assert body["status"] == "Draft"


def test_duplicate_order_number_rejected():
    data = create_test_order()

    response = client.post(
        "/api/v1/production-orders",
        json={
            "order_number": data["order"]["order_number"],
            "product_id": data["product"]["id"],
            "quantity": 500,
            "target_date": str(
                date.today() + timedelta(days=20)
            ),
            "production_line_id": data["line"]["id"],
            "priority": "Low",
            "supervisor_id": data["supervisor"]["id"],
        },
        headers=auth_header(data["admin_token"]),
    )

    assert response.status_code == 409


def test_invalid_product_rejected():
    data = create_test_order()

    response = client.post(
        "/api/v1/production-orders",
        json={
            "order_number": f"PO-{uuid4().hex[:8]}",
            "product_id": 999999,
            "quantity": 100,
            "target_date": str(
                date.today() + timedelta(days=10)
            ),
            "production_line_id": data["line"]["id"],
            "priority": "Medium",
            "supervisor_id": data["supervisor"]["id"],
        },
        headers=auth_header(data["admin_token"]),
    )

    assert response.status_code == 404


def test_invalid_production_line_rejected():
    data = create_test_order()

    response = client.post(
        "/api/v1/production-orders",
        json={
            "order_number": f"PO-{uuid4().hex[:8]}",
            "product_id": data["product"]["id"],
            "quantity": 100,
            "target_date": str(
                date.today() + timedelta(days=10)
            ),
            "production_line_id": 999999,
            "priority": "Medium",
            "supervisor_id": data["supervisor"]["id"],
        },
        headers=auth_header(data["admin_token"]),
    )

    assert response.status_code == 404


def test_invalid_supervisor_rejected():
    data = create_test_order()

    response = client.post(
        "/api/v1/production-orders",
        json={
            "order_number": f"PO-{uuid4().hex[:8]}",
            "product_id": data["product"]["id"],
            "quantity": 100,
            "target_date": str(
                date.today() + timedelta(days=10)
            ),
            "production_line_id": data["line"]["id"],
            "priority": "Medium",
            "supervisor_id": 999999,
        },
        headers=auth_header(data["admin_token"]),
    )

    assert response.status_code == 404


def test_negative_quantity_rejected():
    data = create_test_order()

    response = client.post(
        "/api/v1/production-orders",
        json={
            "order_number": f"PO-{uuid4().hex[:8]}",
            "product_id": data["product"]["id"],
            "quantity": -100,
            "target_date": str(
                date.today() + timedelta(days=10)
            ),
            "production_line_id": data["line"]["id"],
            "priority": "Medium",
            "supervisor_id": data["supervisor"]["id"],
        },
        headers=auth_header(data["admin_token"]),
    )

    assert response.status_code == 422


def test_zero_quantity_rejected():
    data = create_test_order()

    response = client.post(
        "/api/v1/production-orders",
        json={
            "order_number": f"PO-{uuid4().hex[:8]}",
            "product_id": data["product"]["id"],
            "quantity": 0,
            "target_date": str(
                date.today() + timedelta(days=10)
            ),
            "production_line_id": data["line"]["id"],
            "priority": "Medium",
            "supervisor_id": data["supervisor"]["id"],
        },
        headers=auth_header(data["admin_token"]),
    )

    assert response.status_code == 422


def test_get_production_order():
    data = create_test_order()

    response = client.get(
        f"/api/v1/production-orders/{data['order']['id']}",
        headers=auth_header(data["admin_token"]),
    )

    assert response.status_code == 200
    assert response.json()["id"] == data["order"]["id"]


def test_get_nonexistent_production_order():
    token = create_admin()

    response = client.get(
        "/api/v1/production-orders/999999",
        headers=auth_header(token),
    )

    assert response.status_code == 404


def test_list_production_orders():
    data = create_test_order()

    response = client.get(
        "/api/v1/production-orders",
        headers=auth_header(data["admin_token"]),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] >= 1
    assert body["page"] == 1
    assert body["page_size"] == 10
    assert len(body["items"]) >= 1


def test_search_production_orders():
    data = create_test_order()

    order_number = data["order"]["order_number"]

    response = client.get(
        "/api/v1/production-orders",
        params={
            "search": order_number,
        },
        headers=auth_header(data["admin_token"]),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert body["items"][0]["order_number"] == order_number


def test_filter_by_product():
    data = create_test_order()

    response = client.get(
        "/api/v1/production-orders",
        params={
            "product_id": data["product"]["id"],
        },
        headers=auth_header(data["admin_token"]),
    )

    assert response.status_code == 200

    for item in response.json()["items"]:
        assert item["product_id"] == data["product"]["id"]


def test_filter_by_production_line():
    data = create_test_order()

    response = client.get(
        "/api/v1/production-orders",
        params={
            "production_line_id": data["line"]["id"],
        },
        headers=auth_header(data["admin_token"]),
    )

    assert response.status_code == 200

    for item in response.json()["items"]:
        assert item["production_line_id"] == data["line"]["id"]


def test_filter_by_supervisor():
    data = create_test_order()

    response = client.get(
        "/api/v1/production-orders",
        params={
            "supervisor_id": data["supervisor"]["id"],
        },
        headers=auth_header(data["admin_token"]),
    )

    assert response.status_code == 200

    for item in response.json()["items"]:
        assert item["supervisor_id"] == data["supervisor"]["id"]


def test_filter_by_priority():
    data = create_test_order()

    response = client.put(
        f"/api/v1/production-orders/{data['order']['id']}",
        json={
            "priority": "Urgent",
        },
        headers=auth_header(data["admin_token"]),
    )

    assert response.status_code == 200

    response = client.get(
        "/api/v1/production-orders",
        params={
            "priority": "Urgent",
        },
        headers=auth_header(data["admin_token"]),
    )

    assert response.status_code == 200
    assert response.json()["total"] >= 1

    for item in response.json()["items"]:
        assert item["priority"] == "Urgent"


def test_filter_by_status():
    data = create_test_order()

    response = client.get(
        "/api/v1/production-orders",
        params={
            "status": "Draft",
        },
        headers=auth_header(data["admin_token"]),
    )

    assert response.status_code == 200

    for item in response.json()["items"]:
        assert item["status"] == "Draft"


def test_pagination():
    data = create_test_order()

    for _ in range(4):
        create_production_order(
            data["admin_token"],
            data["product"]["id"],
            data["line"]["id"],
            data["supervisor"]["id"],
        )

    response = client.get(
        "/api/v1/production-orders",
        params={
            "page": 1,
            "page_size": 2,
        },
        headers=auth_header(data["admin_token"]),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["page"] == 1
    assert body["page_size"] == 2
    assert len(body["items"]) == 2
    assert body["total"] >= 5


def test_update_production_order():
    data = create_test_order()

    response = client.put(
        f"/api/v1/production-orders/{data['order']['id']}",
        json={
            "quantity": 2000,
            "priority": "High",
        },
        headers=auth_header(data["admin_token"]),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["quantity"] == 2000
    assert body["priority"] == "High"


def test_update_production_order_product():
    data = create_test_order()

    second_product = create_product(
        data["admin_token"]
    )

    response = client.put(
        f"/api/v1/production-orders/{data['order']['id']}",
        json={
            "product_id": second_product["id"],
        },
        headers=auth_header(data["admin_token"]),
    )

    assert response.status_code == 200
    assert response.json()["product_id"] == second_product["id"]


def test_update_production_order_line():
    data = create_test_order()

    second_line = create_production_line(
        data["admin_token"]
    )

    response = client.put(
        f"/api/v1/production-orders/{data['order']['id']}",
        json={
            "production_line_id": second_line["id"],
        },
        headers=auth_header(data["admin_token"]),
    )

    assert response.status_code == 200
    assert response.json()["production_line_id"] == second_line["id"]


def test_update_production_order_supervisor():
    data = create_test_order()

    second_supervisor = create_supervisor()

    response = client.put(
        f"/api/v1/production-orders/{data['order']['id']}",
        json={
            "supervisor_id": second_supervisor["id"],
        },
        headers=auth_header(data["admin_token"]),
    )

    assert response.status_code == 200
    assert response.json()["supervisor_id"] == second_supervisor["id"]


def test_worker_cannot_update_production_order():
    data = create_test_order()

    worker_token = create_worker()

    response = client.put(
        f"/api/v1/production-orders/{data['order']['id']}",
        json={
            "quantity": 5000,
        },
        headers=auth_header(worker_token),
    )

    assert response.status_code == 403


def test_draft_to_scheduled():
    data = create_test_order()

    response = client.patch(
        f"/api/v1/production-orders/{data['order']['id']}/status",
        json={
            "status": "Scheduled",
        },
        headers=auth_header(data["admin_token"]),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Scheduled"


def test_scheduled_to_in_progress():
    data = create_test_order()

    client.patch(
        f"/api/v1/production-orders/{data['order']['id']}/status",
        json={
            "status": "Scheduled"
        },
        headers=auth_header(data["admin_token"]),
    )

    response = client.patch(
        f"/api/v1/production-orders/{data['order']['id']}/status",
        json={
            "status": "In Progress"
        },
        headers=auth_header(data["admin_token"]),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "In Progress"


def test_in_progress_to_paused():
    data = create_test_order()

    client.patch(
        f"/api/v1/production-orders/{data['order']['id']}/status",
        json={
            "status": "Scheduled"
        },
        headers=auth_header(data["admin_token"]),
    )

    client.patch(
        f"/api/v1/production-orders/{data['order']['id']}/status",
        json={
            "status": "In Progress"
        },
        headers=auth_header(data["admin_token"]),
    )

    response = client.patch(
        f"/api/v1/production-orders/{data['order']['id']}/status",
        json={
            "status": "Paused"
        },
        headers=auth_header(data["admin_token"]),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Paused"


def test_paused_to_in_progress():
    data = create_test_order()

    order_id = data["order"]["id"]
    token = data["admin_token"]

    client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "Scheduled"
        },
        headers=auth_header(token),
    )

    client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "In Progress"
        },
        headers=auth_header(token),
    )

    client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "Paused"
        },
        headers=auth_header(token),
    )

    response = client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "In Progress"
        },
        headers=auth_header(token),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "In Progress"


def test_in_progress_to_completed():
    data = create_test_order()

    order_id = data["order"]["id"]
    token = data["admin_token"]

    client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "Scheduled"
        },
        headers=auth_header(token),
    )

    client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "In Progress"
        },
        headers=auth_header(token),
    )

    response = client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "Completed"
        },
        headers=auth_header(token),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Completed"


def test_draft_to_cancelled():
    data = create_test_order()

    response = client.patch(
        f"/api/v1/production-orders/{data['order']['id']}/status",
        json={
            "status": "Cancelled"
        },
        headers=auth_header(data["admin_token"]),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Cancelled"


def test_scheduled_to_cancelled():
    data = create_test_order()

    order_id = data["order"]["id"]
    token = data["admin_token"]

    client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "Scheduled"
        },
        headers=auth_header(token),
    )

    response = client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "Cancelled"
        },
        headers=auth_header(token),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Cancelled"


def test_in_progress_to_cancelled():
    data = create_test_order()

    order_id = data["order"]["id"]
    token = data["admin_token"]

    client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "Scheduled"
        },
        headers=auth_header(token),
    )

    client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "In Progress"
        },
        headers=auth_header(token),
    )

    response = client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "Cancelled"
        },
        headers=auth_header(token),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Cancelled"


def test_paused_to_cancelled():
    data = create_test_order()

    order_id = data["order"]["id"]
    token = data["admin_token"]

    client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "Scheduled"
        },
        headers=auth_header(token),
    )

    client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "In Progress"
        },
        headers=auth_header(token),
    )

    client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "Paused"
        },
        headers=auth_header(token),
    )

    response = client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "Cancelled"
        },
        headers=auth_header(token),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Cancelled"


def test_invalid_draft_to_completed():
    data = create_test_order()

    response = client.patch(
        f"/api/v1/production-orders/{data['order']['id']}/status",
        json={
            "status": "Completed"
        },
        headers=auth_header(data["admin_token"]),
    )

    assert response.status_code == 400


def test_invalid_draft_to_in_progress():
    data = create_test_order()

    response = client.patch(
        f"/api/v1/production-orders/{data['order']['id']}/status",
        json={
            "status": "In Progress"
        },
        headers=auth_header(data["admin_token"]),
    )

    assert response.status_code == 400


def test_invalid_scheduled_to_completed():
    data = create_test_order()

    order_id = data["order"]["id"]
    token = data["admin_token"]

    client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "Scheduled"
        },
        headers=auth_header(token),
    )

    response = client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "Completed"
        },
        headers=auth_header(token),
    )

    assert response.status_code == 400


def test_invalid_scheduled_to_paused():
    data = create_test_order()

    order_id = data["order"]["id"]
    token = data["admin_token"]

    client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "Scheduled"
        },
        headers=auth_header(token),
    )

    response = client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "Paused"
        },
        headers=auth_header(token),
    )

    assert response.status_code == 400


def test_completed_order_cannot_change_status():
    data = create_test_order()

    order_id = data["order"]["id"]
    token = data["admin_token"]

    client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "Scheduled"
        },
        headers=auth_header(token),
    )

    client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "In Progress"
        },
        headers=auth_header(token),
    )

    client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "Completed"
        },
        headers=auth_header(token),
    )

    response = client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "In Progress"
        },
        headers=auth_header(token),
    )

    assert response.status_code == 400


def test_cancelled_order_cannot_change_status():
    data = create_test_order()

    order_id = data["order"]["id"]
    token = data["admin_token"]

    client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "Cancelled"
        },
        headers=auth_header(token),
    )

    response = client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "Scheduled"
        },
        headers=auth_header(token),
    )

    assert response.status_code == 400


def test_completed_order_cannot_be_updated():
    data = create_test_order()

    order_id = data["order"]["id"]
    token = data["admin_token"]

    client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "Scheduled"
        },
        headers=auth_header(token),
    )

    client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "In Progress"
        },
        headers=auth_header(token),
    )

    client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "Completed"
        },
        headers=auth_header(token),
    )

    response = client.put(
        f"/api/v1/production-orders/{order_id}",
        json={
            "quantity": 5000
        },
        headers=auth_header(token),
    )

    assert response.status_code == 400


def test_cancelled_order_cannot_be_updated():
    data = create_test_order()

    order_id = data["order"]["id"]
    token = data["admin_token"]

    client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "Cancelled"
        },
        headers=auth_header(token),
    )

    response = client.put(
        f"/api/v1/production-orders/{order_id}",
        json={
            "quantity": 5000
        },
        headers=auth_header(token),
    )

    assert response.status_code == 400


def test_worker_can_view_production_order():
    data = create_test_order()

    worker_token = create_worker()

    response = client.get(
        f"/api/v1/production-orders/{data['order']['id']}",
        headers=auth_header(worker_token),
    )

    assert response.status_code == 200


def test_worker_can_list_production_orders():
    data = create_test_order()

    worker_token = create_worker()

    response = client.get(
        "/api/v1/production-orders",
        headers=auth_header(worker_token),
    )

    assert response.status_code == 200


def test_production_order_list_requires_authentication():
    response = client.get(
        "/api/v1/production-orders"
    )

    assert response.status_code == 401


def test_worker_cannot_update_status():
    data = create_test_order()

    worker_token = create_worker()

    response = client.patch(
        f"/api/v1/production-orders/{data['order']['id']}/status",
        json={
            "status": "Scheduled"
        },
        headers=auth_header(worker_token),
    )

    assert response.status_code == 403


def test_worker_cannot_delete_production_order():
    data = create_test_order()

    worker_token = create_worker()

    response = client.delete(
        f"/api/v1/production-orders/{data['order']['id']}",
        headers=auth_header(worker_token),
    )

    assert response.status_code == 403


def test_non_draft_order_cannot_be_deleted():
    data = create_test_order()

    order_id = data["order"]["id"]
    token = data["admin_token"]

    client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "Scheduled"
        },
        headers=auth_header(token),
    )

    response = client.delete(
        f"/api/v1/production-orders/{order_id}",
        headers=auth_header(token),
    )

    assert response.status_code == 400


def test_cancelled_order_can_be_deleted():
    data = create_test_order()

    order_id = data["order"]["id"]
    token = data["admin_token"]

    client.patch(
        f"/api/v1/production-orders/{order_id}/status",
        json={
            "status": "Cancelled"
        },
        headers=auth_header(token),
    )

    response = client.delete(
        f"/api/v1/production-orders/{order_id}",
        headers=auth_header(token),
    )

    assert response.status_code in [200, 204]

    response = client.get(
        f"/api/v1/production-orders/{order_id}",
        headers=auth_header(token),
    )

    assert response.status_code == 404


def test_draft_order_can_be_deleted():
    data = create_test_order()

    order_id = data["order"]["id"]
    token = data["admin_token"]

    response = client.delete(
        f"/api/v1/production-orders/{order_id}",
        headers=auth_header(token),
    )

    assert response.status_code in [200, 204]

    response = client.get(
        f"/api/v1/production-orders/{order_id}",
        headers=auth_header(token),
    )

    assert response.status_code == 404