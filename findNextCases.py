#!/usr/bin/env python3
"""Show cases directly linked to a given case.

Usage: python direct_links.py case-001
"""
import json
import sys

case_id = sys.argv[1]

with open("mockProblemsDB.json", encoding="utf-8") as f:
    cases = {c["id"]: c for c in json.load(f)["cases"]}
with open("mockProblemLink.json", encoding="utf-8") as f:
    links = json.load(f)["caseLinks"]

if case_id not in cases:
    sys.exit(f"Unknown case: {case_id}")

print(f'{case_id}: {cases[case_id]["title"]}')
found = False
for l in links:
    # Links count in both directions
    if l["case_id"] == case_id:
        other = l["related_case_id"]
    elif l["related_case_id"] == case_id:
        other = l["case_id"]
    else:
        continue
    found = True
    title = cases[other]["title"] if other in cases else "(case not found)"
    note = f' - {l["note"]}' if l.get("note") else ""
    print(f'  [{l["relation_type"]}] {other}: {title}{note}')

if not found:
    print("  No directly linked cases.")