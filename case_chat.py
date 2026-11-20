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
PEOPLE_WORDS = {"people", "person", "persons", "individual", "individuals", "participants", "names"}
ROSTER_WORDS = {"all", "everyone", "involved", "connected", "identify", "many", "name",
                "network", "people", "persons", "individuals", "participants", "named"}
ROSTER_CONTEXT = {"investigation", "file", "files", "dataset"}
LEAD = re.compile(r"\b(?:strongest lead|lead to follow up|who (?:should|can) (?:i|we) (?:contact|ask|follow up)|insufficient evidence|prioriti[sz]\w*)\b")
LAST = re.compile(r"\b(?:last|latest|most recent)\b.*\b(?:handl\w*|receiv\w*|had|hold\w*|custody|record\w*)\b")
IDENTITY = re.compile(r"\b(?:same (?:name|person)|alias(?:es)?|identity|separat\w*|merge\w*|two records)\b")
CULPABILITY = re.compile(r"\b(?:culprit|guilty|guilt|killer|murderer|criminal|thief|killed|murdered|stole|"
                         r"who committed|who is responsible|did .+? (?:kill|murder|steal)|suspects?)\b")
PROFILE = re.compile(r"\b(?:who (?:is|are|was|were)|tell me about|what do (?:we|you) know about)\b")
PRONOUN = re.compile(r"\bwho (?:is|was) (?:she|he|this person)\b|\bwho (?:are|were) they\b")
GREETINGS = {"hi", "hy", "hey", "hello", "hiya", "good morning", "good afternoon", "good evening"}
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


def node_label(node, *, include_id=False):
    label = node["label"]
    if include_id or re.fullmatch(r"[A-Z]+[0-9]+", node["id"]):
        label += f" [{node['id']}]"
    aliases = [name for name in node["names"] if name != node["label"]]
    if aliases:
        label += f" (also recorded as {', '.join(aliases)})"
    return label


def people_answer(nodes, edges):
    people = sorted((node for node in nodes.values() if node["type"] == "Person"),
                    key=lambda node: (node["label"].casefold(), node["id"]))
    if not people:
        return answer("There are no person records in the open case.")
    label_counts = {}
    person_sources = {}
    for edge in edges.values():
        for key in (edge["source"], edge["target"]):
            person_sources.setdefault(key, edge)
    for node in people:
        label = node["label"].casefold()
        label_counts[label] = label_counts.get(label, 0) + 1
    names = [node_label(node, include_id=label_counts[node["label"].casefold()] > 1) for node in people]
    quotes = []
    for node in people:
        edge = person_sources.get(node["id"])
        evidence = node.get("identity_evidence", [])
        source = edge_citation(edge) if edge else next((citation(row) for row in evidence if row["sentence"]), None)
        if source and source not in quotes:
            quotes.append(source)
        if len(quotes) == LIMIT:
            break
    count = f"{len(people)} {'record' if len(people) == 1 else 'records'}"
    return answer(f"People named in the open case ({count})\n" + "\n".join(f"• {name}" for name in names), quotes)


def follow_up_answer(graph, nodes, edges):
    intro = "The evidence supports following up on custody of the missing KIT-17 recorder. The records leave guilt undetermined."
    lead = graph["lead"]
    if not lead["cards"]:
        return answer(f"{intro} {lead['reason']}", action="leads")
    sources = []
    entries = []
    for card in lead["cards"]:
        records = [edges[key] for key in card["support"] + card["other"]]
        if card["latest"]:
            summary = f"Latest directly reported handling at {card['latest']}."
        elif any(edge["status"] == "Unverified claim" for edge in records):
            summary = "Named in an unverified custody claim."
        else:
            summary = "Named in a denied custody claim."
        if card["conflicts"]:
            summary += " The file includes conflicting evidence."
        entries.append(f"• {node_label(nodes[card['id']])}. {summary}")
        sources.extend(records + [edges[key] for key in card["conflicts"]])
    strongest = lead["strongest"]
    outcome = (f"{nodes[strongest]['label']} is the strongest follow-up lead." if strongest
               else lead_answer(graph, edges)["message"])
    citations = list({edge["id"]: edge_citation(edge) for edge in sources}.values())
    return answer(f"{intro} {outcome}\n" + "\n".join(entries), citations[:LIMIT], "leads")


