"""Extract attributed claims and prepare evidence-backed graphs."""
import csv
import json
import os
import re
from collections import defaultdict
from datetime import datetime
from difflib import SequenceMatcher
from functools import lru_cache
from hashlib import sha256
from itertools import combinations
from pathlib import Path

import networkx as nx
from networkx.algorithms.community import louvain_communities

from benchmark import hand_written_reports
from corpus import examples
from fresh_benchmark import fresh_reports
from retest_benchmark import retest_reports
from training.context_retest import context_retest_reports
from training.test_reports import final_test_reports
import language_rules as rules

ROOT = Path(__file__).resolve().parent
PILOT_PATH = ROOT / "training" / "run" / "model-best"
SELECTION_PATH = ROOT / "training" / "selection.json"
RECORD_ID = re.compile(r"\[(P[0-9]+)\]")
PERSON_ID = re.compile(r"\s*" + RECORD_ID.pattern)
CAPITALS = re.compile(r"\b[A-Z][a-z]*(?:[-'][A-Z]?[a-z]+)?(?: +[A-Z][a-z]*(?:[-'][A-Z]?[a-z]+)?){0,3}\b")
LABELS = {"PERSON": "Person", "ORG": "Organisation", "GPE": "Location", "LOC": "Location", "FAC": "Location"}
ORG_ENDINGS = {"logistics", "transit", "cooperative", "services", "shipping", "foundation", "inc", "ltd", "university"}
PLACE_ENDINGS = {"bay", "port", "quay", "junction", "point", "basin", "street", "park", "station"}
PATTERNS = [
    ("Meeting", r"(?:met|meets?|held a meeting)\s*(?:with)?"),
    ("Communication", r"(?:called|calls|phoned|phones|spoke by phone with)"),
    ("Association", r"(?:works? for|is listed as a member of|is a member of)"),
]
DENIED = re.compile(r"\b(?:did not|never|denied|no evidence|didn't|ruled out)\b", re.I)
HEDGED = re.compile(r"\b(?:alleg\w*|reportedly|according to|may|might|possibly|unconfirmed|witness|claimed|planned to|would|could|rumou?red|unclear|disputed|uncorroborated)\b", re.I)
ALIAS = re.compile(r"^\s*,?\s*(?:also known as|aka|a\.k\.a\.)\s*$", re.I)

@lru_cache(maxsize=1)
def active_detector():
    override = os.environ.get("CASEGRAPH_NER")
    if override:
        if override not in {"pilot", "pretrained"}:
            raise ValueError("CASEGRAPH_NER must be pilot or pretrained.")
        return override
    if SELECTION_PATH.is_file() and PILOT_PATH.is_dir():
        return json.loads(SELECTION_PATH.read_text(encoding="utf-8"))["selected"]
    return "pretrained"


def model(detector=None):
    return load_detector(detector or active_detector())


@lru_cache(maxsize=2)
def load_detector(detector):
    if detector == "pilot":
        import spacy
        pipeline = spacy.load(PILOT_PATH)
        pipeline.add_pipe("sentencizer")
        return pipeline, "Casegraph fine-tuned spaCy"
    if detector != "pretrained":
        raise ValueError(f"Unknown detector: {detector}")
    try:
        import spacy
    except ImportError:
        return None, "Rule-based fallback"
    try:
        pipeline = spacy.load("en_core_web_sm", disable=["parser"])
        pipeline.add_pipe("sentencizer")
        return pipeline, "spaCy en_core_web_sm"
    except OSError:
        pipeline = spacy.blank("en")
        pipeline.add_pipe("sentencizer")
        return pipeline, "spaCy tokenization + rule-based NER"

