import unittest
from pathlib import Path

from app import app


class CaseChatTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def ask(self, dataset, graph, question, **extra):
        return self.client.post("/api/chat", json=dict(
            dataset=dataset, version=graph["source_version"], reports=graph["reports"],
            decisions=graph["decisions"], question=question, **extra
        ))

    def upload_demo(self):
        text = Path(__file__).resolve().parents[1].joinpath("demo-report.txt").read_text(encoding="utf-8")
        return self.client.post("/api/analyze", json={"reports": [
            {"name": "demo-report.txt", "text": text}
        ]}).get_json()

    def test_meeting_answer_cites_both_namesakes_with_original_status(self):
        graph = self.upload_demo()
        reply = self.ask("custom", graph, "Did Mira Sen meet Dev Rao?").get_json()
        self.assertIn("P101", reply["message"])
        self.assertIn("P103", reply["message"])
        self.assertEqual({source["status"] for source in reply["citations"]}, {"Directly reported", "Denied"})
        by_id = {edge["id"]: edge for edge in graph["edges"]}
        for source in reply["citations"]:
            self.assertEqual(source["quote"], by_id[source["edge"]]["sentence"])

    def test_case_chat_does_not_offer_rejected_connection(self):
        graph = self.upload_demo()
        edge = next(edge for edge in graph["edges"] if edge["status"] == "Unverified claim")
        graph["decisions"] = [{"target": edge["id"], "decision": "rejected"}]
        for question in ("Which claims are unverified?", "Which report supports this connection?"):
            reply = self.ask("custom", graph, question, edge=edge["id"]).get_json()
            self.assertEqual(reply["citations"], [])

    def test_lead_answer_uses_reviewed_identity(self):
        graph = self.client.get("/api/lead").get_json()
        question = "Who should I follow up with?"
        before = self.ask("lead", graph, question).get_json()
        self.assertIn("Insufficient evidence", before["message"])
        self.assertEqual(before["action"], "review")
        merge = next(item for item in graph["review"] if item.get("id"))
        graph["decisions"] = [{"target": merge["id"], "decision": "accepted"}]
        after = self.ask("lead", graph, question).get_json()
        self.assertIn("Dev Rao is the strongest follow-up lead", after["message"])
        self.assertEqual({source["report"] for source in after["citations"]}, {"LF-02", "LF-03"})

    def test_cites_raw_incident_passage_and_abstains_on_unknown(self):
        graph = self.client.get("/api/lead").get_json()
        incident = self.ask("lead", graph, "When was KIT-17 found missing?").get_json()
        self.assertIn("15:30", incident["citations"][0]["quote"])
        unknown = self.ask("lead", graph, "What color was Dev Rao wearing?").get_json()
        self.assertEqual(unknown["citations"], [])
        self.assertIn("couldn't find evidence", unknown["message"])

    def test_rejects_invalid_prompt_and_stale_version(self):
        graph = self.client.get("/api/lead").get_json()
        self.assertEqual(self.ask("lead", graph, "a" * 501).status_code, 400)
        graph["source_version"] = "outdated"
        self.assertEqual(self.ask("lead", graph, "Who last handled KIT-17?").status_code, 400)
