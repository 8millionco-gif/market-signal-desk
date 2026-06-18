from __future__ import annotations

import json
import mimetypes
import os
import html
import hashlib
import hmac
import re
import threading
import time
import zipfile
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from io import BytesIO
from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote, unquote, urlencode, urlparse
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
SEED_FILE = DATA_DIR / "seed.json"
WATCHLIST_FILE = DATA_DIR / "watchlist.json"
DART_CORP_CODE_FILE = DATA_DIR / "dart-corp-codes.json"
RUNS_DIR = DATA_DIR / "runs"
KST = timezone(timedelta(hours=9))
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "").strip()
TOSS_BASE_URL = os.getenv("TOSS_BASE_URL", "https://openapi.tossinvest.com").rstrip("/")
TOSS_CLIENT_ID = os.getenv("TOSS_CLIENT_ID", "")
TOSS_CLIENT_SECRET = os.getenv("TOSS_CLIENT_SECRET", "")
TOSS_ACCESS_TOKEN = os.getenv("TOSS_ACCESS_TOKEN", "")
TOSS_ACCOUNT_SEQ = os.getenv("TOSS_ACCOUNT_SEQ", "")
TOSS_LIVE_PRICES = os.getenv("TOSS_LIVE_PRICES", "1").lower() not in {"0", "false", "no", "off"}
TOSS_LIVE_CANDLES = os.getenv("TOSS_LIVE_CANDLES", "1").lower() not in {"0", "false", "no", "off"}
TOSS_LIVE_ORDERBOOK = os.getenv("TOSS_LIVE_ORDERBOOK", "1").lower() not in {"0", "false", "no", "off"}
TOSS_LIVE_TRADES = os.getenv("TOSS_LIVE_TRADES", "1").lower() not in {"0", "false", "no", "off"}
TOSS_PRICE_CACHE_SECONDS = int(os.getenv("TOSS_PRICE_CACHE_SECONDS", "15"))
TOSS_CANDLE_CACHE_SECONDS = int(os.getenv("TOSS_CANDLE_CACHE_SECONDS", "60"))
TOSS_ORDERBOOK_CACHE_SECONDS = int(os.getenv("TOSS_ORDERBOOK_CACHE_SECONDS", "5"))
TOSS_TRADES_CACHE_SECONDS = int(os.getenv("TOSS_TRADES_CACHE_SECONDS", "5"))
TOSS_REQUEST_TIMEOUT_SECONDS = int(os.getenv("TOSS_REQUEST_TIMEOUT_SECONDS", "5"))
TOSS_CANDLE_MAX_CANDIDATES = int(os.getenv("TOSS_CANDLE_MAX_CANDIDATES", "2"))
TOSS_ORDERBOOK_MAX_CANDIDATES = int(os.getenv("TOSS_ORDERBOOK_MAX_CANDIDATES", "2"))
TOSS_TRADES_MAX_CANDIDATES = int(os.getenv("TOSS_TRADES_MAX_CANDIDATES", "2"))
TOSS_TRADES_COUNT = int(os.getenv("TOSS_TRADES_COUNT", "30"))
TOSS_CANDLE_MAX_STALENESS_DAYS = int(os.getenv("TOSS_CANDLE_MAX_STALENESS_DAYS", "7"))
_TOSS_SAMPLE_PRICE_DRIFT_WARN_PERCENT = os.getenv("TOSS_SAMPLE_PRICE_DRIFT_WARN_PERCENT", "").strip()
try:
    TOSS_SAMPLE_PRICE_DRIFT_WARN_PERCENT = (
        Decimal(_TOSS_SAMPLE_PRICE_DRIFT_WARN_PERCENT)
        if _TOSS_SAMPLE_PRICE_DRIFT_WARN_PERCENT
        else None
    )
except InvalidOperation:
    TOSS_SAMPLE_PRICE_DRIFT_WARN_PERCENT = None
DART_BASE_URL = os.getenv("DART_BASE_URL", "https://opendart.fss.or.kr/api").rstrip("/")
DART_API_KEY = os.getenv("DART_API_KEY", "")
DART_LIVE_DISCLOSURES = os.getenv("DART_LIVE_DISCLOSURES", "1").lower() not in {"0", "false", "no", "off"}
DART_DISCLOSURE_LOOKBACK_DAYS = int(os.getenv("DART_DISCLOSURE_LOOKBACK_DAYS", "7"))
DART_DISCLOSURE_CACHE_SECONDS = int(os.getenv("DART_DISCLOSURE_CACHE_SECONDS", "300"))
DART_REQUEST_TIMEOUT_SECONDS = int(os.getenv("DART_REQUEST_TIMEOUT_SECONDS", "6"))
DART_CORP_CODE_TIMEOUT_SECONDS = int(os.getenv("DART_CORP_CODE_TIMEOUT_SECONDS", "10"))
DART_DISCLOSURE_MAX_CANDIDATES = int(os.getenv("DART_DISCLOSURE_MAX_CANDIDATES", "2"))
FX_LIVE_RATES = os.getenv("FX_LIVE_RATES", "1").lower() not in {"0", "false", "no", "off"}
FX_RATE_URL = os.getenv("FX_RATE_URL", "https://open.er-api.com/v6/latest/USD")
FX_RATE_FALLBACK_URL = os.getenv("FX_RATE_FALLBACK_URL", "https://api.frankfurter.app/latest?from=USD&to=KRW")
FX_RATE_CACHE_SECONDS = int(os.getenv("FX_RATE_CACHE_SECONDS", "1800"))
FX_REQUEST_TIMEOUT_SECONDS = int(os.getenv("FX_REQUEST_TIMEOUT_SECONDS", "5"))
MARKET_INDEX_LIVE = os.getenv("MARKET_INDEX_LIVE", "1").lower() not in {"0", "false", "no", "off"}
MARKET_INDEX_PROVIDER = os.getenv("MARKET_INDEX_PROVIDER", "naver")
MARKET_INDEX_URL_TEMPLATE = os.getenv(
    "MARKET_INDEX_URL_TEMPLATE",
    "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=1m",
)
MARKET_INDEX_NAVER_DOMESTIC_URL_TEMPLATE = os.getenv(
    "MARKET_INDEX_NAVER_DOMESTIC_URL_TEMPLATE",
    "https://polling.finance.naver.com/api/realtime/domestic/index/{symbol}",
)
MARKET_INDEX_NAVER_WORLD_URL_TEMPLATE = os.getenv(
    "MARKET_INDEX_NAVER_WORLD_URL_TEMPLATE",
    "https://polling.finance.naver.com/api/realtime/worldstock/index/{symbol}",
)
MARKET_INDEX_CACHE_SECONDS = int(os.getenv("MARKET_INDEX_CACHE_SECONDS", "60"))
MARKET_INDEX_REQUEST_TIMEOUT_SECONDS = int(os.getenv("MARKET_INDEX_REQUEST_TIMEOUT_SECONDS", "5"))
MARKET_INDEX_SYMBOLS = {
    "kospi": os.getenv("MARKET_INDEX_KOSPI_SYMBOL", "KOSPI"),
    "kosdaq": os.getenv("MARKET_INDEX_KOSDAQ_SYMBOL", "KOSDAQ"),
    "nasdaq": os.getenv("MARKET_INDEX_NASDAQ_SYMBOL", ".IXIC"),
}
RAW_NAVER_NEWS_BASE_URL = os.getenv("NAVER_NEWS_BASE_URL", "https://openapi.naver.com/v1/search/news.json")
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")
NAVER_LIVE_NEWS = os.getenv("NAVER_LIVE_NEWS", "1").lower() not in {"0", "false", "no", "off"}
NAVER_NEWS_DISPLAY = int(os.getenv("NAVER_NEWS_DISPLAY", "5"))
NAVER_NEWS_CACHE_SECONDS = int(os.getenv("NAVER_NEWS_CACHE_SECONDS", "300"))
NAVER_NEWS_MAX_CANDIDATES = int(os.getenv("NAVER_NEWS_MAX_CANDIDATES", "3"))
NAVER_REQUEST_TIMEOUT_SECONDS = int(os.getenv("NAVER_REQUEST_TIMEOUT_SECONDS", "5"))
GDELT_DOC_BASE_URL = os.getenv("GDELT_DOC_BASE_URL", "https://api.gdeltproject.org/api/v2/doc/doc").rstrip("/")
GDELT_LIVE_NEWS = os.getenv("GDELT_LIVE_NEWS", "0").lower() not in {"0", "false", "no", "off"}
GDELT_NEWS_DISPLAY = int(os.getenv("GDELT_NEWS_DISPLAY", "5"))
GDELT_NEWS_TIMESPAN = os.getenv("GDELT_NEWS_TIMESPAN", "1week")
GDELT_NEWS_CACHE_SECONDS = int(os.getenv("GDELT_NEWS_CACHE_SECONDS", "300"))
GDELT_NEWS_MAX_CANDIDATES = int(os.getenv("GDELT_NEWS_MAX_CANDIDATES", "1"))
GDELT_REQUEST_TIMEOUT_SECONDS = int(os.getenv("GDELT_REQUEST_TIMEOUT_SECONDS", "20"))
GDELT_REQUEST_SPACING_SECONDS = float(os.getenv("GDELT_REQUEST_SPACING_SECONDS", "5.2"))
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4")
OPENAI_ANALYSIS_ENABLED = os.getenv("OPENAI_ANALYSIS_ENABLED", "1").lower() not in {"0", "false", "no", "off"}
OPENAI_ANALYSIS_CACHE_SECONDS = int(os.getenv("OPENAI_ANALYSIS_CACHE_SECONDS", "900"))
OPENAI_ANALYSIS_MAX_CANDIDATES = int(os.getenv("OPENAI_ANALYSIS_MAX_CANDIDATES", "1"))
OPENAI_REQUEST_TIMEOUT_SECONDS = int(os.getenv("OPENAI_REQUEST_TIMEOUT_SECONDS", "20"))
OUTBOUND_IP_CHECK_URL = os.getenv("OUTBOUND_IP_CHECK_URL", "https://api.ipify.org?format=json")
OUTBOUND_IP_CACHE_SECONDS = int(os.getenv("OUTBOUND_IP_CACHE_SECONDS", "300"))
OUTBOUND_IP_REQUEST_TIMEOUT_SECONDS = int(os.getenv("OUTBOUND_IP_REQUEST_TIMEOUT_SECONDS", "5"))
SIGNAL_SCHEDULER_ENABLED = os.getenv("SIGNAL_SCHEDULER_ENABLED", "0").lower() not in {"0", "false", "no", "off"}
SIGNAL_SCHEDULER_INTERVAL_SECONDS = int(os.getenv("SIGNAL_SCHEDULER_INTERVAL_SECONDS", "30"))
SIGNAL_CLOSE_RUN_TIME = os.getenv("SIGNAL_CLOSE_RUN_TIME", "16:40")
SIGNAL_CLOSE_RUN_WINDOW_MINUTES = int(os.getenv("SIGNAL_CLOSE_RUN_WINDOW_MINUTES", "360"))
SIGNAL_PREOPEN_RUN_TIME = os.getenv("SIGNAL_PREOPEN_RUN_TIME", "08:40")
SIGNAL_PREOPEN_RUN_WINDOW_MINUTES = int(os.getenv("SIGNAL_PREOPEN_RUN_WINDOW_MINUTES", "80"))
SIGNAL_RUN_HISTORY_LIMIT = int(os.getenv("SIGNAL_RUN_HISTORY_LIMIT", "12"))
SIGNAL_PERFORMANCE_RUN_LIMIT = int(os.getenv("SIGNAL_PERFORMANCE_RUN_LIMIT", "12"))
SIGNAL_PERFORMANCE_TOP_CANDIDATES = int(os.getenv("SIGNAL_PERFORMANCE_TOP_CANDIDATES", "3"))
_SIGNAL_PERFORMANCE_SUCCESS_THRESHOLD_PERCENT = os.getenv("SIGNAL_PERFORMANCE_SUCCESS_THRESHOLD_PERCENT", "1")
try:
    SIGNAL_PERFORMANCE_SUCCESS_THRESHOLD_PERCENT = Decimal(_SIGNAL_PERFORMANCE_SUCCESS_THRESHOLD_PERCENT)
except InvalidOperation:
    SIGNAL_PERFORMANCE_SUCCESS_THRESHOLD_PERCENT = Decimal("1")
TOKEN_CACHE: dict[str, object] = {"access_token": "", "expires_at": datetime.min.replace(tzinfo=timezone.utc)}
PRICE_CACHE: dict[str, object] = {"symbols": (), "payload": None, "expires_at": datetime.min.replace(tzinfo=timezone.utc)}
CANDLE_CACHE: dict[tuple[str, str, int], dict[str, object]] = {}
ORDERBOOK_CACHE: dict[str, dict[str, object]] = {}
TRADES_CACHE: dict[tuple[str, int], dict[str, object]] = {}
OUTBOUND_IP_CACHE: dict[str, object] = {"payload": None, "expires_at": datetime.min.replace(tzinfo=timezone.utc)}
CORP_CODE_CACHE: dict[str, object] = {"payload": None}
DISCLOSURE_CACHE: dict[tuple[str, int], dict[str, object]] = {}
NEWS_CACHE: dict[tuple[str, int, int, str], dict[str, object]] = {}
GDELT_NEWS_CACHE: dict[tuple[str, int, str, str], dict[str, object]] = {}
ANALYSIS_CACHE: dict[str, dict[str, object]] = {}
FX_CACHE: dict[str, object] = {"payload": None, "expires_at": datetime.min.replace(tzinfo=timezone.utc)}
INDEX_CACHE: dict[str, object] = {"payload": None, "expires_at": datetime.min.replace(tzinfo=timezone.utc)}
GDELT_RATE_LOCK = threading.Lock()
GDELT_LAST_REQUEST_AT = datetime.min.replace(tzinfo=timezone.utc)
SCHEDULER_LOCK = threading.Lock()
SCHEDULER_STATE: dict[str, object] = {
    "started": False,
    "running": False,
    "lastError": "",
    "lastCheckedAt": "",
    "lastRuns": {},
}


def normalize_naver_news_url(value: str) -> str:
    url = value.strip().rstrip("/")
    if url.endswith("/v1/search/news"):
        return f"{url}.json"
    return url


NAVER_NEWS_BASE_URL = normalize_naver_news_url(RAW_NAVER_NEWS_BASE_URL)


def read_json(path: Path, fallback):
    if not path.exists():
        return fallback
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def seed_data() -> dict:
    return read_json(SEED_FILE, {"candidates": [], "market": {}, "principles": []})


def watchlist() -> list[str]:
    saved = read_json(WATCHLIST_FILE, {"symbols": ["005930", "000660", "AAPL"]})
    return saved.get("symbols", [])


def mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


def toss_config_status() -> dict:
    return {
        "baseUrl": TOSS_BASE_URL,
        "livePricesEnabled": TOSS_LIVE_PRICES,
        "liveCandlesEnabled": TOSS_LIVE_CANDLES,
        "liveOrderbookEnabled": TOSS_LIVE_ORDERBOOK,
        "liveTradesEnabled": TOSS_LIVE_TRADES,
        "clientIdConfigured": bool(TOSS_CLIENT_ID),
        "clientIdPreview": mask_secret(TOSS_CLIENT_ID),
        "clientSecretConfigured": bool(TOSS_CLIENT_SECRET),
        "accessTokenConfigured": bool(TOSS_ACCESS_TOKEN),
        "accountSeqConfigured": bool(TOSS_ACCOUNT_SEQ),
        "readyForTokenIssue": bool(TOSS_CLIENT_ID and TOSS_CLIENT_SECRET),
        "readyForMarketData": bool(TOSS_ACCESS_TOKEN or (TOSS_CLIENT_ID and TOSS_CLIENT_SECRET)),
        "readyForAccountData": bool(TOSS_ACCOUNT_SEQ and (TOSS_ACCESS_TOKEN or (TOSS_CLIENT_ID and TOSS_CLIENT_SECRET))),
        "orderbookMaxCandidates": TOSS_ORDERBOOK_MAX_CANDIDATES,
        "tradesMaxCandidates": TOSS_TRADES_MAX_CANDIDATES,
    }


def auth_config_status() -> dict:
    return {
        "enabled": bool(ADMIN_TOKEN),
    }


def dart_config_status() -> dict:
    return {
        "baseUrl": DART_BASE_URL,
        "liveDisclosuresEnabled": DART_LIVE_DISCLOSURES,
        "apiKeyConfigured": bool(DART_API_KEY),
        "apiKeyPreview": mask_secret(DART_API_KEY),
        "readyForDisclosures": bool(DART_API_KEY),
        "lookbackDays": DART_DISCLOSURE_LOOKBACK_DAYS,
        "corpCodeCacheExists": DART_CORP_CODE_FILE.exists(),
    }


def naver_news_config_status() -> dict:
    return {
        "configuredBaseUrl": RAW_NAVER_NEWS_BASE_URL,
        "baseUrl": NAVER_NEWS_BASE_URL,
        "liveNewsEnabled": NAVER_LIVE_NEWS,
        "clientIdConfigured": bool(NAVER_CLIENT_ID),
        "clientIdPreview": mask_secret(NAVER_CLIENT_ID),
        "clientSecretConfigured": bool(NAVER_CLIENT_SECRET),
        "readyForNews": bool(NAVER_CLIENT_ID and NAVER_CLIENT_SECRET),
        "display": NAVER_NEWS_DISPLAY,
        "maxCandidates": NAVER_NEWS_MAX_CANDIDATES,
        "cacheSeconds": NAVER_NEWS_CACHE_SECONDS,
    }


