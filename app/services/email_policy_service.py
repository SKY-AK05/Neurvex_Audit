"""
email_policy_service.py — Corporate Email Eligibility Verification Service
Validates email syntax and verifies eligibility against an in-memory blocklist
of free, personal, and disposable email providers.
Accepts all valid corporate domains without requiring OTP, mailbox authentication,
or database lookups.
"""

import logging
import os
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)

# RFC 5322 compliant simplified email validation regex
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
)

# Comprehensive set of known personal, consumer, and disposable email providers.
# Stored as an in-memory set for O(1) instantaneous lookups (<0.01 ms).
PERSONAL_EMAIL_DOMAINS: set[str] = {
    # Google
    "gmail.com",
    "googlemail.com",
    # Microsoft Consumer
    "outlook.com",
    "hotmail.com",
    "live.com",
    "msn.com",
    "passport.com",
    "windowslive.com",
    "hotmail.co.uk",
    "hotmail.fr",
    "hotmail.de",
    "hotmail.es",
    "hotmail.it",
    "outlook.co.uk",
    "outlook.fr",
    "outlook.de",
    "outlook.in",
    # Yahoo Consumer
    "yahoo.com",
    "ymail.com",
    "rocketmail.com",
    "yahoo.co.in",
    "yahoo.co.uk",
    "yahoo.ca",
    "yahoo.com.au",
    "yahoo.fr",
    "yahoo.de",
    "yahoo.es",
    "yahoo.it",
    "yahoo.co.jp",
    # Apple Consumer
    "icloud.com",
    "me.com",
    "mac.com",
    # AOL
    "aol.com",
    "aim.com",
    # Privacy / Freemium Webmail
    "proton.me",
    "protonmail.com",
    "pm.me",
    "tutanota.com",
    "tutamail.com",
    "tuta.io",
    "duck.com",
    # Other Global Consumer Providers
    "zoho.com",  # Personal consumer Zoho accounts; corporate Zoho uses custom domains
    "mail.com",
    "email.com",
    "usa.com",
    "post.com",
    "dr.com",
    "consultant.com",
    "gmx.com",
    "gmx.net",
    "gmx.de",
    "web.de",
    "yandex.com",
    "yandex.ru",
    "ya.ru",
    "rediffmail.com",
    "rediff.com",
    "inbox.com",
    "fastmail.com",
    "lycos.com",
    # Disposable / Temporary Mail
    "mailinator.com",
    "guerrillamail.com",
    "guerrillamail.net",
    "guerrillamail.biz",
    "guerrillamail.org",
    "sharklasers.com",
    "grr.la",
    "10minutemail.com",
    "tempmail.com",
    "throwawaymail.com",
    "trashmail.com",
    "dispostable.com",
    "yopmail.com",
    "yopmail.fr",
    "yopmail.net",
}

# Optional environment variable extension for operators
_extra_blocked = os.environ.get("NIWI_BLOCKED_EMAIL_DOMAINS", "")
if _extra_blocked:
    for domain in _extra_blocked.split(","):
        d = domain.strip().lower()
        if d:
            PERSONAL_EMAIL_DOMAINS.add(d)


def extract_and_normalize_domain(email: str) -> Optional[str]:
    """Extracts and lowercases the domain portion from an email address."""
    if not email or "@" not in email:
        return None
    parts = email.strip().split("@")
    if len(parts) != 2:
        return None
    domain = parts[1].strip().lower()
    return domain or None


def validate_email_syntax(email: str) -> bool:
    """Validates standard email syntax."""
    if not email or not isinstance(email, str):
        return False
    email = email.strip()
    if len(email) > 254:
        return False
    return bool(EMAIL_REGEX.match(email))


def check_corporate_email_eligibility(email: str) -> dict[str, Any]:
    """
    Checks whether a supplied email address is eligible under the corporate email policy.
    Accepts any corporate domain; rejects invalid syntax and personal/disposable providers.
    Does not require mailbox verification, DNS lookups, or pre-registration.
    """
    if not email or not isinstance(email, str) or not email.strip():
        return {
            "eligible": False,
            "email_verified": False,
            "domain": None,
            "error": "Email address cannot be empty.",
        }

    clean_email = email.strip()

    if not validate_email_syntax(clean_email):
        return {
            "eligible": False,
            "email_verified": False,
            "domain": None,
            "error": "Please enter a valid email address.",
        }

    domain = extract_and_normalize_domain(clean_email)
    if not domain or "." not in domain:
        return {
            "eligible": False,
            "email_verified": False,
            "domain": domain,
            "error": "Please enter a valid email address with a valid domain name.",
        }

    # Check against personal provider blocklist
    if domain in PERSONAL_EMAIL_DOMAINS:
        return {
            "eligible": False,
            "email_verified": False,
            "domain": domain,
            "error": f"'{domain}' is a personal or free email provider. Please use your corporate work email.",
        }

    # Any other valid domain is eligible as a corporate email
    return {
        "eligible": True,
        "email_verified": False,
        "domain": domain,
    }