def read_report(body, detector=None):
    nlp, _ = model(detector)
    has_ner = nlp is not None and nlp.has_pipe("ner")
    # Keep character positions stable for citations. The original body still
    # supplies identity markers when we attach them to the preceding names.
    model_text = RECORD_ID.sub(lambda match: " " * len(match.group()), body)
    doc = nlp(model_text) if nlp else None
    if doc is not None:
        sentences = [(sentence.start_char, sentence.end_char) for sentence in doc.sents]
    else:
        sentences = [match.span() for match in re.finditer(r"[^\n.!?]+(?:[.!?]+|(?=\n|$))", body)]
    mentions = {}
    for match in rules.KNOWN_NAMES.finditer(body):
        marker = PERSON_ID.match(body, match.end())
        if marker and all(part[0].isupper() for part in match.group().split()):
            mentions[match.span()] = ("Person", marker.group(1))
    for match in CAPITALS.finditer(body):
        if any(start <= match.start() and match.end() <= end for start, end in mentions):
            continue
        name = match.group()
        if " " not in name and not PERSON_ID.match(body, match.end()):
            continue
        tail = name.split()[-1].lower()
        marker = PERSON_ID.match(body, match.end())
        if marker:
            kind = "Person"
        elif has_ner:
            continue
        elif tail in ORG_ENDINGS:
            kind = "Organisation"
        elif tail in PLACE_ENDINGS:
            kind = "Location"
        else:
            kind = "Person"
        mentions[match.span()] = (kind, marker.group(1) if marker else None)
    if doc is not None:
        for ent in doc.ents:
            kind = LABELS.get(ent.label_)
            if RECORD_ID.search(body, ent.start_char, ent.end_char):
                continue
            if kind and not any(ent.start_char < end and ent.end_char > start for start, end in mentions):
                marker = PERSON_ID.match(body, ent.end_char)
                mentions[(ent.start_char, ent.end_char)] = ("Person" if marker else kind, marker.group(1) if marker else None)
    entities = [dict(name=body[start:end], start=start, end=end, type=kind, marker=marker)
                for (start, end), (kind, marker) in sorted(mentions.items())]
    return sentences, entities

def extract(report, include_sentences=False, enhanced=True, reference_entities=None, expanded=True, detector=None, contextual=True):
    body = report["text"]
    sentences, mentions = read_report(body, detector)
    if reference_entities is not None:
        mentions = [dict(start=item["start"], end=item["end"], type=item["type"],
                         name=body[item["start"]:item["end"]], marker=None)
                    for item in sorted(reference_entities, key=lambda item: item["start"])]
    elif enhanced:
        mentions = rules.refine_mentions(body, sentences, mentions, PERSON_ID)
        if expanded and contextual:
            mentions = rules.contextual_mentions(body, sentences, mentions, PERSON_ID)
    claims, aliases = [], []
    coordinated = enhanced and expanded and contextual
    alias_cue = rules.ALIAS_CUE if enhanced else ALIAS
    match_relation = rules.contextual_relationship if contextual else rules.expanded_relationship
    for start, end in sentences:
        text = body[start:end].strip()
        sentence_entities = [entity for entity in mentions if start <= entity["start"] < end]
        if coordinated:
            scopes = rules.claim_clauses(body, start, end, sentence_entities, PERSON_ID)
        else:
            breaks = [m.end() for m in rules.CLAUSE_BREAK.finditer(body, start, end)] if enhanced else []
            scopes = [(a, b, "") for a, b in zip([start, *breaks], [*breaks, end])]

        subject = None
        previous_status = ""
        attributed = False
        for begin, finish, join in scopes:
            members = [entity for entity in sentence_entities if begin <= entity["start"] < finish]
            pairs = [(a, b, a["end"], False) for a, b in zip(members, members[1:])]
            if join in ("and", "but") and subject and members:
                pairs.insert(0, (subject, members[0], begin, True))
            subject = None
            outer_attribution = attributed and join == "and"
            attributed = False
            if enhanced:
                clause_status = rules.claim_status(body[begin:finish], documented_attribution=expanded)
            else:
                clause_status = "Denied" if DENIED.search(text) else "Unverified claim" if HEDGED.search(text) or text.endswith("?") else "Directly reported"
            for left, right, verb_start, inherited in pairs:
                between = PERSON_ID.sub("", body[verb_start:right["start"]]).strip()
                prefix = "" if inherited else body[begin:left["start"]].rstrip()
                suffix = PERSON_ID.sub("", body[right["end"]:finish])
                if not inherited and left["type"] == right["type"] == "Person" and alias_cue.fullmatch(between):
                    aliases.append((left, right, text))
                    continue
                if enhanced and expanded:
                    matched = match_relation(prefix, between, suffix, left["type"], right["type"])
                    if (not matched and coordinated and not prefix and not inherited
                            and left["type"] == "Person" and not text.endswith("?")
                            and rules.SELF_REPORT.match(between)):
                        predicate = rules.SELF_REPORT.sub("", between, count=1)
                        if rules.NEGATIVE.search(predicate) and not any(
                            m["type"] == "Person" and m["name"].casefold() != left["name"].casefold()
                            for m in mentions if m["start"] < left["start"]
                        ):
                            matched = match_relation("", predicate, suffix, left["type"], right["type"])
                elif enhanced:
                    matched = rules.relationship(prefix, between)
                else:
                    matched = next(((kind, False) for kind, pattern in PATTERNS
                                    if re.search(r"\b(?:" + pattern + r")$", between, re.I)), None)
                if not matched:
                    continue
                kind, reverse = matched
                source, target = (right, left) if reverse else (left, right)
                if source["type"] != "Person" or target["type"] != ("Organisation" if kind == "Association" else "Person"):
                    continue
                if (coordinated and not target["marker"] and rules.VOICEMAIL_RECIPIENT.fullmatch(between)
                        and rules.NONPERSON_RECIPIENT.search(target["name"])):
                    continue
                status = clause_status
                if coordinated and status == "Directly reported":
                    if inherited and join == "and" and (rules.BARE_ACTION.match(between) or previous_status == "Unverified claim"):
                        status = previous_status
                    if status == "Directly reported" and (outer_attribution or text.endswith("?")):
                        status = "Unverified claim"
                claims.append(dict(source=source["start"], target=target["start"], type=kind, status=status,
                                   report=report["id"], sentence=text, offset=start))
                if coordinated:
                    attributed = outer_attribution or rules.claim_status(prefix, documented_attribution=True) == "Unverified claim"
                    # Only a verbal predicate supplies a grammatical subject for
                    # a following action. A nominal "meeting between A and B" does not.
                    if (right is members[-1] and not suffix.strip(" ,")
                            and not re.search(r"\band$", prefix, re.I)
                            and rules.contextual_relationship("", between, "", left["type"], right["type"])):
                        subject, previous_status = left, status
    if include_sentences:
        evidence = [(start, end, body[start:end].strip()) for start, end in sentences]
        return mentions, claims, aliases, evidence
    return mentions, claims, aliases

