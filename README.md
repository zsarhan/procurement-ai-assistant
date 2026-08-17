# Procurement AI Assistant

A prototype conversational AI assistant for exploring California State
procurement data. Users ask natural-language questions; a LangGraph agent
translates them into MongoDB aggregation pipelines, executes them, and
returns clear, insight-driven answers.

## Architecture

```
┌────────────────┐        HTTP (JSON)        ┌──────────────────────────┐
│  React frontend │ ───────────────────────► │  FastAPI backend         │
│  (frontend/)     │ ◄─────────────────────── │  (backend/)              │
└────────────────┘                            │                          │
                                               │  LangGraph ReAct agent   │
                                               │  (Gemini LLM)            │
                                               │    │                    │
                                               │    ▼                    │
                                               │  run_mongo_aggregation  │
                                               │  tool                   │
                                               │    │                    │
                                               │    ▼                    │
                                               │  MongoDB Atlas          │
                                               │  purchase_orders        │
                                               └──────────────────────────┘
```

- **Frontend and backend are fully decoupled** — separate codebases, separate
  package managers, communicating only over HTTP (`frontend/README.md`,
  `backend/README.md`).
- **Agent loop**: the LLM reads a schema-aware system prompt, decides on a
  MongoDB aggregation pipeline for the user's question, calls the
  `run_mongo_aggregation` tool to execute it against MongoDB, and then
  converts the raw results into a natural-language answer. See
  `backend/app/agent.py`.
- **Data pipeline**: `backend/data/seed_data.py` loads the Kaggle CSV with
  pandas, normalizes columns, derives `purchase_year` / `purchase_quarter` /
  `purchase_month` fields (so the LLM doesn't have to get MongoDB date-math
  operators right), and bulk-inserts into MongoDB with indexes on the fields
  used by common questions.

## Supported query types

- Total order counts across timeframes (monthly, quarterly, yearly).
- Highest-spending quarter/period.
- Frequently ordered line items.
- Open-ended procurement questions (e.g. "which department spends the most
  with CalCard?").

## Quick start

1. **Backend** — see [`backend/README.md`](backend/README.md): get a MongoDB
   Atlas URI, a Gemini API key, download the dataset, seed the database, run
   the API.
2. **Frontend** — see [`frontend/README.md`](frontend/README.md): `npm install`,
   `npm run dev`.

## Project structure

```
procurement-ai-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py        # FastAPI app + CORS
│   │   ├── routes.py      # POST /api/chat, GET /api/health
│   │   ├── agent.py       # LangGraph agent + MongoDB aggregation tool
│   │   └── database.py    # MongoDB connection
│   ├── data/
│   │   ├── seed_data.py   # CSV -> MongoDB ingestion script
│   │   └── raw_dataset.csv  # (gitignored — download per backend/README.md)
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── App.jsx        # Chat UI
│   │   └── App.css
│   ├── package.json
│   ├── .env.example
│   └── README.md
├── .gitignore
└── README.md
```

