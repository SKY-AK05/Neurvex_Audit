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
                print(f"       * {sec.upper()}: {avg:.2f} / 20 ({org_scores['section_levels'][sec]})")

            if dry_run:
                print("\n[DRY RUN] Rolling back transaction without committing.")
                conn.rollback()
            else:
                print("\n[5/5] Committing transaction to Azure PostgreSQL database...")
                conn.commit()
                print("  -> Transaction committed successfully!")

    except Exception as e:
        print(f"\nERROR DURING IMPORT: {e}")
        conn.rollback()
        print("  -> Transaction rolled back safely.")
        raise e
    finally:
        conn.close()

    print("\n" + "=" * 70)
    print("IMPORT COMPLETE & VERIFIED!")
    print("=" * 70)


if __name__ == "__main__":
    dry_run_mode = "--dry-run" in sys.argv
    run_import(dry_run=dry_run_mode)