def graph_payload(nodes, edges):
    graph = nx.Graph()
    graph.add_nodes_from(nodes)
    graph.add_edges_from((edge["source"], edge["target"]) for edge in edges
                         if edge["status"] == "Directly reported" and edge.get("decision") != "rejected"
                         and edge["source"] != edge["target"])
    connected = graph.subgraph([node for node, degree in graph.degree if degree])
    groups = louvain_communities(connected, seed=42) if connected.number_of_edges() else []
    group_map = {node: i + 1 for i, group in enumerate(sorted(groups, key=lambda group: min(group))) for node in group}
    degree = nx.degree_centrality(graph) if len(graph) > 1 else dict.fromkeys(graph, 0)
    layout_graph = nx.Graph()
    layout_graph.add_nodes_from(nodes)
    layout_graph.add_edges_from((edge["source"], edge["target"]) for edge in edges if edge.get("decision") != "rejected")
    if len(layout_graph) < 400:
        positions = nx.spring_layout(layout_graph, seed=42, weight=None)
    else:
        positions = nx.circular_layout(layout_graph)
    weights = defaultdict(int)
    for edge in edges:
        if "weight" in edge and edge["decision"] != "rejected" and edge["status"] == "Directly reported":
            weights[edge["source"]] += edge["weight"]
            weights[edge["target"]] += edge["weight"]
    payload = [dict(node, activity_weight=weights[key], x=float(positions[key][0]), y=float(positions[key][1]), degree=graph.degree[key],
                    centrality=round(degree[key], 4), community=group_map.get(key))
               for key, node in nodes.items()]
    return dict(nodes=payload, edges=edges, communities=len(groups), model=model()[1])

