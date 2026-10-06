import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "wrappers/python"))
from exchange_calendar import CalendarRegistry

fixture = json.load(open("tests/cross_language_queries.json"))
r = CalendarRegistry()
out = {}
for q in fixture["queries"]:
    op, args = q["op"], q["args"]
    if op == "sessions":
        v = [{"type": s.type, "open": s.open, "close": s.close, "at": s.at} for s in r.sessions(args[0])]
    elif op == "confidence":
        v = r.confidence(args[0], args[1])
    elif op == "is_open":
        v = r.is_open(args[0], args[1], args[2])
    elif op == "as_of":
        rec = r.as_of(args[0], args[1])
        v = {"confidence": rec.get("confidence", {}), "_as_of": rec.get("_as_of")}
    elif op == "holiday_entry":
        v = next((h for h in r.get(args[0]).list_holidays() if h["date"] == args[1]), None)
    else:
        raise SystemExit(f"unknown op {op}")
    out[q["label"]] = v
print(json.dumps(out, indent=2, sort_keys=True))
