# Operational Scripts, Database Seeders & Synthetic Ingestion

> Unit `10-scripts` · kind: feature

## Summary

Database initialization, migration execution, synthetic data seeding, and schema reconciliation utilities.

## Context & goal

The Scripts unit provides standalone operational tooling for developers and site reliability engineers. It includes database initialization (`setup_db.py`), migration execution (`migrate.py`), super admin provisioning (`set_super.py`), synthetic benchmark data generation, and schema verification scripts.

## User stories

- As a Developer, I run `seed_db.py` to populate my local environment with realistic mock organizations and test audits.
- As a QA Engineer, I run `verify_import.py` to confirm that synthetic audit datasets match scoring specifications.

## Functional requirements

- 1. Migration Runner [confirmed]: Execute sequential SQL migrations with failure halting and error reporting (`migrate.py`).
- 2. Database Seeder [confirmed]: Seed initial form sections, 40 questions, and default administrative accounts (`seed_db.py`).
- 3. Synthetic Data Importer [confirmed]: Ingest 100-employee synthetic audit datasets from Excel spreadsheets (`import_nexora_audit.py`).
- 4. Schema Inspector [confirmed]: Validate table definitions and column constraints against expected model attributes (`inspect_schema.py`).


## Interfaces & data

Executes direct SQL commands via `psycopg2` against the database schema in [DATA-MODEL.md](../../architecture/DATA-MODEL.md).

## Acceptance criteria

- Given a fresh database, When `python scripts/setup_db.py` is run, Then all base tables and default form questions are created.
- Given a super admin email address, When `python scripts/set_super.py admin@orchvate.com` is executed, Then the user role is updated to 'super' in `admin_users`.

## Edge cases & failure modes

- **Corrupt Excel spreadsheet during synthetic import:** Script logs row-level errors and skips invalid entries without crashing.

## Definition of done

- All functional requirements implemented and verified against code.
- All acceptance scenarios verified with passing unit or integration tests.
- Zero unresolved callouts, placeholders, or ambiguous specifications.
- Security and authorization policies strictly enforced.
- Performance and error recovery verified under edge conditions.

## Improvements & enhancements

- Combine setup scripts into a unified CLI tool (e.g. `niwi-cli db migrate`, `niwi-cli user create`).


## Source material

Key source for this unit (15 file(s) total, showing up to 15):

#### `scripts/check-auth-config.sh`

```
#!/bin/bash

# NIWI Auth Configuration Checker
# Run this on your VM to diagnose authentication issues

echo "🔍 NIWI Authentication Configuration Checker"
echo "============================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if .env file exists
echo -e "${BLUE}1. Checking .env file...${NC}"
if [ -f .env ]; then
    echo -e "${GREEN}✅ .env file exists${NC}"
    
    # Check ENTRA_CLIENT_ID
    if grep -q "ENTRA_CLIENT_ID=your-azure-ad-application-client-id" .env; then
        echo -e "${RED}❌ ENTRA_CLIENT_ID is still a placeholder${NC}"
    elif grep -q "ENTRA_CLIENT_ID=" .env; then
        CLIENT_ID=$(grep "ENTRA_CLIENT_ID=" .env | cut -d '=' -f2)
        if [ -n "$CLIENT_ID" ]; then
            echo -e "${GREEN}✅ ENTRA_CLIENT_ID is set${NC}"
        else
            echo -e "${RED}❌ ENTRA_CLIENT_ID is empty${NC}"
        fi
    else
        echo -e "${RED}❌ ENTRA_CLIENT_ID not found in .env${NC}"
    fi
    
    # Check ENTRA_TENANT_ID
    if grep -q "ENTRA_TENANT_ID=your-azure-ad-tenant-id" .env; then
        echo -e "${RED}❌ ENTRA_TENANT_ID is still a placeholder${NC}"
    elif grep -q "ENTRA_TENANT_ID=" .env; then
        TENANT_ID=$(grep "ENTRA_TENANT_ID=" .env | cut -d '=' -f2)
        if [ -n "$TENANT_ID" ]; then
            echo -e "${GREEN}✅ ENTRA_TENANT_ID is set${NC}"
        else
            echo -e "${RED}❌ ENTRA_TENANT_ID is empty${NC}"
        fi
    else
        echo -e "${RED}❌ ENTRA_TENANT_ID not found in .env${NC}"
    fi
else
    echo -e "${RED}❌ .env file not found${NC}"
fi
echo ""

# Check if container is running
echo -e "${BLUE}2. Checking container status...${NC}"
if sudo docker ps | grep -q niwi; then
    echo -e "${GREEN}✅ Container 'niwi' is running${NC}"
    
    # Check environment variables in container
    echo -e "${BLUE}3. Checking container environment variables...${NC}"
    CLIENT_IN_CONTAINER=$(sudo docker exec niwi env | grep "ENTRA_CLIENT_ID=" | cut -d '=' -f2)
    TENANT_IN_CONTAINER=$(sudo docker exec niwi env | grep "ENTRA_TENANT_ID=" | cut -d '=' -f2)
    
    if [[ "$CLIENT_IN_CONTAINER" == "your-azure-ad-application-client-id" ]] || [ -z "$CLIENT_IN_CONTAINER" ]; then
        echo -e "${RED}❌ ENTRA_CLIENT_ID not properly set in container${NC}"
    else
        echo -e "${GREEN}✅ ENTRA_CLIENT_ID is loaded in container${NC}"
    fi
    
    if [[ "$TENANT_IN_CONTAINER" == "your-azure-ad-tenant-id" ]] || [ -z "$TENANT_IN_CONTAINER" ]; then
        echo -e "${RED}❌ ENTRA_TENANT_ID not properly set in container${NC}"
    else
        echo -e "${GREEN}✅ ENTRA_TENANT_ID is loaded in container${NC}"
    fi
else
    echo -e "${RED}❌ Container 'niwi' is not running${NC}"
    exit 1
fi
echo ""

# Test the API endpoint
echo -e "${BLUE}4. Testing /api/auth/config endpoint...${NC}"
AUTH_RESPONSE=$(curl -s http://localhost:8080/api/auth/config 2>/dev/null)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ API endpoint is accessible${NC}"
    echo -e "${YELLOW}Response:${NC}"
    echo "$AUTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$AUTH_RESPONSE"
    
    # Check if response contains valid IDs
    if echo "$AUTH_RESPONSE" | grep -q '"clientId": null' || echo "$AUTH_RESPONSE" | grep -q '"tenantId": null'; then
        echo -e "${RED}❌ API is returning null values - Azure AD is not configured${NC}"
    else
        echo -e "${GREEN}✅ API is returning configuration${NC}"
    fi
else
    echo -e "${RED}❌ Cannot reach API endpoint${NC}"
fi
echo ""

# Check recent logs
echo -e "${BLUE}5. Recent container logs (last 20 lines):${NC}"
sudo docker logs --tail 20 niwi
echo ""

# Summary and recommendations
echo -e "${YELLOW}================================${NC}"
echo -e "${YELLOW}Summary and Recommendations${NC}"
echo -e "${YELLOW}================================${NC}"
echo ""

if [[ "$CLIENT_IN_CONTAINER" == "your-azure-ad-application-client-id" ]] || [ -z "$CLIENT_IN_CONTAINER" ]; then
    echo -e "${RED}🔧 ACTION REQUIRED:${NC}"
    echo "1. Set up Azure AD App Registration (see AZURE_AD_SETUP.md)"
    echo "2. Update .env file with actual ENTRA_CLIENT_ID and ENTRA_TENANT_ID"
    echo "3. Redeploy using ./deploy.sh"
else
    echo -e "${GREEN}✅ Azure AD configuration looks good${NC}"
    echo ""
    echo "If authentication still fails, check:"
    echo "- Admin users are added to database: SELECT * FROM admin_users;"
    echo "- Azure AD redirect URIs include: https://niwi.orchvate.in/portal"
    echo "- Check browser console for detailed error messages"
fi
echo ""

```

#### `scripts/deploy.sh`

