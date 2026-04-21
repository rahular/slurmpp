"""CLI entrypoint for bare-metal installs: slurm++ init / start / create-admin"""

import asyncio
import sys


def main():
    if len(sys.argv) < 2:
        print("Usage: slurm++ <command>")
        print("Commands: init, start, create-admin")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "start":
        import uvicorn
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)

    elif cmd == "init":
        asyncio.run(_init())

    elif cmd == "create-admin":
        if len(sys.argv) < 4:
            print("Usage: slurm++ create-admin <username> <password>")
            sys.exit(1)
        asyncio.run(_create_admin(sys.argv[2], sys.argv[3]))

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


async def _init():
    from app.db.database import init_db
    await init_db()
    print("slurm++ database initialized.")


async def _create_admin(username: str, password: str):
    from app.auth.service import hash_password
    from app.db.crud import create_user, get_user
    from app.db.database import AsyncSessionLocal, init_db

    await init_db()
    async with AsyncSessionLocal() as db:
        existing = await get_user(db, username)
        if existing:
            print(f"User '{username}' already exists.")
            sys.exit(1)
        await create_user(db, username, hash_password(password), role="admin")
    print(f"Admin user '{username}' created.")


if __name__ == "__main__":
    main()
