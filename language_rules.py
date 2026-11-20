"""Conservative English patterns for explicitly reported relationship claims."""
import re
from bisect import bisect_left

NAME = re.compile(r"\b[A-Z][a-z]+(?:[-'’][A-Z]?[a-z]+)*(?:[ \t]+[A-Z][a-z]+(?:[-'’][A-Z]?[a-z]+)*){1,3}\b")
ORG_SUFFIX = re.compile(r"\b(?:associates|association|bank|cooperative|corporation|corp|council|department|"
                        r"foundation|freight|group|holdings|inc|institute|laboratories|logistics|ltd|ministry|"
                        r"services|shipping|society|systems|transit|university)\.?$", re.I)
PLACE_SUFFIX = re.compile(r"\b(?:bay|basin|harbour|harbor|junction|park|pier|point|port|quay|station|street)$", re.I)
TITLE = re.compile(r"\b(?:mr|mrs|ms|dr|prof|detective|officer|clerk|archivist|driver|manager|"
                   r"accountant|witness|supervisor|inspector)(?:\.\s*|\s+)(?:named\s+)?$", re.I)
DETERMINER = re.compile(r"^(?:the|a|an)\s+", re.I)
ALIAS_CUE = re.compile(r"^\s*,?\s*(?:also known as|known by the alias|goes by|aka|a\.k\.a\.)\s*$", re.I)
CLAUSE_BREAK = re.compile(r";\s*|,\s*(?:but|whereas|while|however)\s+|\s+(?:but|whereas)\s+", re.I)
NEGATIVE = re.compile(r"\b(?:not(?!\s+(?:only|confirmed|verified))|no\s+(?:call|meeting|contact)|never|den(?:ied|ies|y)|"
                      r"didn['’]t|wasn['’]t|couldn['’]t|ruled out)\b", re.I)
HEDGE = re.compile(r"\b(?:alleg\w*|reportedly|according to|may|might|possibly|unconfirmed|"
                   r"witness\w*|claim\w*|plan(?:ned|s)?\s+to|schedul\w+|would|could|rumou?red|"
                   r"unclear|disputed|uncorroborated|suspect\w*|purported\w*|believ\w*|no evidence|no proof|not confirmed|not verified)\b", re.I)
MODIFIERS = (r"(?:(?:allegedly|reportedly|possibly|purportedly|did\s+not|didn['’]t|never|"
             r"(?:may|might|could|would)(?:\s+have)?|had|has|had\s+not|has\s+not|"
             r"planned\s+to|was\s+scheduled\s+to|is\s+scheduled\s+to)\s+)*")
DIRECT_PATTERNS = [
    ("Meeting", r"(?:met|meet|meets|held\s+(?:a\s+)?meeting)(?:\s+with)?|got\s+together\s+with|denied\s+meeting(?:\s+with)?"),
    ("Communication", r"(?:called|call|calls|phoned|phone|phones|telephoned|rang|texted|messaged|"
                      r"contacted|contact|spoke\s+by\s+phone\s+with|placed\s+a\s+call\s+to|"
                      r"made\s+a\s+call\s+to|sent\s+(?:a\s+)?(?:text|message)\s+to|denied\s+calling)"),
    ("Association", r"works?\s+for|worked\s+for|(?:is|was)\s+(?:listed\s+as\s+)?(?:an?\s+)?member\s+of|"
                    r"(?:is|was)\s+employed\s+by|joined|is\s+affiliated\s+with"),
]
DIRECT = [(kind, re.compile(r"^" + MODIFIERS + r"(?:" + pattern + r")(?:\s+the)?$", re.I))
          for kind, pattern in DIRECT_PATTERNS]
PASSIVE = re.compile(r"^(?:(?:was|were|had been|has been)\s+(?:not\s+)?(?:reportedly\s+)?"
                     r"(?:called|phoned|telephoned|contacted|texted|messaged)\s+by|"
                     r"(?:reportedly\s+|allegedly\s+)?received\s+(?:a\s+)?(?:phone\s+call|call|text|message)\s+from)$", re.I)
