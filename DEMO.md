# Casegraph demo walkthrough

Start the app using the [README](README.md) and open [Casegraph](http://127.0.0.1:5050). The walkthrough fits a short course demo.

## Turn a report into an evidence graph

Choose **Analyze reports**, upload `demo-report.txt` or paste this fictional note, and select **Build graph**.

> Mira Sen [P101] met Dev Rao [P102]. Mira Sen [P101] reportedly called Dev Rao [P102]. Mira Sen [P103] did not meet Dev Rao [P102].

In the graph, point out that the two Mira Sen records have different IDs. Open **Evidence** and select the reported call. Show its original sentence, full report, and **Unverified claim** status. Accept the link to record that the extraction is worth retaining. The source remains unverified. Reject a link and show that the evidence remains available in the inspector while the graph omits the rejected edge.

## Review an identity suggestion

Open **Hand-written cases**, then **Review**. Find a suggestion for Theo Price and compare the two source passages. For the demo, treat them as the same fictional record after reviewing the passages. Select **Accept merge** and show the consolidated entity count. Use **Clear decision** to undo the merge. Explain that similar names and overlapping context support review and can leave the identity unresolved.

Accepting and clearing the merge creates two entries in **Download review history**. The export includes the original report references and sentences.

## Trace a Montagna relationship

Open **Montagna**, choose **Evidence**, and select the meeting between N0 and N1. Show the original file and row: `Montagna_Meetings_Edgelist.csv`, row 2, weight 1. Explain that degree counts distinct neighbors and communities summarize patterns in the available graph.

## Present the benchmark

Open **Evaluation** and start with the **New retest** tables. The contextual rules found 13 of 17 claims on new reports, up from 8 of 17. Then show the original 17 of 17 regression result and explain that these examples were used to build the fixes.

To demonstrate surname resolution, paste “The duty log identifies Clem Arden as the observer. Arden denied calling Jonna Pell.” Open the communication claim for Clem Arden and show the exact sentence containing the surname and the **Denied** label.

Use the **Final NER test** tables to show what fine-tuning contributed before the new context rules. [Project report and scoring details](PROJECT_REPORT.md)
