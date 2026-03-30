import pdfplumber
from collections import defaultdict


DOMAIN_KEYWORDS = {
    "Financial": [
        "interest rate", "loan", "repayment", "covenant", "default", "credit",
        "lender", "borrower", "collateral", "debt", "payment schedule", "fee",
        "principal", "maturity", "financial statement", "balance sheet",
    ],
    "Construction": [
        "contractor", "subcontractor", "scope of work", "milestone", "completion",
        "materials", "specifications", "site", "construction", "delay", "penalty",
        "project schedule", "drawings", "architect", "engineering", "build",
    ],
    "Real Estate": [
        "property", "lease", "tenant", "landlord", "rent", "mortgage",
        "deed", "title", "zoning", "square feet", "premises", "occupancy",
        "real estate", "purchase price", "closing", "escrow",
    ],
    "Investment": [
        "investor", "fund", "equity", "irr", "return", "portfolio", "exit",
        "valuation", "shares", "capital", "term sheet", "preferred stock",
        "investment", "risk factor", "profit", "distribution",
    ],
    "Legal": [
        "indemnification", "liability", "governing law", "arbitration", "jurisdiction",
        "confidentiality", "non-disclosure", "intellectual property", "warranty",
        "breach", "remedy", "termination", "force majeure", "agreement",
    ],
}


def detect_domain(pdf_path: str) -> str:
    """
    Reads the first 3 pages of a PDF and scores keyword matches
    to determine the most likely domain.
    """
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[:3]:
            t = page.extract_text()
            if t:
                text += t.lower()

    scores = defaultdict(int)
    for domain, keywords in DOMAIN_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text:
                scores[domain] += 1

    if not scores or max(scores.values()) == 0:
        return "General"

    return max(scores, key=scores.get)