"""Evidence-backed custody leads for the bundled fictional recorder case."""

import json
import re
from collections import defaultdict
from datetime import time
from itertools import combinations
from pathlib import Path

import networkx as nx

from analysis_engine import evidence_hash, network_version, reviewed_graph

CASE_DIR = Path(__file__).resolve().parent / "lead_cases"
CLOCK = r"(?:[01][0-9]|2[0-3]):[0-5][0-9]"
PERSON = r"[A-Z][A-Za-z.'’ -]+"
LOCATION = r"[a-z][a-z -]+"
CUSTODY = re.compile(
    rf"At (?P<time>{CLOCK}), (?P<name>{PERSON}) \[(?P<actor>P[0-9]+)\] "
    r"(?P<qualifier>reportedly |did not )?"
    r"(?P<action>checked out|check out|signed out|sign out|received|receive|handed over|hand over) "
    rf"(?P<item>[A-Z]+-[0-9]+)(?: to (?P<recipient>{PERSON}) \[(?P<recipient_id>P[0-9]+)\])?"
    rf" at the (?P<location>{LOCATION})\."
)
SHIFT = re.compile(
    rf"From (?P<start>{CLOCK}) to (?P<end>{CLOCK}), (?P<name>{PERSON}) "
    rf"\[(?P<actor>P[0-9]+)\] was logged at the (?P<location>{LOCATION})\."
)
ACTIONS = {"signed out": "Checkout", "sign out": "Checkout", "checked out": "Checkout", "check out": "Checkout", "received": "Receipt", "receive": "Receipt",
           "handed over": "Handover", "hand over": "Handover"}
STATUSES = {"reportedly ": "Unverified claim", "did not ": "Denied"}


def demo_case():
    return json.loads((CASE_DIR / "kit17.json").read_text(encoding="utf-8"))


def demo_answer():
    return json.loads((CASE_DIR / "kit17-answer.json").read_text(encoding="utf-8"))


def case_records(case):
    nodes = {}
    edges = []
    passages = []

    def node(key, label, kind):
        return nodes.setdefault(key, dict(id=key, label=label, type=kind, names=[label], reports=[],
                                         identity_evidence=[]))

    def person(key, name, report_id, sentence):
        record = node(key, name, "Person")
        if record["label"] != name:
            raise ValueError(f"Conflicting names for case record {key}.")
        if report_id not in record["reports"]:
            record["reports"].append(report_id)
        record["identity_evidence"].append(dict(report=report_id, sentence=sentence))

    node(case["item"], case["item"], "Item")
    for report in case["reports"]:
        for line_number, sentence in enumerate(report["text"].splitlines(), 1):
            parsed = CUSTODY.fullmatch(sentence)
            shift = SHIFT.fullmatch(sentence)
            if not sentence.strip():
                continue
            outcome = "parsed" if parsed or shift else (
                "context" if report.get("kind") == "context" else "needs review")
            passages.append(dict(report=report["id"], line=line_number, text=sentence, outcome=outcome))
            if not (parsed or shift):
                continue
            fields = (parsed or shift).groupdict()
            actor, name = fields["actor"], fields["name"]
            person(actor, name, report["id"], sentence)
            if parsed:
                item = fields["item"]
                node(item, item, "Item")
                kind = ACTIONS[fields["action"]]
                if bool(fields["recipient"]) != (kind == "Handover"):
                    raise ValueError("A handover record needs a named recipient.")
                status = STATUSES.get(fields["qualifier"], "Directly reported")
                metadata = dict(time=fields["time"], item=item, location=fields["location"])
                roles = [(actor, "Sender")] if kind == "Handover" else [(actor, "Holder")]
                if fields["recipient_id"]:
                    recipient = fields["recipient_id"]
                    person(recipient, fields["recipient"], report["id"], sentence)
                    roles.append((recipient, "Recipient"))
                target = item
            else:
                if time.fromisoformat(fields["end"]) < time.fromisoformat(fields["start"]):
                    raise ValueError("A shift record ends before it starts.")
                target = "place:" + fields["location"].replace(" ", "-")
                node(target, fields["location"].title(), "Location")
                kind, status = "Shift record", "Directly reported"
                metadata = dict(start=fields["start"], end=fields["end"], location=fields["location"])
                roles = [(actor, "Attendance")]
            for source, role in roles:
                edges.append(dict(id=f'{report["id"]}:{line_number}:{role}', source=source, target=target,
                                  role=role, report=report["id"], origin=report["origin"], sentence=sentence,
                                  type=kind, status=status, **metadata))
    return nodes, edges, passages


