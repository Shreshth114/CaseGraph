"""Fictional relationship retest authored after freezing the contextual rules."""

from fresh_benchmark import annotated_reports

P = "Person"
O = "Organisation"
L = "Location"
DIRECT = "Directly reported"
UNCERTAIN = "Unverified claim"
DENIED = "Denied"

RETEST_CASES = (
    ("context-01", "One voicemail from Irena Polak to Yusef Calder was backed up before the phone was reset. The inquiry lists a branch at Bridgemere Lock.",
     (("Irena Polak", P, "irena"), ("Yusef Calder", P, "yusef"), ("Bridgemere Lock", L, "bridgemere")),
     ((0, 1, "Communication", DIRECT),)),
    ("context-02", "The index places Jonna Pell and Harun Dacre on separate pages. A recording about someone outside this file was never recovered.",
     (("Jonna Pell", P, "jonna"), ("Harun Dacre", P, "harun")), ()),
    ("context-03", "The hearing digest states that Yusef Calder was called by Nessa Drewe after the session at Woodcairn Court.",
     (("Yusef Calder", P, "yusef"), ("Nessa Drewe", P, "nessa"), ("Woodcairn Court", L, "woodcairn")),
     ((1, 0, "Communication", DIRECT),)),
    ("context-04", "The desk diary gives Clem Arden as the duty observer. Arden denied calling Jonna Pell that night.",
     (("Clem Arden", P, "clem"), ("Arden", P, "clem"), ("Jonna Pell", P, "jonna")),
     ((1, 2, "Communication", DENIED),)),
    ("context-05", "The file distinguishes Isla Morel, a medic, from Rafi Morel, a driver. A note headed Morel contains only a date.",
     (("Isla Morel", P, "isla"), ("Rafi Morel", P, "rafi"), ("Morel", P, "morel-unresolved")), ()),
    ("context-06", "The renewal list records Ned Barlow as a member of the Heatherfen Guild. The board posted the renewal on its noticeboard.",
     (("Ned Barlow", P, "ned"), ("Heatherfen Guild", O, "heatherfen")),
     ((0, 1, "Association", DIRECT),)),
    ("context-07", "A parcel was addressed to Anika Sen by Lyle Perrin. Beside it was an empty supply bag from Sandbrook Clinic.",
     (("Anika Sen", P, "anika"), ("Lyle Perrin", P, "lyle"), ("Sandbrook Clinic", O, "sandbrook")),
     ((1, 0, "Communication", DIRECT),)),
    ("context-08", "The concierge noted that Lyle Perrin and Mischa Orlov spent the evening together inside Merrow Hall. Neither signed the visitor book.",
     (("Lyle Perrin", P, "lyle"), ("Mischa Orlov", P, "mischa"), ("Merrow Hall", L, "merrow")),
     ((0, 1, "Meeting", DIRECT),)),
    ("context-09", "A label with Anika Sen's name lay beside a badge issued to Mischa Orlov. The report does not say either person was present.",
     (("Anika Sen", P, "anika"), ("Mischa Orlov", P, "mischa")), ()),
    ("context-10", "The witness claims Rafi Morel might have called Isla Morel, but Rafi Morel met Clem Arden in the yard.",
     (("Rafi Morel", P, "rafi"), ("Isla Morel", P, "isla"), ("Rafi Morel", P, "rafi"), ("Clem Arden", P, "clem")),
     ((0, 1, "Communication", UNCERTAIN), (2, 3, "Meeting", DIRECT))),
    ("context-11", "The listing describes Bronwen Hsu as one of the officers of Cresswell Council. The attachment identifies Ned Barlow as the person who filed the return.",
     (("Bronwen Hsu", P, "bronwen"), ("Cresswell Council", O, "cresswell"), ("Ned Barlow", P, "ned")),
     ((0, 1, "Association", DIRECT),)),
    ("context-12", "Bronwen Hsu answered a call from Halden Frost after the gates shut. The desk phone had just been reconnected.",
     (("Bronwen Hsu", P, "bronwen"), ("Halden Frost", P, "halden")),
     ((1, 0, "Communication", DIRECT),)),
    ("context-13", "The gallery attendant saw Nessa Drewe together with Jonna Pell for the full tour at Oxthorn House. The group then left separately.",
     (("Nessa Drewe", P, "nessa"), ("Jonna Pell", P, "jonna"), ("Oxthorn House", L, "oxthorn")),
     ((0, 1, "Meeting", DIRECT),)),
    ("context-14", "A caller alleged that a voicemail from Irena Polak to Vadim Cross was played in the office. The audio was never produced.",
     (("Irena Polak", P, "irena"), ("Vadim Cross", P, "vadim")),
     ((0, 1, "Communication", UNCERTAIN),)),
    ("context-15", "The operator returned Míra Duclos's call using the number for Sorin Neagu. A recording confirms that Sorin Neagu later phoned Míra Duclos.",
     (("Míra Duclos", P, "mira"), ("Sorin Neagu", P, "sorin"), ("Sorin Neagu", P, "sorin"), ("Míra Duclos", P, "mira")),
     ((2, 3, "Communication", DIRECT),)),
    ("context-16", "Vadim Cross never met Halden Frost, according to the attendance log at Ternwick Depot. Both were originally invited.",
     (("Vadim Cross", P, "vadim"), ("Halden Frost", P, "halden"), ("Ternwick Depot", L, "ternwick")),
     ((0, 1, "Meeting", DENIED),)),
    ("context-17", "Neve Kaur works for Ardent Fen Housing. After the inspection Neve Kaur sent a message to Harun Dacre.",
     (("Neve Kaur", P, "neve"), ("Ardent Fen Housing", O, "ardent-fen"), ("Neve Kaur", P, "neve"), ("Harun Dacre", P, "harun")),
     ((0, 1, "Association", DIRECT), (2, 3, "Communication", DIRECT))),
    ("context-18", "A desk log lists a conversation from Harun Dacre to Neve Kaur. It also records a failed attempt to reach a different office.",
     (("Harun Dacre", P, "harun"), ("Neve Kaur", P, "neve")),
     ((0, 1, "Communication", DIRECT),)),
)


def context_retest_reports():
    return annotated_reports(RETEST_CASES)