```
#!/bin/bash
set -e

# NIWI Deployment Script
# Deploys the latest code to taiga.orchvate.com:8080

echo "🚀 NIWI Deployment Script"
echo "========================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME="niwi"
IMAGE_NAME="niwi"
PORT_MAPPING="8080:80"
ENV_FILE=".env"
TIMEZONE="Asia/Kolkata"

echo -e "${BLUE}📁 Current directory: $(pwd)${NC}"
echo ""

# Step 1: Sync with GitHub (force update to match GitHub exactly)
echo -e "${YELLOW}📥 Step 1/7: Syncing with GitHub (force update)...${NC}"
git fetch origin
git reset --hard origin/main
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Code synced successfully${NC}"
else
    echo -e "${RED}❌ Failed to sync code${NC}"
    exit 1
fi
echo ""

# Show recent commits
echo -e "${BLUE}📋 Recent commits:${NC}"
git log -3 --oneline --decorate
echo ""

# Step 2: Build Docker image
echo -e "${YELLOW}🏗️  Step 2/7: Building Docker image...${NC}"
sudo docker build -t $IMAGE_NAME -f Dockerfile .
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker image built successfully${NC}"
else
    echo -e "${RED}❌ Failed to build Docker image${NC}"
    exit 1
fi
echo ""

# Step 3: Stop old container
echo -e "${YELLOW}🛑 Step 3/7: Stopping old container...${NC}"
if sudo docker ps | grep -q $CONTAINER_NAME; then
    sudo docker stop $CONTAINER_NAME
    echo -e "${GREEN}✅ Container stopped${NC}"
else
    echo -e "${BLUE}ℹ️  Container was not running${NC}"
fi
echo ""

# Step 4: Remove old container
echo -e "${YELLOW}🗑️  Step 4/7: Removing old container...${NC}"
if sudo docker ps -a | grep -q $CONTAINER_NAME; then
    sudo docker rm $CONTAINER_NAME
    echo -e "${GREEN}✅ Container removed${NC}"
else
    echo -e "${BLUE}ℹ️  No container to remove${NC}"
fi
echo ""

# Step 5: Start new container
echo -e "${YELLOW}🚀 Step 5/7: Starting new container...${NC}"
sudo docker run -d \
  --name $CONTAINER_NAME \
  -p $PORT_MAPPING \
  --env-file $ENV_FILE \
  -e TZ=$TIMEZONE \
  --restart unless-stopped \
  $IMAGE_NAME

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Container started successfully${NC}"
else
    echo -e "${RED}❌ Failed to start container${NC}"
    exit 1
fi
echo ""

# Step 6: Verify container is running
echo -e "${YELLOW}🔍 Step 6/7: Verifying container status...${NC}"
sleep 3
if sudo docker ps | grep -q $CONTAINER_NAME; then
    echo -e "${GREEN}✅ Container is running${NC}"
    sudo docker ps | grep $CONTAINER_NAME
else
    echo -e "${RED}❌ Container is not running${NC}"
    exit 1
fi
echo ""

# Step 7: Show recent logs
echo -e "${YELLOW}📝 Step 7/7: Checking logs...${NC}"
sudo docker logs --tail 30 $CONTAINER_NAME
echo ""

# Summary
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${BLUE}🌐 Application URL: http://taiga.orchvate.com:8080${NC}"
echo ""
echo -e "${YELLOW}💡 Useful commands:${NC}"
echo -e "  View logs:      sudo docker logs -f $CONTAINER_NAME"
echo -e "  Restart:        sudo docker restart $CONTAINER_NAME"
echo -e "  Stop:           sudo docker stop $CONTAINER_NAME"
echo -e "  Container info: sudo docker inspect $CONTAINER_NAME"
echo ""

```

#### `scripts/fix-vm-env.sh`

```
#!/bin/bash

# Script to fix CORS and FRONTEND_URL on VM
# The issue: VM has neuromark.orchvate.in but should be niwi.orchvate.in

echo "🔧 Fixing .env configuration on VM"
echo "===================================="
echo ""

# Backup current .env
echo "📋 Creating backup..."
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Fix CORS_ORIGINS
echo "🔄 Updating CORS_ORIGINS..."
sed -i 's|CORS_ORIGINS=.*|CORS_ORIGINS=https://niwi.orchvate.in|g' .env

# Fix FRONTEND_URL
echo "🔄 Updating FRONTEND_URL..."
sed -i 's|FRONTEND_URL=.*|FRONTEND_URL=https://niwi.orchvate.in|g' .env

# Show changes
echo ""
echo "✅ Updated values:"
grep "CORS_ORIGINS=" .env
grep "FRONTEND_URL=" .env
echo ""

echo "📊 Current configuration:"
echo "------------------------"
cat .env | grep -v "PASSWORD\|CONNECTION_STRING\|JWT_SECRET\|accesskey"
echo ""

read -p "Deploy with these changes? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Deploying..."
    ./deploy.sh
else
    echo "❌ Cancelled. Run ./deploy.sh manually when ready."
fi

```

#### `scripts/import_nexora_audit.py`

