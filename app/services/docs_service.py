import os
import json
import re

def find_docs_dir():
    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "docs")),
        "/app/docs",
        os.path.abspath("docs"),
        os.path.join(os.getcwd(), "docs"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs"))
    ]
    for c in candidates:
        if os.path.isdir(c) and (os.path.exists(os.path.join(c, "inventory.json")) or os.path.exists(os.path.join(c, "REBUILD.md"))):
            return c
    for c in candidates:
        if os.path.isdir(c):
            return c
    return candidates[0]

DOCS_DIR = find_docs_dir()

def parse_markdown_table(text: str):
    rows = []
    lines = [l.strip() for l in text.split("\n") if l.strip().startswith("|")]
    if len(lines) < 3:
        return rows
    
    headers = [h.strip() for h in lines[0].split("|")[1:-1]]
    for line in lines[2:]:
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) == len(headers):
            row = dict(zip(headers, cols))
            rows.append(row)
    return rows

def get_system_docs_data():
    """
    Parses the reconstruct documentation suite into structured JSON
    for the Super Admin rich documentation portal.
    """
    data = {
        "overview": {},
        "metrics": {},
        "architecture": {},
        "diagrams": [],
        "interfaces": [],
        "data_model": {"entities": {}, "enums": []},
        "design_system": {},
        "features": [],
        "rebuild": {}
    }

    # 1. Load inventory.json if available
    inv_path = os.path.join(DOCS_DIR, "inventory.json")
    if os.path.exists(inv_path):
        try:
            with open(inv_path, "r", encoding="utf-8") as f:
                inv = json.load(f)
                data["metrics"] = {
                    "total_files": inv.get("metrics", {}).get("totalFiles", 236),
                    "total_lines": inv.get("metrics", {}).get("totalLines", 62498),
                    "features_count": len(inv.get("features", [])),
                    "routes_count": len(inv.get("routes", [])),
                    "tracked_env_vars": len(inv.get("envVars", []))
                }
                data["stack"] = inv.get("stack", {})
        except Exception:
            pass

    # 2. 00-overview/PRD.md
    overview_path = os.path.join(DOCS_DIR, "00-overview", "PRD.md")
    if os.path.exists(overview_path):
        with open(overview_path, "r", encoding="utf-8") as f:
            otxt = f.read()
            prod_summary = ""
            if "## Product summary" in otxt:
                prod_summary = otxt.split("## Product summary")[1].split("## ")[0].strip()
            data["overview"]["product_summary"] = prod_summary

    # 3. architecture/ARCHITECTURE.md
    arch_path = os.path.join(DOCS_DIR, "architecture", "ARCHITECTURE.md")
    if os.path.exists(arch_path):
        with open(arch_path, "r", encoding="utf-8") as f:
            atxt = f.read()
            services = []
            if "## External services & integrations" in atxt:
                svc_txt = atxt.split("## External services & integrations")[1].split("## ")[0]
                for match in re.finditer(r"###?\s*\d*\.?\s*([^\n:]+):?\s*\n(.*?)(?=\n###?|\Z)", svc_txt, re.DOTALL):
                    title = match.group(1).strip()
                    desc = match.group(2).strip()
                    services.append({"name": title, "description": desc})
            data["architecture"]["external_services"] = services

            policies = []
            if "## Cross-cutting policies" in atxt:
                pol_txt = atxt.split("## Cross-cutting policies")[1].split("## ")[0]
                for match in re.finditer(r"###?\s*\d*\.?\s*([^\n:]+):?\s*\n(.*?)(?=\n###?|\Z)", pol_txt, re.DOTALL):
                    title = match.group(1).strip()
                    desc = match.group(2).strip()
                    policies.append({"name": title, "description": desc})
            data["architecture"]["policies"] = policies

    # 4. architecture/diagram.md
    diag_path = os.path.join(DOCS_DIR, "architecture", "diagram.md")
    if os.path.exists(diag_path):
        with open(diag_path, "r", encoding="utf-8") as f:
            dtxt = f.read()
            pattern = re.compile(r"##\s*(\d*\.?\s*[^\n]+)\s*\n+```mermaid\s*\n(.*?)\n```", re.DOTALL)
            for m in pattern.finditer(dtxt):
                title = m.group(1).strip()
                code = m.group(2).strip()
                slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
                data["diagrams"].append({
                    "id": slug,
                    "title": title,
                    "code": code
                })

    # 5. architecture/INTERFACES.md
    interfaces_path = os.path.join(DOCS_DIR, "architecture", "INTERFACES.md")
    if os.path.exists(interfaces_path):
        with open(interfaces_path, "r", encoding="utf-8") as f:
            itxt = f.read()
            if "## Interface table" in itxt:
                tbl_txt = itxt.split("## Interface table")[1].split("## ")[0]
                parsed = parse_markdown_table(tbl_txt)
                for r in parsed:
                    data["interfaces"].append({
                        "method": r.get("Method / Trigger", ""),
                        "path": r.get("Path / Operation", ""),
                        "kind": r.get("Kind", ""),
                        "handler": r.get("Handler file", ""),
                        "auth": r.get("Auth", ""),
                        "notes": r.get("Notes & Side Effects", "") or r.get("Notes", "")
                    })

    # 6. architecture/DATA-MODEL.md
    dm_path = os.path.join(DOCS_DIR, "architecture", "DATA-MODEL.md")
    if os.path.exists(dm_path):
        with open(dm_path, "r", encoding="utf-8") as f:
            dmtxt = f.read()
            if "## Entities" in dmtxt:
                tbl_txt = dmtxt.split("## Entities")[1].split("## ")[0]
                rows = parse_markdown_table(tbl_txt)
                for r in rows:
                    tbl = r.get("Entity / Table", "").replace("`", "").strip()
                    if tbl not in data["data_model"]["entities"]:
                        data["data_model"]["entities"][tbl] = []
                    data["data_model"]["entities"][tbl].append({
                        "field": r.get("Field", "").replace("`", "").strip(),
                        "type": r.get("Type", "").strip(),
                        "constraints": r.get("Constraints", "").strip(),
                        "relation": r.get("Relation", "").strip()
                    })

            if "## Enums & domain types" in dmtxt:
                enum_txt = dmtxt.split("## Enums & domain types")[1].split("## ")[0]
                for match in re.finditer(r"###?\s*\d*\.?\s*`?([^\n`:]+)`?:?\s*\((.*?)\)\s*\n(.*?)(?=\n###?|\Z)", enum_txt, re.DOTALL):
                    name = match.group(1).strip()
                    desc = match.group(2).strip()
                    body = match.group(3).strip()
                    items = [l.strip("- *").strip() for l in body.split("\n") if l.strip().startswith(("-", "*", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8."))]
                    data["data_model"]["enums"].append({
                        "name": name,
                        "description": desc,
                        "items": items
                    })

    # 7. architecture/DESIGN-SYSTEM.md
    ds_path = os.path.join(DOCS_DIR, "architecture", "DESIGN-SYSTEM.md")
    if os.path.exists(ds_path):
        with open(ds_path, "r", encoding="utf-8") as f:
            dstxt = f.read()
            if "### Core Color Palette" in dstxt:
                color_tbl = dstxt.split("### Core Color Palette")[1].split("### ")[0].split("## ")[0]
                data["design_system"]["colors"] = parse_markdown_table(color_tbl)

    # 8. features/*/PRD.md
    features_dir = os.path.join(DOCS_DIR, "features")
    if os.path.exists(features_dir):
        for slug in sorted(os.listdir(features_dir)):
            f_path = os.path.join(features_dir, slug, "PRD.md")
            if not os.path.exists(f_path):
                continue
            with open(f_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else slug

            def extract_section(name):
                if f"## {name}" in content:
                    part = content.split(f"## {name}")[1].split("## ")[0].strip()
                    return part
                return ""

            summary = extract_section("Summary")
            context = extract_section("Context & goal")
            
            stories_raw = extract_section("User stories")
            stories = [s.strip("- *").strip() for s in stories_raw.split("\n") if s.strip().startswith(("-", "*"))]

            reqs_raw = extract_section("Functional requirements")
            reqs = [r.strip("- *").strip() for r in reqs_raw.split("\n") if r.strip().startswith(("-", "*", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8."))]

            acceptance_raw = extract_section("Acceptance criteria")
            acceptance = [a.strip("- *").strip() for a in acceptance_raw.split("\n") if a.strip().startswith(("-", "*"))]

            edge_raw = extract_section("Edge cases & failure modes")
            edge_cases = [e.strip("- *").strip() for e in edge_raw.split("\n") if e.strip().startswith(("-", "*"))]

            improvements_raw = extract_section("Improvements & enhancements")
            improvements = [i.strip("- *").strip() for i in improvements_raw.split("\n") if i.strip().startswith(("-", "*"))]

            data["features"].append({
                "slug": slug,
                "title": title,
                "summary": summary,
                "context": context,
                "stories": stories,
                "requirements": reqs,
                "acceptance": acceptance,
                "edge_cases": edge_cases,
                "improvements": improvements
            })

    # 9. REBUILD.md
    rebuild_path = os.path.join(DOCS_DIR, "REBUILD.md")
    if os.path.exists(rebuild_path):
        with open(rebuild_path, "r", encoding="utf-8") as f:
            rtxt = f.read()
            if "## Build order" in rtxt:
                bo_txt = rtxt.split("## Build order")[1].split("## ")[0]
                data["rebuild"]["build_order"] = [l.strip() for l in bo_txt.split("\n") if l.strip()]
            if "Required env vars configured:" in rtxt:
                env_match = re.search(r"Required env vars configured:\s*`([^`]+)`", rtxt)
                if env_match:
                    raw_vars = [v.strip() for v in env_match.group(1).split(",")]
                    data["rebuild"]["env_vars"] = raw_vars

    return data

