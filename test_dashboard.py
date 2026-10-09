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


client = TestClient(app)


def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def unique_email(prefix="dashboard"):
    return f"{prefix}_{uuid4().hex[:8]}@example.com"


def create_user(
    role="WORKER",
    prefix="dashboard",
    password="Password@12345",
):
    email = unique_email(prefix)

    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": f"Dashboard User {uuid4().hex[:6]}",
            "email": email,
            "password": password,
        },
    )

    assert response.status_code in [200, 201], response.text

    db = SessionLocal()

    try:
        db.execute(
            text(
                "UPDATE users "
                "SET role = :role "
                "WHERE email = :email"
            ),
            {
                "role": role,
                "email": email,
            },
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

    data = response.json()

    return {
        "id": data.get("user", {}).get("id"),
        "email": email,
        "token": data["access_token"],
    }


def create_super_admin():
    return create_user(
        role="SUPER_ADMIN",
        prefix="admin",
        password="Admin@12345",
    )


def create_plant(token):
    code = f"PLANT-{uuid4().hex[:6].upper()}"

    response = client.post(
        "/api/v1/plants",
        headers={
            "Authorization": f"Bearer {token}"
        },
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
    )

    assert response.status_code in [200, 201], response.text

    return response.json()


def create_production_line(token, plant_id):
    code = f"LINE-{uuid4().hex[:6].upper()}"

    response = client.post(
        "/api/v1/production-lines",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "name": f"Production Line {uuid4().hex[:6]}",
            "code": code,
            "production_capacity": 5000,
            "plant_id": plant_id,
            "status": "Active",
        },
    )

    assert response.status_code in [200, 201], response.text

    return response.json()


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}"
    }


def test_dashboard_empty_database():
    reset_database()

    user = create_user(
        prefix="empty"
    )

    response = client.get(
        "/api/v1/dashboard",
        headers=auth_headers(user["token"]),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["total_production_orders"] == 0
    assert data["active_production_orders"] == 0
    assert data["completed_orders"] == 0

    assert data["daily_production"] == []
    assert data["monthly_production"] == []

    assert data["production_efficiency"] == 0
    assert data["machine_utilization"] == 0
    assert data["machine_downtime"] == 0
    assert data["rejection_rate"] == 0
    assert data["quality_pass_percentage"] == 0

    assert data["material_consumption"] == []
    assert data["low_stock_materials"] == []
    assert data["maintenance_due"] == []
    assert data["defect_statistics"] == []


def test_dashboard_requires_authentication():
    reset_database()

    response = client.get(
        "/api/v1/dashboard"
    )

    assert response.status_code == 401


def test_dashboard_returns_machine_utilization():
    reset_database()

    admin = create_super_admin()

    plant = create_plant(
        admin["token"]
    )

    production_line = create_production_line(
        admin["token"],
        plant["id"],
    )

    from core.enums import MachineStatus
    from models.machine import Machine

    db = SessionLocal()

    try:
        machine = Machine(
            machine_code=f"M-DASH-{uuid4().hex[:6].upper()}",
            machine_type="CNC",
            production_line_id=production_line["id"],
            installation_date=date.today(),
            status=MachineStatus.RUNNING,
            operating_hours=80,
        )

        db.add(machine)
        db.commit()
    finally:
        db.close()

    response = client.get(
        "/api/v1/dashboard",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["machine_utilization"] == 100.0


def test_dashboard_returns_low_stock_materials():
    reset_database()

    admin = create_super_admin()

    from core.enums import MaterialStatus
    from models.raw_material import RawMaterial

    db = SessionLocal()

    try:
        material = RawMaterial(
            name="Low Stock Steel",
            material_code=f"MAT-{uuid4().hex[:6].upper()}",
            category="Metal",
            unit="KG",
            available_quantity=10,
            minimum_stock_level=20,
            reorder_level=15,
            supplier_reference="SUP-001",
            status=MaterialStatus.ACTIVE,
        )

        db.add(material)
        db.commit()
    finally:
        db.close()

    response = client.get(
        "/api/v1/dashboard",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert len(data["low_stock_materials"]) == 1

    low_stock = data["low_stock_materials"][0]

    assert low_stock["name"] == "Low Stock Steel"
    assert low_stock["available_quantity"] == 10
    assert low_stock["minimum_stock_level"] == 20
    assert low_stock["reorder_level"] == 15


def test_dashboard_response_contains_all_sections():
    reset_database()

    admin = create_super_admin()

    response = client.get(
        "/api/v1/dashboard",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    expected_keys = {
        "total_production_orders",
        "active_production_orders",
        "completed_orders",
        "daily_production",
        "monthly_production",
        "production_efficiency",
        "machine_utilization",
        "machine_downtime",
        "rejection_rate",
        "quality_pass_percentage",
        "material_consumption",
        "low_stock_materials",
        "maintenance_due",
        "defect_statistics",
    }

    assert expected_keys.issubset(data.keys())


def test_dashboard_production_efficiency_empty():
    reset_database()

    admin = create_super_admin()

    response = client.get(
        "/api/v1/dashboard",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["production_efficiency"] == 0


def test_dashboard_rejection_rate_empty():
    reset_database()

    admin = create_super_admin()

    response = client.get(
        "/api/v1/dashboard",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["rejection_rate"] == 0


def test_dashboard_quality_pass_percentage_empty():
    reset_database()

    admin = create_super_admin()

    response = client.get(
        "/api/v1/dashboard",
        headers=auth_headers(admin["token"]),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["quality_pass_percentage"] == 0