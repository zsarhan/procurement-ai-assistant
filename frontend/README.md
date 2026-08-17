# Procurement AI Assistant — Frontend

React (Vite) chat UI for the Procurement AI Assistant. Fully decoupled from the
backend — talks to it only over HTTP via `VITE_API_URL`.

## Setup

```bash
cd frontend
cp .env.example .env   # edit if the backend isn't on localhost:8000
npm install
npm run dev
```

Open http://localhost:5173. The backend must be running (see `../backend/README.md`)
and its `FRONTEND_ORIGIN` env var must include this dev server's origin (it does
by default).

## What it does

- Single-page chat interface (`src/App.jsx`).
- Sends each user message plus the full prior conversation to
  `POST {VITE_API_URL}/api/chat` and renders the assistant's reply.
- Includes clickable example questions covering the required query types
  (order counts by period, highest-spending quarter, frequently ordered
  items, open-ended questions).
