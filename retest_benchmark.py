"""Fictional retest reports written after the relationship rules were frozen."""

from fresh_benchmark import annotated_reports

_PERSON = "Person"
_ORG = "Organisation"
_PLACE = "Location"
_DIRECT = "Directly reported"
_CLAIM = "Unverified claim"
_DENIED = "Denied"

_REPORTS = (
    ("retest-01", "After the last bus, a voicemail from Bina Alder to Lucan Pitt requested a callback. The record gives no location.",
     (("Bina Alder", _PERSON, "bina"), ("Lucan Pitt", _PERSON, "lucan")),
     ((0, 1, "Communication", _DIRECT),)),
    ("retest-02", "The ferry crew recorded Sadie Niven and Euan Webb arriving separately at Alder Wharf. There was no record of them seeing each other.",
     (("Sadie Niven", _PERSON, "sadie"), ("Euan Webb", _PERSON, "euan"), ("Alder Wharf", _PLACE, "alder-wharf")), ()),
    ("retest-03", "The amended schedule identifies Devika Mall as a dispatcher for Bracken Transit. The entry for Celia Wynn is still blank.",
     (("Devika Mall", _PERSON, "devika"), ("Bracken Transit", _ORG, "bracken-transit"), ("Celia Wynn", _PERSON, "celia")),
     ((0, 1, "Association", _DIRECT),)),
    ("retest-04", "Celia Wynn received a phone call from Sadie Niven shortly after the inspection at Rill Point.",
     (("Celia Wynn", _PERSON, "celia"), ("Sadie Niven", _PERSON, "sadie"), ("Rill Point", _PLACE, "rill-point")),
     ((1, 0, "Communication", _DIRECT),)),
    ("retest-05", "The observer claims Lucan Pitt and Rowan Keel held a private meeting after closing. No other observer supplied a statement.",
     (("Lucan Pitt", _PERSON, "lucan"), ("Rowan Keel", _PERSON, "rowan")),
     ((0, 1, "Meeting", _CLAIM),)),
    ("retest-06", "Rowan Keel flatly denied exchanging messages with Bina Alder during the week of the festival.",
     (("Rowan Keel", _PERSON, "rowan"), ("Bina Alder", _PERSON, "bina")),
     ((0, 1, "Communication", _DENIED),)),
    ("retest-07", "Ivo Shaw works for Millpond Services. The Ivo Shaw named in the hall register is a different person.",
     (("Ivo Shaw", _PERSON, "ivo-employee"), ("Millpond Services", _ORG, "millpond-services"), ("Ivo Shaw", _PERSON, "ivo-visitor")),
     ((0, 1, "Association", _DIRECT),)),
    ("retest-08", "A lookout said Renna Cole might have phoned Euan Webb before lunch, but Euan Webb met Sadie Niven later that day.",
     (("Renna Cole", _PERSON, "renna"), ("Euan Webb", _PERSON, "euan"), ("Euan Webb", _PERSON, "euan"), ("Sadie Niven", _PERSON, "sadie")),
     ((0, 1, "Communication", _CLAIM), (2, 3, "Meeting", _DIRECT))),
    ("retest-09", "Nia Vale, who signs as Nix on the internal rota, was on duty. Nix returned a missed call to Tilda Baird that evening.",
     (("Nia Vale", _PERSON, "nia"), ("Nix", _PERSON, "nia"), ("Nix", _PERSON, "nia"), ("Tilda Baird", _PERSON, "tilda")),
     ((2, 3, "Communication", _DIRECT),)),
    ("retest-10", "Tilda Baird spoke by phone with Gareth Penn according to the dispatch log. The file gives no reason for the call.",
     (("Tilda Baird", _PERSON, "tilda"), ("Gareth Penn", _PERSON, "gareth")),
     ((0, 1, "Communication", _DIRECT),)),
    ("retest-11", "The envelope attached to the file was addressed to Elara Voss by Henri Sorel. A separate note names Nia Vale as the courier.",
     (("Elara Voss", _PERSON, "elara"), ("Henri Sorel", _PERSON, "henri"), ("Nia Vale", _PERSON, "nia")),
     ((1, 0, "Communication", _DIRECT),)),
    ("retest-12", "From the signatures on the minutes, the reviewer concluded that Gareth Penn and Elara Voss were together for the afternoon session at Birch Lock.",
     (("Gareth Penn", _PERSON, "gareth"), ("Elara Voss", _PERSON, "elara"), ("Birch Lock", _PLACE, "birch-lock")),
     ((0, 1, "Meeting", _DIRECT),)),
    ("retest-13", "Henri Sorel never met Gareth Penn. Both were listed as invitees to the same workshop in Newford.",
     (("Henri Sorel", _PERSON, "henri"), ("Gareth Penn", _PERSON, "gareth"), ("Newford", _PLACE, "newford")),
     ((0, 1, "Meeting", _DENIED),)),
    ("retest-14", "An anonymous email lists Toma Quill as being on the payroll of Blackfen Cooperative. The treasurer said the claim was unverified.",
     (("Toma Quill", _PERSON, "toma"), ("Blackfen Cooperative", _ORG, "blackfen-cooperative")),
     ((0, 1, "Association", _CLAIM),)),
    ("retest-15", "Pia Kell was shown a printout bearing the names Toma Quill and Lina Crane. No message or call records were attached.",
     (("Pia Kell", _PERSON, "pia"), ("Toma Quill", _PERSON, "toma"), ("Lina Crane", _PERSON, "lina")), ()),
    ("retest-16", "On the recorded channel, Lina Crane reached Pia Kell on the radio. A minute later Pia Kell phoned Toma Quill.",
     (("Lina Crane", _PERSON, "lina"), ("Pia Kell", _PERSON, "pia"), ("Pia Kell", _PERSON, "pia"), ("Toma Quill", _PERSON, "toma")),
     ((0, 1, "Communication", _DIRECT), (2, 3, "Communication", _DIRECT))),
    ("retest-17", "Mira Denby, the treasurer of Hailcross Society, checked the attendance sheet. Denby later sat down with Darian Moss at Stillwater Pier.",
     (("Mira Denby", _PERSON, "mira"), ("Hailcross Society", _ORG, "hailcross-society"), ("Denby", _PERSON, "mira"),
      ("Darian Moss", _PERSON, "darian"), ("Stillwater Pier", _PLACE, "stillwater-pier")),
     ((0, 1, "Association", _DIRECT), (2, 3, "Meeting", _DIRECT))),
    ("retest-18", "Darian Moss said he had not heard from Mira Denby that month. Nothing in the note describes a meeting.",
     (("Darian Moss", _PERSON, "darian"), ("Mira Denby", _PERSON, "mira")),
     ((1, 0, "Communication", _DENIED),)),
)


def retest_reports():
    return annotated_reports(_REPORTS)