def gdelt_news_config_status() -> dict:
    return {
        "baseUrl": GDELT_DOC_BASE_URL,
        "liveNewsEnabled": GDELT_LIVE_NEWS,
        "apiKeyRequired": False,
        "readyForNews": GDELT_LIVE_NEWS,
        "display": GDELT_NEWS_DISPLAY,
        "timespan": GDELT_NEWS_TIMESPAN,
        "maxCandidates": GDELT_NEWS_MAX_CANDIDATES,
        "cacheSeconds": GDELT_NEWS_CACHE_SECONDS,
        "requestSpacingSeconds": GDELT_REQUEST_SPACING_SECONDS,
    }


def market_config_status() -> dict:
    return {
        "liveFxEnabled": FX_LIVE_RATES,
        "liveIndicesEnabled": MARKET_INDEX_LIVE,
        "fxRateUrl": FX_RATE_URL,
        "fxFallbackUrl": FX_RATE_FALLBACK_URL,
        "indexProvider": MARKET_INDEX_PROVIDER,
        "indexNaverDomesticUrl": MARKET_INDEX_NAVER_DOMESTIC_URL_TEMPLATE,
        "indexNaverWorldUrl": MARKET_INDEX_NAVER_WORLD_URL_TEMPLATE,
        "indexSymbols": MARKET_INDEX_SYMBOLS,
        "readyForFx": FX_LIVE_RATES,
        "readyForIndices": MARKET_INDEX_LIVE,
        "fxCacheSeconds": FX_RATE_CACHE_SECONDS,
        "indexCacheSeconds": MARKET_INDEX_CACHE_SECONDS,
    }


def outbound_ip_status() -> dict:
    cached = OUTBOUND_IP_CACHE.get("payload")
    expires_at = OUTBOUND_IP_CACHE.get("expires_at")
    if cached and isinstance(expires_at, datetime) and expires_at > datetime.now(timezone.utc):
        payload = dict(cached)  # type: ignore[arg-type]
        payload["cached"] = True
        return payload

    try:
        request = Request(
            OUTBOUND_IP_CHECK_URL,
            headers={"User-Agent": "market-signal-desk/1.0"},
            method="GET",
        )
        with urlopen(request, timeout=OUTBOUND_IP_REQUEST_TIMEOUT_SECONDS) as response:
            raw = response.read().decode("utf-8", errors="replace")
        ip = ""
        try:
            parsed = json.loads(raw)
            ip = str(parsed.get("ip") or parsed.get("origin") or "").strip()
        except json.JSONDecodeError:
            ip = raw.strip()
        payload = {
            "source": "external-check",
            "provider": OUTBOUND_IP_CHECK_URL,
            "ip": ip,
            "cached": False,
            "cacheSeconds": OUTBOUND_IP_CACHE_SECONDS,
            "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
            "message": "현재 Render 서버가 외부 API에 접근할 때 보이는 IP입니다.",
        }
        OUTBOUND_IP_CACHE["payload"] = payload
        OUTBOUND_IP_CACHE["expires_at"] = datetime.now(timezone.utc) + timedelta(seconds=OUTBOUND_IP_CACHE_SECONDS)
        return payload
    except Exception as error:
        return {
            "source": "unavailable",
            "provider": OUTBOUND_IP_CHECK_URL,
            "ip": "",
            "cached": False,
            "error": type(error).__name__,
            "message": "외부 IP를 확인하지 못했습니다.",
            "detail": str(error)[:240],
        }


def openai_config_status() -> dict:
    return {
        "baseUrl": OPENAI_BASE_URL,
        "analysisEnabled": OPENAI_ANALYSIS_ENABLED,
        "apiKeyConfigured": bool(OPENAI_API_KEY),
        "apiKeyPreview": mask_secret(OPENAI_API_KEY),
        "readyForAnalysis": bool(OPENAI_API_KEY and OPENAI_ANALYSIS_ENABLED),
        "model": OPENAI_MODEL,
        "maxCandidates": OPENAI_ANALYSIS_MAX_CANDIDATES,
        "cacheSeconds": OPENAI_ANALYSIS_CACHE_SECONDS,
    }


