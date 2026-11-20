import unittest

from analysis_engine import PILOT_PATH, analyze, extract, relationship_key
from training.test_reports import final_test_reports


class LanguageRuleTests(unittest.TestCase):
    def claims(self, text):
        return extract({"id": "test", "text": text})[1]

    def test_call_log_uses_both_participants(self):
        text = "The call log records a conversation from Iris Palmer to Noel Archer."
        [claim] = self.claims(text)
        self.assertEqual((claim["source"], claim["target"], claim["type"], claim["status"]),
                         (text.index("Iris"), text.index("Noel"), "Communication", "Directly reported"))
        self.assertEqual(claim["sentence"], text)

    def test_passive_call_preserves_initiator(self):
        text = "Noel Archer reportedly received a call from Iris Palmer."
        [claim] = self.claims(text)
        self.assertEqual((claim["source"], claim["target"], claim["status"]),
                         (text.index("Iris"), text.index("Noel"), "Unverified claim"))

    def test_clauses_have_separate_claim_status(self):
        text = "Iris Palmer never called Noel Archer, but Iris Palmer met Noel Archer."
        self.assertEqual([(claim["type"], claim["status"]) for claim in self.claims(text)],
                         [("Communication", "Denied"), ("Meeting", "Directly reported")])

    def test_status_only_applies_to_the_matching_clause(self):
        cases = [
            ("Iris Palmer never called Noel Archer, and Dana Brooks called Evan Moss.", ["Denied", "Directly reported"]),
            ("Iris Palmer called Noel Archer and Dana Brooks never called Evan Moss.", ["Directly reported", "Denied"]),
            ("Iris Palmer met Noel Archer and did not attend the lecture.", ["Directly reported"]),
            ("Iris Palmer met Noel Archer and Dana Brooks did not attend.", ["Directly reported"]),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual([claim["status"] for claim in self.claims(text)], expected)

    def test_shared_subject_keeps_direction_scope_and_sentence_evidence(self):
        cases = [
            ("Iris Palmer met Noel Archer and called Dana Brooks.", "Iris", "Noel", "Directly reported", "Directly reported"),
            ("Iris Palmer was called by Noel Archer and met Dana Brooks.", "Noel", "Iris", "Directly reported", "Directly reported"),
            ("Iris Palmer did not meet Noel Archer and call Dana Brooks.", "Iris", "Noel", "Denied", "Denied"),
            ("Iris Palmer met Noel Archer but never called Dana Brooks.", "Iris", "Noel", "Directly reported", "Denied"),
            ("A witness said Iris Palmer met Noel Archer and called Dana Brooks.", "Iris", "Noel", "Unverified claim", "Unverified claim"),
        ]
        for text, first_source, first_target, status1, status2 in cases:
            with self.subTest(text=text):
                a, b = self.claims(text)
                self.assertEqual((a["source"], a["target"], a["status"]), (text.index(first_source), text.index(first_target), status1))
                self.assertEqual((b["source"], b["target"], b["status"]), (text.index("Iris"), text.index("Dana"), status2))
                self.assertEqual([a["sentence"], b["sentence"]], [text, text])

    def test_id_length_does_not_change_relationship_extraction(self):
        for first, second in [("P1", "P2"), ("P11", "P12"), ("P101", "P102"), ("P0001", "P98765")]:
            text = f"Iris Palmer [{first}] called Noel Archer [{second}]."
            with self.subTest(text=text):
                mentions, [claim], _ = extract({"id": "test", "text": text})
                self.assertEqual([(m["name"], m["marker"]) for m in mentions], [("Iris Palmer", first), ("Noel Archer", second)])
                self.assertEqual(claim["target"], text.index("Noel"))
                self.assertEqual(claim["sentence"], text)

    def test_unrelated_mentions_do_not_make_edges(self):
        self.assertEqual(self.claims("The index lists Iris Palmer and Noel Archer on unrelated pages."), [])

    def test_indirect_relationship_examples(self):
        cases = [
            ("A voicemail from Iris Palmer to Noel Archer was saved.", "Iris", "Noel", "Communication"),
            ("Iris Palmer and Noel Archer met after the briefing.", "Iris", "Noel", "Meeting"),
            ("The message was addressed to Noel Archer by Iris Palmer.", "Iris", "Noel", "Communication"),
            ("The payroll list identifies Iris Palmer as a dispatcher for Alder Transit.", "Iris", "Alder", "Association"),
        ]
        for text, source, target, kind in cases:
            with self.subTest(text=text):
                names = [("Iris Palmer", "Person"), ("Noel Archer", "Person"), ("Alder Transit", "Organisation")]
                labels = [dict(start=text.index(name), end=text.index(name) + len(name), type=label)
                          for name, label in names if name in text]
                [claim] = extract({"id": "test", "text": text}, reference_entities=labels)[1]
                self.assertEqual((claim["source"], claim["target"], claim["type"], claim["sentence"]),
                                 (text.index(source), text.index(target), kind, text))

    def test_document_attribution_preserves_other_uncertainty(self):
        text = "Iris Palmer may have called Noel Archer, according to the call log."
        [claim] = self.claims(text)
        self.assertEqual(claim["status"], "Unverified claim")

    @unittest.skipUnless(PILOT_PATH.is_dir(), "Fine-tuned checkpoint is not installed")
    def test_six_missed_claims_are_recovered_without_extra_claims(self):
        seen = []
        for report in final_test_reports():
            previous = extract(report, detector="pilot", contextual=False)[1]
            current = extract(report, detector="pilot")[1]
            key = report["id"]
            expected = {relationship_key(key, claim) for claim in report["relationships"]}
            original = {relationship_key(key, claim) for claim in previous}
            actual = {relationship_key(key, claim) for claim in current}
            self.assertEqual(actual, expected, msg=key)
            if expected - original:
                seen.append(key)
        self.assertEqual(len(seen), 6)

    def test_contextual_rules_skip_lookalikes(self):
        cases = [
            "The register lists Iris Palmer beside Alder Transit as the person who delivered the file.",
            "A packet addressed to Iris Palmer was found beside a note naming Noel Archer.",
            "Iris Palmer and Noel Archer spent the morning at Westmere Hall on separate floors.",
            "Iris Palmer and Noel Archer spent the morning together at a virtual conference.",
            "A voicemail from Alder Transit to Noel Archer was saved.",
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertEqual(self.claims(text), [])

    def test_ambiguous_surname_is_kept_for_review_without_merging(self):
        text = ("Iris Palmer [P101] and Fern Palmer [P102] appear on separate pages. "
                "Palmer denied calling Noel Archer [P103].")
        result = analyze([dict(id="R-01", text=text)])
        [claim] = result["edges"]
        self.assertEqual(claim["status"], "Denied")
        self.assertEqual(claim["source"], "R-01:unresolved:" + str(text.index("Palmer denied")))
        self.assertIn("Several people in the report share the surname Palmer",
                      {proposal["reason"] for proposal in result["review"]})

    def test_name_variant_with_reported_contact_is_proposed_not_merged(self):
        reports = [
            {"id": "A", "text": "Iris Palmer met Noel Archer."},
            {"id": "B", "text": "Iris Parmer called Noel Archer."},
        ]
        graph = analyze(reports)
        proposal = next(item for item in graph["review"] if "Similar names" in item["reason"])
        self.assertEqual(proposal["shared_contacts"], ["noel archer"])
        self.assertEqual({claim["report"] for claim in proposal["supporting_claims"]}, {"A", "B"})
        self.assertEqual(len({node["id"] for node in graph["nodes"] if node["label"].startswith("Iris")}), 2)


if __name__ == "__main__":
    unittest.main()
