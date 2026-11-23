"""
Product scraper used by the web app and the email digest.

The scraper is retailer agnostic: it reads structured product data
(JSON-LD / microdata / Open Graph) and falls back to common price markup.
That covers Nike, Lululemon and most other storefronts without a selector
per retailer.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse, unquote

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

try:  # optional, impersonates a real browser TLS fingerprint
    from curl_cffi import requests as cffi_requests
except Exception:  # pragma: no cover - curl_cffi is optional
    cffi_requests = None

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}

CACHE_TTL = 15 * 60          # a good price for 15 minutes
FAILURE_CACHE_TTL = 2 * 60   # retry blocked pages sooner
DEFAULT_TIMEOUT = 20

_CURRENCY_SYMBOLS = {"USD": "$", "GBP": "£", "EUR": "€", "CAD": "C$", "AUD": "A$", "JPY": "¥"}

_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_cache_lock = threading.Lock()


class BlockedError(Exception):
    """Raised when the retailer serves a bot/access-denied page."""


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------

def _looks_blocked(html: str, status_code: int) -> bool:
    if status_code in (401, 403, 429):
        return True
    head = (html or "")[:3000].lower()
    title_match = re.search(r"<title[^>]*>(.*?)</title>", head, re.S)
    title = re.sub(r"\s+", " ", title_match.group(1)) if title_match else ""
    markers = (
        "access denied",
        "just a moment",
        "attention required",
        "are you a robot",
        "pardon our interruption",
        "request unsuccessful",
        "verify you are human",
        "captcha",
    )
    return any(marker in title for marker in markers)


def _fetch(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Fetch a product page, preferring a browser-like TLS fingerprint."""
    errors: List[str] = []

    if cffi_requests is not None:
        try:
            response = cffi_requests.get(
                url,
                impersonate="chrome",
                headers={"Accept-Language": "en-US,en;q=0.9"},
                timeout=timeout,
                allow_redirects=True,
            )
            html = response.text or ""
            if not _looks_blocked(html, response.status_code):
                return html
            errors.append(f"HTTP {response.status_code} (browser client)")
        except Exception as exc:  # network/TLS problems fall through
            errors.append(f"browser client: {exc}")

    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=timeout)
        html = response.text or ""
        if not _looks_blocked(html, response.status_code):
            return html
        errors.append(f"HTTP {response.status_code}")
    except requests.RequestException as exc:
        errors.append(str(exc))

    raise BlockedError("; ".join(errors) or "The retailer refused the request")


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def _walk_json(value: Any) -> Iterable[Dict[str, Any]]:
    """Yield every dictionary inside a JSON-LD blob, depth first."""
    if isinstance(value, dict):
        yield value
        for key in ("@graph", "mainEntity", "hasVariant", "itemListElement", "offers", "itemOffered"):
            if key in value:
                yield from _walk_json(value[key])
    elif isinstance(value, list):
        for item in value:
            yield from _walk_json(item)


def _type_names(node: Dict[str, Any]) -> List[str]:
    raw = node.get("@type")
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, list):
        return [str(item) for item in raw]
    return []


