"""
test_service_bus_pipeline.py — Unit and integration tests for Azure Service Bus,
Transactional Outbox Pattern, Consumer Worker, and Submission Status API.
"""
import uuid
import json
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.service_bus import publish_event, get_service_bus_client, close_service_bus
from app.services.outbox_service import dispatch_pending_outbox_events
from app.tasks.service_bus_worker import process_message, handle_submission_created

client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Service Bus Core SDK & Publishing
# ---------------------------------------------------------------------------

class TestServiceBusCore:
    def test_publish_event_constructs_valid_message(self):
        """publish_event must send ServiceBusMessage with correlation_id and application_properties."""
        sub_id = str(uuid.uuid4())
        payload = {"submission_id": sub_id, "score": 85.5}

        mock_sender = MagicMock()
        with patch("app.core.service_bus.get_service_bus_sender", return_value=mock_sender):
            msg_id = publish_event(
                event_type="SUBMISSION_CREATED",
                aggregate_id=sub_id,
                payload=payload
            )

        assert msg_id == f"sub-{sub_id}-SUBMISSION_CREATED"
        assert mock_sender.send_messages.called
        sent_msg = mock_sender.send_messages.call_args[0][0]
        assert sent_msg.message_id == msg_id
        assert sent_msg.correlation_id == sub_id
        assert sent_msg.content_type == "application/json"
        assert sent_msg.application_properties["event_type"] == "SUBMISSION_CREATED"
        assert sent_msg.application_properties["aggregate_id"] == sub_id

    def test_close_service_bus_cleans_resources(self):
        """close_service_bus must close active sender and client gracefully."""
        mock_client = MagicMock()
        mock_sender = MagicMock()

        with patch("app.core.service_bus._client", mock_client), \
             patch("app.core.service_bus._sender", mock_sender):
            close_service_bus()
            assert mock_sender.close.called
            assert mock_client.close.called


# ---------------------------------------------------------------------------
# 2. Transactional Outbox Pattern
# ---------------------------------------------------------------------------

class TestTransactionalOutbox:
    def test_outbox_dispatcher_processes_pending_events(self):
        """Outbox dispatcher claims PENDING rows and marks them PUBLISHED upon successful send."""
        evt_id = str(uuid.uuid4())
        sub_id = str(uuid.uuid4())

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        # 1. fetchall for claimed rows: [(id, event_type, aggregate_id, payload, attempt_count)]
        mock_cur.fetchall.return_value = [
            (evt_id, "SUBMISSION_CREATED", sub_id, {"submission_id": sub_id}, 0)
        ]

        with patch("app.services.outbox_service.get_db_connection") as mock_get_conn, \
             patch("app.services.outbox_service.publish_event") as mock_publish:
            mock_get_conn.return_value.__enter__.return_value = mock_conn

            processed = dispatch_pending_outbox_events(batch_size=5, worker_id="test-worker")

            assert processed == 1
            assert mock_publish.called
            # Verify update to PUBLISHED
            sqls = [call[0][0] for call in mock_cur.execute.call_args_list]
            update_published = any("SET status = 'PUBLISHED'" in s for s in sqls)
            assert update_published

    def test_outbox_dispatcher_exponential_backoff_on_failure(self):
        """Outbox dispatcher sets status to FAILED with exponential backoff when send fails."""
        evt_id = str(uuid.uuid4())
        sub_id = str(uuid.uuid4())

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        mock_cur.fetchall.return_value = [
            (evt_id, "SUBMISSION_CREATED", sub_id, {"submission_id": sub_id}, 1)
        ]

        with patch("app.services.outbox_service.get_db_connection") as mock_get_conn, \
             patch("app.services.outbox_service.publish_event", side_effect=Exception("Transient Service Bus failure")):
            mock_get_conn.return_value.__enter__.return_value = mock_conn

            processed = dispatch_pending_outbox_events(batch_size=5, worker_id="test-worker")

            assert processed == 1
            sqls = [call[0][0] for call in mock_cur.execute.call_args_list]
            update_failed = any("SET status = 'FAILED'" in s for s in sqls)
            assert update_failed

    def test_outbox_dispatcher_dead_letters_after_max_attempts(self):
        """Outbox event is routed to DEAD_LETTER when attempt_count reaches max_retries (5)."""
        evt_id = str(uuid.uuid4())
        sub_id = str(uuid.uuid4())

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        # attempt_count is currently 4 -> next attempt is 5 >= MAX_RETRIES
        mock_cur.fetchall.return_value = [
            (evt_id, "SUBMISSION_CREATED", sub_id, {"submission_id": sub_id}, 4)
        ]

        with patch("app.services.outbox_service.get_db_connection") as mock_get_conn, \
             patch("app.services.outbox_service.publish_event", side_effect=Exception("Permanent Service Bus failure")):
            mock_get_conn.return_value.__enter__.return_value = mock_conn

            processed = dispatch_pending_outbox_events(batch_size=5, worker_id="test-worker")

            assert processed == 1
            sqls = [call[0][0] for call in mock_cur.execute.call_args_list]
            update_dlq = any("SET status = 'DEAD_LETTER'" in s for s in sqls)
            assert update_dlq


