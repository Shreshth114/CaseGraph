# Casegraph report-language test

## Affiliation update

After the original test, six missed affiliations informed a rules update. Replaying the same 36 reports through the upload API now recovers **10/11 affiliations** (previously 4/11) and **28/34 relationships** (previously 22/34), with zero extra links. Overall relationship recall is 82.4% and F1 is 90.3%. The one missing affiliation is a denial expressed through a pronoun in `kiln_log-03`. Treat these updated scores as regression results on inspected examples.

The added checks cover recorded offices, employee listings, qualified payroll claims, explicit membership denials and employer-first payroll records. Seven positive examples match the expected person, organisation, status and evidence sentence. Seven lookalikes produce zero links. These are targeted engineering checks. [Affiliation tests](../tests/test_affiliations.py)

## Original frozen test result

On 36 new fictional reports, the current Casegraph upload pipeline found 22 of 34 labeled relationships, missed 12, and produced zero extra relationships. The upload API produced the same results as the scorer. Six reports contained no labeled relationship. All six remained free of predicted links.

## What was measured

The 36 reports describe six fictional cases. Each case includes a report where names or organisations occur without an asserted relationship. The set contains 113 labeled mentions (67 people, 18 organisations, 28 locations) and 34 claims (12 communications, 11 meetings, 11 associations). Examples include denied and uncertain claims, passive calls, multiple actions, record IDs, and organisations mentioned alongside unrelated people. No report text or full labeled name matched any of the 262 earlier training, development and benchmark texts checked.

The implementation assistant wrote the text and reference labels with knowledge of the project's task and earlier error patterns. The data and labels were frozen before inference. Scores describe this particular English synthetic sample. The run used the working tree on top of local commit `d204921`, including the subsequent four fixes. No rules or weights were tuned during this run.

Entities require an exact character span and type. Relationships require the reference source and target mention offsets, relationship type and claim status. Precision measures the share of predictions that match the labels. Recall measures the share of labeled items recovered. F1 is their harmonic mean. Counts below are micro-averaged over the full set before human review.

| System and task | Correct | Extra | Missed | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Stock spaCy, raw entities | 73 | 30 | 40 | 70.9% | 64.6% | 67.6% |
| Fine-tuned spaCy, raw entities | 88 | 26 | 25 | 77.2% | 77.9% | 77.5% |
| Stock spaCy with Casegraph rules, entities | 82 | 22 | 31 | 78.8% | 72.6% | 75.6% |
| Fine-tuned spaCy with Casegraph rules, entities | 93 | 20 | 20 | 82.3% | 82.3% | 82.3% |
| Stock spaCy with Casegraph rules, relationships | 21 | 0 | 13 | 100% | 61.8% | 76.4% |
| Fine-tuned spaCy with Casegraph rules, relationships | 22 | 0 | 12 | 100% | 64.7% | 78.6% |

## Breakdown with the fine-tuned checkpoint

| Entity | Labeled mentions | Raw model F1 | App F1 |
|---|---:|---:|---:|
| Person | 67 | 86.5% | 88.4% |
| Location | 28 | 70.6% | 74.5% |
| Organisation | 18 | 51.4% | 70.3% |

| Relationship | Correct / labeled | Recall |
|---|---:|---:|
| Communication | 10 / 12 | 83.3% |
| Meeting | 8 / 11 | 72.7% |
| Association | 4 / 11 | 36.4% |

By source status, the pipeline recovered 14/22 directly reported claims, 4/6 denied claims and 4/6 unverified claims. All 22 predictions matched the expected direction, type and status.

## What accounted for the misses

A diagnostic pass supplied the labeled entity spans and types to the same relationship rules. It recovered five previously missed claims and reached 27/34. Seven claims remained missing even with correct endpoints. Association extraction accounts for seven of the twelve end-to-end misses.

- In `theatre_keys-01`, the app typed the voicemail recipient Tobin Esker as an organisation. Correcting the entity labels recovered the communication.
- In `library_returns-06`, the app retained only “Armand” from the name “Zélie Armand”. Supplying the complete spans recovered both actions.
- In `pump_receipts-02`, the app correctly detected Nils Harten and Wren Valve Cooperative. The phrase “is listed as the treasurer of” still yielded no association.
- In `tide_board-04`, both people were recognized. Linking the denial in “says he never met” to the named speaker requires resolving the pronoun.

Fine-tuning improved raw entity F1 by 9.9 percentage points. With the same relationship rules it yielded one additional correct link on this sample. Affiliation wording and organisation typing are the clearest targets for further work.

## Reproduce

Run from the project root with the installed pretrained model and the bundled fine-tuned checkpoint.

```sh
.venv/bin/python -m validation.score_report_language
```

The command verifies the original data hash and scores the currently installed rules. It prints both models' scores and the report IDs and endpoints of missed or extra links. [Labeled reports](report_language_test.json) · [Scorer](score_report_language.py)
