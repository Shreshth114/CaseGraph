# Casegraph project report

## Objective

Casegraph is an AI course prototype for exploring entities and reported relationships in investigative text. It links claims to their source, exposes uncertain and denied claims, and supports human review of proposed connections and identity merges.

## Current course release

The frozen field set contains 16 fictional reports and 12 labeled relationships. On the same text and checkpoint, the previous extractor returned 7 correct, 0 extra and 5 missing relationships. The new rules returned 11 correct, 0 extra and 1 missing, for 100% precision, 91.7% recall and 95.7% F1. Results by type were 5/6 communications, 3/3 meetings and 3/3 affiliations. A voicemail involving Sofia Park was missed. The frozen texts and separate custody answer keys were written during implementation. Independent authoring and second-reviewer agreement remain outstanding.

The earlier contextual set went from 13/17 to 17/17 after its errors informed changes. On those reports, the more conservative identity handling automatically linked 1/28 true mention pairs, previously 3/28. Automatic and proposed links together still covered 25/28, with 23 proposals to review. Repeated full names now have distinct mention-level records, explicit source IDs constrain merges and the inspector retains the supporting passages.

| New fictional custody case | Expected | Observed | Evidence |
|---|---|---|---|
| KEY-21 | Prioritize Lila Hart | Lila Hart | Both expected custody citations matched. |
| SEAL-8 | Abstain on a tie | Abstained | Both handlers had two independent citations. |
| MTR-7 | Abstain after competing custody | Abstained | A second person's later receipt remained visible. |

No case produced a wrong prioritization. These three controlled fixtures exercise decisions and citation handling. The live KIT-17 case remains a separate demonstration. Run `python -m validation.check` from the project environment to reproduce the measurements.

## Earlier contextual relationship update

The first fine-tuned test missed six claims. Three were recovered when the correct entity spans and types were supplied. The other three required coverage for membership recorded in a list, an addressed packet and a jointly described meeting.

The update recovers full person names in explicit voicemail and passive-call slots. A surname in a relationship clause links to an earlier full name when the report provides one candidate. If multiple people share that surname, the system keeps the endpoint separate and flags its evidence for review. The new rules cover the three missed constructions and retain the source sentence and claim status. Regression checks include unrelated co-mentions, virtual gatherings and a notification addressed to an organisation.

| Relationship benchmark | Previous rules | Updated rules |
|---|---:|---:|
| Original test reused to develop the fixes | 11 of 17 | 17 of 17 |
| Fresh retest with the same fine-tuned detector | 8 of 17 | 13 of 17 |
| Fresh retest precision | 100.0% | 100.0% |
| Fresh retest recall | 47.1% | 76.5% |
| Fresh retest F1 | 64.0% | 86.7% |

The original set was inspected during development, so its 17 of 17 score is a regression result. The developer authored and annotated the 18 new fictional reports after freezing the rules and made no rule changes after scoring. The new set includes unrelated names and 17 labeled claims. Neither version produced a false relationship on it. Four claims remained missing. One involved an entity span or type error. The other three involved unsupported wording for an officer's affiliation, a jointly attended tour and a call with an intervening time adverb. The fresh result is two correct claims short of 15 of 17.

## Lead Finder demonstration

The Lead Finder uses five fictional KIT-17 reports. A controlled event parser captures checkout, receipt, handover and shift-record statements and retains each complete source sentence. The app compares activity for the selected item, location and time window. It counts distinct origins and custody events. A handover contributes custody support to the recipient. Unverified witness statements and contradictory shift records stay visible in the evidence.

Before identity review, Dev Rao and D. Rao each have one custody record. An approved merge combines the evidence, making Dev Rao the strongest lead with two records and a last reported handover at 15:12. Clearing the merge restores the separate identities. Mira Sen's witness account remains reviewable with a shift record that places her elsewhere at the reported time. The fictional answer is stored separately and revealed on request.

Automated checks exercise identity review and undo, source attribution, copied records, exact item and timing scope, ties, later competing custody, handover direction, and rejected evidence. This is a single-case demonstration of evidence prioritization.

## Fine-tuned NER pilot

Casegraph now defaults to a pipeline fine-tuned from spaCy's `en_core_web_sm` weights. The run updated the sourced `tok2vec` and NER components on CPU. The corpus contains 96 training reports (16 cases, 312 annotated mentions) and 30 development reports (five other cases, 90 mentions). The split uses different identities and writing patterns. Annotations cover person, organisation and location spans without bracketed record IDs. spaCy validated the annotations and found no document overlap. The corpus contains 48 organisation mentions in training and omits labels outside the three target categories. Both are limits of the pilot.

spaCy selected its checkpoint on development data. With the same Casegraph refinement rules applied to both detectors, exact-span development F1 was 76.9% for the pretrained model and 78.9% for the pilot. The development comparison selected the pilot before the final test was scored.

The final test comprises 18 separately authored fictional reports with 62 entity mentions and 17 relationship claims. The same project developer authored the training templates and final test. The final test is disjoint from the training and development cases, was not used to pick the checkpoint, and remains a small synthetic evaluation.

| Final test metric | Pretrained | Fine-tuned |
|---|---:|---:|
| Exact-span entity precision | 83.6% | 86.7% |
| Exact-span entity recall | 74.2% | 83.9% |
| Exact-span entity F1 | 78.6% | 85.2% |
| Person F1 | 83.1% | 88.6% |
| Relationship precision | 100.0% | 100.0% |
| Relationship recall | 58.8% | 64.7% |
| Relationship F1 | 74.1% | 78.6% |
| Correct relationships | 10 of 17 | 11 of 17 |

