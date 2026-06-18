from __future__ import annotations

import json
import mimetypes
import os
import html
import hashlib
import hmac
import copy
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
UNIVERSE_FILE = DATA_DIR / "candidate-universe.json"
WATCHLIST_FILE = DATA_DIR / "watchlist.json"
DART_CORP_CODE_FILE = DATA_DIR / "dart-corp-codes.json"
RUNS_DIR = DATA_DIR / "runs"
DISCOVERY_LATEST_FILE = DATA_DIR / "discovery-latest.json"
SNAPSHOT_STORAGE_MODE = os.getenv("SNAPSHOT_STORAGE_MODE", "filesystem").strip().lower() or "filesystem"
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
TOSS_LIVE_PORTFOLIO = os.getenv("TOSS_LIVE_PORTFOLIO", "0").lower() not in {"0", "false", "no", "off"}
TOSS_PRICE_CACHE_SECONDS = int(os.getenv("TOSS_PRICE_CACHE_SECONDS", "15"))
TOSS_CANDLE_CACHE_SECONDS = int(os.getenv("TOSS_CANDLE_CACHE_SECONDS", "60"))
TOSS_ORDERBOOK_CACHE_SECONDS = int(os.getenv("TOSS_ORDERBOOK_CACHE_SECONDS", "5"))
TOSS_TRADES_CACHE_SECONDS = int(os.getenv("TOSS_TRADES_CACHE_SECONDS", "5"))
TOSS_PORTFOLIO_CACHE_SECONDS = int(os.getenv("TOSS_PORTFOLIO_CACHE_SECONDS", "30"))
TOSS_STOCK_CACHE_SECONDS = int(os.getenv("TOSS_STOCK_CACHE_SECONDS", "86400"))
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
SIGNAL_DISCOVERY_BOT_ENABLED = os.getenv("SIGNAL_DISCOVERY_BOT_ENABLED", "1").lower() not in {"0", "false", "no", "off"}
SIGNAL_DISCOVERY_BOT_INTERVAL_SECONDS = int(os.getenv("SIGNAL_DISCOVERY_BOT_INTERVAL_SECONDS", "600"))
SIGNAL_DISCOVERY_BOT_MODE = os.getenv("SIGNAL_DISCOVERY_BOT_MODE", "intraday").strip().lower() or "intraday"
SIGNAL_CLOSE_RUN_TIME = os.getenv("SIGNAL_CLOSE_RUN_TIME", "16:40")
SIGNAL_CLOSE_RUN_WINDOW_MINUTES = int(os.getenv("SIGNAL_CLOSE_RUN_WINDOW_MINUTES", "360"))
SIGNAL_PREOPEN_RUN_TIME = os.getenv("SIGNAL_PREOPEN_RUN_TIME", "08:40")
SIGNAL_PREOPEN_RUN_WINDOW_MINUTES = int(os.getenv("SIGNAL_PREOPEN_RUN_WINDOW_MINUTES", "80"))
SIGNAL_RUN_HISTORY_LIMIT = int(os.getenv("SIGNAL_RUN_HISTORY_LIMIT", "12"))
SIGNAL_PERFORMANCE_RUN_LIMIT = int(os.getenv("SIGNAL_PERFORMANCE_RUN_LIMIT", "12"))
SIGNAL_PERFORMANCE_TOP_CANDIDATES = int(os.getenv("SIGNAL_PERFORMANCE_TOP_CANDIDATES", "3"))
SIGNAL_AUTO_CANDIDATES_ENABLED = os.getenv("SIGNAL_AUTO_CANDIDATES_ENABLED", "1").lower() not in {"0", "false", "no", "off"}
SIGNAL_DOMESTIC_CANDIDATE_LIMIT = int(os.getenv("SIGNAL_DOMESTIC_CANDIDATE_LIMIT", "10"))
SIGNAL_OVERSEAS_CANDIDATE_LIMIT = int(os.getenv("SIGNAL_OVERSEAS_CANDIDATE_LIMIT", "10"))
SIGNAL_AUTO_CANDIDATE_LIMIT = max(
    int(os.getenv("SIGNAL_AUTO_CANDIDATE_LIMIT", "20")),
    SIGNAL_DOMESTIC_CANDIDATE_LIMIT + SIGNAL_OVERSEAS_CANDIDATE_LIMIT,
)
SIGNAL_DISCOVERY_MAX_SYMBOLS = max(
    int(os.getenv("SIGNAL_DISCOVERY_MAX_SYMBOLS", "40")),
    SIGNAL_AUTO_CANDIDATE_LIMIT,
    SIGNAL_DOMESTIC_CANDIDATE_LIMIT + SIGNAL_OVERSEAS_CANDIDATE_LIMIT + 20,
)
SIGNAL_DISCOVERY_NEWS_DISPLAY = int(os.getenv("SIGNAL_DISCOVERY_NEWS_DISPLAY", "3"))
SIGNAL_DISCOVERY_CACHE_SECONDS = int(os.getenv("SIGNAL_DISCOVERY_CACHE_SECONDS", "600"))
SIGNAL_DISCOVERY_SYMBOLS = os.getenv("SIGNAL_DISCOVERY_SYMBOLS", "").strip()
SIGNAL_DISCOVERY_QUALITY_MIN_SCORE = int(os.getenv("SIGNAL_DISCOVERY_QUALITY_MIN_SCORE", "55"))
SIGNAL_DISCOVERY_RESERVE_MIN_SCORE = int(os.getenv("SIGNAL_DISCOVERY_RESERVE_MIN_SCORE", "42"))
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
STOCK_CACHE: dict[tuple[str, ...], dict[str, object]] = {}
ACCOUNT_CACHE: dict[str, object] = {"payload": None, "expires_at": datetime.min.replace(tzinfo=timezone.utc)}
HOLDINGS_CACHE: dict[tuple[str, str], dict[str, object]] = {}
BUYING_POWER_CACHE: dict[tuple[str, str], dict[str, object]] = {}
SELLABLE_QUANTITY_CACHE: dict[tuple[str, str], dict[str, object]] = {}
OUTBOUND_IP_CACHE: dict[str, object] = {"payload": None, "expires_at": datetime.min.replace(tzinfo=timezone.utc)}
CORP_CODE_CACHE: dict[str, object] = {"payload": None}
DISCLOSURE_CACHE: dict[tuple[str, int], dict[str, object]] = {}
NEWS_CACHE: dict[tuple[str, int, int, str], dict[str, object]] = {}
GDELT_NEWS_CACHE: dict[tuple[str, int, str, str], dict[str, object]] = {}
ANALYSIS_CACHE: dict[str, dict[str, object]] = {}
FX_CACHE: dict[str, object] = {"payload": None, "expires_at": datetime.min.replace(tzinfo=timezone.utc)}
INDEX_CACHE: dict[str, object] = {"payload": None, "expires_at": datetime.min.replace(tzinfo=timezone.utc)}
DISCOVERY_CACHE: dict[str, object] = {"payload": None, "expires_at": datetime.min.replace(tzinfo=timezone.utc)}
GDELT_RATE_LOCK = threading.Lock()
GDELT_LAST_REQUEST_AT = datetime.min.replace(tzinfo=timezone.utc)
SCHEDULER_LOCK = threading.Lock()
DISCOVERY_BOT_LOCK = threading.Lock()
SCHEDULER_STATE: dict[str, object] = {
    "started": False,
    "running": False,
    "lastError": "",
    "lastCheckedAt": "",
    "lastRuns": {},
}
DISCOVERY_BOT_STATE: dict[str, object] = {
    "started": False,
    "running": False,
    "lastError": "",
    "lastCheckedAt": "",
    "lastRun": {},
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


def universe_data() -> dict:
    return read_json(UNIVERSE_FILE, {"symbols": []})


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
        "livePortfolioEnabled": TOSS_LIVE_PORTFOLIO,
        "clientIdConfigured": bool(TOSS_CLIENT_ID),
        "clientIdPreview": mask_secret(TOSS_CLIENT_ID),
        "clientSecretConfigured": bool(TOSS_CLIENT_SECRET),
        "accessTokenConfigured": bool(TOSS_ACCESS_TOKEN),
        "accountSeqConfigured": bool(TOSS_ACCOUNT_SEQ),
        "readyForTokenIssue": bool(TOSS_CLIENT_ID and TOSS_CLIENT_SECRET),
        "readyForMarketData": bool(TOSS_ACCESS_TOKEN or (TOSS_CLIENT_ID and TOSS_CLIENT_SECRET)),
        "readyForAccountData": bool(TOSS_LIVE_PORTFOLIO and (TOSS_ACCESS_TOKEN or (TOSS_CLIENT_ID and TOSS_CLIENT_SECRET))),
        "orderbookMaxCandidates": TOSS_ORDERBOOK_MAX_CANDIDATES,
        "tradesMaxCandidates": TOSS_TRADES_MAX_CANDIDATES,
        "portfolioCacheSeconds": TOSS_PORTFOLIO_CACHE_SECONDS,
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


def toss_api_get(path: str, query: dict | None = None, account_seq: str = "") -> dict:
    token = toss_access_token()
    query_string = f"?{urlencode(query)}" if query else ""
    headers = {"Authorization": f"Bearer {token}"}
    if account_seq:
        headers["X-Tossinvest-Account"] = str(account_seq)
    request = Request(
        f"{TOSS_BASE_URL}{path}{query_string}",
        headers=headers,
        method="GET",
    )
    with urlopen(request, timeout=TOSS_REQUEST_TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_toss_stocks(symbols: list[str]) -> dict:
    normalized = [
        symbol.strip().upper()
        for symbol in symbols
        if re.fullmatch(r"[A-Za-z0-9.\-]{1,20}", symbol.strip())
    ]
    normalized = unique_symbols(normalized)[:200]
    if not normalized:
        return {"result": []}

    cache_key = tuple(sorted(normalized))
    cached = STOCK_CACHE.get(cache_key)
    if cached:
        expires_at = cached.get("expires_at")
        if isinstance(expires_at, datetime) and expires_at > datetime.now(timezone.utc):
            return cached["payload"]  # type: ignore[return-value]

    payload = toss_api_get("/api/v1/stocks", query={"symbols": ",".join(normalized)})
    STOCK_CACHE[cache_key] = {
        "payload": payload,
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=TOSS_STOCK_CACHE_SECONDS),
    }
    return payload


def fetch_toss_accounts() -> dict:
    expires_at = ACCOUNT_CACHE.get("expires_at")
    if ACCOUNT_CACHE.get("payload") is not None and isinstance(expires_at, datetime) and expires_at > datetime.now(timezone.utc):
        return ACCOUNT_CACHE["payload"]  # type: ignore[return-value]
    payload = toss_api_get("/api/v1/accounts")
    ACCOUNT_CACHE["payload"] = payload
    ACCOUNT_CACHE["expires_at"] = datetime.now(timezone.utc) + timedelta(seconds=TOSS_PORTFOLIO_CACHE_SECONDS)
    return payload


def fetch_toss_holdings(account_seq: str, symbol: str = "") -> dict:
    symbol = symbol.strip()
    cache_key = (str(account_seq), symbol)
    cached = HOLDINGS_CACHE.get(cache_key)
    if cached:
        expires_at = cached.get("expires_at")
        if isinstance(expires_at, datetime) and expires_at > datetime.now(timezone.utc):
            return cached["payload"]  # type: ignore[return-value]
    query = {"symbol": symbol} if symbol else None
    payload = toss_api_get("/api/v1/holdings", query=query, account_seq=str(account_seq))
    HOLDINGS_CACHE[cache_key] = {
        "payload": payload,
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=TOSS_PORTFOLIO_CACHE_SECONDS),
    }
    return payload


def fetch_toss_buying_power(account_seq: str, currency: str) -> dict:
    currency = currency.strip().upper()
    cache_key = (str(account_seq), currency)
    cached = BUYING_POWER_CACHE.get(cache_key)
    if cached:
        expires_at = cached.get("expires_at")
        if isinstance(expires_at, datetime) and expires_at > datetime.now(timezone.utc):
            return cached["payload"]  # type: ignore[return-value]
    payload = toss_api_get("/api/v1/buying-power", query={"currency": currency}, account_seq=str(account_seq))
    BUYING_POWER_CACHE[cache_key] = {
        "payload": payload,
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=TOSS_PORTFOLIO_CACHE_SECONDS),
    }
    return payload


def fetch_toss_sellable_quantity(account_seq: str, symbol: str) -> dict:
    symbol = symbol.strip()
    cache_key = (str(account_seq), symbol)
    cached = SELLABLE_QUANTITY_CACHE.get(cache_key)
    if cached:
        expires_at = cached.get("expires_at")
        if isinstance(expires_at, datetime) and expires_at > datetime.now(timezone.utc):
            return cached["payload"]  # type: ignore[return-value]
    payload = toss_api_get("/api/v1/sellable-quantity", query={"symbol": symbol}, account_seq=str(account_seq))
    SELLABLE_QUANTITY_CACHE[cache_key] = {
        "payload": payload,
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=TOSS_PORTFOLIO_CACHE_SECONDS),
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


def display_ratio_percent(value) -> str:
    ratio = decimal_or_none(value)
    if ratio is None:
        return "-"
    return display_decimal_percent(ratio * Decimal(100))


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


def stock_rows(payload: dict) -> list[dict]:
    result = payload.get("result", [])
    return result if isinstance(result, list) else []


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


def account_rows(payload: dict) -> list[dict]:
    result = payload.get("result", [])
    return result if isinstance(result, list) else []