CALL_PREFIX = re.compile(r"\b(?:calls?|phone\s+calls?|conversation|message|text|communication)\s+from$", re.I)
MEETING_PREFIX = re.compile(r"\b(?:meeting|encounter|appointment)\s+between$", re.I)
CALL_BETWEEN = re.compile(r"\b(?:call|phone\s+call|conversation)\s+between$", re.I)

TITLED_TARGET = re.compile(r"\s+(?:mr|mrs|ms|dr|prof|detective|officer|inspector)\.?$", re.I)
EXPANDED_DIRECT = [
    ("Meeting", r"sat\s+down\s+with|spent\s+(?:the\s+)?(?:morning|afternoon|evening)\s+with|"
                r"met\s+in\s+person\s+with|had\s+an?\s+in[- ]person\s+meeting\s+with|"
                r"denied\s+(?:ever\s+)?meeting(?:\s+with)?"),
    ("Communication", r"left\s+(?:an?\s+)?(?:voicemail|message)\s+for|e[- ]?mailed|"
                      r"sent\s+(?:an?\s+)?(?:e[- ]?mail|voicemail|message|text)\s+to|"
                      r"placed\s+(?:the\s+)?call\s+to|"
                      r"(?:(?:explicitly|flatly)\s+)?denied\s+(?:calling|texting|"
                      r"exchanging\s+messages\s+with|speaking\s+(?:by\s+phone|on\s+the\s+radio)\s+with)"),
    ("Association", r"(?:is|was)\s+(?:also\s+)?on\s+(?:the\s+)?(?:staff|payroll)\s+(?:at|of)|"
                    r"(?:is|was)\s+(?:the\s+)?(?:treasurer|director|manager|employee|president|"
                    r"secretary|trustee|chair)\s+of|"
                    r"(?:(?:explicitly|flatly)\s+)?denied\s+(?:working\s+for|being\s+employed\s+by)"),
]
EXPANDED_DIRECT = [(kind, re.compile(r"^" + MODIFIERS + r"(?:" + pattern + r")(?:\s+the)?$", re.I))
                   for kind, pattern in EXPANDED_DIRECT]
VOICEMAIL_FROM = re.compile(r"\b(?:voicemail|email|e-mail|text message|letter|radio message)\s+from$", re.I)
MESSAGE_TO = re.compile(r"\b(?:message|email|e-mail|text|letter)\s+(?:(?:was|is)\s+)?(?:sent|addressed)\s+to$", re.I)
RECEIVED_CALL = re.compile(r"^(?:(?:reportedly|allegedly)\s+)?(?:took|answered|received)\s+(?:an?\s+)?"
                           r"(?:phone\s+call|call|voicemail|text|message|email)\s+from$", re.I)
JOINT_MEETING = re.compile(r"^\s*(?:(?:reportedly|allegedly|later|both)\s+)?(?:met\b|"
                           r"(?:held|hold)\s+(?:(?:an?|the)\s+)?(?:(?:private|brief|in-person)\s+)?meeting\b|"
                           r"sat\s+together\b|(?:sitting|sat)\s+across\s+from\s+each\s+other\b|"
                           r"compared\s+notes\s+in\s+person\b)", re.I)
EMPLOYER_PAYROLL = re.compile(r"^\s+on\s+(?:its|the)\s+payroll\b", re.I)
EMPLOYEE_ROLE = re.compile(r"^(?:,\s*)?(?:as\s+)?(?:an?\s+)?(?:dispatcher|driver|employee|"
                           r"staffer|stagehand|analyst|technician|clerk|accountant|operator|"
                           r"supervisor|coordinator|director|manager)\s+(?:for|with|at)\s*(?:the)?$", re.I)
STAFF_PREFIX = re.compile(r"\b(?:identifies|lists|names|records|describes|employs)\s*$", re.I)
DOCUMENT_ATTRIBUTION = re.compile(r"\baccording\s+to\s+(?:an?\s+|the\s+)?(?:recording|call log|"
                                  r"phone log|dispatch log|time sheet|payroll register|attendance log)\b", re.I)
