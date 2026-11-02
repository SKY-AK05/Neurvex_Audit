"""
conftest.py — Global test configuration, safety guards, and isolated test fixtures for NIWI
"""
import os
import sys
import uuid
import re
import json
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
import pytest
import psycopg2
import psycopg2.extensions
import psycopg2.extras

# Ensure isolated test environment configuration before any app imports
os.environ["APP_ENV"] = "test"
os.environ["TESTING"] = "true"
os.environ["ENABLE_DEV_BYPASS"] = "true"
os.environ["PGHOST"] = "test-isolated-db.internal"
os.environ["PGPORT"] = "5432"
os.environ["PGDATABASE"] = "nd_audit_test"
os.environ["PGUSER"] = "test_runner"
os.environ["PGPASSWORD"] = "test_password_for_isolated_test_suite_32chars!!"
os.environ["ACS_CONNECTION_STRING"] = "endpoint=https://mock-acs.communication.azure.com/;accesskey=mocktestkey=="
os.environ["JWT_SECRET"] = "test-jwt-secret-key-minimum-32chars-for-testing!!"


# ============================================================================
# In-Memory Database Store for Test Isolation
# ============================================================================

class InMemoryStore:
    def __init__(self):
        self.reset()

    def reset(self):
        self.admin_users = {
            "super@test.com": {"id": str(uuid.uuid4()), "email": "super@test.com", "role": "super", "is_active": True},
            "admin@test.com": {"id": str(uuid.uuid4()), "email": "admin@test.com", "role": "admin", "is_active": True},
        }
        self.organizations = {}
        self.submissions = {}
        self.invitations = {}
        self.drafts = {}
        self.reassignments = []
        self.links = []
        self.settings = {
            "id": 1,
            "crm_sync_enabled": False,
            "sender_name": "NIWI Team",
            "sender_address": "test@orchvate.in",
            "notifications_enabled": False,
            "support_email": "support@orchvate.in",
            "low_visibility_threshold": 50
        }
        self.audit_logs = []

MEM_STORE = InMemoryStore()


class MockConnectionInfo:
    def __init__(self):
        self.transaction_status = psycopg2.extensions.TRANSACTION_STATUS_IDLE
        self.status = 1
        self.server_version = 140000