def _to_price(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return round(float(value), 2)
    text = str(value).replace(",", "")
    match = re.search(r"\d+(?:\.\d+)?", text)
    return round(float(match.group()), 2) if match else None


def _offer_price(offers: Any) -> Tuple[Optional[float], Optional[str]]:
    if not offers:
        return None, None
    if isinstance(offers, list):
        for offer in offers:
            price, currency = _offer_price(offer)
            if price is not None:
                return price, currency
        return None, None
    if not isinstance(offers, dict):
        return None, None

    currency = offers.get("priceCurrency")
    for key in ("price", "lowPrice", "highPrice"):
        price = _to_price(offers.get(key))
        if price is not None:
            return price, currency

    spec = offers.get("priceSpecification")
    if isinstance(spec, dict):
        price = _to_price(spec.get("price"))
        if price is not None:
            return price, spec.get("priceCurrency") or currency
    return None, currency


def _jsonld_product(soup: BeautifulSoup) -> Dict[str, Any]:
    names: List[Tuple[int, str]] = []
    images: List[Tuple[int, str]] = []
    price: Optional[float] = None
    currency: Optional[str] = None

    for script in soup.find_all("script", type="application/ld+json"):
        raw = (script.string or script.get_text() or "").strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            continue

        for node in _walk_json(data):
            types = _type_names(node)
            if not any(t in ("Product", "ProductGroup", "IndividualProduct") for t in types):
                continue

            # A ProductGroup name is the canonical product name; variant
            # names add colour/size noise ("... - Black - Size XXS").
            priority = 2 if "ProductGroup" in types else 1
            if node.get("name"):
                names.append((priority, str(node["name"]).strip()))

            image = node.get("image")
            if isinstance(image, dict):
                image = image.get("url")
            if isinstance(image, list):
                image = next((i.get("url") if isinstance(i, dict) else i for i in image if i), None)
            if image:
                images.append((priority, str(image)))

            if price is None:
                price, node_currency = _offer_price(node.get("offers"))
                currency = node_currency or currency

    found: Dict[str, Any] = {}
    if names:
        found["name"] = max(names, key=lambda item: item[0])[1]
    if images:
        found["image"] = max(images, key=lambda item: item[0])[1]
    if price is not None:
        found["price"] = price
        found["currency"] = currency
    return found


def _meta(soup: BeautifulSoup, *, prop: Optional[str] = None, name: Optional[str] = None) -> Optional[str]:
    if prop:
        tag = soup.find("meta", attrs={"property": prop})
        if tag and tag.get("content"):
            return tag["content"].strip()
    if name:
        tag = soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return tag["content"].strip()
    return None


def _meta_price(soup: BeautifulSoup) -> Tuple[Optional[float], Optional[str]]:
    for prop, name in (
        ("product:price:amount", None),
        ("og:price:amount", None),
        (None, "product:price:amount"),
    ):
        value = _meta(soup, prop=prop, name=name)
        if value:
            currency = (
                _meta(soup, prop="product:price:currency")
                or _meta(soup, prop="og:price:currency")
                or _meta(soup, name="product:price:currency")
                or "USD"
            )
            price = _to_price(value)
            if price is not None:
                return price, currency.upper()

    tag = soup.select_one('[itemprop="price"]')
    if tag:
        price = _to_price(tag.get("content") or tag.get_text(strip=True))
        if price is not None:
            currency = _meta(soup, prop="product:price:currency") or "USD"
            return price, currency.upper()
    return None, None


def _selector_price(soup: BeautifulSoup) -> Optional[float]:
    selectors = (
        '[data-testid="product-price"]',
        '[data-test="product-price"]',
        '[data-testid="price"]',
        ".product-price",
        ".price__current",
        ".price",
    )
    for selector in selectors:
        for node in soup.select(selector)[:5]:
            text = node.get_text(" ", strip=True)
            if "$" in text or "€" in text or "£" in text:
                match = re.search(r"[\$£€]\s?(\d[\d,]*(?:\.\d{2})?)", text)
                if match:
                    return _to_price(match.group(1))
    return None


def _clean_name(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    name = re.sub(r"\s+", " ", name).strip()
    # Drop storefront suffixes such as "x. Nike.com" or "| lululemon"
    name = re.sub(r"\s*[|–—-]\s*(Nike\.com|Nike|lululemon|Lululemon)\s*$", "", name, flags=re.I)
    name = re.sub(r"\.\s*(Nike\.com|Nike|lululemon|Lululemon)\s*$", "", name, flags=re.I)
    return name.strip() or None


def _name_from_url(url: str) -> Optional[str]:
    """Best-effort product name from the URL path when the page is blocked."""
    path = urlparse(url).path
    parts = [unquote(p) for p in path.split("/") if p]
    slug = None
    if "/p/" in path:
        # Lululemon: /p/category/Product-Name/_/prod123
        if "_" in parts:
            index = parts.index("_")
            if index > 0:
                slug = parts[index - 1]
        elif len(parts) > 1:
            slug = parts[-1]
    if not slug:
        slug = next((p for p in reversed(parts) if re.search(r"[a-zA-Z]", p) and p not in ("t", "p")), None)
    if not slug or re.fullmatch(r"prod\d+", slug, flags=re.I):
        return None
    slug = re.sub(r"\.(html?|aspx?)$", "", slug, flags=re.I)
    words = [w for w in re.split(r"[-_+]|%20", slug) if w]
    if len(words) < 2:
        return None
    return " ".join(w.capitalize() for w in words)


def _retailer_for(url: str) -> str:
    host = urlparse(url).netloc.lower().replace("www.", "")
    if "lululemon" in host:
        return "Lululemon"
    if "nike" in host:
        return "Nike"
    if "adidas" in host:
        return "adidas"
    if "amazon" in host:
        return "Amazon"
    root = host.split(".")[0] if host else "Retailer"
    return root[:1].upper() + root[1:]


def _clean_image(image: Optional[str], base_url: str) -> Optional[str]:
    if not image:
        return None
    image = str(image).strip()
    if image.startswith("//"):
        return "https:" + image
    if image.startswith("/"):
        parsed = urlparse(base_url)
        return f"{parsed.scheme}://{parsed.netloc}{image}"
    return image if image.startswith(("http://", "https://")) else None


def format_price(price: Optional[float], currency: Optional[str]) -> Optional[str]:
    if price is None:
        return None
    currency = (currency or "USD").upper()
    symbol = _CURRENCY_SYMBOLS.get(currency)
    if symbol:
        return f"{symbol}{price:,.2f}"
    return f"{currency} {price:,.2f}"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_product(html: str, url: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")

    data = _jsonld_product(soup)

    name = _clean_name(data.get("name")) or _clean_name(_meta(soup, prop="og:title")) or _clean_name(
        soup.title.get_text(strip=True) if soup.title else None
    )

    price = data.get("price")
    currency = data.get("currency")
    if price is None:
        price, currency = _meta_price(soup)
    if price is None:
        price = _selector_price(soup)
    if price is not None and not currency:
        currency = "USD"

    image = _clean_image(data.get("image") or _meta(soup, prop="og:image"), url)

    return {
        "url": url,
        "retailer": _retailer_for(url),
        "name": name or _name_from_url(url),
        "price": price,
        "currency": (currency or "USD").upper() if price is not None else None,
        "price_display": format_price(price, currency),
        "image": image,
        "success": price is not None,
        "status": "ok" if price is not None else "price_missing",
        "error": None if price is not None else "Could not find a price on the page",
    }


def _scrape_live(url: str) -> Dict[str, Any]:
    try:
        html = _fetch(url)
        result = parse_product(html, url)
        result["fetched_at"] = datetime.now(timezone.utc).isoformat()
        return result
    except BlockedError as exc:
        logger.warning("Blocked while scraping %s: %s", url, exc)
        return {
            "url": url,
            "retailer": _retailer_for(url),
            "name": _name_from_url(url),
            "price": None,
            "currency": None,
            "price_display": None,
            "image": None,
            "success": False,
            "status": "blocked",
            "error": "The retailer blocked the request from this server",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        logger.exception("Failed to scrape %s", url)
        return {
            "url": url,
            "retailer": _retailer_for(url),
            "name": _name_from_url(url),
            "price": None,
            "currency": None,
            "price_display": None,
            "image": None,
            "success": False,
            "status": "error",
            "error": str(exc)[:200],
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }


def scrape(url: str, force: bool = False) -> Dict[str, Any]:
    """Scrape one product URL, served from a short-lived in-memory cache."""
    now = time.time()
    with _cache_lock:
        cached = _cache.get(url)
    if cached and not force:
        expires_at, value = cached
        if now < expires_at:
            return dict(value)

    result = _scrape_live(url)
    ttl = CACHE_TTL if result["success"] else FAILURE_CACHE_TTL
    with _cache_lock:
        _cache[url] = (now + ttl, result)
    return dict(result)


def scrape_many(urls: List[str], force: bool = False) -> List[Dict[str, Any]]:
    """Scrape several URLs concurrently (keeping the order of the input)."""
    unique = list(dict.fromkeys(urls))
    if not unique:
        return []
    workers = min(4, len(unique))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda u: scrape(u, force=force), unique))
    by_url = {item["url"]: item for item in results}
    return [by_url[url] for url in urls if url in by_url]


def clear_cache() -> None:
    with _cache_lock:
        _cache.clear()
