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

If you get an **SSL certificate error**, see Troubleshooting at the bottom.

**3. Add your API key**

Make a copy of `.env.example`, rename the copy to `.env`, and put your Gemini
key inside:

```
GEMINI_API_KEY=your-key-here
```

The `.env` file is listed in `.gitignore`, so it will not be uploaded to GitHub.

**4. Build the search database**

```powershell
python ingest.py
```

This reads `faq_data.md`, asks Gemini to turn each question and answer into a
vector, and saves them into a `faiss_db` folder. It only takes a few seconds
for 7 entries.

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

### Why Gemini embeddings and not a downloaded model

Most RAG tutorials use `all-MiniLM-L6-v2` from Hugging Face. That model is
trained on **English only**. Our FAQ is in Malay, so it would match Malay
questions badly — a customer asking *"macam mana nak batal langganan"* would
often get the wrong FAQ entry back.

`gemini-embedding-001` supports over 100 languages including Malay, and it
matches **across** languages, so an English question still finds the right
Malay answer. `test_english_questions_find_the_malay_faq` checks exactly that.

It also keeps the project small: no `torch`, no `sentence-transformers`, no
500MB download. That matters for the deployed version, which has to run on a
small free server.

### Step 1 - Guardrails

`is_blocked()` checks the question against a short list of phrases in both
Malay and English, like *"ignore all previous instructions"*, *"abaikan
arahan"* and *"what is your api key"*. If one matches, we reply with a polite
refusal and never call Gemini.

The list is short on purpose. A longer list would start blocking real customer
questions, and a support bot that refuses genuine customers is worse than one
that occasionally answers a silly question. `test_normal_questions_are_not_blocked`
checks we do not over-block.

### Step 2 - Searching the FAQ

`ingest.py` keeps **each question together with its own answer** as one entry,
instead of chopping the whole document into fixed-size pieces.

This matters a lot. If you cut the text into 1000-character blocks, the long
cancellation answer would get split away from the question it belongs to, and
the piece holding the actual steps would no longer look anything like what the
user typed. Because the user types a *question*, keeping the FAQ *question* in
each entry makes the match far more accurate.

`clean_question()` also strips the `Question:` label from the headings. Left
in, all 7 entries would start with the same word, which only makes them look
more alike to the search.

### Step 3 - The "I don't know" cut-off

The search **always** returns something, even for nonsense like *"apakah ibu
negara perancis"*. Without a cut-off, Gemini would get three unrelated FAQ
entries and confidently invent an answer from them.

So we check the distance score first. FAISS gives a distance where **smaller
means more similar**. If even the closest FAQ entry is further away than
`MAX_DISTANCE`, we reply "Maaf, maklumat itu tiada dalam FAQ kami" and never
call Gemini at all. That also saves API quota.

**You must tune this number:**

```powershell
python check_threshold.py
```

It prints the real distances for genuine questions and for off-topic ones, and
suggests a value to put in `chatbot.py`. The value in the file now is a
starting guess, not a measured one.

### Step 4 - Asking Gemini

`ask_gemini()` sends a POST request to the Gemini API using the `requests`
library, as the assessment asks.

Three details worth knowing:

- **The API key goes in a header** (`x-goog-api-key`), not in the web address.
  Keys in the address end up in server logs and browser history.
- **Thinking is turned off** (`"thinkingBudget": 0`). Gemini 2.5 thinks before
  answering by default. For answering from three short FAQ entries that just
  makes it slower, and the thinking can use up the whole output allowance and
  return an empty answer. We also skip any reply pieces marked `"thought"`,
  because those are Gemini's own notes and not the answer.
- **The prompt asks for the user's language.** The FAQ is Malay, but an
  English question gets an English answer translated from the same FAQ entry.

When the FAQ does not cover the question, Gemini is told to reply with the
plain marker `NOT_IN_FAQ`, which the code swaps for a friendly message. Using
a marker instead of a sentence makes it reliable to detect no matter which
language the user typed in.

---

## Tests

```powershell
python ingest.py        # the database must exist first
pytest test_chatbot.py -v
```

The tests cover the bonus point in the assessment - checking that the chatbot
finds the **correct** FAQ entry:

- `test_chatbot_finds_the_correct_faq` - 13 questions worded differently from
  the FAQ (for example *"saya nak berhenti bayar tontonup"* should find the
  cancellation FAQ). They are worded differently on purpose. Testing
  *"Bagaimana saya nak menukar kata laluan?"* against the FAQ entry with the
  same words would only prove the words match, not that the search works.
- `test_best_result_is_usually_the_correct_one` - the right FAQ should be the
  *first* result at least 70% of the time.
- `test_english_questions_find_the_malay_faq` - cross-language matching.
- `test_off_topic_questions_are_refused` - questions the FAQ does not cover
  must fall outside the cut-off.
- `test_real_questions_are_not_refused` - the opposite check, so the cut-off is
  not so strict that it rejects genuine customers.
- Guardrail tests, tests that the FAQ file is read correctly, and tests that
  the FAQ text really does end up in the prompt sent to Gemini.

The search tests need the Gemini API, so they **skip automatically** if
`GEMINI_API_KEY` is not set. The rest run either way.

---

## Putting it on GitHub

```powershell
git init
git add .
git commit -m "Tonton FAQ chatbot"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
git push -u origin main
```

Check the key is not going up before you push:

```powershell
git status
```

`.env` must **not** appear in that list. `.env.example` is fine — it is the
template with no real key in it.

---

## Deploying to Streamlit Cloud

1. Push to GitHub using the steps above.
2. Go to https://share.streamlit.io and create a new app pointing at `app.py`.
   If the project sits in a subfolder of your repo, set the main file path to
   `faq-chatbot/app.py`.
3. In **Settings -> Secrets**, add:
   ```
   GEMINI_API_KEY = "your-key"
   ```
4. Click Deploy.

You do **not** need to upload the `faiss_db` folder. If the database is
missing, `chatbot.py` builds it automatically on the first question using the
key from Secrets. With only 7 entries that takes a few seconds.

---

## Troubleshooting

### "SSL: CERTIFICATE_VERIFY_FAILED - self signed certificate in certificate chain"

Something on your network or PC (a company proxy, or antivirus like Kaspersky
or ESET) is opening your HTTPS traffic and re-signing it with its own
certificate. Python does not trust that certificate, so it refuses to connect.

This breaks both `pip install` and the calls to the Gemini API.

**The fix that covers both** - make Python use the Windows certificate store,
which already trusts your company's certificate:

```powershell
pip install pip-system-certs --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

**If only pip needs fixing**, add the trusted hosts each time:

```powershell
pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

Note this only helps pip. It does **not** help the Gemini API calls.

**Easiest option of all:** run this project on a personal network - home wifi
or a phone hotspot - instead of the company network.

### "WinError 5: Access is denied"

You are installing into the system-wide Python. Use a virtual environment
instead (step 1 above) and this goes away.

**Do not run `pip install --upgrade pip`.** It is not needed, and on a
system-wide Python it can uninstall pip and then fail to replace it. If that
already happened, put pip back with `python -m ensurepip --upgrade`.

### "GEMINI_API_KEY is not set"

Copy `.env.example` to `.env` and put your key in it. On Streamlit Cloud, add
it under Settings -> Secrets instead.

### The chatbot refuses real questions, or answers off-topic ones

The `MAX_DISTANCE` cut-off in `chatbot.py` is wrong for your data. Run
`python check_threshold.py` and use the number it suggests.
