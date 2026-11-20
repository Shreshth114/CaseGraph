"""Hand-written ID-free reports and independently specified reference labels."""

P = "Person"
O = "Organisation"
L = "Location"
DIRECT = "Directly reported"
UNCERTAIN = "Unverified claim"
DENIED = "Denied"

# Each label gives the literal text, entity type, and reference identity.
# Relationship endpoints are indices into that report's ordered mention labels.
CASES = [
    ("Elena Morris met Theo Price near Brighton. The log records no other visitors.",
     [("Elena Morris", P, "elena-archivist"), ("Theo Price", P, "theo"), ("Brighton", L, "brighton")],
     [(0, 1, "Meeting", DIRECT)]),
    ("The witness stated that Theo Price reportedly called Elena Morris during the afternoon.",
     [("Theo Price", P, "theo"), ("Elena Morris", P, "elena-archivist")],
     [(0, 1, "Communication", UNCERTAIN)]),
    ("A payroll clerk named Elena Morris works for Delta Freight. The file describes her as distinct from the archivist of the same name.",
     [("Elena Morris", P, "elena-clerk"), ("Delta Freight", O, "delta")],
     [(0, 1, "Association", DIRECT)]),
    ("Dylan Hart, also known as Milo Hart, signed for the records. Milo Hart later phoned Leila Grant.",
     [("Dylan Hart", P, "dylan"), ("Milo Hart", P, "dylan"), ("Milo Hart", P, "dylan"), ("Leila Grant", P, "leila")],
     [(2, 3, "Communication", DIRECT)]),
    ("Milo Hart did not meet Leila Grant. The venue in Bristol was closed.",
     [("Milo Hart", P, "dylan"), ("Leila Grant", P, "leila"), ("Bristol", L, "bristol")],
     [(0, 1, "Meeting", DENIED)]),
    ("Ruth Quinn and Ruby Quinn appear on unrelated pages of the register. Neither page describes an interaction.",
     [("Ruth Quinn", P, "ruth"), ("Ruby Quinn", P, "ruby")], []),
    ("Ruby Quinn met Leila Grant at a public conference in Leeds.",
     [("Ruby Quinn", P, "ruby"), ("Leila Grant", P, "leila"), ("Leeds", L, "leeds")],
     [(0, 1, "Meeting", DIRECT)]),
    ("The call log lists a conversation from Owen Clarke to Priya Shah. The operator entered the call at noon.",
     [("Owen Clarke", P, "owen"), ("Priya Shah", P, "priya")],
     [(0, 1, "Communication", DIRECT)]),
    ("The witness claimed Priya Shah might have met Owen Clarke in Oxford.",
     [("Priya Shah", P, "priya"), ("Owen Clarke", P, "owen"), ("Oxford", L, "oxford")],
     [(0, 1, "Meeting", UNCERTAIN)]),
    ("Marcus Reed never called Beatrice Hall. Both names were listed on the cover sheet.",
     [("Marcus Reed", P, "marcus"), ("Beatrice Hall", P, "beatrice")],
     [(0, 1, "Communication", DENIED)]),
    ("Beatrice Hall is a member of the Royal Society. The letter was filed in London.",
     [("Beatrice Hall", P, "beatrice"), ("Royal Society", O, "royal"), ("London", L, "london")],
     [(0, 1, "Association", DIRECT)]),
    ("Owen Clarke visited Cambridge. An unrelated application from Ruth Quinn was filed the same day.",
     [("Owen Clarke", P, "owen"), ("Cambridge", L, "cambridge"), ("Ruth Quinn", P, "ruth")], []),
]

def hand_written_reports():
    for index, (text, labels, links) in enumerate(CASES, 1):
        mentions = []
        cursor = 0
        for name, kind, identity in labels:
            start = text.index(name, cursor)
            cursor = start + len(name)
            mentions.append(dict(start=start, end=cursor, type=kind, identity=identity))
        relationships = [dict(source=mentions[a]["start"], target=mentions[b]["start"], type=kind, status=status)
                         for a, b, kind, status in links]
        yield dict(id=f"HAND-{index:02d}", text=text, mentions=mentions, relationships=relationships)
