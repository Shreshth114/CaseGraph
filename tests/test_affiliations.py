"""End-to-end affiliation checks using fictional people and organisations."""
import unittest

from analysis_engine import extract

# Reference endpoints are exact source mentions. Each report stands alone.
CASES = [
    ("The annual return shows Lina Beran is listed as the secretary of Anchorlight Council.",
     "Lina Beran", "Anchorlight Council", "Directly reported"),
    ("The staff roll names Ravi Merton as an employee of Asterhill Press.",
     "Ravi Merton", "Asterhill Press", "Directly reported"),
    ("Klara Miro may be on the payroll of Ember Lane Logistics.",
     "Klara Miro", "Ember Lane Logistics", "Unverified claim"),
    ("The payroll register at Kestrel Freight lists Enid Goss as a dispatcher.",
     "Enid Goss", "Kestrel Freight", "Directly reported"),
    ("Safiya Melin has never been a member of Fernhill Council.",
     "Safiya Melin", "Fernhill Council", "Denied"),
    ("The personnel list identifies Noemi Ravel as a technician for Amber Spool Staging.",
     "Noemi Ravel", "Amber Spool Staging", "Directly reported"),
    ("Cara Vitale was employed by Tall Finch Hydraulics.",
     "Cara Vitale", "Tall Finch Hydraulics", "Directly reported"),
]
NEGATIVES = [
    "The register lists Enid Goss as a visitor at Kestrel Freight.",
    "The personnel list names Ravi Merton as a possible future employee of Asterhill Press.",
    "Klara Miro applied to be on the payroll of Ember Lane Logistics.",
    "Lina Beran delivered papers to the secretary of Anchorlight Council.",
    "The payroll register at Kestrel Freight lists Enid Goss as the driver of a visiting van.",
    "Cara Vitale was employed by David Rowan.",  # An individual employer, outside PERSON → ORG.
    "The payroll register at Kestrel Freight lists Enid Goss as a driver for another company.",
]


class AffiliationTests(unittest.TestCase):
    def test_claim_direction_status_and_evidence(self):
        for text, person, org, status in CASES:
            with self.subTest(text=text):
                claims = extract(dict(id="affiliation", text=text))[1]
                self.assertEqual([(c["source"], c["target"], c["type"], c["status"], c["sentence"])
                                  for c in claims], [(text.index(person), text.index(org), "Association", status, text)])

    def test_lookalikes(self):
        for text in NEGATIVES:
            with self.subTest(text=text):
                self.assertFalse(extract(dict(id="lookalike", text=text))[1])
