import unittest

from app import app
from analysis_engine import ROOT
from validation.check import custody_results


class ReleaseSmokeTests(unittest.TestCase):
    def test_three_custody_cases(self):
        cases = custody_results()
        self.assertEqual(len(cases), 3)
        for case in cases:
            with self.subTest(case=case["case"]):
                self.assertEqual(case["expected"], case["actual"])
                self.assertTrue(case["correct_reason"] and case["citations"])

    def test_demo_walkthrough(self):
        with app.test_client() as client:
            with client.get("/") as response:
                self.assertEqual(response.status_code, 200)
            sample = (ROOT / "demo-report.txt").read_text()
            result = client.post("/api/analyze", json={"reports": [{"text": sample}]}).get_json()
            self.assertEqual({e["status"] for e in result["edges"]}, {"Denied", "Directly reported", "Unverified claim"})
            rows = client.get("/api/montagna").get_json()["edges"]
            self.assertTrue(any(e["sentence"].startswith("Row 2 · N0, N1") for e in rows))
            evaluation = client.get("/api/evaluation")
            self.assertEqual(evaluation.status_code, 200)

    def test_case_round_trip_preserves_citations_and_rejects_stale_sources(self):
        with app.test_client() as client:
            reports = [{"name": "log", "text": "Pia Ford met Ira Moss."},
                       {"name": "log", "text": "Pia Ford called Ira Moss."}]
            base = client.post("/api/analyze", json={"reports": reports}).get_json()
            action = dict(target=base["edges"][0]["id"], decision="rejected",
                          at="2026-11-20T10:00:00Z", note="Reviewed transcript")
            saved = dict(format="casegraph-1", dataset="custom", reports=base["reports"],
                         version=base["source_version"], decisions=[action])
            graph = client.post("/api/cases/open", json=saved).get_json()["graph"]
            self.assertEqual(graph["decisions"], [action])
            self.assertEqual(graph["edges"][0]["decision"], "rejected")
            self.assertEqual(len({r["id"] for r in graph["reports"]}), 2)
            saved["reports"][0]["text"] += " Revised."
            self.assertEqual(client.post("/api/cases/open", json=saved).status_code, 400)

    def test_same_name_mentions_and_transitive_explicit_id_conflict(self):
        with app.test_client() as client:
            reports = [{"text": "Iris Palmer [P11] met Noel Archer. Iris Palmer called Noel Archer. Iris Palmer [P12] phoned Noel Archer."}]
            base = client.post("/api/analyze", json={"reports": reports}).get_json()
            iris = [n for n in base["nodes"] if n["label"] == "Iris Palmer"]
            self.assertEqual(len(iris), 3)
            pairs = [r for r in base["review"] if r.get("records") and
                     all(n["label"] == "Iris Palmer" for n in r["records"]) and
                     any(n["id"].startswith("R-01:") for n in r["records"])]
            actions = [dict(target=r["id"], decision="accepted") for r in pairs]
            self.assertEqual(len(actions), 2)
            result = client.post("/api/review", json=dict(dataset="custom", reports=reports, decisions=actions))
            self.assertEqual(result.status_code, 400)
            self.assertIn("explicit person IDs", result.get_json()["error"])