def issue_toss_token() -> dict:
    if not TOSS_CLIENT_ID or not TOSS_CLIENT_SECRET:
        raise ValueError("TOSS_CLIENT_ID와 TOSS_CLIENT_SECRET이 필요합니다.")

    body = urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": TOSS_CLIENT_ID,
            "client_secret": TOSS_CLIENT_SECRET,
        }
    ).encode("utf-8")
    request = Request(
        f"{TOSS_BASE_URL}/oauth2/token",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urlopen(request, timeout=TOSS_REQUEST_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def toss_access_token() -> str:
    if TOSS_ACCESS_TOKEN:
        return TOSS_ACCESS_TOKEN
    cached_token = str(TOKEN_CACHE.get("access_token") or "")
    expires_at = TOKEN_CACHE.get("expires_at")
    if cached_token and isinstance(expires_at, datetime) and expires_at > datetime.now(timezone.utc):
        return cached_token

    token_payload = issue_toss_token()
    expires_in = int(token_payload.get("expires_in", 0) or 0)
    ttl_seconds = max(0, expires_in - 60)
    TOKEN_CACHE["access_token"] = token_payload["access_token"]
    TOKEN_CACHE["expires_at"] = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    return str(TOKEN_CACHE["access_token"])


def unique_symbols(symbols: list[str]) -> list[str]:
    unique = []
    for symbol in symbols:
        normalized = symbol.strip()
        if normalized and normalized not in unique:
            unique.append(normalized)
    return unique


def fetch_toss_prices(symbols: list[str]) -> dict:
    symbols = unique_symbols(symbols)
    if not symbols:
        return {"result": []}

    cache_key = tuple(sorted(symbols))
    expires_at = PRICE_CACHE.get("expires_at")
    if (
        PRICE_CACHE.get("symbols") == cache_key
        and PRICE_CACHE.get("payload") is not None
        and isinstance(expires_at, datetime)
        and expires_at > datetime.now(timezone.utc)
    ):
        return PRICE_CACHE["payload"]  # type: ignore[return-value]

    token = toss_access_token()
    query = urlencode({"symbols": ",".join(symbols)})
    request = Request(
        f"{TOSS_BASE_URL}/api/v1/prices?{query}",
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    with urlopen(request, timeout=TOSS_REQUEST_TIMEOUT_SECONDS) as response:
        payload = json.loads(response.read().decode("utf-8"))
        PRICE_CACHE["symbols"] = cache_key
        PRICE_CACHE["payload"] = payload
        PRICE_CACHE["expires_at"] = datetime.now(timezone.utc) + timedelta(seconds=TOSS_PRICE_CACHE_SECONDS)
        return payload


def fetch_toss_candles(symbol: str, interval: str = "1d", count: int = 20) -> dict:
    symbol = symbol.strip()
    if not symbol:
        return {"result": {"candles": []}}
    if interval not in {"1m", "1d"}:
        raise ValueError("interval은 1m 또는 1d만 가능합니다.")
    count = max(1, min(int(count), 200))

    cache_key = (symbol, interval, count)
    cached = CANDLE_CACHE.get(cache_key)
    if cached:
        expires_at = cached.get("expires_at")
        if isinstance(expires_at, datetime) and expires_at > datetime.now(timezone.utc):
            return cached["payload"]  # type: ignore[return-value]

    token = toss_access_token()
    query = urlencode({"symbol": symbol, "interval": interval, "count": count, "adjusted": "true"})
    request = Request(
        f"{TOSS_BASE_URL}/api/v1/candles?{query}",
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    with urlopen(request, timeout=TOSS_REQUEST_TIMEOUT_SECONDS) as response:
        payload = json.loads(response.read().decode("utf-8"))
        CANDLE_CACHE[cache_key] = {
            "payload": payload,
            "expires_at": datetime.now(timezone.utc) + timedelta(seconds=TOSS_CANDLE_CACHE_SECONDS),
        }
        return payload


def fetch_toss_orderbook(symbol: str) -> dict:
    symbol = symbol.strip()
    if not symbol:
        return {"result": {"asks": [], "bids": []}}

    cached = ORDERBOOK_CACHE.get(symbol)
    if cached:
        expires_at = cached.get("expires_at")
        if isinstance(expires_at, datetime) and expires_at > datetime.now(timezone.utc):
            return cached["payload"]  # type: ignore[return-value]

    token = toss_access_token()
    query = urlencode({"symbol": symbol})
    request = Request(
        f"{TOSS_BASE_URL}/api/v1/orderbook?{query}",
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    with urlopen(request, timeout=TOSS_REQUEST_TIMEOUT_SECONDS) as response:
        payload = json.loads(response.read().decode("utf-8"))
        ORDERBOOK_CACHE[symbol] = {
            "payload": payload,
            "expires_at": datetime.now(timezone.utc) + timedelta(seconds=TOSS_ORDERBOOK_CACHE_SECONDS),
        }
        return payload


def fetch_toss_trades(symbol: str, count: int | None = None) -> dict:
    symbol = symbol.strip()
    if not symbol:
        return {"result": []}
    count = TOSS_TRADES_COUNT if count is None else int(count)
    count = max(1, min(count, 50))

    cache_key = (symbol, count)
    cached = TRADES_CACHE.get(cache_key)
    if cached:
        expires_at = cached.get("expires_at")
        if isinstance(expires_at, datetime) and expires_at > datetime.now(timezone.utc):
            return cached["payload"]  # type: ignore[return-value]

    token = toss_access_token()
    query = urlencode({"symbol": symbol, "count": count})
    request = Request(
        f"{TOSS_BASE_URL}/api/v1/trades?{query}",
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    with urlopen(request, timeout=TOSS_REQUEST_TIMEOUT_SECONDS) as response:
        payload = json.loads(response.read().decode("utf-8"))
        TRADES_CACHE[cache_key] = {
            "payload": payload,
            "expires_at": datetime.now(timezone.utc) + timedelta(seconds=TOSS_TRADES_CACHE_SECONDS),
        }
        return payload


def decimal_text(value: str) -> str:
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        return str(value)
    normalized = number.normalize()
    return format(normalized, "f").rstrip("0").rstrip(".") if "." in format(normalized, "f") else format(normalized, "f")


def display_price(price: str, currency: str) -> str:
    try:
        number = Decimal(str(price))
    except InvalidOperation:
        return str(price)
    if currency == "KRW":
        return f"{int(number):,}원"
    if currency == "USD":
        return f"${decimal_text(str(number))}"
    return f"{decimal_text(str(number))} {currency}"


def display_change(rate: Decimal) -> str:
    sign = "+" if rate >= 0 else ""
    return f"{sign}{rate.quantize(Decimal('0.1'))}%"


def display_rate(value: Decimal) -> str:
    rounded = value.quantize(Decimal("0.1"))
    return f"{rounded:,.1f}"


def decimal_or_none(value) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def display_number_to_decimal(value) -> Decimal | None:
    cleaned = re.sub(r"[^0-9.\-]", "", str(value or ""))
    if not cleaned:
        return None
    return decimal_or_none(cleaned)


def display_percent_to_decimal(value) -> Decimal | None:
    return display_number_to_decimal(value)


def display_multiplier_to_decimal(value) -> Decimal | None:
    return display_number_to_decimal(value)


def display_percent_abs(rate: Decimal) -> str:
    return f"{abs(rate).quantize(Decimal('0.1'))}%"


def display_decimal_percent(rate: Decimal) -> str:
    sign = "+" if rate >= 0 else ""
    return f"{sign}{rate.quantize(Decimal('0.1'))}%"


def display_multiplier(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.1'))}배"


def display_compact_volume(value: Decimal | None) -> str:
    if value is None:
        return "-"
    if value >= Decimal("100000000"):
        return f"{(value / Decimal('100000000')).quantize(Decimal('0.1'))}억"
    if value >= Decimal("10000"):
        return f"{(value / Decimal('10000')).quantize(Decimal('0.1'))}만"
    return f"{int(value):,}"


def parse_fx_timestamp(value) -> str:
    if value is None:
        return datetime.now(KST).isoformat(timespec="seconds")
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc).astimezone(KST).isoformat(timespec="seconds")
    text = str(value).strip()
    if not text:
        return datetime.now(KST).isoformat(timespec="seconds")
    parsed = parse_iso_datetime(text)
    if parsed:
        return parsed.isoformat(timespec="seconds")
    try:
        parsed_email_date = parsedate_to_datetime(text)
        return parsed_email_date.astimezone(KST).isoformat(timespec="seconds")
    except (TypeError, ValueError, IndexError, OverflowError):
        return text


def parse_fx_payload(payload: dict, source_url: str) -> dict:
    rates = payload.get("rates", {})
    if not isinstance(rates, dict) or "KRW" not in rates:
        raise ValueError("환율 응답에서 KRW 값을 찾지 못했습니다.")
    rate = decimal_or_none(rates.get("KRW"))
    if rate is None or rate <= 0:
        raise ValueError("환율 응답의 KRW 값이 올바르지 않습니다.")
    if str(payload.get("result", "")).lower() == "error":
        raise ValueError(str(payload.get("error-type", "환율 API 오류")))

    timestamp = (
        payload.get("time_last_update_unix")
        or payload.get("time_last_update_utc")
        or payload.get("date")
        or payload.get("time_next_update_utc")
    )
    provider = "open.er-api.com" if "open.er-api.com" in source_url else urlparse(source_url).netloc or "fx"
    return {
        "rate": rate,
        "display": display_rate(rate),
        "timestamp": parse_fx_timestamp(timestamp),
        "provider": provider,
        "sourceUrl": source_url,
    }


def fetch_usd_krw_rate() -> dict:
    cached = FX_CACHE.get("payload")
    expires_at = FX_CACHE.get("expires_at")
    if cached is not None and isinstance(expires_at, datetime) and expires_at > datetime.now(timezone.utc):
        return cached  # type: ignore[return-value]

    errors = []
    for source_url in unique_symbols([FX_RATE_URL, FX_RATE_FALLBACK_URL]):
        if not source_url:
            continue
        try:
            request = Request(source_url, headers={"Accept": "application/json"}, method="GET")
            with urlopen(request, timeout=FX_REQUEST_TIMEOUT_SECONDS) as response:
                payload = json.loads(response.read().decode("utf-8"))
            parsed = parse_fx_payload(payload, source_url)
            FX_CACHE["payload"] = parsed
            FX_CACHE["expires_at"] = datetime.now(timezone.utc) + timedelta(seconds=FX_RATE_CACHE_SECONDS)
            return parsed
        except Exception as error:
            errors.append(f"{urlparse(source_url).netloc}: {error}")
    raise ValueError("; ".join(errors) or "환율 API 호출이 실패했습니다.")


def index_timestamp(value) -> str:
    if value is None:
        return datetime.now(KST).isoformat(timespec="seconds")
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc).astimezone(KST).isoformat(timespec="seconds")
    parsed = parse_iso_datetime(str(value))
    if parsed:
        return parsed.isoformat(timespec="seconds")
    return str(value)


def display_index_value(value: Decimal) -> str:
    if value >= 1000:
        return f"{value.quantize(Decimal('0.01')):,.2f}"
    return decimal_text(str(value.quantize(Decimal('0.01'))))


def market_index_provider_label() -> str:
    provider = MARKET_INDEX_PROVIDER.lower()
    if provider == "naver":
        return "Naver Finance"
    if provider == "yahoo":
        return "Yahoo Finance"
    return MARKET_INDEX_PROVIDER or "Index API"


def index_request_url(key: str, symbol: str) -> str:
    if MARKET_INDEX_PROVIDER.lower() == "naver":
        template = (
            MARKET_INDEX_NAVER_DOMESTIC_URL_TEMPLATE
            if key in {"kospi", "kosdaq"}
            else MARKET_INDEX_NAVER_WORLD_URL_TEMPLATE
        )
        return template.replace("{symbol}", quote(symbol, safe=""))
    return MARKET_INDEX_URL_TEMPLATE.replace("{symbol}", quote(symbol, safe=""))


def parse_naver_index_payload(key: str, symbol: str, payload: dict) -> dict:
    rows = payload.get("datas", [])
    if not isinstance(rows, list) or not rows:
        raise ValueError("네이버 지수 응답에 결과가 없습니다.")
    item = rows[0]
    if not isinstance(item, dict):
        raise ValueError("네이버 지수 응답 형식이 올바르지 않습니다.")

    price = display_number_to_decimal(item.get("closePrice"))
    change_percent = decimal_or_none(item.get("fluctuationsRatio"))
    if price is None:
        raise ValueError("네이버 지수 현재 값을 찾지 못했습니다.")

    timestamp = (
        item.get("localTradedAt")
        or item.get("tradeDateTime")
        or payload.get("time")
        or datetime.now(KST).isoformat(timespec="seconds")
    )
    return {
        "key": key,
        "symbol": symbol,
        "name": item.get("stockName") or item.get("indexName") or symbol,
        "value": display_index_value(price),
        "change": display_change(change_percent) if change_percent is not None else "",
        "timestamp": index_timestamp(timestamp),
        "marketStatus": item.get("marketStatus", ""),
        "provider": "Naver Finance",
        "sourceUrl": index_request_url(key, symbol),
    }


def parse_yahoo_index_payload(key: str, symbol: str, payload: dict) -> dict:
    chart = payload.get("chart", {})
    if not isinstance(chart, dict):
        raise ValueError("지수 응답 형식이 올바르지 않습니다.")
    error = chart.get("error")
    if error:
        raise ValueError(str(error))
    results = chart.get("result", [])
    if not isinstance(results, list) or not results:
        raise ValueError("지수 응답에 결과가 없습니다.")

    result = results[0]
    meta = result.get("meta", {}) if isinstance(result, dict) else {}
    if not isinstance(meta, dict):
        meta = {}
    price = decimal_or_none(
        meta.get("regularMarketPrice")
        or meta.get("previousClose")
        or meta.get("chartPreviousClose")
    )
    previous_close = decimal_or_none(meta.get("previousClose") or meta.get("chartPreviousClose"))
    if price is None:
        raise ValueError("지수 현재 값을 찾지 못했습니다.")

    change = ""
    if previous_close is not None and previous_close > 0:
        change = display_change(((price - previous_close) / previous_close) * Decimal(100))
    if not change:
        raw_change_percent = decimal_or_none(meta.get("regularMarketChangePercent"))
        if raw_change_percent is not None:
            change = display_change(raw_change_percent)

    timestamps = result.get("timestamp", []) if isinstance(result, dict) else []
    last_timestamp = timestamps[-1] if isinstance(timestamps, list) and timestamps else None
    timestamp = meta.get("regularMarketTime") or last_timestamp
    return {
        "key": key,
        "symbol": symbol,
        "name": meta.get("longName") or meta.get("shortName") or symbol,
        "value": display_index_value(price),
        "change": change,
        "timestamp": index_timestamp(timestamp),
        "provider": "Yahoo Finance",
        "sourceUrl": index_request_url(key, symbol),
    }


def fetch_market_indices() -> dict[str, dict]:
    cached = INDEX_CACHE.get("payload")
    expires_at = INDEX_CACHE.get("expires_at")
    if cached is not None and isinstance(expires_at, datetime) and expires_at > datetime.now(timezone.utc):
        return cached  # type: ignore[return-value]

    parsed: dict[str, dict] = {}
    errors: dict[str, str] = {}
    for key, symbol in MARKET_INDEX_SYMBOLS.items():
        if not symbol:
            continue
        try:
            request = Request(
                index_request_url(key, symbol),
                headers={
                    "Accept": "application/json, text/plain, */*",
                    "User-Agent": "Mozilla/5.0",
                    "Referer": "https://m.stock.naver.com/",
                },
                method="GET",
            )
            with urlopen(request, timeout=MARKET_INDEX_REQUEST_TIMEOUT_SECONDS) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if MARKET_INDEX_PROVIDER.lower() == "naver":
                parsed[key] = parse_naver_index_payload(key, symbol, payload)
            else:
                parsed[key] = parse_yahoo_index_payload(key, symbol, payload)
        except Exception as error:
            errors[key] = str(error)[:180]

    if not parsed:
        detail = "; ".join(f"{key}: {message}" for key, message in errors.items())
        raise ValueError(detail or "시장 지수 API 호출이 실패했습니다.")

    payload = {"indices": parsed, "errors": errors}
    INDEX_CACHE["payload"] = payload
    INDEX_CACHE["expires_at"] = datetime.now(timezone.utc) + timedelta(seconds=MARKET_INDEX_CACHE_SECONDS)
    return payload


def enrich_market_with_indices(market: dict) -> tuple[dict, dict]:
    enriched = dict(market)
    if not MARKET_INDEX_LIVE:
        enriched["indexSource"] = {
            "source": "sample",
            "message": "MARKET_INDEX_LIVE가 꺼져 있어 샘플 지수를 사용합니다.",
        }
        return enriched, {
            "source": "sample",
            "enabled": False,
            "message": "샘플 지수를 사용합니다.",
        }

    try:
        payload = fetch_market_indices()
        indices = payload.get("indices", {})
        errors = payload.get("errors", {})
        for key, item in indices.items():
            if item.get("change"):
                enriched[key] = item["change"]
        source = "index-api" if not errors else "index-api-partial"
        latest_timestamp = max(
            [str(item.get("timestamp", "")) for item in indices.values() if item.get("timestamp")],
            default="",
        )
        enriched["indexDetails"] = indices
        enriched["indexSource"] = {
            "source": source,
            "provider": market_index_provider_label(),
            "count": len(indices),
            "timestamp": latest_timestamp,
            "errors": errors,
        }
        return enriched, {
            "source": source,
            "enabled": True,
            "message": "시장 지수를 외부 지수 API로 갱신했습니다.",
            "provider": market_index_provider_label(),
            "count": len(indices),
            "errors": errors,
            "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
        }
    except Exception as error:
        enriched["indexSource"] = {
            "source": "sample",
            "message": "지수 갱신 실패로 샘플 지수를 사용합니다.",
            "error": str(error)[:240],
        }
        return enriched, {
            "source": "sample",
            "enabled": True,
            "error": "index-fetch-failed",
            "message": "지수 갱신 실패로 샘플 지수를 사용합니다.",
            "detail": str(error)[:240],
        }


def enrich_market_with_fx(market: dict) -> tuple[dict, dict]:
    enriched = dict(market)
    sample_value = str(enriched.get("usdKrw", "")).strip()
    if not FX_LIVE_RATES:
        enriched["usdKrwSource"] = {
            "source": "sample",
            "message": "FX_LIVE_RATES가 꺼져 있어 샘플 환율을 사용합니다.",
        }
        return enriched, {
            "source": "sample",
            "enabled": False,
            "message": "샘플 환율을 사용합니다.",
            "sampleValue": sample_value,
        }

    try:
        fx = fetch_usd_krw_rate()
        enriched["usdKrw"] = fx["display"]
        enriched["usdKrwSource"] = {
            "source": "fx-api",
            "provider": fx["provider"],
            "timestamp": fx["timestamp"],
            "sampleValue": sample_value,
        }
        return enriched, {
            "source": "fx-api",
            "enabled": True,
            "message": "USD/KRW 환율을 외부 환율 API로 갱신했습니다.",
            "provider": fx["provider"],
            "value": fx["display"],
            "timestamp": fx["timestamp"],
            "sampleValue": sample_value,
            "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
        }
    except Exception as error:
        enriched["usdKrwSource"] = {
            "source": "sample",
            "message": "환율 갱신 실패로 샘플 환율을 사용합니다.",
            "error": str(error)[:240],
        }
        return enriched, {
            "source": "sample",
            "enabled": True,
            "error": "fx-fetch-failed",
            "message": "환율 갱신 실패로 샘플 환율을 사용합니다.",
            "detail": str(error)[:240],
            "sampleValue": sample_value,
        }


def price_rows(payload: dict) -> list[dict]:
    result = payload.get("result", [])
    return result if isinstance(result, list) else []


def price_by_symbol(payload: dict) -> dict[str, dict]:
    return {
        str(item.get("symbol")): item
        for item in price_rows(payload)
        if item.get("symbol") and item.get("lastPrice") and item.get("currency")
    }


def candle_rows(payload: dict) -> list[dict]:
    result = payload.get("result", {})
    if not isinstance(result, dict):
        return []
    candles = result.get("candles", [])
    return candles if isinstance(candles, list) else []


def orderbook_result(payload: dict) -> dict:
    result = payload.get("result", {})
    return result if isinstance(result, dict) else {}


def orderbook_entries(value) -> list[dict]:
    return value if isinstance(value, list) else []


def trade_rows(payload: dict) -> list[dict]:
    result = payload.get("result", [])
    return result if isinstance(result, list) else []


def sum_entry_volume(entries: list[dict]) -> Decimal:
    total = Decimal("0")
    for entry in entries:
        volume = decimal_or_none(entry.get("volume")) if isinstance(entry, dict) else None
        if volume is not None:
            total += volume
    return total


def candle_volume_spike(candles: list[dict], average_days: int = 5) -> Decimal | None:
    ordered = candles_chronological(candles)
    volumes = [decimal_or_none(candle.get("volume")) for candle in ordered]
    volumes = [value for value in volumes if value is not None and value > 0]
    if len(volumes) < 2:
        return None
    latest = volumes[-1]
    previous = volumes[-(average_days + 1):-1]
    if not previous:
        return None
    average = sum(previous) / Decimal(len(previous))
    if average <= 0:
        return None
    return latest / average


def summarize_orderbook(payload: dict) -> dict | None:
    result = orderbook_result(payload)
    asks = orderbook_entries(result.get("asks"))
    bids = orderbook_entries(result.get("bids"))
    if not asks and not bids:
        return None

    ask_volume = sum_entry_volume(asks)
    bid_volume = sum_entry_volume(bids)
    total_volume = ask_volume + bid_volume
    imbalance = Decimal("0")
    if total_volume > 0:
        imbalance = ((bid_volume - ask_volume) / total_volume) * Decimal(100)

    ask_prices = [
        price
        for price in (decimal_or_none(entry.get("price")) for entry in asks if isinstance(entry, dict))
        if price is not None
    ]
    bid_prices = [
        price
        for price in (decimal_or_none(entry.get("price")) for entry in bids if isinstance(entry, dict))
        if price is not None
    ]
    best_ask = min(ask_prices) if ask_prices else None
    best_bid = max(bid_prices) if bid_prices else None
    spread_percent = None
    if best_ask is not None and best_bid is not None:
        midpoint = (best_ask + best_bid) / Decimal(2)
        if midpoint > 0:
            spread_percent = ((best_ask - best_bid) / midpoint) * Decimal(100)

    if imbalance >= Decimal("15"):
        pressure = "매수 우위"
    elif imbalance <= Decimal("-15"):
        pressure = "매도 우위"
    else:
        pressure = "균형"

    return {
        "source": "toss",
        "timestamp": result.get("timestamp"),
        "currency": result.get("currency"),
        "askLevels": len(asks),
        "bidLevels": len(bids),
        "askVolume": str(ask_volume),
        "bidVolume": str(bid_volume),
        "imbalancePercent": display_decimal_percent(imbalance),
        "spreadPercent": display_percent_abs(spread_percent) if spread_percent is not None else "",
        "pressure": pressure,
        "bestAsk": str(best_ask) if best_ask is not None else "",
        "bestBid": str(best_bid) if best_bid is not None else "",
    }


def summarize_trades(payload: dict) -> dict | None:
    trades = trade_rows(payload)
    if not trades:
        return None

    total_volume = Decimal("0")
    uptick_volume = Decimal("0")
    downtick_volume = Decimal("0")
    flat_volume = Decimal("0")
    chronological = list(reversed(trades))
    previous_price: Decimal | None = None
    for trade in chronological:
        if not isinstance(trade, dict):
            continue
        price = decimal_or_none(trade.get("price"))
        volume = decimal_or_none(trade.get("volume"))
        if volume is None or volume <= 0:
            continue
        total_volume += volume
        if price is None or previous_price is None:
            flat_volume += volume
        elif price > previous_price:
            uptick_volume += volume
        elif price < previous_price:
            downtick_volume += volume
        else:
            flat_volume += volume
        if price is not None:
            previous_price = price

    directional_volume = uptick_volume + downtick_volume
    bias = Decimal("0")
    if directional_volume > 0:
        bias = ((uptick_volume - downtick_volume) / directional_volume) * Decimal(100)
    if bias >= Decimal("20"):
        pressure = "상승 체결 우위"
    elif bias <= Decimal("-20"):
        pressure = "하락 체결 우위"
    else:
        pressure = "중립 체결"

    first = trades[0] if isinstance(trades[0], dict) else {}
    return {
        "source": "toss",
        "count": len(trades),
        "totalVolume": str(total_volume),
        "uptickVolume": str(uptick_volume),
        "downtickVolume": str(downtick_volume),
        "flatVolume": str(flat_volume),
        "biasPercent": display_decimal_percent(bias),
        "pressure": pressure,
        "latestTimestamp": first.get("timestamp"),
        "currency": first.get("currency"),
    }


def candle_datetime(candle: dict) -> datetime | None:
    return parse_iso_datetime(str(candle.get("timestamp", "")))


def candles_chronological(candles: list[dict]) -> list[dict]:
    dated = []
    undated = []
    for index, candle in enumerate(candles):
        parsed = candle_datetime(candle)
        if parsed is None:
            undated.append(candle)
        else:
            dated.append((parsed, index, candle))
    dated.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in dated] + undated


def candle_chart_points(candles: list[dict], limit: int = 10) -> list[int]:
    ordered = candles_chronological(candles)
    closes = [decimal_or_none(candle.get("closePrice")) for candle in ordered]
    values = [value for value in closes if value is not None]
    if not values:
        return []
    values = values[-limit:]
    minimum = min(values)
    maximum = max(values)
    spread = maximum - minimum
    if spread == 0:
        return [50 for _ in values]
    return [int(((value - minimum) / spread) * Decimal(60) + Decimal(30)) for value in values]


def previous_close_for_current_price(current_timestamp: str, candles: list[dict]) -> Decimal | None:
    ordered = candles_chronological(candles)
    current_dt = parse_iso_datetime(current_timestamp)
    latest_with_close = [
        (candle_datetime(candle), decimal_or_none(candle.get("closePrice")))
        for candle in ordered
    ]
    latest_with_close = [
        (timestamp, close)
        for timestamp, close in latest_with_close
        if timestamp is not None and close is not None
    ]
    if not latest_with_close:
        return None

    if current_dt is None:
        return latest_with_close[-1][1]

    current_date = current_dt.date()
    before_current_day = [
        (timestamp, close)
        for timestamp, close in latest_with_close
        if timestamp.date() < current_date
    ]
    if before_current_day:
        return before_current_day[-1][1]

    return latest_with_close[-1][1]


def change_from_candles(current_price: str, candles: list[dict], current_timestamp: str = "") -> str | None:
    current = decimal_or_none(current_price)
    if current is None:
        return None
    previous_close = previous_close_for_current_price(current_timestamp, candles)
    if previous_close is None:
        return None
    if previous_close == 0:
        return None
    rate = ((current - previous_close) / previous_close) * Decimal(100)
    return display_change(rate)


def enrich_candidates_with_toss_prices(candidates: list[dict]) -> tuple[list[dict], dict]:
    if not TOSS_LIVE_PRICES:
        return candidates, {
            "source": "sample",
            "enabled": False,
            "message": "TOSS_LIVE_PRICES가 꺼져 있어 샘플 가격을 사용합니다.",
        }

    if not toss_config_status()["readyForMarketData"]:
        return candidates, {
            "source": "sample",
            "enabled": True,
            "message": "토스증권 API 환경변수가 없어 샘플 가격을 사용합니다.",
        }

    symbols = [str(candidate.get("symbol", "")) for candidate in candidates]
    payload = fetch_toss_prices(symbols)
    prices = price_by_symbol(payload)
    enriched = []
    baseline_drift_count = 0
    for candidate in candidates:
        item = dict(candidate)
        price = prices.get(str(item.get("symbol")))
        if price:
            live_price = decimal_or_none(price["lastPrice"])
            sample_price = display_number_to_decimal(item.get("price"))
            baseline_warning = False
            baseline_difference = None
            if (
                TOSS_SAMPLE_PRICE_DRIFT_WARN_PERCENT is not None
                and live_price is not None
                and sample_price is not None
                and sample_price > 0
            ):
                baseline_difference = ((live_price - sample_price) / sample_price) * Decimal(100)
                baseline_warning = abs(baseline_difference) > TOSS_SAMPLE_PRICE_DRIFT_WARN_PERCENT
                if baseline_warning:
                    baseline_drift_count += 1
            item["price"] = display_price(str(price["lastPrice"]), str(price["currency"]))
            item["livePrice"] = {
                "lastPrice": str(price["lastPrice"]),
                "currency": str(price["currency"]),
                "timestamp": price.get("timestamp"),
                "source": "toss",
            }
            if baseline_warning and baseline_difference is not None:
                item["livePrice"].update({
                    "baselineWarning": True,
                    "baselineDifferencePercent": display_percent_abs(baseline_difference),
                    "samplePrice": candidate.get("price"),
                    "message": "초기 샘플 기준가와 차이가 커서 기준 데이터 갱신 여부를 확인하세요.",
                })
        else:
            item["livePrice"] = {"source": "sample", "message": "토스 현재가 응답에 종목이 없습니다."}
        enriched.append(item)

    return enriched, {
        "source": "toss",
        "enabled": True,
        "message": "토스증권 현재가를 반영했습니다.",
        "priceCount": len(prices),
        "baselineDriftCount": baseline_drift_count,
        "sampleDriftThresholdPercent": (
            display_percent_abs(TOSS_SAMPLE_PRICE_DRIFT_WARN_PERCENT)
            if TOSS_SAMPLE_PRICE_DRIFT_WARN_PERCENT is not None
            else ""
        ),
        "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
    }


def enrich_candidates_with_toss_candles(candidates: list[dict]) -> tuple[list[dict], dict]:
    if not TOSS_LIVE_CANDLES:
        return candidates, {
            "source": "sample",
            "enabled": False,
            "message": "TOSS_LIVE_CANDLES가 꺼져 있어 샘플 차트를 사용합니다.",
        }

    if not toss_config_status()["readyForMarketData"]:
        return candidates, {
            "source": "sample",
            "enabled": True,
            "message": "토스증권 API 환경변수가 없어 샘플 차트를 사용합니다.",
        }

    enriched = []
    candle_count = 0
    stale_count = 0
    for index, candidate in enumerate(candidates):
        item = dict(candidate)
        if index >= TOSS_CANDLE_MAX_CANDIDATES:
            item["liveCandles"] = {"source": "skipped", "message": "캔들 조회 후보 수 제한으로 샘플 차트를 사용합니다."}
            enriched.append(item)
            continue
        symbol = str(item.get("symbol", ""))
        payload = fetch_toss_candles(symbol, interval="1d", count=20)
        candles = candle_rows(payload)
        if candles:
            latest_timestamp = latest_candle_datetime(candles)
            if candles_are_stale(candles):
                stale_count += 1
                item["liveCandles"] = {
                    "source": "stale",
                    "interval": "1d",
                    "count": len(candles),
                    "latestTimestamp": latest_timestamp.isoformat(timespec="seconds") if latest_timestamp else candles[-1].get("timestamp"),
                    "message": "토스 일봉이 최신이 아니어서 샘플 차트와 기존 등락률을 유지합니다.",
                }
                enriched.append(item)
                continue
            candle_count += 1
            chart = candle_chart_points(candles)
            if chart:
                item["chart"] = chart
            volume_spike = candle_volume_spike(candles)
            if volume_spike is not None:
                trend = dict(item.get("trend", {}))
                trend["volumeSpike"] = display_multiplier(volume_spike)
                trend["volumeSource"] = "토스 일봉"
                latest_volume = decimal_or_none(candles_chronological(candles)[-1].get("volume"))
                trend["dailyVolume"] = display_compact_volume(latest_volume)
                item["trend"] = trend
            live_price = item.get("livePrice", {})
            if isinstance(live_price, dict) and live_price.get("source") == "toss":
                change = change_from_candles(
                    str(live_price.get("lastPrice")),
                    candles,
                    str(live_price.get("timestamp", "")),
                )
                if change:
                    item["change"] = change
                    item["livePrice"]["changeSource"] = "toss-candles"
            item["liveCandles"] = {
                "source": "toss",
                "interval": "1d",
                "count": len(candles),
                "latestTimestamp": latest_timestamp.isoformat(timespec="seconds") if latest_timestamp else candles[-1].get("timestamp"),
            }
        else:
            item["liveCandles"] = {"source": "sample", "message": "토스 캔들 응답이 비어 있습니다."}
        enriched.append(item)

    return enriched, {
        "source": "toss",
        "enabled": True,
        "message": "토스증권 일봉 캔들을 반영했습니다.",
        "candleCount": candle_count,
        "staleCount": stale_count,
        "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
    }


def enrich_candidates_with_toss_orderbook(candidates: list[dict]) -> tuple[list[dict], dict]:
    if not TOSS_LIVE_ORDERBOOK:
        return candidates, {
            "source": "sample",
            "enabled": False,
            "message": "TOSS_LIVE_ORDERBOOK이 꺼져 있어 샘플 호가 지표를 사용합니다.",
        }

    if not toss_config_status()["readyForMarketData"]:
        return candidates, {
            "source": "sample",
            "enabled": True,
            "message": "토스증권 API 환경변수가 없어 샘플 호가 지표를 사용합니다.",
        }

    enriched = []
    orderbook_count = 0
    skipped_count = 0
    for index, candidate in enumerate(candidates):
        item = dict(candidate)
        if index >= TOSS_ORDERBOOK_MAX_CANDIDATES:
            skipped_count += 1
            item["liveOrderbook"] = {"source": "skipped", "message": "호가 조회 후보 수 제한으로 샘플 지표를 사용합니다."}
            enriched.append(item)
            continue
        symbol = str(item.get("symbol", ""))
        summary = summarize_orderbook(fetch_toss_orderbook(symbol))
        if summary:
            orderbook_count += 1
            item["liveOrderbook"] = summary
            trend = dict(item.get("trend", {}))
            trend["orderbookPressure"] = summary["pressure"]
            trend["orderbookImbalance"] = summary["imbalancePercent"]
            trend["spread"] = summary["spreadPercent"] or "-"
            item["trend"] = trend
        else:
            item["liveOrderbook"] = {"source": "sample", "message": "토스 호가 응답이 비어 있습니다."}
        enriched.append(item)

    return enriched, {
        "source": "toss",
        "enabled": True,
        "message": "토스증권 호가를 반영했습니다.",
        "orderbookCount": orderbook_count,
        "skippedCount": skipped_count,
        "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
    }


def enrich_candidates_with_toss_trades(candidates: list[dict]) -> tuple[list[dict], dict]:
    if not TOSS_LIVE_TRADES:
        return candidates, {
            "source": "sample",
            "enabled": False,
            "message": "TOSS_LIVE_TRADES가 꺼져 있어 샘플 체결 지표를 사용합니다.",
        }

    if not toss_config_status()["readyForMarketData"]:
        return candidates, {
            "source": "sample",
            "enabled": True,
            "message": "토스증권 API 환경변수가 없어 샘플 체결 지표를 사용합니다.",
        }

    enriched = []
    trade_count = 0
    skipped_count = 0
    for index, candidate in enumerate(candidates):
        item = dict(candidate)
        if index >= TOSS_TRADES_MAX_CANDIDATES:
            skipped_count += 1
            item["liveTrades"] = {"source": "skipped", "message": "체결 조회 후보 수 제한으로 샘플 지표를 사용합니다."}
            enriched.append(item)
            continue
        symbol = str(item.get("symbol", ""))
        summary = summarize_trades(fetch_toss_trades(symbol, count=TOSS_TRADES_COUNT))
        if summary:
            trade_count += 1
            item["liveTrades"] = summary
            trend = dict(item.get("trend", {}))
            trend["tradePressure"] = summary["pressure"]
            trend["tradeBias"] = summary["biasPercent"]
            trend["recentTradeVolume"] = display_compact_volume(decimal_or_none(summary["totalVolume"]))
            item["trend"] = trend
        else:
            item["liveTrades"] = {"source": "sample", "message": "토스 체결 응답이 비어 있습니다."}
        enriched.append(item)

    return enriched, {
        "source": "toss",
        "enabled": True,
        "message": "토스증권 최근 체결을 반영했습니다.",
        "tradeCount": trade_count,
        "skippedCount": skipped_count,
        "requestCount": TOSS_TRADES_COUNT,
        "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
    }


def dart_json_request(path: str, params: dict[str, object]) -> dict:
    if not DART_API_KEY:
        raise ValueError("DART_API_KEY가 필요합니다.")
    query_params = {"crtfc_key": DART_API_KEY}
    query_params.update(params)
    query = urlencode(query_params)
    request = Request(f"{DART_BASE_URL}/{path}?{query}", method="GET")
    with urlopen(request, timeout=DART_REQUEST_TIMEOUT_SECONDS) as response:
        payload = json.loads(response.read().decode("utf-8"))

    status = str(payload.get("status", ""))
    if status not in {"000", "013"}:
        raise ValueError(f"OpenDART 오류 {status}: {payload.get('message', '알 수 없는 오류')}")
    return payload


def parse_dart_corp_code_payload(raw: bytes) -> dict[str, dict]:
    try:
        with zipfile.ZipFile(BytesIO(raw)) as archive:
            xml_name = archive.namelist()[0]
            xml_bytes = archive.read(xml_name)
    except zipfile.BadZipFile:
        xml_bytes = raw

    root = ET.fromstring(xml_bytes)
    by_stock_code: dict[str, dict] = {}
    for item in root.findall("list"):
        stock_code = (item.findtext("stock_code") or "").strip()
        if not stock_code:
            continue
        by_stock_code[stock_code] = {
            "corpCode": (item.findtext("corp_code") or "").strip(),
            "corpName": (item.findtext("corp_name") or "").strip(),
            "corpEngName": (item.findtext("corp_eng_name") or "").strip(),
            "stockCode": stock_code,
            "modifyDate": (item.findtext("modify_date") or "").strip(),
        }
    return by_stock_code


def load_dart_corp_codes() -> dict[str, dict]:
    cached_payload = CORP_CODE_CACHE.get("payload")
    if isinstance(cached_payload, dict):
        return cached_payload
    if DART_CORP_CODE_FILE.exists():
        payload = read_json(DART_CORP_CODE_FILE, {"byStockCode": {}})
        mapping = payload.get("byStockCode", {})
        if isinstance(mapping, dict):
            CORP_CODE_CACHE["payload"] = mapping
            return mapping
    return {}


def fetch_dart_corp_codes(force_refresh: bool = False) -> dict[str, dict]:
    if not force_refresh:
        cached = load_dart_corp_codes()
        if cached:
            return cached
    if not DART_API_KEY:
        raise ValueError("DART_API_KEY가 필요합니다.")

    query = urlencode({"crtfc_key": DART_API_KEY})
    request = Request(f"{DART_BASE_URL}/corpCode.xml?{query}", method="GET")
    with urlopen(request, timeout=DART_CORP_CODE_TIMEOUT_SECONDS) as response:
        raw = response.read()
    mapping = parse_dart_corp_code_payload(raw)
    write_json(
        DART_CORP_CODE_FILE,
        {
            "generatedAt": datetime.now(KST).isoformat(timespec="seconds"),
            "count": len(mapping),
            "byStockCode": mapping,
        },
    )
    CORP_CODE_CACHE["payload"] = mapping
    return mapping


def dart_corp_code_for_symbol(symbol: str) -> dict | None:
    symbol = symbol.strip()
    if not symbol:
        return None
    mapping = fetch_dart_corp_codes()
    return mapping.get(symbol)


def normalize_dart_disclosure(item: dict) -> dict:
    receipt_no = str(item.get("rcept_no", ""))
    report_name = str(item.get("report_nm", ""))
    return {
        "corpName": item.get("corp_name"),
        "corpCode": item.get("corp_code"),
        "stockCode": item.get("stock_code"),
        "reportName": report_name,
        "receiptNo": receipt_no,
        "receivedDate": item.get("rcept_dt"),
        "filerName": item.get("flr_nm"),
        "corpClass": item.get("corp_cls"),
        "remark": item.get("rm"),
        "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={receipt_no}" if receipt_no else "",
    }


def fetch_dart_disclosures(symbol: str, days: int | None = None) -> dict:
    symbol = symbol.strip()
    if not symbol:
        return {"symbol": symbol, "corpCode": None, "items": []}
    days = DART_DISCLOSURE_LOOKBACK_DAYS if days is None else max(1, int(days))

    cache_key = (symbol, days)
    cached = DISCLOSURE_CACHE.get(cache_key)
    if cached:
        expires_at = cached.get("expires_at")
        if isinstance(expires_at, datetime) and expires_at > datetime.now(timezone.utc):
            return cached["payload"]  # type: ignore[return-value]

    corp = dart_corp_code_for_symbol(symbol)
    if not corp:
        return {"symbol": symbol, "corpCode": None, "items": [], "message": "DART 고유번호를 찾지 못했습니다."}

    today = datetime.now(KST).date()
    begin = today - timedelta(days=days)
    payload = dart_json_request(
        "list.json",
        {
            "corp_code": corp["corpCode"],
            "bgn_de": begin.strftime("%Y%m%d"),
            "end_de": today.strftime("%Y%m%d"),
            "last_reprt_at": "N",
            "sort": "date",
            "sort_mth": "desc",
            "page_no": "1",
            "page_count": "10",
        },
    )
    rows = payload.get("list", []) if payload.get("status") == "000" else []
    result = {
        "symbol": symbol,
        "corpCode": corp["corpCode"],
        "corpName": corp["corpName"],
        "lookbackDays": days,
        "items": [normalize_dart_disclosure(item) for item in rows],
        "source": "opendart",
    }
    DISCLOSURE_CACHE[cache_key] = {
        "payload": result,
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=DART_DISCLOSURE_CACHE_SECONDS),
    }
    return result


def disclosure_summary_text(disclosure: dict) -> str:
    items = disclosure.get("items", [])
    if not items:
        return "최근 OpenDART 공시는 발견되지 않았습니다."
    first = items[0]
    return f"최근 OpenDART 공시: {first.get('reportName')} ({first.get('receivedDate')})"


def enrich_candidates_with_dart_disclosures(candidates: list[dict]) -> tuple[list[dict], dict]:
    if not DART_LIVE_DISCLOSURES:
        return candidates, {
            "source": "sample",
            "enabled": False,
            "message": "DART_LIVE_DISCLOSURES가 꺼져 있어 샘플 공시 메모를 사용합니다.",
        }

    if not dart_config_status()["readyForDisclosures"]:
        return candidates, {
            "source": "sample",
            "enabled": True,
            "message": "DART_API_KEY가 없어 샘플 공시 메모를 사용합니다.",
        }

    enriched = []
    disclosure_count = 0
    domestic_count = 0
    for index, candidate in enumerate(candidates):
        item = dict(candidate)
        if index >= DART_DISCLOSURE_MAX_CANDIDATES:
            item["liveDisclosures"] = {"source": "skipped", "message": "공시 조회 후보 수 제한으로 샘플 메모를 사용합니다."}
            enriched.append(item)
            continue
        symbol = str(item.get("symbol", ""))
        is_domestic = item.get("market") == "KR" and symbol.isdigit() and len(symbol) == 6
        if not is_domestic:
            item["liveDisclosures"] = {"source": "not-applicable", "message": "국내 상장 종목만 OpenDART를 조회합니다."}
            enriched.append(item)
            continue

        domestic_count += 1
        disclosure = fetch_dart_disclosures(symbol)
        items = disclosure.get("items", [])
        disclosure_count += len(items)
        item["liveDisclosures"] = disclosure
        if isinstance(item.get("disclosures"), list):
            item["disclosures"] = [disclosure_summary_text(disclosure), *item["disclosures"]]
        enriched.append(item)

    return enriched, {
        "source": "opendart",
        "enabled": True,
        "message": "OpenDART 공시를 반영했습니다.",
        "domesticCount": domestic_count,
        "disclosureCount": disclosure_count,
        "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
    }


def clean_news_text(value: str) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def parse_news_date(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = parsedate_to_datetime(value)
        return parsed.astimezone(KST).isoformat(timespec="seconds")
    except (TypeError, ValueError, IndexError, OverflowError):
        return value


def parse_iso_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(KST)
    except (TypeError, ValueError):
        return None


def latest_candle_datetime(candles: list[dict]) -> datetime | None:
    timestamps = [
        parsed
        for parsed in (parse_iso_datetime(str(candle.get("timestamp", ""))) for candle in candles)
        if parsed is not None
    ]
    return max(timestamps) if timestamps else None


def candles_are_stale(candles: list[dict]) -> bool:
    latest = latest_candle_datetime(candles)
    if latest is None:
        return True
    return latest < datetime.now(KST) - timedelta(days=TOSS_CANDLE_MAX_STALENESS_DAYS)


def fetch_naver_news(query: str, display: int | None = None, start: int = 1, sort: str = "date") -> dict:
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        raise ValueError("NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET이 필요합니다.")
    query = query.strip()
    if not query:
        return {"items": [], "total": 0, "display": 0, "start": start}
    display = NAVER_NEWS_DISPLAY if display is None else max(1, min(int(display), 100))
    start = max(1, min(int(start), 1000))
    if sort not in {"date", "sim"}:
        sort = "date"

    cache_key = (query, display, start, sort)
    cached = NEWS_CACHE.get(cache_key)
    if cached:
        expires_at = cached.get("expires_at")
        if isinstance(expires_at, datetime) and expires_at > datetime.now(timezone.utc):
            return cached["payload"]  # type: ignore[return-value]

    params = urlencode({"query": query, "display": display, "start": start, "sort": sort})
    request = Request(
        f"{NAVER_NEWS_BASE_URL}?{params}",
        headers={
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
        },
        method="GET",
    )
    with urlopen(request, timeout=NAVER_REQUEST_TIMEOUT_SECONDS) as response:
        payload = json.loads(response.read().decode("utf-8"))
    NEWS_CACHE[cache_key] = {
        "payload": payload,
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=NAVER_NEWS_CACHE_SECONDS),
    }
    return payload


def normalize_news_item(item: dict) -> dict:
    original_url = str(item.get("originallink") or item.get("link") or "")
    naver_url = str(item.get("link") or original_url)
    return {
        "title": clean_news_text(str(item.get("title", ""))),
        "summary": clean_news_text(str(item.get("description", ""))),
        "originalUrl": original_url,
        "naverUrl": naver_url,
        "sourceHost": urlparse(original_url).netloc if original_url else "",
        "publishedAt": parse_news_date(str(item.get("pubDate", ""))),
    }


def naver_query_for_candidate(candidate: dict) -> str:
    name = str(candidate.get("name", "")).strip()
    symbol = str(candidate.get("symbol", "")).strip()
    market = str(candidate.get("market", "")).strip()
    if market == "KR":
        return name or symbol
    return f"{name} 주가".strip() if name else symbol


def source_from_news_item(item: dict) -> dict:
    host = item.get("sourceHost") or "뉴스"
    published = item.get("publishedAt") or ""
    time_text = published[11:16] if len(published) >= 16 else ""
    return {
        "title": item.get("title", ""),
        "publisher": host,
        "time": time_text,
        "url": item.get("newsUrl") or item.get("naverUrl") or item.get("originalUrl") or "",
    }


GLOBAL_NEWS_ALIASES = {
    "005930": ["Samsung Electronics", "Samsung HBM"],
    "000660": ["SK hynix", "SK Hynix HBM"],
    "316140": ["Woori Financial Group"],
    "035720": ["Kakao Corp"],
    "AAPL": ["Apple", "AAPL"],
    "NVDA": ["NVIDIA", "NVDA"],
}


def gdelt_phrase(value: str) -> str:
    text = re.sub(r"\s+", " ", clean_news_text(value)).strip()
    if not text:
        return ""
    if re.search(r"\s", text):
        return f'"{text}"'
    return text


def gdelt_query_for_candidate(candidate: dict) -> str:
    symbol = str(candidate.get("symbol", "")).strip()
    name = str(candidate.get("name", "")).strip()
    market = str(candidate.get("market", "")).strip()
    aliases = GLOBAL_NEWS_ALIASES.get(symbol, [])
    terms = unique_texts([*aliases, name, symbol], limit=4)
    phrases = [gdelt_phrase(term) for term in terms if gdelt_phrase(term)]
    if not phrases:
        return symbol or name
    if market == "US" and len(phrases) > 1:
        return f"({' OR '.join(phrases[:3])}) stock"
    if len(phrases) > 1:
        return f"({' OR '.join(phrases[:3])})"
    return phrases[0]


def parse_gdelt_date(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%d%H%M%S", "%Y%m%dT%H%M%S"):
        try:
            parsed = datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
            return parsed.astimezone(KST).isoformat(timespec="seconds")
        except ValueError:
            continue
    parsed = parse_iso_datetime(text)
    return parsed.isoformat(timespec="seconds") if parsed else text


def fetch_gdelt_news(query: str, display: int | None = None, timespan: str | None = None, sort: str = "datedesc") -> dict:
    global GDELT_LAST_REQUEST_AT
    query = query.strip()
    if not query:
        return {"articles": [], "query": query}
    display = GDELT_NEWS_DISPLAY if display is None else max(1, min(int(display), 250))
    timespan = (timespan or GDELT_NEWS_TIMESPAN).strip() or "1week"
    if sort not in {"datedesc", "dateasc", "hybridrel"}:
        sort = "datedesc"

    cache_key = (query, display, timespan, sort)
    cached = GDELT_NEWS_CACHE.get(cache_key)
    if cached:
        expires_at = cached.get("expires_at")
        if isinstance(expires_at, datetime) and expires_at > datetime.now(timezone.utc):
            return cached["payload"]  # type: ignore[return-value]

    params = urlencode(
        {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "maxrecords": display,
            "timespan": timespan,
            "sort": sort,
        }
    )
    request = Request(f"{GDELT_DOC_BASE_URL}?{params}", headers={"User-Agent": "market-signal-desk/1.0"}, method="GET")
    if GDELT_REQUEST_SPACING_SECONDS > 0:
        with GDELT_RATE_LOCK:
            now = datetime.now(timezone.utc)
            elapsed = (now - GDELT_LAST_REQUEST_AT).total_seconds()
            wait_seconds = GDELT_REQUEST_SPACING_SECONDS - elapsed
            if wait_seconds > 0:
                time.sleep(wait_seconds)
            GDELT_LAST_REQUEST_AT = datetime.now(timezone.utc)
    with urlopen(request, timeout=GDELT_REQUEST_TIMEOUT_SECONDS) as response:
        payload = json.loads(response.read().decode("utf-8"))
    payload["query"] = query
    payload["display"] = display
    payload["timespan"] = timespan
    GDELT_NEWS_CACHE[cache_key] = {
        "payload": payload,
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=GDELT_NEWS_CACHE_SECONDS),
    }
    return payload


def normalize_gdelt_news_item(item: dict) -> dict:
    original_url = str(item.get("url") or item.get("url_mobile") or "")
    source_host = clean_news_text(str(item.get("domain") or urlparse(original_url).netloc))
    return {
        "title": clean_news_text(str(item.get("title", ""))),
        "summary": clean_news_text(str(item.get("snippet") or item.get("title", ""))),
        "originalUrl": original_url,
        "newsUrl": original_url,
        "sourceHost": source_host,
        "language": clean_news_text(str(item.get("language", ""))),
        "sourceCountry": clean_news_text(str(item.get("sourcecountry", ""))),
        "publishedAt": parse_gdelt_date(str(item.get("seendate") or item.get("date") or "")),
    }


def enrich_candidates_with_gdelt_news(candidates: list[dict]) -> tuple[list[dict], dict]:
    if not GDELT_LIVE_NEWS:
        return candidates, {
            "source": "sample",
            "enabled": False,
            "message": "GDELT_LIVE_NEWS가 꺼져 있어 글로벌 뉴스 보강을 건너뜁니다.",
        }

    enriched = []
    news_count = 0
    queried_count = 0
    for index, candidate in enumerate(candidates):
        item = dict(candidate)
        if index >= GDELT_NEWS_MAX_CANDIDATES:
            item["globalNews"] = {"source": "skipped", "message": "글로벌 뉴스 조회 후보 수 제한으로 건너뜀"}
            enriched.append(item)
            continue

        query = gdelt_query_for_candidate(item)
        payload = fetch_gdelt_news(query, display=GDELT_NEWS_DISPLAY, timespan=GDELT_NEWS_TIMESPAN)
        queried_count += 1
        articles = payload.get("articles", [])
        if not isinstance(articles, list):
            articles = []
        normalized = [normalize_gdelt_news_item(news_item) for news_item in articles if isinstance(news_item, dict)]
        normalized = [news_item for news_item in normalized if news_item.get("title")]
        news_count += len(normalized)
        item["globalNews"] = {
            "source": "gdelt",
            "query": query,
            "display": payload.get("display", len(normalized)),
            "timespan": payload.get("timespan", GDELT_NEWS_TIMESPAN),
            "items": normalized,
        }
        if normalized:
            live_sources = [source_from_news_item(news_item) for news_item in normalized[:3]]
            item["sources"] = [*live_sources, *item.get("sources", [])][:6]
            trend = dict(item.get("trend", {}))
            existing_count = bounded_int(trend.get("newsCount", 0), 0, 1_000_000)
            if item.get("market") != "KR" or not existing_count:
                trend["newsCount"] = max(existing_count, len(normalized))
            trend["globalNewsCount"] = len(normalized)
            trend["globalNewsSource"] = "GDELT"
            item["trend"] = trend
        enriched.append(item)

    return enriched, {
        "source": "gdelt",
        "enabled": True,
        "message": "GDELT 글로벌 뉴스 결과를 반영했습니다.",
        "queriedCount": queried_count,
        "newsCount": news_count,
        "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
    }


def enrich_candidates_with_naver_news(candidates: list[dict]) -> tuple[list[dict], dict]:
    if not NAVER_LIVE_NEWS:
        return candidates, {
            "source": "sample",
            "enabled": False,
            "message": "NAVER_LIVE_NEWS가 꺼져 있어 샘플 뉴스를 사용합니다.",
        }

    if not naver_news_config_status()["readyForNews"]:
        return candidates, {
            "source": "sample",
            "enabled": True,
            "message": "NAVER_CLIENT_ID/SECRET이 없어 샘플 뉴스를 사용합니다.",
        }

    enriched = []
    news_count = 0
    queried_count = 0
    for index, candidate in enumerate(candidates):
        item = dict(candidate)
        if index >= NAVER_NEWS_MAX_CANDIDATES:
            item["liveNews"] = {"source": "skipped", "message": "뉴스 조회 후보 수 제한으로 건너뜀"}
            enriched.append(item)
            continue

        query = naver_query_for_candidate(item)
        payload = fetch_naver_news(query, display=NAVER_NEWS_DISPLAY, sort="date")
        queried_count += 1
        normalized = [normalize_news_item(news_item) for news_item in payload.get("items", [])]
        normalized = [news_item for news_item in normalized if news_item.get("title")]
        news_count += len(normalized)
        item["liveNews"] = {
            "source": "naver",
            "query": query,
            "total": payload.get("total", 0),
            "display": payload.get("display", len(normalized)),
            "items": normalized,
        }
        if normalized:
            live_sources = [source_from_news_item(news_item) for news_item in normalized[:3]]
            item["sources"] = [*live_sources, *item.get("sources", [])][:6]
            trend = dict(item.get("trend", {}))
            trend["newsCount"] = int(payload.get("total", trend.get("newsCount", 0)) or 0)
            item["trend"] = trend
        enriched.append(item)

    return enriched, {
        "source": "naver",
        "enabled": True,
        "message": "네이버 뉴스 검색 결과를 반영했습니다.",
        "queriedCount": queried_count,
        "newsCount": news_count,
        "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
    }


def bounded_int(value, minimum: int = 0, maximum: int = 100) -> int:
    try:
        number = int(round(float(value)))
    except (TypeError, ValueError):
        number = minimum
    return max(minimum, min(maximum, number))


def text_list(values, limit: int = 5) -> list[str]:
    if not isinstance(values, list):
        return []
    cleaned = []
    for value in values:
        text = clean_news_text(str(value))
        if text:
            cleaned.append(text)
        if len(cleaned) >= limit:
            break
    return cleaned


def unique_texts(values, limit: int = 8) -> list[str]:
    unique = []
    seen = set()
    for value in values:
        text = clean_news_text(str(value))
        key = re.sub(r"\s+", "", text).lower()
        if not text or key in seen:
            continue
        seen.add(key)
        unique.append(text)
        if len(unique) >= limit:
            break
    return unique


def compact_sources(candidate: dict) -> list[dict]:
    sources = candidate.get("sources", [])
    if not isinstance(sources, list):
        return []
    compacted = []
    for source in sources[:6]:
        if not isinstance(source, dict):
            continue
        compacted.append(
            {
                "title": clean_news_text(str(source.get("title", ""))),
                "publisher": clean_news_text(str(source.get("publisher", ""))),
                "time": clean_news_text(str(source.get("time", ""))),
                "url": str(source.get("url", ""))[:220],
            }
        )
    return compacted


def compact_live_news(candidate: dict) -> list[dict]:
    compacted = []
    for news_key in ("liveNews", "globalNews"):
        live_news = candidate.get(news_key, {})
        if not isinstance(live_news, dict):
            continue
        items = live_news.get("items", [])
        if not isinstance(items, list):
            continue
        for item in items[:5]:
            if not isinstance(item, dict):
                continue
            compacted.append(
                {
                    "title": clean_news_text(str(item.get("title", ""))),
                    "summary": clean_news_text(str(item.get("summary", ""))),
                    "sourceHost": clean_news_text(str(item.get("sourceHost", ""))),
                    "publishedAt": clean_news_text(str(item.get("publishedAt", ""))),
                    "provider": news_key,
                }
            )
            if len(compacted) >= 6:
                return compacted
    return compacted


def compact_live_disclosures(candidate: dict) -> list[dict]:
    live_disclosures = candidate.get("liveDisclosures", {})
    if not isinstance(live_disclosures, dict):
        return []
    items = live_disclosures.get("items", [])
    if not isinstance(items, list):
        return []
    compacted = []
    for item in items[:5]:
        if not isinstance(item, dict):
            continue
        compacted.append(
            {
                "reportName": clean_news_text(str(item.get("reportName", ""))),
                "receivedDate": clean_news_text(str(item.get("receivedDate", ""))),
                "corpName": clean_news_text(str(item.get("corpName", ""))),
            }
        )
    return compacted


def analysis_input_for_candidate(candidate: dict) -> dict:
    return {
        "symbol": candidate.get("symbol"),
        "name": candidate.get("name"),
        "market": candidate.get("market"),
        "price": candidate.get("price"),
        "change": candidate.get("change"),
        "headline": candidate.get("headline"),
        "tags": text_list(candidate.get("tags", []), limit=8),
        "score": candidate.get("score", {}),
        "totalScore": candidate.get("totalScore"),
        "triggerReadiness": candidate.get("triggerReadiness"),
        "preopenPriority": candidate.get("preopenPriority"),
        "thesis": candidate.get("thesis"),
        "why": text_list(candidate.get("why", []), limit=5),
        "entryConditions": text_list(candidate.get("entryConditions", []), limit=6),
        "noEntry": text_list(candidate.get("noEntry", []), limit=6),
        "stopRules": text_list(candidate.get("stopRules", []), limit=5),
        "trend": candidate.get("trend", {}),
        "sources": compact_sources(candidate),
        "liveNews": compact_live_news(candidate),
        "disclosures": text_list(candidate.get("disclosures", []), limit=6),
        "liveDisclosures": compact_live_disclosures(candidate),
    }


def openai_analysis_cache_key(candidate: dict) -> str:
    basis = json.dumps(analysis_input_for_candidate(candidate), ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(f"{OPENAI_MODEL}:{basis}".encode("utf-8")).hexdigest()


def openai_analysis_schema() -> dict:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "summary",
            "eventType",
            "sentiment",
            "impactScore",
            "riskScore",
            "confidenceScore",
            "actionBias",
            "catalystBullets",
            "riskFlags",
            "entryConditions",
            "noEntryConditions",
            "stopRules",
            "evidenceNotes",
            "disclaimer",
        ],
        "properties": {
            "summary": {"type": "string"},
            "eventType": {"type": "string"},
            "sentiment": {"type": "string", "enum": ["positive", "neutral", "negative", "mixed"]},
            "impactScore": {"type": "integer", "minimum": 0, "maximum": 100},
            "riskScore": {"type": "integer", "minimum": 0, "maximum": 100},
            "confidenceScore": {"type": "integer", "minimum": 0, "maximum": 100},
            "actionBias": {"type": "string", "enum": ["watch", "wait", "avoid"]},
            "catalystBullets": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 5},
            "riskFlags": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 5},
            "entryConditions": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 6},
            "noEntryConditions": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 6},
            "stopRules": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 5},
            "evidenceNotes": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 5},
            "disclaimer": {"type": "string"},
        },
    }


