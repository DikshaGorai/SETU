# SETU — Societal Engagement & Technological Utilization

Smart India Hackathon 2026 · Problem statement **SIH26043** · Team **6ixTitans**

A digital platform where citizens, panchayats and urban local bodies raise real societal
problems in their own language, and the platform routes each one to the universities,
mentors and CSR partners that actually hold the capability to solve it — then tracks it
through to a verified outcome.

---

## Run it on your laptop

You need Python 3.9 or newer. Nothing else.

```bash
cd setu
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

pip install -r requirements.txt
python run.py
```

The browser opens at **http://127.0.0.1:8000** with a seeded database of five live
challenges from Andhra Pradesh districts.

Useful flags:

| Command | What it does |
|---|---|
| `python run.py` | Normal start |
| `python run.py --reset` | Wipe `setu.db` and reseed — run this right before you present |
| `python run.py --reload` | Auto-restart on code edits while you build |
| `python run.py --no-browser` | Don't open a browser tab |
| `HOST=0.0.0.0 python run.py` | Serve on your wifi so judges can open it on their phones at `http://<your-laptop-ip>:8000` |

If port 8000 is taken: `PORT=8080 python run.py`.

---

## Sign-in accounts

Password for all of them is `setu123`.

| Email | Role | Can do |
|---|---|---|
| `citizen@setu.in` | citizen | Raise and track challenges (Nadia, West Bengal) |
| `sahayak@setu.in` | citizen | Submit on behalf of someone who cannot type |
| `uni@setu.in` | university | Jadavpur University - accept challenges, move stages |
| `uni2@setu.in` | university | BIT Mesra, Ranchi - the Jharkhand side of the demo |
| `csr@setu.in` | csr | Hooghly Steel Foundation - commit funds |
| `csr2@setu.in` | csr | Chhotanagpur Mining CSR Board |
| `admin@setu.in` | admin | Everything, plus override the AI |

---

## Three-minute demo script

1. **Home** — the pipeline numbers and the seven-stage lifecycle. One line: *"a village names the
   problem, a university builds the answer, and this is the missing pipeline between them."*
2. **Raise a challenge** → pick Bengali → **Speak** (or **Load sample text** if the wifi is
   down) → Submit.
   The intake pipeline runs live: Bhashini intake, PII masked, dedupe, scope check,
   domain, priority score, three institutions ranked with the reason for each fit score,
   Schedule VII clause attached.
3. **Load a personal grievance → Submit.** The platform refuses it and forwards it to CPGRAMS.
   This is the strongest moment in the demo — it proves SETU does not degrade into a complaint
   portal, which is the first thing a judge will attack.
4. **Submit the borewell text again.** It merges into SETU-26-0001 as a supporter instead of
   opening a duplicate project.
5. **Sign in as `uni@setu.in`** → open a challenge → *Accept this challenge* → consortium forms,
   lifecycle advances, the action is written to the audit trail.
6. **Sign in as `csr@setu.in`** → commit ₹1 Cr against the clause shown on the page.
7. **Sign in as `admin@setu.in`** → *Human override*: correct the AI's domain and give a reason.
   The correction appears highlighted in the audit table.
8. **Dashboard** — funnel, equity audit by intake language, state and district spread, live
   decision log.

Two extra moments worth thirty seconds each:

- **The state rule.** Open SETU-26-0007 (arsenic and fluoride in Palamu). Birsa Agricultural
  University sits at the top at 71% even though IIT Kharagpur scored 76%, and the explanation
  says exactly why it was promoted. This is the answer to "is this just keyword matching?"
- **Filters.** On the marketplace, filter by state Jharkhand, then by district Dhanbad. Same
  platform, any state, without a code change.

---

## Coverage

- **West Bengal** and **Jharkhand**: every district, because that is the level a state
  innovation cell actually works at.
- **Every other state and union territory**: major cities, which is enough to show a national
  rollout without making the dropdown unusable.
- 25 institutions across the two focus states and the national pool, 7 CSR partners,
  12 seeded challenges spanning Nadia, South 24 Parganas, Howrah, Purulia, Purba Bardhaman,
  Palamu, Dhanbad, Khunti, Gumla, Mumbai and Bengaluru.
- Intake languages include Bengali, Hindi, Santali, Kurukh, Ho, Odia, Nepali, Urdu, Assamese,
  Telugu, Tamil, Marathi, Kannada and English.

### Adding or changing a place

Everything lives in **`app/locations.py`**. Add the name to the right state's list:

```python
    "Jharkhand": [
        "Bokaro", "Chatra", ..., "West Singhbhum", "New Place",
    ],
```

The submit form, the marketplace filters and the state dashboard all read from that one file,
and any challenge raised there is tagged with its state automatically. Restart to pick it up -
no database reset needed, because this list is not stored in the database.

To add an institution or a CSR partner, edit `INSTITUTIONS` or `PARTNERS` in `app/db.py`
and then run `python run.py --reset`, since seed data only loads into a fresh database.

## Project structure

```
setu/
├── run.py                 start script
├── requirements.txt
├── setu.db                created on first run (SQLite)
└── app/
    ├── main.py            FastAPI routes, sessions, JSON API
    ├── engine.py          the AI Problem Management Module
    ├── db.py              schema, seed data, queries
    ├── templates/         Jinja2 pages
    └── static/            css and js
```

