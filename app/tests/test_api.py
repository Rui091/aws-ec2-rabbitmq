"""
Unit tests for the Tasks & Orders REST API.
"""
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_list_tasks_empty(client):
    response = await client.get("/tasks")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_create_task_returns_202(client):
    with patch(
        "app.api.routes.get_rabbitmq_channel",
        new_callable=AsyncMock,
    ) as mock_channel:
        mock_channel.return_value = AsyncMock()
        response = await client.post("/tasks")

    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "pending"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_task_by_id(client):
    with patch(
        "app.api.routes.get_rabbitmq_channel",
        new_callable=AsyncMock,
    ) as mock_channel:
        mock_channel.return_value = AsyncMock()
        create_resp = await client.post("/tasks")

    task_id = create_resp.json()["id"]
    get_resp = await client.get(f"/tasks/{task_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == task_id


@pytest.mark.asyncio
async def test_get_task_not_found(client):
    response = await client.get("/tasks/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_task_returns_202(client):
    with patch(
        "app.api.routes.get_rabbitmq_channel",
        new_callable=AsyncMock,
    ) as mock_channel:
        mock_channel.return_value = AsyncMock()
        create_resp = await client.post("/tasks")
        task_id = create_resp.json()["id"]
        del_resp = await client.delete(f"/tasks/{task_id}")

    assert del_resp.status_code == 202
    assert del_resp.json()["task_id"] == task_id


@pytest.mark.asyncio
async def test_delete_task_not_found(client):
    with patch(
        "app.api.routes.get_rabbitmq_channel",
        new_callable=AsyncMock,
    ):
        response = await client.delete("/tasks/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_orders_empty(client):
    response = await client.get("/orders")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