def response_output_text(payload: dict) -> str:
    direct = payload.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct

    parts = []
    output_items = payload.get("output", [])
    if isinstance(output_items, list):
        for output_item in output_items:
            if not isinstance(output_item, dict):
                continue
            content_items = output_item.get("content", [])
            if not isinstance(content_items, list):
                continue
            for content_item in content_items:
                if not isinstance(content_item, dict):
                    continue
                text = content_item.get("text")
                if isinstance(text, str):
                    parts.append(text)
    return "\n".join(parts).strip()


def normalize_analysis_payload(payload: dict, source: str) -> dict:
    action_bias = payload.get("actionBias") if payload.get("actionBias") in {"watch", "wait", "avoid"} else "wait"
    sentiment = payload.get("sentiment") if payload.get("sentiment") in {"positive", "neutral", "negative", "mixed"} else "mixed"
    normalized = {
        "summary": clean_news_text(str(payload.get("summary", "")))[:600],
        "eventType": display_event_type(payload.get("eventType", "혼합 이벤트"))[:80],
        "sentiment": sentiment,
        "impactScore": bounded_int(payload.get("impactScore")),
        "riskScore": bounded_int(payload.get("riskScore")),
        "confidenceScore": bounded_int(payload.get("confidenceScore")),
        "actionBias": action_bias,
        "catalystBullets": unique_texts(text_list(payload.get("catalystBullets", []), limit=8), limit=5),
        "riskFlags": unique_texts(text_list(payload.get("riskFlags", []), limit=8), limit=5),
        "entryConditions": unique_texts(text_list(payload.get("entryConditions", []), limit=8), limit=6),
        "noEntryConditions": unique_texts(text_list(payload.get("noEntryConditions", []), limit=8), limit=6),
        "stopRules": unique_texts(text_list(payload.get("stopRules", []), limit=8), limit=5),
        "evidenceNotes": unique_texts(text_list(payload.get("evidenceNotes", []), limit=8), limit=5),
        "disclaimer": clean_news_text(
            str(payload.get("disclaimer", "투자 판단 보조 정보이며 매수·매도 추천이 아닙니다."))
        )[:220],
        "source": source,
        "model": OPENAI_MODEL if source == "openai" else "local-rules",
        "generatedAt": datetime.now(KST).isoformat(timespec="seconds"),
    }
    if not normalized["summary"]:
        normalized["summary"] = "뉴스, 공시, 가격 반응을 함께 확인해야 하는 후보입니다."
    if not normalized["catalystBullets"]:
        normalized["catalystBullets"] = ["뉴스와 가격 반응의 방향성이 유지되는지 확인합니다."]
    if not normalized["riskFlags"]:
        normalized["riskFlags"] = ["장 초반 변동성과 거래대금 감소 여부를 확인합니다."]
    if not normalized["entryConditions"]:
        normalized["entryConditions"] = ["가격과 거래대금이 동시에 기준을 충족할 때만 관찰합니다."]
    if not normalized["noEntryConditions"]:
        normalized["noEntryConditions"] = ["뉴스만 많고 가격 반응이 약하면 진입하지 않습니다."]
    if not normalized["stopRules"]:
        normalized["stopRules"] = ["진입 기준가를 이탈하면 관찰을 중단합니다."]
    if not normalized["evidenceNotes"]:
        normalized["evidenceNotes"] = ["현재 화면에 수집된 뉴스, 공시, 가격 데이터를 기준으로 판단했습니다."]
    return normalized


