import os
import time
import logging
from datetime import datetime, timezone
import requests
from typing import Dict, Any

logger = logging.getLogger(__name__)

HUBSPOT_ACCESS_TOKEN = os.environ.get("HUBSPOT_ACCESS_TOKEN", "")

def make_hubspot_request(method: str, url: str, json_data: Any = None, retries: int = 3) -> Dict[str, Any]:
    if not HUBSPOT_ACCESS_TOKEN:
        logger.warning("HubSpot token missing. CRM Sync bypassed.")
        return {}

    headers = {
        "Authorization": f"Bearer {HUBSPOT_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    delay = 1
    for attempt in range(retries):
        try:
            response = requests.request(method, url, headers=headers, json=json_data, timeout=10)
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", delay))
                logger.warning(f"HubSpot rate limit hit. Waiting {retry_after}s to retry...")
                time.sleep(retry_after)
                continue
            
            if response.status_code in (200, 201, 204):
                return response.json() if response.content else {}
                
            logger.error(f"HubSpot API returned status {response.status_code}: {response.text}")
            response.raise_for_status()
        except Exception as e:
            logger.error(f"HubSpot request error (attempt {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
            else:
                raise e
    return {}

def sync_to_hubspot(data: Dict[str, Any], score_data: Dict[str, Any], submission_id: str):
    """
    Syncs the audit submission to HubSpot. Runs inside a background task.
    """
    email = data.get("email")
    name = data.get("name")
    company_name = data.get("company_name")
    designation = data.get("designation")
    contact_number = data.get("contact_number")
    
    overall_avg = score_data.get("overall_avg", 0.0)
    overall_level = score_data.get("overall_level", "Foundational")
    
    # Map score to deal stages
    # Foundational = Prospect, Early Progress = Qualified Lead, Developing = Opportunity, Leading = Closed Won
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
        logger.error(f"Could not query contact search: {e}")

    # Custom properties to write on Contact
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
    else:
        contact_url = "https://api.hubapi.com/crm/v3/objects/contacts"
        try:
            contact_res = make_hubspot_request("POST", contact_url, {"properties": properties})
            contact_id = contact_res.get("id")
        except Exception as e:
            logger.error(f"Contact creation failed: {e}")
            return # Abort if contact cannot be created

    # 3. Create Deal
    deal_url = "https://api.hubapi.com/crm/v3/objects/deals"
    deal_properties = {
        "dealname": f"Neurvex Audit Deal — {company_name}",
        "dealstage": deal_stage,
        "pipeline": "default",
        "amount": "0",  # Consultation deal value can be specified
        "maturity_score": str(overall_avg),
        "maturity_level": overall_level,
        "submission_date": datetime.now(timezone.utc).date().isoformat()
    }
    
    try:
        deal_res = make_hubspot_request("POST", deal_url, {"properties": deal_properties})
        deal_id = deal_res.get("id")
        
        # 4. Associate Deal to Contact
        if deal_id and contact_id:
            association_url = f"https://api.hubapi.com/crm/v3/objects/deals/{deal_id}/associations/contacts/{contact_id}/3"
            make_hubspot_request("PUT", association_url)
            logger.info(f"HubSpot Sync complete for submission {submission_id}")
    except Exception as e:
        logger.error(f"Failed to create/associate HubSpot Deal: {e}")