---

## What the engine actually does

`app/engine.py` is the technical-approach slide in code. Each stage returns a decision **and**
a confidence score, and every decision is written to the `audit` table.

| Stage | Function | Current implementation |
|---|---|---|
| Voice & language intake | `normalise` | Stub for the Bhashini ASR/translate call |
| PII redaction | `redact_pii` | Regex over phone, ID and email patterns |
| Deduplicate & cluster | `find_duplicate` | `difflib` sequence ratio blended with token overlap |
| Scope classifier | `scope_classify` | Weighted grievance vs community markers |
| Domain classification | `classify_domain` | Keyword scoring across eight domains |
| Priority score | `priority_score` | severity × reach × equity, deliberately transparent |
| Capability routing | `route_capabilities` | Capability overlap, proximity, breadth, free capacity |
| CSR eligibility | `csr_match` | Domain → Schedule VII clause → partner focus areas |

### How a fit score is built

Out of 100 points, so no single factor can swamp the rest:

| Factor | Points | Why it counts |
|---|---|---|
| Capability depth | 0-65 | How much of the problem the institution actually covers |
| Proximity | 0-20 | Same district beats same state beats anywhere else |
| Multidisciplinary cover | 0-6 | More than one matching capability |
| Free capacity | 0-7.5 | Open project slots, so work does not pile on one campus |

On top of that sits the **keep-it-in-the-state rule**: if an institution from the same state is
within 8 points of an outside leader, it is promoted to the top and the promotion is written into
the explanation. A state innovation cell wants the work to stay in the state when capability is
comparable, and the ranking says so out loud instead of hiding it.

### Replacing the stub models

Each function takes text and returns a value — swap one at a time without touching the routes.

- **Bhashini**: replace `normalise()` with a call to the Bhashini ASR and translation endpoints.
- **Dedupe**: replace the `difflib` blend with sentence embeddings (`sentence-transformers`) and
  cosine similarity, or pgvector once you move to Postgres.
- **Scope classifier**: replace `scope_classify()` with a fine-tuned classifier or an LLM call
  that returns a label plus confidence. The rest of the pipeline expects exactly that shape.
- **Domain classification**: replace `classify_domain()` with a multi-label model; it must keep
  returning `[(domain_key, weight), ...]`.

---

## JSON API

The pages are server-rendered, but everything is also available as JSON for the PWA or a
mobile client.

| Endpoint | Purpose |
|---|---|
| `GET /api/challenges?domain=water&district=Kakinada` | Filtered list |
| `GET /api/challenge/SETU-26-0001` | One challenge with matches, audit trail and funding |
| `POST /api/submit` | `{"text": "...", "lang": "te", "district": "Kakinada"}` → runs the full pipeline |
| `GET /api/stats` | Dashboard aggregates |
| `GET /healthz` | Liveness check |

```bash
curl -X POST localhost:8000/api/submit -H "Content-Type: application/json" \
  -d '{"text":"600 families in our block have no clean water in the monsoon","lang":"te","district":"Guntur"}'
```

FastAPI also generates interactive API docs at **http://127.0.0.1:8000/docs** — worth opening
for thirty seconds if a judge asks whether this is a real backend.

---

## Moving beyond the laptop

The prototype is deliberately dependency-light. For a real deployment:

- **Database**: swap SQLite for PostgreSQL. Only `app/db.py` changes; the schema is plain SQL.
- **Sessions**: `SESSIONS` in `main.py` is an in-memory dict. Move to Redis or signed cookies
  before running more than one worker.
- **Serving**: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4` behind nginx.
- **Auth**: demo passwords are SHA-256 with a fixed salt. Use bcrypt or Argon2 and MeriPehchaan
  / DigiLocker sign-in for citizens and institutions.
- **Data sovereignty**: everything here runs on one machine with no outbound calls, which is the
  posture the state cloud deployment assumes.

---

## Voice intake

The **Speak** button does real microphone capture through the browser's Web Speech API.
It needs Chrome or Edge, a working microphone, and an internet connection — Chrome sends the
audio out for recognition. On `http://localhost` the browser treats the page as a secure
context, so it will ask for microphone permission the first time; allow it.

**Load sample text** does the same job offline: it drops real Bengali, Hindi, Odia, Nepali,
Urdu, Assamese, Telugu, Tamil, Marathi or Kannada text into the box with the English
translation attached. Use this if the venue wifi is unreliable, the laptop has no microphone,
or you picked Santali, Kurukh or Ho — no browser recognises those, which is precisely the gap
Bhashini fills in the real deployment. That fallback is worth saying out loud to a judge.

Whatever goes wrong, the status line under the buttons says what happened and what to do.

## Known limits (say these before a judge finds them)

- Voice capture is the browser's recogniser, not Bhashini yet. It covers the major scheduled
  languages but not Santali, Kurukh or Ho, and it needs the internet.
- Classification is rule-based, so an unusual phrasing can land in the wrong domain — which is
  exactly why the human override exists and why every decision carries a confidence score.
- Fit scores are computed from a declared capability list. In production these would come from
  publication history, patents and past project records.