def identity_suggestions(nodes):
    people = [node for node in nodes.values() if node["type"] == "Person"]
    for first, second in combinations(people, 2):
        a = first["label"].casefold().split()
        b = second["label"].casefold().split()
        if len(a) == len(b) == 2 and a[1] == b[1] and a[0] != b[0]:
            if any(len(short) == 2 and short.endswith(".") and short[0] == full[0]
                   and len(full) > 2 for short, full in [(a[0], b[0]), (b[0], a[0])]):
                yield dict(reason=f'Initial and surname match: {first["label"]} and {second["label"]}',
                           candidates=[first["id"], second["id"]])


def independent_support(records):
    """Choose as many distinct origin/event pairs as possible and retain a citation for each."""
    graph = nx.Graph()
    for record in sorted(records, key=lambda evidence: evidence["id"]):
        event = (record["time"], record["item"], record["location"])
        origin = record["origin"]
        if not graph.has_edge(origin, event):
            graph.add_edge(origin, event, record=record)
    pairs = nx.max_weight_matching(graph, maxcardinality=True)
    selected = [graph[a][b]["record"] for a, b in pairs]
    return [record["id"] for record in sorted(selected, key=lambda row: (row["time"], row["id"]))]


def rank_leads(case, graph):
    by_person = defaultdict(list)
    start, end = (case["window"][key] for key in ("start", "end"))
    for edge in graph["edges"]:
        if edge["decision"] != "rejected":
            by_person[edge["source"]].append(edge)

    cards = []
    for person in graph["nodes"]:
        sources = by_person.get(person["id"], [])
        custody = [e for e in sources if e.get("item") == case["item"] and e["location"] == case["location"]
                   and start <= e["time"] <= end and e["role"] != "Sender"]
        if not custody:
            continue
        direct = [e for e in custody if e["status"] == "Directly reported"]
        claims = [e for e in custody if e["status"] != "Denied"]
        conflicts = [e for e in sources if e["type"] == "Shift record" and e["location"] != case["location"]
                     and any(e["start"] <= claim["time"] <= e["end"] for claim in claims)]
        supporting = independent_support(direct)
        denied = [e for e in custody if e["status"] == "Denied"]
        conflicts.extend(e for e in denied
                         if any(e["time"] == claim["time"] and e["type"] == claim["type"] for claim in claims))
        conflict_ids = {record["id"] for record in conflicts}
        matches = [r for r in graph["review"] if r.get("decision") == "cleared"
                   and person["id"] in r["resolved"] and len(set(r["resolved"])) > 1]
        cards.append(dict(id=person["id"], name=person["label"], names=person["names"],
                          count=len(supporting), support=supporting,
                          other=[e["id"] for e in custody if e["id"] not in supporting and e["id"] not in conflict_ids],
                          conflicts=[e["id"] for e in conflicts], pending_matches=[r["id"] for r in matches],
                          latest=max((e["time"] for e in direct), default=None)))

    cards.sort(key=lambda lead: (-lead["count"], lead["name"].casefold(), lead["id"]))
    strongest = None
    reason = "Insufficient evidence to prioritize one lead."
    if cards and cards[0]["count"] >= 2:
        first, *rest = cards
        if any(card["count"] == first["count"] for card in rest):
            reason = "The strongest leads have equal independent support."
        elif first["conflicts"]:
            reason = "The most supported lead has conflicting evidence to review."
        elif first["pending_matches"]:
            reason = "Review the remaining identity match before prioritizing this lead."
        elif any(card["latest"] and card["latest"] >= first["latest"] for card in rest):
            reason = "Another record places a different handler at the same time or later."
        else:
            strongest = first["id"]
            reason = "Two or more independent custody records support the latest documented handling."
    return dict(cards=cards, strongest=strongest, reason=reason)


def lead_graph(case, decisions=(), *, expected_version=None):
    nodes, edges, passages = case_records(case)
    suggestions = list(identity_suggestions(nodes))
    public_case = {key: case[key] for key in ("id", "title", "question", "item", "date", "location", "window")}
    version = network_version(nodes, edges, suggestions, case["reports"])
    version = evidence_hash(["custody-v2", version, public_case, passages])
    graph = reviewed_graph(nodes, edges, suggestions, case["reports"], decisions,
                           source_version=version, expected_version=expected_version)
    lead = rank_leads(case, graph)
    if any(p["outcome"] == "needs review" for p in passages):
        lead.update(strongest=None, reason="A source passage needs review before prioritizing a handler.")
    return dict(graph, case=public_case, lead=lead, passages=passages, model="Custody event rules")