class MockCursor:
    def __init__(self, store: InMemoryStore, dict_cursor: bool = False, conn=None):
        self.store = store
        self.dict_cursor = dict_cursor
        self.conn = conn
        self._results = []
        self._index = 0
        self.rowcount = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def close(self):
        pass

    def _format_row(self, row):
        if self.dict_cursor:
            return psycopg2.extras.RealDictRow(row) if not isinstance(row, psycopg2.extras.RealDictRow) else row
        if isinstance(row, dict):
            return tuple(row.values())
        return row

    def execute(self, sql, params=None):
        self._results = []
        self._index = 0
        self.rowcount = 0
        sql_clean = " ".join(sql.strip().split())
        sql_lower = sql_clean.lower()
        p = params or ()

        # 0. Test Temp Table Exception check
        if "from test_reset" in sql_lower:
            raise psycopg2.ProgrammingError('relation "test_reset" does not exist')

        # 1. Advisory Lock / Health checks / Literal SELECTs
        if "pg_advisory_xact_lock" in sql_lower:
            self._results = [{"locked": True}] if self.dict_cursor else [(True,)]
            self.rowcount = 1
            return

        if sql_lower.startswith("select") and "from" not in sql_lower:
            if p:
                val = p[0]
            else:
                raw = sql_lower.replace("select", "").strip()
                try:
                    val = int(raw)
                except ValueError:
                    val = raw
            self._results = [{"val": val}] if self.dict_cursor else [(val,)]
            self.rowcount = 1
            return

        # 2. Admin Users Lookups
        if "from admin_users" in sql_lower and sql_lower.startswith("select"):
            email = p[0].lower() if p else ""
            user = self.store.admin_users.get(email)
            if user:
                if "select role from admin_users" in sql_lower:
                    self._results = [{"role": user["role"]}] if self.dict_cursor else [(user["role"],)]
                else:
                    self._results = [user] if self.dict_cursor else [(user["email"], user["role"])]
                self.rowcount = 1
            return

        if "delete from admin_users" in sql_lower:
            for email in p:
                self.store.admin_users.pop(email.lower(), None)
            self.rowcount = len(p)
            return

        if "insert into admin_users" in sql_lower:
            email = p[0].lower() if p else "admin@test.com"
            if len(p) > 1:
                role = p[1]
            elif "'super'" in sql_lower:
                role = "super"
            else:
                role = "admin"
            self.store.admin_users[email] = {
                "id": str(uuid.uuid4()), "email": email, "role": role, "is_active": True
            }
            self.rowcount = 1
            return

        # 3. Organizations
        if "insert into organizations" in sql_lower:
            approval_status = "approved"
            if "(id, name" in sql_lower and len(p) >= 2:
                org_id = str(p[0])
                name = str(p[1])
                if len(p) >= 5 and p[4] in ("pending", "rejected", "approved"):
                    approval_status = p[4]
            else:
                org_id = str(uuid.uuid4())
                if p:
                    name = str(p[0])
                    if len(p) >= 4 and p[3] in ("pending", "rejected", "approved"):
                        approval_status = p[3]
                    elif len(p) >= 2 and p[1] in ("pending", "rejected", "approved"):
                        approval_status = p[1]
                else:
                    m = re.search(r"values\s*\(\s*'([^']+)'", sql, re.IGNORECASE)
                    name = m.group(1) if m else "Test Org"

            org = {
                "id": org_id,
                "name": name,
                "is_active": True,
                "is_deleted": False,
                "approval_status": approval_status,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            self.store.organizations[org_id] = org
            if self.conn is not None:
                self.conn._uncommitted.append(lambda: self.store.organizations.pop(org_id, None))
            self.rowcount = 1
            if "returning" in sql_lower:
                self._results = [org] if self.dict_cursor else [(org_id, name)]
            return

        if "select count(*)" in sql_lower and "from organizations" in sql_lower:
            if "concurrent test" in sql_lower:
                cnt = len([o for o in self.store.organizations.values() if o.get("name", "").startswith("Concurrent Test")])
            else:
                cnt = len([o for o in self.store.organizations.values() if not o.get("is_deleted")])
            self._results = [{"count": cnt}] if self.dict_cursor else [(cnt,)]
            self.rowcount = 1
            return

        if "from organizations" in sql_lower and sql_lower.startswith("select"):
            if "where lower(trim(name)) =" in sql_lower:
                name_q = p[0].strip().lower()
                matches = [o for o in self.store.organizations.values() if o["name"].strip().lower() == name_q and not o["is_deleted"]]
                self._results = matches if self.dict_cursor else [(m["id"], m["name"], m["approval_status"], m["is_active"]) for m in matches]
            elif "where id = %s" in sql_lower:
                org_id = str(p[0])
                o = self.store.organizations.get(org_id)
                if o:
                    if sql_lower.startswith("select name from"):
                        self._results = [{"name": o["name"]}] if self.dict_cursor else [(o["name"],)]
                    else:
                        self._results = [o] if self.dict_cursor else [(o["id"], o["name"], o["is_active"], o["is_deleted"], o["approval_status"])]
            else:
                matches = [o for o in self.store.organizations.values() if not o["is_deleted"]]
                self._results = matches if self.dict_cursor else [tuple(m.values()) for m in matches]
            self.rowcount = len(self._results)
            return

        if "delete from organizations" in sql_lower:
            if p:
                self.store.organizations.pop(str(p[0]), None)
            self.rowcount = 1
            return

        # 4. Submissions
        if "insert into submissions" in sql_lower:
            sub_id = str(uuid.uuid4())
            if isinstance(p, dict):
                name = p.get("name", "User")
                email = p.get("email", "user@test.com")
                company = p.get("company_name", "Company")
                org_id = str(p.get("organization_id")) if p.get("organization_id") else None
                source = p.get("submission_source", "DIRECT")
                inv_id = str(p.get("invitation_id")) if p.get("invitation_id") else None
            elif len(p) == 1:
                org_id = str(p[0])
                name = "Test User"
                email = "testuser@test.com"
                company = "Test Organization Security"
                source = "DIRECT"
                inv_id = None
            elif len(p) >= 6:
                name = p[0]
                email = p[1]
                company = p[2]
                org_id = str(p[5]) if p[5] else None
                source = p[6] if len(p) > 6 else "DIRECT"
                inv_id = None
            else:
                name = "User"
                email = "user@test.com"
                company = "Company"
                org_id = str(p[3]) if len(p) > 3 and p[3] else None
                source = "DIRECT"
                inv_id = None

            sub = {
                "id": sub_id,
                "name": name,
                "email": email,
                "company_name": company,
                "organization_id": org_id,
                "submission_source": source,
                "status": "pending",
                "submitted_at": datetime.now(timezone.utc),
                "overall_avg": 14.5,
                "overall_level": "Developing",
                "answers": {},
                "invitation_id": inv_id
            }
            self.store.submissions[sub_id] = sub
            if self.conn is not None:
                self.conn._uncommitted.append(lambda: self.store.submissions.pop(sub_id, None))
            self.rowcount = 1
            if "returning" in sql_lower:
                self._results = [sub] if self.dict_cursor else [(sub_id,)]
            return

        if "from app_settings" in sql_lower:
            settings_dict = {
                "id": 1,
                "notification_email": "",
                "notification_cc_email": "",
                "notifications_enabled": False,
                "sender_name": "NIWI Team",
                "sender_address": "test@orchvate.in",
                "crm_sync_enabled": False,
                "hubspot_api_key": "",
                "support_email": "support@orchvate.in",
                "low_visibility_threshold": 50
            }
            if "crm_sync_enabled" in sql_lower and "notification_email" not in sql_lower:
                self._results = [{"crm_sync_enabled": False}] if self.dict_cursor else [(False,)]
            elif "notification_email" in sql_lower:
                self._results = [settings_dict] if self.dict_cursor else [("", "", False, "NIWI Team", "test@orchvate.in")]
            else:
                self._results = [settings_dict] if self.dict_cursor else [tuple(settings_dict.values())]
            self.rowcount = 1
            return

        if "from submissions" in sql_lower and sql_lower.startswith("select"):
            if "where lower(trim(email)) =" in sql_lower:
                email_q = p[0].strip().lower() if p else ""
                now = datetime.now(timezone.utc)
                matches = [
                    s for s in self.store.submissions.values()
                    if s.get("email", "").strip().lower() == email_q
                    and (now - s.get("submitted_at", now)).total_seconds() < 300
                ]
                self._results = matches if self.dict_cursor else [(m["id"],) for m in matches]
            elif "where id = %s" in sql_lower:
                sub_id = str(p[0])
                s = self.store.submissions.get(sub_id)
                if s:
                    self._results = [s] if self.dict_cursor else [tuple(s.values())]
            else:
                subs = list(self.store.submissions.values())
                self._results = subs if self.dict_cursor else [tuple(s.values()) for s in subs]
            self.rowcount = len(self._results)
            return

        if "update submissions set" in sql_lower:
            if "organization_id = %s" in sql_lower and len(p) >= 3:
                new_org = str(p[0])
                new_name = p[1]
                sub_id = str(p[2])
                if sub_id in self.store.submissions:
                    self.store.submissions[sub_id]["organization_id"] = new_org
                    self.store.submissions[sub_id]["company_name"] = new_name
            self.rowcount = 1
            return

        if "delete from submissions" in sql_lower:
            if p:
                self.store.submissions.pop(str(p[0]), None)
            else:
                self.store.submissions.clear()
            self.rowcount = 1
            return

        # 5. Invitations
        if "insert into organization_invitations" in sql_lower:
            inv_id = str(uuid.uuid4())
            org_id = str(p[0])
            tok_hash = p[1]
            exp = p[2] if len(p) > 2 else datetime.now(timezone.utc) + timedelta(days=7)
            org = self.store.organizations.get(org_id, {})
            max_sub = 1 if ", 1, 0," in sql_lower else 100
            inv = {
                "id": inv_id,
                "organization_id": org_id,
                "token_hash": tok_hash,
                "is_active": True,
                "expires_at": exp,
                "created_by": "test",
                "current_submissions": 0,
                "submission_count": 0,
                "max_submissions": max_sub,
                "revoked_at": None,
                "org_name": org.get("name", "Test Org"),
                "org_active": org.get("is_active", True),
                "org_deleted": org.get("is_deleted", False)
            }
            self.store.invitations[tok_hash] = inv
            self.store.invitations[inv_id] = inv
            self.rowcount = 1
            if "returning" in sql_lower:
                self._results = [inv] if self.dict_cursor else [(inv_id,)]
            return

        if "from organization_invitations" in sql_lower and sql_lower.startswith("select"):
            param_val = str(p[0]) if p else ""
            matches = []
            if "where id = %s" in sql_lower:
                matches = [inv for inv in self.store.invitations.values() if inv.get("id") == param_val]
            else:
                matches = [inv for inv in self.store.invitations.values() if inv.get("token_hash") == param_val]
            if matches:
                inv = matches[0]
                org = self.store.organizations.get(inv.get("organization_id"), {})
                inv_copy = dict(inv)
                inv_copy["org_name"] = org.get("name", inv.get("org_name", "Test Org"))
                inv_copy["org_active"] = org.get("is_active", True)
                inv_copy["org_deleted"] = org.get("is_deleted", False)
                self._results = [inv_copy] if self.dict_cursor else [tuple(inv_copy.values())]
            self.rowcount = len(self._results)
            return

        if "update organization_invitations" in sql_lower:
            if "submission_count = submission_count + 1" in sql_lower and p:
                target_id = str(p[0])
                seen = set()
                for inv in self.store.invitations.values():
                    if inv.get("id") == target_id and id(inv) not in seen:
                        seen.add(id(inv))
                        inv["submission_count"] = inv.get("submission_count", 0) + 1
                        inv["current_submissions"] = inv["submission_count"]
            self.rowcount = 1
            return

        if "delete from organization_invitations" in sql_lower:
            if p:
                target = str(p[0])
                to_delete = [k for k, v in self.store.invitations.items() if v.get("id") == target or v.get("organization_id") == target]
                for k in to_delete:
                    self.store.invitations.pop(k, None)
            self.rowcount = 1
            return

        # 6. Reassignments & Links
        if "insert into submission_reassignments" in sql_lower:
            self.store.reassignments.append({
                "submission_id": str(p[0]),
                "old_organization_id": str(p[1]),
                "new_organization_id": str(p[2]),
                "reason": p[4] if len(p) > 4 else "reassigned",
                "reassigned_at": datetime.now(timezone.utc)
            })
            self.rowcount = 1
            return

        if "from submission_reassignments" in sql_lower and sql_lower.startswith("select"):
            sub_id = str(p[0]) if p else ""
            matches = [r for r in self.store.reassignments if r["submission_id"] == sub_id]
            self._results = matches if self.dict_cursor else [tuple(m.values()) for m in matches]
            self.rowcount = len(self._results)
            return

        if "insert into org_submission_links" in sql_lower:
            self.store.links.append({
                "org": p[0] if len(p) > 0 else "",
                "sub": p[1] if len(p) > 1 else "",
                "name": p[2] if len(p) > 2 else ""
            })
            self.rowcount = 1
            return

        # 7. Draft Submissions
        if "insert into draft_submissions" in sql_lower:
            draft_id = str(uuid.uuid4())
            email = p[0] if len(p) > 0 else ""
            company = p[1] if len(p) > 1 else ""
            form_state = p[2] if len(p) > 2 else "{}"
            current_step = p[3] if len(p) > 3 else 1
            if isinstance(form_state, str):
                try:
                    form_state = json.loads(form_state)
                except Exception:
                    pass
            draft = {
                "id": draft_id,
                "email": email,
                "company_name": company,
                "form_state": form_state,
                "current_step": current_step,
                "submitted": False
            }
            self.store.drafts[draft_id] = draft
            self.rowcount = 1
            if "returning" in sql_lower:
                self._results = [draft] if self.dict_cursor else [(draft_id,)]
            return

        if "from draft_submissions" in sql_lower and sql_lower.startswith("select"):
            draft_id = str(p[0]) if p else ""
            d = self.store.drafts.get(draft_id)
            if d:
                if "select submitted from" in sql_lower:
                    self._results = [{"submitted": d["submitted"]}] if self.dict_cursor else [(d["submitted"],)]
                else:
                    self._results = [d] if self.dict_cursor else [(d["email"], d["company_name"], d["form_state"], d["current_step"], d["submitted"])]
            self.rowcount = len(self._results)
            return

        if "update draft_submissions" in sql_lower:
            if "submitted = true" in sql_lower and p:
                draft_id = str(p[0])
                if draft_id in self.store.drafts:
                    self.store.drafts[draft_id]["submitted"] = True
            elif "email = %s" in sql_lower and p:
                draft_id = str(p[4]) if len(p) > 4 else ""
                if draft_id in self.store.drafts:
                    self.store.drafts[draft_id]["email"] = p[0]
                    self.store.drafts[draft_id]["company_name"] = p[1]
                    try:
                        self.store.drafts[draft_id]["form_state"] = json.loads(p[2]) if isinstance(p[2], str) else p[2]
                    except Exception:
                        self.store.drafts[draft_id]["form_state"] = p[2]
                    self.store.drafts[draft_id]["current_step"] = p[3]
            self.rowcount = 1
            if "returning" in sql_lower:
                self._results = [{"id": draft_id}] if self.dict_cursor else [(draft_id,)]
            return

        # Default fallback
        self.rowcount = 1

    def fetchone(self):
        if self._index < len(self._results):
            row = self._results[self._index]
            self._index += 1
            return self._format_row(row)
        return None

    def fetchall(self):
        res = [self._format_row(r) for r in self._results[self._index:]]
        self._index = len(self._results)
        return res


class MockConnection:
    def __init__(self, store: InMemoryStore):
        self.store = store
        self.closed = 0
        self.autocommit = False
        self.info = MockConnectionInfo()
        self._uncommitted = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()

    def cursor(self, cursor_factory=None):
        is_dict = cursor_factory == psycopg2.extras.RealDictCursor or (cursor_factory and getattr(cursor_factory, "__name__", "") == "RealDictCursor")
        return MockCursor(self.store, dict_cursor=bool(is_dict), conn=self)

    def commit(self):
        self._uncommitted.clear()

    def rollback(self):
        for undo in reversed(self._uncommitted):
            undo()
        self._uncommitted.clear()

    def close(self):
        self.closed = 1


# Globally redirect psycopg2.connect to the isolated in-memory test engine
_orig_psycopg2_connect = psycopg2.connect
def _isolated_mock_connect(*args, **kwargs):
    return MockConnection(MEM_STORE)

psycopg2.connect = _isolated_mock_connect


@pytest.fixture(autouse=True)
def clean_test_state():
    """Clear dashboard memory cache and ensure clean test state."""
    from app.api.routes import dashboard_cache
    dashboard_cache.clear()
    yield
    dashboard_cache.clear()


@pytest.fixture(scope="session", autouse=True)
def verify_test_database_isolation():
    """Verify and report database target for every test run to guarantee safety."""
    host = os.environ.get("PGHOST", "")
    db = os.environ.get("PGDATABASE", "")
    target = f"{host}:{os.environ.get('PGPORT', '5432')}/{db}"
    if "postgres.database.azure.com" in host.lower() or "generative-ai" in host.lower():
        pytest.fail(f"CRITICAL SAFETY VIOLATION: Test suite attempted to target production database ({target})!")
    print(f"\n========================================================")
    print(f" [TEST DATABASE TARGET]: {target}")
    print(f" [ISOLATION STATUS]: PRODUCTION AZURE ACCESS STRICTLY BLOCKED")
    print(f"========================================================\n")
    yield


@pytest.fixture(autouse=True)
def mock_acs_email_globally():
    """Globally mock all Azure Communication Services email operations during testing."""
    with patch("app.services.settings_service.send_acs_email", return_value={"status": "sent", "id": "mock-email-id"}), \
         patch("app.api.org.send_acs_email", return_value={"status": "sent", "id": "mock-email-id"}), \
         patch("azure.communication.email.EmailClient.from_connection_string", MagicMock()):
        yield


@pytest.fixture(autouse=True)
def disable_rate_limits():
    """Disable rate limiting in test sessions to prevent 429 flake."""
    from app.main import app
    orig_enabled = getattr(app.state.limiter, "enabled", True)
    app.state.limiter.enabled = False
    yield
    app.state.limiter.enabled = orig_enabled