def identity_candidates(nodes, edges, review):
    names_to_nodes = defaultdict(set)
    for node in nodes.values():
        if node["type"] == "Person":
            for name in node["names"]:
                names_to_nodes[name.casefold()].add(node["id"])

    contacts = defaultdict(dict)
    for edge in edges:
        if edge["status"] != "Directly reported" or edge["type"] == "Association":
            continue
        a, b = edge["source"], edge["target"]
        for source, contact in ((a, b), (b, a)):
            for name in nodes[contact]["names"]:
                contacts[source].setdefault(name.casefold(), edge)

    candidates = {}

    def propose(a, b, reason, priority):
        pair = tuple(sorted((a, b)))
        if a == b or (pair in candidates and candidates[pair]["priority"] >= priority):
            return
        shared = sorted(set(contacts[a]) & set(contacts[b]))
        support = []
        for name in shared[:3]:
            for node in pair:
                edge = contacts[node][name]
                source = dict(report=edge["report"], sentence=edge["sentence"])
                if source not in support:
                    support.append(source)
        candidates[pair] = dict(reason=reason, candidates=pair, priority=priority,
                                shared_contacts=shared, supporting_claims=support)

    for name, records in sorted(names_to_nodes.items()):
        for a, b in combinations(sorted(records), 2):
            propose(a, b, f"Multiple records share the name {name}", 2)

    blocks = defaultdict(list)
    for name in sorted(names_to_nodes):
        if " " in name:
            first, last = name.split()[0], name.split()[-1]
            blocks[("last", last)].append(name)
            blocks[("first", first)].append(name)
    for (position, _), names in blocks.items():
        for name, other in combinations(names, 2):
            similarity = SequenceMatcher(None, name, other).ratio()
            for a in sorted(names_to_nodes[name]):
                for b in sorted(names_to_nodes[other]):
                    corroborated = bool(contacts[a].keys() & contacts[b].keys())
                    similar = position == "last" and similarity >= .86
                    variant_with_context = corroborated and similarity >= .72
                    if similar or variant_with_context:
                        propose(a, b, f"Similar names: {name} and {other}", 1)
    return review + sorted(candidates.values(),
                           key=lambda item: (-bool(item["shared_contacts"]), -item["priority"], item["candidates"]))

def extract_network(reports, enhanced=True, expanded=True, detector=None, contextual=True):
    nodes, edges, review, mention_nodes = {}, [], [], {}
    resolution = defaultdict(list)
    for report in reports:
        mentions, claims, aliases, evidence_sentences = extract(
            report, include_sentences=True, enhanced=enhanced, expanded=expanded,
            detector=detector, contextual=contextual)
        ids = {}
        for mention in mentions:
            name = mention["name"].casefold()
            marker = mention["marker"]
            local_id = f'{report["id"]}:{mention["type"]}:{name}'
            if mention["type"] == "Person":
                local_id = f'{report["id"]}:person:{mention["start"]}'
            ids[mention["start"]] = marker or local_id
        for left, right, sentence in aliases:
            if left["marker"] and right["marker"] and left["marker"] != right["marker"]:
                review.append(dict(report=report["id"], sentence=sentence, reason="Alias claim has conflicting record IDs"))
                continue
            chosen = left["marker"] or right["marker"] or ids[left["start"]]
            if (rules.claim_status(sentence) != "Directly reported" if enhanced else DENIED.search(sentence) or HEDGED.search(sentence)):
                review.append(dict(report=report["id"], sentence=sentence, reason="Uncertain alias claim"))
                continue
            resolution[chosen].append(dict(report=report["id"], sentence=sentence))
            ids[left["start"]] = ids[right["start"]] = chosen
        for mention in mentions:
            offset = mention["start"]
            if mention.get("ambiguous_surname"):
                sentence = next((text for start, end, text in evidence_sentences if start <= offset < end), "")
                ids[offset] = f'{report["id"]}:unresolved:{offset}'
                review.append(dict(report=report["id"], sentence=sentence,
                                   reason=f"Several people in the report share the surname {mention['name']}"))
            elif "antecedent" in mention and not mention["marker"]:
                ids[offset] = ids[mention["antecedent"]]
            key = ids[offset]
            node = nodes.setdefault(key, dict(id=key, label=mention["name"], type=mention["type"], names=[], reports=[]))
            if mention["marker"]:
                node["record_id"] = mention["marker"]
            if mention["name"] not in node["names"]:
                node["names"].append(mention["name"])
            if report["id"] not in node["reports"]:
                node["reports"].append(report["id"])
            sentence = next((text for start, end, text in evidence_sentences if start <= offset < end), "")
            node.setdefault("identity_evidence", []).append(dict(report=report["id"], start=offset,
                                                              end=mention["end"], sentence=sentence))
            mention_nodes[(report["id"], mention["start"], mention["end"], mention["type"])] = key
        for claim in claims:
            source, target = ids[claim["source"]], ids[claim["target"]]
            if source != target:
                key = (report["id"], claim["source"], claim["target"], claim["type"], claim["status"])
                edges.append(dict(claim, source=source, target=target, source_offset=claim["source"],
                                  target_offset=claim["target"], id="claim-" + evidence_hash(key)[:24]))
    if enhanced:
        review = identity_candidates(nodes, edges, review)
    else:
        similar = defaultdict(list)
        for node in nodes.values():
            if node["type"] == "Person":
                for name in {name.casefold() for name in node["names"]}:
                    similar[name].append(node["id"])
        for name, candidates in similar.items():
            if len(candidates) > 1:
                review.append(dict(reason=f"Multiple records share the name {name}", candidates=candidates))
        surname_blocks = defaultdict(list)
        for name in similar:
            if " " in name:
                surname_blocks[name.rsplit(" ", 1)[-1]].append(name)
        for names in surname_blocks.values():
            for index, name in enumerate(names):
                for other in names[index + 1:]:
                    candidates = sorted(set(similar[name] + similar[other]))
                    if len(candidates) > 1 and SequenceMatcher(None, name, other).ratio() >= .86:
                        review.append(dict(reason=f"Similar names: {name} and {other}", candidates=candidates))
    for key, evidence in resolution.items():
        if key in nodes:
            nodes[key]["aliases"] = evidence
    return nodes, edges, review, mention_nodes