def display_event_type(value) -> str:
    text = clean_news_text(str(value or "혼합 이벤트"))
    lower = text.lower()
    if "sector" in lower and ("re-rating" in lower or "rerating" in lower):
        return "섹터 재평가"
    if "demand" in lower and ("expectation" in lower or "growth" in lower):
        return "수요 기대"
    if "supply" in lower:
        return "공급 이슈"
    if "earnings" in lower:
        return "실적 기대"
    if "policy" in lower or "regulation" in lower:
        return "정책/규제"
    if re.search(r"[_A-Za-z]", text) and not re.search(r"[가-힣]", text):
        return text.replace("_", " ").replace("-", " ").strip().title()
    return text


def display_sentiment(value) -> str:
    return {
        "positive": "긍정",
        "neutral": "중립",
        "negative": "부정",
        "mixed": "혼조",
    }.get(str(value), str(value))


def local_candidate_analysis(candidate: dict) -> dict:
    score = bounded_int(candidate.get("totalScore", score_candidate(candidate)))
    readiness = bounded_int(candidate.get("triggerReadiness", 0))
    score_detail = candidate.get("score", {})
    if not isinstance(score_detail, dict):
        score_detail = {}
    risk_penalty = bounded_int(score_detail.get("riskPenalty", 0), 0, 30)
    heat_penalty = bounded_int(score_detail.get("heatPenalty", 0), 0, 30)
    risk_score = bounded_int((risk_penalty * 4) + (heat_penalty * 3) + max(0, 60 - readiness) // 2)
    impact_score = bounded_int((score * 0.7) + (readiness * 0.3))
    confidence_score = bounded_int(45 + min(score, 80) * 0.35 + min(len(candidate.get("sources", [])), 6) * 3)
    change = str(candidate.get("change", ""))
    sentiment = "negative" if change.startswith("-") else "positive" if score >= 70 else "mixed"
    if risk_score >= 70 or score < 50:
        action_bias = "avoid"
    elif readiness < 70 or heat_penalty >= 6:
        action_bias = "wait"
    else:
        action_bias = "watch"

    tags = text_list(candidate.get("tags", []), limit=3)
    event_type = tags[0] if tags else "뉴스·가격 반응"
    payload = {
        "summary": candidate.get("thesis") or candidate.get("headline") or "후보 종목의 재료와 가격 반응을 확인합니다.",
        "eventType": event_type,
        "sentiment": sentiment,
        "impactScore": impact_score,
        "riskScore": risk_score,
        "confidenceScore": confidence_score,
        "actionBias": action_bias,
        "catalystBullets": text_list(candidate.get("why", []), limit=5),
        "riskFlags": [
            *text_list(candidate.get("noEntry", []), limit=3),
            *text_list(candidate.get("disclosures", []), limit=2),
        ],
        "entryConditions": text_list(candidate.get("entryConditions", []), limit=6),
        "noEntryConditions": text_list(candidate.get("noEntry", []), limit=6),
        "stopRules": text_list(candidate.get("stopRules", []), limit=5),
        "evidenceNotes": [
            f"후보 점수 {score}/100, 트리거 준비도 {readiness}/100",
            f"뉴스 근거 {len(candidate.get('sources', []))}건, 공시/리스크 메모 {len(candidate.get('disclosures', []))}건",
        ],
        "disclaimer": "투자 판단 보조 정보이며 매수·매도 추천이 아닙니다.",
    }
    return normalize_analysis_payload(payload, "local")


def fetch_openai_analysis(candidate: dict) -> dict:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY가 필요합니다.")

    cache_key = openai_analysis_cache_key(candidate)
    cached = ANALYSIS_CACHE.get(cache_key)
    if cached:
        expires_at = cached.get("expires_at")
        if isinstance(expires_at, datetime) and expires_at > datetime.now(timezone.utc):
            return cached["payload"]  # type: ignore[return-value]

    request_payload = {
        "model": OPENAI_MODEL,
        "reasoning": {"effort": "low"},
        "instructions": (
            "너는 한국어 주식 리서치 보조 엔진이다. 제공된 뉴스, 공시, 가격 반응만 근거로 "
            "단기 관찰 조건과 리스크를 정리한다. 매수, 매도, 수익 보장 표현은 금지한다. "
            "확정적 예측 대신 조건부 관찰, 보류, 회피 관점으로 답한다. "
            "eventType은 '섹터 재평가', '수요 기대', '실적 기대'처럼 화면에 바로 노출 가능한 짧은 한국어 라벨로 작성한다."
        ),
        "input": json.dumps(analysis_input_for_candidate(candidate), ensure_ascii=False),
        "text": {
            "format": {
                "type": "json_schema",
                "name": "market_signal_analysis",
                "schema": openai_analysis_schema(),
                "strict": True,
            }
        },
    }
    encoded = json.dumps(request_payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        f"{OPENAI_BASE_URL}/responses",
        data=encoded,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=OPENAI_REQUEST_TIMEOUT_SECONDS) as response:
        response_payload = json.loads(response.read().decode("utf-8"))

    output_text = response_output_text(response_payload)
    if not output_text:
        raise ValueError("OpenAI 응답에서 분석 JSON을 찾지 못했습니다.")
    analysis = normalize_analysis_payload(json.loads(output_text), "openai")
    ANALYSIS_CACHE[cache_key] = {
        "payload": analysis,
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=OPENAI_ANALYSIS_CACHE_SECONDS),
    }
    return analysis


