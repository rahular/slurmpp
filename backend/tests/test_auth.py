import pytest


@pytest.mark.asyncio
async def test_setup_admin(client):
    resp = await client.post("/auth/setup", json={"username": "admin", "password": "secret123"})
    assert resp.status_code == 201
    assert resp.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_setup_admin_twice_fails(client):
    await client.post("/auth/setup", json={"username": "admin", "password": "secret123"})
    resp = await client.post("/auth/setup", json={"username": "admin2", "password": "secret123"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_login(client):
    await client.post("/auth/setup", json={"username": "admin", "password": "secret123"})
    resp = await client.post("/auth/login", json={"username": "admin", "password": "secret123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_bad_password(client):
    await client.post("/auth/setup", json={"username": "admin", "password": "secret123"})
    resp = await client.post("/auth/login", json={"username": "admin", "password": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client):
    await client.post("/auth/setup", json={"username": "admin", "password": "secret123"})
    login_resp = await client.post("/auth/login", json={"username": "admin", "password": "secret123"})
    refresh_token = login_resp.json()["refresh_token"]

    resp = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(client):
    resp = await client.get("/api/v1/cluster/health")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoint_with_token(client):
    await client.post("/auth/setup", json={"username": "admin", "password": "secret123"})
    login_resp = await client.post("/auth/login", json={"username": "admin", "password": "secret123"})
    token = login_resp.json()["access_token"]

    resp = await client.get("/api/v1/cluster/health", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