def evidence_hash(value):
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(data.encode("utf-8")).hexdigest()


def network_version(nodes, edges, review, reports):
    return evidence_hash(["network-extraction-v2", reports, nodes, edges, review, model()[1]])


def reviewed_graph(nodes, edges, review, reports, decisions=(), *, source_version=None, expected_version=None):
    source_version = source_version or network_version(nodes, edges, review, reports)
    if expected_version is not None and source_version != expected_version:
        raise ValueError("Source or extraction version changed. Saved decisions require a new review.")
    suggestions = {}
    notices = []
    for item in review:
        if "candidates" not in item:
            notices.append(item)
            continue
        for pair in combinations(sorted(set(item["candidates"])), 2):
            key = "m-" + sha256(repr(pair).encode()).hexdigest()[:24]
            if key not in suggestions:
                records = [dict(id=node, label=nodes[node]["label"], evidence=nodes[node]["identity_evidence"])
                           for node in pair]
                suggestions[key] = dict(id=key, reason=item["reason"], records=records,
                                        shared_contacts=item.get("shared_contacts", []),
                                        supporting_claims=item.get("supporting_claims", []))
    targets = set(suggestions) | {edge["id"] for edge in edges}
    if not isinstance(decisions, (tuple, list)) or len(decisions) > 300:
        raise ValueError("Provide a list of up to 300 review decisions.")
    history, latest = [], {}
    for item in decisions:
        if not isinstance(item, dict) or not isinstance(item.get("target"), str) or item["target"] not in targets:
            raise ValueError("A review target does not belong to this case.")
        choice = item.get("decision")
        if choice not in ("accepted", "rejected", "cleared"):
            raise ValueError("A review decision must be accepted, rejected, or cleared.")
        latest[item["target"]] = choice
        action = dict(target=item["target"], decision=choice)
        if "at" in item:
            if not isinstance(item["at"], str) or len(item["at"]) > 40:
                raise ValueError("Invalid review timestamp.")
            datetime.fromisoformat(item["at"])
            action["at"] = item["at"]
        if "note" in item:
            if not isinstance(item["note"], str) or len(item["note"]) > 300:
                raise ValueError("Review notes must fit in 300 characters.")
            action["note"] = item["note"]
        history.append(action)

    accepted = nx.Graph()
    accepted.add_nodes_from(nodes)
    for key, proposal in suggestions.items():
        proposal["decision"] = latest.get(key, "cleared")
        if proposal["decision"] == "accepted":
            accepted.add_edge(*(record["id"] for record in proposal["records"]))
    canonical = {}
    for group in nx.connected_components(accepted):
        markers = {nodes[key]["record_id"] for key in group if nodes[key].get("record_id")}
        if len(markers) > 1:
            raise ValueError("The proposed merge conflicts with distinct explicit person IDs.")
        root = next(iter(markers)) if markers else min(group)
        canonical.update(dict.fromkeys(group, root))
    for proposal in suggestions.values():
        a, b = (canonical[record["id"]] for record in proposal["records"])
        if proposal["decision"] == "rejected" and a == b:
            raise ValueError("This decision conflicts with another merge. Clear the conflicting decision first.")
        proposal["resolved"] = [a, b]

    merged = {}
    for key, node in nodes.items():
        root = canonical[key]
        target = merged.setdefault(root, dict(nodes[root], names=[], reports=[], identity_evidence=[], aliases=[]))
        for field in ("names", "reports", "identity_evidence", "aliases"):
            for item in node.get(field, []):
                if item not in target[field]:
                    target[field].append(item)

    reviewed_edges = [
        dict(edge, source=canonical[edge["source"]], target=canonical[edge["target"]],
             original_source=edge["source"], original_target=edge["target"],
             decision=latest.get(edge["id"], "cleared"))
        for edge in edges
    ]
    return dict(graph_payload(merged, reviewed_edges), source_version=source_version,
                review=notices + list(suggestions.values()),
                reports=reports, decisions=history)