EXPLICIT_CHANNEL = re.compile(r"^\s+(?:by\s+phone|by\s+(?:text|email)|on\s+(?:the\s+)?radio|"
                              r"via\s+(?:radio|email|text|phone))\b", re.I)


def expanded_relationship(prefix, between, suffix, left_type, right_type):
    """Match extra explicit constructions, with type and context gates."""
    between = TITLED_TARGET.sub("", between)
    base = relationship(prefix, between)
    if base:
        return base
    normalized = between.casefold()
    if left_type == "Organisation" and right_type == "Person":
        if normalized in {"has", "had", "listed", "lists"} and EMPLOYER_PAYROLL.search(suffix):
            return "Association", True
        if normalized == "employs":
            return "Association", True
    if left_type != "Person":
        return None
    if right_type == "Organisation":
        if EMPLOYEE_ROLE.fullmatch(between) and (STAFF_PREFIX.search(prefix) or between.startswith(",")):
            return "Association", False
    if right_type == "Person":
        if RECEIVED_CALL.fullmatch(between) or (normalized == "by" and MESSAGE_TO.search(prefix)):
            return "Communication", True
        if normalized == "to" and VOICEMAIL_FROM.search(prefix):
            return "Communication", False
        if normalized == "and" and JOINT_MEETING.search(suffix):
            return "Meeting", False
        if normalized == "reached" and EXPLICIT_CHANNEL.search(suffix):
            return "Communication", False
        if re.fullmatch(r"(?:sent|emailed|e-mailed|forwarded)", between, re.I) and re.match(
                r"^\s+(?:an?\s+|the\s+)?(?:(?:revised|updated|attached|requested)\s+)?"
                r"(?:email|e-mail|message|roster|schedule|document|attachment)\b", suffix, re.I):
            return "Communication", False
    for kind, pattern in EXPANDED_DIRECT:
        if pattern.fullmatch(between):
            return kind, False
    return None


def relationship(prefix, between):
    """Return relationship type and whether the right-hand mention initiates it."""
    if PASSIVE.fullmatch(between):
        return "Communication", True
    for kind, pattern in DIRECT:
        if pattern.fullmatch(between):
            return kind, False
    if between.casefold() == "to" and CALL_PREFIX.search(prefix):
        return "Communication", False
    if between.casefold() == "and":
        if MEETING_PREFIX.search(prefix):
            return "Meeting", False
        if CALL_BETWEEN.search(prefix):
            return "Communication", False
    return None


def refine_mentions(body, sentences, mentions, marker_pattern):
    """Use relation slots and explicit titles to repair plausible person-name spans."""
    spans = {}
    for entity in mentions:
        entity = entity.copy()
        if entity["type"] != "Person":
            stripped = DETERMINER.match(entity["name"])
            if stripped:
                entity["start"] += stripped.end()
                entity["name"] = body[entity["start"]:entity["end"]]
        name = entity["name"]
        if not entity["marker"] and ORG_SUFFIX.search(name):
            entity["type"] = "Organisation"
        elif not entity["marker"] and PLACE_SUFFIX.search(name):
            entity["type"] = "Location"
        spans[(entity["start"], entity["end"])] = entity

    for start, end in sentences:
        candidates = [match.span() for match in NAME.finditer(body, start, end)]
        people = set()
        for left, right in zip(candidates, candidates[1:]):
            prefix = body[start:left[0]].rstrip()
            between = marker_pattern.sub("", body[left[1]:right[0]]).strip()
            matched = relationship(prefix, between)
            if ALIAS_CUE.fullmatch(between):
                people.update((left, right))
            elif matched:
                people.add(left)
                if matched[0] != "Association":
                    people.add(right)
        for span in candidates:
            a, b = span
            name = body[a:b]
            if span not in people and not TITLE.search(body[max(start, a - 50):a]):
                continue
            if ORG_SUFFIX.search(name) or PLACE_SUFFIX.search(name):
                continue
            overlaps = [key for key in spans if a < key[1] and b > key[0]]
            if any(key != span for key in overlaps):
                continue
            marker = marker_pattern.match(body, b)
            spans[span] = dict(name=name, start=a, end=b, type="Person", marker=marker.group(1) if marker else None)
    # Propagate an explicitly evidenced person type to an otherwise ambiguous
    # occurrence of precisely the same name within this report.
    known_people = {entity["name"].casefold() for entity in spans.values() if entity["type"] == "Person"}
    for entity in spans.values():
        if entity["name"].casefold() in known_people:
            entity["type"] = "Person"
    return [spans[key] for key in sorted(spans)]