def apply_analysis_to_candidate(candidate: dict, analysis: dict) -> dict:
    item = dict(candidate)
    item["aiAnalysis"] = analysis
    item["thesis"] = analysis.get("summary") or item.get("thesis", "")
    if analysis.get("catalystBullets"):
        item["why"] = analysis["catalystBullets"]
    if analysis.get("entryConditions"):
        item["entryConditions"] = analysis["entryConditions"]
    if analysis.get("noEntryConditions"):
        item["noEntry"] = analysis["noEntryConditions"]
    if analysis.get("stopRules"):
        item["stopRules"] = analysis["stopRules"]
    risk_flags = analysis.get("riskFlags", [])
    if isinstance(risk_flags, list) and risk_flags:
        item["disclosures"] = unique_texts(
            [*risk_flags, *text_list(item.get("disclosures", []), limit=6)],
            limit=6,
        )
    else:
        item["disclosures"] = unique_texts(text_list(item.get("disclosures", []), limit=8), limit=6)

    item["why"] = unique_texts(text_list(item.get("why", []), limit=8), limit=5)
    item["entryConditions"] = unique_texts(text_list(item.get("entryConditions", []), limit=8), limit=6)
    item["noEntry"] = unique_texts(text_list(item.get("noEntry", []), limit=8), limit=6)
    item["stopRules"] = unique_texts(text_list(item.get("stopRules", []), limit=8), limit=5)

    tags = []
    for value in [analysis.get("eventType"), display_sentiment(analysis.get("sentiment")), *item.get("tags", [])]:
        text = display_event_type(value)
        if text and text not in tags:
            tags.append(text)
    item["tags"] = tags[:8]
    return item


def enrich_candidates_with_openai_analysis(candidates: list[dict]) -> tuple[list[dict], dict]:
    if not OPENAI_ANALYSIS_ENABLED:
        enriched = [apply_analysis_to_candidate(candidate, local_candidate_analysis(candidate)) for candidate in candidates]
        return enriched, {
            "source": "local",
            "enabled": False,
            "message": "OPENAI_ANALYSIS_ENABLED가 꺼져 있어 로컬 분석을 사용합니다.",
            "localCount": len(enriched),
        }

    if not OPENAI_API_KEY:
        enriched = [apply_analysis_to_candidate(candidate, local_candidate_analysis(candidate)) for candidate in candidates]
        return enriched, {
            "source": "local",
            "enabled": True,
            "message": "OPENAI_API_KEY가 없어 로컬 분석을 사용합니다.",
            "localCount": len(enriched),
        }

    enriched = []
    openai_count = 0
    fallback_count = 0
    last_error = ""
    for index, candidate in enumerate(candidates):
        if index >= OPENAI_ANALYSIS_MAX_CANDIDATES:
            analysis = local_candidate_analysis(candidate)
            analysis["source"] = "local-skipped"
            analysis["note"] = "OpenAI 분석 후보 수 제한으로 로컬 분석을 사용했습니다."
            fallback_count += 1
            enriched.append(apply_analysis_to_candidate(candidate, analysis))
            continue
        try:
            analysis = fetch_openai_analysis(candidate)
            openai_count += 1
        except Exception as error:
            analysis = local_candidate_analysis(candidate)
            analysis["source"] = "local-fallback"
            analysis["error"] = str(error)[:240]
            last_error = str(error)[:240]
            fallback_count += 1
        enriched.append(apply_analysis_to_candidate(candidate, analysis))

    return enriched, {
        "source": "openai" if openai_count else "local",
        "enabled": True,
        "message": "OpenAI 분석을 반영했습니다." if openai_count else "OpenAI 호출 실패로 로컬 분석을 사용합니다.",
        "openaiCount": openai_count,
        "fallbackCount": fallback_count,
        "maxCandidates": OPENAI_ANALYSIS_MAX_CANDIDATES,
        "lastError": last_error,
        "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
    }


def integration_error_payload(error: Exception) -> tuple[dict, int]:
    if isinstance(error, ValueError):
        return {"error": "missing-config", "message": str(error)}, 400
    if isinstance(error, HTTPError):
        detail = error.read().decode("utf-8", errors="replace")
        return {
            "error": "upstream-http-error",
            "status": error.code,
            "message": "외부 API 호출이 실패했습니다.",
            "detail": detail[:500],
        }, 502
    if isinstance(error, URLError):
        return {
            "error": "upstream-network-error",
            "message": "외부 API에 연결하지 못했습니다.",
            "detail": str(error.reason),
        }, 502
    return {"error": "internal-error", "message": str(error)}, 500


def market_index_key_for_candidate(candidate: dict) -> str:
    if candidate.get("market") == "KR":
        return "kospi"
    return "nasdaq"


def dynamic_news_score(candidate: dict, base_score: dict, notes: list[str]) -> int:
    score = bounded_int(base_score.get("news", 0), 0, 22)
    live_news = candidate.get("liveNews", {})
    if isinstance(live_news, dict) and live_news.get("source") == "naver":
        display_count = bounded_int(live_news.get("display", 0), 0, 100)
        item_count = len(live_news.get("items", [])) if isinstance(live_news.get("items"), list) else 0
        score = max(score, bounded_int(8 + min(display_count, 10) * 2 + min(item_count, 5), 0, 22))
        notes.append(f"네이버 최신 뉴스 {item_count}건을 후보 점수에 반영")

    global_news = candidate.get("globalNews", {})
    if isinstance(global_news, dict) and global_news.get("source") == "gdelt":
        display_count = bounded_int(global_news.get("display", 0), 0, 250)
        item_count = len(global_news.get("items", [])) if isinstance(global_news.get("items"), list) else 0
        gdelt_score = bounded_int(7 + min(display_count, 10) * 2 + min(item_count, 5), 0, 20)
        score = max(score, gdelt_score)
        if isinstance(live_news, dict) and live_news.get("source") == "naver" and item_count:
            score += 2
        notes.append(f"GDELT 글로벌 뉴스 {item_count}건을 후보 점수에 반영")

    return bounded_int(score, 0, 22)


def dynamic_price_score(candidate: dict, base_score: dict, notes: list[str]) -> tuple[int, int]:
    change = display_percent_to_decimal(candidate.get("change"))
    if change is None:
        return bounded_int(base_score.get("price", 0), 0, 16), bounded_int(base_score.get("heatPenalty", 0), 0, 20)

    heat = bounded_int(base_score.get("heatPenalty", 0), 0, 20)
    if change < Decimal("-2"):
        score = 3
        notes.append(f"가격 반응 {display_change(change)}로 약세 위험 반영")
    elif change < 0:
        score = 6
        notes.append(f"가격 반응 {display_change(change)}로 추세 확인 필요")
    elif change <= Decimal("3"):
        score = 15
        notes.append(f"가격 반응 {display_change(change)}로 무리 없는 상승 구간")
    elif change <= Decimal("6"):
        score = 12
        heat += 3
        notes.append(f"가격 반응 {display_change(change)}로 단기 과열 일부 반영")
    else:
        score = 8
        heat += 7
        notes.append(f"가격 반응 {display_change(change)}로 추격 위험 반영")
    return bounded_int(score, 0, 16), bounded_int(heat, 0, 20)


def dynamic_volume_score(candidate: dict, base_score: dict, notes: list[str]) -> int:
    trend = candidate.get("trend", {})
    volume = display_multiplier_to_decimal(trend.get("volumeSpike") if isinstance(trend, dict) else "")
    score = bounded_int(base_score.get("volume", 0), 0, 18)
    if volume is not None and volume >= Decimal("2.5"):
        notes.append(f"거래량 {volume}배로 수급 반응 강함")
        score = 18
    elif volume is not None and volume >= Decimal("1.8"):
        notes.append(f"거래량 {volume}배로 수급 확인")
        score = 15
    elif volume is not None and volume >= Decimal("1.2"):
        score = max(score, 11)
    elif volume is not None:
        score = min(score, 6)

    orderbook = candidate.get("liveOrderbook", {})
    if isinstance(orderbook, dict) and orderbook.get("source") == "toss":
        imbalance = display_percent_to_decimal(orderbook.get("imbalancePercent"))
        if imbalance is not None and imbalance >= Decimal("20"):
            notes.append(f"호가 잔량 {orderbook.get('pressure')}({orderbook.get('imbalancePercent')})")
            score += 2
        elif imbalance is not None and imbalance <= Decimal("-20"):
            notes.append(f"호가 잔량 {orderbook.get('pressure')}({orderbook.get('imbalancePercent')})")
            score -= 2

    trades = candidate.get("liveTrades", {})
    if isinstance(trades, dict) and trades.get("source") == "toss":
        bias = display_percent_to_decimal(trades.get("biasPercent"))
        if bias is not None and bias >= Decimal("20"):
            notes.append(f"최근 체결 {trades.get('pressure')}({trades.get('biasPercent')})")
            score += 2
        elif bias is not None and bias <= Decimal("-20"):
            notes.append(f"최근 체결 {trades.get('pressure')}({trades.get('biasPercent')})")
            score -= 2

    return bounded_int(score, 0, 18)


def dynamic_market_score(candidate: dict, market: dict, base_score: dict, notes: list[str]) -> int:
    index_key = market_index_key_for_candidate(candidate)
    index_change = display_percent_to_decimal(market.get(index_key))
    if index_change is None:
        return bounded_int(base_score.get("market", 0), 0, 12)
    label = {"kospi": "코스피", "kosdaq": "코스닥", "nasdaq": "나스닥"}.get(index_key, index_key)
    if index_change >= Decimal("1"):
        notes.append(f"{label} {display_change(index_change)}로 시장 바람 우호적")
        return 12
    if index_change >= 0:
        notes.append(f"{label} {display_change(index_change)}로 시장 방향 양호")
        return 9
    if index_change <= Decimal("-1"):
        notes.append(f"{label} {display_change(index_change)}로 시장 역풍 반영")
        return 3
    return 6


def dynamic_attention_score(candidate: dict, base_score: dict, watched: set[str], notes: list[str]) -> int:
    source_count = len(candidate.get("sources", [])) if isinstance(candidate.get("sources"), list) else 0
    score = bounded_int(base_score.get("attention", 0), 0, 12)
    score += min(source_count, 6) // 2
    if candidate.get("symbol") in watched:
        score += 2
        notes.append("관심 종목으로 등록되어 관찰 우선순위 가산")
    return bounded_int(score, 0, 12)


def dynamic_risk_score(candidate: dict, market: dict, base_score: dict, notes: list[str]) -> int:
    risk = bounded_int(base_score.get("riskPenalty", 0), 0, 30)
    live_disclosures = candidate.get("liveDisclosures", {})
    if isinstance(live_disclosures, dict):
        disclosure_items = live_disclosures.get("items", [])
        disclosure_count = len(disclosure_items) if isinstance(disclosure_items, list) else 0
        if disclosure_count:
            risk += min(disclosure_count * 3, 9)
            notes.append(f"최근 공시 {disclosure_count}건으로 확인 필요")
    index_change = display_percent_to_decimal(market.get(market_index_key_for_candidate(candidate)))
    if index_change is not None and index_change <= Decimal("-1"):
        risk += 4
    change = display_percent_to_decimal(candidate.get("change"))
    if change is not None and change < Decimal("-2"):
        risk += 5
    return bounded_int(risk, 0, 30)


def event_score_from_candidate(candidate: dict, base_score: dict) -> int:
    text = " ".join(
        [
            str(candidate.get("headline", "")),
            str(candidate.get("thesis", "")),
            " ".join(str(tag) for tag in candidate.get("tags", []) if tag),
        ]
    ).lower()
    score = bounded_int(base_score.get("event", 0), 0, 25)
    keyword_groups = [
        ["hbm", "ai", "반도체", "인프라"],
        ["공급", "수요", "실적", "목표가"],
        ["주주환원", "배당", "자사주"],
        ["원전", "수주", "정책"],
    ]
    for group in keyword_groups:
        if any(keyword in text for keyword in group):
            score += 1
    return bounded_int(score, 0, 25)


def verdict_from_scores(total: int, readiness: int, risk: int, heat: int) -> str:
    if total >= 75 and readiness >= 70 and risk < 18:
        return "조건 충족 시 관찰"
    if total >= 65 and heat >= 8:
        return "눌림 대기"
    if total >= 60:
        return "준비됨"
    if risk >= 22 or total < 45:
        return "관찰 제외"
    return "조건부 관찰"


