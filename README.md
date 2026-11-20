# Casegraph

Casegraph is a local investigation-network prototype for an AI course project. It processes text reports into attributed relationship claims and lets you inspect those claims alongside the original evidence.

## Run locally

Use **Python 3.12**. Unzip the submission and open a terminal in the extracted `Casegraph` folder. Installation requires internet access. The trained checkpoint is included.

On macOS or Linux:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m spacy download en_core_web_sm-3.8.0 --direct
.venv/bin/python app.py
```

On Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m spacy download en_core_web_sm-3.8.0 --direct
.venv\Scripts\python.exe app.py
```

Open [Casegraph](http://127.0.0.1:5050). The trained detector is identified as **Casegraph fine-tuned spaCy** in the app footer. The pretrained download is used for the baseline in **Evaluation**. Reports are processed on the local server. Use **Save case** to keep a portable copy before closing the tab. If port 5050 is occupied, append `--port 5051` and open [the alternate port](http://127.0.0.1:5051).

On Windows, use `.venv\Scripts\python.exe` in place of `.venv/bin/python` in the testing and training examples below.

For a first run, upload `demo-report.txt` and follow the [demo walkthrough](DEMO.md). The [project report](PROJECT_REPORT.md) explains the data and scores. See [data and model credits](CREDITS.md) for original sources.

## Explore the project

- **Fictional reports** loads 36 reproducible synthetic reports from `corpus.py`. The corpus includes aliases, similar names, co-mentions, denied claims, and witness accounts. These are fictional cases unrelated to the Montagna IDs.
- **Montagna** loads the three workspace files from the [published Zenodo deposit](https://zenodo.org/records/3938818). Each edge retains the source filename, original row number, and weight. The importer excludes the meeting self-loop. Degree centrality and Louvain communities use a simple undirected graph, where repeated and reversed rows contribute a single neighbor connection. The inspector preserves individual source rows.
- **Analyze reports** accepts new documents. spaCy extracts person, organisation, and location mentions. Explicit person record IDs such as `[P101]` provide identity evidence. Document-local alias statements can link mentions within the report. Names alone are insufficient for cross-report merges. Potential same-name conflicts and similar names with a shared surname appear in Review.
- **Evaluation** scores entity spans and types, relationship endpoints and claim statuses, and person identity pairs. It shows the frozen field comparison, custody outcomes and historical regression checks.

## Interpretation

Relationship extraction uses sentence-level rules for meetings, calls, and explicit organisation associations. The status labels describe what the source says. **Directly reported** indicates a positive claim in the text or a relationship present in a dataset row. **Unverified claim** and **Denied** preserve the source language for review and are excluded from centrality and community calculations. Degree describes distinct neighbors in the available direct-claim graph. Click a node or edge, or use the inspector lists with a keyboard. Drag the graph to pan and scroll over it to zoom.

The prototype supports English plain text. When the pretrained model is missing, the UI reports which fallback is active. The system uses source claims and graph structure to support review. It makes no guilt or criminal responsibility determinations.

## Hand-written benchmark and review

**Hand-written cases** opens the 12 development reports from `benchmark.py`. **Evaluation** compares the previous and expanded relationship rules on the 18-report set in `retest_benchmark.py`. Both versions receive only report text and a document identifier. The diagnostic tables separately compare detected and human-labeled entities on the earlier independently authored reports in `fresh_benchmark.py`. The evaluation distinguishes automatically resolved identity pairs from pairs surfaced for human review. See the [project report](PROJECT_REPORT.md) for the results and error analysis.

The updated rules use titles and relationship roles to repair some person types, recognize indirect and passive descriptions including voicemails, addressed messages and employment roles, and display the sentences behind shared-contact name suggestions. To run the regression suite, use `.venv/bin/python -m unittest discover -s tests -v`.

Select a claim in **Evidence** to accept, reject or clear its review decision. Use **Review** to compare source passages and accept, reject or clear an identity merge. Rejected claims remain in evidence and are excluded from graph calculations. Accepting a claim leaves its original source status intact. Review actions and their source references can be downloaded from the Review panel before refreshing the tab.

See the [demo walkthrough](DEMO.md) for the presentation sequence.


## Contextual relationship retest

The app uses reporting context to recover names in explicit call slots and links a surname to a unique earlier full name within the report. Ambiguous surname references stay separate and appear in **Review**. The rules also recognize documented membership, addressed packets and explicit in-person joint activity.

Before the latest update the contextual test scored 13/17. It now scores 17/17 as a regression set. The separately frozen field set scores 11/12 with zero false positives across 16 reports. [See the project report](PROJECT_REPORT.md)

## Lead Finder

Open **Lead Finder** for the bundled fictional KIT-17 case. Read its incident report and compare custody records, witness statements and conflicting shift records. **Review identity match** opens the source passages for the possible Dev Rao and D. Rao match. Accepting the merge groups the custody evidence and recomputes the lead. **Reveal fictional answer** opens the case's separate reference answer after review.

The demo recognizes controlled checkout, receipt and handover sentences in its five case records. It requires two independent directly reported custody records for a prioritized lead. The incident window and location determine scope, and duplicate events and origins each count once. Ties, conflicting lead evidence, pending identity matches and competing direct records at the same time or later can leave prioritization unresolved. [Demo steps](DEMO.md)

## Reproduce the NER pilot

The app uses the checkpoint in `training/run/model-best` when the development selection chooses it. The model comparison on **Evaluation** holds the relationship and identity rules fixed. To run using the original detector, start the app with `CASEGRAPH_NER=pretrained .venv/bin/python app.py`.

Rebuild the labeled corpora, validate, and train from the project folder with Python 3.12, spaCy 3.8 and `en_core_web_sm` 3.8.0.

```sh
.venv/bin/python training/prepare_data.py
.venv/bin/python -m spacy debug data training/config.cfg
.venv/bin/python -m spacy train training/config.cfg --output training/run --gpu-id -1
.venv/bin/python -m training.select_model
.venv/bin/python app.py
```

The `training/data` folder contains the readable JSONL annotations and the compiled `.spacy` corpora. The final comparison uses `training/test_reports.py`. Its reports are separate from the training and development cases. [See the results and limitations](PROJECT_REPORT.md).


## Continue a case and explore the evidence

- **Save case** downloads a JSON file with source reports and timestamped review decisions. **Open saved case** restores it after a refresh. The local server holds extracted evidence for the eight most recent text batches in memory. Review decisions reuse that evidence. Reopening after a server restart or cache eviction extracts the text once and checks its fingerprint before replaying decisions. A changed source or extraction fingerprint requires another review. Store saved files with the same care as the original reports.
- **Timeline** in Lead Finder orders custody and shift records by time. Select an entry for its original passage. **Source coverage** distinguishes parsed passages, narrative context and unread records. An unread candidate record pauses prioritization.
- **Paths** finds a shortest connection through directly reported, unrejected evidence. Each hop lists all qualifying rows in either direction. **Size by source weight** in Montagna compares total incident weight with the default distinct-neighbor view. Degree centrality and communities keep their original definitions.
- **Evaluation** includes the three custody cases and the frozen field-set comparison. Run `.venv/bin/python -m validation.check` for the machine-readable scores. [Annotation guide](ANNOTATION_GUIDE.md)
- Build the submission using `.venv/bin/python package_submission.py`. The resulting `dist/Casegraph-submission.zip` includes a SHA-256 manifest and the tests.
