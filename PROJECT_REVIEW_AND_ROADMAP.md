# Casegraph project review and roadmap

**Reviewed 20 November 2026** against the local `lead-finder` checkout, including its uncommitted changes. This document covers the original course requirements, the Lead Finder extension, the evidence for both, and an ordered plan for the next release.

## Implementation update after the review

The historical findings below describe the starting checkout. The release now includes maximum independent-source matching, passage coverage, three scored custody fixtures, contextual extraction fixes, portable saved cases, mention-level identity review, a custody timeline, a path inspector and optional weighted Montagna node sizing. The ZIP is built with a content manifest. The new 16-report field set improved from 7/12 to 11/12 relationships. Independent authorship and double-labeling by a second reviewer remain open. [Release results](PROJECT_REPORT.md) · [Current walkthrough](DEMO.md)

## What the team could demonstrate at baseline

An investigator can upload a report, find the people and organisations it mentions, inspect a reported connection, read the sentence behind it, and record a review decision. They can explore the Montagna meeting and call network through the same interface. In the fictional KIT-17 exercise, reviewing a possible alias changes which custody records can be attributed to one handler. Clearing the decision reverses the result.

**The original ten features are present at prototype level.** The trained component detects entities. Rules extract relationships, propose identity matches and interpret custody events. NetworkX computes graph statistics. The strongest next investment is testing the evidence and review workflow across new cases. Supplying correct entity labels recovered one of the four relationship misses diagnosed below. The other three still required changes downstream.

## Delivery against the feature list

| # | Requested feature | What works today | Main remaining gap |
|---|---|---|---|
| 1 | Document input | Paste English text or upload UTF-8 text files. The API accepts 1–50 reports, up to 20,000 characters each and 100,000 combined. | Uploaded cases live in the tab. Scans, PDFs and document revisions need their own ingestion workflow. |
| 2 | Named entity recognition | A fine-tuned spaCy model and context rules extract people, organisations and locations. An explicit person ID can anchor a mention. | Organisation boundaries and types can cost a downstream relationship. Report results for each entity type. |
| 3 | Relationship extraction | Meetings, communications and organisation associations retain endpoints, direction where applicable, source and claim status. | Extraction compares adjacent mentions within a sentence. Intervening names, paraphrases and cross-sentence references can hide links. |
| 4 | Entity resolution | Record IDs, local alias statements and some surname references link mentions. Similar names and shared contacts can generate proposals. Reviewers can accept, reject and clear merges. | Identical unmarked names of the same type share a key within one report. Two people with the same full name in that report can collapse before review. |
| 5 | Knowledge graph | Entities and individual evidence edges feed a NetworkX projection for analytics. Reviewed merges preserve original endpoint IDs on edges. | General text has no first-class event record tying together participants, item, time and place. Lead Finder has its own narrower event representation. |
| 6 | Interactive visualization | Search by name or ID, filter by relationship type, pan, zoom, select a node or edge, or use the inspector lists. | Repeated connections overlap on the canvas. Lines lack direction arrows, making the evidence text important when identifying a caller or recipient. |
| 7 | Graph analytics | Degree centrality and seeded Louvain communities use distinct, directly reported, unrejected links. Isolated nodes receive no community. | Frequency and direction are lost in the analytics projection. A graph path or shared community alone provides no evidence for a new contact. |
| 8 | Evidence traceability | A text edge opens the source sentence and full report. Montagna edges carry file, row and weight. Lead cards link to supporting and conflicting records. | Exportable findings need durable source and span identifiers that survive reopening a case. Review history currently exports selected evidence. |
| 9 | Confidence and uncertainty | Directly reported, unverified and denied describe the source wording. Review decisions are recorded separately. | These are qualitative claim statuses. A calibrated estimate of extraction reliability would require separate labeled data and validation. |
| 10 | Evaluation | The Evaluation view calculates precision, recall and F1 for exact typed entity spans and for relationships. It also scores automatic and proposed identity pairs. | Small synthetic sets limit generalization. The headline relationship score covers 17 claims. |
| 11 | Lead Finder extension | Five fictional records support a question about the last documented handler of one item. Evidence counts, conflicting records, identity review, abstention and answer reveal work together. | One scripted case and a controlled parser. General text uploads use the network pipeline. A team has yet to measure lead quality across independently authored cases. |

## What data we have and what each set answers