def claim_status(text, documented_attribution=False):
    if documented_attribution:
        text = DOCUMENT_ATTRIBUTION.sub("", text)
    if NEGATIVE.search(text):
        return "Denied"
    if HEDGE.search(text) or text.rstrip().endswith("?"):
        return "Unverified claim"
    return "Directly reported"

# Contextual rules are enabled separately so prior evaluation runs stay reproducible.
LISTED_MEMBER = re.compile(r"^as\s+(?:an?\s+)?member\s+of(?:\s+the)?$", re.I)
ADDRESSED_PACKET = re.compile(r"\b(?:packet|envelope|parcel)\s+(?:was|is)\s+addressed\s+to$", re.I)
TIME_TOGETHER = re.compile(r"^\s*(?:reportedly\s+|allegedly\s+)?spent\s+"
                           r"(?:(?:the|an?)\s+)?(?:morning|afternoon|evening|night|day|hour)\s+"
                           r"together\s+(?:at|in|inside)\s+", re.I)
REMOTE_CONTACT = re.compile(r"\b(?:online|virtual(?:ly)?|remotely|on (?:the|a) (?:phone|video call|conference call))\b", re.I)
KNOWN_NONPERSON = re.compile(
    r"\b(?:authority|club|company|court|firm|guild|junction|lock|mill|museum|network|pier|"
    r"plaza|railway|station|university|wharf|works|yard)$", re.I
)
NAME_WORD = r"[^\W\d_a-z](?:[^\W\d_]|[\u0300-\u036f])*(?:[’'-][^\W\d_]+)*"
KNOWN_NAMES = re.compile(rf"\b{NAME_WORD}(?:[ \t]+{NAME_WORD}){{1,3}}(?=\W|$)")
GIVEN_WORD = re.compile(r"\b[^\W\d_a-z][^\W\d_]*(?:[’'-][^\W\d_]+)*\b")
SURNAME_IDENTIFICATION = re.compile(
    r"\b(?P<short>[^\W\d_]+),?\s+(?:who\s+)?(?:is|was)\s+"
    r"(?:identified|recorded|listed)\s+(?:elsewhere\s+)?(?:in\s+(?:the|this)\s+"
    r"(?:file|report|register|record)\s+)?as$", re.I
)
HONORIFIC = re.compile(r"^(?:Mr|Mrs|Ms|Dr|Prof|Detective|Officer|Inspector)\s+")
NAME_STOPWORDS = {"A", "An", "At", "By", "From", "The", "In", "On", "And", "To"}


TIMED_CALL = re.compile(r"^(?:(?:reportedly|never|did not)\s+)?(?:later|subsequently|then)\s+(?:called|phoned|telephoned|call|phone)$", re.I)
OFFICER_ROLE = re.compile(r"^as (?:one of the officers|an officer) of(?: the)?$", re.I)
TOUR_OBSERVATION = re.compile(r"^\s+(?:for|during) (?:the |a |an )?(?:full |afternoon |morning )?tour\b", re.I)
QUALIFIED_JOINT_MEETING = re.compile(
    r"^\s+(?:may|might|could) (?:have met|meet)"
    r"(?=\s*(?:[.!?,]|$)|\s+(?:at|in|near|on|after|before|during|yesterday|today|last|later|that|with each other)\b)",
    re.I,
)
VOICEMAIL_RECIPIENT = re.compile(r"^" + MODIFIERS + r"left\s+(?:an?\s+)?voicemail\s+for$", re.I)
NONPERSON_RECIPIENT = re.compile(r"\b(?:agency|clinic|desk|helpdesk|hotline|office|reception|team|theatre)$", re.I)
SELF_REPORT = re.compile(r"^(?:says?|said|states?|stated)\s+(?:that\s+)?(?:he|she)\s+", re.I)


