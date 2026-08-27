# FAQ Chatbot (RAG)

A chatbot that answers questions from an FAQ document.

It uses **RAG (Retrieval-Augmented Generation)**: instead of asking the AI to
answer from memory, we first search the FAQ for the entries that best match the
user's question, then give only those entries to Gemini and ask it to answer
from them. If the FAQ does not cover the question, the chatbot says so instead
of making something up.

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

If you get an **SSL certificate error**, see Troubleshooting at the bottom.

**3. Add your API key**

Make a copy of `.env.example`, rename the copy to `.env`, and put your Gemini
key inside:

```
GEMINI_API_KEY=your-key-here
```

The `.env` file is listed in `.gitignore`, so it will not be uploaded to GitHub.

**4. Build the search database**

```bash
python ingest.py
```

This reads `faq_data.md`, turns each question and answer into numbers
(vectors), and saves them into a `faiss_db` folder. You only need to do this
once, or again whenever you change the FAQ. The first run downloads a small
model (about 80MB).

**5. Start the chatbot**

```bash
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

---

## The files

| File | What it does |
|---|---|
| `faq_data.md` | The FAQ. Every question starts with `## `. |
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
"I don't have         4. Send the FAQ entries + question to Gemini
 that in the FAQ"        (chatbot.py -> ask_gemini)
 (no API call)             |
                           v
                        Show the answer + the FAQ entries used
```

### Step 1 - Guardrails

`is_blocked()` checks the question against a short list of phrases like
"ignore all previous instructions" and "what is your api key". If one matches,
we reply with a polite refusal and never call Gemini.

The list is short on purpose. A longer list would start blocking real customer
questions, and a support bot that refuses genuine customers is worse than one
that occasionally answers a silly question. `test_chatbot.py` has a test
(`test_normal_questions_are_not_blocked`) that checks we do not over-block.

### Step 2 - Searching the FAQ

`ingest.py` keeps **each question together with its own answer** as one entry,
instead of chopping the whole document into fixed-size pieces.

This matters a lot. If you cut the text into 1000-character blocks, an answer
can get separated from the question it belongs to, and the piece holding the
real information no longer looks anything like what the user typed. Because the
user types a *question*, keeping the FAQ *question* in each entry makes the
match far more accurate.

### Step 3 - The "I don't know" cut-off

The search **always** returns something, even for nonsense like "what is the
capital of France". Without a cut-off, Gemini would get four unrelated FAQ
entries and confidently invent an answer from them.

So we check the distance score first. FAISS gives a distance where **smaller
means more similar**. If even the closest FAQ entry is further away than
`MAX_DISTANCE`, we reply "I don't have that in the FAQ" and never call Gemini
at all. That also saves API quota.

**You should tune this number for your FAQ:**

```bash
python check_threshold.py
```

It prints the real distances for genuine questions and for off-topic ones, and
suggests a value to put in `chatbot.py`.

### Step 4 - Asking Gemini

`ask_gemini()` sends a POST request to the Gemini API using the `requests`
library, as the assessment asks.

Two details worth knowing:

- **The API key goes in a header** (`x-goog-api-key`), not in the web address.
  Keys in the address end up in server logs and browser history.
- **Thinking is turned off** (`"thinkingBudget": 0`). Gemini 2.5 thinks before
  answering by default. For answering from four short FAQ entries that just
  makes it slower, and the thinking can use up the whole output allowance and
  return an empty answer. We also skip any reply pieces marked `"thought"`,
  because those are Gemini's own notes and not the answer.

The prompt tells Gemini to use only the FAQ entries given, and gives it an exact
sentence to use when it does not know. Giving the model a specific way to say
"I don't know" makes it much less likely to invent something.

---

## Tests

```bash
python ingest.py        # the database must exist first
pytest test_chatbot.py -v
```

The tests cover the bonus point in the assessment - checking that the chatbot
finds the **correct** FAQ entry:

- `test_chatbot_finds_the_correct_faq` - 15 questions worded differently from
  the FAQ (for example "i want my money back" should find the refund FAQ). They
  are worded differently on purpose. Testing "How do I reset my password?"
  against the FAQ entry "How do I reset my password?" would only prove the words
  match, not that the search works.
- `test_best_result_is_usually_the_correct_one` - the right FAQ should be the
  *first* result at least 70% of the time.
- `test_off_topic_questions_are_refused` - questions the FAQ does not cover must
  fall outside the cut-off.
- `test_real_questions_are_not_refused` - the opposite check, so the cut-off is
  not so strict that it rejects genuine customers.
- Guardrail tests, and tests that the FAQ text really does end up in the prompt
  sent to Gemini.

---

## Before submitting - two things to do

**1. Replace the FAQ.**
`faq_data.md` is a placeholder. The assessment PDF links to an FAQ
(`<FAQ LINK>`) that was not included in the file, so this stands in so
everything runs. Replace it with the real FAQ, keeping the same format (every
question starts with `## `), then run `python ingest.py` again and update the
questions in `SEARCH_TESTS` inside `test_chatbot.py`.

**2. Use your own API key.**
The key printed in the assessment PDF has been shared in a document, so treat it
as public. Get a fresh one from Google AI Studio and put it in `.env`.

---

## Deploying to Streamlit Cloud

1. Push this folder to GitHub.
2. Go to share.streamlit.io and create a new app pointing at `app.py`.
3. In **Settings -> Secrets**, add:
   ```
   GEMINI_API_KEY = "your-key"
   ```
4. The `faiss_db` folder is in `.gitignore`, so it will not be uploaded. Either
   remove that line so the database is included in the repo, or delete
   `faiss_db/` from `.gitignore` before pushing.

---

## Troubleshooting

### "SSL: CERTIFICATE_VERIFY_FAILED - self signed certificate in certificate chain"

Something on your network or PC (a company proxy, or antivirus like Kaspersky
or ESET) is opening your HTTPS traffic and re-signing it with its own
certificate. Python does not trust that certificate, so it refuses to connect.

This will break **three** things, not just pip:

1. `pip install`
2. `python ingest.py`, which downloads the embedding model from Hugging Face
3. `chatbot.py`, which calls the Gemini API with `requests`

**The fix that covers all three** - make Python use the Windows certificate
store, which already trusts your company's certificate:

```powershell
pip install pip-system-certs --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

After that, normal `pip install -r requirements.txt` should work, and so should
the model download and the Gemini calls.

**If only pip needs fixing**, you can add the trusted hosts each time:

```powershell
pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

But note this only helps pip. It does **not** help Hugging Face or Gemini.

**Easiest option of all:** run this project on a personal network - home wifi or
a phone hotspot - instead of the company network. Most corporate certificate
inspection disappears and everything works normally.

### "WinError 5: Access is denied"

You are installing into the system-wide Python. Use a virtual environment
instead (step 1 above) and this goes away.

**Do not run `pip install --upgrade pip`.** It is not needed for this project,
and on a system-wide Python install it can uninstall pip and then fail to
replace it, leaving you with no pip at all.

If that already happened, put pip back with:

```powershell
python -m ensurepip --upgrade
```

### "Database not found. Please run 'python ingest.py' first."

You started the chatbot before building the search database. Run
`python ingest.py`, then start it again.

### The chatbot says "I don't have that in the FAQ" for real questions

The `MAX_DISTANCE` cut-off in `chatbot.py` is too strict. Run
`python check_threshold.py` and use the number it suggests.
