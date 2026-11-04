"""
test_reliability_remediation.py — Comprehensive test suite for NIWI Service Bus Reliability Remediation.
Tests cover:
1. Single Worker Ownership (No duplicate legacy jobs, single outbox event)
2. Accurate Status Semantics (SKIPPED, SENT, SYNCED, FAILED, PENDING, GENERATED)
3. HubSpot Deal Idempotency (Lookup before create, update existing, timeout safety)
4. Per-Operation Idempotency and Crash Recovery (Message redelivery, crash points, concurrent claims)
5. Regression & Security checks (Tenant isolation, auth)
"""
import uuid
import json
from unittest.mock import MagicMock, patch, call
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.tasks.service_bus_worker import (
    handle_submission_created,
    claim_and_execute_operation,
    process_message,
    OP_REPORT_GENERATION,
    OP_EMAIL_DELIVERY,
    OP_CRM_SYNC,
    OP_ADMIN_NOTIFICATION,
)
from app.services.crm_service import sync_to_hubspot, is_hubspot_configured
from app.services.settings_service import is_acs_configured, send_acs_email, notify_admin_new_submission

client = TestClient(app)


# ============================================================================
# 1. Functional Tests & Single Worker Ownership
# ============================================================================

class TestSingleWorkerOwnership:
    def test_submission_cte_has_no_post_submit_jobs(self):
        """Verify routes.py does not insert into post_submit_jobs in CTE."""
        from app.api import routes
        import inspect
        source = inspect.getsource(routes.submit)
        assert "post_submit_jobs" not in source, "Found legacy post_submit_jobs in submit!"
        assert "service_bus_outbox" in source, "service_bus_outbox must be present in submit!"

    def test_supervisord_has_no_job_worker(self):
        """Verify supervisord.conf does not launch legacy job_worker."""
        with open("supervisord.conf", "r") as f:
            content = f.read()
        assert "[program:job_worker]" not in content
        assert "[program:service_bus_worker]" in content
        assert "[program:outbox_dispatcher]" in content
        assert "[unix_http_server]" in content


# ============================================================================
# 2. Status Accuracy Semantics (Phase 2)
# ============================================================================

