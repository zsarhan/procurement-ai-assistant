import json
import math
import os
import re
from datetime import date, datetime
from decimal import Decimal

from bson import ObjectId
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from app.database import get_orders_collection

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

FORBIDDEN_STAGES = {"$out", "$merge", "$function", "$accumulator"}
MAX_RESULTS_RETURNED = 200

SCHEMA_DESCRIPTION = """
Collection: purchase_orders (California State Procurement purchase order line items)

Fields available on every document:
- creation_date (datetime): when the PO record was created
- purchase_date (datetime): when the purchase was made
- purchase_year (int): year extracted from purchase_date, e.g. 2013
- purchase_month (int): month number 1-12 extracted from purchase_date
- purchase_quarter (int): calendar quarter 1-4 extracted from purchase_date
- fiscal_year (string): state fiscal year label, e.g. "2012-2013"
- lpa_number, purchase_order_number, requisition_number (string identifiers)
- acquisition_type, sub_acquisition_type, acquisition_method, sub_acquisition_method (string categories)
- department_name (string): purchasing state department/agency
- supplier_code, supplier_name, supplier_qualifications, supplier_zip_code (supplier info)
- calcard (string "YES"/"NO"): whether purchase used state CalCard
- item_name (string): short line item name -- use this for "most frequently ordered item" questions
- item_description (string): longer free-text description of the line item
- quantity (float): quantity purchased
- unit_price (float): price per unit in USD
- total_price (float): quantity * unit_price, total line item cost in USD -- use this for spend questions
- classification_codes, normalized_unspsc (UNSPSC classification codes)
- commodity_title, class_code, class_title, family_code, family_title, segment_code, segment_title (UNSPSC taxonomy labels)
- location (string): delivery/purchase location

Query pattern guidance:
- "How many orders" in a period -> $match on purchase_year/purchase_quarter/purchase_month, then $count
  or $group by purchase_order_number first if you must dedupe multi-line orders.
- "Highest spending quarter" -> $group by {purchase_year, purchase_quarter} summing total_price, then $sort descending, $limit.
- "Frequently ordered line items" -> $group by item_name, sum quantity and/or count documents, $sort descending, $limit.
- Always add $limit to pipelines that return raw documents (cap well under 200 rows).
- Only use read-only aggregation stages ($match, $group, $sort, $limit, $project, $unwind, $count, $addFields, $facet, $bucket). Never use $out or $merge.
"""

SYSTEM_PROMPT = f"""You are a procurement data analyst assistant for California state procurement records.
You answer natural-language questions by querying a MongoDB collection through the run_mongo_aggregation tool.

{SCHEMA_DESCRIPTION}

Rules:
1. For any question that requires data (counts, totals, rankings, trends, lookups), you MUST call
   run_mongo_aggregation with a valid pipeline before answering. Never guess numbers.
2. Write the pipeline as a JSON array of MongoDB aggregation stages.
3. After getting tool results, answer in clear, concise natural language aimed at a procurement
   professional: state the direct answer first, then brief supporting numbers. Use $ and commas for
   money, and name actual departments/items/quarters from the data. You may use markdown (bold,
   bullet lists) for readability.
4. If the question is open-ended or ambiguous, make a reasonable interpretation, state that
   interpretation briefly, and answer it with real data.
5. If a pipeline returns no results, say so plainly instead of inventing an answer.
6. When your answer's core numbers are a small set of comparable values across categories (e.g. top
   spending quarters, most frequently ordered items, spend by department) -- ideally 3 to 8 data
   points -- append ONE fenced ```chart_data block after your prose answer, containing a single JSON
   object: {{"title": "short chart title", "labels": ["label1", "label2", ...], "values": [num1, num2, ...]}}.
   Labels and values must be the same length and in the same order as the values (e.g. sorted
   descending by value already). Omit this block entirely for yes/no answers, single-number answers,
   or lookups that aren't a comparison across categories.
"""


def _json_default(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, Decimal):
        return float(value)
    return str(value)


