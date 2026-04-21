import pytest


async def _login(client):
    await client.post("/auth/setup", json={"username": "admin", "password": "secret"})
    resp = await client.post("/auth/login", json={"username": "admin", "password": "secret"})
    return resp.json()["access_token"]


@pytest.mark.asyncio
async def test_list_jobs_empty(client):
    token = await _login(client)
    resp = await client.get("/api/v1/jobs", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"] == []
    assert data["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_submit_job_validates_time_limit(client):
    token = await _login(client)
    resp = await client.post(
        "/api/v1/jobs/submit",
        json={
            "job_name": "test",
            "partition": "general",
            "num_nodes": 1,
            "num_cpus_per_task": 1,
            "num_tasks": 1,
            "time_limit_seconds": 99999999,  # exceeds 30 days
            "script_body": "#!/bin/bash\necho hi",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_cluster_overview(client):
    token = await _login(client)
    resp = await client.get("/api/v1/cluster/overview", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "running_jobs" in data
    assert "total_nodes" in data


@pytest.mark.asyncio
async def test_admin_endpoint_requires_admin(client):
    # Create regular user
    await client.post("/auth/setup", json={"username": "admin", "password": "secret"})
    # Create non-admin user
    from app.auth.service import hash_password
    from app.db.crud import create_user
    from app.db.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        await create_user(db, "regular", hash_password("pass"), role="user")

    resp = await client.post("/auth/login", json={"username": "regular", "password": "pass"})
    token = resp.json()["access_token"]

    resp = await client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
