from langchain_community.vectorstores import FAISS
from embeddings import embeddings
import os

FOLDER = os.path.dirname(os.path.abspath(__file__))
FAQ_FILE = os.path.join(FOLDER, "faq_data.md")
DB_FOLDER = os.path.join(FOLDER, "faiss_db")


def clean_question(line):
    """Tidy up a question heading.

    Our FAQ file writes headings as "## Question: Kenapa ...". The words
    "Question:" are just a label, not part of the question, so we remove them.
    Left in, every entry would start with the same word and that only makes
    the entries look more alike to the search.
    """
    question = line.strip()
    for prefix in ("Question:", "Soalan:", "Q:"):
        if question.lower().startswith(prefix.lower()):
            question = question[len(prefix):].strip()
            break
    return question


def load_faq(file_path):
    """Split the FAQ file into a list of question + answer texts.

    Every question in the file starts with '## ', so we split on that instead
    of cutting the text into fixed-size pieces. Keeping each question together
    with its own answer gives much better search results, because the user's
    question looks like the FAQ question.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    blocks = ("\n" + text).split("\n## ")

    faqs = []
    for block in blocks[1:]:
        block = block.strip()
        if not block:
            continue

        parts = block.split("\n", 1)
        if len(parts) < 2:
            continue

        question = clean_question(parts[0])
        answer = parts[1].strip()
        if question and answer:
            faqs.append("Soalan: " + question + "\nJawapan: " + answer)

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

    print("Asking Gemini to turn them into vectors...")
    db = FAISS.from_texts(faqs, embedding=embeddings)
    db.save_local(DB_FOLDER)

    print("Saved database to the '" + DB_FOLDER + "' folder")


if __name__ == "__main__":
    build_database()
    print("Now run:  streamlit run app.py")
