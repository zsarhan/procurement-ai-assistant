import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "procurement")
ORDERS_COLLECTION = os.getenv("MONGODB_COLLECTION", "purchase_orders")

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(MONGODB_URI)
    return _client


def get_db() -> Database:
    return get_client()[MONGODB_DB]


def get_orders_collection() -> Collection:
    return get_db()[ORDERS_COLLECTION]
