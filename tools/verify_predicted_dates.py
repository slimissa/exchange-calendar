#!/usr/bin/env python3
"""
verify_predicted_dates.py — Track and verify "predicted" Islamic holiday dates.

Usage:
  python3 tools/verify_predicted_dates.py          # Report pending dates
  python3 tools/verify_predicted_dates.py --check  # Exit 1 if past-due dates exist
  python3 tools/verify_predicted_dates.py --list   # List all pending dates grouped by exchange
"""

import json
import sys
from datetime import date
from pathlib import Path

TODAY = date.today()

def load_exchanges(exchanges_dir: Path) -> dict:
    """Load all exchange files into a dict keyed by MIC code."""
    exchanges = {}
    for path in sorted(exchanges_dir.glob("*.json")):
        with open(path) as f:
            data = json.load(f)
        exchanges[data["code"]] = data
    return exchanges


def find_predicted_entries(exchanges: dict) -> list:
    """Find all entries with predicted=true field or "(predicted)" in name."""
    pending = []
    for code, data in exchanges.items():
        for holiday in data.get("holidays", {}).get("explicit", []):
            name = holiday.get("name", "")
            is_predicted_field = holiday.get("predicted", False)
            is_predicted_suffix = "(predicted)" in name
            is_predicted = is_predicted_field or is_predicted_suffix
            
            if is_predicted:
                entry_date = date.fromisoformat(holiday["date"])
                days_since = (TODAY - entry_date).days if entry_date < TODAY else None
                pending.append({
                    "exchange": code,
                    "date": holiday["date"],
                    "name": name,
                    "is_past": entry_date < TODAY,
                    "days_since": days_since,
                    "has_field": is_predicted_field,
                    "has_suffix": is_predicted_suffix
                })
    return pending


def find_past_due(pending: list) -> list:
    """Find predicted entries whose dates have passed (now verifiable)."""
    return [e for e in pending if e["is_past"]]


def find_future(pending: list) -> list:
    """Find predicted entries whose dates are still in the future."""
    return [e for e in pending if not e["is_past"]]


def print_report(pending: list, past_due: list, future: list):
    """Print a formatted report."""
    print(f"\n{'='*80}")
    print(f"PREDICTED ISLAMIC DATES STATUS — {TODAY}")
    print(f"{'='*80}")
    print(f"\n  Total predicted: {len(pending)}")
    print(f"  Past due (verifiable now): {len(past_due)}")
    print(f"  Future (not yet announced): {len(future)}")
    
    if past_due:
        print(f"\n{'='*80}")
        print("PAST DUE — THESE CAN NOW BE VERIFIED")
        print(f"{'='*80}")
        print(f"\n  {'Exchange':<10} {'Date':<12} {'Days Ago':<10} {'Holiday'}")
        print(f"  {'-'*10} {'-'*12} {'-'*10} {'-'*40}")
        for e in sorted(past_due, key=lambda x: x["date"]):
            print(f"  {e['exchange']:<10} {e['date']:<12} {e['days_since']:<10} {e['name']}")
    
    if future:
        print(f"\n{'='*80}")
        print("FUTURE — MOON-SIGHTING NOT YET ANNOUNCED")
        print(f"{'='*80}")
        print(f"\n  {'Exchange':<10} {'Date':<12} {'Holiday'}")
        print(f"  {'-'*10} {'-'*12} {'-'*40}")
        for e in sorted(future, key=lambda x: x["date"]):
            print(f"  {e['exchange']:<10} {e['date']:<12} {e['name']}")
    
    # Check for inconsistencies
    print(f"\n{'='*80}")
    print("CONSISTENCY CHECKS")
    print(f"{'='*80}")
    
    field_only = [e for e in pending if e["has_field"] and not e["has_suffix"]]
    suffix_only = [e for e in pending if e["has_suffix"] and not e["has_field"]]
    both = [e for e in pending if e["has_field"] and e["has_suffix"]]
    
    print(f"  predicted=true only (no suffix): {len(field_only)}")
    print(f"  '(predicted)' suffix only (no field): {len(suffix_only)}")
    print(f"  Both field and suffix: {len(both)}")
    
    if field_only:
        print(f"\n  ⚠️  Entries with predicted=true but no suffix (should have both):")
        for e in field_only:
            print(f"    {e['exchange']}: {e['date']} — {e['name']}")
    
    if suffix_only:
        print(f"\n  ⚠️  Entries with suffix but no predicted=true (should have both):")
        for e in suffix_only:
            print(f"    {e['exchange']}: {e['date']} — {e['name']}")
    
    if not field_only and not suffix_only:
        print(f"\n  ✅ All predicted entries have both field and suffix (or neither)")


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Track and verify predicted Islamic holiday dates"
    )
    parser.add_argument("--check", action="store_true", 
                        help="Exit 1 if any predicted dates are past-due")
    parser.add_argument("--list", action="store_true", 
                        help="List all pending dates grouped by exchange")
    parser.add_argument("--registry-dir", default=".", 
                        help="Registry root directory")
    args = parser.parse_args()

    exchanges_dir = Path(args.registry_dir) / "exchanges"
    if not exchanges_dir.exists():
        print(f"❌ Exchanges directory not found: {exchanges_dir}")
        sys.exit(2)
    
    exchanges = load_exchanges(exchanges_dir)
    pending = find_predicted_entries(exchanges)
    past_due = find_past_due(pending)
    future = find_future(pending)

    if args.list or (not args.check and not args.list):
        print_report(pending, past_due, future)

    if args.check:
        if past_due:
            print(f"\n❌ {len(past_due)} predicted dates are past-due for verification")
            print("   These dates can now be verified against actual announcements.")
            print("   See: docs/predicted_dates_pending.md")
            sys.exit(1)
        else:
            print(f"\n✅ No past-due predicted dates")
            print(f"   {len(future)} future dates pending moon-sighting announcements")
            sys.exit(0)


if __name__ == "__main__":
    main()
