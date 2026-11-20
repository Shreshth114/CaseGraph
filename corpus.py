"""Reproducible fictional reports with mention and assertion annotations."""
from string import Formatter

TEMPLATES = [
    ("{a} met with {b} near {place}. {org} supplied the venue schedule.", "Meeting", "Directly reported"),
    ("According to a witness, {a} reportedly called {b}. The witness was at {place}.", "Communication", "Unverified claim"),
    ("{a} is listed as a member of {org}. A separate entry names {b} and {place}.", "Association", "Directly reported"),
    ("{alias} called {b} from {place}. {org} was mentioned in a separate note.", "Communication", "Directly reported"),
    ("{a} did not meet {b} at {place}. {org} supplied a schedule.", "Meeting", "Denied"),
    ("The document lists {a} and {b}. The address field shows {place}.", None, None),
    ("At {place}, {b} phoned {a}. An earlier entry mentioned {org}.", "Communication", "Directly reported"),
    ("A witness alleged that {a} held a meeting with {b} at {place}.", "Meeting", "Unverified claim"),
    ("{b} never called {a}. Both were mentioned in a note about {org}.", "Communication", "Denied"),
    ("{a} works for {org}. The record also mentions {b} and {place}.", "Association", "Directly reported"),
    ("{alias} spoke by phone with {b} near {place}.", "Communication", "Directly reported"),
    ("The note lists {a} and {b} on different pages. It mentions {org} in an appendix.", None, None),
]
NAMES = [
    ("Mira Sen", "Meera Sen", "Mira S", "Marrow Bay", "Juniper Logistics"),
    ("Dev Rao", "Devan Rao", "D Rao", "Linden Port", "Cedar Transit"),
    ("Tara Malik", "Tara Malek", "T Malik", "Ashford Quay", "Birch Cooperative"),
    ("Leena Das", "Lina Das", "L Das", "Harbor Junction", "Willow Services"),
    ("Nalin Bose", "Nalin Basu", "N Bose", "Copper Point", "Alder Shipping"),
    ("Arun Kale", "Arun Kalia", "A Kale", "Silver Basin", "Rowan Foundation"),
]

def examples():
    for group, (a, b, alias, place, org) in enumerate(NAMES):
        start = 0 if group < 4 else 6
        for index in range(start, start + 6):
            template, relation, status = TEMPLATES[index]
            if index in (3, 10):
                template += " The file identifies {a}, also known as {alias}."
            identities = {"a": f"P{group}01", "alias": f"P{group}01", "b": f"P{group}02"}
            names = dict(a=a, b=b, alias=alias, place=place, org=org)
            types = dict(a="Person", b="Person", alias="Person", org="Organisation", place="Location")
            body, mentions = "", []
            for literal, field, _, _ in Formatter().parse(template):
                body += literal
                if field:
                    name = names[field]
                    mentions.append({"field": field, "start": len(body), "end": len(body) + len(name), "type": types[field]})
                    body += name + (f" [{identities[field]}]" if field in identities else "")
            endpoints = mentions[:2] if index != 6 else mentions[1:3]
            gold = [] if relation is None else [{
                "source": endpoints[0]["start"], "target": endpoints[1]["start"],
                "type": relation, "status": status,
            }]
            yield {"id": f"SYN-{group * 6 + index - start + 1:02d}", "text": body,
                   "split": "development" if group < 4 else "test",
                   "mentions": mentions, "relationships": gold}
