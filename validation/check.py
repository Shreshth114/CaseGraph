"""Score frozen fictional fixtures, including source citations and decisions to abstain."""
import json
from pathlib import Path

from analysis_engine import PILOT_PATH, extract, metrics, relationship_key, score_reports
from lead_finder import lead_graph

HERE = Path(__file__).resolve().parent


def fixture(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def custody_results():
    keys = {row["id"]: row for row in fixture("custody_keys.json")}
    results = []
    for case in fixture("custody_cases.json"):
        graph = lead_graph(case)
        lead = graph["lead"]
        key = keys[case["id"]]
        support = {card["id"]: card["support"] for card in lead["cards"]}
        sources = {row["id"]: row["text"].splitlines() for row in case["reports"]}
        cited = {eid for values in support.values() for eid in values}
        exact = all(edge["sentence"] in sources[edge["report"]] for edge in graph["edges"] if edge["id"] in cited)
        results.append(dict(case=case["id"], expected=key["strongest"], actual=lead["strongest"],
                            reason=lead["reason"], correct_reason=key["reason"] in lead["reason"],
                            citations=exact and support == key["support"]))
    return results


def field_results():
    rows = fixture("field_reports.json")
    expected = {relationship_key(r["id"], c) for r in rows for c in r["relationships"]}
    detector = "pilot" if PILOT_PATH.is_dir() else "pretrained"
    predicted = {relationship_key(r["id"], c) for r in rows for c in extract(r, detector=detector)[1]}
    by_type = {k: metrics({x for x in expected if x[3] == k}, {x for x in predicted if x[3] == k})
               for k in ("Communication", "Association", "Meeting")}
    current = score_reports(rows, detector=detector, contextual=True)
    return dict(previous=fixture("baseline.json")["field"], current=dict(current, types=by_type))


if __name__ == "__main__":
    print(json.dumps(dict(custody=custody_results(), field=field_results()), indent=2))
