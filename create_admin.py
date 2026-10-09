
from sqlalchemy import select

from database import SessionLocal
from models.user import User
from core.enums import AccountStatus, UserRole
from core.security import hash_password


db = SessionLocal()

try:
    email = "admin@manufacturing.com"

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_user:
        existing_user.role = UserRole.SUPER_ADMIN
        existing_user.status = AccountStatus.ACTIVE

        db.commit()
        db.refresh(existing_user)

        print("Existing account promoted to Super Admin.")
        print(f"Email: {existing_user.email}")
        print(f"Role: {existing_user.role}")
        print(f"Status: {existing_user.status}")
        print("Existing password preserved.")

    else:
        admin = User(
            full_name="Manufacturing Super Admin",
            email=email,
            password_hash=hash_password("Admin@12345"),
            role=UserRole.SUPER_ADMIN,
            status=AccountStatus.ACTIVE,
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("Super Admin created successfully.")
        print(f"Email: {email}")
        print("Password: Admin@12345")

except Exception:
    db.rollback()
    raise

finally:
    db.close()

