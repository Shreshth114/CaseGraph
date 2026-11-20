"""Build report-level NER corpora with character offsets from annotated text."""

import argparse
import hashlib
import json
from pathlib import Path
from string import Formatter

import spacy
from spacy.tokens import DocBin

# Each row is a separate fictional case with two people, one organisation,
# one location, and an optional short name for the first person.
TRAIN_CASES = [
    ("Rina Mistry", "Owen Kersey", "Northbank Survey", "Alder Basin", "Rina"),
    ("Reem Haddad", "Clive Bexley", "Copperleaf Trading", "Fenwick Steps", "Haddad"),
    ("Lúcia Torres", "Dario Kwon", "Westbank Credit Union", "Little Carr", "Torres"),
    ("Yasmin El-Sayed", "Bo Lin", "Nightingale Printworks", "Rushmere", "Yasmin"),
    ("Niamh O’Rourke", "Marlon Pike", "Celandine Council", "Harpley Green", "Niamh"),
    ("Jae-Min Park", "Asha Desai", "Blackcap Health", "Juniper Walk", "Park"),
    ("Idris Nasser", "Ela Kovač", "Harborough Works", "Old Candle Yard", "Nasser"),
    ("Mae Tan", "Freja Solberg", "Quietwater Studio", "Redwater", "Mae"),
    ("Tariq Baines", "Chloe Mercer", "Thicket Rail", "Longferry", "Baines"),
    ("Tomasz Żak", "Ariel Monroe", "Moorbridge Trust", "Sparrow Crossing", "Żak"),
    ("Leïla Moreau", "Ayo Mensah", "Oxbow Analytics", "Woodrush Hill", "Moreau"),
    ("Danica Flores", "Amin Rahal", "Bittern Housing", "Barleycourt", "Danica"),
    ("Selma Duran", "Silas Broome", "Greenhaven", "Northmere", "Duran"),
    ("Fatou Diop", "Marek Dvořák", "Larchline Energy", "Twinbridge", "Diop"),
    ("Niko Aalto", "Priya Jaisal", "Whitebeam Repair", "Dockside Common", "Niko"),
    ("Maya N'Dour", "Ciro Valente", "Sorrel Archive", "Vale Cross", "Maya"),
]

DEV_CASES = [
    ("Alina Voron", "Amadou Keita", "Sablewood Insurance", "Ives Hill", "Voron"),
    ("Tessa Yuen", "Omar Delaney", "Osprey Exchange", "Thornby", "Tessa"),
    ("Milo Haddock", "Aya Fujita", "Seaforth College", "Millburn Landing", "Haddock"),
    ("Devi Krishnan", "Hugo Peralta", "Wrenmark Engineering", "Priorstead", "Devi"),
    ("Sana Akhtar", "Ivo Jelinek", "Mallowbrook Records", "East Breck", "Sana"),
]