| Source in the repository | Size | Appropriate use |
|---|---:|---|
| Three Montagna CSVs | 144 graph nodes, 288 usable meeting rows, 150 call rows | Explore a published structured network and trace rows. One meeting self-loop is skipped. Meeting and call weights remain visible. These files provide no report sentences for scoring NLP. |
| [Template demo](corpus.py) | 36 reports, 140 mentions, 30 claims | Demonstrate extraction with controlled wording, ID markers, denials and unrelated mentions. |
| [Hand-written development cases](benchmark.py) | 12 reports, 32 mentions, 10 claims | Develop and demonstrate handling of ambiguous names and wording without markers. |
| [First relationship benchmark](fresh_benchmark.py) | 18 reports, 87 mentions, 27 claims | Historical diagnosis of the “10 out of 27” result. The set was later inspected while improving the rules. |
| [Earlier relationship retest](retest_benchmark.py) | 18 reports, 53 mentions, 19 claims | Compare earlier relationship changes on a different sample. |
| [NER training and development data](training/data) | 96 training reports across 16 cases, 312 annotated mentions. 30 development reports across five other cases, 90 mentions. | Fine-tune spaCy and choose the detector on case-separated development data. The generator supplies entity spans. No relationship classifier is trained here. |
| [NER comparison and subsequent regression set](training/test_reports.py) | 18 reports, 62 mentions, 17 claims | Compare pretrained and fine-tuned detectors under fixed rules. The later 17/17 result checks known examples used in rule development. |
| [Contextual retest](training/context_retest.py) | 18 reports, 51 mentions, 17 claims | Measure the contextual changes on examples written after the rules were frozen. The same project developer authored this set. |
| [KIT-17 case and answer](lead_cases) | One incident, five reports, one separate answer file | Demonstrate evidence review and a reversible identity decision. The reference explanation also contains story details beyond the records available to the investigator. |

The planned 30–50 synthetic demo reports are covered by the 36-report collection. The larger training inventory answers a different question. Repeated templates, shared authorship and few independent cases matter more for estimating performance than the total number of files. Dataset and model provenance are in [CREDITS.md](CREDITS.md).

## Results reproduced during this review

All **23 automated tests passed** in the project environment. Flask's test client returned HTTP 200 for the home page, fictional reports, hand-written cases, Montagna, Lead Finder and Evaluation. Posting the bundled sample to the upload API produced three claims, one each directly reported, unverified and denied. The Montagna view returned 438 evidence rows and nine communities under the current projection.

| Current pipeline on the 18-report contextual retest | Correct / reference | Precision | Recall | F1 |
|---|---:|---:|---:|---:|
| Exact entity span and type | 44 / 51 | 86.3% | 86.3% | 86.3% |
| Relationship endpoints, type and source status | 13 / 17 | 100% | 76.5% | 86.7% |
| Automatically linked same-person mention pairs | 3 / 28 | 100% | 10.7% | 19.4% |
| Same-person pairs linked or surfaced for review | 25 / 28 | 100% | 89.3% | 94.3% |

The relationship result moved from **8/17 to 13/17** on the same contextual retest with the same trained detector. The 13 predictions comprised **9/10 communications, 3/4 meetings and 1/3 associations**. The observed 100% precision comes from those 13 predictions. Identity suggestions likewise measure which pairs reach a reviewer. Only three true pairs were automatically linked. Keep the denominators visible in the presentation.

Historically, fine-tuning raised development entity F1 from 76.9% to 78.9%. On the separate NER comparison set, entity F1 rose from 78.6% to 85.2% and relationship recovery went from 10/17 to 11/17 under fixed relationship rules. Later changes recovered all 17 known claims on that set. The [project report](PROJECT_REPORT.md) records the sequence of experiments.

### Where the four remaining relationships went

I repeated extraction with the labeled entity spans supplied to the current rules. This isolates whether correcting the mentions alone recovers each claim.

| Report | What the reference says | Recovered with labeled entities? | Engineering implication |
|---|---|---|---|
| `context-06` | A renewal list records membership in Heatherfen Guild. | Yes | Inspect the organisation mention and its boundary alongside the member's name. Add varied roster examples to development data. |
| `context-11` | A person is listed as one of an organisation's officers. | No | Cover explicit officer affiliations and include examples where someone merely files an organisation's paperwork. |
| `context-13` | An attendant observed two people together for a tour. | No | Distinguish witnessed joint attendance from separate attendance or an invitation. |
| `context-15` | A record says one person “later phoned” another. | No | Handle intervening time words while preserving caller direction, negation and attribution. |

These four cases can now serve as regression examples. To pursue the team's 15–16/17 target, freeze a new test before tuning. Report how often the system inserts a wrong link as well as how many labeled links it recovers. One extra correct claim moves recall by almost six percentage points on a 17-claim test.

## Findings that change the implementation priorities