def profile_answer(graph, nodes, edges, candidates):
    people = {key for key in candidates if nodes[key]["type"] == "Person"}
    candidates = people or candidates
    if not candidates:
        return dict(answer("Who do you mean? Include a name or record ID, or select an entity before opening the chat."), node=None)
    if len(candidates) > 1:
        choices = ", ".join(f"{nodes[key]['label']} [{key}]" for key in sorted(candidates)[:LIMIT])
        return dict(answer(f"Which record do you mean? The case matches {choices}. Ask using the record ID."), node=None)

    key = next(iter(candidates))
    node = nodes[key]
    name = node["label"]
    label = node_label(node)
    rows = [edge for edge in edges.values() if key in (edge["source"], edge["target"])]
    card = next((card for card in graph.get("lead", {}).get("cards", []) if card["id"] == key), None)
    if card and card["conflicts"]:
        shift = next((edges[edge_id] for edge_id in card["conflicts"] if edges[edge_id]["type"] == "Shift record"), None)
        if shift:
            custody_records = (edges[edge_id] for edge_id in card["support"] + card["other"])
            custody = next((edge for edge in custody_records if edge["status"] != "Denied"
                            and shift["start"] <= edge["time"] <= shift["end"]
                            and edge["location"] != shift["location"]), None)
            if custody:
                message = (f"The shift register places {label} at the {shift['location']} from "
                           f"{shift['start']} to {shift['end']}. A custody record with status "
                           f"{custody['status'].lower()} places {name} at the {custody['location']} "
                           f"at {custody['time']}. Lead Finder flags the conflicting locations.")
                return dict(answer(message, [edge_citation(shift), edge_citation(custody)]), node=key)
    quotes = [edge_citation(edge) for edge in rows[:LIMIT]]
    if not quotes:
        quotes = [citation(source) for source in node.get("identity_evidence", [])[:LIMIT] if source["sentence"]]
    message = f"{label} appears in the case as a {node['type'].lower()}."
    if quotes:
        message += " These records show what the sources say about this entity."
    return dict(answer(message, quotes), node=key)


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


def ask_case(question, graph, context_edge=None, context_node=None):
    tokens = words(question)
    terms = set(tokens)
    phrase = " ".join(tokens)
    if phrase in GREETINGS:
        example = "Who last handled KIT-17?" if "lead" in graph else "Which claims are unverified?"
        return answer(f"Hi! I can help you read this case. Try “{example}” or ask who a person in the graph is.")
    nodes = {node["id"]: node for node in graph["nodes"]}
    edges = {edge["id"]: edge for edge in graph["edges"] if edge["decision"] != "rejected"}
    groups = matching_nodes(tokens, nodes)
    mentioned = set().union(*groups)

    if terms.intersection({"suspect", "suspects"}) and not any(nodes[key]["type"] == "Person" for key in mentioned):
        if graph.get("lead"):
            return follow_up_answer(graph, nodes, edges)
        roster = people_answer(nodes, edges)
        roster["message"] = "These records identify people mentioned in the case. Their mention alone gives no basis to classify them as suspects.\n" + roster["message"]
        return roster
    if CULPABILITY.search(phrase):
        intro = ("This case concerns the missing KIT-17 recorder. " if graph.get("lead") else "")
        intro += "The open records provide insufficient evidence to determine guilt."
        if mentioned:
            result = profile_answer(graph, nodes, edges, mentioned)
            result["message"] = f"{intro} {result['message']}"
            return result
        if graph.get("lead"):
            result = lead_answer(graph, edges)
            result["message"] = f"{intro} {result['message']}"
            return result
        return answer(f"{intro} Ask about a person or relationship to read the underlying evidence.")
    roster_words = QUESTION_WORDS | PEOPLE_WORDS | ROSTER_WORDS | ROSTER_CONTEXT
    if not mentioned and terms.intersection(ROSTER_WORDS) and terms <= roster_words:
        if "how" in terms and "many" in terms:
            count = sum(node["type"] == "Person" for node in nodes.values())
            return answer(f"The open case contains {count} person {'record' if count == 1 else 'records'}.")
        return people_answer(nodes, edges)
    if IDENTITY.search(phrase) and (mentioned or not re.search(r"\band\b.*\bsame person\b", phrase)):
        return identity_answer(graph, nodes, mentioned)
    if graph.get("lead") and (LEAD.search(phrase) or LAST.search(phrase)):
        named_items = {term for term in terms if re.fullmatch(r"[a-z]+-[0-9]+", term)}
        if not named_items or graph["case"]["item"].casefold() in named_items:
            return lead_answer(graph, edges, latest=bool(LAST.search(phrase)))
    profile = PROFILE.search(phrase)
    if profile:
        remainder = set(words(phrase[profile.end():])) - QUESTION_WORDS - {"she", "he", "person", "them", "her", "him"}
        for key in mentioned:
            remainder.difference_update(words(nodes[key]["id"]))
            for name in nodes[key]["names"]:
                remainder.difference_update(words(name))
        if not remainder:
            if not mentioned and PRONOUN.search(phrase):
                edge = edges.get(context_edge)
                if context_node in nodes:
                    mentioned = {context_node}
                elif edge:
                    mentioned = {edge["source"], edge["target"]}
            return profile_answer(graph, nodes, edges, mentioned)
    if REFERENCE.search(phrase):
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
