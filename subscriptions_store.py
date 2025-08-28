import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

SUBSCRIPTIONS_FILE = os.path.join(os.path.abspath("."), "subscriptions.json")


def _read_store() -> Dict[str, Any]:
    if not os.path.exists(SUBSCRIPTIONS_FILE):
        return {"subscriptions": {}, "last_updated": None}
    try:
        with open(SUBSCRIPTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"subscriptions": {}, "last_updated": None}


def _write_store(store: Dict[str, Any]) -> None:
    store["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(SUBSCRIPTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)


def _detect_company(product_url: str) -> Optional[str]:
    host = urlparse(product_url).netloc.lower()
    if "lululemon" in host:
        return "lululemon"
    if "nike" in host:
        return "nike"
    return None


def get_products(email: str) -> List[Dict[str, str]]:
    store = _read_store()
    return store.get("subscriptions", {}).get(email.lower(), [])


def add_product(email: str, product_url: str) -> Dict[str, Any]:
    email_key = (email or "").strip().lower()
    product_url = (product_url or "").strip()
    if not email_key or not product_url:
        return {"success": False, "error": "Email and URL are required"}

    # Basic URL sanity check
    parsed = urlparse(product_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return {"success": False, "error": "Invalid URL"}

    company = _detect_company(product_url)
    if not company:
        return {"success": False, "error": "Unsupported product URL (only Lululemon/Nike supported)"}

    store = _read_store()
    subs = store.setdefault("subscriptions", {}).setdefault(email_key, [])

    # Prevent duplicates
    if any(entry.get("url") == product_url for entry in subs):
        return {"success": True, "message": "Product already added"}

    subs.append({"url": product_url, "company": company, "added_at": datetime.now(timezone.utc).isoformat()})
    _write_store(store)
    return {"success": True, "message": "Product added"}


def remove_product(email: str, product_url: str) -> Dict[str, Any]:
    email_key = (email or "").strip().lower()
    product_url = (product_url or "").strip()
    store = _read_store()
    subs = store.setdefault("subscriptions", {}).setdefault(email_key, [])
    before = len(subs)
    subs = [entry for entry in subs if entry.get("url") != product_url]
    store["subscriptions"][email_key] = subs
    if len(subs) == before:
        return {"success": False, "error": "Product not found"}
    _write_store(store)
    return {"success": True, "message": "Product removed"}


def list_all_subscriptions() -> Dict[str, List[Dict[str, str]]]:
    store = _read_store()
    return store.get("subscriptions", {})
