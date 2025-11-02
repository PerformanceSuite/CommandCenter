"""
Integration tests for WebSocket real-time updates.

Tests the complete WebSocket workflow including:
- Connection establishment and authentication
- Real-time job progress updates
- Broadcast to multiple clients
- Connection cleanup and error handling
"""

import pytest
import asyncio
import json
from typing import Dict, Any, List
from fastapi import WebSocket
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models import Job, JobStatus, Project
from app.services.job_service import JobService
from app.routers.jobs import manager as connection_manager


pytestmark = pytest.mark.integration


class TestWebSocketIntegration:
    """Integration tests for WebSocket real-time updates."""

    @pytest.mark.asyncio
    async def test_websocket_connection_establishment(
        self,
        test_job: Job,
        db_session: AsyncSession,
    ):
        """Test WebSocket connection can be established for a valid job."""
        with TestClient(app) as client:
            with client.websocket_connect(f"/api/v1/jobs/ws/{test_job.id}") as websocket:
                # Should receive initial connection message
                data = websocket.receive_json()
                assert data["type"] == "connected"
                assert data["job_id"] == test_job.id
                assert "status" in data
                assert "progress" in data

    @pytest.mark.asyncio
    async def test_websocket_job_not_found(self):
        """Test WebSocket connection fails gracefully for non-existent job."""
        from starlette.websockets import WebSocketDisconnect

        with TestClient(app) as client:
            with pytest.raises((WebSocketDisconnect, ConnectionError)):  # Connection will fail
                with client.websocket_connect("/api/v1/jobs/ws/99999") as websocket:
                    pass

    @pytest.mark.asyncio
    async def test_websocket_progress_updates(
        self,
        test_job: Job,
        db_session: AsyncSession,
    ):
        """Test WebSocket receives real-time progress updates."""
        with TestClient(app) as client:
            with client.websocket_connect(f"/api/v1/jobs/ws/{test_job.id}") as websocket:
                # Receive initial connection
                initial_data = websocket.receive_json()
                assert initial_data["type"] == "connected"

                # Update job progress in another context
                service = JobService(db_session)
                await service.update_job(
                    job_id=test_job.id,
                    status="running",
                    progress=50,
                    current_step="Processing data",
                )

                # WebSocket should receive progress update within polling interval
                # Use retry logic to handle timing variations
                progress_data = None
                for attempt in range(5):
                    try:
                        data = websocket.receive_json(timeout=1)
                        if data.get("type") == "progress" and data.get("progress") == 50:
                            progress_data = data
                            break
                    except Exception:
                        continue

                assert progress_data is not None, "Progress update not received"
                assert progress_data["type"] == "progress"
                assert progress_data["job_id"] == test_job.id
                assert progress_data["status"] == "running"
                assert progress_data["progress"] == 50

    @pytest.mark.asyncio
    async def test_websocket_job_completion(
        self,
        test_job: Job,
        db_session: AsyncSession,
    ):
        """Test WebSocket connection closes when job completes."""
        with TestClient(app) as client:
            with client.websocket_connect(f"/api/v1/jobs/ws/{test_job.id}") as websocket:
                # Receive initial connection
                initial_data = websocket.receive_json()
                assert initial_data["type"] == "connected"

                # Mark job as completed
                service = JobService(db_session)
                await service.update_job(
                    job_id=test_job.id,
                    status="completed",
                    progress=100,
                    current_step="Finished",
                    result={"success": True},
                )

                # Should receive completion message
                messages = []
                try:
                    for _ in range(5):  # Collect messages until completion
                        msg = websocket.receive_json(timeout=2)
                        messages.append(msg)
                        if msg["type"] == "completed":
                            break
                except Exception:
                    pass

                # Find completion message
                completion_messages = [m for m in messages if m["type"] == "completed"]
                assert len(completion_messages) > 0

                completion_msg = completion_messages[0]
                assert completion_msg["job_id"] == test_job.id
                assert completion_msg["status"] == "completed"
                assert "result" in completion_msg

    @pytest.mark.asyncio
    async def test_websocket_multiple_clients(
        self,
        test_job: Job,
        db_session: AsyncSession,
    ):
        """Test multiple clients can connect to same job."""
        with TestClient(app) as client:
            # Connect two clients to the same job
            with client.websocket_connect(
                f"/api/v1/jobs/ws/{test_job.id}"
            ) as ws1, client.websocket_connect(f"/api/v1/jobs/ws/{test_job.id}") as ws2:
                # Both should receive initial connection
                data1 = ws1.receive_json()
                data2 = ws2.receive_json()

                assert data1["type"] == "connected"
                assert data2["type"] == "connected"
                assert data1["job_id"] == test_job.id
                assert data2["job_id"] == test_job.id

    @pytest.mark.asyncio
    async def test_websocket_broadcast_to_multiple_clients(
        self,
        test_job: Job,
        db_session: AsyncSession,
    ):
        """Test broadcast sends updates to all connected clients."""
        with TestClient(app) as client:
            with client.websocket_connect(
                f"/api/v1/jobs/ws/{test_job.id}"
            ) as ws1, client.websocket_connect(f"/api/v1/jobs/ws/{test_job.id}") as ws2:
                # Clear initial connection messages
                ws1.receive_json()
                ws2.receive_json()

                # Update job progress
                service = JobService(db_session)
                await service.update_job(
                    job_id=test_job.id,
                    status="running",
                    progress=75,
                    current_step="Almost done",
                )

                # Both clients should receive the update
                # Collect messages from both clients
                messages1 = []
                messages2 = []

                try:
                    for _ in range(3):
                        messages1.append(ws1.receive_json(timeout=2))
                except Exception:
                    pass

                try:
                    for _ in range(3):
                        messages2.append(ws2.receive_json(timeout=2))
                except Exception:
                    pass

                # Both clients should have received progress updates
                progress_msgs1 = [m for m in messages1 if m.get("progress") == 75]
                progress_msgs2 = [m for m in messages2 if m.get("progress") == 75]

                assert len(progress_msgs1) > 0, "Client 1 did not receive update"
                assert len(progress_msgs2) > 0, "Client 2 did not receive update"

    @pytest.mark.asyncio
    async def test_websocket_error_handling(
        self,
        test_job: Job,
        db_session: AsyncSession,
    ):
        """Test WebSocket handles job errors gracefully."""
        with TestClient(app) as client:
            with client.websocket_connect(f"/api/v1/jobs/ws/{test_job.id}") as websocket:
                # Clear initial connection
                websocket.receive_json()

                # Mark job as failed
                service = JobService(db_session)
                await service.update_job(
                    job_id=test_job.id,
                    status="failed",
                    progress=50,
                    error="Test error message",
                    traceback="Test traceback",
                )

                # Should receive completion message with error
                messages = []
                try:
                    for _ in range(5):
                        msg = websocket.receive_json(timeout=2)
                        messages.append(msg)
                        if msg["type"] == "completed":
                            break
                except Exception:
                    pass

                # Find completion message
                completion_messages = [m for m in messages if m["type"] == "completed"]
                assert len(completion_messages) > 0

                completion_msg = completion_messages[0]
                assert completion_msg["status"] == "failed"
                assert "error" in completion_msg

    @pytest.mark.asyncio
    async def test_websocket_connection_cleanup(
        self,
        test_job: Job,
    ):
        """Test WebSocket connections are properly cleaned up."""
        # Verify no connections before test
        assert test_job.id not in connection_manager.active_connections

        with TestClient(app) as client:
            with client.websocket_connect(f"/api/v1/jobs/ws/{test_job.id}") as websocket:
                websocket.receive_json()  # Initial connection
                # Connection should be registered
                assert test_job.id in connection_manager.active_connections

        # After context exit, connection should be cleaned up
        # Note: cleanup happens in finally block
        assert (
            test_job.id not in connection_manager.active_connections
            or len(connection_manager.active_connections[test_job.id]) == 0
        ), "WebSocket connection not properly cleaned up"

    @pytest.mark.asyncio
    async def test_websocket_concurrent_updates(
        self,
        test_job: Job,
        db_session: AsyncSession,
    ):
        """Test WebSocket handles concurrent job updates correctly."""
        with TestClient(app) as client:
            with client.websocket_connect(f"/api/v1/jobs/ws/{test_job.id}") as websocket:
                # Clear initial connection
                websocket.receive_json()

                # Make multiple rapid updates
                service = JobService(db_session)
                for progress in [10, 20, 30, 40, 50]:
                    await service.update_job(
                        job_id=test_job.id,
                        progress=progress,
                        current_step=f"Step {progress}",
                    )
                    await asyncio.sleep(0.1)  # Small delay

                # Collect messages
                messages = []
                try:
                    for _ in range(10):
                        msg = websocket.receive_json(timeout=2)
                        messages.append(msg)
                except Exception:
                    pass

                # Should have received multiple progress updates
                progress_values = [m.get("progress") for m in messages if "progress" in m]
                assert len(progress_values) >= 3  # At least some updates received

    @pytest.mark.asyncio
    async def test_websocket_json_serialization(
        self,
        test_job: Job,
        db_session: AsyncSession,
    ):
        """Test WebSocket properly serializes complex JSON data."""
        with TestClient(app) as client:
            with client.websocket_connect(f"/api/v1/jobs/ws/{test_job.id}") as websocket:
                # Clear initial connection
                websocket.receive_json()

                # Update with complex result data
                complex_result = {
                    "nested": {
                        "data": [1, 2, 3],
                        "string": "test",
                        "boolean": True,
                    }
                }

                service = JobService(db_session)
                await service.update_job(
                    job_id=test_job.id,
                    status="completed",
                    progress=100,
                    result=complex_result,
                )

                # Should receive properly serialized completion message
                messages = []
                try:
                    for _ in range(5):
                        msg = websocket.receive_json(timeout=2)
                        messages.append(msg)
                        if msg["type"] == "completed":
                            break
                except Exception:
                    pass

                completion_messages = [m for m in messages if m["type"] == "completed"]
                assert len(completion_messages) > 0

                completion_msg = completion_messages[0]
                assert completion_msg["result"] == complex_result


