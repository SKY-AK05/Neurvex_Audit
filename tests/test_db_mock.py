import uuid
import re
from datetime import datetime, timezone

class InMemoryDB:
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
        self.reassignments = []
        self.links = []
        self.settings = {
            "sender_name": "NIWI Team",
            "sender_address": "test@orchvate.in",
            "notifications_enabled": True
        }

db = InMemoryDB()
print("DB initialized successfully")

