import os
from groq import Groq
from langchain_community.vectorstores import FAISS


client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "llama-3.1-8b-instant"


def _query_groq(system_prompt: str, user_prompt: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=512,
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()


def ask_question(vectorstore, question: str, chat_history: list) -> str:
    # Retrieve relevant chunks from vectorstore
    docs = vectorstore.similarity_search(question, k=4)
    context = "\n\n".join([d.page_content for d in docs])

    system = """You are a friendly document assistant.
- Answer ONLY based on the document context provided to you.
- Use plain, simple English — like explaining to a non-expert friend.
- If the answer is not found in the context, say exactly: "I couldn't find that in the document."
- Be concise, clear, and never make up information."""

    # Build conversation history
    history_text = ""
    for msg in chat_history[:-1]:
        role = "User" if msg["role"] == "user" else "Assistant"
        history_text += f"{role}: {msg['content']}\n"

    user = f"""Document context:
{context}

{history_text}
User question: {question}"""

    return _query_groq(system, user)