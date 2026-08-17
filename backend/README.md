# Procurement AI Assistant — Backend

FastAPI service that exposes a conversational endpoint over a MongoDB collection
of California State procurement purchase orders. Natural-language questions are
translated into MongoDB aggregation pipelines by a Gemini-backed LangGraph agent,
executed against the database, and turned back into a natural-language answer.

## Architecture

```
frontend (React)  --HTTP-->  FastAPI (app/main.py, app/routes.py)
                                    |
                                    v
                        LangGraph ReAct agent (app/agent.py)
                          - Gemini LLM decides the MongoDB
                            aggregation pipeline
                          - run_mongo_aggregation tool executes it
                          - Gemini turns results into NL answer
                                    |
                                    v
                          MongoDB (app/database.py)
                          purchase_orders collection
```

## 1. Get a MongoDB Atlas connection string

1. Create a free account/cluster at https://www.mongodb.com/cloud/atlas/register (M0 free tier).
2. In Atlas: Database Access → add a database user with a password.
3. Network Access → add your current IP (or `0.0.0.0/0` for a quick prototype demo).
4. Database → Connect → "Drivers" → copy the `mongodb+srv://...` connection string.

## 2. Get a Gemini API key

1. Go to https://aistudio.google.com/app/apikey and create a free API key.

## 3. Download the dataset

This project targets the **"Large Purchases by the State of CA"** dataset on Kaggle
(California's public purchase order data). Search Kaggle for
"California State Procurement" / "Large Purchases by the State of CA" if the
link below has moved:

https://www.kaggle.com/datasets/sohier/large-purchases-by-the-state-of-ca

Download the CSV and save it as:

```
backend/data/raw_dataset.csv
```

## 4. Configure environment

```bash
cd backend
cp .env.example .env
# then edit .env and fill in MONGODB_URI and GEMINI_API_KEY
```

## 5. Install dependencies

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

## 6. Load the dataset into MongoDB

```bash
python -m data.seed_data --drop
```

This normalizes column names, parses dates/numeric fields, derives
`purchase_year` / `purchase_quarter` / `purchase_month`, batch-inserts into the
`purchase_orders` collection, and creates indexes used by common queries.

## 7. Run the API

```bash
uvicorn app.main:app --reload --port 8000
```

- Health check: `GET http://localhost:8000/api/health`
- Chat endpoint: `POST http://localhost:8000/api/chat`

```json
{
  "message": "What was our highest spending quarter?",
  "history": []
}
```

Response:

```json
{ "response": "The highest-spending quarter was Q3 2013, with total spend of $..." }
```

The frontend keeps conversation history client-side and resends it as `history`
on each request — the backend itself is stateless between requests.
