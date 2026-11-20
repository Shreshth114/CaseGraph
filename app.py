"""Local Flask server for the investigation workspace."""
import argparse
from functools import lru_cache

from flask import Flask, jsonify, request

from analysis_engine import analyze, evaluate, montagna
from validation.check import custody_results, field_results
from benchmark import hand_written_reports
from case_chat import ask_case
from corpus import examples
from lead_finder import demo_answer, demo_case, lead_graph

app = Flask(__name__, static_url_path="/assets")
app.config["MAX_CONTENT_LENGTH"] = 1_500_000

@app.get("/")
def home():
    return app.send_static_file("index.html")

@app.get("/api/demo")
def demo():
    return jsonify(analyze(list(examples())))

@app.get("/api/benchmark")
def benchmark_demo():
    return jsonify(analyze(benchmark_input()))

def benchmark_input():
    return [dict(id=row["id"], text=row["text"]) for row in hand_written_reports()]

@app.get("/api/montagna")
def montagna_graph():
    return jsonify(montagna())

@app.get("/api/lead")
def lead_case():
    return jsonify(lead_graph(demo_case()))

@app.get("/api/lead/answer")
def reveal_lead_answer():
    return jsonify(demo_answer())

@app.get("/api/evaluation")
def evaluation():
    return jsonify(dict(evaluate(), release=release_evaluation()))


@lru_cache(maxsize=1)
def release_evaluation():
    return dict(field=field_results(), custody=custody_results())

@app.post("/api/analyze")
def analyze_reports():
    body = request.get_json(silent=True)
    items = body.get("reports") if isinstance(body, dict) else None
    return jsonify(analyze(normalize_reports(items)))

def normalize_reports(items):
    if not isinstance(items, list) or not 1 <= len(items) <= 50:
        raise ValueError("Provide between 1 and 50 text reports.")
    reports = []
    for index, item in enumerate(items, 1):
        content = item.get("text") if isinstance(item, dict) else None
        if not isinstance(content, str) or not 1 <= len(content.strip()) <= 20_000:
            raise ValueError(f"Report {index} needs 1–20,000 characters of text.")
        name = item.get("name")
        name = name[:120] if isinstance(name, str) and name.strip() else "Pasted report"
        reports.append(dict(id=f"R-{index:02d}", name=name, text=content.strip()))
    if sum(len(report["text"]) for report in reports) > 100_000:
        raise ValueError("The combined text must be at most 100,000 characters.")
    return reports

@app.post("/api/review")
def update_review():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ValueError("Provide a dataset and its review decisions.")
    version = body.get("version")
    if version is not None and not isinstance(version, str):
        raise ValueError("Invalid evidence version.")
    return jsonify(reviewed_case(body, body.get("decisions"), expected_version=version))


def reviewed_case(body, decisions, *, expected_version=None):
    dataset = body.get("dataset")
    if dataset == "montagna":
        return montagna(decisions, expected_version=expected_version)
    if dataset == "lead":
        return lead_graph(demo_case(), decisions, expected_version=expected_version)
    if dataset == "benchmark":
        reports = benchmark_input()
    elif dataset == "demo":
        reports = list(examples())
    elif dataset == "custom":
        reports = normalize_reports(body.get("reports"))
    else:
        raise ValueError("Choose a reviewable case.")
    return analyze(reports, decisions, expected_version=expected_version)


@app.post("/api/chat")
def case_chat():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ValueError("Provide a case and a question.")
    question = body.get("question")
    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 500:
        raise ValueError("Enter a question of up to 500 characters.")
    version = body.get("version")
    if not isinstance(version, str) or not isinstance(body.get("decisions"), list):
        raise ValueError("Open a case before asking a question.")
    edge, node = body.get("edge"), body.get("node")
    if any(value is not None and not isinstance(value, str) for value in (edge, node)):
        raise ValueError("Invalid evidence selection.")
    graph = reviewed_case(body, body["decisions"], expected_version=version)
    return jsonify(ask_case(question, graph, edge, node))


@app.post("/api/cases/open")
def open_case():
    saved = request.get_json(silent=True)
    if not isinstance(saved, dict) or saved.get("format") != "casegraph-1":
        raise ValueError("Choose a version 1 Casegraph case file.")
    if not isinstance(saved.get("version"), str):
        raise ValueError("The case is missing its evidence version.")
    if not isinstance(saved.get("decisions"), list):
        raise ValueError("The case is missing its review history.")
    graph = reviewed_case(saved, saved["decisions"], expected_version=saved["version"])
    if saved.get("reports") != graph["reports"]:
        raise ValueError("Source or extraction version changed. Saved decisions require a new review.")
    return jsonify(dataset=saved["dataset"], graph=graph)


@app.errorhandler(ValueError)
def invalid_input(error):
    return jsonify(error=str(error)), 400

@app.errorhandler(413)
def too_large(_error):
    return jsonify(error="The report batch exceeds the upload limit."), 413

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=5050)
    args = parser.parse_args()
    app.run(host="127.0.0.1", port=args.port)
