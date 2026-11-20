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

    def test_uploaded_claims_preserve_status_scope_ids_and_graph_analytics(self):
        text = "Iris Palmer [P11] never called Noel Archer [P12], and Dana Brooks [P13] called Evan Moss [P14]."
        with app.test_client() as client:
            result = client.post("/api/analyze", json={"reports": [{"text": text}]}).get_json()
        self.assertEqual({n["id"]: n["degree"] for n in result["nodes"]},
                         {"P11": 0, "P12": 0, "P13": 1, "P14": 1})
        self.assertEqual([(e["source"], e["target"], e["status"]) for e in result["edges"]],
                         [("P11", "P12", "Denied"), ("P13", "P14", "Directly reported")])
        for edge in result["edges"]:
            self.assertEqual(edge["sentence"], text)
            self.assertEqual(edge["offset"], 0)
        self.assertEqual(result["edges"][1]["source_offset"], text.index("Dana"))
        self.assertEqual(result["edges"][1]["target_offset"], text.index("Evan"))

    def test_review_and_reopen_reuse_evidence_and_isolate_decisions(self):
        from unittest.mock import patch
        from analysis_engine import extract_network, prepared_text_evidence

        prepared_text_evidence.cache_clear()
        self.addCleanup(prepared_text_evidence.cache_clear)
        with app.test_client() as client, patch("analysis_engine.extract_network", wraps=extract_network) as extract:
            reports = [{"text": "Iris Palmer met Noel Archer and called Dana Brooks."}]
            graph = client.post("/api/analyze", json={"reports": reports}).get_json()
            self.assertEqual(len(graph["edges"]), 2)
            first, second = graph["edges"]
            self.assertEqual(first["source"], second["source"])
            action = dict(target=second["id"], decision="rejected")
            saved = dict(format="casegraph-1", dataset="custom", version=graph["source_version"],
                         reports=graph["reports"], decisions=[action])
            reviewed = client.post("/api/review", json=saved).get_json()
            self.assertEqual(reviewed["edges"][1]["decision"], "rejected")
            self.assertEqual(reviewed["source_version"], graph["source_version"])
            self.assertEqual(client.post("/api/cases/open", json=saved).get_json()["graph"], reviewed)
            untouched = client.post("/api/analyze", json={"reports": reports}).get_json()
            self.assertEqual(untouched, graph)
            self.assertEqual(extract.call_count, 1)

            prepared_text_evidence.cache_clear()
            reopened = client.post("/api/cases/open", json=saved).get_json()["graph"]
            self.assertEqual(reopened, reviewed)
            self.assertEqual(extract.call_count, 2)
            saved["reports"][0]["text"] += " Updated."
            stale = client.post("/api/review", json=saved)
            self.assertEqual(stale.status_code, 400)
            self.assertIn("version changed", stale.get_json()["error"])
