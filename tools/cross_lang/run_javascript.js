const fs = require("fs");
const path = require("path");
const { CalendarRegistry } = require(path.resolve("wrappers/javascript/src"));

const fixture = JSON.parse(fs.readFileSync("tests/cross_language_queries.json", "utf8"));
const r = new CalendarRegistry();
const out = {};
for (const q of fixture.queries) {
  const [a, b, c] = q.args;
  let v;
  if (q.op === "sessions") v = r.sessions(a).map(s => ({ type: s.type, open: s.open ?? null, close: s.close ?? null, at: s.at ?? null }));
  else if (q.op === "confidence") v = r.confidence(a, b);
  else if (q.op === "is_open") v = r.isOpen(a, b, c);
  else if (q.op === "as_of") { const rec = r.asOf(a, b); v = { confidence: rec.confidence, _as_of: rec._as_of }; }
  else if (q.op === "holiday_entry") v = r.get(a).listHolidays().find(h => h.date === b) ?? null;
  else throw new Error(`unknown op ${q.op}`);
  out[q.label] = v;
}
function sortKeys(obj) {
  if (Array.isArray(obj)) return obj.map(sortKeys);
  if (obj && typeof obj === 'object') {
    const sorted = {};
    for (const k of Object.keys(obj).sort()) sorted[k] = sortKeys(obj[k]);
    return sorted;
  }
  return obj;
}
console.log(JSON.stringify(sortKeys(out), null, 2));