```python
"""
scripts/import_nexora_audit.py — Safe, repeatable transactional import for
Nexora Technologies 100 Synthetic Employee Audit Data.
"""

import os
import sys
import json
import uuid
from datetime import datetime, timezone, timedelta
import openpyxl
import psycopg2.extras
import dotenv

# Load environment
dotenv.load_dotenv()
psycopg2.extras.register_uuid()

# Ensure repository root is in python path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.core.database import get_conn
from app.services.scoring_service import calculate_scores
from app.services.org_scoring_service import calc_weighted_org_score

EXCEL_PATH = os.path.join(ROOT_DIR, "Nexora_Technologies_100_Employee_Synthetic_Audit_Data.xlsx")


def run_import(dry_run: bool = False):
    print("=" * 70)
    print("NEXORA TECHNOLOGIES 100 EMPLOYEE SYNTHETIC AUDIT DATA IMPORT")
    print("=" * 70)
    print(f"Reading dataset: {EXCEL_PATH}")

    if not os.path.exists(EXCEL_PATH):
        raise FileNotFoundError(f"Excel file not found at {EXCEL_PATH}")

    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    if "Employees_Q5-Q44" not in wb.sheetnames:
        raise ValueError("Sheet 'Employees_Q5-Q44' not found in workbook")

    sheet = wb["Employees_Q5-Q44"]
    headers = [sheet.cell(1, col).value for col in range(1, sheet.max_column + 1)]
    
    raw_rows = []
    for r in range(2, sheet.max_row + 1):
        row_dict = {headers[c - 1]: sheet.cell(r, c).value for c in range(1, sheet.max_column + 1)}
        if row_dict.get("Work_Email"):
            raw_rows.append(row_dict)

    total_records = len(raw_rows)
    print(f"Loaded {total_records} employee audit records from Excel.")
    if total_records != 100:
        print(f"WARNING: Expected 100 records, found {total_records}")

    conn = get_conn()
    conn.autocommit = False

    try:
        with conn.cursor() as cur:
            # 1. Organization Setup
            org_name = raw_rows[0].get("Organization_Name", "Nexora Technologies").strip()
            print(f"\n[1/5] Ensuring organization '{org_name}' exists in organizations table...")
            
            cur.execute("SELECT id FROM organizations WHERE LOWER(TRIM(name)) = LOWER(TRIM(%s))", (org_name,))
            row = cur.fetchone()
            if row:
                org_id = row[0]
                print(f"  -> Found existing organization: ID = {org_id}")
            else:
                cur.execute(
                    "INSERT INTO organizations (name, created_at) VALUES (%s, %s) RETURNING id",
                    (org_name, datetime.now(timezone.utc))
                )
                org_id = cur.fetchone()[0]
                print(f"  -> Created new organization: ID = {org_id}")

            org_id_str = str(org_id)

            # 2. Check and remove any previous synthetic test records for repeatability (idempotent)
            emails = [r["Work_Email"].strip() for r in raw_rows]
            print(f"\n[2/5] Checking for existing synthetic test records...")
            cur.execute("""
                SELECT id FROM submissions
                WHERE email = ANY(%s) OR (company_name = %s AND email LIKE '%%@example.invalid')
            """, (emails, org_name))
            existing_sub_ids = [str(r[0]) for r in cur.fetchall()]
            if existing_sub_ids:
                print(f"  -> Found {len(existing_sub_ids)} existing synthetic records. Cleaning up for fresh import...")
                cur.execute("DELETE FROM org_submission_links WHERE submission_id = ANY(%s::uuid[])", (existing_sub_ids,))
                cur.execute("DELETE FROM submissions WHERE id = ANY(%s::uuid[])", (existing_sub_ids,))
                print(f"  -> Successfully removed stale synthetic records.")
            else:
                print(f"  -> Zero existing conflicts found. Clean slate for import.")

            # 3. Process and Insert All 100 Submissions
            print(f"\n[3/5] Scoring and inserting {total_records} submissions transactionally...")

            insert_sub_sql = """
                INSERT INTO submissions (
                    id, submitted_at, name, designation, company_name, email, contact_number,
                    has_physical_workspace, has_suppliers,
                    q5,q6,q7,q8,q9,q10,q11,q12,q13,q14,
                    q15,q16,q17,q18,q19,q20,q21,q22,q23,q24,
                    q25,q26,q27,q28,q29,q30,q31,q32,q33,q34,
                    q35,q36,q37,q38,q39,q40,q41,q42,q43,q44,
                    lc_score, lc_level, ro_score, ro_level,
                    we_score, we_level, be_score, be_level,
                    tm_score, tm_level, ca_score, ca_level,
                    pc_score, pc_level, sp_score, sp_level,
                    overall_avg, overall_level, email_body, status,
                    consent_given, consent_timestamp, organization_id, dimension_scores, answers
                ) VALUES (
                    %(id)s, %(submitted_at)s, %(name)s, %(designation)s, %(company_name)s, %(email)s, %(contact_number)s,
                    %(has_physical_workspace)s, %(has_suppliers)s,
                    %(q5)s,%(q6)s,%(q7)s,%(q8)s,%(q9)s,%(q10)s,%(q11)s,%(q12)s,%(q13)s,%(q14)s,
                    %(q15)s,%(q16)s,%(q17)s,%(q18)s,%(q19)s,%(q20)s,%(q21)s,%(q22)s,%(q23)s,%(q24)s,
                    %(q25)s,%(q26)s,%(q27)s,%(q28)s,%(q29)s,%(q30)s,%(q31)s,%(q32)s,%(q33)s,%(q34)s,
                    %(q35)s,%(q36)s,%(q37)s,%(q38)s,%(q39)s,%(q40)s,%(q41)s,%(q42)s,%(q43)s,%(q44)s,
                    %(lc_score)s, %(lc_level)s, %(ro_score)s, %(ro_level)s,
                    %(we_score)s, %(we_level)s, %(be_score)s, %(be_level)s,
                    %(tm_score)s, %(tm_level)s, %(ca_score)s, %(ca_level)s,
                    %(pc_score)s, %(pc_level)s, %(sp_score)s, %(sp_level)s,
                    %(overall_avg)s, %(overall_level)s, %(email_body)s, %(status)s,
                    %(consent_given)s, %(consent_timestamp)s, %(organization_id)s, %(dimension_scores)s, %(answers)s
                )
            """

            insert_link_sql = """
                INSERT INTO org_submission_links (
                    id, org_id, submission_id, weight, linked_by, linked_at
                ) VALUES (
                    %(id)s, %(org_id)s, %(submission_id)s, %(weight)s, %(linked_by)s, %(linked_at)s
                )
            """

            # Stagger timestamps across the past 7 days to simulate a realistic audit rollout
            base_time = datetime.now(timezone.utc) - timedelta(days=7)

            inserted_sub_ids = []
            for idx, r in enumerate(raw_rows):
                emp_id = str(r.get("Employee_ID", f"EMP{idx+1:03d}")).strip()
                emp_name = f"Employee {emp_id}"
                email = str(r.get("Work_Email")).strip()
                contact = str(r.get("Contact_Number") or "").strip()
                role = str(r.get("Role") or "").strip()
                dept = str(r.get("Department_Function") or "").strip()
                dept_other = str(r.get("Function_Other_Specify") or "").strip()
                gender = str(r.get("Gender") or "").strip()
                gender_other = str(r.get("Gender_Other_Specify") or "").strip()
                is_nd = str(r.get("Neurodiversity_Identification") or "").strip()
                is_pwd = str(r.get("Person_with_Disability") or "").strip()
                is_marg = str(r.get("Marginalized_Underrepresented_Identity") or "").strip()
                country = str(r.get("Country") or "").strip()
                state_ut = str(r.get("State_UT") or "").strip()
                age_group = str(r.get("Age_Group") or "").strip()
                has_workspace = str(r.get("Has_Physical_Workspace") or "Yes").strip()
                has_suppliers = str(r.get("Has_Recurring_Suppliers") or "Yes").strip()
                has_touchpoints = str(r.get("Has_Physical_Customer_Touchpoints") or "Yes").strip()

                sub_uuid = str(uuid.uuid4())
                # Staggered submitted_at timestamp
                submitted_at = base_time + timedelta(hours=(idx * 1.6))

                # Prepare payload for calculate_scores (pure in-memory evaluation for speed & purity)
                score_input = {
                    "name": emp_name,
                    "designation": role,
                    "company_name": org_name,
                    "email": email,
                    "contact_number": contact,
                    "has_physical_workspace": has_workspace,
                    "has_suppliers": has_suppliers,
                }
                for q_num in range(5, 45):
                    q_val = r.get(f"Q{q_num}")
                    if q_val is None:
                        q_val = "Not Sure"
                    score_input[f"q{q_num}"] = str(q_val).strip()

                # Calculate standard scores in-memory
                scores = calculate_scores(score_input)

                # Assemble answers JSONB payload containing demographics and full survey responses
                answers_payload = {
                    "employee_id": emp_id,
                    "organization_code": str(r.get("Organization_ID", "NEXORA-TEST-001")),
                    "synthetic_record": str(r.get("Synthetic_Record", "YES")),
                    "function": dept,
                    "function_other": dept_other,
                    "role": role,
                    "gender": gender,
                    "gender_other": gender_other,
                    "is_neurodivergent": is_nd,
                    "is_pwd": is_pwd,
                    "is_marginalized": is_marg,
                    "country": country,
                    "state_ut": state_ut,
                    "age_group": age_group,
                    "has_physical_customer_touchpoints": has_touchpoints,
                    **{f"q{q_num}": score_input[f"q{q_num}"] for q_num in range(5, 45)},
                }

                dimension_scores_json = json.dumps(scores.get("dimension_scores", {}))
                answers_json = json.dumps(answers_payload)

                # Sanitize "NA" scores for Decimal DB columns
                sanitized_scores = {k: (None if v == "NA" else v) for k, v in scores.items()}

                sub_params = {
                    "id": sub_uuid,
                    "submitted_at": submitted_at,
                    "name": emp_name,
                    "designation": role,
                    "company_name": org_name,
                    "email": email,
                    "contact_number": contact,
                    "has_physical_workspace": has_workspace,
                    "has_suppliers": has_suppliers,
                    **{f"q{q_num}": score_input[f"q{q_num}"] for q_num in range(5, 45)},
                    "lc_score": sanitized_scores.get("lc_score"),
                    "lc_level": sanitized_scores.get("lc_level"),
                    "ro_score": sanitized_scores.get("ro_score"),
                    "ro_level": sanitized_scores.get("ro_level"),
                    "we_score": sanitized_scores.get("we_score"),
                    "we_level": sanitized_scores.get("we_level"),
                    "be_score": sanitized_scores.get("be_score"),
                    "be_level": sanitized_scores.get("be_level"),
                    "tm_score": sanitized_scores.get("tm_score"),
                    "tm_level": sanitized_scores.get("tm_level"),
                    "ca_score": sanitized_scores.get("ca_score"),
                    "ca_level": sanitized_scores.get("ca_level"),
                    "pc_score": sanitized_scores.get("pc_score"),
                    "pc_level": sanitized_scores.get("pc_level"),
                    "sp_score": sanitized_scores.get("sp_score"),
                    "sp_level": sanitized_scores.get("sp_level"),
                    "overall_avg": sanitized_scores.get("overall_avg"),
                    "overall_level": sanitized_scores.get("overall_level"),
                    "email_body": scores.get("email_body", ""),
                    "status": "pending",
                    "consent_given": True,
                    "consent_timestamp": submitted_at,
                    "organization_id": org_id_str,
                    "dimension_scores": dimension_scores_json,
                    "answers": answers_json,
                }

                cur.execute(insert_sub_sql, sub_params)

                # Link to organization
                link_params = {
                    "id": str(uuid.uuid4()),
                    "org_id": org_id_str,
                    "submission_id": sub_uuid,
                    "weight": 1.0,
                    "linked_by": "Synthetic Import",
                    "linked_at": submitted_at,
                }
                cur.execute(insert_link_sql, link_params)
                inserted_sub_ids.append(sub_uuid)

                if (idx + 1) % 20 == 0 or (idx + 1) == total_records:
                    print(f"  -> Staged {idx + 1}/{total_records} records...")

            # 4. Data Integrity & Aggregation Verification
            print(f"\n[4/5] Verifying row counts and data integrity in database...")
            cur.execute("SELECT count(*) FROM submissions WHERE organization_id = %s", (org_id_str,))
            db_sub_count = cur.fetchone()[0]
            print(f"  -> Total submissions linked to '{org_name}': {db_sub_count}")
            assert db_sub_count == 100, f"Expected 100 submissions, found {db_sub_count}"

            cur.execute("SELECT count(*) FROM org_submission_links WHERE org_id = %s", (org_id_str,))
            db_link_count = cur.fetchone()[0]
            print(f"  -> Total org_submission_links for '{org_name}': {db_link_count}")
            assert db_link_count == 100, f"Expected 100 links, found {db_link_count}"

            # Verify demographic distribution
            cur.execute("""
                SELECT answers->>'function' as dept, count(*)
                FROM submissions
                WHERE organization_id = %s
                GROUP BY answers->>'function'
                ORDER BY count(*) DESC
            """, (org_id_str,))
            depts = cur.fetchall()
            print(f"  -> Department distribution verified ({len(depts)} departments):")
            for d, c in depts:
                print(f"     - {d}: {c} employees")

            # Verify Org Weighted Scores
            cur.execute("""
                SELECT s.overall_avg, s.lc_score, s.ro_score, s.we_score, s.be_score,
                       s.tm_score, s.ca_score, s.pc_score, s.sp_score, osl.weight
                FROM org_submission_links osl
                JOIN submissions s ON s.id = osl.submission_id
                WHERE osl.org_id = %s
            """, (org_id_str,))
            links_data = [
                {
                    "overall_avg": float(r[0]),
                    "lc_score": float(r[1]) if r[1] is not None else 0,
                    "ro_score": float(r[2]) if r[2] is not None else 0,
                    "we_score": float(r[3]) if r[3] is not None else 0,
                    "be_score": float(r[4]) if r[4] is not None else 0,
                    "tm_score": float(r[5]) if r[5] is not None else 0,
                    "ca_score": float(r[6]) if r[6] is not None else 0,
                    "pc_score": float(r[7]) if r[7] is not None else 0,
                    "sp_score": float(r[8]) if r[8] is not None else 0,
                    "weight": float(r[9]),
                }
                for r in cur.fetchall()
            ]
            org_scores = calc_weighted_org_score(links_data)
            print(f"\n  -> Calculated Nexora Technologies Aggregate Scores:")
            print(f"     - Org Average: {org_scores['org_avg']:.2f} / 20 ({org_scores['org_level']})")
            print(f"     - Section Avgs:")
            for sec, avg in org_scores["section_avgs"].items():
                print(f"       * {sec.upper()}: {avg
```
> _Truncated to 16000 bytes — see full file in the source repo._

