import os
import json
from datetime import datetime
import re
from typing import List, Dict, Any


RECIPIENTS_FILE = os.path.join(os.path.abspath("."), "recipients.json")


def _read_store() -> Dict[str, Any]:
    if not os.path.exists(RECIPIENTS_FILE):
        return {"recipients": [], "last_updated": None}
    try:
        with open(RECIPIENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"recipients": [], "last_updated": None}


def _write_store(store: Dict[str, Any]) -> None:
    store["last_updated"] = datetime.utcnow().isoformat()
    with open(RECIPIENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)


def validate_email(email: str) -> bool:
    if not isinstance(email, str):
        return False
    email = email.strip()
    # Simple RFC5322-inspired regex (good enough for UI validation)
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return re.match(pattern, email) is not None


def load_recipients() -> List[str]:
    store = _read_store()
    recipients = []
    for entry in store.get("recipients", []):
        email = entry.get("email")
        if email:
            recipients.append(email)
    return recipients


def add_recipient(email: str) -> Dict[str, Any]:
    email_normalized = (email or "").strip().lower()
    if not validate_email(email_normalized):
        return {"success": False, "error": "Invalid email format"}

    store = _read_store()
    existing = {e.get("email", "").lower() for e in store.get("recipients", [])}
    if email_normalized in existing:
        return {"success": True, "message": "Email already subscribed"}

    store.setdefault("recipients", []).append({
        "email": email_normalized,
        "added_at": datetime.utcnow().isoformat()
    })
    _write_store(store)
    return {"success": True, "message": "Email added"}


def remove_recipient(email: str) -> Dict[str, Any]:
    email_normalized = (email or "").strip().lower()
    store = _read_store()
    before_count = len(store.get("recipients", []))
    store["recipients"] = [e for e in store.get("recipients", []) if e.get("email", "").lower() != email_normalized]
    after_count = len(store.get("recipients", []))
    if after_count == before_count:
        return {"success": False, "error": "Email not found"}
    _write_store(store)
    return {"success": True, "message": "Email removed"}