# ---------------------------------------------------------------------------
# 3. Service Bus Worker & Message Settlement
# ---------------------------------------------------------------------------

class TestServiceBusWorker:
    def test_process_message_completes_on_success(self):
        """process_message settles message via complete_message upon successful handling."""
        mock_receiver = MagicMock()
        mock_msg = MagicMock()
        sub_id = str(uuid.uuid4())
        mock_msg.message_id = "msg-123"
        mock_msg.delivery_count = 1
        mock_msg.correlation_id = sub_id
        mock_msg.body = [json.dumps({"submission_id": sub_id, "event_type": "SUBMISSION_CREATED"}).encode("utf-8")]
        mock_msg.application_properties = {"event_type": "SUBMISSION_CREATED"}

        with patch("app.tasks.service_bus_worker.handle_submission_created") as mock_handler:
            process_message(mock_receiver, mock_msg)
            assert mock_handler.called
            assert mock_receiver.complete_message.called

    def test_process_message_dead_letters_malformed_json(self):
        """process_message immediately dead-letters poison messages with invalid JSON."""
        mock_receiver = MagicMock()
        mock_msg = MagicMock()
        mock_msg.message_id = "msg-poison"
        mock_msg.delivery_count = 1
        mock_msg.body = [b"NOT_A_VALID_JSON_STRING{{{"]
        mock_msg.application_properties = {}

        process_message(mock_receiver, mock_msg)
        assert mock_receiver.dead_letter_message.called
        call_kwargs = mock_receiver.dead_letter_message.call_args[1]
        assert call_kwargs["reason"] == "JSONDecodeError"

    def test_process_message_abandons_on_transient_error(self):
        """process_message abandons message for retry when handler raises transient exception."""
        mock_receiver = MagicMock()
        mock_msg = MagicMock()
        sub_id = str(uuid.uuid4())
        mock_msg.message_id = "msg-transient"
        mock_msg.delivery_count = 2
        mock_msg.correlation_id = sub_id
        mock_msg.body = [json.dumps({"submission_id": sub_id}).encode("utf-8")]
        mock_msg.application_properties = {"event_type": "SUBMISSION_CREATED"}

        with patch("app.tasks.service_bus_worker.handle_submission_created", side_effect=Exception("Transient DB timeout")):
            process_message(mock_receiver, mock_msg)
            assert mock_receiver.abandon_message.called

    def test_handle_submission_created_idempotent_skip(self):
        """handle_submission_created skips work if submission is already marked COMPLETED."""
        sub_id = str(uuid.uuid4())
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        # (async_status, email_status, crm_status)
        mock_cur.fetchone.return_value = ("COMPLETED", "SENT", "SYNCED")

        with patch("app.tasks.service_bus_worker.get_db_connection") as mock_get_conn, \
             patch("app.tasks.service_bus_worker.process_email_job") as mock_email:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            handle_submission_created(sub_id, {"submission_id": sub_id})

            assert not mock_email.called


# ---------------------------------------------------------------------------
# 4. Submission Status API Endpoint
# ---------------------------------------------------------------------------

class TestSubmissionStatusEndpoint:
    def test_get_status_invalid_uuid(self):
        """Invalid ID format returns 400 Bad Request."""
        res = client.get("/api/submissions/not-a-valid-uuid-or-id!/status")
        assert res.status_code == 400
        assert "Invalid submission ID format" in res.json()["detail"]

    def test_get_status_not_found(self):
        """Non-existent submission returns 404 Not Found."""
        random_id = str(uuid.uuid4())
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_cur.fetchone.return_value = None

        with patch("app.api.routes.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            res = client.get(f"/api/submissions/{random_id}/status")
            assert res.status_code == 404

    def test_get_status_success(self):
        """Existing submission returns 200 with status fields."""
        sub_id = str(uuid.uuid4())
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_cur.fetchone.return_value = {
            "id": sub_id,
            "organization_id": str(uuid.uuid4()),
            "async_status": "COMPLETED",
            "email_status": "SENT",
            "crm_status": "SYNCED",
            "submitted_at": None,
            "async_completed_at": None
        }

        with patch("app.api.routes.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            res = client.get(f"/api/submissions/{sub_id}/status")
            assert res.status_code == 200
            data = res.json()
            assert data["submission_id"] == sub_id
            assert data["status"] == "COMPLETED"
            assert data["email_status"] == "SENT"
            assert data["crm_status"] == "SYNCED"

