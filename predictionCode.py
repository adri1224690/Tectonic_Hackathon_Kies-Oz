#!/usr/bin/env python3
"""Predict which kinds of cases a (new) company might run into.

It finds existing companies that resemble the described one (country, industry,
size) and looks at which kinds of cases those companies have had. Each issue
type gets a score: the similarity-weighted share of comparable companies that
have had that type of issue.

Usage:
    python predict_cases.py --country Belgium --size medium
    python predict_cases.py --country Belgium --industry Consulting --size medium --top 5

Needs cases.json and companies.json in the current folder.
Company size is an optional field ("small", "medium", "large") in companies.json;
companies without it are simply compared on country and industry.
"""
import argparse
from collections import defaultdict

import json
import re

# Keyword -> theme. Extend this to match the vocabulary in your own cases.
THEMES = {
    "pay_equity": ["unequal", "gender", "gap", "equal", "discrimination"],
    "working_time_pay": ["overtime", "night", "shift", "premium", "unpaid"],
    "benefits_allowances": ["allowance", "bonus", "remote", "eligibility"],
    "equity_compensation": ["stock", "option", "vesting", "equity", "executive"],
    "leave": ["parental", "leave", "maternity", "sick"],
    "wage_bargaining": ["wage", "agreement", "deadlock", "inflation", "adjustment", "indexation"],
    "worker_status": ["contractor", "misclassification", "freelance"],
    "disclosure": ["disclosure", "transparency"],
}

INDUSTRY_GROUPS = {
    "tech": {"Software", "Data Analytics", "Digital Agency", "Robotics"},
    "professional_services": {"Consulting", "Financial Services"},
    "industrial": {"Manufacturing", "Logistics", "Energy", "Pharmaceuticals"},
}

COUNTRY_REGIONS = {
    "benelux_dach_fr": {"Belgium", "Netherlands", "Germany", "France", "Switzerland"},
    "nordics_uk": {"Sweden", "United Kingdom"},
    "north_america": {"United States", "Canada"},
    "asia_pacific": {"Japan"},
}
EUROPE = {"Belgium", "Netherlands", "Germany", "France", "Switzerland",
          "Sweden", "United Kingdom"}

STOPWORDS = {"a", "an", "the", "of", "for", "and", "or", "to", "in", "on",
             "resolved", "solved", "fixed", "settled", "closed", "ended",
             "approved", "corrected", "mediated", "repaid", "dispute", "claim"}


def read(path, key):
    with open(path, encoding="utf-8") as f:
        return json.load(f)[key]


def words(text):
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in STOPWORDS}


def themes(title):
    w = words(title)
    return {t for t, kws in THEMES.items() if w & set(kws)}


def group_of(value, groups):
    return next((g for g, members in groups.items() if value in members), None)


SIZES = ["micro", "small", "medium", "large", "enterprise"]


def company_similarity(q, c):
    """Return (similarity 0..1, reasons). Only signals known on both sides count."""
    earned = possible = 0.0
    why = []

    if q.get("country") and c.get("country"):
        possible += 3
        if q["country"] == c["country"]:
            earned += 3; why.append(f"same country ({c['country']})")
        elif group_of(q["country"], COUNTRY_REGIONS) == group_of(c["country"], COUNTRY_REGIONS) \
                and group_of(c["country"], COUNTRY_REGIONS):
            earned += 1.5; why.append(f"same region ({c['country']})")
        elif q["country"] in EUROPE and c["country"] in EUROPE:
            earned += 0.75; why.append("both in Europe")

    if q.get("industry") and c.get("industry"):
        possible += 3
        if q["industry"] == c["industry"]:
            earned += 3; why.append(f"same industry ({c['industry']})")
        else:
            g = group_of(q["industry"], INDUSTRY_GROUPS)
            if g and g == group_of(c["industry"], INDUSTRY_GROUPS):
                earned += 1.5; why.append(f"related industry ({c['industry']})")

    if q.get("size") and c.get("size") and q["size"] in SIZES and c["size"] in SIZES:
        possible += 2
        gap = abs(SIZES.index(q["size"]) - SIZES.index(c["size"]))
        if gap == 0:
            earned += 2; why.append(f"same size ({c['size']})")
        elif gap == 1:
            earned += 1; why.append(f"similar size ({c['size']})")

    return (earned / possible if possible else 0.0), why


def predict(query, companies, cases, min_sim):
    by_company = defaultdict(list)
    for c in cases.values():
        by_company[c["company_id"]].append(c)

    comparable = []  # (similarity, company, reasons)
    for comp in companies.values():
        sim, why = company_similarity(query, comp)
        if sim >= min_sim:
            comparable.append((sim, comp, why))
    comparable.sort(key=lambda x: -x[0])

    total_weight = sum(s for s, _, _ in comparable)
    theme_weight = defaultdict(float)   # weight of companies that had the theme
    theme_cases = defaultdict(list)     # (similarity, company, case)
    for sim, comp, _ in comparable:
        seen = set()
        for case in by_company.get(comp["id"], []):
            ts = themes(case["title"]) or {"other"}
            for t in ts:
                theme_cases[t].append((sim, comp, case))
                if t not in seen:          # count each company once per theme
                    theme_weight[t] += sim
                    seen.add(t)
    return comparable, total_weight, theme_weight, theme_cases


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--country")
    p.add_argument("--industry")
    p.add_argument("--size", choices=SIZES)
    p.add_argument("--top", type=int, default=5, help="max issue types to show")
    p.add_argument("--min-sim", type=float, default=0.3,
                   help="ignore companies less similar than this (0-1)")
    p.add_argument("--cases", default="mockProblemsDB.json")
    p.add_argument("--companies", default="mockCompaniesDB.json")
    a = p.parse_args()
    if not (a.country or a.industry or a.size):
        p.error("give at least one of --country, --industry, --size")

    query = {"country": a.country, "industry": a.industry, "size": a.size}
    companies = {c["id"]: c for c in read(a.companies, "companies")}
    cases = {c["id"]: c for c in read(a.cases, "cases")}

    comparable, total, theme_weight, theme_cases = predict(query, companies, cases, a.min_sim)
    desc = ", ".join(f"{k}: {v}" for k, v in query.items() if v)
    print(f"New company -> {desc}")

    if not comparable:
        print("\nNo comparable companies found (try lowering --min-sim).")
        return

    print("\n== Comparable companies ==")
    for sim, comp, why in comparable:
        n = sum(1 for c in cases.values() if c["company_id"] == comp["id"])
        print(f"  {sim:.0%}  {comp['name']} ({n} case{'s' if n != 1 else ''}) - {'; '.join(why)}")

    print("\n== Issues this company might run into ==")
    ranked = sorted(theme_weight, key=lambda t: -theme_weight[t])[:a.top]
    if not ranked:
        print("  Comparable companies have no recorded cases.")
    for t in ranked:
        print(f"\n  {t.replace('_', ' ')}  -  {theme_weight[t] / total:.0%} of comparable companies (weighted)")
        for sim, comp, case in sorted(theme_cases[t], key=lambda x: -x[0]):
            print(f"      {case['id']} ({case['year']}, {comp['name']}): {case['title']}")

    print(f"\nBased on {len(comparable)} comparable compan{'y' if len(comparable) == 1 else 'ies'}; "
          "with few companies treat this as a rough pointer, not a probability.")


if __name__ == "__main__":
    main()