1. **Independent custody evidence can be undercounted.** I reproduced this with three fictional records for one handler. Register A records a 15:06 checkout, register B records that same event, and register A records a second event at 15:09. The current loop marks an origin and an event as used even when it skips their pair. It returns one supporting record. B at 15:06 and A at 15:09 satisfy the stated distinct-origin and distinct-event rule and give two. Use maximum bipartite matching between origin and event, retain the actual source rows chosen, and test permutations and duplicate copies. Source independence itself still depends on the supplied origin metadata. [Ranking code](lead_finder.py)
2. **A present but unread custody record can look like missing evidence.** Changing “checked out” to “signed out” in the demo dropped the checkout edge. The parser silently skips lines outside its grammar. Record a parse outcome per source passage, distinguish narrative context from an unparsed event candidate, and expose coverage before prioritizing a handler. The current time comparison also assumes one day and matching location text. [Case parser](lead_finder.py)
3. **Review work is easy to lose.** The tab keeps the active case and its decision history in memory. Downloading history works, but the app has no reopen workflow. General text edge IDs depend on extraction order, and the review API limits a request to 300 decisions. A saved case needs source versions, durable IDs, and replay rules when text or model versions change. [Review API](app.py) · [Client and export](static/app.js)
4. **The demo can imply more AI than it uses.** The Lead Finder screen inherits the graph's spaCy footer even though its case uses the custody parser. Label the active method per view and distinguish the documented last handler from facts supplied by the fictional answer key. [Client](static/app.js) · [Answer key](lead_cases/kit17-answer.json)
5. **The submission archive trails the workspace.** The inspected ZIP contains the earlier app and excludes the Lead Finder module, case files and its tests. The `lead-finder` checkout has uncommitted feature changes. The base submission diff contains 88,685 inserted lines, including 84,978 in spaCy's generated vocabulary JSON. Git tracks no `node_modules` files. Build the next archive from a recorded revision and test the extracted copy. [Setup](README.md) · [Walkthrough](DEMO.md)

## Recommended implementation order

Each step has a check the team can run. Steps 1–5 make a defensible course submission. Steps 6–9 grow it into a more useful workspace.

| Order | Work | Completion check |
|---|---|---|
| 1. Freeze the baseline | Record the revision, checkpoint, detector, split IDs, per-task counts and current demo output. Keep answer keys outside extraction and ranking inputs. | A teammate can reproduce the table above using the bundled model, and identify which sets have already influenced development. |
| 2. Fix evidence counting and visibility | Correct the origin/event example above. Show the chosen supporting rows, skipped duplicates and unparsed candidate records. Name the actual extraction method in the UI. | The three-record example gives two supports in every input order. A copy alone gives one. An unread custody statement is visible for review. |
| 3. Validate Lead Finder beyond KIT-17 | Have a teammate independently write three fictional cases with separate keys. Include a clear last handler, a tie or insufficient evidence, and later custody by a different handler. Label acceptable outcomes and supporting passages before running the tool. Keep KIT-17 as the live demo. | For every case, publish expected and actual handler or abstention, whether each cited passage supports the decision, and whether competing evidence is visible. Count incorrect prioritizations separately. |
| 4. Improve NLP where the evidence points | Write an annotation guide for typed spans, dates, aliases, direction, negation and attributed claims. Double-label a sample and adjudicate disagreements. Split by case and author, then target the four failure families above. Include similar sentences without a relationship. | Compare the baseline and candidate on the same fresh cases. Publish TP, FP, FN and per-type results. Keep observed regression and fresh performance in separate tables. Retrain NER when the new annotations demonstrate an entity gap. |
| 5. Cut a reproducible course release | Run unit and API checks, rehearse the walkthrough, capture approved changes in version control, and build an archive containing the case, model, credits and tests. Add a packaging command or CI job so a future feature cannot quietly drop out. | On a clean extraction, start the app, upload the sample, trace a Montagna row, review and undo the KIT-17 merge, reveal its answer and run Evaluation. Verify links, counts and files against the released revision. |
| 6. Save and reopen cases | Add local SQLite or a versioned portable case file. Store original text, input hashes, extraction version, evidence spans, timestamped decisions and optional reviewer notes. | Reopening restores the exact graph and decision history. Re-importing a changed source flags stale decisions. Two identically named reports retain separate IDs. |
| 7. Strengthen identity review | Give each mention a stable identity before consolidation. Add explicit “different people” evidence, side-by-side contexts and optional date or role cues. Measure reviewer workload as well as true-pair coverage. | Same-name people in one report remain separable. An explicit conflicting ID survives a chain of merges. A reviewer can trace why a pair was proposed and undo acceptance. |
| 8. Add a custody timeline | Start with the existing item, time, actor, origin and claim-status fields. Show custody changes in order, link every entry to its sentence, and show contradictory locations side by side. Extend to dates or uncertain times only when supported by source data. | A presenter can explain who appears in the last documented handover, which record competes with it, and how a review decision changes the timeline. |
| 9. Add evidence-backed network exploration | Offer a two-entity path inspector, parallel-edge grouping, and an optional weighted Montagna view. Explain how call direction, repeated rows and weights are handled. | Every step on a displayed path opens its source. Users can compare distinct-neighbor degree with weighted activity, inspect both call directions and see which claims entered each calculation. |