def holdings_result(payload: dict) -> dict:
    result = payload.get("result", {})
    return result if isinstance(result, dict) else {}


def holding_items(payload: dict) -> list[dict]:
    items = holdings_result(payload).get("items", [])
    return items if isinstance(items, list) else []


def masked_account(account: dict) -> dict:
    account_no = str(account.get("accountNo", ""))
    tail = account_no[-4:] if len(account_no) >= 4 else account_no
    return {
        "accountSeq": str(account.get("accountSeq", "")),
        "accountNoPreview": f"****{tail}" if tail else "",
        "accountType": account.get("accountType", ""),
    }


def selected_account_seq(accounts: list[dict]) -> str:
    if TOSS_ACCOUNT_SEQ:
        return str(TOSS_ACCOUNT_SEQ)
    first = accounts[0] if accounts else {}
    value = first.get("accountSeq", "")
    return str(value) if value != "" else ""


def find_account(accounts: list[dict], account_seq: str) -> dict:
    for account in accounts:
        if str(account.get("accountSeq", "")) == str(account_seq):
            return account
    return accounts[0] if accounts else {}


def currency_amounts(value) -> dict:
    return value if isinstance(value, dict) else {}


def money_display(value, currency: str) -> str:
    number = decimal_or_none(value)
    if number is None:
        return "-"
    return display_price(str(number), currency)


def portfolio_position_label(profit_rate: Decimal | None, allocation_percent: Decimal | None) -> str:
    if allocation_percent is not None and allocation_percent >= Decimal("35"):
        return "비중 점검"
    if profit_rate is not None and profit_rate <= Decimal("-7"):
        return "손절 경계"
    if profit_rate is not None and profit_rate >= Decimal("12"):
        return "분할매도 검토"
    if profit_rate is not None and profit_rate <= Decimal("-3"):
        return "추가매수 대기"
    return "보유 유지"


def normalize_holding_item(item: dict, totals_by_currency: dict) -> dict:
    currency = str(item.get("currency", "KRW"))
    market_value = item.get("marketValue", {}) if isinstance(item.get("marketValue"), dict) else {}
    profit_loss = item.get("profitLoss", {}) if isinstance(item.get("profitLoss"), dict) else {}
    daily_profit_loss = item.get("dailyProfitLoss", {}) if isinstance(item.get("dailyProfitLoss"), dict) else {}
    amount = decimal_or_none(market_value.get("amount"))
    total_amount = decimal_or_none(totals_by_currency.get(currency.lower()) or totals_by_currency.get(currency))
    allocation_percent = None
    if amount is not None and total_amount is not None and total_amount > 0:
        allocation_percent = (amount / total_amount) * Decimal(100)
    profit_rate = decimal_or_none(profit_loss.get("rate"))
    return {
        "symbol": item.get("symbol", ""),
        "name": item.get("name", ""),
        "marketCountry": item.get("marketCountry", ""),
        "currency": currency,
        "quantity": item.get("quantity", "0"),
        "marketValueAmount": str(amount) if amount is not None else "",
        "lastPrice": money_display(item.get("lastPrice"), currency),
        "averagePurchasePrice": money_display(item.get("averagePurchasePrice"), currency),
        "marketValue": money_display(market_value.get("amount"), currency),
        "purchaseAmount": money_display(market_value.get("purchaseAmount"), currency),
        "profitLoss": money_display(profit_loss.get("amount"), currency),
        "profitLossRate": display_ratio_percent(profit_loss.get("rate")),
        "dailyProfitLossRate": display_ratio_percent(daily_profit_loss.get("rate")),
        "allocation": display_decimal_percent(allocation_percent) if allocation_percent is not None else "-",
        "judgement": portfolio_position_label(profit_rate, allocation_percent),
    }


