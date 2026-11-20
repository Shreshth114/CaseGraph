"""Hand-annotated fictional reports held out from extraction development.

Each mention specification gives its exact surface form, entity type, and
identity. Specifications follow text order, including repeated surface forms.
Relationship specifications refer to the numbered mentions in that order
(starting at zero), and the emitted fixtures use character offsets.
"""

_PERSON = "Person"
_ORG = "Organisation"
_PLACE = "Location"
_DIRECT = "Directly reported"
_CLAIM = "Unverified claim"
_DENIED = "Denied"

_REPORTS = (
    (
        "fresh-01",
        "The caretaker at Briar Quay recorded Imani Vale and Tobin Crewe arriving an hour apart. "
        "At noon, Vale sat down with Noor Saye in the canteen.",
        (
            ("Briar Quay", _PLACE, "briar-quay"),
            ("Imani Vale", _PERSON, "imani-vale"),
            ("Tobin Crewe", _PERSON, "tobin-crewe"),
            ("Vale", _PERSON, "imani-vale"),
            ("Noor Saye", _PERSON, "noor-saye"),
        ),
        ((3, 4, "Meeting", _DIRECT),),
    ),
    (
        "fresh-02",
        "A saved voicemail from Noor Saye to Tobin Crewe asks for a key to the storeroom at Moss Court. "
        "No reply from Crewe appears in the file.",
        (
            ("Noor Saye", _PERSON, "noor-saye"),
            ("Tobin Crewe", _PERSON, "tobin-crewe"),
            ("Moss Court", _PLACE, "moss-court"),
            ("Crewe", _PERSON, "tobin-crewe"),
        ),
        ((0, 1, "Communication", _DIRECT),),
    ),
    (
        "fresh-03",
        "The staff list identifies Ren Calder as a dispatcher for Fenlace Transit. "
        "Ellis Rook picked up a spare jacket bearing the Fenlace Transit crest at Sedge Gate.",
        (
            ("Ren Calder", _PERSON, "ren-calder"),
            ("Fenlace Transit", _ORG, "fenlace-transit"),
            ("Ellis Rook", _PERSON, "ellis-rook"),
            ("Fenlace Transit", _ORG, "fenlace-transit"),
            ("Sedge Gate", _PLACE, "sedge-gate"),
        ),
        ((0, 1, "Association", _DIRECT),),
    ),
    (
        "fresh-04",
        "An unsigned note alleges that Ellis Rook works for the North Sluice Trust. "
        "Rook denied working for the Trust when asked about the note.",
        (
            ("Ellis Rook", _PERSON, "ellis-rook"),
            ("North Sluice Trust", _ORG, "north-sluice-trust"),
            ("Rook", _PERSON, "ellis-rook"),
            ("Trust", _ORG, "north-sluice-trust"),
        ),
        ((0, 1, "Association", _CLAIM), (2, 3, "Association", _DENIED)),
    ),
    (
        "fresh-05",
        "The tipster claims Avery Lorne met Dr. Senan Quill behind Glass Ferry. "
        "Lorne explicitly denied meeting Quill that evening.",
        (
            ("Avery Lorne", _PERSON, "avery-lorne"),
            ("Senan Quill", _PERSON, "senan-quill"),
            ("Glass Ferry", _PLACE, "glass-ferry"),
            ("Lorne", _PERSON, "avery-lorne"),
            ("Quill", _PERSON, "senan-quill"),
        ),
        ((0, 1, "Meeting", _CLAIM), (3, 4, "Meeting", _DENIED)),
    ),
    (
        "fresh-06",
        "Mara Venn, who uses the name Kestrel at work, filed the report. "
        "The attached email shows that Kestrel sent Leif Torr the revised roster.",
        (
            ("Mara Venn", _PERSON, "mara-venn"),
            ("Kestrel", _PERSON, "mara-venn"),
            ("Kestrel", _PERSON, "mara-venn"),
            ("Leif Torr", _PERSON, "leif-torr"),
        ),
        ((2, 3, "Communication", _DIRECT),),
    ),
    (
        "fresh-07",
        "The log uses occupations to distinguish two people with identical names. "
        "Kit Sorel, a stagehand with the Merrow Lantern Company, arrived at Ashlock Pier first. "
        "Kit Sorel, a taxi driver, took a call from Zoya Dray later that night.",
        (
            ("Kit Sorel", _PERSON, "kit-sorel-stagehand"),
            ("Merrow Lantern Company", _ORG, "merrow-lantern-company"),
            ("Ashlock Pier", _PLACE, "ashlock-pier"),
            ("Kit Sorel", _PERSON, "kit-sorel-driver"),
            ("Zoya Dray", _PERSON, "zoya-dray"),
        ),
        ((0, 1, "Association", _DIRECT), (4, 3, "Communication", _DIRECT)),
    ),
    (
        "fresh-08",
        "At Alder Steps, Zoya Dray never met Leif Torr because the appointment was canceled. "
        "Dray passed the afternoon with Tansy Leen instead.",
        (
            ("Alder Steps", _PLACE, "alder-steps"),
            ("Zoya Dray", _PERSON, "zoya-dray"),
            ("Leif Torr", _PERSON, "leif-torr"),
            ("Dray", _PERSON, "zoya-dray"),
            ("Tansy Leen", _PERSON, "tansy-leen"),
        ),
        ((1, 2, "Meeting", _DENIED), (3, 4, "Meeting", _DIRECT)),
    ),
    (
        "fresh-09",
        "A receptionist said that Orla Fenn might have phoned Idris Mael the day before. "
        "Mael flatly denied calling Fenn during the same period.",
        (
            ("Orla Fenn", _PERSON, "orla-fenn"),
            ("Idris Mael", _PERSON, "idris-mael"),
            ("Mael", _PERSON, "idris-mael"),
            ("Fenn", _PERSON, "orla-fenn"),
        ),
        ((0, 1, "Communication", _CLAIM), (2, 3, "Communication", _DENIED)),
    ),
    (
        "fresh-10",
        "The Cinderbank Archive (CBA) has Oona Pell on its payroll. "
        "Pell and Niall Wren met at Bramble Lock while the CBA's office was closed.",
        (
            ("Cinderbank Archive", _ORG, "cinderbank-archive"),
            ("CBA", _ORG, "cinderbank-archive"),
            ("Oona Pell", _PERSON, "oona-pell"),
            ("Pell", _PERSON, "oona-pell"),
            ("Niall Wren", _PERSON, "niall-wren"),
            ("Bramble Lock", _PLACE, "bramble-lock"),
            ("CBA", _ORG, "cinderbank-archive"),
        ),
        ((2, 0, "Association", _DIRECT), (3, 4, "Meeting", _DIRECT)),
    ),
    (
        "fresh-11",
        "Two receipts place Idris Mael in Little Vacker and Elspeth Dorn in Marden Reach at 9 a.m. "
        "Each receipt lists Grayfin Freight as the carrier.",
        (
            ("Idris Mael", _PERSON, "idris-mael"),
            ("Little Vacker", _PLACE, "little-vacker"),
            ("Elspeth Dorn", _PERSON, "elspeth-dorn"),
            ("Marden Reach", _PLACE, "marden-reach"),
            ("Grayfin Freight", _ORG, "grayfin-freight"),
        ),
        (),
    ),
    (
        "fresh-12",
        "The message was addressed to Elspeth Dorn by Ivo March, with the words 'ask about Wych Pool' "
        "in the subject line. The copy displayed beside it mentions Oona Pell in a separate note.",
        (
            ("Elspeth Dorn", _PERSON, "elspeth-dorn"),
            ("Ivo March", _PERSON, "ivo-march"),
            ("Wych Pool", _PLACE, "wych-pool"),
            ("Oona Pell", _PERSON, "oona-pell"),
        ),
        ((1, 0, "Communication", _DIRECT),),
    ),
    (
        "fresh-13",
        "Yesterday the repair crew at Vesper Cut logged Niall Wren and Sia Holt sitting across from "
        "each other over lunch. An unnamed caller claimed Holt was also on staff at Mallow Signal Works.",
        (
            ("Vesper Cut", _PLACE, "vesper-cut"),
            ("Niall Wren", _PERSON, "niall-wren"),
            ("Sia Holt", _PERSON, "sia-holt"),
            ("Holt", _PERSON, "sia-holt"),
            ("Mallow Signal Works", _ORG, "mallow-signal-works"),
        ),
        ((1, 2, "Meeting", _DIRECT), (3, 4, "Association", _CLAIM)),
    ),
    (
        "fresh-14",
        "Jo Anik reached Sia Holt on the radio at dawn, according to a recording from Rookery Bend. "
        "Holt is the treasurer of the Hushwater Club.",
        (
            ("Jo Anik", _PERSON, "jo-anik"),
            ("Sia Holt", _PERSON, "sia-holt"),
            ("Rookery Bend", _PLACE, "rookery-bend"),
            ("Holt", _PERSON, "sia-holt"),
            ("Hushwater Club", _ORG, "hushwater-club"),
        ),
        ((0, 1, "Communication", _DIRECT), (3, 4, "Association", _DIRECT)),
    ),
    (
        "fresh-15",
        "Tansy Leen received Cato Ní Friel in the office at Larch Run. "
        "The next morning the dispatch log records a call that Ní Friel placed to Jo Anik.",
        (
            ("Tansy Leen", _PERSON, "tansy-leen"),
            ("Cato Ní Friel", _PERSON, "cato-ni-friel"),
            ("Larch Run", _PLACE, "larch-run"),
            ("Ní Friel", _PERSON, "cato-ni-friel"),
            ("Jo Anik", _PERSON, "jo-anik"),
        ),
        ((0, 1, "Meeting", _DIRECT), (3, 4, "Communication", _DIRECT)),
    ),
    (
        "fresh-16",
        "Saffron Crowe and Jory Dace were both named in the Wrenfall Cooperative newsletter. "
        "Crowe denied exchanging messages with Dace, whose name appears directly beneath hers.",
        (
            ("Saffron Crowe", _PERSON, "saffron-crowe"),
            ("Jory Dace", _PERSON, "jory-dace"),
            ("Wrenfall Cooperative", _ORG, "wrenfall-cooperative"),
            ("Crowe", _PERSON, "saffron-crowe"),
            ("Dace", _PERSON, "jory-dace"),
        ),
        ((3, 4, "Communication", _DENIED),),
    ),
    (
        "fresh-17",
        "On the workshop rota, Elin D'Orne goes by Linnie. "
        "Jory Dace and Linnie compared notes in person at Cedar Weir after closing.",
        (
            ("Elin D'Orne", _PERSON, "elin-dorne"),
            ("Linnie", _PERSON, "elin-dorne"),
            ("Jory Dace", _PERSON, "jory-dace"),
            ("Linnie", _PERSON, "elin-dorne"),
            ("Cedar Weir", _PLACE, "cedar-weir"),
        ),
        ((2, 3, "Meeting", _DIRECT),),
    ),
    (
        "fresh-18",
        "Someone who left no name claimed to have seen Marcel Flint and E.J. Thorne hold a private meeting inside "
        "Low Bell Depot. A separate log confirms that Thorne rang Marcel Flint before sunrise.",
        (
            ("Marcel Flint", _PERSON, "marcel-flint"),
            ("E.J. Thorne", _PERSON, "ej-thorne"),
            ("Low Bell Depot", _PLACE, "low-bell-depot"),
            ("Thorne", _PERSON, "ej-thorne"),
            ("Marcel Flint", _PERSON, "marcel-flint"),
        ),
        ((0, 1, "Meeting", _CLAIM), (3, 4, "Communication", _DIRECT)),
    ),
)


def fresh_reports():
    """Yield the original independently authored fixtures."""
    return annotated_reports(_REPORTS)


def annotated_reports(specifications):
    """Decode exact text spans and relation endpoints from ordered annotations."""
    for report_id, text, mention_specs, relationship_specs in specifications:
        mentions = []
        next_start = 0
        for surface, entity_type, identity in mention_specs:
            start = text.index(surface, next_start)
            end = start + len(surface)
            mentions.append(
                {"start": start, "end": end, "type": entity_type, "identity": identity}
            )
            next_start = end

        relationships = [
            {
                "source": mentions[source]["start"],
                "target": mentions[target]["start"],
                "type": relation_type,
                "status": status,
            }
            for source, target, relation_type, status in relationship_specs
        ]
        yield {
            "id": report_id,
            "text": text,
            "mentions": mentions,
            "relationships": relationships,
        }