OFFICE = r"(?:treasurer|secretary|president|chair|director|trustee|officer|member)"
RECORDED_OFFICE = re.compile(
    rf"^(?:is|was) (?:not )?(?:listed|recorded|named) as (?:the |an? )?{OFFICE} of(?: the)?$", re.I)
MEMBERSHIP = re.compile(
    r"^(?:(?:has|had) (?:never|not) been|(?:is|was) (?:never|not)|"
    r"den(?:ies|ied) being) (?:an? )?member of(?: the)?$", re.I)
QUALIFIED_PAYROLL = re.compile(
    r"^(?:may|might|could) (?:be|have been) on (?:the |its )?payroll (?:of|at)(?: the)?$", re.I)
PAYROLL_HEADER = re.compile(r"\bpayroll (?:register|ledger|list|record) (?:at|of|for)(?: the)?$", re.I)
PAYROLL_ENTRY = re.compile(
    r"^\s+as (?:an? |the )?(?:driver|dispatcher|technician|clerk|operator|accountant|manager|employee)"
    r"\s*(?:[.!?]\s*)?$", re.I)
# Business descriptors support a type repair only inside an explicit affiliation.
BUSINESS_HEAD = re.compile(r"\b(?:press|books|publishers|cartography|hydraulics|staging|works|guild)$", re.I)


def contextual_affiliation(prefix, between, suffix):
    """Identify an explicit affiliation and return whether the employer appears first."""
    if (RECORDED_OFFICE.fullmatch(between) or MEMBERSHIP.fullmatch(between)
            or QUALIFIED_PAYROLL.fullmatch(between)):
        return "Association", False
    if STAFF_PREFIX.search(prefix) and (
            LISTED_MEMBER.fullmatch(between) or OFFICER_ROLE.fullmatch(between)
            or re.fullmatch(r"as an? employee of(?: the)?", between, re.I)):
        return "Association", False
    if (PAYROLL_HEADER.search(prefix) and between.casefold() in {"lists", "listed", "names", "named"}
            and PAYROLL_ENTRY.fullmatch(suffix)):
        return "Association", True
    return None


def contextual_relationship(prefix, between, suffix, left_type, right_type):
    """Recognize explicit affiliation, addressing and in-person joint activity."""
    base = expanded_relationship(prefix, between, suffix, left_type, right_type)
    if base:
        return base
    affiliation = contextual_affiliation(prefix, between, suffix)
    if affiliation:
        expected = ("Organisation", "Person") if affiliation[1] else ("Person", "Organisation")
        if (left_type, right_type) == expected:
            return affiliation
    if left_type != "Person":
        return None
    if right_type == "Person":
        if TIMED_CALL.fullmatch(between):
            return "Communication", False
        if (between.casefold() == "together with" and re.search(r"\b(?:saw|observed)$", prefix, re.I)
                and TOUR_OBSERVATION.match(suffix) and not REMOTE_CONTACT.search(suffix)):
            return "Meeting", False
        if between.casefold() == "by" and ADDRESSED_PACKET.search(prefix):
            return "Communication", True
        if between.casefold() == "and" and TIME_TOGETHER.search(suffix) and not REMOTE_CONTACT.search(suffix):
            return "Meeting", False
        if between.casefold() == "and" and QUALIFIED_JOINT_MEETING.match(suffix) and not REMOTE_CONTACT.search(suffix):
            return "Meeting", False
    return None


# A conjunction between names can belong to one meeting or a name list.
# Split plain "and" only when a new predicate or independent clause follows.
COORDINATOR = re.compile(r";\s*|,?\s+\b(?:and|but|whereas)\s+|,\s*(?:while|however)\s+", re.I)
CLAUSE_AUXILIARY = re.compile(r"^(?:did(?:n[’']t)?|does|has|had|was|were|is|are|never|may|might|could|would)\b", re.I)
BARE_ACTION = re.compile(r"^(?:call|phone|meet|contact|text|work|join|send|leave|receive)\b", re.I)


