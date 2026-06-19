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
import importlib
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
try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover - Windows runtimes can miss tzdata.
    ZoneInfo = None


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
SEED_FILE = DATA_DIR / "seed.json"
UNIVERSE_FILE = DATA_DIR / "candidate-universe.json"
STOCK_SEARCH_MASTER_FILE = DATA_DIR / "stock-search-master.json"
STOCK_SEARCH_GENERATED_FILE = DATA_DIR / "stock-search-generated.json"
WATCHLIST_FILE = DATA_DIR / "watchlist.json"
DART_CORP_CODE_FILE = DATA_DIR / "dart-corp-codes.json"
RUNS_DIR = DATA_DIR / "runs"
DISCOVERY_LATEST_FILE = DATA_DIR / "discovery-latest.json"
CANDIDATE_POOL_FILE = DATA_DIR / "candidate-pool.json"
DASHBOARD_CACHE_FILE = DATA_DIR / "dashboard-cache.json"
RAW_EVENTS_FILE = DATA_DIR / "raw-events.json"
MARKET_DATA_LATEST_FILE = DATA_DIR / "market-data-latest.json"
LIVE_STATE_FILE = DATA_DIR / "live-state.json"
CANDIDATE_DATA_FILE = DATA_DIR / "candidate-data-snapshots.json"
SNAPSHOT_STORAGE_MODE = os.getenv("SNAPSHOT_STORAGE_MODE", "filesystem").strip().lower() or "filesystem"
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
SIGNAL_STORAGE_BACKEND = os.getenv("SIGNAL_STORAGE_BACKEND", "auto").strip().lower() or "auto"
SIGNAL_DB_AUTO_MIGRATE = os.getenv("SIGNAL_DB_AUTO_MIGRATE", "1").lower() not in {"0", "false", "no", "off"}
SIGNAL_DB_MIGRATE_RUN_LIMIT = int(os.getenv("SIGNAL_DB_MIGRATE_RUN_LIMIT", "200"))
SIGNAL_RAW_EVENT_STORAGE_ENABLED = os.getenv("SIGNAL_RAW_EVENT_STORAGE_ENABLED", "1").lower() not in {"0", "false", "no", "off"}
SIGNAL_RAW_EVENT_FILE_LIMIT = int(os.getenv("SIGNAL_RAW_EVENT_FILE_LIMIT", "500"))
SIGNAL_RAW_EVENT_PAYLOAD_LIMIT = int(os.getenv("SIGNAL_RAW_EVENT_PAYLOAD_LIMIT", "40"))
SIGNAL_MARKET_DATA_LATEST_ENABLED = os.getenv("SIGNAL_MARKET_DATA_LATEST_ENABLED", "1").lower() not in {"0", "false", "no", "off"}
SIGNAL_MARKET_DATA_LATEST_MAX_ITEMS = int(os.getenv("SIGNAL_MARKET_DATA_LATEST_MAX_ITEMS", "2000"))
MARKET_DATA_LATEST_KV_KEY = "market_data_latest"
SIGNAL_STOCK_SEARCH_MASTER_AUTO_REFRESH = os.getenv("SIGNAL_STOCK_SEARCH_MASTER_AUTO_REFRESH", "1").lower() not in {"0", "false", "no", "off"}
SIGNAL_STOCK_SEARCH_MASTER_REFRESH_SECONDS = int(os.getenv("SIGNAL_STOCK_SEARCH_MASTER_REFRESH_SECONDS", "86400"))
STOCK_SEARCH_MASTER_KV_KEY = "stock_search_master"
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
TOSS_PRICE_CACHE_SECONDS = int(os.getenv("TOSS_PRICE_CACHE_SECONDS", "5"))
TOSS_CANDLE_CACHE_SECONDS = int(os.getenv("TOSS_CANDLE_CACHE_SECONDS", "60"))
TOSS_ORDERBOOK_CACHE_SECONDS = int(os.getenv("TOSS_ORDERBOOK_CACHE_SECONDS", "5"))
TOSS_TRADES_CACHE_SECONDS = int(os.getenv("TOSS_TRADES_CACHE_SECONDS", "5"))
TOSS_PORTFOLIO_CACHE_SECONDS = int(os.getenv("TOSS_PORTFOLIO_CACHE_SECONDS", "30"))
TOSS_STOCK_CACHE_SECONDS = int(os.getenv("TOSS_STOCK_CACHE_SECONDS", "86400"))
TOSS_REQUEST_TIMEOUT_SECONDS = int(os.getenv("TOSS_REQUEST_TIMEOUT_SECONDS", "5"))
TOSS_PRICE_BATCH_SIZE = max(1, int(os.getenv("TOSS_PRICE_BATCH_SIZE", "20")))
TOSS_CANDLE_MAX_CANDIDATES = int(os.getenv("TOSS_CANDLE_MAX_CANDIDATES", "5"))
TOSS_ORDERBOOK_MAX_CANDIDATES = int(os.getenv("TOSS_ORDERBOOK_MAX_CANDIDATES", "5"))
TOSS_TRADES_MAX_CANDIDATES = int(os.getenv("TOSS_TRADES_MAX_CANDIDATES", "5"))
TOSS_TRADES_COUNT = int(os.getenv("TOSS_TRADES_COUNT", "30"))
TOSS_CANDLE_MAX_STALENESS_DAYS = int(os.getenv("TOSS_CANDLE_MAX_STALENESS_DAYS", "7"))
SIGNAL_LIVE_PRICE_POLL_SECONDS = int(os.getenv("SIGNAL_LIVE_PRICE_POLL_SECONDS", "10"))
SIGNAL_LIVE_PRICE_FRESH_SECONDS = int(os.getenv("SIGNAL_LIVE_PRICE_FRESH_SECONDS", str(max(30, SIGNAL_LIVE_PRICE_POLL_SECONDS * 3))))
SIGNAL_LIVE_PRICE_DELAYED_SECONDS = int(os.getenv("SIGNAL_LIVE_PRICE_DELAYED_SECONDS", str(max(120, SIGNAL_LIVE_PRICE_POLL_SECONDS * 12))))
SIGNAL_CLOSED_MARKET_BASELINE_MAX_AGE_SECONDS = int(os.getenv("SIGNAL_CLOSED_MARKET_BASELINE_MAX_AGE_SECONDS", str(60 * 60 * 24 * 7)))
SIGNAL_LIVE_PRICE_SYMBOL_LIMIT = int(os.getenv("SIGNAL_LIVE_PRICE_SYMBOL_LIMIT", "80"))
SIGNAL_LIVE_STATE_STORAGE_ENABLED = os.getenv("SIGNAL_LIVE_STATE_STORAGE_ENABLED", "1").lower() not in {"0", "false", "no", "off"}
SIGNAL_LIVE_STATE_RETAIN_SECONDS = int(os.getenv("SIGNAL_LIVE_STATE_RETAIN_SECONDS", str(max(180, SIGNAL_LIVE_PRICE_POLL_SECONDS * 18))))
SIGNAL_LIVE_STATE_MAX_ITEMS = int(os.getenv("SIGNAL_LIVE_STATE_MAX_ITEMS", "240"))
LIVE_STATE_KV_KEY = "live_price_state"
SIGNAL_CANDIDATE_DATA_STORAGE_ENABLED = os.getenv("SIGNAL_CANDIDATE_DATA_STORAGE_ENABLED", "1").lower() not in {"0", "false", "no", "off"}
SIGNAL_CANDIDATE_DATA_MAX_ITEMS = int(os.getenv("SIGNAL_CANDIDATE_DATA_MAX_ITEMS", "1000"))
SIGNAL_CANDIDATE_DATA_HISTORY_LIMIT = int(os.getenv("SIGNAL_CANDIDATE_DATA_HISTORY_LIMIT", "30"))
SIGNAL_FINAL_DECISION_STABILITY_ENABLED = os.getenv("SIGNAL_FINAL_DECISION_STABILITY_ENABLED", "1").lower() not in {"0", "false", "no", "off"}
SIGNAL_FINAL_DECISION_STABILITY_SECONDS = int(os.getenv("SIGNAL_FINAL_DECISION_STABILITY_SECONDS", str(max(120, SIGNAL_LIVE_PRICE_POLL_SECONDS * 12))))
CANDIDATE_DATA_KV_KEY = "candidate_data_snapshots"
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
SIGNAL_DASHBOARD_STORED_DISCOVERY_FIRST = os.getenv("SIGNAL_DASHBOARD_STORED_DISCOVERY_FIRST", "1").lower() not in {"0", "false", "no", "off"}
SIGNAL_CLOSE_RUN_TIME = os.getenv("SIGNAL_CLOSE_RUN_TIME", "16:40")
SIGNAL_CLOSE_RUN_WINDOW_MINUTES = int(os.getenv("SIGNAL_CLOSE_RUN_WINDOW_MINUTES", "360"))
SIGNAL_PREOPEN_RUN_TIME = os.getenv("SIGNAL_PREOPEN_RUN_TIME", "08:40")
SIGNAL_PREOPEN_RUN_WINDOW_MINUTES = int(os.getenv("SIGNAL_PREOPEN_RUN_WINDOW_MINUTES", "80"))
SIGNAL_RUN_HISTORY_LIMIT = int(os.getenv("SIGNAL_RUN_HISTORY_LIMIT", "12"))
SIGNAL_PERFORMANCE_RUN_LIMIT = int(os.getenv("SIGNAL_PERFORMANCE_RUN_LIMIT", "12"))
SIGNAL_PERFORMANCE_TOP_CANDIDATES = int(os.getenv("SIGNAL_PERFORMANCE_TOP_CANDIDATES", "3"))
SIGNAL_PERFORMANCE_AUTO_UPDATE = os.getenv("SIGNAL_PERFORMANCE_AUTO_UPDATE", "1").lower() not in {"0", "false", "no", "off"}
SIGNAL_PERFORMANCE_MIN_AGE_MINUTES = int(os.getenv("SIGNAL_PERFORMANCE_MIN_AGE_MINUTES", "60"))
SIGNAL_AUTO_CANDIDATES_ENABLED = os.getenv("SIGNAL_AUTO_CANDIDATES_ENABLED", "1").lower() not in {"0", "false", "no", "off"}
SIGNAL_DOMESTIC_CANDIDATE_LIMIT = int(os.getenv("SIGNAL_DOMESTIC_CANDIDATE_LIMIT", "10"))
SIGNAL_OVERSEAS_CANDIDATE_LIMIT = int(os.getenv("SIGNAL_OVERSEAS_CANDIDATE_LIMIT", "10"))
SIGNAL_AUTO_CANDIDATE_LIMIT = max(
    int(os.getenv("SIGNAL_AUTO_CANDIDATE_LIMIT", "20")),
    SIGNAL_DOMESTIC_CANDIDATE_LIMIT + SIGNAL_OVERSEAS_CANDIDATE_LIMIT,
)
SIGNAL_DISCOVERY_SELECTION_LIMIT = max(
    int(os.getenv("SIGNAL_DISCOVERY_SELECTION_LIMIT", "80")),
    SIGNAL_AUTO_CANDIDATE_LIMIT,
)
SIGNAL_DISCOVERY_MAX_SYMBOLS = max(
    int(os.getenv("SIGNAL_DISCOVERY_MAX_SYMBOLS", "160")),
    SIGNAL_DISCOVERY_SELECTION_LIMIT,
    SIGNAL_DOMESTIC_CANDIDATE_LIMIT + SIGNAL_OVERSEAS_CANDIDATE_LIMIT + 80,
)
SIGNAL_DISCOVERY_NEWS_DISPLAY = int(os.getenv("SIGNAL_DISCOVERY_NEWS_DISPLAY", "3"))
SIGNAL_DISCOVERY_CACHE_SECONDS = int(os.getenv("SIGNAL_DISCOVERY_CACHE_SECONDS", "600"))
SIGNAL_DISCOVERY_SYMBOLS = os.getenv("SIGNAL_DISCOVERY_SYMBOLS", "").strip()
SIGNAL_DISCOVERY_SCAN_ROTATION_ENABLED = os.getenv("SIGNAL_DISCOVERY_SCAN_ROTATION_ENABLED", "1").lower() not in {"0", "false", "no", "off"}
SIGNAL_DISCOVERY_QUALITY_MIN_SCORE = int(os.getenv("SIGNAL_DISCOVERY_QUALITY_MIN_SCORE", "55"))
SIGNAL_DISCOVERY_RESERVE_MIN_SCORE = int(os.getenv("SIGNAL_DISCOVERY_RESERVE_MIN_SCORE", "42"))
SIGNAL_DISCOVERY_STRONG_EVIDENCE_SCORE = int(os.getenv("SIGNAL_DISCOVERY_STRONG_EVIDENCE_SCORE", "68"))
SIGNAL_DISCOVERY_QUALIFIED_EVIDENCE_SCORE = int(os.getenv("SIGNAL_DISCOVERY_QUALIFIED_EVIDENCE_SCORE", "52"))
SIGNAL_CANDIDATE_POOL_ENABLED = os.getenv("SIGNAL_CANDIDATE_POOL_ENABLED", "1").lower() not in {"0", "false", "no", "off"}
SIGNAL_CANDIDATE_POOL_MAX_ITEMS = int(os.getenv("SIGNAL_CANDIDATE_POOL_MAX_ITEMS", "500"))
SIGNAL_CANDIDATE_POOL_TTL_DAYS = int(os.getenv("SIGNAL_CANDIDATE_POOL_TTL_DAYS", "14"))
SIGNAL_CANDIDATE_POOL_DEMOTION_CONFIRMATIONS = int(os.getenv("SIGNAL_CANDIDATE_POOL_DEMOTION_CONFIRMATIONS", "2"))
SIGNAL_CANDIDATE_POOL_RETAIN_LIMIT = int(os.getenv("SIGNAL_CANDIDATE_POOL_RETAIN_LIMIT", "40"))
SIGNAL_CANDIDATE_POOL_SCAN_LIMIT = int(os.getenv("SIGNAL_CANDIDATE_POOL_SCAN_LIMIT", "200"))
SIGNAL_CANDIDATE_POOL_RETAIN_MIN_SCORE = int(os.getenv("SIGNAL_CANDIDATE_POOL_RETAIN_MIN_SCORE", "58"))
SIGNAL_CANDIDATE_POOL_TOP_LIMIT = int(os.getenv("SIGNAL_CANDIDATE_POOL_TOP_LIMIT", "5"))
SIGNAL_CANDIDATE_PREFETCH_ENABLED = os.getenv("SIGNAL_CANDIDATE_PREFETCH_ENABLED", "1").lower() not in {"0", "false", "no", "off"}
SIGNAL_CANDIDATE_PREFETCH_LIMIT = max(1, int(os.getenv("SIGNAL_CANDIDATE_PREFETCH_LIMIT", "80")))
SIGNAL_CANDIDATE_PREFETCH_INTERVAL_SECONDS = max(
    30,
    int(os.getenv("SIGNAL_CANDIDATE_PREFETCH_INTERVAL_SECONDS", "60")),
)
_SIGNAL_PERFORMANCE_SUCCESS_THRESHOLD_PERCENT = os.getenv("SIGNAL_PERFORMANCE_SUCCESS_THRESHOLD_PERCENT", "1")
try:
    SIGNAL_PERFORMANCE_SUCCESS_THRESHOLD_PERCENT = Decimal(_SIGNAL_PERFORMANCE_SUCCESS_THRESHOLD_PERCENT)
except InvalidOperation:
    SIGNAL_PERFORMANCE_SUCCESS_THRESHOLD_PERCENT = Decimal("1")
_SIGNAL_PERFORMANCE_OUTLIER_PERCENT = os.getenv("SIGNAL_PERFORMANCE_OUTLIER_PERCENT", "25")
try:
    SIGNAL_PERFORMANCE_OUTLIER_PERCENT = Decimal(_SIGNAL_PERFORMANCE_OUTLIER_PERCENT)
except InvalidOperation:
    SIGNAL_PERFORMANCE_OUTLIER_PERCENT = Decimal("25")
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
CANDIDATE_POOL_LOCK = threading.Lock()
DB_LOCK = threading.Lock()
DB_MIGRATION_LOCK = threading.Lock()
RAW_EVENT_LOCK = threading.Lock()
MARKET_DATA_LOCK = threading.Lock()
LIVE_STATE_LOCK = threading.Lock()
CANDIDATE_DATA_LOCK = threading.Lock()
STOCK_SEARCH_MASTER_LOCK = threading.Lock()
CANDIDATE_PREFETCH_LOCK = threading.Lock()
DB_SCHEMA_READY = False
DB_MIGRATION_DONE = False
DB_LAST_ERROR = ""
DB_MIGRATION_STATUS: dict[str, object] = {
    "enabled": SIGNAL_DB_AUTO_MIGRATE,
    "done": False,
    "ran": False,
    "candidatePool": "pending",
    "candidateData": "pending",
    "discoveryLatest": "pending",
    "snapshotsInserted": 0,
    "snapshotsScanned": 0,
    "error": "",
}
RAW_EVENT_STATE: dict[str, object] = {
    "enabled": SIGNAL_RAW_EVENT_STORAGE_ENABLED,
    "lastStoredAt": "",
    "lastSource": "",
    "lastEventType": "",
    "lastStorage": "",
    "lastError": "",
}
MARKET_DATA_LATEST_STATE: dict[str, object] = {
    "enabled": SIGNAL_MARKET_DATA_LATEST_ENABLED,
    "lastUpdatedAt": "",
    "lastStorage": "",
    "lastCount": 0,
    "lastError": "",
}
STOCK_SEARCH_MASTER_STATE: dict[str, object] = {
    "autoRefreshEnabled": SIGNAL_STOCK_SEARCH_MASTER_AUTO_REFRESH,
    "lastCheckedAt": "",
    "lastRefresh": {},
    "lastError": "",
}
SCHEDULER_STATE: dict[str, object] = {
    "started": False,
    "running": False,
    "lastError": "",
    "lastCheckedAt": "",
    "lastRuns": {},
    "lastPerformanceUpdate": {},
    "lastPerformanceError": "",
    "lastCandidatePrefetch": {},
    "lastCandidatePrefetchError": "",
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


def database_storage_enabled() -> bool:
    if SIGNAL_STORAGE_BACKEND in {"", "0", "false", "off", "filesystem", "file", "json", "local", "ephemeral"}:
        return False
    return bool(DATABASE_URL)


def database_storage_requested() -> bool:
    return SIGNAL_STORAGE_BACKEND in {"auto", "database", "db", "postgres", "postgresql"} or bool(DATABASE_URL)


def set_db_error(error: Exception | str) -> None:
    global DB_LAST_ERROR
    DB_LAST_ERROR = str(error)[:240]


def psycopg_modules():
    psycopg = importlib.import_module("psycopg")
    json_module = importlib.import_module("psycopg.types.json")
    return psycopg, json_module.Jsonb


def safe_read_json_file(path: Path):
    try:
        if path.exists():
            return read_json(path, None)
    except (OSError, json.JSONDecodeError):
        return None
    return None


def ensure_database_schema() -> bool:
    global DB_SCHEMA_READY
    if not database_storage_enabled():
        return False
    if DB_SCHEMA_READY:
        migrate_files_to_database()
        return True
    with DB_LOCK:
        if DB_SCHEMA_READY:
            schema_ready = True
        else:
            schema_ready = False
        if schema_ready:
            migrate_files_to_database()
            return True
        try:
            psycopg, _jsonb = psycopg_modules()
            with psycopg.connect(DATABASE_URL, connect_timeout=5) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS signal_kv (
                            key TEXT PRIMARY KEY,
                            payload JSONB NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        )
                        """
                    )
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS signal_snapshots (
                            id TEXT PRIMARY KEY,
                            mode TEXT NOT NULL,
                            run_trigger TEXT NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL,
                            summary JSONB NOT NULL DEFAULT '{}'::jsonb,
                            dashboard JSONB NOT NULL DEFAULT '{}'::jsonb,
                            payload JSONB NOT NULL,
                            file_name TEXT NOT NULL DEFAULT '',
                            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        )
                        """
                    )
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS signal_raw_events (
                            id TEXT PRIMARY KEY,
                            source TEXT NOT NULL,
                            event_type TEXT NOT NULL,
                            symbol TEXT NOT NULL DEFAULT '',
                            query TEXT NOT NULL DEFAULT '',
                            collected_at TIMESTAMPTZ NOT NULL,
                            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        )
                        """
                    )
                    cur.execute(
                        """
                        CREATE INDEX IF NOT EXISTS signal_snapshots_mode_created_idx
                        ON signal_snapshots (mode, created_at DESC)
                        """
                    )
                    cur.execute(
                        """
                        CREATE INDEX IF NOT EXISTS signal_snapshots_trigger_created_idx
                        ON signal_snapshots (run_trigger, created_at DESC)
                        """
                    )
                    cur.execute(
                        """
                        CREATE INDEX IF NOT EXISTS signal_raw_events_source_collected_idx
                        ON signal_raw_events (source, collected_at DESC)
                        """
                    )
                    cur.execute(
                        """
                        CREATE INDEX IF NOT EXISTS signal_raw_events_symbol_collected_idx
                        ON signal_raw_events (symbol, collected_at DESC)
                        """
                    )
                    cur.execute(
                        """
                        CREATE INDEX IF NOT EXISTS signal_raw_events_type_collected_idx
                        ON signal_raw_events (event_type, collected_at DESC)
                        """
                    )
            DB_SCHEMA_READY = True
            set_db_error("")
        except Exception as error:
            set_db_error(error)
            return False
    migrate_files_to_database()
    return True


def normalize_db_payload(value, fallback):
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return fallback
    return fallback


def short_text(value: object, limit: int) -> str:
    text = str(value or "")
    limit = max(0, int(limit))
    return text if len(text) <= limit else text[:limit]


def db_storage_counts() -> dict:
    if not ensure_database_schema():
        return {}
    try:
        psycopg, _jsonb = psycopg_modules()
        with psycopg.connect(DATABASE_URL, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM signal_kv")
                kv_count = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM signal_snapshots")
                snapshot_count = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM signal_raw_events")
                raw_event_count = cur.fetchone()[0]
                cur.execute("SELECT payload FROM signal_kv WHERE key = 'candidate_pool'")
                pool_row = cur.fetchone()
                cur.execute("SELECT payload FROM signal_kv WHERE key = %s", (CANDIDATE_DATA_KV_KEY,))
                candidate_data_row = cur.fetchone()
                cur.execute("SELECT payload FROM signal_kv WHERE key = %s", (MARKET_DATA_LATEST_KV_KEY,))
                market_data_row = cur.fetchone()
        pool_payload = normalize_db_payload(pool_row[0], {}) if pool_row else {}
        pool_items = pool_payload.get("items", {}) if isinstance(pool_payload, dict) and isinstance(pool_payload.get("items"), dict) else {}
        candidate_data_payload = normalize_db_payload(candidate_data_row[0], {}) if candidate_data_row else {}
        candidate_data_items = (
            candidate_data_payload.get("items", {})
            if isinstance(candidate_data_payload, dict) and isinstance(candidate_data_payload.get("items"), dict)
            else {}
        )
        market_data_payload = normalize_db_payload(market_data_row[0], {}) if market_data_row else {}
        market_data_items = (
            market_data_payload.get("items", {})
            if isinstance(market_data_payload, dict) and isinstance(market_data_payload.get("items"), dict)
            else {}
        )
        active_pool = len([
            record
            for record in pool_items.values()
            if isinstance(record, dict) and str(record.get("stateKey", "")) not in {"excluded", "expired"}
        ])
        set_db_error("")
        return {
            "kvCount": bounded_int(kv_count, 0, 1_000_000),
            "snapshotCount": bounded_int(snapshot_count, 0, 1_000_000),
            "rawEventCount": bounded_int(raw_event_count, 0, 10_000_000),
            "candidatePoolCount": len(pool_items),
            "candidatePoolActiveCount": active_pool,
            "candidateDataCount": len(candidate_data_items),
            "marketDataLatestCount": len(market_data_items),
        }
    except Exception as error:
        set_db_error(error)
        return {}


def migrate_files_to_database(force: bool = False) -> dict:
    global DB_MIGRATION_DONE, DB_MIGRATION_STATUS
    if not SIGNAL_DB_AUTO_MIGRATE and not force:
        DB_MIGRATION_STATUS = {
            **DB_MIGRATION_STATUS,
            "enabled": False,
            "done": True,
            "ran": False,
            "candidatePool": "disabled",
            "candidateData": "disabled",
            "discoveryLatest": "disabled",
            "error": "",
        }
        DB_MIGRATION_DONE = True
        return DB_MIGRATION_STATUS
    if not database_storage_enabled() or not DB_SCHEMA_READY:
        DB_MIGRATION_STATUS = {
            **DB_MIGRATION_STATUS,
            "enabled": bool(SIGNAL_DB_AUTO_MIGRATE or force),
            "done": False,
            "ran": False,
            "error": DB_LAST_ERROR,
        }
        return DB_MIGRATION_STATUS
    if DB_MIGRATION_DONE and not force:
        return DB_MIGRATION_STATUS
    with DB_MIGRATION_LOCK:
        if DB_MIGRATION_DONE and not force:
            return DB_MIGRATION_STATUS
        status: dict[str, object] = {
            "enabled": bool(SIGNAL_DB_AUTO_MIGRATE or force),
            "done": False,
            "ran": True,
            "candidatePool": "missing",
            "candidateData": "missing",
            "discoveryLatest": "missing",
            "snapshotsInserted": 0,
            "snapshotsScanned": 0,
            "snapshotLimit": max(0, SIGNAL_DB_MIGRATE_RUN_LIMIT),
            "error": "",
        }
        try:
            psycopg, Jsonb = psycopg_modules()
            candidate_pool = safe_read_json_file(CANDIDATE_POOL_FILE)
            candidate_data = safe_read_json_file(CANDIDATE_DATA_FILE)
            discovery_latest = safe_read_json_file(DISCOVERY_LATEST_FILE)
            run_paths = []
            if RUNS_DIR.exists() and SIGNAL_DB_MIGRATE_RUN_LIMIT != 0:
                limit = max(0, SIGNAL_DB_MIGRATE_RUN_LIMIT)
                run_paths = sorted(RUNS_DIR.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
                if limit:
                    run_paths = run_paths[:limit]
            with psycopg.connect(DATABASE_URL, connect_timeout=5) as conn:
                with conn.cursor() as cur:
                    if isinstance(candidate_pool, dict) and candidate_pool.get("items"):
                        cur.execute(
                            """
                            INSERT INTO signal_kv (key, payload, updated_at)
                            VALUES ('candidate_pool', %s, NOW())
                            ON CONFLICT (key) DO NOTHING
                            """,
                            (Jsonb(candidate_pool),),
                        )
                        status["candidatePool"] = "inserted" if cur.rowcount else "already-present"
                    elif isinstance(candidate_pool, dict):
                        status["candidatePool"] = "empty"

                    if isinstance(candidate_data, dict) and candidate_data.get("items"):
                        cur.execute(
                            """
                            INSERT INTO signal_kv (key, payload, updated_at)
                            VALUES (%s, %s, NOW())
                            ON CONFLICT (key) DO NOTHING
                            """,
                            (CANDIDATE_DATA_KV_KEY, Jsonb(candidate_data)),
                        )
                        status["candidateData"] = "inserted" if cur.rowcount else "already-present"
                    elif isinstance(candidate_data, dict):
                        status["candidateData"] = "empty"

                    if isinstance(discovery_latest, dict) and discovery_latest:
                        cur.execute(
                            """
                            INSERT INTO signal_kv (key, payload, updated_at)
                            VALUES ('discovery_latest', %s, NOW())
                            ON CONFLICT (key) DO NOTHING
                            """,
                            (Jsonb(discovery_latest),),
                        )
                        status["discoveryLatest"] = "inserted" if cur.rowcount else "already-present"
                    elif isinstance(discovery_latest, dict):
                        status["discoveryLatest"] = "empty"

                    inserted = 0
                    scanned = 0
                    for path in run_paths:
                        snapshot = safe_read_json_file(path)
                        if not isinstance(snapshot, dict) or not snapshot.get("id"):
                            continue
                        scanned += 1
                        cur.execute(
                            """
                            INSERT INTO signal_snapshots (
                                id, mode, run_trigger, created_at, summary, dashboard, payload, file_name, updated_at
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                            ON CONFLICT (id) DO NOTHING
                            """,
                            (
                                str(snapshot.get("id")),
                                str(snapshot.get("mode", "")),
                                str(snapshot.get("trigger", "")),
                                str(snapshot.get("createdAt") or datetime.now(KST).isoformat(timespec="seconds")),
                                Jsonb(snapshot.get("summary", {})),
                                Jsonb(snapshot.get("dashboard", {})),
                                Jsonb(snapshot),
                                path.name,
                            ),
                        )
                        inserted += max(0, cur.rowcount)
                    status["snapshotsInserted"] = inserted
                    status["snapshotsScanned"] = scanned
            status["done"] = True
            DB_MIGRATION_DONE = True
            DB_MIGRATION_STATUS = status
            set_db_error("")
            return DB_MIGRATION_STATUS
        except Exception as error:
            status["error"] = str(error)[:240]
            DB_MIGRATION_STATUS = status
            set_db_error(error)
            return DB_MIGRATION_STATUS


def run_database_migration() -> tuple[dict, int]:
    if not DATABASE_URL:
        return {
            "ok": False,
            "error": "database-not-configured",
            "message": "DATABASE_URL이 설정되어 있지 않습니다.",
            "storage": snapshot_storage_status(),
        }, 400
    if not database_storage_enabled():
        return {
            "ok": False,
            "error": "database-backend-disabled",
            "message": "SIGNAL_STORAGE_BACKEND가 DB 사용 모드가 아닙니다.",
            "storage": snapshot_storage_status(),
        }, 400
    if not ensure_database_schema():
        return {
            "ok": False,
            "error": "database-unavailable",
            "message": "DB 스키마를 준비하지 못했습니다.",
            "storage": snapshot_storage_status(),
        }, 503
    migration = migrate_files_to_database(force=True)
    ok = not migration.get("error")
    return {
        "ok": ok,
        "migration": migration,
        "storage": snapshot_storage_status(),
    }, 200 if ok else 500


def db_read_kv(key: str, fallback):
    if not ensure_database_schema():
        return fallback
    try:
        psycopg, _jsonb = psycopg_modules()
        with psycopg.connect(DATABASE_URL, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT payload FROM signal_kv WHERE key = %s", (key,))
                row = cur.fetchone()
        if not row:
            return fallback
        return normalize_db_payload(row[0], fallback)
    except Exception as error:
        set_db_error(error)
        return fallback


def db_write_kv(key: str, payload) -> bool:
    if not ensure_database_schema():
        return False
    try:
        psycopg, Jsonb = psycopg_modules()
        with psycopg.connect(DATABASE_URL, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO signal_kv (key, payload, updated_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (key)
                    DO UPDATE SET payload = EXCLUDED.payload, updated_at = NOW()
                    """,
                    (key, Jsonb(payload)),
                )
        set_db_error("")
        return True
    except Exception as error:
        set_db_error(error)
        return False


def payload_item_count(payload: object, item_key: str = "items") -> int:
    if not isinstance(payload, dict):
        return 0
    items = payload.get(item_key)
    if isinstance(items, dict):
        return len(items)
    if isinstance(items, list):
        return len(items)
    return 0


def kv_payload_read_probe(key: str, file_path: Path, item_key: str = "items") -> dict:
    db_enabled = database_storage_enabled()
    db_ready = bool(db_enabled and ensure_database_schema())
    db_payload = db_read_kv(key, None) if db_ready else None
    file_payload = safe_read_json_file(file_path)
    if isinstance(db_payload, dict):
        read_source = "postgres"
    elif isinstance(file_payload, dict):
        read_source = "filesystem"
    else:
        read_source = "empty"
    file_exists = file_path.exists()
    return {
        "readSource": read_source,
        "databaseConfigured": bool(DATABASE_URL),
        "databaseEnabled": db_enabled,
        "databaseReady": db_ready,
        "databaseError": DB_LAST_ERROR,
        "dbItemCount": payload_item_count(db_payload, item_key),
        "fileItemCount": payload_item_count(file_payload, item_key),
        "fileExists": file_exists,
        "writeFallback": bool(db_enabled and read_source != "postgres"),
        "readable": read_source != "empty",
    }


def db_write_snapshot(snapshot: dict, file_name: str = "") -> bool:
    if not ensure_database_schema():
        return False
    snapshot_id = str(snapshot.get("id", "")).strip()
    if not snapshot_id:
        return False
    try:
        psycopg, Jsonb = psycopg_modules()
        with psycopg.connect(DATABASE_URL, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO signal_snapshots (
                        id, mode, run_trigger, created_at, summary, dashboard, payload, file_name, updated_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (id)
                    DO UPDATE SET
                        mode = EXCLUDED.mode,
                        run_trigger = EXCLUDED.run_trigger,
                        created_at = EXCLUDED.created_at,
                        summary = EXCLUDED.summary,
                        dashboard = EXCLUDED.dashboard,
                        payload = EXCLUDED.payload,
                        file_name = EXCLUDED.file_name,
                        updated_at = NOW()
                    """,
                    (
                        snapshot_id,
                        str(snapshot.get("mode", "")),
                        str(snapshot.get("trigger", "")),
                        str(snapshot.get("createdAt") or datetime.now(KST).isoformat(timespec="seconds")),
                        Jsonb(snapshot.get("summary", {})),
                        Jsonb(snapshot.get("dashboard", {})),
                        Jsonb(snapshot),
                        file_name,
                    ),
                )
        set_db_error("")
        return True
    except Exception as error:
        set_db_error(error)
        return False


def compact_raw_payload(value, list_limit: int | None = None, depth: int = 0):
    list_limit = SIGNAL_RAW_EVENT_PAYLOAD_LIMIT if list_limit is None else max(1, int(list_limit))
    if depth > 4:
        return short_text(str(value), 500)
    if isinstance(value, dict):
        compacted = {}
        for key, item in value.items():
            text_key = short_text(str(key), 120)
            compacted[text_key] = compact_raw_payload(item, list_limit=list_limit, depth=depth + 1)
        return compacted
    if isinstance(value, list):
        return [compact_raw_payload(item, list_limit=list_limit, depth=depth + 1) for item in value[:list_limit]]
    if isinstance(value, tuple):
        return [compact_raw_payload(item, list_limit=list_limit, depth=depth + 1) for item in list(value)[:list_limit]]
    if isinstance(value, (datetime, Decimal)):
        return str(value)
    if isinstance(value, str):
        return short_text(value, 2000)
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return short_text(str(value), 1000)


def raw_event_id(source: str, event_type: str, symbol: str, query: str, collected_at: str, payload) -> str:
    fingerprint = json.dumps(
        {
            "source": source,
            "eventType": event_type,
            "symbol": symbol,
            "query": query,
            "collectedAt": collected_at,
            "payload": payload,
        },
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:32]


def db_write_raw_event(event: dict) -> bool:
    if not ensure_database_schema():
        return False
    try:
        psycopg, Jsonb = psycopg_modules()
        with psycopg.connect(DATABASE_URL, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO signal_raw_events (
                        id, source, event_type, symbol, query, collected_at, payload
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        event["id"],
                        event["source"],
                        event["eventType"],
                        event.get("symbol", ""),
                        event.get("query", ""),
                        event["collectedAt"],
                        Jsonb(event.get("payload", {})),
                    ),
                )
        set_db_error("")
        return True
    except Exception as error:
        set_db_error(error)
        RAW_EVENT_STATE["lastError"] = str(error)[:240]
        return False


def file_write_raw_event(event: dict) -> bool:
    with RAW_EVENT_LOCK:
        try:
            existing = safe_read_json_file(RAW_EVENTS_FILE)
            if isinstance(existing, dict):
                events = existing.get("events", [])
            elif isinstance(existing, list):
                events = existing
            else:
                events = []
            if not isinstance(events, list):
                events = []
            limit = max(1, SIGNAL_RAW_EVENT_FILE_LIMIT)
            next_events = [event, *[item for item in events if isinstance(item, dict) and item.get("id") != event["id"]]][:limit]
            write_json(
                RAW_EVENTS_FILE,
                {
                    "version": 1,
                    "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
                    "events": next_events,
                },
            )
            return True
        except OSError as error:
            RAW_EVENT_STATE["lastError"] = str(error)[:240]
            return False


def market_data_latest_empty() -> dict:
    return {"version": 1, "updatedAt": "", "items": {}, "summary": {}}


def market_data_latest_data() -> dict:
    if not SIGNAL_MARKET_DATA_LATEST_ENABLED:
        return market_data_latest_empty()
    stored = db_read_kv(MARKET_DATA_LATEST_KV_KEY, None) if database_storage_enabled() else None
    file_data = safe_read_json_file(MARKET_DATA_LATEST_FILE)
    data = stored if isinstance(stored, dict) else file_data if isinstance(file_data, dict) else market_data_latest_empty()
    if not isinstance(data, dict):
        return market_data_latest_empty()
    if not isinstance(data.get("items"), dict):
        data["items"] = {}
    if not isinstance(data.get("summary"), dict):
        data["summary"] = {}
    return data


def market_data_latest_write(data: dict) -> tuple[bool, str]:
    if not SIGNAL_MARKET_DATA_LATEST_ENABLED:
        return False, "disabled"
    payload = live_state_json_safe(data)
    if database_storage_enabled() and db_write_kv(MARKET_DATA_LATEST_KV_KEY, payload):
        return True, "postgres"
    write_json(MARKET_DATA_LATEST_FILE, payload)
    return True, "filesystem-fallback" if database_storage_enabled() else "filesystem"


def market_data_latest_key(source: str, event_type: str, symbol: str = "", query: str = "") -> str:
    symbol = str(symbol or "").strip().upper()
    if symbol:
        return f"{source}:{event_type}:{symbol}"
    query = str(query or "").strip()
    digest = hashlib.sha256(query.encode("utf-8")).hexdigest()[:16] if query else "global"
    return f"{source}:{event_type}:{digest}"


def payload_result_rows(payload: object) -> list[dict]:
    if not isinstance(payload, dict):
        return []
    result = payload.get("result")
    if isinstance(result, list):
        return [item for item in result if isinstance(item, dict)]
    if isinstance(result, dict):
        rows = result.get("items") or result.get("data") or result.get("list")
        if isinstance(rows, list):
            return [item for item in rows if isinstance(item, dict)]
    return []


def payload_symbol(value: dict) -> str:
    for key in ("symbol", "ticker", "code", "stockCode", "isuSrtCd", "itemCode"):
        symbol = str(value.get(key, "")).strip().upper()
        if symbol:
            return symbol
    return ""


def market_data_records_from_event(event: dict) -> list[tuple[str, dict]]:
    source = str(event.get("source", "unknown")).strip().lower() or "unknown"
    event_type = str(event.get("eventType", "raw")).strip().lower() or "raw"
    symbol = str(event.get("symbol", "")).strip().upper()
    query = str(event.get("query", "")).strip()
    payload = event.get("payload", {}) if isinstance(event.get("payload"), dict) else {}
    data = payload.get("data") if isinstance(payload, dict) else {}
    metadata = payload.get("metadata", {}) if isinstance(payload, dict) and isinstance(payload.get("metadata"), dict) else {}
    collected_at = str(event.get("collectedAt", ""))
    base_record = {
        "source": source,
        "eventType": event_type,
        "symbol": symbol,
        "query": query,
        "collectedAt": collected_at,
        "rawEventId": event.get("id", ""),
        "metadata": metadata,
        "payload": payload,
    }
    records: list[tuple[str, dict]] = [(market_data_latest_key(source, event_type, symbol, query), base_record)]

    for row in payload_result_rows(data):
        row_symbol = payload_symbol(row)
        if not row_symbol:
            continue
        record = {
            **base_record,
            "symbol": row_symbol,
            "payload": {
                "data": row,
                "metadata": metadata,
            },
        }
        records.append((market_data_latest_key(source, event_type, row_symbol, ""), record))
    return records


def trim_market_data_latest_items(items: dict) -> dict:
    if len(items) <= SIGNAL_MARKET_DATA_LATEST_MAX_ITEMS:
        return items
    ranked = sorted(
        items.items(),
        key=lambda pair: str(pair[1].get("collectedAt", "")) if isinstance(pair[1], dict) else "",
        reverse=True,
    )
    return dict(ranked[: max(1, SIGNAL_MARKET_DATA_LATEST_MAX_ITEMS)])


def update_market_data_latest(event: dict) -> dict:
    if not SIGNAL_MARKET_DATA_LATEST_ENABLED:
        return {"enabled": False, "stored": False, "storage": "disabled", "updatedCount": 0}
    records = market_data_records_from_event(event)
    if not records:
        return {"enabled": True, "stored": False, "storage": "", "updatedCount": 0}
    with MARKET_DATA_LOCK:
        data = market_data_latest_data()
        items = data.get("items", {}) if isinstance(data.get("items"), dict) else {}
        for key, record in records:
            previous = items.get(key, {}) if isinstance(items.get(key), dict) else {}
            items[key] = {
                **previous,
                **record,
                "updatedAt": event.get("collectedAt", datetime.now(KST).isoformat(timespec="seconds")),
                "observations": int(previous.get("observations", 0) or 0) + 1,
            }
        data["items"] = trim_market_data_latest_items(items)
        data["updatedAt"] = datetime.now(KST).isoformat(timespec="seconds")
        by_source: dict[str, int] = {}
        by_type: dict[str, int] = {}
        for item in data["items"].values():
            if not isinstance(item, dict):
                continue
            item_source = str(item.get("source", "unknown"))
            item_type = str(item.get("eventType", "raw"))
            by_source[item_source] = by_source.get(item_source, 0) + 1
            by_type[item_type] = by_type.get(item_type, 0) + 1
        data["summary"] = {
            "itemCount": len(data["items"]),
            "bySource": by_source,
            "byType": by_type,
            "updatedAt": data["updatedAt"],
        }
        ok, storage = market_data_latest_write(data)
    MARKET_DATA_LATEST_STATE.update({
        "enabled": True,
        "lastUpdatedAt": data["updatedAt"] if ok else "",
        "lastStorage": storage if ok else "",
        "lastCount": len(data.get("items", {})) if isinstance(data.get("items"), dict) else 0,
        "lastError": "" if ok else "latest-write-failed",
    })
    return {
        "enabled": True,
        "stored": ok,
        "storage": storage,
        "updatedCount": len(records),
        "itemCount": len(data.get("items", {})) if isinstance(data.get("items"), dict) else 0,
        "updatedAt": data.get("updatedAt", ""),
    }


def update_market_data_latest_from_candidates(candidates: list[dict], mode: str = "", stage: str = "selected") -> dict:
    if not SIGNAL_MARKET_DATA_LATEST_ENABLED:
        return {"enabled": False, "stored": False, "storage": "disabled", "updatedCount": 0, "message": "최신 수집값 저장이 꺼져 있습니다."}

    now_text = datetime.now(KST).isoformat(timespec="seconds")
    rows: list[tuple[str, dict]] = []
    skipped_count = 0
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        symbol = str(candidate.get("symbol", "")).strip().upper()
        live_price = candidate.get("livePrice", {}) if isinstance(candidate.get("livePrice"), dict) else {}
        if not symbol or str(live_price.get("source", "")) != "toss" or not live_price.get("lastPrice") or not live_price.get("currency"):
            skipped_count += 1
            continue
        timestamp = str(live_price.get("timestamp") or live_price.get("updatedAt") or candidate.get("updated") or now_text)
        row = {
            "symbol": symbol,
            "name": candidate.get("name", ""),
            "market": candidate.get("market", ""),
            "lastPrice": str(live_price.get("lastPrice")),
            "currency": str(live_price.get("currency")),
            "timestamp": timestamp,
            "updatedAt": str(live_price.get("updatedAt") or timestamp),
            "mode": mode,
            "stage": stage,
            "dataSource": str(live_price.get("dataSource") or "candidate-final"),
            "retained": bool(live_price.get("retained")),
        }
        change = display_percent_to_decimal(candidate.get("change"))
        if change is not None:
            row["changeRate"] = str(change)
        for source_key in ("changeSource", "changeMessage", "freshness"):
            if source_key in live_price:
                row[source_key] = live_state_json_safe(live_price.get(source_key))
        completeness = candidate.get("dataCompleteness", {}) if isinstance(candidate.get("dataCompleteness"), dict) else candidate_data_completeness(candidate)
        row["dataCompleteness"] = live_state_json_safe({
            "displayReady": bool(completeness.get("displayReady")),
            "entryReady": bool(completeness.get("entryReady")),
            "missing": completeness.get("missing", []),
        })
        record = {
            "source": "toss",
            "eventType": "prices",
            "symbol": symbol,
            "query": "candidate-final",
            "collectedAt": now_text,
            "rawEventId": "",
            "metadata": {
                "mode": mode,
                "stage": stage,
                "source": "candidate-final",
                "retained": bool(live_price.get("retained")),
            },
            "payload": {
                "data": row,
                "metadata": {
                    "mode": mode,
                    "stage": stage,
                    "source": "candidate-final",
                },
            },
        }
        rows.append((market_data_latest_key("toss", "prices", symbol, ""), record))

    if not rows:
        return {
            "enabled": True,
            "stored": False,
            "storage": "",
            "updatedCount": 0,
            "skippedCount": skipped_count,
            "message": "최종 후보 중 저장할 Toss 가격이 없습니다.",
        }

    with MARKET_DATA_LOCK:
        data = market_data_latest_data()
        items = data.get("items", {}) if isinstance(data.get("items"), dict) else {}
        for key, record in rows:
            previous = items.get(key, {}) if isinstance(items.get(key), dict) else {}
            items[key] = {
                **previous,
                **record,
                "updatedAt": now_text,
                "observations": int(previous.get("observations", 0) or 0) + 1,
            }
        data["items"] = trim_market_data_latest_items(items)
        data["updatedAt"] = now_text
        by_source: dict[str, int] = {}
        by_type: dict[str, int] = {}
        for item in data["items"].values():
            if not isinstance(item, dict):
                continue
            item_source = str(item.get("source", "unknown"))
            item_type = str(item.get("eventType", "raw"))
            by_source[item_source] = by_source.get(item_source, 0) + 1
            by_type[item_type] = by_type.get(item_type, 0) + 1
        data["summary"] = {
            "itemCount": len(data["items"]),
            "bySource": by_source,
            "byType": by_type,
            "updatedAt": data["updatedAt"],
            "lastCandidateFinalCount": len(rows),
            "lastCandidateFinalStage": stage,
        }
        ok, storage = market_data_latest_write(data)
    MARKET_DATA_LATEST_STATE.update({
        "enabled": True,
        "lastUpdatedAt": data["updatedAt"] if ok else "",
        "lastStorage": storage if ok else "",
        "lastCount": len(data.get("items", {})) if isinstance(data.get("items"), dict) else 0,
        "lastError": "" if ok else "candidate-latest-write-failed",
    })
    return {
        "enabled": True,
        "stored": ok,
        "storage": storage,
        "updatedCount": len(rows),
        "skippedCount": skipped_count,
        "itemCount": len(data.get("items", {})) if isinstance(data.get("items"), dict) else 0,
        "updatedAt": data.get("updatedAt", ""),
        "message": f"서버 최종 후보 Toss 가격 {len(rows)}개를 최신값 저장소에 업데이트했습니다.",
    }


def market_data_latest_status() -> dict:
    if not SIGNAL_MARKET_DATA_LATEST_ENABLED:
        return {"enabled": False, "storage": "disabled", "itemCount": 0, "message": "최신 수집값 저장이 꺼져 있습니다."}
    data = market_data_latest_data()
    items = data.get("items", {}) if isinstance(data.get("items"), dict) else {}
    summary = data.get("summary", {}) if isinstance(data.get("summary"), dict) else {}
    probe = kv_payload_read_probe(MARKET_DATA_LATEST_KV_KEY, MARKET_DATA_LATEST_FILE)
    storage = probe["readSource"]
    persistent = storage == "postgres"
    if persistent:
        message = "서버가 수집한 최신 원천 데이터를 Postgres DB에서 읽고 업데이트합니다."
    elif probe["databaseReady"] and probe["fileItemCount"] > 0:
        message = "DB는 연결됐지만 최신 원천 데이터가 아직 DB에 없어 파일 fallback을 읽고 있습니다. 다음 수집 또는 DB 이관 후 DB 기준으로 전환됩니다."
    elif probe["databaseReady"]:
        message = "DB는 연결됐지만 최신 원천 데이터가 아직 저장되지 않았습니다. 다음 수집 주기에서 DB에 저장됩니다."
    elif probe["databaseConfigured"]:
        message = "DB 연결 또는 스키마 확인에 실패해 최신 원천 데이터를 파일 fallback으로 읽습니다."
    else:
        message = "최신 원천 데이터가 임시 파일 저장소에 저장됩니다. 재배포/재시작 후 보존을 장담할 수 없습니다."
    return {
        "enabled": True,
        "storage": storage,
        "readSource": probe["readSource"],
        "databaseConfigured": probe["databaseConfigured"],
        "databaseReady": probe["databaseReady"],
        "databaseError": probe["databaseError"],
        "dbItemCount": probe["dbItemCount"],
        "fileItemCount": probe["fileItemCount"],
        "fileExists": probe["fileExists"],
        "writeFallback": probe["writeFallback"],
        "operationReady": persistent and len(items) > 0,
        "persistent": persistent,
        "volatileFallback": not persistent,
        "itemCount": len(items),
        "bySource": summary.get("bySource", {}),
        "byType": summary.get("byType", {}),
        "latestAt": data.get("updatedAt", ""),
        "lastStorage": MARKET_DATA_LATEST_STATE.get("lastStorage", ""),
        "lastUpdatedAt": MARKET_DATA_LATEST_STATE.get("lastUpdatedAt", ""),
        "message": message,
    }


def stored_market_data_latest_records(source: str = "", event_type: str = "") -> dict[str, dict]:
    if not SIGNAL_MARKET_DATA_LATEST_ENABLED:
        return {}
    data = market_data_latest_data()
    items = data.get("items", {}) if isinstance(data.get("items"), dict) else {}
    source_filter = str(source or "").strip().lower()
    type_filter = str(event_type or "").strip().lower()
    records: dict[str, dict] = {}
    for item in items.values():
        if not isinstance(item, dict):
            continue
        item_source = str(item.get("source", "")).strip().lower()
        item_type = str(item.get("eventType", "")).strip().lower()
        if source_filter and item_source != source_filter:
            continue
        if type_filter and item_type != type_filter:
            continue
        symbol = str(item.get("symbol", "")).strip().upper()
        payload = item.get("payload", {}) if isinstance(item.get("payload"), dict) else {}
        row = payload.get("data", {}) if isinstance(payload.get("data"), dict) else {}
        row_symbol = payload_symbol(row)
        normalized = symbol or row_symbol
        if normalized:
            previous = records.get(normalized)
            if not previous or str(item.get("updatedAt") or item.get("collectedAt") or "") >= str(previous.get("updatedAt") or previous.get("collectedAt") or ""):
                records[normalized] = item
    return records


def market_data_record_payload_row(record: dict) -> dict:
    payload = record.get("payload", {}) if isinstance(record.get("payload"), dict) else {}
    row = payload.get("data", {}) if isinstance(payload.get("data"), dict) else {}
    return row


def market_data_record_timestamp(record: dict) -> str:
    row = market_data_record_payload_row(record)
    return str(
        row.get("timestamp")
        or row.get("updatedAt")
        or record.get("updatedAt")
        or record.get("collectedAt")
        or ""
    )


def timestamp_is_newer(left: str, right: str) -> bool:
    left_dt = parse_iso_datetime(str(left or ""))
    right_dt = parse_iso_datetime(str(right or ""))
    if left_dt is None:
        return False
    if right_dt is None:
        return True
    return left_dt > right_dt


def live_price_from_market_data_record(record: dict, fallback_updated_at: str = "", market: str = "") -> dict | None:
    row = market_data_record_payload_row(record)
    last_price = row.get("lastPrice")
    currency = row.get("currency")
    if last_price in {"", None} or not currency:
        return None
    updated_at = str(record.get("updatedAt") or record.get("collectedAt") or fallback_updated_at)
    live_price = {
        "lastPrice": str(last_price),
        "currency": str(currency),
        "timestamp": row.get("timestamp") or updated_at,
        "updatedAt": updated_at,
        "source": "toss",
        "dataSource": "market_data_latest",
        "retained": True,
        "message": "서버 DB에 저장된 최신 토스 현재가를 후보 판단에 반영했습니다.",
    }
    change = change_from_toss_price_row(row)
    if change:
        live_price["changeSource"] = "market-data-latest"
    else:
        live_price["changeSource"] = "pending-change"
        live_price["changeMessage"] = "DB 최신 가격에는 있으나 등락률 기준가는 추가 확인 중입니다."
    live_price["freshness"] = live_price_freshness(live_price, updated_at, market)
    return live_price


def live_price_from_candidate_data_record(record: dict, fallback_updated_at: str = "", market: str = "") -> dict | None:
    if not isinstance(record, dict):
        return None
    live_price = record.get("livePrice", {}) if isinstance(record.get("livePrice"), dict) else {}
    if str(live_price.get("source", "")) != "toss" or not live_price.get("lastPrice") or not live_price.get("currency"):
        return None
    updated_at = str(
        live_price.get("updatedAt")
        or live_price.get("timestamp")
        or record.get("collectedAt")
        or fallback_updated_at
        or ""
    )
    retained = copy.deepcopy(live_price)
    retained.update({
        "source": "toss",
        "dataSource": "candidate_data_snapshots",
        "retained": True,
        "updatedAt": updated_at,
        "message": "서버에 저장된 후보별 최종 토스 가격을 후보 판단에 반영했습니다.",
    })
    if not retained.get("timestamp"):
        retained["timestamp"] = updated_at
    if not retained.get("changeSource"):
        retained["changeSource"] = "stored-candidate-data"
    if not retained.get("changeMessage"):
        retained["changeMessage"] = "저장된 후보 데이터의 등락률을 유지합니다."
    retained["freshness"] = live_price_freshness(retained, updated_at, market)
    return retained


def stored_live_price_for_candidate(
    candidate: dict,
    market_records: dict[str, dict] | None = None,
    candidate_records: dict[str, dict] | None = None,
) -> tuple[dict | None, dict]:
    symbol = str(candidate.get("symbol", "")).strip().upper()
    if not symbol:
        return None, {"source": "none", "message": "종목 코드가 없습니다."}
    market = str(candidate.get("market", ""))
    fallback_updated_at = str(candidate.get("updated", ""))
    market_records = market_records if isinstance(market_records, dict) else stored_market_data_latest_records("toss", "prices")
    candidate_records = candidate_records if isinstance(candidate_records, dict) else stored_candidate_data_latest_records()

    market_record = market_records.get(symbol)
    if isinstance(market_record, dict):
        live_price = live_price_from_market_data_record(market_record, fallback_updated_at, market)
        if live_price is not None:
            return live_price, {
                "source": "market_data_latest",
                "timestamp": market_data_record_timestamp(market_record),
                "message": "DB 최신 토스 원천 가격을 사용했습니다.",
            }

    candidate_record = candidate_records.get(symbol)
    if isinstance(candidate_record, dict):
        live_price = live_price_from_candidate_data_record(candidate_record, fallback_updated_at, market)
        if live_price is not None:
            return live_price, {
                "source": "candidate_data_snapshots",
                "timestamp": candidate_data_record_timestamp(candidate_record),
                "message": "저장 후보 데이터의 최종 토스 가격을 사용했습니다.",
            }

    return None, {"source": "none", "message": "저장된 토스 가격이 없습니다."}


def merge_market_data_latest_into_candidates(candidates: list[dict]) -> tuple[list[dict], dict]:
    if not SIGNAL_MARKET_DATA_LATEST_ENABLED:
        return candidates, {"enabled": False, "mergedCount": 0, "message": "최신 수집값 저장이 꺼져 있습니다."}
    records = stored_market_data_latest_records("toss", "prices")
    if not records:
        return candidates, {"enabled": True, "mergedCount": 0, "message": "DB에 저장된 토스 최신 가격이 아직 없습니다."}

    merged: list[dict] = []
    merged_count = 0
    price_merged_count = 0
    change_merged_count = 0
    retained_count = 0
    for candidate in candidates:
        if not isinstance(candidate, dict):
            merged.append(candidate)
            continue
        item = copy.deepcopy(candidate)
        symbol = str(item.get("symbol", "")).strip().upper()
        record = records.get(symbol)
        if not record:
            merged.append(item)
            continue

        record_live_price = live_price_from_market_data_record(record, item.get("updated", ""), str(item.get("market", "")))
        if record_live_price is None:
            merged.append(item)
            continue

        current_live_price = item.get("livePrice", {}) if isinstance(item.get("livePrice"), dict) else {}
        current_timestamp = str(current_live_price.get("timestamp") or current_live_price.get("updatedAt") or "")
        record_timestamp = market_data_record_timestamp(record)
        has_current_price = candidate_has_toss_last_price(item)
        should_merge_price = not has_current_price or timestamp_is_newer(record_timestamp, current_timestamp)
        if should_merge_price:
            item["price"] = display_price(str(record_live_price["lastPrice"]), str(record_live_price["currency"]))
            item["livePrice"] = record_live_price
            price_merged_count += 1
        else:
            retained_count += 1

        row = market_data_record_payload_row(record)
        change = change_from_toss_price_row(row)
        if change and (not candidate_data_has_change(item) or should_merge_price):
            item["change"] = change
            if isinstance(item.get("livePrice"), dict):
                item["livePrice"] = {
                    **item["livePrice"],
                    "changeSource": "market-data-latest",
                    "changeMessage": "DB에 저장된 토스 최신 가격 기준 등락률을 반영했습니다.",
                }
            change_merged_count += 1

        item["marketDataLatest"] = {
            "source": "market_data_latest",
            "eventType": record.get("eventType", ""),
            "collectedAt": record.get("collectedAt", ""),
            "updatedAt": record.get("updatedAt", ""),
            "ageSeconds": seconds_since_timestamp(record_timestamp),
            "message": "서버가 수집해 저장한 최신 원천 가격을 우선 반영했습니다.",
        }
        merged_count += 1
        merged.append(item)

    return merged, {
        "enabled": True,
        "source": "market_data_latest",
        "mergedCount": merged_count,
        "priceMergedCount": price_merged_count,
        "changeMergedCount": change_merged_count,
        "retainedCount": retained_count,
        "availableCount": len(records),
        "message": f"DB 최신 토스 가격 {merged_count}개를 후보 판단에 반영했습니다.",
    }


def write_raw_event(
    source: str,
    event_type: str,
    payload,
    symbol: str = "",
    query: str = "",
    metadata: dict | None = None,
) -> dict:
    if not SIGNAL_RAW_EVENT_STORAGE_ENABLED:
        return {"stored": False, "storage": "disabled"}
    compact_payload = compact_raw_payload({
        "data": payload,
        "metadata": metadata or {},
    })
    source = short_text(str(source or "unknown").strip().lower(), 60) or "unknown"
    event_type = short_text(str(event_type or "raw").strip().lower(), 80) or "raw"
    symbol = short_text(str(symbol or "").strip(), 40)
    query = short_text(str(query or "").strip(), 240)
    collected_at = datetime.now(KST).isoformat(timespec="seconds")
    event = {
        "id": raw_event_id(source, event_type, symbol, query, collected_at, compact_payload),
        "source": source,
        "eventType": event_type,
        "symbol": symbol,
        "query": query,
        "collectedAt": collected_at,
        "payload": compact_payload,
    }
    stored = False
    storage = "filesystem"
    if database_storage_enabled():
        stored = db_write_raw_event(event)
        storage = "postgres" if stored else "filesystem-fallback"
    if not stored:
        stored = file_write_raw_event(event)
    RAW_EVENT_STATE.update({
        "enabled": SIGNAL_RAW_EVENT_STORAGE_ENABLED,
        "lastStoredAt": collected_at if stored else "",
        "lastSource": source,
        "lastEventType": event_type,
        "lastStorage": storage if stored else "",
        "lastError": "" if stored else str(RAW_EVENT_STATE.get("lastError", "")),
    })
    latest = update_market_data_latest(event) if stored else {"stored": False, "updatedCount": 0}
    return {"stored": stored, "storage": storage, "id": event["id"], "latest": latest}


def db_raw_event_counts() -> dict:
    if not ensure_database_schema():
        return {}
    try:
        psycopg, _jsonb = psycopg_modules()
        with psycopg.connect(DATABASE_URL, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM signal_raw_events")
                total_count = cur.fetchone()[0]
                cur.execute(
                    """
                    SELECT source, COUNT(*)
                    FROM signal_raw_events
                    GROUP BY source
                    ORDER BY COUNT(*) DESC, source ASC
                    LIMIT 8
                    """
                )
                source_rows = cur.fetchall()
                cur.execute(
                    """
                    SELECT source, event_type, symbol, query, collected_at
                    FROM signal_raw_events
                    ORDER BY collected_at DESC
                    LIMIT 1
                    """
                )
                latest = cur.fetchone()
        latest_record = {}
        if latest:
            collected_at = latest[4]
            latest_record = {
                "source": latest[0],
                "eventType": latest[1],
                "symbol": latest[2],
                "query": latest[3],
                "collectedAt": collected_at.isoformat(timespec="seconds") if hasattr(collected_at, "isoformat") else str(collected_at),
            }
        set_db_error("")
        return {
            "count": bounded_int(total_count, 0, 10_000_000),
            "bySource": {str(source): bounded_int(count, 0, 10_000_000) for source, count in source_rows},
            "latest": latest_record,
        }
    except Exception as error:
        set_db_error(error)
        return {}


def file_raw_event_counts() -> dict:
    existing = safe_read_json_file(RAW_EVENTS_FILE)
    if isinstance(existing, dict):
        events = existing.get("events", [])
    elif isinstance(existing, list):
        events = existing
    else:
        events = []
    events = [event for event in events if isinstance(event, dict)]
    by_source: dict[str, int] = {}
    for event in events:
        source = str(event.get("source") or "unknown")
        by_source[source] = by_source.get(source, 0) + 1
    latest = events[0] if events else {}
    return {
        "count": len(events),
        "bySource": by_source,
        "latest": {
            "source": latest.get("source", ""),
            "eventType": latest.get("eventType", ""),
            "symbol": latest.get("symbol", ""),
            "query": latest.get("query", ""),
            "collectedAt": latest.get("collectedAt", ""),
        } if latest else {},
    }


def raw_event_storage_status() -> dict:
    db_counts = db_raw_event_counts() if SIGNAL_RAW_EVENT_STORAGE_ENABLED and database_storage_enabled() else {}
    if db_counts:
        counts = db_counts
        implementation = "postgres"
        persistent = True
    else:
        counts = file_raw_event_counts() if SIGNAL_RAW_EVENT_STORAGE_ENABLED else {"count": 0, "bySource": {}, "latest": {}}
        implementation = "filesystem"
        persistent = False
    return {
        "enabled": SIGNAL_RAW_EVENT_STORAGE_ENABLED,
        "implementation": implementation,
        "persistent": persistent,
        "file": display_local_path(RAW_EVENTS_FILE),
        "count": counts.get("count", 0),
        "bySource": counts.get("bySource", {}),
        "latest": counts.get("latest", {}),
        "last": dict(RAW_EVENT_STATE),
    }


def db_recent_scheduler_runs(limit: int) -> list[dict]:
    if not ensure_database_schema():
        return []
    try:
        psycopg, _jsonb = psycopg_modules()
        with psycopg.connect(DATABASE_URL, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, mode, run_trigger, created_at, file_name, summary
                    FROM signal_snapshots
                    ORDER BY created_at DESC, updated_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
        records = []
        for snapshot_id, mode, trigger, created_at, file_name, summary in rows:
            created_text = created_at.isoformat(timespec="seconds") if hasattr(created_at, "isoformat") else str(created_at)
            records.append({
                "id": snapshot_id,
                "mode": mode,
                "trigger": trigger,
                "createdAt": created_text,
                "file": file_name or "database",
                "summary": normalize_db_payload(summary, {}),
            })
        set_db_error("")
        return records
    except Exception as error:
        set_db_error(error)
        return []


def db_scheduled_snapshot_exists(run_date: str, mode: str) -> bool:
    if not ensure_database_schema():
        return False
    try:
        psycopg, _jsonb = psycopg_modules()
        with psycopg.connect(DATABASE_URL, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 1
                    FROM signal_snapshots
                    WHERE mode = %s AND run_trigger = 'scheduled' AND created_at::date = %s::date
                    LIMIT 1
                    """,
                    (mode, run_date),
                )
                row = cur.fetchone()
        set_db_error("")
        return bool(row)
    except Exception as error:
        set_db_error(error)
        return False


def db_snapshot_detail(run_id: str) -> dict | None:
    if not ensure_database_schema():
        return None
    try:
        psycopg, _jsonb = psycopg_modules()
        with psycopg.connect(DATABASE_URL, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT payload FROM signal_snapshots WHERE id = %s", (run_id,))
                row = cur.fetchone()
        if not row:
            return None
        snapshot = normalize_db_payload(row[0], {})
        if not isinstance(snapshot, dict):
            return None
        record = {
            "id": snapshot.get("id", run_id),
            "mode": snapshot.get("mode"),
            "trigger": snapshot.get("trigger"),
            "createdAt": snapshot.get("createdAt"),
            "file": "database",
            "summary": snapshot.get("summary", {}),
        }
        set_db_error("")
        return {"record": record, "dashboard": snapshot.get("dashboard", {})}
    except Exception as error:
        set_db_error(error)
        return None


def db_latest_snapshot_detail(mode: str | None = None) -> dict | None:
    if not ensure_database_schema():
        return None
    try:
        psycopg, _jsonb = psycopg_modules()
        params: tuple = ()
        where_clause = ""
        if mode:
            where_clause = "WHERE mode = %s"
            params = (mode,)
        with psycopg.connect(DATABASE_URL, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT payload
                    FROM signal_snapshots
                    {where_clause}
                    ORDER BY created_at DESC, updated_at DESC
                    LIMIT 1
                    """,
                    params,
                )
                row = cur.fetchone()
        if not row:
            set_db_error("")
            return None
        snapshot = normalize_db_payload(row[0], {})
        if not isinstance(snapshot, dict):
            return None
        record = {
            "id": snapshot.get("id", ""),
            "mode": snapshot.get("mode"),
            "trigger": snapshot.get("trigger"),
            "createdAt": snapshot.get("createdAt"),
            "file": "database",
            "summary": snapshot.get("summary", {}),
        }
        set_db_error("")
        return {"record": record, "dashboard": snapshot.get("dashboard", {})}
    except Exception as error:
        set_db_error(error)
        return None


def database_status() -> dict:
    enabled = database_storage_enabled()
    ready = ensure_database_schema() if enabled else False
    counts = db_storage_counts() if ready else {}
    requested = database_storage_requested()
    if ready:
        message = "Postgres DB를 기준 저장소로 사용 중입니다."
        next_action = "운영 가능"
    elif DATABASE_URL:
        message = "DATABASE_URL은 설정되어 있으나 DB 연결 또는 스키마 확인에 실패했습니다."
        next_action = "DB 연결 오류 확인"
    elif requested:
        message = "DATABASE_URL이 없어 서버 수집 데이터가 임시 파일 저장소로 대체됩니다."
        next_action = "Postgres DATABASE_URL 연결"
    else:
        message = "DB 저장소가 비활성화되어 파일 저장소를 사용합니다."
        next_action = "운영 전 DB 저장소 검토"
    return {
        "backend": SIGNAL_STORAGE_BACKEND,
        "urlConfigured": bool(DATABASE_URL),
        "enabled": enabled,
        "ready": ready,
        "implementation": "postgres" if enabled else "filesystem",
        "persistent": bool(ready),
        "volatileFallback": not bool(ready),
        "requiredForStableOperation": True,
        "requested": requested,
        "autoMigrate": SIGNAL_DB_AUTO_MIGRATE,
        "migration": dict(DB_MIGRATION_STATUS),
        "counts": counts,
        "message": message,
        "nextAction": next_action,
        "error": DB_LAST_ERROR,
    }


def seed_data() -> dict:
    return read_json(SEED_FILE, {"candidates": [], "market": {}, "principles": []})


def universe_data() -> dict:
    return read_json(UNIVERSE_FILE, {"symbols": []})


def stock_search_master_data() -> dict:
    return read_json(STOCK_SEARCH_MASTER_FILE, {"symbols": []})


def stock_search_generated_data() -> tuple[dict, str]:
    if database_storage_enabled():
        payload = db_read_kv(STOCK_SEARCH_MASTER_KV_KEY, {})
        if isinstance(payload, dict) and isinstance(payload.get("symbols"), list):
            return payload, "database"
    payload = read_json(STOCK_SEARCH_GENERATED_FILE, {})
    if isinstance(payload, dict) and isinstance(payload.get("symbols"), list):
        return payload, "filesystem"
    return {"symbols": []}, "none"


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
        "priceBatchSize": TOSS_PRICE_BATCH_SIZE,
        "candleMaxCandidates": TOSS_CANDLE_MAX_CANDIDATES,
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


def symbol_batches(symbols: list[str], batch_size: int) -> list[list[str]]:
    batch_size = max(1, int(batch_size or 1))
    return [symbols[index:index + batch_size] for index in range(0, len(symbols), batch_size)]


def fetch_toss_price_batch(symbols: list[str], token: str) -> dict:
    query = urlencode({"symbols": ",".join(symbols)})
    request = Request(
        f"{TOSS_BASE_URL}/api/v1/prices?{query}",
        headers={"Authorization": f"Bearer {token}"},
        method="GET",
    )
    with urlopen(request, timeout=TOSS_REQUEST_TIMEOUT_SECONDS) as response:
        payload = json.loads(response.read().decode("utf-8"))
        write_raw_event("toss", "prices", payload, query=",".join(symbols), metadata={"symbolCount": len(symbols)})
        return payload


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
    merged_rows: list[dict] = []
    errors: list[dict] = []
    batches = symbol_batches(symbols, TOSS_PRICE_BATCH_SIZE)
    for batch in batches:
        try:
            payload = fetch_toss_price_batch(batch, token)
        except Exception as error:
            errors.append({
                "symbols": batch,
                "error": str(error)[:180],
            })
            continue
        merged_rows.extend(price_rows(payload))

    if not merged_rows and errors:
        raise RuntimeError(f"토스 가격 배치 조회 실패: {errors[0].get('error', 'unknown')}")

    payload = {
        "result": merged_rows,
        "metadata": {
            "requestedCount": len(symbols),
            "receivedCount": len(merged_rows),
            "batchSize": TOSS_PRICE_BATCH_SIZE,
            "batchCount": len(batches),
            "errorCount": len(errors),
            "errors": errors[:5],
        },
    }
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
        write_raw_event("toss", "candles", payload, symbol=symbol, metadata={"interval": interval, "count": count})
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
        write_raw_event("toss", "orderbook", payload, symbol=symbol)
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
        write_raw_event("toss", "trades", payload, symbol=symbol, metadata={"count": count})
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


def normalized_rate_percent(value: Decimal | None) -> Decimal | None:
    if value is None:
        return None
    return value * Decimal(100) if abs(value) <= Decimal("2") else value


def portfolio_position_label(profit_rate: Decimal | None, allocation_percent: Decimal | None) -> str:
    profit_percent = normalized_rate_percent(profit_rate)
    if allocation_percent is not None and allocation_percent >= Decimal("35"):
        return "비중 점검"
    if profit_percent is not None and profit_percent <= Decimal("-7"):
        return "손절 경계"
    if profit_percent is not None and profit_percent >= Decimal("12"):
        return "분할매도 검토"
    if profit_percent is not None and profit_percent <= Decimal("-3"):
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
    profit_percent = normalized_rate_percent(profit_rate)
    average_price = decimal_or_none(item.get("averagePurchasePrice"))
    return {
        "symbol": item.get("symbol", ""),
        "name": item.get("name", ""),
        "marketCountry": item.get("marketCountry", ""),
        "currency": currency,
        "quantity": item.get("quantity", "0"),
        "marketValueAmount": str(amount) if amount is not None else "",
        "lastPrice": money_display(item.get("lastPrice"), currency),
        "averagePurchasePrice": money_display(item.get("averagePurchasePrice"), currency),
        "averagePurchasePriceAmount": str(average_price) if average_price is not None else "",
        "marketValue": money_display(market_value.get("amount"), currency),
        "purchaseAmount": money_display(market_value.get("purchaseAmount"), currency),
        "profitLoss": money_display(profit_loss.get("amount"), currency),
        "profitLossRate": display_ratio_percent(profit_loss.get("rate")),
        "profitLossPercent": str(profit_percent.quantize(Decimal("0.01"))) if profit_percent is not None else "",
        "dailyProfitLossRate": display_ratio_percent(daily_profit_loss.get("rate")),
        "allocation": display_decimal_percent(allocation_percent) if allocation_percent is not None else "-",
        "allocationPercent": str(allocation_percent.quantize(Decimal("0.01"))) if allocation_percent is not None else "",
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


def safe_portfolio_status() -> dict:
    fallback = {
        "enabled": TOSS_LIVE_PORTFOLIO,
        "readOnly": True,
        "ready": bool(TOSS_LIVE_PORTFOLIO and (TOSS_ACCESS_TOKEN or (TOSS_CLIENT_ID and TOSS_CLIENT_SECRET))),
        "source": "unavailable",
        "message": "포트폴리오 정보를 후보 판단에 반영하지 못했습니다.",
        "accounts": [],
        "items": [],
        "summary": {},
        "buyingPower": {},
    }
    try:
        return portfolio_status()
    except Exception as error:
        return integration_failure_status(fallback, error, "포트폴리오 정보를 후보 판단에 반영하지 못했습니다.")


def normalized_match_text(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "")).lower()


def holding_lookup(portfolio: dict) -> tuple[dict[str, dict], dict[str, dict]]:
    by_symbol: dict[str, dict] = {}
    by_name: dict[str, dict] = {}
    for item in portfolio.get("items", []) if isinstance(portfolio, dict) else []:
        if not isinstance(item, dict):
            continue
        symbol = str(item.get("symbol", "")).strip().upper()
        name = normalized_match_text(str(item.get("name", "")))
        if symbol:
            by_symbol[symbol] = item
        if name:
            by_name[name] = item
    return by_symbol, by_name


def portfolio_currency_for_candidate(candidate: dict) -> str:
    market = str(candidate.get("market", "") or candidate.get("category", "")).lower()
    price = str(candidate.get("price", ""))
    symbol = str(candidate.get("symbol", ""))
    if "$" in price or market in {"us", "usa", "overseas", "global"} or symbol.isalpha():
        return "USD"
    return "KRW"


def portfolio_buying_power(portfolio: dict, currency: str) -> dict:
    buying_power = portfolio.get("buyingPower", {}) if isinstance(portfolio, dict) else {}
    item = buying_power.get(currency, {}) if isinstance(buying_power, dict) else {}
    cash_text = item.get("cashBuyingPower", "-") if isinstance(item, dict) else "-"
    cash_value = display_number_to_decimal(cash_text)
    return {
        "currency": currency,
        "cashBuyingPower": cash_text,
        "cashBuyingPowerAmount": str(cash_value) if cash_value is not None else "",
        "hasCash": cash_value is not None and cash_value > 0,
    }


def enrich_candidates_with_portfolio(candidates: list[dict], portfolio: dict) -> tuple[list[dict], dict]:
    by_symbol, by_name = holding_lookup(portfolio)
    enriched = []
    linked_count = 0
    for candidate in candidates:
        item = dict(candidate)
        symbol = str(item.get("symbol", "")).strip().upper()
        name = normalized_match_text(str(item.get("name", "")))
        holding = by_symbol.get(symbol) or by_name.get(name)
        currency = portfolio_currency_for_candidate(item)
        context = {
            "source": portfolio.get("source", "unavailable") if isinstance(portfolio, dict) else "unavailable",
            "isHeld": bool(holding),
            "currency": currency,
            "buyingPower": portfolio_buying_power(portfolio, currency),
        }
        if holding:
            linked_count += 1
            context["holding"] = holding
        item["portfolio"] = context
        enriched.append(item)

    return enriched, {
        "source": portfolio.get("source", "unavailable") if isinstance(portfolio, dict) else "unavailable",
        "enabled": bool(portfolio.get("enabled")) if isinstance(portfolio, dict) else False,
        "ready": bool(portfolio.get("ready")) if isinstance(portfolio, dict) else False,
        "message": portfolio.get("message", "포트폴리오 연결 상태를 확인했습니다.") if isinstance(portfolio, dict) else "포트폴리오 연결 상태를 확인했습니다.",
        "holdingCount": len(by_symbol),
        "linkedCandidateCount": linked_count,
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


def change_from_toss_price_row(price: dict) -> str | None:
    for key in [
        "fluctuationsRatio",
        "fluctuationRatio",
        "changeRatio",
        "changeRate",
        "changePercent",
        "regularMarketChangePercent",
    ]:
        value = decimal_or_none(price.get(key))
        if value is not None:
            return display_change(value)

    previous_close = decimal_or_none(
        price.get("previousClosePrice")
        or price.get("basePrice")
        or price.get("prevClosePrice")
        or price.get("regularMarketPreviousClose")
    )
    current = decimal_or_none(price.get("lastPrice"))
    if previous_close is None or current is None or previous_close == 0:
        return None
    return display_change(((current - previous_close) / previous_close) * Decimal(100))


def candles_from_market_data_record(record: dict) -> list[dict]:
    row = market_data_record_payload_row(record)
    if not isinstance(row, dict):
        return []

    candles = candle_rows(row)
    if candles:
        return candles

    result = row.get("result")
    if isinstance(result, dict):
        candles = result.get("candles")
        if isinstance(candles, list):
            return [item for item in candles if isinstance(item, dict)]

    for key in ("candles", "items", "data", "list"):
        rows = row.get(key)
        if isinstance(rows, list):
            return [item for item in rows if isinstance(item, dict)]
    return []


def stored_candle_change_for_candidate(
    candidate: dict,
    current_price: str,
    current_timestamp: str = "",
    candle_records: dict[str, dict] | None = None,
) -> tuple[str | None, dict]:
    symbol = str(candidate.get("symbol", "")).strip().upper()
    if not symbol:
        return None, {"source": "none", "message": "종목 코드가 없어 저장 캔들을 확인하지 못했습니다."}

    candle_records = candle_records if isinstance(candle_records, dict) else stored_market_data_latest_records("toss", "candles")
    record = candle_records.get(symbol)
    if not isinstance(record, dict):
        return None, {"source": "none", "message": "저장된 Toss 일봉 캔들이 없습니다."}

    candles = candles_from_market_data_record(record)
    if not candles:
        return None, {"source": "none", "message": "저장된 Toss 일봉 캔들이 비어 있습니다."}

    change = change_from_candles(current_price, candles, current_timestamp)
    if not change:
        return None, {"source": "none", "message": "저장된 Toss 일봉으로 등락률 기준가를 계산하지 못했습니다."}

    timestamp = market_data_record_timestamp(record)
    return change, {
        "source": "stored-toss-candles",
        "timestamp": timestamp,
        "message": "토스 현재가의 등락률이 비어 있어 서버에 저장된 Toss 일봉 기준가로 보강했습니다.",
    }


def seconds_since_timestamp(value: str | None) -> int | None:
    parsed = parse_iso_datetime(str(value or ""))
    if parsed is None:
        return None
    return max(0, int((datetime.now(KST) - parsed.astimezone(KST)).total_seconds()))


def us_eastern_datetime(now: datetime | None = None) -> datetime:
    base = now or datetime.now(KST)
    if base.tzinfo is None:
        base = base.replace(tzinfo=KST)
    if ZoneInfo is not None:
        try:
            return base.astimezone(ZoneInfo("America/New_York"))
        except Exception:
            pass
    dst_month = 3 <= base.astimezone(timezone.utc).month <= 11
    offset = -4 if dst_month else -5
    return base.astimezone(timezone(timedelta(hours=offset)))


def us_market_holiday_label(day) -> str:
    month_day = day.strftime("%m-%d")
    if month_day == "01-01":
        return "New Year's Day"
    if month_day == "06-19":
        return "Juneteenth"
    if month_day == "07-04":
        return "Independence Day"
    if month_day == "12-25":
        return "Christmas"
    return ""


def market_session_context(market: str = "", now: datetime | None = None) -> dict:
    normalized = str(market or "").strip().upper()
    current = now or datetime.now(KST)
    if current.tzinfo is None:
        current = current.replace(tzinfo=KST)
    if normalized in {"US", "NASDAQ", "NYSE", "AMEX", "ARCA", "BATS"}:
        eastern = us_eastern_datetime(current)
        minutes = eastern.hour * 60 + eastern.minute
        holiday = us_market_holiday_label(eastern.date())
        is_weekend = eastern.weekday() >= 5
        is_regular = not is_weekend and not holiday and (9 * 60 + 30) <= minutes < (16 * 60)
        if holiday:
            phase, label = "holiday", "미국장 휴장"
        elif is_weekend:
            phase, label = "closed", "미국장 휴장"
        elif minutes < 9 * 60 + 30:
            phase, label = "preopen", "미국장 개장 전"
        elif minutes >= 16 * 60:
            phase, label = "after_close", "미국장 마감 후"
        else:
            phase, label = "regular", "미국장 정규장"
        return {
            "market": "US",
            "phase": phase,
            "label": label,
            "isRegular": is_regular,
            "isClosedOrPreopen": not is_regular,
            "holiday": holiday,
            "timestamp": eastern.isoformat(timespec="seconds"),
        }
    kst_now = current.astimezone(KST)
    minutes = kst_now.hour * 60 + kst_now.minute
    is_weekend = kst_now.weekday() >= 5
    is_regular = not is_weekend and (9 * 60) <= minutes < (15 * 60 + 30)
    if is_weekend:
        phase, label = "closed", "국내장 휴장"
    elif minutes < 9 * 60:
        phase, label = "preopen", "국내장 개장 전"
    elif minutes >= 15 * 60 + 30:
        phase, label = "after_close", "국내장 마감 후"
    else:
        phase, label = "regular", "국내장 정규장"
    return {
        "market": normalized or "KR",
        "phase": phase,
        "label": label,
        "isRegular": is_regular,
        "isClosedOrPreopen": not is_regular,
        "holiday": "",
        "timestamp": kst_now.isoformat(timespec="seconds"),
    }


def live_price_freshness(live_price: dict | None, fallback_updated_at: str = "", market: str = "") -> dict:
    live_price = live_price if isinstance(live_price, dict) else {}
    source = str(live_price.get("source", "")).strip()
    timestamp = str(live_price.get("timestamp") or live_price.get("updatedAt") or fallback_updated_at or "").strip()
    age_seconds = seconds_since_timestamp(timestamp)
    session = market_session_context(market)
    closed_baseline_allowed = (
        source == "toss"
        and bool(live_price.get("lastPrice"))
        and bool(session.get("isClosedOrPreopen"))
        and (age_seconds is None or age_seconds <= SIGNAL_CLOSED_MARKET_BASELINE_MAX_AGE_SECONDS)
    )

    if source == "toss":
        if closed_baseline_allowed:
            status, label = "closed-baseline", "마감가 기준"
            session_reason = str(session.get("label") or "비정규 시간")
            message = f"{session_reason}이라 직전 정규장 마감가와 저장된 가격 기준으로 분석합니다. 실시간 진입 판단은 개장 후 확인하세요."
        elif age_seconds is None:
            status, label, message = "unknown", "시간 미확인", "토스 가격 시간이 없어 실시간 판단에 사용하지 않습니다."
        elif age_seconds <= SIGNAL_LIVE_PRICE_FRESH_SECONDS:
            status, label, message = "live", "실시간", "토스 현재가를 실시간 판단에 사용합니다."
        elif age_seconds <= SIGNAL_LIVE_PRICE_DELAYED_SECONDS:
            status, label, message = "delayed", "지연", "토스 현재가가 지연되어 신규 진입 판단을 보류합니다."
        else:
            status, label, message = "stale", "오래됨", "토스 현재가가 오래되어 저장 가격처럼만 참고합니다."
    elif source in {"sample", "seed", "lookup", "candidate_pool", "snapshot", "retained"}:
        status, label, message = "snapshot", "저장값", "저장된 가격이라 실시간 반응 판단에는 사용하지 않습니다."
    elif source:
        status, label, message = "missing", "미확인", str(live_price.get("message") or "실시간 가격을 확인하지 못했습니다.")
    else:
        status, label, message = "missing", "미확인", "실시간 가격 정보가 없습니다."

    return {
        "status": status,
        "label": label,
        "timestamp": timestamp,
        "ageSeconds": age_seconds,
        "freshSeconds": SIGNAL_LIVE_PRICE_FRESH_SECONDS,
        "delayedSeconds": SIGNAL_LIVE_PRICE_DELAYED_SECONDS,
        "isFresh": status == "live",
        "isDelayed": status == "delayed",
        "isStale": status in {"stale", "snapshot", "unknown", "missing"},
        "usableForReaction": status == "live",
        "usableForBaseline": status in {"live", "closed-baseline", "delayed"},
        "isClosedBaseline": status == "closed-baseline",
        "session": session,
        "message": message,
    }


def annotate_candidate_live_price_freshness(candidate: dict, fallback_updated_at: str = "") -> dict:
    item = dict(candidate)
    live_price = item.get("livePrice", {}) if isinstance(item.get("livePrice"), dict) else {}
    item["livePrice"] = {
        **live_price,
        "freshness": live_price_freshness(live_price, fallback_updated_at, str(item.get("market", ""))),
    }
    return item


def candidate_has_fresh_live_price(candidate: dict) -> bool:
    live_price = candidate.get("livePrice", {}) if isinstance(candidate.get("livePrice"), dict) else {}
    freshness = live_price.get("freshness") if isinstance(live_price.get("freshness"), dict) else live_price_freshness(live_price, market=str(candidate.get("market", "")))
    return str(live_price.get("source", "")) == "toss" and bool(freshness.get("usableForReaction"))


def candidate_has_usable_price_basis(candidate: dict) -> bool:
    live_price = candidate.get("livePrice", {}) if isinstance(candidate.get("livePrice"), dict) else {}
    freshness = live_price.get("freshness") if isinstance(live_price.get("freshness"), dict) else live_price_freshness(live_price, market=str(candidate.get("market", "")))
    if str(live_price.get("source", "")) == "toss" and live_price.get("lastPrice"):
        return bool(
            freshness.get("usableForBaseline")
            or freshness.get("usableForReaction")
            or str(freshness.get("status", "")) == "closed-baseline"
        )
    return display_number_to_decimal(candidate.get("price")) is not None


def live_price_freshness_counts(candidates: list[dict]) -> dict:
    counts = {"live": 0, "delayed": 0, "stale": 0, "snapshot": 0, "missing": 0, "unknown": 0}
    for candidate in candidates:
        live_price = candidate.get("livePrice", {}) if isinstance(candidate.get("livePrice"), dict) else {}
        freshness = live_price.get("freshness") if isinstance(live_price.get("freshness"), dict) else live_price_freshness(live_price, market=str(candidate.get("market", "")))
        status = str(freshness.get("status") or "unknown")
        if status not in counts:
            counts[status] = 0
        counts[status] += 1
    counts["fresh"] = counts.get("live", 0)
    counts["total"] = len(candidates)
    return counts


def retained_toss_live_price(candidate: dict, now_text: str) -> dict | None:
    live_price = candidate.get("livePrice", {}) if isinstance(candidate.get("livePrice"), dict) else {}
    if str(live_price.get("source", "")) != "toss":
        return None
    if not live_price.get("lastPrice"):
        return None
    retained = dict(live_price)
    retained.update({
        "retained": True,
        "missedInLastFetch": True,
        "message": "이번 토스 응답에 종목이 없어 직전 토스 현재가를 유지합니다.",
    })
    retained["freshness"] = live_price_freshness(retained, now_text, str(candidate.get("market", "")))
    return retained


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
    retained_count = 0
    stored_fallback_count = 0
    stored_candle_change_count = 0
    change_pending_count = 0
    missing_count = 0
    missing_symbols: list[str] = []
    now_text = datetime.now(KST).isoformat(timespec="seconds")
    price_metadata = payload.get("metadata", {}) if isinstance(payload.get("metadata"), dict) else {}
    stored_market_records = stored_market_data_latest_records("toss", "prices")
    stored_candle_records = stored_market_data_latest_records("toss", "candles")
    stored_candidate_records = stored_candidate_data_latest_records()
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
                "updatedAt": now_text,
                "source": "toss",
            }
            item["livePrice"]["freshness"] = live_price_freshness(item["livePrice"], now_text, str(item.get("market", "")))
            change = change_from_toss_price_row(price)
            change_source = "toss-prices" if change else ""
            if not change:
                candle_change, candle_status = stored_candle_change_for_candidate(
                    item,
                    str(price.get("lastPrice", "")),
                    str(price.get("timestamp") or now_text),
                    stored_candle_records,
                )
                if candle_change:
                    change = candle_change
                    change_source = str(candle_status.get("source") or "stored-toss-candles")
                    item["livePrice"]["changeMessage"] = str(candle_status.get("message") or "")
                    if candle_status.get("timestamp"):
                        item["livePrice"]["changeReferenceAt"] = str(candle_status.get("timestamp"))
                    stored_candle_change_count += 1
            if change:
                item["change"] = change
                item["livePrice"]["changeSource"] = change_source or "toss-prices"
            elif candidate_change_text_usable(item.get("change")):
                item["livePrice"]["changeSource"] = "retained-change"
                item["livePrice"]["changeMessage"] = "토스 현재가 응답에 등락률이 없어 서버에 저장된 직전 등락률을 유지합니다."
            else:
                item["livePrice"]["changeSource"] = "pending-change"
                item["livePrice"]["changeMessage"] = "현재가는 수신했지만 등락률 기준가를 서버에서 추가 확인 중입니다."
                change_pending_count += 1
            if baseline_warning and baseline_difference is not None:
                item["livePrice"].update({
                    "baselineWarning": True,
                    "baselineDifferencePercent": display_percent_abs(baseline_difference),
                    "samplePrice": candidate.get("price"),
                    "message": "초기 샘플 기준가와 차이가 커서 기준 데이터 갱신 여부를 확인하세요.",
                })
        else:
            retained_live_price = retained_toss_live_price(candidate, now_text)
            if retained_live_price:
                item["livePrice"] = retained_live_price
                retained_count += 1
            else:
                stored_live_price, stored_status = stored_live_price_for_candidate(
                    item,
                    stored_market_records,
                    stored_candidate_records,
                )
                if stored_live_price:
                    item["price"] = display_price(str(stored_live_price["lastPrice"]), str(stored_live_price["currency"]))
                    item["livePrice"] = {
                        **stored_live_price,
                        "missedInLastFetch": True,
                        "message": f"이번 토스 응답에는 없지만 {stored_status.get('message', '저장된 토스 가격을 유지합니다.')}",
                    }
                    stored_record = stored_candidate_records.get(str(item.get("symbol", "")).strip().upper(), {})
                    if not candidate_data_has_change(item) and candidate_data_has_change(stored_record):
                        item["change"] = stored_record.get("change", item.get("change", ""))
                        item["livePrice"]["changeSource"] = item["livePrice"].get("changeSource") or "stored-candidate-data"
                        item["livePrice"]["changeMessage"] = item["livePrice"].get("changeMessage") or "저장된 후보 데이터의 등락률을 유지합니다."
                    if not candidate_data_has_change(item) and stored_live_price.get("lastPrice"):
                        candle_change, candle_status = stored_candle_change_for_candidate(
                            item,
                            str(stored_live_price.get("lastPrice", "")),
                            str(stored_live_price.get("timestamp") or stored_status.get("timestamp") or now_text),
                            stored_candle_records,
                        )
                        if candle_change:
                            item["change"] = candle_change
                            item["livePrice"]["changeSource"] = str(candle_status.get("source") or "stored-toss-candles")
                            item["livePrice"]["changeMessage"] = str(candle_status.get("message") or "")
                            if candle_status.get("timestamp"):
                                item["livePrice"]["changeReferenceAt"] = str(candle_status.get("timestamp"))
                            stored_candle_change_count += 1
                    if not candidate_data_has_change(item):
                        change_pending_count += 1
                    stored_fallback_count += 1
                else:
                    item["livePrice"] = {
                        "source": "sample",
                        "updatedAt": now_text,
                        "message": "토스 현재가 응답과 서버 저장소 모두에서 종목 가격을 확인하지 못했습니다.",
                    }
                    item["livePrice"]["freshness"] = live_price_freshness(item["livePrice"], now_text, str(item.get("market", "")))
                    missing_count += 1
                    symbol = str(item.get("symbol", "")).strip().upper()
                    if symbol:
                        missing_symbols.append(symbol)
        enriched.append(item)

    return enriched, {
        "source": "toss",
        "enabled": True,
        "message": "토스증권 현재가를 반영했습니다.",
        "requestedCount": price_metadata.get("requestedCount", len(symbols)),
        "receivedCount": price_metadata.get("receivedCount", len(price_rows(payload))),
        "batchSize": price_metadata.get("batchSize", TOSS_PRICE_BATCH_SIZE),
        "batchCount": price_metadata.get("batchCount", 1),
        "batchErrorCount": price_metadata.get("errorCount", 0),
        "batchErrors": price_metadata.get("errors", []),
        "priceCount": len(prices),
        "retainedCount": retained_count,
        "storedFallbackCount": stored_fallback_count,
        "storedCandleChangeCount": stored_candle_change_count,
        "changePendingCount": change_pending_count,
        "missingCount": missing_count,
        "missingSymbols": unique_texts(missing_symbols, limit=20),
        "baselineDriftCount": baseline_drift_count,
        "sampleDriftThresholdPercent": (
            display_percent_abs(TOSS_SAMPLE_PRICE_DRIFT_WARN_PERCENT)
            if TOSS_SAMPLE_PRICE_DRIFT_WARN_PERCENT is not None
            else ""
        ),
        "updatedAt": now_text,
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

    def candle_fetch_priority(pair: tuple[int, dict]) -> tuple[int, int, int]:
        index, candidate = pair
        live_price = candidate.get("livePrice", {}) if isinstance(candidate.get("livePrice"), dict) else {}
        has_live_price = str(live_price.get("source", "")) == "toss" and bool(live_price.get("lastPrice"))
        change_missing = not candidate_data_has_change(candidate)
        has_candles = candidate_data_source_ok(candidate.get("liveCandles", {}))
        selected_boost = 0 if index == 0 else 1
        if has_live_price and change_missing:
            return (0, selected_boost, index)
        if has_live_price and not has_candles:
            return (1, selected_boost, index)
        if change_missing:
            return (2, selected_boost, index)
        return (3, selected_boost, index)

    priority_pairs = sorted(list(enumerate(candidates)), key=candle_fetch_priority)
    fetch_indexes = {
        index for index, _candidate in priority_pairs[: max(0, TOSS_CANDLE_MAX_CANDIDATES)]
    }
    enriched_by_index: dict[int, dict] = {}
    candle_count = 0
    stale_count = 0
    for index, candidate in enumerate(candidates):
        item = dict(candidate)
        if index not in fetch_indexes:
            item["liveCandles"] = {"source": "skipped", "message": "캔들 조회 후보 수 제한으로 샘플 차트를 사용합니다."}
            enriched_by_index[index] = item
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
                enriched_by_index[index] = item
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
        enriched_by_index[index] = item

    enriched = [enriched_by_index.get(index, dict(candidate)) for index, candidate in enumerate(candidates)]
    return enriched, {
        "source": "toss",
        "enabled": True,
        "message": "토스증권 일봉 캔들을 등락률 미확인 후보 우선으로 반영했습니다.",
        "candleCount": candle_count,
        "staleCount": stale_count,
        "prioritizedCount": len(fetch_indexes),
        "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
    }


def candidate_depth_fetch_priority(pair: tuple[int, dict], target_key: str) -> tuple[int, int, int, int, int]:
    index, candidate = pair
    live_price = candidate.get("livePrice", {}) if isinstance(candidate.get("livePrice"), dict) else {}
    has_live_price = str(live_price.get("source", "")) == "toss" and bool(live_price.get("lastPrice"))
    has_change = candidate_data_has_change(candidate)
    has_target = candidate_data_source_ok(candidate.get(target_key, {}))
    completeness = (
        candidate.get("dataCompleteness", {})
        if isinstance(candidate.get("dataCompleteness"), dict)
        else candidate_data_completeness(candidate)
    )
    missing_values = completeness.get("missing", []) if isinstance(completeness.get("missing"), list) else []
    missing_depth = "차트/호가/체결" in missing_values
    final_decision = candidate.get("finalDecision", {}) if isinstance(candidate.get("finalDecision"), dict) else {}
    decision_group = candidate.get("decisionGroup", {}) if isinstance(candidate.get("decisionGroup"), dict) else {}
    action_key = str(final_decision.get("actionKey", ""))
    group_key = str(decision_group.get("key", ""))
    score = bounded_int(candidate.get("totalScore", candidate.get("score", 0)), 0, 100)
    readiness = bounded_int(candidate.get("triggerReadiness", 0), 0, 100)
    urgent = group_key == "action" or action_key in {"buy", "add", "watch", "pullback"} or score >= 72 or readiness >= 70
    selected_boost = 0 if index == 0 else 1
    if has_live_price and has_change and missing_depth and not has_target:
        rank = 0
    elif has_live_price and missing_depth and not has_target:
        rank = 1
    elif urgent and not has_target:
        rank = 2
    elif not has_target:
        rank = 3
    else:
        rank = 4
    return (rank, selected_boost, -readiness, -score, index)


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

    priority_pairs = sorted(list(enumerate(candidates)), key=lambda pair: candidate_depth_fetch_priority(pair, "liveOrderbook"))
    fetch_indexes = {
        index for index, _candidate in priority_pairs[: max(0, TOSS_ORDERBOOK_MAX_CANDIDATES)]
    }
    enriched_by_index: dict[int, dict] = {}
    orderbook_count = 0
    skipped_count = 0
    for index, candidate in enumerate(candidates):
        item = dict(candidate)
        if index not in fetch_indexes:
            skipped_count += 1
            item["liveOrderbook"] = {"source": "skipped", "message": "호가 조회 후보 수 제한으로 샘플 지표를 사용합니다."}
            enriched_by_index[index] = item
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
        enriched_by_index[index] = item

    enriched = [enriched_by_index.get(index, dict(candidate)) for index, candidate in enumerate(candidates)]
    return enriched, {
        "source": "toss",
        "enabled": True,
        "message": "토스증권 호가를 미수신/진입 후보 우선으로 반영했습니다.",
        "orderbookCount": orderbook_count,
        "skippedCount": skipped_count,
        "prioritizedCount": len(fetch_indexes),
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

    priority_pairs = sorted(list(enumerate(candidates)), key=lambda pair: candidate_depth_fetch_priority(pair, "liveTrades"))
    fetch_indexes = {
        index for index, _candidate in priority_pairs[: max(0, TOSS_TRADES_MAX_CANDIDATES)]
    }
    enriched_by_index: dict[int, dict] = {}
    trade_count = 0
    skipped_count = 0
    for index, candidate in enumerate(candidates):
        item = dict(candidate)
        if index not in fetch_indexes:
            skipped_count += 1
            item["liveTrades"] = {"source": "skipped", "message": "체결 조회 후보 수 제한으로 샘플 지표를 사용합니다."}
            enriched_by_index[index] = item
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
        enriched_by_index[index] = item

    enriched = [enriched_by_index.get(index, dict(candidate)) for index, candidate in enumerate(candidates)]
    return enriched, {
        "source": "toss",
        "enabled": True,
        "message": "토스증권 최근 체결을 미수신/진입 후보 우선으로 반영했습니다.",
        "tradeCount": trade_count,
        "skippedCount": skipped_count,
        "prioritizedCount": len(fetch_indexes),
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


def clean_disclosure_text(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def dart_disclosure_freshness_days(value: object) -> int | None:
    text = re.sub(r"\D", "", str(value or ""))
    if len(text) != 8:
        return None
    try:
        received = datetime.strptime(text, "%Y%m%d").date()
    except ValueError:
        return None
    return max(0, (datetime.now(KST).date() - received).days)


def classify_dart_disclosure(report_name: object, received_date: object = "") -> dict:
    title = clean_disclosure_text(report_name)
    compact = re.sub(r"\s+", "", title).lower()
    warnings: list[str] = []

    def has_any(keywords: list[str]) -> bool:
        return any(keyword.lower() in compact for keyword in keywords)

    correction = has_any(["정정", "기재정정"])
    if correction:
        warnings.append("정정 공시이므로 원공시와 변경 내용을 함께 확인")

    key = "general"
    label = "일반 공시"
    tone = "neutral"
    importance = 45
    score_impact = 0
    risk_impact = 1
    reason = "공식 공시로 확인됐지만 방향성 영향은 별도 검증이 필요"

    if has_any(["거래정지", "상장폐지", "관리종목", "횡령", "배임", "회생", "파산", "감사의견거절", "의견거절", "불성실공시", "소송"]):
        key, label, tone = "critical_risk", "중대 리스크 공시", "risk"
        importance, score_impact, risk_impact = 94, -6, 12
        reason = "거래 지속성 또는 기업 신뢰도에 직접 영향을 줄 수 있는 공식 리스크"
    elif has_any(["유상증자", "전환사채", "신주인수권부사채", "교환사채", "cb", "bw", "감자"]):
        key, label, tone = "financing_risk", "자금조달/희석 공시", "risk"
        importance, score_impact, risk_impact = 84, -3, 8
        reason = "주식 희석 또는 단기 수급 부담으로 이어질 수 있는 공시"
    elif has_any(["최대주주변경", "주식등의대량보유", "임원ㆍ주요주주", "임원·주요주주", "자기주식처분"]):
        key, label, tone = "ownership_caution", "지분/수급 확인 공시", "caution"
        importance, score_impact, risk_impact = 68, 0, 4
        reason = "지분 변화와 수급 영향을 확인해야 하는 공식 공시"
    elif has_any(["단일판매", "공급계약", "수주", "계약체결"]):
        key, label, tone = "contract", "수주/계약 공시", "positive"
        importance, score_impact, risk_impact = 84, 5, 0
        reason = "매출 가시성이나 업황 기대를 높일 수 있는 공식 계약 공시"
    elif has_any(["자기주식취득", "자사주취득", "현금ㆍ현물배당", "현금·현물배당", "배당결정", "주주환원"]):
        key, label, tone = "shareholder_return", "주주환원 공시", "positive"
        importance, score_impact, risk_impact = 78, 4, 0
        reason = "주주환원 정책이 수급과 투자심리에 긍정적으로 작용할 수 있는 공시"
    elif has_any(["영업(잠정)실적", "잠정실적", "매출액또는손익구조", "실적", "매출액 또는 손익구조"]):
        key, label, tone = "earnings", "실적 공시", "positive"
        importance, score_impact, risk_impact = 72, 3, 1
        reason = "실적 변화가 밸류에이션 재평가로 연결될 수 있는 공식 공시"
    elif has_any(["신규시설투자", "투자판단관련주요경영사항", "타법인주식및출자증권취득"]):
        key, label, tone = "investment", "투자/전략 공시", "positive"
        importance, score_impact, risk_impact = 64, 2, 1
        reason = "중장기 성장 기대를 만들 수 있으나 투자 부담도 함께 확인해야 하는 공시"
    elif has_any(["사업보고서", "분기보고서", "반기보고서"]):
        key, label, tone = "periodic_report", "정기보고서", "neutral"
        importance, score_impact, risk_impact = 58, 1, 1
        reason = "재무와 사업 현황을 검증할 수 있는 정기 공식 자료"
    elif has_any(["조회공시", "풍문", "보도"]):
        key, label, tone = "rumor_check", "풍문/조회공시", "caution"
        importance, score_impact, risk_impact = 62, 0, 4
        reason = "뉴스성 재료의 사실 여부를 공식 답변으로 확인해야 하는 공시"

    freshness_days = dart_disclosure_freshness_days(received_date)
    if freshness_days is not None:
        if freshness_days <= 1:
            importance += 5
        elif freshness_days <= 3:
            importance += 2
        elif freshness_days > 7:
            importance -= 4

    if correction:
        risk_impact += 2
        importance += 2

    return {
        "eventKey": key,
        "eventLabel": label,
        "eventTone": tone,
        "eventImportance": bounded_int(importance, 0, 100),
        "scoreImpact": bounded_int(score_impact, -10, 10),
        "riskImpact": bounded_int(risk_impact, 0, 15),
        "freshnessDays": freshness_days,
        "officialReliability": 90 if not correction else 82,
        "reason": reason,
        "warnings": unique_texts(warnings, limit=3),
    }


def normalize_dart_disclosure(item: dict) -> dict:
    receipt_no = str(item.get("rcept_no", ""))
    report_name = str(item.get("report_nm", ""))
    received_date = item.get("rcept_dt")
    classification = classify_dart_disclosure(report_name, received_date)
    return {
        "corpName": item.get("corp_name"),
        "corpCode": item.get("corp_code"),
        "stockCode": item.get("stock_code"),
        "reportName": report_name,
        "receiptNo": receipt_no,
        "receivedDate": received_date,
        "filerName": item.get("flr_nm"),
        "corpClass": item.get("corp_cls"),
        "remark": item.get("rm"),
        "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={receipt_no}" if receipt_no else "",
        **classification,
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
    write_raw_event(
        "opendart",
        "disclosures",
        payload,
        symbol=symbol,
        metadata={"corpCode": corp["corpCode"], "lookbackDays": days, "normalizedItemCount": len(result["items"])},
    )
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


LIVE_STATE_CANDIDATE_FIELDS = [
    "symbol",
    "name",
    "market",
    "price",
    "change",
    "chart",
    "livePrice",
    "liveCandles",
    "liveOrderbook",
    "liveTrades",
    "trend",
    "priceReaction",
    "qualityGate",
    "finalDecision",
    "signalValidation",
    "dataConfidence",
    "sourceReliability",
    "dataCompleteness",
    "priceReadiness",
    "evaluationMode",
    "decisionGroup",
    "candidateCompression",
    "score",
    "totalScore",
    "triggerReadiness",
    "preopenPriority",
]


def live_state_empty() -> dict:
    return {"version": 1, "updatedAt": "", "items": {}}


def live_state_json_safe(value):
    if isinstance(value, dict):
        return {str(key): live_state_json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [live_state_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [live_state_json_safe(item) for item in value]
    if isinstance(value, (datetime, Decimal)):
        return str(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def live_state_data() -> dict:
    if not SIGNAL_LIVE_STATE_STORAGE_ENABLED:
        return live_state_empty()
    stored = db_read_kv(LIVE_STATE_KV_KEY, None) if database_storage_enabled() else None
    file_data = safe_read_json_file(LIVE_STATE_FILE)
    data = stored if isinstance(stored, dict) else file_data if isinstance(file_data, dict) else live_state_empty()
    if not isinstance(data, dict):
        return live_state_empty()
    items = data.get("items", {})
    if not isinstance(items, dict):
        data["items"] = {}
    return data


def live_state_write(data: dict) -> bool:
    if not SIGNAL_LIVE_STATE_STORAGE_ENABLED:
        return False
    payload = live_state_json_safe(data)
    if database_storage_enabled() and db_write_kv(LIVE_STATE_KV_KEY, payload):
        return True
    write_json(LIVE_STATE_FILE, payload)
    return True


def live_state_record_timestamp(record: dict) -> str:
    candidate = record.get("candidate", {}) if isinstance(record.get("candidate"), dict) else {}
    live_price = candidate.get("livePrice", {}) if isinstance(candidate.get("livePrice"), dict) else {}
    return str(
        live_price.get("timestamp")
        or live_price.get("updatedAt")
        or record.get("updatedAt")
        or ""
    )


def live_state_record_age_seconds(record: dict) -> int | None:
    parsed = parse_iso_datetime(live_state_record_timestamp(record))
    if parsed is None:
        return None
    return max(0, int((datetime.now(KST) - parsed.astimezone(KST)).total_seconds()))


def live_state_record_usable(record: dict) -> bool:
    if not isinstance(record, dict):
        return False
    candidate = record.get("candidate", {}) if isinstance(record.get("candidate"), dict) else {}
    live_price = candidate.get("livePrice", {}) if isinstance(candidate.get("livePrice"), dict) else {}
    if str(live_price.get("source", "")) != "toss" or not live_price.get("lastPrice"):
        return False
    age = live_state_record_age_seconds(record)
    return age is not None and age <= SIGNAL_LIVE_STATE_RETAIN_SECONDS


def live_state_record_from_candidate(candidate: dict, mode: str, now_text: str, previous: dict | None = None) -> dict | None:
    symbol = str(candidate.get("symbol", "")).strip().upper()
    if not symbol:
        return None
    live_price = candidate.get("livePrice", {}) if isinstance(candidate.get("livePrice"), dict) else {}
    if str(live_price.get("source", "")) != "toss" or not live_price.get("lastPrice"):
        return None
    previous = previous if isinstance(previous, dict) else {}
    candidate_payload = {
        key: copy.deepcopy(candidate[key])
        for key in LIVE_STATE_CANDIDATE_FIELDS
        if key in candidate
    }
    return {
        "symbol": symbol,
        "mode": mode,
        "updatedAt": now_text,
        "firstSeenAt": previous.get("firstSeenAt") or now_text,
        "observations": int(previous.get("observations", 0) or 0) + 1,
        "candidate": live_state_json_safe(candidate_payload),
    }


def trim_live_state_items(items: dict) -> dict:
    usable_items = {
        symbol: record
        for symbol, record in items.items()
        if isinstance(record, dict) and live_state_record_usable(record)
    }
    if len(usable_items) <= SIGNAL_LIVE_STATE_MAX_ITEMS:
        return usable_items
    ranked = sorted(
        usable_items.items(),
        key=lambda pair: str(pair[1].get("updatedAt", "")),
        reverse=True,
    )
    return dict(ranked[: max(1, SIGNAL_LIVE_STATE_MAX_ITEMS)])


def update_live_state_from_candidates(candidates: list[dict], mode: str) -> dict:
    if not SIGNAL_LIVE_STATE_STORAGE_ENABLED:
        return {"enabled": False, "storedCount": 0, "storage": "disabled"}
    now_text = datetime.now(KST).isoformat(timespec="seconds")
    with LIVE_STATE_LOCK:
        data = live_state_data()
        items = data.get("items", {}) if isinstance(data.get("items"), dict) else {}
        stored_count = 0
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            symbol = str(candidate.get("symbol", "")).strip().upper()
            record = live_state_record_from_candidate(candidate, mode, now_text, items.get(symbol))
            if record is None:
                continue
            items[symbol] = record
            stored_count += 1
        data["items"] = trim_live_state_items(items)
        data["updatedAt"] = now_text
        ok = live_state_write(data)
    return {
        "enabled": True,
        "stored": ok,
        "storedCount": stored_count,
        "retainedCount": len(data.get("items", {})) if isinstance(data.get("items"), dict) else 0,
        "storage": "postgres" if database_storage_enabled() else "filesystem",
        "updatedAt": now_text,
    }


def merge_live_state_into_candidates(candidates: list[dict], mode: str) -> tuple[list[dict], dict]:
    if not SIGNAL_LIVE_STATE_STORAGE_ENABLED:
        return candidates, {"enabled": False, "mergedCount": 0}
    data = live_state_data()
    items = data.get("items", {}) if isinstance(data.get("items"), dict) else {}
    merged: list[dict] = []
    merged_count = 0
    for candidate in candidates:
        if not isinstance(candidate, dict):
            merged.append(candidate)
            continue
        item = copy.deepcopy(candidate)
        symbol = str(item.get("symbol", "")).strip().upper()
        record = items.get(symbol)
        if live_state_record_usable(record):
            state_candidate = record.get("candidate", {}) if isinstance(record.get("candidate"), dict) else {}
            for key in LIVE_STATE_CANDIDATE_FIELDS:
                if key in state_candidate:
                    item[key] = copy.deepcopy(state_candidate[key])
            item["liveState"] = {
                "source": "stored-live-state",
                "mode": record.get("mode", ""),
                "updatedAt": record.get("updatedAt", ""),
                "ageSeconds": live_state_record_age_seconds(record),
                "message": "직전 토스 확정 상태를 먼저 반영했습니다.",
            }
            merged_count += 1
        merged.append(item)
    return merged, {
        "enabled": True,
        "source": "live_price_state",
        "mergedCount": merged_count,
        "retainedCount": len(items),
        "updatedAt": data.get("updatedAt", ""),
        "retainSeconds": SIGNAL_LIVE_STATE_RETAIN_SECONDS,
    }


def candidate_data_snapshot_empty() -> dict:
    return {"version": 1, "updatedAt": "", "items": {}, "summary": {}}


def candidate_data_snapshot_data() -> dict:
    if not SIGNAL_CANDIDATE_DATA_STORAGE_ENABLED:
        return candidate_data_snapshot_empty()
    stored = db_read_kv(CANDIDATE_DATA_KV_KEY, None) if database_storage_enabled() else None
    file_data = safe_read_json_file(CANDIDATE_DATA_FILE)
    data = stored if isinstance(stored, dict) else file_data if isinstance(file_data, dict) else candidate_data_snapshot_empty()
    if not isinstance(data, dict):
        return candidate_data_snapshot_empty()
    if not isinstance(data.get("items"), dict):
        data["items"] = {}
    if not isinstance(data.get("summary"), dict):
        data["summary"] = {}
    return data


def candidate_data_snapshot_write(data: dict) -> tuple[bool, str]:
    if not SIGNAL_CANDIDATE_DATA_STORAGE_ENABLED:
        return False, "disabled"
    payload = live_state_json_safe(data)
    if database_storage_enabled() and db_write_kv(CANDIDATE_DATA_KV_KEY, payload):
        return True, "postgres"
    write_json(CANDIDATE_DATA_FILE, payload)
    return True, "filesystem-fallback" if database_storage_enabled() else "filesystem"


def candidate_data_source_ok(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    source = str(value.get("source", "")).strip().lower()
    if source in {"toss", "naver", "opendart", "openai"}:
        return True
    if source in {"retained", "stored-live-state"}:
        return True
    if source in {"sample", "seed", "skipped", "not-applicable", "disabled", "error"}:
        return False
    return bool(source and source not in {"-", "none", "missing"})


def candidate_change_text_usable(change: object) -> bool:
    text = str(change or "").strip()
    if not text or text in {"-", "미수신", "확인 대기"}:
        return False
    if text.lower() in {"n/a", "na", "none"}:
        return False
    return True


def candidate_data_has_change(candidate: dict) -> bool:
    if not candidate_change_text_usable(candidate.get("change")):
        return False
    live_price = candidate.get("livePrice", {}) if isinstance(candidate.get("livePrice"), dict) else {}
    if str(live_price.get("changeSource", "")).lower() == "missing":
        return False
    return True


def candidate_data_completeness(candidate: dict) -> dict:
    live_price = candidate.get("livePrice", {}) if isinstance(candidate.get("livePrice"), dict) else {}
    live_candles = candidate.get("liveCandles", {}) if isinstance(candidate.get("liveCandles"), dict) else {}
    live_orderbook = candidate.get("liveOrderbook", {}) if isinstance(candidate.get("liveOrderbook"), dict) else {}
    live_trades = candidate.get("liveTrades", {}) if isinstance(candidate.get("liveTrades"), dict) else {}
    try:
        news_items = compact_live_news(candidate)
    except Exception:
        news_items = []
    try:
        disclosure_items = compact_live_disclosures(candidate)
    except Exception:
        disclosure_items = []
    trend = candidate.get("trend", {}) if isinstance(candidate.get("trend"), dict) else {}
    news_count = len(news_items) or bounded_int(trend.get("newsCount", 0), 0, 999999)
    disclosure_count = len(disclosure_items)
    live_price_ok = candidate_has_fresh_live_price(candidate)
    price_ok = candidate_has_usable_price_basis(candidate)
    change_ok = price_ok and candidate_data_has_change(candidate)
    candle_ok = candidate_data_source_ok(live_candles)
    orderbook_ok = candidate_data_source_ok(live_orderbook)
    trade_ok = candidate_data_source_ok(live_trades)
    material_ok = news_count > 0 or disclosure_count > 0
    reaction_ready = live_price_ok and change_ok and (candle_ok or orderbook_ok or trade_ok)
    display_ready = price_ok and change_ok and material_ok
    entry_ready = display_ready and reaction_ready
    missing = []
    if not price_ok:
        missing.append("가격 기준")
    if not change_ok:
        missing.append("등락률")
    if not material_ok:
        missing.append("뉴스/공시")
    if not (candle_ok or orderbook_ok or trade_ok):
        missing.append("차트/호가/체결")
    status = "entry_ready" if entry_ready else "display_ready" if display_ready else "collecting"
    return {
        "status": status,
        "label": {
            "entry_ready": "진입 데이터 준비",
            "display_ready": "후보 데이터 준비",
            "collecting": "수집 중",
        }[status],
        "priceOk": price_ok,
        "changeOk": change_ok,
        "candleOk": candle_ok,
        "orderbookOk": orderbook_ok,
        "tradeOk": trade_ok,
        "materialOk": material_ok,
        "reactionReady": reaction_ready,
        "displayReady": display_ready,
        "entryReady": entry_ready,
        "newsCount": news_count,
        "disclosureCount": disclosure_count,
        "missing": unique_texts(missing, limit=8),
        "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
        "freshness": live_price_freshness(live_price, str(candidate.get("updated", "")), str(candidate.get("market", ""))),
    }


def candidate_price_readiness(candidate: dict) -> dict:
    completeness = candidate.get("dataCompleteness", {}) if isinstance(candidate.get("dataCompleteness"), dict) else candidate_data_completeness(candidate)
    freshness = completeness.get("freshness", {}) if isinstance(completeness.get("freshness"), dict) else {}
    missing = completeness.get("missing", []) if isinstance(completeness.get("missing"), list) else []
    price_ok = bool(completeness.get("priceOk"))
    change_ok = bool(completeness.get("changeOk"))
    display_ready = bool(completeness.get("displayReady"))
    entry_ready = bool(completeness.get("entryReady"))
    status = str(freshness.get("status", "missing"))
    if entry_ready:
        key, label, message = "entry_ready", "실시간 평가 가능", "가격·등락률·거래 반응 데이터가 모두 확인되었습니다."
    elif display_ready and status == "closed-baseline":
        key, label, message = "closed_baseline", "마감가 기준", "직전 정규장 가격 기준은 확보됐지만 실시간 진입은 개장 후 확인합니다."
    elif display_ready:
        key, label, message = "display_ready", "후보 분석 가능", "가격 기준은 있으나 차트·호가·체결 반응 보강 전까지 진입 후보로 올리지 않습니다."
    elif price_ok and not change_ok:
        key, label, message = "change_wait", "등락률 수집 중", "현재가는 있으나 등락률이 없어 서버 보강 전까지 가격 반응 판단을 보류합니다."
    elif not price_ok:
        key, label, message = "price_wait", "가격 수집 중", "현재가 또는 마감가 기준이 없어 서버 보강 전까지 후보 평가를 보류합니다."
    else:
        key, label, message = "collecting", "서버 수집 중", "가격·뉴스·공시 데이터를 수집한 뒤 판단합니다."
    return {
        "key": key,
        "label": label,
        "message": message,
        "priceOk": price_ok,
        "changeOk": change_ok,
        "displayReady": display_ready,
        "entryReady": entry_ready,
        "freshnessStatus": status,
        "missing": unique_texts(missing, limit=8),
    }


def candidate_evaluation_mode(candidate: dict) -> dict:
    readiness = candidate.get("priceReadiness", {}) if isinstance(candidate.get("priceReadiness"), dict) else candidate_price_readiness(candidate)
    completeness = candidate.get("dataCompleteness", {}) if isinstance(candidate.get("dataCompleteness"), dict) else candidate_data_completeness(candidate)
    key = str(readiness.get("key", "collecting"))
    missing = unique_texts(readiness.get("missing", []) if isinstance(readiness.get("missing"), list) else [], limit=6)
    base = {
        "entry_ready": {
            "key": "entry_ready",
            "label": "실시간 평가 가능",
            "status": "ready",
            "message": "서버가 가격·등락률·거래 반응을 확보해 진입 판단에 사용할 수 있습니다.",
            "tradeEligible": True,
            "rankEligible": True,
        },
        "closed_baseline": {
            "key": "closed_baseline",
            "label": "장마감 기준",
            "status": "baseline",
            "message": "직전 정규장 가격 기준으로 분석합니다. 신규 진입은 개장 후 실시간 반응을 확인합니다.",
            "tradeEligible": False,
            "rankEligible": True,
        },
        "display_ready": {
            "key": "display_ready",
            "label": "후보 분석 가능",
            "status": "analysis",
            "message": "가격과 재료는 확보됐지만 차트·호가·체결 보강 전까지 진입 후보로 올리지 않습니다.",
            "tradeEligible": False,
            "rankEligible": True,
        },
        "change_wait": {
            "key": "collecting_change",
            "label": "등락률 수집 중",
            "status": "collecting",
            "message": "현재가는 들어왔지만 등락률 기준이 없어 서버가 전일 대비와 기준가를 보강 중입니다.",
            "tradeEligible": False,
            "rankEligible": False,
        },
        "price_wait": {
            "key": "collecting_price",
            "label": "가격 수집 중",
            "status": "collecting",
            "message": "현재가 또는 마감가 기준이 없어 서버가 토스 시세를 다시 수집 중입니다.",
            "tradeEligible": False,
            "rankEligible": False,
        },
        "collecting": {
            "key": "collecting",
            "label": "서버 수집 중",
            "status": "collecting",
            "message": "가격·뉴스·공시 중 필수 데이터가 부족해 서버 보강 후 평가합니다.",
            "tradeEligible": False,
            "rankEligible": False,
        },
    }.get(key, {
        "key": "unavailable",
        "label": "평가 불가",
        "status": "blocked",
        "message": "필수 데이터가 부족해 현재 후보 평가는 참고용으로만 표시합니다.",
        "tradeEligible": False,
        "rankEligible": False,
    })
    mode = dict(base)
    mode["sourceKey"] = key
    mode["missing"] = missing
    mode["priceOk"] = bool(completeness.get("priceOk"))
    mode["changeOk"] = bool(completeness.get("changeOk"))
    mode["displayReady"] = bool(completeness.get("displayReady"))
    mode["entryReady"] = bool(completeness.get("entryReady"))
    if missing and mode["status"] == "collecting":
        mode["message"] = f"{', '.join(missing[:4])} 보강 후 평가합니다."
    return mode


def candidate_trade_data_gate(candidate: dict) -> dict:
    completeness = candidate.get("dataCompleteness", {}) if isinstance(candidate.get("dataCompleteness"), dict) else candidate_data_completeness(candidate)
    readiness = candidate.get("priceReadiness", {}) if isinstance(candidate.get("priceReadiness"), dict) else candidate_price_readiness(candidate)
    evaluation = candidate.get("evaluationMode", {}) if isinstance(candidate.get("evaluationMode"), dict) else candidate_evaluation_mode(candidate)
    missing = unique_texts(
        completeness.get("missing", []) if isinstance(completeness.get("missing"), list) else [],
        limit=8,
    )
    display_ready = bool(completeness.get("displayReady"))
    entry_ready = bool(completeness.get("entryReady"))
    trade_ready = bool(entry_ready and evaluation.get("tradeEligible"))
    rank_ready = bool(display_ready and evaluation.get("rankEligible"))
    readiness_key = str(readiness.get("key", "collecting"))
    closed_baseline = readiness_key == "closed_baseline"
    if trade_ready:
        label = "실시간 진입 검증 완료"
        reason = "서버가 가격·등락률·거래 반응을 모두 확보했습니다."
    elif closed_baseline:
        label = "장마감 기준 관찰"
        reason = "직전 정규장 가격 기준은 확보됐지만 신규 진입은 개장 후 실시간 반응을 확인합니다."
    elif display_ready:
        label = "반응 검증 대기"
        reason = "가격과 재료는 확보됐지만 차트·호가·체결 반응 보강 전까지 진입 후보로 올리지 않습니다."
    else:
        label = str(readiness.get("label") or evaluation.get("label") or "서버 수집 중")
        reason = str(evaluation.get("message") or readiness.get("message") or "필수 데이터를 서버에서 보강 중입니다.")
    return {
        "tradeReady": trade_ready,
        "rankReady": rank_ready,
        "displayReady": display_ready,
        "entryReady": entry_ready,
        "closedBaseline": closed_baseline,
        "readinessKey": readiness_key,
        "evaluationKey": evaluation.get("key", ""),
        "label": label,
        "reason": reason,
        "missing": missing,
    }


def candidate_data_snapshot_record(candidate: dict, mode: str, stage: str, now_text: str) -> dict | None:
    symbol = str(candidate.get("symbol", "")).strip().upper()
    if not symbol:
        return None
    completeness = candidate_data_completeness(candidate)
    candidate["dataCompleteness"] = completeness
    return {
        "symbol": symbol,
        "name": candidate.get("name", ""),
        "market": candidate.get("market", ""),
        "category": candidate.get("category", ""),
        "mode": mode,
        "stage": stage,
        "collectedAt": now_text,
        "price": candidate.get("price", ""),
        "change": candidate.get("change", ""),
        "updated": candidate.get("updated", ""),
        "totalScore": candidate.get("totalScore", 0),
        "triggerReadiness": candidate.get("triggerReadiness", 0),
        "preopenPriority": candidate.get("preopenPriority", 0),
        "score": compact_raw_payload(candidate.get("score", {}), list_limit=20),
        "priceReadiness": compact_raw_payload(candidate_price_readiness(candidate), list_limit=20),
        "evaluationMode": compact_raw_payload(candidate_evaluation_mode(candidate), list_limit=20),
        "livePrice": compact_raw_payload(candidate.get("livePrice", {}), list_limit=20),
        "liveCandles": compact_raw_payload(candidate.get("liveCandles", {}), list_limit=20),
        "liveOrderbook": compact_raw_payload(candidate.get("liveOrderbook", {}), list_limit=20),
        "liveTrades": compact_raw_payload(candidate.get("liveTrades", {}), list_limit=20),
        "liveNews": compact_live_news(candidate),
        "liveDisclosures": compact_live_disclosures(candidate),
        "priceReaction": compact_raw_payload(candidate.get("priceReaction", {}), list_limit=20),
        "qualityGate": compact_raw_payload(candidate.get("qualityGate", {}), list_limit=20),
        "finalDecision": compact_raw_payload(candidate.get("finalDecision", {}), list_limit=20),
        "signalValidation": compact_raw_payload(candidate.get("signalValidation", {}), list_limit=20),
        "candidateCompression": compact_raw_payload(candidate.get("candidateCompression", {}), list_limit=20),
        "sourceReliability": compact_raw_payload(candidate.get("sourceReliability", {}), list_limit=20),
        "dataConfidence": compact_raw_payload(candidate.get("dataConfidence", {}), list_limit=20),
        "dataCompleteness": completeness,
    }


def carry_forward_candidate_data_record(record: dict, previous: dict) -> tuple[dict, list[str]]:
    if not isinstance(record, dict) or not isinstance(previous, dict):
        return record, []
    previous_latest = previous.get("latest", {}) if isinstance(previous.get("latest"), dict) else {}
    if not previous_latest:
        return record, []

    carried: list[str] = []
    if not candidate_has_toss_last_price(record) and candidate_has_toss_last_price(previous_latest):
        for key in ("price", "updated", "livePrice"):
            if key in previous_latest:
                record[key] = copy.deepcopy(previous_latest[key])
        if isinstance(record.get("livePrice"), dict):
            record["livePrice"] = {
                **record["livePrice"],
                "retained": True,
                "dataSource": record["livePrice"].get("dataSource") or "candidate_data_snapshots",
                "message": "이번 수집에서 가격이 누락되어 서버에 저장된 직전 유효 토스 가격을 유지합니다.",
            }
        carried.append("price")

    if not candidate_data_has_change(record) and candidate_data_has_change(previous_latest):
        record["change"] = previous_latest.get("change", record.get("change", ""))
        previous_live_price = previous_latest.get("livePrice", {}) if isinstance(previous_latest.get("livePrice"), dict) else {}
        if isinstance(record.get("livePrice"), dict):
            record["livePrice"] = {
                **record["livePrice"],
                "retainedChange": True,
                "changeSource": previous_live_price.get("changeSource") or "stored-candidate-data",
                "changeMessage": "이번 수집에서 등락률이 누락되어 서버에 저장된 직전 등락률을 유지합니다.",
            }
        carried.append("change")

    for key in ("liveCandles", "liveOrderbook", "liveTrades"):
        current_value = record.get(key, {}) if isinstance(record.get(key), dict) else {}
        previous_value = previous_latest.get(key, {}) if isinstance(previous_latest.get(key), dict) else {}
        if not candidate_data_source_ok(current_value) and candidate_data_source_ok(previous_value):
            record[key] = copy.deepcopy(previous_value)
            carried.append(key)

    if carried:
        record["carriedForward"] = unique_texts(carried, limit=8)
        record["dataCompleteness"] = candidate_data_completeness(record)
    return record, unique_texts(carried, limit=8)


def trim_candidate_data_items(items: dict) -> dict:
    if len(items) <= SIGNAL_CANDIDATE_DATA_MAX_ITEMS:
        return items
    ranked = sorted(
        items.items(),
        key=lambda pair: str(pair[1].get("latestAt", "")) if isinstance(pair[1], dict) else "",
        reverse=True,
    )
    return dict(ranked[: max(1, SIGNAL_CANDIDATE_DATA_MAX_ITEMS)])


def update_candidate_data_snapshots(candidates: list[dict], mode: str, stage: str = "selected") -> dict:
    if not SIGNAL_CANDIDATE_DATA_STORAGE_ENABLED:
        return {"enabled": False, "storedCount": 0, "storage": "disabled", "message": "후보 데이터 저장이 꺼져 있습니다."}
    now_text = datetime.now(KST).isoformat(timespec="seconds")
    with CANDIDATE_DATA_LOCK:
        data = candidate_data_snapshot_data()
        items = data.get("items", {}) if isinstance(data.get("items"), dict) else {}
        stored_count = 0
        display_ready_count = 0
        entry_ready_count = 0
        carried_forward_count = 0
        carried_forward_fields: dict[str, int] = {}
        missing_counts: dict[str, int] = {}
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            record = candidate_data_snapshot_record(candidate, mode, stage, now_text)
            if record is None:
                continue
            symbol = str(record["symbol"])
            previous = items.get(symbol, {}) if isinstance(items.get(symbol), dict) else {}
            record, carried_fields = carry_forward_candidate_data_record(record, previous)
            if carried_fields:
                carried_forward_count += 1
                for key in carried_fields:
                    carried_forward_fields[str(key)] = carried_forward_fields.get(str(key), 0) + 1
            completeness = record.get("dataCompleteness", {}) if isinstance(record.get("dataCompleteness"), dict) else {}
            if completeness.get("displayReady"):
                display_ready_count += 1
            if completeness.get("entryReady"):
                entry_ready_count += 1
            for key in (completeness.get("missing", []) if isinstance(completeness.get("missing"), list) else []):
                missing_counts[str(key)] = missing_counts.get(str(key), 0) + 1
            history = previous.get("history", []) if isinstance(previous.get("history"), list) else []
            history = [*history, record][-max(1, SIGNAL_CANDIDATE_DATA_HISTORY_LIMIT):]
            items[symbol] = {
                "symbol": symbol,
                "name": record.get("name", ""),
                "market": record.get("market", ""),
                "mode": mode,
                "latestAt": now_text,
                "firstSeenAt": previous.get("firstSeenAt") or now_text,
                "observations": int(previous.get("observations", 0) or 0) + 1,
                "carriedForwardCount": int(previous.get("carriedForwardCount", 0) or 0) + (1 if carried_fields else 0),
                "latest": record,
                "history": history,
            }
            stored_count += 1
        data["items"] = trim_candidate_data_items(items)
        data["updatedAt"] = now_text
        data["summary"] = {
            "storedCount": stored_count,
            "itemCount": len(data["items"]),
            "displayReadyCount": display_ready_count,
            "entryReadyCount": entry_ready_count,
            "carriedForwardCount": carried_forward_count,
            "carriedForwardFields": carried_forward_fields,
            "missingCounts": missing_counts,
            "mode": mode,
            "stage": stage,
            "updatedAt": now_text,
        }
        ok, storage = candidate_data_snapshot_write(data)
    return {
        "enabled": True,
        "stored": ok,
        "storage": storage,
        "storedCount": stored_count,
        "itemCount": len(data.get("items", {})) if isinstance(data.get("items"), dict) else 0,
        "displayReadyCount": display_ready_count,
        "entryReadyCount": entry_ready_count,
        "carriedForwardCount": carried_forward_count,
        "carriedForwardFields": carried_forward_fields,
        "missingCounts": missing_counts,
        "updatedAt": now_text,
        "message": f"후보 {stored_count}개 데이터 묶음을 저장했습니다.",
    }


def candidate_data_snapshot_status() -> dict:
    if not SIGNAL_CANDIDATE_DATA_STORAGE_ENABLED:
        return {"enabled": False, "storage": "disabled", "itemCount": 0, "message": "후보 데이터 저장이 꺼져 있습니다."}
    data = candidate_data_snapshot_data()
    items = data.get("items", {}) if isinstance(data.get("items"), dict) else {}
    summary = data.get("summary", {}) if isinstance(data.get("summary"), dict) else {}
    probe = kv_payload_read_probe(CANDIDATE_DATA_KV_KEY, CANDIDATE_DATA_FILE)
    storage = probe["readSource"]
    persistent = storage == "postgres"
    if persistent:
        message = "후보별 최신 수신 데이터 묶음을 Postgres DB에서 읽고 업데이트합니다."
    elif probe["databaseReady"] and probe["fileItemCount"] > 0:
        message = "DB는 연결됐지만 후보 데이터 묶음이 아직 DB에 없어 파일 fallback을 읽고 있습니다. 다음 수집 또는 DB 이관 후 DB 기준으로 전환됩니다."
    elif probe["databaseReady"]:
        message = "DB는 연결됐지만 후보 데이터 묶음이 아직 저장되지 않았습니다. 다음 후보 수집에서 DB에 저장됩니다."
    elif probe["databaseConfigured"]:
        message = "DB 연결 또는 스키마 확인에 실패해 후보 데이터 묶음을 파일 fallback으로 읽습니다."
    else:
        message = "후보별 최신 수신 데이터 묶음이 임시 파일 저장소에 저장됩니다. 운영 기준 저장소는 아직 미완료입니다."
    return {
        "enabled": True,
        "storage": storage,
        "file": display_local_path(CANDIDATE_DATA_FILE),
        "readSource": probe["readSource"],
        "databaseConfigured": probe["databaseConfigured"],
        "databaseReady": probe["databaseReady"],
        "databaseError": probe["databaseError"],
        "dbItemCount": probe["dbItemCount"],
        "fileItemCount": probe["fileItemCount"],
        "fileExists": probe["fileExists"],
        "writeFallback": probe["writeFallback"],
        "operationReady": persistent and len(items) > 0,
        "persistent": persistent,
        "volatileFallback": not persistent,
        "itemCount": len(items),
        "storedCount": summary.get("storedCount", 0),
        "displayReadyCount": summary.get("displayReadyCount", 0),
        "entryReadyCount": summary.get("entryReadyCount", 0),
        "carriedForwardCount": summary.get("carriedForwardCount", 0),
        "carriedForwardFields": summary.get("carriedForwardFields", {}),
        "missingCounts": summary.get("missingCounts", {}),
        "latestAt": data.get("updatedAt", ""),
        "message": message,
    }


def candidate_data_record_timestamp(record: dict) -> str:
    if not isinstance(record, dict):
        return ""
    live_price = record.get("livePrice", {}) if isinstance(record.get("livePrice"), dict) else {}
    return str(
        live_price.get("timestamp")
        or live_price.get("updatedAt")
        or record.get("collectedAt")
        or ""
    )


def candidate_data_record_age_seconds(record: dict) -> int | None:
    parsed = parse_iso_datetime(candidate_data_record_timestamp(record))
    if parsed is None:
        return None
    return max(0, int((datetime.now(KST) - parsed.astimezone(KST)).total_seconds()))


def candidate_has_toss_last_price(candidate: dict) -> bool:
    live_price = candidate.get("livePrice", {}) if isinstance(candidate.get("livePrice"), dict) else {}
    return str(live_price.get("source", "")) == "toss" and bool(live_price.get("lastPrice"))


def stored_candidate_data_latest_records() -> dict[str, dict]:
    data = candidate_data_snapshot_data()
    items = data.get("items", {}) if isinstance(data.get("items"), dict) else {}
    records: dict[str, dict] = {}
    for symbol, item in items.items():
        if not isinstance(item, dict):
            continue
        latest = item.get("latest", {}) if isinstance(item.get("latest"), dict) else {}
        if not latest:
            continue
        normalized = str(latest.get("symbol") or symbol).strip().upper()
        if normalized:
            records[normalized] = latest
    return records


def merge_candidate_data_snapshots_into_candidates(candidates: list[dict], mode: str = "") -> tuple[list[dict], dict]:
    if not SIGNAL_CANDIDATE_DATA_STORAGE_ENABLED:
        return candidates, {"enabled": False, "mergedCount": 0, "message": "후보 데이터 저장이 꺼져 있습니다."}
    records = stored_candidate_data_latest_records()
    if not records:
        return candidates, {"enabled": True, "mergedCount": 0, "message": "저장된 후보 데이터가 아직 없습니다."}

    merged: list[dict] = []
    merged_count = 0
    price_merged_count = 0
    change_merged_count = 0
    depth_merged_count = 0
    for candidate in candidates:
        if not isinstance(candidate, dict):
            merged.append(candidate)
            continue
        item = copy.deepcopy(candidate)
        symbol = str(item.get("symbol", "")).strip().upper()
        record = records.get(symbol)
        if not record:
            merged.append(item)
            continue

        has_current_price = candidate_has_toss_last_price(item)
        record_live_price = record.get("livePrice", {}) if isinstance(record.get("livePrice"), dict) else {}
        has_record_price = str(record_live_price.get("source", "")) == "toss" and bool(record_live_price.get("lastPrice"))
        current_live_price = item.get("livePrice", {}) if isinstance(item.get("livePrice"), dict) else {}
        current_timestamp = str(current_live_price.get("timestamp") or current_live_price.get("updatedAt") or "")
        record_timestamp = candidate_data_record_timestamp(record)
        record_is_newer = bool(record_timestamp and timestamp_is_newer(record_timestamp, current_timestamp))
        if has_record_price and (not has_current_price or record_is_newer):
            for key in ("price", "updated", "livePrice"):
                if key in record:
                    item[key] = copy.deepcopy(record[key])
            price_merged_count += 1

        if candidate_data_has_change(record) and (not candidate_data_has_change(item) or record_is_newer):
            item["change"] = record.get("change", item.get("change", ""))
            if isinstance(item.get("livePrice"), dict) and isinstance(record_live_price, dict):
                item["livePrice"] = {
                    **item["livePrice"],
                    "changeSource": record_live_price.get("changeSource") or "stored-candidate-data",
                    "changeMessage": record_live_price.get("changeMessage") or "저장된 후보 데이터의 등락률을 유지합니다.",
                }
            change_merged_count += 1

        for key in ("liveCandles", "liveOrderbook", "liveTrades"):
            current_value = item.get(key, {}) if isinstance(item.get(key), dict) else {}
            record_value = record.get(key, {}) if isinstance(record.get(key), dict) else {}
            if not candidate_data_source_ok(current_value) and candidate_data_source_ok(record_value):
                item[key] = copy.deepcopy(record_value)
                depth_merged_count += 1

        for key in ("trend", "priceReaction", "qualityGate", "finalDecision", "signalValidation", "candidateCompression", "sourceReliability", "dataConfidence", "dataCompleteness"):
            if key not in item and key in record:
                item[key] = copy.deepcopy(record[key])
        if isinstance(record.get("finalDecision"), dict):
            item["storedFinalDecision"] = copy.deepcopy(record["finalDecision"])
        for key in ("liveNews", "liveDisclosures"):
            if not item.get(key) and record.get(key):
                item[key] = copy.deepcopy(record[key])

        item["candidateDataSnapshot"] = {
            "source": "candidate_data_snapshots",
            "mode": record.get("mode", ""),
            "stage": record.get("stage", ""),
            "collectedAt": record.get("collectedAt", ""),
            "ageSeconds": candidate_data_record_age_seconds(record),
            "message": "서버에 저장된 후보별 최종 수신값을 우선 반영했습니다.",
        }
        merged_count += 1
        merged.append(item)

    return merged, {
        "enabled": True,
        "source": "candidate_data_snapshots",
        "mergedCount": merged_count,
        "priceMergedCount": price_merged_count,
        "changeMergedCount": change_merged_count,
        "depthMergedCount": depth_merged_count,
        "retainedCount": len(records),
        "message": f"저장된 후보 데이터 {merged_count}개를 후보 판단에 반영했습니다.",
    }


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
    write_raw_event(
        "naver",
        "news",
        payload,
        query=query,
        metadata={"display": display, "start": start, "sort": sort, "itemCount": len(payload.get("items", []))},
    )
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
    relevance = item.get("relevance", {}) if isinstance(item.get("relevance"), dict) else {}
    return {
        "title": item.get("title", ""),
        "publisher": host,
        "time": time_text,
        "url": item.get("newsUrl") or item.get("naverUrl") or item.get("originalUrl") or "",
        "relevanceScore": relevance.get("score"),
        "relevanceLabel": relevance.get("label", ""),
        "impactTypes": relevance.get("impactTypes", []),
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
    write_raw_event(
        "gdelt",
        "news",
        payload,
        query=query,
        metadata={"display": display, "timespan": timespan, "sort": sort, "articleCount": len(payload.get("articles", []))},
    )
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
    filtered_count = 0
    material_count = 0
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
        relevant = filter_relevant_news_items(item, normalized)
        filtered_out = max(0, len(normalized) - len(relevant))
        filtered_count += filtered_out
        relevance_summary = news_relevance_summary(relevant)
        material_count += bounded_int(relevance_summary.get("material", 0), 0, 100)
        normalized = relevant
        news_count += len(normalized)
        item["globalNews"] = {
            "source": "gdelt",
            "query": query,
            "display": len(normalized),
            "rawDisplay": payload.get("display", len(normalized)),
            "filteredOut": filtered_out,
            "timespan": payload.get("timespan", GDELT_NEWS_TIMESPAN),
            "items": normalized,
            "relevanceSummary": relevance_summary,
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
        "filteredNewsCount": filtered_count,
        "materialNewsCount": material_count,
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
    material_count = 0
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
        relevance_summary = news_relevance_summary(relevant)
        material_count += bounded_int(relevance_summary.get("material", 0), 0, 100)
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
            "relevanceSummary": relevance_summary,
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
        "materialNewsCount": material_count,
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
                    "relevance": item.get("relevance", {}),
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
                "eventLabel": clean_news_text(str(item.get("eventLabel", ""))),
                "eventTone": clean_news_text(str(item.get("eventTone", ""))),
                "eventImportance": item.get("eventImportance"),
            }
        )
    return compacted


def disclosure_item_with_classification(item: dict) -> dict:
    if item.get("eventKey"):
        return item
    classified = classify_dart_disclosure(item.get("reportName", ""), item.get("receivedDate", ""))
    return {**item, **classified}


def official_event_signal(candidate: dict) -> dict:
    live_disclosures = candidate.get("liveDisclosures", {})
    if not isinstance(live_disclosures, dict):
        return {"source": "none", "count": 0, "summary": "공식 공시 미확인"}

    raw_items = live_disclosures.get("items", [])
    items = [disclosure_item_with_classification(item) for item in raw_items if isinstance(item, dict)] if isinstance(raw_items, list) else []
    if not items:
        return {
            "source": live_disclosures.get("source", "none"),
            "count": 0,
            "summary": "최근 공식 공시는 발견되지 않았습니다.",
            "items": [],
            "scoreBoost": 0,
            "riskBoost": 0,
            "confidenceBoost": 0,
            "riskLevel": "none",
        }

    positive_items = [item for item in items if item.get("eventTone") == "positive"]
    risk_items = [item for item in items if item.get("eventTone") == "risk"]
    caution_items = [item for item in items if item.get("eventTone") == "caution"]
    score_boost = bounded_int(sum(int(item.get("scoreImpact", 0) or 0) for item in items), -10, 12)
    risk_boost = bounded_int(sum(int(item.get("riskImpact", 0) or 0) for item in items), 0, 18)
    confidence_boost = bounded_int(5 + len(items) * 2 + len(positive_items) * 2, 0, 16)
    primary = sorted(items, key=lambda item: bounded_int(item.get("eventImportance", 0), 0, 100), reverse=True)[0]

    if risk_items and (risk_boost >= 8 or bounded_int(primary.get("eventImportance", 0), 0, 100) >= 80):
        risk_level = "high"
        summary = f"공식 공시 리스크: {primary.get('eventLabel', '확인 필요')} 확인"
    elif risk_boost >= 4 or caution_items:
        risk_level = "medium"
        summary = f"공식 공시 확인 필요: {primary.get('eventLabel', '확인 필요')}"
    elif positive_items:
        risk_level = "low"
        summary = f"공식 이벤트 확인: {primary.get('eventLabel', '긍정 공시')}"
    else:
        risk_level = "low"
        summary = f"공식 자료 확인: {primary.get('eventLabel', '일반 공시')}"

    reasons = []
    warnings = []
    for item in items[:5]:
        label = item.get("eventLabel") or "공시"
        report = item.get("reportName") or ""
        reason = item.get("reason") or ""
        if item.get("eventTone") == "risk":
            warnings.append(f"{label}: {report}")
        elif item.get("eventTone") == "caution":
            warnings.append(f"{label}: 확인 필요")
        else:
            reasons.append(f"{label}: {reason}")
        warnings.extend(text_list(item.get("warnings", []), limit=2))

    return {
        "source": live_disclosures.get("source", "opendart"),
        "count": len(items),
        "positiveCount": len(positive_items),
        "riskCount": len(risk_items),
        "cautionCount": len(caution_items),
        "neutralCount": len(items) - len(positive_items) - len(risk_items) - len(caution_items),
        "scoreBoost": score_boost,
        "riskBoost": risk_boost,
        "confidenceBoost": confidence_boost,
        "riskLevel": risk_level,
        "summary": summary,
        "primary": {
            "reportName": primary.get("reportName", ""),
            "eventLabel": primary.get("eventLabel", ""),
            "eventTone": primary.get("eventTone", ""),
            "eventImportance": primary.get("eventImportance", 0),
            "receivedDate": primary.get("receivedDate", ""),
            "url": primary.get("url", ""),
        },
        "reasons": unique_texts(reasons, limit=4),
        "warnings": unique_texts(warnings, limit=4),
        "items": [
            {
                "reportName": item.get("reportName", ""),
                "eventLabel": item.get("eventLabel", ""),
                "eventTone": item.get("eventTone", ""),
                "eventImportance": item.get("eventImportance", 0),
                "receivedDate": item.get("receivedDate", ""),
                "url": item.get("url", ""),
            }
            for item in items[:5]
        ],
    }


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
        "officialSignal": candidate.get("officialSignal", {}),
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

    official_signal = candidate.get("officialSignal", {})
    if not isinstance(official_signal, dict) or not official_signal.get("count"):
        official_signal = official_event_signal(candidate)
    tags = text_list(candidate.get("tags", []), limit=3)
    primary_official = official_signal.get("primary", {}) if isinstance(official_signal.get("primary"), dict) else {}
    event_type = primary_official.get("eventLabel") or (tags[0] if tags else "뉴스·가격 반응")
    if official_signal.get("riskLevel") == "high":
        sentiment = "negative"
        action_bias = "avoid"
        risk_score = max(risk_score, 78)
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
            *text_list(official_signal.get("warnings", []), limit=2),
            *text_list(candidate.get("noEntry", []), limit=3),
            *text_list(candidate.get("disclosures", []), limit=2),
        ],
        "entryConditions": text_list(candidate.get("entryConditions", []), limit=6),
        "noEntryConditions": text_list(candidate.get("noEntry", []), limit=6),
        "stopRules": text_list(candidate.get("stopRules", []), limit=5),
        "evidenceNotes": [
            f"후보 점수 {score}/100, 트리거 준비도 {readiness}/100",
            f"공식 이벤트 {official_signal.get('count', 0)}건, 위험 {official_signal.get('riskCount', 0)}건",
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
        relevance_summary = live_news.get("relevanceSummary", {}) if isinstance(live_news.get("relevanceSummary"), dict) else {}
        high = bounded_int(relevance_summary.get("high", 0), 0, 100)
        medium = bounded_int(relevance_summary.get("medium", 0), 0, 100)
        material = bounded_int(relevance_summary.get("material", 0), 0, 100)
        if item_count:
            relevant_score = bounded_int(6 + high * 5 + medium * 3 + material * 4 + min(display_count, 5), 0, 22)
            score = max(score, relevant_score)
            notes.append(f"네이버 고관련 뉴스 {item_count}건, 재료성 뉴스 {material}건 반영")
        elif filtered_count:
            score = min(score, 8)
            notes.append("뉴스 검색 결과가 있었지만 종목명/티커와 맞지 않아 점수 반영 제외")
        if filtered_count:
            notes.append(f"관련성 낮은 뉴스 {filtered_count}건 제외")

    global_news = candidate.get("globalNews", {})
    if isinstance(global_news, dict) and global_news.get("source") == "gdelt":
        display_count = bounded_int(global_news.get("display", 0), 0, 250)
        item_count = len(global_news.get("items", [])) if isinstance(global_news.get("items"), list) else 0
        filtered_count = bounded_int(global_news.get("filteredOut", 0), 0, 250)
        relevance_summary = global_news.get("relevanceSummary", {}) if isinstance(global_news.get("relevanceSummary"), dict) else {}
        high = bounded_int(relevance_summary.get("high", 0), 0, 250)
        medium = bounded_int(relevance_summary.get("medium", 0), 0, 250)
        material = bounded_int(relevance_summary.get("material", 0), 0, 250)
        if item_count:
            gdelt_score = bounded_int(5 + high * 5 + medium * 3 + material * 4 + min(display_count, 5), 0, 20)
            score = max(score, gdelt_score)
            if isinstance(live_news, dict) and live_news.get("source") == "naver":
                score += 2
            notes.append(f"GDELT 고관련 뉴스 {item_count}건, 재료성 뉴스 {material}건 반영")
        elif filtered_count:
            notes.append(f"GDELT 관련성 낮은 뉴스 {filtered_count}건 제외")

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


def candidate_event_pressure(candidate: dict, score_detail: dict) -> bool:
    news_score = bounded_int(score_detail.get("news", 0), 0, 22)
    event_score = bounded_int(score_detail.get("event", 0), 0, 25)
    live_news = candidate.get("liveNews", {})
    news_items = len(live_news.get("items", [])) if isinstance(live_news, dict) and isinstance(live_news.get("items"), list) else 0
    global_news = candidate.get("globalNews", {})
    global_items = len(global_news.get("items", [])) if isinstance(global_news, dict) and isinstance(global_news.get("items"), list) else 0
    disclosures = candidate.get("liveDisclosures", {})
    disclosure_items = disclosures.get("items", []) if isinstance(disclosures, dict) else []
    disclosure_count = len(disclosure_items) if isinstance(disclosure_items, list) else 0
    return news_score >= 14 or event_score >= 16 or news_items > 0 or global_items > 0 or disclosure_count > 0


def candidate_price_reaction(candidate: dict, score_detail: dict) -> dict:
    score = 0
    reasons: list[str] = []
    warnings: list[str] = []
    blockers: list[str] = []
    sources: list[str] = []
    confirmed_factors: list[str] = []
    missing_factors: list[str] = []

    change = display_percent_to_decimal(candidate.get("change"))
    live_price = candidate.get("livePrice", {})
    live_freshness = live_price.get("freshness") if isinstance(live_price, dict) and isinstance(live_price.get("freshness"), dict) else live_price_freshness(live_price, market=str(candidate.get("market", "")))
    has_live_price = candidate_has_fresh_live_price(candidate)
    has_price_basis = candidate_has_usable_price_basis(candidate)
    closed_baseline = bool(live_freshness.get("isClosedBaseline"))
    if has_live_price:
        sources.append("토스 현재가")
    elif has_price_basis and closed_baseline:
        sources.append("토스 마감가")
        warnings.append(str(live_freshness.get("message") or "마감가 기준으로 분석하고 실시간 진입은 개장 후 확인합니다."))
    elif isinstance(live_price, dict) and live_price.get("source") == "toss":
        warnings.append(str(live_freshness.get("message") or "토스 현재가가 지연되어 실시간 판단 보류"))
    price_reaction_positive = False
    price_reaction_confirmed = False
    if change is None:
        warnings.append("등락률 미확인")
        missing_factors.append("가격")
    elif change >= Decimal("0.4") and change <= Decimal("3"):
        score += 28
        price_reaction_positive = True
        price_reaction_confirmed = True
        confirmed_factors.append("가격")
        reasons.append(f"가격이 {display_change(change)}로 재료에 반응")
    elif change > 0:
        score += 18
        price_reaction_positive = True
        if change >= Decimal("0.25"):
            price_reaction_confirmed = True
            confirmed_factors.append("가격")
        else:
            missing_factors.append("가격 강도")
        reasons.append(f"가격이 {display_change(change)}로 소폭 반응")
    elif change >= Decimal("-0.5"):
        score += 8
        missing_factors.append("가격")
        warnings.append(f"가격 반응이 {display_change(change)}로 약함")
    elif change >= Decimal("-2"):
        score += 3
        missing_factors.append("가격")
        warnings.append(f"가격이 {display_change(change)}로 약세")
    else:
        score -= 8
        missing_factors.append("가격")
        warnings.append(f"가격이 {display_change(change)}로 재료를 부정")

    trend = candidate.get("trend", {}) if isinstance(candidate.get("trend"), dict) else {}
    volume = display_multiplier_to_decimal(trend.get("volumeSpike"))
    candles = candidate.get("liveCandles", {})
    has_live_candles = isinstance(candles, dict) and candles.get("source") == "toss"
    if has_live_candles:
        sources.append("토스 일봉")
    volume_confirmed = False
    if volume is None:
        warnings.append("거래량 배수 미확인")
        missing_factors.append("거래량")
    elif volume >= Decimal("2.2"):
        score += 25
        volume_confirmed = True
        confirmed_factors.append("거래량")
        reasons.append(f"거래량 {volume.quantize(Decimal('0.1'))}배로 수급 반응 강함")
    elif volume >= Decimal("1.5"):
        score += 18
        volume_confirmed = True
        confirmed_factors.append("거래량")
        reasons.append(f"거래량 {volume.quantize(Decimal('0.1'))}배로 수급 확인")
    elif volume >= Decimal("1.1"):
        score += 10
        reasons.append(f"거래량 {volume.quantize(Decimal('0.1'))}배로 최소 반응")
        missing_factors.append("거래량 강도")
    else:
        score += 2
        missing_factors.append("거래량")
        warnings.append(f"거래량 {volume.quantize(Decimal('0.1'))}배로 반응 부족")

    orderbook = candidate.get("liveOrderbook", {})
    has_orderbook = isinstance(orderbook, dict) and orderbook.get("source") == "toss"
    orderbook_imbalance = None
    if has_orderbook:
        sources.append("토스 호가")
        orderbook_imbalance = display_percent_to_decimal(orderbook.get("imbalancePercent"))
        if orderbook_imbalance is not None and orderbook_imbalance >= Decimal("15"):
            score += 15
            reasons.append(f"호가 {orderbook.get('pressure')}({orderbook.get('imbalancePercent')})")
        elif orderbook_imbalance is not None and orderbook_imbalance <= Decimal("-15"):
            score -= 8
            warnings.append(f"호가 {orderbook.get('pressure')}({orderbook.get('imbalancePercent')})")
        else:
            score += 5
            reasons.append("호가 균형 확인")
    else:
        warnings.append("호가 반응 미확인")

    trades = candidate.get("liveTrades", {})
    has_trades = isinstance(trades, dict) and trades.get("source") == "toss"
    trade_bias = None
    if has_trades:
        sources.append("토스 체결")
        trade_bias = display_percent_to_decimal(trades.get("biasPercent"))
        if trade_bias is not None and trade_bias >= Decimal("20"):
            score += 20
            reasons.append(f"체결 {trades.get('pressure')}({trades.get('biasPercent')})")
        elif trade_bias is not None and trade_bias >= Decimal("5"):
            score += 12
            reasons.append(f"체결 {trades.get('pressure')}({trades.get('biasPercent')})")
        elif trade_bias is not None and trade_bias <= Decimal("-20"):
            score -= 10
            warnings.append(f"체결 {trades.get('pressure')}({trades.get('biasPercent')})")
        elif trade_bias is not None and trade_bias <= Decimal("-5"):
            score -= 4
            warnings.append(f"체결 {trades.get('pressure')}({trades.get('biasPercent')})")
        else:
            score += 5
            reasons.append("체결 중립 확인")
    else:
        warnings.append("체결 반응 미확인")

    has_event = candidate_event_pressure(candidate, score_detail)
    volume_weak = volume is None or volume < Decimal("1.2")
    liquidity_positive = (
        (orderbook_imbalance is not None and orderbook_imbalance >= Decimal("8"))
        or (trade_bias is not None and trade_bias >= Decimal("5"))
    )
    liquidity_negative = (
        (orderbook_imbalance is not None and orderbook_imbalance <= Decimal("-15"))
        or (trade_bias is not None and trade_bias <= Decimal("-15"))
    )
    if liquidity_positive:
        confirmed_factors.append("수급")
    else:
        missing_factors.append("수급")
    confirmed_factors = unique_texts(confirmed_factors, limit=4)
    missing_factors = unique_texts(missing_factors, limit=4)
    confirmation_count = len(confirmed_factors)
    required_confirmations = 2 if has_event else 1
    if price_reaction_confirmed and volume_confirmed:
        score += 12
        reasons.append("가격과 거래량이 동시에 확인")
    elif price_reaction_confirmed and liquidity_positive:
        score += 10
        reasons.append("가격과 수급이 동시에 확인")
    reaction_gate = "watch"
    entry_block = False

    if not has_price_basis:
        reaction_gate = "wait"
        entry_block = True
        blockers.append("가격 기준 미확인")
    if has_event and not price_reaction_positive:
        score = min(score, 40)
        reaction_gate = "wait"
        entry_block = True
        blockers.append("재료 대비 가격 상승 반응 미확인")
    if has_event and change is not None and change <= 0 and (volume is None or volume < Decimal("1.2")):
        score = min(score, 38)
        warnings.append("뉴스·공시 재료 대비 가격과 거래량 반응 부족")
        blockers.append("재료 이후 가격·거래량 반응 부족")
    if has_event and score < 45:
        warnings.append("재료는 있으나 시장 자금 반응 확인 전")
    if has_event and change is not None and change <= Decimal("-1") and volume_weak:
        score = min(score, 28)
        reaction_gate = "blocked"
        entry_block = True
        blockers.append("재료 이후 가격이 약세이고 거래량도 부족")
    elif has_event and change is not None and change <= 0 and volume_weak:
        reaction_gate = "wait"
        entry_block = True
        blockers.append("재료 대비 가격·거래량 확인 필요")
    elif has_event and change is not None and change > 0 and volume_weak and not liquidity_positive:
        score = min(score, 48)
        reaction_gate = "wait"
        entry_block = True
        blockers.append("가격은 움직였지만 거래량·수급 확인 부족")
    elif has_event and confirmation_count < required_confirmations:
        score = min(score, 52)
        reaction_gate = "wait"
        entry_block = True
        blockers.append("가격·거래량·수급 중 2개 이상 확인 필요")
    elif has_event and liquidity_negative:
        score = min(score, 44)
        reaction_gate = "wait"
        entry_block = True
        blockers.append("호가·체결 수급이 약세")
    elif change is not None and change >= Decimal("5"):
        reaction_gate = "wait"
        entry_block = True
        warnings.append("단기 급등으로 추격 진입 금지")
        blockers.append("단기 급등 구간")

    score = bounded_int(score, 0, 100)
    if score >= 72:
        key, label, priority = "strong", "반응 강함", 0
    elif score >= 56:
        key, label, priority = "confirmed", "반응 확인", 1
    elif score >= 40:
        key, label, priority = "weak", "반응 약함", 2
    else:
        key, label, priority = "missing", "반응 부족", 3

    if reaction_gate not in {"blocked", "wait"}:
        if (
            key in {"strong", "confirmed"}
            and has_live_price
            and price_reaction_confirmed
            and (volume_confirmed or liquidity_positive)
        ):
            reaction_gate = "confirmed"
        elif key == "weak":
            reaction_gate = "watch"
        else:
            reaction_gate = "wait"
            if has_event:
                entry_block = True

    supports_entry = (
        reaction_gate == "confirmed"
        and not entry_block
        and has_live_price
        and price_reaction_confirmed
        and (volume_confirmed or liquidity_positive)
        and confirmation_count >= required_confirmations
    )
    market_response_confirmed = volume_confirmed or liquidity_positive
    entry_criteria = [
        {
            "key": "live_price",
            "label": "가격 기준",
            "ok": has_price_basis,
            "value": (
                f"{live_freshness.get('label')} · {candidate.get('price', '-')}"
                if isinstance(live_price, dict) and live_price.get("source") == "toss"
                else str(live_freshness.get("label") or "가격 기준 대기")
            ),
            "required": True,
        },
        {
            "key": "price_direction",
            "label": "가격 방향",
            "ok": price_reaction_confirmed,
            "value": display_change(change) if change is not None else "등락률 확인 중",
            "required": True,
        },
        {
            "key": "market_response",
            "label": "거래·수급",
            "ok": market_response_confirmed,
            "value": (
                f"거래량 {volume.quantize(Decimal('0.1'))}배"
                if volume_confirmed and volume is not None
                else "호가·체결 우위" if liquidity_positive
                else "거래량·체결 대기"
            ),
            "required": True,
        },
        {
            "key": "confirmation_count",
            "label": "확인 조건",
            "ok": confirmation_count >= required_confirmations,
            "value": f"{confirmation_count}/{required_confirmations}",
            "required": True,
        },
    ]
    if supports_entry:
        next_check = "가격·거래량 반응이 확인되었습니다. 매수 구간과 리스크 기준만 점검하세요."
    elif blockers:
        next_check = blockers[0]
    elif not has_price_basis:
        next_check = str(live_freshness.get("message") or "가격 기준 수신을 기다립니다.")
    elif closed_baseline and not has_live_price:
        next_check = "직전 정규장 마감가 기준 분석입니다. 실시간 매수 판단은 개장 후 가격·거래량 반응을 확인하세요."
    elif not price_reaction_confirmed:
        next_check = "뉴스 방향과 같은 가격 반응이 확인될 때까지 대기합니다."
    elif not market_response_confirmed:
        next_check = "거래량 증가 또는 호가·체결 우위가 확인될 때까지 대기합니다."
    elif confirmation_count < required_confirmations:
        next_check = f"가격·거래량·수급 중 {required_confirmations}개 이상 확인이 필요합니다."
    else:
        next_check = "가격 반응과 리스크 기준을 한 번 더 확인합니다."

    if reaction_gate == "blocked":
        reaction_decision = {
            "key": "blocked",
            "label": "반응 차단",
            "tone": "risk",
            "action": "오늘 제외",
            "summary": next_check,
            "tradeAllowed": False,
        }
    elif supports_entry:
        reaction_decision = {
            "key": "confirmed",
            "label": "반응 확인",
            "tone": "buy",
            "action": "매수 구간 점검",
            "summary": next_check,
            "tradeAllowed": True,
        }
    elif reaction_gate == "confirmed":
        reaction_decision = {
            "key": "confirmed",
            "label": "반응 확인",
            "tone": "buy",
            "action": "조건 점검",
            "summary": next_check,
            "tradeAllowed": False,
        }
    elif reaction_gate == "watch":
        reaction_decision = {
            "key": "watch",
            "label": "관찰 지속",
            "tone": "watch",
            "action": "추가 확인",
            "summary": next_check,
            "tradeAllowed": False,
        }
    else:
        reaction_decision = {
            "key": "wait",
            "label": "반응 대기",
            "tone": "wait",
            "action": "진입 보류",
            "summary": next_check,
            "tradeAllowed": False,
        }

    return {
        "key": key,
        "label": label,
        "priority": priority,
        "score": score,
        "reactionGate": reaction_gate,
        "decision": reaction_decision,
        "decisionKey": reaction_decision["key"],
        "decisionLabel": reaction_decision["label"],
        "actionLabel": reaction_decision["action"],
        "entryBlock": entry_block,
        "supportsEntry": supports_entry,
        "entryReady": supports_entry,
        "entryCriteria": entry_criteria,
        "nextCheck": next_check,
        "hasEvent": has_event,
        "metrics": {
            "priceChange": display_change(change) if change is not None else "",
            "volumeSpike": f"{volume.quantize(Decimal('0.1'))}배" if volume is not None else "",
            "hasLivePrice": has_live_price,
            "hasLiveCandles": has_live_candles,
            "hasOrderbook": has_orderbook,
            "hasTrades": has_trades,
            "orderbookImbalance": display_change(orderbook_imbalance) if orderbook_imbalance is not None else "",
            "tradeBias": display_change(trade_bias) if trade_bias is not None else "",
            "priceConfirmed": price_reaction_confirmed,
            "volumeConfirmed": volume_confirmed,
            "liquidityConfirmed": liquidity_positive,
            "confirmationCount": confirmation_count,
            "requiredConfirmations": required_confirmations,
            "confirmedFactors": confirmed_factors,
            "missingFactors": missing_factors,
        },
        "sources": unique_texts(sources, limit=4),
        "reasons": unique_texts(reasons, limit=5),
        "warnings": unique_texts(warnings, limit=5),
        "blockers": unique_texts(blockers, limit=5),
    }


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
    official_signal = candidate.get("officialSignal", {})
    if not isinstance(official_signal, dict) or official_signal.get("count") is None:
        official_signal = official_event_signal(candidate)
    if official_signal.get("count"):
        risk += bounded_int(official_signal.get("riskBoost", 0), 0, 18)
        if official_signal.get("riskLevel") == "high":
            notes.append("중대 공시 리스크가 발견되어 진입 기준 강화")
        elif official_signal.get("riskLevel") == "medium":
            notes.append("공식 공시 확인 필요 신호 반영")
        elif official_signal.get("positiveCount", 0):
            notes.append(f"공식 긍정 이벤트 {official_signal.get('positiveCount')}건 확인")
    live_disclosures = candidate.get("liveDisclosures", {})
    if isinstance(live_disclosures, dict):
        disclosure_items = live_disclosures.get("items", [])
        disclosure_count = len(disclosure_items) if isinstance(disclosure_items, list) else 0
        if disclosure_count:
            risk += min(disclosure_count, 3)
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
    official_signal = candidate.get("officialSignal", {})
    if not isinstance(official_signal, dict) or official_signal.get("count") is None:
        official_signal = official_event_signal(candidate)
    score += int(official_signal.get("scoreBoost", 0) or 0)
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
    trade_gate = candidate_trade_data_gate(candidate)

    if risk >= 24 or total < 45:
        key, label, priority = "exclude", "오늘 제외", 4
        reason = "리스크나 종합 점수가 후보 기준에 부족합니다."
    elif not trade_gate["displayReady"]:
        key, label, priority = "wait", trade_gate["label"], 3
        reason = trade_gate["reason"]
    elif not trade_gate["tradeReady"]:
        key, priority = "wait", 3
        if trade_gate["closedBaseline"]:
            label = "장마감 관찰"
        else:
            label = "반응 검증 대기"
        reason = trade_gate["reason"]
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
        "tradeDataReady": bool(trade_gate["tradeReady"]),
        "displayDataReady": bool(trade_gate["displayReady"]),
        "dataGateLabel": trade_gate["label"],
        "missingData": trade_gate["missing"],
    }


def decision_group_counts(candidates: list[dict]) -> dict:
    counts = {"action": 0, "hidden": 0, "momentum": 0, "wait": 0, "exclude": 0}
    for item in candidates:
        group = item.get("decisionGroup", {}) if isinstance(item, dict) else {}
        key = str(group.get("key", "wait")) if isinstance(group, dict) else "wait"
        counts[key if key in counts else "wait"] += 1
    return counts


def raw_event_reliability_context() -> dict:
    db_enabled = database_storage_enabled()
    persistent = bool(db_enabled and DB_SCHEMA_READY and not DB_LAST_ERROR)
    return {
        "enabled": SIGNAL_RAW_EVENT_STORAGE_ENABLED,
        "backend": "postgres" if db_enabled else "filesystem",
        "persistent": persistent,
        "lastStoredAt": RAW_EVENT_STATE.get("lastStoredAt", ""),
        "lastSource": RAW_EVENT_STATE.get("lastSource", ""),
        "lastEventType": RAW_EVENT_STATE.get("lastEventType", ""),
    }


def reliability_component(score: int, label: str, status: str, reason: str = "", weight: int = 1) -> dict:
    return {
        "score": bounded_int(score, 0, 100),
        "label": label,
        "status": status,
        "reason": reason,
        "weight": max(1, int(weight)),
    }


def candidate_source_reliability(candidate: dict, raw_context: dict | None = None) -> dict:
    raw_context = raw_context if isinstance(raw_context, dict) else raw_event_reliability_context()
    components: dict[str, dict] = {}
    reasons: list[str] = []
    warnings: list[str] = []
    blockers: list[str] = []

    live_price = candidate.get("livePrice", {})
    if isinstance(live_price, dict) and live_price.get("source") == "toss":
        score = 95
        freshness = live_price.get("freshness") if isinstance(live_price.get("freshness"), dict) else live_price_freshness(live_price, market=str(candidate.get("market", "")))
        label = "Toss 마감가" if freshness.get("isClosedBaseline") else "Toss 현재가"
        status = "verified"
        reason = "마감가 기준 출처 확인" if freshness.get("isClosedBaseline") else "실시간 현재가 출처 확인"
        if live_price.get("baselineWarning"):
            score -= 18
            warnings.append("샘플 기준가와 실시간 현재가 차이가 큼")
    elif display_number_to_decimal(candidate.get("price")) is not None:
        score, label, status, reason = 42, "샘플 현재가", "fallback", "실시간 현재가 미확인"
        blockers.append("실시간 현재가 미확인")
    else:
        score, label, status, reason = 8, "현재가 없음", "missing", "가격 기준 계산 불가"
        blockers.append("현재가 미확인")
    components["price"] = reliability_component(score, label, status, reason, weight=24)

    live_candles = candidate.get("liveCandles", {})
    if isinstance(live_candles, dict) and live_candles.get("source") == "toss":
        score, label, status, reason = 90, "Toss 차트", "verified", "일봉/차트 출처 확인"
    elif isinstance(live_candles, dict) and live_candles.get("source") == "stale":
        score, label, status, reason = 38, "오래된 차트", "stale", "차트 최신성 부족"
        warnings.append("차트 최신성 확인 필요")
    else:
        score, label, status, reason = 30, "샘플 차트", "fallback", "실시간 차트 미확인"
    components["chart"] = reliability_component(score, label, status, reason, weight=14)

    liquidity_scores = []
    orderbook = candidate.get("liveOrderbook", {})
    trades = candidate.get("liveTrades", {})
    if isinstance(orderbook, dict) and orderbook.get("source") == "toss":
        liquidity_scores.append(88)
        reasons.append("호가 출처 확인")
    if isinstance(trades, dict) and trades.get("source") == "toss":
        liquidity_scores.append(88)
        reasons.append("체결 출처 확인")
    if liquidity_scores:
        liquidity_score = round(sum(liquidity_scores) / len(liquidity_scores))
        label, status, reason = "호가/체결 확인", "verified", "수급 원천 일부 확인"
    else:
        liquidity_score, label, status, reason = 35, "수급 미확인", "missing", "호가·체결 원천 미확인"
        warnings.append("수급 반응은 가격만으로 판단 중")
    components["liquidity"] = reliability_component(liquidity_score, label, status, reason, weight=13)

    live_news = candidate.get("liveNews", {}) if isinstance(candidate.get("liveNews"), dict) else {}
    global_news = candidate.get("globalNews", {}) if isinstance(candidate.get("globalNews"), dict) else {}
    news_items = len(live_news.get("items", [])) if isinstance(live_news.get("items"), list) else 0
    global_items = len(global_news.get("items", [])) if isinstance(global_news.get("items"), list) else 0
    relevance = live_news.get("relevanceSummary", {}) if isinstance(live_news.get("relevanceSummary"), dict) else {}
    gdelt_relevance = global_news.get("relevanceSummary", {}) if isinstance(global_news.get("relevanceSummary"), dict) else {}
    material = bounded_int(relevance.get("material", 0), 0, 100) + bounded_int(gdelt_relevance.get("material", 0), 0, 100)
    high = bounded_int(relevance.get("high", 0), 0, 100) + bounded_int(gdelt_relevance.get("high", 0), 0, 100)
    filtered = bounded_int(live_news.get("filteredOut", 0), 0, 1_000)
    if news_items or global_items:
        news_score = bounded_int(58 + min(22, (news_items + global_items) * 3) + material * 5 + high * 3, 0, 100)
        label, status, reason = "관련 뉴스 확인", "verified", f"관련 뉴스 {news_items + global_items}건"
        if material:
            reasons.append(f"재료성 뉴스 {material}건")
    elif filtered:
        news_score, label, status, reason = 36, "뉴스 관련성 낮음", "weak", "검색 뉴스는 있으나 종목 관련성이 낮음"
        warnings.append("뉴스 관련성 필터 통과 건수 부족")
    else:
        news_score, label, status, reason = 28, "뉴스 미확인", "missing", "후보 재료 뉴스 미확인"
    components["news"] = reliability_component(news_score, label, status, reason, weight=18)

    live_disclosures = candidate.get("liveDisclosures", {}) if isinstance(candidate.get("liveDisclosures"), dict) else {}
    official_signal = candidate.get("officialSignal", {})
    if not isinstance(official_signal, dict) or official_signal.get("count") is None:
        official_signal = official_event_signal(candidate)
    disclosure_items = live_disclosures.get("items", []) if isinstance(live_disclosures.get("items"), list) else []
    if official_signal.get("riskLevel") == "high":
        official_score, label, status, reason = 42, "공식 리스크", "risk", "중대 공시 리스크 확인"
        blockers.append("중대 공식 공시 리스크")
    elif live_disclosures.get("source") in {"opendart", "dart"}:
        official_score = 94 if disclosure_items else 82
        label, status = "OpenDART 확인", "verified"
        reason = f"공식 공시 {len(disclosure_items)}건" if disclosure_items else "최근 공식 공시 조회 완료"
    elif str(candidate.get("market", "")).upper() == "KR":
        official_score, label, status, reason = 38, "공시 미확인", "missing", "국내 종목 공식 공시 조회 미확인"
        warnings.append("국내 종목은 공시 확인 전 매수 후보로 낮춤")
    else:
        official_score, label, status, reason = 52, "해외 공시 미연결", "partial", "해외 공식 공시 수집은 아직 미연결"
    if official_signal.get("count") and status != "risk":
        official_score = max(official_score, 86)
        reasons.append(f"공식 이벤트 {official_signal.get('count')}건 분류")
    components["official"] = reliability_component(official_score, label, status, reason, weight=18)

    if raw_context.get("enabled") and raw_context.get("persistent"):
        raw_score, label, status, reason = 90, "DB 원천 저장", "persistent", "원천 이벤트 DB 저장 가능"
    elif raw_context.get("enabled"):
        raw_score, label, status, reason = 58, "파일 원천 저장", "filesystem", "원천 이벤트 파일 저장 가능"
        warnings.append("원천 데이터는 DB가 아니면 재배포 후 유지가 불안정")
    else:
        raw_score, label, status, reason = 22, "원천 저장 꺼짐", "disabled", "판단 근거 사후 검증 어려움"
        blockers.append("원천 데이터 저장 비활성")
    components["rawStorage"] = reliability_component(raw_score, label, status, reason, weight=8)

    weighted_total = sum(component["score"] * component["weight"] for component in components.values())
    weight_sum = sum(component["weight"] for component in components.values()) or 1
    score = bounded_int(round(weighted_total / weight_sum), 0, 100)
    if score >= 78:
        label = "높음"
        action = "신뢰 통과"
    elif score >= 64:
        label = "보통"
        action = "조건부 활용"
    elif score >= 48:
        label = "낮음"
        action = "근거 보강"
    else:
        label = "부족"
        action = "오늘 제외 검토"

    strongest = sorted(components.items(), key=lambda item: item[1]["score"], reverse=True)[:3]
    weakest = sorted(components.items(), key=lambda item: item[1]["score"])[:3]
    reasons = unique_texts([*reasons, *[component["reason"] for _, component in strongest if component.get("reason")]], limit=5)
    warnings = unique_texts([*warnings, *[component["reason"] for _, component in weakest if component.get("score", 0) < 55 and component.get("reason")]], limit=5)

    return {
        "score": score,
        "label": label,
        "action": action,
        "components": components,
        "reasons": reasons,
        "warnings": warnings,
        "blockers": unique_texts(blockers, limit=4),
        "rawStorage": {
            "enabled": bool(raw_context.get("enabled")),
            "persistent": bool(raw_context.get("persistent")),
            "backend": raw_context.get("backend", ""),
        },
    }


def candidate_data_confidence(candidate: dict, source_reliability: dict | None = None) -> dict:
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
        relevance_summary = live_news.get("relevanceSummary", {}) if isinstance(live_news.get("relevanceSummary"), dict) else {}
        material = bounded_int(relevance_summary.get("material", 0), 0, 100)
        high = bounded_int(relevance_summary.get("high", 0), 0, 100)
        score += min(18, 8 + news_items * 2 + material * 2 + high)
        reasons.append(f"고관련 뉴스 {news_items}건")
        if material:
            reasons.append(f"투자 재료 뉴스 {material}건")
    elif isinstance(live_news, dict) and live_news.get("filteredOut"):
        warnings.append("뉴스 검색 결과의 종목 관련성 낮음")

    global_news = candidate.get("globalNews", {})
    global_items = len(global_news.get("items", [])) if isinstance(global_news, dict) and isinstance(global_news.get("items"), list) else 0
    if global_items:
        score += min(10, 5 + global_items * 2)
        reasons.append(f"글로벌 뉴스 {global_items}건")

    live_disclosures = candidate.get("liveDisclosures", {})
    if isinstance(live_disclosures, dict) and live_disclosures.get("source") in {"opendart", "dart"}:
        score += 8
        reasons.append("OpenDART 확인")
        if isinstance(live_disclosures.get("items"), list) and live_disclosures.get("items"):
            reasons.append(f"OpenDART 공시 {len(live_disclosures.get('items', []))}건")
    official_signal = candidate.get("officialSignal", {})
    if not isinstance(official_signal, dict) or official_signal.get("count") is None:
        official_signal = official_event_signal(candidate)
    if official_signal.get("count"):
        score += bounded_int(official_signal.get("confidenceBoost", 0), 0, 16)
        reasons.append(f"공식 이벤트 {official_signal.get('count')}건 분류")
        if official_signal.get("riskLevel") == "high":
            score -= 8
            warnings.append("중대 공시 리스크 우선 확인")
        elif official_signal.get("riskLevel") == "medium":
            warnings.append("공시 영향 확인 필요")

    discovery = candidate.get("discovery", {}) if isinstance(candidate.get("discovery"), dict) else {}
    quality_tier = discovery.get("qualityTier")
    if quality_tier == "primary":
        score += 8
    elif quality_tier == "reserve":
        score += 4
    elif quality_tier == "rejected":
        score -= 12
        warnings.append("발굴 품질 기준 미달")

    if isinstance(source_reliability, dict):
        reliability_score = bounded_int(source_reliability.get("score", 0), 0, 100)
        score = round((score * 0.72) + (reliability_score * 0.28))
        reasons.append(f"원천 신뢰 {reliability_score}/100")
        warnings.extend(text_list(source_reliability.get("warnings", []), limit=3))
        warnings.extend(text_list(source_reliability.get("blockers", []), limit=2))

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


def candidate_quality_gate(candidate: dict, score_detail: dict, total: int, readiness: int, confidence: dict, reaction: dict | None = None) -> dict:
    group = candidate.get("decisionGroup", {}) if isinstance(candidate.get("decisionGroup"), dict) else {}
    group_key = str(group.get("key", "wait"))
    risk = bounded_int(score_detail.get("riskPenalty", 0), 0, 30)
    heat = bounded_int(score_detail.get("heatPenalty", 0), 0, 20)
    confidence_score = bounded_int(confidence.get("score", 0), 0, 100)
    source_reliability = candidate.get("sourceReliability", {}) if isinstance(candidate.get("sourceReliability"), dict) else {}
    reliability_score = bounded_int(source_reliability.get("score", confidence_score), 0, 100)
    reaction = reaction if isinstance(reaction, dict) else candidate_price_reaction(candidate, score_detail)
    reaction_score = bounded_int(reaction.get("score", 0), 0, 100)
    reaction_key = str(reaction.get("key", "missing"))
    reaction_gate = str(reaction.get("reactionGate", "wait"))
    reaction_entry_block = bool(reaction.get("entryBlock"))
    reaction_supports_entry = bool(reaction.get("supportsEntry"))
    reaction_entry_ready = bool(reaction.get("entryReady", reaction_supports_entry))
    live_price = candidate.get("livePrice", {})
    live_freshness = live_price.get("freshness") if isinstance(live_price, dict) and isinstance(live_price.get("freshness"), dict) else live_price_freshness(live_price, market=str(candidate.get("market", "")))
    has_live_price = candidate_has_fresh_live_price(candidate)
    completeness = candidate.get("dataCompleteness", {}) if isinstance(candidate.get("dataCompleteness"), dict) else candidate_data_completeness(candidate)
    price_readiness = candidate_price_readiness(candidate)
    evaluation_mode = candidate_evaluation_mode(candidate)
    display_data_ready = bool(completeness.get("displayReady"))
    entry_data_ready = bool(completeness.get("entryReady"))
    missing_data = completeness.get("missing", []) if isinstance(completeness.get("missing"), list) else []
    official_signal = candidate.get("officialSignal", {})
    if not isinstance(official_signal, dict) or official_signal.get("count") is None:
        official_signal = official_event_signal(candidate)
    reasons = []

    if official_signal.get("riskLevel") == "high":
        key, label, priority = "exclude", "공시 리스크", 4
        reasons.append("중대 공식 공시가 있어 신규 진입 제외")
    elif reliability_score < 45:
        key, label, priority = "defer", "원천 확인 대기", 3
        reasons.append("가격·뉴스·공시 원천 신뢰도가 낮아 보강 전까지 진입 보류")
    elif reliability_score < 58 and group_key == "action":
        key, label, priority = "defer", "근거 보강 대기", 3
        reasons.append("진입 후보로 보기에는 원천 데이터 보강 필요")
    elif not display_data_ready:
        key, label, priority = "defer", evaluation_mode["label"], 3
        reasons.append(evaluation_mode["message"])
    elif group_key == "action" and not entry_data_ready:
        key, label, priority = "defer", evaluation_mode["label"], 3
        if missing_data:
            reasons.append(f"진입 필수 데이터 보강 중: {', '.join(str(item) for item in missing_data[:4])}")
        else:
            reasons.append("진입 판단 전 가격·등락률·거래 반응 데이터 보강 필요")
    elif group_key in {"hidden", "momentum"} and not entry_data_ready:
        key, label, priority = "defer", evaluation_mode["label"], 3
        reasons.append(evaluation_mode["message"])
    elif reaction_gate == "blocked":
        key, label, priority = "exclude", "가격 반응 차단", 4
        reasons.append("재료 이후 가격·거래량 반응이 부정적")
    elif group_key == "action" and not has_live_price:
        key, label, priority = "defer", "개장 후 확인", 3
        reasons.append(str(live_freshness.get("message") or "정규장 가격·거래량 확인 전까지 진입 판단 보류"))
    elif reaction_entry_block and reaction.get("hasEvent"):
        key, label, priority = "defer", "반응 검증 대기", 3
        reasons.append(str(reaction.get("nextCheck") or "재료는 있으나 진입 전 가격·거래량 검증 필요"))
    elif official_signal.get("riskLevel") == "medium" and group_key == "action":
        key, label, priority = "defer", "공시 확인 대기", 3
        reasons.append("공식 공시 영향 확인 전까지 진입 보류")
    elif risk >= 24:
        key, label, priority = "exclude", "오늘 제외", 4
        reasons.append("리스크 또는 종합 점수가 기준 미달")
    elif total < 45 or group_key == "exclude":
        key, label, priority = "defer", "후보 보강 대기", 3
        reasons.append("후보 점수는 낮지만 리스크 차단은 아니므로 다음 가격·뉴스 갱신까지 대기")
    elif (
        group_key == "action"
        and has_live_price
        and confidence_score >= 68
        and reaction_entry_ready
        and reaction_score >= 62
        and risk < 18
        and heat < 10
        and readiness >= 70
    ):
        key, label, priority = "actionable", "실전 후보", 0
        reasons.append("가격·거래량 반응, 준비도, 신뢰도 기준 통과")
    elif reaction_key in {"missing", "weak"} and reaction.get("hasEvent"):
        key, label, priority = "defer", "반응 확인 대기", 3
        reasons.append("재료 대비 가격·거래량 반응 부족")
    elif group_key in {"hidden", "momentum"} and confidence_score >= 55 and reaction_score >= 40 and risk < 22:
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
        "sourceReliabilityScore": reliability_score,
        "reactionScore": reaction_score,
        "reactionGate": reaction_gate,
        "tradeAllowed": key == "actionable",
        "reasons": unique_texts([*reasons, *official_signal.get("warnings", []), *reaction.get("blockers", []), *reaction.get("warnings", []), *confidence.get("warnings", []), *source_reliability.get("blockers", [])], limit=5),
    }


def server_price_from_template(value: Decimal, template: str = "") -> str:
    text = str(template or "")
    if "$" in text:
        return f"${value.quantize(Decimal('0.01')):,.2f}"
    if "원" in text or "." not in text:
        return f"{int(value.quantize(Decimal('1'))):,}원"
    return f"{value.quantize(Decimal('0.01')):,.2f}"


def server_price_range(low: Decimal, high: Decimal, template: str = "") -> str:
    return f"{server_price_from_template(low, template)} ~ {server_price_from_template(high, template)}"


def final_price_band(candidate: dict, score_detail: dict, total: int, readiness: int, action_key: str) -> dict | None:
    current = display_number_to_decimal(candidate.get("price"))
    if current is None or current <= 0:
        return None

    change = display_percent_to_decimal(candidate.get("change"))
    heat = bounded_int(score_detail.get("heatPenalty", 0), 0, 20)
    opportunity = bounded_int(score_detail.get("opportunity", 0), 0, 18)
    strength = bounded_int((total * 0.45) + (readiness * 0.35) + (opportunity * 1.2), 0, 100)
    hot = change is not None and change >= Decimal("3")
    weak = change is not None and change <= Decimal("-2")

    entry_low_pct = Decimal("0.014")
    entry_high_pct = Decimal("0.002")
    pullback_pct = Decimal("0.028")
    chase_pct = Decimal("0.020")
    stop_pct = Decimal("0.040")
    trim_pct = Decimal("0.052")

    if action_key in {"buy", "add"}:
        entry_low_pct = Decimal("0.006") if strength >= 78 else Decimal("0.010")
        entry_high_pct = Decimal("0.005") if strength >= 78 else Decimal("0.003")
        pullback_pct = Decimal("0.018")
        stop_pct = Decimal("0.032")
        trim_pct = Decimal("0.058")
    elif action_key in {"pullback", "hold"}:
        entry_low_pct = Decimal("0.030")
        entry_high_pct = Decimal("-0.004")
        pullback_pct = Decimal("0.035")
        chase_pct = Decimal("0.012")
        stop_pct = Decimal("0.040")
    elif action_key == "trim":
        entry_low_pct = Decimal("0.020")
        entry_high_pct = Decimal("-0.004")
        pullback_pct = Decimal("0.030")
        chase_pct = Decimal("0.010")
        stop_pct = Decimal("0.038")
        trim_pct = Decimal("0.030")
    elif action_key in {"exclude", "stop"}:
        entry_low_pct = Decimal("0.040")
        entry_high_pct = Decimal("0.020")
        pullback_pct = Decimal("0.055")
        stop_pct = Decimal("0.030")
        trim_pct = Decimal("0.025")
    elif action_key == "verify":
        entry_low_pct = Decimal("0.020")
        entry_high_pct = Decimal("-0.002")
        pullback_pct = Decimal("0.035")
        stop_pct = Decimal("0.038")

    if hot:
        entry_low_pct = max(entry_low_pct, Decimal("0.030") + min(Decimal("0.025"), (change - Decimal("2")) / Decimal("100")))
        entry_high_pct = min(entry_high_pct, Decimal("-0.004"))
        pullback_pct = max(pullback_pct, Decimal("0.036"))
        chase_pct = min(chase_pct, Decimal("0.012"))
        stop_pct = max(stop_pct, Decimal("0.040"))
    elif weak:
        entry_low_pct = max(entry_low_pct, Decimal("0.020"))
        entry_high_pct = min(entry_high_pct, Decimal("-0.002"))
        pullback_pct = max(pullback_pct, Decimal("0.035"))
        stop_pct = min(stop_pct, Decimal("0.032"))

    entry_low = current * (Decimal("1") - entry_low_pct)
    entry_high = current * (Decimal("1") + entry_high_pct)
    low = min(entry_low, entry_high)
    high = max(entry_low, entry_high)
    return {
        "strength": strength,
        "current": server_price_from_template(current, str(candidate.get("price", ""))),
        "entryLow": server_price_from_template(low, str(candidate.get("price", ""))),
        "entryHigh": server_price_from_template(high, str(candidate.get("price", ""))),
        "entryRange": server_price_range(low, high, str(candidate.get("price", ""))),
        "pullback": server_price_from_template(current * (Decimal("1") - pullback_pct), str(candidate.get("price", ""))),
        "chaseLimit": server_price_from_template(current * (Decimal("1") + chase_pct), str(candidate.get("price", ""))),
        "stopLine": server_price_from_template(low * (Decimal("1") - stop_pct), str(candidate.get("price", ""))),
        "trimLine": server_price_from_template(current * (Decimal("1") + trim_pct), str(candidate.get("price", ""))),
        "reboundLine": server_price_from_template(current * Decimal("1.012"), str(candidate.get("price", ""))) if weak else "",
    }


def candidate_final_decision(candidate: dict, score_detail: dict, total: int, readiness: int, confidence: dict, gate: dict, reaction: dict | None = None) -> dict:
    group = candidate.get("decisionGroup", {}) if isinstance(candidate.get("decisionGroup"), dict) else {}
    group_key = str(group.get("key", "wait"))
    gate_key = str(gate.get("key", "defer"))
    portfolio = candidate.get("portfolio", {}) if isinstance(candidate.get("portfolio"), dict) else {}
    holding = portfolio.get("holding", {}) if isinstance(portfolio.get("holding"), dict) else {}
    is_held = bool(portfolio.get("isHeld") or holding)
    risk = bounded_int(score_detail.get("riskPenalty", 0), 0, 30)
    heat = bounded_int(score_detail.get("heatPenalty", 0), 0, 20)
    change = display_percent_to_decimal(candidate.get("change"))
    has_price = display_number_to_decimal(candidate.get("price")) is not None
    confidence_score = bounded_int(confidence.get("score", 0), 0, 100)
    source_reliability = candidate.get("sourceReliability", {}) if isinstance(candidate.get("sourceReliability"), dict) else {}
    reliability_score = bounded_int(source_reliability.get("score", confidence_score), 0, 100)
    hot = change is not None and change >= Decimal("3")
    weak = change is not None and change <= Decimal("-2")
    reaction = reaction if isinstance(reaction, dict) else candidate_price_reaction(candidate, score_detail)
    reaction_score = bounded_int(reaction.get("score", 0), 0, 100)
    reaction_key = str(reaction.get("key", "missing"))
    reaction_gate = str(reaction.get("reactionGate", "wait"))
    reaction_entry_block = bool(reaction.get("entryBlock"))
    reaction_supports_entry = bool(reaction.get("entryReady", reaction.get("supportsEntry")))
    official_signal = candidate.get("officialSignal", {})
    if not isinstance(official_signal, dict) or official_signal.get("count") is None:
        official_signal = official_event_signal(candidate)
    completeness = candidate.get("dataCompleteness", {}) if isinstance(candidate.get("dataCompleteness"), dict) else candidate_data_completeness(candidate)
    price_readiness = candidate_price_readiness(candidate)
    evaluation_mode = candidate_evaluation_mode(candidate)
    display_data_ready = bool(completeness.get("displayReady"))
    entry_data_ready = bool(completeness.get("entryReady"))
    missing_data = completeness.get("missing", []) if isinstance(completeness.get("missing"), list) else []
    evidence = candidate_discovery_evidence_strength(candidate)
    profit_percent = display_number_to_decimal(holding.get("profitLossPercent") or holding.get("profitLossRate"))
    allocation_percent = display_number_to_decimal(holding.get("allocationPercent") or holding.get("allocation"))
    holding_judgement = str(holding.get("judgement", "보유 유지"))

    if is_held:
        if official_signal.get("riskLevel") == "high":
            action_key, action, tone = "stop", "손절 점검", "risk"
            summary = "보유 종목에 중대 공식 공시 리스크가 있어 손절 기준과 비중 축소 여부를 먼저 확인합니다."
        elif risk >= 24 or (profit_percent is not None and profit_percent <= Decimal("-7")) or "손절" in holding_judgement:
            action_key, action, tone = "stop", "손절 점검", "risk"
            summary = "보유 손실 또는 리스크가 커져 추가매수보다 손절 기준 이탈 여부를 먼저 확인합니다."
        elif (allocation_percent is not None and allocation_percent >= Decimal("35")) or (profit_percent is not None and profit_percent >= Decimal("12")) or "분할매도" in holding_judgement or "비중" in holding_judgement:
            action_key, action, tone = "trim", "분할매도 검토", "sell"
            summary = "수익 또는 비중이 커진 보유 종목입니다. 신규 매수보다 일부 이익 실현과 비중 조절을 먼저 봅니다."
        elif profit_percent is not None and profit_percent <= Decimal("-3"):
            if gate_key == "actionable" and reaction_supports_entry and risk < 18:
                action_key, action, tone = "add", "추가매수 검토", "buy"
                summary = "보유 손실 구간이지만 가격 반응과 신뢰도가 확인되어 소액 추가매수 조건을 점검합니다."
            else:
                action_key, action, tone = "hold", "추가매수 대기", "wait"
                summary = "손실 구간이나 가격 반응 또는 신뢰도가 부족해 성급한 물타기를 피하고 반응 확인을 기다립니다."
        elif reaction_key in {"missing", "weak"} and reaction.get("hasEvent"):
            action_key, action, tone = "hold", "보유 유지", "wait"
            summary = "보유 종목에 재료는 있으나 시장 반응이 약해 추가매수보다 보유 관찰이 우선입니다."
        else:
            action_key, action, tone = "hold", "보유 유지", "wait"
            summary = "보유 종목은 신규 진입보다 기존 수익률, 비중, 가격 반응을 기준으로 관리합니다."
    elif not has_price:
        action_key, action, tone = "verify", evaluation_mode["label"], "wait"
        summary = evaluation_mode["message"]
    elif not display_data_ready:
        action_key, action, tone = "verify", evaluation_mode["label"], "wait"
        missing_text = ", ".join(str(item) for item in missing_data[:4]) if missing_data else "필수 데이터"
        summary = evaluation_mode["message"] or f"{missing_text} 확인 전까지 신규 진입 판단을 확정하지 않습니다."
    elif not entry_data_ready:
        action_key, action, tone = "verify", evaluation_mode["label"], "wait"
        summary = evaluation_mode["message"]
    elif gate_key == "actionable" and not entry_data_ready:
        action_key, action, tone = "verify", "반응 데이터 대기", "wait"
        missing_text = ", ".join(str(item) for item in missing_data[:4]) if missing_data else "가격·거래 반응"
        summary = f"{missing_text} 보강 전까지 매수 가능 후보로 올리지 않습니다."
    elif official_signal.get("riskLevel") == "high":
        action_key, action, tone = "exclude", "공시 리스크 제외", "risk"
        summary = "중대 공식 공시 리스크가 있어 가격 반응보다 공시 내용 확인을 우선합니다."
    elif reliability_score < 45:
        action_key, action, tone = "verify", "원천 확인 대기", "wait"
        summary = "가격·뉴스·공시 원천 신뢰도가 낮아 신규 진입보다 데이터 보강을 기다립니다."
    elif reliability_score < 58:
        action_key, action, tone = "verify", "근거 보강 대기", "wait"
        summary = "후보 신호는 있으나 원천 데이터 신뢰도가 낮아 시세·뉴스·공시 보강 전까지 대기합니다."
    elif official_signal.get("riskLevel") == "medium" and reaction_key not in {"strong", "confirmed"}:
        action_key, action, tone = "verify", "공시 확인 대기", "wait"
        summary = "공식 공시 영향이 아직 가격과 거래량으로 검증되지 않아 진입을 보류합니다."
    elif reaction_gate == "blocked":
        action_key, action, tone = "exclude", "가격 반응 부정", "risk"
        summary = "재료는 있으나 가격과 거래량이 부정적으로 반응해 오늘 신규 진입 대상에서 제외합니다."
    elif reaction_entry_block and reaction.get("hasEvent"):
        action_key, action, tone = "verify", "반응 검증 대기", "wait"
        summary = "뉴스·공시 재료는 있으나 가격·거래량·수급 확인이 부족해 진입을 보류합니다."
    elif gate_key == "exclude" or risk >= 24:
        action_key, action, tone = "exclude", "오늘 제외", "risk"
        summary = "리스크 또는 점수 기준이 부족해 신규 진입 대상에서 제외합니다."
    elif total < 45:
        action_key, action, tone = "verify", "후보 보강 대기", "wait"
        if evidence.get("qualified") or reaction.get("hasEvent"):
            summary = "재료는 있으나 점수와 가격 반응이 부족해 다음 가격·뉴스 갱신까지 대기합니다."
        else:
            summary = "후보 점수가 낮아 신규 진입은 보류하고 추가 근거가 생기는지 확인합니다."
    elif reaction_key == "missing" and reaction.get("hasEvent"):
        action_key, action, tone = "verify", "반응 확인 대기", "wait"
        summary = "뉴스·공시 재료는 있으나 가격·거래량 반응이 부족해 추가 확인 전까지 대기합니다."
    elif reaction_key == "weak":
        action_key, action, tone = "watch", "관찰", "wait"
        summary = "재료 대비 가격 반응이 약해 매수보다 거래량과 체결 반응 확인이 우선입니다."
    elif gate_key == "defer" or confidence_score < 45:
        action_key, action, tone = "verify", "확인 대기", "wait"
        summary = "실시간 가격·공시·뉴스 근거가 부족해 추가 검증 전까지 대기합니다."
    elif hot or heat >= 10:
        action_key, action, tone = "pullback", "눌림 대기", "wait"
        summary = "가격이 이미 반응했거나 과열 신호가 있어 추격보다 눌림 확인이 우선입니다."
    elif weak:
        action_key, action, tone = "watch", "관찰", "wait"
        summary = "가격이 약한 구간이라 거래량을 동반한 반등 회복 전까지 관찰합니다."
    elif gate_key == "actionable" and reaction_supports_entry and readiness >= 70 and total >= 72:
        action_key, action, tone = "buy", "매수 가능", "buy"
        summary = "신뢰도·가격·거래량 반응·리스크 기준을 통과했습니다. 단, 분할 관찰 기준으로만 접근합니다."
    elif group_key in {"hidden", "momentum"} or gate_key == "watch":
        action_key, action, tone = "watch", "관찰", "wait"
        summary = "재료는 있으나 가격·거래량 반응을 한 번 더 확인해야 합니다."
    else:
        action_key, action, tone = "pullback", "눌림 대기", "wait"
        summary = "후보 신호는 있으나 현재 가격에서는 즉시 진입보다 가격대 확인이 우선입니다."

    band = final_price_band(candidate, score_detail, total, readiness, action_key)
    signal_cards = [
        ["현재 판단", action],
        ["가격 반응", f"{reaction.get('label', '미확인')} · {reaction_score}/100"],
        ["매수 구간", band["entryRange"] if band else "현재가 확인 후 계산"],
        ["위험 기준", f"{band['stopLine']} 이탈" if band else "-"],
    ]
    if is_held:
        signal_cards = [
            ["현재 판단", action],
            ["보유 손익", holding.get("profitLossRate", "-")],
            ["평균단가", holding.get("averagePurchasePrice", "-")],
            ["비중", holding.get("allocation", "-")],
        ]
    rows = [
        ["관찰 매수", band["entryRange"] if band else "현재가 확인 후 계산"],
        ["눌림 대기", f"{band['pullback']} 부근 확인" if band else "-"],
        ["반등 확인", f"{band['reboundLine']} 회복" if band and band.get("reboundLine") else "약세 전환 시 확인"],
        ["추격 금지", f"{band['chaseLimit']} 이상" if band else "-"],
        ["손절 점검", f"{band['stopLine']} 이탈" if band else "-"],
        ["분할매도", f"{band['trimLine']} 이상 또는 과열 신호" if band else "-"],
    ]
    if is_held:
        rows.append(["보유 수량", str(holding.get("quantity", "-"))])
        rows.append(["평가금액", str(holding.get("marketValue", "-"))])
        rows.append(["매수가능", portfolio.get("buyingPower", {}).get("cashBuyingPower", "-") if isinstance(portfolio.get("buyingPower"), dict) else "-"])
    reasons = [
        f"최종 게이트: {gate.get('label', '미분류')}",
        f"데이터 신뢰도: {confidence_score}/100",
        f"원천 신뢰도: {reliability_score}/100",
        f"후보 점수: {total}/100",
        f"진입 준비도: {readiness}/100",
    ]
    if is_held:
        reasons.insert(0, f"보유 상태: {holding_judgement} · 손익 {holding.get('profitLossRate', '-')}")
    if change is not None:
        reasons.append(f"현재 등락률: {candidate.get('change')}")
    if group.get("reason"):
        reasons.append(str(group.get("reason")))
    if official_signal.get("count"):
        reasons.append(f"공식 이벤트: {official_signal.get('summary')}")

    return {
        "actionKey": action_key,
        "action": action,
        "tone": tone,
        "summary": summary,
        "tradeAllowed": action_key in {"buy", "add"},
        "gateKey": gate_key,
        "confidenceScore": confidence_score,
        "sourceReliabilityScore": reliability_score,
        "sourceReliabilityLabel": source_reliability.get("label", ""),
        "reactionScore": reaction_score,
        "reactionLabel": reaction.get("label", ""),
        "reactionGate": reaction_gate,
        "evaluationMode": evaluation_mode,
        "officialSignal": official_signal,
        "portfolioAware": is_held,
        "holdingJudgement": holding_judgement if is_held else "",
        "priceLevels": band or {},
        "signalCards": signal_cards,
        "rows": rows,
        "reasons": unique_texts([*reasons, *reaction.get("reasons", []), *reaction.get("blockers", []), *reaction.get("warnings", [])], limit=6),
        "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
    }


def final_decision_age_seconds(decision: dict) -> int | None:
    if not isinstance(decision, dict):
        return None
    parsed = parse_iso_datetime(str(decision.get("updatedAt", "")))
    if parsed is None:
        return None
    return max(0, int((datetime.now(KST) - parsed.astimezone(KST)).total_seconds()))


def stable_final_decision_candidate(candidate: dict) -> dict:
    stored = candidate.get("storedFinalDecision") if isinstance(candidate.get("storedFinalDecision"), dict) else {}
    current = candidate.get("finalDecision") if isinstance(candidate.get("finalDecision"), dict) else {}
    if stored:
        return stored
    return current if isinstance(current, dict) else {}


def decision_stability_merge(previous: dict, new_decision: dict, candidate: dict) -> tuple[dict, bool]:
    if not SIGNAL_FINAL_DECISION_STABILITY_ENABLED:
        return new_decision, False
    if not isinstance(previous, dict) or not previous.get("actionKey"):
        return new_decision, False
    if not isinstance(new_decision, dict) or not new_decision.get("actionKey"):
        return new_decision, False
    age_seconds = final_decision_age_seconds(previous)
    if age_seconds is None or age_seconds > SIGNAL_FINAL_DECISION_STABILITY_SECONDS:
        return new_decision, False

    previous_key = str(previous.get("actionKey", ""))
    new_key = str(new_decision.get("actionKey", ""))
    completeness = candidate.get("dataCompleteness", {}) if isinstance(candidate.get("dataCompleteness"), dict) else candidate_data_completeness(candidate)
    entry_ready = bool(completeness.get("entryReady"))
    display_ready = bool(completeness.get("displayReady"))
    risk_keys = {"stop", "exclude"}
    trade_keys = {"buy", "add"}

    if new_key in risk_keys and previous_key not in risk_keys:
        return new_decision, False
    if previous_key in trade_keys and not entry_ready:
        return new_decision, False
    if previous_key not in trade_keys and new_key in trade_keys and entry_ready:
        return new_decision, False
    if previous_key == "verify" and display_ready and new_key != "verify":
        return new_decision, False
    if previous_key in risk_keys and new_key not in risk_keys:
        return new_decision, False
    if previous_key == new_key and display_ready:
        return new_decision, False

    held = copy.deepcopy(previous)
    for key in (
        "priceLevels",
        "rows",
        "signalCards",
        "reactionScore",
        "reactionLabel",
        "reactionGate",
        "confidenceScore",
        "sourceReliabilityScore",
        "sourceReliabilityLabel",
        "officialSignal",
        "portfolioAware",
        "holdingJudgement",
    ):
        if key in new_decision:
            held[key] = copy.deepcopy(new_decision[key])
    if isinstance(held.get("signalCards"), list) and held["signalCards"]:
        first_card = held["signalCards"][0]
        if isinstance(first_card, list) and len(first_card) >= 2:
            first_card[1] = previous.get("action", first_card[1])
    held["actionKey"] = previous_key
    held["action"] = previous.get("action", held.get("action", "확인 대기"))
    held["tone"] = previous.get("tone", held.get("tone", "wait"))
    held["tradeAllowed"] = bool(previous.get("tradeAllowed"))
    held["gateKey"] = previous.get("gateKey", held.get("gateKey", "defer"))
    held["summary"] = str(previous.get("summary") or held.get("summary") or "이전 검증 판단을 유지합니다.")
    held["updatedAt"] = new_decision.get("updatedAt") or datetime.now(KST).isoformat(timespec="seconds")
    held["stability"] = {
        "source": "stored-final-decision",
        "held": True,
        "heldFrom": previous.get("updatedAt", ""),
        "ageSeconds": age_seconds,
        "windowSeconds": SIGNAL_FINAL_DECISION_STABILITY_SECONDS,
        "previousAction": previous.get("action", ""),
        "newAction": new_decision.get("action", ""),
        "reason": "10초 가격 갱신의 일시적인 미수신/등락 변동으로 최종 판단이 흔들리지 않도록 이전 검증 판단을 유지합니다.",
    }
    return held, True


def candidate_compression_score(candidate: dict) -> int:
    score_detail = candidate.get("score", {}) if isinstance(candidate.get("score"), dict) else {}
    final_decision = candidate.get("finalDecision", {}) if isinstance(candidate.get("finalDecision"), dict) else {}
    gate = candidate.get("qualityGate", {}) if isinstance(candidate.get("qualityGate"), dict) else {}
    confidence = candidate.get("dataConfidence", {}) if isinstance(candidate.get("dataConfidence"), dict) else {}
    reaction = candidate.get("priceReaction", {}) if isinstance(candidate.get("priceReaction"), dict) else {}
    official = candidate.get("officialSignal", {}) if isinstance(candidate.get("officialSignal"), dict) else {}
    trend = candidate.get("trend", {}) if isinstance(candidate.get("trend"), dict) else {}
    discovery = candidate.get("discovery", {}) if isinstance(candidate.get("discovery"), dict) else {}
    validation = candidate.get("signalValidation", {}) if isinstance(candidate.get("signalValidation"), dict) else {}
    price_readiness = candidate_price_readiness(candidate)

    action_key = str(final_decision.get("actionKey", "verify"))
    gate_key = str(gate.get("key", "defer"))
    reaction_gate = str(reaction.get("reactionGate", "wait"))
    risk = bounded_int(score_detail.get("riskPenalty", 0), 0, 30)
    heat = bounded_int(score_detail.get("heatPenalty", 0), 0, 20)
    base = {
        "buy": 30,
        "add": 28,
        "hold": 16,
        "trim": 12,
        "watch": 14,
        "pullback": 10,
        "verify": 2,
        "stop": -28,
        "exclude": -36,
    }.get(action_key, 0)
    gate_bonus = {"actionable": 22, "watch": 10, "defer": -8, "exclude": -30}.get(gate_key, -4)
    reaction_gate_penalty = {"confirmed": 0, "watch": -4, "wait": -12, "blocked": -28}.get(reaction_gate, -8)
    official_bonus = 0
    if official.get("riskLevel") == "high":
        official_bonus -= 30
    elif official.get("riskLevel") == "medium":
        official_bonus -= 8
    elif official.get("positiveCount"):
        official_bonus += min(10, bounded_int(official.get("positiveCount", 0), 0, 20) * 2)

    material_news = bounded_int(
        trend.get("materialNewsCount", discovery.get("materialNewsItems", 0)),
        0,
        20,
    )
    pool_bonus = candidate_pool_decision_bonus(candidate)
    readiness_penalty = 0
    if not price_readiness["displayReady"]:
        readiness_penalty = 42
    elif not price_readiness["entryReady"]:
        readiness_penalty = 20
    score = (
        base
        + gate_bonus
        + official_bonus
        + pool_bonus
        + (bounded_int(candidate.get("totalScore", 0), 0, 100) * 0.18)
        + (bounded_int(candidate.get("triggerReadiness", 0), 0, 100) * 0.16)
        + (bounded_int(confidence.get("score", 0), 0, 100) * 0.18)
        + (bounded_int(reaction.get("score", 0), 0, 100) * 0.22)
        + (bounded_int(validation.get("score", 0), 0, 100) * 0.2)
        + min(8, material_news * 2)
        + (bounded_int(score_detail.get("volume", 0), 0, 18) * 0.35)
        + (bounded_int(score_detail.get("price", 0), 0, 16) * 0.35)
        + reaction_gate_penalty
        - (risk * 1.2)
        - (heat * 0.8)
        - readiness_penalty
    )
    return bounded_int(round(score), 0, 100)


def candidate_signal_validation_profile(candidate: dict) -> dict:
    discovery = candidate.get("discovery", {}) if isinstance(candidate.get("discovery"), dict) else {}
    evidence = discovery.get("evidenceProfile", {}) if isinstance(discovery.get("evidenceProfile"), dict) else {}
    reaction = candidate.get("priceReaction", {}) if isinstance(candidate.get("priceReaction"), dict) else {}
    confidence = candidate.get("dataConfidence", {}) if isinstance(candidate.get("dataConfidence"), dict) else {}
    score_detail = candidate.get("score", {}) if isinstance(candidate.get("score"), dict) else {}
    final_decision = candidate.get("finalDecision", {}) if isinstance(candidate.get("finalDecision"), dict) else {}
    gate = candidate.get("qualityGate", {}) if isinstance(candidate.get("qualityGate"), dict) else {}
    official = candidate.get("officialSignal", {}) if isinstance(candidate.get("officialSignal"), dict) else {}
    price_readiness = candidate_price_readiness(candidate)
    evidence_strength = candidate_discovery_evidence_strength(candidate)

    evidence_grade = str(evidence.get("grade", discovery.get("evidenceGrade", "weak")))
    evidence_score = bounded_int(evidence.get("score", discovery.get("evidenceScore", 0)), 0, 100)
    reaction_key = str(reaction.get("key", "missing"))
    reaction_gate = str(reaction.get("reactionGate", "wait"))
    reaction_entry_block = bool(reaction.get("entryBlock"))
    reaction_score = bounded_int(reaction.get("score", 0), 0, 100)
    confidence_score = bounded_int(confidence.get("score", 0), 0, 100)
    risk = bounded_int(score_detail.get("riskPenalty", 0), 0, 30)
    heat = bounded_int(score_detail.get("heatPenalty", 0), 0, 20)
    action_key = str(final_decision.get("actionKey", "verify"))
    gate_key = str(gate.get("key", "defer"))
    material_news = bounded_int(evidence_strength.get("materialNews", 0), 0, 100)
    official_positive = bounded_int(official.get("positiveCount", 0), 0, 100)
    if material_news >= 2 or official_positive > 0:
        evidence_score = max(evidence_score, SIGNAL_DISCOVERY_QUALIFIED_EVIDENCE_SCORE)
    if material_news >= 3 or official_positive >= 2:
        evidence_score = max(evidence_score, SIGNAL_DISCOVERY_STRONG_EVIDENCE_SCORE)
    has_material_evidence = evidence_strength["qualified"] or evidence_grade in {"strong", "qualified"} or evidence_score >= SIGNAL_DISCOVERY_QUALIFIED_EVIDENCE_SCORE
    strong_evidence = evidence_strength["strong"] or evidence_grade == "strong" or evidence_score >= SIGNAL_DISCOVERY_STRONG_EVIDENCE_SCORE
    price_confirmed = reaction_key in {"strong", "confirmed"} and reaction_gate == "confirmed" and reaction_score >= 56 and not reaction_entry_block
    price_weak = reaction_key in {"weak", "missing"} or reaction_score < 56 or reaction_gate in {"wait", "blocked"} or reaction_entry_block
    blockers: list[str] = []
    reasons: list[str] = []

    if not price_readiness["displayReady"]:
        blockers.append(price_readiness["message"])
        price_confirmed = False
        price_weak = True
    elif not price_readiness["entryReady"]:
        blockers.append(price_readiness["message"])

    if has_material_evidence:
        reasons.append(f"발굴 근거 {evidence_score}/100")
    else:
        blockers.append("발굴 근거가 아직 약함")
    if price_confirmed:
        reasons.append(f"가격 반응 {reaction_score}/100")
    else:
        blockers.append("가격·거래량 반응 확인 필요")
    if confidence_score >= 60:
        reasons.append(f"데이터 신뢰도 {confidence_score}/100")
    else:
        blockers.append("데이터 신뢰도 보강 필요")

    if reaction_gate == "blocked":
        key, label, priority = "blocked", "가격 반응 차단", 4
        blockers.append("재료 이후 가격·거래량 반응이 부정적")
    elif official.get("riskLevel") == "high" or action_key == "stop" or risk >= 24:
        key, label, priority = "blocked", "리스크 차단", 4
        blockers.append("리스크 또는 제외 판단이 우선")
    elif not price_readiness["displayReady"]:
        key, label, priority = "insufficient", price_readiness["label"], 3
    elif not price_readiness["entryReady"] and has_material_evidence:
        key, label, priority = "evidence_wait", price_readiness["label"], 2
        blockers.append("실시간 가격·거래량·수급 반응 확인 전")
    elif not price_readiness["entryReady"]:
        key, label, priority = "insufficient", price_readiness["label"], 3
    elif strong_evidence and price_confirmed and confidence_score >= 68 and risk < 18 and heat < 10:
        key, label, priority = "confirmed", "근거+가격 확인", 0
        reasons.append("강한 근거와 가격 반응이 동시에 확인")
    elif has_material_evidence and price_confirmed and confidence_score >= 60 and risk < 20:
        key, label, priority = "confirmed", "근거+가격 확인", 1
        reasons.append("투자 근거와 시장 반응이 함께 확인")
    elif has_material_evidence and price_weak:
        key, label, priority = "evidence_wait", "재료 후 반응 대기", 2
        blockers.append("뉴스·공시 대비 자금 반응이 약함")
    elif not has_material_evidence and price_confirmed:
        key, label, priority = "reaction_only", "가격 선행 확인", 2
        blockers.append("가격은 움직였지만 근거 뉴스 검증 필요")
    else:
        key, label, priority = "insufficient", "근거·반응 부족", 3

    validation_score = bounded_int(
        evidence_score * 0.36
        + reaction_score * 0.38
        + confidence_score * 0.16
        - risk * 0.8
        - heat * 0.45
        + (8 if key == "confirmed" else 0)
        - (12 if key == "blocked" else 0),
        0,
        100,
    )
    return {
        "key": key,
        "label": label,
        "priority": priority,
        "score": validation_score,
        "entryReady": key == "confirmed",
        "evidenceScore": evidence_score,
        "evidenceGrade": evidence_grade,
        "reactionScore": reaction_score,
        "reactionKey": reaction_key,
        "reactionGate": reaction_gate,
        "confidenceScore": confidence_score,
        "reasons": unique_texts(reasons, limit=5),
        "blockers": unique_texts([*blockers, *evidence.get("blockers", []), *reaction.get("blockers", []), *reaction.get("warnings", [])], limit=6),
    }


def candidate_is_portfolio_linked(candidate: dict) -> bool:
    portfolio = candidate.get("portfolio", {}) if isinstance(candidate.get("portfolio"), dict) else {}
    holding = portfolio.get("holding", {}) if isinstance(portfolio.get("holding"), dict) else {}
    return bool(portfolio.get("isHeld") or holding)


def candidate_discovery_evidence_strength(candidate: dict) -> dict:
    discovery = candidate.get("discovery", {}) if isinstance(candidate.get("discovery"), dict) else {}
    evidence = discovery.get("evidenceProfile", {}) if isinstance(discovery.get("evidenceProfile"), dict) else {}
    trend = candidate.get("trend", {}) if isinstance(candidate.get("trend"), dict) else {}
    official = candidate.get("officialSignal", {}) if isinstance(candidate.get("officialSignal"), dict) else {}
    evidence_grade = str(evidence.get("grade", discovery.get("evidenceGrade", "weak")))
    evidence_score = bounded_int(evidence.get("score", discovery.get("evidenceScore", 0)), 0, 100)
    material_news = bounded_int(
        trend.get("materialNewsCount", discovery.get("materialNewsItems", 0)),
        0,
        1_000,
    )
    official_count = bounded_int(official.get("count", 0), 0, 100)
    official_positive = bounded_int(official.get("positiveCount", 0), 0, 100)
    strong = (
        evidence_grade in {"strong", "qualified"}
        or evidence_score >= SIGNAL_DISCOVERY_QUALIFIED_EVIDENCE_SCORE
        or material_news >= 2
        or official_positive > 0
    )
    qualified = strong or evidence_score >= 58 or material_news >= 1 or official_count > 0
    return {
        "strong": strong,
        "qualified": qualified,
        "score": evidence_score,
        "grade": evidence_grade,
        "materialNews": material_news,
        "officialCount": official_count,
    }


def candidate_core_eligible(candidate: dict) -> bool:
    final_decision = candidate.get("finalDecision", {}) if isinstance(candidate.get("finalDecision"), dict) else {}
    gate = candidate.get("qualityGate", {}) if isinstance(candidate.get("qualityGate"), dict) else {}
    confidence = candidate.get("dataConfidence", {}) if isinstance(candidate.get("dataConfidence"), dict) else {}
    reaction = candidate.get("priceReaction", {}) if isinstance(candidate.get("priceReaction"), dict) else {}
    score_detail = candidate.get("score", {}) if isinstance(candidate.get("score"), dict) else {}
    official = candidate.get("officialSignal", {}) if isinstance(candidate.get("officialSignal"), dict) else {}
    validation = candidate.get("signalValidation", {}) if isinstance(candidate.get("signalValidation"), dict) else candidate_signal_validation_profile(candidate)
    source_reliability = candidate.get("sourceReliability", {}) if isinstance(candidate.get("sourceReliability"), dict) else {}
    evidence = candidate_discovery_evidence_strength(candidate)
    price_readiness = candidate_price_readiness(candidate)
    risk = bounded_int(score_detail.get("riskPenalty", 0), 0, 30)
    heat = bounded_int(score_detail.get("heatPenalty", 0), 0, 20)
    action_key = str(final_decision.get("actionKey", ""))
    gate_key = str(gate.get("key", ""))
    reaction_gate = str(reaction.get("reactionGate", "wait"))
    confidence_score = bounded_int(confidence.get("score", 0), 0, 100)
    reliability_score = bounded_int(source_reliability.get("score", confidence_score), 0, 100)
    total = bounded_int(candidate.get("totalScore", 0), 0, 100)
    readiness = bounded_int(candidate.get("triggerReadiness", 0), 0, 100)
    reaction_score = bounded_int(reaction.get("score", 0), 0, 100)
    if candidate_is_portfolio_linked(candidate):
        return False
    if not price_readiness["entryReady"]:
        return False
    if official.get("riskLevel") in {"medium", "high"}:
        return False
    if action_key in {"exclude", "stop"} or gate_key == "exclude":
        return False
    if reaction_gate == "blocked" or (reaction.get("entryBlock") and not evidence["strong"]):
        return False
    if not evidence["qualified"]:
        return False
    return (
        total >= (70 if validation.get("entryReady") else 60)
        and readiness >= (68 if validation.get("entryReady") else 50)
        and confidence_score >= 58
        and reliability_score >= 50
        and reaction_score >= (56 if reaction_gate == "confirmed" else 28)
        and risk < 22
        and heat < 14
    )


def assign_candidate_compression(candidates: list[dict]) -> dict:
    max_core = 3
    for item in candidates:
        item["signalValidation"] = candidate_signal_validation_profile(item)
    ranked = sorted(candidates, key=candidate_compression_score, reverse=True)
    rank_by_symbol = {
        str(item.get("symbol", "")).upper(): index
        for index, item in enumerate(ranked, start=1)
        if str(item.get("symbol", "")).strip()
    }
    core_item_ids: set[int] = set()
    for item in ranked:
        if len(core_item_ids) >= max_core:
            break
        if candidate_core_eligible(item):
            core_item_ids.add(id(item))

    counts = {"core": 0, "review": 0, "wait": 0, "portfolio": 0, "exclude": 0}
    validation_counts = {"confirmed": 0, "evidence_wait": 0, "reaction_only": 0, "insufficient": 0, "blocked": 0}
    top_candidates: list[dict] = []
    for item in candidates:
        symbol = str(item.get("symbol", "")).upper()
        final_decision = item.get("finalDecision", {}) if isinstance(item.get("finalDecision"), dict) else {}
        gate = item.get("qualityGate", {}) if isinstance(item.get("qualityGate"), dict) else {}
        reaction = item.get("priceReaction", {}) if isinstance(item.get("priceReaction"), dict) else {}
        confidence = item.get("dataConfidence", {}) if isinstance(item.get("dataConfidence"), dict) else {}
        score_detail = item.get("score", {}) if isinstance(item.get("score"), dict) else {}
        official = item.get("officialSignal", {}) if isinstance(item.get("officialSignal"), dict) else {}
        price_readiness = candidate_price_readiness(item)
        action_key = str(final_decision.get("actionKey", "verify"))
        gate_key = str(gate.get("key", "defer"))
        reaction_gate = str(reaction.get("reactionGate", "wait"))
        risk = bounded_int(score_detail.get("riskPenalty", 0), 0, 30)
        validation = item.get("signalValidation", {}) if isinstance(item.get("signalValidation"), dict) else {}
        validation_key = str(validation.get("key", "insufficient"))
        validation_counts[validation_key] = validation_counts.get(validation_key, 0) + 1
        compression_score = candidate_compression_score(item)
        pool_bonus = candidate_pool_decision_bonus(item)
        evidence = candidate_discovery_evidence_strength(item)
        hard_exclude = (
            official.get("riskLevel") == "high"
            or action_key == "stop"
            or reaction_gate == "blocked"
            or risk >= 24
        )
        soft_exclude = action_key == "exclude" or gate_key == "exclude"

        if not price_readiness["displayReady"]:
            tier, label = "wait", "보강 대기"
            reason = price_readiness["message"]
        elif not price_readiness["entryReady"] and hard_exclude:
            tier, label = "exclude", "제외"
            reason = "가격 반응 데이터가 미완성이고 리스크 기준에 걸려 신규 진입 제외"
        elif not price_readiness["entryReady"]:
            if price_readiness.get("key") == "closed_baseline":
                tier, label = "wait", "장마감 관찰"
            else:
                tier, label = "wait", "보강 대기"
            reason = f"{price_readiness['message']} 진입 후보 승격은 가격·등락률·차트/호가/체결 반응 확인 후에만 허용합니다."
        elif id(item) in core_item_ids:
            tier, label = "core", "핵심"
            if validation_key == "confirmed":
                reason = "발굴 근거와 가격 반응이 동시에 확인된 압축 후보"
            else:
                reason = "강한 뉴스·공시 근거와 신뢰도 기준으로 우선 추적할 핵심 후보"
        elif hard_exclude:
            tier, label = "exclude", "제외"
            reason = "리스크나 최종 판단 기준으로 오늘 신규 진입 제외"
        elif soft_exclude and (evidence["qualified"] or validation_key in {"evidence_wait", "reaction_only"}):
            tier, label = "review", "검토"
            reason = "재료는 있으나 가격·거래량 또는 원천 데이터 확인 전이라 검토로 유지"
        elif soft_exclude:
            tier, label = "wait", "대기"
            reason = "리스크 차단은 아니지만 근거와 가격 반응이 부족해 대기"
        elif candidate_is_portfolio_linked(item):
            tier, label = "portfolio", "보유"
            reason = "보유 자산 기준으로 추가매수·보유·매도 판단 대상"
        elif validation_key == "evidence_wait":
            tier, label = "review", "검토"
            reason = "근거는 있으나 가격·거래량 반응 확인 전"
        elif validation_key == "reaction_only":
            tier, label = "review", "검토"
            reason = "가격은 움직였지만 뉴스·공시 근거 검증 필요"
        elif validation_key == "insufficient":
            tier, label = "wait", "대기"
            reason = "발굴 근거와 가격 반응이 함께 부족해 다음 갱신까지 대기"
        elif gate_key == "watch" or action_key in {"watch", "pullback"} or compression_score >= 62:
            tier, label = "review", "검토"
            reason = "재료는 있으나 가격·거래량 또는 진입가 확인이 필요"
        else:
            tier, label = "wait", "대기"
            reason = "신뢰도나 가격 반응이 부족해 다음 갱신까지 대기"

        counts[tier] = counts.get(tier, 0) + 1
        compression = {
            "tier": tier,
            "label": label,
            "rank": rank_by_symbol.get(symbol, 0),
            "score": compression_score,
            "coreLimit": max_core,
            "tradeReady": tier == "core" and validation_key == "confirmed",
            "reason": reason,
            "confidenceScore": bounded_int(confidence.get("score", 0), 0, 100),
            "reactionScore": bounded_int(reaction.get("score", 0), 0, 100),
            "validationKey": validation_key,
            "validationLabel": validation.get("label", ""),
            "poolBonus": pool_bonus,
        }
        item["candidateCompression"] = compression
        if tier == "core":
            top_candidates.append({
                "symbol": item.get("symbol", ""),
                "name": item.get("name", ""),
                "score": item.get("totalScore", 0),
                "compressionScore": compression_score,
                "decision": final_decision.get("action", ""),
                "reason": reason,
                "validation": validation.get("label", ""),
            })

    return {
        "candidateCompressionCounts": counts,
        "coreCandidateCount": counts.get("core", 0),
        "reviewCandidateCount": counts.get("review", 0),
        "waitCandidateCompressionCount": counts.get("wait", 0),
        "portfolioCandidateCompressionCount": counts.get("portfolio", 0),
        "excludeCandidateCompressionCount": counts.get("exclude", 0),
        "compressedTopCandidates": top_candidates,
        "coreCandidateLimit": max_core,
        "signalValidationCounts": validation_counts,
        "confirmedSignalCount": validation_counts.get("confirmed", 0),
        "evidenceWaitSignalCount": validation_counts.get("evidence_wait", 0),
        "reactionOnlySignalCount": validation_counts.get("reaction_only", 0),
        "insufficientSignalCount": validation_counts.get("insufficient", 0),
        "blockedSignalCount": validation_counts.get("blocked", 0),
    }


CANDIDATE_POOL_STATES = {
    "collected": {"label": "수집됨", "rank": 10},
    "watching": {"label": "관찰중", "rank": 20},
    "validating": {"label": "검증중", "rank": 30},
    "entry_candidate": {"label": "진입 후보", "rank": 40},
    "pullback_wait": {"label": "눌림 대기", "rank": 35},
    "portfolio": {"label": "보유 판단", "rank": 34},
    "excluded": {"label": "제외", "rank": 5},
    "expired": {"label": "만료", "rank": 0},
}


def candidate_pool_decision_bonus(candidate: dict) -> int:
    discovery = candidate.get("discovery", {}) if isinstance(candidate.get("discovery"), dict) else {}
    memory = discovery.get("poolMemory", {}) if isinstance(discovery.get("poolMemory"), dict) else {}
    pool = candidate.get("candidatePool", {}) if isinstance(candidate.get("candidatePool"), dict) else {}
    state_key = str(pool.get("stateKey") or memory.get("stateKey") or "")
    if state_key in {"excluded", "expired"}:
        return -10
    pool_score = bounded_int(memory.get("score", discovery.get("poolScore", pool.get("retainScore", 0))), 0, 100)
    observations = bounded_int(pool.get("observations", memory.get("observations", 0)), 0, 100_000)
    selected_count = bounded_int(pool.get("selectedCount", memory.get("selectedCount", 0)), 0, 100_000)
    score_delta = bounded_int(pool.get("scoreDelta", 0), -100, 100)
    performance_measured = bounded_int(pool.get("performanceMeasuredCount", memory.get("performanceMeasuredCount", 0)), 0, 100_000)
    performance_hit_rate = (
        decimal_or_none(pool.get("performanceHitRateValue", memory.get("performanceHitRateValue")))
        or display_percent_to_decimal(pool.get("performanceHitRate", memory.get("performanceHitRate")))
        or Decimal("0")
    )
    performance_average = (
        decimal_or_none(pool.get("performanceAverageChangeRate", memory.get("performanceAverageChangeRate")))
        or display_percent_to_decimal(pool.get("performanceAverageChange", memory.get("performanceAverageChange")))
        or Decimal("0")
    )
    performance_latest = str(pool.get("performanceLatestOutcome", memory.get("performanceLatestOutcome", "")))
    state_bonus = {
        "entry_candidate": 8,
        "pullback_wait": 6,
        "portfolio": 5,
        "validating": 5,
        "watching": 3,
        "collected": 0,
    }.get(state_key, 0)
    momentum_bonus = 2 if score_delta >= 5 else (-3 if score_delta <= -5 else 0)
    performance_bonus = 0
    if performance_measured:
        if performance_measured >= 3 and performance_hit_rate >= Decimal("60"):
            performance_bonus += 3
        elif performance_measured >= 3 and performance_hit_rate < Decimal("35"):
            performance_bonus -= 4
        if performance_average >= Decimal("1"):
            performance_bonus += 3
        elif performance_average <= Decimal("-1"):
            performance_bonus -= 4
        if performance_latest == "상승":
            performance_bonus += 2
        elif performance_latest == "하락":
            performance_bonus -= 2
    return bounded_int(
        state_bonus
        + min(7, pool_score // 14)
        + min(3, observations // 3)
        + min(3, selected_count)
        + momentum_bonus
        + performance_bonus,
        -10,
        18,
    )


def candidate_pool_rank(state_key: str) -> int:
    return CANDIDATE_POOL_STATES.get(state_key, {}).get("rank", 0)


def candidate_pool_empty() -> dict:
    return {
        "version": 1,
        "updatedAt": "",
        "items": {},
    }


def candidate_pool_data() -> dict:
    stored = db_read_kv("candidate_pool", None) if database_storage_enabled() else None
    data = stored if isinstance(stored, dict) else read_json(CANDIDATE_POOL_FILE, candidate_pool_empty())
    if not isinstance(data, dict):
        return candidate_pool_empty()
    if not isinstance(data.get("items"), dict):
        data["items"] = {}
    return data


def candidate_pool_state(candidate: dict, stage: str = "selected", existing: dict | None = None) -> tuple[str, str]:
    discovery = candidate.get("discovery", {}) if isinstance(candidate.get("discovery"), dict) else {}
    evidence = discovery.get("evidenceProfile", {}) if isinstance(discovery.get("evidenceProfile"), dict) else {}
    final_decision = candidate.get("finalDecision", {}) if isinstance(candidate.get("finalDecision"), dict) else {}
    compression = candidate.get("candidateCompression", {}) if isinstance(candidate.get("candidateCompression"), dict) else {}
    validation = candidate.get("signalValidation", {}) if isinstance(candidate.get("signalValidation"), dict) else {}
    quality = discovery.get("qualityProfile", {}) if isinstance(discovery.get("qualityProfile"), dict) else {}
    official = candidate.get("officialSignal", {}) if isinstance(candidate.get("officialSignal"), dict) else {}
    score_detail = candidate.get("score", {}) if isinstance(candidate.get("score"), dict) else {}
    trade_gate = candidate_trade_data_gate(candidate)

    action_key = str(final_decision.get("actionKey", ""))
    compression_tier = str(compression.get("tier", ""))
    validation_key = str(validation.get("key", ""))
    evidence_score = bounded_int(evidence.get("score", discovery.get("evidenceScore", 0)), 0, 100)
    quality_tier = str(discovery.get("qualityTier", quality.get("tier", "")))
    risk = bounded_int(score_detail.get("riskPenalty", 0), 0, 30)
    previous_state = str((existing or {}).get("stateKey", ""))

    if official.get("riskLevel") == "high" or action_key == "stop" or compression_tier == "exclude" or risk >= 24:
        return "excluded", "리스크 또는 제외 판단으로 신규 진입 대상에서 제외"
    if candidate_is_portfolio_linked(candidate):
        return "portfolio", "보유 자산과 연결되어 추가매수·보유·매도 판단 대상"
    if not trade_gate["displayReady"]:
        if stage == "discovered" and candidate_pool_rank(previous_state) >= candidate_pool_rank("validating"):
            return "validating", f"{trade_gate['reason']} · 기존 검증 후보로 유지하되 진입 후보 승격은 차단"
        return "watching", f"{trade_gate['reason']} · 가격/등락률 보강 전까지 관찰 풀에만 유지"
    if not trade_gate["tradeReady"]:
        if action_key == "pullback":
            return "pullback_wait", "재료는 있으나 실시간 거래 반응 확인 전이라 눌림 구간만 관찰"
        return "validating", f"{trade_gate['reason']} · 실시간 반응 확인 전까지 진입 후보 승격 차단"
    if compression_tier == "core" or (action_key in {"buy", "add"} and validation_key == "confirmed"):
        return "entry_candidate", "근거와 가격 반응이 확인되어 오늘 판단 후보로 승격"
    if action_key == "pullback":
        return "pullback_wait", "재료는 있으나 가격이 이미 반응해 눌림 구간 대기"
    if validation_key in {"evidence_wait", "reaction_only"}:
        return "validating", "재료와 가격 반응 중 하나가 부족해 검증 중"
    if action_key in {"watch", "verify"} or compression_tier in {"review", "wait"}:
        return "watching", "조건은 감지됐지만 진입 전 추가 확인 필요"
    if stage == "discovered" and (quality_tier in {"primary", "reserve"} or evidence_score >= SIGNAL_DISCOVERY_QUALIFIED_EVIDENCE_SCORE):
        if candidate_pool_rank(previous_state) >= candidate_pool_rank("validating"):
            return previous_state, "이전 검증 상태를 유지하고 정밀 분석 결과로 강등 여부를 확인"
        return "watching", "수집 단계에서 의미 있는 근거가 감지되어 관찰 풀에 유지"
    if stage == "discovered" and candidate_pool_rank(previous_state) >= candidate_pool_rank("validating"):
        return previous_state, "수집 단계의 약한 신호만으로 기존 고신뢰 상태를 낮추지 않음"
    return "collected", "봇이 발견했지만 아직 투자 판단 근거는 부족"


def candidate_pool_record(candidate: dict, existing: dict, mode: str, stage: str, now: datetime) -> tuple[dict, bool]:
    symbol = str(candidate.get("symbol", "")).strip().upper()
    discovery = candidate.get("discovery", {}) if isinstance(candidate.get("discovery"), dict) else {}
    evidence = discovery.get("evidenceProfile", {}) if isinstance(discovery.get("evidenceProfile"), dict) else {}
    validation = candidate.get("signalValidation", {}) if isinstance(candidate.get("signalValidation"), dict) else {}
    compression = candidate.get("candidateCompression", {}) if isinstance(candidate.get("candidateCompression"), dict) else {}
    final_decision = candidate.get("finalDecision", {}) if isinstance(candidate.get("finalDecision"), dict) else {}
    confidence = candidate.get("dataConfidence", {}) if isinstance(candidate.get("dataConfidence"), dict) else {}
    reaction = candidate.get("priceReaction", {}) if isinstance(candidate.get("priceReaction"), dict) else {}
    previous_state = str(existing.get("stateKey", ""))
    desired_state, desired_reason = candidate_pool_state(candidate, stage, existing)
    trade_gate = candidate_trade_data_gate(candidate)
    now_text = now.isoformat(timespec="seconds")
    previous_rank = candidate_pool_rank(previous_state)
    desired_rank = candidate_pool_rank(desired_state)
    soft_demotion_count = bounded_int(existing.get("softDemotionCount", 0), 0, 100_000)
    demotion_confirmations = max(1, SIGNAL_CANDIDATE_POOL_DEMOTION_CONFIRMATIONS)
    force_state_change = desired_state in {"excluded", "expired"} or desired_rank >= previous_rank or not previous_state
    if previous_state == "entry_candidate" and desired_state != "entry_candidate" and not trade_gate["tradeReady"]:
        force_state_change = True
    if stage == "selected" and previous_rank > desired_rank and not force_state_change:
        soft_demotion_count += 1
        if soft_demotion_count < demotion_confirmations:
            state_key = previous_state
            state_reason = f"{desired_reason} · {soft_demotion_count}/{demotion_confirmations}회 약화 확인, 급격한 강등 보류"
        else:
            state_key = desired_state
            state_reason = f"{desired_reason} · {soft_demotion_count}회 연속 약화되어 강등"
            soft_demotion_count = 0
    else:
        state_key = desired_state
        state_reason = desired_reason
        if desired_rank >= previous_rank or desired_state in {"excluded", "expired"}:
            soft_demotion_count = 0
    current_score = bounded_int(candidate.get("totalScore", existing.get("totalScore", 0)), 0, 100)
    current_readiness = bounded_int(candidate.get("triggerReadiness", existing.get("triggerReadiness", 0)), 0, 100)
    current_confidence = bounded_int(confidence.get("score", existing.get("confidenceScore", 0)), 0, 100)
    current_reaction = bounded_int(reaction.get("score", existing.get("reactionScore", 0)), 0, 100)
    current_evidence = bounded_int(evidence.get("score", discovery.get("evidenceScore", existing.get("evidenceScore", 0))), 0, 100)
    previous_score = bounded_int(existing.get("totalScore", current_score), 0, 100)
    score_delta = current_score - previous_score
    if score_delta >= 5:
        momentum_label = "개선"
    elif score_delta <= -5:
        momentum_label = "약화"
    else:
        momentum_label = "유지"

    record = dict(existing)
    record.update({
        "symbol": symbol,
        "name": candidate.get("name", existing.get("name", symbol)),
        "market": candidate.get("market", existing.get("market", "")),
        "category": candidate.get("category", existing.get("category", "")),
        "headline": candidate.get("headline", existing.get("headline", "")),
        "price": candidate.get("price", existing.get("price", "-")),
        "change": candidate.get("change", existing.get("change", "-")),
        "stateKey": state_key,
        "stateLabel": CANDIDATE_POOL_STATES.get(state_key, {}).get("label", state_key),
        "stateReason": state_reason,
        "lastMode": mode,
        "lastStage": stage,
        "lastSeenAt": now_text,
        "observations": bounded_int(existing.get("observations", 0), 0, 100_000) + 1,
        "totalScore": current_score,
        "triggerReadiness": current_readiness,
        "confidenceScore": current_confidence,
        "reactionScore": current_reaction,
        "evidenceScore": current_evidence,
        "peakScore": max(bounded_int(existing.get("peakScore", 0), 0, 100), current_score),
        "peakReadiness": max(bounded_int(existing.get("peakReadiness", 0), 0, 100), current_readiness),
        "peakConfidenceScore": max(bounded_int(existing.get("peakConfidenceScore", 0), 0, 100), current_confidence),
        "peakReactionScore": max(bounded_int(existing.get("peakReactionScore", 0), 0, 100), current_reaction),
        "peakEvidenceScore": max(bounded_int(existing.get("peakEvidenceScore", 0), 0, 100), current_evidence),
        "scoreDelta": score_delta,
        "momentumLabel": momentum_label,
        "softDemotionCount": soft_demotion_count,
        "evidenceGrade": evidence.get("grade", discovery.get("evidenceGrade", existing.get("evidenceGrade", ""))),
        "validationKey": validation.get("key", existing.get("validationKey", "")),
        "validationLabel": validation.get("label", existing.get("validationLabel", "")),
        "compressionTier": compression.get("tier", existing.get("compressionTier", "")),
        "compressionLabel": compression.get("label", existing.get("compressionLabel", "")),
        "finalActionKey": final_decision.get("actionKey", existing.get("finalActionKey", "")),
        "finalAction": final_decision.get("action", existing.get("finalAction", "")),
        "newsItems": bounded_int(discovery.get("newsItems", existing.get("newsItems", 0)), 0, 100_000),
        "materialNewsItems": bounded_int(discovery.get("materialNewsItems", existing.get("materialNewsItems", 0)), 0, 100_000),
        "qualityTier": discovery.get("qualityTier", existing.get("qualityTier", "")),
        "reactionGate": reaction.get("reactionGate", existing.get("reactionGate", "")),
        "reactionEntryBlock": bool(reaction.get("entryBlock", existing.get("reactionEntryBlock", False))),
        "tradeDataReady": bool(trade_gate["tradeReady"]),
        "displayDataReady": bool(trade_gate["displayReady"]),
        "dataGateLabel": trade_gate["label"],
        "dataGateReason": trade_gate["reason"],
        "missingData": trade_gate["missing"],
        "sourceReliabilityScore": bounded_int(
            candidate.get("sourceReliability", {}).get("score", existing.get("sourceReliabilityScore", 0))
            if isinstance(candidate.get("sourceReliability"), dict)
            else existing.get("sourceReliabilityScore", 0),
            0,
            100,
        ),
        "updatedAt": now_text,
    })
    record.update(candidate_pool_monitor_profile(record))
    if not record.get("firstSeenAt"):
        record["firstSeenAt"] = now_text
    if stage == "selected":
        record["lastSelectedAt"] = now_text
        record["selectedCount"] = bounded_int(existing.get("selectedCount", 0), 0, 100_000) + 1

    changed = state_key != previous_state
    if changed:
        record["stateChangedAt"] = now_text
        record["stateChangeCount"] = bounded_int(existing.get("stateChangeCount", 0), 0, 100_000) + 1
        if previous_state and desired_rank > previous_rank:
            record["promotionCount"] = bounded_int(existing.get("promotionCount", 0), 0, 100_000) + 1
        elif previous_state and desired_rank < previous_rank:
            record["demotionCount"] = bounded_int(existing.get("demotionCount", 0), 0, 100_000) + 1
        history = existing.get("transitionHistory", [])
        if not isinstance(history, list):
            history = []
        history.append({
            "at": now_text,
            "from": previous_state or "-",
            "to": state_key,
            "fromLabel": CANDIDATE_POOL_STATES.get(previous_state, {}).get("label", previous_state or "-"),
            "toLabel": CANDIDATE_POOL_STATES.get(state_key, {}).get("label", state_key),
            "mode": mode,
            "stage": stage,
            "reason": state_reason,
            "score": current_score,
        })
        record["transitionHistory"] = history[-8:]
    elif not record.get("stateChangedAt"):
        record["stateChangedAt"] = now_text

    promoted = bool(previous_state) and previous_state not in {"entry_candidate", "portfolio"} and state_key in {"entry_candidate", "portfolio"}
    return record, promoted


def expire_candidate_pool_items(items: dict, now: datetime) -> int:
    if SIGNAL_CANDIDATE_POOL_TTL_DAYS <= 0:
        return 0
    expired = 0
    threshold = now - timedelta(days=SIGNAL_CANDIDATE_POOL_TTL_DAYS)
    for record in items.values():
        if not isinstance(record, dict):
            continue
        if record.get("stateKey") == "expired":
            continue
        last_seen = parse_iso_datetime(str(record.get("lastSeenAt", "")))
        if last_seen and last_seen.astimezone(KST) < threshold:
            record["stateKey"] = "expired"
            record["stateLabel"] = CANDIDATE_POOL_STATES["expired"]["label"]
            record["stateReason"] = f"{SIGNAL_CANDIDATE_POOL_TTL_DAYS}일 동안 새 근거가 없어 만료"
            record["updatedAt"] = now.isoformat(timespec="seconds")
            expired += 1
    return expired


def trim_candidate_pool_items(items: dict) -> int:
    if SIGNAL_CANDIDATE_POOL_MAX_ITEMS <= 0 or len(items) <= SIGNAL_CANDIDATE_POOL_MAX_ITEMS:
        return 0
    ranked = sorted(
        items.items(),
        key=lambda pair: (
            CANDIDATE_POOL_STATES.get(str(pair[1].get("stateKey", "")), {}).get("rank", 0),
            bounded_int(pair[1].get("totalScore", 0), 0, 100),
            str(pair[1].get("lastSeenAt", "")),
        ),
        reverse=True,
    )
    keep = {symbol for symbol, _record in ranked[:SIGNAL_CANDIDATE_POOL_MAX_ITEMS]}
    removed = 0
    for symbol in list(items.keys()):
        if symbol not in keep:
            items.pop(symbol, None)
            removed += 1
    return removed


def candidate_pool_performance_metrics(history: list[dict]) -> dict:
    measured = [
        item
        for item in history
        if isinstance(item, dict) and item.get("measured", True) and decimal_or_none(item.get("changeRate")) is not None
    ]
    measured.sort(key=lambda item: str(item.get("observedAt") or item.get("createdAt") or ""), reverse=True)
    changes = [decimal_or_none(item.get("changeRate")) for item in measured]
    changes = [change for change in changes if change is not None]
    positive = [item for item in measured if item.get("outcome") == "상승"]
    negative = [item for item in measured if item.get("outcome") == "하락"]
    neutral = [item for item in measured if item.get("outcome") == "중립"]
    average = decimal_average(changes) if changes else Decimal("0")
    hit_rate = (Decimal(len(positive)) / Decimal(len(measured)) * Decimal(100)) if measured else Decimal("0")
    latest = measured[0] if measured else {}
    latest_change = decimal_or_none(latest.get("changeRate"))
    return {
        "performanceMeasuredCount": len(measured),
        "performancePositiveCount": len(positive),
        "performanceNegativeCount": len(negative),
        "performanceNeutralCount": len(neutral),
        "performanceHitRate": display_percent_abs(hit_rate) if measured else "-",
        "performanceHitRateValue": str(hit_rate.quantize(Decimal("0.01"))) if measured else "0",
        "performanceAverageChange": display_decimal_percent(average) if measured else "-",
        "performanceAverageChangeRate": str(average.quantize(Decimal("0.01"))) if measured else "0",
        "performanceLatestChange": display_decimal_percent(latest_change) if latest_change is not None else "-",
        "performanceLatestChangeRate": str(latest_change.quantize(Decimal("0.01"))) if latest_change is not None else "0",
        "performanceLatestOutcome": latest.get("outcome", "-") if latest else "-",
        "performanceLatestAt": latest.get("observedAt") or latest.get("createdAt") or "",
    }


def candidate_pool_performance_bonus(record: dict) -> int:
    measured_count = bounded_int(record.get("performanceMeasuredCount", 0), 0, 100_000)
    if not measured_count:
        return 0
    hit_rate = (
        decimal_or_none(record.get("performanceHitRateValue"))
        or display_percent_to_decimal(record.get("performanceHitRate"))
        or Decimal("0")
    )
    average = (
        decimal_or_none(record.get("performanceAverageChangeRate"))
        or display_percent_to_decimal(record.get("performanceAverageChange"))
        or Decimal("0")
    )
    latest_outcome = str(record.get("performanceLatestOutcome", ""))
    bonus = bounded_int(average * Decimal("1.5"), -6, 6)
    if measured_count >= 3 and hit_rate >= Decimal("60"):
        bonus += 5
    elif measured_count >= 3 and hit_rate < Decimal("35"):
        bonus -= 8
    if latest_outcome == "상승":
        bonus += 3
    elif latest_outcome == "하락":
        bonus -= 4
    return bounded_int(bonus, -12, 10)


def candidate_pool_performance_fields(record: dict) -> dict:
    keys = [
        "performanceMeasuredCount",
        "performancePositiveCount",
        "performanceNegativeCount",
        "performanceNeutralCount",
        "performanceHitRate",
        "performanceHitRateValue",
        "performanceAverageChange",
        "performanceAverageChangeRate",
        "performanceLatestChange",
        "performanceLatestChangeRate",
        "performanceLatestOutcome",
        "performanceLatestAt",
    ]
    return {key: record.get(key) for key in keys if key in record}


def candidate_pool_summary(data: dict | None = None) -> dict:
    payload = data if isinstance(data, dict) else candidate_pool_data()
    items = payload.get("items", {}) if isinstance(payload.get("items"), dict) else {}
    counts: dict[str, int] = {key: 0 for key in CANDIDATE_POOL_STATES}
    active_count = 0
    promotion_count = 0
    demotion_count = 0
    soft_demotion_count = 0
    improving_count = 0
    weakening_count = 0
    performance_symbol_count = 0
    performance_measured_count = 0
    performance_positive_count = 0
    performance_negative_count = 0
    performance_neutral_count = 0
    performance_change_weighted_total = Decimal("0")
    performance_latest_at = ""
    monitor_ready_count = 0
    monitor_wait_count = 0
    monitor_weak_count = 0
    top_records: list[dict] = []
    for record in items.values():
        if not isinstance(record, dict):
            continue
        key = str(record.get("stateKey", "collected"))
        counts[key] = counts.get(key, 0) + 1
        if key not in {"excluded", "expired"}:
            active_count += 1
        promotion_count += bounded_int(record.get("promotionCount", 0), 0, 100_000)
        demotion_count += bounded_int(record.get("demotionCount", 0), 0, 100_000)
        soft_demotion_count += bounded_int(record.get("softDemotionCount", 0), 0, 100_000)
        momentum = str(record.get("momentumLabel", ""))
        if momentum == "개선":
            improving_count += 1
        elif momentum == "약화":
            weakening_count += 1
        monitor_profile = candidate_pool_monitor_profile(record)
        monitor_score = bounded_int(monitor_profile.get("monitorScore", record.get("monitorScore", 0)), 0, 100)
        monitor_label = str(monitor_profile.get("monitorLabel", record.get("monitorLabel", "")))
        monitor_reason = str(monitor_profile.get("monitorReason", record.get("monitorReason", "")))
        if monitor_score >= 72:
            monitor_ready_count += 1
        elif monitor_score >= 55:
            monitor_wait_count += 1
        elif key not in {"excluded", "expired"}:
            monitor_weak_count += 1
        performance_count = bounded_int(record.get("performanceMeasuredCount", 0), 0, 100_000)
        if performance_count:
            performance_symbol_count += 1
            performance_measured_count += performance_count
            performance_positive_count += bounded_int(record.get("performancePositiveCount", 0), 0, 100_000)
            performance_negative_count += bounded_int(record.get("performanceNegativeCount", 0), 0, 100_000)
            performance_neutral_count += bounded_int(record.get("performanceNeutralCount", 0), 0, 100_000)
            average_change = decimal_or_none(record.get("performanceAverageChangeRate"))
            if average_change is not None:
                performance_change_weighted_total += average_change * Decimal(performance_count)
            latest_at = str(record.get("performanceLatestAt", ""))
            if latest_at > performance_latest_at:
                performance_latest_at = latest_at
        if key not in {"excluded", "expired"}:
            top_record = {
                "symbol": record.get("symbol", ""),
                "name": record.get("name", record.get("symbol", "")),
                "stateKey": key,
                "stateLabel": record.get("stateLabel") or CANDIDATE_POOL_STATES.get(key, {}).get("label", key),
                "score": bounded_int(record.get("totalScore", 0), 0, 100),
                "peakScore": bounded_int(record.get("peakScore", record.get("totalScore", 0)), 0, 100),
                "readiness": bounded_int(record.get("triggerReadiness", 0), 0, 100),
                "evidenceScore": bounded_int(record.get("evidenceScore", 0), 0, 100),
                "reactionScore": bounded_int(record.get("reactionScore", 0), 0, 100),
                "monitorScore": monitor_score,
                "monitorLabel": monitor_label,
                "monitorReason": monitor_reason,
                "reactionGate": record.get("reactionGate", ""),
                "observations": bounded_int(record.get("observations", 0), 0, 100_000),
                "selectedCount": bounded_int(record.get("selectedCount", 0), 0, 100_000),
                "momentumLabel": momentum,
                "scoreDelta": bounded_int(record.get("scoreDelta", 0), -100, 100),
                "lastSeenAt": record.get("lastSeenAt", ""),
                "reason": record.get("stateReason", ""),
            }
            top_record.update(candidate_pool_performance_fields(record))
            top_records.append(top_record)
    top_records.sort(
        key=lambda record: (
            candidate_pool_rank(str(record.get("stateKey", ""))),
            bounded_int(record.get("monitorScore", 0), 0, 100),
            bounded_int(record.get("peakScore", 0), 0, 100),
            bounded_int(record.get("score", 0), 0, 100),
            bounded_int(record.get("evidenceScore", 0), 0, 100),
            bounded_int(record.get("reactionScore", 0), 0, 100),
            bounded_int(record.get("observations", 0), 0, 100_000),
            str(record.get("lastSeenAt", "")),
        ),
        reverse=True,
    )
    performance_hit_rate = (
        Decimal(performance_positive_count) / Decimal(performance_measured_count) * Decimal(100)
        if performance_measured_count
        else Decimal("0")
    )
    performance_average_change = (
        performance_change_weighted_total / Decimal(performance_measured_count)
        if performance_measured_count
        else Decimal("0")
    )
    return {
        "enabled": SIGNAL_CANDIDATE_POOL_ENABLED,
        "file": display_local_path(CANDIDATE_POOL_FILE),
        "totalCount": len(items),
        "activeCount": active_count,
        "statusCounts": counts,
        "promotionCount": promotion_count,
        "demotionCount": demotion_count,
        "softDemotionCount": soft_demotion_count,
        "improvingCount": improving_count,
        "weakeningCount": weakening_count,
        "monitorReadyCount": monitor_ready_count,
        "monitorWaitCount": monitor_wait_count,
        "monitorWeakCount": monitor_weak_count,
        "performanceSymbolCount": performance_symbol_count,
        "performanceMeasuredCount": performance_measured_count,
        "performancePositiveCount": performance_positive_count,
        "performanceNegativeCount": performance_negative_count,
        "performanceNeutralCount": performance_neutral_count,
        "performanceHitRate": display_percent_abs(performance_hit_rate) if performance_measured_count else "-",
        "performanceAverageChange": display_decimal_percent(performance_average_change) if performance_measured_count else "-",
        "performanceLatestAt": performance_latest_at,
        "updatedAt": payload.get("updatedAt", ""),
        "maxItems": SIGNAL_CANDIDATE_POOL_MAX_ITEMS,
        "ttlDays": SIGNAL_CANDIDATE_POOL_TTL_DAYS,
        "demotionConfirmations": max(1, SIGNAL_CANDIDATE_POOL_DEMOTION_CONFIRMATIONS),
        "scanLimit": SIGNAL_CANDIDATE_POOL_SCAN_LIMIT,
        "retainLimit": SIGNAL_CANDIDATE_POOL_RETAIN_LIMIT,
        "retainMinScore": SIGNAL_CANDIDATE_POOL_RETAIN_MIN_SCORE,
        "topCandidates": top_records[: max(0, SIGNAL_CANDIDATE_POOL_TOP_LIMIT)],
        "topLimit": SIGNAL_CANDIDATE_POOL_TOP_LIMIT,
    }


def candidate_pool_selection_score(record: dict) -> int:
    state_key = str(record.get("stateKey", "collected"))
    if state_key in {"excluded", "expired"}:
        return 0
    state_bonus = {
        "entry_candidate": 30,
        "pullback_wait": 24,
        "portfolio": 22,
        "validating": 20,
        "watching": 10,
        "collected": 0,
    }.get(state_key, 0)
    peak_score = bounded_int(record.get("peakScore", record.get("totalScore", 0)), 0, 100)
    score = bounded_int(record.get("totalScore", 0), 0, 100)
    readiness = bounded_int(record.get("peakReadiness", record.get("triggerReadiness", 0)), 0, 100)
    evidence = bounded_int(record.get("peakEvidenceScore", record.get("evidenceScore", 0)), 0, 100)
    reaction = bounded_int(record.get("peakReactionScore", record.get("reactionScore", 0)), 0, 100)
    selected = min(10, bounded_int(record.get("selectedCount", 0), 0, 100_000))
    observations = min(12, bounded_int(record.get("observations", 0), 0, 100_000))
    momentum_penalty = 8 if str(record.get("momentumLabel", "")) == "약화" else 0
    performance_bonus = candidate_pool_performance_bonus(record)
    return bounded_int(
        state_bonus
        + peak_score * 0.24
        + score * 0.18
        + readiness * 0.16
        + evidence * 0.14
        + reaction * 0.14
        + selected
        + observations // 2
        + performance_bonus
        - momentum_penalty,
        0,
        100,
    )


def candidate_pool_monitor_profile(record: dict) -> dict:
    state_key = str(record.get("stateKey", "collected"))
    if state_key in {"excluded", "expired"}:
        return {
            "monitorScore": 0,
            "monitorLabel": "감시 제외",
            "monitorReason": record.get("stateReason", "제외 또는 만료 상태"),
        }

    selection_score = candidate_pool_selection_score(record)
    evidence = max(
        bounded_int(record.get("evidenceScore", 0), 0, 100),
        bounded_int(record.get("peakEvidenceScore", 0), 0, 100),
    )
    reaction = max(
        bounded_int(record.get("reactionScore", 0), 0, 100),
        bounded_int(record.get("peakReactionScore", 0), 0, 100),
    )
    confidence = max(
        bounded_int(record.get("confidenceScore", 0), 0, 100),
        bounded_int(record.get("peakConfidenceScore", 0), 0, 100),
        bounded_int(record.get("sourceReliabilityScore", 0), 0, 100),
    )
    readiness = max(
        bounded_int(record.get("triggerReadiness", 0), 0, 100),
        bounded_int(record.get("peakReadiness", 0), 0, 100),
    )
    reaction_gate = str(record.get("reactionGate", ""))
    validation_key = str(record.get("validationKey", ""))
    final_action = str(record.get("finalActionKey", ""))
    performance_measured = bounded_int(record.get("performanceMeasuredCount", 0), 0, 100_000)
    performance_average = (
        decimal_or_none(record.get("performanceAverageChangeRate"))
        or display_percent_to_decimal(record.get("performanceAverageChange"))
        or Decimal("0")
    )
    performance_hit_rate = (
        decimal_or_none(record.get("performanceHitRateValue"))
        or display_percent_to_decimal(record.get("performanceHitRate"))
        or Decimal("0")
    )

    score = selection_score
    if reaction_gate == "confirmed":
        score += 8
    elif reaction_gate == "blocked":
        score -= 18
    elif bool(record.get("reactionEntryBlock")):
        score -= 8
    if evidence >= 65 and reaction >= 56 and confidence >= 60:
        score += 8
    if readiness >= 70:
        score += 5
    if str(record.get("momentumLabel", "")) == "개선":
        score += 4
    elif str(record.get("momentumLabel", "")) == "약화":
        score -= 6
    if performance_measured >= 3 and performance_average <= Decimal("-1") and performance_hit_rate < Decimal("40"):
        score -= 10
    elif performance_measured >= 3 and performance_average >= Decimal("1") and performance_hit_rate >= Decimal("50"):
        score += 6

    score = bounded_int(score, 0, 100)
    if final_action in {"buy", "add"} or state_key == "entry_candidate":
        label = "핵심 재검토"
        reason = "최종 판단 또는 후보 풀 상태가 진입 후보에 가까움"
    elif evidence >= 65 and reaction_gate != "confirmed":
        label = "반응 대기"
        reason = "근거는 있으나 가격·거래량 반응 확인 전"
    elif reaction_gate == "confirmed" and evidence < 60:
        label = "근거 보강"
        reason = "가격은 반응했지만 뉴스·공시 근거 보강 필요"
    elif state_key == "pullback_wait" or final_action == "pullback":
        label = "눌림 감시"
        reason = "재료와 관심은 있으나 추격보다 가격대 확인 필요"
    elif validation_key in {"evidence_wait", "reaction_only"} or state_key == "validating":
        label = "검증 지속"
        reason = "재료와 가격 반응 중 한 축을 계속 확인"
    elif performance_measured >= 3 and performance_average <= Decimal("-1"):
        label = "성과 약화"
        reason = "최근 후보 선정 이후 성과가 약해 재진입 기준 강화"
    elif score >= 55:
        label = "관찰 유지"
        reason = "후보 풀 점수가 유지되어 다음 스캔에서도 확인"
    else:
        label = "낮은 우선"
        reason = "현재는 근거·가격 반응·성과 중 강한 축이 부족"

    return {
        "monitorScore": score,
        "monitorLabel": label,
        "monitorReason": reason,
    }


def candidate_pool_memory_payload(record: dict) -> dict:
    score = bounded_int(record.get("retainScore", candidate_pool_selection_score(record)), 0, 100)
    state_key = str(record.get("stateKey", "collected"))
    monitor = candidate_pool_monitor_profile(record)
    payload = {
        "retained": True,
        "score": score,
        "stateKey": state_key,
        "stateLabel": record.get("stateLabel") or CANDIDATE_POOL_STATES.get(state_key, {}).get("label", state_key),
        "stateReason": record.get("stateReason", ""),
        "peakScore": bounded_int(record.get("peakScore", record.get("totalScore", 0)), 0, 100),
        "peakReadiness": bounded_int(record.get("peakReadiness", record.get("triggerReadiness", 0)), 0, 100),
        "observations": bounded_int(record.get("observations", 0), 0, 100_000),
        "selectedCount": bounded_int(record.get("selectedCount", 0), 0, 100_000),
        "monitorScore": monitor.get("monitorScore", 0),
        "monitorLabel": monitor.get("monitorLabel", ""),
        "monitorReason": monitor.get("monitorReason", ""),
        "lastSeenAt": record.get("lastSeenAt", ""),
        "reason": monitor.get("monitorReason") or "후보 풀에서 의미 있는 상태가 유지되어 재점검 대상",
    }
    payload.update(candidate_pool_performance_fields(record))
    return payload


def candidate_pool_retainable_records(limit: int | None = None) -> list[dict]:
    selected_limit = limit if limit is not None else SIGNAL_CANDIDATE_POOL_SCAN_LIMIT
    if not SIGNAL_CANDIDATE_POOL_ENABLED or selected_limit <= 0:
        return []
    data = candidate_pool_data()
    items = data.get("items", {}) if isinstance(data.get("items"), dict) else {}
    records = []
    keep_states = {"entry_candidate", "pullback_wait", "portfolio", "validating", "watching"}
    for record in items.values():
        if not isinstance(record, dict):
            continue
        symbol = str(record.get("symbol", "")).strip().upper()
        state_key = str(record.get("stateKey", "collected"))
        if not symbol or state_key in {"excluded", "expired"}:
            continue
        retain_score = candidate_pool_selection_score(record)
        monitor = candidate_pool_monitor_profile(record)
        monitor_score = bounded_int(monitor.get("monitorScore", 0), 0, 100)
        if max(retain_score, monitor_score) < SIGNAL_CANDIDATE_POOL_RETAIN_MIN_SCORE and state_key not in keep_states:
            continue
        item = dict(record)
        item["symbol"] = symbol
        item["retainScore"] = retain_score
        item["monitorScore"] = monitor_score
        item["monitorLabel"] = monitor.get("monitorLabel", item.get("monitorLabel", ""))
        item["monitorReason"] = monitor.get("monitorReason", item.get("monitorReason", ""))
        records.append(item)
    records.sort(
        key=lambda item: (
            bounded_int(item.get("monitorScore", 0), 0, 100),
            bounded_int(item.get("retainScore", 0), 0, 100),
            candidate_pool_rank(str(item.get("stateKey", ""))),
            bounded_int(item.get("peakScore", item.get("totalScore", 0)), 0, 100),
            str(item.get("lastSeenAt", "")),
        ),
        reverse=True,
    )
    return records[: max(0, selected_limit)]


def candidate_pool_entry_from_record(record: dict) -> dict:
    symbol = str(record.get("symbol", "")).strip().upper()
    name = str(record.get("name") or symbol)
    market = str(record.get("market") or ("US" if re.fullmatch(r"[A-Z.\-]{1,8}", symbol) else "KR"))
    category = str(record.get("category") or ("overseas" if market == "US" else "domestic"))
    headline = str(record.get("headline") or f"{name} 후보 풀 재점검")
    themes = unique_texts(
        [
            record.get("monitorLabel", ""),
            record.get("stateLabel", ""),
            record.get("finalAction", ""),
            record.get("compressionLabel", ""),
            record.get("validationLabel", ""),
        ],
        limit=4,
    )
    return {
        "symbol": symbol,
        "name": name,
        "market": market,
        "category": category,
        "themes": themes,
        "query": " ".join(value for value in [name, symbol, headline] if value).strip(),
        "focusWeight": min(15, 7 + candidate_pool_rank(str(record.get("stateKey", ""))) // 10),
        "discoveryTier": "pool",
        "opportunityType": "pool-retain",
        "headline": headline,
        "poolMemory": candidate_pool_memory_payload(record),
    }


def merge_candidate_pool_scan_entries(entries: list[dict], pool_records: list[dict]) -> tuple[list[dict], dict]:
    pool_by_symbol = {
        str(record.get("symbol", "")).strip().upper(): record
        for record in pool_records
        if str(record.get("symbol", "")).strip()
    }
    merged = []
    seen = set()
    retained_existing = 0
    retained_added = 0
    for entry in entries:
        symbol = str(entry.get("symbol", "")).strip().upper()
        if not symbol:
            continue
        item = dict(entry)
        if symbol in pool_by_symbol:
            item["poolMemory"] = candidate_pool_memory_payload(pool_by_symbol[symbol])
            retained_existing += 1
        merged.append(item)
        seen.add(symbol)
    for record in pool_records:
        symbol = str(record.get("symbol", "")).strip().upper()
        if not symbol or symbol in seen:
            continue
        merged.append(candidate_pool_entry_from_record(record))
        seen.add(symbol)
        retained_added += 1
    return merged, {
        "retainedInputCount": len(pool_records),
        "retainedExistingCount": retained_existing,
        "retainedAddedCount": retained_added,
        "retainedScanCount": retained_existing + retained_added,
    }


def apply_candidate_pool_memory(candidates: list[dict], pool_records: list[dict]) -> dict:
    pool_by_symbol = {
        str(record.get("symbol", "")).strip().upper(): record
        for record in pool_records
        if str(record.get("symbol", "")).strip()
    }
    applied = 0
    for candidate in candidates:
        symbol = str(candidate.get("symbol", "")).strip().upper()
        record = pool_by_symbol.get(symbol)
        if not record:
            continue
        discovery = dict(candidate.get("discovery", {})) if isinstance(candidate.get("discovery"), dict) else {}
        memory = discovery.get("poolMemory") if isinstance(discovery.get("poolMemory"), dict) else candidate_pool_memory_payload(record)
        pool_score = bounded_int(memory.get("score", record.get("retainScore", 0)), 0, 100)
        current_score = bounded_int(discovery.get("score", 0), 0, 100)
        bonus = min(8, pool_score // 12)
        discovery["poolRetained"] = True
        discovery["poolMemory"] = memory
        discovery["poolScore"] = pool_score
        discovery["score"] = bounded_int(current_score + bonus, 0, 100)
        evidence = dict(discovery.get("evidenceProfile", {})) if isinstance(discovery.get("evidenceProfile"), dict) else {}
        reasons = text_list(evidence.get("reasons", []), limit=8)
        evidence["reasons"] = unique_texts([*reasons, memory.get("reason", "후보 풀 재점검")], limit=8)
        discovery["evidenceProfile"] = evidence
        candidate["discovery"] = discovery
        applied += 1
    return {"appliedCount": applied}


def update_candidate_pool(candidates: list[dict], mode: str = "", stage: str = "selected") -> dict:
    if not SIGNAL_CANDIDATE_POOL_ENABLED:
        return {
            "enabled": False,
            "message": "후보 풀 저장이 꺼져 있습니다.",
            "totalCount": 0,
            "activeCount": 0,
            "statusCounts": {},
        }
    now = datetime.now(KST)
    with CANDIDATE_POOL_LOCK:
        data = candidate_pool_data()
        items = data.get("items", {}) if isinstance(data.get("items"), dict) else {}
        new_count = 0
        updated_count = 0
        promoted_count = 0
        for candidate in candidates:
            symbol = str(candidate.get("symbol", "")).strip().upper()
            if not symbol:
                continue
            existing = items.get(symbol, {}) if isinstance(items.get(symbol), dict) else {}
            if not existing:
                new_count += 1
            else:
                updated_count += 1
            items[symbol], promoted = candidate_pool_record(candidate, existing, mode, stage, now)
            candidate["candidatePool"] = {
                key: items[symbol].get(key)
                for key in [
                    "stateKey",
                    "stateLabel",
                    "stateReason",
                    "firstSeenAt",
                    "lastSeenAt",
                    "lastSelectedAt",
                    "observations",
                    "selectedCount",
                    "stateChangedAt",
                    "stateChangeCount",
                    "promotionCount",
                    "demotionCount",
                    "softDemotionCount",
                    "peakScore",
                    "peakReadiness",
                    "peakConfidenceScore",
                    "peakReactionScore",
                    "peakEvidenceScore",
                    "scoreDelta",
                    "momentumLabel",
                    "performanceMeasuredCount",
                    "performancePositiveCount",
                    "performanceNegativeCount",
                    "performanceNeutralCount",
                    "performanceHitRate",
                    "performanceHitRateValue",
                    "performanceAverageChange",
                    "performanceAverageChangeRate",
                    "performanceLatestChange",
                    "performanceLatestChangeRate",
                    "performanceLatestOutcome",
                    "performanceLatestAt",
                    "monitorScore",
                    "monitorLabel",
                    "monitorReason",
                    "reactionGate",
                    "reactionEntryBlock",
                    "sourceReliabilityScore",
                    "transitionHistory",
                ]
                if key in items[symbol]
            }
            if promoted:
                promoted_count += 1
        expired_count = expire_candidate_pool_items(items, now)
        removed_count = trim_candidate_pool_items(items)
        data["items"] = items
        data["updatedAt"] = now.isoformat(timespec="seconds")
        if not db_write_kv("candidate_pool", data):
            write_json(CANDIDATE_POOL_FILE, data)
        summary = candidate_pool_summary(data)
    summary.update({
        "stage": stage,
        "mode": mode,
        "newCount": new_count,
        "updatedCount": updated_count,
        "promotedCount": promoted_count,
        "expiredCount": expired_count,
        "removedCount": removed_count,
        "message": f"후보 풀 {summary['totalCount']}개 중 {summary['activeCount']}개를 계속 관찰합니다.",
    })
    return summary


def apply_candidate_selection(candidates: list[dict], market: dict, watched: set[str], stabilize_decisions: bool = False) -> tuple[list[dict], dict]:
    enriched = []
    score_shifts = []
    opportunity_scores = []
    confidence_scores = []
    reliability_scores = []
    reaction_scores = []
    official_scores = []
    reliability_counts = {"high": 0, "medium": 0, "low": 0, "poor": 0}
    official_counts = {"positive": 0, "risk": 0, "caution": 0, "neutral": 0, "highRisk": 0}
    gate_counts = {"actionable": 0, "watch": 0, "defer": 0, "exclude": 0}
    reaction_counts = {"strong": 0, "confirmed": 0, "weak": 0, "missing": 0}
    reaction_gate_counts = {"confirmed": 0, "watch": 0, "wait": 0, "blocked": 0}
    price_readiness_counts = {
        "entry_ready": 0,
        "closed_baseline": 0,
        "display_ready": 0,
        "change_wait": 0,
        "price_wait": 0,
        "collecting": 0,
    }
    evaluation_mode_counts = {
        "entry_ready": 0,
        "closed_baseline": 0,
        "display_ready": 0,
        "collecting_change": 0,
        "collecting_price": 0,
        "collecting": 0,
        "unavailable": 0,
    }
    final_decision_counts = {
        "buy": 0,
        "add": 0,
        "hold": 0,
        "trim": 0,
        "stop": 0,
        "pullback": 0,
        "watch": 0,
        "verify": 0,
        "exclude": 0,
    }
    stable_decision_count = 0
    for candidate in candidates:
        item = annotate_candidate_live_price_freshness(dict(candidate))
        previous_final_decision = stable_final_decision_candidate(item)
        base_score = item.get("score", {})
        if not isinstance(base_score, dict):
            base_score = {}
        notes: list[str] = []
        original_total = bounded_int(item.get("totalScore", score_candidate(item)))
        official_signal = official_event_signal(item)
        item["officialSignal"] = official_signal
        if official_signal.get("count"):
            official_scores.append(bounded_int(official_signal.get("scoreBoost", 0), -10, 12))
            official_counts["positive"] += bounded_int(official_signal.get("positiveCount", 0), 0, 100)
            official_counts["risk"] += bounded_int(official_signal.get("riskCount", 0), 0, 100)
            official_counts["caution"] += bounded_int(official_signal.get("cautionCount", 0), 0, 100)
            official_counts["neutral"] += bounded_int(official_signal.get("neutralCount", 0), 0, 100)
            if official_signal.get("riskLevel") == "high":
                official_counts["highRisk"] += 1

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
        item["dataCompleteness"] = candidate_data_completeness(item)
        item["priceReadiness"] = candidate_price_readiness(item)
        item["evaluationMode"] = candidate_evaluation_mode(item)
        readiness_key = str(item["priceReadiness"].get("key", "collecting"))
        price_readiness_counts[readiness_key] = price_readiness_counts.get(readiness_key, 0) + 1
        evaluation_key = str(item["evaluationMode"].get("key", "collecting"))
        evaluation_mode_counts[evaluation_key] = evaluation_mode_counts.get(evaluation_key, 0) + 1
        item["verdict"] = verdict_from_scores(total, readiness, risk, heat, opportunity)
        item["decisionGroup"] = candidate_decision_group(item, score_detail, total, readiness, preopen_priority)
        source_reliability = candidate_source_reliability(item)
        reliability_score = bounded_int(source_reliability.get("score", 0), 0, 100)
        reliability_scores.append(reliability_score)
        if reliability_score >= 78:
            reliability_counts["high"] += 1
        elif reliability_score >= 64:
            reliability_counts["medium"] += 1
        elif reliability_score >= 48:
            reliability_counts["low"] += 1
        else:
            reliability_counts["poor"] += 1
        item["sourceReliability"] = source_reliability
        confidence = candidate_data_confidence(item, source_reliability)
        reaction = candidate_price_reaction(item, score_detail)
        reaction_scores.append(bounded_int(reaction.get("score", 0), 0, 100))
        reaction_counts[reaction["key"]] = reaction_counts.get(reaction["key"], 0) + 1
        reaction_gate = str(reaction.get("reactionGate", "wait"))
        reaction_gate_counts[reaction_gate] = reaction_gate_counts.get(reaction_gate, 0) + 1
        gate = candidate_quality_gate(item, score_detail, total, readiness, confidence, reaction)
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
        final_decision = candidate_final_decision(item, score_detail, total, readiness, confidence, gate, reaction)
        if stabilize_decisions:
            final_decision, held_stable = decision_stability_merge(previous_final_decision, final_decision, item)
            if held_stable:
                stable_decision_count += 1
        final_decision_counts[final_decision["actionKey"]] = final_decision_counts.get(final_decision["actionKey"], 0) + 1
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
        item["priceReaction"] = reaction
        item["qualityGate"] = gate
        item["finalDecision"] = final_decision
        enriched.append(item)

    average_shift = sum(score_shifts) / len(score_shifts) if score_shifts else 0
    average_opportunity = sum(opportunity_scores) / len(opportunity_scores) if opportunity_scores else 0
    average_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
    average_reliability = sum(reliability_scores) / len(reliability_scores) if reliability_scores else 0
    average_reaction = sum(reaction_scores) / len(reaction_scores) if reaction_scores else 0
    average_official = sum(official_scores) / len(official_scores) if official_scores else 0
    hidden_opportunity_count = len([score for score in opportunity_scores if score >= 8])
    compression_status = assign_candidate_compression(enriched)
    groups = decision_group_counts(enriched)
    return enriched, {
        "source": "live-rules",
        "enabled": True,
        "message": "뉴스, 시세, 지수, 공시 신호로 후보 점수를 재계산했습니다.",
        "candidateCount": len(enriched),
        "averageScoreShift": round(average_shift, 1),
        "averageOpportunityScore": round(average_opportunity, 1),
        "averageDataConfidence": round(average_confidence, 1),
        "averageSourceReliability": round(average_reliability, 1),
        "sourceReliabilityCounts": reliability_counts,
        "averagePriceReaction": round(average_reaction, 1),
        "averageOfficialEventScore": round(average_official, 1),
        "officialEventCounts": official_counts,
        "officialEventCandidateCount": len(official_scores),
        "officialRiskCandidateCount": official_counts.get("highRisk", 0),
        "hiddenOpportunityCount": hidden_opportunity_count,
        "decisionGroups": groups,
        "actionCandidateCount": groups.get("action", 0),
        "qualityGateCounts": gate_counts,
        "priceReactionCounts": reaction_counts,
        "priceReactionGateCounts": reaction_gate_counts,
        "priceReadinessCounts": price_readiness_counts,
        "evaluationModeCounts": evaluation_mode_counts,
        "tradeEvaluationReadyCount": evaluation_mode_counts.get("entry_ready", 0),
        "baselineEvaluationCount": evaluation_mode_counts.get("closed_baseline", 0),
        "serverCollectingCount": (
            evaluation_mode_counts.get("collecting_change", 0)
            + evaluation_mode_counts.get("collecting_price", 0)
            + evaluation_mode_counts.get("collecting", 0)
        ),
        "unavailableEvaluationCount": evaluation_mode_counts.get("unavailable", 0),
        "entryDataReadyCount": price_readiness_counts.get("entry_ready", 0),
        "closedBaselineCandidateCount": price_readiness_counts.get("closed_baseline", 0),
        "displayDataReadyCount": (
            price_readiness_counts.get("entry_ready", 0)
            + price_readiness_counts.get("closed_baseline", 0)
            + price_readiness_counts.get("display_ready", 0)
        ),
        "priceBasisWaitCount": price_readiness_counts.get("price_wait", 0),
        "changeWaitCount": price_readiness_counts.get("change_wait", 0),
        "priceReactionEntryBlockedCount": len([item for item in enriched if item.get("priceReaction", {}).get("entryBlock")]),
        "finalDecisionCounts": final_decision_counts,
        "stableDecisionCount": stable_decision_count,
        "finalDecisionStabilitySeconds": SIGNAL_FINAL_DECISION_STABILITY_SECONDS if stabilize_decisions and SIGNAL_FINAL_DECISION_STABILITY_ENABLED else 0,
        **compression_status,
        "buyDecisionCount": final_decision_counts.get("buy", 0),
        "addDecisionCount": final_decision_counts.get("add", 0),
        "holdDecisionCount": final_decision_counts.get("hold", 0),
        "trimDecisionCount": final_decision_counts.get("trim", 0),
        "stopDecisionCount": final_decision_counts.get("stop", 0),
        "pullbackDecisionCount": final_decision_counts.get("pullback", 0),
        "watchDecisionCount": final_decision_counts.get("watch", 0),
        "verifyDecisionCount": final_decision_counts.get("verify", 0),
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
    return re.sub(r"[^0-9a-zA-Z가-힣ㄱ-ㅎㅏ-ㅣ]+", "", str(value or "")).lower()


HANGUL_INITIALS = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"


STOCK_SEARCH_ALIAS_OVERRIDES = {
    "005930": ["삼전", "삼성", "삼성반도체", "삼성전자보통주", "samsung", "samsung electronics"],
    "000660": ["하닉", "하이닉", "sk하닉", "에스케이하이닉스", "sk hynix", "hynix"],
    "035420": ["네이버", "naver", "naver corp"],
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
    "069500": ["코덱스200", "kodex200", "kodex 200", "코스피200", "kospi200"],
    "102110": ["타이거200", "tiger200", "tiger 200", "코스피200", "kospi200"],
    "278530": ["코덱스200tr", "kodex200tr", "kodex 200 tr", "코스피200tr"],
    "122630": ["코덱스레버리지", "kodex leverage", "kodex레버리지", "코스피레버리지"],
    "252670": ["곱버스", "코덱스인버스2x", "kodex inverse 2x", "kodex200선물인버스2x"],
}

STOCK_SEARCH_QUERY_SYNONYMS = {
    "삼성": ["삼성전자", "삼전", "samsung", "samsung electronics"],
    "삼전": ["삼성전자", "samsung electronics"],
    "하이닉스": ["SK하이닉스", "하닉", "sk hynix", "hynix"],
    "하닉": ["SK하이닉스", "하이닉스", "sk hynix"],
    "네이버": ["NAVER", "naver", "035420"],
    "카카오": ["kakao", "카톡", "035720"],
    "현대차": ["현대자동차", "hyundai motor", "005380"],
    "엔비디아": ["NVIDIA", "NVDA", "nvidia"],
    "엔비": ["NVIDIA", "NVDA", "nvidia"],
    "애플": ["Apple", "AAPL", "apple"],
    "마이크로소프트": ["Microsoft", "MSFT", "microsoft"],
    "마소": ["Microsoft", "MSFT", "microsoft"],
    "아마존": ["Amazon", "AMZN", "amazon"],
    "테슬라": ["Tesla", "TSLA", "tesla"],
    "구글": ["Alphabet", "GOOGL", "google"],
    "메타": ["Meta", "META", "facebook"],
    "타이거200": ["TIGER 200", "tiger200", "102110", "코스피200"],
    "tiger200": ["TIGER 200", "타이거200", "102110", "코스피200"],
    "코덱스200": ["KODEX 200", "kodex200", "069500", "코스피200"],
    "kodex200": ["KODEX 200", "코덱스200", "069500", "코스피200"],
    "코덱스반도체": ["KODEX 반도체", "091160", "반도체ETF"],
    "kodex반도체": ["KODEX 반도체", "091160", "반도체ETF"],
}

ETF_BRAND_ALIASES = {
    "KODEX": ["코덱스", "kodex"],
    "TIGER": ["타이거", "tiger"],
    "ACE": ["에이스", "ace"],
    "SOL": ["솔", "sol"],
    "KBSTAR": ["케이비스타", "KB스타", "kbstar"],
    "HANARO": ["하나로", "hanaro"],
    "ARIRANG": ["아리랑", "arirang"],
    "KOSEF": ["코세프", "kosef"],
    "TIMEFOLIO": ["타임폴리오", "timefolio"],
    "RISE": ["라이즈", "rise"],
    "PLUS": ["플러스", "plus"],
}


STOCK_SEARCH_MANUAL_UNIVERSE = [
    {
        "symbol": "069500",
        "name": "KODEX 200",
        "market": "KR",
        "category": "domestic",
        "securityType": "ETF",
        "aliases": ["코덱스200", "KODEX200", "kodex 200", "코스피200"],
        "themes": ["ETF", "코스피200"],
        "focusWeight": 4,
        "source": "manual-etf",
        "sourceLabel": "ETF 검색 마스터",
    },
    {
        "symbol": "102110",
        "name": "TIGER 200",
        "market": "KR",
        "category": "domestic",
        "securityType": "ETF",
        "aliases": ["타이거200", "TIGER200", "tiger 200", "코스피200"],
        "themes": ["ETF", "코스피200"],
        "focusWeight": 4,
        "source": "manual-etf",
        "sourceLabel": "ETF 검색 마스터",
    },
    {
        "symbol": "278530",
        "name": "KODEX 200TR",
        "market": "KR",
        "category": "domestic",
        "securityType": "ETF",
        "aliases": ["코덱스200TR", "KODEX200TR", "kodex 200 tr", "코스피200TR"],
        "themes": ["ETF", "코스피200", "TR"],
        "focusWeight": 4,
        "source": "manual-etf",
        "sourceLabel": "ETF 검색 마스터",
    },
    {
        "symbol": "091160",
        "name": "KODEX 반도체",
        "market": "KR",
        "category": "domestic",
        "securityType": "ETF",
        "aliases": ["코덱스반도체", "KODEX반도체", "kodex semiconductor", "반도체ETF"],
        "themes": ["ETF", "반도체"],
        "focusWeight": 5,
        "source": "manual-etf",
        "sourceLabel": "ETF 검색 마스터",
    },
    {
        "symbol": "091230",
        "name": "TIGER 반도체",
        "market": "KR",
        "category": "domestic",
        "securityType": "ETF",
        "aliases": ["타이거반도체", "TIGER반도체", "tiger semiconductor", "반도체ETF"],
        "themes": ["ETF", "반도체"],
        "focusWeight": 5,
        "source": "manual-etf",
        "sourceLabel": "ETF 검색 마스터",
    },
    {
        "symbol": "360750",
        "name": "TIGER 미국S&P500",
        "market": "KR",
        "category": "domestic",
        "securityType": "ETF",
        "aliases": ["타이거미국S&P500", "TIGER미국S&P500", "tiger sp500", "s&p500etf"],
        "themes": ["ETF", "S&P500", "미국"],
        "focusWeight": 4,
        "source": "manual-etf",
        "sourceLabel": "ETF 검색 마스터",
    },
]


STOCK_SEARCH_UNIVERSE_CACHE: list[dict] | None = None


def hangul_initials(value: str) -> str:
    letters = []
    for char in str(value or ""):
        code = ord(char) - 0xAC00
        if 0 <= code <= 11171:
            letters.append(HANGUL_INITIALS[code // 588])
        elif char.strip():
            letters.append(char.lower())
    return normalized_search_text("".join(letters))


def search_query_is_initials(query: str) -> bool:
    text = normalized_search_text(query)
    return bool(text) and all("ㄱ" <= char <= "ㅎ" for char in text)


def search_text_subsequence(needle: str, haystack: str) -> bool:
    if not needle:
        return False
    cursor = 0
    for char in haystack:
        if cursor < len(needle) and needle[cursor] == char:
            cursor += 1
    return cursor == len(needle)


def expanded_stock_aliases(symbol: str, aliases: list[str] | None = None) -> list[str]:
    normalized_symbol = str(symbol or "").strip().upper()
    return unique_texts(
        [
            *(aliases or []),
            *STOCK_SEARCH_ALIAS_OVERRIDES.get(normalized_symbol, []),
        ],
        limit=32,
    )


def compact_alias(value: str) -> str:
    return re.sub(r"\s+", "", clean_news_text(str(value or "")))


def stock_search_query_variants(query: str) -> list[str]:
    raw = clean_news_text(str(query or ""))
    normalized = normalized_search_text(raw)
    if not normalized:
        return []
    variants: list[str] = [raw, normalized]
    compact = compact_alias(raw)
    if compact:
        variants.append(compact)

    synonyms = STOCK_SEARCH_QUERY_SYNONYMS.get(normalized, [])
    variants.extend(synonyms)

    alpha_number = re.fullmatch(r"([a-zA-Z]+)([0-9].*)", compact or raw)
    if alpha_number:
        brand, rest = alpha_number.groups()
        upper_brand = brand.upper()
        variants.extend([f"{upper_brand} {rest}", f"{upper_brand}{rest}"])
        for brand_alias in ETF_BRAND_ALIASES.get(upper_brand, []):
            variants.extend([f"{brand_alias}{rest}", f"{brand_alias} {rest}"])

    hangul_number = re.fullmatch(r"([가-힣]+)([0-9].*)", compact or raw)
    if hangul_number:
        brand, rest = hangul_number.groups()
        for canonical, brand_aliases in ETF_BRAND_ALIASES.items():
            normalized_aliases = [normalized_search_text(alias) for alias in brand_aliases]
            if normalized_search_text(brand) in normalized_aliases:
                variants.extend([f"{canonical} {rest}", f"{canonical}{rest}"])

    return unique_texts(variants, limit=16)


def stock_search_auto_aliases(entry: dict) -> list[str]:
    name = str(entry.get("name") or "").strip()
    english_name = str(entry.get("englishName") or "").strip()
    security_type = str(entry.get("securityType") or "").upper()
    themes = text_list(entry.get("themes", []), limit=8)
    aliases: list[str] = []
    for value in [name, english_name]:
        compact = compact_alias(value)
        if value:
            aliases.append(value)
        if compact and compact != value:
            aliases.append(compact)

    is_etf = security_type == "ETF" or any("ETF" in str(theme).upper() for theme in themes)
    if not is_etf or not name:
        return unique_texts(aliases, limit=24)

    parts = name.split(maxsplit=1)
    if not parts:
        return unique_texts(aliases, limit=24)

    brand = parts[0].strip().upper()
    rest = parts[1].strip() if len(parts) > 1 else ""
    rest_compact = compact_alias(rest)
    brand_aliases = ETF_BRAND_ALIASES.get(brand, [])
    if brand_aliases and rest:
        for brand_alias in brand_aliases:
            aliases.extend(
                [
                    f"{brand_alias}{rest_compact}",
                    f"{brand_alias} {rest}",
                    f"{brand_alias}{rest_compact}ETF",
                ]
            )
    if rest:
        aliases.extend([rest, rest_compact, f"{rest_compact}ETF", f"{rest} ETF"])
    for theme in themes:
        theme_compact = compact_alias(theme)
        aliases.extend([theme, theme_compact])
    return unique_texts(aliases, limit=24)


def search_query_looks_symbol(query: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9.\-]{2,20}", query.strip()))


def universe_aliases_for_symbol(symbol: str) -> list[str]:
    normalized_symbol = str(symbol or "").strip().upper()
    if not normalized_symbol:
        return []
    for entry in stock_search_universe_entries():
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
            *stock_search_auto_aliases(candidate),
        ],
        limit=32,
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
        ("검색어", "query"),
        ("유형", "securityType"),
        ("시장", "market"),
    ]:
        value = item.get(key)
        if value:
            terms.append((label, str(value)))
    for alias in text_list(item.get("aliases", []), limit=32):
        terms.append(("별칭", alias))
    for theme in text_list(item.get("themes", []), limit=8):
        terms.append(("테마", theme))
    return terms


def stock_search_match_info(query: str, item: dict) -> dict:
    query_variants = stock_search_query_variants(query)
    if not query_variants:
        return {"matched": False, "rank": 99, "field": "", "text": ""}

    original_normalized = normalized_search_text(query_variants[0])
    best = {"matched": False, "rank": 99, "field": "", "text": "", "variant": ""}
    for variant in query_variants:
        normalized_query = normalized_search_text(variant)
        if not normalized_query:
            continue
        initials_query = search_query_is_initials(variant)
        variant_penalty = 0 if normalized_query == original_normalized else 1
        for field, raw_text in search_terms_for_item(item):
            text = str(raw_text or "")
            normalized_text = normalized_search_text(text)
            if not normalized_text:
                continue
            initials = hangul_initials(text)
            allow_initials = field not in {"테마", "검색어"}
            rank = None
            if normalized_query == normalized_text:
                rank = 0
            elif normalized_text.startswith(normalized_query):
                rank = 1
            elif allow_initials and initials and initials.startswith(normalized_query):
                rank = 2
            elif normalized_query in normalized_text:
                rank = 3
            elif allow_initials and initials and normalized_query in initials:
                rank = 4
            elif allow_initials and initials_query and initials and search_text_subsequence(normalized_query, initials):
                rank = 5
            if rank is None:
                continue
            adjusted_rank = min(98, rank + variant_penalty)
            candidate = {"matched": True, "rank": adjusted_rank, "field": field, "text": text, "variant": variant}
            if (
                adjusted_rank < best["rank"]
                or (
                    adjusted_rank == best["rank"]
                    and stock_search_field_priority(field) < stock_search_field_priority(str(best.get("field", "")))
                )
            ):
                best = candidate
    return best


def stock_search_field_priority(field: str) -> int:
    return {
        "코드": 0,
        "종목명": 1,
        "별칭": 1,
        "영문명": 2,
        "검색어": 3,
        "테마": 4,
        "유형": 5,
        "시장": 6,
    }.get(str(field), 7)


def search_relevance_rank(query: str, item: dict) -> tuple[int, ...]:
    match = item.get("match")
    if not isinstance(match, dict) or normalized_search_text(match.get("query", "")) != normalized_search_text(query):
        match = stock_search_match_info(query, item)
    bucket = bounded_int(match.get("rank", 99), 0, 99)
    field_priority = stock_search_field_priority(str(match.get("field", "")))
    score = bounded_int(item.get("score", item.get("totalScore", 0)), 0, 100)
    name = normalized_search_text(item.get("name", ""))
    symbol = normalized_search_text(item.get("symbol", ""))
    in_candidates = 0 if item.get("inCandidates") else 1
    watched = 0 if item.get("isWatched") else 1
    security_type = str(item.get("securityType", "")).upper()
    source = str(item.get("source", ""))
    source_priority = {
        "candidate": 0,
        "candidate-universe": 1,
        "stock-search-generated": 2,
        "stock-search-master": 3,
        "manual-etf": 3,
        "dart-corp-code": 4,
        "toss": 5,
    }.get(source, 6)
    etf_priority = 0 if security_type == "ETF" and ("etf" in normalized_search_text(query) or any(brand.lower() in normalized_search_text(query) for brand in ETF_BRAND_ALIASES)) else 1
    return bucket, field_priority, in_candidates, watched, etf_priority, source_priority, -score, len(name or symbol)


def stock_search_universe_summary(entries: list[dict] | None = None) -> dict:
    entries = entries if isinstance(entries, list) else stock_search_universe_entries()
    domestic = 0
    overseas = 0
    etf = 0
    stock = 0
    sources: dict[str, int] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        category = str(entry.get("category", "")).lower()
        market = str(entry.get("market", "")).upper()
        security_type = str(entry.get("securityType", "")).upper()
        source = str(entry.get("source", "unknown"))
        sources[source] = sources.get(source, 0) + 1
        if category == "overseas" or market in {"US", "NASDAQ", "NYSE", "AMEX", "ARCA", "BATS"}:
            overseas += 1
        else:
            domestic += 1
        if security_type == "ETF":
            etf += 1
        else:
            stock += 1
    return {
        "total": len(entries),
        "domestic": domestic,
        "overseas": overseas,
        "etf": etf,
        "stock": stock,
        "sources": sources,
    }


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
        "aliases": expanded_stock_aliases(symbol, [*text_list(entry.get("aliases", []), limit=24), *stock_search_auto_aliases(entry)]),
        "price": "-",
        "change": "",
        "headline": " · ".join(themes) if themes else f"{name} 감시 유니버스",
        "score": bounded_int(42 + focus * 3, 0, 100),
        "updated": "자동완성",
        "isWatched": symbol in watched,
        "inCandidates": False,
        "securityType": entry.get("securityType", ""),
        "source": entry.get("source", "universe"),
        "sourceLabel": entry.get("sourceLabel", "감시 유니버스"),
    }


def dart_stock_search_entries() -> list[dict]:
    payload = load_dart_corp_codes()
    by_stock_code = payload.get("byStockCode", payload) if isinstance(payload, dict) else {}
    if not isinstance(by_stock_code, dict):
        return []
    entries = []
    for symbol, item in by_stock_code.items():
        if not isinstance(item, dict):
            continue
        stock_code = str(item.get("stockCode") or symbol).strip().upper()
        if not re.fullmatch(r"[0-9A-Z]{6}", stock_code):
            continue
        name = str(item.get("corpName") or stock_code).strip()
        english_name = str(item.get("corpEngName") or "").strip()
        aliases = unique_texts([name, english_name], limit=4)
        entries.append({
            "symbol": stock_code,
            "name": name,
            "englishName": english_name,
            "market": "KR",
            "category": "domestic",
            "securityType": "STOCK",
            "aliases": aliases,
            "themes": ["OpenDART 등록 상장사"],
            "query": name,
            "focusWeight": 2,
            "discoveryTier": "lookup",
            "opportunityType": "lookup",
            "source": "dart-corp-code",
            "sourceLabel": "OpenDART 종목마스터",
        })
    return entries


def normalize_stock_search_entry(entry: dict, default_source: str, default_label: str) -> dict | None:
    if not isinstance(entry, dict):
        return None
    symbol = str(entry.get("symbol", "")).strip().upper()
    name = str(entry.get("name") or symbol).strip()
    if not symbol or not name:
        return None
    item = dict(entry)
    market = str(item.get("market") or ("US" if re.fullmatch(r"[A-Z.\-]{1,6}", symbol) else "KR")).strip().upper()
    item["symbol"] = symbol
    item["name"] = name
    item["market"] = market
    if not item.get("category"):
        item["category"] = "overseas" if market in {"US", "NASDAQ", "NYSE", "AMEX", "ARCA", "BATS"} else "domestic"
    item["securityType"] = item.get("securityType", "STOCK")
    item["aliases"] = expanded_stock_aliases(symbol, [*text_list(item.get("aliases", []), limit=24), *stock_search_auto_aliases(item)])
    item["themes"] = text_list(item.get("themes", []), limit=8)
    item["focusWeight"] = bounded_int(item.get("focusWeight", 3), 0, 15)
    item["source"] = item.get("source", default_source)
    item["sourceLabel"] = item.get("sourceLabel", default_label)
    return item


def stock_search_master_entries() -> list[dict]:
    payload = stock_search_master_data()
    raw_entries = payload.get("symbols", []) if isinstance(payload, dict) else []
    if not isinstance(raw_entries, list):
        return []
    entries = []
    for entry in raw_entries:
        item = normalize_stock_search_entry(entry, "stock-search-master", "검색 확장 마스터")
        if item:
            entries.append(item)
    return entries


def stock_search_generated_entries() -> list[dict]:
    payload, _storage = stock_search_generated_data()
    raw_entries = payload.get("symbols", []) if isinstance(payload, dict) else []
    if not isinstance(raw_entries, list):
        return []
    entries = []
    for entry in raw_entries:
        item = normalize_stock_search_entry(entry, "stock-search-generated", "저장 검색 마스터")
        if item:
            entries.append(item)
    return entries


def stock_search_source_lists(include_generated: bool = False) -> list[tuple[str, list[dict]]]:
    sources = []
    if include_generated:
        sources.append(("stock-search-generated", stock_search_generated_entries()))
    sources.extend(
        [
            ("candidate-universe", candidate_universe_entries()),
            ("stock-search-master", stock_search_master_entries()),
            ("manual-etf", STOCK_SEARCH_MANUAL_UNIVERSE),
            ("opendart-corp-code", dart_stock_search_entries()),
        ]
    )
    return sources


def merge_stock_search_entries(source_lists: list[tuple[str, list[dict]]]) -> tuple[list[dict], dict]:
    entries = []
    seen: set[str] = set()
    source_counts: dict[str, int] = {}
    for source_name, source_entries in source_lists:
        source_counts[source_name] = len(source_entries) if isinstance(source_entries, list) else 0
        for entry in source_entries:
            default_label = {
                "candidate-universe": "감시 유니버스",
                "stock-search-master": "검색 확장 마스터",
                "manual-etf": "수동 ETF 마스터",
                "opendart-corp-code": "OpenDART 종목마스터",
                "stock-search-generated": "저장 검색 마스터",
            }.get(source_name, source_name)
            item = normalize_stock_search_entry(entry, source_name, default_label)
            if not item:
                continue
            symbol = str(item.get("symbol", "")).strip().upper()
            if symbol in seen:
                continue
            entries.append(item)
            seen.add(symbol)
    return entries, source_counts


def build_stock_search_master_payload(trigger: str = "manual") -> dict:
    entries, source_counts = merge_stock_search_entries(stock_search_source_lists(include_generated=False))
    generated_at = datetime.now(KST).isoformat(timespec="seconds")
    return {
        "version": 1,
        "trigger": trigger,
        "generatedAt": generated_at,
        "count": len(entries),
        "sourceCounts": source_counts,
        "sources": list(source_counts.keys()),
        "symbols": entries,
    }


def write_stock_search_generated_data(payload: dict) -> str:
    if db_write_kv(STOCK_SEARCH_MASTER_KV_KEY, payload):
        return "database"
    write_json(STOCK_SEARCH_GENERATED_FILE, payload)
    return "filesystem"


def refresh_stock_search_master(trigger: str = "manual") -> dict:
    global STOCK_SEARCH_UNIVERSE_CACHE
    with STOCK_SEARCH_MASTER_LOCK:
        try:
            payload = build_stock_search_master_payload(trigger=trigger)
            storage = write_stock_search_generated_data(payload)
            STOCK_SEARCH_UNIVERSE_CACHE = None
            status = {
                "ok": True,
                "storage": storage,
                "generatedAt": payload.get("generatedAt", ""),
                "count": payload.get("count", 0),
                "sourceCounts": payload.get("sourceCounts", {}),
                "trigger": trigger,
            }
            STOCK_SEARCH_MASTER_STATE["lastRefresh"] = status
            STOCK_SEARCH_MASTER_STATE["lastError"] = ""
            return status
        except Exception as error:
            message = str(error)[:240]
            STOCK_SEARCH_MASTER_STATE["lastError"] = message
            return {"ok": False, "error": "stock-search-master-refresh-failed", "message": message}


def stock_search_master_refresh_due(now: datetime | None = None) -> bool:
    if not SIGNAL_STOCK_SEARCH_MASTER_AUTO_REFRESH:
        return False
    now = now or datetime.now(KST)
    payload, _storage = stock_search_generated_data()
    generated_at = parse_iso_datetime(str(payload.get("generatedAt", ""))) if isinstance(payload, dict) else None
    if generated_at is None:
        return True
    elapsed = (now - generated_at).total_seconds()
    return elapsed >= max(3600, SIGNAL_STOCK_SEARCH_MASTER_REFRESH_SECONDS)


def stock_search_master_status() -> dict:
    payload, storage = stock_search_generated_data()
    generated_symbols = payload.get("symbols", []) if isinstance(payload, dict) else []
    generated_count = len(generated_symbols) if isinstance(generated_symbols, list) else 0
    live_entries = stock_search_universe_entries()
    with STOCK_SEARCH_MASTER_LOCK:
        state = dict(STOCK_SEARCH_MASTER_STATE)
    return {
        "ok": True,
        "storage": storage,
        "generated": {
            "exists": storage != "none",
            "count": generated_count,
            "generatedAt": payload.get("generatedAt", "") if isinstance(payload, dict) else "",
            "trigger": payload.get("trigger", "") if isinstance(payload, dict) else "",
            "sourceCounts": payload.get("sourceCounts", {}) if isinstance(payload, dict) else {},
        },
        "active": {
            "count": len(live_entries),
            "usesGeneratedMaster": generated_count > 0,
        },
        "config": {
            "autoRefreshEnabled": SIGNAL_STOCK_SEARCH_MASTER_AUTO_REFRESH,
            "refreshSeconds": SIGNAL_STOCK_SEARCH_MASTER_REFRESH_SECONDS,
            "databaseEnabled": database_storage_enabled(),
            "databaseReady": ensure_database_schema() if database_storage_enabled() else False,
            "fallbackFile": str(STOCK_SEARCH_GENERATED_FILE),
        },
        "state": state,
    }


def stock_search_universe_entries() -> list[dict]:
    global STOCK_SEARCH_UNIVERSE_CACHE
    if STOCK_SEARCH_UNIVERSE_CACHE is not None:
        return STOCK_SEARCH_UNIVERSE_CACHE
    entries, _source_counts = merge_stock_search_entries(stock_search_source_lists(include_generated=True))
    STOCK_SEARCH_UNIVERSE_CACHE = entries
    return entries


def universe_candidate_search(query: str, watched: set[str], limit: int = 8, existing_symbols: set[str] | None = None) -> list[dict]:
    normalized_query = normalized_search_text(query)
    if not normalized_query:
        return []
    existing_symbols = existing_symbols or set()
    matches = []
    for entry in stock_search_universe_entries():
        symbol = str(entry.get("symbol", "")).strip().upper()
        if not symbol or symbol in existing_symbols:
            continue
        result = universe_search_result(entry, watched)
        result["englishName"] = entry.get("englishName", "")
        result["themes"] = text_list(entry.get("themes", []), limit=6)
        result["aliases"] = expanded_stock_aliases(symbol, [*text_list(entry.get("aliases", []), limit=24), *stock_search_auto_aliases(entry)])
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
    generated_master, generated_storage = stock_search_generated_data()
    generated_count = len(generated_master.get("symbols", [])) if isinstance(generated_master, dict) and isinstance(generated_master.get("symbols", []), list) else 0
    search_master_entries = stock_search_universe_entries()
    search_master_count = len(search_master_entries)
    search_master_summary = stock_search_universe_summary(search_master_entries)
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
        "status": {
            **toss_status,
            "searchMasterCount": search_master_count,
            "searchMasterSummary": search_master_summary,
            "searchMasterStorage": generated_storage,
            "generatedMasterCount": generated_count,
            "usingGeneratedMaster": generated_count > 0,
            "searchMasterSources": ["stock-search-generated", "candidate-universe", "stock-search-master", "manual-etf", "opendart-corp-code"],
        },
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
            for entry in stock_search_universe_entries()
            if str(entry.get("symbol", "")).strip().upper() == symbol
        ),
        None,
    )
    if universe_match:
        candidate = default_candidate_for_entry(universe_match, [], {"source": "lookup", "total": 0})
        candidate["candidateSource"] = f"search-{universe_match.get('source', 'universe')}"
        candidate["updated"] = "검색 분석"
        return decorate_candidate(candidate, watched), {
            "source": universe_match.get("source", "universe"),
            "message": "검색 마스터에 있는 종목을 분석합니다.",
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
    portfolio = safe_portfolio_status()

    statuses: dict[str, dict] = {
        "lookup": lookup_status,
        "indices": index_status,
        "fx": fx_status,
        "portfolio": {
            "source": portfolio.get("source", "unavailable"),
            "enabled": portfolio.get("enabled", False),
            "ready": portfolio.get("ready", False),
            "message": portfolio.get("message", "포트폴리오 연결 상태를 확인했습니다."),
            "holdingCount": len(portfolio.get("items", [])) if isinstance(portfolio.get("items"), list) else 0,
            "linkedCandidateCount": 0,
        },
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

    candidates, statuses["portfolio"] = enrich_candidates_with_portfolio(candidates, portfolio)
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


NEWS_MATERIAL_KEYWORDS = {
    "earnings": {
        "label": "실적",
        "keywords": ["실적", "매출", "영업이익", "순이익", "어닝", "guidance", "earnings", "revenue", "profit"],
        "weight": 12,
    },
    "contract": {
        "label": "수주/계약",
        "keywords": ["수주", "공급계약", "계약", "납품", "order", "contract", "deal", "supply agreement"],
        "weight": 13,
    },
    "guidance": {
        "label": "전망/목표가",
        "keywords": ["전망", "목표가", "상향", "하향", "투자의견", "가이던스", "upgrade", "downgrade", "price target", "outlook"],
        "weight": 9,
    },
    "capital": {
        "label": "자본/희석",
        "keywords": ["유상증자", "전환사채", "cb", "bw", "증자", "감자", "offering", "convertible", "dilution"],
        "weight": 10,
    },
    "policy": {
        "label": "정책/규제",
        "keywords": ["정책", "규제", "금리", "관세", "보조금", "제재", "policy", "regulation", "tariff", "rate cut"],
        "weight": 8,
    },
    "shareholder": {
        "label": "주주환원",
        "keywords": ["배당", "자사주", "주주환원", "buyback", "dividend", "shareholder return"],
        "weight": 10,
    },
    "product": {
        "label": "제품/기술",
        "keywords": ["출시", "신제품", "인증", "hbm", "ai", "gpu", "chip", "launch", "product", "approval"],
        "weight": 7,
    },
    "supply_demand": {
        "label": "수급",
        "keywords": ["순매수", "외국인", "기관", "거래대금", "수급", "inflow", "outflow", "volume"],
        "weight": 7,
    },
    "risk": {
        "label": "리스크",
        "keywords": ["소송", "조사", "리콜", "횡령", "거래정지", "상장폐지", "lawsuit", "probe", "recall", "fraud", "halt"],
        "weight": 12,
    },
}


NEWS_NOISE_KEYWORDS = [
    "채용",
    "인사",
    "사회공헌",
    "봉사",
    "기부",
    "이벤트",
    "프로모션",
    "블로그",
    "맛집",
    "부동산",
    "날씨",
    "스포츠",
]


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


def news_theme_terms(entry: dict) -> list[str]:
    terms = []
    for key in ("themes", "tags"):
        values = entry.get(key, [])
        if isinstance(values, list):
            terms.extend(str(value) for value in values)
    return unique_texts([term for term in terms if len(str(term).strip()) >= 2], limit=10)


def news_relevance_score(entry: dict, item: dict) -> dict:
    title = clean_news_text(str(item.get("title", "")))
    summary = clean_news_text(str(item.get("summary", "")))
    host = clean_news_text(str(item.get("sourceHost", "")))
    title_compact = compact_match_text(title)
    body_compact = compact_match_text(f"{title} {summary}")
    lower_text = f"{title} {summary}".lower()
    score = 0
    matched_terms: list[str] = []
    material_labels: list[str] = []
    impact_types: list[str] = []
    penalties: list[str] = []

    symbol = compact_match_text(str(entry.get("symbol", "")))
    name = compact_match_text(str(entry.get("name", "")))
    if symbol and len(symbol) >= 2 and symbol in body_compact:
        score += 28 if symbol in title_compact else 18
        matched_terms.append(str(entry.get("symbol", "")))
    if name and len(name) >= 2 and name in body_compact:
        score += 34 if name in title_compact else 24
        matched_terms.append(str(entry.get("name", "")))

    for term in news_relevance_terms(entry):
        normalized = compact_match_text(term)
        if not normalized or normalized in {symbol, name}:
            continue
        if len(normalized) <= 2 and normalized not in {symbol, name}:
            continue
        if normalized in body_compact:
            weight = 18 if normalized in title_compact else 10
            if len(normalized) <= 3:
                weight = min(weight, 8)
            score += weight
            matched_terms.append(term)

    for term in news_theme_terms(entry):
        normalized = compact_match_text(term)
        if normalized and normalized in body_compact:
            score += 5
            material_labels.append(term)

    for key, config in NEWS_MATERIAL_KEYWORDS.items():
        keywords = config["keywords"]
        if any(str(keyword).lower() in lower_text for keyword in keywords):
            score += int(config["weight"])
            impact_types.append(str(config["label"]))

    if host:
        if any(source in host for source in ["dart.fss.or.kr", "fss.or.kr", "sec.gov"]):
            score += 16
            material_labels.append("공식 출처")
        elif any(source in host for source in ["naver.com", "youtube.com", "blog", "cafe"]):
            score -= 4
            penalties.append("투자 판단 신뢰도가 낮은 출처")

    if any(keyword in lower_text for keyword in NEWS_NOISE_KEYWORDS):
        score -= 10
        penalties.append("주가 영향이 낮은 일반 기사")

    if not matched_terms:
        score -= 25
        penalties.append("종목명/티커 직접 언급 없음")
    elif len(set(compact_match_text(term) for term in matched_terms if term)) == 1 and matched_terms[0] in {"삼성", "애플", "현대", "우리"}:
        score -= 10
        penalties.append("광범위한 브랜드명만 일치")

    score = bounded_int(score, 0, 100)
    if score >= 70:
        level, label = "high", "높은 관련성"
    elif score >= 50:
        level, label = "medium", "관련성 확인"
    elif score >= 35:
        level, label = "low", "약한 관련성"
    else:
        level, label = "reject", "관련성 낮음"

    return {
        "score": score,
        "level": level,
        "label": label,
        "accepted": score >= 50,
        "material": bool(impact_types) and score >= 50,
        "matchedTerms": unique_texts(matched_terms, limit=5),
        "materialTerms": unique_texts(material_labels, limit=5),
        "impactTypes": unique_texts(impact_types, limit=4),
        "penalties": unique_texts(penalties, limit=3),
    }


def annotate_news_item_relevance(entry: dict, item: dict) -> dict:
    return {**item, "relevance": news_relevance_score(entry, item)}


def news_matches_entry(entry: dict, item: dict) -> bool:
    relevance = item.get("relevance") if isinstance(item, dict) else None
    if not isinstance(relevance, dict):
        relevance = news_relevance_score(entry, item)
    return bool(relevance.get("accepted"))


def filter_relevant_news_items(entry: dict, items: list[dict]) -> list[dict]:
    annotated = [annotate_news_item_relevance(entry, item) for item in items]
    relevant = [item for item in annotated if news_matches_entry(entry, item)]
    relevant.sort(key=lambda item: item.get("relevance", {}).get("score", 0), reverse=True)
    return relevant


def news_relevance_summary(items: list[dict]) -> dict:
    high = 0
    medium = 0
    low = 0
    material = 0
    impact_types: list[str] = []
    scores = []
    for item in items:
        relevance = item.get("relevance", {}) if isinstance(item, dict) else {}
        score = relevance.get("score")
        if score is not None:
            scores.append(bounded_int(score, 0, 100))
        level = relevance.get("level")
        if level == "high":
            high += 1
        elif level == "medium":
            medium += 1
        elif level == "low":
            low += 1
        if relevance.get("material"):
            material += 1
        impact_types.extend(text_list(relevance.get("impactTypes", []), limit=4))
    average = round(sum(scores) / len(scores), 1) if scores else 0
    return {
        "high": high,
        "medium": medium,
        "low": low,
        "material": material,
        "averageScore": average,
        "impactTypes": unique_texts(impact_types, limit=5),
    }


def discovery_evidence_profile(
    entry: dict,
    news_items: list[dict],
    news_status: dict,
    seed_score: int,
    watched: set[str],
) -> dict:
    symbol = str(entry.get("symbol", "")).strip().upper()
    name = str(entry.get("name", symbol)).strip() or symbol
    focus = bounded_int(entry.get("focusWeight", 5), 0, 15)
    relevance_summary = (
        news_status.get("relevanceSummary", {})
        if isinstance(news_status.get("relevanceSummary"), dict)
        else news_relevance_summary(news_items)
    )
    high = bounded_int(relevance_summary.get("high", 0), 0, 100)
    medium = bounded_int(relevance_summary.get("medium", 0), 0, 100)
    material = bounded_int(relevance_summary.get("material", 0), 0, 100)
    average = display_number_to_decimal(relevance_summary.get("averageScore")) or Decimal("0")
    raw_display = bounded_int(news_status.get("rawDisplay", 0), 0, 1_000)
    filtered = bounded_int(news_status.get("filteredOut", 0), 0, 1_000)
    source = str(news_status.get("source", "universe"))
    impact_types = text_list(relevance_summary.get("impactTypes", []), limit=6)
    risk_impact = "리스크" in impact_types
    positive_impact = any(label in impact_types for label in ["실적", "수주/계약", "전망/목표가", "주주환원", "제품/기술", "수급", "정책/규제"])
    reasons: list[str] = []
    blockers: list[str] = []

    if news_items:
        reasons.append(f"고관련 뉴스 {len(news_items)}건")
    if high:
        reasons.append(f"높은 관련성 뉴스 {high}건")
    if material:
        reasons.append(f"투자 재료성 뉴스 {material}건")
    if impact_types:
        reasons.append(f"영향 유형: {', '.join(impact_types[:3])}")
    if symbol in watched:
        reasons.append("관심 종목으로 추적 중")
    if focus >= 8:
        reasons.append("중점 테마 유니버스")

    if source == "naver" and raw_display and not news_items:
        blockers.append("검색 뉴스는 있었지만 종목 관련성이 낮음")
    if filtered >= max(2, raw_display // 2) and raw_display:
        blockers.append(f"뉴스 {filtered}건 관련성 필터 제외")
    if not news_items and symbol not in watched:
        blockers.append("최신 고관련 뉴스 없음")
    if risk_impact and not positive_impact:
        blockers.append("리스크성 재료가 우세")

    evidence_score = bounded_int(
        focus * 2
        + high * 20
        + medium * 11
        + material * 18
        + float(average) * 0.32
        + min(seed_score, 90) * 0.08
        + (8 if positive_impact else 0)
        + (8 if symbol in watched else 0)
        - (12 if source == "naver" and raw_display and not news_items else 0)
        - (10 if risk_impact and not positive_impact else 0),
        0,
        100,
    )

    if risk_impact and not positive_impact and evidence_score >= SIGNAL_DISCOVERY_QUALIFIED_EVIDENCE_SCORE:
        grade, label, priority = "risk", "리스크 검토", 3
    elif material and evidence_score >= SIGNAL_DISCOVERY_STRONG_EVIDENCE_SCORE and average >= Decimal("60"):
        grade, label, priority = "strong", "강한 발굴 근거", 0
    elif (high or material or positive_impact) and evidence_score >= SIGNAL_DISCOVERY_QUALIFIED_EVIDENCE_SCORE:
        grade, label, priority = "qualified", "검증된 발굴 근거", 1
    elif news_items or symbol in watched or focus >= 8:
        grade, label, priority = "thin", "약한 발굴 근거", 2
    else:
        grade, label, priority = "weak", "발굴 근거 부족", 4

    return {
        "grade": grade,
        "label": label,
        "priority": priority,
        "score": evidence_score,
        "symbol": symbol,
        "name": name,
        "source": source,
        "newsItems": len(news_items),
        "rawNewsItems": raw_display,
        "filteredNewsItems": filtered,
        "highRelevanceCount": high,
        "mediumRelevanceCount": medium,
        "materialNewsCount": material,
        "averageRelevance": float(average),
        "impactTypes": impact_types,
        "reasons": unique_texts(reasons, limit=5),
        "blockers": unique_texts(blockers, limit=5),
    }


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
    relevance_summary = news_relevance_summary(relevant)
    return relevant, {
        "source": "naver",
        "query": query,
        "total": len(relevant),
        "rawTotal": payload.get("total", 0),
        "display": len(relevant),
        "rawDisplay": payload.get("display", len(normalized)),
        "filteredOut": max(0, len(normalized) - len(relevant)),
        "relevanceSummary": relevance_summary,
        "materialNewsCount": relevance_summary.get("material", 0),
    }


def default_candidate_for_entry(entry: dict, news_items: list[dict], news_status: dict) -> dict:
    symbol = str(entry.get("symbol", "")).strip().upper()
    name = str(entry.get("name", "") or symbol).strip()
    themes = text_list(entry.get("themes", []), limit=6)
    headline = news_items[0].get("title") if news_items else f"{name} 관련 신호 점검"
    source_items = [source_from_news_item(item) for item in news_items[:3]]
    news_total = bounded_int(news_status.get("total", len(news_items)), 0, 10_000_000)
    relevance_summary = news_status.get("relevanceSummary", {}) if isinstance(news_status.get("relevanceSummary"), dict) else news_relevance_summary(news_items)
    high_relevance = bounded_int(relevance_summary.get("high", 0), 0, 100)
    medium_relevance = bounded_int(relevance_summary.get("medium", 0), 0, 100)
    material_news = bounded_int(relevance_summary.get("material", 0), 0, 100)
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
            "event": bounded_int(8 + focus + high_relevance * 3 + material_news * 4, 0, 25),
            "news": bounded_int(5 + high_relevance * 5 + medium_relevance * 3 + material_news * 4, 0, 22),
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
            "materialNewsCount": material_news,
            "newsRelevance": relevance_summary.get("averageScore", 0),
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
        relevance_summary = news_status.get("relevanceSummary", {}) if isinstance(news_status.get("relevanceSummary"), dict) else news_relevance_summary(news_items)
        base["liveNews"] = {
            "source": "naver",
            "query": news_status.get("query", universe_query(entry)),
            "total": news_status.get("total", len(news_items)),
            "rawTotal": news_status.get("rawTotal", news_status.get("total", len(news_items))),
            "display": news_status.get("display", len(news_items)),
            "rawDisplay": news_status.get("rawDisplay", news_status.get("display", len(news_items))),
            "filteredOut": news_status.get("filteredOut", 0),
            "items": news_items,
            "relevanceSummary": relevance_summary,
            "discovery": True,
        }
        trend = dict(base.get("trend", {}))
        trend["materialNewsCount"] = relevance_summary.get("material", 0)
        trend["newsRelevance"] = relevance_summary.get("averageScore", 0)
        base["trend"] = trend

    focus = bounded_int(entry.get("focusWeight", 5), 0, 15)
    news_total = bounded_int(news_status.get("total", len(news_items)), 0, 10_000_000)
    relevance_summary = news_status.get("relevanceSummary", {}) if isinstance(news_status.get("relevanceSummary"), dict) else news_relevance_summary(news_items)
    high_relevance = bounded_int(relevance_summary.get("high", 0), 0, 100)
    medium_relevance = bounded_int(relevance_summary.get("medium", 0), 0, 100)
    material_news = bounded_int(relevance_summary.get("material", 0), 0, 100)
    seed_score = score_candidate(base)
    evidence = discovery_evidence_profile(entry, news_items, news_status, seed_score, watched)
    no_relevant_live_news = (
        news_status.get("source") == "naver"
        and not news_items
        and bounded_int(news_status.get("rawDisplay", 0), 0, 100) > 0
    )
    relevance_penalty = 16 if no_relevant_live_news else 0
    discovery_score = bounded_int(
        focus * 3
        + high_relevance * 18
        + medium_relevance * 10
        + material_news * 12
        + min(news_total, 20) * 0.2
        + min(seed_score, 90) * 0.18
        + bounded_int(evidence.get("score", 0), 0, 100) * 0.22
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
        "materialNewsItems": material_news,
        "newsRelevanceAverage": relevance_summary.get("averageScore", 0),
        "newsImpactTypes": relevance_summary.get("impactTypes", []),
        "newsTotal": news_total,
        "focusWeight": focus,
        "quality": "matched-news" if news_items else ("filtered-news" if no_relevant_live_news else "universe"),
        "evidenceProfile": evidence,
        "evidenceGrade": evidence.get("grade"),
        "evidenceLabel": evidence.get("label"),
        "evidenceScore": evidence.get("score"),
        "evidenceReasons": evidence.get("reasons", []),
        "evidenceBlockers": evidence.get("blockers", []),
    }
    pool_memory = entry.get("poolMemory")
    if isinstance(pool_memory, dict):
        base["discovery"]["poolRetained"] = True
        base["discovery"]["poolMemory"] = pool_memory
        base["discovery"]["poolScore"] = bounded_int(pool_memory.get("score", 0), 0, 100)
    return base


def auto_candidate_cache_key(watched: set[str]) -> str:
    return json.dumps(
        {
            "enabled": SIGNAL_AUTO_CANDIDATES_ENABLED,
            "limit": SIGNAL_AUTO_CANDIDATE_LIMIT,
            "selectionLimit": SIGNAL_DISCOVERY_SELECTION_LIMIT,
            "domesticLimit": SIGNAL_DOMESTIC_CANDIDATE_LIMIT,
            "overseasLimit": SIGNAL_OVERSEAS_CANDIDATE_LIMIT,
            "maxSymbols": SIGNAL_DISCOVERY_MAX_SYMBOLS,
            "scanRotation": SIGNAL_DISCOVERY_SCAN_ROTATION_ENABLED,
            "scanBucket": discovery_scan_bucket(),
            "display": SIGNAL_DISCOVERY_NEWS_DISPLAY,
            "qualityMinScore": SIGNAL_DISCOVERY_QUALITY_MIN_SCORE,
            "reserveMinScore": SIGNAL_DISCOVERY_RESERVE_MIN_SCORE,
            "strongEvidenceScore": SIGNAL_DISCOVERY_STRONG_EVIDENCE_SCORE,
            "qualifiedEvidenceScore": SIGNAL_DISCOVERY_QUALIFIED_EVIDENCE_SCORE,
            "poolRetainLimit": SIGNAL_CANDIDATE_POOL_RETAIN_LIMIT,
            "poolRetainMinScore": SIGNAL_CANDIDATE_POOL_RETAIN_MIN_SCORE,
            "poolUpdatedAt": candidate_pool_summary().get("updatedAt", ""),
            "symbols": SIGNAL_DISCOVERY_SYMBOLS,
            "watch": sorted(watched),
            "naverReady": NAVER_LIVE_NEWS and naver_news_config_status()["readyForNews"],
            "date": datetime.now(KST).date().isoformat(),
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def discovery_scan_bucket() -> int:
    interval = max(60, SIGNAL_DISCOVERY_BOT_INTERVAL_SECONDS, SIGNAL_DISCOVERY_CACHE_SECONDS)
    return int(datetime.now(KST).timestamp() // interval)


def discovery_scan_entries(entries: list[dict]) -> tuple[list[dict], dict]:
    total = len(entries)
    limit = max(1, SIGNAL_DISCOVERY_MAX_SYMBOLS)
    if total <= limit:
        return entries, {
            "rotationEnabled": False,
            "offset": 0,
            "limit": limit,
            "total": total,
            "wrapped": False,
        }
    if not SIGNAL_DISCOVERY_SCAN_ROTATION_ENABLED:
        return entries[:limit], {
            "rotationEnabled": False,
            "offset": 0,
            "limit": limit,
            "total": total,
            "wrapped": False,
        }
    bucket = discovery_scan_bucket()
    offset = (bucket * limit) % total
    rotated = [*entries[offset:], *entries[:offset]]
    return rotated[:limit], {
        "rotationEnabled": True,
        "bucket": bucket,
        "offset": offset,
        "limit": limit,
        "total": total,
        "wrapped": offset + limit > total,
    }


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
    evidence = discovery.get("evidenceProfile", {}) if isinstance(discovery.get("evidenceProfile"), dict) else {}
    evidence_score = bounded_int(evidence.get("score", discovery.get("evidenceScore", 0)), 0, 100)
    evidence_grade = str(evidence.get("grade", discovery.get("evidenceGrade", "weak")))
    focus = bounded_int(discovery.get("focusWeight", 0), 0, 15)
    news_items = bounded_int(discovery.get("newsItems", 0), 0, 1_000)
    raw_news = bounded_int(discovery.get("rawNewsItems", 0), 0, 1_000)
    filtered = bounded_int(discovery.get("filteredNewsItems", 0), 0, 1_000)
    material_news = bounded_int(discovery.get("materialNewsItems", 0), 0, 1_000)
    relevance_average = display_number_to_decimal(discovery.get("newsRelevanceAverage"))
    pool_memory = discovery.get("poolMemory", {}) if isinstance(discovery.get("poolMemory"), dict) else {}
    pool_retained = bool(discovery.get("poolRetained") or pool_memory.get("retained"))
    pool_score = bounded_int(pool_memory.get("score", discovery.get("poolScore", 0)), 0, 100)
    hidden = is_hidden_discovery_candidate(candidate)
    watched_hit = symbol in watched

    if evidence_grade == "strong" and score >= SIGNAL_DISCOVERY_RESERVE_MIN_SCORE:
        tier, rank, reason = "primary", 0, "강한 발굴 근거와 투자 재료성 뉴스가 확인된 후보"
    elif evidence_grade == "qualified" and score >= SIGNAL_DISCOVERY_RESERVE_MIN_SCORE:
        tier, rank, reason = "primary", 0, "뉴스 관련성과 재료성이 검증된 후보"
    elif evidence_grade == "risk" and score >= SIGNAL_DISCOVERY_RESERVE_MIN_SCORE:
        tier, rank, reason = "reserve", 1, "리스크성 뉴스 후보라 신규 진입 전 확인 필요"
    elif watched_hit and evidence_grade in {"thin", "qualified", "strong"} and score >= SIGNAL_DISCOVERY_RESERVE_MIN_SCORE:
        tier, rank, reason = "reserve", 1, "관심 종목이나 발굴 근거 추가 확인 필요"
    elif material_news > 0 and score >= max(45, SIGNAL_DISCOVERY_RESERVE_MIN_SCORE) and evidence_score >= SIGNAL_DISCOVERY_QUALIFIED_EVIDENCE_SCORE:
        tier, rank, reason = "primary", 0, "투자 재료성 뉴스가 확인된 후보"
    elif news_items > 0 and relevance_average is not None and relevance_average >= Decimal("65") and evidence_score >= SIGNAL_DISCOVERY_QUALIFIED_EVIDENCE_SCORE:
        tier, rank, reason = "primary", 0, "고관련 뉴스가 확인된 후보"
    elif news_items > 0 and score >= SIGNAL_DISCOVERY_RESERVE_MIN_SCORE and evidence_grade != "weak":
        tier, rank, reason = "reserve", 1, "관련 뉴스는 있으나 투자 재료성 추가 확인 필요"
    elif hidden and score >= SIGNAL_DISCOVERY_QUALITY_MIN_SCORE and evidence_grade in {"thin", "qualified", "strong"}:
        tier, rank, reason = "reserve", 1, "숨은 후보이나 뉴스·가격 반응 추가 확인 필요"
    elif focus >= 8 and filtered == 0 and score >= SIGNAL_DISCOVERY_QUALITY_MIN_SCORE and evidence_score >= 45:
        tier, rank, reason = "reserve", 1, "테마 가중치가 높아 보조 후보로 유지"
    elif pool_retained and pool_score >= SIGNAL_CANDIDATE_POOL_RETAIN_MIN_SCORE and score >= max(40, SIGNAL_DISCOVERY_RESERVE_MIN_SCORE - 8):
        tier, rank, reason = "reserve", 1, "후보 풀에서 검증 상태가 유지되어 재점검 대상"
    elif raw_news and filtered and not news_items:
        tier, rank, reason = "rejected", 3, "검색 뉴스는 있었지만 종목 관련성이 낮음"
    elif evidence_grade == "weak":
        tier, rank, reason = "rejected", 3, "발굴 근거 점수가 낮아 후보 제외"
    else:
        tier, rank, reason = "rejected", 3, "뉴스·점수 기준 미달"

    return {
        "tier": tier,
        "rank": rank,
        "reason": reason,
        "score": score,
        "evidenceScore": evidence_score,
        "evidenceGrade": evidence_grade,
        "focusWeight": focus,
        "newsItems": news_items,
    }


def discovery_selection_sort_key(candidate: dict) -> tuple[int, int, int, int, int, int, int]:
    discovery = candidate.get("discovery", {}) if isinstance(candidate.get("discovery"), dict) else {}
    quality = discovery.get("qualityProfile", {}) if isinstance(discovery.get("qualityProfile"), dict) else {}
    evidence = discovery.get("evidenceProfile", {}) if isinstance(discovery.get("evidenceProfile"), dict) else {}
    pool_memory = discovery.get("poolMemory", {}) if isinstance(discovery.get("poolMemory"), dict) else {}
    return (
        -bounded_int(quality.get("rank", 9), 0, 9),
        bounded_int(evidence.get("score", discovery.get("evidenceScore", 0)), 0, 100),
        bounded_int(discovery.get("materialNewsItems", 0), 0, 1_000),
        bounded_int(pool_memory.get("score", discovery.get("poolScore", 0)), 0, 100),
        bounded_int(quality.get("score", discovery.get("score", 0)), 0, 100),
        bounded_int(discovery.get("newsItems", 0), 0, 1_000),
        score_candidate(candidate),
    )


def prepare_quality_candidates(discovered: list[dict], watched: set[str]) -> tuple[list[dict], dict]:
    prepared = []
    counts = {
        "primary": 0,
        "reserve": 0,
        "rejected": 0,
        "evidenceStrong": 0,
        "evidenceQualified": 0,
        "evidenceThin": 0,
        "evidenceRisk": 0,
        "evidenceWeak": 0,
        "evidenceScoreTotal": 0,
        "evidenceScoredCount": 0,
    }
    for candidate in discovered:
        item = dict(candidate)
        discovery = dict(item.get("discovery", {})) if isinstance(item.get("discovery"), dict) else {}
        profile = discovery_quality_profile(item, watched)
        evidence = discovery.get("evidenceProfile", {}) if isinstance(discovery.get("evidenceProfile"), dict) else {}
        evidence_grade = str(evidence.get("grade", profile.get("evidenceGrade", "weak")))
        evidence_score = bounded_int(evidence.get("score", profile.get("evidenceScore", 0)), 0, 100)
        discovery["qualityProfile"] = profile
        discovery["qualityTier"] = profile["tier"]
        discovery["qualityReason"] = profile["reason"]
        item["discovery"] = discovery
        counts[profile["tier"]] = counts.get(profile["tier"], 0) + 1
        evidence_key = {
            "strong": "evidenceStrong",
            "qualified": "evidenceQualified",
            "thin": "evidenceThin",
            "risk": "evidenceRisk",
            "weak": "evidenceWeak",
        }.get(evidence_grade, "evidenceWeak")
        counts[evidence_key] = counts.get(evidence_key, 0) + 1
        counts["evidenceScoreTotal"] += evidence_score
        counts["evidenceScoredCount"] += 1
        prepared.append(item)
    prepared.sort(key=discovery_selection_sort_key, reverse=True)
    if counts["evidenceScoredCount"]:
        counts["averageEvidenceScore"] = round(counts["evidenceScoreTotal"] / counts["evidenceScoredCount"], 1)
    else:
        counts["averageEvidenceScore"] = 0
    return prepared, counts


def balanced_candidate_selection(discovered: list[dict], watched: set[str]) -> tuple[list[dict], dict]:
    quality_candidates, quality_counts = prepare_quality_candidates(discovered, watched)
    selection_limit = max(1, SIGNAL_DISCOVERY_SELECTION_LIMIT)
    domestic_target = max(SIGNAL_DOMESTIC_CANDIDATE_LIMIT, selection_limit // 2)
    overseas_target = max(SIGNAL_OVERSEAS_CANDIDATE_LIMIT, selection_limit // 2)
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

    add_from_bucket(domestic, domestic_target, "primary")
    add_from_bucket(overseas, overseas_target, "primary")
    add_from_bucket(domestic, domestic_target, "reserve")
    add_from_bucket(overseas, overseas_target, "reserve")
    add_from_bucket(domestic_all, domestic_target)
    add_from_bucket(overseas_all, overseas_target)

    seen = {str(item.get("symbol", "")).upper() for item in selected}
    for item in selectable:
        if len(selected) >= selection_limit:
            break
        symbol = str(item.get("symbol", "")).upper()
        if symbol in seen:
            continue
        selected.append(item)
        seen.add(symbol)

    fallback_selected = 0
    if not selected and quality_candidates:
        selected = quality_candidates[: min(selection_limit, 12)]
        fallback_selected = len(selected)

    domestic_selected = sorted(
        [item for item in selected if candidate_bucket(item) == "domestic"],
        key=discovery_selection_sort_key,
        reverse=True,
    )
    overseas_selected = sorted(
        [item for item in selected if candidate_bucket(item) == "overseas"],
        key=discovery_selection_sort_key,
        reverse=True,
    )
    final_selected = [*domestic_selected, *overseas_selected]
    seen_final = {str(item.get("symbol", "")).upper() for item in final_selected}
    if len(final_selected) < selection_limit:
        for item in sorted(selected, key=discovery_selection_sort_key, reverse=True):
            if len(final_selected) >= selection_limit:
                break
            symbol = str(item.get("symbol", "")).upper()
            if symbol in seen_final:
                continue
            final_selected.append(item)
            seen_final.add(symbol)
    final_selected = sorted(final_selected[:selection_limit], key=discovery_selection_sort_key, reverse=True)
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
        "evidenceStrongCount": quality_counts.get("evidenceStrong", 0),
        "evidenceQualifiedCount": quality_counts.get("evidenceQualified", 0),
        "evidenceThinCount": quality_counts.get("evidenceThin", 0),
        "evidenceRiskCount": quality_counts.get("evidenceRisk", 0),
        "evidenceWeakCount": quality_counts.get("evidenceWeak", 0),
        "averageEvidenceScore": quality_counts.get("averageEvidenceScore", 0),
        "qualityMinScore": SIGNAL_DISCOVERY_QUALITY_MIN_SCORE,
        "reserveMinScore": SIGNAL_DISCOVERY_RESERVE_MIN_SCORE,
        "targetCandidateCount": selection_limit,
        "selectionLimit": selection_limit,
        "domesticSelected": domestic_selected_count,
        "overseasSelected": overseas_selected_count,
        "domesticLimit": domestic_target,
        "overseasLimit": overseas_target,
        "domesticShortfall": max(0, SIGNAL_DOMESTIC_CANDIDATE_LIMIT - domestic_selected_count),
        "overseasShortfall": max(0, SIGNAL_OVERSEAS_CANDIDATE_LIMIT - overseas_selected_count),
    }


DISCOVERY_STATUS_SUMMARY_KEYS = [
    "universeCount",
    "scanTargetCount",
    "scanRotation",
    "scannedCount",
    "domesticSelected",
    "overseasSelected",
    "domesticLimit",
    "overseasLimit",
    "qualityPrimaryCount",
    "qualityReserveCount",
    "qualityRejectedCount",
    "qualitySelectedPrimary",
    "qualitySelectedReserve",
    "qualitySelectedFallback",
    "qualityFallbackCount",
    "evidenceStrongCount",
    "evidenceQualifiedCount",
    "evidenceThinCount",
    "evidenceRiskCount",
    "evidenceWeakCount",
    "averageEvidenceScore",
    "targetCandidateCount",
    "selectionLimit",
    "domesticShortfall",
    "overseasShortfall",
    "discoveryNewsCount",
    "materialNewsCount",
    "selectedMaterialNewsCount",
    "filteredNewsCount",
    "candidatePoolRetainLimit",
    "candidatePoolRetainMinScore",
    "candidatePoolRetainedInputCount",
    "candidatePoolRetainedScanCount",
    "candidatePoolMemoryAppliedCount",
    "candidatePoolSelectedCount",
    "candidatePoolSelectedSymbols",
]


def stored_discovery_initial_candidates(mode: str, watched: set[str]) -> tuple[list[dict], dict] | None:
    if not SIGNAL_DASHBOARD_STORED_DISCOVERY_FIRST:
        return None
    record = discovery_latest_record(include_dashboard=True)
    if not isinstance(record, dict) or not record:
        return None
    dashboard_payload = record.get("dashboard", {})
    if not isinstance(dashboard_payload, dict) or not dashboard_payload:
        return None
    raw_candidates = dashboard_payload.get("candidates", [])
    if not isinstance(raw_candidates, list) or not raw_candidates:
        return None
    candidates = []
    for candidate in raw_candidates:
        if not isinstance(candidate, dict):
            continue
        item = copy.deepcopy(candidate)
        discovery = dict(item.get("discovery", {})) if isinstance(item.get("discovery"), dict) else {}
        discovery["storedDiscovery"] = True
        discovery["storedRunId"] = record.get("id", "")
        discovery["storedMode"] = record.get("mode") or dashboard_payload.get("mode", "")
        discovery["storedCreatedAt"] = record.get("createdAt", dashboard_payload.get("generatedAt", ""))
        item["discovery"] = discovery
        item["candidateSource"] = "stored-discovery"
        candidates.append(item)
    if not candidates:
        return None

    stored_mode = str(record.get("mode") or dashboard_payload.get("mode") or "")
    summary = dashboard_payload.get("summary", {}) if isinstance(dashboard_payload.get("summary"), dict) else {}
    status = {
        "source": "stored-discovery",
        "enabled": True,
        "stored": True,
        "message": "저장된 최신 발굴 후보를 사용합니다. 새 후보 발굴은 봇/스케줄러/수동 실행에서만 수행합니다.",
        "candidateCount": len(candidates),
        "storedCandidateCount": len(candidates),
        "storedRunId": record.get("id", ""),
        "storedMode": stored_mode,
        "requestedMode": mode,
        "modeMatched": not stored_mode or stored_mode == mode,
        "storedCreatedAt": record.get("createdAt", dashboard_payload.get("generatedAt", "")),
        "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
    }
    for key in DISCOVERY_STATUS_SUMMARY_KEYS:
        if key in summary:
            status[key] = summary.get(key)
    return candidates, status


def candidate_pool_initial_candidates(seed_candidates: list[dict], watched: set[str], mode: str) -> tuple[list[dict], dict] | None:
    pool_records = candidate_pool_retainable_records(limit=SIGNAL_DISCOVERY_SELECTION_LIMIT)
    if not pool_records:
        return None
    candidates = []
    for record in pool_records:
        entry = candidate_pool_entry_from_record(record)
        candidate = default_candidate_for_entry(entry, [], {"source": "candidate_pool", "total": 0, "relevanceSummary": {}})
        memory = candidate_pool_memory_payload(record)
        discovery = dict(candidate.get("discovery", {})) if isinstance(candidate.get("discovery"), dict) else {}
        evidence = dict(discovery.get("evidenceProfile", {})) if isinstance(discovery.get("evidenceProfile"), dict) else {}
        evidence["score"] = bounded_int(record.get("evidenceScore", memory.get("evidenceScore", 0)), 0, 100)
        evidence["grade"] = record.get("evidenceGrade", memory.get("evidenceGrade", "pool"))
        evidence["reasons"] = unique_texts([record.get("stateReason", ""), memory.get("reason", ""), "저장 후보 풀에서 재검토"], limit=5)
        discovery.update({
            "source": "candidate_pool",
            "poolRetained": True,
            "poolMemory": memory,
            "poolScore": bounded_int(memory.get("score", record.get("retainScore", 0)), 0, 100),
            "score": bounded_int(record.get("retainScore", candidate.get("totalScore", 0)), 0, 100),
            "evidenceProfile": evidence,
            "qualityTier": record.get("qualityTier", ""),
        })
        candidate["discovery"] = discovery
        candidate["candidateSource"] = "candidate-pool"
        candidate["updated"] = record.get("lastSeenAt", "후보 풀")
        candidate["price"] = record.get("price", candidate.get("price", "-"))
        candidate["change"] = record.get("change", candidate.get("change", ""))
        candidates.append(candidate)

    status = {
        "source": "candidate-pool",
        "enabled": True,
        "stored": True,
        "message": "저장된 후보 풀을 사용합니다. 새 발굴 결과가 저장되기 전까지 상시 관찰 대상을 우선 표시합니다.",
        "candidateCount": len(candidates),
        "candidatePoolRetainedInputCount": len(pool_records),
        "candidatePoolRetainedScanCount": len(pool_records),
        "candidatePoolSelectedCount": len(candidates),
        "candidatePoolSelectedSymbols": [item.get("symbol", "") for item in candidates],
        "requestedMode": mode,
        "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
    }
    return candidates, status


def initial_candidates(data: dict, watched: set[str], mode: str = "", force_discovery: bool = False) -> tuple[list[dict], dict]:
    seed_candidates = data.get("candidates", [])
    if not SIGNAL_AUTO_CANDIDATES_ENABLED:
        return seed_candidates, {
            "source": "seed",
            "enabled": False,
            "message": "자동 후보 생성이 꺼져 있어 샘플 후보를 사용합니다.",
            "candidateCount": len(seed_candidates),
        }

    if not force_discovery:
        stored_result = stored_discovery_initial_candidates(mode, watched)
        if stored_result is not None:
            return stored_result
        pool_result = candidate_pool_initial_candidates(seed_candidates, watched, mode)
        if pool_result is not None:
            return pool_result

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

    base_entries = candidate_universe_entries()
    scan_entries, scan_rotation_status = discovery_scan_entries(base_entries)
    pool_records = candidate_pool_retainable_records(limit=SIGNAL_CANDIDATE_POOL_SCAN_LIMIT)
    entries, pool_input_status = merge_candidate_pool_scan_entries(
        scan_entries,
        pool_records,
    )
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

    pool_memory_status = apply_candidate_pool_memory(discovered, pool_records) if discovered else {"appliedCount": 0}
    discovered.sort(
        key=lambda item: (
            bounded_int(item.get("discovery", {}).get("score", 0)),
            score_candidate(item),
        ),
        reverse=True,
    )
    pool_scan_status = update_candidate_pool(discovered, mode=mode, stage="discovered") if discovered else {}
    selected, balance_status = balanced_candidate_selection(discovered, watched) if discovered else (seed_candidates[:SIGNAL_DISCOVERY_SELECTION_LIMIT], {})
    pool_selected = [
        item
        for item in selected
        if isinstance(item.get("discovery"), dict)
        and bool(item.get("discovery", {}).get("poolRetained"))
    ]
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
        "universeCount": len(base_entries),
        "scanTargetCount": len(entries),
        "scanRotation": scan_rotation_status,
        "scannedCount": len(discovered),
        "candidateCount": len(selected),
        "candidatePoolRetainLimit": SIGNAL_CANDIDATE_POOL_RETAIN_LIMIT,
        "candidatePoolScanLimit": SIGNAL_CANDIDATE_POOL_SCAN_LIMIT,
        "candidatePoolRetainMinScore": SIGNAL_CANDIDATE_POOL_RETAIN_MIN_SCORE,
        "candidatePoolRetainedInputCount": pool_input_status.get("retainedInputCount", 0),
        "candidatePoolRetainedExistingCount": pool_input_status.get("retainedExistingCount", 0),
        "candidatePoolRetainedAddedCount": pool_input_status.get("retainedAddedCount", 0),
        "candidatePoolRetainedScanCount": pool_input_status.get("retainedScanCount", 0),
        "candidatePoolMemoryAppliedCount": pool_memory_status.get("appliedCount", 0),
        "candidatePoolSelectedCount": len(pool_selected),
        "candidatePoolSelectedSymbols": [item.get("symbol", "") for item in pool_selected],
        **balance_status,
        "newsItemCount": sum(bounded_int(item.get("discovery", {}).get("newsItems", 0), 0, 1_000) for item in discovered),
        "selectedNewsItemCount": sum(bounded_int(item.get("discovery", {}).get("newsItems", 0), 0, 1_000) for item in selected),
        "materialNewsItemCount": sum(bounded_int(item.get("discovery", {}).get("materialNewsItems", 0), 0, 1_000) for item in discovered),
        "selectedMaterialNewsItemCount": sum(bounded_int(item.get("discovery", {}).get("materialNewsItems", 0), 0, 1_000) for item in selected),
        "filteredNewsCount": sum(bounded_int(item.get("discovery", {}).get("filteredNewsItems", 0), 0, 1_000) for item in discovered),
        "candidatePool": pool_scan_status,
        "candidatePoolCount": pool_scan_status.get("totalCount"),
        "candidatePoolActiveCount": pool_scan_status.get("activeCount"),
        "candidatePoolStatusCounts": pool_scan_status.get("statusCounts", {}),
        "candidatePoolNewCount": pool_scan_status.get("newCount"),
        "candidatePoolPromotedCount": pool_scan_status.get("promotedCount"),
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
        "portfolio": {
            "source": "disabled",
            "enabled": TOSS_LIVE_PORTFOLIO,
            "ready": False,
            "message": "포트폴리오 정보를 후보 판단에 반영하지 않았습니다.",
            "holdingCount": 0,
            "linkedCandidateCount": 0,
        },
        "selection": {
            "source": "static",
            "enabled": True,
            "message": "기본 후보 점수를 사용합니다.",
        },
        "candidate_pool": candidate_pool_summary(),
        "candidate_data": candidate_data_snapshot_status(),
        "market_data_latest": market_data_latest_status(),
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


def collect_signal_inputs(mode: str, force_discovery: bool = False) -> dict:
    data = seed_data()
    market, index_status = enrich_market_with_indices(data.get("market", {}))
    market, fx_status = enrich_market_with_fx(market)
    watched = set(watchlist())
    portfolio = safe_portfolio_status()
    raw_candidates, discovery_status = initial_candidates(data, watched, mode, force_discovery=force_discovery)
    candidates = [decorate_candidate(item, watched) for item in raw_candidates]
    candidates, candidate_data_merge_status = merge_candidate_data_snapshots_into_candidates(candidates, mode)
    candidates, live_state_merge_status = merge_live_state_into_candidates(candidates, mode)
    candidates, market_data_merge_status = merge_market_data_latest_into_candidates(candidates)
    defaults = dashboard_status_defaults()
    return {
        "mode": mode,
        "data": data,
        "market": market,
        "watched": watched,
        "portfolio": portfolio,
        "candidates": candidates,
        "statuses": {
            **defaults,
            "index": index_status,
            "fx": fx_status,
            "portfolio": {
                "source": portfolio.get("source", "unavailable"),
                "enabled": portfolio.get("enabled", False),
                "ready": portfolio.get("ready", False),
                "message": portfolio.get("message", "포트폴리오 연결 상태를 확인했습니다."),
                "holdingCount": len(portfolio.get("items", [])) if isinstance(portfolio.get("items"), list) else 0,
                "linkedCandidateCount": 0,
            },
            "discovery": discovery_status,
            "candidate_pool": discovery_status.get("candidatePool") or defaults.get("candidate_pool", {}),
            "candidate_data_merge": candidate_data_merge_status,
            "live_state_merge": live_state_merge_status,
            "market_data_latest": market_data_latest_status(),
            "market_data_merge": market_data_merge_status,
        },
        "pipeline": [
            pipeline_step(
                "collector",
                "후보·시장 수집",
                "ok",
                discovery_status.get("message", "후보와 시장 데이터를 수집했습니다."),
                len(candidates),
            ),
            pipeline_step(
                "storage",
                "저장 후보 데이터 반영",
                "ok" if candidate_data_merge_status.get("mergedCount", 0) else "fallback",
                candidate_data_merge_status.get("message", "저장된 후보별 수신 데이터를 확인했습니다."),
                candidate_data_merge_status.get("mergedCount", 0),
            ),
            pipeline_step(
                "storage",
                "직전 실시간 상태 반영",
                "ok" if live_state_merge_status.get("mergedCount", 0) else "fallback",
                live_state_merge_status.get("message", "직전 토스 확정 상태를 확인했습니다."),
                live_state_merge_status.get("mergedCount", 0),
            ),
            pipeline_step(
                "storage",
                "DB 최신 가격 반영",
                "ok" if market_data_merge_status.get("mergedCount", 0) else "fallback",
                market_data_merge_status.get("message", "DB 최신 토스 가격을 확인했습니다."),
                market_data_merge_status.get("mergedCount", 0),
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
    context["candidates"], context["statuses"]["portfolio"] = enrich_candidates_with_portfolio(
        context["candidates"],
        context.get("portfolio", {}),
    )
    context["pipeline"].append(
        pipeline_step(
            "portfolio",
            "보유 자산 반영",
            "ok" if context["statuses"]["portfolio"].get("source") == "toss" else "fallback",
            context["statuses"]["portfolio"].get("message", "포트폴리오 연결 상태를 확인했습니다."),
            context["statuses"]["portfolio"].get("linkedCandidateCount", 0),
        )
    )
    context["candidates"], context["statuses"]["selection"] = apply_candidate_selection(
        context["candidates"],
        context["market"],
        context["watched"],
    )
    context["statuses"]["candidate_pool"] = update_candidate_pool(
        context["candidates"],
        mode=context["mode"],
        stage="selected",
    )
    context["statuses"]["candidate_data"] = update_candidate_data_snapshots(
        context["candidates"],
        mode=context["mode"],
        stage="selected",
    )
    context["statuses"]["candidate_market_data_latest"] = update_market_data_latest_from_candidates(
        context["candidates"],
        mode=context["mode"],
        stage="selected",
    )
    context["statuses"]["market_data_latest"] = market_data_latest_status()
    context["pipeline"].append(
        pipeline_step(
            "scorer",
            "후보 점수 재계산",
            "ok",
            context["statuses"]["selection"].get("message", "후보 점수를 재계산했습니다."),
            len(context["candidates"]),
        )
    )
    context["pipeline"].append(
        pipeline_step(
            "pool",
            "후보 풀 갱신",
            "ok" if context["statuses"]["candidate_pool"].get("enabled", False) else "fallback",
            context["statuses"]["candidate_pool"].get("message", "후보 풀 상태를 갱신했습니다."),
            context["statuses"]["candidate_pool"].get("activeCount", 0),
        )
    )
    context["pipeline"].append(
        pipeline_step(
            "storage",
            "후보 데이터 저장",
            "ok" if context["statuses"]["candidate_data"].get("stored", False) else "fallback",
            context["statuses"]["candidate_data"].get("message", "후보별 수신 데이터 묶음을 저장했습니다."),
            context["statuses"]["candidate_data"].get("storedCount", 0),
        )
    )
    context["pipeline"].append(
        pipeline_step(
            "storage",
            "최종 Toss 가격 저장",
            "ok" if context["statuses"]["candidate_market_data_latest"].get("stored", False) else "fallback",
            context["statuses"]["candidate_market_data_latest"].get("message", "최종 후보의 Toss 가격을 최신값 저장소에 반영했습니다."),
            context["statuses"]["candidate_market_data_latest"].get("updatedCount", 0),
        )
    )
    return context


def sort_candidates_for_mode(candidates: list[dict], mode: str) -> list[dict]:
    def compression_rank(item: dict) -> int:
        compression = item.get("candidateCompression", {}) if isinstance(item, dict) else {}
        tier = str(compression.get("tier", "")) if isinstance(compression, dict) else ""
        return {
            "core": 120,
            "review": 92,
            "portfolio": 84,
            "wait": 48,
            "exclude": 8,
        }.get(tier, 50)

    def final_rank(item: dict) -> int:
        decision = item.get("finalDecision", {}) if isinstance(item, dict) else {}
        key = str(decision.get("actionKey", "")) if isinstance(decision, dict) else ""
        return {
            "buy": 100,
            "add": 96,
            "hold": 86,
            "trim": 84,
            "watch": 82,
            "pullback": 72,
            "stop": 60,
            "verify": 45,
            "exclude": 10,
        }.get(key, 50)

    def group_rank(item: dict) -> int:
        group = item.get("decisionGroup", {}) if isinstance(item, dict) else {}
        priority = bounded_int(group.get("priority", 9), 0, 9) if isinstance(group, dict) else 9
        return 100 - priority

    def decision_score(item: dict) -> int:
        group = item.get("decisionGroup", {}) if isinstance(item, dict) else {}
        return bounded_int(group.get("score", 0), 0, 100) if isinstance(group, dict) else 0

    if mode == "preopen":
        candidates.sort(key=lambda item: (compression_rank(item), final_rank(item), group_rank(item), item["preopenPriority"], decision_score(item), candidate_pool_decision_bonus(item), item["totalScore"]), reverse=True)
    elif mode == "intraday":
        candidates.sort(key=lambda item: (compression_rank(item), final_rank(item), group_rank(item), item["triggerReadiness"], decision_score(item), candidate_pool_decision_bonus(item), item["totalScore"]), reverse=True)
    else:
        candidates.sort(key=lambda item: (compression_rank(item), final_rank(item), group_rank(item), item["totalScore"], decision_score(item), candidate_pool_decision_bonus(item)), reverse=True)
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
    pool_status = context["statuses"].get("candidate_pool", candidate_pool_summary())
    market_data_status = context["statuses"].get("market_data_latest", market_data_latest_status())
    candidate_market_data_status = context["statuses"].get("candidate_market_data_latest", {})
    market_data_merge_status = context["statuses"].get("market_data_merge", {})
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
            "candidateSourceStored": bool(discovery_status.get("stored")),
            "storedDiscoveryRunId": discovery_status.get("storedRunId", ""),
            "storedDiscoveryMode": discovery_status.get("storedMode", ""),
            "storedDiscoveryCreatedAt": discovery_status.get("storedCreatedAt", ""),
            "storedDiscoveryModeMatched": discovery_status.get("modeMatched"),
            "universeCount": discovery_status.get("universeCount"),
            "scanTargetCount": discovery_status.get("scanTargetCount"),
            "scanRotation": discovery_status.get("scanRotation"),
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
            "evidenceStrongCount": discovery_status.get("evidenceStrongCount"),
            "evidenceQualifiedCount": discovery_status.get("evidenceQualifiedCount"),
            "evidenceThinCount": discovery_status.get("evidenceThinCount"),
            "evidenceRiskCount": discovery_status.get("evidenceRiskCount"),
            "evidenceWeakCount": discovery_status.get("evidenceWeakCount"),
            "averageEvidenceScore": discovery_status.get("averageEvidenceScore"),
            "targetCandidateCount": discovery_status.get("targetCandidateCount"),
            "selectionLimit": discovery_status.get("selectionLimit"),
            "domesticShortfall": discovery_status.get("domesticShortfall"),
            "overseasShortfall": discovery_status.get("overseasShortfall"),
            "discoveryNewsCount": discovery_status.get("newsItemCount"),
            "materialNewsCount": discovery_status.get("materialNewsItemCount"),
            "selectedMaterialNewsCount": discovery_status.get("selectedMaterialNewsItemCount"),
            "filteredNewsCount": discovery_status.get("filteredNewsCount"),
            "averageScoreShift": selection_status.get("averageScoreShift"),
            "averageOpportunityScore": selection_status.get("averageOpportunityScore"),
            "averageDataConfidence": selection_status.get("averageDataConfidence"),
            "averageSourceReliability": selection_status.get("averageSourceReliability"),
            "sourceReliabilityCounts": selection_status.get("sourceReliabilityCounts", {}),
            "averagePriceReaction": selection_status.get("averagePriceReaction"),
            "averageOfficialEventScore": selection_status.get("averageOfficialEventScore"),
            "officialEventCounts": selection_status.get("officialEventCounts", {}),
            "officialEventCandidateCount": selection_status.get("officialEventCandidateCount"),
            "officialRiskCandidateCount": selection_status.get("officialRiskCandidateCount"),
            "hiddenOpportunityCount": selection_status.get("hiddenOpportunityCount"),
            "decisionGroups": selection_status.get("decisionGroups", {}),
            "qualityGateCounts": selection_status.get("qualityGateCounts", {}),
            "priceReactionCounts": selection_status.get("priceReactionCounts", {}),
            "priceReactionGateCounts": selection_status.get("priceReactionGateCounts", {}),
            "priceReadinessCounts": selection_status.get("priceReadinessCounts", {}),
            "evaluationModeCounts": selection_status.get("evaluationModeCounts", {}),
            "tradeEvaluationReadyCount": selection_status.get("tradeEvaluationReadyCount"),
            "baselineEvaluationCount": selection_status.get("baselineEvaluationCount"),
            "serverCollectingCount": selection_status.get("serverCollectingCount"),
            "unavailableEvaluationCount": selection_status.get("unavailableEvaluationCount"),
            "entryDataReadyCount": selection_status.get("entryDataReadyCount"),
            "closedBaselineCandidateCount": selection_status.get("closedBaselineCandidateCount"),
            "displayDataReadyCount": selection_status.get("displayDataReadyCount"),
            "priceBasisWaitCount": selection_status.get("priceBasisWaitCount"),
            "changeWaitCount": selection_status.get("changeWaitCount"),
            "priceReactionEntryBlockedCount": selection_status.get("priceReactionEntryBlockedCount"),
            "finalDecisionCounts": selection_status.get("finalDecisionCounts", {}),
            "candidateCompressionCounts": selection_status.get("candidateCompressionCounts", {}),
            "signalValidationCounts": selection_status.get("signalValidationCounts", {}),
            "candidatePoolCount": pool_status.get("totalCount"),
            "candidatePoolActiveCount": pool_status.get("activeCount"),
            "candidatePoolStatusCounts": pool_status.get("statusCounts", {}),
            "candidatePoolNewCount": pool_status.get("newCount"),
            "candidatePoolUpdatedCount": pool_status.get("updatedCount"),
            "candidatePoolPromotedCount": pool_status.get("promotedCount"),
            "candidatePoolExpiredCount": pool_status.get("expiredCount"),
            "candidatePoolTotalPromotionCount": pool_status.get("promotionCount"),
            "candidatePoolTotalDemotionCount": pool_status.get("demotionCount"),
            "candidatePoolSoftDemotionCount": pool_status.get("softDemotionCount"),
            "candidatePoolImprovingCount": pool_status.get("improvingCount"),
            "candidatePoolWeakeningCount": pool_status.get("weakeningCount"),
            "candidatePoolMonitorReadyCount": pool_status.get("monitorReadyCount"),
            "candidatePoolMonitorWaitCount": pool_status.get("monitorWaitCount"),
            "candidatePoolMonitorWeakCount": pool_status.get("monitorWeakCount"),
            "candidatePoolPerformanceSymbolCount": pool_status.get("performanceSymbolCount"),
            "candidatePoolPerformanceMeasuredCount": pool_status.get("performanceMeasuredCount"),
            "candidatePoolPerformancePositiveCount": pool_status.get("performancePositiveCount"),
            "candidatePoolPerformanceNegativeCount": pool_status.get("performanceNegativeCount"),
            "candidatePoolPerformanceHitRate": pool_status.get("performanceHitRate"),
            "candidatePoolPerformanceAverageChange": pool_status.get("performanceAverageChange"),
            "candidatePoolPerformanceLatestAt": pool_status.get("performanceLatestAt"),
            "candidatePoolRetainLimit": discovery_status.get("candidatePoolRetainLimit"),
            "candidatePoolScanLimit": discovery_status.get("candidatePoolScanLimit", pool_status.get("scanLimit")),
            "candidatePoolRetainMinScore": discovery_status.get("candidatePoolRetainMinScore"),
            "candidatePoolRetainedInputCount": discovery_status.get("candidatePoolRetainedInputCount"),
            "candidatePoolRetainedScanCount": discovery_status.get("candidatePoolRetainedScanCount"),
            "candidatePoolMemoryAppliedCount": discovery_status.get("candidatePoolMemoryAppliedCount"),
            "candidatePoolSelectedCount": discovery_status.get("candidatePoolSelectedCount"),
            "candidatePoolSelectedSymbols": discovery_status.get("candidatePoolSelectedSymbols", []),
            "candidatePoolTopCandidates": pool_status.get("topCandidates", []),
            "confirmedSignalCount": selection_status.get("confirmedSignalCount"),
            "evidenceWaitSignalCount": selection_status.get("evidenceWaitSignalCount"),
            "reactionOnlySignalCount": selection_status.get("reactionOnlySignalCount"),
            "insufficientSignalCount": selection_status.get("insufficientSignalCount"),
            "blockedSignalCount": selection_status.get("blockedSignalCount"),
            "coreCandidateCount": selection_status.get("coreCandidateCount"),
            "reviewCandidateCount": selection_status.get("reviewCandidateCount"),
            "waitCandidateCompressionCount": selection_status.get("waitCandidateCompressionCount"),
            "portfolioCandidateCompressionCount": selection_status.get("portfolioCandidateCompressionCount"),
            "excludeCandidateCompressionCount": selection_status.get("excludeCandidateCompressionCount"),
            "compressedTopCandidates": selection_status.get("compressedTopCandidates", []),
            "coreCandidateLimit": selection_status.get("coreCandidateLimit"),
            "buyDecisionCount": selection_status.get("buyDecisionCount"),
            "addDecisionCount": selection_status.get("addDecisionCount"),
            "holdDecisionCount": selection_status.get("holdDecisionCount"),
            "trimDecisionCount": selection_status.get("trimDecisionCount"),
            "stopDecisionCount": selection_status.get("stopDecisionCount"),
            "pullbackDecisionCount": selection_status.get("pullbackDecisionCount"),
            "watchDecisionCount": selection_status.get("watchDecisionCount"),
            "verifyDecisionCount": selection_status.get("verifyDecisionCount"),
            "portfolioLinkedCandidateCount": context["statuses"].get("portfolio", {}).get("linkedCandidateCount", 0),
            "portfolioHoldingCount": context["statuses"].get("portfolio", {}).get("holdingCount", 0),
            "marketDataLatestCount": market_data_status.get("itemCount"),
            "marketDataLatestAt": market_data_status.get("latestAt"),
            "candidateMarketDataLatestUpdatedCount": candidate_market_data_status.get("updatedCount", 0),
            "candidateMarketDataLatestStored": bool(candidate_market_data_status.get("stored", False)),
            "marketDataMergedCount": market_data_merge_status.get("mergedCount", 0),
            "marketDataPriceMergedCount": market_data_merge_status.get("priceMergedCount", 0),
            "marketDataChangeMergedCount": market_data_merge_status.get("changeMergedCount", 0),
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
            "candidatePool": pool_status,
            "marketDataLatest": market_data_status,
            "candidateMarketDataLatest": candidate_market_data_status,
            "marketDataMerge": market_data_merge_status,
            "portfolio": context["statuses"].get("portfolio", {}),
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


def dashboard(mode: str, force_discovery: bool = False) -> dict:
    context = collect_signal_inputs(mode, force_discovery=force_discovery)
    context = analyze_signal_context(context)
    context = score_signal_context(context)
    context = select_signal_context(context)
    return build_dashboard_payload(context)


def candidate_from_pool_record_for_prefetch(record: dict, seed_lookup: dict[str, dict], watched: set[str]) -> dict:
    entry = candidate_pool_entry_from_record(record)
    symbol = str(entry.get("symbol", "")).strip().upper()
    if symbol and symbol in seed_lookup:
        candidate = copy.deepcopy(seed_lookup[symbol])
        candidate["headline"] = entry.get("headline") or candidate.get("headline", "")
        candidate["themes"] = unique_texts(
            [
                *text_list(entry.get("themes", []), limit=8),
                *text_list(candidate.get("themes", []), limit=8),
            ],
            limit=8,
        )
    else:
        candidate = default_candidate_for_entry(
            entry,
            [],
            {
                "source": "candidate-pool",
                "total": 0,
                "display": 0,
                "message": "후보 풀 저장값을 기반으로 보강 대상을 구성했습니다.",
            },
        )

    candidate["symbol"] = symbol or str(candidate.get("symbol", "")).strip().upper()
    candidate["name"] = candidate.get("name") or entry.get("name") or candidate["symbol"]
    candidate["market"] = candidate.get("market") or entry.get("market", "")
    candidate["category"] = candidate.get("category") or entry.get("category", "")
    candidate["candidateSource"] = "candidate-pool-prefetch"
    candidate["discoveryTier"] = entry.get("discoveryTier", candidate.get("discoveryTier", "pool"))
    candidate["opportunityType"] = entry.get("opportunityType", candidate.get("opportunityType", "pool-retain"))

    for key in ("price", "change"):
        value = record.get(key)
        if value not in {None, "", "-"}:
            candidate[key] = value
    if record.get("lastSeenAt"):
        candidate["updated"] = record.get("lastSeenAt")

    discovery = dict(candidate.get("discovery", {})) if isinstance(candidate.get("discovery"), dict) else {}
    memory = entry.get("poolMemory") if isinstance(entry.get("poolMemory"), dict) else candidate_pool_memory_payload(record)
    discovery.update({
        "source": discovery.get("source") or "candidate-pool",
        "poolRetained": True,
        "poolMemory": memory,
        "poolScore": bounded_int(memory.get("score", record.get("retainScore", 0)), 0, 100),
        "score": max(
            bounded_int(discovery.get("score", 0), 0, 100),
            bounded_int(record.get("retainScore", record.get("totalScore", 0)), 0, 100),
        ),
        "evidenceScore": max(
            bounded_int(discovery.get("evidenceScore", 0), 0, 100),
            bounded_int(record.get("evidenceScore", 0), 0, 100),
        ),
        "evidenceGrade": discovery.get("evidenceGrade") or record.get("evidenceGrade", ""),
        "qualityTier": discovery.get("qualityTier") or record.get("qualityTier", ""),
    })
    candidate["discovery"] = discovery
    candidate["totalScore"] = bounded_int(record.get("totalScore", candidate.get("totalScore", 0)), 0, 100)
    candidate["triggerReadiness"] = bounded_int(record.get("triggerReadiness", candidate.get("triggerReadiness", 0)), 0, 100)
    return decorate_candidate(candidate, watched)


def prefetch_enrichment_status(source: str, error: Exception, message: str) -> dict:
    return {
        "source": source,
        "enabled": True,
        "error": str(error)[:180],
        "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
        "message": message,
    }


def prefetch_candidate_pool_market_data(mode: str, trigger: str = "bot", market: dict | None = None) -> dict:
    if not SIGNAL_CANDIDATE_PREFETCH_ENABLED:
        return {
            "enabled": False,
            "mode": mode,
            "trigger": trigger,
            "message": "후보 풀 사전 보강이 꺼져 있습니다.",
        }

    records = candidate_pool_retainable_records(limit=SIGNAL_CANDIDATE_PREFETCH_LIMIT)
    if not records:
        return {
            "enabled": True,
            "mode": mode,
            "trigger": trigger,
            "inputCount": 0,
            "prefetchedCount": 0,
            "message": "보강할 후보 풀 종목이 아직 없습니다.",
        }

    data = seed_data()
    seed_lookup = {
        str(item.get("symbol", "")).strip().upper(): item
        for item in data.get("candidates", [])
        if isinstance(item, dict) and str(item.get("symbol", "")).strip()
    }
    watched = set(watchlist())
    candidates = [candidate_from_pool_record_for_prefetch(record, seed_lookup, watched) for record in records]
    candidates, candidate_data_merge_status = merge_candidate_data_snapshots_into_candidates(candidates, mode)
    candidates, live_state_merge_status = merge_live_state_into_candidates(candidates, mode)
    candidates, market_data_merge_status = merge_market_data_latest_into_candidates(candidates)

    statuses: dict[str, dict] = {
        "candidateDataMerge": candidate_data_merge_status,
        "liveStateMerge": live_state_merge_status,
        "marketDataMerge": market_data_merge_status,
    }

    enrichers = [
        ("prices", enrich_candidates_with_toss_prices, "토스 현재가 사전 보강에 실패했습니다."),
        ("candles", enrich_candidates_with_toss_candles, "토스 차트 사전 보강에 실패했습니다."),
        ("orderbook", enrich_candidates_with_toss_orderbook, "토스 호가 사전 보강에 실패했습니다."),
        ("trades", enrich_candidates_with_toss_trades, "토스 체결 사전 보강에 실패했습니다."),
        ("disclosures", enrich_candidates_with_dart_disclosures, "공시 사전 보강에 실패했습니다."),
        ("naver", enrich_candidates_with_naver_news, "뉴스 사전 보강에 실패했습니다."),
        ("gdelt", enrich_candidates_with_gdelt_news, "글로벌 뉴스 사전 보강에 실패했습니다."),
    ]
    for key, enricher, failure_message in enrichers:
        try:
            candidates, statuses[key] = enricher(candidates)
        except Exception as error:
            statuses[key] = prefetch_enrichment_status("error", error, failure_message)

    try:
        portfolio = safe_portfolio_status()
        candidates, statuses["portfolio"] = enrich_candidates_with_portfolio(candidates, portfolio)
    except Exception as error:
        statuses["portfolio"] = prefetch_enrichment_status("error", error, "포트폴리오 사전 보강에 실패했습니다.")

    candidates, statuses["selection"] = apply_candidate_selection(
        candidates,
        market if isinstance(market, dict) else data.get("market", {}),
        watched,
    )
    candidates = sort_candidates_for_mode(candidates, mode)
    live_state_status = update_live_state_from_candidates(candidates, mode)
    pool_status = update_candidate_pool(candidates, mode=mode, stage="prefetch")
    candidate_data_status = update_candidate_data_snapshots(candidates, mode, stage=f"prefetch-{trigger}")
    candidate_latest_status = update_market_data_latest_from_candidates(candidates, mode=mode, stage=f"prefetch-{trigger}")

    completeness = [candidate.get("dataCompleteness", {}) for candidate in candidates if isinstance(candidate, dict)]
    entry_ready_count = len([item for item in completeness if isinstance(item, dict) and item.get("entryReady")])
    display_ready_count = len([item for item in completeness if isinstance(item, dict) and item.get("displayReady")])
    missing_counts: dict[str, int] = {}
    for item in completeness:
        if not isinstance(item, dict):
            continue
        missing_values = item.get("missing", []) if isinstance(item.get("missing"), list) else []
        for key in missing_values:
            missing_counts[str(key)] = missing_counts.get(str(key), 0) + 1

    price_status = statuses.get("prices", {})
    return {
        "enabled": True,
        "mode": mode,
        "trigger": trigger,
        "inputCount": len(records),
        "prefetchedCount": len(candidates),
        "limit": SIGNAL_CANDIDATE_PREFETCH_LIMIT,
        "priceCount": price_status.get("priceCount", 0),
        "requestedPriceCount": price_status.get("requestedCount", len(candidates)),
        "receivedPriceCount": price_status.get("receivedCount", price_status.get("priceCount", 0)),
        "priceBatchCount": price_status.get("batchCount", 0),
        "priceBatchErrorCount": price_status.get("batchErrorCount", 0),
        "storedFallbackCount": price_status.get("storedFallbackCount", 0),
        "retainedCount": price_status.get("retainedCount", 0),
        "missingCount": price_status.get("missingCount", 0),
        "missingSymbols": price_status.get("missingSymbols", []),
        "displayReadyCount": display_ready_count,
        "entryReadyCount": entry_ready_count,
        "missingCounts": missing_counts,
        "candidateData": candidate_data_status,
        "candidateMarketDataLatest": candidate_latest_status,
        "liveState": live_state_status,
        "candidatePool": pool_status,
        "statuses": statuses,
        "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
        "message": f"후보 풀 {len(candidates)}개를 서버에서 사전 보강하고 저장했습니다.",
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
        "candidatePrefetchEnabled": SIGNAL_CANDIDATE_PREFETCH_ENABLED,
        "candidatePrefetchLimit": SIGNAL_CANDIDATE_PREFETCH_LIMIT,
        "candidatePrefetchIntervalSeconds": SIGNAL_CANDIDATE_PREFETCH_INTERVAL_SECONDS,
        "historyLimit": SIGNAL_RUN_HISTORY_LIMIT,
        "performanceAutoUpdate": SIGNAL_PERFORMANCE_AUTO_UPDATE,
        "performanceMinAgeMinutes": max(0, SIGNAL_PERFORMANCE_MIN_AGE_MINUTES),
        "performanceRunLimit": SIGNAL_PERFORMANCE_RUN_LIMIT,
        "performanceTopCandidates": SIGNAL_PERFORMANCE_TOP_CANDIDATES,
        "jobs": scheduler_jobs(),
        "runsDir": display_local_path(RUNS_DIR),
    }


def scheduled_snapshot_exists(run_date: str, mode: str) -> bool:
    if database_storage_enabled():
        exists = db_scheduled_snapshot_exists(run_date, mode)
        if exists or not DB_LAST_ERROR:
            return exists
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


def candidate_prefetch_due(now: datetime | None = None) -> bool:
    if not SIGNAL_SCHEDULER_ENABLED or not SIGNAL_CANDIDATE_PREFETCH_ENABLED:
        return False
    now = now or datetime.now(KST)
    with SCHEDULER_LOCK:
        latest = SCHEDULER_STATE.get("lastCandidatePrefetch", {})
    latest_at = ""
    if isinstance(latest, dict):
        latest_at = str(latest.get("updatedAt") or latest.get("checkedAt") or "")
    parsed = parse_iso_datetime(latest_at)
    if parsed is None:
        return True
    age_seconds = max(0, int((now - parsed.astimezone(KST)).total_seconds()))
    return age_seconds >= SIGNAL_CANDIDATE_PREFETCH_INTERVAL_SECONDS


def run_scheduler_candidate_prefetch(now: datetime | None = None) -> dict:
    now = now or datetime.now(KST)
    if not CANDIDATE_PREFETCH_LOCK.acquire(blocking=False):
        status = {
            "enabled": SIGNAL_CANDIDATE_PREFETCH_ENABLED,
            "skipped": True,
            "reason": "already-running",
            "checkedAt": now.isoformat(timespec="seconds"),
            "message": "후보 데이터 보강이 이미 실행 중입니다.",
        }
        with SCHEDULER_LOCK:
            SCHEDULER_STATE["lastCandidatePrefetch"] = status
        return status
    try:
        with DISCOVERY_BOT_LOCK:
            discovery_running = bool(DISCOVERY_BOT_STATE.get("running"))
        if discovery_running:
            status = {
                "enabled": SIGNAL_CANDIDATE_PREFETCH_ENABLED,
                "skipped": True,
                "reason": "discovery-running",
                "checkedAt": now.isoformat(timespec="seconds"),
                "message": "발굴 봇 실행 중이라 후보 데이터 보강을 다음 주기로 미룹니다.",
            }
        else:
            status = prefetch_candidate_pool_market_data(
                discovery_bot_mode(),
                trigger="scheduler-prefetch",
            )
            status["scheduled"] = True
            status["intervalSeconds"] = SIGNAL_CANDIDATE_PREFETCH_INTERVAL_SECONDS
            status["checkedAt"] = now.isoformat(timespec="seconds")
        with SCHEDULER_LOCK:
            SCHEDULER_STATE["lastCandidatePrefetch"] = status
            SCHEDULER_STATE["lastCandidatePrefetchError"] = ""
        return status
    except Exception as error:
        status = {
            "enabled": SIGNAL_CANDIDATE_PREFETCH_ENABLED,
            "error": str(error)[:240],
            "checkedAt": now.isoformat(timespec="seconds"),
            "message": "후보 풀 Toss 데이터 보강에 실패했습니다.",
        }
        with SCHEDULER_LOCK:
            SCHEDULER_STATE["lastCandidatePrefetch"] = status
            SCHEDULER_STATE["lastCandidatePrefetchError"] = status["error"]
        return status
    finally:
        CANDIDATE_PREFETCH_LOCK.release()


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
            "reaction": item.get("priceReaction", {}).get("score") if isinstance(item.get("priceReaction"), dict) else None,
            "finalDecision": item.get("finalDecision", {}).get("action", "") if isinstance(item.get("finalDecision"), dict) else "",
            "compression": item.get("candidateCompression", {}).get("label", "") if isinstance(item.get("candidateCompression"), dict) else "",
            "validation": item.get("signalValidation", {}).get("label", "") if isinstance(item.get("signalValidation"), dict) else "",
            "poolState": item.get("candidatePool", {}).get("stateLabel", "") if isinstance(item.get("candidatePool"), dict) else "",
            "evidence": item.get("discovery", {}).get("evidenceLabel", "") if isinstance(item.get("discovery"), dict) else "",
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
        "averageSourceReliability": summary.get("averageSourceReliability"),
        "averagePriceReaction": summary.get("averagePriceReaction"),
        "sourceReliabilityCounts": summary.get("sourceReliabilityCounts", {}),
        "materialNewsCount": summary.get("materialNewsCount"),
        "selectedMaterialNewsCount": summary.get("selectedMaterialNewsCount"),
        "filteredNewsCount": summary.get("filteredNewsCount"),
        "qualityGateCounts": summary.get("qualityGateCounts", {}),
        "priceReactionCounts": summary.get("priceReactionCounts", {}),
        "priceReactionGateCounts": summary.get("priceReactionGateCounts", {}),
        "priceReadinessCounts": summary.get("priceReadinessCounts", {}),
        "evaluationModeCounts": summary.get("evaluationModeCounts", {}),
        "tradeEvaluationReadyCount": summary.get("tradeEvaluationReadyCount"),
        "baselineEvaluationCount": summary.get("baselineEvaluationCount"),
        "serverCollectingCount": summary.get("serverCollectingCount"),
        "unavailableEvaluationCount": summary.get("unavailableEvaluationCount"),
        "entryDataReadyCount": summary.get("entryDataReadyCount"),
        "closedBaselineCandidateCount": summary.get("closedBaselineCandidateCount"),
        "displayDataReadyCount": summary.get("displayDataReadyCount"),
        "priceBasisWaitCount": summary.get("priceBasisWaitCount"),
        "changeWaitCount": summary.get("changeWaitCount"),
        "priceReactionEntryBlockedCount": summary.get("priceReactionEntryBlockedCount"),
        "finalDecisionCounts": summary.get("finalDecisionCounts", {}),
        "candidateCompressionCounts": summary.get("candidateCompressionCounts", {}),
        "signalValidationCounts": summary.get("signalValidationCounts", {}),
        "candidatePoolCount": summary.get("candidatePoolCount"),
        "candidatePoolActiveCount": summary.get("candidatePoolActiveCount"),
        "candidatePoolStatusCounts": summary.get("candidatePoolStatusCounts", {}),
        "candidatePoolNewCount": summary.get("candidatePoolNewCount"),
        "candidatePoolPromotedCount": summary.get("candidatePoolPromotedCount"),
        "candidatePoolTotalPromotionCount": summary.get("candidatePoolTotalPromotionCount"),
        "candidatePoolTotalDemotionCount": summary.get("candidatePoolTotalDemotionCount"),
        "candidatePoolSoftDemotionCount": summary.get("candidatePoolSoftDemotionCount"),
        "candidatePoolImprovingCount": summary.get("candidatePoolImprovingCount"),
        "candidatePoolWeakeningCount": summary.get("candidatePoolWeakeningCount"),
        "candidatePoolMonitorReadyCount": summary.get("candidatePoolMonitorReadyCount"),
        "candidatePoolMonitorWaitCount": summary.get("candidatePoolMonitorWaitCount"),
        "candidatePoolMonitorWeakCount": summary.get("candidatePoolMonitorWeakCount"),
        "candidatePoolPerformanceSymbolCount": summary.get("candidatePoolPerformanceSymbolCount"),
        "candidatePoolPerformanceMeasuredCount": summary.get("candidatePoolPerformanceMeasuredCount"),
        "candidatePoolPerformancePositiveCount": summary.get("candidatePoolPerformancePositiveCount"),
        "candidatePoolPerformanceNegativeCount": summary.get("candidatePoolPerformanceNegativeCount"),
        "candidatePoolPerformanceHitRate": summary.get("candidatePoolPerformanceHitRate"),
        "candidatePoolPerformanceAverageChange": summary.get("candidatePoolPerformanceAverageChange"),
        "candidatePoolRetainLimit": summary.get("candidatePoolRetainLimit"),
        "candidatePoolScanLimit": summary.get("candidatePoolScanLimit"),
        "candidatePoolRetainMinScore": summary.get("candidatePoolRetainMinScore"),
        "candidatePoolRetainedInputCount": summary.get("candidatePoolRetainedInputCount"),
        "candidatePoolRetainedScanCount": summary.get("candidatePoolRetainedScanCount"),
        "candidatePoolMemoryAppliedCount": summary.get("candidatePoolMemoryAppliedCount"),
        "candidatePoolSelectedCount": summary.get("candidatePoolSelectedCount"),
        "candidatePoolSelectedSymbols": summary.get("candidatePoolSelectedSymbols", []),
        "candidatePoolTopCandidates": summary.get("candidatePoolTopCandidates", []),
        "confirmedSignalCount": summary.get("confirmedSignalCount"),
        "evidenceWaitSignalCount": summary.get("evidenceWaitSignalCount"),
        "reactionOnlySignalCount": summary.get("reactionOnlySignalCount"),
        "blockedSignalCount": summary.get("blockedSignalCount"),
        "coreCandidateCount": summary.get("coreCandidateCount"),
        "reviewCandidateCount": summary.get("reviewCandidateCount"),
        "compressedTopCandidates": summary.get("compressedTopCandidates", []),
        "evidenceStrongCount": summary.get("evidenceStrongCount"),
        "evidenceQualifiedCount": summary.get("evidenceQualifiedCount"),
        "evidenceThinCount": summary.get("evidenceThinCount"),
        "evidenceRiskCount": summary.get("evidenceRiskCount"),
        "evidenceWeakCount": summary.get("evidenceWeakCount"),
        "averageEvidenceScore": summary.get("averageEvidenceScore"),
        "buyDecisionCount": summary.get("buyDecisionCount"),
        "addDecisionCount": summary.get("addDecisionCount"),
        "holdDecisionCount": summary.get("holdDecisionCount"),
        "trimDecisionCount": summary.get("trimDecisionCount"),
        "stopDecisionCount": summary.get("stopDecisionCount"),
        "pullbackDecisionCount": summary.get("pullbackDecisionCount"),
        "watchDecisionCount": summary.get("watchDecisionCount"),
        "verifyDecisionCount": summary.get("verifyDecisionCount"),
        "portfolioLinkedCandidateCount": summary.get("portfolioLinkedCandidateCount"),
        "portfolioHoldingCount": summary.get("portfolioHoldingCount"),
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
        "dashboardStoredDiscoveryFirst": SIGNAL_DASHBOARD_STORED_DISCOVERY_FIRST,
        "candidatePrefetchEnabled": SIGNAL_CANDIDATE_PREFETCH_ENABLED,
        "candidatePrefetchLimit": SIGNAL_CANDIDATE_PREFETCH_LIMIT,
        "candidatePrefetchIntervalSeconds": SIGNAL_CANDIDATE_PREFETCH_INTERVAL_SECONDS,
        "latestFile": display_local_path(DISCOVERY_LATEST_FILE),
        "candidatePoolFile": display_local_path(CANDIDATE_POOL_FILE),
    }


def discovery_latest_record(include_dashboard: bool = False) -> dict:
    stored = db_read_kv("discovery_latest", None) if database_storage_enabled() else None
    record = stored if isinstance(stored, dict) else read_json(DISCOVERY_LATEST_FILE, {})
    if not isinstance(record, dict):
        return {}
    if include_dashboard:
        return record
    return {key: value for key, value in record.items() if key != "dashboard"}


def write_discovery_latest_record(record: dict) -> None:
    if not db_write_kv("discovery_latest", record):
        write_json(DISCOVERY_LATEST_FILE, record)


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
        payload = dashboard(selected_mode, force_discovery=True)
        prefetch_status = prefetch_candidate_pool_market_data(
            selected_mode,
            trigger=trigger,
            market=payload.get("market", {}),
        )
        payload.setdefault("integrations", {})["candidatePrefetch"] = prefetch_status
        summary = dashboard_summary(payload)
        summary["candidatePrefetch"] = prefetch_status
        run_id = f"{now.strftime('%Y%m%d-%H%M%S')}-{selected_mode}-discovery-{trigger}"
        record = {
            "id": run_id,
            "mode": selected_mode,
            "trigger": trigger,
            "createdAt": now.isoformat(timespec="seconds"),
            "summary": summary,
            "prefetch": prefetch_status,
            "dashboard": payload,
        }
        write_discovery_latest_record(record)
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
    if database_storage_enabled():
        records = db_recent_scheduler_runs(limit)
        if records or not DB_LAST_ERROR:
            return records
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
    db_status = database_status()
    raw_events = raw_event_storage_status()
    candidate_data = candidate_data_snapshot_status()
    market_data = market_data_latest_status()
    if db_status["enabled"] and db_status["ready"]:
        recent_runs = recent_scheduler_runs()
        data_storage_ready = bool(candidate_data.get("persistent") and market_data.get("persistent"))
        operation_ready = bool(data_storage_ready)
        if operation_ready:
            message = "Postgres DB에 스냅샷, 후보 풀, 최신 수집값을 저장하고 DB 기준으로 읽습니다."
            error = ""
        else:
            message = "DB는 연결됐지만 후보 데이터 또는 최신 가격 데이터가 아직 DB 기준으로 읽히지 않습니다. 다음 수집 또는 DB 이관 후 운영 기준으로 전환됩니다."
            error = "candidate-or-market-data-not-db-backed"
        return {
            "mode": SIGNAL_STORAGE_BACKEND,
            "implementation": "postgres",
            "runsDir": display_local_path(RUNS_DIR),
            "runsDirExists": RUNS_DIR.exists(),
            "writable": True,
            "persistent": operation_ready,
            "volatileFallback": not operation_ready,
            "operationReady": operation_ready,
            "recentRunCount": len(recent_runs),
            "latestRunId": recent_runs[0]["id"] if recent_runs else "",
            "latestRunCreatedAt": recent_runs[0]["createdAt"] if recent_runs else "",
            "database": db_status,
            "rawEvents": raw_events,
            "candidateData": candidate_data,
            "marketData": market_data,
            "message": message,
            "error": error,
        }

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
        "volatileFallback": True,
        "operationReady": False,
        "recentRunCount": len(recent_runs),
        "latestRunId": recent_runs[0]["id"] if recent_runs else "",
        "latestRunCreatedAt": recent_runs[0]["createdAt"] if recent_runs else "",
        "database": db_status,
        "rawEvents": raw_events,
        "candidateData": candidate_data,
        "marketData": market_data,
        "message": (
            "영구 저장소로 표시되어 있습니다."
            if persistent
            else "DB가 연결되지 않아 스냅샷, 후보 풀, Toss 최신값이 임시 파일 저장소에 남습니다. 실전 운영 전에는 Postgres DB 연결이 필요합니다."
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
    if database_storage_enabled():
        detail = db_snapshot_detail(run_id)
        if detail or not DB_LAST_ERROR:
            return detail
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


def latest_file_snapshot_detail(mode: str | None = None) -> dict | None:
    if not RUNS_DIR.exists():
        return None
    for path in sorted(RUNS_DIR.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            snapshot = read_json(path, {})
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(snapshot, dict):
            continue
        if mode and str(snapshot.get("mode", "")) != mode:
            continue
        dashboard_payload = snapshot.get("dashboard", {})
        if not isinstance(dashboard_payload, dict) or not dashboard_payload:
            continue
        return {
            "record": scheduler_record_from_snapshot(path, snapshot),
            "dashboard": dashboard_payload,
        }
    return None


def latest_scheduler_snapshot_detail(mode: str | None = None) -> dict | None:
    if database_storage_enabled():
        detail = db_latest_snapshot_detail(mode)
        if detail is not None:
            return detail
        if DB_LAST_ERROR:
            file_detail = latest_file_snapshot_detail(mode)
            if file_detail is not None:
                return file_detail
    return latest_file_snapshot_detail(mode)


def dashboard_cache_key(mode: str) -> str:
    selected = mode if mode in {"close", "preopen", "intraday"} else "close"
    return f"dashboard_cache:{selected}"


def dashboard_cache_file_data() -> dict:
    data = safe_read_json_file(DASHBOARD_CACHE_FILE) or {"items": {}}
    if not isinstance(data, dict):
        return {"items": {}}
    if not isinstance(data.get("items"), dict):
        data["items"] = {}
    return data


def dashboard_cache_record(mode: str) -> dict | None:
    key = dashboard_cache_key(mode)
    stored = db_read_kv(key, None) if database_storage_enabled() else None
    if isinstance(stored, dict) and isinstance(stored.get("dashboard"), dict):
        return stored
    data = dashboard_cache_file_data()
    record = data.get("items", {}).get(mode)
    if isinstance(record, dict) and isinstance(record.get("dashboard"), dict):
        return record
    return None


def write_dashboard_cache_record(mode: str, dashboard_payload: dict, source: str = "dashboard") -> bool:
    if not isinstance(dashboard_payload, dict) or not dashboard_payload:
        return False
    candidates = dashboard_payload.get("candidates", [])
    if not isinstance(candidates, list) or not candidates:
        return False
    selected_mode = mode if mode in {"close", "preopen", "intraday"} else str(dashboard_payload.get("mode", "close"))
    payload = copy.deepcopy(dashboard_payload)
    payload.pop("cache", None)
    created_at = str(payload.get("generatedAt") or datetime.now(KST).isoformat(timespec="seconds"))
    record = {
        "id": f"{created_at}-{selected_mode}-dashboard-cache",
        "mode": selected_mode,
        "source": source,
        "createdAt": created_at,
        "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
        "summary": payload.get("summary", {}),
        "dashboard": payload,
    }
    if db_write_kv(dashboard_cache_key(selected_mode), record):
        return True
    data = dashboard_cache_file_data()
    items = data.get("items", {})
    items[selected_mode] = record
    data["items"] = items
    data["updatedAt"] = record["updatedAt"]
    write_json(DASHBOARD_CACHE_FILE, data)
    return True


def cached_detail_timestamp(detail: dict) -> datetime:
    record = detail.get("record", {}) if isinstance(detail.get("record"), dict) else {}
    dashboard_payload = detail.get("dashboard", {}) if isinstance(detail.get("dashboard"), dict) else {}
    text = str(record.get("createdAt") or dashboard_payload.get("generatedAt") or "")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.astimezone(timezone.utc)


def newest_cached_detail(details: list[dict]) -> dict | None:
    usable = [
        detail
        for detail in details
        if isinstance(detail, dict) and isinstance(detail.get("dashboard"), dict) and detail.get("dashboard")
    ]
    if not usable:
        return None
    return max(usable, key=cached_detail_timestamp)


def dashboard_cache_detail(mode: str) -> dict | None:
    record = dashboard_cache_record(mode)
    if not isinstance(record, dict):
        return None
    dashboard_payload = record.get("dashboard", {})
    if not isinstance(dashboard_payload, dict) or not dashboard_payload:
        return None
    return {
        "source": "dashboard_cache",
        "record": {key: value for key, value in record.items() if key != "dashboard"},
        "dashboard": dashboard_payload,
    }


def cached_dashboard_detail(mode: str) -> dict | None:
    exact_details: list[dict] = []
    cache_detail = dashboard_cache_detail(mode)
    if cache_detail is not None:
        exact_details.append(cache_detail)

    latest_discovery = discovery_latest_record(include_dashboard=True)
    if isinstance(latest_discovery, dict):
        discovery_dashboard = latest_discovery.get("dashboard", {})
        if (
            isinstance(discovery_dashboard, dict)
            and discovery_dashboard
            and str(latest_discovery.get("mode", "")) == mode
        ):
            exact_details.append({
                "source": "discovery_latest",
                "record": {key: value for key, value in latest_discovery.items() if key != "dashboard"},
                "dashboard": discovery_dashboard,
            })

    scheduler_detail = latest_scheduler_snapshot_detail(mode)
    if isinstance(scheduler_detail, dict) and isinstance(scheduler_detail.get("dashboard"), dict):
        exact_details.append({"source": "snapshot", **scheduler_detail})

    exact_match = newest_cached_detail(exact_details)
    if exact_match is not None:
        return exact_match

    fallback_details: list[dict] = []
    if isinstance(latest_discovery, dict):
        discovery_dashboard = latest_discovery.get("dashboard", {})
        if isinstance(discovery_dashboard, dict) and discovery_dashboard:
            fallback_details.append({
                "source": "discovery_latest",
                "record": {key: value for key, value in latest_discovery.items() if key != "dashboard"},
                "dashboard": discovery_dashboard,
            })

    fallback_detail = latest_scheduler_snapshot_detail(None)
    if isinstance(fallback_detail, dict) and isinstance(fallback_detail.get("dashboard"), dict):
        fallback_details.append({"source": "snapshot", **fallback_detail})
    return newest_cached_detail(fallback_details)



def cached_dashboard_payload(mode: str, fallback_error: str = "") -> dict | None:
    detail = cached_dashboard_detail(mode)
    if not detail:
        return None
    dashboard_payload = detail.get("dashboard")
    if not isinstance(dashboard_payload, dict) or not dashboard_payload:
        return None
    record = detail.get("record", {}) if isinstance(detail.get("record"), dict) else {}
    payload = copy.deepcopy(dashboard_payload)
    candidates = payload.get("candidates", [])
    if isinstance(candidates, list):
        merged_candidates, candidate_data_merge = merge_candidate_data_snapshots_into_candidates(
            [item for item in candidates if isinstance(item, dict)],
            mode,
        )
        merged_candidates, live_state_merge = merge_live_state_into_candidates(merged_candidates, mode)
        merged_candidates, market_data_merge = merge_market_data_latest_into_candidates(merged_candidates)
        merge_by_symbol = {
            str(item.get("symbol", "")).strip().upper(): item
            for item in merged_candidates
            if isinstance(item, dict) and str(item.get("symbol", "")).strip()
        }
        payload["candidates"] = [
            annotate_candidate_live_price_freshness(
                merge_by_symbol.get(str(candidate.get("symbol", "")).strip().upper(), candidate),
                payload.get("generatedAt", ""),
            )
            if isinstance(candidate, dict)
            else candidate
            for candidate in candidates
        ]
        if isinstance(payload.get("selected"), dict):
            selected_symbol = str(payload["selected"].get("symbol", "")).strip().upper()
            payload["selected"] = annotate_candidate_live_price_freshness(
                merge_by_symbol.get(selected_symbol, payload["selected"]),
                payload.get("generatedAt", ""),
            )
        freshness_counts = live_price_freshness_counts([item for item in payload["candidates"] if isinstance(item, dict)])
    else:
        freshness_counts = {}
        candidate_data_merge = {"mergedCount": 0}
        live_state_merge = {"mergedCount": 0}
        market_data_merge = {"mergedCount": 0}
    payload["cache"] = {
        "cached": True,
        "source": detail.get("source", "snapshot"),
        "requestedMode": mode,
        "mode": record.get("mode") or payload.get("mode", ""),
        "id": record.get("id", ""),
        "createdAt": record.get("createdAt", payload.get("generatedAt", "")),
        "fallbackError": fallback_error,
    }
    if isinstance(payload.get("summary"), dict):
        payload["summary"]["dashboardCacheSource"] = payload["cache"]["source"]
        payload["summary"]["dashboardCacheCreatedAt"] = payload["cache"]["createdAt"]
        payload["summary"]["dashboardCacheFallbackError"] = fallback_error
        payload["summary"]["livePriceFreshnessCounts"] = freshness_counts
        payload["summary"]["candidateDataMergedCount"] = candidate_data_merge.get("mergedCount", 0)
        payload["summary"]["liveStateMergedCount"] = live_state_merge.get("mergedCount", 0)
        payload["summary"]["marketDataMergedCount"] = market_data_merge.get("mergedCount", 0)
        payload["summary"]["marketDataPriceMergedCount"] = market_data_merge.get("priceMergedCount", 0)
    integrations = payload.get("integrations", {}) if isinstance(payload.get("integrations"), dict) else {}
    integrations["candidateDataMerge"] = candidate_data_merge
    integrations["liveStateMerge"] = live_state_merge
    integrations["marketDataMerge"] = market_data_merge
    integrations["marketDataLatest"] = market_data_latest_status()
    payload["integrations"] = integrations
    return payload


def stored_candidate_pool_dashboard_payload(mode: str, fallback_error: str = "") -> dict | None:
    data = seed_data()
    watched = set(watchlist())
    pool_result = candidate_pool_initial_candidates(data.get("candidates", []), watched, mode)
    if pool_result is None:
        return None

    raw_candidates, discovery_status = pool_result
    if not raw_candidates:
        return None

    market = copy.deepcopy(data.get("market", {}))
    candidates = [decorate_candidate(copy.deepcopy(item), watched) for item in raw_candidates]
    candidates, candidate_data_merge = merge_candidate_data_snapshots_into_candidates(candidates, mode)
    candidates, live_state_merge = merge_live_state_into_candidates(candidates, mode)
    candidates, market_data_merge = merge_market_data_latest_into_candidates(candidates)
    candidates, selection_status = apply_candidate_selection(candidates, market, watched, stabilize_decisions=True)
    candidates = [apply_analysis_to_candidate(candidate, local_candidate_analysis(candidate)) for candidate in candidates]
    candidates = sort_candidates_for_mode(candidates, mode)
    now_text = datetime.now(KST).isoformat(timespec="seconds")

    defaults = dashboard_status_defaults()
    pool_status = candidate_pool_summary()
    discovery_status = {
        **discovery_status,
        "source": "candidate-pool",
        "stored": True,
        "dashboardOnly": True,
        "message": "저장 후보 풀을 우선 표시합니다. 새 후보 발굴은 스케줄러나 수동 갱신에서만 수행합니다.",
        "updatedAt": now_text,
    }
    selection_status = {
        **selection_status,
        "source": "stored-rules",
        "message": "저장 후보 풀을 외부 API 호출 없이 로컬 판단 규칙으로 재점검했습니다.",
        "updatedAt": now_text,
    }
    context = {
        "mode": mode,
        "data": data,
        "market": market,
        "watched": watched,
        "portfolio": {},
        "candidates": candidates,
        "selected": candidates[0] if candidates else None,
        "statuses": {
            **defaults,
            "index": {
                "source": "stored",
                "enabled": False,
                "message": "저장 후보 조회에서는 지수 실시간 조회를 생략했습니다.",
                "updatedAt": now_text,
            },
            "fx": {
                "source": "stored",
                "enabled": False,
                "message": "저장 후보 조회에서는 환율 실시간 조회를 생략했습니다.",
                "updatedAt": now_text,
            },
            "discovery": discovery_status,
            "selection": selection_status,
            "candidate_pool": pool_status,
            "candidate_data_merge": candidate_data_merge,
            "live_state_merge": live_state_merge,
            "market_data_latest": market_data_latest_status(),
            "market_data_merge": market_data_merge,
        },
        "pipeline": [
            pipeline_step(
                "cache",
                "저장 후보 풀 조회",
                "ok",
                discovery_status["message"],
                len(candidates),
            ),
            pipeline_step(
                "storage",
                "저장 후보 데이터 반영",
                "ok" if candidate_data_merge.get("mergedCount", 0) else "fallback",
                candidate_data_merge.get("message", "저장된 후보별 토스 데이터를 확인했습니다."),
                candidate_data_merge.get("mergedCount", 0),
            ),
            pipeline_step(
                "storage",
                "직전 실시간 상태 반영",
                "ok" if live_state_merge.get("mergedCount", 0) else "fallback",
                live_state_merge.get("message", "직전 토스 확정 상태를 확인했습니다."),
                live_state_merge.get("mergedCount", 0),
            ),
            pipeline_step(
                "storage",
                "DB 최신 가격 반영",
                "ok" if market_data_merge.get("mergedCount", 0) else "fallback",
                market_data_merge.get("message", "DB 최신 토스 가격을 확인했습니다."),
                market_data_merge.get("mergedCount", 0),
            ),
            pipeline_step(
                "scorer",
                "저장 후보 재점검",
                "ok",
                selection_status["message"],
                len(candidates),
            ),
            pipeline_step(
                "selector",
                "저장 후보 정렬",
                "fallback",
                "실시간 수집 없이 저장된 후보를 정렬했습니다.",
                len(candidates),
            ),
        ],
    }
    payload = build_dashboard_payload(context)
    payload["cache"] = {
        "cached": True,
        "source": "candidate_pool",
        "requestedMode": mode,
        "mode": mode,
        "id": f"{now_text}-{mode}-candidate-pool",
        "createdAt": pool_status.get("updatedAt") or now_text,
        "fallbackError": fallback_error,
    }
    if isinstance(payload.get("summary"), dict):
        payload["summary"]["dashboardCacheSource"] = "candidate_pool"
        payload["summary"]["dashboardCacheCreatedAt"] = payload["cache"]["createdAt"]
        payload["summary"]["dashboardCacheFallbackError"] = fallback_error
        payload["summary"]["candidateSourceStored"] = True
    return payload


def seed_dashboard_payload_for_live_prices(mode: str) -> dict:
    data = seed_data()
    watched = set(watchlist())
    market = copy.deepcopy(data.get("market", {}))
    candidates = [decorate_candidate(copy.deepcopy(item), watched) for item in data.get("candidates", [])]
    candidates, candidate_data_merge = merge_candidate_data_snapshots_into_candidates(candidates, mode)
    candidates, live_state_merge = merge_live_state_into_candidates(candidates, mode)
    candidates, market_data_merge = merge_market_data_latest_into_candidates(candidates)
    candidates, selection_status = apply_candidate_selection(candidates, market, watched, stabilize_decisions=True)
    candidates = sort_candidates_for_mode(candidates, mode)
    return {
        "generatedAt": datetime.now(KST).isoformat(timespec="seconds"),
        "mode": mode,
        "market": market,
        "principles": data.get("principles", []),
        "summary": {
            "candidateCount": len(candidates),
            "watchedCount": len([item for item in candidates if item.get("isWatched")]),
            "highScoreCount": len([item for item in candidates if item.get("totalScore", 0) >= 75]),
            "readyCount": len([item for item in candidates if item.get("triggerReadiness", 0) >= 70]),
            "selectionSource": selection_status.get("source"),
            "candidateSource": "sample",
            "averagePriceReaction": selection_status.get("averagePriceReaction"),
            "priceReactionCounts": selection_status.get("priceReactionCounts", {}),
            "priceReactionGateCounts": selection_status.get("priceReactionGateCounts", {}),
            "evaluationModeCounts": selection_status.get("evaluationModeCounts", {}),
            "tradeEvaluationReadyCount": selection_status.get("tradeEvaluationReadyCount"),
            "baselineEvaluationCount": selection_status.get("baselineEvaluationCount"),
            "serverCollectingCount": selection_status.get("serverCollectingCount"),
            "unavailableEvaluationCount": selection_status.get("unavailableEvaluationCount"),
            "priceReactionEntryBlockedCount": selection_status.get("priceReactionEntryBlockedCount"),
            "qualityGateCounts": selection_status.get("qualityGateCounts", {}),
            "finalDecisionCounts": selection_status.get("finalDecisionCounts", {}),
            "candidateCompressionCounts": selection_status.get("candidateCompressionCounts", {}),
            "signalValidationCounts": selection_status.get("signalValidationCounts", {}),
        },
        "integrations": {
            "selection": selection_status,
            "candidateDataMerge": candidate_data_merge,
            "liveStateMerge": live_state_merge,
            "marketDataMerge": market_data_merge,
            "toss": {
                "config": toss_config_status(),
                "prices": {"source": "sample", "message": "시드 후보 기준입니다."},
                "candles": {"source": "sample"},
                "orderbook": {"source": "sample"},
                "trades": {"source": "sample"},
            },
        },
        "cache": {"cached": False, "source": "seed", "mode": mode},
        "candidates": candidates,
        "selected": candidates[0] if candidates else None,
    }


def dashboard_base_for_live_prices(mode: str) -> tuple[dict, str]:
    cached_payload = cached_dashboard_payload(mode)
    if cached_payload is not None:
        cache = cached_payload.get("cache", {}) if isinstance(cached_payload.get("cache"), dict) else {}
        return cached_payload, str(cache.get("source") or "dashboard_cache")

    stored_payload = stored_candidate_pool_dashboard_payload(mode)
    if stored_payload is not None:
        return stored_payload, "candidate_pool"

    return seed_dashboard_payload_for_live_prices(mode), "seed"


def live_price_summary_from_selection(candidates: list[dict], selection_status: dict, base_summary: dict) -> dict:
    summary = copy.deepcopy(base_summary) if isinstance(base_summary, dict) else {}
    compression_counts = selection_status.get("candidateCompressionCounts", {})
    validation_counts = selection_status.get("signalValidationCounts", {})
    now_text = datetime.now(KST).isoformat(timespec="seconds")
    summary.update({
        "candidateCount": len(candidates),
        "watchedCount": len([item for item in candidates if item.get("isWatched")]),
        "highScoreCount": len([item for item in candidates if item.get("totalScore", 0) >= 75]),
        "readyCount": len([item for item in candidates if item.get("triggerReadiness", 0) >= 70]),
        "selectionSource": selection_status.get("source", "live-price-rules"),
        "livePriceUpdatedAt": now_text,
        "livePricePollSeconds": SIGNAL_LIVE_PRICE_POLL_SECONDS,
        "averageScoreShift": selection_status.get("averageScoreShift"),
        "averageOpportunityScore": selection_status.get("averageOpportunityScore"),
        "averageDataConfidence": selection_status.get("averageDataConfidence"),
        "averageSourceReliability": selection_status.get("averageSourceReliability"),
        "sourceReliabilityCounts": selection_status.get("sourceReliabilityCounts", {}),
        "averagePriceReaction": selection_status.get("averagePriceReaction"),
        "averageOfficialEventScore": selection_status.get("averageOfficialEventScore"),
        "officialEventCounts": selection_status.get("officialEventCounts", {}),
        "officialEventCandidateCount": selection_status.get("officialEventCandidateCount"),
        "officialRiskCandidateCount": selection_status.get("officialRiskCandidateCount"),
        "hiddenOpportunityCount": selection_status.get("hiddenOpportunityCount"),
        "decisionGroups": selection_status.get("decisionGroups", {}),
        "qualityGateCounts": selection_status.get("qualityGateCounts", {}),
        "priceReactionCounts": selection_status.get("priceReactionCounts", {}),
        "priceReactionGateCounts": selection_status.get("priceReactionGateCounts", {}),
        "priceReadinessCounts": selection_status.get("priceReadinessCounts", {}),
        "evaluationModeCounts": selection_status.get("evaluationModeCounts", {}),
        "tradeEvaluationReadyCount": selection_status.get("tradeEvaluationReadyCount"),
        "baselineEvaluationCount": selection_status.get("baselineEvaluationCount"),
        "serverCollectingCount": selection_status.get("serverCollectingCount"),
        "unavailableEvaluationCount": selection_status.get("unavailableEvaluationCount"),
        "entryDataReadyCount": selection_status.get("entryDataReadyCount"),
        "closedBaselineCandidateCount": selection_status.get("closedBaselineCandidateCount"),
        "displayDataReadyCount": selection_status.get("displayDataReadyCount"),
        "priceBasisWaitCount": selection_status.get("priceBasisWaitCount"),
        "changeWaitCount": selection_status.get("changeWaitCount"),
        "priceReactionEntryBlockedCount": selection_status.get("priceReactionEntryBlockedCount"),
        "finalDecisionCounts": selection_status.get("finalDecisionCounts", {}),
        "candidateCompressionCounts": compression_counts,
        "signalValidationCounts": validation_counts,
        "coreCandidateCount": selection_status.get("coreCandidateCount"),
        "reviewCandidateCount": selection_status.get("reviewCandidateCount"),
        "waitCandidateCompressionCount": compression_counts.get("wait"),
        "portfolioCandidateCompressionCount": compression_counts.get("portfolio"),
        "excludeCandidateCompressionCount": compression_counts.get("exclude"),
        "confirmedSignalCount": validation_counts.get("confirmed"),
        "evidenceWaitSignalCount": validation_counts.get("evidence_wait"),
        "reactionOnlySignalCount": validation_counts.get("reaction_only"),
        "blockedSignalCount": validation_counts.get("blocked"),
        "buyDecisionCount": selection_status.get("buyDecisionCount"),
        "addDecisionCount": selection_status.get("addDecisionCount"),
        "holdDecisionCount": selection_status.get("holdDecisionCount"),
        "trimDecisionCount": selection_status.get("trimDecisionCount"),
        "stopDecisionCount": selection_status.get("stopDecisionCount"),
        "pullbackDecisionCount": selection_status.get("pullbackDecisionCount"),
        "watchDecisionCount": selection_status.get("watchDecisionCount"),
        "verifyDecisionCount": selection_status.get("verifyDecisionCount"),
        "investableCandidateCount": selection_status.get("investableCandidateCount"),
        "watchCandidateCount": selection_status.get("watchCandidateCount"),
        "deferCandidateCount": selection_status.get("deferCandidateCount"),
        "actionCandidateCount": selection_status.get("actionCandidateCount"),
        "momentumCandidateCount": selection_status.get("momentumCandidateCount"),
        "waitCandidateCount": selection_status.get("waitCandidateCount"),
        "excludeCandidateCount": selection_status.get("excludeCandidateCount"),
    })
    return summary


def price_only_candidate_update(candidate: dict) -> dict:
    item = annotate_candidate_live_price_freshness(dict(candidate))
    item["dataCompleteness"] = candidate_data_completeness(item)
    item["priceReadiness"] = candidate_price_readiness(item)
    item["evaluationMode"] = candidate_evaluation_mode(item)
    return item


def price_only_selection_status(candidates: list[dict], base_summary: dict, base_integrations: dict) -> dict:
    base_selection = (
        copy.deepcopy(base_integrations.get("selection", {}))
        if isinstance(base_integrations.get("selection"), dict)
        else {}
    )
    price_readiness_counts: dict[str, int] = {}
    evaluation_mode_counts: dict[str, int] = {}
    final_decision_counts = {
        "buy": 0,
        "add": 0,
        "hold": 0,
        "trim": 0,
        "stop": 0,
        "pullback": 0,
        "watch": 0,
        "verify": 0,
        "exclude": 0,
    }
    compression_counts: dict[str, int] = {}
    validation_counts: dict[str, int] = {}
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        readiness = candidate.get("priceReadiness", {}) if isinstance(candidate.get("priceReadiness"), dict) else {}
        evaluation = candidate.get("evaluationMode", {}) if isinstance(candidate.get("evaluationMode"), dict) else {}
        final_decision = candidate.get("finalDecision", {}) if isinstance(candidate.get("finalDecision"), dict) else {}
        compression = candidate.get("candidateCompression", {}) if isinstance(candidate.get("candidateCompression"), dict) else {}
        validation = candidate.get("signalValidation", {}) if isinstance(candidate.get("signalValidation"), dict) else {}
        readiness_key = str(readiness.get("key", "collecting"))
        evaluation_key = str(evaluation.get("key", "collecting"))
        action_key = str(final_decision.get("actionKey", "verify"))
        compression_key = str(compression.get("tier", "wait"))
        validation_key = str(validation.get("key", "evidence_wait"))
        price_readiness_counts[readiness_key] = price_readiness_counts.get(readiness_key, 0) + 1
        evaluation_mode_counts[evaluation_key] = evaluation_mode_counts.get(evaluation_key, 0) + 1
        final_decision_counts[action_key if action_key in final_decision_counts else "verify"] += 1
        compression_counts[compression_key] = compression_counts.get(compression_key, 0) + 1
        validation_counts[validation_key] = validation_counts.get(validation_key, 0) + 1

    summary = base_summary if isinstance(base_summary, dict) else {}
    status = {
        **base_selection,
        "source": "price-only-retained",
        "enabled": True,
        "message": "10초 가격 갱신은 후보 재선정 없이 기존 판단을 유지하고 가격·등락률만 보강합니다.",
        "candidateCount": len(candidates),
        "priceReadinessCounts": price_readiness_counts,
        "evaluationModeCounts": evaluation_mode_counts,
        "tradeEvaluationReadyCount": evaluation_mode_counts.get("entry_ready", 0),
        "baselineEvaluationCount": evaluation_mode_counts.get("closed_baseline", 0),
        "serverCollectingCount": (
            evaluation_mode_counts.get("collecting_change", 0)
            + evaluation_mode_counts.get("collecting_price", 0)
            + evaluation_mode_counts.get("collecting", 0)
        ),
        "unavailableEvaluationCount": evaluation_mode_counts.get("unavailable", 0),
        "entryDataReadyCount": price_readiness_counts.get("entry_ready", 0),
        "closedBaselineCandidateCount": price_readiness_counts.get("closed_baseline", 0),
        "displayDataReadyCount": (
            price_readiness_counts.get("entry_ready", 0)
            + price_readiness_counts.get("closed_baseline", 0)
            + price_readiness_counts.get("display_ready", 0)
        ),
        "priceBasisWaitCount": price_readiness_counts.get("price_wait", 0),
        "changeWaitCount": price_readiness_counts.get("change_wait", 0),
        "decisionGroups": decision_group_counts(candidates),
        "finalDecisionCounts": final_decision_counts,
        "candidateCompressionCounts": compression_counts or summary.get("candidateCompressionCounts", {}),
        "signalValidationCounts": validation_counts or summary.get("signalValidationCounts", {}),
        "stableDecisionCount": len([
            candidate
            for candidate in candidates
            if isinstance(candidate.get("finalDecision"), dict)
            and bool(candidate.get("finalDecision", {}).get("stability", {}).get("held"))
        ]),
        "finalDecisionStabilitySeconds": SIGNAL_FINAL_DECISION_STABILITY_SECONDS if SIGNAL_FINAL_DECISION_STABILITY_ENABLED else 0,
    }
    return status


def dashboard_live_price_payload(symbols: list[str], mode: str, detail: str = "price") -> dict:
    base_payload, base_source = dashboard_base_for_live_prices(mode)
    base_candidates = [
        copy.deepcopy(item)
        for item in base_payload.get("candidates", [])
        if isinstance(item, dict) and str(item.get("symbol", "")).strip()
    ]
    base_candidates, candidate_data_merge_status = merge_candidate_data_snapshots_into_candidates(base_candidates, mode)
    base_candidates, market_data_merge_status = merge_market_data_latest_into_candidates(base_candidates)
    base_candidates, live_state_status = merge_live_state_into_candidates(base_candidates, mode)
    requested = unique_symbols(symbols)
    has_requested_symbols = bool(requested)
    if not has_requested_symbols:
        requested = unique_symbols([str(item.get("symbol", "")) for item in base_candidates])
    requested = requested[:SIGNAL_LIVE_PRICE_SYMBOL_LIMIT]
    requested_priority = {symbol: index for index, symbol in enumerate(requested)}
    indexed_candidates = list(enumerate(base_candidates))
    indexed_candidates.sort(
        key=lambda pair: (
            requested_priority.get(str(pair[1].get("symbol", "")), len(requested_priority) + pair[0]),
            pair[0],
        )
    )
    if has_requested_symbols:
        refresh_candidates = [
            item for _, item in indexed_candidates
            if str(item.get("symbol", "")) in requested_priority
        ][:SIGNAL_LIVE_PRICE_SYMBOL_LIMIT]
    else:
        refresh_candidates = [item for _, item in indexed_candidates][:SIGNAL_LIVE_PRICE_SYMBOL_LIMIT]
    if not refresh_candidates:
        return {
            "mode": mode,
            "source": "live-price",
            "baseSource": base_source,
            "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
            "pollSeconds": SIGNAL_LIVE_PRICE_POLL_SECONDS,
            "candidates": [],
            "summary": {
                "candidateCount": 0,
                "livePriceUpdatedAt": datetime.now(KST).isoformat(timespec="seconds"),
                "marketDataMergedCount": market_data_merge_status.get("mergedCount", 0),
            },
            "message": "갱신할 후보가 없습니다.",
        }

    price_status = {"source": "sample", "message": "현재가 갱신 전입니다."}
    include_depth = detail in {"full", "depth", "market-depth"}
    candle_status = {"source": "retained", "message": "가격 전용 갱신에서는 기존 일봉 정보를 유지합니다."}
    orderbook_status = {"source": "retained", "message": "가격 전용 갱신에서는 기존 호가 정보를 유지합니다."}
    trade_status = {"source": "retained", "message": "가격 전용 갱신에서는 기존 체결 정보를 유지합니다."}
    try:
        refresh_candidates, price_status = enrich_candidates_with_toss_prices(refresh_candidates)
        if include_depth:
            refresh_candidates, candle_status = enrich_candidates_with_toss_candles(refresh_candidates)
            refresh_candidates, orderbook_status = enrich_candidates_with_toss_orderbook(refresh_candidates)
            refresh_candidates, trade_status = enrich_candidates_with_toss_trades(refresh_candidates)
    except Exception as error:
        error_payload, _ = integration_error_payload(error)
        price_status = {
            "source": "error",
            "enabled": TOSS_LIVE_PRICES,
            "message": error_payload.get("message", "토스 라이브 가격 갱신에 실패했습니다."),
            "error": error_payload.get("error", str(error)[:160]),
        }

    refreshed_by_symbol = {
        str(item.get("symbol", "")).strip().upper(): item
        for item in refresh_candidates
        if isinstance(item, dict) and str(item.get("symbol", "")).strip()
    }
    candidates: list[dict] = []
    seen_symbols: set[str] = set()
    for candidate in base_candidates:
        symbol = str(candidate.get("symbol", "")).strip().upper()
        if not symbol:
            candidates.append(candidate)
            continue
        candidates.append(refreshed_by_symbol.get(symbol, candidate))
        seen_symbols.add(symbol)
    for symbol, candidate in refreshed_by_symbol.items():
        if symbol not in seen_symbols:
            candidates.append(candidate)

    watched = set(watchlist())
    for item in candidates:
        item["isWatched"] = str(item.get("symbol", "")) in watched
    market = copy.deepcopy(base_payload.get("market", seed_data().get("market", {})))
    base_integrations = copy.deepcopy(base_payload.get("integrations", {})) if isinstance(base_payload.get("integrations"), dict) else {}
    if include_depth:
        candidates, selection_status = apply_candidate_selection(candidates, market, watched, stabilize_decisions=True)
        candidates = sort_candidates_for_mode(candidates, mode)
        selection_cycle = "full-analysis"
    else:
        candidates = [price_only_candidate_update(candidate) for candidate in candidates]
        selection_status = price_only_selection_status(candidates, base_payload.get("summary", {}), base_integrations)
        selection_cycle = "price-only"
    live_state_write_status = update_live_state_from_candidates(candidates, mode)
    candidate_data_status = update_candidate_data_snapshots(candidates, mode, stage="live-price")
    candidate_latest_status = update_market_data_latest_from_candidates(candidates, mode=mode, stage="live-price")
    market_data_status = market_data_latest_status()
    freshness_counts = live_price_freshness_counts(candidates)
    summary = live_price_summary_from_selection(candidates, selection_status, base_payload.get("summary", {}))
    summary.update({
        "livePriceFreshnessCounts": freshness_counts,
        "livePriceRequestedCount": len(requested),
        "livePriceTossRequestedCount": price_status.get("requestedCount", len(refresh_candidates)),
        "livePriceTossReceivedCount": price_status.get("receivedCount", price_status.get("priceCount", 0)),
        "livePriceBatchCount": price_status.get("batchCount", 0),
        "livePriceBatchErrorCount": price_status.get("batchErrorCount", 0),
        "livePriceRefreshedCount": len(refresh_candidates),
        "livePriceCandidateCount": len(candidates),
        "livePriceStoredFallbackCount": price_status.get("storedFallbackCount", 0),
        "livePriceRetainedCount": price_status.get("retainedCount", 0),
        "livePriceMissingCount": price_status.get("missingCount", 0),
        "livePriceMissingSymbols": price_status.get("missingSymbols", []),
        "liveStateMergedCount": live_state_status.get("mergedCount", 0),
        "candidateDataMergedCount": candidate_data_merge_status.get("mergedCount", 0),
        "marketDataMergedCount": market_data_merge_status.get("mergedCount", 0),
        "marketDataPriceMergedCount": market_data_merge_status.get("priceMergedCount", 0),
        "marketDataChangeMergedCount": market_data_merge_status.get("changeMergedCount", 0),
        "marketDataLatestCount": market_data_status.get("itemCount", 0),
        "marketDataLatestAt": market_data_status.get("latestAt", ""),
        "candidateMarketDataLatestUpdatedCount": candidate_latest_status.get("updatedCount", 0),
        "candidateMarketDataLatestStored": bool(candidate_latest_status.get("stored", False)),
        "liveStateStoredCount": live_state_write_status.get("storedCount", 0),
        "candidateDataStoredCount": candidate_data_status.get("storedCount", 0),
        "candidateDataDisplayReadyCount": candidate_data_status.get("displayReadyCount", 0),
        "candidateDataEntryReadyCount": candidate_data_status.get("entryReadyCount", 0),
        "candidateDataCarriedForwardCount": candidate_data_status.get("carriedForwardCount", 0),
        "candidateDataCarriedForwardFields": candidate_data_status.get("carriedForwardFields", {}),
        "stableDecisionCount": selection_status.get("stableDecisionCount", 0),
        "finalDecisionStabilitySeconds": selection_status.get("finalDecisionStabilitySeconds", 0),
    })
    integrations = base_integrations
    integrations["selection"] = selection_status
    integrations["livePrice"] = {
        "source": "toss-dashboard-poll",
        "baseSource": base_source,
        "pollSeconds": SIGNAL_LIVE_PRICE_POLL_SECONDS,
        "symbolLimit": SIGNAL_LIVE_PRICE_SYMBOL_LIMIT,
        "requestedCount": len(requested),
        "refreshedCount": len(refresh_candidates),
        "candidateCount": len(candidates),
        "freshnessCounts": freshness_counts,
        "candidateDataRead": candidate_data_merge_status,
        "marketDataRead": market_data_merge_status,
        "stateRead": live_state_status,
        "stateWrite": live_state_write_status,
        "candidateData": candidate_data_status,
        "candidateMarketDataLatest": candidate_latest_status,
        "marketDataLatest": market_data_status,
        "selectionCycle": selection_cycle,
        "updatedAt": summary["livePriceUpdatedAt"],
    }
    toss_status = copy.deepcopy(integrations.get("toss", {})) if isinstance(integrations.get("toss"), dict) else {}
    toss_status.update({
        "config": toss_config_status(),
        "prices": price_status,
        "candles": candle_status,
        "orderbook": orderbook_status,
        "trades": trade_status,
    })
    integrations["toss"] = toss_status
    integrations["marketDataMerge"] = market_data_merge_status
    integrations["candidateMarketDataLatest"] = candidate_latest_status
    integrations["marketDataLatest"] = market_data_status
    return {
        "mode": mode,
        "source": "live-price",
        "baseSource": base_source,
        "selectionCycle": selection_cycle,
        "detail": "full" if include_depth else "price",
        "updatedAt": summary["livePriceUpdatedAt"],
        "pollSeconds": SIGNAL_LIVE_PRICE_POLL_SECONDS,
        "symbols": requested,
        "requestedCount": len(requested),
        "refreshedCount": len(refresh_candidates),
        "candidateCount": len(candidates),
        "summary": summary,
        "integrations": integrations,
        "candidates": candidates,
        "selected": candidates[0] if candidates else None,
        "message": "현재 후보 전체의 토스 라이브 가격을 갱신했습니다.",
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


def performance_horizon(created_at: str) -> dict:
    created = parse_iso_datetime(created_at)
    if created is None:
        return {"key": "unknown", "label": "시점 미확인", "elapsedMinutes": None}
    minutes = max(0, int((datetime.now(KST) - created).total_seconds() // 60))
    if minutes < 90:
        key, label = "1h", "1시간"
    elif minutes < 24 * 60:
        key, label = "close", "당일"
    elif minutes < 3 * 24 * 60:
        key, label = "1d", "1일"
    elif minutes < 5 * 24 * 60:
        key, label = "3d", "3일"
    else:
        key, label = "5d", "5일+"
    return {"key": key, "label": label, "elapsedMinutes": minutes}


def performance_hit_rate(items: list[dict]) -> str:
    if not items:
        return "-"
    positives = len([item for item in items if item.get("outcome") == "상승"])
    return display_percent_abs(Decimal(positives) / Decimal(len(items)) * Decimal(100))


def performance_average_change(items: list[dict]) -> str:
    changes = [Decimal(str(item["changeRate"])) for item in items if item.get("measured")]
    return display_decimal_percent(decimal_average(changes)) if changes else "-"


def performance_summary(observations: list[dict], run_count: int, price_status: dict) -> dict:
    measured = [item for item in observations if item.get("measured")]
    changes = [Decimal(str(item["changeRate"])) for item in measured]
    positive = [item for item in measured if item.get("outcome") == "상승"]
    negative = [item for item in measured if item.get("outcome") == "하락"]
    neutral = [item for item in measured if item.get("outcome") == "중립"]
    actionable = [item for item in measured if item.get("gateKey") == "actionable"]
    buy_decisions = [item for item in measured if item.get("finalActionKey") == "buy"]
    add_decisions = [item for item in measured if item.get("finalActionKey") == "add"]
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
        "actionableMeasuredCount": len(actionable),
        "actionableHitRate": performance_hit_rate(actionable),
        "actionableAverageChange": performance_average_change(actionable),
        "buyDecisionMeasuredCount": len(buy_decisions),
        "buyDecisionHitRate": performance_hit_rate(buy_decisions),
        "buyDecisionAverageChange": performance_average_change(buy_decisions),
        "addDecisionMeasuredCount": len(add_decisions),
        "addDecisionHitRate": performance_hit_rate(add_decisions),
        "addDecisionAverageChange": performance_average_change(add_decisions),
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


def performance_group_rows(observations: list[dict], key_field: str, label_field: str, order: list[str]) -> list[dict]:
    grouped: dict[str, dict] = {}
    for item in observations:
        key = str(item.get(key_field) or "unknown")
        label = str(item.get(label_field) or key or "미분류")
        bucket = grouped.setdefault(key, {"label": label, "items": []})
        bucket["items"].append(item)

    rows = []
    for key, group in grouped.items():
        items = group["items"]
        measured = [item for item in items if item.get("measured")]
        positives = len([item for item in measured if item.get("outcome") == "상승"])
        latest = items[0] if items else {}
        rows.append({
            "key": key,
            "label": group["label"],
            "observationCount": len(items),
            "measuredCount": len(measured),
            "positiveCount": positives,
            "hitRate": performance_hit_rate(measured),
            "averageChange": performance_average_change(measured),
            "latestChange": latest.get("change", "-"),
            "latestOutcome": latest.get("outcome", "-"),
        })

    order_index = {key: index for index, key in enumerate(order)}
    rows.sort(key=lambda item: (order_index.get(item["key"], len(order)), -item["measuredCount"]))
    return rows


def performance_by_gate(observations: list[dict]) -> list[dict]:
    return performance_group_rows(
        observations,
        "gateKey",
        "gateLabel",
        ["actionable", "watch", "defer", "exclude", "unknown"],
    )


def performance_by_horizon(observations: list[dict]) -> list[dict]:
    return performance_group_rows(
        observations,
        "horizonKey",
        "horizonLabel",
        ["1h", "close", "1d", "3d", "5d", "unknown"],
    )


def performance_by_final_action(observations: list[dict]) -> list[dict]:
    return performance_group_rows(
        observations,
        "finalActionKey",
        "finalAction",
        ["buy", "add", "hold", "trim", "stop", "watch", "pullback", "verify", "exclude", "unknown"],
    )


def performance_by_reaction(observations: list[dict]) -> list[dict]:
    return performance_group_rows(
        observations,
        "reactionKey",
        "reactionLabel",
        ["strong", "confirmed", "weak", "missing", "unknown"],
    )


def update_candidate_pool_performance(observations: list[dict], observed_at: str) -> dict:
    if not SIGNAL_CANDIDATE_POOL_ENABLED:
        return {
            "enabled": False,
            "updatedCount": 0,
            "message": "후보 풀 저장이 꺼져 있어 성과를 반영하지 않았습니다.",
        }
    measured = [
        item
        for item in observations
        if isinstance(item, dict)
        and item.get("measured")
        and item.get("priceSanity", True)
        and str(item.get("symbol", "")).strip()
    ]
    if not measured:
        return {
            "enabled": True,
            "updatedCount": 0,
            "measuredCount": 0,
            "message": "후보 풀에 반영할 측정 성과가 아직 없습니다.",
        }

    grouped: dict[str, list[dict]] = {}
    for item in measured:
        grouped.setdefault(str(item.get("symbol", "")).strip().upper(), []).append(item)

    updated_count = 0
    updated_symbols: list[str] = []
    total_measured = 0
    total_positive = 0
    total_negative = 0
    total_change = Decimal("0")

    with CANDIDATE_POOL_LOCK:
        data = candidate_pool_data()
        items = data.get("items", {}) if isinstance(data.get("items"), dict) else {}
        for symbol, symbol_observations in grouped.items():
            record = items.get(symbol)
            if not isinstance(record, dict):
                continue
            history = record.get("performanceHistory", [])
            if not isinstance(history, list):
                history = []
            by_key = {
                str(entry.get("key")): dict(entry)
                for entry in history
                if isinstance(entry, dict) and entry.get("key")
            }
            for item in symbol_observations:
                key = f"{item.get('runId') or item.get('createdAt') or observed_at}:{symbol}"
                entry = {
                    "key": key,
                    "runId": item.get("runId"),
                    "mode": item.get("mode"),
                    "trigger": item.get("trigger"),
                    "createdAt": item.get("createdAt"),
                    "observedAt": observed_at,
                    "horizonKey": item.get("horizonKey"),
                    "horizonLabel": item.get("horizonLabel"),
                    "snapshotPrice": item.get("snapshotPrice"),
                    "currentPrice": item.get("currentPrice"),
                    "change": item.get("change"),
                    "changeRate": item.get("changeRate"),
                    "outcome": item.get("outcome"),
                    "score": item.get("score"),
                    "readiness": item.get("readiness"),
                    "gateKey": item.get("gateKey"),
                    "gateLabel": item.get("gateLabel"),
                    "finalActionKey": item.get("finalActionKey"),
                    "finalAction": item.get("finalAction"),
                    "reactionKey": item.get("reactionKey"),
                    "reactionLabel": item.get("reactionLabel"),
                    "reactionScore": item.get("reactionScore"),
                    "measured": True,
                }
                by_key[key] = entry
            performance_history = sorted(
                by_key.values(),
                key=lambda entry: str(entry.get("observedAt") or entry.get("createdAt") or ""),
                reverse=True,
            )[:20]
            metrics = candidate_pool_performance_metrics(performance_history)
            record["performanceHistory"] = performance_history
            record.update(metrics)
            record["updatedAt"] = observed_at
            items[symbol] = record
            updated_count += 1
            updated_symbols.append(symbol)

        data["items"] = items
        if updated_count:
            data["updatedAt"] = observed_at
            if not db_write_kv("candidate_pool", data):
                write_json(CANDIDATE_POOL_FILE, data)
        summary = candidate_pool_summary(data)

    for item in measured:
        change_rate = decimal_or_none(item.get("changeRate"))
        if change_rate is None:
            continue
        total_measured += 1
        total_change += change_rate
        if item.get("outcome") == "상승":
            total_positive += 1
        elif item.get("outcome") == "하락":
            total_negative += 1

    hit_rate = Decimal(total_positive) / Decimal(total_measured) * Decimal(100) if total_measured else Decimal("0")
    average_change = total_change / Decimal(total_measured) if total_measured else Decimal("0")
    return {
        "enabled": True,
        "updatedCount": updated_count,
        "updatedSymbols": updated_symbols[:12],
        "measuredCount": total_measured,
        "positiveCount": total_positive,
        "negativeCount": total_negative,
        "hitRate": display_percent_abs(hit_rate) if total_measured else "-",
        "averageChange": display_decimal_percent(average_change) if total_measured else "-",
        "summary": summary,
        "message": f"후보 풀 {updated_count}개에 사후 성과를 반영했습니다." if updated_count else "후보 풀에 연결된 성과 항목이 없습니다.",
    }


def performance_report(limit: int | None = None, top_n: int | None = None, min_age_minutes: int | None = None) -> dict:
    limit = SIGNAL_PERFORMANCE_RUN_LIMIT if limit is None else max(1, min(int(limit), 50))
    top_n = SIGNAL_PERFORMANCE_TOP_CANDIDATES if top_n is None else max(1, min(int(top_n), 10))
    min_age = max(0, SIGNAL_PERFORMANCE_MIN_AGE_MINUTES if min_age_minutes is None else int(min_age_minutes))
    generated_at_dt = datetime.now(KST)
    runs = recent_scheduler_runs(limit)
    snapshot_candidates: list[tuple[dict, dict]] = []
    symbols: list[str] = []
    eligible_run_count = 0
    fresh_run_skipped_count = 0
    for run in runs:
        created_at = parse_iso_datetime(str(run.get("createdAt", "")))
        if created_at and min_age > 0:
            elapsed_minutes = int((generated_at_dt - created_at.astimezone(KST)).total_seconds() // 60)
            if elapsed_minutes < min_age:
                fresh_run_skipped_count += 1
                continue
        eligible_run_count += 1
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
        score_detail = candidate.get("score", {}) if isinstance(candidate.get("score"), dict) else {}
        total_score = bounded_int(candidate.get("totalScore", score_candidate(candidate)))
        readiness = bounded_int(candidate.get("triggerReadiness", 0))
        confidence = candidate.get("dataConfidence") if isinstance(candidate.get("dataConfidence"), dict) else candidate_data_confidence(candidate)
        reaction = candidate.get("priceReaction") if isinstance(candidate.get("priceReaction"), dict) else candidate_price_reaction(candidate, score_detail)
        gate = candidate.get("qualityGate") if isinstance(candidate.get("qualityGate"), dict) else candidate_quality_gate(
            candidate,
            score_detail,
            total_score,
            readiness,
            confidence,
            reaction,
        )
        decision_group = candidate.get("decisionGroup", {}) if isinstance(candidate.get("decisionGroup"), dict) else {}
        final_decision = candidate.get("finalDecision") if isinstance(candidate.get("finalDecision"), dict) else candidate_final_decision(
            candidate,
            score_detail,
            total_score,
            readiness,
            confidence,
            gate,
            reaction,
        )
        horizon = performance_horizon(str(run.get("createdAt", "")))
        measured = start_price is not None and start_price > 0 and isinstance(current_price, Decimal)
        change_rate = Decimal("0")
        outcome = "미측정"
        price_sanity = True
        sanity_message = ""
        if measured:
            change_rate = ((current_price - start_price) / start_price) * Decimal(100)
            if SIGNAL_PERFORMANCE_OUTLIER_PERCENT > 0 and abs(change_rate) > SIGNAL_PERFORMANCE_OUTLIER_PERCENT:
                price_sanity = False
                sanity_message = f"가격 변화가 {display_percent_abs(change_rate)}로 커서 기준가와 현재가 출처 확인이 필요합니다."
                measured = False
                change_rate = Decimal("0")
                outcome = "가격 검증 필요"
            else:
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
            "decisionGroup": decision_group.get("label", ""),
            "finalActionKey": final_decision.get("actionKey", ""),
            "finalAction": final_decision.get("action", ""),
            "gateKey": gate.get("key", "unknown"),
            "gateLabel": gate.get("label", "미분류"),
            "confidenceScore": confidence.get("score"),
            "confidenceLabel": confidence.get("label", ""),
            "reactionKey": reaction.get("key", ""),
            "reactionLabel": reaction.get("label", ""),
            "reactionScore": reaction.get("score"),
            "horizonKey": horizon.get("key", "unknown"),
            "horizonLabel": horizon.get("label", "시점 미확인"),
            "elapsedMinutes": horizon.get("elapsedMinutes"),
            "snapshotPrice": candidate.get("price", "-"),
            "currentPrice": current.get("price", "-"),
            "priceSource": current.get("source", "missing"),
            "change": display_decimal_percent(change_rate) if measured else "-",
            "changeRate": str(change_rate.quantize(Decimal("0.01"))) if measured else "0",
            "outcome": outcome,
            "measured": measured,
            "priceSanity": price_sanity,
            "sanityMessage": sanity_message,
        })

    generated_at = generated_at_dt.isoformat(timespec="seconds")
    candidate_pool_performance = update_candidate_pool_performance(observations, generated_at)
    summary = performance_summary(observations, len(runs), price_status)
    summary.update({
        "eligibleRunCount": eligible_run_count,
        "freshRunSkippedCount": fresh_run_skipped_count,
        "minAgeMinutes": min_age,
    })
    return {
        "generatedAt": generated_at,
        "config": {
            "runLimit": limit,
            "topCandidates": top_n,
            "minAgeMinutes": min_age,
            "successThreshold": display_percent_abs(threshold),
            "outlierThreshold": display_percent_abs(SIGNAL_PERFORMANCE_OUTLIER_PERCENT),
        },
        "priceStatus": price_status,
        "candidatePoolPerformance": candidate_pool_performance,
        "summary": summary,
        "bySymbol": performance_by_symbol(observations),
        "byGate": performance_by_gate(observations),
        "byFinalAction": performance_by_final_action(observations),
        "byReaction": performance_by_reaction(observations),
        "byHorizon": performance_by_horizon(observations),
        "observations": observations,
    }


def performance_auto_update_summary(report: dict, trigger: str) -> dict:
    pool_update = report.get("candidatePoolPerformance", {}) if isinstance(report.get("candidatePoolPerformance"), dict) else {}
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
    return {
        "enabled": SIGNAL_PERFORMANCE_AUTO_UPDATE,
        "trigger": trigger,
        "updatedAt": report.get("generatedAt", datetime.now(KST).isoformat(timespec="seconds")),
        "updatedCount": pool_update.get("updatedCount", 0),
        "updatedSymbols": pool_update.get("updatedSymbols", []),
        "measuredCount": pool_update.get("measuredCount", summary.get("measuredCount", 0)),
        "positiveCount": pool_update.get("positiveCount", summary.get("positiveCount", 0)),
        "negativeCount": pool_update.get("negativeCount", summary.get("negativeCount", 0)),
        "hitRate": pool_update.get("hitRate", summary.get("hitRate", "-")),
        "averageChange": pool_update.get("averageChange", summary.get("averageChange", "-")),
        "eligibleRunCount": summary.get("eligibleRunCount", 0),
        "freshRunSkippedCount": summary.get("freshRunSkippedCount", 0),
        "minAgeMinutes": summary.get("minAgeMinutes", SIGNAL_PERFORMANCE_MIN_AGE_MINUTES),
        "message": pool_update.get("message", "성과 검증을 자동 실행했습니다."),
    }


def run_performance_auto_update(trigger: str = "snapshot") -> dict:
    if not SIGNAL_PERFORMANCE_AUTO_UPDATE:
        status = {
            "enabled": False,
            "trigger": trigger,
            "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
            "message": "성과 자동 반영이 꺼져 있습니다.",
        }
        with SCHEDULER_LOCK:
            SCHEDULER_STATE["lastPerformanceUpdate"] = status
            SCHEDULER_STATE["lastPerformanceError"] = ""
        return status
    try:
        report = performance_report(
            limit=SIGNAL_PERFORMANCE_RUN_LIMIT,
            top_n=SIGNAL_PERFORMANCE_TOP_CANDIDATES,
            min_age_minutes=SIGNAL_PERFORMANCE_MIN_AGE_MINUTES,
        )
        status = performance_auto_update_summary(report, trigger)
        with SCHEDULER_LOCK:
            SCHEDULER_STATE["lastPerformanceUpdate"] = status
            SCHEDULER_STATE["lastPerformanceError"] = ""
        return status
    except Exception as error:
        status = {
            "enabled": SIGNAL_PERFORMANCE_AUTO_UPDATE,
            "trigger": trigger,
            "updatedAt": datetime.now(KST).isoformat(timespec="seconds"),
            "error": str(error)[:240],
            "message": "성과 자동 반영 중 오류가 발생했습니다.",
        }
        with SCHEDULER_LOCK:
            SCHEDULER_STATE["lastPerformanceUpdate"] = status
            SCHEDULER_STATE["lastPerformanceError"] = status["error"]
        return status


def run_signal_snapshot(mode: str, trigger: str = "manual") -> dict:
    if mode not in {"close", "preopen", "intraday"}:
        raise ValueError("mode는 close, preopen, intraday 중 하나여야 합니다.")
    now = datetime.now(KST)
    payload = dashboard(mode, force_discovery=True)
    prefetch_status = prefetch_candidate_pool_market_data(
        mode,
        trigger=trigger,
        market=payload.get("market", {}),
    )
    payload.setdefault("integrations", {})["candidatePrefetch"] = prefetch_status
    summary = dashboard_summary(payload)
    summary["candidatePrefetch"] = prefetch_status
    run_id = f"{now.strftime('%Y%m%d-%H%M%S')}-{mode}-{trigger}"
    file_name = f"{now.date().isoformat()}_{mode}_{trigger}_{now.strftime('%H%M%S')}.json"
    path = RUNS_DIR / file_name
    snapshot = {
        "id": run_id,
        "mode": mode,
        "trigger": trigger,
        "createdAt": now.isoformat(timespec="seconds"),
        "summary": summary,
        "prefetch": prefetch_status,
        "dashboard": payload,
    }
    if db_write_snapshot(snapshot, file_name=file_name):
        record = {
            "id": snapshot.get("id", run_id),
            "mode": snapshot.get("mode"),
            "trigger": snapshot.get("trigger"),
            "createdAt": snapshot.get("createdAt"),
            "file": "database",
            "summary": snapshot.get("summary", {}),
        }
    else:
        write_json(path, snapshot)
        record = scheduler_record_from_snapshot(path, snapshot)
    performance_update = run_performance_auto_update(trigger=f"{mode}:{trigger}")
    record["performanceUpdate"] = performance_update
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
            "lastPerformanceUpdate": SCHEDULER_STATE.get("lastPerformanceUpdate", {}),
            "lastPerformanceError": SCHEDULER_STATE.get("lastPerformanceError", ""),
            "lastCandidatePrefetch": SCHEDULER_STATE.get("lastCandidatePrefetch", {}),
            "lastCandidatePrefetchError": SCHEDULER_STATE.get("lastCandidatePrefetchError", ""),
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
        STOCK_SEARCH_MASTER_STATE["lastCheckedAt"] = now.isoformat(timespec="seconds")
        if stock_search_master_refresh_due(now):
            refresh_stock_search_master(trigger="scheduled")
        if candidate_prefetch_due(now):
            run_scheduler_candidate_prefetch(now)
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

        if parsed.path == "/api/stocks/master/status":
            self.send_json(stock_search_master_status())
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

        if parsed.path == "/api/candidate-pool/status":
            self.send_json(candidate_pool_summary())
            return

        if parsed.path == "/api/storage/status":
            self.send_json(snapshot_storage_status())
            return

        if parsed.path == "/api/raw-events/status":
            self.send_json(raw_event_storage_status())
            return

        if parsed.path == "/api/performance":
            query = parse_qs(parsed.query)
            limit = int(query.get("limit", [str(SIGNAL_PERFORMANCE_RUN_LIMIT)])[0])
            top_n = int(query.get("top", [str(SIGNAL_PERFORMANCE_TOP_CANDIDATES)])[0])
            min_age = int(query.get("minAge", [str(SIGNAL_PERFORMANCE_MIN_AGE_MINUTES)])[0])
            self.send_json(performance_report(limit=limit, top_n=top_n, min_age_minutes=min_age))
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

        if parsed.path == "/api/dashboard/live-prices":
            query = parse_qs(parsed.query)
            mode = query.get("mode", ["close"])[0]
            if mode not in {"close", "preopen", "intraday"}:
                mode = "close"
            symbols = [
                symbol.strip()
                for symbol in query.get("symbols", [""])[0].split(",")
                if symbol.strip()
            ]
            detail = query.get("detail", ["price"])[0].strip().lower()
            try:
                self.send_json(dashboard_live_price_payload(symbols, mode, detail=detail))
            except Exception as error:
                payload, status = integration_error_payload(error)
                self.send_json(payload, status)
            return

        if parsed.path == "/api/dashboard":
            query = parse_qs(parsed.query)
            mode = query.get("mode", ["close"])[0]
            if mode not in {"close", "preopen", "intraday"}:
                mode = "close"
            force_refresh = query.get("refresh", ["0"])[0].lower() in {"1", "true", "yes", "on"}
            if not force_refresh:
                cached_payload = cached_dashboard_payload(mode)
                if cached_payload is not None:
                    self.send_json(cached_payload)
                    return
                stored_pool_payload = stored_candidate_pool_dashboard_payload(mode)
                if stored_pool_payload is not None:
                    self.send_json(stored_pool_payload)
                    return
            try:
                payload = dashboard(mode, force_discovery=force_refresh)
                write_dashboard_cache_record(mode, payload, source="manual-refresh" if force_refresh else "computed")
                self.send_json(payload)
            except Exception as error:
                cached_payload = cached_dashboard_payload(mode, fallback_error=str(error)[:240])
                if cached_payload is not None:
                    self.send_json(cached_payload)
                    return
                stored_pool_payload = stored_candidate_pool_dashboard_payload(mode, fallback_error=str(error)[:240])
                if stored_pool_payload is not None:
                    self.send_json(stored_pool_payload)
                    return
                raise
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

        if parsed.path == "/api/stocks/master/refresh":
            self.send_json(refresh_stock_search_master(trigger="manual"))
            return

        if parsed.path == "/api/storage/migrate":
            payload, status = run_database_migration()
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