def portfolio_status() -> dict:
    base = {
        "enabled": TOSS_LIVE_PORTFOLIO,
        "readOnly": True,
        "cacheSeconds": TOSS_PORTFOLIO_CACHE_SECONDS,
        "ready": bool(TOSS_LIVE_PORTFOLIO and (TOSS_ACCESS_TOKEN or (TOSS_CLIENT_ID and TOSS_CLIENT_SECRET))),
    }
    if not TOSS_LIVE_PORTFOLIO:
        return {
            **base,
            "source": "disabled",
            "message": "TOSS_LIVE_PORTFOLIO가 꺼져 있어 내 자산을 조회하지 않습니다.",
            "accounts": [],
            "items": [],
            "summary": {},
            "buyingPower": {},
        }
    if not base["ready"]:
        return {
            **base,
            "source": "not-configured",
            "message": "토스 API 키 또는 액세스 토큰이 필요합니다.",
            "accounts": [],
            "items": [],
            "summary": {},
            "buyingPower": {},
        }

    accounts_payload = fetch_toss_accounts()
    accounts = account_rows(accounts_payload)
    account_seq = selected_account_seq(accounts)
    if not account_seq:
        return {
            **base,
            "source": "toss",
            "message": "조회 가능한 종합매매 계좌가 없습니다.",
            "accounts": [masked_account(account) for account in accounts],
            "selectedAccountSeq": "",
            "items": [],
            "summary": {},
            "buyingPower": {},
        }

    selected_account = find_account(accounts, account_seq)
    holdings_payload = fetch_toss_holdings(account_seq)
    result = holdings_result(holdings_payload)
    overview_market_value = result.get("marketValue", {}) if isinstance(result.get("marketValue"), dict) else {}
    totals_by_currency = currency_amounts(overview_market_value.get("amount"))
    raw_items = holding_items(holdings_payload)
    items = [normalize_holding_item(item, totals_by_currency) for item in raw_items if isinstance(item, dict)]
    items.sort(
        key=lambda item: decimal_or_none(item.get("marketValueAmount")) or Decimal("0"),
        reverse=True,
    )

    buying_power = {}
    for currency in ["KRW", "USD"]:
        try:
            payload = fetch_toss_buying_power(account_seq, currency)
            value = (payload.get("result", {}) if isinstance(payload.get("result"), dict) else {}).get("cashBuyingPower")
            buying_power[currency] = {
                "cashBuyingPower": money_display(value, currency),
                "source": "toss",
            }
        except Exception as error:
            buying_power[currency] = {
                "cashBuyingPower": "-",
                "source": "unavailable",
                "error": str(error)[:160],
            }

    profit_loss = result.get("profitLoss", {}) if isinstance(result.get("profitLoss"), dict) else {}
    daily_profit_loss = result.get("dailyProfitLoss", {}) if isinstance(result.get("dailyProfitLoss"), dict) else {}
    return {
        **base,
        "source": "toss",
        "message": "토스 보유 주식 정보를 읽기 전용으로 조회했습니다.",
        "accounts": [masked_account(account) for account in accounts],
        "selectedAccount": masked_account(selected_account),
        "selectedAccountSeq": account_seq,
        "summary": {
            "holdingCount": len(items),
            "profitLossRate": display_ratio_percent(profit_loss.get("rate")),
            "profitLossRateAfterCost": display_ratio_percent(profit_loss.get("rateAfterCost")),
            "dailyProfitLossRate": display_ratio_percent(daily_profit_loss.get("rate")),
            "marketValue": {
                "KRW": money_display(totals_by_currency.get("krw"), "KRW"),
                "USD": money_display(totals_by_currency.get("usd"), "USD"),
            },
        },
        "buyingPower": buying_power,
        "items": items[:12],
        "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
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
    filtered_count = 0
    queried_count = 0
    for index, candidate in enumerate(candidates):
        item = dict(candidate)
        if index >= NAVER_NEWS_MAX_CANDIDATES:
            if item.get("liveNews", {}).get("source") != "naver":
                item["liveNews"] = {"source": "skipped", "message": "뉴스 조회 후보 수 제한으로 건너뜀"}
            enriched.append(item)
            continue

        query = naver_query_for_candidate(item)
        payload = fetch_naver_news(query, display=NAVER_NEWS_DISPLAY, sort="date")
        queried_count += 1
        normalized = [normalize_news_item(news_item) for news_item in payload.get("items", [])]
        normalized = [news_item for news_item in normalized if news_item.get("title")]
        relevant = filter_relevant_news_items(item, normalized)
        filtered_out = max(0, len(normalized) - len(relevant))
        filtered_count += filtered_out
        normalized = relevant
        news_count += len(normalized)
        item["liveNews"] = {
            "source": "naver",
            "query": query,
            "total": len(normalized),
            "rawTotal": payload.get("total", 0),
            "display": len(normalized),
            "rawDisplay": payload.get("display", len(normalized)),
            "filteredOut": filtered_out,
            "items": normalized,
        }
        if normalized:
            live_sources = [source_from_news_item(news_item) for news_item in normalized[:3]]
            item["sources"] = [*live_sources, *item.get("sources", [])][:6]
            trend = dict(item.get("trend", {}))
            trend["newsCount"] = max(
                bounded_int(trend.get("newsCount", 0), 0, 10_000_000),
                len(normalized),
            )
            item["trend"] = trend
        enriched.append(item)

    return enriched, {
        "source": "naver",
        "enabled": True,
        "message": "네이버 뉴스 검색 결과를 반영했습니다.",
        "queriedCount": queried_count,
        "newsCount": news_count,
        "filteredNewsCount": filtered_count,
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
        filtered_count = bounded_int(live_news.get("filteredOut", 0), 0, 100)
        if item_count:
            score = max(score, bounded_int(8 + min(display_count, 10) * 2 + min(item_count, 5), 0, 22))
            notes.append(f"네이버 최신 뉴스 {item_count}건을 후보 점수에 반영")
        elif filtered_count:
            score = min(score, 8)
            notes.append("뉴스 검색 결과가 있었지만 종목명/티커와 맞지 않아 점수 반영 제외")
        if filtered_count:
            notes.append(f"관련성 낮은 뉴스 {filtered_count}건 제외")

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


def is_hidden_discovery_candidate(candidate: dict) -> bool:
    return candidate.get("discoveryTier") == "hidden" or candidate.get("opportunityType") == "hidden"


def hidden_opportunity_score(candidate: dict, score_detail: dict, notes: list[str]) -> tuple[int, list[str]]:
    signals: list[str] = []
    opportunity = bounded_int(score_detail.get("opportunity", 0), 0, 18)
    change = display_percent_to_decimal(candidate.get("change"))
    trend = candidate.get("trend", {})
    volume = display_multiplier_to_decimal(trend.get("volumeSpike") if isinstance(trend, dict) else "")
    news_items = len(candidate.get("liveNews", {}).get("items", [])) if isinstance(candidate.get("liveNews"), dict) else 0
    global_items = len(candidate.get("globalNews", {}).get("items", [])) if isinstance(candidate.get("globalNews"), dict) else 0
    is_hidden = is_hidden_discovery_candidate(candidate)

    if is_hidden:
        opportunity += 5
        signals.append("자동 발굴에서 기존 핵심 후보 밖 숨은 종목으로 분류")

    if news_items or global_items:
        opportunity += min((news_items + global_items) * 2, 6)
        signals.append(f"관련 뉴스 {news_items + global_items}건 감지")

    if change is not None:
        if Decimal("-1.5") <= change <= Decimal("1.5") and (news_items or global_items or is_hidden):
            opportunity += 4
            signals.append(f"뉴스 대비 가격 반응이 {display_change(change)}로 아직 크지 않음")
        elif change > Decimal("3"):
            opportunity -= 4
            signals.append(f"이미 {display_change(change)} 상승해 추격 위험 우선 확인")
        elif change < Decimal("-3"):
            opportunity -= 3
            signals.append(f"{display_change(change)} 약세로 반등 확인 필요")

    if volume is not None:
        if Decimal("1.2") <= volume < Decimal("2.5"):
            opportunity += 3
            signals.append(f"거래량 {volume}배로 초기 수급 반응")
        elif volume >= Decimal("2.5"):
            opportunity += 1
            signals.append(f"거래량 {volume}배로 관심은 높지만 과열 여부 확인")

    if score_detail.get("market", 0) >= 9 and is_hidden:
        opportunity += 2
        signals.append("시장 방향이 우호적인 상태에서 숨은 후보로 포착")

    if candidate.get("isWatched"):
        opportunity += 1

    opportunity = bounded_int(opportunity, 0, 18)
    if opportunity >= 8:
        notes.append(f"숨은 기회 신호 {opportunity}/18 반영")
    return opportunity, unique_texts(signals, limit=4)


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


def verdict_from_scores(total: int, readiness: int, risk: int, heat: int, opportunity: int = 0) -> str:
    if total >= 75 and readiness >= 70 and risk < 18:
        return "조건 충족 시 관찰"
    if opportunity >= 10 and total >= 65 and risk < 22 and heat < 8:
        return "숨은 기회 관찰"
    if total >= 65 and heat >= 8:
        return "눌림 대기"
    if total >= 60:
        return "준비됨"
    if risk >= 22 or total < 45:
        return "관찰 제외"
    return "조건부 관찰"


def candidate_decision_group(
    candidate: dict,
    score_detail: dict,
    total: int,
    readiness: int,
    preopen_priority: int,
) -> dict:
    risk = bounded_int(score_detail.get("riskPenalty", 0), 0, 30)
    heat = bounded_int(score_detail.get("heatPenalty", 0), 0, 20)
    opportunity = bounded_int(score_detail.get("opportunity", 0), 0, 18)
    news = bounded_int(score_detail.get("news", 0), 0, 22)
    volume = bounded_int(score_detail.get("volume", 0), 0, 18)
    price = bounded_int(score_detail.get("price", 0), 0, 16)
    action_score = bounded_int(
        (readiness * 0.35)
        + (preopen_priority * 0.2)
        + (total * 0.25)
        + (price * 0.8)
        + (volume * 0.45)
        + (opportunity * 0.5)
        - (risk * 0.55)
        - (heat * 0.3)
    )

    if risk >= 24 or total < 45:
        key, label, priority = "exclude", "오늘 제외", 4
        reason = "리스크나 종합 점수가 후보 기준에 부족합니다."
    elif total >= 75 and readiness >= 70 and risk < 18 and heat < 8:
        key, label, priority = "action", "진입 후보", 0
        reason = "점수, 준비도, 리스크 조건이 동시에 충족됩니다."
    elif opportunity >= 10 and total >= 62 and risk < 22:
        key, label, priority = "hidden", "숨은 기회", 1
        reason = "뉴스와 가격 반응 대비 아직 덜 반영된 기회 신호가 있습니다."
    elif total >= 62 and risk < 24 and (news >= 15 or volume >= 14 or price >= 14):
        key, label, priority = "momentum", "모멘텀", 2
        reason = "뉴스, 가격, 수급 중 하나 이상의 모멘텀이 확인됩니다."
    else:
        key, label, priority = "wait", "가격대 대기", 3
        reason = "후보 신호는 있으나 진입 가격이나 추가 확인이 필요합니다."

    if candidate.get("isWatched") and key in {"wait", "momentum"}:
        reason = f"관심 종목입니다. {reason}"

    return {
        "key": key,
        "label": label,
        "priority": priority,
        "score": action_score,
        "reason": reason,
    }


def decision_group_counts(candidates: list[dict]) -> dict:
    counts = {"action": 0, "hidden": 0, "momentum": 0, "wait": 0, "exclude": 0}
    for item in candidates:
        group = item.get("decisionGroup", {}) if isinstance(item, dict) else {}
        key = str(group.get("key", "wait")) if isinstance(group, dict) else "wait"
        counts[key if key in counts else "wait"] += 1
    return counts


def candidate_data_confidence(candidate: dict) -> dict:
    score = 0
    reasons: list[str] = []
    warnings: list[str] = []

    live_price = candidate.get("livePrice", {})
    if isinstance(live_price, dict) and live_price.get("source") == "toss":
        score += 28
        reasons.append("토스 현재가 확인")
        if live_price.get("changeSource") == "toss-candles":
            score += 8
            reasons.append("일봉 기준 등락률 확인")
        elif display_percent_to_decimal(candidate.get("change")) is not None:
            score += 4
        if live_price.get("baselineWarning"):
            score -= 10
            warnings.append("샘플 기준가와 현재가 차이 큼")
    elif display_number_to_decimal(candidate.get("price")) is not None:
        score += 10
        warnings.append("현재가는 샘플 또는 비실시간 값")
    else:
        warnings.append("현재가 미확인")

    live_candles = candidate.get("liveCandles", {})
    if isinstance(live_candles, dict) and live_candles.get("source") == "toss":
        score += 18
        reasons.append("토스 일봉 확인")
    elif isinstance(live_candles, dict) and live_candles.get("source") == "stale":
        score += 4
        warnings.append("일봉 데이터 최신성 확인 필요")

    for key, label in [("liveOrderbook", "호가"), ("liveTrades", "체결")]:
        payload = candidate.get(key, {})
        if isinstance(payload, dict) and payload.get("source") == "toss":
            score += 7
            reasons.append(f"토스 {label} 확인")

    live_news = candidate.get("liveNews", {})
    news_items = len(live_news.get("items", [])) if isinstance(live_news, dict) and isinstance(live_news.get("items"), list) else 0
    if news_items:
        score += min(18, 8 + news_items * 3)
        reasons.append(f"관련 뉴스 {news_items}건")
    elif isinstance(live_news, dict) and live_news.get("filteredOut"):
        warnings.append("뉴스 검색 결과의 종목 관련성 낮음")

    global_news = candidate.get("globalNews", {})
    global_items = len(global_news.get("items", [])) if isinstance(global_news, dict) and isinstance(global_news.get("items"), list) else 0
    if global_items:
        score += min(10, 5 + global_items * 2)
        reasons.append(f"글로벌 뉴스 {global_items}건")

    live_disclosures = candidate.get("liveDisclosures", {})
    if isinstance(live_disclosures, dict) and live_disclosures.get("source") == "dart":
        score += 8
        reasons.append("OpenDART 확인")
        if isinstance(live_disclosures.get("items"), list) and live_disclosures.get("items"):
            warnings.append("최근 공시 리스크 확인 필요")

    discovery = candidate.get("discovery", {}) if isinstance(candidate.get("discovery"), dict) else {}
    quality_tier = discovery.get("qualityTier")
    if quality_tier == "primary":
        score += 8
    elif quality_tier == "reserve":
        score += 4
    elif quality_tier == "rejected":
        score -= 12
        warnings.append("발굴 품질 기준 미달")

    score = bounded_int(score, 0, 100)
    if score >= 75:
        label = "높음"
    elif score >= 60:
        label = "보통"
    elif score >= 45:
        label = "낮음"
    else:
        label = "부족"

    return {
        "score": score,
        "label": label,
        "reasons": unique_texts(reasons, limit=5),
        "warnings": unique_texts(warnings, limit=4),
    }


def candidate_quality_gate(candidate: dict, score_detail: dict, total: int, readiness: int, confidence: dict) -> dict:
    group = candidate.get("decisionGroup", {}) if isinstance(candidate.get("decisionGroup"), dict) else {}
    group_key = str(group.get("key", "wait"))
    risk = bounded_int(score_detail.get("riskPenalty", 0), 0, 30)
    heat = bounded_int(score_detail.get("heatPenalty", 0), 0, 20)
    confidence_score = bounded_int(confidence.get("score", 0), 0, 100)
    live_price = candidate.get("livePrice", {})
    has_live_price = isinstance(live_price, dict) and live_price.get("source") == "toss"
    reasons = []

    if risk >= 24 or total < 45 or group_key == "exclude":
        key, label, priority = "exclude", "오늘 제외", 4
        reasons.append("리스크 또는 종합 점수가 기준 미달")
    elif group_key == "action" and has_live_price and confidence_score >= 68 and risk < 18 and heat < 10 and readiness >= 70:
        key, label, priority = "actionable", "실전 후보", 0
        reasons.append("가격·준비도·신뢰도 기준 통과")
    elif group_key in {"hidden", "momentum"} and confidence_score >= 55 and risk < 22:
        key, label, priority = "watch", "관찰 후보", 1
        reasons.append("재료는 있으나 진입 조건 추가 확인")
    elif confidence_score < 45 or not has_live_price:
        key, label, priority = "defer", "확인 대기", 3
        reasons.append("실시간 가격 또는 근거 데이터 부족")
    elif total >= 62 and risk < 22:
        key, label, priority = "watch", "관찰 후보", 2
        reasons.append("후보 점수는 있으나 가격 조건 확인 필요")
    else:
        key, label, priority = "defer", "확인 대기", 3
        reasons.append("신규 진입보다 조건 확인 우선")

    return {
        "key": key,
        "label": label,
        "priority": priority,
        "confidenceScore": confidence_score,
        "tradeAllowed": key == "actionable",
        "reasons": unique_texts([*reasons, *confidence.get("warnings", [])], limit=5),
    }


def apply_candidate_selection(candidates: list[dict], market: dict, watched: set[str]) -> tuple[list[dict], dict]:
    enriched = []
    score_shifts = []
    opportunity_scores = []
    confidence_scores = []
    gate_counts = {"actionable": 0, "watch": 0, "defer": 0, "exclude": 0}
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
        opportunity, opportunity_signals = hidden_opportunity_score(item, score_detail, notes)
        score_detail["opportunity"] = opportunity
        total = score_candidate({"score": score_detail})
        readiness = bounded_int(
            (total * 0.58)
            + (price * 1.4)
            + (volume * 0.7)
            + (market_score * 0.6)
            + (opportunity * 0.45)
            - (risk * 0.45)
        )
        preopen_priority = bounded_int(
            (total * 0.66)
            + (news * 0.9)
            + (event * 0.45)
            + (market_score * 0.8)
            + (opportunity * 0.65)
            - (heat * 0.5)
        )
        shift = total - original_total
        score_shifts.append(shift)
        opportunity_scores.append(opportunity)

        item["score"] = score_detail
        item["totalScore"] = total
        item["triggerReadiness"] = readiness
        item["preopenPriority"] = preopen_priority
        item["verdict"] = verdict_from_scores(total, readiness, risk, heat, opportunity)
        item["decisionGroup"] = candidate_decision_group(item, score_detail, total, readiness, preopen_priority)
        confidence = candidate_data_confidence(item)
        gate = candidate_quality_gate(item, score_detail, total, readiness, confidence)
        confidence_scores.append(bounded_int(confidence.get("score", 0), 0, 100))
        gate_counts[gate["key"]] = gate_counts.get(gate["key"], 0) + 1
        if gate["key"] in {"defer", "exclude"} and item["decisionGroup"].get("key") == "action":
            item["decisionGroup"] = {
                **item["decisionGroup"],
                "key": "wait" if gate["key"] == "defer" else "exclude",
                "label": "확인 대기" if gate["key"] == "defer" else "오늘 제외",
                "priority": 3 if gate["key"] == "defer" else 4,
                "reason": "신뢰도 게이트에서 실전 진입 후보로 인정하지 않았습니다.",
            }
        item["hiddenOpportunity"] = {
            "score": opportunity,
            "maxScore": 18,
            "signals": opportunity_signals,
            "tier": item.get("discoveryTier", "core"),
            "type": item.get("opportunityType", "core"),
        }
        item["selection"] = {
            "source": "live-rules",
            "previousScore": original_total,
            "scoreChange": shift,
            "opportunityScore": opportunity,
            "components": score_detail,
            "notes": unique_texts(notes, limit=5),
            "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
        }
        item["dataConfidence"] = confidence
        item["qualityGate"] = gate
        enriched.append(item)

    average_shift = sum(score_shifts) / len(score_shifts) if score_shifts else 0
    average_opportunity = sum(opportunity_scores) / len(opportunity_scores) if opportunity_scores else 0
    average_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
    hidden_opportunity_count = len([score for score in opportunity_scores if score >= 8])
    groups = decision_group_counts(enriched)
    return enriched, {
        "source": "live-rules",
        "enabled": True,
        "message": "뉴스, 시세, 지수, 공시 신호로 후보 점수를 재계산했습니다.",
        "candidateCount": len(enriched),
        "averageScoreShift": round(average_shift, 1),
        "averageOpportunityScore": round(average_opportunity, 1),
        "averageDataConfidence": round(average_confidence, 1),
        "hiddenOpportunityCount": hidden_opportunity_count,
        "decisionGroups": groups,
        "actionCandidateCount": groups.get("action", 0),
        "qualityGateCounts": gate_counts,
        "investableCandidateCount": gate_counts.get("actionable", 0),
        "watchCandidateCount": gate_counts.get("watch", 0),
        "deferCandidateCount": gate_counts.get("defer", 0),
        "momentumCandidateCount": groups.get("momentum", 0),
        "waitCandidateCount": groups.get("wait", 0),
        "excludeCandidateCount": groups.get("exclude", 0),
        "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
    }


def score_candidate(candidate: dict) -> int:
    score = candidate.get("score", {})
    positive = sum(
        int(score.get(key, 0))
        for key in ["event", "news", "volume", "price", "market", "attention", "opportunity"]
    )
    penalty = sum(int(score.get(key, 0)) for key in ["riskPenalty", "heatPenalty"])
    return max(0, min(100, positive - penalty))


def decorate_candidate(candidate: dict, watched: set[str]) -> dict:
    decorated = dict(candidate)
    decorated["totalScore"] = score_candidate(candidate)
    decorated["isWatched"] = candidate.get("symbol") in watched
    return decorated


def normalized_search_text(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "")).lower()


HANGUL_INITIALS = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"


STOCK_SEARCH_ALIAS_OVERRIDES = {
    "005930": ["삼전", "삼성반도체", "삼성전자보통주", "samsung"],
    "000660": ["하닉", "하이닉", "sk하닉", "에스케이하이닉스"],
    "035420": ["네이버", "naver"],
    "035720": ["카톡", "카카오톡", "kakao"],
    "005380": ["현차", "현대자동차"],
    "012450": ["한에어", "한화에어로", "한화방산"],
    "207940": ["삼바", "삼성바이오"],
    "068270": ["셀트", "셀트리온"],
    "091160": ["반도체etf", "코덱스반도체"],
    "AAPL": ["애플", "apple"],
    "NVDA": ["엔비", "엔비디아", "nvidia"],
    "MSFT": ["마소", "마이크로", "마이크로소프트", "microsoft"],
    "TSLA": ["테슬라", "tesla"],
    "AMD": ["암드", "advancedmicrodevices"],
    "AVGO": ["브컴", "브로드컴", "broadcom"],
    "AMZN": ["아마존", "aws", "amazon"],
    "GOOGL": ["구글", "알파벳", "alphabet", "google"],
    "META": ["메타", "페북", "facebook"],
    "TSM": ["tsmc", "대만반도체", "파운드리"],
    "ASML": ["euv", "반도체장비"],
    "PLTR": ["팔란티어", "palantir"],
    "VRT": ["버티브", "vertiv"],
    "SMCI": ["슈마컴", "슈퍼마이크로", "supermicro"],
}


def hangul_initials(value: str) -> str:
    letters = []
    for char in str(value or ""):
        code = ord(char) - 0xAC00
        if 0 <= code <= 11171:
            letters.append(HANGUL_INITIALS[code // 588])
        elif char.strip():
            letters.append(char.lower())
    return normalized_search_text("".join(letters))


def expanded_stock_aliases(symbol: str, aliases: list[str] | None = None) -> list[str]:
    normalized_symbol = str(symbol or "").strip().upper()
    return unique_texts(
        [
            *(aliases or []),
            *STOCK_SEARCH_ALIAS_OVERRIDES.get(normalized_symbol, []),
        ],
        limit=16,
    )


def search_query_looks_symbol(query: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9.\-]{2,20}", query.strip()))


def universe_aliases_for_symbol(symbol: str) -> list[str]:
    normalized_symbol = str(symbol or "").strip().upper()
    if not normalized_symbol:
        return []
    for entry in universe_data().get("symbols", []):
        if not isinstance(entry, dict):
            continue
        if str(entry.get("symbol", "")).strip().upper() == normalized_symbol:
            return expanded_stock_aliases(normalized_symbol, text_list(entry.get("aliases", []), limit=12))
    return []


def candidate_search_result(candidate: dict) -> dict:
    aliases = unique_texts(
        [
            *text_list(candidate.get("aliases", []), limit=8),
            *universe_aliases_for_symbol(str(candidate.get("symbol", ""))),
        ],
        limit=16,
    )
    aliases = expanded_stock_aliases(str(candidate.get("symbol", "")), aliases)
    return {
        "symbol": candidate.get("symbol", ""),
        "name": candidate.get("name", candidate.get("symbol", "")),
        "market": candidate.get("market", ""),
        "category": candidate.get("category", ""),
        "aliases": aliases,
        "price": candidate.get("price", "-"),
        "change": candidate.get("change", ""),
        "headline": candidate.get("headline", ""),
        "score": candidate.get("totalScore", score_candidate(candidate)),
        "updated": candidate.get("updated", ""),
        "isWatched": bool(candidate.get("isWatched")),
        "inCandidates": True,
        "source": "candidate",
        "sourceLabel": "오늘 후보",
    }


def search_haystack(values: list[object]) -> str:
    flattened = []
    for value in values:
        if isinstance(value, list):
            flattened.extend(str(item) for item in value if item)
        elif value:
            flattened.append(str(value))
    return normalized_search_text(" ".join(flattened))


def search_terms_for_item(item: dict) -> list[tuple[str, str]]:
    terms: list[tuple[str, str]] = []
    for label, key in [
        ("코드", "symbol"),
        ("종목명", "name"),
        ("영문명", "englishName"),
        ("테마", "headline"),
    ]:
        value = item.get(key)
        if value:
            terms.append((label, str(value)))
    for alias in text_list(item.get("aliases", []), limit=16):
        terms.append(("별칭", alias))
    for theme in text_list(item.get("themes", []), limit=8):
        terms.append(("테마", theme))
    return terms


def stock_search_match_info(query: str, item: dict) -> dict:
    normalized_query = normalized_search_text(query)
    if not normalized_query:
        return {"matched": False, "rank": 99, "field": "", "text": ""}

    best = {"matched": False, "rank": 99, "field": "", "text": ""}
    for field, raw_text in search_terms_for_item(item):
        text = str(raw_text or "")
        normalized_text = normalized_search_text(text)
        if not normalized_text:
            continue
        initials = hangul_initials(text)
        rank = None
        if normalized_query == normalized_text:
            rank = 0
        elif normalized_text.startswith(normalized_query):
            rank = 1
        elif initials and initials.startswith(normalized_query):
            rank = 2
        elif normalized_query in normalized_text:
            rank = 3
        elif initials and normalized_query in initials:
            rank = 4
        if rank is not None and rank < best["rank"]:
            best = {"matched": True, "rank": rank, "field": field, "text": text}
    return best


def search_relevance_rank(query: str, item: dict) -> tuple[int, int, int]:
    match = item.get("match")
    if not isinstance(match, dict) or normalized_search_text(match.get("query", "")) != normalized_search_text(query):
        match = stock_search_match_info(query, item)
    bucket = bounded_int(match.get("rank", 99), 0, 99)
    score = bounded_int(item.get("score", item.get("totalScore", 0)), 0, 100)
    name = normalized_search_text(item.get("name", ""))
    symbol = normalized_search_text(item.get("symbol", ""))
    return bucket, -score, len(name or symbol)


def seed_candidate_search(query: str, watched: set[str], limit: int = 8) -> list[dict]:
    normalized_query = normalized_search_text(query)
    if not normalized_query:
        return []
    matches = []
    for candidate in seed_data().get("candidates", []):
        decorated = decorate_candidate(candidate, watched)
        result = candidate_search_result(decorated)
        match = stock_search_match_info(query, result)
        if not match.get("matched"):
            continue
        result["match"] = {**match, "query": query}
        matches.append(result)
    matches.sort(key=lambda item: search_relevance_rank(query, item))
    return matches[:limit]


def universe_search_result(entry: dict, watched: set[str]) -> dict:
    symbol = str(entry.get("symbol", "")).strip().upper()
    name = str(entry.get("name") or symbol).strip()
    focus = bounded_int(entry.get("focusWeight", 5), 0, 15)
    themes = text_list(entry.get("themes", []), limit=4)
    return {
        "symbol": symbol,
        "name": name,
        "market": entry.get("market", ""),
        "category": entry.get("category", ""),
        "discoveryTier": entry.get("discoveryTier", "core"),
        "opportunityType": entry.get("opportunityType", "core"),
        "aliases": expanded_stock_aliases(symbol, text_list(entry.get("aliases", []), limit=12)),
        "price": "-",
        "change": "",
        "headline": " · ".join(themes) if themes else f"{name} 감시 유니버스",
        "score": bounded_int(42 + focus * 3, 0, 100),
        "updated": "자동완성",
        "isWatched": symbol in watched,
        "inCandidates": False,
        "source": "universe",
        "sourceLabel": "감시 유니버스",
    }


def universe_candidate_search(query: str, watched: set[str], limit: int = 8, existing_symbols: set[str] | None = None) -> list[dict]:
    normalized_query = normalized_search_text(query)
    if not normalized_query:
        return []
    existing_symbols = existing_symbols or set()
    matches = []
    for entry in candidate_universe_entries():
        symbol = str(entry.get("symbol", "")).strip().upper()
        if not symbol or symbol in existing_symbols:
            continue
        result = universe_search_result(entry, watched)
        result["englishName"] = entry.get("englishName", "")
        result["themes"] = text_list(entry.get("themes", []), limit=6)
        result["aliases"] = expanded_stock_aliases(symbol, text_list(entry.get("aliases", []), limit=12))
        match = stock_search_match_info(query, result)
        if not match.get("matched"):
            continue
        result["match"] = {**match, "query": query}
        matches.append(result)
    matches.sort(key=lambda item: search_relevance_rank(query, item))
    return matches[:limit]


def stock_category(stock: dict) -> str:
    market = str(stock.get("market", "")).upper()
    currency = str(stock.get("currency", "")).upper()
    if currency == "USD" or market in {"NASDAQ", "NYSE", "AMEX", "ARCA", "BATS"}:
        return "overseas"
    return "domestic"


def stock_search_result(stock: dict, price: dict | None, watched: set[str]) -> dict:
    symbol = str(stock.get("symbol", "")).strip().upper()
    stock_currency = str(stock.get("currency", "")).strip().upper()
    price_currency = str(price.get("currency", "")).strip().upper() if price else ""
    currency = stock_currency or price_currency
    price_text = "-"
    if price and price.get("lastPrice") and price.get("currency"):
        price_text = display_price(str(price.get("lastPrice")), str(price.get("currency")))
    return {
        "symbol": symbol,
        "name": stock.get("name") or stock.get("englishName") or symbol,
        "englishName": stock.get("englishName", ""),
        "market": stock.get("market", ""),
        "category": stock_category(stock),
        "securityType": stock.get("securityType", ""),
        "status": stock.get("status", ""),
        "currency": currency,
        "aliases": universe_aliases_for_symbol(symbol),
        "price": price_text,
        "change": "",
        "headline": "토스증권 종목 기본정보 조회 결과",
        "score": None,
        "updated": "직접 조회",
        "isWatched": symbol in watched,
        "inCandidates": False,
        "source": "toss",
        "sourceLabel": "토스 종목정보",
        "livePrice": {
            "source": "toss" if price_text != "-" else "unavailable",
            "lastPrice": str(price.get("lastPrice")) if price else "",
            "currency": str(price.get("currency")) if price else currency,
            "timestamp": price.get("timestamp") if price else "",
        },
    }


def stock_search(query: str, limit: int = 8) -> dict:
    query = query.strip()
    limit = max(1, min(int(limit), 20))
    watched = set(watchlist())
    candidate_items = seed_candidate_search(query, watched, limit=limit)
    items = list(candidate_items)
    existing_symbols = {str(item.get("symbol", "")).upper() for item in items}
    if query:
        items.extend(universe_candidate_search(query, watched, limit=limit, existing_symbols=existing_symbols))
        items.sort(key=lambda item: search_relevance_rank(query, item))
        items = items[:limit]
    messages = []
    toss_status = {
        "source": "skipped",
        "enabled": False,
        "message": "종목명, 별칭, 코드로 자동완성합니다.",
    }

    if query and search_query_looks_symbol(query):
        if toss_config_status()["readyForMarketData"]:
            try:
                stock_payload = fetch_toss_stocks([query])
                stocks = stock_rows(stock_payload)
                prices = {}
                if TOSS_LIVE_PRICES and stocks:
                    symbols = [str(stock.get("symbol", "")) for stock in stocks if stock.get("symbol")]
                    prices = price_by_symbol(fetch_toss_prices(symbols))
                existing_symbols = {str(item.get("symbol", "")).upper() for item in items}
                for stock in stocks:
                    symbol = str(stock.get("symbol", "")).upper()
                    if not symbol or symbol in existing_symbols:
                        continue
                    result = stock_search_result(stock, prices.get(symbol), watched)
                    result["match"] = {**stock_search_match_info(query, result), "query": query}
                    items.append(result)
                toss_status = {
                    "source": "toss",
                    "enabled": True,
                    "message": "토스증권 종목 기본정보를 조회했습니다.",
                    "stockCount": len(stocks),
                    "priceCount": len(prices),
                }
            except Exception as error:
                payload, _ = integration_error_payload(error)
                toss_status = {
                    "source": "error",
                    "enabled": True,
                    "error": payload.get("error", "unknown"),
                    "status": payload.get("status"),
                    "detail": payload.get("detail", ""),
                    "message": payload.get("message", "토스 종목 조회에 실패했습니다."),
                }
                if not items:
                    messages.append(toss_status["message"])
        else:
            toss_status = {
                "source": "disabled",
                "enabled": False,
                "message": "토스증권 키/토큰 또는 허용 IP 설정 후 종목 코드 직접 조회가 가능합니다.",
            }
            if not items:
                messages.append(toss_status["message"])
    elif query and not items:
        messages.append("종목명 일부, 별칭, 코드나 티커로 검색할 수 있습니다.")

    if not items and not messages:
        messages.append("검색 결과가 없습니다.")

    return {
        "query": query,
        "items": sorted(items[:limit], key=lambda item: search_relevance_rank(query, item)),
        "status": toss_status,
        "message": " ".join(unique_texts(messages, limit=3)),
        "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
    }


def candidate_market_from_search_item(item: dict) -> str:
    if item.get("category") == "overseas":
        return "US"
    market = str(item.get("market", "")).upper()
    currency = str(item.get("currency", "")).upper()
    if currency == "USD" or market in {"NASDAQ", "NYSE", "AMEX", "ARCA", "BATS"}:
        return "US"
    return "KR"


def candidate_from_stock_search_item(item: dict) -> dict:
    symbol = str(item.get("symbol", "")).strip().upper()
    name = str(item.get("name") or symbol).strip()
    tags = unique_texts(
        [
            "종목 검색",
            str(item.get("market", "")),
            str(item.get("securityType", "")),
            str(item.get("currency", "")),
            str(item.get("status", "")),
        ],
        limit=5,
    )
    return {
        "symbol": symbol,
        "name": name,
        "englishName": item.get("englishName", ""),
        "market": candidate_market_from_search_item(item),
        "category": item.get("category", "domestic"),
        "price": item.get("price") or "-",
        "change": item.get("change") or "",
        "updated": "검색 분석",
        "headline": f"{name} 검색 종목 분석",
        "verdict": "분석 대기",
        "stage": "lookup-analysis",
        "preopenPriority": 0,
        "triggerReadiness": 0,
        "score": {
            "event": 8,
            "news": 4,
            "volume": 4,
            "price": 6,
            "market": 5,
            "attention": 4,
            "riskPenalty": 6,
            "heatPenalty": 2,
        },
        "tags": tags or ["종목 검색"],
        "thesis": "후보 목록 밖에서 직접 검색한 종목입니다. 최신 뉴스, 공시, 가격 반응을 연결해 관찰 가능성을 점검합니다.",
        "why": [
            f"{name} 기본정보를 조회했습니다.",
            "검색 종목은 후보 편입 전 가격, 뉴스, 공시 근거를 먼저 확인합니다.",
        ],
        "entryConditions": [
            "뉴스와 공시 재료가 최근 가격 반응과 같은 방향인지 확인",
            "거래대금과 섹터 흐름이 후보 기준을 충족하는지 확인",
            "손절 기준이 진입가에서 3% 안쪽으로 관리되는 가격대인지 확인",
        ],
        "noEntry": [
            "뉴스만 있고 실제 수급 반응이 확인되지 않은 경우",
            "현재가나 거래량 데이터가 연결되지 않은 상태",
            "공시 리스크가 가격 반응보다 큰 경우",
        ],
        "stopRules": [
            "후보 편입 후 기준 가격 재이탈",
            "섹터 동반 약세 전환",
            "거래량 없는 상승만 이어지는 경우",
        ],
        "trend": {
            "newsCount": 0,
            "globalNewsCount": None,
            "newsSpike": "-",
            "volumeSpike": "-",
            "dailyVolume": "-",
            "tradePressure": "-",
            "orderbookPressure": "-",
            "spread": "-",
            "sentiment": "-",
        },
        "sources": [
            {
                "title": item.get("sourceLabel") or "종목 기본정보 조회",
                "publisher": "Toss Open API" if item.get("source") == "toss" else "후보 목록",
                "time": item.get("updated") or "검색",
            }
        ],
        "disclosures": [
            "직접 조회 종목은 후보 편입 전 검증 단계입니다.",
            "가격 행동 구간은 수집된 현재가 기준으로 계산됩니다.",
        ],
        "related": [],
        "chart": [50, 50, 50, 50, 50, 50],
        "livePrice": item.get("livePrice") or {"source": "lookup", "message": "종목 검색 결과입니다."},
        "liveCandles": {"source": "lookup"},
        "lookupOnly": False,
        "candidateSource": "search-analysis",
    }


def lookup_candidate_for_symbol(symbol: str, watched: set[str]) -> tuple[dict, dict]:
    symbol = symbol.strip().upper()
    if not symbol:
        raise ValueError("분석할 종목 코드가 필요합니다.")

    seed_lookup = seed_candidate_by_symbol()
    if symbol in seed_lookup:
        candidate = copy.deepcopy(seed_lookup[symbol])
        candidate["candidateSource"] = "search-candidate"
        return decorate_candidate(candidate, watched), {
            "source": "candidate",
            "message": "오늘 후보에 있는 종목을 분석합니다.",
        }

    universe_match = next(
        (
            entry
            for entry in candidate_universe_entries()
            if str(entry.get("symbol", "")).strip().upper() == symbol
        ),
        None,
    )
    if universe_match:
        candidate = default_candidate_for_entry(universe_match, [], {"source": "lookup", "total": 0})
        candidate["candidateSource"] = "search-universe"
        candidate["updated"] = "검색 분석"
        return decorate_candidate(candidate, watched), {
            "source": "universe",
            "message": "감시 유니버스에 있는 종목을 분석합니다.",
        }

    search_payload = stock_search(symbol, limit=8)
    items = search_payload.get("items", []) if isinstance(search_payload, dict) else []
    exact = next(
        (item for item in items if str(item.get("symbol", "")).strip().upper() == symbol),
        items[0] if items else None,
    )
    if not exact:
        raise ValueError("검색 종목을 찾지 못했습니다.")
    candidate = candidate_from_stock_search_item(exact)
    return decorate_candidate(candidate, watched), {
        "source": exact.get("source", "lookup"),
        "message": "후보 밖 검색 종목을 분석합니다.",
        "searchStatus": search_payload.get("status", {}),
    }


def search_analysis_error_status(source: str, error: Exception, fallback_message: str) -> dict:
    payload, _ = integration_error_payload(error)
    return {
        "source": source,
        "enabled": True,
        "error": payload.get("error", "unknown"),
        "status": payload.get("status"),
        "detail": payload.get("detail", ""),
        "message": payload.get("message", fallback_message),
    }


def analyze_stock_lookup(symbol: str) -> dict:
    watched = set(watchlist())
    data = seed_data()
    market, index_status = enrich_market_with_indices(data.get("market", {}))
    market, fx_status = enrich_market_with_fx(market)
    candidate, lookup_status = lookup_candidate_for_symbol(symbol, watched)
    candidates = [candidate]

    statuses: dict[str, dict] = {
        "lookup": lookup_status,
        "indices": index_status,
        "fx": fx_status,
    }

    try:
        candidates, statuses["prices"] = enrich_candidates_with_toss_prices(candidates)
    except Exception as error:
        statuses["prices"] = search_analysis_error_status("sample", error, "토스 현재가 반영에 실패했습니다.")
    try:
        candidates, statuses["candles"] = enrich_candidates_with_toss_candles(candidates)
    except Exception as error:
        statuses["candles"] = search_analysis_error_status("sample", error, "토스 일봉 반영에 실패했습니다.")
    try:
        candidates, statuses["disclosures"] = enrich_candidates_with_dart_disclosures(candidates)
    except Exception as error:
        statuses["disclosures"] = search_analysis_error_status("sample", error, "OpenDART 공시 반영에 실패했습니다.")
    try:
        candidates, statuses["naver"] = enrich_candidates_with_naver_news(candidates)
    except Exception as error:
        statuses["naver"] = search_analysis_error_status("sample", error, "네이버 뉴스 반영에 실패했습니다.")
    try:
        candidates, statuses["gdelt"] = enrich_candidates_with_gdelt_news(candidates)
    except Exception as error:
        statuses["gdelt"] = search_analysis_error_status("sample", error, "GDELT 글로벌 뉴스 반영에 실패했습니다.")

    candidates, statuses["selection"] = apply_candidate_selection(candidates, market, watched)

    try:
        candidates, statuses["analysis"] = enrich_candidates_with_openai_analysis(candidates)
    except Exception as error:
        statuses["analysis"] = search_analysis_error_status("local", error, "OpenAI 분석에 실패해 로컬 분석을 사용합니다.")
        candidates = [apply_analysis_to_candidate(candidate, local_candidate_analysis(candidate)) for candidate in candidates]

    item = candidates[0]
    item["lookupOnly"] = False
    item["analysisMode"] = "search"
    item["updated"] = "검색 분석"
    return {
        "symbol": item.get("symbol"),
        "candidate": item,
        "status": statuses,
        "generatedAt": datetime.now(KST).isoformat(timespec="seconds"),
    }


def seed_candidate_by_symbol() -> dict[str, dict]:
    return {
        str(candidate.get("symbol", "")).strip().upper(): candidate
        for candidate in seed_data().get("candidates", [])
        if candidate.get("symbol")
    }


def candidate_universe_entries() -> list[dict]:
    entries = []
    seen = set()
    seed_lookup = seed_candidate_by_symbol()

    for entry in universe_data().get("symbols", []):
        if not isinstance(entry, dict):
            continue
        symbol = str(entry.get("symbol", "")).strip().upper()
        if not symbol or symbol in seen:
            continue
        item = dict(entry)
        item["symbol"] = symbol
        entries.append(item)
        seen.add(symbol)

    for symbol in [value.strip().upper() for value in SIGNAL_DISCOVERY_SYMBOLS.split(",") if value.strip()]:
        if symbol in seen:
            continue
        seed = seed_lookup.get(symbol, {})
        entries.append({
            "symbol": symbol,
            "name": seed.get("name", symbol),
            "market": seed.get("market", "US" if re.fullmatch(r"[A-Z.\-]+", symbol) else "KR"),
            "category": seed.get("category", "overseas" if re.fullmatch(r"[A-Z.\-]+", symbol) else "domestic"),
            "themes": seed.get("tags", []),
            "query": seed.get("name", symbol),
            "focusWeight": 5,
        })
        seen.add(symbol)

    for symbol, seed in seed_lookup.items():
        if symbol in seen:
            continue
        entries.append({
            "symbol": symbol,
            "name": seed.get("name", symbol),
            "market": seed.get("market", ""),
            "category": seed.get("category", ""),
            "themes": seed.get("tags", []),
            "query": seed.get("name", symbol),
            "focusWeight": 5,
        })
        seen.add(symbol)

    return entries


def universe_query(entry: dict) -> str:
    query = str(entry.get("query", "")).strip()
    if query:
        return query
    name = str(entry.get("name", "")).strip()
    symbol = str(entry.get("symbol", "")).strip()
    themes = " ".join(str(theme) for theme in entry.get("themes", []) if theme)
    return " ".join(value for value in [name or symbol, themes] if value).strip()


def compact_match_text(value: str) -> str:
    return re.sub(r"[\s·\-_.,'\"()\[\]{}:;|/\\]+", "", clean_news_text(value)).lower()


def news_relevance_terms(entry: dict) -> list[str]:
    terms = [
        str(entry.get("symbol", "")),
        str(entry.get("name", "")),
        str(entry.get("englishName", "")),
    ]
    aliases = entry.get("aliases", [])
    if isinstance(aliases, list):
        terms.extend(str(alias) for alias in aliases)
    return unique_texts([term for term in terms if len(str(term).strip()) >= 2], limit=12)


def news_matches_entry(entry: dict, item: dict) -> bool:
    text = compact_match_text(
        " ".join(
            [
                str(item.get("title", "")),
                str(item.get("summary", "")),
            ]
        )
    )
    if not text:
        return False
    for term in news_relevance_terms(entry):
        normalized = compact_match_text(term)
        if len(normalized) >= 2 and normalized in text:
            return True
    return False


def filter_relevant_news_items(entry: dict, items: list[dict]) -> list[dict]:
    relevant = [item for item in items if news_matches_entry(entry, item)]
    if relevant:
        return relevant
    return []


def discovery_news_for_entry(entry: dict) -> tuple[list[dict], dict]:
    if not (NAVER_LIVE_NEWS and naver_news_config_status()["readyForNews"]):
        return [], {
            "source": "disabled",
            "message": "네이버 뉴스 설정 전이라 유니버스 기본 점수로 후보를 구성합니다.",
        }

    query = universe_query(entry)
    payload = fetch_naver_news(query, display=SIGNAL_DISCOVERY_NEWS_DISPLAY, sort="date")
    normalized = [normalize_news_item(news_item) for news_item in payload.get("items", [])]
    normalized = [news_item for news_item in normalized if news_item.get("title")]
    relevant = filter_relevant_news_items(entry, normalized)
    return relevant, {
        "source": "naver",
        "query": query,
        "total": len(relevant),
        "rawTotal": payload.get("total", 0),
        "display": len(relevant),
        "rawDisplay": payload.get("display", len(normalized)),
        "filteredOut": max(0, len(normalized) - len(relevant)),
    }


def default_candidate_for_entry(entry: dict, news_items: list[dict], news_status: dict) -> dict:
    symbol = str(entry.get("symbol", "")).strip().upper()
    name = str(entry.get("name", "") or symbol).strip()
    themes = text_list(entry.get("themes", []), limit=6)
    headline = news_items[0].get("title") if news_items else f"{name} 관련 신호 점검"
    source_items = [source_from_news_item(item) for item in news_items[:3]]
    news_total = bounded_int(news_status.get("total", len(news_items)), 0, 10_000_000)
    focus = bounded_int(entry.get("focusWeight", 5), 0, 15)
    return {
        "symbol": symbol,
        "name": name,
        "market": entry.get("market", "KR"),
        "category": entry.get("category", "domestic"),
        "discoveryTier": entry.get("discoveryTier", "core"),
        "opportunityType": entry.get("opportunityType", "core"),
        "aliases": text_list(entry.get("aliases", []), limit=10),
        "price": "-",
        "change": "",
        "updated": "자동 선정",
        "headline": headline,
        "verdict": "자동 후보",
        "stage": "auto",
        "preopenPriority": 0,
        "triggerReadiness": 0,
        "score": {
            "event": bounded_int(9 + focus + min(len(news_items), 3) * 2, 0, 25),
            "news": bounded_int(6 + min(len(news_items), 5) * 3 + min(news_total, 30) // 10, 0, 22),
            "volume": 8,
            "price": 8,
            "market": 6,
            "attention": bounded_int(4 + focus // 2, 0, 12),
            "riskPenalty": 5,
            "heatPenalty": 2,
        },
        "tags": themes[:6] or ["자동 후보"],
        "thesis": "유니버스 종목 중 최신 뉴스와 관심 테마가 감지되어 후보로 올렸습니다. 실제 진입은 가격, 거래량, 공시 리스크 확인 후 판단합니다.",
        "why": unique_texts(
            [
                *(item.get("summary") or item.get("title") for item in news_items[:3]),
                f"{name} 관련 최신 뉴스 {len(news_items)}건을 확인했습니다." if news_items else "",
                "후보 편입 후 시세와 거래대금 반응을 추가 확인합니다.",
            ],
            limit=5,
        ),
        "entryConditions": [
            "현재가와 전일 대비 방향이 뉴스 재료와 같은지 확인",
            "5분 거래대금이 최근 평균보다 증가하는지 확인",
            "돌파 또는 눌림 기준가가 손절 3% 안쪽인지 확인",
        ],
        "noEntry": [
            "뉴스는 있으나 가격과 거래량 반응이 없는 경우",
            "지수와 섹터가 동시에 약세로 전환되는 경우",
            "공시 리스크가 가격 반응보다 큰 경우",
        ],
        "stopRules": [
            "기준가 재이탈",
            "VWAP 회복 실패",
            "거래량 실린 음봉 발생",
        ],
        "trend": {
            "newsCount": news_total or len(news_items),
            "newsSpike": "-",
            "volumeSpike": "-",
            "sentiment": "뉴스 확인 필요",
        },
        "sources": source_items,
        "disclosures": [],
        "related": [],
        "chart": [50, 50, 50, 50, 50, 50],
    }


def candidate_from_universe_entry(entry: dict, seed_lookup: dict[str, dict], watched: set[str]) -> dict:
    symbol = str(entry.get("symbol", "")).strip().upper()
    news_items, news_status = discovery_news_for_entry(entry)
    base = copy.deepcopy(seed_lookup.get(symbol)) if symbol in seed_lookup else default_candidate_for_entry(entry, news_items, news_status)
    base["aliases"] = unique_texts(
        [
            *text_list(entry.get("aliases", []), limit=12),
            *text_list(base.get("aliases", []), limit=12),
        ],
        limit=12,
    )
    base["discoveryTier"] = entry.get("discoveryTier", base.get("discoveryTier", "core"))
    base["opportunityType"] = entry.get("opportunityType", base.get("opportunityType", "core"))
    if symbol in seed_lookup and news_items:
        live_sources = [source_from_news_item(item) for item in news_items[:3]]
        base["sources"] = [*live_sources, *base.get("sources", [])][:6]
        base["headline"] = news_items[0].get("title") or base.get("headline", "")
        base["why"] = unique_texts(
            [
                *(item.get("summary") or item.get("title") for item in news_items[:3]),
                *text_list(base.get("why", []), limit=5),
            ],
            limit=5,
        )
        trend = dict(base.get("trend", {}))
        trend["newsCount"] = max(
            bounded_int(trend.get("newsCount", 0), 0, 10_000_000),
            bounded_int(news_status.get("total", len(news_items)), 0, 10_000_000),
        )
        base["trend"] = trend
    if news_status.get("source") == "naver":
        base["liveNews"] = {
            "source": "naver",
            "query": news_status.get("query", universe_query(entry)),
            "total": news_status.get("total", len(news_items)),
            "rawTotal": news_status.get("rawTotal", news_status.get("total", len(news_items))),
            "display": news_status.get("display", len(news_items)),
            "rawDisplay": news_status.get("rawDisplay", news_status.get("display", len(news_items))),
            "filteredOut": news_status.get("filteredOut", 0),
            "items": news_items,
            "discovery": True,
        }

    focus = bounded_int(entry.get("focusWeight", 5), 0, 15)
    news_total = bounded_int(news_status.get("total", len(news_items)), 0, 10_000_000)
    seed_score = score_candidate(base)
    no_relevant_live_news = (
        news_status.get("source") == "naver"
        and not news_items
        and bounded_int(news_status.get("rawDisplay", 0), 0, 100) > 0
    )
    relevance_penalty = 16 if no_relevant_live_news else 0
    discovery_score = bounded_int(
        focus * 3
        + len(news_items) * 12
        + min(news_total, 50) * 0.25
        + min(seed_score, 90) * 0.18
        + (10 if symbol in watched else 0)
        - relevance_penalty,
        0,
        100,
    )
    base["candidateSource"] = "auto-discovery"
    base["discovery"] = {
        "source": news_status.get("source", "universe"),
        "query": news_status.get("query", universe_query(entry)),
        "score": discovery_score,
        "newsItems": len(news_items),
        "rawNewsItems": bounded_int(news_status.get("rawDisplay", 0), 0, 100),
        "filteredNewsItems": bounded_int(news_status.get("filteredOut", 0), 0, 100),
        "newsTotal": news_total,
        "focusWeight": focus,
        "quality": "matched-news" if news_items else ("filtered-news" if no_relevant_live_news else "universe"),
    }
    return base


def auto_candidate_cache_key(watched: set[str]) -> str:
    return json.dumps(
        {
            "enabled": SIGNAL_AUTO_CANDIDATES_ENABLED,
            "limit": SIGNAL_AUTO_CANDIDATE_LIMIT,
            "domesticLimit": SIGNAL_DOMESTIC_CANDIDATE_LIMIT,
            "overseasLimit": SIGNAL_OVERSEAS_CANDIDATE_LIMIT,
            "maxSymbols": SIGNAL_DISCOVERY_MAX_SYMBOLS,
            "display": SIGNAL_DISCOVERY_NEWS_DISPLAY,
            "qualityMinScore": SIGNAL_DISCOVERY_QUALITY_MIN_SCORE,
            "reserveMinScore": SIGNAL_DISCOVERY_RESERVE_MIN_SCORE,
            "symbols": SIGNAL_DISCOVERY_SYMBOLS,
            "watch": sorted(watched),
            "naverReady": NAVER_LIVE_NEWS and naver_news_config_status()["readyForNews"],
            "date": datetime.now(KST).date().isoformat(),
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def candidate_bucket(candidate: dict) -> str:
    category = str(candidate.get("category", "")).lower()
    market = str(candidate.get("market", "")).upper()
    symbol = str(candidate.get("symbol", ""))
    if category == "overseas" or market == "US" or re.fullmatch(r"[A-Z.\-]{1,8}", symbol):
        return "overseas"
    return "domestic"


def discovery_quality_profile(candidate: dict, watched: set[str]) -> dict:
    discovery = candidate.get("discovery", {}) if isinstance(candidate.get("discovery"), dict) else {}
    symbol = str(candidate.get("symbol", "")).strip().upper()
    score = bounded_int(discovery.get("score", 0), 0, 100)
    focus = bounded_int(discovery.get("focusWeight", 0), 0, 15)
    news_items = bounded_int(discovery.get("newsItems", 0), 0, 1_000)
    raw_news = bounded_int(discovery.get("rawNewsItems", 0), 0, 1_000)
    filtered = bounded_int(discovery.get("filteredNewsItems", 0), 0, 1_000)
    hidden = is_hidden_discovery_candidate(candidate)
    watched_hit = symbol in watched

    if watched_hit:
        tier, rank, reason = "primary", 0, "관심 종목이라 우선 검토"
    elif news_items > 0 and score >= max(35, SIGNAL_DISCOVERY_RESERVE_MIN_SCORE):
        tier, rank, reason = "primary", 0, "관련 뉴스가 확인된 후보"
    elif score >= SIGNAL_DISCOVERY_QUALITY_MIN_SCORE:
        tier, rank, reason = "primary", 0, "발굴 점수가 1차 기준을 통과"
    elif hidden and score >= SIGNAL_DISCOVERY_RESERVE_MIN_SCORE:
        tier, rank, reason = "reserve", 1, "숨은 후보이나 추가 확인 필요"
    elif focus >= 8 and filtered == 0 and score >= SIGNAL_DISCOVERY_RESERVE_MIN_SCORE:
        tier, rank, reason = "reserve", 1, "테마 가중치가 높아 보조 후보로 유지"
    elif filtered == 0 and focus >= 5 and score >= 28:
        tier, rank, reason = "reserve", 1, "유니버스 관심 종목으로 가격 반응 확인"
    elif raw_news and filtered and not news_items:
        tier, rank, reason = "rejected", 3, "검색 뉴스는 있었지만 종목 관련성이 낮음"
    else:
        tier, rank, reason = "rejected", 3, "뉴스·점수 기준 미달"

    return {
        "tier": tier,
        "rank": rank,
        "reason": reason,
        "score": score,
        "focusWeight": focus,
        "newsItems": news_items,
    }


def discovery_selection_sort_key(candidate: dict) -> tuple[int, int, int, int]:
    discovery = candidate.get("discovery", {}) if isinstance(candidate.get("discovery"), dict) else {}
    quality = discovery.get("qualityProfile", {}) if isinstance(discovery.get("qualityProfile"), dict) else {}
    return (
        -bounded_int(quality.get("rank", 9), 0, 9),
        bounded_int(quality.get("score", discovery.get("score", 0)), 0, 100),
        bounded_int(discovery.get("newsItems", 0), 0, 1_000),
        score_candidate(candidate),
    )


def prepare_quality_candidates(discovered: list[dict], watched: set[str]) -> tuple[list[dict], dict]:
    prepared = []
    counts = {"primary": 0, "reserve": 0, "rejected": 0}
    for candidate in discovered:
        item = dict(candidate)
        discovery = dict(item.get("discovery", {})) if isinstance(item.get("discovery"), dict) else {}
        profile = discovery_quality_profile(item, watched)
        discovery["qualityProfile"] = profile
        discovery["qualityTier"] = profile["tier"]
        discovery["qualityReason"] = profile["reason"]
        item["discovery"] = discovery
        counts[profile["tier"]] = counts.get(profile["tier"], 0) + 1
        prepared.append(item)
    prepared.sort(key=discovery_selection_sort_key, reverse=True)
    return prepared, counts


def balanced_candidate_selection(discovered: list[dict], watched: set[str]) -> tuple[list[dict], dict]:
    quality_candidates, quality_counts = prepare_quality_candidates(discovered, watched)
    selectable = [
        item
        for item in quality_candidates
        if item.get("discovery", {}).get("qualityTier") in {"primary", "reserve"}
    ]
    domestic = [item for item in selectable if candidate_bucket(item) == "domestic"]
    overseas = [item for item in selectable if candidate_bucket(item) == "overseas"]
    domestic_all = [item for item in quality_candidates if candidate_bucket(item) == "domestic"]
    overseas_all = [item for item in quality_candidates if candidate_bucket(item) == "overseas"]
    selected: list[dict] = []

    def add_from_bucket(bucket: list[dict], limit: int, tier: str | None = None) -> None:
        existing = {str(item.get("symbol", "")).upper() for item in selected}
        bucket_count = len([item for item in selected if candidate_bucket(item) == candidate_bucket(bucket[0])]) if bucket else 0
        for item in bucket:
            if bucket_count >= limit:
                break
            if tier and item.get("discovery", {}).get("qualityTier") != tier:
                continue
            symbol = str(item.get("symbol", "")).upper()
            if not symbol or symbol in existing:
                continue
            selected.append(item)
            existing.add(symbol)
            bucket_count += 1

    add_from_bucket(domestic, SIGNAL_DOMESTIC_CANDIDATE_LIMIT, "primary")
    add_from_bucket(overseas, SIGNAL_OVERSEAS_CANDIDATE_LIMIT, "primary")
    add_from_bucket(domestic, SIGNAL_DOMESTIC_CANDIDATE_LIMIT, "reserve")
    add_from_bucket(overseas, SIGNAL_OVERSEAS_CANDIDATE_LIMIT, "reserve")
    add_from_bucket(domestic_all, SIGNAL_DOMESTIC_CANDIDATE_LIMIT)
    add_from_bucket(overseas_all, SIGNAL_OVERSEAS_CANDIDATE_LIMIT)

    seen = {str(item.get("symbol", "")).upper() for item in selected}
    for item in selectable:
        if len(selected) >= SIGNAL_AUTO_CANDIDATE_LIMIT:
            break
        symbol = str(item.get("symbol", "")).upper()
        if symbol in seen:
            continue
        selected.append(item)
        seen.add(symbol)

    fallback_selected = 0
    if not selected and quality_candidates:
        selected = quality_candidates[: min(SIGNAL_AUTO_CANDIDATE_LIMIT, 6)]
        fallback_selected = len(selected)

    domestic_selected = sorted(
        [item for item in selected if candidate_bucket(item) == "domestic"],
        key=discovery_selection_sort_key,
        reverse=True,
    )[:SIGNAL_DOMESTIC_CANDIDATE_LIMIT]
    overseas_selected = sorted(
        [item for item in selected if candidate_bucket(item) == "overseas"],
        key=discovery_selection_sort_key,
        reverse=True,
    )[:SIGNAL_OVERSEAS_CANDIDATE_LIMIT]
    final_selected = [*domestic_selected, *overseas_selected]
    seen_final = {str(item.get("symbol", "")).upper() for item in final_selected}
    if len(final_selected) < SIGNAL_AUTO_CANDIDATE_LIMIT:
        for item in sorted(selected, key=discovery_selection_sort_key, reverse=True):
            if len(final_selected) >= SIGNAL_AUTO_CANDIDATE_LIMIT:
                break
            symbol = str(item.get("symbol", "")).upper()
            if symbol in seen_final:
                continue
            final_selected.append(item)
            seen_final.add(symbol)
    final_selected = sorted(final_selected[:SIGNAL_AUTO_CANDIDATE_LIMIT], key=discovery_selection_sort_key, reverse=True)
    selected_tiers = {
        "primary": len([item for item in final_selected if item.get("discovery", {}).get("qualityTier") == "primary"]),
        "reserve": len([item for item in final_selected if item.get("discovery", {}).get("qualityTier") == "reserve"]),
        "rejected": len([item for item in final_selected if item.get("discovery", {}).get("qualityTier") == "rejected"]),
    }
    domestic_selected_count = len([item for item in final_selected if candidate_bucket(item) == "domestic"])
    overseas_selected_count = len([item for item in final_selected if candidate_bucket(item) == "overseas"])
    return final_selected, {
        "domesticScanned": len([item for item in quality_candidates if candidate_bucket(item) == "domestic"]),
        "overseasScanned": len([item for item in quality_candidates if candidate_bucket(item) == "overseas"]),
        "qualityPrimaryCount": quality_counts.get("primary", 0),
        "qualityReserveCount": quality_counts.get("reserve", 0),
        "qualityRejectedCount": quality_counts.get("rejected", 0),
        "qualitySelectedPrimary": selected_tiers["primary"],
        "qualitySelectedReserve": selected_tiers["reserve"],
        "qualitySelectedFallback": selected_tiers["rejected"],
        "qualityFallbackCount": max(fallback_selected, selected_tiers["rejected"]),
        "qualityMinScore": SIGNAL_DISCOVERY_QUALITY_MIN_SCORE,
        "reserveMinScore": SIGNAL_DISCOVERY_RESERVE_MIN_SCORE,
        "targetCandidateCount": SIGNAL_DOMESTIC_CANDIDATE_LIMIT + SIGNAL_OVERSEAS_CANDIDATE_LIMIT,
        "domesticSelected": domestic_selected_count,
        "overseasSelected": overseas_selected_count,
        "domesticLimit": SIGNAL_DOMESTIC_CANDIDATE_LIMIT,
        "overseasLimit": SIGNAL_OVERSEAS_CANDIDATE_LIMIT,
        "domesticShortfall": max(0, SIGNAL_DOMESTIC_CANDIDATE_LIMIT - domestic_selected_count),
        "overseasShortfall": max(0, SIGNAL_OVERSEAS_CANDIDATE_LIMIT - overseas_selected_count),
    }


def initial_candidates(data: dict, watched: set[str]) -> tuple[list[dict], dict]:
    seed_candidates = data.get("candidates", [])
    if not SIGNAL_AUTO_CANDIDATES_ENABLED:
        return seed_candidates, {
            "source": "seed",
            "enabled": False,
            "message": "자동 후보 생성이 꺼져 있어 샘플 후보를 사용합니다.",
            "candidateCount": len(seed_candidates),
        }

    cache_key = auto_candidate_cache_key(watched)
    expires_at = DISCOVERY_CACHE.get("expires_at")
    if (
        DISCOVERY_CACHE.get("key") == cache_key
        and DISCOVERY_CACHE.get("payload") is not None
        and isinstance(expires_at, datetime)
        and expires_at > datetime.now(timezone.utc)
    ):
        cached = copy.deepcopy(DISCOVERY_CACHE["payload"])  # type: ignore[index]
        return cached["candidates"], cached["status"]

    entries = candidate_universe_entries()[: max(1, SIGNAL_DISCOVERY_MAX_SYMBOLS)]
    if not entries:
        return seed_candidates, {
            "source": "seed",
            "enabled": True,
            "message": "후보 유니버스가 없어 샘플 후보를 사용합니다.",
            "candidateCount": len(seed_candidates),
        }

    seed_lookup = seed_candidate_by_symbol()
    discovered = []
    errors = []
    for entry in entries:
        try:
            discovered.append(candidate_from_universe_entry(entry, seed_lookup, watched))
        except Exception as error:
            errors.append(str(error)[:160])

    discovered.sort(
        key=lambda item: (
            bounded_int(item.get("discovery", {}).get("score", 0)),
            score_candidate(item),
        ),
        reverse=True,
    )
    selected, balance_status = balanced_candidate_selection(discovered, watched) if discovered else (seed_candidates[:SIGNAL_AUTO_CANDIDATE_LIMIT], {})
    source = (
        "auto-news"
        if any(
            item.get("discovery", {}).get("source") == "naver"
            and bounded_int(item.get("discovery", {}).get("newsItems", 0), 0, 1_000) > 0
            for item in selected
        )
        else "auto-universe"
    )
    quality_selected = bounded_int(balance_status.get("qualitySelectedPrimary", 0), 0, 1_000) + bounded_int(
        balance_status.get("qualitySelectedReserve", 0),
        0,
        1_000,
    )
    status = {
        "source": source,
        "enabled": True,
        "message": (
            f"품질 기준을 통과한 후보 {quality_selected}개를 우선 선정했습니다."
            if quality_selected
            else ("뉴스와 유니버스 점수로 오늘 후보를 자동 생성했습니다." if source == "auto-news" else "유니버스 기본 점수로 오늘 후보를 구성했습니다.")
        ),
        "universeCount": len(entries),
        "scannedCount": len(discovered),
        "candidateCount": len(selected),
        **balance_status,
        "newsItemCount": sum(bounded_int(item.get("discovery", {}).get("newsItems", 0), 0, 1_000) for item in discovered),
        "selectedNewsItemCount": sum(bounded_int(item.get("discovery", {}).get("newsItems", 0), 0, 1_000) for item in selected),
        "filteredNewsCount": sum(bounded_int(item.get("discovery", {}).get("filteredNewsItems", 0), 0, 1_000) for item in discovered),
        "errorCount": len(errors),
        "errors": errors[:3],
        "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
    }
    DISCOVERY_CACHE["key"] = cache_key
    DISCOVERY_CACHE["payload"] = copy.deepcopy({"candidates": selected, "status": status})
    DISCOVERY_CACHE["expires_at"] = datetime.now(timezone.utc) + timedelta(seconds=SIGNAL_DISCOVERY_CACHE_SECONDS)
    return selected, status


def pipeline_step(stage: str, label: str, status: str, message: str = "", count: int | None = None) -> dict:
    step = {
        "stage": stage,
        "label": label,
        "status": status,
        "message": message,
        "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
    }
    if count is not None:
        step["count"] = count
    return step


def dashboard_status_defaults() -> dict:
    return {
        "toss_price": {
            "source": "sample",
            "enabled": TOSS_LIVE_PRICES,
            "message": "샘플 가격을 사용합니다.",
        },
        "toss_candle": {
            "source": "sample",
            "enabled": TOSS_LIVE_CANDLES,
            "message": "샘플 차트를 사용합니다.",
        },
        "toss_orderbook": {
            "source": "sample",
            "enabled": TOSS_LIVE_ORDERBOOK,
            "message": "샘플 호가 지표를 사용합니다.",
        },
        "toss_trades": {
            "source": "sample",
            "enabled": TOSS_LIVE_TRADES,
            "message": "샘플 체결 지표를 사용합니다.",
        },
        "dart_disclosure": {
            "source": "sample",
            "enabled": DART_LIVE_DISCLOSURES,
            "message": "샘플 공시 메모를 사용합니다.",
        },
        "naver_news": {
            "source": "sample",
            "enabled": NAVER_LIVE_NEWS,
            "message": "샘플 뉴스를 사용합니다.",
        },
        "gdelt_news": {
            "source": "sample",
            "enabled": GDELT_LIVE_NEWS,
            "message": "글로벌 뉴스 보강을 사용하지 않았습니다.",
        },
        "openai_analysis": {
            "source": "local",
            "enabled": OPENAI_ANALYSIS_ENABLED,
            "message": "로컬 분석을 사용합니다.",
        },
        "selection": {
            "source": "static",
            "enabled": True,
            "message": "기본 후보 점수를 사용합니다.",
        },
    }


def integration_failure_status(fallback: dict, error: Exception, message: str) -> dict:
    payload, _ = integration_error_payload(error)
    status = dict(fallback)
    status.update({
        "error": payload.get("error", "unknown"),
        "status": payload.get("status"),
        "detail": payload.get("detail", ""),
        "message": payload.get("message", message),
        "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
    })
    return status


def collect_signal_inputs(mode: str) -> dict:
    data = seed_data()
    market, index_status = enrich_market_with_indices(data.get("market", {}))
    market, fx_status = enrich_market_with_fx(market)
    watched = set(watchlist())
    raw_candidates, discovery_status = initial_candidates(data, watched)
    candidates = [decorate_candidate(item, watched) for item in raw_candidates]
    defaults = dashboard_status_defaults()
    return {
        "mode": mode,
        "data": data,
        "market": market,
        "watched": watched,
        "candidates": candidates,
        "statuses": {
            **defaults,
            "index": index_status,
            "fx": fx_status,
            "discovery": discovery_status,
        },
        "pipeline": [
            pipeline_step(
                "collector",
                "후보·시장 수집",
                "ok",
                discovery_status.get("message", "후보와 시장 데이터를 수집했습니다."),
                len(candidates),
            )
        ],
    }


def run_candidate_enricher(context: dict, key: str, label: str, enricher, failure_message: str) -> None:
    fallback = context["statuses"][key]
    try:
        context["candidates"], context["statuses"][key] = enricher(context["candidates"])
        status = "ok" if context["statuses"][key].get("source") not in {"sample", "disabled"} else "fallback"
        message = context["statuses"][key].get("message", f"{label} 완료")
    except Exception as error:
        context["statuses"][key] = integration_failure_status(fallback, error, failure_message)
        status = "fallback"
        message = context["statuses"][key].get("message", failure_message)
    context["pipeline"].append(pipeline_step("analyzer", label, status, message, len(context["candidates"])))


def analyze_signal_context(context: dict) -> dict:
    run_candidate_enricher(
        context,
        "toss_price",
        "현재가 수집",
        enrich_candidates_with_toss_prices,
        "토스 현재가 반영에 실패해 샘플 가격을 사용합니다.",
    )
    run_candidate_enricher(
        context,
        "toss_candle",
        "차트 수집",
        enrich_candidates_with_toss_candles,
        "토스 캔들 반영에 실패해 샘플 차트를 사용합니다.",
    )
    run_candidate_enricher(
        context,
        "toss_orderbook",
        "호가 수집",
        enrich_candidates_with_toss_orderbook,
        "토스 호가 반영에 실패해 샘플 호가 지표를 사용합니다.",
    )
    run_candidate_enricher(
        context,
        "toss_trades",
        "체결 수집",
        enrich_candidates_with_toss_trades,
        "토스 체결 반영에 실패해 샘플 체결 지표를 사용합니다.",
    )
    run_candidate_enricher(
        context,
        "dart_disclosure",
        "공시 수집",
        enrich_candidates_with_dart_disclosures,
        "OpenDART 공시 반영에 실패해 샘플 공시 메모를 사용합니다.",
    )
    run_candidate_enricher(
        context,
        "naver_news",
        "국내 뉴스 수집",
        enrich_candidates_with_naver_news,
        "네이버 뉴스 반영에 실패해 샘플 뉴스를 사용합니다.",
    )
    run_candidate_enricher(
        context,
        "gdelt_news",
        "글로벌 뉴스 수집",
        enrich_candidates_with_gdelt_news,
        "GDELT 글로벌 뉴스 반영에 실패해 샘플 뉴스를 사용합니다.",
    )
    return context


def score_signal_context(context: dict) -> dict:
    context["candidates"], context["statuses"]["selection"] = apply_candidate_selection(
        context["candidates"],
        context["market"],
        context["watched"],
    )
    context["pipeline"].append(
        pipeline_step(
            "scorer",
            "후보 점수 재계산",
            "ok",
            context["statuses"]["selection"].get("message", "후보 점수를 재계산했습니다."),
            len(context["candidates"]),
        )
    )
    return context


def sort_candidates_for_mode(candidates: list[dict], mode: str) -> list[dict]:
    def group_rank(item: dict) -> int:
        group = item.get("decisionGroup", {}) if isinstance(item, dict) else {}
        priority = bounded_int(group.get("priority", 9), 0, 9) if isinstance(group, dict) else 9
        return 100 - priority

    def decision_score(item: dict) -> int:
        group = item.get("decisionGroup", {}) if isinstance(item, dict) else {}
        return bounded_int(group.get("score", 0), 0, 100) if isinstance(group, dict) else 0

    if mode == "preopen":
        candidates.sort(key=lambda item: (group_rank(item), item["preopenPriority"], decision_score(item), item["totalScore"]), reverse=True)
    elif mode == "intraday":
        candidates.sort(key=lambda item: (group_rank(item), item["triggerReadiness"], decision_score(item), item["totalScore"]), reverse=True)
    else:
        candidates.sort(key=lambda item: (group_rank(item), item["totalScore"], decision_score(item)), reverse=True)
    return candidates


def select_signal_context(context: dict) -> dict:
    context["candidates"] = sort_candidates_for_mode(context["candidates"], context["mode"])
    try:
        context["candidates"], context["statuses"]["openai_analysis"] = enrich_candidates_with_openai_analysis(context["candidates"])
        analysis_status = "ok" if context["statuses"]["openai_analysis"].get("source") == "openai" else "fallback"
        message = context["statuses"]["openai_analysis"].get("message", "분석 문장을 생성했습니다.")
    except Exception as error:
        context["statuses"]["openai_analysis"] = integration_failure_status(
            context["statuses"]["openai_analysis"],
            error,
            "OpenAI 분석에 실패해 로컬 분석을 사용합니다.",
        )
        context["candidates"] = [
            apply_analysis_to_candidate(candidate, local_candidate_analysis(candidate))
            for candidate in context["candidates"]
        ]
        analysis_status = "fallback"
        message = context["statuses"]["openai_analysis"].get("message", "OpenAI 분석에 실패해 로컬 분석을 사용합니다.")

    context["selected"] = context["candidates"][0] if context["candidates"] else None
    context["pipeline"].append(pipeline_step("selector", "후보 정렬·대표 선정", analysis_status, message, len(context["candidates"])))
    return context


def build_dashboard_payload(context: dict) -> dict:
    candidates = context["candidates"]
    discovery_status = context["statuses"]["discovery"]
    selection_status = context["statuses"]["selection"]
    return {
        "generatedAt": datetime.now(KST).isoformat(timespec="seconds"),
        "mode": context["mode"],
        "market": context["market"],
        "principles": context["data"].get("principles", []),
        "summary": {
            "candidateCount": len(candidates),
            "watchedCount": len([item for item in candidates if item["isWatched"]]),
            "highScoreCount": len([item for item in candidates if item["totalScore"] >= 75]),
            "readyCount": len([item for item in candidates if item["triggerReadiness"] >= 70]),
            "selectionSource": selection_status.get("source"),
            "candidateSource": discovery_status.get("source"),
            "universeCount": discovery_status.get("universeCount"),
            "scannedCount": discovery_status.get("scannedCount"),
            "domesticSelected": discovery_status.get("domesticSelected"),
            "overseasSelected": discovery_status.get("overseasSelected"),
            "domesticLimit": discovery_status.get("domesticLimit"),
            "overseasLimit": discovery_status.get("overseasLimit"),
            "qualityPrimaryCount": discovery_status.get("qualityPrimaryCount"),
            "qualityReserveCount": discovery_status.get("qualityReserveCount"),
            "qualityRejectedCount": discovery_status.get("qualityRejectedCount"),
            "qualitySelectedPrimary": discovery_status.get("qualitySelectedPrimary"),
            "qualitySelectedReserve": discovery_status.get("qualitySelectedReserve"),
            "qualitySelectedFallback": discovery_status.get("qualitySelectedFallback"),
            "qualityFallbackCount": discovery_status.get("qualityFallbackCount"),
            "targetCandidateCount": discovery_status.get("targetCandidateCount"),
            "domesticShortfall": discovery_status.get("domesticShortfall"),
            "overseasShortfall": discovery_status.get("overseasShortfall"),
            "discoveryNewsCount": discovery_status.get("newsItemCount"),
            "filteredNewsCount": discovery_status.get("filteredNewsCount"),
            "averageScoreShift": selection_status.get("averageScoreShift"),
            "averageOpportunityScore": selection_status.get("averageOpportunityScore"),
            "averageDataConfidence": selection_status.get("averageDataConfidence"),
            "hiddenOpportunityCount": selection_status.get("hiddenOpportunityCount"),
            "decisionGroups": selection_status.get("decisionGroups", {}),
            "qualityGateCounts": selection_status.get("qualityGateCounts", {}),
            "investableCandidateCount": selection_status.get("investableCandidateCount"),
            "watchCandidateCount": selection_status.get("watchCandidateCount"),
            "deferCandidateCount": selection_status.get("deferCandidateCount"),
            "actionCandidateCount": selection_status.get("actionCandidateCount"),
            "momentumCandidateCount": selection_status.get("momentumCandidateCount"),
            "waitCandidateCount": selection_status.get("waitCandidateCount"),
            "excludeCandidateCount": selection_status.get("excludeCandidateCount"),
        },
        "integrations": {
            "pipeline": context["pipeline"],
            "discovery": discovery_status,
            "selection": selection_status,
            "toss": {
                "config": toss_config_status(),
                "prices": context["statuses"]["toss_price"],
                "candles": context["statuses"]["toss_candle"],
                "orderbook": context["statuses"]["toss_orderbook"],
                "trades": context["statuses"]["toss_trades"],
            },
            "market": {
                "config": market_config_status(),
                "indices": context["statuses"]["index"],
                "fx": context["statuses"]["fx"],
            },
            "dart": {
                "config": dart_config_status(),
                "disclosures": context["statuses"]["dart_disclosure"],
            },
            "news": {
                "naver": {
                    "config": naver_news_config_status(),
                    "items": context["statuses"]["naver_news"],
                },
                "gdelt": {
                    "config": gdelt_news_config_status(),
                    "items": context["statuses"]["gdelt_news"],
                },
            },
            "openai": {
                "config": openai_config_status(),
                "analysis": context["statuses"]["openai_analysis"],
            },
        },
        "candidates": candidates,
        "selected": context.get("selected"),
    }


def dashboard(mode: str) -> dict:
    context = collect_signal_inputs(mode)
    context = analyze_signal_context(context)
    context = score_signal_context(context)
    context = select_signal_context(context)
    return build_dashboard_payload(context)


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


def scheduled_datetime(job: dict, run_date) -> datetime | None:
    scheduled_minutes = minutes_from_hhmm(str(job.get("time", "")))
    if scheduled_minutes is None:
        return None
    return datetime.combine(run_date, datetime.min.time(), tzinfo=KST) + timedelta(minutes=scheduled_minutes)


def next_scheduler_run(now: datetime | None = None) -> dict:
    now = now or datetime.now(KST)
    candidates = []
    for job in scheduler_jobs():
        mode = str(job.get("mode", ""))
        run_at = scheduled_datetime(job, now.date())
        if run_at is None:
            continue
        window_minutes = bounded_int(job.get("windowMinutes", 0), 0, 24 * 60)
        window_end = run_at + timedelta(minutes=window_minutes)
        already_ran_today = scheduled_snapshot_exists(now.date().isoformat(), mode)
        if already_ran_today or now > window_end:
            run_at = scheduled_datetime(job, now.date() + timedelta(days=1))
            already_ran_today = False
        if run_at is None:
            continue
        due_seconds = max(0, int((run_at - now).total_seconds()))
        status = "ready-now" if SIGNAL_SCHEDULER_ENABLED and due_seconds == 0 and not already_ran_today else "waiting"
        candidates.append({
            "mode": mode,
            "label": job.get("label", ""),
            "time": job.get("time", ""),
            "runAt": run_at.isoformat(timespec="seconds"),
            "dueInMinutes": due_seconds // 60,
            "windowMinutes": window_minutes,
            "status": status,
        })
    candidates.sort(key=lambda item: item["runAt"])
    return candidates[0] if candidates else {}


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
            "gate": item.get("qualityGate", {}).get("label", "") if isinstance(item.get("qualityGate"), dict) else "",
            "confidence": item.get("dataConfidence", {}).get("score") if isinstance(item.get("dataConfidence"), dict) else None,
        })
    summary = payload.get("summary", {})
    if not isinstance(summary, dict):
        summary = {}
    integrations = payload.get("integrations", {})
    if not isinstance(integrations, dict):
        integrations = {}
    pipeline = integrations.get("pipeline", [])
    if not isinstance(pipeline, list):
        pipeline = []
    return {
        "mode": payload.get("mode"),
        "generatedAt": payload.get("generatedAt"),
        "candidateCount": summary.get("candidateCount", len(candidates)),
        "highScoreCount": summary.get("highScoreCount", 0),
        "readyCount": summary.get("readyCount", 0),
        "averageScoreShift": summary.get("averageScoreShift"),
        "averageDataConfidence": summary.get("averageDataConfidence"),
        "qualityGateCounts": summary.get("qualityGateCounts", {}),
        "investableCandidateCount": summary.get("investableCandidateCount"),
        "watchCandidateCount": summary.get("watchCandidateCount"),
        "deferCandidateCount": summary.get("deferCandidateCount"),
        "topCandidates": top_candidates,
        "pipeline": [
            {
                "stage": step.get("stage", ""),
                "label": step.get("label", ""),
                "status": step.get("status", ""),
                "count": step.get("count"),
            }
            for step in pipeline
            if isinstance(step, dict)
        ],
    }


def discovery_bot_mode(mode: str | None = None) -> str:
    normalized = str(mode or SIGNAL_DISCOVERY_BOT_MODE or "intraday").strip().lower()
    return normalized if normalized in {"close", "preopen", "intraday"} else "intraday"


def discovery_bot_config_status() -> dict:
    return {
        "enabled": SIGNAL_DISCOVERY_BOT_ENABLED,
        "intervalSeconds": SIGNAL_DISCOVERY_BOT_INTERVAL_SECONDS,
        "mode": discovery_bot_mode(),
        "latestFile": display_local_path(DISCOVERY_LATEST_FILE),
    }


def discovery_latest_record(include_dashboard: bool = False) -> dict:
    record = read_json(DISCOVERY_LATEST_FILE, {})
    if not isinstance(record, dict):
        return {}
    if include_dashboard:
        return record
    return {key: value for key, value in record.items() if key != "dashboard"}


def discovery_bot_status() -> dict:
    with DISCOVERY_BOT_LOCK:
        state = {
            "started": bool(DISCOVERY_BOT_STATE.get("started")),
            "running": bool(DISCOVERY_BOT_STATE.get("running")),
            "lastError": DISCOVERY_BOT_STATE.get("lastError", ""),
            "lastCheckedAt": DISCOVERY_BOT_STATE.get("lastCheckedAt", ""),
            "lastRun": DISCOVERY_BOT_STATE.get("lastRun") or discovery_latest_record(False),
        }
    return {
        "config": discovery_bot_config_status(),
        "state": state,
        "latest": discovery_latest_record(False),
    }


def run_discovery_bot_cycle(mode: str | None = None, trigger: str = "manual") -> dict:
    selected_mode = discovery_bot_mode(mode)
    with DISCOVERY_BOT_LOCK:
        if DISCOVERY_BOT_STATE.get("running"):
            latest = discovery_latest_record(False)
            return {
                "ok": False,
                "skipped": True,
                "message": "발굴 봇이 이미 실행 중입니다.",
                "latest": latest,
            }
        DISCOVERY_BOT_STATE["running"] = True
        DISCOVERY_BOT_STATE["lastCheckedAt"] = datetime.now(KST).isoformat(timespec="seconds")

    try:
        now = datetime.now(KST)
        payload = dashboard(selected_mode)
        run_id = f"{now.strftime('%Y%m%d-%H%M%S')}-{selected_mode}-discovery-{trigger}"
        record = {
            "id": run_id,
            "mode": selected_mode,
            "trigger": trigger,
            "createdAt": now.isoformat(timespec="seconds"),
            "summary": dashboard_summary(payload),
            "dashboard": payload,
        }
        write_json(DISCOVERY_LATEST_FILE, record)
        public_record = {key: value for key, value in record.items() if key != "dashboard"}
        with DISCOVERY_BOT_LOCK:
            DISCOVERY_BOT_STATE["lastRun"] = public_record
            DISCOVERY_BOT_STATE["lastError"] = ""
        return record
    except Exception as error:
        with DISCOVERY_BOT_LOCK:
            DISCOVERY_BOT_STATE["lastError"] = str(error)[:240]
        raise
    finally:
        with DISCOVERY_BOT_LOCK:
            DISCOVERY_BOT_STATE["running"] = False


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


def snapshot_storage_status() -> dict:
    writable = False
    error = ""
    check_path = RUNS_DIR / ".storage-check.tmp"
    try:
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        check_path.write_text(datetime.now(KST).isoformat(timespec="seconds"), encoding="utf-8")
        check_path.unlink(missing_ok=True)
        writable = True
    except OSError as storage_error:
        error = str(storage_error)

    recent_runs = recent_scheduler_runs()
    persistent = SNAPSHOT_STORAGE_MODE not in {"", "filesystem", "local", "ephemeral"}
    return {
        "mode": SNAPSHOT_STORAGE_MODE,
        "implementation": "filesystem",
        "runsDir": display_local_path(RUNS_DIR),
        "runsDirExists": RUNS_DIR.exists(),
        "writable": writable,
        "persistent": persistent,
        "recentRunCount": len(recent_runs),
        "latestRunId": recent_runs[0]["id"] if recent_runs else "",
        "latestRunCreatedAt": recent_runs[0]["createdAt"] if recent_runs else "",
        "message": (
            "영구 저장소로 표시되어 있습니다."
            if persistent
            else "현재 스냅샷은 파일 저장소에 남습니다. 운영 전에는 영구 저장소를 검토하세요."
        ),
        "error": error,
    }


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
        "nextRun": next_scheduler_run(),
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


def discovery_bot_loop() -> None:
    with DISCOVERY_BOT_LOCK:
        DISCOVERY_BOT_STATE["started"] = True
    while True:
        now = datetime.now(KST)
        with DISCOVERY_BOT_LOCK:
            DISCOVERY_BOT_STATE["lastCheckedAt"] = now.isoformat(timespec="seconds")
        if SIGNAL_DISCOVERY_BOT_ENABLED:
            try:
                run_discovery_bot_cycle(discovery_bot_mode(), trigger="bot")
            except Exception as error:
                with DISCOVERY_BOT_LOCK:
                    DISCOVERY_BOT_STATE["lastError"] = str(error)[:240]
        time.sleep(max(60, SIGNAL_DISCOVERY_BOT_INTERVAL_SECONDS))


def start_discovery_bot_thread() -> None:
    thread = threading.Thread(target=discovery_bot_loop, name="market-signal-discovery-bot", daemon=True)
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

        if parsed.path == "/api/portfolio/status":
            try:
                self.send_json(portfolio_status())
            except Exception as error:
                payload, status = integration_error_payload(error)
                self.send_json(payload, status)
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

        if parsed.path == "/api/stocks/search":
            query = parse_qs(parsed.query)
            search_query = query.get("query", [""])[0].strip()
            limit = int(query.get("limit", ["8"])[0])
            try:
                self.send_json(stock_search(search_query, limit=limit))
            except Exception as error:
                payload, status = integration_error_payload(error)
                self.send_json(payload, status)
            return

        if parsed.path == "/api/stocks/analyze":
            query = parse_qs(parsed.query)
            symbol = query.get("symbol", [""])[0].strip()
            try:
                self.send_json(analyze_stock_lookup(symbol))
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

        if parsed.path == "/api/discovery/status":
            self.send_json(discovery_bot_status())
            return

        if parsed.path == "/api/discovery/latest":
            query = parse_qs(parsed.query)
            include_dashboard = query.get("includeDashboard", ["0"])[0].lower() in {"1", "true", "yes", "on"}
            latest = discovery_latest_record(include_dashboard)
            if not latest:
                self.send_json({"error": "not-found", "message": "아직 저장된 발굴 결과가 없습니다."}, 404)
                return
            self.send_json(latest)
            return

        if parsed.path == "/api/storage/status":
            self.send_json(snapshot_storage_status())
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

        if parsed.path == "/api/discovery/run":
            body = self.read_body()
            mode = str(body.get("mode", SIGNAL_DISCOVERY_BOT_MODE)).strip()
            try:
                record = run_discovery_bot_cycle(mode, trigger="manual")
                self.send_json({"ok": True, "latest": {key: value for key, value in record.items() if key != "dashboard"}, "status": discovery_bot_status()})
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
    start_discovery_bot_thread()
    display_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
    print(f"Market Signal Desk is running at http://{display_host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
