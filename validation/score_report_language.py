"""Score the frozen fictional report-language test. Run with python -m validation.score_report_language."""
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

from analysis_engine import LABELS, extract, metrics, model, relationship_key

DATA = Path(__file__).with_name("report_language_test.json")
DIGEST = "3717d81ebae794cd19dc9f0187e522b2f77926e17882521b2b4d596610d8a7e7"


def load_reports():
    raw = DATA.read_bytes()
    if sha256(raw).hexdigest() != DIGEST:
        raise ValueError("The test file differs from the frozen labels.")
    return json.loads(raw)


def by_label(gold, predicted, index):
    return {label: metrics({r for r in gold if r[index] == label},
                           {r for r in predicted if r[index] == label})
            for label in sorted({r[index] for r in gold | predicted})}


def score(rows, detector):
    pipeline, model_name = model(detector)
    if not pipeline or not pipeline.has_pipe("ner"):
        raise ValueError(f"Install the requested NER checkpoint for {detector}.")
    gold_entities, raw_entities, app_entities = set(), set(), set()
    gold_links, app_links, oracle_links = set(), set(), set()
    for row in rows:
        rid, text = row["id"], row["text"]
        doc = pipeline(text)
        raw_entities.update((rid, ent.start_char, ent.end_char, LABELS[ent.label_])
                            for ent in doc.ents if ent.label_ in LABELS)
        for mention in row["mentions"]:
            assert text[mention["start"]:mention["end"]] == mention["name"]
            gold_entities.add((rid, mention["start"], mention["end"], mention["type"]))
        sample = dict(id=rid, text=text)
        mentions, claims, _ = extract(sample, detector=detector)
        app_entities.update((rid, m["start"], m["end"], m["type"]) for m in mentions)
        gold_links.update(relationship_key(rid, c) for c in row["relationships"])
        app_links.update(relationship_key(rid, c) for c in claims)
        # Diagnostic pass only. Supply the reference entity spans to isolate rule coverage.
        _, oracle_claims, _ = extract(sample, detector=detector, reference_entities=row["mentions"])
        oracle_links.update(relationship_key(rid, c) for c in oracle_claims)
    positives = {r[0] for r in gold_links}
    negatives = {r["id"] for r in rows} - positives
    rows_by_id = {r["id"]: r for r in rows}

    def describe(link):
        rid, a, b, kind, status = link
        names = {m["start"]: m["name"] for m in rows_by_id[rid]["mentions"]}
        return dict(report=rid, source_offset=a, source=names.get(a), target_offset=b, target=names.get(b),
                    type=kind, status=status)

    return dict(model=model_name, raw_ner=metrics(gold_entities, raw_entities),
                raw_ner_by_type=by_label(gold_entities, raw_entities, 3),
                app_ner=metrics(gold_entities, app_entities), app_ner_by_type=by_label(gold_entities, app_entities, 3),
                relationships=metrics(gold_links, app_links), relationships_by_type=by_label(gold_links, app_links, 3),
                relationships_by_status=by_label(gold_links, app_links, 4),
                with_reference_mentions=metrics(gold_links, oracle_links),
                recovered_with_reference_mentions=len((gold_links - app_links) & oracle_links),
                negative_reports=len(negatives), negative_reports_with_predictions=len(negatives & {r[0] for r in app_links}),
                missed=[describe(k) for k in sorted(gold_links - app_links)],
                extra=[describe(k) for k in sorted(app_links - gold_links)])


if __name__ == "__main__":
    rows = load_reports()
    print(json.dumps(dict(sha256=DIGEST, cases=dict(Counter(r["case"] for r in rows)),
                          pretrained=score(rows, "pretrained"), fine_tuned=score(rows, "pilot")),
                     ensure_ascii=False, indent=2))