class TestConnectionManager:
    """Test the WebSocket ConnectionManager class."""

    @pytest.mark.asyncio
    async def test_connection_manager_connect(self):
        """Test ConnectionManager.connect() method."""
        manager = connection_manager

        # Note: Can't fully test without actual WebSocket, but we can test structure
        assert isinstance(manager.active_connections, dict)

    @pytest.mark.asyncio
    async def test_connection_manager_disconnect(self):
        """Test ConnectionManager.disconnect() method."""
        manager = connection_manager
        job_id = 999  # Use high ID to avoid conflicts

        # Create mock websocket
        mock_ws = object()

        # Manually add to active connections
        if job_id not in manager.active_connections:
            manager.active_connections[job_id] = []
        manager.active_connections[job_id].append(mock_ws)

        # Disconnect
        manager.disconnect(job_id, mock_ws)

        # Should be removed
        assert (
            job_id not in manager.active_connections or len(manager.active_connections[job_id]) == 0
        )

    @pytest.mark.asyncio
    async def test_connection_manager_broadcast(self):
        """Test ConnectionManager.broadcast() method."""
        manager = connection_manager
        job_id = 998  # Use high ID to avoid conflicts

        # Test broadcast to non-existent job (should not error)
        await manager.broadcast(job_id, {"type": "test", "message": "hello"})

        # Should not raise exception
        assert True


