"""Link cases to other cases, stored in a separate JSON file.

Data file format (caseLinks.json, created automatically on first use):
{
  "caseLinks": [
    {
      "id": "clink-001",
      "case_id": "case-001",
      "related_case_id": "case-008",
      "relation_type": "related",
      "note": null
    }
  ]
}
"""

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

# Adjust these two paths to match your file names.
CASES_FILE = Path("mockProblemsDB.json")
CASE_LINKS_FILE = Path("mockProblemLink.json")
WRAPPER_KEY = "caseLinks"


# ---------- small utilities ----------

def load_json(path, default=None):
    """Load JSON. If a default is given, a missing or empty file returns it."""
    path = Path(path)
    if not path.exists():
        if default is not None:
            return default
        raise ValueError(f"{path} not found (looking in {path.resolve().parent}).")
    text = path.read_text(encoding="utf-8-sig")
    if not text.strip() and default is not None:
        return default
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"{path} is not valid JSON ({e}). Is the file empty?")


def save_json(path, data):
    """Write atomically so a crash can't leave a half-written file."""
    fd, tmp = tempfile.mkstemp(dir=Path(path).resolve().parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception:
        os.unlink(tmp)
        raise


def next_id(prefix, items, width=3):
    numbers = [
        int(m.group(1))
        for item in items
        if (m := re.fullmatch(rf"{re.escape(prefix)}-(\d+)", item["id"]))
    ]
    return f"{prefix}-{max(numbers, default=0) + 1:0{width}d}"


# ---------- link two cases ----------

def link_cases(case_id, related_case_id, relation_type="related", note=None):
    """
    Link one case to another and return the link.

    - Both cases must exist in the cases file.
    - A case cannot be linked to itself.
    - If the same pair is already linked with the same relation_type
      (in either direction), the existing link is returned unchanged.
    """
    if case_id == related_case_id:
        raise ValueError("A case cannot be linked to itself.")

    known_ids = {c["id"] for c in load_json(CASES_FILE)["cases"]}
    for cid in (case_id, related_case_id):
        if cid not in known_ids:
            raise ValueError(f"Case '{cid}' not found.")

    data = load_json(CASE_LINKS_FILE, default={WRAPPER_KEY: []})
    links = data[WRAPPER_KEY]

    pair = {case_id, related_case_id}
    for existing in links:
        if (
            {existing["case_id"], existing["related_case_id"]} == pair
            and existing["relation_type"] == relation_type
        ):
            return existing

    link = {
        "id": next_id("clink", links),
        "case_id": case_id,
        "related_case_id": related_case_id,
        "relation_type": relation_type,
        "note": note,
    }
    links.append(link)
    save_json(CASE_LINKS_FILE, data)
    return link


# ---------- look up links ----------

def get_linked_cases(case_id):
    """Return every case linked to case_id, regardless of link direction."""
    links = load_json(CASE_LINKS_FILE, default={WRAPPER_KEY: []})[WRAPPER_KEY]
    result = []
    for l in links:
        if l["case_id"] == case_id:
            other = l["related_case_id"]
        elif l["related_case_id"] == case_id:
            other = l["case_id"]
        else:
            continue
        result.append({
            "linked_case_id": other,
            "relation_type": l["relation_type"],
            "note": l.get("note"),
            "link_id": l["id"],
        })
    return result


# ---------- command-line interface ----------

def main():
    parser = argparse.ArgumentParser(description="Link cases to other cases.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_link = sub.add_parser("link", help="Link two cases")
    p_link.add_argument("--case", required=True, help="e.g. case-001")
    p_link.add_argument("--related", required=True, help="e.g. case-008")
    p_link.add_argument("--type", default="related",
                        help='e.g. related, duplicate, follow-up (default: related)')
    p_link.add_argument("--note", default=None, help="Optional free-text note")

    p_list = sub.add_parser("list", help="List cases linked to a case")
    p_list.add_argument("--case", required=True)

    args = parser.parse_args()

    try:
        if args.command == "link":
            result = link_cases(args.case, args.related, args.type, args.note)
            print("Linked:")
        else:
            result = get_linked_cases(args.case)
            print(f"Cases linked to {args.case}:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except ValueError as e:
        sys.exit(f"Error: {e}")


if __name__ == "__main__":
    main()