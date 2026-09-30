"""Helpers for managing companies and case-company links stored in JSON files."""

import json
import os
import re
import tempfile
from pathlib import Path

DATA_DIR = Path(".")
COMPANIES_FILE = DATA_DIR / "mockCompaniesDB.json"
CASES_FILE = DATA_DIR / "mockProblemsDB.json"
LINKS_FILE = DATA_DIR / "mockCompanyCaseLinks.json"


# ---------- small utilities ----------

def load_json(path):
    try:
        # utf-8-sig also handles files saved with a BOM (common with Windows Notepad)
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except FileNotFoundError:
        raise ValueError(f"{path} not found (looking in {Path(path).resolve().parent}).")
    except json.JSONDecodeError as e:
        raise ValueError(f"{path} is not valid JSON ({e}). Is the file empty?")


def save_json(path, data):
    """Write atomically so a crash can't leave a half-written file."""
    fd, tmp = tempfile.mkstemp(dir=Path(path).parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception:
        os.unlink(tmp)
        raise


def next_id(prefix, items, width=3):
    """Return the next id like 'comp-011' based on the highest existing one."""
    numbers = [
        int(m.group(1))
        for item in items
        if (m := re.fullmatch(rf"{re.escape(prefix)}-(\d+)", item["id"]))
    ]
    return f"{prefix}-{max(numbers, default=0) + 1:0{width}d}"


# ---------- 1. add a company ----------

def add_company(name, country, industry):
    """Add a new company to companies.json and return it."""
    data = load_json(COMPANIES_FILE)
    companies = data["companies"]

    if any(c["name"].strip().lower() == name.strip().lower() for c in companies):
        raise ValueError(f"A company named '{name}' already exists.")

    company = {
        "id": next_id("comp", companies),
        "name": name.strip(),
        "country": country.strip(),
        "industry": industry.strip(),
    }
    companies.append(company)
    save_json(COMPANIES_FILE, data)
    return company


# ---------- 2. link a company to a case (problem) ----------

def link_company_to_case(case_id, company_id, replace=False):
    """
    Link a company to a case.

    Updates both case_company_links.json and the case's own company_id field,
    so the two sources stay in sync. Each case can have only one company:
    if the case is already linked to a different company, a ValueError is
    raised unless replace=True.
    """
    companies = load_json(COMPANIES_FILE)["companies"]
    cases_data = load_json(CASES_FILE)
    links_data = load_json(LINKS_FILE)

    case = next((c for c in cases_data["cases"] if c["id"] == case_id), None)
    if case is None:
        raise ValueError(f"Case '{case_id}' not found.")
    if not any(c["id"] == company_id for c in companies):
        raise ValueError(f"Company '{company_id}' not found.")

    links = links_data["case_company_links"]
    existing = next((l for l in links if l["case_id"] == case_id), None)

    if existing:
        if existing["company_id"] == company_id:
            return existing  # already linked, nothing to do
        if not replace:
            raise ValueError(
                f"{case_id} is already linked to {existing['company_id']}. "
                "Use replace=True to change it."
            )
        existing["company_id"] = company_id
        link = existing
    else:
        link = {
            "id": next_id("link", links),
            "case_id": case_id,
            "company_id": company_id,
        }
        links.append(link)

    case["company_id"] = company_id
    save_json(LINKS_FILE, links_data)
    save_json(CASES_FILE, cases_data)
    return link


# ---------- command-line interface ----------

def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Manage companies and case links.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add-company", help="Add a new company")
    p_add.add_argument("--name", required=True)
    p_add.add_argument("--country", required=True)
    p_add.add_argument("--industry", required=True)

    p_link = sub.add_parser("link", help="Link a company to a case")
    p_link.add_argument("--case", required=True, help="e.g. case-004")
    p_link.add_argument("--company", required=True, help="e.g. comp-008")
    p_link.add_argument("--replace", action="store_true",
                        help="Move the case if it is already linked to another company")

    args = parser.parse_args()

    try:
        if args.command == "add-company":
            result = add_company(args.name, args.country, args.industry)
            print("Added company:")
        else:
            result = link_company_to_case(args.case, args.company, args.replace)
            print("Linked:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except ValueError as e:
        sys.exit(f"Error: {e}")


if __name__ == "__main__":
    main()