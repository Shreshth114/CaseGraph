"""Fictional final test annotations, excluded from training and checkpoint selection."""

from fresh_benchmark import annotated_reports

P = "Person"
O = "Organisation"
L = "Location"
DIRECT = "Directly reported"
UNCERTAIN = "Unverified claim"
DENIED = "Denied"

TEST_CASES = (
    ("test-01", "The recording gives the sender as Nerissa Holt. A voicemail from Nerissa Holt to Soren Mead then asks about a missed delivery at Whitcombe Lock.",
     (("Nerissa Holt", P, "nerissa"), ("Nerissa Holt", P, "nerissa"), ("Soren Mead", P, "soren"), ("Whitcombe Lock", L, "whitcombe-lock")),
     ((1, 2, "Communication", DIRECT),)),
    ("test-02", "A handwritten margin note names Mead, who is identified elsewhere in the file as Soren Mead. Mead denied calling Mei Larkin.",
     (("Mead", P, "soren"), ("Soren Mead", P, "soren"), ("Mead", P, "soren"), ("Mei Larkin", P, "mei")),
     ((2, 3, "Communication", DENIED),)),
    ("test-03", "The annual return lists Mei Larkin as a member of the Firthstone Guild. A separate entry mentions a room booking at Eldwick Yard.",
     (("Mei Larkin", P, "mei"), ("Firthstone Guild", O, "firthstone-guild"), ("Eldwick Yard", L, "eldwick-yard")),
     ((0, 1, "Association", DIRECT),)),
    ("test-04", "An unnamed source claims Torin Akande and Kira Voss held a private meeting at Bellsford Green. The file gives no time.",
     (("Torin Akande", P, "torin"), ("Kira Voss", P, "kira"), ("Bellsford Green", L, "bellsford-green")),
     ((0, 1, "Meeting", UNCERTAIN),)),
    ("test-05", "Kira Voss works for Emberline Design. A contributor listed as Kira Voss on the parish roll is a different person.",
     (("Kira Voss", P, "kira"), ("Emberline Design", O, "emberline-design"), ("Kira Voss", P, "kira-roll")),
     ((0, 1, "Association", DIRECT),)),
    ("test-06", "Torin Akande and Dimitra Rossi met in Sedgewick after the site walk. The notes were copied to Baytree Utilities.",
     (("Torin Akande", P, "torin"), ("Dimitra Rossi", P, "dimitra"), ("Sedgewick", L, "sedgewick"), ("Baytree Utilities", O, "baytree-utilities")),
     ((0, 1, "Meeting", DIRECT),)),
    ("test-07", "A packet was addressed to Hassan Vale by Edith Carron. The courier deposited it in a locker at Northwill.",
     (("Hassan Vale", P, "hassan"), ("Edith Carron", P, "edith"), ("Northwill", L, "northwill")),
     ((1, 0, "Communication", DIRECT),)),
    ("test-08", "The Harbourmere Authority index names Hassan Vale and Pablo Treviño on separate pages. The entries concern different incidents.",
     (("Harbourmere Authority", O, "harbourmere-authority"), ("Hassan Vale", P, "hassan"), ("Pablo Treviño", P, "pablo")), ()),
    ("test-09", "Pablo Treviño was called by Edith Carron after the public hearing. Carron logged the call from Upton Cut.",
     (("Pablo Treviño", P, "pablo"), ("Edith Carron", P, "edith"), ("Carron", P, "edith"), ("Upton Cut", L, "upton-cut")),
     ((1, 0, "Communication", DIRECT),)),
    ("test-10", "An aide alleges that Anwen Brodie works for Clovehurst Partners. Anwen Brodie denied working for Clovehurst Partners when asked.",
     (("Anwen Brodie", P, "anwen"), ("Clovehurst Partners", O, "clovehurst-partners"),
      ("Anwen Brodie", P, "anwen"), ("Clovehurst Partners", O, "clovehurst-partners")),
     ((0, 1, "Association", UNCERTAIN), (2, 3, "Association", DENIED))),
    ("test-11", "The dispatch entry calls the operator Boon and gives the full name Boon Narang on the next line. Boon Narang reached Agata Lin on the radio.",
     (("Boon", P, "boon"), ("Boon Narang", P, "boon"), ("Boon Narang", P, "boon"), ("Agata Lin", P, "agata")),
     ((2, 3, "Communication", DIRECT),)),
    ("test-12", "Agata Lin arrived at Kettlebar Pier at noon. The notes give a departure time for Anwen Brodie on the previous day, with no shared event.",
     (("Agata Lin", P, "agata"), ("Kettlebar Pier", L, "kettlebar-pier"), ("Anwen Brodie", P, "anwen")), ()),
    ("test-13", "Danil Speer, otherwise known as Daz, checked the rota. Daz got together with Saira Khatri at Hemfold Square after work.",
     (("Danil Speer", P, "danil"), ("Daz", P, "danil"), ("Daz", P, "danil"), ("Saira Khatri", P, "saira"),
      ("Hemfold Square", L, "hemfold-square")),
     ((2, 3, "Meeting", DIRECT),)),
    ("test-14", "Saira Khatri never met Luc Tremayne at the depot. Both names appear on the Alderhaven Foundation invitation sheet.",
     (("Saira Khatri", P, "saira"), ("Luc Tremayne", P, "luc"), ("Alderhaven Foundation", O, "alderhaven-foundation")),
     ((0, 1, "Meeting", DENIED),)),
    ("test-15", "The staff register names Luc Tremayne as an operator for Whitecrest Ferries. Danil Speer signed for fuel at Orwick Bay.",
     (("Luc Tremayne", P, "luc"), ("Whitecrest Ferries", O, "whitecrest-ferries"), ("Danil Speer", P, "danil"), ("Orwick Bay", L, "orwick-bay")),
     ((0, 1, "Association", DIRECT),)),
    ("test-16", "The witness claimed Saira Khatri might have texted Danil Speer. Nothing confirms who used the handset.",
     (("Saira Khatri", P, "saira"), ("Danil Speer", P, "danil")),
     ((0, 1, "Communication", UNCERTAIN),)),
    ("test-17", "From the sign-in book, the reviewer concluded that Moira Iqbal and Zaid Nevin spent the morning together at Lanton Mill.",
     (("Moira Iqbal", P, "moira"), ("Zaid Nevin", P, "zaid"), ("Lanton Mill", L, "lanton-mill")),
     ((0, 1, "Meeting", DIRECT),)),
    ("test-18", "Zaid Nevin phoned Moira Iqbal, according to the dispatch log. The caller used a line assigned to Halewater Institute.",
     (("Zaid Nevin", P, "zaid"), ("Moira Iqbal", P, "moira"), ("Halewater Institute", O, "halewater-institute")),
     ((0, 1, "Communication", DIRECT),)),
)


def final_test_reports():
    return annotated_reports(TEST_CASES)
