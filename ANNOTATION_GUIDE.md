# Labeling a Casegraph evaluation case

Give each reviewer the fictional report text and case question before showing predictions or the answer key. Assign complete cases to one split and record the author. Keep names, templates and source narratives for a held-out case out of development. Freeze report IDs, texts, labels and file hashes before comparing extractors.

| Label | What to record |
|---|---|
| Entity | Mark the exact start and exclusive end of each person, organisation and location. Exclude titles, determiners, possessive endings and bracketed record IDs. Annotate each occurrence. |
| Identity | Assign a case-local reference ID when the source establishes identity. Keep same-name people, unresolved surnames and competing aliases separate. Cite the passage behind each merge. |
| Relationship | Mark source and target mention offsets in the same report, type and claim status. The caller or writer is the source for communication. A person is the source for affiliation. For a symmetric meeting use the textual order. |
| Claim status | Use directly reported for an affirmative account, unverified for a qualified allegation, and denied for an explicit denial. Annotate each clause separately. Flag a genuinely ambiguous interpretation for adjudication. |
| Negative example | Label entities even when no interaction is asserted. Separate attendance, invitations and names appearing on adjacent pages can have zero edges. |
| Custody | Record the item, holder or sender and recipient, event time, place, date if available, report ID and source origin. Preserve literal uncertainty. Mark copied accounts and unresolved dates. Dates are event metadata outside the three NER labels. |
| Lead answer | Specify the last documented handler or abstention, supporting row IDs, competing rows and reason. Keep narrative answer keys separate from the records supplied for ranking. |

For independent validation, two reviewers label the same untouched sample separately. Compare exact typed spans, directed claim tuples, identity pairs and custody citations. Retain both label files and record an adjudicated label with a reason for each disagreement. Publish TP, FP and FN alongside precision, recall and F1, plus number of candidate identity pairs a human must review. Record the number of wrong prioritizations and abstentions on cases with enough evidence. The current field fixtures were authored in the implementation session and await independent double-labeling.
