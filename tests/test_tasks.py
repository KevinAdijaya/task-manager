from uuid import uuid4

import pytest
from httpx import AsyncClient


class TestTasksCreate:
    @pytest.mark.asyncio
    async def test_create_task_success(self, client: AsyncClient, auth_headers):
        response = await client.post(
            "/api/v1/tasks/",
            headers=auth_headers,
            json={
                "title": "New Task",
                "description": "Task description",
                "status": "pending",
                "priority": "high",
                "category": "Work",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Task"
        assert data["description"] == "Task description"
        assert data["status"] == "pending"
        assert data["priority"] == "high"
        assert data["category"] == "Work"
        assert "id" in data
        assert "owner_id" in data

    @pytest.mark.asyncio
    async def test_create_task_minimal(self, client: AsyncClient, auth_headers):
        response = await client.post(
            "/api/v1/tasks/",
            headers=auth_headers,
            json={"title": "Minimal Task"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Minimal Task"
        assert data["status"] == "pending"
        assert data["priority"] == "medium"

    @pytest.mark.asyncio
    async def test_create_task_unauthorized(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/tasks/",
            json={"title": "Unauthorized Task"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_task_validation_error(self, client: AsyncClient, auth_headers):
        response = await client.post(
            "/api/v1/tasks/",
            headers=auth_headers,
            json={"title": ""},  # Empty title should fail
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_task_title_too_long(self, client: AsyncClient, auth_headers):
        response = await client.post(
            "/api/v1/tasks/",
            headers=auth_headers,
            json={"title": "x" * 201},  # Max 200 chars
        )
        assert response.status_code == 422


class TestTasksList:
    @pytest.mark.asyncio
    async def test_list_tasks_empty(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/v1/tasks/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 20

    @pytest.mark.asyncio
    async def test_list_tasks_with_data(self, client: AsyncClient, auth_headers, multiple_tasks):
        response = await client.get("/api/v1/tasks/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 10

    @pytest.mark.asyncio
    async def test_list_tasks_pagination(self, client: AsyncClient, auth_headers, multiple_tasks):
        response = await client.get("/api/v1/tasks/?page=1&page_size=5", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert data["total_pages"] == 2

    @pytest.mark.asyncio
    async def test_list_tasks_filter_status(
        self, client: AsyncClient, auth_headers, multiple_tasks
    ):
        response = await client.get("/api/v1/tasks/?status=done", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(task["status"] == "done" for task in data["items"])

    @pytest.mark.asyncio
    async def test_list_tasks_filter_priority(
        self, client: AsyncClient, auth_headers, multiple_tasks
    ):
        response = await client.get("/api/v1/tasks/?priority=high", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(task["priority"] == "high" for task in data["items"])

    @pytest.mark.asyncio
    async def test_list_tasks_filter_category(
        self, client: AsyncClient, auth_headers, multiple_tasks
    ):
        response = await client.get("/api/v1/tasks/?category=Work", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(task["category"] == "Work" for task in data["items"])

    @pytest.mark.asyncio
    async def test_list_tasks_search(self, client: AsyncClient, auth_headers, multiple_tasks):
        response = await client.get("/api/v1/tasks/?search=Task 1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert any("Task 1" in task["title"] for task in data["items"])


class TestTasksGet:
    @pytest.mark.asyncio
    async def test_get_task_success(self, client: AsyncClient, auth_headers, test_task):
        response = await client.get(f"/api/v1/tasks/{test_task.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_task.id)
        assert data["title"] == test_task.title

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, client: AsyncClient, auth_headers):
        response = await client.get(f"/api/v1/tasks/{uuid4()}", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_task_unauthorized(self, client: AsyncClient, test_task):
        response = await client.get(f"/api/v1/tasks/{test_task.id}")
        assert response.status_code == 401


class TestTasksUpdate:
    @pytest.mark.asyncio
    async def test_update_task_success(self, client: AsyncClient, auth_headers, test_task):
        response = await client.patch(
            f"/api/v1/tasks/{test_task.id}",
            headers=auth_headers,
            json={
                "title": "Updated Title",
                "status": "in_progress",
                "priority": "low",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["status"] == "in_progress"
        assert data["priority"] == "low"

    @pytest.mark.asyncio
    async def test_update_task_partial(self, client: AsyncClient, auth_headers, test_task):
        original_title = test_task.title
        response = await client.patch(
            f"/api/v1/tasks/{test_task.id}",
            headers=auth_headers,
            json={"status": "done"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "done"
        assert data["title"] == original_title  # Unchanged

    @pytest.mark.asyncio
    async def test_update_task_not_found(self, client: AsyncClient, auth_headers):
        response = await client.patch(
            f"/api/v1/tasks/{uuid4()}",
            headers=auth_headers,
            json={"title": "Updated"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_task_unauthorized(self, client: AsyncClient, test_task):
        response = await client.patch(
            f"/api/v1/tasks/{test_task.id}",
            json={"title": "Updated"},
        )
        assert response.status_code == 401


class TestTasksDelete:
    @pytest.mark.asyncio
    async def test_delete_task_success(self, client: AsyncClient, auth_headers, test_task):
        response = await client.delete(f"/api/v1/tasks/{test_task.id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify deleted
        get_response = await client.get(f"/api/v1/tasks/{test_task.id}", headers=auth_headers)
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, client: AsyncClient, auth_headers):
        response = await client.delete(f"/api/v1/tasks/{uuid4()}", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_task_unauthorized(self, client: AsyncClient, test_task):
        response = await client.delete(f"/api/v1/tasks/{test_task.id}")
        assert response.status_code == 401


class TestTasksStats:
    @pytest.mark.asyncio
    async def test_get_stats_empty(self, client: AsyncClient, auth_headers):
        response = await client.get("/api/v1/tasks/stats/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["overdue"] == 0

    @pytest.mark.asyncio
    async def test_get_stats_with_data(self, client: AsyncClient, auth_headers, multiple_tasks):
        response = await client.get("/api/v1/tasks/stats/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 10
        assert "pending" in data["by_status"]
        assert "in_progress" in data["by_status"]
        assert "done" in data["by_status"]
        assert "low" in data["by_priority"]
        assert "medium" in data["by_priority"]
        assert "high" in data["by_priority"]

    @pytest.mark.asyncio
    async def test_get_stats_unauthorized(self, client: AsyncClient):
        response = await client.get("/api/v1/tasks/stats/summary")
        assert response.status_code == 401
