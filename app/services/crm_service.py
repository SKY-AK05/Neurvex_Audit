import os
import time
import logging
from datetime import datetime, timezone
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

HUBSPOT_ACCESS_TOKEN = os.environ.get("HUBSPOT_ACCESS_TOKEN", "")


def get_hubspot_token() -> str:
    """Retrieve HubSpot access token from module attribute, environment, or config."""
    global HUBSPOT_ACCESS_TOKEN
    return (HUBSPOT_ACCESS_TOKEN or os.environ.get("HUBSPOT_ACCESS_TOKEN", "")).strip()


def is_hubspot_configured() -> bool:
    """Check if HubSpot CRM integration is configured."""
    return bool(get_hubspot_token())


def make_hubspot_request(method: str, url: str, json_data: Any = None, retries: int = 3, timeout: int = 10) -> Dict[str, Any]:
    token = get_hubspot_token()
    if not token:
        logger.warning("HubSpot token missing. CRM request bypassed.")
        return {}

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    delay = 1
    for attempt in range(retries):
        try:
            response = requests.request(method, url, headers=headers, json=json_data, timeout=timeout)
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", delay))
                logger.warning(f"HubSpot rate limit hit. Waiting {retry_after}s to retry...")
                time.sleep(retry_after)
                continue

            if response.status_code in (200, 201, 204):
                return response.json() if response.content else {}

            logger.error(f"HubSpot API returned status {response.status_code}: {response.text}")
            response.raise_for_status()
        except requests.exceptions.Timeout as te:
            logger.warning(
                "HubSpot API request timed out (attempt %d/%d) for %s %s. Operation may have been received remotely.",
                attempt + 1, retries, method, url
            )
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
            else:
                raise te
        except Exception as e:
            logger.error(f"HubSpot request error (attempt {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
            else:
                raise e
    return {}


def sync_to_hubspot(
    data: Dict[str, Any],
    score_data: Dict[str, Any],
    submission_id: str,
    known_deal_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Syncs the audit submission to HubSpot with deal idempotency.
    
    1. Checks if HubSpot integration is configured. If not, returns SKIPPED.
    2. Searches/creates/updates Contact by email.
    3. Searches for existing Deal using stable submission ID identifier.
    4. Updates existing deal if found, otherwise creates new deal.
    5. Associates deal with contact.
    6. Returns status dict with deal_id and contact_id.
    """
    if not is_hubspot_configured():
        logger.info("HubSpot access token not configured, skipping CRM sync for submission %s", submission_id)
        return {
            "status": "SKIPPED",
            "reason": "HUBSPOT_ACCESS_TOKEN not configured"
        }

    email = data.get("email")
    name = data.get("name") or ""
    company_name = data.get("company_name") or ""
    designation = data.get("designation") or ""
    contact_number = data.get("contact_number") or ""

    overall_avg = score_data.get("overall_avg", 0.0)
    overall_level = score_data.get("overall_level", "Foundational")

    # Map score to deal stages
    if overall_avg <= 6:
        deal_stage = "prospect"
    elif overall_avg <= 11:
        deal_stage = "qualifiedlead"
    elif overall_avg <= 15:
        deal_stage = "opportunity"
    else:
        deal_stage = "closedwon"

    # 1. Search if contact already exists
    search_url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
    search_query = {
        "filterGroups": [{
            "filters": [{
                "propertyName": "email",
                "operator": "EQ",
                "value": email
            }]
        }]
    }

    contact_id = None
    try:
        search_res = make_hubspot_request("POST", search_url, search_query)
        if search_res.get("results"):
            contact_id = search_res["results"][0]["id"]
    except Exception as e:
        logger.warning(f"Could not query contact search (will attempt creation): {e}")

    properties = {
        "email": email,
        "firstname": name.split(" ")[0] if " " in name else name,
        "lastname": name.split(" ")[1] if " " in name else "",
        "company": company_name,
        "jobtitle": designation,
        "phone": contact_number,
        "maturity_score": str(overall_avg),
        "maturity_level": overall_level,
        "audit_id": submission_id
    }

    # 2. Create or Update Contact
    if contact_id:
        contact_url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
        try:
            make_hubspot_request("PATCH", contact_url, {"properties": properties})
        except Exception as e:
            logger.error(f"Contact update failed: {e}")
            raise RuntimeError(f"HubSpot contact update failed: {e}") from e
    else:
        contact_url = "https://api.hubapi.com/crm/v3/objects/contacts"
        try:
            contact_res = make_hubspot_request("POST", contact_url, {"properties": properties})
            contact_id = contact_res.get("id")
            if not contact_id:
                raise RuntimeError("HubSpot contact creation succeeded without returning an id")
        except Exception as e:
            logger.error(f"Contact creation failed: {e}")
            raise RuntimeError(f"HubSpot contact creation failed: {e}") from e

    # 3. Idempotent Deal Management
    # Use stable submission ID in dealname and description for business identification
    stable_deal_name = f"NeuroMark Audit Deal — {company_name} [{submission_id}]"
    deal_properties = {
        "dealname": stable_deal_name,
        "dealstage": deal_stage,
        "pipeline": "default",
        "amount": "0",
        "description": f"NIWI Submission ID: {submission_id}",
        "maturity_score": str(overall_avg),
        "maturity_level": overall_level,
        "submission_date": datetime.now(timezone.utc).date().isoformat()
    }

    deal_id = known_deal_id

    # If deal ID not already known, search for an existing deal by dealname
    if not deal_id:
        deal_search_url = "https://api.hubapi.com/crm/v3/objects/deals/search"
        deal_search_query = {
            "filterGroups": [{
                "filters": [{
                    "propertyName": "dealname",
                    "operator": "EQ",
                    "value": stable_deal_name
                }]
            }],
            "properties": ["dealname", "dealstage", "pipeline", "amount"]
        }
        try:
            deal_search_res = make_hubspot_request("POST", deal_search_url, deal_search_query)
            if deal_search_res.get("results"):
                deal_id = deal_search_res["results"][0]["id"]
                logger.info("Found existing HubSpot deal %s for submission %s, updating deal", deal_id, submission_id)
        except Exception as e:
            logger.warning("Could not query deal search for submission %s: %s", submission_id, e)

    # Update existing deal or create new one
    if deal_id:
        update_url = f"https://api.hubapi.com/crm/v3/objects/deals/{deal_id}"
        try:
            make_hubspot_request("PATCH", update_url, {"properties": deal_properties})
            logger.info("Successfully updated existing HubSpot deal %s for submission %s", deal_id, submission_id)
        except Exception as e:
            logger.error("Failed to update existing HubSpot deal %s: %s", deal_id, e)
            raise RuntimeError(f"HubSpot deal update failed: {e}") from e
    else:
        create_url = "https://api.hubapi.com/crm/v3/objects/deals"
        try:
            deal_res = make_hubspot_request("POST", create_url, {"properties": deal_properties})
            deal_id = deal_res.get("id")
            if not deal_id:
                raise RuntimeError("HubSpot deal creation succeeded without returning an id")
            logger.info("Successfully created new HubSpot deal %s for submission %s", deal_id, submission_id)
        except requests.exceptions.Timeout as te:
            logger.error(
                "HubSpot deal creation timed out for submission %s. The deal may exist remotely.",
                submission_id
            )
            raise RuntimeError(
                f"HubSpot deal creation timed out for submission {submission_id}. "
                "Idempotency search will reconcile on retry."
            ) from te
        except Exception as e:
            logger.error(f"Failed to create HubSpot Deal for submission {submission_id}: {e}")
            raise RuntimeError(f"HubSpot Deal creation failed: {e}") from e

    # 4. Associate Deal to Contact
    if deal_id and contact_id:
        try:
            association_url = f"https://api.hubapi.com/crm/v3/objects/deals/{deal_id}/associations/contacts/{contact_id}/3"
            make_hubspot_request("PUT", association_url)
            logger.info("HubSpot association complete [deal=%s, contact=%s] for submission %s", deal_id, contact_id, submission_id)
        except Exception as e:
            logger.error("Failed to associate deal %s with contact %s: %s", deal_id, contact_id, e)
            raise RuntimeError(f"HubSpot deal-contact association failed: {e}") from e

    return {
        "status": "SYNCED",
        "deal_id": deal_id,
        "contact_id": contact_id
    }