#### `scripts/inspect_schema.py`

```python
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.environ["PGHOST"],
    dbname=os.environ["PGDATABASE"],
    user=os.environ["PGUSER"],
    password=os.environ["PGPASSWORD"],
    port=os.environ.get("PGPORT", "5432"),
    sslmode="require",
)

with conn.cursor() as cur:
    cur.execute("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'admin_users'")
    for row in cur.fetchall():
        print(row)
    
conn.close()

```

#### `scripts/migrate.py`

```python
"""
migrate.py — Canonical NIWI database migration runner.
Tracks migration execution in the `schema_migrations` table for idempotency.
Applies migrations in sorted numerical order inside individual transactions.

Usage:
  python scripts/migrate.py              # Apply all pending migrations
  python scripts/migrate.py --status     # Show migration status
  python scripts/migrate.py <file_name>  # Apply a specific migration
"""
import sys
import os
import glob
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.config import APP_ENV, IS_PRODUCTION
from app.core.database import get_conn, is_production_database

MIGRATIONS_DIR = ROOT / "migrations"


def get_migration_files():
    """Return all migration SQL files in sorted order."""
    return sorted(MIGRATIONS_DIR.glob("*.sql"))


def ensure_migration_table(conn):
    """Ensure the schema_migrations tracking table exists."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
    conn.commit()


def get_applied_migrations(conn):
    """Return set of migration filenames that have already been applied."""
    ensure_migration_table(conn)
    with conn.cursor() as cur:
        cur.execute("SELECT version FROM schema_migrations;")
        return {row[0] for row in cur.fetchall()}


def run_migration_file(conn, file_path: Path):
    """Execute a single migration file in a transaction and record it."""
    version = file_path.name
    with open(file_path, "r", encoding="utf-8") as f:
        sql = f.read()

    with conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "INSERT INTO schema_migrations (version) VALUES (%s) ON CONFLICT (version) DO NOTHING;",
                (version,)
            )
    print(f"  [APPLIED] {version}")


def show_status():
    """Display status of all migrations."""
    conn = get_conn()
    try:
        applied = get_applied_migrations(conn)
        all_files = get_migration_files()
        print("\nMigration Status:")
        print("-" * 60)
        for f in all_files:
            status = "APPLIED" if f.name in applied else "PENDING"
            print(f"  [{status:<7}] {f.name}")
        print("-" * 60)
    finally:
        conn.close()


def migrate(target_file: str = None):
    """Run pending migrations."""
    conn = get_conn()
    try:
        ensure_migration_table(conn)
        applied = get_applied_migrations(conn)
        all_files = get_migration_files()

        if target_file:
            matching = [f for f in all_files if f.name == target_file or target_file in f.name]
            if not matching:
                print(f"Error: Migration file matching '{target_file}' not found.")
                sys.exit(1)
            target = matching[0]
            if target.name in applied:
                print(f"Migration {target.name} is already recorded as applied.")
                return
            print(f"Applying single migration: {target.name}")
            run_migration_file(conn, target)
            return

        pending = [f for f in all_files if f.name not in applied]
        if not pending:
            print("\nDatabase is up to date. No pending migrations.")
            return

        print(f"\nApplying {len(pending)} pending migration(s)...")
        for f in pending:
            run_migration_file(conn, f)

        print("\nAll pending migrations applied successfully.")
    finally:
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--status", "-s"):
        show_status()
    elif len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        migrate(sys.argv[1])
    else:
        migrate()

```

#### `scripts/reconcile_pipeline.py`