TRAIN_PATTERNS = [
    (
        "A stamped log from {place} names {a} as the officer on duty. {b} returned the key the next afternoon.",
        "A saved message from {a} to {b} refers to a parcel for {org}. No pickup time is visible.",
        "{a} and {b} were listed on different attendance sheets at {place}. {org} issued both sheets.",
        "Dr. {a} was interviewed separately. In the later interview, {short} said the package was still at {place}.",
        "The {org} payroll lists {a} as a technician. The notes also mention {b}, whose role is unclear.",
        "At {place}, {b} phoned {a} at noon. The call is indexed under {short}.",
    ),
    (
        "Before the shift ended, {b} signed a return form for {org}. The earlier version carries the name {a}.",
        "A witness says {a} may have met {b} near {place}. The notebook gives no time.",
        "Nothing in the file confirms a call from {a} to {b}. One envelope is addressed to {org}.",
        "A clerk gave the full name as {a}. In the register, {short} appears beside an address in {place}.",
        "{a} worked for {org} during the period covered by the inquiry. {b} lived in {place}.",
        "The summary records that {b} saw {short} at {place}. The previous page identifies {short} as {a}.",
    ),
    (
        "On a separate page, the desk officer identifies {a} and {b} as the people listed in the file. Both attended the briefing at {place}.",
        "{a} received a voicemail from {b}. {org} filed the recording at the end of the week.",
        "The scanned ledger carries the name {a} under the heading for {org}. The second column shows {place}.",
        "{b} met Ms. {a} outside the building. The caller later described {short} as the duty supervisor.",
        "The label reads {org}; the recipient line names {b}. The package never reached {place}.",
        "{short} was listed twice under the full name {a}. Another record names {b} as a separate contact.",
    ),
    (
        "The cover sheet shows {place} as the interview location. {a} signed on the first line and {b} signed below.",
        "{b} denied calling {a} that week. The note was sent to {org} for review.",
        "{org} identified {a} as a driver. {b} is mentioned elsewhere in connection with a different delivery.",
        "{short}, whose full name is {a}, picked up a file from the reception desk in {place}.",
        "According to the gate log, {a} spoke with {b} at {place}. The recording is filed under {org}.",
        "On the phone, {b} asked to speak to {short}. The office roster expands that name to {a}.",
    ),
]

DEV_PATTERNS = (
    "Under the entry headed {place}, the register identifies {b} as the caller and {a} as the recipient.",
    "A member of {org} told the clerk that {a} and {b} used different entrances.",
    "The statement uses {short} for {a} throughout. It mentions a stop at {place} on the last page.",
    "The message reached {b} after noon. Its sender, {a}, was using an account at {org}.",
    "Two witnesses give different accounts of whether {b} spoke to {a} in {place}.",
    "The receiving officer put {org} on the delivery label. The package had previously been signed for by {a} in {place}.",
)

LABELS = {"a": "PERSON", "b": "PERSON", "org": "ORG", "place": "GPE", "short": "PERSON"}


def annotated_reports(cases, split):
    for case_number, case in enumerate(cases, 1):
        names = dict(zip(LABELS, case, strict=True))
        patterns = DEV_PATTERNS if split == "dev" else TRAIN_PATTERNS[(case_number - 1) % len(TRAIN_PATTERNS)]
        for report_number, pattern in enumerate(patterns, 1):
            text, entities = "", []
            for literal, field, _, _ in Formatter().parse(pattern):
                text += literal
                if field is not None:
                    name = names[field]
                    entities.append([len(text), len(text) + len(name), LABELS[field]])
                    text += name
            yield dict(id=f"{split}-{case_number:02d}-{report_number:02d}",
                       case=f"{split}-{case_number:02d}", text=text, entities=entities)


def prepare(output):
    output.mkdir(parents=True, exist_ok=True)
    nlp = spacy.load("en_core_web_sm", exclude=["tok2vec", "tagger", "parser",
                                               "senter", "attribute_ruler", "lemmatizer", "ner"])
    for split, cases in (("train", TRAIN_CASES), ("dev", DEV_CASES)):
        reports = list(annotated_reports(cases, split))
        serialized = DocBin()
        for report in reports:
            doc = nlp.make_doc(report["text"])
            spans = [doc.char_span(start, end, label=label, alignment_mode="strict")
                     for start, end, label in report["entities"]]
            if any(span is None for span in spans):
                raise ValueError(f"Token boundary mismatch in {report['id']}")
            doc.ents = spans
            serialized.add(doc)
        serialized.to_disk(output / f"{split}.spacy")
        data = "".join(json.dumps(report, ensure_ascii=False) + "\n" for report in reports)
        (output / f"{split}.jsonl").write_text(data, encoding="utf-8")
        print(f"{split}: {len(reports)} reports, {len(cases)} cases, "
              f"{sum(len(r['entities']) for r in reports)} annotations, "
              f"SHA-256 {hashlib.sha256(data.encode()).hexdigest()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("training/data"))
    prepare(parser.parse_args().output)