class TestStatusAccuracySemantics:
    def test_unconfigured_acs_marks_email_and_admin_skipped(self):
        """When ACS_CONNECTION_STRING is missing, email and admin notify are SKIPPED, not SENT."""
        with patch.dict("os.environ", {"ACS_CONNECTION_STRING": ""}, clear=False), \
             patch("app.services.settings_service.get_settings", return_value={
                 "notifications_enabled": True,
                 "notification_email": "admin@example.com",
                 "notification_cc_email": "",
                 "sender_address": "sender@orchvate.com",
                 "sender_name": "Orchvate"
             }):
            assert not is_acs_configured()
            assert send_acs_email(
                subject="Test", html="<p>Test</p>", plain="Test",
                sender_address="test@orchvate.com", sender_name="Orchvate"
            ) is False

            status, reason = notify_admin_new_submission(
                cur=None, submission_id=123, name="John Doe", company_name="Acme", sync=True
            )
            assert status == "SKIPPED"
            assert "ACS" in reason or "not configured" in reason

    def test_unconfigured_hubspot_marks_crm_skipped(self):
        """When HUBSPOT_ACCESS_TOKEN is missing, CRM sync is SKIPPED, not SYNCED."""
        with patch.dict("os.environ", {"HUBSPOT_ACCESS_TOKEN": ""}, clear=False):
            assert not is_hubspot_configured()
            res = sync_to_hubspot(
                data={"email": "test@example.com"},
                score_data={"overall_avg": 12.0},
                submission_id=str(uuid.uuid4())
            )
            assert res["status"] == "SKIPPED"
            assert "HUBSPOT_ACCESS_TOKEN" in res["reason"]

    def test_status_endpoint_returns_granular_statuses(self):
        """Status API distinguishes report_status from external delivery statuses."""
        sub_id = str(uuid.uuid4())
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_cur.fetchone.return_value = {
            "id": sub_id,
            "organization_id": str(uuid.uuid4()),
            "async_status": "COMPLETED",
            "email_status": "SKIPPED",
            "crm_status": "SKIPPED",
            "report_status": "GENERATED",
            "admin_notify_status": "SKIPPED",
            "hubspot_deal_id": None,
            "submitted_at": None,
            "async_completed_at": None,
            "email_body": "<p>Report</p>"
        }

        with patch("app.api.routes.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            res = client.get(f"/api/submissions/{sub_id}/status")
            assert res.status_code == 200
            data = res.json()
            assert data["submission_id"] == sub_id
            assert data["status"] == "COMPLETED"
            assert data["report_status"] == "GENERATED"
            assert data["email_status"] == "SKIPPED"
            assert data["crm_status"] == "SKIPPED"
            assert data["admin_notify_status"] == "SKIPPED"


# ============================================================================
# 3. HubSpot Deal Idempotency (Phase 3)
# ============================================================================

class TestHubSpotDealIdempotency:
    def test_deal_creation_searches_before_post(self):
        """sync_to_hubspot searches for existing deal with stable identifier before creating."""
        sub_id = str(uuid.uuid4())
        data = {
            "email": "lead@company.com",
            "name": "Jane Lead",
            "company_name": "Acme Corp",
            "designation": "Director",
            "contact_number": "1234567890"
        }
        score_data = {"overall_avg": 8.0, "overall_level": "Early Progress"}

        mock_req = MagicMock()
        # 1. Contact search -> returns existing contact 'c-100'
        # 2. Contact update -> returns {}
        # 3. Deal search -> returns existing deal 'd-200'
        # 4. Deal update PATCH -> returns {}
        # 5. Deal-Contact association PUT -> returns {}
        mock_req.side_effect = [
            {"results": [{"id": "c-100"}]},       # contact search
            {},                                    # contact patch
            {"results": [{"id": "d-200"}]},       # deal search finds existing
            {},                                    # deal patch update
            {}                                     # association put
        ]

        with patch.dict("os.environ", {"HUBSPOT_ACCESS_TOKEN": "test-token"}), \
             patch("app.services.crm_service.make_hubspot_request", mock_req):
            res = sync_to_hubspot(data, score_data, sub_id)

            assert res["status"] == "SYNCED"
            assert res["deal_id"] == "d-200"
            assert res["contact_id"] == "c-100"

            # Check calls: make sure POST /crm/v3/objects/deals (creation) was NEVER called
            urls_called = [c[0][1] for c in mock_req.call_args_list]
            methods_called = [c[0][0] for c in mock_req.call_args_list]
            deal_creation_calls = [
                (m, u) for m, u in zip(methods_called, urls_called)
                if m == "POST" and u == "https://api.hubapi.com/crm/v3/objects/deals"
            ]
            assert len(deal_creation_calls) == 0, "Deal creation POST was called even though deal already existed!"

    def test_deal_creation_when_not_found(self):
        """When deal does not exist, sync_to_hubspot creates a new deal and associates it."""
        sub_id = str(uuid.uuid4())
        data = {"email": "new@company.com", "name": "New User", "company_name": "New Co"}
        score_data = {"overall_avg": 14.0}

        mock_req = MagicMock()
        mock_req.side_effect = [
            {"results": []},                       # contact search: none
            {"id": "c-created-1"},                 # contact create: return id
            {"results": []},                       # deal search: none
            {"id": "d-created-1"},                 # deal create: return id
            {}                                     # association
        ]

        with patch.dict("os.environ", {"HUBSPOT_ACCESS_TOKEN": "test-token"}), \
             patch("app.services.crm_service.make_hubspot_request", mock_req):
            res = sync_to_hubspot(data, score_data, sub_id)

            assert res["status"] == "SYNCED"
            assert res["deal_id"] == "d-created-1"
            assert res["contact_id"] == "c-created-1"

    def test_hubspot_timeout_re_raises_for_idempotent_retry(self):
        """Network timeout during deal creation raises exception for redelivery reconciliation."""
        import requests
        sub_id = str(uuid.uuid4())
        data = {"email": "new@company.com", "name": "New User", "company_name": "New Co"}
        score_data = {"overall_avg": 14.0}

        def mock_hubspot(method, url, json_data=None, retries=3, timeout=10):
            if method == "POST" and url == "https://api.hubapi.com/crm/v3/objects/deals":
                raise requests.exceptions.Timeout("Connection timed out waiting for HubSpot")
            elif method == "POST" and "contacts/search" in url:
                return {"results": [{"id": "c-1"}]}
            elif method == "PATCH" and "contacts" in url:
                return {}
            elif method == "POST" and "deals/search" in url:
                return {"results": []}
            return {}

        with patch.dict("os.environ", {"HUBSPOT_ACCESS_TOKEN": "test-token"}), \
             patch("app.services.crm_service.make_hubspot_request", side_effect=mock_hubspot):
            with pytest.raises(RuntimeError) as exc_info:
                sync_to_hubspot(data, score_data, sub_id)
            assert "timed out" in str(exc_info.value).lower()


# ============================================================================
# 4. Per-Operation Idempotency & Crash Recovery (Phase 4)
# ============================================================================

class TestPerOperationIdempotencyAndCrashRecovery:
    def test_claim_and_execute_reclaims_expired_lock(self):
        """Worker claims operation if lock is expired (> 5 minutes)."""
        sub_id = str(uuid.uuid4())
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        # Atomic insert RETURNING returns claimed row (expired lock reclaimed)
        mock_cur.fetchone.return_value = (str(uuid.uuid4()), "PROCESSING", {}, 2)

        fn = MagicMock(return_value={"status": "GENERATED", "metadata": {}})
        with patch("app.tasks.service_bus_worker.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            res = claim_and_execute_operation(sub_id, OP_REPORT_GENERATION, "worker-1", fn)

            assert res["status"] == "GENERATED"
            assert fn.called

    def test_claim_and_execute_skips_already_completed_operation(self):
        """Worker skips operation execution if already marked COMPLETED/GENERATED."""
        sub_id = str(uuid.uuid4())
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        # 1. Atomic INSERT RETURNING returns None (conflict matched existing completed)
        # 2. Inspection query returns existing status 'GENERATED'
        mock_cur.fetchone.side_effect = [
            None,
            ("GENERATED", {"generated": True}, None, None)
        ]

        fn = MagicMock()
        with patch("app.tasks.service_bus_worker.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            res = claim_and_execute_operation(sub_id, OP_REPORT_GENERATION, "worker-1", fn)

            assert res["status"] == "GENERATED"
            assert res.get("reused") is True
            assert not fn.called, "Handler function should NOT be called for already-completed operation!"

    def test_concurrent_worker_locked_operation_skips_execution(self):
        """Second worker attempting actively locked operation does not execute concurrently."""
        sub_id = str(uuid.uuid4())
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        mock_cur.fetchone.side_effect = [
            None,
            ("PROCESSING", {}, "2026-11-04 12:00:00", "worker-other")
        ]

        fn = MagicMock()
        with patch("app.tasks.service_bus_worker.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            res = claim_and_execute_operation(sub_id, OP_CRM_SYNC, "worker-me", fn)

            assert res["status"] == "LOCKED"
            assert not fn.called, "Concurrent worker must not execute actively locked operation!"

    def test_crash_after_report_generation_recovers_without_regenerating(self):
        """If worker crashes after report generation, redelivery skips report generation and proceeds."""
        sub_id = str(uuid.uuid4())
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur

        # Sub row: async_status='PENDING', report_status='GENERATED'
        # 1st query: submission lookup
        # 2nd query (REPORT_GEN): returns None for claim, inspection returns 'GENERATED'
        # 3rd query (EMAIL_DEL): claimed, returns row
        # 4th query (CRM_SYNC): claimed, returns row
        # 5th query (ADMIN_NOTIF): claimed, returns row
        mock_cur.fetchone.side_effect = [
            ("PENDING", "PENDING", "PENDING", "GENERATED", None),  # submission lookup
            None,                                                 # report claim conflict
            ("GENERATED", {}, None, None),                         # report inspection -> reused
            (str(uuid.uuid4()), "PROCESSING", {}, 1),             # email claim
            (str(uuid.uuid4()), "PROCESSING", {}, 1),             # crm claim
            (str(uuid.uuid4()), "PROCESSING", {}, 1),             # admin claim
        ]

        with patch("app.tasks.service_bus_worker.get_db_connection") as mock_get_conn, \
             patch("app.tasks.service_bus_worker.get_settings", return_value={"crm_sync_enabled": False, "notifications_enabled": False}), \
             patch("app.tasks.service_bus_worker.process_email_job") as mock_gen_report, \
             patch("app.tasks.service_bus_worker.is_acs_configured", return_value=False), \
             patch("app.tasks.service_bus_worker.is_hubspot_configured", return_value=False):
            mock_get_conn.return_value.__enter__.return_value = mock_conn

            handle_submission_created(sub_id, {"submission_id": sub_id})

            assert not mock_gen_report.called, "Report generation should be skipped on crash recovery redelivery!"

    def test_message_completed_only_after_durable_commit(self):
        """process_message completes message only after handle_submission_created succeeds."""
        mock_receiver = MagicMock()
        mock_msg = MagicMock()
        sub_id = str(uuid.uuid4())
        mock_msg.message_id = "msg-settle"
        mock_msg.delivery_count = 1
        mock_msg.correlation_id = sub_id
        mock_msg.body = [json.dumps({"submission_id": sub_id}).encode("utf-8")]
        mock_msg.application_properties = {"event_type": "SUBMISSION_CREATED"}

        order_tracker = []
        def mock_handle(s_id, payload, worker_id="sb-worker-1"):
            order_tracker.append("handled")

        def mock_complete(m):
            order_tracker.append("completed")

        mock_receiver.complete_message.side_effect = mock_complete

        with patch("app.tasks.service_bus_worker.handle_submission_created", side_effect=mock_handle):
            process_message(mock_receiver, mock_msg)

            assert order_tracker == ["handled", "completed"], "Message completed before handling finished!"


# ============================================================================
# 5. Regression & Security Isolation Tests
# ============================================================================

class TestRegressionAndSecurity:
    def test_tenant_isolation_on_status_api(self):
        """Users of Org A cannot access submission status of Org B."""
        import jwt
        from app.core.config import JWT_SECRET
        sub_id = str(uuid.uuid4())
        org_a = str(uuid.uuid4())
        org_b = str(uuid.uuid4())

        token_b = jwt.encode({"sub": "user_b", "role": "org_member", "org_id": org_b}, JWT_SECRET, algorithm="HS256")

        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cur
        mock_cur.fetchone.return_value = {
            "id": sub_id,
            "organization_id": org_a, # Submission belongs to Org A
            "async_status": "COMPLETED",
            "email_status": "SKIPPED",
            "crm_status": "SKIPPED",
            "report_status": "GENERATED",
            "admin_notify_status": "SKIPPED",
            "hubspot_deal_id": None,
            "submitted_at": None,
            "async_completed_at": None,
            "email_body": "test"
        }

        with patch("app.api.routes.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__enter__.return_value = mock_conn
            res = client.get(
                f"/api/submissions/{sub_id}/status",
                headers={"Authorization": f"Bearer {token_b}"}
            )
            assert res.status_code == 403
            assert "Forbidden" in res.json()["detail"]
