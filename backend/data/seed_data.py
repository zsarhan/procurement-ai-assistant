import argparse
import math
import re
import sys
from pathlib import Path

import pandas as pd
from pymongo import ASCENDING, InsertOne

sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.database import get_client, get_db

DEFAULT_CSV = Path(__file__).resolve().parent / "raw_dataset.csv"
BATCH_SIZE = 5000

COLUMN_ALIASES = {
    "creation_date": "creation_date",
    "purchase_date": "purchase_date",
    "fiscal_year": "fiscal_year",
    "lpa_number": "lpa_number",
    "purchase_order_number": "purchase_order_number",
    "requisition_number": "requisition_number",
    "acquisition_type": "acquisition_type",
    "sub_acquisition_type": "sub_acquisition_type",
    "acquisition_method": "acquisition_method",
    "sub_acquisition_method": "sub_acquisition_method",
    "department_name": "department_name",
    "supplier_code": "supplier_code",
    "supplier_name": "supplier_name",
    "supplier_qualifications": "supplier_qualifications",
    "supplier_zip_code": "supplier_zip_code",
    "calcard": "calcard",
    "item_name": "item_name",
    "item_description": "item_description",
    "quantity": "quantity",
    "unit_price": "unit_price",
    "total_price": "total_price",
    "classification_codes": "classification_codes",
    "normalized_unspsc": "normalized_unspsc",
    "commodity_title": "commodity_title",
    "class": "class_code",
    "class_title": "class_title",
    "family": "family_code",
    "family_title": "family_title",
    "segment": "segment_code",
    "segment_title": "segment_title",
    "location": "location",
}

DATE_FIELDS = ["creation_date", "purchase_date"]
NUMERIC_FIELDS = ["quantity", "unit_price", "total_price"]


def normalize_header(col: str) -> str:
    col = col.strip().lower()
    col = re.sub(r"[^a-z0-9]+", "_", col)
    return col.strip("_")


def load_dataframe(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, low_memory=False)
    df.columns = [normalize_header(c) for c in df.columns]

    rename_map = {c: COLUMN_ALIASES[c] for c in df.columns if c in COLUMN_ALIASES}
    df = df.rename(columns=rename_map)

    for field in DATE_FIELDS:
        if field in df.columns:
            df[field] = pd.to_datetime(df[field], errors="coerce")

    for field in NUMERIC_FIELDS:
        if field in df.columns:
            df[field] = pd.to_numeric(
                df[field].astype(str).str.replace(r"[\$,]", "", regex=True),
                errors="coerce",
            )

    if "purchase_date" in df.columns:
        df["purchase_year"] = df["purchase_date"].dt.year
        df["purchase_month"] = df["purchase_date"].dt.month
        df["purchase_quarter"] = df["purchase_date"].dt.quarter

    df = df.where(pd.notnull(df), None)
    return df


def to_documents(df: pd.DataFrame):
    for record in df.to_dict(orient="records"):
        for key in DATE_FIELDS:
            value = record.get(key)
            if value is not None and hasattr(value, "to_pydatetime"):
                record[key] = None if pd.isna(value) else value.to_pydatetime()
        for key, value in record.items():
            if isinstance(value, float) and math.isnan(value):
                record[key] = None
        yield record


def seed(csv_path: Path, drop: bool) -> None:
    if not csv_path.exists():
        raise FileNotFoundError(
            f"CSV not found at {csv_path}. Download the California State "
            "Procurement dataset from Kaggle and save it there (see backend/README.md)."
        )

    print(f"Reading {csv_path} ...")
    df = load_dataframe(csv_path)
    print(f"Loaded {len(df):,} rows with columns: {list(df.columns)}")

    db = get_db()
    collection = db["purchase_orders"]

    if drop:
        print("Dropping existing purchase_orders collection ...")
        collection.drop()

    total_inserted = 0
    batch = []
    for doc in to_documents(df):
        batch.append(InsertOne(doc))
        if len(batch) >= BATCH_SIZE:
            result = collection.bulk_write(batch, ordered=False)
            total_inserted += result.inserted_count
            print(f"  inserted {total_inserted:,} / {len(df):,}", end="\r")
            batch = []
    if batch:
        result = collection.bulk_write(batch, ordered=False)
        total_inserted += result.inserted_count

    print(f"\nInserted {total_inserted:,} documents into '{collection.name}'.")

    print("Creating indexes ...")
    collection.create_index([("purchase_date", ASCENDING)])
    collection.create_index([("purchase_year", ASCENDING), ("purchase_quarter", ASCENDING)])
    collection.create_index([("department_name", ASCENDING)])
    collection.create_index([("item_name", ASCENDING)])
    collection.create_index([("supplier_name", ASCENDING)])
    print("Done.")

    get_client().close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="Path to the CSV file")
    parser.add_argument(
        "--drop", action="store_true", help="Drop the purchase_orders collection before loading"
    )
    args = parser.parse_args()
    seed(args.csv, args.drop)
