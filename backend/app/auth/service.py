import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import crud
from app.db.models import User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


async def authenticate_local(db: AsyncSession, username: str, password: str) -> User | None:
    user = await crud.get_user(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def authenticate_ldap(username: str, password: str) -> dict | None:
    """Returns {"username": str, "role": str} or None on failure."""
    if not settings.ldap_url:
        return None
    try:
        import ldap3  # noqa: F401
        from ldap3 import Connection, Server, SIMPLE, ALL

        server = Server(settings.ldap_url, get_info=ALL)
        user_dn = settings.ldap_user_dn_template.format(
            username=username, base_dn=settings.ldap_base_dn
        )
        conn = Connection(server, user=user_dn, password=password, authentication=SIMPLE)
        if not conn.bind():
            return None

        role = "user"
        if settings.ldap_admin_group_dn:
            conn.search(
                settings.ldap_admin_group_dn,
                f"(member={user_dn})",
                attributes=["cn"],
            )
            if conn.entries:
                role = "admin"
        conn.unbind()
        return {"username": username, "role": role}
    except Exception:
        return None


async def authenticate(db: AsyncSession, username: str, password: str) -> tuple[str, str] | None:
    """Returns (username, role) or None."""
    if settings.auth_backend == "ldap":
        result = await authenticate_ldap(username, password)
        if result:
            return result["username"], result["role"]
        return None
    else:
        user = await authenticate_local(db, username, password)
        if user:
            return user.username, user.role
        return None