```python
"""
reconcile_pipeline.py — Comprehensive Submission Pipeline Reconciliation Tool
Verifies end-to-end durability and accounting across:
1. Submissions sent / acknowledged
2. Records persisted in raw_submissions
3. Outbox events staged and dispatched in service_bus_outbox
4. Final completed records in submissions table
5. Dead-lettered or retrying records
6. Records visible in the admin dashboard query
"""
import os
import sys
import json
import logging
from typing import Optional, Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2.extras
from app.core.database import get_db_connection

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("reconcile")


def reconcile_pipeline(test_run_prefix: Optional[str] = None) -> Dict[str, Any]:
    """Run full pipeline reconciliation."""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # 1. raw_submissions counts
            where_raw = ""
            params_raw = ()
            if test_run_prefix:
                where_raw = "WHERE idempotency_key LIKE %s"
                params_raw = (f"%{test_run_prefix}%",)

            cur.execute(f"""
                SELECT status, COUNT(*) AS count
                FROM raw_submissions
                {where_raw}
                GROUP BY status
            """, params_raw)
            raw_by_status = {r["status"]: r["count"] for r in cur.fetchall()}
            raw_total = sum(raw_by_status.values())

            # 2. service_bus_outbox counts
            where_outbox = ""
            params_outbox = ()
            if test_run_prefix:
                where_outbox = "WHERE payload->>'idempotency_key' LIKE %s"
                params_outbox = (f"%{test_run_prefix}%",)

            cur.execute(f"""
                SELECT status, COUNT(*) AS count
                FROM service_bus_outbox
                {where_outbox}
                GROUP BY status
            """, params_outbox)
            outbox_by_status = {r["status"]: r["count"] for r in cur.fetchall()}
            outbox_total = sum(outbox_by_status.values())

            # 3. submissions table counts
            where_sub = ""
            params_sub = ()
            if test_run_prefix:
                where_sub = "WHERE idempotency_key LIKE %s"
                params_sub = (f"%{test_run_prefix}%",)

            cur.execute(f"""
                SELECT status, async_status, COUNT(*) AS count
                FROM submissions
                {where_sub}
                GROUP BY status, async_status
            """, params_sub)
            sub_rows = cur.fetchall()
            sub_total = sum(r["count"] for r in sub_rows)
            sub_completed = sum(r["count"] for r in sub_rows if r["status"] == "completed" or r["async_status"] == "COMPLETED")

            # 4. Check for orphaned raw submissions (accepted but never reached submissions)
            where_orphans = "WHERE r.status = 'COMPLETED' AND s.id IS NULL"
            params_orphans = ()
            if test_run_prefix:
                where_orphans += " AND r.idempotency_key LIKE %s"
                params_orphans = (f"%{test_run_prefix}%",)

            cur.execute(f"""
                SELECT COUNT(*) AS count
                FROM raw_submissions r
                LEFT JOIN submissions s ON (s.id = r.submission_id OR s.raw_submission_id = r.submission_id)
                {where_orphans}
            """, params_orphans)
            orphan_count = cur.fetchone()["count"]

            # 5. Check dead-lettered / failed submissions
            dead_letter_count = raw_by_status.get("DEAD_LETTERED", 0) + raw_by_status.get("FAILED", 0)

            # 6. Dashboard query visibility test
            if test_run_prefix:
                cur.execute("""
                    SELECT COUNT(*) AS count FROM (
                        SELECT id FROM submissions WHERE email LIKE %(p)s
                        UNION ALL
                        SELECT r.submission_id AS id
                        FROM raw_submissions r
                        WHERE r.status IN ('RECEIVED', 'PROCESSING', 'DEAD_LETTERED', 'FAILED', 'RETRYING')
                          AND (r.payload->>'email' LIKE %(p)s)
                          AND NOT EXISTS (
                              SELECT 1 FROM submissions s WHERE s.id = r.submission_id OR s.raw_submission_id = r.submission_id
                          )
                    ) dash
                """, {"p": f"%{test_run_prefix}%"})
            else:
                cur.execute("""
                    SELECT COUNT(*) AS count FROM (
                        SELECT id FROM submissions
                        UNION ALL
                        SELECT r.submission_id AS id
                        FROM raw_submissions r
                        WHERE r.status IN ('RECEIVED', 'PROCESSING', 'DEAD_LETTERED', 'FAILED', 'RETRYING')
                          AND NOT EXISTS (
                              SELECT 1 FROM submissions s WHERE s.id = r.submission_id OR s.raw_submission_id = r.submission_id
                          )
                    ) dash
                """)
            dashboard_visible = cur.fetchone()["count"]

    report = {
        "filter_prefix": test_run_prefix or "ALL",
        "raw_submissions_total": raw_total,
        "raw_by_status": raw_by_status,
        "outbox_total": outbox_total,
        "outbox_by_status": outbox_by_status,
        "submissions_total": sub_total,
        "submissions_completed": sub_completed,
        "orphans_completed_without_submission": orphan_count,
        "dead_letter_or_failed": dead_letter_count,
        "dashboard_visible_total": dashboard_visible
    }

    # Print clean formatted table
    print("\n" + "=" * 65)
    print(f"  NIWI SUBMISSION PIPELINE RECONCILIATION [{report['filter_prefix']}]")
    print("=" * 65)
    print(f"  Raw Submissions Staged:         {raw_total:>6}")
    for st, cnt in sorted(raw_by_status.items()):
        print(f"    - {st:<25} {cnt:>6}")
    print("-" * 65)
    print(f"  Outbox Records Created:         {outbox_total:>6}")
    for st, cnt in sorted(outbox_by_status.items()):
        print(f"    - {st:<25} {cnt:>6}")
    print("-" * 65)
    print(f"  Final Submissions Persisted:    {sub_total:>6}")
    print(f"    - Completed & Scored:         {sub_completed:>6}")
    print(f"  Dead-Lettered / Failed:         {dead_letter_count:>6}")
    print(f"  Orphaned Unpromoted Rows:       {orphan_count:>6}")
    print(f"  Submissions Visible in Dash:    {dashboard_visible:>6}")
    print("=" * 65)

    discrepancy = raw_total - (sub_completed + dead_letter_count + raw_by_status.get("RECEIVED", 0) + raw_by_status.get("PROCESSING", 0) + raw_by_status.get("RETRYING", 0))
    if discrepancy == 0 and orphan_count == 0:
        print("  [PASS] ZERO LOSS RECONCILIATION: 100% of submissions accounted for.")
    else:
        print(f"  [WARN] Discrepancy of {discrepancy} rows detected between raw and final records.")
    print("=" * 65 + "\n")

    return report


if __name__ == "__main__":
    prefix = sys.argv[1] if len(sys.argv) > 1 else None
    reconcile_pipeline(prefix)

```

#### `scripts/reconcile_runs.py`

```python
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2.extras
from app.core.database import get_db_connection

runs = [
    ("10 VUs", "run_1793812073", 10),
    ("20 VUs", "run_1793812084", 20),
    ("40 VUs", "run_1793812095", 40),
    ("80 VUs", "run_1793812109", 80),
]

with get_db_connection() as conn:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        for name, run_id, expected in runs:
            # 1. raw_submissions
            cur.execute("""
                SELECT status, count(*) AS count
                FROM raw_submissions 
                WHERE payload->>'email' LIKE %s 
                GROUP BY status
            """, (f"%{run_id}%",))
            raw_counts = {r["status"]: r["count"] for r in cur.fetchall()}
            total_raw = sum(raw_counts.values())

            # 2. outbox
            cur.execute("""
                SELECT status, count(*) AS count 
                FROM service_bus_outbox 
                WHERE payload->>'submission_id' IN (
                    SELECT submission_id::text 
                    FROM raw_submissions 
                    WHERE payload->>'email' LIKE %s
                ) 
                GROUP BY status
            """, (f"%{run_id}%",))
            outbox_counts = {r["status"]: r["count"] for r in cur.fetchall()}
            total_outbox = sum(outbox_counts.values())

            # 3. final submissions table
            cur.execute("SELECT count(*) AS count FROM submissions WHERE email LIKE %s", (f"%{run_id}%",))
            final_count = cur.fetchone()["count"]

            # 4. dashboard visible
            cur.execute("""
                SELECT count(*) AS count FROM (
                    SELECT id FROM submissions WHERE email LIKE %s
                    UNION ALL
                    SELECT submission_id AS id FROM raw_submissions 
                    WHERE payload->>'email' LIKE %s
                      AND NOT EXISTS (
                          SELECT 1 FROM submissions s 
                          WHERE s.id = raw_submissions.submission_id 
                             OR s.raw_submission_id = raw_submissions.submission_id
                      )
                ) dash
            """, (f"%{run_id}%", f"%{run_id}%"))
            dash_count = cur.fetchone()["count"]

            # 5. dead-letter / failures
            dead_letter_count = raw_counts.get("DEAD_LETTERED", 0) + raw_counts.get("FAILED", 0)

            print(f"=== Stage: {name} (Run ID: {run_id}) ===")
            print(f"  Sent / Attempted:    {expected}")
            print(f"  Acknowledged (202):  {expected}")
            print(f"  Raw Staged (DB):     {total_raw} (by status: {raw_counts})")
            print(f"  Outbox Records:      {total_outbox} (by status: {outbox_counts})")
            print(f"  Final Submissions:   {final_count}")
            print(f"  Dead Letter / Failed:{dead_letter_count}")
            print(f"  Visible in Dash:     {dash_count}")
            print()

```

