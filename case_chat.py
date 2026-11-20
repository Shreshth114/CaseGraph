"""Evidence retrieval and case-specific answers for the Inspector chat."""

import re

from analysis_engine import model

WORD = re.compile(r"[^\W_]+(?:[-’'][^\W_]+)*")
RELATIONSHIP = {
    "Meeting": {"meet", "meets", "met", "meeting", "meetings"},
    "Communication": {"call", "calls", "called", "communication", "communications", "phone", "phoned", "voicemail"},
    "Association": {"association", "affiliation", "member", "membership", "work", "works", "worked", "employed"},
}
STATUS = {
    "Denied": {"denied", "deny", "negated"},
    "Unverified claim": {"unverified", "uncertain", "reportedly", "alleged", "unconfirmed"},
    "Directly reported": {"directly", "documented", "affirmative"},
}
QUESTION_WORDS = set("""
a about according all and any are as at be between by can case could did do does else for found from
give had has have how i in is it link links list me of on or our please report reported reports
record records row says said see show some source sources support supports tell that the their
there these they this those to us was were what when where which who whom why will with would
you evidence connection connections relationship relationships claim claims say mentioned mentions
mention details detail information related knows know summary summarize find happened
""".split())
LEAD = re.compile(r"\b(?:strongest lead|lead to follow up|who (?:should|can) (?:i|we) (?:contact|ask|follow up)|insufficient evidence|prioriti[sz]\w*)\b")
LAST = re.compile(r"\b(?:last|latest|most recent)\b.*\b(?:handl\w*|receiv\w*|had|hold\w*|custody|record\w*)\b")
IDENTITY = re.compile(r"\b(?:same (?:name|person)|alias(?:es)?|identity|separat\w*|merge\w*|two records)\b")
CULPABILITY = re.compile(r"\b(?:culprit|guilty|guilt|who stole|who committed|who is responsible|who (?:is|was) the (?:criminal|thief|suspect))\b")
REFERENCE = re.compile(r"\b(?:this|that|the selected|last|previous) (?:connection|link|claim|relationship|evidence|answer|record)\b|\bits source\b")
LIMIT = 5


def words(text):
    return WORD.findall(text.casefold())


def answer(message, citations=(), action=None):
    return dict(message=message, citations=list(citations), action=action)


def citation(source, *, status=None, edge=None):
    return dict(report=source["report"], quote=source["sentence"], status=status, edge=edge)


def edge_citation(edge):
    return citation(edge, status=edge["status"], edge=edge["id"])


def matching_nodes(question_words, nodes):
    """Use full names, aliases and record IDs. Prefer an explicit ID over its shared name."""
    phrase = f" {' '.join(question_words)} "
    matching_ids = set()
    matching_names = {}
    for node in nodes.values():
        if f" {' '.join(words(node['id']))} " in phrase:
            matching_ids.add(node["id"])
        for name in node["names"]:
            normalized = " ".join(words(name))
            if f" {normalized} " in phrase:
                matching_names.setdefault(normalized, set()).add(node["id"])
    return [{key} for key in sorted(matching_ids)] + [
        group for group in matching_names.values() if not group.intersection(matching_ids)
    ]


def lead_answer(graph, edges, *, latest=False):
    lead = graph["lead"]
    cards = lead["cards"]
    if latest:
        last_time = max((card["latest"] for card in cards if card["latest"]), default=None)
        if last_time is None:
            return answer(lead["reason"], action="leads")
        latest_cards = [card for card in cards if card["latest"] == last_time]
        names = ", ".join(card["name"] for card in latest_cards)
        source_ids = [edge_id for card in latest_cards for edge_id in card["support"] + card["other"]
                      if edges[edge_id].get("time") == last_time and edges[edge_id]["status"] == "Directly reported"]
        message = f"The latest directly reported handling at {last_time} names {names}."
        if not lead["strongest"]:
            message += f" {lead['reason']}"
        return answer(message, (edge_citation(edges[key]) for key in source_ids[:LIMIT]), "leads")
    strongest = next((card for card in cards if card["id"] == lead["strongest"]), None)
    if strongest:
        message = (f"{strongest['name']} is the strongest follow-up lead. "
                   f"{strongest['count']} independent custody records support the lead, "
                   f"with the latest directly reported handling at {strongest['latest']}.")
        return answer(message, (edge_citation(edges[key]) for key in strongest["support"][:LIMIT]), "leads")
    pending = [item for item in graph["review"] if item.get("id") and item["decision"] == "cleared"
               and len(set(item["resolved"])) > 1]
    if pending and ("Insufficient evidence" in lead["reason"] or "identity match" in lead["reason"]):
        match = pending[0]
        names = " and ".join(record["label"] for record in match["records"])
        sources = [citation(source) for record in match["records"] for source in record["evidence"][:1]]
        return answer(f"{lead['reason']} The records name {names}. Review the possible identity match.", sources, "review")
    supporting = dict.fromkeys(key for card in cards for key in card["support"] + card["conflicts"] + card["other"])
    return answer(lead["reason"], (edge_citation(edges[key]) for key in list(supporting)[:LIMIT]), "leads")


