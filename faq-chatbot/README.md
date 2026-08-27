# Tonton FAQ Chatbot (RAG)

A chatbot that answers customer questions from the Tonton FAQ.

It uses **RAG (Retrieval-Augmented Generation)**: instead of asking the AI to
answer from memory, we first search the FAQ for the entries that best match the
user's question, then give only those entries to Gemini and ask it to answer
from them. If the FAQ does not cover the question, the chatbot says so instead
of making something up.

The FAQ is in Malay, and customers can ask in **either Malay or English** — the
search matches across both.

---

## How to run it

Needs Python 3.10 or newer.

**1. Make a virtual environment**

This keeps the packages inside the project folder, so you never get
"Access is denied" errors from Windows.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

You should now see `(venv)` at the start of your prompt.

*(If PowerShell blocks the script, run
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first, then try again.)*

**2. Install the packages**

```powershell
pip install -r requirements.txt
```


**3. Add your API key**

Create an env file `.env`, and put your Gemini
key inside as below:

```
GEMINI_API_KEY=your-key-here
```

**4. Build the search database**

```powershell
python ingest.py
```

This reads `faq_data.md`, asks Gemini to turn each question and answer into a
vector, and saves them into a `faiss_db` folder. 

**5. Start the chatbot**

```powershell
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

---

## The files

| File | What it does |
|---|---|
| `faq_data.md` | The Tonton FAQ. Every question starts with `## `. |
| `embeddings.py` | Turns text into vectors using the Gemini embedding API. |
| `ingest.py` | Reads the FAQ and builds the search database. Run once. |
| `chatbot.py` | The main logic: search the FAQ, then ask Gemini. |
| `app.py` | The Streamlit web page. |
| `test_chatbot.py` | Automated tests. |
| `check_threshold.py` | Helper to tune the "I don't know" cut-off. |

---

## How it works

```
User question
      |
      v
1. Check for bad questions   (chatbot.py -> is_blocked)
      |
      v
2. Search the FAQ database   (chatbot.py -> search_faq)
      |
      v
3. Is the closest FAQ close enough?
      |                    |
     No                   Yes
      |                    |
      v                    v
"Maaf, maklumat itu   4. Send the FAQ entries + question to Gemini
 tiada dalam FAQ"        (chatbot.py -> ask_gemini)
 (no API call)             |
                           v
                        Show the answer + the FAQ entries used
```