class TestWebSocketPerformance:
    """Performance tests for WebSocket connections."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_websocket_handles_rapid_updates(
        self,
        test_job: Job,
        db_session: AsyncSession,
    ):
        """Test WebSocket can handle rapid job updates without issues."""
        with TestClient(app) as client:
            with client.websocket_connect(f"/api/v1/jobs/ws/{test_job.id}") as websocket:
                # Clear initial connection
                websocket.receive_json()

                # Send 50 rapid updates
                service = JobService(db_session)
                for i in range(50):
                    await service.update_job(
                        job_id=test_job.id,
                        progress=i * 2,
                        current_step=f"Step {i}",
                    )

                # Collect messages (with timeout to avoid hanging)
                messages = []
                try:
                    while len(messages) < 20:  # Collect up to 20 messages
                        msg = websocket.receive_json(timeout=1)
                        messages.append(msg)
                except Exception:
                    pass

                # Should have received multiple updates
                assert len(messages) > 5

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_websocket_memory_cleanup(
        self,
        test_job: Job,
    ):
        """Test WebSocket connections don't leak memory."""
        manager = connection_manager

        # Record initial connection count
        initial_job_count = len(manager.active_connections)

        # Create and close multiple connections
        with TestClient(app) as client:
            for _ in range(10):
                with client.websocket_connect(f"/api/v1/jobs/ws/{test_job.id}") as websocket:
                    websocket.receive_json()
                # Connection should be cleaned up after context exit

        # After all connections closed, should not have grown significantly
        final_job_count = len(manager.active_connections)
        assert final_job_count <= initial_job_count + 1  # Allow for test job entry