def claim_clauses(body, start, end, entities, marker_pattern):
    """Return sentence spans and the conjunction introducing each claim scope."""
    offsets = [e["start"] for e in entities]
    beginning, join = start, ""
    first = 0
    for match in COORDINATOR.finditer(body, start, end):
        word = match.group().strip().strip(",").strip().lower()
        index = bisect_left(offsets, match.end())
        if index and entities[index - 1]["end"] > match.start():
            continue
        if word == "and" and "," not in match.group():
            tail = body[match.end():end]
            following = entities[index:index + 2]
            new_clause = CLAUSE_AUXILIARY.match(tail)
            if following:
                obj = following[0]
                head = marker_pattern.sub("", body[match.end():obj["start"]]).strip()
                after = marker_pattern.sub("", body[obj["end"]:end])
                if (not head and index > first and obj["type"] == "Person"
                        and entities[index - 1]["type"] == "Person"
                        and QUALIFIED_JOINT_MEETING.match(after)):
                    # Keep the two names together unless the left name already
                    # belongs to a complete claim before the conjunction.
                    if index - first == 1:
                        continue
                    prior, left = entities[index - 2:index]
                    prefix = body[beginning:prior["start"]].rstrip()
                    between = marker_pattern.sub("", body[prior["end"]:left["start"]]).strip()
                    if not contextual_relationship(prefix, between, "", prior["type"], left["type"]):
                        continue
                if head:
                    new_clause = new_clause or contextual_relationship("", head, after, "Person", obj["type"])
                elif index - first >= 2 or join:
                    # A second named subject can deny an unrelated action that
                    # has no extractable object of its own.
                    new_clause = CLAUSE_AUXILIARY.match(after.lstrip())
                    if len(following) == 2 and not new_clause:
                        other = following[1]
                        predicate = marker_pattern.sub("", body[obj["end"]:other["start"]]).strip()
                        new_clause = contextual_relationship("", predicate, body[other["end"]:end],
                                                             obj["type"], other["type"])
            if not new_clause:
                continue
        yield beginning, match.start(), join
        beginning, first, join = match.end(), index, word
    yield beginning, end, join


def name_spans(body, start, end):
    for match in KNOWN_NAMES.finditer(body, start, end):
        title = HONORIFIC.match(match.group())
        left = match.start() + (title.end() if title else 0)
        parts = body[left:match.end()].split()
        if len(parts) >= 2 and all(word[0].isupper() and word not in NAME_STOPWORDS for word in parts):
            yield left, match.end()