def apply_candidate_selection(candidates: list[dict], market: dict, watched: set[str]) -> tuple[list[dict], dict]:
    enriched = []
    score_shifts = []
    for candidate in candidates:
        item = dict(candidate)
        base_score = item.get("score", {})
        if not isinstance(base_score, dict):
            base_score = {}
        notes: list[str] = []
        original_total = bounded_int(item.get("totalScore", score_candidate(item)))

        event = event_score_from_candidate(item, base_score)
        news = dynamic_news_score(item, base_score, notes)
        volume = dynamic_volume_score(item, base_score, notes)
        price, heat = dynamic_price_score(item, base_score, notes)
        market_score = dynamic_market_score(item, market, base_score, notes)
        attention = dynamic_attention_score(item, base_score, watched, notes)
        risk = dynamic_risk_score(item, market, base_score, notes)

        score_detail = {
            "event": event,
            "news": news,
            "volume": volume,
            "price": price,
            "market": market_score,
            "attention": attention,
            "riskPenalty": risk,
            "heatPenalty": heat,
        }
        total = score_candidate({"score": score_detail})
        readiness = bounded_int((total * 0.58) + (price * 1.4) + (volume * 0.7) + (market_score * 0.6) - (risk * 0.45))
        preopen_priority = bounded_int((total * 0.66) + (news * 0.9) + (event * 0.45) + (market_score * 0.8) - (heat * 0.5))
        shift = total - original_total
        score_shifts.append(shift)

        item["score"] = score_detail
        item["totalScore"] = total
        item["triggerReadiness"] = readiness
        item["preopenPriority"] = preopen_priority
        item["verdict"] = verdict_from_scores(total, readiness, risk, heat)
        item["selection"] = {
            "source": "live-rules",
            "previousScore": original_total,
            "scoreChange": shift,
            "components": score_detail,
            "notes": unique_texts(notes, limit=5),
            "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
        }
        enriched.append(item)

    average_shift = sum(score_shifts) / len(score_shifts) if score_shifts else 0
    return enriched, {
        "source": "live-rules",
        "enabled": True,
        "message": "뉴스, 시세, 지수, 공시 신호로 후보 점수를 재계산했습니다.",
        "candidateCount": len(enriched),
        "averageScoreShift": round(average_shift, 1),
        "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
    }


def score_candidate(candidate: dict) -> int:
    score = candidate.get("score", {})
    positive = sum(
        int(score.get(key, 0))
        for key in ["event", "news", "volume", "price", "market", "attention"]
    )
    penalty = sum(int(score.get(key, 0)) for key in ["riskPenalty", "heatPenalty"])
    return max(0, min(100, positive - penalty))


def decorate_candidate(candidate: dict, watched: set[str]) -> dict:
    decorated = dict(candidate)
    decorated["totalScore"] = score_candidate(candidate)
    decorated["isWatched"] = candidate.get("symbol") in watched
    return decorated


def dashboard(mode: str) -> dict:
    data = seed_data()
    market, index_status = enrich_market_with_indices(data.get("market", {}))
    market, fx_status = enrich_market_with_fx(market)
    watched = set(watchlist())
    candidates = [decorate_candidate(item, watched) for item in data.get("candidates", [])]
    toss_price_status = {
        "source": "sample",
        "enabled": TOSS_LIVE_PRICES,
        "message": "샘플 가격을 사용합니다.",
    }
    toss_candle_status = {
        "source": "sample",
        "enabled": TOSS_LIVE_CANDLES,
        "message": "샘플 차트를 사용합니다.",
    }
    toss_orderbook_status = {
        "source": "sample",
        "enabled": TOSS_LIVE_ORDERBOOK,
        "message": "샘플 호가 지표를 사용합니다.",
    }
    toss_trades_status = {
        "source": "sample",
        "enabled": TOSS_LIVE_TRADES,
        "message": "샘플 체결 지표를 사용합니다.",
    }
    dart_disclosure_status = {
        "source": "sample",
        "enabled": DART_LIVE_DISCLOSURES,
        "message": "샘플 공시 메모를 사용합니다.",
    }
    naver_news_status = {
        "source": "sample",
        "enabled": NAVER_LIVE_NEWS,
        "message": "샘플 뉴스를 사용합니다.",
    }
    gdelt_news_status = {
        "source": "sample",
        "enabled": GDELT_LIVE_NEWS,
        "message": "글로벌 뉴스 보강을 사용하지 않았습니다.",
    }
    openai_analysis_status = {
        "source": "local",
        "enabled": OPENAI_ANALYSIS_ENABLED,
        "message": "로컬 분석을 사용합니다.",
    }
    selection_status = {
        "source": "static",
        "enabled": True,
        "message": "기본 후보 점수를 사용합니다.",
    }
    try:
        candidates, toss_price_status = enrich_candidates_with_toss_prices(candidates)
    except Exception as error:
        payload, _ = integration_error_payload(error)
        toss_price_status = {
            "source": "sample",
            "enabled": TOSS_LIVE_PRICES,
            "error": payload.get("error", "unknown"),
            "status": payload.get("status"),
            "detail": payload.get("detail", ""),
            "message": payload.get("message", "토스 현재가 반영에 실패해 샘플 가격을 사용합니다."),
        }
    try:
        candidates, toss_candle_status = enrich_candidates_with_toss_candles(candidates)
    except Exception as error:
        payload, _ = integration_error_payload(error)
        toss_candle_status = {
            "source": "sample",
            "enabled": TOSS_LIVE_CANDLES,
            "error": payload.get("error", "unknown"),
            "status": payload.get("status"),
            "detail": payload.get("detail", ""),
            "message": payload.get("message", "토스 캔들 반영에 실패해 샘플 차트를 사용합니다."),
        }
    try:
        candidates, toss_orderbook_status = enrich_candidates_with_toss_orderbook(candidates)
    except Exception as error:
        payload, _ = integration_error_payload(error)
        toss_orderbook_status = {
            "source": "sample",
            "enabled": TOSS_LIVE_ORDERBOOK,
            "error": payload.get("error", "unknown"),
            "status": payload.get("status"),
            "detail": payload.get("detail", ""),
            "message": payload.get("message", "토스 호가 반영에 실패해 샘플 호가 지표를 사용합니다."),
        }
    try:
        candidates, toss_trades_status = enrich_candidates_with_toss_trades(candidates)
    except Exception as error:
        payload, _ = integration_error_payload(error)
        toss_trades_status = {
            "source": "sample",
            "enabled": TOSS_LIVE_TRADES,
            "error": payload.get("error", "unknown"),
            "status": payload.get("status"),
            "detail": payload.get("detail", ""),
            "message": payload.get("message", "토스 체결 반영에 실패해 샘플 체결 지표를 사용합니다."),
        }
    try:
        candidates, dart_disclosure_status = enrich_candidates_with_dart_disclosures(candidates)
    except Exception as error:
        payload, _ = integration_error_payload(error)
        dart_disclosure_status = {
            "source": "sample",
            "enabled": DART_LIVE_DISCLOSURES,
            "error": payload.get("error", "unknown"),
            "message": payload.get("message", "OpenDART 공시 반영에 실패해 샘플 공시 메모를 사용합니다."),
        }
    try:
        candidates, naver_news_status = enrich_candidates_with_naver_news(candidates)
    except Exception as error:
        payload, _ = integration_error_payload(error)
        naver_news_status = {
            "source": "sample",
            "enabled": NAVER_LIVE_NEWS,
            "error": payload.get("error", "unknown"),
            "message": payload.get("message", "네이버 뉴스 반영에 실패해 샘플 뉴스를 사용합니다."),
        }
    try:
        candidates, gdelt_news_status = enrich_candidates_with_gdelt_news(candidates)
    except Exception as error:
        payload, _ = integration_error_payload(error)
        gdelt_news_status = {
            "source": "sample",
            "enabled": GDELT_LIVE_NEWS,
            "error": payload.get("error", "unknown"),
            "message": payload.get("message", "GDELT 글로벌 뉴스 반영에 실패해 샘플 뉴스를 사용합니다."),
            "detail": payload.get("detail", ""),
            "status": payload.get("status", ""),
            "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
        }

    candidates, selection_status = apply_candidate_selection(candidates, market, watched)

    if mode == "preopen":
        candidates.sort(key=lambda item: (item["preopenPriority"], item["totalScore"]), reverse=True)
    elif mode == "intraday":
        candidates.sort(key=lambda item: (item["triggerReadiness"], item["totalScore"]), reverse=True)
    else:
        candidates.sort(key=lambda item: item["totalScore"], reverse=True)

    try:
        candidates, openai_analysis_status = enrich_candidates_with_openai_analysis(candidates)
    except Exception as error:
        payload, _ = integration_error_payload(error)
        openai_analysis_status = {
            "source": "local",
            "enabled": OPENAI_ANALYSIS_ENABLED,
            "error": payload.get("error", "unknown"),
            "message": payload.get("message", "OpenAI 분석에 실패해 로컬 분석을 사용합니다."),
        }
        candidates = [apply_analysis_to_candidate(candidate, local_candidate_analysis(candidate)) for candidate in candidates]

    selected = candidates[0] if candidates else None
    return {
        "generatedAt": datetime.now(KST).isoformat(timespec="seconds"),
        "mode": mode,
        "market": market,
        "principles": data.get("principles", []),
        "summary": {
            "candidateCount": len(candidates),
            "watchedCount": len([item for item in candidates if item["isWatched"]]),
            "highScoreCount": len([item for item in candidates if item["totalScore"] >= 75]),
            "readyCount": len([item for item in candidates if item["triggerReadiness"] >= 70]),
            "selectionSource": selection_status.get("source"),
            "averageScoreShift": selection_status.get("averageScoreShift"),
        },
        "integrations": {
            "selection": selection_status,
            "toss": {
                "config": toss_config_status(),
                "prices": toss_price_status,
                "candles": toss_candle_status,
                "orderbook": toss_orderbook_status,
                "trades": toss_trades_status,
            },
            "market": {
                "config": market_config_status(),
                "indices": index_status,
                "fx": fx_status,
            },
            "dart": {
                "config": dart_config_status(),
                "disclosures": dart_disclosure_status,
            },
            "news": {
                "naver": {
                    "config": naver_news_config_status(),
                    "items": naver_news_status,
                },
                "gdelt": {
                    "config": gdelt_news_config_status(),
                    "items": gdelt_news_status,
                }
            },
            "openai": {
                "config": openai_config_status(),
                "analysis": openai_analysis_status,
            }
        },
        "candidates": candidates,
        "selected": selected,
    }


def minutes_from_hhmm(value: str) -> int | None:
    match = re.fullmatch(r"([01]?\d|2[0-3]):([0-5]\d)", str(value or "").strip())
    if not match:
        return None
    return int(match.group(1)) * 60 + int(match.group(2))


def scheduler_jobs() -> list[dict]:
    return [
        {
            "mode": "preopen",
            "label": "장전 후보 점검",
            "time": SIGNAL_PREOPEN_RUN_TIME,
            "windowMinutes": SIGNAL_PREOPEN_RUN_WINDOW_MINUTES,
        },
        {
            "mode": "close",
            "label": "장마감 후보 발굴",
            "time": SIGNAL_CLOSE_RUN_TIME,
            "windowMinutes": SIGNAL_CLOSE_RUN_WINDOW_MINUTES,
        },
    ]


def display_local_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(BASE_DIR))
    except ValueError:
        return str(path)


def scheduler_config_status() -> dict:
    return {
        "enabled": SIGNAL_SCHEDULER_ENABLED,
        "intervalSeconds": SIGNAL_SCHEDULER_INTERVAL_SECONDS,
        "historyLimit": SIGNAL_RUN_HISTORY_LIMIT,
        "jobs": scheduler_jobs(),
        "runsDir": display_local_path(RUNS_DIR),
    }


def scheduled_snapshot_exists(run_date: str, mode: str) -> bool:
    return any(RUNS_DIR.glob(f"{run_date}_{mode}_scheduled_*.json"))


def job_is_due(job: dict, now: datetime) -> bool:
    scheduled_minutes = minutes_from_hhmm(str(job.get("time", "")))
    if scheduled_minutes is None:
        return False
    now_minutes = now.hour * 60 + now.minute
    window = bounded_int(job.get("windowMinutes", 0), 0, 24 * 60)
    if now_minutes < scheduled_minutes or now_minutes > scheduled_minutes + window:
        return False
    return not scheduled_snapshot_exists(now.date().isoformat(), str(job.get("mode", "")))


def dashboard_summary(payload: dict) -> dict:
    candidates = payload.get("candidates", [])
    if not isinstance(candidates, list):
        candidates = []
    top_candidates = []
    for item in candidates[:5]:
        if not isinstance(item, dict):
            continue
        top_candidates.append({
            "symbol": item.get("symbol", ""),
            "name": item.get("name", ""),
            "score": item.get("totalScore", 0),
            "verdict": item.get("verdict", ""),
            "change": item.get("change", ""),
        })
    summary = payload.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}
    return {
        "mode": payload.get("mode"),
        "generatedAt": payload.get("generatedAt"),
        "candidateCount": summary.get("candidateCount", len(candidates)),
        "highScoreCount": summary.get("highScoreCount", 0),
        "readyCount": summary.get("readyCount", 0),
        "averageScoreShift": summary.get("averageScoreShift"),
        "topCandidates": top_candidates,
    }


def scheduler_record_from_snapshot(path: Path, snapshot: dict) -> dict:
    return {
        "id": snapshot.get("id", path.stem),
        "mode": snapshot.get("mode"),
        "trigger": snapshot.get("trigger"),
        "createdAt": snapshot.get("createdAt"),
        "file": display_local_path(path),
        "summary": snapshot.get("summary", {}),
    }


def recent_scheduler_runs(limit: int | None = None) -> list[dict]:
    limit = SIGNAL_RUN_HISTORY_LIMIT if limit is None else max(1, int(limit))
    if not RUNS_DIR.exists():
        return []
    records = []
    for path in sorted(RUNS_DIR.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)[:limit]:
        try:
            snapshot = read_json(path, {})
            if isinstance(snapshot, dict):
                records.append(scheduler_record_from_snapshot(path, snapshot))
        except (OSError, json.JSONDecodeError):
            continue
    return records


def scheduler_snapshot_path(run_id: str) -> Path | None:
    run_id = str(run_id or "").strip()
    if not run_id or not RUNS_DIR.exists():
        return None
    for path in RUNS_DIR.glob("*.json"):
        try:
            snapshot = read_json(path, {})
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(snapshot, dict) and str(snapshot.get("id", "")) == run_id:
            return path
    return None


def scheduler_snapshot_detail(run_id: str) -> dict | None:
    path = scheduler_snapshot_path(run_id)
    if path is None:
        return None
    snapshot = read_json(path, {})
    if not isinstance(snapshot, dict):
        return None
    record = scheduler_record_from_snapshot(path, snapshot)
    return {
        "record": record,
        "dashboard": snapshot.get("dashboard", {}),
    }


def current_price_lookup(symbols: list[str]) -> tuple[dict[str, dict], dict]:
    unique = unique_symbols(symbols)
    seed_lookup = {
        str(candidate.get("symbol")): candidate
        for candidate in seed_data().get("candidates", [])
        if candidate.get("symbol")
    }
    lookup: dict[str, dict] = {}
    for symbol in unique:
        fallback = seed_lookup.get(symbol, {})
        value = display_number_to_decimal(fallback.get("price"))
        lookup[symbol] = {
            "symbol": symbol,
            "price": fallback.get("price", "-"),
            "value": value,
            "source": "sample" if value is not None else "missing",
        }

    if not unique:
        return lookup, {
            "source": "none",
            "enabled": TOSS_LIVE_PRICES,
            "message": "비교할 종목이 없습니다.",
            "priceCount": 0,
        }

    if not TOSS_LIVE_PRICES or not toss_config_status()["readyForMarketData"]:
        return lookup, {
            "source": "sample",
            "enabled": TOSS_LIVE_PRICES,
            "message": "토스 현재가를 사용할 수 없어 샘플 가격으로 성과를 계산합니다.",
            "priceCount": len([item for item in lookup.values() if item.get("value") is not None]),
        }

    try:
        prices = price_by_symbol(fetch_toss_prices(unique))
    except Exception as error:
        payload, _ = integration_error_payload(error)
        return lookup, {
            "source": "sample",
            "enabled": TOSS_LIVE_PRICES,
            "error": payload.get("error", "unknown"),
            "message": payload.get("message", "토스 현재가 조회 실패로 샘플 가격을 사용합니다."),
            "priceCount": len([item for item in lookup.values() if item.get("value") is not None]),
        }

    for symbol, price in prices.items():
        value = decimal_or_none(price.get("lastPrice"))
        if value is None:
            continue
        lookup[symbol] = {
            "symbol": symbol,
            "price": display_price(str(price.get("lastPrice")), str(price.get("currency"))),
            "value": value,
            "currency": price.get("currency"),
            "timestamp": price.get("timestamp"),
            "source": "toss",
        }

    return lookup, {
        "source": "toss",
        "enabled": TOSS_LIVE_PRICES,
        "message": "토스 현재가로 스냅샷 후보 성과를 계산했습니다.",
        "priceCount": len(prices),
        "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
    }


def performance_outcome(change_rate: Decimal, threshold: Decimal) -> str:
    if change_rate >= threshold:
        return "상승"
    if change_rate <= -threshold:
        return "하락"
    return "중립"


def decimal_average(values: list[Decimal]) -> Decimal:
    return sum(values) / Decimal(len(values)) if values else Decimal("0")


