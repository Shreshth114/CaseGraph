# Casegraph demo walkthrough

Start the app using the [README](README.md) and open [Casegraph](http://127.0.0.1:5050). The walkthrough fits a short course demo.

## Find a lead in the fictional recorder case

1. Open **Lead Finder**. Read the question and **Read incident report**. The panel starts with insufficient evidence to prioritize a person. The checkout log names Dev Rao and the handover note names D. Rao.
2. On Mira Sen's card, open **Witness account** and **Shift register**. The account is labeled **Unverified claim**. The register places her at a different desk during the alleged handling. Select **Clear selection** after each source to return to the leads.
3. Click **Review identity match** on either Rao card. Compare both source sentences and choose **Accept merge**. Return to **Leads**. Dev Rao now has two independent custody records, with the latest at 15:12.
4. Open **Equipment checkout log** and **Handover note** from Dev's card. Show that both retain their original wording and name references.
5. Click **Reveal fictional answer**. This opens the separately authored answer for the exercise. The evidence supports a last handler for follow-up. The reveal explains what happened to the recorder in the fictional scenario.
6. Optional live check. Open **Review → Clear decision** for the alias and return to **Leads**. The two Rao records split and the prioritized lead disappears.


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

Open **Evaluation** and start with **Frozen field set**. The current extractor found 11 of 12 claims, up from 7, across 16 fictional reports. It missed one communication. Show the three custody cases, including both abstentions. The earlier contextual set now scores 17/17 after its four misses informed development.

To demonstrate surname resolution, paste “The duty log identifies Clem Arden as the observer. Arden denied calling Jonna Pell.” Open the communication claim for Clem Arden and show the exact sentence containing the surname and the **Denied** label.

Use the **Final NER test** tables to show what fine-tuning contributed before the new context rules. [Project report and scoring details](PROJECT_REPORT.md)


After accepting the KIT-17 merge, open **Timeline** and select the 15:12 entry. Show the original D. Rao sentence. Choose **Save case**, refresh, then **Open saved case** and select the downloaded JSON. Confirm the prioritized lead and clear the merge to demonstrate reversibility. In Montagna, open **Paths**, choose N0 and N1, and inspect the row supporting their connection. Toggle **Size by source weight** to change the node sizes.
