import os
from groq import Groq


client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "llama-3.1-8b-instant"


DOMAIN_PROMPTS = {
    "Financial": {
        "Payment & Fee Terms": "What are the payment amounts, schedules, fees, or interest rates mentioned?",
        "Default & Penalties": "What happens if someone fails to pay or breaches the agreement?",
        "Key Covenants": "What are the main rules or obligations both parties must follow?",
        "Termination Conditions": "Under what conditions can this agreement be ended?",
    },
    "Construction": {
        "Scope of Work": "What work or tasks are described in this document?",
        "Project Timeline & Milestones": "What are the deadlines, milestones, or completion dates?",
        "Penalty & Delay Clauses": "What happens if work is delayed or not done properly?",
        "Materials & Specifications": "What materials, standards, or technical specs are mentioned?",
    },
    "Real Estate": {
        "Property Details": "What property is described — address, size, type?",
        "Price & Payment Terms": "What is the price, deposit, and how payments are structured?",
        "Lease / Tenancy Terms": "What are the rental period, rent amount, and renewal conditions?",
        "Restrictions & Obligations": "What are the buyer/seller/tenant obligations or property restrictions?",
    },
    "Investment": {
        "Investment Terms": "What are the investment amount, equity stake, or fund terms?",
        "Returns & Projections": "What financial returns, IRR, or profit projections are mentioned?",
        "Risk Factors": "What risks are mentioned in this document?",
        "Exit Strategy": "What are the exit options or conditions for investors?",
    },
    "Legal": {
        "Parties Involved": "Who are the parties to this agreement and what are their roles?",
        "Key Obligations": "What must each party do under this agreement?",
        "Indemnification": "Who is responsible if something goes wrong or causes loss?",
        "Governing Law & Disputes": "Which laws govern this document and how are disputes resolved?",
    },
    "General": {
        "Main Purpose": "What is the main purpose of this document?",
        "Key Parties": "Who is involved in this document and what are their roles?",
        "Important Terms": "What are the most important terms or conditions?",
        "Dates & Deadlines": "What important dates or deadlines are mentioned?",
    },
}


def extract_key_info(vectorstore, domain: str) -> dict:
    """
    Runs domain-specific questions against the vectorstore
    and returns plain English answers using Groq LLaMA3.
    """
    prompts = DOMAIN_PROMPTS.get(domain, DOMAIN_PROMPTS["General"])
    results = {}

    system = """You are a helpful document analyst.
- Answer ONLY from the document context provided.
- Use plain, simple English — no legal or technical jargon.
- If the information is not in the context, say exactly: "Not mentioned in this document."
- Keep answers to 3-5 sentences maximum.
- Never make up or assume information."""

    for section, question in prompts.items():
        docs = vectorstore.similarity_search(question, k=3)
        context = "\n\n".join([d.page_content for d in docs])

        user = f"""Document context:
{context}

Question: {question}

Answer in plain simple English:"""

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=300,
            temperature=0.1,
        )
        results[section] = response.choices[0].message.content.strip()

    return results