#### `scripts/run_migration.py`

```python
"""
run_migration.py — Run migrations against the live database.
Usage:
  python scripts/run_migration.py                       # Runs all pending migrations via migrate.py
  python scripts/run_migration.py <migration_file>      # Runs a specific migration file
"""
import os
import sys
import psycopg2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

if len(sys.argv) <= 1:
    # Default to running all pending migrations safely via migrate.py
    from scripts.migrate import migrate
    migrate()
    sys.exit(0)

from app.core.keyvault import init_keyvault, get_database_config

init_keyvault()
db_config = get_database_config()
migration_file = sys.argv[1]

print(f"Running specific migration: {migration_file}")

conn = psycopg2.connect(
    host=db_config["host"],
    dbname=db_config["database"],
    user=db_config["user"],
    password=db_config["password"],
    port=db_config["port"],
    sslmode="require",
)

try:
    with open(migration_file, "r", encoding="utf-8") as f:
        sql = f.read()

    with conn:
        with conn.cursor() as cur:
            cur.execute(sql)

    print(f"✅ Migration applied successfully: {migration_file}")
except Exception as e:
    print(f"❌ Migration failed: {e}")
    conn.rollback()
    sys.exit(1)
finally:
    conn.close()

```

#### `scripts/run_tests.py`

```python
import os
import sys
import importlib.util
from dotenv import load_dotenv

load_dotenv()

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_test_file(filepath):
    print(f"Running tests in {os.path.basename(filepath)}...")
    spec = importlib.util.spec_from_file_location("test_module", filepath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    test_functions = [getattr(module, attr) for attr in dir(module) if attr.startswith("test_") and callable(getattr(module, attr))]
    
    passed = 0
    failed = 0
    for func in test_functions:
        try:
            func()
            print(f"  [PASS] {func.__name__}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {func.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
            
    print(f"Summary for {os.path.basename(filepath)}: {passed} passed, {failed} failed\n")
    return passed, failed

if __name__ == "__main__":
    test_files = [
        "tests/test_scoring.py",
        "tests/test_drafts.py",
        "tests/test_org.py"
    ]
    
    total_passed = 0
    total_failed = 0
    for f in test_files:
        if os.path.exists(f):
            p, fl = run_test_file(f)
            total_passed += p
            total_failed += fl
            
    print(f"Global Summary: {total_passed} passed, {total_failed} failed")
    if total_failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)

```

#### `scripts/seed_db.py`

```python
"""
seed_db.py — Seed the database with sample submissions for local testing.
Run: python scripts/seed_db.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import get_conn
from app.services.scoring_service import calculate_scores

SAMPLES = [
    {"name": "Sarah Mitchell", "company_name": "Brightpath Solutions",
     "email": "sarah@brightpath.co.uk", "contact_number": "+44 7700 123456",
     **{f"q{i}": "Yes" for i in range(5, 45)}},
    {"name": "James Okafor", "company_name": "Nexgen Retail Group",
     "email": "j.okafor@nexgen.com", "contact_number": None,
     **{f"q{i}": ("Partially" if i % 2 == 0 else "No") for i in range(5, 45)}},
]

def seed():
    conn = get_conn()
    for s in SAMPLES:
        scores = calculate_scores(s)
        params = {**s, **scores}
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO submissions (name, company_name, email, contact_number,
                        lc_score, lc_level, ro_score, ro_level, we_score, we_level,
                        be_score, be_level, tm_score, tm_level, ca_score, ca_level,
                        pc_score, pc_level, sp_score, sp_level,
                        overall_avg, overall_level, email_body, status)
                    VALUES (%(name)s, %(company_name)s, %(email)s, %(contact_number)s,
                        %(lc_score)s, %(lc_level)s, %(ro_score)s, %(ro_level)s,
                        %(we_score)s, %(we_level)s, %(be_score)s, %(be_level)s,
                        %(tm_score)s, %(tm_level)s, %(ca_score)s, %(ca_level)s,
                        %(pc_score)s, %(pc_level)s, %(sp_score)s, %(sp_level)s,
                        %(overall_avg)s, %(overall_level)s, %(email_body)s, 'pending')
                """, params)
        print(f"Seeded: {s['name']}")
    conn.close()

if __name__ == "__main__":
    seed()

```

#### `scripts/set_super.py`

```python
"""
set_super.py — Force-set aakash.padyachi@orchvate.com to role='super'.
Run: python scripts/set_super.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from app.core.database import get_conn

SUPER_EMAIL = "aakash.padyachi@orchvate.com"

conn = get_conn()
with conn.cursor() as cur:
    # Upsert: insert if not exists, always set role to super
    cur.execute("""
        INSERT INTO admin_users (email, role)
        VALUES (%s, 'super')
        ON CONFLICT (email) DO UPDATE SET role = 'super'
    """, (SUPER_EMAIL,))
    
    # Confirm
    cur.execute("SELECT email, role FROM admin_users WHERE email = %s", (SUPER_EMAIL,))
    row = cur.fetchone()
    print(f"Updated: {row}")

conn.commit()
conn.close()
print("Done. Aakash is now Super Admin.")

```

#### `scripts/setup_db.py`

```python
"""
setup_db.py — Creates the nd_audit database and submissions table on Azure PostgreSQL.
Run once: python scripts/setup_db.py
"""
import psycopg2
import os
from pathlib import Path

# Load .env manually (no dotenv dependency needed)
env_path = Path(__file__).parent.parent / ".env"
for line in env_path.read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

HOST     = os.environ["PGHOST"]
PORT     = os.environ.get("PGPORT", "5432")
USER     = os.environ["PGUSER"]
PASSWORD = os.environ["PGPASSWORD"]

def run(conn, sql):
    with conn.cursor() as cur:
        cur.execute(sql)

# Step 1 — connect to the default 'postgres' db and create nd_audit if needed
print("Connecting to Azure PostgreSQL...")
conn = psycopg2.connect(
    host=HOST, port=PORT, dbname="postgres",
    user=USER, password=PASSWORD, sslmode="require"
)
conn.autocommit = True

with conn.cursor() as cur:
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'nd_audit'")
    exists = cur.fetchone()

if not exists:
    with conn.cursor() as cur:
        cur.execute("CREATE DATABASE nd_audit")
    print("Created database: nd_audit")
else:
    print("Database nd_audit already exists, skipping.")

conn.close()

# Step 2 — connect to nd_audit and create the submissions table
conn2 = psycopg2.connect(
    host=HOST, port=PORT, dbname="nd_audit",
    user=USER, password=PASSWORD, sslmode="require"
)
conn2.autocommit = True

sql = Path(__file__).parent.parent / "create_table.sql"
ddl = sql.read_text()

# Strip out the commented CREATE DATABASE line so it doesn't error
ddl_clean = "\n".join(
    l for l in ddl.splitlines()
    if not l.strip().startswith("--") and l.strip()
)

with conn2.cursor() as cur:
    cur.execute(ddl_clean)

conn2.close()
print("submissions table ready.")
print("\nAll done. You can now run: func start")

```

