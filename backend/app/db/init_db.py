from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.models.core import AppUser


def ensure_default_admin(db: Session) -> None:
    if settings.environment.lower() != "development":
        return

    email = settings.dev_admin_email
    password = settings.dev_admin_password

    existing = db.query(AppUser).filter(AppUser.email == email).first()
    if existing is not None:
        return

    admin = AppUser(
        email=email,
        password_hash=hash_password(password),
        full_name="Local Admin",
        is_admin=True,
        is_active=True,
    )
    db.add(admin)
    db.commit()