Relationship and identity rules were fixed for the comparison. On the older 19-claim retest, the same detector change raised correct claims from 9 to 11 with one false positive in each version. The final test still missed six claims, and one automatic person-identity pair was incorrect. The two 100% precision values reflect just 10 and 11 relationship predictions respectively.

## Data and methods

- The [Montagna CSV files](https://zenodo.org/records/3938818) supply 144 distinct IDs and 438 usable source rows after exclusion of one meeting self-loop. Montagna exercises graph import and evidence navigation.
- The 36 fictional template reports and 12 hand-written development reports serve as examples and development diagnostics.
- The 18 fresh fictional reports were authored and annotated separately from the extractor changes. They contain 87 entity mentions, 27 labeled relationship claims and 44 same-person mention pairs. Their text has no record ID markers. Both versions were scored on the same locked reports, using the same installed spaCy model.

The updated pipeline combines spaCy entity spans with constrained person cues, including titles and participant positions in recognized clauses. It adds patterns for attributed or passive calls, meetings described as occurring between two people, and explicit organisational affiliation. Contrast clauses receive separate claim statuses. The original sentence stays attached to each claim. Spelling variants can be suggested when the reports mention a contact name in common. These suggestions require human review, and the interface shows the passages behind them.

NetworkX calculates degree centrality and Louvain communities from a simple undirected graph of directly reported, unrejected connections. Repeated source rows and self-links created by reviewed merges remain available as evidence. Self-links are excluded from centrality and communities.

## Relationship diagnostic and retest

The diagnostic reused the 18 earlier reports and replaced detected mentions with the human-labeled entity spans and types. Sentence segmentation, relationship rules, claim status rules and scoring stayed fixed within each comparison. No identity labels or relationship labels were supplied to the extractor.

| Rules on the earlier reports | Detected entities | Human-labeled entities |
|---|---:|---:|
| Before the targeted fix | 3 of 27 (11.1% recall) | 4 of 27 (14.8% recall) |
| After expanding the relationship rules | 10 of 27 (37.0% recall) | 21 of 27 (77.8% recall) |

The original one-claim difference pointed to missing relationship constructions. The targeted update added voicemail and addressed-message wording, joint-subject meetings, explicit job roles and payroll, and scoped attribution from records such as phone logs. Direction checks distinguish the sender from the recipient in passive statements. The larger gap after the fix indicates that entity detection now prevents the extractor from reaching many of the links its expanded rules can recognize.

After freezing the rules, the same developer authored and annotated a new 18-report fictional retest. The retest contains 53 entity mentions and 19 claims, including unrelated co-mentions, disputed links and denials. Neither version received the reference labels during scoring. The retest scores were recorded without further rule tuning. This is a fresh synthetic comparison by one author and is separate from the earlier independently authored benchmark.

| Fresh retest relationship metric | Before | Expanded rules |
|---|---:|---:|
| Precision | 85.7% | 90.0% |
| Recall | 31.6% | 47.4% |
| F1 | 46.2% | 62.1% |
| True positives / false positives / false negatives | 6 / 1 / 13 | 9 / 1 / 10 |

Entity extraction stayed at 80.8% F1 on this retest because the targeted update kept mention detection unchanged. Automatic identity resolution found 2 of 33 true mention pairs and produced one incorrect pair. The combination of automatic links and review suggestions surfaced 21 of 33 true pairs with two incorrect proposals overall. Review continues to preserve original evidence and claim status.

## Earlier frozen comparison

Scores are micro-averaged before human review. Entity matches require exact spans and types. Relationship matches require the two mention offsets, relationship type and claim status. Identity results compare same-person mention pairs. **Found or suggested** includes automatic pairs and review candidates. These candidates remain separate records until accepted.

| Fresh test task | Previous F1 | Updated F1 | Updated precision | Updated recall | Updated TP / FP / FN |
|---|---:|---:|---:|---:|---:|
| All entity types | 59.6% | 67.1% | 73.0% | 62.1% | 54 / 20 / 33 |
| People | 74.5% | 76.5% | 92.9% | 65.0% | 39 / 3 / 21 |
| Relationships | 13.3% | 20.0% | 100.0% | 11.1% | 3 / 0 / 24 |
| Automatic identity pairs | 4.3% | 16.3% | 80.0% | 9.1% | 4 / 1 / 40 |
| Identity pairs found or suggested | 30.2% | 39.3% | 91.7% | 25.0% | 11 / 1 / 33 |

The 12 hand-written development reports reach 96.9% entity F1 and 94.7% relationship F1 after the changes. They informed the rules, so those figures are development diagnostics. The fresh comparison is the estimate on unseen examples.

## Earlier error analysis and general limits

The version before the targeted relationship fix missed 24 of the 27 earlier relationship claims. Fifteen misses had a missing or mistyped endpoint at the expected mention offset. The other nine had the expected endpoint types and start offsets, but no matching extraction for the expected relationship and direction. The measured 100% relationship precision comes from three predictions. The recall and error breakdown point first to stronger mention detection and then to broader support for varied relationship wording.

The resolver made one incorrect automatic mention-pair link in the fresh benchmark. Human review and contextual suggestions help surface ambiguous cases. A reported contact name can itself be ambiguous, so it provides corroborating context but does not establish identity.

The prototype accepts English plain text. The evaluation is small and fictional. Graph structure reflects the supplied records, and a review decision preserves the source's uncertainty status. Review history lives in the browser tab and can be exported as JSON.
