import unittest

from app import app


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.reports = [
            {"text": "Theo Price met Leila Grant."},
            {"text": "Theo Price [P351] reportedly called Leila Grant [P352]."},
            {"text": "Theo Price met Ruth Quinn."},
        ]
        self.graph = self.client.post("/api/analyze", json={"reports": self.reports}).get_json()

    def update(self, *decisions):
        return self.client.post("/api/review", json={
            "dataset": "custom", "reports": self.reports,
            "decisions": [{"target": target, "decision": decision} for target, decision in decisions],
        })

    def test_rejected_link_keeps_evidence_but_leaves_analytics(self):
        edge = next(item for item in self.graph["edges"] if item["status"] == "Directly reported")
        reviewed = self.update((edge["id"], "rejected")).get_json()
        retained = next(item for item in reviewed["edges"] if item["id"] == edge["id"])
        self.assertEqual(retained["sentence"], edge["sentence"])
        self.assertEqual(retained["decision"], "rejected")
        self.assertFalse(next(node for node in reviewed["nodes"] if node["id"] == edge["source"])["degree"])

    def test_accepting_claim_preserves_uncertainty(self):
        edge = next(item for item in self.graph["edges"] if item["status"] == "Unverified claim")
        reviewed = self.update((edge["id"], "accepted")).get_json()
        retained = next(item for item in reviewed["edges"] if item["id"] == edge["id"])
        self.assertEqual(retained["status"], "Unverified claim")
        self.assertFalse(next(node for node in reviewed["nodes"] if node["id"] == edge["source"])["degree"])

    def test_merge_recomputes_graph_and_can_be_cleared(self):
        proposal = next(item for item in self.graph["review"] if "theo price" in item["reason"])
        key = proposal["id"]
        actions = [(key, "accepted")]
        reviewed = self.update(*actions).get_json()
        self.assertEqual(len(reviewed["nodes"]), len(self.graph["nodes"]) - 1)
        self.assertEqual([edge["sentence"] for edge in reviewed["edges"]],
                         [edge["sentence"] for edge in self.graph["edges"]])
        restored = self.update(*actions, (key, "cleared")).get_json()
        self.assertEqual(len(restored["nodes"]), len(self.graph["nodes"]))
        self.assertEqual([item["decision"] for item in restored["decisions"]], ["accepted", "cleared"])

    def test_rejected_identity_pair_blocks_transitive_merge(self):
        choices = [item for item in self.graph["review"] if "theo price" in item["reason"]]
        self.assertEqual(len(choices), 3)
        response = self.update((choices[0]["id"], "rejected"),
                               (choices[1]["id"], "accepted"), (choices[2]["id"], "accepted"))
        self.assertEqual(response.status_code, 400)
        self.assertIn("conflicts", response.get_json()["error"])


if __name__ == "__main__":
    unittest.main()