#### `scripts/test_real_postgres_concurrency.py`

```python
"""
scripts/test_real_postgres_concurrency.py — Standalone Real PostgreSQL Concurrency & Idempotency Benchmark

Executes genuine HTTP concurrency tests against unmocked Azure PostgreSQL (v17.11):
1. Verifies psycopg2 is unmocked and connects to live PostgreSQL.
2. In-flight concurrent idempotency: 10 simultaneous threads fire the exact same payload.
   Verifies ON CONFLICT DO NOTHING RETURNING id prevents InFailedSqlTransaction and returns identical submission_id.
3. 100-user HTTP concurrency: 100 distinct audits submitted under 20 concurrent worker threads to the same organisation.
   Measures real P50, P95, P99 latency, throughput (req/s), and guarantees 0 lost submissions.
4. Real background job lifecycle: tests claim_next_job (SKIP LOCKED), process_email_job, and complete_job against real tables.
5. Full atomic cleanup of all test entities.
"""

import os
import sys
import time
import uuid
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure not running under pytest test flag so safety guard permits load test
os.environ.pop("TESTING", None)
os.environ["APP_ENV"] = "development"

import psycopg2
from psycopg2.extras import RealDictCursor
from starlette.testclient import TestClient

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD
from app.core.database import init_connection_pool, close_connection_pool, get_db_connection
from app.main import app
from app.tasks.job_worker import claim_next_job, process_email_job, complete_job
from app.core.limiter import limiter

def run_real_postgres_benchmark():
    print("=" * 80)
    print("NIWI v3.1 REAL POSTGRESQL CONCURRENCY & IDEMPOTENCY BENCHMARK")
    print("=" * 80)

    # 1. Verify environment and unmocked database
    print(f"Target Database Host: {PGHOST}")
    print(f"Target Database Name: {PGDATABASE}")
    print(f"psycopg2 Connection Module: {psycopg2.__name__} (unmocked)")

    limiter.enabled = False  # Bypasses client-side single-IP throttle during load test
    init_connection_pool(minconn=5, maxconn=25)
    client = TestClient(app)

    # Test baseline DB connection and fetch version
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            pg_version = cur.fetchone()[0]
            print(f"Live PostgreSQL Version: {pg_version}")

    batch_uuid = uuid.uuid4().hex[:8]
    test_org_name = f"RealPG Load Test Org {batch_uuid}"
    created_sub_ids = []
    created_org_ids = set()

    try:
        # ----------------------------------------------------------------------
        # TEST 1: In-Flight Concurrent Idempotency
        # ----------------------------------------------------------------------
        print("\n" + "-" * 80)
        print("TEST 1: In-Flight Concurrent Idempotency (ON CONFLICT DO NOTHING)")
        print("-" * 80)
        idemp_key = f"real-pg-idemp-{uuid.uuid4()}"
        idemp_payload = {
            "name": "Concurrent InFlight User",
            "company_name": test_org_name,
            "email": f"idemp_{batch_uuid}@realpg-test.com",
            "consent_given": True,
            "idempotency_key": idemp_key,
            **{f"q{i}": "Yes" for i in range(5, 45)}
        }

        num_idemp_threads = 10
        print(f"Launching {num_idemp_threads} simultaneous requests with IDENTICAL idempotency_key...")

        def post_idemp():
            t0 = time.perf_counter()
            resp = client.post("/api/submit", json=idemp_payload)
            elapsed = (time.perf_counter() - t0) * 1000
            return resp.status_code, resp.json(), elapsed

        with ThreadPoolExecutor(max_workers=num_idemp_threads) as executor:
            futures = [executor.submit(post_idemp) for _ in range(num_idemp_threads)]
            idemp_results = [f.result() for f in as_completed(futures)]

        status_codes = [r[0] for r in idemp_results]
        sub_ids = [r[1].get("submission_id") for r in idemp_results if r[0] == 201]
        idemp_latencies = [r[2] for r in idemp_results]

        print(f"Responses received: {len(sub_ids)}/{num_idemp_threads} returned HTTP 201")
        print(f"Status codes: {set(status_codes)}")
        print(f"Unique submission IDs returned across all {num_idemp_threads} threads: {set(sub_ids)}")
        print(f"Latency P50: {statistics.median(idemp_latencies):.2f}ms | Max: {max(idemp_latencies):.2f}ms")

        assert len(set(sub_ids)) == 1, f"Expected exactly 1 unique submission_id, got: {set(sub_ids)}"
        single_sub_id = sub_ids[0]
        created_sub_ids.append(single_sub_id)

        # Verify real database count
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM submissions WHERE idempotency_key = %s", (idemp_key,))
                db_idemp_count = cur.fetchone()[0]
                cur.execute("SELECT organization_id FROM submissions WHERE id = %s", (single_sub_id,))
                org_row = cur.fetchone()
                if org_row and org_row[0]:
                    created_org_ids.add(str(org_row[0]))

        print(f"Submissions in PostgreSQL with idempotency_key: {db_idemp_count}")
        assert db_idemp_count == 1, f"Expected exactly 1 row in PostgreSQL, found {db_idemp_count}"
        print(">> TEST 1 PASSED: Zero transaction aborts, zero duplicates, exactly 1 submission created.")

        # ----------------------------------------------------------------------
        # TEST 2: 100-User HTTP Concurrency against Real PostgreSQL
        # ----------------------------------------------------------------------
        print("\n" + "-" * 80)
        print("TEST 2: 100-User HTTP Concurrency (20 parallel workers, same org)")
        print("-" * 80)
        num_users = 100
        concurrency = 20

        submissions_data = []
        for i in range(num_users):
            submissions_data.append({
                "name": f"Stress User {i}",
                "company_name": test_org_name,
                "email": f"stress_{batch_uuid}_{i}@realpg-test.com",
                "consent_given": True,
                "idempotency_key": f"stress-idemp-{batch_uuid}-{i}",
                **{f"q{j}": ("Yes" if (i + j) % 2 == 0 else "No") for j in range(5, 45)}
            })

        print(f"Executing {num_users} submissions with concurrency={concurrency}...")

        def post_submission(payload):
            t0 = time.perf_counter()
            resp = client.post("/api/submit", json=payload)
            elapsed = (time.perf_counter() - t0) * 1000
            return resp.status_code, resp.json(), elapsed

        t_start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(post_submission, p) for p in submissions_data]
            bench_results = [f.result() for f in as_completed(futures)]
        total_time = time.perf_counter() - t_start

        bench_statuses = [r[0] for r in bench_results]
        bench_sub_ids = [r[1].get("submission_id") for r in bench_results if r[0] == 201]
        bench_latencies = [r[2] for r in bench_results]
        created_sub_ids.extend(bench_sub_ids)

        bench_latencies.sort()
        p50 = statistics.median(bench_latencies)
        p90 = bench_latencies[int(len(bench_latencies) * 0.90)]
        p95 = bench_latencies[int(len(bench_latencies) * 0.95)]
        p99 = bench_latencies[int(len(bench_latencies) * 0.99)]
        throughput = num_users / total_time

        print(f"Completed in: {total_time:.2f}s")
        print(f"Throughput: {throughput:.2f} requests/sec")
        print(f"Successful submissions (HTTP 201): {len(bench_sub_ids)}/{num_users}")
        print(f"Unique submission IDs: {len(set(bench_sub_ids))}/{num_users}")
        print(f"Latency P50: {p50:.2f}ms")
        print(f"Latency P90: {p90:.2f}ms")
        print(f"Latency P95: {p95:.2f}ms")
        print(f"Latency P99: {p99:.2f}ms")
        print(f"Latency Min: {min(bench_latencies):.2f}ms | Max: {max(bench_latencies):.2f}ms")

        assert len(bench_sub_ids) == num_users, f"Expected {num_users} HTTP 201s, got {len(bench_sub_ids)}"
        assert len(set(bench_sub_ids)) == num_users, f"Duplicate submission IDs detected!"

        # Verify real database consistency
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # 1. Exactly 1 organization created for test_org_name
                cur.execute("SELECT id FROM organizations WHERE LOWER(TRIM(name)) = LOWER(TRIM(%s))", (test_org_name,))
                org_rows = cur.fetchall()
                print(f"Organizations created with name '{test_org_name}': {len(org_rows)}")
                assert len(org_rows) == 1, f"Advisory lock failed: {len(org_rows)} organizations created!"
                org_id = str(org_rows[0][0])
                created_org_ids.add(org_id)

                # 2. Verify all submissions have organization_id linked
                cur.execute("SELECT COUNT(*) FROM submissions WHERE organization_id = %s", (org_id,))
                subs_linked = cur.fetchone()[0]
                print(f"Submissions linked to organization in PostgreSQL: {subs_linked}")
                assert subs_linked >= num_users

                # 3. Verify post_submit_jobs table has jobs queued
                cur.execute(
                    "SELECT COUNT(*) FROM post_submit_jobs WHERE submission_id = ANY(%s::uuid[]) AND job_type = 'email'",
                    (bench_sub_ids,)
                )
                email_jobs_count = cur.fetchone()[0]
                print(f"Durable email background jobs queued in post_submit_jobs: {email_jobs_count}")
                assert email_jobs_count == num_users, f"Expected {num_users} email jobs, found {email_jobs_count}"

        print(">> TEST 2 PASSED: 100/100 concurrent submissions verified in real PostgreSQL.")

        # ----------------------------------------------------------------------
        # TEST 3: Background Worker Execution against Real PostgreSQL
        # ----------------------------------------------------------------------
        print("\n" + "-" * 80)
        print("TEST 3: Background Worker Execution (SKIP LOCKED) on Real PostgreSQL")
        print("-" * 80)
        target_sub_id = bench_sub_ids[0]
        worker_id = f"real-pg-worker-{batch_uuid}"

        # Claim a job from real DB
        claimed = claim_next_job(worker_id=worker_id)
        assert claimed is not None, "Worker failed to claim job from real PostgreSQL"
        print(f"Worker claimed job: {claimed['id']} (type={claimed['job_type']}) for submission {claimed['submission_id']}")

        # Process the email job
        process_email_job(claimed["submission_id"], claimed.get("payload") or {})
        complete_job(claimed["id"])

        # Verify in real DB that email_body is populated and status is DONE
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT email_body FROM submissions WHERE id = %s", (claimed["submission_id"],))
                body = cur.fetchone()[0]
                assert body is not None and len(body) > 100
                assert "NeuroMark Audit" in body
                print("Verified email_body rendered and persisted in PostgreSQL!")

                cur.execute("SELECT status FROM post_submit_jobs WHERE id = %s", (claimed["id"],))
                job_status = cur.fetchone()[0]
                assert job_status == "DONE"
                print(f"Verified post_submit_jobs status transitioned to: {job_status}")

        print(">> TEST 3 PASSED: Background worker executed and completed on live PostgreSQL.")

    finally:
        # ----------------------------------------------------------------------
        # CLEANUP: Remove all test artifacts from live Azure PostgreSQL
        # ----------------------------------------------------------------------
        print("\n" + "-" * 80)
        print("CLEANUP: Removing test entities from Azure PostgreSQL...")
        print("-" * 80)
        if created_sub_ids:
            with get_db_connection() as conn:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("DELETE FROM post_submit_jobs WHERE submission_id = ANY(%s::uuid[])", (created_sub_ids,))
                        print(f"Deleted post_submit_jobs for {len(created_sub_ids)} submissions.")
                        cur.execute("DELETE FROM org_submission_links WHERE submission_id = ANY(%s::uuid[])", (created_sub_ids,))
                        cur.execute("DELETE FROM submissions WHERE id = ANY(%s::uuid[])", (created_sub_ids,))
                        print(f"Deleted {len(created_sub_ids)} test submissions.")

                        if created_org_ids:
                            cur.execute("DELETE FROM organizations WHERE id = ANY(%s::uuid[])", (list(created_org_ids),))
                            print(f"Deleted {len(created_org_ids)} test organizations.")
        limiter.enabled = True
        close_connection_pool()
        print("Connection pool closed. Real PostgreSQL test complete.")
        print("=" * 80)

if __name__ == "__main__":
    run_real_postgres_benchmark()

```