def identity_answer(graph, nodes, mentioned):
    proposals = [item for item in graph["review"] if item.get("records")
                 and (not mentioned or mentioned.intersection(item["resolved"]))]
    if proposals:
        proposal = max(proposals, key=lambda item: len(mentioned.intersection(item["resolved"])))
        records = proposal["records"]
        labels = " and ".join(f"{record['label']} [{record['id']}]" for record in records)
        state = ("are grouped after identity review" if len(set(proposal["resolved"])) == 1
                 else "are separate records in this case")
        quotes = [citation(source) for record in records for source in record["evidence"][:1]]
        if len(set(proposal["resolved"])) > 1 and all(re.fullmatch(r"P\d+", record["id"]) for record in records):
            if records[0]["label"].casefold() == records[1]["label"].casefold():
                return answer(f"{labels} are shown separately because the reports give them distinct record IDs.", quotes)
        return answer(f"{labels} {state}. {proposal['reason']}.", quotes, "review")
    groups = {}
    for node in nodes.values():
        if node["type"] == "Person":
            groups.setdefault(node["label"].casefold(), []).append(node)
    for group in groups.values():
        if len(group) > 1 and (not mentioned or mentioned.intersection(node["id"] for node in group)):
            labels = ", ".join(f"{node['label']} [{node['id']}]" for node in group[:LIMIT])
            quotes = [citation(source) for node in group[:LIMIT] for source in node.get("identity_evidence", [])[:1]]
            return answer(f"{labels} are displayed separately because they have distinct record IDs.", quotes)
    return answer("I found no matching identity comparison in this case. Try asking with both names or record IDs.",
                  action="review")


def report_matches(reports, terms):
    if not terms:
        return []
    nlp, _ = model()
    matches = []
    for report in reports:
        text = report["text"]
        passages = (span.text for span in nlp.get_pipe("sentencizer")(nlp.make_doc(text)).sents) if nlp else text.splitlines()
        for passage in passages:
            if terms.issubset(words(passage)):
                matches.append(citation(dict(report=report["id"], sentence=passage.strip())))
                if len(matches) == LIMIT:
                    return matches
    return matches


def ask_case(question, graph, context_edge=None):
    tokens = words(question)
    terms = set(tokens)
    phrase = " ".join(tokens)
    nodes = {node["id"]: node for node in graph["nodes"]}
    edges = {edge["id"]: edge for edge in graph["edges"] if edge["decision"] != "rejected"}
    groups = matching_nodes(tokens, nodes)
    mentioned = set().union(*groups)

    if CULPABILITY.search(phrase):
        if graph.get("lead"):
            result = lead_answer(graph, edges)
            result["message"] = "The records can support a follow-up lead. " + result["message"]
            return result
        return answer("The case records support exploring reported connections. For an evidence-backed answer, ask about a specific person, meeting, or call.")
    if IDENTITY.search(phrase) and (mentioned or not re.search(r"\band\b.*\bsame person\b", phrase)):
        return identity_answer(graph, nodes, mentioned)
    if graph.get("lead") and (LEAD.search(phrase) or LAST.search(phrase)):
        named_items = {term for term in terms if re.fullmatch(r"[a-z]+-[0-9]+", term)}
        if not named_items or graph["case"]["item"].casefold() in named_items:
            return lead_answer(graph, edges, latest=bool(LAST.search(phrase)))
    elif REFERENCE.search(phrase):
        edge = edges.get(context_edge)
        if edge:
            return answer(f"The selected {edge['type'].lower()} is marked {edge['status']}.", [edge_citation(edge)])
        return answer("Select a graph connection and reopen Ask this case, or include the names from the connection in your question.")

    kinds = {kind for kind, synonyms in RELATIONSHIP.items() if synonyms.intersection(terms)}
    statuses = {status for status, synonyms in STATUS.items() if synonyms.intersection(terms)}
    if re.search(r"\b(?:did|does|do) not\b|\bnever\b", phrase):
        statuses.add("Denied")
    leftover = terms - QUESTION_WORDS - {"not", "never"}
    for options in (*RELATIONSHIP.values(), *STATUS.values()):
        leftover -= options
    for key in mentioned:
        node = nodes[key]
        leftover.difference_update(words(node["id"]))
        for name in node["names"]:
            leftover.difference_update(words(name))

    if mentioned or kinds or statuses or leftover:
        hits = []
        for edge in edges.values():
            endpoints = {edge["source"], edge["target"]}
            if not all(endpoints.intersection(group) for group in groups):
                continue
            if (kinds and edge["type"] not in kinds) or (statuses and edge["status"] not in statuses):
                continue
            if leftover and not leftover.issubset(words(edge["sentence"] + " " + edge["report"])):
                continue
            hits.append(edge)
        if hits:
            labels = {key: node["label"] for key, node in nodes.items()}
            for group in groups:
                for key in group:
                    if len(group) > 1 or (nodes[key].get("record_id") and key.casefold() in terms):
                        labels[key] += f" [{key}]"
            summary = ", ".join(f"{labels[edge['source']]} · {labels[edge['target']]} "
                                f"({edge['type'].lower()}, {edge['status'].lower()})" for edge in hits[:LIMIT])
            more = f" Showing {LIMIT} of {len(hits)} matching rows." if len(hits) > LIMIT else ""
            return answer(f"Matching evidence includes {summary}.{more}", (edge_citation(edge) for edge in hits[:LIMIT]))

    if not (kinds or statuses) and leftover:
        matches = report_matches(graph["reports"], terms - QUESTION_WORDS)
        if matches:
            return answer("These source passages match your question. Open a passage to read more of the report.", matches)
    return answer("I couldn't find evidence that answers that in the open case. Try a person’s full name, a record ID, or a relationship type.")