### Further additions, in order of likely value

| Enhancement | Useful outcome | Prerequisite or tradeoff |
|---|---|---|
| Case summary export | Generate a shareable brief with the question, cited observations, unresolved conflicts and review history. | Build on durable evidence IDs. Check every citation in the exported brief against its original source. |
| Full-text evidence search and status filters | Find all reports mentioning a name, a denied meeting or an unresolved alias, including passages that generated no edge. | Index original passages alongside the graph. This also gives the reviewer a way to find extraction misses. |
| New text sources | Start with independently written fictional interview notes, shift logs and call summaries. Later consider de-identified material with documented permission and matching annotation definitions. | Another structured network can test graph import. Improving text extraction requires text with labeled spans and relationships. |
| PDF and scanned-document input | Preserve page references and highlight the exact passage behind each extraction. | Begin with text PDFs. Add OCR with visible transcription quality and a way to correct text while retaining the original. |
| Richer extraction models | Compare a learned relation classifier or span-based model with the current rules for paraphrases and longer clauses. | Build enough diverse relationship labels and negative examples first. Compare citation accuracy, false positives and latency under the same split. |
| Multi-user review and larger cases | Add case access controls, reviewer attribution and versioned edits if the prototype moves beyond a local classroom demo. Profile repeated NLP, candidate pairing and graph layout on increasing batch sizes first. | Measure performance and concurrent edits before selecting deployment infrastructure. Keep local fictional cases usable independently. |

## Suggested five-minute presentation

1. **0:00–1:00 — From text to claims.** Upload `demo-report.txt`. Open the reported call, show its source sentence and distinguish the two Mira records with different IDs.
2. **1:00–2:30 — A review decision changes a lead.** Open KIT-17. Compare the witness account with the shift register. Review the two Rao records, accept the merge, inspect both custody citations, then clear the merge. Explain exactly why the app can prioritize a last documented handler.
3. **2:30–3:30 — Explore the structured network.** Open the N0–N1 meeting in Montagna. Trace it to row 2 and explain what a distinct neighbor contributes to degree centrality.
4. **3:30–4:30 — Show the evidence for performance.** Open Evaluation. Use 13/17 on the contextual retest, give the four misses, and explain what the 17/17 regression check measures.
5. **4:30–5:00 — Close with the next milestone.** Show the proposed three-case Lead Finder evaluation and the criteria for a correct abstention. A reviewer should be able to explain both a prioritized lead and a decision to leave the case unresolved.

## How to reproduce and navigate the review

From the project root in the configured Python 3.12 environment, run:

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python app.py
```

Open the local app at `http://127.0.0.1:5050`. **Evaluation → New retest** shows the current metrics. The sample upload, merge and undo sequence, and Montagna example are in [DEMO.md](DEMO.md). This review used local code, fixtures, the installed checkpoint, Flask API responses and the ZIP manifest. It did not retrain the model or perform a new browser or clean-install test.

| Project area | Source |
|---|---|
| App entry points and validation | [app.py](app.py) |
| Extraction, identity resolution, review, graph projection and scoring | [analysis_engine.py](analysis_engine.py) · [language_rules.py](language_rules.py) |
| Custody parser, ranking and fictional records | [lead_finder.py](lead_finder.py) · [lead_cases](lead_cases) |
| Front end and inspector | [Page](static/index.html) · [Interactions](static/app.js) · [Styles](static/style.css) |
| NER training, selection and checkpoint | [Training data builder](training/prepare_data.py) · [Training configuration](training/config.cfg) · [Detector selection](training/selection.json) · [Bundled model](training/run/model-best) |
| Regression coverage | [Language rules](tests/test_language_rules.py) · [Review](tests/test_review.py) · [Lead Finder](tests/test_lead_finder.py) |
| Installation, earlier experiments and attribution | [README](README.md) · [Project report](PROJECT_REPORT.md) · [Credits](CREDITS.md) |
