import unittest

from app import app
from lead_finder import demo_case, independent_support, lead_graph
from itertools import permutations


class LeadFinderTests(unittest.TestCase):
    def setUp(self):
        self.case = demo_case()
        self.result = lead_graph(self.case)
        self.suggestion, = self.result["review"]
        self.merge = dict(target=self.suggestion["id"], decision="accepted")

    def add(self, report_id, origin, text):
        self.case["reports"].append(dict(id=report_id, name=report_id, origin=origin, text=text))

    def person(self, result, record):
        return next(card for card in result["lead"]["cards"] if card["id"] == record)

    def test_alias_review_changes_lead_and_preserves_original_evidence(self):
        self.assertIsNone(self.result["lead"]["strongest"])
        self.assertEqual(self.person(self.result, "P102")["count"], 1)
        self.assertEqual(self.person(self.result, "P104")["count"], 1)
        reviewed = lead_graph(self.case, [self.merge])
        self.assertEqual(reviewed["lead"]["strongest"], "P102")
        card = self.person(reviewed, "P102")
        self.assertEqual(card["names"], ["Dev Rao", "D. Rao"])
        self.assertEqual(card["latest"], "15:12")
        evidence = {edge["id"]: edge for edge in reviewed["edges"]}
        self.assertEqual([evidence[key]["report"] for key in card["support"]], ["LF-02", "LF-03"])
        self.assertIn("D. Rao [P104]", evidence[card["support"][1]]["sentence"])
        undone = lead_graph(self.case, [self.merge, dict(self.merge, decision="cleared")])
        self.assertIsNone(undone["lead"]["strongest"])
        self.assertEqual(self.person(undone, "P104")["count"], 1)

    def test_unverified_account_is_shown_with_conflicting_shift_record(self):
        card = self.person(self.result, "P101")
        self.assertEqual(card["count"], 0)
        evidence = {edge["id"]: edge for edge in self.result["edges"]}
        account, = card["other"]
        conflict, = card["conflicts"]
        self.assertEqual(evidence[account]["status"], "Unverified claim")
        self.assertEqual(evidence[conflict]["report"], "LF-05")

    def test_repeated_origin_and_copied_event_do_not_corroborate(self):
        self.add("COPY", "Different credit", "At 15:06, Dev Rao [P102] checked out KIT-17 at the media returns desk.")
        self.add("SAME", "Equipment register", "At 15:09, Dev Rao [P102] received KIT-17 at the media returns desk.")
        self.add("REPHRASED", "Paraphrased copy", "At 15:06, Dev Rao [P102] received KIT-17 at the media returns desk.")
        result = lead_graph(self.case)
        card = self.person(result, "P102")
        self.assertEqual((card["count"], len(card["other"])), (2, 2))
        self.assertIsNone(result["lead"]["strongest"])

    def test_matching_uses_alternate_origin_for_shared_event(self):
        rows = [dict(id=key, origin=origin, time=clock, item="KEY-1", location="desk")
                for key, origin, clock in [("a", "log", "09:06"), ("b", "receipt", "09:06"),
                                           ("c", "log", "09:09")]]
        for order in permutations(rows):
            self.assertEqual(independent_support(order), ["b", "c"])
        self.assertEqual(len(independent_support(rows[:2])), 1)

    def test_unparsed_custody_blocks_priority_and_keeps_source(self):
        self.add("NEW", "Clerk", "The clerk initialled the form for a later collection.")
        result = lead_graph(self.case, [self.merge])
        self.assertIsNone(result["lead"]["strongest"])
        self.assertEqual(result["passages"][-1]["outcome"], "needs review")
        self.assertEqual(result["passages"][-1]["report"], "NEW")

    def test_wrong_item_location_and_time_are_left_out_of_lead_scores(self):
        for key, text in [
            ("ITEM", "At 15:08, Dev Rao [P102] received KIT-18 at the media returns desk."),
            ("TIME", "At 16:08, Dev Rao [P102] received KIT-17 at the media returns desk."),
            ("PLACE", "At 15:08, Dev Rao [P102] received KIT-17 at the editing room."),
        ]:
            self.add(key, key, text)
        result = lead_graph(self.case)
        self.assertEqual(self.person(result, "P102")["count"], 1)
        self.assertIsNone(result["lead"]["strongest"])
        self.assertEqual(len(result["edges"]), len(self.result["edges"]) + 3)

    def test_tie_remains_unresolved(self):
        self.add("ALT1", "Another register", "At 15:08, Jana Cole [P109] checked out KIT-17 at the media returns desk.")
        self.add("ALT2", "Another witness", "At 15:11, Jana Cole [P109] received KIT-17 at the media returns desk.")
        result = lead_graph(self.case, [self.merge])
        self.assertIsNone(result["lead"]["strongest"])
        self.assertIn("equal independent support", result["lead"]["reason"])

    def test_same_or_later_custody_is_visible_as_a_competing_record(self):
        self.add("LATER", "Collection log", "At 15:14, Jana Cole [P109] received KIT-17 at the media returns desk.")
        result = lead_graph(self.case, [self.merge])
        self.assertIsNone(result["lead"]["strongest"])
        self.assertIn("same time or later", result["lead"]["reason"])

    def test_handover_counts_for_recipient_and_keeps_sender_evidence(self):
        self.add("TRANSFER", "Equipment steward",
                 "At 15:11, Jana Cole [P109] handed over KIT-17 to D. Rao [P104] at the media returns desk.")
        result = lead_graph(self.case)
        self.assertEqual(self.person(result, "P104")["count"], 2)
        self.assertEqual(next(e for e in result["edges"] if e["id"] == "TRANSFER:1:Sender")["source"], "P109")
        self.assertIsNone(result["lead"]["strongest"])

    def test_rejected_edge_no_longer_counts_and_source_stays_visible(self):
        rejected = dict(target="LF-03:1:Holder", decision="rejected")
        result = lead_graph(self.case, [self.merge, rejected])
        self.assertEqual(self.person(result, "P102")["count"], 1)
        self.assertIsNone(result["lead"]["strongest"])
        self.assertTrue(any(e["id"] == rejected["target"] and e["decision"] == "rejected" for e in result["edges"]))

    def test_api_answer_is_separate_from_case_and_review(self):
        with app.test_client() as client:
            result = client.get("/api/lead").get_json()
            self.assertNotIn("explanation", result)
            self.assertNotIn("answer", result["case"])
            payload = dict(dataset="lead", decisions=[self.merge])
            reviewed = client.post("/api/review", json=payload).get_json()
            self.assertEqual(reviewed["lead"]["strongest"], "P102")
            self.assertEqual(client.get("/api/lead/answer").get_json()["person"], "Dev Rao")


if __name__ == "__main__":
    unittest.main()