@lru_cache(maxsize=8)
def prepared_text_evidence(serialized_reports, detector):
    """Keep original evidence for recent batches in process memory. Exclude review decisions."""
    reports = json.loads(serialized_reports)
    nodes, edges, review, _ = extract_network(reports, detector=detector)
    return nodes, edges, review, network_version(nodes, edges, review, reports)


def analyze(reports, decisions=(), *, expected_version=None):
    key = json.dumps(reports, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    nodes, edges, review, version = prepared_text_evidence(key, active_detector())
    return reviewed_graph(nodes, edges, review, reports, decisions, source_version=version,
                          expected_version=expected_version)

@lru_cache(maxsize=1)
def montagna_records():
    nodes, edges = {}, []
    with (ROOT / "Montagna_Roles.csv").open(encoding="utf-8-sig") as data:
        roles = {row["Node"]: row for row in csv.DictReader(data)}
    for filename, kind in [("Montagna_Meetings_Edgelist.csv", "Meeting"), ("Montagna_Phone_Calls_Edgelist.csv", "Communication")]:
        with (ROOT / filename).open(encoding="utf-8-sig") as data:
            rows = csv.reader(data) if kind == "Communication" else map(str.split, data)
            next(rows)
            for line, (a, b, weight) in enumerate(rows, 2):
                if a == b:
                    continue
                for key in (a, b):
                    metadata = {k: v for k, v in roles.get(key, {}).items() if v and k != "Node"}
                    nodes.setdefault(key, dict(id=key, label=key, type="Person", names=[key], metadata=metadata))
                edges.append(dict(id=f"e{len(edges)}", source=a, target=b, type=kind, status="Directly reported",
                                  report=filename, sentence=f"Row {line} · {a}, {b}, weight {weight}", weight=int(weight)))
    return nodes, edges

def montagna(decisions=(), *, expected_version=None):
    nodes, edges = montagna_records()
    return reviewed_graph(nodes, edges, [], [], decisions, expected_version=expected_version)

def metrics(expected, predicted):
    tp = len(expected & predicted)
    precision = tp / len(predicted) if predicted else 0
    recall = tp / len(expected) if expected else 0
    return dict(precision=precision, recall=recall, f1=2 * precision * recall / (precision + recall) if precision + recall else 0,
                tp=tp, fp=len(predicted) - tp, fn=len(expected) - tp)

def relationship_key(report_id, claim):
    return report_id, claim["source"], claim["target"], claim["type"], claim["status"]


def relationship_diagnostic(reports, expanded):
    expected, predicted, with_labels = set(), set(), set()
    for report in reports:
        key = report["id"]
        document = dict(id=key, text=report["text"])
        baseline = extract(document, expanded=expanded, detector="pretrained", contextual=False)[1]
        supplied = extract(document, expanded=expanded, reference_entities=report["mentions"], detector="pretrained", contextual=False)[1]
        expected.update(relationship_key(key, claim) for claim in report["relationships"])
        predicted.update(relationship_key(key, claim) for claim in baseline)
        with_labels.update(relationship_key(key, claim) for claim in supplied)
    return dict(predicted=metrics(expected, predicted), reference=metrics(expected, with_labels),
                labels=len(expected))


def score_reports(reports, enhanced=True, expanded=True, detector="pretrained", contextual=False):
    ner_gold, ner_pred, rel_gold, rel_pred = set(), set(), set(), set()
    for report in reports:
        mentions, claims, _ = extract(dict(id=report["id"], text=report["text"]), enhanced=enhanced, expanded=expanded, detector=detector, contextual=contextual)
        key = report["id"]
        for entities, target in ((report["mentions"], ner_gold), (mentions, ner_pred)):
            target.update((key, entity["start"], entity["end"], entity["type"]) for entity in entities)
        for relationships, target in ((report["relationships"], rel_gold), (claims, rel_pred)):
            target.update(relationship_key(key, claim) for claim in relationships)
    inputs = [dict(id=report["id"], text=report["text"]) for report in reports]
    _, _, proposals, resolved = extract_network(inputs, enhanced=enhanced, expanded=expanded, detector=detector, contextual=contextual)
    expected_clusters, predicted_clusters = defaultdict(list), defaultdict(list)
    for report in reports:
        for mention in report["mentions"]:
            if mention["type"] == "Person" and "identity" in mention:
                key = (report["id"], mention["start"], mention["end"], mention["type"])
                expected_clusters[mention["identity"]].append(key)
    for key, node in resolved.items():
        if key[-1] == "Person":
            predicted_clusters[node].append(key)
    def pairs(clusters):
        return {pair for group in clusters.values() for pair in combinations(sorted(group), 2)}
    expected_pairs = pairs(expected_clusters)
    automatic = pairs(predicted_clusters)
    proposed_node_pairs = {pair for item in proposals if "candidates" in item
                           for pair in combinations(sorted(set(item["candidates"])), 2)}
    proposed_mentions = {tuple(sorted((left, right))) for a, b in proposed_node_pairs
                         for left in predicted_clusters[a] for right in predicted_clusters[b]}
    identities = metrics(expected_pairs, automatic) if expected_clusters else None
    candidate_coverage = metrics(expected_pairs, automatic | proposed_mentions) if expected_clusters else None
    people = metrics({item for item in ner_gold if item[-1] == "Person"},
                     {item for item in ner_pred if item[-1] == "Person"})
    return dict(reports=len(reports), model=model(detector)[1], ner=metrics(ner_gold, ner_pred), people=people,
                relationships=metrics(rel_gold, rel_pred), identities=identities, identity_coverage=candidate_coverage)

@lru_cache(maxsize=1)
def evaluate():
    diagnostic = list(fresh_reports())
    retest = list(retest_reports())
    training_test = list(final_test_reports())
    training_scores = dict(pretrained=score_reports(training_test),
                           pilot=score_reports(training_test, detector="pilot") if PILOT_PATH.is_dir() else None,
                           selected=active_detector())
    contextual_test = list(context_retest_reports())
    detector = "pilot" if PILOT_PATH.is_dir() else "pretrained"
    contextual_scores = dict(before=score_reports(contextual_test, detector=detector),
                             after=score_reports(contextual_test, detector=detector, contextual=True),
                             regression_before=training_scores.get(detector)["relationships"],
                             regression_after=score_reports(training_test, detector=detector, contextual=True)["relationships"])
    return dict(score_reports(retest),
                contextual=contextual_scores,
                training=training_scores,
                baseline=score_reports(retest, expanded=False),
                diagnostic=dict(reports=len(diagnostic),
                                previous=relationship_diagnostic(diagnostic, expanded=False),
                                updated=relationship_diagnostic(diagnostic, expanded=True)),
                diagnosis=score_reports(list(hand_written_reports())),
                templates=score_reports([report for report in examples() if report["split"] == "test"]))
