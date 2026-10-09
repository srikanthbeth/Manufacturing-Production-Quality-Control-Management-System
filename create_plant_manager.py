from sqlalchemy import select

from database import SessionLocal
from models.user import User
from core.enums import AccountStatus, UserRole
from core.security import hash_password


db = SessionLocal()

try:
    email = "plantmanager@manufacturing.com"

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_user:
        print("Plant Manager already exists.")
    else:
        manager = User(
            full_name="Manufacturing Plant Manager",
            email=email,
            password_hash=hash_password("Manager@12345"),
            role=UserRole.PLANT_MANAGER,
            status=AccountStatus.ACTIVE,
        )

        db.add(manager)
        db.commit()

        print("Plant Manager created successfully.")
        print("Email: plantmanager@manufacturing.com")
        print("Password: Manager@12345")

finally:
    db.close()