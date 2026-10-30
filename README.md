# Remote Healthcare Platform

A telehealth triage prototype for rural and underserved communities in India. A patient or community health worker describes symptoms in English, Hindi or Kannada. The app screens the message for emergencies, retrieves relevant guidance from a small knowledge base, and uses an LLM (Groq) to produce a structured triage note for a clinician.

This is a prototype built on synthetic data. It is not a medical device and must not be used for real patients.

## How triage works

```
message ──> emergency screen ──┬── emergency ──> "call 112 / 108" message, stop
             (rules, then LLM)  │
                                └── not emergency ──> retrieve top 3 knowledge entries
                                                        ──> LLM triage (JSON) with citations
```

1. Emergency screen (`ai/safety.py`). Regex rules in English, Hindi and Kannada, in native script and romanized form, grouped by category: cardiac, breathing, neurological, bleeding, poisoning, self-harm, injury, bites, allergy, pregnancy, and WHO IMCI danger signs in children. It handles negation, so "no chest pain" and "सीने में दर्द नहीं है" are not flagged while "can't breathe" is. If the rules find nothing, a Groq classifier gets a second look. The LLM can only escalate. It is never asked about messages the rules flagged, and if it is unavailable the rules result stands.
2. Retrieval (`ai/rag.py`). The 27 entries in `knowledge/` are embedded with `intfloat/multilingual-e5-small` and stored in a ChromaDB collection under `data/vectorstore/`. The index rebuilds itself when the knowledge files or the model change. Emergencies skip retrieval, so no first-aid text for the wrong condition appears next to the emergency message.
3. Triage (`ai/triage.py`). The LLM gets the message and the retrieved entries, replies in JSON mode, and lists the topics it used. Citations that were not in the retrieved set are dropped.

## Evaluation

### Emergency screen

`ai/evaluation/cases.json` has 85 labelled messages: 52 emergencies and 33 non-emergencies across English, Hindi, Kannada, and romanized Hindi and Kannada. It includes negation traps, an education question, a past event, and three emergencies described with no keyword at all.

Rules only (`python -m ai.evaluation.run`):

| Screen | Precision | Recall | F1 | Missed | False alarms |
|---|---|---|---|---|---|
| Original 17-phrase substring match | 0.727 | 0.154 | 0.254 | 44 | 3 |
| Current rules | 0.961 | 0.942 | 0.951 | 3 | 2 |

The three misses are the no-keyword cases (signs of shock, chest indrawing described in plain words, severe dehydration). They are what the LLM check is for; run `python -m ai.evaluation.run --llm` with a Groq key to measure the combined screen. The two false alarms are "What are the warning signs of a heart attack?" and a heart attack mentioned as a past event. The LLM cannot clear these, by design.

The cases were written alongside the rules, so these numbers are in-sample and optimistic. A held-out set written by someone else would give a fairer estimate.

### Retrieval

`ai/evaluation/retrieval_cases.json` has 24 queries in English, Hindi and Kannada with the knowledge entries that should come back. Run `python -m ai.evaluation.retrieval` to get hit@1, hit@3 and mean reciprocal rank; the report is saved to `ai/evaluation/results/retrieval.json`.

## Running it

You need Python 3.12 and, for the web frontend, Node 20.

```bash
git clone https://github.com/meghana1186/Remote-Healthcare-Platform.git
cd Remote-Healthcare-Platform
python -m venv .venv
.venv\Scripts\activate          # Windows; on macOS or Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # macOS or Linux: cp .env.example .env
```

Put your Groq API key in `.env`. Without a key the app still runs: the emergency rules and retrieval work, and the LLM steps return a placeholder reply.

The first run downloads the embedding model (about 470 MB). To build the index and try a query:

```bash
python -m ai.rag "fever with chills since two days"
```

### Streamlit app

```bash
streamlit run app.py
```

### FastAPI backend and Next.js frontend

```bash
uvicorn backend.app.main:app --reload --port 8000     # from the project root
cd frontend && npm install && npm run dev               # in a second terminal
```

Open http://localhost:3000. API docs are at http://localhost:8000/docs.

### Docker

```bash
docker compose up --build
```

This starts the frontend, API, Postgres and Redis. Compose passes `.env` to the containers; it is not copied into the image.

## Tests

```bash
pip install pytest httpx
python -m pytest
```

53 tests cover the emergency rules, negation in all three languages, the LLM escalation logic (with the LLM mocked), the evaluation recall floor, the retrieval index and its wiring into triage (with a small offline embedder), and the dashboard metrics. They run without network access or an API key.

## Project structure

```
ai/
  safety.py            emergency screen: rules plus LLM second check
  rag.py               embeddings, ChromaDB index, retrieval
  triage.py            screen, retrieve, LLM triage
  groq_client.py       Groq chat, JSON mode, emergency classifier, Whisper
  prompts.py
  evaluation/          labelled cases, eval scripts, saved results
backend/app/           FastAPI: /api/v1/triage, /api/v1/demo/*
frontend/              Next.js patient interface
app.py                 Streamlit interface with all pages
knowledge/             27 guidance entries with sources (see knowledge/sources.md)
services/metrics.py    dashboard numbers computed from data/
data/                  synthetic seed data (see data/README.md)
tests/
```

## Not built yet

These exist as models or stubs but are not wired up:

- Authentication and roles. `backend/app/core/security.py` can hash passwords and create JWTs, but no endpoint requires a token.
- Audit logging. The tables exist; nothing writes to them.
- Follow-up notifications. `workers/tasks.py` has one Celery task that nothing calls.
- The Next.js Overview, Appointments, Health Record and Referrals pages show static example content.
- Report analysis is a single LLM call with no extraction or checks.

## Limitations

- The rules do not tell current symptoms from past ones ("had chest pain last year" is flagged).
- Tamil, Telugu and Marathi appear in the language menu, but the emergency rules cover only English, Hindi and Kannada. Messages in other languages rely on the LLM check alone.
- The knowledge base is short, paraphrased, and not reviewed by a clinician.

## Data and sources

All patient, clinician and activity data in `data/` is synthetic. Knowledge entries cite their sources, mainly WHO fact sheets and guidelines, IFRC first-aid guidelines, India's National Tuberculosis Elimination Programme, and Tele-MANAS.