def contextual_mentions(body, sentences, mentions, marker_pattern):
    """Repair explicit contact and employer slots and resolve local surname references."""
    spans = {(item["start"], item["end"]): item.copy() for item in mentions}
    short_references = {}
    for entity in spans.values():
        if (not entity["marker"] and entity["name"].endswith(" Guild")
                and re.search(r"\bmember of (?:the )?$", body[:entity["start"]], re.I)):
            entity["type"] = "Organisation"

    def nonperson(span):
        name = body[span[0]:span[1]]
        return ORG_SUFFIX.search(name) or PLACE_SUFFIX.search(name) or KNOWN_NONPERSON.search(name)

    def register_person(span, **attributes):
        start, end = span
        if nonperson(span):
            return
        overlaps = [candidate for candidate in spans if start < candidate[1] and end > candidate[0]]
        for candidate in overlaps:
            existing = spans[candidate]
            if candidate != span and (candidate[0] < start or candidate[1] > end or existing["marker"]):
                return
        for candidate in overlaps:
            spans.pop(candidate)
        marker = marker_pattern.match(body, end)
        spans[span] = dict(name=body[start:end], start=start, end=end, type="Person",
                           marker=marker.group(1) if marker else None, **attributes)

    for start, end in sentences:
        full_names = list(name_spans(body, start, end))
        for left, right in zip(full_names, full_names[1:]):
            prefix = body[start:left[0]].rstrip()
            between = marker_pattern.sub("", body[left[1]:right[0]]).strip()
            suffix = marker_pattern.sub("", body[right[1]:end])
            affiliation = contextual_affiliation(prefix, between, suffix)
            if not affiliation and (
                (STAFF_PREFIX.search(prefix) and EMPLOYEE_ROLE.fullmatch(between))
                or re.fullmatch(r"(?:is|was) employed by(?: the)?", between, re.I)
            ):
                affiliation = "Association", False
            if affiliation:
                person, employer = (right, left) if affiliation[1] else (left, right)
                org = spans.get(employer)
                employer_name = body[employer[0]:employer[1]]
                # Occupations can name individual employers too. Require separate
                # evidence of an organisation before correcting either endpoint.
                if (org and not org["marker"] and not nonperson(person)
                        and not BUSINESS_HEAD.search(body[person[0]:person[1]])
                        and (org["type"] == "Organisation" or ORG_SUFFIX.search(employer_name)
                             or BUSINESS_HEAD.search(employer_name))):
                    if spans.get(person, {}).get("type") != "Organisation" or marker_pattern.match(body, person[1]):
                        org["type"] = "Organisation"
                        register_person(person)
            two_contact_names = ((between.casefold() == "to" and VOICEMAIL_FROM.search(prefix))
                                 or PASSIVE.fullmatch(between) or RECEIVED_CALL.fullmatch(between)
                                 or TIMED_CALL.fullmatch(between))
            if VOICEMAIL_RECIPIENT.fullmatch(between):
                two_contact_names = not any(
                    NONPERSON_RECIPIENT.search(body[a:b]) or BUSINESS_HEAD.search(body[a:b])
                    for a, b in (left, right)
                )
            if two_contact_names and not any(nonperson(span) for span in (left, right)):
                register_person(left)
                register_person(right)
        for span in full_names:
            prefix = body[start:span[0]].rstrip()
            identification = SURNAME_IDENTIFICATION.search(prefix)
            surname = body[span[0]:span[1]].split()[-1]
            if identification and identification.group("short").casefold() == surname.casefold():
                register_person(span)
                short_span = (start + identification.start("short"), start + identification.end("short"))
                short_references[short_span] = span

    people_by_surname = {}
    for span, item in sorted(spans.items()):
        if item["type"] == "Person" and " " in item["name"]:
            surname = item["name"].rsplit(None, 1)[1].casefold()
            people_by_surname.setdefault(surname, []).append((span, item))
    for short_span, full_span in short_references.items():
        if spans.get(full_span, {}).get("type") == "Person":
            register_person(short_span, antecedent=full_span[0])

    for start, end in sentences:
        for match in GIVEN_WORD.finditer(body, start, end):
            short = match.group()
            span = match.span()
            if not short[0].isupper() or span in short_references:
                continue
            candidates = [(key, item) for key, item in people_by_surname.get(short.casefold(), ())
                          if key[1] < span[0]]
            if not candidates or any(a < span[1] and b > span[0] and (a, b) != span for a, b in spans):
                continue
            # Only infer a short name in a relationship slot with another known person.
            people = [key for key, item in spans.items()
                      if start <= key[0] < end and key != span and item["type"] == "Person"]
            for partner in people:
                left, right = sorted((span, partner))
                prefix = body[start:left[0]].rstrip()
                between = marker_pattern.sub("", body[left[1]:right[0]]).strip()
                suffix = marker_pattern.sub("", body[right[1]:end])
                matched = contextual_relationship(prefix, between, suffix, "Person", "Person")
                if matched and matched[0] != "Association":
                    break
            else:
                continue
            aliases = {}
            for candidate_span, item in candidates:
                label = item["marker"] or item["name"].casefold()
                aliases.setdefault(label, candidate_span[0])
            if len(aliases) == 1:
                register_person(span, antecedent=next(iter(aliases.values())))
            else:
                register_person(span, ambiguous_surname=True)
    return [spans[key] for key in sorted(spans)]
