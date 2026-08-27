# Turns text into vectors (lists of numbers) using the Gemini embedding API.
#
# Why Gemini instead of a downloaded model:
#   1. Our FAQ is in Malay. The popular small models like all-MiniLM-L6-v2 are
#      trained on English only, so they match Malay questions badly.
#      gemini-embedding-001 supports over 100 languages, Malay included.
#   2. Nothing to download. No torch, no sentence-transformers. That keeps
#      installing simple and keeps the deployed app small enough to run on a
#      free Streamlit Cloud server.
#
# Cost is tiny: 7 calls once when building the database, then 1 call per
# question a user asks.

from langchain_core.embeddings import Embeddings
from dotenv import load_dotenv
import requests
import json
import os
import math

load_dotenv()

EMBED_MODEL = "gemini-embedding-001"
EMBED_URL = "https://generativelanguage.googleapis.com/v1beta/models/" + EMBED_MODEL + ":embedContent"

# The full model gives 3072 numbers per text. We ask for 768 instead - just as
# accurate for a small FAQ, and it keeps the database file small.
EMBED_SIZE = 768


def normalise(vector):
    """Scale a vector so its length is exactly 1.

    Gemini only normalises automatically at the full 3072 size, so we do it
    ourselves. It matters: FAISS measures distance, and without this the
    distances would depend on text length instead of meaning.
    """
    length = math.sqrt(sum(value * value for value in vector))
    if length == 0:
        return vector
    return [value / length for value in vector]


def embed_one(text, task_type):
    """Send one piece of text to Gemini and get its vector back.

    task_type tells Gemini how the text will be used:
      RETRIEVAL_DOCUMENT - text we are storing in the database
      RETRIEVAL_QUERY    - a question someone is asking
    Using the right one on each side noticeably improves the matching.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise Exception(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and put your key in it."
        )

    headers = {
        "Content-Type": "application/json",
        # The key goes in a header, not in the web address, so it does not
        # end up in server logs.
        "x-goog-api-key": api_key,
    }

    data = {
        "model": "models/" + EMBED_MODEL,
        "content": {"parts": [{"text": text}]},
        "taskType": task_type,
        "outputDimensionality": EMBED_SIZE,
    }

    response = requests.post(EMBED_URL, headers=headers, data=json.dumps(data), timeout=30)

    if response.status_code != 200:
        raise Exception(
            "Gemini embedding failed (HTTP " + str(response.status_code) + "): "
            + response.text[:300]
        )

    values = response.json()["embedding"]["values"]
    return normalise(values)


class GeminiEmbeddings(Embeddings):
    """Small wrapper so LangChain's FAISS can use the Gemini API.

    LangChain only needs these two methods.
    """

    def embed_documents(self, texts):
        """Vectors for the FAQ entries we are storing."""
        vectors = []
        for number, text in enumerate(texts, start=1):
            print("  embedding " + str(number) + "/" + str(len(texts)))
            vectors.append(embed_one(text, "RETRIEVAL_DOCUMENT"))
        return vectors

    def embed_query(self, text):
        """Vector for a question the user just typed."""
        return embed_one(text, "RETRIEVAL_QUERY")


# One shared instance, used by both ingest.py and chatbot.py.
# They MUST use the same one - a database built with one model cannot be
# searched with another.
embeddings = GeminiEmbeddings()