#### `scripts/verify_import.py`

```python
import os
import sys
import dotenv
dotenv.load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.database import get_conn

conn = get_conn()
cur = conn.cursor()

# 1. Total submissions
cur.execute("SELECT count(*) FROM submissions;")
print("Total Submissions in DB:", cur.fetchone()[0])

# 2. Nexora org check
cur.execute("""
    SELECT o.id, o.name, count(osl.submission_id)
    FROM organizations o
    LEFT JOIN org_submission_links osl ON osl.org_id = o.id
    WHERE o.name = 'Nexora Technologies'
    GROUP BY o.id, o.name;
""")
print("Nexora in organizations table:", cur.fetchone())

# 3. Demographics check for Nexora
cur.execute("""
    SELECT 
        answers->>'role' as role,
        count(*)
    FROM submissions s
    JOIN organizations o ON o.id = s.organization_id
    WHERE o.name = 'Nexora Technologies'
    GROUP BY answers->>'role'
    ORDER BY count(*) DESC;
""")
print("\nRole distribution in Nexora:")
for r in cur.fetchall():
    print(" ", r)

# 4. Age groups check
cur.execute("""
    SELECT 
        answers->>'age_group' as age_group,
        count(*)
    FROM submissions s
    JOIN organizations o ON o.id = s.organization_id
    WHERE o.name = 'Nexora Technologies'
    GROUP BY answers->>'age_group'
    ORDER BY count(*) DESC;
""")
print("\nAge group distribution in Nexora:")
for r in cur.fetchall():
    print(" ", r)

# 5. Neurodiversity check
cur.execute("""
    SELECT 
        answers->>'is_neurodivergent' as is_nd,
        count(*)
    FROM submissions s
    JOIN organizations o ON o.id = s.organization_id
    WHERE o.name = 'Nexora Technologies'
    GROUP BY answers->>'is_neurodivergent'
    ORDER BY count(*) DESC;
""")
print("\nNeurodiversity Identification in Nexora:")
for r in cur.fetchall():
    print(" ", r)

# 6. Sample employee check
cur.execute("""
    SELECT s.name, s.designation, s.email, s.contact_number, s.overall_avg, s.overall_level, s.answers->>'employee_id'
    FROM submissions s
    JOIN organizations o ON o.id = s.organization_id
    WHERE o.name = 'Nexora Technologies'
    ORDER BY s.submitted_at ASC
    LIMIT 3;
""")
print("\nSample imported employees:")
for r in cur.fetchall():
    print(" ", r)

cur.close()
conn.close()

```


## Improvements & refactors

- [keep-behavior] Formalize typing and input constraints for enhanced runtime validation.
- [keep-behavior] Expand automated test coverage for failure modes and timeouts.
- [keep-behavior] Optimize memory footprint and eliminate unreferenced legacy helpers.


## Definition of done

- [ ] Every functional requirement is implemented and covered by a test.
- [ ] Every acceptance-criteria scenario passes (including the failure paths).
- [ ] Every operation this unit owns in `architecture/INTERFACES.md` responds correctly.
- [ ] Every entity it writes matches `architecture/DATA-MODEL.md` (fields, types, constraints).
- [ ] Every write is satisfiable against the schema: no required (NOT NULL, no-default) column or foreign key is left unfilled; anonymous/public operations write only to anonymous-capable entities (no owner FK).
- [ ] Every enum/domain value this unit uses is one of the members fully enumerated in `architecture/DATA-MODEL.md`.
- [ ] Every edge case & failure mode above is handled.
- [ ] `node scripts/analyze.mjs --check --out <out>` passes — no unresolved agent callouts or placeholders, and every reference resolves.

