"""Choose the default detector using exact-span NER F1 on development cases."""

import json
from pathlib import Path

from analysis_engine import LABELS, SELECTION_PATH, score_reports

DATA = Path(__file__).with_name("data")


def main():
    reports = []
    for line in (DATA / "dev.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        mentions = [dict(start=start, end=end, type=LABELS[label])
                    for start, end, label in row["entities"]]
        reports.append(dict(id=row["id"], text=row["text"], mentions=mentions, relationships=[]))

    pretrained = score_reports(reports, detector="pretrained")
    pilot = score_reports(reports, detector="pilot")
    selected = "pilot" if pilot["ner"]["f1"] > pretrained["ner"]["f1"] else "pretrained"
    result = dict(selected=selected, criterion="case-separated development exact-span NER F1",
                  reports=len(reports), pretrained=pretrained["ner"], pilot=pilot["ner"])
    content = json.dumps(result, indent=2) + "\n"
    SELECTION_PATH.write_text(content, encoding="utf-8")
    print(content, end="")


if __name__ == "__main__":
    main()