def performance_summary(observations: list[dict], run_count: int, price_status: dict) -> dict:
    measured = [item for item in observations if item.get("measured")]
    changes = [Decimal(str(item["changeRate"])) for item in measured]
    positive = [item for item in measured if item.get("outcome") == "상승"]
    negative = [item for item in measured if item.get("outcome") == "하락"]
    neutral = [item for item in measured if item.get("outcome") == "중립"]
    average = decimal_average(changes)
    best = max(measured, key=lambda item: Decimal(str(item["changeRate"])), default=None)
    worst = min(measured, key=lambda item: Decimal(str(item["changeRate"])), default=None)
    hit_rate = (Decimal(len(positive)) / Decimal(len(measured)) * Decimal(100)) if measured else Decimal("0")
    return {
        "runCount": run_count,
        "observationCount": len(observations),
        "measuredCount": len(measured),
        "positiveCount": len(positive),
        "negativeCount": len(negative),
        "neutralCount": len(neutral),
        "hitRate": display_percent_abs(hit_rate),
        "averageChange": display_decimal_percent(average),
        "best": best,
        "worst": worst,
        "priceSource": price_status.get("source", "-"),
    }


def performance_by_symbol(observations: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for item in observations:
        if not item.get("measured"):
            continue
        grouped.setdefault(str(item.get("symbol", "")), []).append(item)

    rows = []
    for symbol, items in grouped.items():
        changes = [Decimal(str(item["changeRate"])) for item in items]
        positives = len([item for item in items if item.get("outcome") == "상승"])
        rows.append({
            "symbol": symbol,
            "name": items[0].get("name", symbol),
            "count": len(items),
            "positiveCount": positives,
            "averageChange": display_decimal_percent(decimal_average(changes)),
            "latestChange": display_decimal_percent(changes[0]),
            "latestOutcome": items[0].get("outcome"),
        })

    rows.sort(key=lambda item: (item["positiveCount"], display_number_to_decimal(item["averageChange"]) or Decimal("0")), reverse=True)
    return rows


def performance_report(limit: int | None = None, top_n: int | None = None) -> dict:
    limit = SIGNAL_PERFORMANCE_RUN_LIMIT if limit is None else max(1, min(int(limit), 50))
    top_n = SIGNAL_PERFORMANCE_TOP_CANDIDATES if top_n is None else max(1, min(int(top_n), 10))
    runs = recent_scheduler_runs(limit)
    snapshot_candidates: list[tuple[dict, dict]] = []
    symbols: list[str] = []
    for run in runs:
        detail = scheduler_snapshot_detail(str(run.get("id", "")))
        dashboard_payload = detail.get("dashboard", {}) if detail else {}
        candidates = dashboard_payload.get("candidates", [])
        if not isinstance(candidates, list):
            continue
        for candidate in candidates[:top_n]:
            if not isinstance(candidate, dict):
                continue
            snapshot_candidates.append((run, candidate))
            symbols.append(str(candidate.get("symbol", "")))

    prices, price_status = current_price_lookup(symbols)
    threshold = SIGNAL_PERFORMANCE_SUCCESS_THRESHOLD_PERCENT
    observations = []
    for run, candidate in snapshot_candidates:
        symbol = str(candidate.get("symbol", ""))
        start_price = display_number_to_decimal(candidate.get("price"))
        current = prices.get(symbol, {})
        current_price = current.get("value")
        measured = start_price is not None and start_price > 0 and isinstance(current_price, Decimal)
        change_rate = Decimal("0")
        outcome = "미측정"
        if measured:
            change_rate = ((current_price - start_price) / start_price) * Decimal(100)
            outcome = performance_outcome(change_rate, threshold)
        observations.append({
            "runId": run.get("id"),
            "mode": run.get("mode"),
            "trigger": run.get("trigger"),
            "createdAt": run.get("createdAt"),
            "symbol": symbol,
            "name": candidate.get("name", symbol),
            "score": candidate.get("totalScore", 0),
            "readiness": candidate.get("triggerReadiness", 0),
            "verdict": candidate.get("verdict", ""),
            "snapshotPrice": candidate.get("price", "-"),
            "currentPrice": current.get("price", "-"),
            "priceSource": current.get("source", "missing"),
            "change": display_decimal_percent(change_rate) if measured else "-",
            "changeRate": str(change_rate.quantize(Decimal("0.01"))) if measured else "0",
            "outcome": outcome,
            "measured": measured,
        })

    return {
        "generatedAt": datetime.now(KST).isoformat(timespec="seconds"),
        "config": {
            "runLimit": limit,
            "topCandidates": top_n,
            "successThreshold": display_percent_abs(threshold),
        },
        "priceStatus": price_status,
        "summary": performance_summary(observations, len(runs), price_status),
        "bySymbol": performance_by_symbol(observations),
        "observations": observations,
    }


def run_signal_snapshot(mode: str, trigger: str = "manual") -> dict:
    if mode not in {"close", "preopen", "intraday"}:
        raise ValueError("mode는 close, preopen, intraday 중 하나여야 합니다.")
    now = datetime.now(KST)
    payload = dashboard(mode)
    run_id = f"{now.strftime('%Y%m%d-%H%M%S')}-{mode}-{trigger}"
    file_name = f"{now.date().isoformat()}_{mode}_{trigger}_{now.strftime('%H%M%S')}.json"
    path = RUNS_DIR / file_name
    snapshot = {
        "id": run_id,
        "mode": mode,
        "trigger": trigger,
        "createdAt": now.isoformat(timespec="seconds"),
        "summary": dashboard_summary(payload),
        "dashboard": payload,
    }
    write_json(path, snapshot)
    record = scheduler_record_from_snapshot(path, snapshot)
    with SCHEDULER_LOCK:
        last_runs = dict(SCHEDULER_STATE.get("lastRuns", {}))
        last_runs[mode] = record
        SCHEDULER_STATE["lastRuns"] = last_runs
        SCHEDULER_STATE["lastError"] = ""
    return record


def scheduler_status() -> dict:
    with SCHEDULER_LOCK:
        state = {
            "started": bool(SCHEDULER_STATE.get("started")),
            "running": bool(SCHEDULER_STATE.get("running")),
            "lastError": SCHEDULER_STATE.get("lastError", ""),
            "lastCheckedAt": SCHEDULER_STATE.get("lastCheckedAt", ""),
            "lastRuns": SCHEDULER_STATE.get("lastRuns", {}),
        }
    return {
        "config": scheduler_config_status(),
        "state": state,
        "recentRuns": recent_scheduler_runs(),
    }


def scheduler_loop() -> None:
    with SCHEDULER_LOCK:
        SCHEDULER_STATE["started"] = True
    while True:
        now = datetime.now(KST)
        with SCHEDULER_LOCK:
            SCHEDULER_STATE["lastCheckedAt"] = now.isoformat(timespec="seconds")
        if SIGNAL_SCHEDULER_ENABLED:
            for job in scheduler_jobs():
                if not job_is_due(job, now):
                    continue
                try:
                    with SCHEDULER_LOCK:
                        SCHEDULER_STATE["running"] = True
                    run_signal_snapshot(str(job["mode"]), trigger="scheduled")
                except Exception as error:
                    with SCHEDULER_LOCK:
                        SCHEDULER_STATE["lastError"] = str(error)[:240]
                finally:
                    with SCHEDULER_LOCK:
                        SCHEDULER_STATE["running"] = False
        time.sleep(max(10, SIGNAL_SCHEDULER_INTERVAL_SECONDS))


def start_scheduler_thread() -> None:
    thread = threading.Thread(target=scheduler_loop, name="market-signal-scheduler", daemon=True)
    thread.start()


class AppHandler(BaseHTTPRequestHandler):
    server_version = "MarketSignalDesk/0.1"

    def auth_required_for_path(self, path: str) -> bool:
        if not ADMIN_TOKEN:
            return False
        if path in {"/api/health", "/api/auth/status"}:
            return False
        return path.startswith("/api/")

    def is_authorized(self) -> bool:
        if not ADMIN_TOKEN:
            return True
        token = self.headers.get("X-Admin-Token", "").strip()
        authorization = self.headers.get("Authorization", "").strip()
        if not token and authorization.lower().startswith("bearer "):
            token = authorization[7:].strip()
        return hmac.compare_digest(token, ADMIN_TOKEN)

    def reject_unauthorized(self) -> None:
        self.send_json(
            {
                "error": "auth-required",
                "message": "관리자 토큰이 필요합니다.",
            },
            401,
        )

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.send_json({"ok": True, "time": datetime.now(KST).isoformat(timespec="seconds")})
            return

        if parsed.path == "/api/auth/status":
            self.send_json(auth_config_status())
            return

        if self.auth_required_for_path(parsed.path) and not self.is_authorized():
            self.reject_unauthorized()
            return

        if parsed.path == "/api/integrations/toss/status":
            self.send_json(toss_config_status())
            return

        if parsed.path == "/api/network/outbound-ip":
            self.send_json(outbound_ip_status())
            return

        if parsed.path == "/api/integrations/market/status":
            market, index_status = enrich_market_with_indices(seed_data().get("market", {}))
            _, fx_status = enrich_market_with_fx(market)
            self.send_json({"config": market_config_status(), "indices": index_status, "fx": fx_status})
            return

        if parsed.path == "/api/integrations/toss/prices":
            query = parse_qs(parsed.query)
            symbols = [symbol.strip() for symbol in query.get("symbols", ["005930"])[0].split(",") if symbol.strip()]
            try:
                self.send_json(fetch_toss_prices(symbols))
            except Exception as error:
                payload, status = integration_error_payload(error)
                self.send_json(payload, status)
            return

        if parsed.path == "/api/integrations/toss/candles":
            query = parse_qs(parsed.query)
            symbol = query.get("symbol", ["005930"])[0].strip()
            interval = query.get("interval", ["1d"])[0].strip()
            count = int(query.get("count", ["20"])[0])
            try:
                self.send_json(fetch_toss_candles(symbol, interval=interval, count=count))
            except Exception as error:
                payload, status = integration_error_payload(error)
                self.send_json(payload, status)
            return

        if parsed.path == "/api/integrations/toss/orderbook":
            query = parse_qs(parsed.query)
            symbol = query.get("symbol", ["005930"])[0].strip()
            try:
                self.send_json(fetch_toss_orderbook(symbol))
            except Exception as error:
                payload, status = integration_error_payload(error)
                self.send_json(payload, status)
            return

        if parsed.path == "/api/integrations/toss/trades":
            query = parse_qs(parsed.query)
            symbol = query.get("symbol", ["005930"])[0].strip()
            count = int(query.get("count", [str(TOSS_TRADES_COUNT)])[0])
            try:
                self.send_json(fetch_toss_trades(symbol, count=count))
            except Exception as error:
                payload, status = integration_error_payload(error)
                self.send_json(payload, status)
            return

        if parsed.path == "/api/integrations/dart/status":
            self.send_json(dart_config_status())
            return

        if parsed.path == "/api/integrations/dart/corp-code":
            query = parse_qs(parsed.query)
            symbol = query.get("symbol", ["005930"])[0].strip()
            try:
                corp = dart_corp_code_for_symbol(symbol)
                self.send_json({"symbol": symbol, "corp": corp})
            except Exception as error:
                payload, status = integration_error_payload(error)
                self.send_json(payload, status)
            return

        if parsed.path == "/api/integrations/dart/disclosures":
            query = parse_qs(parsed.query)
            symbol = query.get("symbol", ["005930"])[0].strip()
            days = int(query.get("days", [str(DART_DISCLOSURE_LOOKBACK_DAYS)])[0])
            try:
                self.send_json(fetch_dart_disclosures(symbol, days=days))
            except Exception as error:
                payload, status = integration_error_payload(error)
                self.send_json(payload, status)
            return

        if parsed.path == "/api/integrations/news/status":
            self.send_json({"naver": naver_news_config_status(), "gdelt": gdelt_news_config_status()})
            return

        if parsed.path == "/api/integrations/news/search":
            query = parse_qs(parsed.query)
            search_query = query.get("query", ["삼성전자"])[0].strip()
            provider = query.get("provider", ["naver"])[0].strip().lower()
            try:
                if provider == "gdelt":
                    display = int(query.get("display", [str(GDELT_NEWS_DISPLAY)])[0])
                    timespan = query.get("timespan", [GDELT_NEWS_TIMESPAN])[0].strip()
                    sort = query.get("sort", ["datedesc"])[0].strip()
                    payload = fetch_gdelt_news(search_query, display=display, timespan=timespan, sort=sort)
                    articles = payload.get("articles", [])
                    payload["items"] = [
                        normalize_gdelt_news_item(item)
                        for item in articles
                        if isinstance(item, dict)
                    ]
                else:
                    display = int(query.get("display", [str(NAVER_NEWS_DISPLAY)])[0])
                    sort = query.get("sort", ["date"])[0].strip()
                    payload = fetch_naver_news(search_query, display=display, sort=sort)
                    payload["items"] = [normalize_news_item(item) for item in payload.get("items", [])]
                self.send_json(payload)
            except Exception as error:
                payload, status = integration_error_payload(error)
                self.send_json(payload, status)
            return

        if parsed.path == "/api/integrations/openai/status":
            self.send_json(openai_config_status())
            return

        if parsed.path == "/api/scheduler/status":
            self.send_json(scheduler_status())
            return

        if parsed.path == "/api/performance":
            query = parse_qs(parsed.query)
            limit = int(query.get("limit", [str(SIGNAL_PERFORMANCE_RUN_LIMIT)])[0])
            top_n = int(query.get("top", [str(SIGNAL_PERFORMANCE_TOP_CANDIDATES)])[0])
            self.send_json(performance_report(limit=limit, top_n=top_n))
            return

        if parsed.path == "/api/scheduler/runs":
            query = parse_qs(parsed.query)
            limit = int(query.get("limit", [str(SIGNAL_RUN_HISTORY_LIMIT)])[0])
            self.send_json({"runs": recent_scheduler_runs(limit)})
            return

        if parsed.path.startswith("/api/scheduler/runs/"):
            run_id = unquote(parsed.path.removeprefix("/api/scheduler/runs/"))
            detail = scheduler_snapshot_detail(run_id)
            if detail is None:
                self.send_json({"error": "not-found", "message": "스냅샷을 찾을 수 없습니다."}, 404)
                return
            self.send_json(detail)
            return

        if parsed.path == "/api/integrations/openai/analyze":
            query = parse_qs(parsed.query)
            symbol = query.get("symbol", ["005930"])[0].strip()
            candidates = dashboard("close")["candidates"]
            match = next((item for item in candidates if item["symbol"] == symbol), None)
            if not match:
                self.send_json({"error": "not-found", "message": "종목을 찾을 수 없습니다."}, 404)
                return
            self.send_json(match.get("aiAnalysis", local_candidate_analysis(match)))
            return

        if parsed.path == "/api/dashboard":
            query = parse_qs(parsed.query)
            mode = query.get("mode", ["close"])[0]
            if mode not in {"close", "preopen", "intraday"}:
                mode = "close"
            self.send_json(dashboard(mode))
            return

        if parsed.path.startswith("/api/signals/"):
            symbol = unquote(parsed.path.removeprefix("/api/signals/"))
            candidates = dashboard("close")["candidates"]
            match = next((item for item in candidates if item["symbol"] == symbol), None)
            if not match:
                self.send_json({"error": "not-found", "message": "종목을 찾을 수 없습니다."}, 404)
                return
            self.send_json(match)
            return

        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_file(STATIC_DIR / "index.html")
            return

        if parsed.path.startswith("/static/"):
            relative = unquote(parsed.path.removeprefix("/static/"))
            target = (STATIC_DIR / relative).resolve()
            if STATIC_DIR.resolve() not in target.parents and target != STATIC_DIR.resolve():
                self.send_json({"error": "bad-path"}, 400)
                return
            self.send_file(target)
            return

        self.send_json({"error": "not-found"}, 404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if self.auth_required_for_path(parsed.path) and not self.is_authorized():
            self.reject_unauthorized()
            return

        if parsed.path == "/api/scheduler/run":
            body = self.read_body()
            mode = str(body.get("mode", "close")).strip()
            try:
                record = run_signal_snapshot(mode, trigger="manual")
                self.send_json({"ok": True, "record": record, "status": scheduler_status()})
            except Exception as error:
                payload, status = integration_error_payload(error)
                self.send_json(payload, status)
            return

        if parsed.path == "/api/watchlist":
            body = self.read_body()
            symbol = str(body.get("symbol", "")).strip()
            should_watch = bool(body.get("watch", True))
            if not symbol:
                self.send_json({"error": "invalid-request", "message": "symbol 값이 필요합니다."}, 400)
                return

            symbols = watchlist()
            if should_watch and symbol not in symbols:
                symbols.append(symbol)
            if not should_watch and symbol in symbols:
                symbols.remove(symbol)
            write_json(WATCHLIST_FILE, {"symbols": symbols})
            self.send_json({"symbols": symbols})
            return

        self.send_json({"error": "not-found"}, 404)

    def read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}

    def send_json(self, payload, status: int = 200) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def send_file(self, path: Path) -> None:
        if not path.exists() or not path.is_file():
            self.send_json({"error": "not-found"}, 404)
            return
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args) -> None:
        return


def main() -> None:
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8787"))
    server = ThreadingHTTPServer((host, port), AppHandler)
    start_scheduler_thread()
    display_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    print(f"Market Signal Desk is running at http://{display_host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