def _sanitize(value):
    if isinstance(value, float):
        return None if math.isnan(value) or math.isinf(value) else value
    if isinstance(value, dict):
        return {k: _sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize(v) for v in value]
    return value


@tool
def run_mongo_aggregation(pipeline_json: str) -> str:
    """Execute a read-only MongoDB aggregation pipeline against the purchase_orders
    collection and return the results as a JSON string.

    Args:
        pipeline_json: A JSON-encoded array of MongoDB aggregation pipeline stages,
            e.g. '[{"$match": {"purchase_year": 2013}}, {"$count": "total"}]'
    """
    try:
        pipeline = json.loads(pipeline_json)
    except json.JSONDecodeError as exc:
        return json.dumps({"error": f"pipeline_json is not valid JSON: {exc}"})

    if not isinstance(pipeline, list):
        return json.dumps({"error": "pipeline_json must be a JSON array of stage objects"})

    for stage in pipeline:
        if not isinstance(stage, dict):
            return json.dumps({"error": "each pipeline stage must be an object"})
        if FORBIDDEN_STAGES.intersection(stage.keys()):
            return json.dumps({"error": "pipeline contains a forbidden write/output stage"})

    collection = get_orders_collection()
    try:
        cursor = collection.aggregate(pipeline)
        results = list(cursor)
    except Exception as exc:
        return json.dumps({"error": str(exc)})

    truncated = len(results) > MAX_RESULTS_RETURNED
    results = results[:MAX_RESULTS_RETURNED]

    for doc in results:
        if isinstance(doc.get("_id"), ObjectId):
            doc.pop("_id", None)

    results = _sanitize(results)

    return json.dumps(
        {"result_count": len(results), "truncated": truncated, "results": results},
        default=_json_default,
    )


MAX_TOOL_ITERATIONS = 6

TOOLS_BY_NAME = {run_mongo_aggregation.name: run_mongo_aggregation}


def _build_llm():
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to backend/.env (see backend/README.md)."
        )
    llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=GEMINI_API_KEY, temperature=0)
    return llm.bind_tools([run_mongo_aggregation])


_llm = None


def get_llm():
    global _llm
    if _llm is None:
        _llm = _build_llm()
    return _llm


CHART_BLOCK_RE = re.compile(r"```chart_data\s*(\{.*?\})\s*```", re.DOTALL)


def _extract_chart(text: str) -> tuple[str, dict | None]:
    match = CHART_BLOCK_RE.search(text)
    if not match:
        return text.strip(), None

    chart = None
    try:
        candidate = json.loads(match.group(1))
        labels = candidate.get("labels")
        values = candidate.get("values")
        if (
            isinstance(labels, list)
            and isinstance(values, list)
            and len(labels) == len(values)
            and len(labels) > 0
        ):
            chart = {
                "title": str(candidate.get("title") or ""),
                "labels": [str(label) for label in labels],
                "values": [float(v) for v in values],
            }
    except (json.JSONDecodeError, TypeError, ValueError):
        chart = None

    display_text = (text[: match.start()] + text[match.end() :]).strip()
    return display_text, chart


def ask_agent(message: str, history: list[dict] | None = None) -> dict:
    llm = get_llm()

    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for turn in history or []:
        if turn.get("role") == "user":
            messages.append(HumanMessage(content=turn["content"]))
        else:
            messages.append(AIMessage(content=turn["content"]))
    messages.append(HumanMessage(content=message))

    for _ in range(MAX_TOOL_ITERATIONS):
        response = llm.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            text, chart = _extract_chart(response.text)
            return {"text": text, "chart": chart}

        for tool_call in response.tool_calls:
            tool = TOOLS_BY_NAME.get(tool_call["name"])
            if tool is None:
                result = json.dumps({"error": f"unknown tool {tool_call['name']}"})
            else:
                result = tool.invoke(tool_call["args"])
            messages.append(
                ToolMessage(content=result, tool_call_id=tool_call["id"])
            )

    return {
        "text": "I wasn't able to reach a final answer for that question in time. Could you rephrase or narrow it down?",
        "chart": None,
    }
