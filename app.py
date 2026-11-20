"""Local Flask server for the investigation workspace."""
import argparse

from flask import Flask, jsonify, request

from analysis_engine import analyze, evaluate, montagna
from benchmark import hand_written_reports
from corpus import examples

app = Flask(__name__, static_url_path="/assets")
app.config["MAX_CONTENT_LENGTH"] = 450_000

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

@app.get("/api/evaluation")
def evaluation():
    return jsonify(evaluate())

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
    dataset, decisions = body.get("dataset"), body.get("decisions")
    if dataset == "montagna":
        return jsonify(montagna(decisions))
    if dataset == "benchmark":
        reports = benchmark_input()
    elif dataset == "demo":
        reports = list(examples())
    elif dataset == "custom":
        reports = normalize_reports(body.get("reports"))
    else:
        raise ValueError("Choose a reviewable case.")
    return jsonify(analyze(reports, decisions))

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
