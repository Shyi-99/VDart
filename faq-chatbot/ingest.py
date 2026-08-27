# Reads the FAQ file, splits it into question/answer pairs,
# turns them into vectors and saves them to a local FAISS database.
#
# Run this once before starting the chatbot:
#     python ingest.py

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import os

FAQ_FILE = "faq_data.md"
DB_FOLDER = "faiss_db"

# The embedding model. Runs on your own computer, so it costs nothing
# and does not use up the Gemini quota.
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    encode_kwargs={"normalize_embeddings": True},
)


def load_faq(file_path):
    """Split the FAQ file into a list of question + answer texts.

    The file uses '## ' in front of every question, so we can just
    split on that instead of cutting the text into fixed-size pieces.
    Keeping each question with its own answer gives much better search
    results, because the user's question looks like the FAQ question.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Split on "## " only when it is at the start of a line, so a "## "
    # that happens to appear inside an answer is not mistaken for a question.
    # The extra "\n" at the front makes the first question split correctly too.
    blocks = ("\n" + text).split("\n## ")

    faqs = []
    # blocks[0] is the file title / any notes before the first question, so skip it
    for block in blocks[1:]:
        block = block.strip()
        if not block:
            continue

        # First line is the question, the rest is the answer.
        parts = block.split("\n", 1)
        if len(parts) < 2:
            continue

        question = parts[0].strip()
        answer = parts[1].strip()
        if question and answer:
            faqs.append("Question: " + question + "\nAnswer: " + answer)

    return faqs


def build_database():
    """Create the FAISS database from the FAQ file."""
    if not os.path.exists(FAQ_FILE):
        print("Cannot find " + FAQ_FILE)
        return

    faqs = load_faq(FAQ_FILE)
    print("Found " + str(len(faqs)) + " FAQ entries")

    if len(faqs) == 0:
        print("No FAQ entries found. Check that every question starts with '## '")
        return

    print("Creating vectors...")
    db = FAISS.from_texts(faqs, embedding=embeddings)
    db.save_local(DB_FOLDER)

    print("Saved database to the '" + DB_FOLDER + "' folder")
    print("Now run:  streamlit run app.py")


if __name__ == "__main__":
    build_database()
