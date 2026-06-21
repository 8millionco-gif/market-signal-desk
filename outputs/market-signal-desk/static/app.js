function readStoredValue(key, fallback = "") {
  try {
    return window.localStorage.getItem(key) ?? fallback;
  } catch (error) {
    return fallback;
  }
}

function writeStoredValue(key, value) {
  try {
    window.localStorage.setItem(key, value);
  } catch (error) {
    // 브라우저 저장소가 제한된 환경에서는 알림 설정만 유지하지 않습니다.
  }
}

function removeStoredValue(key) {
  try {
    window.localStorage.removeItem(key);
  } catch (error) {
    // 저장소 삭제가 제한된 환경에서는 현재 세션 값만 비웁니다.
  }
}

function koreaTimeParts(date = new Date()) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "Asia/Seoul",
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  }).formatToParts(date);
  const get = (type) => parts.find((part) => part.type === type)?.value ?? "";
  const hour = Number(get("hour"));
  return {
    weekday: get("weekday"),
    hour: hour === 24 ? 0 : hour,
    minute: Number(get("minute"))
  };
}

function detectedAnalysisMode(date = new Date()) {
  const { weekday, hour, minute } = koreaTimeParts(date);
  const minutes = hour * 60 + minute;
  if (["Sat", "Sun"].includes(weekday)) return "close";
  if (minutes >= 9 * 60 && minutes < 15 * 60 + 30) return "intraday";
  return "close";
}

function normalizeAnalysisMode(mode) {
  return mode === "intraday" ? "intraday" : "close";
}

function dashboardRequestMode() {
  return state.modeAutoFollow ? "auto" : state.mode;
}

function applyServerDashboardMode(dashboard) {
  const serverMode = normalizeAnalysisMode(dashboard?.mode || dashboard?.market?.analysisMode || state.mode);
  state.mode = serverMode;
  state.autoMode = serverMode;
}

const state = {
  view: "signals",
  mode: detectedAnalysisMode(),
  autoMode: detectedAnalysisMode(),
  modeAutoFollow: true,
  filter: "all",
  strategy: "core",
  query: "",
  dashboard: null,
  feedExpanded: false,
  stockSearch: {
    query: "",
    loading: false,
    items: [],
    message: "",
    status: null,
    analyzingSymbol: null,
    activeIndex: -1
  },
  selectedLookup: null,
  searchTimer: null,
  performance: null,
  performanceLoading: false,
  authEnabled: false,
  authReadOnlyPublic: false,
  authRequired: false,
  adminToken: readStoredValue("marketSignalAdminToken", ""),
  schedulerStatus: null,
  discoveryBotStatus: null,
  storageStatus: null,
  evidenceStatus: null,
  stockMasterStatus: null,
  portfolioStatus: null,
  livePrice: {
    loading: false,
    updatedAt: "",
    attemptAt: "",
    message: "",
    source: "",
    error: "",
    pollSeconds: 10,
    refreshCount: 0,
    lastDepthAt: "",
    timer: null
  },
  viewingSnapshot: null,
  selectedSymbol: null,
  candidateDisplayMemory: {},
  notificationsEnabled: readStoredValue("marketSignalNotifications") === "1",
  lastNotifiedKey: readStoredValue("marketSignalLastNotifiedKey", ""),
  lastRunNotifiedId: readStoredValue("marketSignalLastRunNotifiedId", ""),
  schedulerStatusInitialized: false,
  activity: {
    active: false,
    title: "",
    detail: ""
  }
};

const els = {
  candidateFeed: document.querySelector("#candidateFeed"),
  signalDetail: document.querySelector("#signalDetail"),
  workspaceView: document.querySelector("#workspaceView"),
  settingsView: document.querySelector("#settingsView"),
  marketSessionLabel: document.querySelector("#marketSessionLabel"),
  analysisModeLabel: document.querySelector("#analysisModeLabel"),
  analysisModeDetail: document.querySelector("#analysisModeDetail"),
  modeSelect: document.querySelector("#modeSelect"),
  candidateCount: document.querySelector("#candidateCount"),
  candidateSource: document.querySelector("#candidateSource"),
  candidateSourceDetail: document.querySelector("#candidateSourceDetail"),
  searchInput: document.querySelector("#searchInput"),
  quickSearch: document.querySelector("#quickSearch"),
  stockSearchResults: document.querySelector("#stockSearchResults"),
  principles: document.querySelector("#principles"),
  kospiValue: document.querySelector("#kospiValue"),
  kospiChange: document.querySelector("#kospiChange"),
  kosdaqValue: document.querySelector("#kosdaqValue"),
  kosdaqChange: document.querySelector("#kosdaqChange"),
  nasdaqValue: document.querySelector("#nasdaqValue"),
  nasdaqChange: document.querySelector("#nasdaqChange"),
  usdKrwValue: document.querySelector("#usdKrwValue"),
  usdKrwPair: document.querySelector("#usdKrwPair"),
  marketNote: document.querySelector("#marketNote"),
  metricCandidates: document.querySelector("#metricCandidates"),
  metricHighScore: document.querySelector("#metricHighScore"),
  metricReady: document.querySelector("#metricReady"),
  metricWatched: document.querySelector("#metricWatched"),
  tradeDecisionStatus: document.querySelector("#tradeDecisionStatus"),
  livePriceStatus: document.querySelector("#livePriceStatus"),
  marketStatus: document.querySelector("#marketStatus"),
  authStatus: document.querySelector("#authStatus"),
  notificationStatus: document.querySelector("#notificationStatus"),
  candidatePoolStatus: document.querySelector("#candidatePoolStatus"),
  schedulerStatus: document.querySelector("#schedulerStatus"),
  discoveryBotStatus: document.querySelector("#discoveryBotStatus"),
  readinessStatus: document.querySelector("#readinessStatus"),
  storageStatus: document.querySelector("#storageStatus"),
  evidenceStatus: document.querySelector("#evidenceStatus"),
  stockMasterStatus: document.querySelector("#stockMasterStatus"),
  portfolioStatus: document.querySelector("#portfolioStatus"),
  snapshotHistory: document.querySelector("#snapshotHistory"),
  networkStatus: document.querySelector("#networkStatus"),
  tossStatus: document.querySelector("#tossStatus"),
  dartStatus: document.querySelector("#dartStatus"),
  newsStatus: document.querySelector("#newsStatus"),
  openaiStatus: document.querySelector("#openaiStatus"),
  performanceButton: document.querySelector("#performanceButton"),
  settingsButton: document.querySelector("#settingsButton"),
  deskButton: document.querySelector("#deskButton"),
  refreshButton: document.querySelector("#refreshButton")
};

els.activityBar = document.querySelector("#activityBar");
els.activityTitle = document.querySelector("#activityTitle");
els.activityDetail = document.querySelector("#activityDetail");
els.activityFill = document.querySelector("#activityFill");

const QUICK_SEARCH_PRESETS = [
  { label: "삼성", query: "삼성" },
  { label: "하이닉스", query: "하이닉스" },
  { label: "방산", query: "방산" },
  { label: "엔비디아", query: "엔비디아" },
  { label: "AI", query: "AI" },
  { label: "배당", query: "배당" }
];

const DASHBOARD_BROWSER_CACHE_PREFIX = "marketSignalDashboardCache:";
const DASHBOARD_BROWSER_CACHE_LAST = "marketSignalDashboardCache:last";
const LIVE_PRICE_MIN_POLL_MS = 5000;
const LIVE_PRICE_SYMBOL_LIMIT = 80;
const LIVE_MARKET_DEPTH_REFRESH_EVERY = 0;
const LIVE_PRICE_RETAIN_SECONDS = 90;
const LIVE_CHANGE_RETAIN_SECONDS = 180;
const CANDIDATE_DISPLAY_STICKY_MS = 60000;
const CANDIDATE_FEED_VISIBLE_LIMIT = 4;
const CANDIDATE_FEED_ALL_VISIBLE_LIMIT = 5;
const CANDIDATE_FEED_EXPANDED_LIMIT = 8;

function scoreClass(score) {
  if (score >= 75) return "";
  if (score >= 55) return "warn";
  return "low";
}

function changeClass(change) {
  const text = String(change ?? "").trim();
  if (text.startsWith("-")) return "change-down";
  if (text.startsWith("+")) return "change-up";
  return "change-neutral";
}

function displayChangeText(change) {
  const text = String(change ?? "").trim();
  if (!text || text === "-" || text.includes("확인")) return "-";
  const parsed = parseDisplayPercent(text);
  if (parsed == null) return text;
  const sign = parsed > 0 ? "+" : parsed < 0 ? "-" : "";
  const value = Math.abs(parsed).toLocaleString("ko-KR", {
    minimumFractionDigits: Number.isInteger(parsed) ? 0 : 1,
    maximumFractionDigits: 2
  });
  return `${sign}${value}%`;
}

function changeMissingText(item) {
  const livePrice = item?.livePrice ?? {};
  const hasLivePrice = livePrice.source === "toss" && Boolean(livePrice.lastPrice);
  const freshness = priceFreshnessInfo(item);
  if (livePrice.changeSource === "pending-change" || livePrice.changeSource === "missing") {
    if (hasLivePrice && freshness.isBaseline) return "마감 등락률 확인중";
    return hasLivePrice ? "등락률 수집중" : "가격 수집중";
  }
  if (livePrice.source === "toss" && (!item?.change || item.change === "-")) {
    if (hasLivePrice && freshness.isBaseline) return "마감 등락률 확인중";
    return hasLivePrice ? "등락률 수집중" : "가격 수집중";
  }
  return "";
}

function displayCandidateChangeText(item) {
  const value = displayChangeText(item?.change);
  return value === "-" ? changeMissingText(item) || "-" : value;
}

function candidateChangeClass(item) {
  const text = displayCandidateChangeText(item);
  if (text.includes("수집")) return "change-missing";
  if (text.includes("확인")) return "change-wait";
  return changeClass(item?.change);
}

function initials(name) {
  return name
    .split("")
    .filter((char) => /[A-Za-z0-9가-힣]/.test(char))
    .slice(0, 2)
    .join("")
    .toUpperCase();
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setTextIfChanged(node, value) {
  if (!node) return;
  const next = String(value ?? "");
  if (node.textContent !== next) node.textContent = next;
}

function setClassIfChanged(node, value) {
  if (!node) return;
  const next = String(value ?? "");
  if (node.className !== next) node.className = next;
}

function setHtmlIfChanged(node, value) {
  if (!node) return;
  const next = String(value ?? "");
  if (node.innerHTML !== next) node.innerHTML = next;
}

function dashboardBrowserCacheKey(mode) {
  return `${DASHBOARD_BROWSER_CACHE_PREFIX}${mode || state.mode || "close"}`;
}

function saveDashboardToBrowserCache(dashboard) {
  if (!dashboard || !Array.isArray(dashboard.candidates) || !dashboard.candidates.length) return;
  const mode = dashboard.mode || state.mode || "close";
  const record = {
    mode,
    savedAt: new Date().toISOString(),
    dashboard
  };
  try {
    const text = JSON.stringify(record);
    writeStoredValue(dashboardBrowserCacheKey(mode), text);
    writeStoredValue(DASHBOARD_BROWSER_CACHE_LAST, text);
  } catch (error) {
    // 대시보드가 브라우저 저장 한도를 넘으면 서버 저장본만 사용합니다.
  }
}

function readDashboardFromBrowserCache(mode) {
  const candidates = [
    readStoredValue(dashboardBrowserCacheKey(mode), ""),
    readStoredValue(DASHBOARD_BROWSER_CACHE_LAST, "")
  ];
  for (const text of candidates) {
    if (!text) continue;
    try {
      const record = JSON.parse(text);
      const dashboard = record?.dashboard;
      if (dashboard && Array.isArray(dashboard.candidates) && dashboard.candidates.length) {
        return { ...record, dashboard };
      }
    } catch (error) {
      // 손상된 브라우저 캐시는 무시하고 다음 후보를 확인합니다.
    }
  }
  return null;
}

function browserCachedDashboardPayload(mode, error) {
  const record = readDashboardFromBrowserCache(mode);
  if (!record) return null;
  const dashboard = JSON.parse(JSON.stringify(record.dashboard));
  const fallbackError = error?.name === "AbortError" ? "응답 지연" : "서버 연결 실패";
  const createdAt = record.savedAt || dashboard.generatedAt || "";
  dashboard.cache = {
    ...(dashboard.cache ?? {}),
    cached: true,
    source: "browser_cache",
    requestedMode: mode,
    mode: record.mode || dashboard.mode || mode,
    createdAt,
    fallbackError
  };
  dashboard.summary = {
    ...(dashboard.summary ?? {}),
    dashboardCacheSource: "browser_cache",
    dashboardCacheCreatedAt: createdAt,
    dashboardCacheFallbackError: fallbackError,
    candidateSourceStored: true
  };
  return dashboard;
}

function uniqueTexts(values = [], limit = 8) {
  const seen = new Set();
  const result = [];
  values.forEach((value) => {
    const text = String(value ?? "").replace(/\s+/g, " ").trim();
    const key = text.replace(/\s+/g, "").toLowerCase();
    if (!text || seen.has(key)) return;
    seen.add(key);
    result.push(text);
  });
  return result.slice(0, limit);
}

function shortText(value, limit = 32) {
  const text = String(value ?? "").replace(/\s+/g, " ").trim();
  return text.length > limit ? `${text.slice(0, limit - 1)}…` : text;
}

function renderActivity() {
  if (!els.activityBar) return;
  els.activityBar.hidden = !state.activity.active;
  if (els.activityTitle) els.activityTitle.textContent = state.activity.title || "데이터 갱신 중";
  if (els.activityDetail) els.activityDetail.textContent = state.activity.detail || "잠시만 기다려주세요";
  if (els.refreshButton) els.refreshButton.classList.toggle("active", state.activity.active);
}

function startActivity(title, detail = "") {
  state.activity = { active: true, title, detail };
  renderActivity();
}

function updateActivity(title, detail = "") {
  if (!state.activity.active) {
    startActivity(title, detail);
    return;
  }
  state.activity = { active: true, title, detail };
  renderActivity();
}

function finishActivity() {
  state.activity = { active: false, title: "", detail: "" };
  renderActivity();
}

function adminHeaders(extra = {}) {
  const headers = { ...extra };
  if (state.adminToken) {
    headers["X-Admin-Token"] = state.adminToken;
  }
  return headers;
}

function isAuthError(error) {
  return error?.message === "auth-required";
}

async function fetchJson(path, timeoutMs = 15000) {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(path, {
      signal: controller.signal,
      headers: adminHeaders()
    });
    if (response.status === 401) {
      state.authRequired = true;
      throw new Error("auth-required");
    }
    if (!response.ok) {
      throw new Error(`${response.status} ${response.statusText}`);
    }
    state.authRequired = false;
    return await response.json();
  } finally {
    window.clearTimeout(timer);
  }
}

async function safeFetchJson(path, fallback, timeoutMs = 5000) {
  try {
    return await fetchJson(path, timeoutMs);
  } catch (error) {
    if (isAuthError(error)) {
      return {
        ...fallback,
        error: "auth-required",
        message: "관리자 토큰이 필요합니다."
      };
    }
    return {
      ...fallback,
      error: "unavailable",
      message: error?.name === "AbortError" ? "응답 지연" : "연결 실패"
    };
  }
}

async function postJson(path, body = {}, timeoutMs = 45000) {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(path, {
      method: "POST",
      headers: adminHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify(body),
      signal: controller.signal
    });
    if (response.status === 401) {
      state.authRequired = true;
      throw new Error("auth-required");
    }
    if (!response.ok) {
      throw new Error(`${response.status} ${response.statusText}`);
    }
    state.authRequired = false;
    return await response.json();
  } finally {
    window.clearTimeout(timer);
  }
}

function statusFallbacks() {
  return {
    auth: {
      enabled: false
    },
    scheduler: {
      config: { enabled: false, jobs: [], performanceAutoUpdate: false, performanceMinAgeMinutes: 60 },
      state: { started: false, running: false, lastError: "", lastPerformanceUpdate: {}, lastPerformanceError: "" },
      recentRuns: []
    },
    discoveryBot: {
      config: { enabled: false, intervalSeconds: 0, mode: "intraday" },
      state: { started: false, running: false, lastError: "", lastRun: {} },
      latest: {}
    },
    storage: {
      mode: "filesystem",
      implementation: "filesystem",
      runsDir: "",
      writable: false,
      persistent: false,
      recentRunCount: 0,
      rawEvents: {
        enabled: false,
        implementation: "filesystem",
        count: 0,
        bySource: {},
        latest: {}
      },
      newsEvents: {
        enabled: false,
        implementation: "filesystem",
        count: 0,
        byProvider: {},
        latest: {}
      }
    },
    evidence: {
      enabled: false,
      implementation: "unavailable",
      persistent: false,
      operationReady: false,
      decisionReady: false,
      totalCount: 0,
      byKind: {},
      latestAt: "",
      openAiPendingCount: 0,
      stalePriceCount: 0,
      priceCoverage: 0,
      basisCounts: {},
      requiredKinds: {},
      optionalKinds: {},
      readiness: {
        operationReady: false,
        decisionReady: false,
        gaps: [],
        nextAction: "근거 수집 상태 확인 필요"
      }
    },
    stockMaster: {
      ok: false,
      storage: "none",
      generated: { exists: false, count: 0, generatedAt: "", sourceCounts: {} },
      active: { count: 0, usesGeneratedMaster: false },
      config: { autoRefreshEnabled: false, refreshSeconds: 0, databaseEnabled: false, databaseReady: false },
      state: {}
    },
    portfolio: {
      enabled: false,
      ready: false,
      source: "disabled",
      summary: {},
      buyingPower: {},
      items: []
    },
    network: {
      source: "unavailable",
      provider: "",
      ip: ""
    },
    toss: {
      clientIdConfigured: false,
      clientSecretConfigured: false,
      readyForTokenIssue: false,
      readyForMarketData: false
    },
    dart: {
      apiKeyConfigured: false,
      readyForDisclosures: false,
      corpCodeCacheExists: false
    },
    news: {
      naver: {
        clientIdConfigured: false,
        clientSecretConfigured: false,
        readyForNews: false
      },
      gdelt: {
        liveNewsEnabled: false,
        readyForNews: false,
        apiKeyRequired: false
      }
    },
    openai: {
      apiKeyConfigured: false,
      readyForAnalysis: false,
      model: "-"
    }
  };
}

async function loadDashboard(options = {}) {
  const forceRefresh = Boolean(options.refresh);
  startActivity(
    forceRefresh ? "오늘 후보 갱신 중" : "저장 후보 불러오는 중",
    forceRefresh ? "국내/해외 후보와 시장 지표를 새로 분석합니다" : "최근 저장된 후보와 시장 지표를 먼저 불러옵니다"
  );
  state.viewingSnapshot = null;
  const fallbacks = statusFallbacks();
  updateActivity("연결 상태 확인 중", "토스·뉴스·공시·OpenAI 연결 상태를 점검합니다");
  const statusPromise = Promise.all([
    safeFetchJson("/api/auth/status", fallbacks.auth),
    safeFetchJson("/api/scheduler/status", fallbacks.scheduler),
    safeFetchJson("/api/discovery/status", fallbacks.discoveryBot),
    safeFetchJson("/api/storage/status", fallbacks.storage),
    safeFetchJson("/api/evidence/status", fallbacks.evidence),
    safeFetchJson("/api/stocks/master/status", fallbacks.stockMaster),
    safeFetchJson("/api/portfolio/status", fallbacks.portfolio),
    safeFetchJson("/api/network/outbound-ip", fallbacks.network),
    safeFetchJson("/api/integrations/toss/status", fallbacks.toss),
    safeFetchJson("/api/integrations/dart/status", fallbacks.dart),
    safeFetchJson("/api/integrations/news/status", fallbacks.news),
    safeFetchJson("/api/integrations/openai/status", fallbacks.openai)
  ]).then(([authStatus, schedulerStatus, discoveryBotStatus, storageStatus, evidenceStatus, stockMasterStatus, portfolioStatus, networkStatus, tossStatus, dartStatus, newsStatus, openaiStatus]) => {
    state.authEnabled = Boolean(authStatus?.enabled);
    state.authReadOnlyPublic = Boolean(authStatus?.readOnlyPublic);
    state.schedulerStatus = schedulerStatus;
    state.discoveryBotStatus = discoveryBotStatus;
    state.storageStatus = storageStatus;
    state.evidenceStatus = evidenceStatus;
    state.stockMasterStatus = stockMasterStatus;
    state.portfolioStatus = portfolioStatus;
    state.networkStatus = networkStatus;
    state.tossStatus = tossStatus;
    state.dartStatus = dartStatus;
    state.newsStatus = newsStatus;
    state.openaiStatus = openaiStatus;
    maybeNotifySchedulerRun(schedulerStatus);
    renderAuthStatus();
    renderSchedulerStatus();
    renderDiscoveryBotStatus();
    renderReadinessStatus();
    renderStorageStatus();
    renderEvidenceStatus();
    renderStockMasterStatus();
    renderPortfolioStatus();
    renderSnapshotHistory();
    renderNotificationStatus();
    renderMarketStatus();
    renderNetworkStatus();
    renderTossStatus();
    renderDartStatus();
    renderNewsStatus();
    renderOpenAIStatus();
    renderCandidateSourceDetail();
  });

  let warmCacheRendered = false;
  if (!forceRefresh) {
    const cachedDashboard = browserCachedDashboardPayload(state.mode, { name: "WarmStart" });
    if (cachedDashboard) {
      state.dashboard = cachedDashboard;
      applyServerDashboardMode(cachedDashboard);
      const candidates = state.dashboard.candidates ?? [];
      if (!candidates.some((item) => item.symbol === state.selectedSymbol)) {
        const defaultCandidate = bestCandidate(candidates);
        state.selectedSymbol = defaultCandidate?.symbol ?? state.dashboard.selected?.symbol ?? null;
      }
      render();
      renderCandidateSourceDetail();
      finishActivity();
      warmCacheRendered = true;
    }
  }

  try {
    if (!warmCacheRendered) {
      updateActivity(
        forceRefresh ? "후보 분석 중" : "저장 데이터 확인 중",
        forceRefresh ? "뉴스, 공시, 가격 반응으로 후보 점수를 계산합니다" : "DB나 최신 스냅샷에 저장된 후보를 확인합니다"
      );
    }
    const params = new URLSearchParams({ mode: dashboardRequestMode() });
    if (forceRefresh) params.set("refresh", "1");
    const dashboard = await fetchJson(`/api/dashboard?${params.toString()}`, forceRefresh ? 45000 : 15000);
    await statusPromise;
    applyServerDashboardMode(dashboard);
    state.dashboard = dashboard;
    saveDashboardToBrowserCache(dashboard);
    if (!state.selectedSymbol) {
      const defaultCandidate = bestCandidate(state.dashboard.candidates ?? []);
      state.selectedSymbol = defaultCandidate?.symbol ?? state.dashboard.selected?.symbol ?? null;
    }
    if (!warmCacheRendered) {
      updateActivity("화면 구성 중", "선정 후보와 가격 행동 지표를 정리합니다");
    }
    render();
    finishActivity();
    startLivePricePolling();
  } catch (error) {
    await statusPromise;
    stopLivePricePolling();
    finishActivity();
    if (isAuthError(error)) {
      state.dashboard = null;
      renderAuthGate();
      return;
    }
    if (restoreDashboardFromBrowserCache(error)) return;
    state.dashboard = null;
    renderLoadError(error);
  }
}

function restoreDashboardFromBrowserCache(error) {
  const dashboard = browserCachedDashboardPayload(state.mode, error);
  if (!dashboard) return false;
  applyServerDashboardMode(dashboard);
  state.dashboard = dashboard;
  const candidates = state.dashboard.candidates ?? [];
  if (!candidates.some((item) => item.symbol === state.selectedSymbol)) {
    const defaultCandidate = bestCandidate(candidates);
    state.selectedSymbol = defaultCandidate?.symbol ?? state.dashboard.selected?.symbol ?? null;
  }
  render();
  renderCandidateSourceDetail();
  startLivePricePolling();
  return true;
}

function normalizeLiveSymbol(value) {
  return String(value ?? "").trim().toUpperCase();
}

function candidateLiveSymbol(item) {
  return normalizeLiveSymbol(item?.symbol);
}

function watchedCandidateSymbols() {
  return (state.dashboard?.candidates ?? [])
    .filter((item) => item?.isWatched)
    .map(candidateLiveSymbol)
    .filter(Boolean);
}

function portfolioHoldingSymbols() {
  const items = Array.isArray(state.portfolioStatus?.items) ? state.portfolioStatus.items : [];
  return items
    .map((item) => normalizeLiveSymbol(item?.symbol ?? item?.stockCode ?? item?.code ?? item?.ticker))
    .filter(Boolean);
}

function priorityLiveSymbols() {
  return [...new Set([...portfolioHoldingSymbols(), ...watchedCandidateSymbols()].filter(Boolean))];
}

function livePriceSymbols() {
  const candidates = state.dashboard?.candidates ?? [];
  const selected = normalizeLiveSymbol(selectedCandidate()?.symbol || state.selectedSymbol || "");
  const prioritySymbols = priorityLiveSymbols();
  const visibleSymbols = filteredCandidates()
    .filter((item) => item?.symbol)
    .map(candidateLiveSymbol);
  const candidateSymbols = candidates
    .filter((item) => item?.symbol)
    .map(candidateLiveSymbol);
  const rankedOverflow = [...candidates]
    .filter((item) => item?.symbol)
    .sort((a, b) => livePricePriority(a) - livePricePriority(b))
    .map(candidateLiveSymbol);
  return [...new Set([selected, ...prioritySymbols, ...visibleSymbols, ...rankedOverflow, ...candidateSymbols].filter(Boolean))]
    .slice(0, LIVE_PRICE_SYMBOL_LIMIT);
}

function candidateNeedsMarketDepth(item) {
  if (!item) return false;
  const candles = item.liveCandles ?? {};
  const orderbook = item.liveOrderbook ?? {};
  const trades = item.liveTrades ?? {};
  const livePrice = item.livePrice ?? {};
  const changePending =
    livePrice.source === "toss" &&
    livePrice.lastPrice &&
    (livePrice.changeSource === "pending-change" ||
      livePrice.changeSource === "missing" ||
      !item.change ||
      displayChangeText(item.change) === "-");
  return (
    changePending ||
    candles.source !== "toss" ||
    orderbook.source !== "toss" ||
    trades.source !== "toss"
  );
}

function livePriceRefreshDetail() {
  // Automatic 10-second polling must not trigger full candidate re-analysis.
  // Full depth/decision refresh is handled by scheduler/manual refresh so the
  // visible candidate and final judgement do not jump on every price tick.
  return "price";
}

function livePricePriority(item) {
  const symbol = item?.symbol || "";
  if (state.selectedSymbol && symbol === state.selectedSymbol) return -1000;
  const gate = item?.qualityGate?.key || "";
  const group = decisionGroupForDisplay(item).key;
  const plan = tradePlan(item);
  const compression = compressionForDisplay(item).tier;
  const score = Number(item?.totalScore ?? 0);
  const readiness = Number(item?.triggerReadiness ?? 0);
  const confidence = Number(item?.confidence?.score ?? 0);
  const reaction = Number(item?.priceReaction?.score ?? 0);
  const risk = Number(item?.score?.riskPenalty ?? 0);
  const heat = Number(item?.score?.heatPenalty ?? 0);
  let priority = 100;

  if (gate === "actionable") priority -= 40;
  if (selectedHoldingFor(item)) priority -= 28;
  if (item?.isWatched) priority -= 22;
  if (group === "action") priority -= 24;
  if (plan.tone === "buy") priority -= 22;
  if (compression === "core") priority -= 18;
  if (compression === "review") priority -= 10;
  if (state.strategy === "pullback" && isPullbackCandidate(item)) priority -= 14;
  if (state.strategy === "portfolio" && isHoldingCandidate(item)) priority -= 16;
  if (gate === "defer" || plan.tone === "wait") priority += 10;
  if (gate === "exclude" || plan.tone === "risk") priority += 40;

  priority -= Math.min(16, Math.max(0, score - 60) / 2);
  priority -= Math.min(12, Math.max(0, readiness - 55) / 2);
  priority -= Math.min(10, Math.max(0, confidence - 55) / 3);
  priority -= Math.min(10, Math.max(0, reaction - 45) / 3);
  priority += Math.min(18, risk / 2);
  priority += Math.min(12, heat / 2);
  return priority;
}

function candidateLiveRenderSignature(item = {}, options = {}) {
  const livePrice = item.livePrice ?? {};
  const freshness = livePrice.freshness ?? {};
  const priceSignature = {
    price: item.price || "",
    change: displayCandidateChangeText(item),
    updated: item.updated || "",
    livePrice: livePrice.lastPrice || "",
    liveChange: livePrice.changePercent ?? livePrice.changeRate ?? "",
    liveSource: livePrice.source || "",
    liveTimestamp: freshness.timestamp || livePrice.timestamp || livePrice.updatedAt || "",
    retained: Boolean(livePrice.retained),
    retainedChange: Boolean(livePrice.retainedChange)
  };
  if (options.priceOnly) return JSON.stringify(priceSignature);

  const plan = tradePlan(item);
  const primary = primaryDecisionForDisplay(item, plan);
  const finalDecision = item.finalDecision ?? {};
  return JSON.stringify({
    ...priceSignature,
    action: plan.action,
    tone: plan.tone,
    decision: primary.key || primary.label || "",
    score: item.totalScore ?? "",
    stabilityHeld: Boolean(finalDecision.stability?.held)
  });
}

function mergeLivePricePayload(payload) {
  const incoming = Array.isArray(payload?.candidates) ? payload.candidates : [];
  if (!state.dashboard || !incoming.length) return false;
  const priceOnly = payload?.detail === "price" || payload?.selectionCycle === "price-only";
  const existing = state.dashboard.candidates ?? [];
  const existingBySymbol = new Map(existing.map((item) => [item.symbol, item]));
  const signatureOptions = { priceOnly };
  const previousSignatures = new Map(existing.map((item) => [item.symbol, candidateLiveRenderSignature(item, signatureOptions)]));
  const incomingBySymbol = new Map(incoming.map((item) => [item.symbol, item]));
  const incomingSymbols = new Set(incomingBySymbol.keys());
  const merged = existing.map((item) => {
    const next = incomingBySymbol.get(item.symbol);
    return next ? mergeLiveCandidate(item, next, { priceOnly }) : item;
  });
  if (payload?.allowCandidateAppend) {
    incoming.forEach((item) => {
      if (!existingBySymbol.has(item.symbol)) merged.push(item);
    });
  }
  const changedSymbols = merged
    .filter((item) => previousSignatures.get(item.symbol) !== candidateLiveRenderSignature(item, signatureOptions))
    .map((item) => item.symbol);
  state.dashboard = {
    ...state.dashboard,
    generatedAt: payload.updatedAt || state.dashboard.generatedAt,
    summary: {
      ...(state.dashboard.summary ?? {}),
      ...livePriceSummaryPatch(payload.summary, { priceOnly })
    },
    integrations: {
      ...(state.dashboard.integrations ?? {}),
      ...livePriceIntegrationsPatch(payload.integrations)
    },
    candidates: merged,
    selected: merged.find((item) => item.symbol === state.selectedSymbol) || payload.selected || state.dashboard.selected
  };
  state.livePrice = {
    ...state.livePrice,
    changedSymbols,
    changedCount: changedSymbols.length
  };
  if (state.selectedLookup && incomingSymbols.has(state.selectedLookup.symbol)) {
    state.selectedLookup = merged.find((item) => item.symbol === state.selectedLookup.symbol) || null;
  }
  return true;
}

function livePriceTimestampMs(livePrice = {}) {
  const timestamp = livePrice?.freshness?.timestamp || livePrice?.timestamp || livePrice?.updatedAt || "";
  const parsed = timestamp ? Date.parse(timestamp) : NaN;
  return Number.isFinite(parsed) ? parsed : null;
}

function livePriceAgeSeconds(livePrice = {}) {
  const parsed = livePriceTimestampMs(livePrice);
  if (parsed == null) return null;
  return Math.max(0, Math.round((Date.now() - parsed) / 1000));
}

function currentLivePriceStillUsable(current, seconds = LIVE_PRICE_RETAIN_SECONDS) {
  const livePrice = current?.livePrice ?? {};
  if (livePrice.source !== "toss" || !livePrice.lastPrice) return false;
  const ageSeconds = livePriceAgeSeconds(livePrice);
  if (ageSeconds == null) return false;
  const pollWindow = Number(state.livePrice?.pollSeconds || 10) * 9;
  return ageSeconds <= Math.max(seconds, pollWindow);
}

function incomingLivePriceMissing(incoming) {
  const livePrice = incoming?.livePrice ?? {};
  if (!livePrice || !Object.keys(livePrice).length) return true;
  if (livePrice.source !== "toss") return true;
  return !livePrice.lastPrice;
}

function currentChangeStillUsable(current) {
  const display = displayChangeText(current?.change);
  if (!current?.change || !display || display === "-" || display.includes("수집")) return false;
  const livePrice = current?.livePrice ?? {};
  if (livePrice.source !== "toss") return true;
  const ageSeconds = livePriceAgeSeconds(livePrice);
  if (ageSeconds == null) return true;
  const pollWindow = Number(state.livePrice?.pollSeconds || 10) * 18;
  return ageSeconds <= Math.max(LIVE_CHANGE_RETAIN_SECONDS, pollWindow);
}

function incomingChangeMissing(incoming) {
  const livePrice = incoming?.livePrice ?? {};
  if (livePrice.changeSource === "missing" || livePrice.changeSource === "pending-change") return true;
  return !incoming?.change || displayChangeText(incoming.change) === "-";
}

function retainedLivePrice(current) {
  return {
    ...(current?.livePrice ?? {}),
    retained: true,
    missedInLastFetch: true,
    message: "이번 갱신에서 토스 응답이 누락되어 직전 정상 가격을 유지합니다."
  };
}

function mergeLiveCandidate(current, incoming, options = {}) {
  const merged = { ...current };
  const priceOnly = Boolean(options.priceOnly);
  const retainCurrentPrice = currentLivePriceStillUsable(current) && incomingLivePriceMissing(incoming);
  const retainCurrentChange =
    !retainCurrentPrice &&
    currentChangeStillUsable(current) &&
    incomingChangeMissing(incoming);
  const priceRetainedFields = new Set(["price", "change", "updated", "livePrice", "dataCompleteness", "priceReadiness", "evaluationMode", "priceReaction", "qualityGate", "finalDecision", "signalValidation"]);
  const changeRetainedFields = new Set(["change", "priceReaction", "dataCompleteness", "priceReadiness", "evaluationMode", "qualityGate", "finalDecision", "signalValidation"]);
  const priceOnlyFields = [
    "price",
    "change",
    "updated",
    "livePrice"
  ];
  const analysisFields = [
    "price",
    "change",
    "chart",
    "updated",
    "livePrice",
    "liveCandles",
    "liveOrderbook",
    "liveTrades",
    "dataCompleteness",
    "priceReadiness",
    "evaluationMode",
    "priceReaction",
    "qualityGate",
    "finalDecision",
    "signalValidation",
    "dataConfidence",
    "sourceReliability",
    "decisionGroup",
    "candidateCompression"
  ];
  const liveFields = priceOnly ? priceOnlyFields : analysisFields;
  liveFields.forEach((key) => {
    if (retainCurrentPrice && priceRetainedFields.has(key)) return;
    if (retainCurrentChange && changeRetainedFields.has(key)) return;
    if (incoming[key] !== undefined) merged[key] = incoming[key];
  });
  if (retainCurrentPrice) {
    merged.livePrice = retainedLivePrice(current);
    merged.price = current.price;
    merged.change = current.change;
    merged.updated = current.updated;
    merged.priceReaction = current.priceReaction;
  } else if (retainCurrentChange) {
    merged.change = current.change;
    merged.priceReaction = current.priceReaction;
    merged.livePrice = {
      ...(merged.livePrice ?? {}),
      retainedChange: true,
      changeSource: current.livePrice?.changeSource || "retained-change",
      changeMessage: "이번 토스 현재가 응답에 등락률이 없어 직전 등락률을 유지합니다."
    };
  }
  if (incoming.trend) {
    merged.trend = {
      ...(current.trend ?? {}),
      ...incoming.trend
    };
  }
  if (!priceOnly && incoming.finalDecision) {
    merged.finalDecision = mergeLiveFinalDecision(current.finalDecision, incoming.finalDecision);
  }
  merged.liveUpdate = {
    updatedAt: merged.livePrice?.updatedAt || incoming.livePrice?.updatedAt || incoming.updated || new Date().toISOString(),
    source: merged.livePrice?.source || incoming.livePrice?.source || "live-price"
  };
  return merged;
}

function mergeLiveFinalDecision(current = {}, incoming = {}) {
  if (!incoming || !Object.keys(incoming).length) return current || {};
  return {
    ...(current ?? {}),
    ...incoming
  };
}

function livePriceSummaryPatch(summary, options = {}) {
  const source = summary && typeof summary === "object" ? summary : {};
  const priceOnly = Boolean(options.priceOnly);
  const allowedKeys = [
    "livePriceUpdatedAt",
    "livePricePollSeconds",
    "livePriceFreshnessCounts",
    "livePriceRequestedCount",
    "livePriceTossRequestedCount",
    "livePriceTossReceivedCount",
    "livePriceBatchCount",
    "livePriceBatchErrorCount",
    "livePriceRefreshedCount",
    "livePriceStoredFallbackCount",
    "livePriceRetainedCount",
    "livePriceMissingCount",
    "livePriceMissingSymbols",
    "tossDataCoverage",
    "tossPriceCoverageCount",
    "tossChangeCoverageCount",
    "tossChartCoverageCount",
    "tossOrderbookCoverageCount",
    "tossTradeCoverageCount",
    "candidateMarketDataLatestUpdatedCount",
    "candidateMarketDataLatestStored",
    "candidateDataCarriedForwardCount",
    "candidateDataCarriedForwardFields"
  ];
  const analysisKeys = [
    "tossEntryDataReadyCount",
    "stableDecisionCount",
    "finalDecisionStabilitySeconds",
    "evaluationModeCounts",
    "tradeEvaluationReadyCount",
    "baselineEvaluationCount",
    "serverCollectingCount",
    "unavailableEvaluationCount"
  ];
  if (!priceOnly) allowedKeys.push(...analysisKeys);
  return allowedKeys.reduce((patch, key) => {
    if (source[key] !== undefined) patch[key] = source[key];
    return patch;
  }, {});
}

function livePriceIntegrationsPatch(integrations) {
  const source = integrations && typeof integrations === "object" ? integrations : {};
  const patch = {};
  if (source.livePrice) patch.livePrice = source.livePrice;
  if (source.candidateMarketDataLatest) patch.candidateMarketDataLatest = source.candidateMarketDataLatest;
  if (source.marketDataLatest) patch.marketDataLatest = source.marketDataLatest;
  if (source.marketDataMerge) patch.marketDataMerge = source.marketDataMerge;
  if (source.toss) {
    patch.toss = {
      ...(state.dashboard?.integrations?.toss ?? {}),
      ...source.toss
    };
  }
  return patch;
}

function renderLivePriceUpdate(payload = {}) {
  const priceOnly = payload?.detail === "price" || payload?.selectionCycle === "price-only";
  const changedSymbols = new Set(state.livePrice?.changedSymbols || []);
  const selectedChanged = state.selectedSymbol && changedSymbols.has(state.selectedSymbol);
  if (!priceOnly && selectedChanged) {
    renderTradeDecisionStatus();
  }
  renderLivePriceStatus();
  if (!changedSymbols.size && priceOnly) return;
  updateLivePriceFragments({ detail: payload.detail || "price", priceOnly, changedSymbols });
}

function updateLivePriceFragments(options = {}) {
  updateFeedPriceFragments(options);
  updateSelectedPriceFragments(options);
}

function updateFeedPriceFragments(options = {}) {
  const priceOnly = Boolean(options.priceOnly);
  const changedSymbols = options.changedSymbols instanceof Set ? options.changedSymbols : new Set();
  const candidates = state.dashboard?.candidates ?? [];
  const bySymbol = new Map(candidates.map((item) => [item.symbol, item]));
  document.querySelectorAll(".feed-item[data-symbol]").forEach((button) => {
    if (changedSymbols.size && !changedSymbols.has(button.dataset.symbol)) return;
    const item = bySymbol.get(button.dataset.symbol);
    if (!item) return;
    const plan = tradePlan(item);
    const action = button.querySelector("[data-feed-action]");
    const score = button.querySelector("[data-feed-score]");
    const time = button.querySelector("[data-feed-time]");
    const price = button.querySelector("[data-feed-price]");
    const change = button.querySelector("[data-feed-change]");
    const decision = button.querySelector("[data-feed-decision]");
    const liveData = button.querySelector("[data-feed-live]");
    const primary = primaryDecisionForDisplay(item, plan);
    if (!priceOnly && action) {
      setTextIfChanged(action, feedActionLabel(item, plan));
      setClassIfChanged(action, `feed-action ${plan.tone}`);
    }
    if (!priceOnly && score) {
      setTextIfChanged(score, item.totalScore ?? "-");
      setClassIfChanged(score, `score-pill ${scoreClass(item.totalScore)}`);
    }
    setTextIfChanged(time, livePriceLabel(item) || item.updated || "");
    setTextIfChanged(price, item.price || "-");
    if (change) {
      setTextIfChanged(change, displayCandidateChangeText(item));
      setClassIfChanged(change, candidateChangeClass(item));
    }
    if (!priceOnly && decision) {
      setTextIfChanged(decision, primary.label);
      setClassIfChanged(decision, `feed-badge decision-badge decision-${primary.key}`);
    }
    setHtmlIfChanged(liveData, liveDataCoverageChips(item, true));
  });
}

function updateSelectedPriceFragments(options = {}) {
  const item = selectedCandidate();
  if (!item) return;
  const priceOnly = Boolean(options.priceOnly);
  const changedSymbols = options.changedSymbols instanceof Set ? options.changedSymbols : new Set();
  if (changedSymbols.size && !changedSymbols.has(item.symbol)) return;
  const plan = tradePlan(item);
  const primaryDecision = primaryDecisionForDisplay(item, plan);
  const priceNode = document.querySelector("[data-selected-price]");
  const changeNode = document.querySelector("[data-selected-change]");
  const sourceNode = document.querySelector("[data-selected-price-meta]");
  const liveDataNode = document.querySelector("[data-selected-live-data]");
  const decisionNode = document.querySelector("[data-selected-decision-summary]");
  const decisionLabelNode = decisionNode?.querySelector("strong");
  const decisionDetailNode = decisionNode?.querySelector("span");
  setTextIfChanged(priceNode, item.price || "-");
  if (changeNode) {
    setTextIfChanged(changeNode, displayCandidateChangeText(item));
    setClassIfChanged(changeNode, candidateChangeClass(item));
  }
  setTextIfChanged(sourceNode, priceMeta(item));
  setHtmlIfChanged(liveDataNode, liveDataCoverageChips(item));
  if (priceOnly) {
    updateSelectedLivePriceOnlyFragments(item);
    return;
  }
  setClassIfChanged(decisionNode, `decision-summary decision-${primaryDecision.key}`);
  setTextIfChanged(decisionLabelNode, primaryDecision.label);
  setTextIfChanged(decisionDetailNode, primaryDecision.detail);
  updateSignalFlowFragments(item, plan, primaryDecision);
  updatePriceReactionFragments(item);
  updateTradePlanFragments(item);
  if (options.detail && options.detail !== "price") {
    drawChart(item.chart);
  }
}

function updateSelectedLivePriceOnlyFragments(item) {
  const cardMeta = document.querySelector("[data-reaction-card-meta]");
  const liveGrid = document.querySelector("[data-reaction-live-grid]");
  setTextIfChanged(cardMeta, priceMeta(item));
  setHtmlIfChanged(liveGrid, reactionLiveGridHtml(item));
}

function updateSignalFlowFragments(item, plan, primaryDecision) {
  const stage = reactionStageForDisplay(item);
  const sourceMeta = candidateSignalMeta(item) || "출처 확인 중";
  const newsMeta = document.querySelector("[data-flow-news-meta]");
  const priceLabel = document.querySelector("[data-flow-price-label]");
  const priceSummary = document.querySelector("[data-flow-price-summary]");
  const finalLabel = document.querySelector("[data-flow-final-label]");
  const finalAction = document.querySelector("[data-flow-final-action]");
  setTextIfChanged(newsMeta, sourceMeta);
  setTextIfChanged(priceLabel, stage.label);
  setTextIfChanged(priceSummary, stage.summary);
  setTextIfChanged(finalLabel, primaryDecision.label);
  setTextIfChanged(finalAction, plan.action);
}

function reactionCheckGridHtml(stage) {
  return stage.checks
    .map(
      ([label, ok, value]) => `
        <div class="${ok ? "ok" : "wait"}">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
        </div>
      `
    )
    .join("");
}

function reactionLiveMetrics(item) {
  const reaction = item?.priceReaction ?? {};
  const metrics = reaction.metrics ?? {};
  const freshness = priceFreshnessInfo(item);
  const candles = item?.liveCandles ?? {};
  const orderbook = item?.liveOrderbook ?? {};
  const trades = item?.liveTrades ?? {};
  const volumeValue = metrics.volumeSpike || volumeReactionText(item);
  const candleValue = candles.source === "toss"
    ? `토스 일봉 ${candles.count ?? 0}개`
    : dataSourceLabel(candles.source || "", "차트 대기", candles.message);
  const orderbookValue = metrics.orderbookImbalance
    ? `${orderbook.pressure || "호가"} ${metrics.orderbookImbalance}`
    : orderbook.source === "toss"
      ? orderbook.pressure || "반영"
      : dataSourceLabel(orderbook.source || "", "호가 대기", orderbook.message);
  const tradeValue = metrics.tradeBias
    ? `${trades.pressure || "체결"} ${metrics.tradeBias}`
    : trades.source === "toss"
      ? trades.pressure || "반영"
      : dataSourceLabel(trades.source || "", "체결 대기", trades.message);
  return [
    {
      label: "현재가",
      value: `${item?.price ?? "-"} ${displayCandidateChangeText(item)}`.trim(),
      note: freshness.isFresh || freshness.isBaseline ? livePriceLabel(item) : freshness.message || "토스 현재가 대기",
      tone: freshness.isFresh ? "ok" : freshness.isBaseline || freshness.isDelayed ? "warn" : "wait"
    },
    {
      label: "거래량",
      value: volumeValue && volumeValue !== "-" ? volumeValue : candleValue,
      note: candles.source === "toss"
        ? `토스 일봉 기반${metrics.volumeConfirmed ? " · 거래량 반응 확인" : ""}`
        : candles.message || "거래량 확인 필요",
      tone: metrics.volumeConfirmed ? "ok" : candles.source === "toss" ? "warn" : dataSourceTone(candles.source, candles.message)
    },
    {
      label: "호가",
      value: orderbookValue || "-",
      note: orderbook.source === "toss" ? `스프레드 ${orderbook.spreadPercent || "-"}` : orderbook.message || "호가 대기",
      tone: metrics.hasOrderbook ? (metrics.liquidityConfirmed ? "ok" : "warn") : "wait"
    },
    {
      label: "체결",
      value: tradeValue || "-",
      note: trades.source === "toss" ? `최근 체결 ${trades.count ?? "-"}건` : trades.message || "체결 대기",
      tone: metrics.hasTrades ? (metrics.liquidityConfirmed ? "ok" : "warn") : "wait"
    }
  ];
}

function reactionLiveGridHtml(item) {
  return reactionLiveMetrics(item)
    .map(
      (entry) => `
        <div class="${escapeHtml(entry.tone)}">
          <span>${escapeHtml(entry.label)}</span>
          <strong>${escapeHtml(entry.value)}</strong>
          <em>${escapeHtml(entry.note)}</em>
        </div>
      `
    )
    .join("");
}

function updatePriceReactionFragments(item) {
  const stage = reactionStageForDisplay(item);
  const label = document.querySelector("[data-reaction-label]");
  const summary = document.querySelector("[data-reaction-summary]");
  const card = document.querySelector("[data-reaction-status-card]");
  const cardLabel = document.querySelector("[data-reaction-card-label]");
  const cardMeta = document.querySelector("[data-reaction-card-meta]");
  const liveGrid = document.querySelector("[data-reaction-live-grid]");
  const checks = document.querySelector("[data-reaction-check-grid]");
  setTextIfChanged(label, stage.label);
  setTextIfChanged(summary, stage.summary);
  setClassIfChanged(card, `reaction-status-card reaction-${stage.tone}`);
  setTextIfChanged(cardLabel, stage.label);
  setTextIfChanged(cardMeta, priceMeta(item));
  setHtmlIfChanged(liveGrid, reactionLiveGridHtml(item));
  setHtmlIfChanged(checks, reactionCheckGridHtml(stage));
}

function tradeZoneGridHtml(plan) {
  return tradeZoneCards(plan)
    .map(
      ([label, value, note]) => `
        <div>
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
          <em>${escapeHtml(note)}</em>
        </div>
      `
    )
    .join("");
}

function updateTradePlanFragments(item) {
  const plan = tradePlan(item);
  const now = tradeNowGuide(item, plan);
  const action = document.querySelector("[data-plan-action]");
  const summary = document.querySelector("[data-plan-summary]");
  const pill = document.querySelector("[data-plan-action-pill]");
  const nowCard = document.querySelector("[data-now-card]");
  const nowTitle = document.querySelector("[data-now-title]");
  const nowSummary = document.querySelector("[data-now-summary]");
  const nowCurrent = document.querySelector("[data-now-current]");
  const nowFocus = document.querySelector("[data-now-focus]");
  const zoneGrid = document.querySelector("[data-trade-zone-grid]");
  setTextIfChanged(action, plan.action);
  setTextIfChanged(summary, plan.summary);
  if (pill) {
    setTextIfChanged(pill, plan.action);
    setClassIfChanged(pill, `action-pill ${plan.tone}`);
  }
  setClassIfChanged(nowCard, `decision-now-card decision-${now.tone}`);
  setTextIfChanged(nowTitle, now.title);
  setTextIfChanged(nowSummary, now.summary);
  setTextIfChanged(nowCurrent, now.current || "-");
  setTextIfChanged(nowFocus, `기준 ${now.focus || "-"}`);
  setHtmlIfChanged(zoneGrid, tradeZoneGridHtml(plan));
}

async function refreshLivePrices() {
  if (state.view !== "signals") return;
  if (!state.dashboard?.candidates?.length) return;
  if (state.activity.active || state.livePrice.loading) return;
  const symbols = livePriceSymbols();
  if (!symbols.length) return;

  state.livePrice = {
    ...state.livePrice,
    loading: true,
    attemptAt: new Date().toISOString(),
    error: "",
    symbols,
    symbolCount: symbols.length
  };
  renderLivePriceStatus();
  const params = new URLSearchParams({
    mode: dashboardRequestMode(),
    symbols: symbols.join(","),
    detail: livePriceRefreshDetail(symbols)
  });
  const fallback = {
    candidates: [],
    summary: {},
    integrations: {},
    pollSeconds: state.livePrice.pollSeconds,
    message: "라이브 가격 갱신 실패",
    error: "unavailable",
    symbols,
    requestedCount: symbols.length
  };
  const payload = await safeFetchJson(`/api/dashboard/live-prices?${params.toString()}`, fallback, 12000);
  const priceOnlyPayload = payload?.detail === "price" || payload?.selectionCycle === "price-only";
  const stableDecisionCount = state.livePrice.stableDecisionCount ?? 0;
  const finalDecisionStabilitySeconds = state.livePrice.finalDecisionStabilitySeconds ?? 0;
  const merged = mergeLivePricePayload(payload);
  state.livePrice = {
    ...state.livePrice,
    loading: false,
    updatedAt: payload.updatedAt || state.livePrice.updatedAt,
    message: payload.message || (merged ? "라이브 가격 반영" : "라이브 가격 대기"),
    source: payload.source || state.livePrice.source,
    selectionCycle: payload.selectionCycle || payload.integrations?.livePrice?.selectionCycle || state.livePrice.selectionCycle,
    error: payload.error || "",
    pollSeconds: Number(payload.pollSeconds || state.livePrice.pollSeconds || 10),
    refreshCount: Number(state.livePrice.refreshCount || 0) + 1,
    lastDepthAt: payload.detail === "full" ? (payload.updatedAt || state.livePrice.lastDepthAt) : state.livePrice.lastDepthAt,
    symbols: Array.isArray(payload.symbols) && payload.symbols.length ? payload.symbols : symbols,
    symbolCount: Number(payload.requestedCount || payload.refreshedCount || symbols.length),
    storedFallbackCount: Number(payload.summary?.livePriceStoredFallbackCount ?? 0),
    retainedCount: Number(payload.summary?.livePriceRetainedCount ?? 0),
    missingCount: Number(payload.summary?.livePriceMissingCount ?? 0),
    tossDataCoverage: payload.summary?.tossDataCoverage ?? state.livePrice.tossDataCoverage ?? {},
    stableDecisionCount: Number(
      priceOnlyPayload ? stableDecisionCount : payload.summary?.stableDecisionCount ?? stableDecisionCount
    ),
    finalDecisionStabilitySeconds: Number(
      priceOnlyPayload
        ? finalDecisionStabilitySeconds
        : payload.summary?.finalDecisionStabilitySeconds ?? finalDecisionStabilitySeconds
    ),
    candidateDataCarriedForwardCount: Number(
      payload.summary?.candidateDataCarriedForwardCount ?? state.livePrice.candidateDataCarriedForwardCount ?? 0
    )
  };
  if (merged) {
    renderLivePriceUpdate(payload);
  } else {
    renderLivePriceStatus();
  }
}

function stopLivePricePolling() {
  if (state.livePrice.timer) {
    window.clearInterval(state.livePrice.timer);
    state.livePrice.timer = null;
  }
}

function startLivePricePolling() {
  stopLivePricePolling();
  if (!state.dashboard?.candidates?.length) return;
  const pollMs = Math.max(
    LIVE_PRICE_MIN_POLL_MS,
    Number(state.livePrice.pollSeconds || 10) * 1000
  );
  state.livePrice.timer = window.setInterval(() => {
    refreshLivePrices();
  }, pollMs);
  refreshLivePrices();
}

async function loadPerformance() {
  state.performanceLoading = true;
  startActivity("성과 검증 중", "저장된 후보와 현재 가격을 비교합니다");
  renderPerformance();
  try {
    state.performance = await fetchJson("/api/performance?limit=12&top=3", 30000);
  } catch (error) {
    if (isAuthError(error)) {
      state.performanceLoading = false;
      finishActivity();
      renderAuthGate();
      return;
    }
    state.performance = {
      error: "load-failed",
      message: error?.name === "AbortError" ? "성과 검증 응답이 지연되고 있습니다." : "성과 검증 데이터를 불러오지 못했습니다.",
      summary: {},
      observations: [],
      bySymbol: []
    };
  } finally {
    state.performanceLoading = false;
    finishActivity();
    renderPerformance();
  }
}

function renderLoadError(error) {
  const message = error?.name === "AbortError" ? "외부 API 응답이 지연되고 있습니다." : "백엔드 서버 응답을 받지 못했습니다.";
  els.candidateCount.textContent = "0개";
  if (els.candidateSource) els.candidateSource.textContent = "연결 실패";
  renderCandidateSourceDetail([
    ["후보 출처", false, "연결 실패"],
    ["저장 상태", false, "불러오기 실패"],
    ["다음 조치", false, "새로고침 또는 서버 확인"]
  ]);
  els.metricCandidates.textContent = 0;
  els.metricHighScore.textContent = 0;
  els.metricReady.textContent = 0;
  els.metricWatched.textContent = 0;
  if (els.candidatePoolStatus) {
    els.candidatePoolStatus.innerHTML = `
      <div>
        <span>관찰 후보</span>
        <strong class="warn">연결 실패</strong>
      </div>
    `;
  }
  els.principles.innerHTML = "";
  els.candidateFeed.innerHTML = `
    <div class="empty-state">
      <h2>후보를 불러오지 못했습니다</h2>
      <p>${escapeHtml(message)}</p>
    </div>
  `;
  els.signalDetail.innerHTML = `
    <div class="empty-state">
      <h2>데이터 연결을 확인하세요</h2>
      <p>새로고침하거나 실행 중인 서버를 다시 시작해 주세요.</p>
    </div>
  `;
}

function filteredCandidates() {
  const base = baseFilteredCandidates();
  let strategy = state.strategy;
  let actualCandidates = candidatesForStrategy(base, strategy);
  let retainedCandidates = retainedVisibleCandidates(base, actualCandidates, strategy);
  if (!actualCandidates.length && strategy !== "all" && !retainedCandidates.length) {
    const resolved = resolveCandidateStrategy(base, strategy);
    strategy = resolved.strategy;
    state.strategy = strategy;
    actualCandidates = resolved.candidates;
    retainedCandidates = retainedVisibleCandidates(base, actualCandidates, strategy);
  }
  rememberVisibleCandidates(strategy, actualCandidates);
  return sortCandidatesForStrategy([...actualCandidates, ...retainedCandidates], strategy);
}

function candidateFeedBaseLimit() {
  return state.strategy === "all" ? CANDIDATE_FEED_ALL_VISIBLE_LIMIT : CANDIDATE_FEED_VISIBLE_LIMIT;
}

function visibleFeedCandidates(candidates = []) {
  const items = Array.isArray(candidates) ? candidates : [];
  const queryActive = Boolean(state.query.trim());
  const baseLimit = candidateFeedBaseLimit();
  const collapsedLimit = queryActive ? Math.max(baseLimit, CANDIDATE_FEED_ALL_VISIBLE_LIMIT) : baseLimit;
  const expandedLimit = Math.max(collapsedLimit, CANDIDATE_FEED_EXPANDED_LIMIT);
  const canToggle = items.length > collapsedLimit;
  const expanded = Boolean(state.feedExpanded && canToggle);
  const effectiveLimit = expanded ? Math.min(items.length, expandedLimit) : collapsedLimit;
  if (!canToggle) {
    return {
      items,
      hiddenCount: 0,
      baseLimit: collapsedLimit,
      expandedLimit,
      canToggle: false,
      expanded: false
    };
  }

  const visible = items.slice(0, effectiveLimit);
  if (state.selectedSymbol && !visible.some((item) => item.symbol === state.selectedSymbol)) {
    const selected = items.find((item) => item.symbol === state.selectedSymbol);
    if (selected) {
      visible.splice(Math.max(0, effectiveLimit - 1), 1, selected);
    }
  }

  return {
    items: visible,
    hiddenCount: Math.max(0, items.length - visible.length),
    baseLimit: collapsedLimit,
    expandedLimit,
    canToggle,
    expanded
  };
}

function candidateFeedToggleMarkup(feedView, totalCount) {
  if (!feedView?.canToggle) return "";
  const hiddenText = feedView.expanded
    ? feedView.hiddenCount > 0
      ? `${feedView.hiddenCount}개 후보는 설정/성과 화면에서 확인하고 서버가 계속 관찰합니다.`
      : "메인 화면을 다시 압축해서 봅니다."
    : `${feedView.hiddenCount}개 후보는 서버와 DB에서 계속 관찰 중입니다.`;
  const actionText = feedView.expanded ? "상위만 보기" : `더 보기`;
  const titleText = feedView.expanded
    ? `압축 후보 ${feedView.items.length}/${totalCount}개`
    : `상위 ${feedView.items.length}개만 표시`;
  return `
    <button class="feed-limit-panel" type="button" data-feed-toggle>
      <span>
        <strong>${escapeHtml(titleText)}</strong>
        <em>${escapeHtml(hiddenText)}</em>
      </span>
      <b>${escapeHtml(actionText)}</b>
    </button>
  `;
}

function candidateDisplayMemoryKey(strategy = state.strategy) {
  return [
    state.mode,
    state.filter,
    strategy,
    state.query.trim().toLowerCase()
  ].join("|");
}

function cleanupCandidateDisplayMemory(now = Date.now()) {
  Object.entries(state.candidateDisplayMemory || {}).forEach(([key, value]) => {
    const memory = value && typeof value === "object" ? value : {};
    Object.entries(memory).forEach(([symbol, lastSeenAt]) => {
      if (now - Number(lastSeenAt || 0) > CANDIDATE_DISPLAY_STICKY_MS) {
        delete memory[symbol];
      }
    });
    if (!Object.keys(memory).length) {
      delete state.candidateDisplayMemory[key];
    }
  });
}

function rememberVisibleCandidates(strategy, candidates = []) {
  if (!Array.isArray(candidates) || !candidates.length || strategy === "all") {
    cleanupCandidateDisplayMemory();
    return;
  }
  const now = Date.now();
  const key = candidateDisplayMemoryKey(strategy);
  const memory = state.candidateDisplayMemory[key] ?? {};
  candidates.forEach((item) => {
    if (item?.symbol) memory[item.symbol] = now;
  });
  state.candidateDisplayMemory[key] = memory;
  cleanupCandidateDisplayMemory(now);
}

function retainedVisibleCandidates(baseCandidates = [], actualCandidates = [], strategy = state.strategy) {
  if (strategy === "all") return [];
  const key = candidateDisplayMemoryKey(strategy);
  const memory = state.candidateDisplayMemory[key];
  if (!memory || typeof memory !== "object") return [];
  const now = Date.now();
  const actualSymbols = new Set(actualCandidates.map((item) => item?.symbol).filter(Boolean));
  const bySymbol = new Map(baseCandidates.map((item) => [item.symbol, item]));
  return Object.entries(memory)
    .filter(([, lastSeenAt]) => now - Number(lastSeenAt || 0) <= CANDIDATE_DISPLAY_STICKY_MS)
    .map(([symbol]) => {
      if (actualSymbols.has(symbol)) return null;
      const item = bySymbol.get(symbol);
      if (!item) return null;
      if (strategy !== "exclude" && isExcludeCandidate(item)) return null;
      return {
        ...item,
        displayRetained: true
      };
    })
    .filter(Boolean);
}

function selectionLockedByLookup() {
  return Boolean(state.selectedLookup?.symbol && state.selectedLookup.symbol === state.selectedSymbol);
}

function selectionFromCandidates(candidates = []) {
  if (!Array.isArray(candidates) || !candidates.length) return null;
  if (state.selectedSymbol) {
    const current = candidates.find((item) => item.symbol === state.selectedSymbol);
    if (current) return current;
  }
  return candidates[0] || null;
}

function syncSelectedToVisibleCandidates(candidates = filteredCandidates()) {
  if (selectionLockedByLookup()) return false;
  const next = selectionFromCandidates(candidates);
  const nextSymbol = next?.symbol ?? null;
  if (state.selectedSymbol === nextSymbol) return false;
  state.selectedSymbol = nextSymbol;
  return true;
}

function baseFilteredCandidates() {
  const candidates = state.dashboard?.candidates ?? [];
  return candidates.filter((item) => {
    const matchesFilter =
      state.filter === "all" ||
      item.category === state.filter ||
      (state.filter === "watched" && item.isWatched);
    const query = state.query.trim().toLowerCase();
    const matchesQuery =
      !query ||
      item.name.toLowerCase().includes(query) ||
      item.symbol.toLowerCase().includes(query);
    return matchesFilter && matchesQuery;
  });
}

function applyStrategyFilter(candidates = []) {
  return candidatesForStrategy(candidates, state.strategy);
}

function candidatesForStrategy(candidates = [], strategy = "all") {
  if (strategy === "all") return candidates;
  if (strategy === "core") return candidates.filter(isCoreCandidate);
  if (strategy === "review") return candidates.filter(isReviewCandidate);
  if (strategy === "wait") return candidates.filter(isWaitBucketCandidate);
  if (strategy === "pullback") return candidates.filter(isPullbackCandidate);
  if (strategy === "hidden") return candidates.filter(isHiddenOpportunity);
  if (strategy === "momentum") return candidates.filter(hasMomentumSignal);
  if (strategy === "holding") return candidates.filter(isHoldingCandidate);
  if (strategy === "exclude") return candidates.filter(isExcludeCandidate);
  if (strategy === "action") return candidates.filter(isActionCandidate);
  return candidates;
}

function resolveCandidateStrategy(candidates = [], preferred = "core") {
  if (!Array.isArray(candidates) || !candidates.length) {
    return { strategy: preferred || "all", candidates: [] };
  }
  const preferredCandidates = candidatesForStrategy(candidates, preferred);
  if (preferredCandidates.length || preferred === "all") {
    return { strategy: preferred, candidates: preferredCandidates };
  }
  const fallbackOrder = ["core", "action", "review", "wait", "pullback", "hidden", "momentum", "holding"];
  for (const strategy of fallbackOrder) {
    if (strategy === preferred) continue;
    const matched = candidatesForStrategy(candidates, strategy);
    if (matched.length) {
      return { strategy, candidates: matched };
    }
  }
  return { strategy: "all", candidates };
}

function compressionForDisplay(item) {
  const compression = item?.candidateCompression ?? {};
  return {
    tier: compression.tier || "wait",
    label: compression.label || "대기",
    rank: Number(compression.rank ?? 0),
    score: Number(compression.score ?? 0),
    reason: compression.reason || "가격, 뉴스, 수급 조건을 추가 확인합니다."
  };
}

function isCoreCandidate(item) {
  return compressionForDisplay(item).tier === "core";
}

function isReviewCandidate(item) {
  return compressionForDisplay(item).tier === "review";
}

function isWaitBucketCandidate(item) {
  if (isActionCandidate(item) || isHoldingCandidate(item) || isExcludeCandidate(item) || isCoreCandidate(item)) return false;
  return (
    isReviewCandidate(item) ||
    isPullbackCandidate(item) ||
    isHiddenOpportunity(item) ||
    hasMomentumSignal(item) ||
    tradePlan(item).tone === "wait"
  );
}

function isHiddenOpportunity(item) {
  const group = decisionGroupForDisplay(item);
  return (
    group.key === "hidden" ||
    item?.discoveryTier === "hidden" ||
    item?.opportunityType === "hidden" ||
    Number(item?.hiddenOpportunity?.score ?? 0) >= 8
  );
}

function hasMomentumSignal(item) {
  const group = decisionGroupForDisplay(item);
  const score = item?.score ?? {};
  const discoveryNews = Number(item?.discovery?.newsItems ?? item?.liveNews?.items?.length ?? 0);
  const change = parseDisplayPercent(item?.change);
  return (
    group.key === "momentum" ||
    discoveryNews > 0 ||
    Number(score.news ?? 0) >= 12 ||
    Number(score.price ?? 0) >= 12 ||
    Number(score.volume ?? 0) >= 12 ||
    Number(score.opportunity ?? 0) >= 10 ||
    (change != null && change > 0.8)
  );
}

function discoveryQualityLabel(item) {
  const tier = item?.discovery?.qualityTier;
  if (tier === "primary") return "1차";
  if (tier === "reserve") return "보조";
  if (tier === "rejected") return "제외";
  return "";
}

function discoveryEvidenceForDisplay(item) {
  const evidence = item?.discovery?.evidenceProfile ?? {};
  return {
    grade: evidence.grade || item?.discovery?.evidenceGrade || "",
    label: evidence.label || item?.discovery?.evidenceLabel || "",
    score: Number(evidence.score ?? item?.discovery?.evidenceScore ?? 0),
    reasons: Array.isArray(evidence.reasons) ? evidence.reasons : item?.discovery?.evidenceReasons ?? [],
    blockers: Array.isArray(evidence.blockers) ? evidence.blockers : item?.discovery?.evidenceBlockers ?? [],
    impactTypes: Array.isArray(evidence.impactTypes) ? evidence.impactTypes : item?.discovery?.newsImpactTypes ?? [],
    newsItems: Number(evidence.newsItems ?? item?.discovery?.newsItems ?? 0),
    filteredNewsItems: Number(evidence.filteredNewsItems ?? item?.discovery?.filteredNewsItems ?? 0),
    averageRelevance: Number(evidence.averageRelevance ?? item?.discovery?.newsRelevanceAverage ?? 0)
  };
}

function signalValidationForDisplay(item) {
  const validation = item?.signalValidation ?? {};
  return {
    key: validation.key || "insufficient",
    label: validation.label || "근거·반응 부족",
    score: Number(validation.score ?? 0),
    entryReady: Boolean(validation.entryReady),
    evidenceScore: Number(validation.evidenceScore ?? item?.discovery?.evidenceScore ?? 0),
    reactionScore: Number(validation.reactionScore ?? item?.priceReaction?.score ?? 0),
    reactionGate: validation.reactionGate || item?.priceReaction?.reactionGate || item?.finalDecision?.reactionGate || "",
    confidenceScore: Number(validation.confidenceScore ?? item?.dataConfidence?.score ?? 0),
    reasons: Array.isArray(validation.reasons) ? validation.reasons : [],
    blockers: Array.isArray(validation.blockers) ? validation.blockers : [],
    reactionBlockers: Array.isArray(item?.priceReaction?.blockers) ? item.priceReaction.blockers : []
  };
}

function evaluationModeForDisplay(item) {
  const itemMode = item?.evaluationMode ?? {};
  const decisionMode = item?.finalDecision?.evaluationMode ?? {};
  const decisionIsBaseline =
    decisionMode?.key === "closed_baseline" ||
    decisionMode?.status === "baseline" ||
    (state.mode === "close" && decisionMode?.priceOk && decisionMode?.changeOk);
  const mode = decisionIsBaseline ? decisionMode : (itemMode?.key || itemMode?.status ? itemMode : decisionMode);
  const readiness = item?.priceReadiness ?? {};
  const key = mode.key || readiness.key || "collecting";
  const blockerReasons = Array.isArray(mode.blockerReasons)
    ? mode.blockerReasons
    : Array.isArray(readiness.blockerReasons)
      ? readiness.blockerReasons
      : [];
  const primaryBlocker = mode.primaryBlocker || readiness.primaryBlocker || blockerReasons[0] || "";
  const fallback = {
    entry_ready: ["실시간 평가 가능", "ready", "서버가 가격·등락률·거래 반응을 확보했습니다."],
    closed_baseline: ["장마감 기준가", "baseline", "장마감 기준가와 전일 등락률 기준으로 다음 거래일 후보를 평가합니다. 장 시작 후 가격·거래량 반응을 확인합니다."],
    display_ready: ["후보 분석 가능", "analysis", "가격과 재료는 확보됐지만 거래 반응 보강 전까지 진입 후보로 올리지 않습니다."],
    collecting_change: ["등락률 수집 중", "collecting", "현재가는 있으나 등락률 기준을 서버가 보강 중입니다."],
    change_wait: ["등락률 수집 중", "collecting", "현재가는 있으나 등락률 기준을 서버가 보강 중입니다."],
    collecting_price: ["가격 수집 중", "collecting", "토스 가격 또는 장마감 기준가를 서버가 보강 중입니다."],
    price_wait: ["가격 수집 중", "collecting", "토스 가격 또는 장마감 기준가를 서버가 보강 중입니다."],
    collecting: ["서버 수집 중", "collecting", "필수 데이터가 부족해 서버 보강 후 평가합니다."],
    unavailable: ["평가 불가", "blocked", "필수 데이터가 부족해 현재 후보 평가는 참고용입니다."]
  }[key] || ["서버 수집 중", "collecting", "필수 데이터가 부족해 서버 보강 후 평가합니다."];
  let message = mode.message || readiness.message || fallback[2];
  if (blockerReasons.length && ["collecting", "blocked", "analysis"].includes(mode.status || fallback[1])) {
    message = `${blockerReasons.slice(0, 4).join(", ")} 보강 후 평가합니다.`;
  }
  return {
    key,
    label: fallback[1] === "baseline" ? (mode.label || readiness.label || fallback[0]) : (primaryBlocker || mode.label || readiness.label || fallback[0]),
    status: mode.status || fallback[1],
    message,
    tradeEligible: Boolean(mode.tradeEligible || readiness.entryReady),
    rankEligible: Boolean(mode.rankEligible || readiness.displayReady),
    missing: Array.isArray(mode.missing) ? mode.missing : Array.isArray(readiness.missing) ? readiness.missing : [],
    blockerReasons,
    primaryBlocker
  };
}

function reactionGateLabel(value) {
  if (value === "confirmed") return "반응 확인";
  if (value === "watch") return "관찰 지속";
  if (value === "wait") return "반응 보강";
  if (value === "blocked") return "반응 차단";
  return "가격 반응";
}

function reactionBadgeText(reaction) {
  const score = reaction?.score != null ? ` ${reaction.score}` : "";
  return `${reaction?.decision?.label || reaction.decisionLabel || reactionGateLabel(reaction?.reactionGate)}${score}`;
}

function priceFreshnessInfo(item) {
  const livePrice = item?.livePrice ?? {};
  const freshness = livePrice.freshness ?? {};
  const timestamp = freshness.timestamp || livePrice.timestamp || livePrice.updatedAt || state.livePrice.updatedAt || "";
  const source = livePrice.source || "";
  const basis = livePrice.basis || item?.priceBasis?.basis || item?.priceBasis?.key || item?.priceReadiness?.key || "";
  const ageMs = timestamp ? Date.now() - Date.parse(timestamp) : NaN;
  const ageSeconds = Number.isFinite(ageMs) ? Math.max(0, Math.round(ageMs / 1000)) : Number(freshness.ageSeconds ?? NaN);
  const freshSeconds = Number(freshness.freshSeconds ?? 30);
  const delayedSeconds = Number(freshness.delayedSeconds ?? 120);
  let status = freshness.status || (source === "toss" ? "unknown" : "snapshot");
  const explicitBaseline =
    basis === "closed_baseline" ||
    item?.evaluationMode?.key === "closed_baseline" ||
    item?.finalDecision?.evaluationMode?.key === "closed_baseline";
  const serverBaseline = status === "closed-baseline" || explicitBaseline || Boolean(freshness.isClosedBaseline || freshness.usableForBaseline && freshness.session?.isClosedOrPreopen);
  const hasDisplayPrice = Boolean(item?.price && item.price !== "-" && !String(item.price).includes("미수신"));
  const hasDisplayChange = parseDisplayPercent(item?.change) != null;
  const closeModeBaseline = state.mode === "close" && hasDisplayPrice && hasDisplayChange && Boolean(freshness.session?.isClosedOrPreopen || status === "snapshot" || source !== "toss");
  if (source === "toss" && !serverBaseline) {
    if (!Number.isFinite(ageSeconds)) status = "unknown";
    else if (ageSeconds <= freshSeconds) status = "live";
    else if (ageSeconds <= delayedSeconds) status = "delayed";
    else status = "stale";
  }
  const ageText = timestamp ? elapsedLabel(timestamp) : "";
  const isFresh = status === "live" && source === "toss";
  const isBaseline = status === "closed-baseline" || serverBaseline || closeModeBaseline;
  const isDelayed = ["delayed", "stale", "unknown"].includes(status) && source === "toss" && !isBaseline;
  const isSnapshot = status === "snapshot" || source !== "toss";
  const fallbackLabel =
    isFresh ? "실시간" :
    isBaseline ? "장마감 기준가" :
    status === "delayed" ? "지연" :
    status === "stale" ? "오래됨" :
    isSnapshot ? "저장값" : "미확인";
  const fallbackMessage =
    isFresh ? "토스 현재가를 실시간 판단에 사용합니다." :
    isBaseline ? (freshness.message || "장마감 기준가와 전일 등락률 기준으로 다음 거래일 후보를 평가합니다. 장 시작 후 가격·거래량 반응을 확인하세요.") :
    status === "delayed" ? "토스 현재가가 지연되어 신규 진입 판단을 보류합니다." :
    status === "stale" ? "토스 현재가가 오래되어 저장 가격처럼만 참고합니다." :
    freshness.message || livePrice.message || "";
  return {
    status,
    label: fallbackLabel,
    source,
    timestamp,
    ageText,
    isFresh,
    isBaseline,
    isDelayed,
    isSnapshot,
    message: fallbackMessage
  };
}

function isClosedBaselineCandidate(item) {
  const freshness = priceFreshnessInfo(item);
  const basis = item?.livePrice?.basis || item?.priceBasis?.basis || item?.priceBasis?.key || "";
  const readiness = item?.priceReadiness ?? {};
  const evaluation = item?.evaluationMode ?? {};
  const decisionEvaluation = item?.finalDecision?.evaluationMode ?? {};
  return Boolean(
    freshness.isBaseline ||
    basis === "closed_baseline" ||
    readiness.key === "closed_baseline" ||
    evaluation.key === "closed_baseline" ||
    evaluation.status === "baseline" ||
    decisionEvaluation.key === "closed_baseline" ||
    decisionEvaluation.status === "baseline"
  );
}

function closedBaselineDecisionLabel(label, fallback = "다음 장 관찰") {
  const text = String(label ?? "").trim();
  if (!text) return fallback;
  if (text.includes("가격 확인") || text.includes("미수신") || text.includes("반응 대기") || text.includes("확인 대기")) {
    return fallback;
  }
  return text;
}

function priceBasisKeyForDisplay(item) {
  const livePrice = item?.livePrice ?? {};
  const priceBasis = item?.priceBasis ?? {};
  const readiness = item?.priceReadiness ?? {};
  const evaluation = item?.evaluationMode ?? {};
  const finalEvaluation = item?.finalDecision?.evaluationMode ?? {};
  return (
    livePrice.basis ||
    priceBasis.basis ||
    priceBasis.key ||
    readiness.basis ||
    readiness.key ||
    evaluation.basis ||
    evaluation.key ||
    finalEvaluation.basis ||
    finalEvaluation.key ||
    ""
  );
}

function basisAwareDecisionLabel(item, label = "", fallback = "데이터 보강 대기") {
  const text = String(label ?? "").trim();
  const basis = priceBasisKeyForDisplay(item);
  const closedBaseline = isClosedBaselineCandidate(item);
  const retained = Boolean(item?.livePrice?.retained || item?.displayRetained);
  const replacement = closedBaseline
    ? "다음 장 관찰"
    : basis === "last_good" || retained
      ? "마지막 정상값 확인"
      : fallback;
  if (!text) return replacement;
  if (text.includes("가격 확인") || text.includes("미수신") || text.includes("반응 대기") || text.includes("확인 대기")) {
    return replacement;
  }
  return text;
}

function basisAwareDecisionSummary(item, summary = "") {
  const text = String(summary ?? "").trim();
  const basis = priceBasisKeyForDisplay(item);
  const closedBaseline = isClosedBaselineCandidate(item);
  const retained = Boolean(item?.livePrice?.retained || item?.displayRetained);
  const fallback = closedBaseline
    ? "장마감 기준가로 다음 거래일 후보를 평가합니다. 장 시작 후 가격·거래량 반응을 확인합니다."
    : basis === "last_good" || retained
      ? "마지막 정상 가격을 유지해 후보를 보존합니다. 다음 수집에서 가격·등락률을 다시 검증합니다."
      : "서버가 DB에 가격·등락률·거래량을 보강한 뒤 판단합니다.";
  if (!text) return fallback;
  if (text.includes("가격 확인 필요") || text.includes("가격확인 필요") || text.includes("미수신") || text.includes("반응대기")) {
    return fallback;
  }
  return text;
}

function livePriceLabel(item) {
  const info = priceFreshnessInfo(item);
  if (info.isFresh) return info.ageText ? `실시간 ${info.ageText}` : "실시간";
  if (info.isBaseline) return info.ageText ? `장마감 ${info.ageText}` : "장마감 기준가";
  if (info.isDelayed) return info.ageText ? `${info.label} ${info.ageText}` : info.label;
  if (info.isSnapshot) return "저장가";
  return "실시간 대기";
}

function dataSourceTone(source, message = "") {
  if (source === "toss") return "ok";
  if (["sample", "stale", "error"].includes(source)) return "warn";
  if (["skipped", "retained"].includes(source)) return "wait";
  if (String(message).includes("응답이 비어")) return "wait";
  return "wait";
}

function fallbackStatusLabel(status, fallback = "대체값") {
  const source = typeof status === "string" ? status : status?.source;
  const message = String(typeof status === "object" ? status?.message ?? status?.detail ?? "" : "");
  if (!source) return fallback;
  if (source === "toss") return "토스 반영";
  if (source === "opendart") return "OpenDART";
  if (source === "naver") return "네이버";
  if (source === "gdelt") return "GDELT";
  if (source === "fx-api" || source === "index-api" || source === "index-api-partial") return "API 반영";
  if (source === "retained") return "직전값 유지";
  if (source === "skipped") return "후보 제한";
  if (source === "stale") return "데이터 오래됨";
  if (source === "lookup") return "검색값";
  if (source === "error") return "오류";
  if (source === "sample") {
    if (message.includes("응답이 비어")) return "보강 대기";
    if (message.includes("환경변수") || message.includes("키")) return "설정 대기";
    if (message.includes("꺼져")) return "라이브 꺼짐";
    if (message.includes("실패")) return "대체값";
    return fallback;
  }
  return fallback;
}

function dataSourceLabel(source, fallback = "대기", message = "") {
  if (source === "toss") return "반영";
  if (source === "stale") return "오래됨";
  if (source === "skipped") return "제한";
  if (source === "retained") return "유지";
  if (source === "sample") return fallbackStatusLabel({ source, message }, "대체값");
  if (source === "lookup") return "검색";
  if (source === "error") return "오류";
  return fallback;
}

function liveDataCoverage(item) {
  const freshness = priceFreshnessInfo(item);
  const candles = item?.liveCandles ?? {};
  const orderbook = item?.liveOrderbook ?? {};
  const trades = item?.liveTrades ?? {};
  const priceTone = freshness.isFresh ? "ok" : freshness.isBaseline || freshness.isDelayed ? "warn" : "wait";
  const retainedPrice = Boolean(item?.livePrice?.retained);
  const candleSource = candles.source || "";
  const orderbookSource = orderbook.source || "";
  const tradesSource = trades.source || "";
  return [
    {
      key: "price",
      label: "가격",
      short: "가",
      tone: priceTone,
      value: retainedPrice ? "직전가" : freshness.isFresh ? "실시간" : freshness.isBaseline ? "장마감" : freshness.label || "대기",
      title: priceMeta(item)
    },
    {
      key: "candles",
      label: "차트",
      short: "차",
      tone: dataSourceTone(candleSource, candles.message),
      value: candleSource === "toss" ? `${candles.count ?? 0}개` : dataSourceLabel(candleSource, "대기", candles.message),
      title: candleSource === "toss"
        ? `토스 일봉 ${candles.count ?? 0}개 반영`
        : candles.message || "토스 차트 반영 대기"
    },
    {
      key: "orderbook",
      label: "호가",
      short: "호",
      tone: dataSourceTone(orderbookSource, orderbook.message),
      value: orderbookSource === "toss" ? orderbook.pressure || "반영" : dataSourceLabel(orderbookSource, "대기", orderbook.message),
      title: orderbookSource === "toss"
        ? `호가 ${orderbook.pressure || "반영"} · 스프레드 ${orderbook.spreadPercent || "-"}`
        : orderbook.message || "토스 호가 반영 대기"
    },
    {
      key: "trades",
      label: "체결",
      short: "체",
      tone: dataSourceTone(tradesSource, trades.message),
      value: tradesSource === "toss" ? trades.pressure || "반영" : dataSourceLabel(tradesSource, "대기", trades.message),
      title: tradesSource === "toss"
        ? `최근 체결 ${trades.pressure || "반영"} · ${trades.biasPercent || "-"}`
        : trades.message || "토스 체결 반영 대기"
    }
  ];
}

function liveDataCoverageChips(item, compact = false) {
  const entries = liveDataCoverage(item);
  const displayEntries = compact
    ? [
        entries.find((entry) => entry.key === "price"),
        ...entries.filter((entry) => entry.key !== "price" && entry.tone === "ok")
      ].filter(Boolean).slice(0, 2)
    : entries;
  return displayEntries
    .map(
      (entry) => `
        <span class="live-data-chip ${escapeHtml(entry.tone)}" title="${escapeHtml(entry.title)}">
          <b>${escapeHtml(compact ? entry.short : entry.label)}</b>
          <em>${escapeHtml(entry.value)}</em>
        </span>
      `
    )
    .join("");
}

function metricLooksReady(value) {
  const text = String(value ?? "").trim();
  return Boolean(text && text !== "-" && !["0", "0건", "없음", "대기"].includes(text));
}

function volumeReactionText(item) {
  const trend = item?.trend ?? {};
  return trend.volumeSpike || trend.dailyVolume || trend.tradePressure || "-";
}

function reactionStageForDisplay(item) {
  const reaction = item?.priceReaction ?? {};
  const decision = reaction.decision ?? {};
  const metrics = reaction.metrics ?? {};
  const evaluation = evaluationModeForDisplay(item);
  const freshness = priceFreshnessInfo(item);
  const closedBaseline = isClosedBaselineCandidate(item);
  const serverCriteria = Array.isArray(reaction.entryCriteria) ? reaction.entryCriteria.filter(Boolean) : [];
  const confirmationCount = Number(metrics.confirmationCount ?? 0);
  const requiredConfirmations = Number(metrics.requiredConfirmations ?? 2);
  const change = parseDisplayPercent(item?.change);
  const hasLivePrice = freshness.isFresh;
  const hasPositivePrice = change != null && change > 0;
  const hasPrice = Boolean(item?.price && item.price !== "-");
  const hasVolume = metricLooksReady(volumeReactionText(item));
  const confirmedFactors = uniqueTexts(metrics.confirmedFactors ?? [], 4);
  const missingFactors = uniqueTexts([...(metrics.missingFactors ?? []), ...(reaction.blockers ?? [])], 4);
  const gate = reaction.reactionGate || "";

  let label = decision.label || reaction.decisionLabel || (closedBaseline ? "다음 장 관찰" : "데이터 보강 대기");
  let tone = decision.tone || "wait";
  let summary = decision.summary || reaction.nextCheck || "뉴스 재료는 있으나 실시간 가격·거래량이 아직 진입 조건을 통과하지 않았습니다.";
  const isBaseline = closedBaseline || evaluation.status === "baseline";
  if (isBaseline) {
    label = closedBaselineDecisionLabel(label);
    tone = "watch";
    summary = decision.summary || reaction.nextCheck || evaluation.message || freshness.message || "장마감 기준가로 다음 거래일 우선 관찰 후보를 평가합니다. 장 시작 후 가격·거래량 반응을 확인합니다.";
  } else if (evaluation.status === "collecting" || evaluation.status === "blocked") {
    label = evaluation.label;
    tone = "wait";
    summary = evaluation.message;
  }
  if (decision.key && !["collecting", "blocked", "baseline"].includes(evaluation.status)) {
    if (isBaseline) {
      label = closedBaselineDecisionLabel(label);
      tone = "watch";
    } else if (decision.key === "blocked") tone = "risk";
    else if (decision.key === "confirmed") tone = "buy";
    else if (decision.key === "watch") tone = "watch";
    else tone = "wait";
  } else if (!isBaseline && gate === "blocked") {
    label = "오늘 제외";
    tone = "risk";
    summary = reaction.nextCheck || "재료 대비 가격 또는 거래량 반응이 부정적이라 신규 진입을 막습니다.";
  } else if (!isBaseline && (reaction.entryReady || reaction.supportsEntry || (gate === "confirmed" && !reaction.entryBlock))) {
    label = "가격 반응 확인";
    tone = "buy";
    summary = reaction.nextCheck || "뉴스 재료와 가격 움직임이 같은 방향으로 확인됩니다.";
  } else if (!isBaseline && (reaction.entryBlock || gate === "wait")) {
    label = "데이터 보강 대기";
    tone = "wait";
    summary = reaction.nextCheck || "서버 DB의 가격·거래량·수급 근거가 충분히 채워진 뒤 판단합니다.";
  } else if (!isBaseline && gate === "watch") {
    label = "관찰 유지";
    summary = reaction.nextCheck || "일부 반응은 있으나 진입 판단 전 가격 흐름을 더 확인합니다.";
  } else if (!isBaseline && hasPositivePrice && hasVolume) {
    label = "반응 관찰";
    summary = reaction.nextCheck || "가격과 거래량 단서는 있으나 확인 개수가 아직 부족합니다.";
  }

  const checks = serverCriteria.length
    ? serverCriteria.map((criterion) => [
        criterion.label || criterion.key || "확인",
        Boolean(criterion.ok),
        criterion.value || (criterion.ok ? "확인" : "대기")
      ])
    : [
        ["가격 기준", hasLivePrice || freshness.isBaseline || freshness.isSnapshot, hasLivePrice ? livePriceLabel(item) : freshness.isBaseline ? "장마감 기준가" : "DB 가격 보강"],
        ["가격 방향", hasPositivePrice, displayCandidateChangeText(item)],
        ["거래 반응", hasVolume, volumeReactionText(item)],
        ["확인 조건", confirmationCount >= requiredConfirmations, `${confirmationCount}/${requiredConfirmations}`]
      ];
  return {
    label,
    tone,
    summary,
    checks,
    confirmedFactors,
    missingFactors,
    hasPrice
  };
}

function primaryDecisionForDisplay(item, plan = tradePlan(item)) {
  const decision = item?.finalDecision ?? {};
  const gate = item?.qualityGate ?? {};
  const reaction = item?.priceReaction ?? {};
  const reactionDecision = reaction.decision ?? {};
  const freshness = priceFreshnessInfo(item);
  const evaluation = evaluationModeForDisplay(item);
  const closedBaseline = isClosedBaselineCandidate(item);
  if (plan.tone === "sell") {
    return { key: "sell", label: "분할매도 점검", detail: plan.summary || "보유 수익을 점검합니다." };
  }
  if (plan.tone === "risk" || decision.actionKey === "exclude" || gate.key === "exclude") {
    return { key: "avoid", label: "오늘 제외", detail: plan.summary || "신규 진입하지 않습니다." };
  }
  if (!closedBaseline && reactionDecision.key === "blocked") {
    return { key: "avoid", label: reactionDecision.action || "오늘 제외", detail: reactionDecision.summary || "가격 반응이 차단되어 신규 진입하지 않습니다." };
  }
  if (!closedBaseline && (evaluation.status === "collecting" || evaluation.status === "blocked")) {
    return { key: "wait", label: evaluation.label, detail: evaluation.message };
  }
  if (closedBaseline && !selectedHoldingFor(item)) {
    const label = basisAwareDecisionLabel(item, decision.action || reactionDecision.action || reactionDecision.label || reaction.decisionLabel, "다음 장 관찰");
    return {
      key: "wait",
      label,
      detail: decision.summary || reactionDecision.summary || evaluation.message || freshness.message || "장마감 기준가 분석입니다. 다음 장 시작 후 가격·거래량 반응을 확인하세요."
    };
  }
  if (evaluation.status === "analysis" && decision.actionKey === "verify") {
    return { key: "wait", label: evaluation.label, detail: evaluation.message };
  }
  if (["wait", "watch"].includes(reactionDecision.key) && !reactionDecision.tradeAllowed && (decision.actionKey === "buy" || gate.key === "actionable")) {
    return { key: "wait", label: reactionDecision.label || "반응 보강", detail: reactionDecision.summary || "가격·거래량 반응을 더 확인합니다." };
  }
  if (decision.actionKey === "buy" || decision.actionKey === "add" || gate.key === "actionable") {
    if (freshness.isBaseline) {
      return { key: "wait", label: "장마감 기준가", detail: freshness.message || "장마감 기준가 분석입니다. 개장 후 가격·거래량 반응을 확인하세요." };
    }
    if (!freshness.isFresh) {
      return { key: "wait", label: "가격 보강 대기", detail: freshness.message || "서버가 DB 가격 기준을 보강한 뒤 진입 여부를 판단합니다." };
    }
    return { key: "buy", label: "매수 가능", detail: plan.summary || "조건 충족 시 관찰 매수 후보입니다." };
  }
  if (decision.actionKey === "hold" || decision.portfolioAware || selectedHoldingFor(item)) {
    return { key: "hold", label: "보유 대응", detail: plan.summary || "보유 종목 기준으로 판단합니다." };
  }
  if (decision.actionKey === "pullback" || String(plan.action).includes("눌림")) {
    return { key: "wait", label: "눌림 대기", detail: plan.summary || "가격 조정을 기다립니다." };
  }
  if (reaction.reactionGate === "wait" || reaction.entryBlock || decision.actionKey === "verify") {
    const stage = reactionStageForDisplay(item);
    return { key: "wait", label: stage.label, detail: stage.summary };
  }
  if (gate.key === "watch" || decision.actionKey === "watch" || plan.tone === "wait") {
    return { key: "wait", label: "진입 보류", detail: plan.summary || "현재가와 거래 반응을 더 확인합니다." };
  }
  return { key: "check", label: "확인 중", detail: plan.summary || "추가 확인이 필요합니다." };
}

function candidatePoolStateForDisplay(item) {
  const pool = item?.candidatePool ?? {};
  const memory = item?.discovery?.poolMemory ?? {};
  const fallbackByCompression = {
    core: ["entry_candidate", "진입 후보"],
    review: ["validating", "관찰 중"],
    wait: ["watching", "관찰 중"],
    portfolio: ["portfolio", "보유 판단"],
    exclude: ["excluded", "제외"]
  };
  const compression = compressionForDisplay(item);
  const [fallbackKey, fallbackLabel] = fallbackByCompression[compression.tier] ?? ["collected", "수집됨"];
  return {
    key: pool.stateKey || fallbackKey,
    label: pool.stateLabel || fallbackLabel,
    reason: pool.stateReason || compression.reason || "봇이 후보 풀에서 계속 관찰합니다.",
    observations: Number(pool.observations ?? 0),
    selectedCount: Number(pool.selectedCount ?? 0),
    stateChangedAt: pool.stateChangedAt || "",
    stateChangeCount: Number(pool.stateChangeCount ?? 0),
    promotionCount: Number(pool.promotionCount ?? 0),
    demotionCount: Number(pool.demotionCount ?? 0),
    softDemotionCount: Number(pool.softDemotionCount ?? 0),
    peakScore: Number(pool.peakScore ?? 0),
    peakReadiness: Number(pool.peakReadiness ?? 0),
    peakConfidenceScore: Number(pool.peakConfidenceScore ?? 0),
    peakReactionScore: Number(pool.peakReactionScore ?? 0),
    peakEvidenceScore: Number(pool.peakEvidenceScore ?? 0),
    monitorScore: Number(pool.monitorScore ?? memory.monitorScore ?? 0),
    monitorLabel: pool.monitorLabel || memory.monitorLabel || "",
    monitorReason: pool.monitorReason || memory.monitorReason || "",
    scoreDelta: Number(pool.scoreDelta ?? 0),
    momentumLabel: pool.momentumLabel || "",
    performanceMeasuredCount: Number(pool.performanceMeasuredCount ?? memory.performanceMeasuredCount ?? 0),
    performancePositiveCount: Number(pool.performancePositiveCount ?? memory.performancePositiveCount ?? 0),
    performanceNegativeCount: Number(pool.performanceNegativeCount ?? memory.performanceNegativeCount ?? 0),
    performanceHitRate: pool.performanceHitRate || memory.performanceHitRate || "",
    performanceAverageChange: pool.performanceAverageChange || memory.performanceAverageChange || "",
    performanceLatestChange: pool.performanceLatestChange || memory.performanceLatestChange || "",
    performanceLatestOutcome: pool.performanceLatestOutcome || memory.performanceLatestOutcome || "",
    performanceLatestAt: pool.performanceLatestAt || memory.performanceLatestAt || "",
    retained: Boolean(item?.discovery?.poolRetained || memory.retained),
    retainScore: Number(memory.score ?? item?.discovery?.poolScore ?? 0),
    retainReason: memory.reason || "",
    retainStateLabel: memory.stateLabel || "",
    transitionHistory: Array.isArray(pool.transitionHistory) ? pool.transitionHistory : [],
    firstSeenAt: pool.firstSeenAt || "",
    lastSeenAt: pool.lastSeenAt || "",
    lastSelectedAt: pool.lastSelectedAt || ""
  };
}

function isActionCandidate(item) {
  const gate = item?.qualityGate;
  if (gate?.key === "actionable") return true;
  if (["defer", "exclude"].includes(gate?.key)) return false;
  const group = decisionGroupForDisplay(item);
  const plan = tradePlan(item);
  const score = Number(item?.totalScore ?? 0);
  const readiness = Number(item?.triggerReadiness ?? 0);
  const risk = Number(item?.score?.riskPenalty ?? 0);
  const heat = Number(item?.score?.heatPenalty ?? 0);
  if (plan.tone === "risk") return false;
  if (!plan.hasPrice || plan.tone !== "buy") return false;
  if (group.key === "action" && risk < 18 && heat < 10) return true;
  return score >= 78 && readiness >= 74 && risk < 18 && heat < 10;
}

function isPullbackCandidate(item) {
  const group = decisionGroupForDisplay(item);
  const plan = tradePlan(item);
  const change = parseDisplayPercent(item?.change);
  if (!plan.hasPrice || plan.tone === "risk") return false;
  return (
    plan.action.includes("눌림") ||
    plan.action.includes("반등") ||
    (plan.tone === "wait" && group.key === "momentum" && change != null && change >= 1.2)
  );
}

function isHoldingCandidate(item) {
  const group = decisionGroupForDisplay(item);
  return group.key === "holding" || Boolean(selectedHoldingFor(item));
}

function isExcludeCandidate(item) {
  if (item?.qualityGate?.key === "exclude") return true;
  const group = decisionGroupForDisplay(item);
  const plan = tradePlan(item);
  return group.key === "exclude" || plan.tone === "risk" || plan.action.includes("제외");
}

function actionPriority(item) {
  const group = decisionGroupForDisplay(item);
  const plan = tradePlan(item);
  if (plan.tone === "buy") return 0;
  if (plan.tone === "sell") return 1;
  if (group.key === "holding") return 1;
  if (Number.isFinite(Number(group.priority))) return Number(group.priority) + 1;
  if (plan.action.includes("보유") || plan.action.includes("반등")) return 2;
  if (plan.tone === "wait") return 3;
  if (plan.tone === "risk") return 4;
  return 5;
}

function strategyPriority(item, strategy) {
  if (strategy === "core" && isCoreCandidate(item)) return 0;
  if (strategy === "review" && isReviewCandidate(item)) return 0;
  if (strategy === "wait" && isWaitBucketCandidate(item)) return 0;
  if (strategy === "hidden" && isHiddenOpportunity(item)) return 0;
  if (strategy === "momentum" && hasMomentumSignal(item)) return 0;
  if (strategy === "action" && isActionCandidate(item)) return 0;
  if (strategy === "pullback" && isPullbackCandidate(item)) return 0;
  if (strategy === "holding" && isHoldingCandidate(item)) return 0;
  if (strategy === "exclude" && isExcludeCandidate(item)) return 0;
  return 1;
}

function sortCandidatesForStrategy(candidates = [], strategy = "action") {
  return [...candidates].sort((a, b) => {
    const strategyDiff = strategyPriority(a, strategy) - strategyPriority(b, strategy);
    if (strategyDiff !== 0) return strategyDiff;
    return compareCandidatesForAction(a, b);
  });
}

function compareCandidatesForAction(a, b) {
  const readinessDiff = dataReadinessPriority(a) - dataReadinessPriority(b);
  if (readinessDiff !== 0) return readinessDiff;
  const compressionDiff = compressionPriority(a) - compressionPriority(b);
  if (compressionDiff !== 0) return compressionDiff;
  const priorityDiff = actionPriority(a) - actionPriority(b);
  if (priorityDiff !== 0) return priorityDiff;
  const readyDiff = Number(b.triggerReadiness ?? 0) - Number(a.triggerReadiness ?? 0);
  if (readyDiff !== 0) return readyDiff;
  const decisionDiff = Number(decisionGroupForDisplay(b).score ?? 0) - Number(decisionGroupForDisplay(a).score ?? 0);
  if (decisionDiff !== 0) return decisionDiff;
  return Number(b.totalScore ?? 0) - Number(a.totalScore ?? 0);
}

function dataReadinessPriority(item) {
  const evaluation = evaluationModeForDisplay(item);
  const key = evaluation.key || "collecting";
  let priority = {
    entry_ready: 0,
    closed_baseline: state.mode === "close" ? 1 : 3,
    display_ready: state.mode === "close" ? 2 : 2,
    collecting_change: 5,
    change_wait: 5,
    collecting_price: 7,
    price_wait: 7,
    collecting: 8,
    unavailable: 10
  }[key] ?? 8;
  const blockers = Array.isArray(evaluation.blockerReasons) ? evaluation.blockerReasons.join(" ") : "";
  if (blockers.includes("가격 미수신") || blockers.includes("가격 저장값 없음") || blockers.includes("가격 보강")) priority += 3;
  if (blockers.includes("등락률")) priority += 1;
  if (blockers.includes("응답 없음")) priority += 1;
  if (blockers.includes("후보 제한")) priority += 1;
  if (blockers.includes("장 시간 외") && state.mode === "close") {
    priority = Math.max(0, priority - 1);
  }
  return priority;
}

function compressionPriority(item) {
  const tier = compressionForDisplay(item).tier;
  return {
    core: 0,
    review: 1,
    portfolio: 2,
    wait: 3,
    exclude: 4
  }[tier] ?? 3;
}

function sortCandidatesForAction(candidates = []) {
  return [...candidates].sort(compareCandidatesForAction);
}

function bestCandidate(candidates = []) {
  return sortCandidatesForAction(candidates)[0] ?? null;
}

function candidateActionSummary(candidates = []) {
  return candidates.reduce(
    (summary, item) => {
      const plan = tradePlan(item);
      if (isActionCandidate(item)) summary.buy += 1;
      else if (plan.tone === "risk") summary.exclude += 1;
      else summary.wait += 1;
      return summary;
    },
    { buy: 0, wait: 0, exclude: 0 }
  );
}

function candidateStrategyCounts(candidates = []) {
  return {
    core: candidates.filter(isCoreCandidate).length,
    review: candidates.filter(isReviewCandidate).length,
    action: candidates.filter(isActionCandidate).length,
    wait: candidates.filter(isWaitBucketCandidate).length,
    pullback: candidates.filter(isPullbackCandidate).length,
    hidden: candidates.filter(isHiddenOpportunity).length,
    momentum: candidates.filter(hasMomentumSignal).length,
    holding: candidates.filter(isHoldingCandidate).length,
    exclude: candidates.filter(isExcludeCandidate).length,
    all: candidates.length
  };
}

function selectedCandidate() {
  if (selectionLockedByLookup()) {
    return state.selectedLookup;
  }
  const candidates = state.dashboard?.candidates ?? [];
  if (state.selectedSymbol) {
    return candidates.find((item) => item.symbol === state.selectedSymbol) || null;
  }
  return selectionFromCandidates(filteredCandidates());
}

function candidateFromSearchResult(item, options = {}) {
  const analysisLoading = Boolean(options.analysisLoading);
  const analysisError = options.analysisError || "";
  const matchText = stockSearchMatchText(item);
  const tags = uniqueTexts([
    "종목 검색",
    matchText,
    item.market,
    item.securityType,
    item.currency,
    item.status
  ], 5);
  return {
    symbol: item.symbol,
    name: item.name || item.symbol,
    market: item.market || "",
    category: item.category || "domestic",
    price: item.price || "-",
    change: item.change || "",
    updated: item.updated || "직접 조회",
    headline: analysisLoading ? "검색 종목 분석 중" : item.headline || "후보 편입 전 종목 조회",
    verdict: analysisLoading ? "분석 중" : "후보 편입 전",
    stage: "lookup",
    totalScore: 0,
    triggerReadiness: 0,
    preopenPriority: 0,
    score: {},
    tags,
    thesis: analysisLoading
      ? "현재가, 뉴스, 공시, 가격 반응을 연결해 후보 분석 형태로 변환하고 있습니다."
      : analysisError || "오늘 후보로 점수화되기 전의 직접 조회 결과입니다. 뉴스, 공시, 가격 반응을 확인한 뒤 후보 편입 여부를 먼저 판단해야 합니다.",
    why: [
      `${item.name || item.symbol} 기본정보를 조회했습니다.`,
      matchText ? `검색 자동완성 근거: ${matchText}` : "",
      item.price && item.price !== "-" ? `현재가 ${item.price} 기준으로 추가 분석을 시작할 수 있습니다.` : "현재가는 아직 연결되지 않았습니다.",
      "후보 점수화 전에는 신규 매수 판단보다 관찰 목록 편입 여부를 먼저 봅니다."
    ].filter(Boolean),
    entryConditions: [
      "뉴스와 공시 재료가 최근 가격 반응과 같은 방향인지 확인",
      "거래대금과 섹터 흐름이 후보 기준을 충족하는지 확인",
      "손절 기준이 진입가에서 3% 안쪽으로 관리되는 가격대인지 확인"
    ],
    noEntry: [
      "후보 점수와 매수 가격대가 계산되기 전",
      "현재가나 거래량 데이터가 연결되지 않은 상태",
      "뉴스만 있고 실제 수급 반응이 확인되지 않은 경우"
    ],
    stopRules: [
      "후보 편입 후 기준 가격 재이탈",
      "섹터 동반 약세 전환",
      "거래량 없는 상승만 이어지는 경우"
    ],
    trend: {
      newsCount: 0,
      globalNewsCount: null,
      newsSpike: "-",
      volumeSpike: "-",
      dailyVolume: "-",
      tradePressure: "-",
      orderbookPressure: "-",
      spread: "-",
      sentiment: "-"
    },
    sources: [
      {
        title: item.sourceLabel || "종목 기본정보 조회",
        publisher: item.source === "toss" ? "Toss Open API" : "후보 목록",
        time: item.updated || "검색"
      }
    ],
    disclosures: [
      "직접 조회 종목은 아직 뉴스/공시/시세 점수화가 완료되지 않았습니다.",
      "후보 편입 전 매수/매도 판단에는 사용하지 않는 것이 좋습니다."
    ],
    related: [],
    chart: [50, 50, 50, 50, 50, 50],
    livePrice: item.livePrice || { source: "lookup", message: "종목 검색 결과입니다." },
    liveCandles: { source: "lookup" },
    isWatched: Boolean(item.isWatched),
    lookupOnly: true,
    analysisLoading,
    analysisError
  };
}

function tradeActionText(item) {
  return tradePlan(item).action;
}

function tradeActionOk(item) {
  const plan = tradePlan(item);
  return plan.tone === "buy" || (plan.tone === "wait" && plan.hasPrice);
}

function renderTradeDecisionStatus() {
  if (!els.tradeDecisionStatus) return;
  const item = selectedCandidate();
  if (!item) {
    els.tradeDecisionStatus.innerHTML = `
      <div>
        <span>종목 선택</span>
        <strong class="warn">대기</strong>
      </div>
    `;
    return;
  }
  const plan = tradePlan(item);
  const primary = primaryDecisionForDisplay(item, plan);
  const closedBaseline = isClosedBaselineCandidate(item);
  const currentRow = plan.rows.find(([label]) => label === "관찰 매수")?.[1] ?? "-";
  const holdingRow = plan.holding ? `${plan.holding.judgement ?? "보유"} · ${plan.holding.profitLossRate ?? "-"}` : "미보유";
  const rows = [
    ["선택", true, item.name ?? item.symbol ?? "-"],
    ["최종 판단", closedBaseline || primary.key === "buy" || primary.key === "hold" || primary.key === "sell", primary.label],
    ["현재가", plan.hasPrice, `${item.price ?? "-"} ${displayCandidateChangeText(item)}`.trim()],
    ["관찰 매수", plan.tone === "buy", currentRow],
    ["보유", Boolean(plan.holding), holdingRow]
  ];
  setHtmlIfChanged(els.tradeDecisionStatus, rows
    .map(([label, ok, value]) => {
      const tone = ok ? "ok" : "warn";
      return `
        <div>
          <span>${escapeHtml(label)}</span>
          <strong class="${tone}">${escapeHtml(value)}</strong>
        </div>
      `;
    })
    .join(""));
}

function parseTimeMs(value) {
  const time = Date.parse(String(value ?? ""));
  return Number.isFinite(time) ? time : null;
}

function elapsedLabel(value) {
  const time = parseTimeMs(value);
  if (!time) return "-";
  const seconds = Math.max(0, Math.round((Date.now() - time) / 1000));
  if (seconds < 60) return `${seconds}초 전`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}분 전`;
  return `${Math.round(minutes / 60)}시간 전`;
}

function livePriceDiagnostics() {
  const live = state.livePrice ?? {};
  const candidates = state.dashboard?.candidates ?? [];
  const total = candidates.length;
  const freshnessList = candidates.map((item) => priceFreshnessInfo(item));
  const freshCount = freshnessList.filter((item) => item.isFresh).length;
  const delayedCount = freshnessList.filter((item) => item.isDelayed).length;
  const snapshotCount = freshnessList.filter((item) => item.isSnapshot).length;
  const tossCount = freshnessList.filter((item) => item.source === "toss").length;
  const retainedCount = candidates.filter((item) => item?.livePrice?.retained).length;
  const storedFallbackCount = Number(live.storedFallbackCount || state.dashboard?.summary?.livePriceStoredFallbackCount || 0);
  const missingCount = Number(live.missingCount || state.dashboard?.summary?.livePriceMissingCount || 0);
  const tossRequestedCount = Number(live.livePriceTossRequestedCount || state.dashboard?.summary?.livePriceTossRequestedCount || 0);
  const tossReceivedCount = Number(live.livePriceTossReceivedCount || state.dashboard?.summary?.livePriceTossReceivedCount || 0);
  const batchCount = Number(live.livePriceBatchCount || state.dashboard?.summary?.livePriceBatchCount || 0);
  const batchErrorCount = Number(live.livePriceBatchErrorCount || state.dashboard?.summary?.livePriceBatchErrorCount || 0);
  const missingSymbols = Array.isArray(live.livePriceMissingSymbols)
    ? live.livePriceMissingSymbols
    : Array.isArray(state.dashboard?.summary?.livePriceMissingSymbols)
      ? state.dashboard.summary.livePriceMissingSymbols
      : [];
  const coverage = live.tossDataCoverage ?? state.dashboard?.summary?.tossDataCoverage ?? {};
  const coverageTotal = Number(coverage.total ?? total ?? 0);
  const missingCounts = coverage.missingCounts && typeof coverage.missingCounts === "object"
    ? coverage.missingCounts
    : {};
  const coverageMissingReasonText = Object.keys(missingCounts).length
    ? Object.entries(missingCounts)
        .slice(0, 3)
        .map(([key, count]) => `${key} ${count}`)
        .join(" · ")
    : "없음";
  const changedCount = Number(live.changedCount || live.changedSymbols?.length || 0);
  const stableDecisionCount = Number(live.stableDecisionCount || state.dashboard?.summary?.stableDecisionCount || 0);
  const carriedForwardCount = Number(
    live.candidateDataCarriedForwardCount || state.dashboard?.summary?.candidateDataCarriedForwardCount || 0
  );
  const finalDecisionStabilitySeconds = Number(
    live.finalDecisionStabilitySeconds || state.dashboard?.summary?.finalDecisionStabilitySeconds || 0
  );
  const priorityCount = priorityLiveSymbols().length;
  const symbolCount = Number(live.symbolCount || live.symbols?.length || 0);
  const notFreshCount = Math.max(0, total - freshCount);
  const updatedMs = parseTimeMs(live.updatedAt);
  const ageSeconds = updatedMs ? Math.max(0, Math.round((Date.now() - updatedMs) / 1000)) : null;
  const pollSeconds = Number(live.pollSeconds || 10);
  const stale = ageSeconds != null && ageSeconds > Math.max(30, pollSeconds * 3);
  const selectionCycle = live.selectionCycle || state.dashboard?.integrations?.livePrice?.selectionCycle || "";
  const selectionCycleLabel = selectionCycle === "price-only"
    ? "가격만 갱신"
    : selectionCycle === "full-analysis"
      ? "전체 분석"
      : "대기";
  const enabled = Boolean(state.tossStatus?.livePricesEnabled ?? state.dashboard?.integrations?.toss?.config?.readyForMarketData ?? true);
  let label = "대기";
  let ok = false;
  if (!enabled) {
    label = "꺼짐";
  } else if (live.loading) {
    label = "갱신 중";
  } else if (live.error) {
    label = "갱신 실패";
  } else if (updatedMs && stale) {
    label = "지연";
  } else if (updatedMs && freshCount > 0) {
    label = "정상";
    ok = true;
  } else if (updatedMs && tossCount > 0) {
    label = "지연 반영";
  } else if (updatedMs) {
    label = "저장값";
  }
  return {
    enabled,
    ok,
    stale,
    label,
    freshCount,
    delayedCount,
    snapshotCount,
    tossCount,
    retainedCount,
    storedFallbackCount,
    missingCount,
    tossRequestedCount,
    tossReceivedCount,
    coverage,
    coverageTotal,
    coverageMissingReasonText,
    batchCount,
    batchErrorCount,
    missingSymbols,
    changedCount,
    stableDecisionCount,
    carriedForwardCount,
    finalDecisionStabilitySeconds,
    total,
    priorityCount,
    notFreshCount,
    pollSeconds,
    symbolCount,
    selectionCycle,
    selectionCycleLabel,
    updatedAt: live.updatedAt,
    attemptAt: live.attemptAt,
    message: live.error ? live.message || live.error : live.message || "",
    source: live.source || state.dashboard?.integrations?.livePrice?.source || "-"
  };
}

function renderLivePriceStatus() {
  if (!els.livePriceStatus) return;
  const diag = livePriceDiagnostics();
  const rows = [
    ["상태", diag.ok, diag.label],
    ["우선 포함", true, diag.priorityCount ? `보유·관심 ${diag.priorityCount}개` : "없음"],
    ["요청 대상", diag.symbolCount >= diag.total && diag.total > 0, diag.symbolCount ? `${diag.symbolCount}개` : "대기"],
    [
      "토스 수신",
      diag.tossRequestedCount === 0 || diag.tossReceivedCount >= Math.min(diag.tossRequestedCount, diag.symbolCount || diag.tossRequestedCount),
      diag.tossRequestedCount ? `${diag.tossReceivedCount}/${diag.tossRequestedCount}` : "-"
    ],
    ["배치 상태", diag.batchErrorCount === 0, diag.batchCount ? `${diag.batchCount}회 · 오류 ${diag.batchErrorCount}` : "-"],
    [
      "가격 기준",
      diag.coverageTotal > 0 && Number(diag.coverage.priceBasisCount ?? 0) >= diag.coverageTotal,
      `${Number(diag.coverage.priceBasisCount ?? 0)}/${diag.coverageTotal || 0}`
    ],
    [
      "등락률",
      diag.coverageTotal > 0 && Number(diag.coverage.changeCount ?? 0) >= diag.coverageTotal,
      `${Number(diag.coverage.changeCount ?? 0)}/${diag.coverageTotal || 0}`
    ],
    [
      "차트",
      diag.coverageTotal > 0 && Number(diag.coverage.chartCount ?? 0) >= diag.coverageTotal,
      `${Number(diag.coverage.chartCount ?? 0)}/${diag.coverageTotal || 0}`
    ],
    [
      "호가",
      diag.coverageTotal > 0 && Number(diag.coverage.orderbookCount ?? 0) >= diag.coverageTotal,
      `${Number(diag.coverage.orderbookCount ?? 0)}/${diag.coverageTotal || 0}`
    ],
    [
      "체결",
      diag.coverageTotal > 0 && Number(diag.coverage.tradeCount ?? 0) >= diag.coverageTotal,
      `${Number(diag.coverage.tradeCount ?? 0)}/${diag.coverageTotal || 0}`
    ],
    [
      "진입 데이터",
      diag.coverageTotal > 0 && Number(diag.coverage.entryReadyCount ?? 0) > 0,
      `${Number(diag.coverage.entryReadyCount ?? 0)}/${diag.coverageTotal || 0}`
    ],
    ["실시간 반영", diag.freshCount > 0, `${diag.freshCount}/${diag.total || 0}`],
    ["미반영/지연", diag.notFreshCount === 0, `${diag.notFreshCount}/${diag.total || 0}`],
    ["저장값 복구", diag.storedFallbackCount === 0, diag.storedFallbackCount ? `${diag.storedFallbackCount}개` : "없음"],
    ["최종 보강", diag.missingCount === 0, diag.missingCount ? `${diag.missingCount}개` : "없음"],
    ["직전가 유지", diag.retainedCount === 0, diag.retainedCount ? `${diag.retainedCount}개` : "없음"],
    ["DB 보강", true, diag.carriedForwardCount ? `${diag.carriedForwardCount}개 유지` : "없음"],
    ["부분 갱신", true, diag.changedCount ? `${diag.changedCount}개 변경` : "변경 없음"],
    ["갱신 범위", true, diag.selectionCycleLabel],
    [
      "판단 유지",
      true,
      diag.stableDecisionCount
        ? `${diag.stableDecisionCount}개 · ${diag.finalDecisionStabilitySeconds || 120}초`
        : "없음"
    ],
    ["최근 갱신", Boolean(diag.updatedAt && !diag.stale), diag.updatedAt ? elapsedLabel(diag.updatedAt) : "대기"],
    ["갱신 간격", diag.pollSeconds > 0, `${diag.pollSeconds}초`],
    ["최근 시도", Boolean(diag.attemptAt), diag.attemptAt ? elapsedLabel(diag.attemptAt) : "-"],
    [
      "누락 심볼",
      !diag.missingSymbols.length,
      diag.missingSymbols.length ? shortText(diag.missingSymbols.slice(0, 5).join(", "), 32) : "없음"
    ],
    ["부족 원인", diag.coverageMissingReasonText === "없음", diag.coverageMissingReasonText],
    ["메시지", !diag.message || diag.ok, diag.message || diag.source]
  ];
  setHtmlIfChanged(els.livePriceStatus, rows
    .map(([label, ok, value]) => {
      const tone = ok ? "ok" : "warn";
      return `
        <div>
          <span>${escapeHtml(label)}</span>
          <strong class="${tone}">${escapeHtml(value)}</strong>
        </div>
      `;
    })
    .join(""));
}

function renderCandidatePoolStatus() {
  if (!els.candidatePoolStatus) return;
  const summary = state.dashboard?.summary ?? {};
  const pool = state.dashboard?.integrations?.candidatePool ?? {};
  const counts = summary.candidatePoolStatusCounts ?? pool.statusCounts ?? {};
  const top = Array.isArray(summary.candidatePoolTopCandidates)
    ? summary.candidatePoolTopCandidates
    : Array.isArray(pool.topCandidates)
      ? pool.topCandidates
      : [];
  const active = Number(summary.candidatePoolActiveCount ?? pool.activeCount ?? 0);
  const total = Number(summary.candidatePoolCount ?? pool.totalCount ?? 0);
  const selected = Number(summary.candidatePoolSelectedCount ?? 0);
  const retained = Number(summary.candidatePoolRetainedScanCount ?? 0);
  const scanLimit = Number(summary.candidatePoolScanLimit ?? pool.scanLimit ?? 0);
  const improving = Number(summary.candidatePoolImprovingCount ?? pool.improvingCount ?? 0);
  const weakening = Number(summary.candidatePoolWeakeningCount ?? pool.weakeningCount ?? 0);
  const monitorReady = Number(summary.candidatePoolMonitorReadyCount ?? pool.monitorReadyCount ?? 0);
  const monitorWait = Number(summary.candidatePoolMonitorWaitCount ?? pool.monitorWaitCount ?? 0);
  const performanceMeasured = Number(summary.candidatePoolPerformanceMeasuredCount ?? pool.performanceMeasuredCount ?? 0);
  const performanceHitRate = summary.candidatePoolPerformanceHitRate ?? pool.performanceHitRate ?? "-";
  const performanceAverage = summary.candidatePoolPerformanceAverageChange ?? pool.performanceAverageChange ?? "-";
  const topText = top.length
    ? top
        .slice(0, 2)
        .map((item) => `${item.name || item.symbol} ${item.monitorLabel || item.stateLabel || ""} ${item.monitorScore ?? item.peakScore ?? item.score ?? "-"}점`)
        .join(" · ")
    : "상위 관찰 후보 없음";
  const rows = [
    ["관찰 후보", active > 0, `${active}/${total}`],
    ["매수 관찰", (counts.entry_candidate ?? 0) + (counts.validating ?? 0) > 0, `${(counts.entry_candidate ?? 0) + (counts.validating ?? 0)}개`],
    ["눌림 대기", (counts.pullback_wait ?? 0) + (counts.watching ?? 0) > 0, `${(counts.pullback_wait ?? 0) + (counts.watching ?? 0)}개`],
    ["오늘 선정", retained > 0 || selected > 0, `${selected}개 · 재확인 ${retained}${scanLimit ? `/${scanLimit}` : ""}`],
    ["우선 확인", monitorReady > 0 || monitorWait > 0, `${monitorReady}개 · 대기 ${monitorWait}`],
    ["흐름", improving >= weakening, `개선 ${improving} · 약화 ${weakening}`],
    ["성과", performanceMeasured > 0, `${performanceMeasured}건 · 승률 ${performanceHitRate} · 평균 ${performanceAverage}`],
    ["상위", top.length > 0, topText]
  ];
  els.candidatePoolStatus.innerHTML = rows
    .map(([label, ok, value]) => {
      const tone = ok ? "ok" : "warn";
      return `
        <div>
          <span>${escapeHtml(label)}</span>
          <strong class="${tone}">${escapeHtml(value)}</strong>
        </div>
      `;
    })
    .join("");
}

function candidateSourceLabel(summary = {}) {
  const cache = state.dashboard?.cache ?? {};
  if (cache.cached && cache.source === "browser_cache") return "브라우저 저장본";
  if (cache.cached && cache.source === "dashboard_cache") return "저장 대시보드";
  if (cache.cached && cache.source === "discovery_latest") return "저장 발굴본";
  if (cache.cached) return "저장 스냅샷";
  if (summary.candidateSourceStored) return "저장 발굴 후보";
  if (summary.candidateSource === "candidate-pool") return "관찰 후보 재확인";
  if (summary.candidateSource === "auto-discovery") return "실시간 발굴";
  if (summary.candidateSource === "auto-news") return "자동 뉴스 선정";
  if (summary.candidateSource === "auto-universe") return "자동 유니버스 선정";
  if (summary.candidateSource === "sample") return "시드 후보";
  return summary.candidateSource || "후보 출처 확인 중";
}

function candidateSourceDetailRows(summary = {}) {
  const cache = state.dashboard?.cache ?? {};
  const discovery = state.dashboard?.integrations?.discovery ?? {};
  const sourceLabel = candidateSourceLabel(summary);
  const cachedAt = cache.createdAt || summary.dashboardCacheCreatedAt || summary.storedDiscoveryCreatedAt || state.dashboard?.generatedAt || "";
  const scanned = Number(summary.scannedCount ?? discovery.scannedCount ?? 0);
  const materialNews = Number(summary.selectedMaterialNewsCount ?? summary.materialNewsCount ?? discovery.selectedMaterialNewsItemCount ?? discovery.materialNewsItemCount ?? 0);
  const cacheSuffix = cache.fallbackError ? " · 실시간 실패 대체" : "";
  const compressionCounts = summary.candidateCompressionCounts ?? {};
  const coreCount = Number(summary.coreCandidateCount ?? compressionCounts.core ?? 0);
  const actionCount = Number(summary.actionCandidateCount ?? summary.entryCandidateCount ?? compressionCounts.action ?? 0);
  const waitCount = Number(summary.waitCandidateCompressionCount ?? compressionCounts.wait ?? 0);
  const portfolioCount = Number(summary.portfolioCandidateCompressionCount ?? compressionCounts.portfolio ?? 0);
  const priceBasis = state.storageStatus?.basisCounts ?? state.dashboard?.integrations?.marketDataLatest?.basisCounts ?? {};
  const liveCount = Number(priceBasis.live ?? 0);
  const closedCount = Number(priceBasis.closed_baseline ?? 0);
  const lastGoodCount = Number(priceBasis.last_good ?? 0);
  const priceText =
    liveCount > 0
      ? `실시간 ${liveCount}개`
      : closedCount > 0
        ? `장마감 기준가 ${closedCount}개`
        : lastGoodCount > 0
          ? `마지막 정상값 ${lastGoodCount}개`
          : "가격 보강 중";
  const live = state.livePrice ?? {};
  const liveText = live.loading
    ? "갱신 중"
    : live.updatedAt
      ? `${timeLabel(live.updatedAt)} · ${live.error ? live.message || "갱신 실패" : live.message || "토스 현재가 반영"}`
      : "대기";
  const basisText = live.updatedAt && !live.error ? liveText : priceText;
  return [
    ["후보 기준", sourceLabel !== "시드 후보", `${sourceLabel}${cacheSuffix}${cachedAt ? ` · ${timeLabel(cachedAt)}` : ""}`],
    ["판단 압축", coreCount + actionCount + waitCount + portfolioCount > 0, `핵심 ${coreCount} · 진입 ${actionCount} · 대기 ${waitCount} · 보유 ${portfolioCount}`],
    ["가격 기준", liveCount + closedCount + lastGoodCount > 0 || Boolean(live.updatedAt), basisText],
    ["재료 근거", scanned > 0 || materialNews > 0, scanned > 0 ? `${scanned}종목 점검 · 재료뉴스 ${materialNews}건` : "수집 대기"]
  ];
}

function renderCandidateSourceDetail(rows = null) {
  if (!els.candidateSourceDetail) return;
  const sourceRows = rows ?? candidateSourceDetailRows(state.dashboard?.summary ?? {});
  setHtmlIfChanged(els.candidateSourceDetail, sourceRows
    .map(([label, ok, value]) => {
      const tone = ok ? "ok" : "warn";
      return `
        <div>
          <span>${escapeHtml(label)}</span>
          <strong class="${tone}">${escapeHtml(value)}</strong>
        </div>
      `;
    })
    .join(""));
}

function render() {
  updateShellView();
  updateModeStatus();
  renderMarket();
  renderMetrics();
  renderTradeDecisionStatus();
  renderPortfolioStatus();
  renderFeed();
  if (state.view === "settings") {
    renderSettingsPanels();
  }
  renderCurrentView();
  if (state.view === "signals") {
    maybeNotifyDashboard();
  }
}

function renderSettingsPanels() {
  renderLivePriceStatus();
  renderCandidatePoolStatus();
  renderAuthStatus();
  renderSchedulerStatus();
  renderDiscoveryBotStatus();
  renderReadinessStatus();
  renderStorageStatus();
  renderEvidenceStatus();
  renderStockMasterStatus();
  renderSnapshotHistory();
  renderNotificationStatus();
  renderMarketStatus();
  renderNetworkStatus();
  renderTossStatus();
  renderDartStatus();
  renderNewsStatus();
  renderOpenAIStatus();
  renderPrinciples();
}

function renderCurrentView() {
  if (state.view === "settings") {
    return;
  }
  if (state.view === "performance") {
    renderPerformance();
    return;
  }
  renderDetail();
}

function saveAdminToken(token) {
  const trimmed = String(token ?? "").trim();
  if (!trimmed) return;
  state.adminToken = trimmed;
  state.authRequired = false;
  writeStoredValue("marketSignalAdminToken", trimmed);
  renderAuthStatus();
  loadDashboard();
}

function clearAdminToken() {
  state.adminToken = "";
  state.authRequired = state.authEnabled;
  removeStoredValue("marketSignalAdminToken");
  renderAuthStatus();
  if (state.authEnabled && !state.authReadOnlyPublic) {
    renderAuthGate();
  } else {
    loadDashboard();
  }
}

function promptAdminToken() {
  const token = window.prompt("관리자 토큰을 입력하세요.");
  if (token) {
    saveAdminToken(token);
  }
}

function renderAuthGate() {
  state.authRequired = true;
  renderAuthStatus();
  els.candidateCount.textContent = "보호됨";
  if (els.candidateSource) els.candidateSource.textContent = "관리자 토큰 필요";
  renderCandidateSourceDetail([
    ["후보 출처", false, "잠금"],
    ["저장 상태", false, "토큰 필요"],
    ["다음 조치", false, "설정에서 토큰 입력"]
  ]);
  els.metricCandidates.textContent = 0;
  els.metricHighScore.textContent = 0;
  els.metricReady.textContent = 0;
  els.metricWatched.textContent = 0;
  els.principles.innerHTML = "";
  els.candidateFeed.innerHTML = `
    <div class="empty-state">
      <h2>접근 보호 중</h2>
      <p>관리자 토큰을 입력하면 후보와 성과 데이터를 불러옵니다.</p>
    </div>
  `;
  els.signalDetail.innerHTML = `
    <div class="auth-gate">
      <div>
        <p class="eyebrow">접근 보호</p>
        <h2>관리자 토큰이 필요합니다</h2>
        <p>공개 URL에서 API 호출량과 연결 키를 보호하기 위한 잠금입니다.</p>
      </div>
      <form class="auth-form" id="authForm">
        <input id="authTokenInput" type="password" autocomplete="current-password" placeholder="관리자 토큰" />
        <button type="submit">확인</button>
      </form>
    </div>
  `;
  const form = document.querySelector("#authForm");
  const input = document.querySelector("#authTokenInput");
  if (input) input.focus();
  if (form) {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      saveAdminToken(input?.value ?? "");
    });
  }
}

function renderAuthStatus() {
  if (!els.authStatus) return;
  const enabled = Boolean(state.authEnabled);
  const readOnlyPublic = Boolean(state.authReadOnlyPublic);
  const hasToken = Boolean(state.adminToken);
  const rows = [
    ["보호 상태", enabled, enabled ? "관리 작업 보호" : "꺼짐"],
    ["조회 화면", !enabled || readOnlyPublic || hasToken, !enabled || readOnlyPublic ? "공개" : hasToken ? "허용" : "토큰 필요"],
    ["관리 작업", !enabled || hasToken, !enabled ? "공개" : hasToken ? "허용" : "토큰 필요"]
  ];
  els.authStatus.innerHTML = `
    ${rows
      .map(([label, ok, value]) => {
        const tone = ok ? "ok" : "warn";
        return `
          <div>
            <span>${escapeHtml(label)}</span>
            <strong class="${tone}">${escapeHtml(value)}</strong>
          </div>
        `;
      })
      .join("")}
    <div class="auth-actions">
      <button type="button" data-auth-action="enter">${hasToken ? "다시 입력" : "토큰 입력"}</button>
      <button type="button" data-auth-action="clear" ${hasToken ? "" : "disabled"}>삭제</button>
    </div>
  `;
  els.authStatus.querySelectorAll("[data-auth-action]").forEach((button) => {
    button.addEventListener("click", () => {
      if (button.dataset.authAction === "enter") promptAdminToken();
      if (button.dataset.authAction === "clear") clearAdminToken();
    });
  });
}

function notificationSupported() {
  return typeof window !== "undefined" && "Notification" in window;
}

function notificationPermission() {
  return notificationSupported() ? window.Notification.permission : "unsupported";
}

function notificationEnabled() {
  return state.notificationsEnabled && notificationPermission() === "granted";
}

function notificationPermissionLabel(permission) {
  if (permission === "granted") return "허용됨";
  if (permission === "denied") return "차단됨";
  if (permission === "default") return "미요청";
  return "미지원";
}

function notificationCandidate() {
  const candidates = state.dashboard?.candidates ?? [];
  return notificationTriggers(candidates)[0] ?? null;
}

function notificationTriggers(candidates = []) {
  return candidates
    .map(notificationTriggerForCandidate)
    .filter(Boolean)
    .sort((a, b) => {
      const priorityDiff = a.priority - b.priority;
      if (priorityDiff !== 0) return priorityDiff;
      const readinessDiff = Number(b.item?.triggerReadiness ?? 0) - Number(a.item?.triggerReadiness ?? 0);
      if (readinessDiff !== 0) return readinessDiff;
      return Number(b.item?.totalScore ?? 0) - Number(a.item?.totalScore ?? 0);
    });
}

function rowValue(plan, label) {
  return plan.rows.find(([rowLabel]) => rowLabel === label)?.[1] ?? "-";
}

function notificationTriggerForCandidate(item) {
  const plan = tradePlan(item);
  if (!plan.hasPrice) return null;
  const score = Number(item.totalScore ?? 0);
  const readiness = Number(item.triggerReadiness ?? 0);
  const verdict = String(item.verdict ?? "");
  const group = decisionGroupForDisplay(item);
  const watched = Boolean(item.isWatched);
  const baseReady =
    score >= 72 ||
    readiness >= 70 ||
    watched ||
    verdict.includes("조건 충족") ||
    verdict.includes("준비") ||
    group.key === "action";
  const entryRange = rowValue(plan, "관찰 매수");
  const pullback = rowValue(plan, "눌림 대기");
  const rebound = rowValue(plan, "반등 확인");
  const stopLine = rowValue(plan, "손절 점검");
  const trimLine = rowValue(plan, "분할매도");

  let trigger = null;
  if (plan.tone === "sell") {
    trigger = {
      type: "trim",
      label: "분할매도 점검",
      title: "분할매도 구간 점검",
      criterion: trimLine,
      body: `${item.name} ${trimLine} · 보유 수익을 일부 확정할지 점검합니다.`,
      priority: 0
    };
  } else if (plan.tone === "risk" && plan.holding) {
    trigger = {
      type: "risk",
      label: "위험 기준 이탈 점검",
      title: "위험 기준 점검",
      criterion: stopLine,
      body: `${item.name} ${stopLine} · 추가 매수보다 리스크 축소를 먼저 봅니다.`,
      priority: 1
    };
  } else if (plan.tone === "buy" && baseReady) {
    trigger = {
      type: "entry",
      label: "관찰 매수 구간",
      title: "매수 관찰 구간 도달",
      criterion: entryRange,
      body: `${item.name} ${entryRange} · 조건 충족 시 관찰 매수 후보입니다.`,
      priority: 2
    };
  } else if (plan.action.includes("눌림") && baseReady) {
    trigger = {
      type: "pullback",
      label: "눌림 대기",
      title: "눌림 구간 대기",
      criterion: pullback,
      body: `${item.name} ${pullback} · 추격보다 눌림 확인이 우선입니다.`,
      priority: 3
    };
  } else if (plan.action.includes("반등") && (readiness >= 65 || watched)) {
    trigger = {
      type: "rebound",
      label: "반등 확인",
      title: "반등 확인 필요",
      criterion: rebound,
      body: `${item.name} ${rebound} · 약세 구간에서 회복 여부를 확인합니다.`,
      priority: 4
    };
  } else if ((group.key === "hidden" || group.key === "momentum") && (score >= 68 || readiness >= 65 || watched)) {
    trigger = {
      type: "watch",
      label: group.key === "hidden" ? "숨은 기회 관찰" : "모멘텀 관찰",
      title: "관찰 후보 변화 감지",
      criterion: entryRange,
      body: `${item.name} ${entryRange} · ${plan.summary}`,
      priority: 5
    };
  }

  if (!trigger) return null;
  return {
    ...trigger,
    item,
    plan
  };
}

function legacyNotificationCandidate() {
  const candidates = state.dashboard?.candidates ?? [];
  return candidates.find((item) => {
    const score = Number(item.totalScore ?? 0);
    const readiness = Number(item.triggerReadiness ?? 0);
    const verdict = String(item.verdict ?? "");
    return score >= 75 || readiness >= 70 || verdict.includes("조건 충족") || verdict.includes("준비");
  });
}

function notificationKeyForCandidate(trigger) {
  const item = trigger.item ?? trigger;
  return [
    "candidate",
    state.dashboard?.generatedAt ?? "",
    item.symbol ?? "",
    trigger.type ?? "legacy",
    item.totalScore ?? "",
    item.triggerReadiness ?? "",
    item.price ?? ""
  ].join(":");
}

function sendBrowserNotification(title, body, tag) {
  if (!notificationEnabled()) return false;
  try {
    const notification = new window.Notification(title, {
      body,
      tag,
      renotify: false
    });
    notification.onclick = () => window.focus();
    return true;
  } catch (error) {
    return false;
  }
}

function maybeNotifyDashboard() {
  if (state.viewingSnapshot) return;
  const trigger = notificationCandidate();
  if (!trigger || !notificationEnabled()) return;
  const key = notificationKeyForCandidate(trigger);
  if (state.lastNotifiedKey === key) return;
  const body = shortText(trigger.body, 90);
  if (sendBrowserNotification(trigger.title, body, key)) {
    state.lastNotifiedKey = key;
    writeStoredValue("marketSignalLastNotifiedKey", key);
  }
}

function maybeNotifySchedulerRun(status) {
  const latest = Array.isArray(status?.recentRuns) ? status.recentRuns[0] : null;
  if (!latest?.id) return;
  if (!state.schedulerStatusInitialized) {
    state.schedulerStatusInitialized = true;
    state.lastRunNotifiedId = latest.id;
    writeStoredValue("marketSignalLastRunNotifiedId", latest.id);
    return;
  }
  if (latest.id === state.lastRunNotifiedId) return;
  const topText = snapshotTopText(latest);
  sendBrowserNotification(
    `${modeLabel(latest.mode)} 분석 저장 완료`,
    shortText(topText, 90),
    `snapshot:${latest.id}`
  );
  state.lastRunNotifiedId = latest.id;
  writeStoredValue("marketSignalLastRunNotifiedId", latest.id);
}

async function enableNotifications() {
  if (!notificationSupported()) return;
  let permission = notificationPermission();
  try {
    if (permission !== "granted") {
      permission = await window.Notification.requestPermission();
    }
  } catch (error) {
    permission = "denied";
  }
  state.notificationsEnabled = permission === "granted";
  writeStoredValue("marketSignalNotifications", state.notificationsEnabled ? "1" : "0");
  renderNotificationStatus();
  maybeNotifyDashboard();
}

function disableNotifications() {
  state.notificationsEnabled = false;
  writeStoredValue("marketSignalNotifications", "0");
  renderNotificationStatus();
}

function testNotification() {
  sendBrowserNotification(
    "Market Signal Desk 테스트",
    "매수 구간, 위험 기준, 분할매도 구간이 감지되면 이 방식으로 알림을 보냅니다.",
    "market-signal-test"
  );
}

function renderNotificationStatus() {
  if (!els.notificationStatus) return;
  const supported = notificationSupported();
  const permission = notificationPermission();
  const enabled = notificationEnabled();
  const trigger = notificationCandidate();
  const legacyCandidate = trigger ? null : legacyNotificationCandidate();
  const autoText = enabled ? "켜짐" : state.notificationsEnabled ? "권한 필요" : "꺼짐";
  const rows = [
    ["브라우저 지원", supported, supported ? "가능" : "미지원"],
    ["권한", permission === "granted", notificationPermissionLabel(permission)],
    ["자동 알림", enabled, autoText],
    [
      "감시 조건",
      Boolean(trigger),
      trigger ? `${trigger.item.name} · ${trigger.label}` : legacyCandidate ? `${legacyCandidate.name} 후보 대기` : "대기"
    ],
    ["가격 기준", Boolean(trigger), trigger ? trigger.criterion : "조건 계산 대기"]
  ];
  const deniedHint =
    permission === "denied"
      ? `<div><span>권한 복구</span><strong class="warn">브라우저 설정 필요</strong></div>`
      : "";
  els.notificationStatus.innerHTML = `
    ${rows
      .map(([label, ok, value]) => {
        const tone = ok ? "ok" : "warn";
        return `
          <div>
            <span>${escapeHtml(label)}</span>
            <strong class="${tone}">${escapeHtml(value)}</strong>
          </div>
        `;
      })
      .join("")}
    ${deniedHint}
    <div class="notification-actions">
      <button type="button" data-notification-action="enable" ${enabled || !supported || permission === "denied" ? "disabled" : ""}>알림 켜기</button>
      <button type="button" data-notification-action="test" ${enabled ? "" : "disabled"}>테스트</button>
      <button type="button" data-notification-action="disable" ${state.notificationsEnabled ? "" : "disabled"}>끄기</button>
    </div>
  `;
  els.notificationStatus.querySelectorAll("[data-notification-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      const action = button.dataset.notificationAction;
      if (action === "enable") await enableNotifications();
      if (action === "test") testNotification();
      if (action === "disable") disableNotifications();
    });
  });
}

function marketIndexDisplay(market, key) {
  const detail = market?.indexDetails?.[key] ?? {};
  return {
    value: detail.value || "-",
    change: displayChangeText(detail.change || market?.[key] || "-")
  };
}

function renderMarketIndex(valueNode, changeNode, data) {
  if (valueNode) valueNode.textContent = data.value || "-";
  if (changeNode) {
    changeNode.textContent = data.change || "-";
    changeNode.className = changeClass(data.change);
  }
}

function renderMarket() {
  const market = state.dashboard?.market ?? {};
  renderMarketIndex(els.kospiValue, els.kospiChange, marketIndexDisplay(market, "kospi"));
  renderMarketIndex(els.kosdaqValue, els.kosdaqChange, marketIndexDisplay(market, "kosdaq"));
  renderMarketIndex(els.nasdaqValue, els.nasdaqChange, marketIndexDisplay(market, "nasdaq"));
  if (els.usdKrwValue) els.usdKrwValue.textContent = market.usdKrw ?? "-";
  if (els.usdKrwPair) els.usdKrwPair.textContent = "USD/KRW";
  const fxSource = market.usdKrwSource;
  const fxTimestamp = fxSource?.lastGoodAt || fxSource?.timestamp || "";
  const fxText =
    fxSource?.source === "fx-api" || fxSource?.source === "market-data-latest"
      ? `환율: ${fxSource.provider}${fxTimestamp ? ` · ${fxTimestamp}` : ""}${fxSource.stale ? " · 지연" : ""}`
      : fxSource?.source === "sample"
        ? `환율: ${fallbackStatusLabel(fxSource, "대체 환율")}`
        : "";
  const indexSource = market.indexSource;
  const indexTimestamp = indexSource?.lastGoodAt || indexSource?.timestamp || "";
  const indexText =
    indexSource?.source === "index-api" || indexSource?.source === "market-data-latest"
      ? `지수: ${indexSource.provider}${indexTimestamp ? ` · ${indexTimestamp}` : ""}${indexSource.stale ? " · 지연" : ""}`
      : indexSource?.source === "index-api-partial"
        ? `지수: ${indexSource.provider} 일부${indexTimestamp ? ` · ${indexTimestamp}` : ""}`
        : indexSource?.source === "sample"
          ? `지수: ${fallbackStatusLabel(indexSource, "대체 지수")}`
          : "";
  const snapshotText = state.viewingSnapshot
    ? `스냅샷 보기: ${modeLabel(state.viewingSnapshot.mode)} · ${timeLabel(state.viewingSnapshot.createdAt)}`
    : "";
  const cache = state.dashboard?.cache ?? {};
  const cacheText = cache.cached
    ? `저장본: ${modeLabel(cache.mode || cache.requestedMode)} · ${cache.createdAt ? timeLabel(cache.createdAt) : "시간 미확인"}${cache.fallbackError ? " · 실시간 갱신 실패 후 대체" : ""}`
    : "";
  const liveText = state.livePrice?.updatedAt
    ? `라이브 가격: ${timeLabel(state.livePrice.updatedAt)}${state.livePrice.error ? " · 갱신 실패" : ""}`
    : "";
  els.marketNote.textContent = [fxText, indexText, liveText, snapshotText, cacheText, market.note].filter(Boolean).join("  ·  ");
}

function candidateBriefForMain(summary = {}) {
  const discovery = state.dashboard?.integrations?.discovery ?? {};
  const cache = state.dashboard?.cache ?? {};
  const compressionCounts = summary.candidateCompressionCounts ?? {};
  const priceBasis = state.storageStatus?.basisCounts ?? state.dashboard?.integrations?.marketDataLatest?.basisCounts ?? {};
  const sourceLabel = candidateSourceLabel(summary);
  const coreCount = Number(summary.coreCandidateCount ?? compressionCounts.core ?? 0);
  const actionCount = Number(summary.actionCandidateCount ?? summary.entryCandidateCount ?? compressionCounts.action ?? 0);
  const waitCount = Number(summary.waitCandidateCompressionCount ?? compressionCounts.wait ?? 0);
  const candidateCount = Number(summary.candidateCount ?? 0);
  const liveCount = Number(priceBasis.live ?? 0);
  const closedCount = Number(priceBasis.closed_baseline ?? 0);
  const lastGoodCount = Number(priceBasis.last_good ?? 0);
  const materialNews = Number(
    summary.selectedMaterialNewsCount ??
      summary.materialNewsCount ??
      discovery.selectedMaterialNewsItemCount ??
      discovery.materialNewsItemCount ??
      0
  );
  const priceText =
    liveCount > 0
      ? `실시간 ${liveCount}`
      : closedCount > 0
        ? `장마감 ${closedCount}`
        : lastGoodCount > 0
          ? `마지막값 ${lastGoodCount}`
          : "가격 보강";
  const sourceText = cache.cached
    ? cache.source === "browser_cache"
      ? "브라우저 저장본"
      : cache.source === "discovery_latest"
        ? "저장 발굴본"
        : "저장 스냅샷"
    : sourceLabel;
  const line = [
    sourceText,
    candidateCount ? `후보 ${candidateCount}` : "",
    `핵심 ${coreCount}`,
    actionCount ? `진입 ${actionCount}` : "",
    waitCount ? `대기 ${waitCount}` : "",
    materialNews ? `재료 ${materialNews}` : "",
    priceText
  ].filter(Boolean).join(" · ");
  return {
    line: shortText(line || sourceLabel, 64),
    title: line || sourceLabel
  };
}

function renderMetrics() {
  const summary = state.dashboard?.summary ?? {};
  els.candidateCount.textContent = `${summary.candidateCount ?? 0}개`;
  if (els.candidateSource) {
    const brief = candidateBriefForMain(summary);
    els.candidateSource.textContent = brief.line;
    els.candidateSource.title = brief.title;
  }
  renderCandidateSourceDetail();
  els.metricCandidates.textContent = summary.candidateCount ?? 0;
  els.metricHighScore.textContent = summary.highScoreCount ?? 0;
  els.metricReady.textContent = summary.readyCount ?? 0;
  els.metricWatched.textContent = summary.watchedCount ?? 0;
}

function timeLabel(value) {
  const text = String(value ?? "");
  return text ? text.replace("T", " ").slice(5, 16) : "-";
}

function scheduleTimeLabel(value) {
  const text = String(value ?? "");
  if (!text) return "-";
  const date = text.slice(5, 10);
  const time = text.slice(11, 16);
  return `${date} ${time}`;
}

function modeLabel(mode) {
  if (mode === "intraday") return "장중";
  return "장마감";
}

function modeSummary(mode) {
  if (mode === "intraday") {
    return {
      label: "장중 분석",
      detail: "토스 실시간 가격·호가·체결 반응을 우선 반영합니다"
    };
  }
  return {
    label: "장마감 분석",
    detail: "장마감 기준가·뉴스·공시·해외지수로 다음 거래일 후보를 준비합니다"
  };
}

function updateModeStatus() {
  const serverSessionMode = state.dashboard?.market?.marketSession?.analysisMode || state.dashboard?.market?.analysisMode || "";
  state.autoMode = serverSessionMode ? normalizeAnalysisMode(serverSessionMode) : detectedAnalysisMode();
  const autoLabel = modeLabel(state.autoMode);
  const selected = modeSummary(state.mode);
  const isAuto = state.mode === state.autoMode;
  if (els.marketSessionLabel) {
    els.marketSessionLabel.textContent = `현재 ${autoLabel}`;
  }
  if (els.analysisModeLabel) {
    els.analysisModeLabel.textContent = selected.label;
  }
  if (els.analysisModeDetail) {
    els.analysisModeDetail.textContent = isAuto && state.modeAutoFollow ? selected.detail : `수동 기준 · ${selected.detail}`;
  }
  if (els.modeSelect && els.modeSelect.value !== state.mode) {
    els.modeSelect.value = state.mode;
  }
}

function triggerLabel(trigger) {
  if (trigger === "scheduled") return "자동";
  if (String(trigger ?? "").startsWith("manual")) return "수동";
  return trigger || "-";
}

function snapshotTopText(run) {
  const top = run?.summary?.topCandidates ?? [];
  if (!Array.isArray(top) || !top.length) return "상위 후보 없음";
  return top
    .slice(0, 3)
    .map((item) => `${item.name ?? item.symbol} ${item.score ?? 0}`)
    .join(" · ");
}

function renderSchedulerStatus() {
  if (!els.schedulerStatus) return;
  const status = state.schedulerStatus;
  if (!status) return;
  const config = status.config ?? {};
  const schedulerState = status.state ?? {};
  const nextRun = status.nextRun ?? {};
  const jobs = Array.isArray(config.jobs) ? config.jobs : [];
  const recentRuns = Array.isArray(status.recentRuns) ? status.recentRuns : [];
  const performanceUpdate = schedulerState.lastPerformanceUpdate ?? {};
  const candidatePrefetch = schedulerState.lastCandidatePrefetch ?? {};
  const performanceMinAge = Number(config.performanceMinAgeMinutes ?? 60);
  const prefetchInterval = Number(config.candidatePrefetchIntervalSeconds ?? 60);
  const latest = recentRuns[0];
  const runText = latest
    ? `${modeLabel(latest.mode)} · ${triggerLabel(latest.trigger)} · ${String(latest.createdAt ?? "").replace("T", " ").slice(5, 16)}`
    : "없음";
  const nextRunText = config.enabled && nextRun?.runAt
    ? `${modeLabel(nextRun.mode)} · ${scheduleTimeLabel(nextRun.runAt)}`
    : config.enabled
      ? "계산 중"
      : "꺼짐";
  const jobText = jobs.length
    ? jobs.map((job) => `${modeLabel(job.mode)} ${job.time}`).join(" · ")
    : "-";
  const performanceText = performanceUpdate.updatedAt
    ? `${performanceUpdate.updatedCount ?? 0}개 반영 · 승률 ${performanceUpdate.hitRate ?? "-"} · ${timeLabel(performanceUpdate.updatedAt)}`
    : "대기";
  const prefetchText = config.candidatePrefetchEnabled
    ? `${config.candidatePrefetchLimit ?? "-"}개 · ${prefetchInterval}초마다`
    : "꺼짐";
  const prefetchAt = candidatePrefetch.updatedAt || candidatePrefetch.checkedAt || "";
  const prefetchRunText = prefetchAt
    ? candidatePrefetch.skipped
      ? `${candidatePrefetch.reason ?? "대기"} · ${timeLabel(prefetchAt)}`
      : `${candidatePrefetch.prefetchedCount ?? 0}/${candidatePrefetch.inputCount ?? 0}개 · 진입 ${candidatePrefetch.entryReadyCount ?? 0} · ${timeLabel(prefetchAt)}`
    : "대기";
  const rows = [
    ["자동 실행", config.enabled, config.enabled ? "켜짐" : "꺼짐"],
    ["실행 상태", !schedulerState.running && !schedulerState.lastError, schedulerState.running ? "실행 중" : schedulerState.lastError ? "확인 필요" : "대기"],
    ["예약", true, jobText],
    ["다음 실행", Boolean(config.enabled && nextRun?.runAt), nextRunText],
    ["후보 보강", Boolean(config.candidatePrefetchEnabled), prefetchText],
    ["최근 보강", Boolean(prefetchAt && !candidatePrefetch.error), prefetchRunText],
    ["최근 실행", Boolean(latest), runText],
    ["성과 자동", config.performanceAutoUpdate, config.performanceAutoUpdate ? `${performanceMinAge}분 후 반영` : "꺼짐"],
    ["최근 성과", Boolean(performanceUpdate.updatedAt), performanceText]
  ];
  const lastError = schedulerState.lastError
    ? `<div><span>최근 오류</span><strong class="warn">${escapeHtml(schedulerState.lastError)}</strong></div>`
    : "";
  const performanceError = schedulerState.lastPerformanceError
    ? `<div><span>성과 오류</span><strong class="warn">${escapeHtml(schedulerState.lastPerformanceError)}</strong></div>`
    : "";
  const candidatePrefetchError = schedulerState.lastCandidatePrefetchError
    ? `<div><span>보강 오류</span><strong class="warn">${escapeHtml(schedulerState.lastCandidatePrefetchError)}</strong></div>`
    : "";
  els.schedulerStatus.innerHTML = `
    ${rows
      .map(([label, ok, value]) => {
        const tone = ok ? "ok" : "warn";
        return `
          <div>
            <span>${escapeHtml(label)}</span>
            <strong class="${tone}">${escapeHtml(value)}</strong>
          </div>
        `;
      })
      .join("")}
    ${lastError}
    ${performanceError}
    ${candidatePrefetchError}
    <div class="schedule-actions">
      <button type="button" data-scheduler-mode="close">장마감 실행</button>
      <button type="button" data-scheduler-mode="intraday">장중 실행</button>
    </div>
  `;
  els.schedulerStatus.querySelectorAll("[data-scheduler-mode]").forEach((button) => {
    button.addEventListener("click", async () => {
      await runSchedulerMode(button.dataset.schedulerMode);
    });
  });
}

function renderDiscoveryBotStatus() {
  if (!els.discoveryBotStatus) return;
  const status = state.discoveryBotStatus;
  if (!status) return;
  const config = status.config ?? {};
  const botState = status.state ?? {};
  const latest = status.latest && Object.keys(status.latest).length ? status.latest : botState.lastRun ?? {};
  const summary = latest.summary ?? {};
  const topText = snapshotTopText({ summary });
  const pipeline = Array.isArray(summary.pipeline) ? summary.pipeline : [];
  const pipelineText = pipeline.length
    ? uniqueTexts(pipeline.map((step) => step.stage || step.label).filter(Boolean), 4).join(" → ")
    : "-";
  const evidenceText =
    summary.evidenceStrongCount != null || summary.evidenceQualifiedCount != null || summary.evidenceWeakCount != null
      ? `강 ${summary.evidenceStrongCount ?? 0} · 검증 ${summary.evidenceQualifiedCount ?? 0} · 약 ${summary.evidenceThinCount ?? 0} · 리스크 ${summary.evidenceRiskCount ?? 0} · 부족 ${summary.evidenceWeakCount ?? 0}`
      : "-";
  const validationText =
    summary.confirmedSignalCount != null || summary.evidenceWaitSignalCount != null || summary.reactionOnlySignalCount != null
      ? `확인 ${summary.confirmedSignalCount ?? 0} · 반응대기 ${summary.evidenceWaitSignalCount ?? 0} · 가격선행 ${summary.reactionOnlySignalCount ?? 0}`
      : "-";
  const intervalMinutes = Math.max(1, Math.round(Number(config.intervalSeconds ?? 0) / 60));
  const latestText = latest.createdAt ? `${modeLabel(latest.mode)} · ${timeLabel(latest.createdAt)}` : "아직 없음";
  const rows = [
    ["자동 발굴", config.enabled, config.enabled ? "켜짐" : "꺼짐"],
    ["실행 상태", !botState.running && !botState.lastError, botState.running ? "실행 중" : botState.lastError ? "확인 필요" : "대기"],
    ["주기", Boolean(config.intervalSeconds), config.enabled ? `${intervalMinutes}분마다` : "수동 실행"],
    ["최신 발굴", Boolean(latest.createdAt), latestText],
    ["파이프라인", pipeline.length >= 4, pipelineText],
    ["발굴 근거", evidenceText !== "-", evidenceText],
    ["검증 신호", validationText !== "-", validationText],
    ["상위 후보", Boolean(summary.topCandidates?.length), topText]
  ];
  const lastError = botState.lastError
    ? `<div><span>최근 오류</span><strong class="warn">${escapeHtml(botState.lastError)}</strong></div>`
    : "";
  els.discoveryBotStatus.innerHTML = `
    ${rows
      .map(([label, ok, value]) => {
        const tone = ok ? "ok" : "warn";
        return `
          <div>
            <span>${escapeHtml(label)}</span>
            <strong class="${tone}">${escapeHtml(value)}</strong>
          </div>
        `;
      })
      .join("")}
    ${lastError}
    <div class="schedule-actions">
      <button type="button" data-discovery-action="run">지금 발굴</button>
    </div>
  `;
  const button = els.discoveryBotStatus.querySelector("[data-discovery-action='run']");
  if (button) {
    button.addEventListener("click", runDiscoveryBot);
  }
}

function readinessState() {
  const integrations = state.dashboard?.integrations ?? {};
  const toss = integrations.toss ?? {};
  const dart = integrations.dart ?? {};
  const news = integrations.news ?? {};
  const openai = integrations.openai ?? {};
  const scheduler = state.schedulerStatus ?? {};
  const recentRuns = Array.isArray(scheduler.recentRuns) ? scheduler.recentRuns : [];
  const tossReady =
    toss.prices?.source === "toss" &&
    toss.candles?.source === "toss" &&
    toss.orderbook?.source === "toss" &&
    toss.trades?.source === "toss";
  const contextReady =
    dart.disclosures?.source === "opendart" &&
    news.naver?.items?.source === "naver" &&
    openai.analysis?.source === "openai";
  const manualRunReady = recentRuns.some((run) => String(run.trigger ?? "").startsWith("manual"));
  const autoEnabled = Boolean(scheduler.config?.enabled);
  const hasError = Boolean(scheduler.state?.lastError);
  return {
    tossReady,
    contextReady,
    manualRunReady,
    autoEnabled,
    hasError,
    allBeforeAuto: tossReady && contextReady && manualRunReady && !hasError,
    fullReady: tossReady && contextReady && manualRunReady && autoEnabled && !hasError
  };
}

function renderReadinessStatus() {
  if (!els.readinessStatus) return;
  const readiness = readinessState();
  const rows = [
    [
      "실시간 데이터",
      readiness.tossReady,
      readiness.tossReady ? "Toss 완료" : "Toss 점검"
    ],
    [
      "분석 재료",
      readiness.contextReady,
      readiness.contextReady ? "뉴스·공시·AI 완료" : "연결 점검"
    ],
    [
      "수동 스냅샷",
      readiness.manualRunReady,
      readiness.manualRunReady ? "저장됨" : "먼저 실행"
    ],
    [
      "자동 실행",
      readiness.autoEnabled,
      readiness.autoEnabled ? "켜짐" : readiness.allBeforeAuto ? "켜도 됨" : "대기"
    ],
    [
      "판정",
      readiness.fullReady || readiness.allBeforeAuto,
      readiness.fullReady ? "운영 중" : readiness.allBeforeAuto ? "활성화 가능" : "준비 중"
    ]
  ];
  const actionLabel = !readiness.manualRunReady
    ? "장마감 수동 실행"
    : readiness.allBeforeAuto && !readiness.autoEnabled
      ? "성과 보기"
      : "스냅샷 확인";
  const actionMarkup = `
    <div class="readiness-actions">
      <button type="button" data-readiness-action="${readiness.manualRunReady ? "performance" : "run-close"}">
        ${escapeHtml(actionLabel)}
      </button>
    </div>
  `;
  els.readinessStatus.innerHTML = `
    ${rows
      .map(([label, ok, value]) => {
        const tone = ok ? "ok" : "warn";
        return `
          <div>
            <span>${escapeHtml(label)}</span>
            <strong class="${tone}">${escapeHtml(value)}</strong>
          </div>
        `;
      })
      .join("")}
    ${actionMarkup}
  `;
  const actionButton = els.readinessStatus.querySelector("[data-readiness-action]");
  if (actionButton) {
    actionButton.addEventListener("click", async () => {
      const action = actionButton.dataset.readinessAction;
      if (action === "run-close") {
        await runSchedulerMode("close");
      } else {
        await showPerformanceView();
      }
    });
  }
}

function renderStorageStatus() {
  if (!els.storageStatus) return;
  const status = state.storageStatus;
  if (!status) return;
  const database = status.database ?? {};
  const connectivity = database.connectivity ?? {};
  const databaseUrl = database.url ?? {};
  const migration = database.migration ?? {};
  const counts = database.counts ?? {};
  const rawEvents = status.rawEvents ?? {};
  const newsEvents = status.newsEvents ?? {};
  const candidateData = status.candidateData ?? {};
  const marketData = status.marketData ?? {};
  const operationReady = Boolean(status.operationReady);
  const marketStorageReady = Boolean(marketData.enabled && marketData.readSource === "postgres");
  const candidateStorageReady = Boolean(candidateData.enabled && candidateData.readSource === "postgres");
  const analysisReady = Boolean(status.analysisReady || (Number(candidateData.itemCount ?? 0) > 0 && Number(marketData.itemCount ?? 0) > 0));
  const analysisPersistent = Boolean(status.analysisPersistent || (analysisReady && candidateStorageReady && marketStorageReady));
  const displayFallbackReady = Boolean(status.displayFallbackReady || (analysisReady && !analysisPersistent));
  const degradedDisplayReady = Boolean(status.degradedDisplayReady || (displayFallbackReady && !analysisPersistent));
  const lastGoodDisplayReady = Boolean(status.lastGoodDisplayReady || analysisPersistent || degradedDisplayReady);
  const decisionReady = Boolean(operationReady && analysisPersistent);
  const volatileFallback = Boolean(status.volatileFallback || (!operationReady && status.implementation !== "postgres"));
  const modeText = status.implementation === "postgres"
    ? "Postgres DB"
    : volatileFallback
    ? "임시 파일 fallback"
    : status.mode || "-";
  const persistenceText = decisionReady ? "DB 영구 저장" : degradedDisplayReady ? "검수용 스냅샷" : displayFallbackReady ? "임시 파일 표시" : "DB 기준 대기";
  const latestText = status.latestRunCreatedAt
    ? `${status.recentRunCount ?? 0}건 · ${String(status.latestRunCreatedAt).replace("T", " ").slice(5, 16)}`
    : `${status.recentRunCount ?? 0}건`;
  const nextText = decisionReady
    ? "운영 가능"
    : degradedDisplayReady
    ? "DB 복구 후 운영 전환"
    : !database.urlConfigured
    ? "DATABASE_URL 연결 필요"
    : database.ready
    ? "DB 이관 또는 다음 수집 필요"
    : database.nextAction || "DB 연결 확인 필요";
  const dbText = database.urlConfigured
    ? database.ready
      ? "Postgres 준비"
      : shortText(database.error || "DB 연결 확인", 28)
    : "미연결";
  const dbConnectionText = database.urlConfigured
    ? database.connectionReady || connectivity.ready
      ? "연결 가능"
      : connectivity.connectionRefused
      ? "연결 거부"
      : connectivity.connectionFailure
      ? "연결 실패"
      : database.backoffActive
      ? "재시도 대기"
      : "확인 필요"
    : "미설정";
  const dbActionText = connectivity.needsServiceRestart
    ? "DB Available 확인 후 Web 재시작"
    : database.nextAction || nextText;
  const dbHostText = databaseUrl.configured
    ? `${databaseUrl.hostKind || "unknown"}${databaseUrl.host ? ` · ${databaseUrl.host}` : ""}`
    : "DATABASE_URL 미설정";
  const dbRetryText = Number(database.nextRetrySeconds ?? 0) > 0
    ? `${database.nextRetrySeconds}초 후 재시도`
    : database.ready
    ? "대기 없음"
    : database.lastConnectAttemptAt
    ? "즉시 재시도 가능"
    : "시도 전";
  const dbSchemaText = database.schemaReady
    ? "준비됨"
    : database.schemaCheckedAt
    ? `확인 실패 · ${timeLabel(database.schemaCheckedAt)}`
    : "확인 전";
  const dbLastErrorText = database.lastError
    ? `${database.lastErrorType || "Error"} · ${shortText(database.lastError, 34)}`
    : database.ready
    ? "없음"
    : "-";
  const migrationText = migration.enabled
    ? migration.error
      ? shortText(migration.error, 28)
      : migration.done
      ? `완료 · 스냅샷 ${migration.snapshotsInserted ?? 0}/${migration.snapshotsScanned ?? 0}`
      : "대기"
    : "꺼짐";
  const recordText = counts.snapshotCount != null
    ? `스냅샷 ${counts.snapshotCount} · 풀 ${counts.candidatePoolActiveCount ?? 0}/${counts.candidatePoolCount ?? 0} · 데이터 ${counts.candidateDataCount ?? 0} · 최신 ${counts.marketDataLatestCount ?? 0}`
    : "-";
  const rawSourceText = rawEvents.bySource && Object.keys(rawEvents.bySource).length
    ? Object.entries(rawEvents.bySource)
        .slice(0, 3)
        .map(([source, count]) => `${source} ${count}`)
        .join(" · ")
    : "";
  const rawEventText = rawEvents.enabled
    ? `${rawEvents.count ?? 0}건${rawSourceText ? ` · ${rawSourceText}` : ""}`
    : "꺼짐";
  const newsProviderText = newsEvents.byProvider && Object.keys(newsEvents.byProvider).length
    ? Object.entries(newsEvents.byProvider)
        .slice(0, 3)
        .map(([provider, count]) => `${provider} ${count}`)
        .join(" · ")
    : "";
  const newsEventText = newsEvents.enabled
    ? `${newsEvents.count ?? 0}건${newsProviderText ? ` · ${newsProviderText}` : ""}`
    : "꺼짐";
  const newsLatest = newsEvents.latest ?? {};
  const newsLatestText = newsLatest.collectedAt
    ? `${timeLabel(newsLatest.collectedAt)} · ${shortText(newsLatest.title || newsLatest.query || newsLatest.provider || "뉴스", 24)}`
    : "-";
  const marketSourceText = marketData.bySource && Object.keys(marketData.bySource).length
    ? Object.entries(marketData.bySource)
        .slice(0, 3)
        .map(([source, count]) => `${source} ${count}`)
        .join(" · ")
    : "";
  const marketDataText = marketData.enabled
    ? `${marketData.itemCount ?? 0}개 · ${marketData.readSource === "postgres" ? "DB 읽기" : marketData.readSource === "filesystem" ? "파일 fallback" : "비어 있음"}${marketSourceText ? ` · ${marketSourceText}` : ""}`
    : "꺼짐";
  const marketLatestText = marketData.latestAt ? timeLabel(marketData.latestAt) : "-";
  const priceReadiness = status.priceReadiness ?? marketData.readiness ?? {};
  const storedCandidateCount = Number(status.storedCandidateCount ?? candidateData.itemCount ?? 0);
  const storedPriceCount = Number(status.storedPriceCount ?? marketData.priceCount ?? marketData.storedPriceCount ?? 0);
  const usablePriceCount = Number(status.usablePriceCount ?? marketData.usablePriceCount ?? priceReadiness.usablePriceCount ?? 0);
  const priceCoverageValue = status.priceCoverage ?? marketData.priceCoverage ?? priceReadiness.priceCoverage ?? 0;
  const priceCoverageText = status.priceCoveragePercent || marketData.priceCoveragePercent || priceReadiness.priceCoveragePercent || evidenceCoverageText(priceCoverageValue);
  const basisCounts = status.basisCounts ?? marketData.basisCounts ?? {};
  const livePriceCount = Number(status.livePriceCount ?? basisCounts.live ?? priceReadiness.livePriceCount ?? 0);
  const closedBaselinePriceCount = Number(status.closedBaselinePriceCount ?? basisCounts.closed_baseline ?? priceReadiness.closedBaselinePriceCount ?? 0);
  const lastGoodPriceCount = Number(status.lastGoodPriceCount ?? basisCounts.last_good ?? priceReadiness.lastGoodPriceCount ?? 0);
  const unknownBasisCount = Number(status.unknownBasisCount ?? basisCounts.unknown ?? priceReadiness.unknownBasisCount ?? 0);
  const basisStatusText = [
    livePriceCount ? `실시간 ${livePriceCount}` : "",
    closedBaselinePriceCount ? `장마감 ${closedBaselinePriceCount}` : "",
    lastGoodPriceCount ? `마지막값 ${lastGoodPriceCount}` : "",
    unknownBasisCount ? `기준 미정 ${unknownBasisCount}` : ""
  ].filter(Boolean).join(" · ") || "기준 없음";
  const priceReadinessText = usablePriceCount > 0
    ? `판단 ${usablePriceCount}/${storedCandidateCount || storedPriceCount || "-"} · ${priceCoverageText}`
    : storedPriceCount > 0
    ? `저장 ${storedPriceCount} · 판단 가능값 없음`
    : "가격 저장 대기";
  const candidateDataText = candidateData.enabled
    ? `${candidateData.itemCount ?? 0}종목 · ${candidateData.readSource === "postgres" ? "DB 읽기" : candidateData.readSource === "filesystem" ? "파일 fallback" : "비어 있음"}`
    : "꺼짐";
  const candidateReadyText = candidateData.enabled
    ? `후보 ${candidateData.displayReadyCount ?? 0} · 진입 ${candidateData.entryReadyCount ?? 0}`
    : "-";
  const candidateMissingText = candidateData.missingCounts && Object.keys(candidateData.missingCounts).length
    ? Object.entries(candidateData.missingCounts)
        .slice(0, 3)
        .map(([key, count]) => `${key} ${count}`)
        .join(" · ")
    : "누락 없음";
  const candidateLatestText = candidateData.latestAt ? timeLabel(candidateData.latestAt) : "-";
  const storageBasisText = (info) => {
    if (!info?.enabled) return "꺼짐";
    const readSource = info.readSource || info.storage || "unknown";
    const sourceText = readSource === "postgres"
      ? "DB 기준"
      : readSource === "filesystem"
      ? "파일 fallback"
      : readSource === "empty"
      ? "저장 없음"
      : readSource;
    const dbCount = Number(info.dbItemCount ?? 0);
    const fileCount = Number(info.fileItemCount ?? 0);
    return `${sourceText} · DB ${dbCount} · 파일 ${fileCount}`;
  };
  const storageWarningText = analysisPersistent
    ? "후보/최신값 DB 기준"
    : degradedDisplayReady
    ? `DB 장애 중 · 마지막 스냅샷 표시 · 후보 ${candidateData.readSource || "-"} · 최신 ${marketData.readSource || "-"}`
    : displayFallbackReady
    ? `임시 표시용 · 후보 ${candidateData.readSource || "-"} · 최신 ${marketData.readSource || "-"}`
    : `후보 ${candidateData.readSource || "-"} · 최신 ${marketData.readSource || "-"}`;
  const rows = [
    ["표시 상태", lastGoodDisplayReady, decisionReady ? "실전 DB 표시" : degradedDisplayReady ? "검수용 마지막 스냅샷" : "표시 대기"],
    ["운영 저장소", decisionReady, decisionReady ? "DB 기준" : "DB 기준 미완료"],
    ["분석 저장소", analysisReady, analysisPersistent ? "DB 저장값 확보" : displayFallbackReady ? "임시 저장값만 있음" : "후보/최신값 대기"],
    ["실전 판단", decisionReady, decisionReady ? "가능" : degradedDisplayReady ? "검수 가능 · 실전 보류" : "DB 기준 전환 전 보류"],
    ["저장 방식", Boolean(status.mode || status.implementation), modeText],
    ["쓰기 가능", Boolean(status.writable), status.writable ? "가능" : shortText(status.error || "확인 필요", 28)],
    ["DB 상태", Boolean(database.ready), dbText],
    ["DB 연결", Boolean(database.connectionReady || connectivity.ready), dbConnectionText],
    ["DB URL", Boolean(database.urlConfigured && databaseUrl.recommendedForRenderWebService), dbHostText],
    ["스키마", Boolean(database.schemaReady), dbSchemaText],
    ["재시도", Boolean(database.ready || Number(database.nextRetrySeconds ?? 0) === 0), dbRetryText],
    ["DB 오류", Boolean(database.ready || !database.lastError), dbLastErrorText],
    ["DB 조치", Boolean(database.ready), shortText(dbActionText, 42)],
    ["후보 기준", candidateStorageReady, storageBasisText(candidateData)],
    ["최신값 기준", marketStorageReady, storageBasisText(marketData)],
    ["저장 위험", !volatileFallback, volatileFallback ? "배포/재시작 시 유실 가능" : "낮음"],
    ["판단 기준", decisionReady, storageWarningText],
    ["표시 사유", !degradedDisplayReady, degradedDisplayReady ? shortText(status.degradedReason || "DB 복구 전 파일 스냅샷 표시", 38) : "정상"],
    ["DB 이관", Boolean(migration.done), migrationText],
    ["DB 기록", counts.snapshotCount != null, recordText],
    ["원천 이벤트", Boolean(rawEvents.enabled && Number(rawEvents.count ?? 0) > 0), rawEventText],
    ["뉴스 이벤트", Boolean(newsEvents.enabled && Number(newsEvents.count ?? 0) > 0), newsEventText],
    ["뉴스 저장", Boolean(newsEvents.persistent), newsEvents.persistent ? "DB 기준" : newsEvents.enabled ? "파일 fallback" : "꺼짐"],
    ["뉴스 최신", Boolean(newsLatest.collectedAt), newsLatestText],
    ["최신 수집값", Boolean(marketData.enabled && Number(marketData.itemCount ?? 0) > 0), marketDataText],
    ["가격 커버리지", usablePriceCount > 0, priceReadinessText],
    ["가격 기준", usablePriceCount > 0 && unknownBasisCount === 0, basisStatusText],
    ["최신값 갱신", Boolean(marketData.latestAt), marketLatestText],
    ["후보 데이터", Boolean(candidateData.enabled && Number(candidateData.itemCount ?? 0) > 0), candidateDataText],
    ["진입 데이터", Boolean(Number(candidateData.entryReadyCount ?? 0) > 0), candidateReadyText],
    ["누락 항목", candidateMissingText === "누락 없음", candidateMissingText],
    ["최근 후보 저장", Boolean(candidateData.latestAt), candidateLatestText],
    ["보존성", decisionReady, persistenceText],
    ["최근 기록", Number(status.recentRunCount ?? 0) > 0, latestText],
    ["다음", decisionReady && status.writable, nextText]
  ];
  const canMigrate = Boolean(database.urlConfigured && database.ready);
  const canRetryDb = Boolean(database.urlConfigured);
  const actionMarkup = `
    <div class="storage-actions">
      <button type="button" data-storage-action="refresh">새로고침</button>
      <button type="button" data-storage-action="db-retry" ${canRetryDb ? "" : "disabled"}>DB 재연결</button>
      <button type="button" data-storage-action="migrate" ${canMigrate ? "" : "disabled"}>DB 이관 실행</button>
    </div>
  `;
  els.storageStatus.innerHTML = `
    ${rows
      .map(([label, ok, value]) => {
        const tone = ok ? "ok" : "warn";
        return `
          <div>
            <span>${escapeHtml(label)}</span>
            <strong class="${tone}">${escapeHtml(value)}</strong>
          </div>
        `;
      })
      .join("")}
    ${actionMarkup}
  `;
  els.storageStatus.querySelectorAll("[data-storage-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      const action = button.dataset.storageAction;
      if (action === "refresh") {
        await refreshStorageStatus();
      }
      if (action === "db-retry") {
        await retryDatabaseConnection();
      }
      if (action === "migrate") {
        await runStorageMigration();
      }
    });
  });
}

function evidenceCountText(value, suffix = "건") {
  const count = Number(value ?? 0);
  return `${Number.isFinite(count) ? count : 0}${suffix}`;
}

function evidenceKindCount(status, key) {
  const byKind = status?.byKind ?? {};
  const required = status?.requiredKinds ?? {};
  const optional = status?.optionalKinds ?? {};
  return Number(required[key]?.count ?? optional[key]?.count ?? byKind[key] ?? 0);
}

function evidenceKindReady(status, key) {
  const required = status?.requiredKinds ?? {};
  const optional = status?.optionalKinds ?? {};
  const count = evidenceKindCount(status, key);
  return Boolean(required[key]?.ready ?? optional[key]?.ready ?? count > 0);
}

function evidenceCoverageText(value) {
  const numeric = Number(value ?? 0);
  if (!Number.isFinite(numeric) || numeric <= 0) return "0%";
  const percent = numeric <= 1 ? numeric * 100 : numeric;
  return `${Math.round(percent)}%`;
}

function renderEvidenceStatus() {
  if (!els.evidenceStatus) return;
  const status = state.evidenceStatus;
  if (!status) return;
  const readiness = status.readiness ?? {};
  const operationReady = Boolean(status.operationReady ?? readiness.operationReady);
  const decisionReady = Boolean(status.decisionReady ?? readiness.decisionReady);
  const marketData = status.marketData ?? {};
  const basisCounts = status.basisCounts ?? marketData.basisCounts ?? {};
  const priceCoverage = status.priceCoverage ?? marketData.priceCoverage ?? 0;
  const totalCount = Number(status.totalCount ?? status.rawEvents?.count ?? 0);
  const newsCount = evidenceKindCount(status, "news");
  const priceCount = evidenceKindCount(status, "price") || Number(marketData.itemCount ?? marketData.storedPriceCount ?? 0);
  const marketContextCount = evidenceKindCount(status, "marketContext");
  const disclosureCount = evidenceKindCount(status, "disclosure");
  const chartCount = evidenceKindCount(status, "chart");
  const orderbookCount = evidenceKindCount(status, "orderbook");
  const tradeCount = evidenceKindCount(status, "trade");
  const depthCount = chartCount + orderbookCount + tradeCount;
  const openAiPending = Number(status.openAiPendingCount ?? status.openAi?.pendingCount ?? 0);
  const stalePriceCount = Number(status.stalePriceCount ?? marketData.stalePriceCount ?? 0);
  const usablePriceCount = Number(marketData.usablePriceCount ?? status.usablePriceCount ?? priceCount ?? 0);
  const liveCount = Number(basisCounts.live ?? 0);
  const closedCount = Number(basisCounts.closed_baseline ?? 0);
  const lastGoodCount = Number(basisCounts.last_good ?? 0);
  const unknownCount = Number(basisCounts.unknown ?? 0);
  const basisText = [
    liveCount ? `실시간 ${liveCount}` : "",
    closedCount ? `마감 ${closedCount}` : "",
    lastGoodCount ? `마지막값 ${lastGoodCount}` : "",
    unknownCount ? `기준 미정 ${unknownCount}` : ""
  ].filter(Boolean).join(" · ") || "기준 없음";
  const gaps = Array.isArray(readiness.gaps) ? readiness.gaps : [];
  const nextAction = readiness.nextAction || status.nextAction || "근거 수집 상태 확인";
  const rows = [
    ["운영 판단", operationReady, operationReady ? "가능" : "보강 필요"],
    ["최종 판단", decisionReady, decisionReady ? "가능" : "근거 보강"],
    ["저장", Boolean(status.persistent), status.persistent ? "Postgres" : status.implementation || "미확인"],
    ["전체 근거", totalCount > 0, evidenceCountText(totalCount)],
    ["뉴스/트렌드", evidenceKindReady(status, "news"), evidenceCountText(newsCount)],
    ["가격 기준", usablePriceCount > 0, `${evidenceCoverageText(priceCoverage)} · ${basisText}`],
    ["시장 환경", evidenceKindReady(status, "marketContext"), evidenceCountText(marketContextCount)],
    ["공시/IR", evidenceKindReady(status, "disclosure"), disclosureCount ? evidenceCountText(disclosureCount) : "부족"],
    ["심화 데이터", depthCount > 0, `차트 ${chartCount} · 호가 ${orderbookCount} · 체결 ${tradeCount}`],
    ["OpenAI 대기", openAiPending === 0, evidenceCountText(openAiPending)],
    ["누락", gaps.length === 0, gaps.length ? gaps.slice(0, 3).join(" · ") : "없음"],
    ["최근 수집", Boolean(status.latestAt), status.latestAt ? timeLabel(status.latestAt) : "-"],
    ["다음", decisionReady, nextAction]
  ];
  setHtmlIfChanged(els.evidenceStatus, rows
    .map(([label, ok, value]) => {
      const tone = ok ? "ok" : "warn";
      return `
        <div>
          <span>${escapeHtml(label)}</span>
          <strong class="${tone}">${escapeHtml(value)}</strong>
        </div>
      `;
    })
    .join(""));
}

function stockMasterStorageLabel(value) {
  if (value === "database") return "DB 저장";
  if (value === "filesystem") return "파일 저장";
  if (value === "none") return "미생성";
  return value || "-";
}

function renderStockMasterStatus() {
  if (!els.stockMasterStatus) return;
  const status = state.stockMasterStatus;
  if (!status) return;
  const generated = status.generated ?? {};
  const active = status.active ?? {};
  const config = status.config ?? {};
  const stateInfo = status.state ?? {};
  const sourceCounts = generated.sourceCounts ?? {};
  const generatedAt = generated.generatedAt ? timeLabel(generated.generatedAt) : "-";
  const sourceText = Object.entries(sourceCounts)
    .filter(([, count]) => Number(count) > 0)
    .slice(0, 4)
    .map(([source, count]) => `${source.replace("stock-search-", "").replace("candidate-", "")} ${count}`)
    .join(" · ");
  const refreshMinutes = Math.max(1, Math.round(Number(config.refreshSeconds ?? 0) / 60));
  const rows = [
    ["저장 위치", generated.exists, stockMasterStorageLabel(status.storage)],
    ["저장 마스터", Number(generated.count ?? 0) > 0, `${generated.count ?? 0}개`],
    ["활성 검색", Number(active.count ?? 0) > 0, `${active.count ?? 0}개`],
    ["저장본 사용", Boolean(active.usesGeneratedMaster), active.usesGeneratedMaster ? "사용 중" : "직접 병합"],
    ["최근 생성", Boolean(generated.generatedAt), generatedAt],
    ["자동 갱신", Boolean(config.autoRefreshEnabled), config.autoRefreshEnabled ? `${refreshMinutes}분 기준` : "꺼짐"],
    ["DB 연결", Boolean(config.databaseReady || !config.databaseEnabled), config.databaseEnabled ? (config.databaseReady ? "DB 준비" : "DB 대기") : "파일 fallback"],
    ["출처", Boolean(sourceText), sourceText || "-"]
  ];
  const lastError = stateInfo.lastError
    ? `<div><span>최근 오류</span><strong class="warn">${escapeHtml(stateInfo.lastError)}</strong></div>`
    : "";
  const actionMarkup = `
    <div class="storage-actions">
      <button type="button" data-stock-master-action="refresh">새로고침</button>
      <button type="button" data-stock-master-action="rebuild">마스터 재생성</button>
    </div>
  `;
  els.stockMasterStatus.innerHTML = `
    ${rows
      .map(([label, ok, value]) => {
        const tone = ok ? "ok" : "warn";
        return `
          <div>
            <span>${escapeHtml(label)}</span>
            <strong class="${tone}">${escapeHtml(value)}</strong>
          </div>
        `;
      })
      .join("")}
    ${lastError}
    ${actionMarkup}
  `;
  els.stockMasterStatus.querySelectorAll("[data-stock-master-action]").forEach((button) => {
    button.addEventListener("click", async () => {
      const action = button.dataset.stockMasterAction;
      if (action === "refresh") {
        await refreshStockMasterStatus();
      }
      if (action === "rebuild") {
        await rebuildStockMaster();
      }
    });
  });
}

async function refreshStockMasterStatus() {
  const buttons = els.stockMasterStatus?.querySelectorAll("[data-stock-master-action]") ?? [];
  buttons.forEach((button) => {
    button.disabled = true;
  });
  try {
    state.stockMasterStatus = await safeFetchJson("/api/stocks/master/status", statusFallbacks().stockMaster, 10000);
  } finally {
    renderStockMasterStatus();
  }
}

async function rebuildStockMaster() {
  const buttons = els.stockMasterStatus?.querySelectorAll("[data-stock-master-action]") ?? [];
  buttons.forEach((button) => {
    button.disabled = true;
  });
  startActivity("검색 마스터 재생성 중", "OpenDART 캐시, 확장 마스터, ETF 사전을 통합합니다");
  try {
    const result = await postJson("/api/stocks/master/refresh", {}, 30000);
    const latest = await safeFetchJson("/api/stocks/master/status", statusFallbacks().stockMaster, 10000);
    state.stockMasterStatus = {
      ...latest,
      state: {
        ...(latest.state ?? {}),
        lastRefresh: result
      }
    };
  } catch (error) {
    const current = state.stockMasterStatus ?? statusFallbacks().stockMaster;
    state.stockMasterStatus = {
      ...current,
      state: {
        ...(current.state ?? {}),
        lastError: error?.name === "AbortError" ? "검색 마스터 재생성 지연" : "검색 마스터 재생성 실패"
      }
    };
  } finally {
    finishActivity();
    renderStockMasterStatus();
  }
}

async function refreshStorageStatus() {
  const buttons = els.storageStatus?.querySelectorAll("[data-storage-action]") ?? [];
  buttons.forEach((button) => {
    button.disabled = true;
  });
  try {
    state.storageStatus = await safeFetchJson("/api/storage/status", statusFallbacks().storage, 10000);
    state.evidenceStatus = await safeFetchJson("/api/evidence/status", statusFallbacks().evidence, 10000);
  } finally {
    renderStorageStatus();
    renderEvidenceStatus();
  }
}

async function retryDatabaseConnection() {
  const buttons = els.storageStatus?.querySelectorAll("[data-storage-action]") ?? [];
  buttons.forEach((button) => {
    button.disabled = true;
  });
  startActivity("DB 재연결 확인 중", "Postgres 연결 백오프를 초기화하고 스키마를 다시 확인합니다");
  try {
    const payload = await postJson("/api/storage/db-retry", {}, 30000);
    state.storageStatus = payload.storage ?? await safeFetchJson("/api/storage/status?fresh=1", statusFallbacks().storage, 10000);
    state.evidenceStatus = await safeFetchJson("/api/evidence/status", statusFallbacks().evidence, 10000);
  } catch (error) {
    const current = state.storageStatus ?? statusFallbacks().storage;
    state.storageStatus = {
      ...current,
      database: {
        ...(current.database ?? {}),
        error: error?.name === "AbortError" ? "DB 재연결 응답 지연" : "DB 재연결 실패",
        nextAction: "Render Postgres Available 상태와 Web Service 환경변수/재시작을 확인"
      }
    };
  } finally {
    finishActivity();
    renderStorageStatus();
    renderEvidenceStatus();
  }
}

async function runStorageMigration() {
  const buttons = els.storageStatus?.querySelectorAll("[data-storage-action]") ?? [];
  buttons.forEach((button) => {
    button.disabled = true;
  });
  startActivity("DB 이관 실행 중", "파일 저장 후보 풀과 스냅샷을 Postgres에 확인합니다");
  try {
    const payload = await postJson("/api/storage/migrate", {}, 60000);
    state.storageStatus = payload.storage ?? await safeFetchJson("/api/storage/status", statusFallbacks().storage, 10000);
    state.evidenceStatus = await safeFetchJson("/api/evidence/status", statusFallbacks().evidence, 10000);
  } catch (error) {
    const current = state.storageStatus ?? statusFallbacks().storage;
    state.storageStatus = {
      ...current,
      database: {
        ...(current.database ?? {}),
        error: error?.name === "AbortError" ? "DB 이관 응답 지연" : "DB 이관 실패",
        migration: {
          ...((current.database ?? {}).migration ?? {}),
          done: false,
          error: error?.name === "AbortError" ? "timeout" : "request-failed"
        }
      }
    };
  } finally {
    finishActivity();
    renderStorageStatus();
    renderEvidenceStatus();
  }
}

function isPositiveText(value) {
  const text = String(value ?? "").trim();
  return Boolean(text && text !== "-" && !text.startsWith("-"));
}

function parseDisplayNumber(value) {
  const text = String(value ?? "").replace(/,/g, "");
  if (!text || text.trim() === "-") return null;
  const match = text.match(/-?\d+(?:\.\d+)?/);
  if (!match) return null;
  const number = Number(match[0]);
  return Number.isFinite(number) ? number : null;
}

function parseDisplayPercent(value) {
  const match = String(value ?? "").match(/[+-]?\d+(?:\.\d+)?/);
  if (!match) return null;
  const number = Number(match[0]);
  return Number.isFinite(number) ? number : null;
}

function formatPriceFromTemplate(number, template = "") {
  if (!Number.isFinite(number)) return "-";
  const text = String(template ?? "");
  if (text.includes("$")) {
    return `$${number.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
  if (text.includes("원") || !text.includes(".")) {
    return `${Math.round(number).toLocaleString("ko-KR")}원`;
  }
  return number.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatPriceRange(low, high, template = "") {
  return `${formatPriceFromTemplate(low, template)} ~ ${formatPriceFromTemplate(high, template)}`;
}

function selectedHoldingFor(item) {
  const serverHolding = item?.portfolio?.holding;
  if (serverHolding && typeof serverHolding === "object") return serverHolding;
  const holdings = Array.isArray(state.portfolioStatus?.items) ? state.portfolioStatus.items : [];
  const symbol = String(item?.symbol ?? "").toUpperCase();
  const name = String(item?.name ?? "").replace(/\s+/g, "").toLowerCase();
  return (
    holdings.find((holding) => String(holding.symbol ?? "").toUpperCase() === symbol) ||
    holdings.find((holding) => String(holding.name ?? "").replace(/\s+/g, "").toLowerCase() === name) ||
    null
  );
}

function decisionGroupForDisplay(item) {
  const holding = selectedHoldingFor(item);
  if (holding) {
    return {
      key: "holding",
      label: "보유 대응",
      priority: 1,
      score: Number(item?.decisionGroup?.score ?? item?.totalScore ?? 0),
      reason: `${holding.judgement ?? "보유"} · ${holding.profitLossRate ?? "-"}`
    };
  }
  const group = item?.decisionGroup ?? {};
  return {
    key: group.key || "wait",
    label: group.label || "가격대 대기",
    priority: Number(group.priority ?? 3),
    score: Number(group.score ?? item?.totalScore ?? 0),
    reason: group.reason || "가격, 뉴스, 수급 조건을 추가 확인합니다."
  };
}

function decisionGroupClass(value) {
  return `group-${String(value || "wait").replace(/[^a-z0-9_-]/gi, "").toLowerCase() || "wait"}`;
}

function clampNumber(value, min, max) {
  const number = Number(value);
  if (!Number.isFinite(number)) return min;
  return Math.min(max, Math.max(min, number));
}

function priceBandFor(item, current, group, change, score) {
  const readiness = Number(item?.triggerReadiness ?? 0);
  const opportunity = Number(item?.hiddenOpportunity?.score ?? 0);
  const strength = clampNumber((score * 0.45) + (readiness * 0.35) + (opportunity * 1.2), 0, 100);
  const hot = change != null && change >= 3;
  const weak = change != null && change <= -2;
  const groupKey = group.key || "wait";

  let entryLowPct = 0.012;
  let entryHighPct = 0.004;
  let pullbackPct = 0.025;
  let chasePct = 0.025;
  let stopPct = 0.036;
  let trimPct = 0.052;

  if (groupKey === "action") {
    entryLowPct = strength >= 78 ? 0.006 : 0.01;
    entryHighPct = strength >= 78 ? 0.006 : 0.003;
    pullbackPct = 0.018;
    stopPct = 0.032;
    trimPct = 0.058;
  } else if (groupKey === "hidden") {
    entryLowPct = 0.014;
    entryHighPct = 0.002;
    pullbackPct = 0.03;
    stopPct = 0.04;
    trimPct = 0.05;
  } else if (groupKey === "momentum") {
    entryLowPct = 0.01;
    entryHighPct = 0.004;
    pullbackPct = 0.024;
    stopPct = 0.038;
    trimPct = 0.055;
  } else if (groupKey === "holding") {
    entryLowPct = 0.018;
    entryHighPct = 0;
    pullbackPct = 0.028;
    stopPct = 0.045;
    trimPct = 0.035;
  } else if (groupKey === "exclude") {
    entryLowPct = 0.035;
    entryHighPct = 0.02;
    pullbackPct = 0.05;
    stopPct = 0.03;
    trimPct = 0.025;
  }

  if (hot) {
    const heatOffset = clampNumber((change - 2) / 100, 0.01, 0.05);
    entryLowPct = Math.max(entryLowPct, 0.02 + heatOffset * 0.4);
    entryHighPct = -0.004;
    pullbackPct = Math.max(pullbackPct, 0.032 + heatOffset * 0.25);
    chasePct = 0.012;
    stopPct = Math.max(stopPct, 0.04);
  } else if (weak) {
    entryLowPct = Math.max(entryLowPct, 0.018);
    entryHighPct = -0.002;
    pullbackPct = Math.max(pullbackPct, 0.035);
    chasePct = 0.015;
    stopPct = 0.03;
  }

  const entryLow = current * (1 - entryLowPct);
  const entryHigh = current * (1 + entryHighPct);
  return {
    strength: Math.round(strength),
    entryLow,
    entryHigh,
    pullback: current * (1 - pullbackPct),
    chaseLimit: current * (1 + chasePct),
    stopLine: entryLow * (1 - stopPct),
    trimLine: current * (1 + trimPct),
    reboundLine: weak ? current * 1.012 : null,
    entryRangeText: formatPriceRange(Math.min(entryLow, entryHigh), Math.max(entryLow, entryHigh), item?.price ?? ""),
    template: item?.price ?? ""
  };
}

function tradePlanFromFinalDecision(item, decision, holding = null) {
  const signalCards = Array.isArray(decision.signalCards) ? decision.signalCards : [];
  const rows = Array.isArray(decision.rows) ? decision.rows : [];
  const reasons = Array.isArray(decision.reasons) ? decision.reasons : [];
  const closedBaseline = isClosedBaselineCandidate(item);
  const action = closedBaseline
    ? basisAwareDecisionLabel(item, decision.action, "다음 장 관찰")
    : basisAwareDecisionLabel(item, decision.action);
  const summary = closedBaseline
    ? basisAwareDecisionSummary(item, decision.summary)
    : basisAwareDecisionSummary(item, decision.summary || "가격, 신뢰도, 수급 조건을 추가 확인합니다.");
  const displaySignalCards = signalCards.map(([label, value]) => [
    label,
    basisAwareDecisionLabel(item, value, label === "현재 판단" && closedBaseline ? "다음 장 관찰" : String(value ?? ""))
  ]);
  return {
    action,
    tone: decision.tone || "wait",
    summary,
    holding,
    hasPrice: Boolean(item?.price),
    signalCards: displaySignalCards.length
      ? displaySignalCards
      : [
          ["현재 판단", action],
          ["매수 구간", decision.priceLevels?.entryRange || "현재가 확인 후 계산"],
          ["위험 기준", decision.priceLevels?.stopLine ? `${decision.priceLevels.stopLine} 이탈` : "-"]
        ],
    rows: rows.length
      ? rows
      : [
          ["관찰 매수", decision.priceLevels?.entryRange || "현재가 확인 후 계산"],
          ["눌림 대기", decision.priceLevels?.pullback ? `${decision.priceLevels.pullback} 부근 확인` : "-"],
          ["반등 확인", decision.priceLevels?.reboundLine ? `${decision.priceLevels.reboundLine} 회복` : "약세 전환 시 확인"],
          ["추격 금지", decision.priceLevels?.chaseLimit ? `${decision.priceLevels.chaseLimit} 이상` : "-"],
          ["손절 점검", decision.priceLevels?.stopLine ? `${decision.priceLevels.stopLine} 이탈` : "-"],
          ["분할매도", decision.priceLevels?.trimLine ? `${decision.priceLevels.trimLine} 이상 또는 과열 신호` : "-"]
        ],
    reasons: uniqueTexts(
      [
        ...reasons,
        decision.tradeAllowed ? "서버 최종 판단: 조건부 매수 가능" : "서버 최종 판단: 추가 확인 우선"
      ],
      5
    )
  };
}

function tradePlan(item) {
  const score = Number(item?.totalScore ?? 0);
  const current = parseDisplayNumber(item?.price);
  const change = parseDisplayPercent(item?.change);
  const group = decisionGroupForDisplay(item);
  const holding = selectedHoldingFor(item);
  if (item?.finalDecision) {
    return tradePlanFromFinalDecision(item, item.finalDecision, holding);
  }
  const holdingRate = parseDisplayPercent(holding?.profitLossRate);
  const holdingJudgement = String(holding?.judgement ?? "");
  const hasPrice = Number.isFinite(current);
  const isHeld = Boolean(holding);
  const isAvoid = group.key === "exclude" || String(item?.verdict ?? "").includes("회피") || score < 55;
  const overheated = change != null && change >= 3;
  const weak = change != null && change <= -2;
  const band = hasPrice ? priceBandFor(item, current, group, change, score) : null;
  const closedBaseline = isClosedBaselineCandidate(item);
  const basis = priceBasisKeyForDisplay(item);
  const retained = Boolean(item?.livePrice?.retained || item?.displayRetained);
  const missingPriceText = closedBaseline
    ? "장마감 기준가로 판단"
    : basis === "last_good" || retained
      ? "마지막 정상값 확인"
      : "DB 가격 저장 후 계산";

  let action = closedBaseline
    ? "다음 장 관찰"
    : basis === "last_good" || retained
      ? "마지막 정상값 확인"
      : "데이터 보강 대기";
  let tone = "wait";
  let summary = basisAwareDecisionSummary(item);
  if (hasPrice) {
    if (isHeld && (holdingJudgement.includes("분할매도") || (holdingRate != null && holdingRate >= 12))) {
      action = "분할매도 검토";
      tone = "sell";
      summary = "보유 수익과 후보 점수가 높아 일부 이익 실현 여부를 먼저 점검합니다.";
    } else if (isHeld && (holdingJudgement.includes("손절") || (holdingRate != null && holdingRate <= -7))) {
      action = "리스크 축소 점검";
      tone = "risk";
      summary = "손실이 커진 보유 종목은 추가 매수보다 기준 이탈 여부를 먼저 봅니다.";
    } else if (isAvoid) {
      action = "오늘은 제외";
      tone = "risk";
      summary = "점수나 리스크 조건이 부족해 신규 진입보다 관찰 제외가 우선입니다.";
    } else if (overheated) {
      action = isHeld ? "보유 유지" : "눌림 대기";
      tone = "wait";
      summary = "이미 오른 구간은 추격하지 않고 눌림 또는 재돌파 확인을 기다립니다.";
    } else if (weak) {
      action = "반등 확인 대기";
      tone = "wait";
      summary = "가격이 약한 구간이라 거래량이 동반된 반등 확인 후 판단합니다.";
    } else if (group.key === "action" || score >= 75) {
      action = isHeld ? "보유 유지" : "관찰 매수 후보";
      tone = "buy";
      summary = "점수와 가격대가 무리하지 않아 조건 충족 시 관찰 후보입니다.";
    } else if (group.key === "hidden") {
      action = "숨은 기회 관찰";
      tone = "wait";
      summary = "재료는 포착됐지만 즉시 매수보다 가격 반영 여부를 확인합니다.";
    } else if (group.key === "momentum") {
      action = "모멘텀 확인";
      tone = "wait";
      summary = "뉴스와 수급 반응은 있으나 돌파 유지와 거래대금을 함께 확인합니다.";
    } else {
      action = "가격대 대기";
      tone = "wait";
      summary = "후보 점수는 있으나 바로 진입보다 조건에 맞는 가격대까지 기다립니다.";
    }
  }

  const template = item?.price ?? "";
  const immediateText =
    !hasPrice
      ? missingPriceText
      : tone === "buy"
        ? `구간 안착 시 관찰`
        : tone === "sell"
          ? `일부 이익 실현 점검`
          : tone === "risk"
            ? `신규 진입 금지`
            : weak
              ? `반등선 회복 대기`
              : overheated
                ? `눌림 확인 전 대기`
                : closedBaseline
                  ? `다음 장 확인`
                  : `가격대 관찰`;

  return {
    action,
    tone,
    summary,
    holding,
    hasPrice,
    signalCards: [
      ["현재 판단", immediateText],
      ["매수 구간", band ? band.entryRangeText : missingPriceText],
      ["위험 기준", band ? `${formatPriceFromTemplate(band.stopLine, template)} 이탈` : "-"]
    ],
    rows: [
      ["관찰 매수", band ? band.entryRangeText : missingPriceText],
      ["눌림 대기", band ? `${formatPriceFromTemplate(band.pullback, template)} 부근 확인` : "-"],
      ["반등 확인", band?.reboundLine ? `${formatPriceFromTemplate(band.reboundLine, template)} 회복` : "약세 전환 시 확인"],
      ["추격 금지", band ? `${formatPriceFromTemplate(band.chaseLimit, template)} 이상` : "-"],
      ["손절 점검", band ? `${formatPriceFromTemplate(band.stopLine, template)} 이탈` : "-"],
      ["분할매도", band ? `${formatPriceFromTemplate(band.trimLine, template)} 이상 또는 과열 신호` : "-"],
      ["보유 상태", holding ? `${holding.judgement ?? "보유"} · ${holding.profitLossRate ?? "-"}` : "미보유"]
    ],
    reasons: uniqueTexts(
      [
        `후보 점수 ${score}/100`,
        band ? `가격 판단 강도 ${band.strength}/100` : "",
        `후보 분류 ${group.label}`,
        change != null ? `현재 등락률 ${item.change}` : "",
        item.hiddenOpportunity?.score ? `숨은 기회 ${item.hiddenOpportunity.score}/18` : "",
        holding ? `내 보유 상태 ${holding.judgement ?? "보유"} · ${holding.profitLossRate ?? "-"}` : "내 보유 없음",
        item.aiAnalysis?.actionBias ? `AI 판단 ${actionBiasLabel(item.aiAnalysis.actionBias)}` : ""
      ],
      4
    )
  };
}

function renderPortfolioStatus() {
  if (!els.portfolioStatus) return;
  const status = state.portfolioStatus;
  if (!status) return;
  const summary = status.summary ?? {};
  const buyingPower = status.buyingPower ?? {};
  const items = Array.isArray(status.items) ? status.items : [];
  const krwPower = buyingPower.KRW?.cashBuyingPower ?? "-";
  const usdPower = buyingPower.USD?.cashBuyingPower ?? "-";
  const rows = [
    ["보유", Number(summary.holdingCount ?? 0) > 0, `${summary.holdingCount ?? 0}종목`],
    ["총 손익률", isPositiveText(summary.profitLossRate), summary.profitLossRate ?? "-"],
    ["오늘", isPositiveText(summary.dailyProfitLossRate), summary.dailyProfitLossRate ?? "-"],
    ["매수 가능", krwPower !== "-" || usdPower !== "-", `${krwPower}${usdPower !== "-" ? ` · ${usdPower}` : ""}`]
  ];
  const holdingRows = items.slice(0, 2).map((item) => [
    item.name || item.symbol || "보유 종목",
    !String(item.judgement ?? "").includes("경계"),
    `${item.judgement ?? "보유"} · ${item.profitLossRate ?? "-"}`
  ]);
  setHtmlIfChanged(els.portfolioStatus, [...rows, ...holdingRows]
    .map(([label, ok, value]) => {
      const tone = ok ? "ok" : "warn";
      return `
        <div>
          <span>${escapeHtml(label)}</span>
          <strong class="${tone}">${escapeHtml(value)}</strong>
        </div>
      `;
    })
    .join(""));
}

function renderSnapshotHistory() {
  if (!els.snapshotHistory) return;
  const runs = state.schedulerStatus?.recentRuns ?? [];
  if (!Array.isArray(runs) || !runs.length) {
    els.snapshotHistory.innerHTML = `<div class="history-empty">아직 저장된 스냅샷이 없습니다</div>`;
    return;
  }
  const viewingId = state.viewingSnapshot?.id ?? "";
  const backButton = state.viewingSnapshot
    ? `<button type="button" class="history-current" id="currentDashboardButton">현재 보기</button>`
    : "";
  els.snapshotHistory.innerHTML = `
    ${backButton}
    ${runs
      .slice(0, 6)
      .map((run) => {
        const active = run.id === viewingId ? "active" : "";
        return `
          <button type="button" class="history-item ${active}" data-run-id="${escapeHtml(run.id)}">
            <span class="history-row">
              <strong>${escapeHtml(modeLabel(run.mode))}</strong>
              <span>${escapeHtml(timeLabel(run.createdAt))}</span>
            </span>
            <span class="history-meta">
              ${escapeHtml(triggerLabel(run.trigger))} · 후보 ${escapeHtml(run.summary?.candidateCount ?? 0)} · 준비 ${escapeHtml(run.summary?.readyCount ?? 0)}
            </span>
            <span class="history-top">${escapeHtml(snapshotTopText(run))}</span>
          </button>
        `;
      })
      .join("")}
  `;
  const currentButton = document.querySelector("#currentDashboardButton");
  if (currentButton) {
    currentButton.addEventListener("click", loadDashboard);
  }
  els.snapshotHistory.querySelectorAll("[data-run-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      await loadSnapshotRun(button.dataset.runId);
    });
  });
}

async function loadSnapshotRun(runId) {
  if (!runId) return;
  try {
    const payload = await fetchJson(`/api/scheduler/runs/${encodeURIComponent(runId)}`, 15000);
    if (!payload.dashboard) return;
    state.dashboard = payload.dashboard;
    state.viewingSnapshot = payload.record ?? { id: runId };
    state.selectedSymbol = state.dashboard.selected?.symbol ?? state.dashboard.candidates?.[0]?.symbol ?? null;
    render();
  } catch (error) {
    state.schedulerStatus = {
      ...(state.schedulerStatus ?? {}),
      state: {
        ...((state.schedulerStatus ?? {}).state ?? {}),
        lastError: "스냅샷을 불러오지 못했습니다."
      }
    };
    renderSchedulerStatus();
    renderSnapshotHistory();
  }
}

async function runSchedulerMode(mode) {
  if (!mode) return;
  const buttons = els.schedulerStatus?.querySelectorAll("[data-scheduler-mode]") ?? [];
  buttons.forEach((button) => {
    button.disabled = true;
  });
  try {
    const payload = await postJson("/api/scheduler/run", { mode }, 60000);
    state.schedulerStatus = payload.status ?? state.schedulerStatus;
    state.storageStatus = await safeFetchJson("/api/storage/status", statusFallbacks().storage, 5000);
    state.evidenceStatus = await safeFetchJson("/api/evidence/status", statusFallbacks().evidence, 5000);
    state.stockMasterStatus = await safeFetchJson("/api/stocks/master/status", statusFallbacks().stockMaster, 5000);
    maybeNotifySchedulerRun(state.schedulerStatus);
    renderSchedulerStatus();
    renderStorageStatus();
    renderEvidenceStatus();
    renderStockMasterStatus();
    renderSnapshotHistory();
  } catch (error) {
    state.schedulerStatus = {
      ...(state.schedulerStatus ?? {}),
      state: {
        ...((state.schedulerStatus ?? {}).state ?? {}),
        lastError: error?.name === "AbortError" ? "실행 시간이 지연되었습니다." : "수동 실행에 실패했습니다."
      }
    };
    renderSchedulerStatus();
  } finally {
    buttons.forEach((button) => {
      button.disabled = false;
    });
  }
}

async function runDiscoveryBot() {
  const buttons = els.discoveryBotStatus?.querySelectorAll("[data-discovery-action]") ?? [];
  buttons.forEach((button) => {
    button.disabled = true;
  });
  startActivity("발굴 봇 실행 중", "최신 뉴스, 가격, 공시 신호로 후보를 다시 점검합니다");
  try {
    const payload = await postJson("/api/discovery/run", { mode: state.mode }, 70000);
    state.discoveryBotStatus = payload.status ?? state.discoveryBotStatus;
    state.evidenceStatus = await safeFetchJson("/api/evidence/status", statusFallbacks().evidence, 5000);
    state.stockMasterStatus = await safeFetchJson("/api/stocks/master/status", statusFallbacks().stockMaster, 5000);
    renderDiscoveryBotStatus();
    renderEvidenceStatus();
    renderStockMasterStatus();
  } catch (error) {
    state.discoveryBotStatus = {
      ...(state.discoveryBotStatus ?? {}),
      state: {
        ...((state.discoveryBotStatus ?? {}).state ?? {}),
        lastError: error?.name === "AbortError" ? "발굴 실행 시간이 지연되었습니다." : "발굴 봇 실행에 실패했습니다."
      }
    };
    renderDiscoveryBotStatus();
  } finally {
    finishActivity();
    buttons.forEach((button) => {
      button.disabled = false;
    });
  }
}

function renderMarketStatus() {
  if (!els.marketStatus) return;
  const marketStatus = state.dashboard?.integrations?.market;
  const indexStatus = marketStatus?.indices;
  const fxStatus = marketStatus?.fx;
  const indexOk = indexStatus?.source === "index-api" || indexStatus?.source === "index-api-partial";
  const fxOk = fxStatus?.source === "fx-api";
  const rows = [
    [
      "지수 조회",
      indexOk,
      indexStatus?.source === "index-api"
        ? `${indexStatus.provider ?? "API"} ${indexStatus.count ?? 0}건`
        : indexStatus?.source === "index-api-partial"
          ? `${indexStatus.provider ?? "API"} 일부`
          : fallbackStatusLabel(indexStatus, "대체 지수")
    ],
    [
      "환율 조회",
      fxOk,
      fxStatus?.source === "fx-api" ? `${fxStatus.provider ?? "API"}` : fallbackStatusLabel(fxStatus, "대체 환율")
    ]
  ];
  els.marketStatus.innerHTML = rows
    .map(([label, ok, value]) => {
      const tone = ok ? "ok" : "warn";
      return `
        <div>
          <span>${escapeHtml(label)}</span>
          <strong class="${tone}">${escapeHtml(value)}</strong>
        </div>
      `;
    })
    .join("");
}

function renderNetworkStatus() {
  if (!els.networkStatus) return;
  const status = state.networkStatus;
  const rows = [
    ["현재 외부 IP", Boolean(status?.ip), status?.ip || "확인 실패"],
    [
      "확인 방식",
      status?.source === "external-check",
      status?.source === "external-check" ? "외부 조회" : "대시보드 확인"
    ],
    [
      "등록 위치",
      true,
      "Toss 허용 IP"
    ],
    [
      "주의",
      !status?.error,
      status?.error ? shortText(status.detail || status.message || status.error, 28) : "범위/고정IP 확인"
    ]
  ];
  els.networkStatus.innerHTML = rows
    .map(([label, ok, value]) => {
      const tone = ok ? "ok" : "warn";
      return `
        <div>
          <span>${escapeHtml(label)}</span>
          <strong class="${tone}">${escapeHtml(value)}</strong>
        </div>
      `;
    })
    .join("");
}

function renderTossStatus() {
  const status = state.tossStatus;
  if (!status) return;
  const priceStatus = state.dashboard?.integrations?.toss?.prices;
  const candleStatus = state.dashboard?.integrations?.toss?.candles;
  const orderbookStatus = state.dashboard?.integrations?.toss?.orderbook;
  const tradesStatus = state.dashboard?.integrations?.toss?.trades;
  const baselineDriftCount = priceStatus?.baselineDriftCount ?? 0;
  const tossIssue = firstTossIssue([priceStatus, candleStatus, orderbookStatus, tradesStatus]);
  const priceSourceValue =
    priceStatus?.source === "toss"
      ? `토스 ${priceStatus.priceCount ?? 0}건${baselineDriftCount > 0 ? ` · 기준가 차이 ${baselineDriftCount}건` : ""}`
      : tossSourceLabel(priceStatus, status.livePricesEnabled, "priceCount");
  const rows = [
    ["Client ID", status.clientIdConfigured, status.clientIdPreview || "미설정"],
    ["Client Secret", status.clientSecretConfigured, status.clientSecretConfigured ? "설정됨" : "미설정"],
    ["토큰 발급", status.readyForTokenIssue, status.readyForTokenIssue ? "준비됨" : "대기"],
    ["시세 조회", status.readyForMarketData, status.readyForMarketData ? "가능" : "대기"],
    ["자산 조회", status.readyForAccountData, status.livePortfolioEnabled ? "준비됨" : "꺼짐"],
    ["오류 사유", !tossIssue, tossIssue || "없음"],
    ["가격 live", status.livePricesEnabled, status.livePricesEnabled ? "켜짐" : "꺼짐"],
    [
      "상세 범위",
      status.liveCandlesEnabled || status.liveOrderbookEnabled || status.liveTradesEnabled,
      `차트 ${status.candleMaxCandidates ?? "-"} · 호가 ${status.orderbookMaxCandidates ?? "-"} · 체결 ${status.tradesMaxCandidates ?? "-"}`
    ],
    [
      "가격 출처",
      priceStatus?.source === "toss" && baselineDriftCount === 0,
      priceSourceValue
    ],
    ["차트 live", status.liveCandlesEnabled, status.liveCandlesEnabled ? "켜짐" : "꺼짐"],
    [
      "차트 출처",
      candleStatus?.source === "toss" && (candleStatus.candleCount ?? 0) > 0,
      candleStatus?.source === "toss" && (candleStatus.candleCount ?? 0) > 0
        ? `토스 ${candleStatus.candleCount ?? 0}건`
        : (candleStatus?.staleCount ?? 0) > 0
          ? `오래됨 ${candleStatus.staleCount}건`
          : tossSourceLabel(candleStatus, status.liveCandlesEnabled, "candleCount")
    ],
    ["호가 live", status.liveOrderbookEnabled, status.liveOrderbookEnabled ? "켜짐" : "꺼짐"],
    [
      "호가 출처",
      orderbookStatus?.source === "toss" && (orderbookStatus.orderbookCount ?? 0) > 0,
      orderbookStatus?.source === "toss" && (orderbookStatus.orderbookCount ?? 0) > 0
        ? `토스 ${orderbookStatus.orderbookCount ?? 0}건`
        : tossSourceLabel(orderbookStatus, status.liveOrderbookEnabled, "orderbookCount")
    ],
    ["체결 live", status.liveTradesEnabled, status.liveTradesEnabled ? "켜짐" : "꺼짐"],
    [
      "체결 출처",
      tradesStatus?.source === "toss" && (tradesStatus.tradeCount ?? 0) > 0,
      tradesStatus?.source === "toss" && (tradesStatus.tradeCount ?? 0) > 0
        ? `토스 ${tradesStatus.tradeCount ?? 0}건`
        : tossSourceLabel(tradesStatus, status.liveTradesEnabled, "tradeCount")
    ]
  ];
  setHtmlIfChanged(els.tossStatus, rows
    .map(([label, ok, value]) => {
      const tone = ok ? "ok" : "warn";
      return `
        <div>
          <span>${escapeHtml(label)}</span>
          <strong class="${tone}">${escapeHtml(value)}</strong>
        </div>
      `;
    })
    .join(""));
}

function tossSourceLabel(status, liveEnabled, countKey) {
  if (!liveEnabled || status?.enabled === false) return "라이브 꺼짐";
  if (!status) return "확인 중";
  if (status.error) return status.status ? `오류 ${status.status}` : "오류";
  if (status.source === "retained") return "이전값 유지";
  if (status.source === "skipped") return "후보 제한";
  if (status.source === "stale") return "데이터 오래됨";
  if (status.source === "sample") return fallbackStatusLabel(status, "대체값");
  if (status.source === "toss") return `토스 ${status[countKey] ?? 0}건`;
  const message = String(status.message ?? "");
  if (message.includes("응답이 비어")) return "응답 없음";
  if (message.includes("환경변수")) return "키 설정 대기";
  if (message.includes("꺼져")) return "라이브 꺼짐";
  if (message.includes("제한")) return "후보 제한";
  return "대체 데이터";
}

function firstTossIssue(statuses) {
  const failed = statuses.find((status) => status?.error);
  if (!failed) return "";
  const detail = String(failed.detail ?? failed.message ?? failed.error ?? "");
  const lower = detail.toLowerCase();
  if (failed.status === 401 || lower.includes("unauthorized") || lower.includes("invalid_token")) {
    return "토큰/키 확인";
  }
  if (
    failed.status === 403 ||
    lower.includes("forbidden") ||
    lower.includes("ip") ||
    detail.includes("허용") ||
    detail.includes("권한")
  ) {
    return "IP/권한 확인";
  }
  if (failed.status === 404 || lower.includes("not found")) {
    return "경로 확인";
  }
  if (failed.status) return `HTTP ${failed.status}`;
  return String(failed.error ?? "오류");
}

function renderDartStatus() {
  const status = state.dartStatus;
  if (!status) return;
  const disclosureStatus = state.dashboard?.integrations?.dart?.disclosures;
  const rows = [
    ["API Key", status.apiKeyConfigured, status.apiKeyConfigured ? status.apiKeyPreview : "미설정"],
    ["공시 조회", status.readyForDisclosures, status.readyForDisclosures ? "가능" : "대기"],
    ["고유번호 캐시", status.corpCodeCacheExists, status.corpCodeCacheExists ? "있음" : "없음"],
    [
      "공시 출처",
      disclosureStatus?.source === "opendart",
      disclosureStatus?.source === "opendart" ? `${disclosureStatus.disclosureCount ?? 0}건` : fallbackStatusLabel(disclosureStatus, "대체 공시")
    ]
  ];
  els.dartStatus.innerHTML = rows
    .map(([label, ok, value]) => {
      const tone = ok ? "ok" : "warn";
      return `
        <div>
          <span>${escapeHtml(label)}</span>
          <strong class="${tone}">${escapeHtml(value)}</strong>
        </div>
      `;
    })
    .join("");
}

function newsSourceLabel(status, liveSource, sampleLabel = "대체 뉴스") {
  if (!status) return sampleLabel;
  if (status.source === liveSource) {
    return `${status.newsCount ?? status.disclosureCount ?? 0}건`;
  }
  if (status.error) {
    if (String(status.detail ?? "").includes("limit requests")) return "제한";
    return "오류";
  }
  if (status.source === "skipped") return "건너뜀";
  if (status.enabled === false) return "꺼짐";
  return fallbackStatusLabel(status, sampleLabel);
}

function renderNewsStatus() {
  const naver = state.newsStatus?.naver;
  const gdelt = state.newsStatus?.gdelt;
  if (!naver && !gdelt) return;
  const naverStatus = state.dashboard?.integrations?.news?.naver?.items;
  const gdeltStatus = state.dashboard?.integrations?.news?.gdelt?.items;
  const rows = [
    ["네이버 ID", naver?.clientIdConfigured, naver?.clientIdConfigured ? naver.clientIdPreview : "미설정"],
    ["네이버 Secret", naver?.clientSecretConfigured, naver?.clientSecretConfigured ? "설정됨" : "미설정"],
    [
      "네이버 출처",
      naverStatus?.source === "naver",
      newsSourceLabel(naverStatus, "naver")
    ],
    [
      "GDELT",
      gdelt?.readyForNews,
      gdelt?.readyForNews ? "키 없이 가능" : "꺼짐"
    ],
    [
      "글로벌 출처",
      gdeltStatus?.source === "gdelt",
      newsSourceLabel(gdeltStatus, "gdelt")
    ]
  ];
  els.newsStatus.innerHTML = rows
    .map(([label, ok, value]) => {
      const tone = ok ? "ok" : "warn";
      return `
        <div>
          <span>${escapeHtml(label)}</span>
          <strong class="${tone}">${escapeHtml(value)}</strong>
        </div>
      `;
    })
    .join("");
}

function renderOpenAIStatus() {
  const status = state.openaiStatus;
  if (!status || !els.openaiStatus) return;
  const analysisStatus = state.dashboard?.integrations?.openai?.analysis;
  const rows = [
    ["API Key", status.apiKeyConfigured, status.apiKeyConfigured ? status.apiKeyPreview : "미설정"],
    ["모델", status.model, status.model || "-"],
    [
      "분석",
      status.readyForAnalysis && analysisStatus?.source === "openai",
      status.readyForAnalysis ? "OpenAI 준비" : "로컬 사용"
    ],
    [
      "결과 출처",
      analysisStatus?.source === "openai",
      analysisStatus?.source === "openai"
        ? `OpenAI ${analysisStatus.openaiCount ?? 0}건`
        : `로컬 ${analysisStatus?.fallbackCount ?? analysisStatus?.localCount ?? 0}건`
    ]
  ];
  if (analysisStatus?.lastError) {
    rows.push(["실패 사유", false, shortText(analysisStatus.lastError, 38)]);
  }
  els.openaiStatus.innerHTML = rows
    .map(([label, ok, value]) => {
      const tone = ok ? "ok" : "warn";
      return `
        <div>
          <span>${escapeHtml(label)}</span>
          <strong class="${tone}">${escapeHtml(value)}</strong>
        </div>
      `;
    })
    .join("");
}

function renderPrinciples() {
  const principles = state.dashboard?.principles ?? [];
  els.principles.innerHTML = principles.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function applySearchQuery(query) {
  state.query = String(query ?? "").trim();
  state.selectedLookup = null;
  state.feedExpanded = false;
  if (els.searchInput) {
    els.searchInput.value = state.query;
  }
  if (state.searchTimer) {
    window.clearTimeout(state.searchTimer);
    state.searchTimer = null;
  }
  renderFeed();
  renderTradeDecisionStatus();
  renderDetail();
  refreshLivePrices();
  loadStockSearch();
}

function renderQuickSearch() {
  if (!els.quickSearch) return;
  const query = state.query.trim();
  if (query) {
    els.quickSearch.hidden = true;
    els.quickSearch.innerHTML = "";
    return;
  }
  const candidateTerms = (state.dashboard?.candidates ?? [])
    .slice(0, 4)
    .map((item) => ({
      label: item.name || item.symbol,
      query: item.name || item.symbol
    }));
  const items = uniqueTexts(
    [...candidateTerms, ...QUICK_SEARCH_PRESETS].map((item) => `${item.label}|${item.query}`),
    8
  )
    .map((value) => {
      const [label, searchQuery] = value.split("|");
      return { label, query: searchQuery || label };
    })
    .slice(0, 8);

  els.quickSearch.hidden = false;
  els.quickSearch.innerHTML = `
    ${items
      .map(
        (item) => `
          <button type="button" class="quick-search-chip" data-search-query="${escapeHtml(item.query)}">
            ${escapeHtml(item.label)}
          </button>
        `
      )
      .join("")}
  `;

  els.quickSearch.querySelectorAll("[data-search-query]").forEach((button) => {
    button.addEventListener("click", () => applySearchQuery(button.dataset.searchQuery));
  });
}

function primaryPriceGuide(plan) {
  const rows = plan?.rows ?? [];
  if (plan?.tone === "buy") {
    return rows.find(([label]) => label === "관찰 매수")?.[1] ?? "조건 충족 시 관찰";
  }
  if (plan?.tone === "sell") {
    return rows.find(([label]) => label === "분할매도")?.[1] ?? "일부 이익 실현 점검";
  }
  if (plan?.tone === "risk") {
    return "신규 진입 금지";
  }
  if (String(plan?.action ?? "").includes("눌림")) {
    return rows.find(([label]) => label === "눌림 대기")?.[1] ?? "눌림 구간 관찰";
  }
  if (String(plan?.action ?? "").includes("반등")) {
    return rows.find(([label]) => label === "반등 확인")?.[1] ?? "반등 구간 관찰";
  }
  return rows.find(([label]) => label === "관찰 매수")?.[1] ?? plan?.summary ?? "가격대 관찰";
}

function feedActionLabel(item, plan) {
  return primaryDecisionForDisplay(item, plan).label;
}

function candidateEvidenceSummary(item) {
  return item?.evidenceSummary && typeof item.evidenceSummary === "object" ? item.evidenceSummary : {};
}

function evidenceScoreValue(summary) {
  const raw = summary?.weightedScore ?? summary?.score;
  const value = Number(raw);
  return Number.isFinite(value) ? Math.max(0, Math.min(100, Math.round(value))) : null;
}

function scoreTextFromValue(value, suffix = "") {
  const score = Number(value);
  return Number.isFinite(score) ? `${Math.max(0, Math.min(100, Math.round(score)))}/100${suffix}` : "-";
}

function evidenceScoreText(summary) {
  const score = evidenceScoreValue(summary);
  return score == null ? "-" : scoreTextFromValue(score);
}

function evidenceSummaryLabel(summary) {
  if (summary?.label) return String(summary.label);
  const score = evidenceScoreValue(summary);
  if (score == null) return "근거 확인";
  if (score >= 75) return "근거 강함";
  if (score >= 60) return "검증 중";
  if (score >= 45) return "보강 필요";
  return "근거 약함";
}

function candidateSignalMeta(item) {
  const evidence = candidateEvidenceSummary(item);
  const counts = evidence.sourceCounts ?? {};
  const sourceCount = Array.isArray(item?.sources) ? item.sources.length : 0;
  const newsCount = Number(counts.news ?? evidence.newsCount ?? item?.trend?.newsCount ?? 0);
  const materialNews = Number(counts.materialNews ?? evidence.materialNews ?? item?.trend?.materialNewsCount ?? 0);
  const officialCount = Number(counts.official ?? evidence.officialCount ?? item?.officialSignal?.count ?? 0);
  const parts = [];
  const evidenceScore = evidenceScoreValue(evidence);
  if (evidenceScore != null) parts.push(`${evidenceSummaryLabel(evidence)} ${evidenceScore}/100`);
  if (materialNews) parts.push(`재료 ${materialNews}건`);
  else if (sourceCount) parts.push(`출처 ${sourceCount}개`);
  else if (newsCount) parts.push(`뉴스 ${newsCount}건`);
  if (officialCount) parts.push(`공시 ${officialCount}건`);
  const liveText = evidence?.priceBasis?.label || livePriceLabel(item);
  if (liveText) parts.push(liveText);
  return parts.join(" · ");
}

function feedReasonText(item, plan) {
  const signalMeta = candidateSignalMeta(item);
  const headline = item?.headline || "";
  const priceGuide = primaryPriceGuide(plan);
  return shortText(signalMeta || headline || priceGuide, 58);
}

function renderFeed() {
  const candidates = filteredCandidates();
  const feedView = visibleFeedCandidates(candidates);
  renderStrategyCounts();
  const selectionChanged = syncSelectedToVisibleCandidates(candidates);
  renderQuickSearch();
  renderStockSearchResults();
  if (!candidates.length) {
    const label = strategyLabel(state.strategy);
    els.candidateFeed.innerHTML = `
      <div class="empty-state">
        <h2>${escapeHtml(label)} 후보가 없습니다</h2>
        <p>${escapeHtml(strategyEmptyMessage(state.strategy))}</p>
      </div>
    `;
    if (selectionChanged && state.view === "signals") {
      window.requestAnimationFrame(() => {
        renderTradeDecisionStatus();
        renderDetail();
      });
    }
    return;
  }

  const feedItemsHtml = feedView.items
    .map((item) => {
      const active = item.symbol === state.selectedSymbol ? "active" : "";
      const retained = item.displayRetained ? "retained" : "";
      const plan = tradePlan(item);
      const actionLabel = feedActionLabel(item, plan);
      const primaryDecision = primaryDecisionForDisplay(item, plan);
      const liveText = livePriceLabel(item);
      const reasonText = feedReasonText(item, plan);
      const headlineText = shortText(item.headline, 64);
      return `
        <button class="feed-item ${active} ${retained}" data-symbol="${escapeHtml(item.symbol)}">
          <span class="logo-mark">${escapeHtml(initials(item.name))}</span>
          <span class="feed-main">
            <span class="feed-title">
              <strong>${escapeHtml(item.name)}</strong>
              <span>${escapeHtml(item.symbol)}</span>
              <span class="feed-badge decision-badge decision-${escapeHtml(primaryDecision.key)}" data-feed-decision>${escapeHtml(primaryDecision.label)}</span>
            </span>
            <span class="feed-subtitle">${escapeHtml(headlineText)}</span>
            <span class="feed-signal-line ${escapeHtml(plan.tone)}">
              <strong>근거</strong>
              <em>${escapeHtml(reasonText)}</em>
            </span>
            ${active ? `<span class="live-data-strip feed-live-data-strip" data-feed-live>${liveDataCoverageChips(item, true)}</span>` : ""}
          </span>
          <span class="feed-meta">
            <span class="feed-price-line">
              <b data-feed-price>${escapeHtml(item.price || "-")}</b>
              <em class="${escapeHtml(candidateChangeClass(item))}" data-feed-change>${escapeHtml(displayCandidateChangeText(item))}</em>
            </span>
            <span class="feed-action ${escapeHtml(plan.tone)}" data-feed-action>${escapeHtml(actionLabel)}</span>
            <span class="score-pill ${scoreClass(item.totalScore)}" data-feed-score>${item.totalScore}</span>
            <span class="feed-time" data-feed-time>${escapeHtml(liveText || item.updated)}</span>
          </span>
        </button>
      `;
    })
    .join("");
  els.candidateFeed.innerHTML = `${feedItemsHtml}${candidateFeedToggleMarkup(feedView, candidates.length)}`;

  if (selectionChanged && state.view === "signals") {
    window.requestAnimationFrame(() => {
      renderTradeDecisionStatus();
      renderDetail();
    });
  }

  document.querySelectorAll(".feed-item").forEach((button) => {
    button.addEventListener("click", () => {
      state.view = "signals";
      updateShellView();
      updateViewButtons();
      state.selectedSymbol = button.dataset.symbol;
      renderFeed();
      renderTradeDecisionStatus();
      renderDetail();
      refreshLivePrices();
    });
  });

  const toggleButton = els.candidateFeed.querySelector("[data-feed-toggle]");
  if (toggleButton) {
    toggleButton.addEventListener("click", () => {
      state.feedExpanded = !state.feedExpanded;
      renderFeed();
    });
  }
}

function strategyLabel(value) {
  if (value === "core") return "핵심 후보";
  if (value === "review") return "검토 후보";
  if (value === "action") return "진입 가능";
  if (value === "wait") return "대기 후보";
  if (value === "pullback") return "눌림 대기";
  if (value === "hidden") return "숨은 기회";
  if (value === "momentum") return "모멘텀";
  if (value === "holding") return "보유 대응";
  if (value === "exclude") return "오늘 제외";
  if (value === "all") return "전체";
  return "진입 가능";
}

function strategyEmptyMessage(value) {
  if (value === "core") return "신뢰도, 가격 반응, 리스크를 동시에 통과한 핵심 후보가 없습니다. 오늘은 후보를 억지로 고르지 않고 검토·눌림 탭에서 관찰만 유지하세요.";
  if (value === "review") return "핵심은 아니지만 추가 확인할 후보가 없습니다. 지금은 대기 또는 전체 후보만 참고하세요.";
  if (value === "action") return "현재는 가격, 준비도, 리스크를 동시에 통과한 진입 후보가 없습니다. 무리한 진입보다 눌림이나 전체 후보를 확인하세요.";
  if (value === "wait") return "추가 확인 후보가 없습니다. 지금은 핵심 후보 또는 전체 후보만 참고하세요.";
  if (value === "pullback") return "눌림이나 반등 확인 구간에 있는 후보가 없습니다. 추격보다 다음 갱신을 기다리는 편이 낫습니다.";
  if (value === "hidden") return "뉴스 대비 가격 반영이 덜 된 숨은 후보가 없습니다. 전체 후보에서 테마 변화를 확인할 수 있습니다.";
  if (value === "momentum") return "뉴스, 가격, 수급 모멘텀이 동시에 살아 있는 후보가 없습니다.";
  if (value === "holding") return "현재 불러온 포트폴리오와 연결되는 후보가 없습니다.";
  if (value === "exclude") return "제외 후보가 없습니다. 좋은 신호입니다.";
  return "현재 필터 조건에 맞는 후보가 없습니다. 검색어나 국내/해외 필터를 조정해 보세요.";
}

function renderStrategyCounts() {
  const counts = candidateStrategyCounts(baseFilteredCandidates());
  document.querySelectorAll(".strategy-button").forEach((button) => {
    const strategy = button.dataset.strategy || "action";
    const label = button.dataset.label || strategyLabel(strategy);
    const count = counts[strategy] ?? 0;
    button.innerHTML = `<span>${escapeHtml(label)}</span><strong>${escapeHtml(count)}</strong>`;
    button.title = `${strategyLabel(strategy)} ${count}개`;
    button.classList.toggle("active", strategy === state.strategy);
  });
}

function stockSearchMatchText(item) {
  const match = item?.match ?? {};
  if (!match.text || !match.field) return "";
  return `${match.field}: ${match.text}`;
}

function stockSearchSubtitle(item) {
  const matchText = stockSearchMatchText(item);
  const parts = [
    matchText,
    item.sourceLabel,
    !matchText && item.aliases?.length ? `별칭 ${item.aliases.slice(0, 2).join(", ")}` : "",
    item.market,
    item.securityType,
    item.status,
    item.price && item.price !== "-" ? item.price : ""
  ].filter(Boolean);
  return parts.join(" · ") || "종목 검색 결과";
}

function stockSearchStatusText(payload) {
  const status = payload?.status ?? {};
  const masterCount = Number(status.searchMasterCount ?? 0);
  const generatedCount = Number(status.generatedMasterCount ?? 0);
  const summary = status.searchMasterSummary ?? {};
  const storage = stockMasterStorageLabel(status.searchMasterStorage);
  const sourceLabel =
    status.source === "toss"
      ? "토스 직접조회"
      : status.source === "error"
        ? "토스 조회 오류"
        : status.source === "disabled"
          ? "마스터 검색"
          : "자동완성";
  const coverageParts = [
    Number(summary.domestic ?? 0) ? `국내 ${summary.domestic}` : "",
    Number(summary.overseas ?? 0) ? `해외 ${summary.overseas}` : "",
    Number(summary.etf ?? 0) ? `ETF ${summary.etf}` : ""
  ].filter(Boolean);
  const parts = [
    masterCount ? `마스터 ${masterCount}개` : "",
    coverageParts.length ? coverageParts.join("/") : "",
    generatedCount ? `저장 ${generatedCount}개` : "",
    status.searchMasterStorage ? storage : "",
    sourceLabel
  ].filter(Boolean);
  return parts.join(" · ");
}

function stockSearchEmptyMessage(payload) {
  const query = state.query.trim();
  const statusText = stockSearchStatusText(payload);
  const base = payload.message || `${query} 검색 결과가 없습니다.`;
  const help = statusText
    ? `${statusText} 기준입니다. ETF나 해외 종목이 빠지면 설정에서 검색 마스터를 재생성하세요.`
    : "삼성, 하이닉스, 엔비, AAPL처럼 종목명·별칭·코드로 입력하세요.";
  return `${base} ${help}`;
}

function shouldSearchStocks(query) {
  const text = String(query ?? "").trim();
  if (!text) return false;
  if (/[가-힣]/.test(text)) return text.length >= 1;
  return text.length >= 2;
}

function stockSearchActiveItem() {
  const items = state.stockSearch.items ?? [];
  if (!items.length) return null;
  const visibleCount = Math.min(items.length, 8);
  const index = Math.min(Math.max(Number(state.stockSearch.activeIndex ?? 0), 0), visibleCount - 1);
  return items[index] ?? items[0] ?? null;
}

function setStockSearchActiveIndex(index) {
  const items = state.stockSearch.items ?? [];
  if (!items.length) return;
  const visibleCount = Math.min(items.length, 8);
  const next = ((index % visibleCount) + visibleCount) % visibleCount;
  state.stockSearch = { ...state.stockSearch, activeIndex: next };
  renderStockSearchResults();
}

async function openSearchResult(symbol) {
  const item = (state.stockSearch.items ?? []).find((entry) => entry.symbol === symbol);
  if (!item) return;
  const candidate = (state.dashboard?.candidates ?? []).find((entry) => entry.symbol === symbol);
  state.view = "signals";
  updateShellView();
  updateViewButtons();
  if (candidate) {
    state.selectedLookup = candidate;
    state.selectedSymbol = candidate.symbol;
    state.stockSearch = { ...state.stockSearch, analyzingSymbol: null };
    renderFeed();
    renderTradeDecisionStatus();
    renderDetail();
    refreshLivePrices();
    return;
  } else {
    state.selectedLookup = candidateFromSearchResult(item, { analysisLoading: true });
    state.selectedSymbol = item.symbol;
    state.stockSearch = { ...state.stockSearch, analyzingSymbol: item.symbol };
  }
  renderFeed();
  renderTradeDecisionStatus();
  renderDetail();

  startActivity("검색 종목 분석 중", `${item.name || item.symbol}의 가격·뉴스·공시를 확인합니다`);
  const payload = await safeFetchJson(
    `/api/stocks/analyze?symbol=${encodeURIComponent(item.symbol)}`,
    { candidate: null, message: "검색 종목 분석을 불러오지 못했습니다." },
    45000
  );
  if (state.selectedSymbol !== item.symbol) {
    finishActivity();
    return;
  }
  updateActivity("분석 결과 정리 중", "가격 행동 지표와 판단 문장을 구성합니다");
  state.stockSearch = { ...state.stockSearch, analyzingSymbol: null };
  if (payload?.candidate) {
    state.selectedLookup = payload.candidate;
  } else {
    state.selectedLookup = candidateFromSearchResult(item, {
      analysisError: payload?.message || "검색 종목 분석을 불러오지 못했습니다."
    });
  }
  renderFeed();
  renderTradeDecisionStatus();
  renderDetail();
  finishActivity();
}

function renderStockSearchResults() {
  if (!els.stockSearchResults) return;
  const query = state.query.trim();
  const payload = state.stockSearch;
  if (!shouldSearchStocks(query)) {
    els.stockSearchResults.hidden = true;
    els.stockSearchResults.innerHTML = "";
    return;
  }

  const items = payload.items ?? [];
  const stale = payload.query !== query;
  const loading = payload.loading || stale;
  const message = payload.message || payload.status?.message || "";
  const statusText = stockSearchStatusText(payload);
  const activeIndex = items.length ? Math.min(Math.max(Number(payload.activeIndex ?? 0), 0), items.length - 1) : -1;
  els.stockSearchResults.hidden = false;
  els.stockSearchResults.innerHTML = `
    <div class="stock-search-head">
      <strong>종목 자동완성</strong>
      <span>${loading ? "조회 중" : items.length ? `${items.length}건` : "결과 없음"}</span>
    </div>
    ${statusText ? `<div class="stock-search-status">${escapeHtml(statusText)}</div>` : ""}
    ${
      items.length
        ? `<div class="stock-search-list">
            ${items
              .slice(0, 8)
              .map(
                (item, index) => `
                  <button class="stock-result ${index === activeIndex ? "active" : ""}" type="button" data-search-symbol="${escapeHtml(item.symbol)}" data-search-index="${index}" aria-selected="${index === activeIndex ? "true" : "false"}">
                    <span class="logo-mark">${escapeHtml(initials(item.name || item.symbol))}</span>
                    <span>
                      <strong>${escapeHtml(item.name || item.symbol)} <small>${escapeHtml(item.symbol)}</small></strong>
                      <em>${escapeHtml(stockSearchSubtitle(item))}</em>
                    </span>
                    <span>${escapeHtml(
                      payload.analyzingSymbol === item.symbol ? "분석 중" : item.inCandidates ? "후보 열기" : "분석"
                    )}</span>
                  </button>
                `
              )
              .join("")}
          </div>`
        : `<p>${escapeHtml(loading ? "검색 마스터에서 종목을 찾고 있습니다." : stockSearchEmptyMessage(payload))}</p>`
    }
    ${message && items.length ? `<p>${escapeHtml(message)}</p>` : ""}
  `;

  els.stockSearchResults.querySelectorAll("[data-search-symbol]").forEach((button) => {
    button.addEventListener("click", () => openSearchResult(button.dataset.searchSymbol));
    button.addEventListener("mouseenter", () => {
      const index = Number(button.dataset.searchIndex ?? -1);
      if (index >= 0) {
        state.stockSearch = { ...state.stockSearch, activeIndex: index };
      }
    });
  });
}

async function loadStockSearch() {
  const query = state.query.trim();
  if (!shouldSearchStocks(query)) {
    state.stockSearch = {
      query,
      loading: false,
      items: [],
      message: "",
      status: null,
      analyzingSymbol: null,
      activeIndex: -1
    };
    renderStockSearchResults();
    return;
  }

  state.stockSearch = {
    ...state.stockSearch,
    query,
    loading: true,
    message: "",
    activeIndex: -1
  };
  renderStockSearchResults();

  const payload = await safeFetchJson(
    `/api/stocks/search?query=${encodeURIComponent(query)}&limit=12`,
    { query, items: [], message: "종목 검색을 불러오지 못했습니다.", status: null },
    10000
  );
  if (state.query.trim() !== query) return;
  state.stockSearch = {
    query,
    loading: false,
    items: Array.isArray(payload.items) ? payload.items : [],
    message: payload.message || "",
    status: payload.status || null,
    analyzingSymbol: state.stockSearch.analyzingSymbol,
    activeIndex: Array.isArray(payload.items) && payload.items.length ? 0 : -1
  };
  renderStockSearchResults();
}

function officialToneText(tone) {
  if (tone === "positive") return "긍정";
  if (tone === "risk") return "리스크";
  if (tone === "caution") return "확인";
  return "중립";
}

function officialSignalSection(item) {
  const signal = item.officialSignal ?? item.finalDecision?.officialSignal ?? {};
  if (!signal.count) return "";
  const primary = signal.primary ?? {};
  const items = Array.isArray(signal.items) ? signal.items : [];
  return `
    <section class="detail-section official-section">
      <div class="section-title">
        <p class="eyebrow">공식 이벤트</p>
        <h2>${escapeHtml(signal.summary || "OpenDART 공시 확인")}</h2>
      </div>
      <div class="stat-grid">
        ${statCard("공시 수", `${signal.count ?? 0}건`)}
        ${statCard("긍정", `${signal.positiveCount ?? 0}건`)}
        ${statCard("리스크", `${signal.riskCount ?? 0}건`)}
        ${statCard("중요도", `${primary.eventImportance ?? 0}/100`)}
      </div>
      <ul class="source-list official-event-list">
        ${items
          .map(
            (event) => `
              <li class="official-tone-${escapeHtml(event.eventTone || "neutral")}">
                <strong>${escapeHtml(event.eventLabel || officialToneText(event.eventTone))} · ${escapeHtml(event.reportName || "-")}</strong>
                <span>${escapeHtml(event.receivedDate || "-")} · 중요도 ${escapeHtml(event.eventImportance ?? 0)}/100${event.url ? " · OpenDART" : ""}</span>
              </li>
            `
          )
          .join("")}
      </ul>
      <ul class="bullet-list ${signal.riskLevel === "high" ? "avoid-list" : "entry-list"}">
        ${(signal.reasons ?? []).slice(0, 3).map((text) => `<li>${escapeHtml(text)}</li>`).join("")}
        ${(signal.warnings ?? []).slice(0, 3).map((text) => `<li>${escapeHtml(text)}</li>`).join("")}
      </ul>
    </section>
  `;
}

function renderDetail() {
  const item = selectedCandidate();
  if (!item) {
    els.signalDetail.innerHTML = `
      <div class="empty-state">
        <h2>선택된 후보가 없습니다</h2>
        <p>왼쪽 후보 목록에서 종목을 선택하세요.</p>
      </div>
    `;
    return;
  }
  const plan = tradePlan(item);
  const primaryDecision = primaryDecisionForDisplay(item, plan);

  els.signalDetail.innerHTML = `
    <div class="detail-hero">
      <div>
        <div class="hero-title">
          <span class="logo-mark">${escapeHtml(initials(item.name))}</span>
          <h2>${escapeHtml(item.name)}</h2>
          <span data-selected-price>${escapeHtml(item.price)}</span>
          <span class="${candidateChangeClass(item)}" data-selected-change>${escapeHtml(displayCandidateChangeText(item))}</span>
          <button
            class="watch-button ${item.isWatched ? "active" : ""}"
            id="watchButton"
            type="button"
            aria-label="${item.isWatched ? "관심 해제" : "관심 등록"}"
            title="${item.isWatched ? "관심 해제" : "관심 등록"}"
          >
            <span aria-hidden="true">♥</span>
            <span class="sr-only">${item.isWatched ? "관심 해제" : "관심 등록"}</span>
          </button>
        </div>
        <p class="headline">${escapeHtml(item.headline)}</p>
        <p class="thesis">${escapeHtml(item.thesis)}</p>
        <p class="decision-summary decision-${escapeHtml(primaryDecision.key)}" data-selected-decision-summary>
          <strong>${escapeHtml(primaryDecision.label)}</strong>
          <span>${escapeHtml(primaryDecision.detail)}</span>
        </p>
        <p class="data-source" data-selected-price-meta>${escapeHtml(priceMeta(item))}</p>
        <div class="live-data-strip detail-live-data-strip" data-selected-live-data>
          ${liveDataCoverageChips(item)}
        </div>
        <div class="chips">
          ${item.tags.map((tag) => `<span class="chip">${escapeHtml(tag)}</span>`).join("")}
        </div>
      </div>
      <div class="hero-side">
        <div class="score-card">
          <div class="score-number">
            <strong>${item.totalScore}</strong>
            <span>/ 100</span>
          </div>
          <div class="progress-track">
            <div class="progress-fill" style="width:${item.totalScore}%"></div>
          </div>
        </div>
        <canvas class="mini-chart" id="miniChart" width="460" height="236" aria-label="가격 흐름"></canvas>
      </div>
    </div>

    ${signalFlowStrip(item, plan, primaryDecision)}

    <div class="detail-grid">
      ${newsSignalSection(item)}
      ${priceReactionSection(item)}
      ${tradePlanSection(item)}
      ${supportingDetailSection(item)}
    </div>
  `;

  document.querySelector("#watchButton").addEventListener("click", () => toggleWatch(item));
  drawChart(item.chart);
}

function renderPerformance() {
  if (!els.signalDetail) return;
  if (state.performanceLoading && !state.performance) {
    els.signalDetail.innerHTML = `
      <div class="empty-state">
        <h2>성과를 계산하는 중입니다</h2>
        <p>저장된 스냅샷과 현재 가격을 비교하고 있습니다.</p>
      </div>
    `;
    return;
  }

  const payload = state.performance;
  if (!payload || payload.error) {
    els.signalDetail.innerHTML = `
      <div class="empty-state">
        <h2>성과 검증 데이터가 없습니다</h2>
        <p>${escapeHtml(payload?.message ?? "스냅샷을 먼저 저장하면 후보 성과를 비교할 수 있습니다.")}</p>
      </div>
    `;
    return;
  }

  const summary = payload.summary ?? {};
  const observations = Array.isArray(payload.observations) ? payload.observations : [];
  const bySymbol = Array.isArray(payload.bySymbol) ? payload.bySymbol : [];
  const byGate = Array.isArray(payload.byGate) ? payload.byGate : [];
  const byFinalAction = Array.isArray(payload.byFinalAction) ? payload.byFinalAction : [];
  const byReaction = Array.isArray(payload.byReaction) ? payload.byReaction : [];
  const byHorizon = Array.isArray(payload.byHorizon) ? payload.byHorizon : [];
  const poolPerformance = payload.candidatePoolPerformance ?? {};
  const poolUpdatedSymbols = Array.isArray(poolPerformance.updatedSymbols) ? poolPerformance.updatedSymbols : [];
  const priceSource = payload.priceStatus?.source === "toss" ? "토스 현재가" : fallbackStatusLabel(payload.priceStatus, "대체 가격");
  const threshold = payload.config?.successThreshold ?? "+1.0%";
  const best = summary.best;
  const worst = summary.worst;
  const measuredCount = Number(summary.measuredCount ?? 0);
  const runCount = Number(summary.runCount ?? 0);
  const hasPerformanceData =
    runCount > 0 ||
    measuredCount > 0 ||
    observations.length > 0 ||
    bySymbol.length > 0 ||
    byGate.length > 0 ||
    byFinalAction.length > 0 ||
    byReaction.length > 0;

  if (!hasPerformanceData) {
    els.signalDetail.innerHTML = `
      <div class="empty-state performance-empty-state">
        <h2>성과 검증은 아직 시작 전입니다</h2>
        <p>장마감·장중 스냅샷이 저장되면 1시간, 종가, 1일, 3일, 5일 성과를 여기서 검증합니다.</p>
        <div class="signal-flow-strip">
          <div>
            <span>1. 후보 저장</span>
            <strong>스냅샷 생성</strong>
            <em>장마감·장중 후보와 가격을 기록</em>
          </div>
          <div>
            <span>2. 가격 추적</span>
            <strong>성과 관측</strong>
            <em>토스 현재가 기준으로 변화율 확인</em>
          </div>
          <div>
            <span>3. 기준 보정</span>
            <strong>실전 검증</strong>
            <em>수익에 도움 된 조건만 남김</em>
          </div>
        </div>
      </div>
    `;
    return;
  }

  els.signalDetail.innerHTML = `
    <div class="performance-board">
      <div class="performance-hero">
        <div>
          <p class="eyebrow">성과 검증</p>
          <h2>스냅샷 후보 추적</h2>
          <p>저장된 후보의 당시 가격과 현재 가격을 비교해 선정 기준의 방향성을 검증합니다.</p>
        </div>
        <div class="performance-source">
          <span>가격 기준</span>
          <strong>${escapeHtml(priceSource)}</strong>
          <span>상승 판정 ${escapeHtml(threshold)} 이상</span>
        </div>
      </div>

      <div class="performance-metrics">
        ${performanceMetric("스냅샷", summary.runCount ?? 0)}
        ${performanceMetric("검증 대상", summary.eligibleRunCount ?? 0)}
        ${performanceMetric("관측 대기", summary.freshRunSkippedCount ?? 0)}
        ${performanceMetric("관측", summary.measuredCount ?? 0)}
        ${performanceMetric("상승 비율", summary.hitRate ?? "-")}
        ${performanceMetric("평균 변화", summary.averageChange ?? "-", changeClass(summary.averageChange ?? ""))}
        ${performanceMetric("실전 관측", summary.actionableMeasuredCount ?? 0)}
        ${performanceMetric("실전 승률", summary.actionableHitRate ?? "-")}
        ${performanceMetric("매수 판단", summary.buyDecisionMeasuredCount ?? 0)}
        ${performanceMetric("매수 승률", summary.buyDecisionHitRate ?? "-")}
        ${performanceMetric("추가 판단", summary.addDecisionMeasuredCount ?? 0)}
        ${performanceMetric("추가 승률", summary.addDecisionHitRate ?? "-")}
        ${performanceMetric("풀 반영", poolPerformance.updatedCount ?? 0)}
        ${performanceMetric("풀 승률", poolPerformance.hitRate ?? "-")}
        ${performanceMetric("풀 평균", poolPerformance.averageChange ?? "-", changeClass(poolPerformance.averageChange ?? ""))}
        ${performanceMetric("상승", summary.positiveCount ?? 0)}
        ${performanceMetric("하락", summary.negativeCount ?? 0)}
      </div>

      <div class="performance-grid">
        <section class="detail-section">
          <div class="section-title">
            <p class="eyebrow">종목별</p>
            <h2>반복 성과</h2>
          </div>
          <div class="performance-list">
            ${
              bySymbol.length
                ? bySymbol.slice(0, 8).map(renderSymbolPerformance).join("")
                : `<div class="history-empty">측정 가능한 종목이 아직 없습니다</div>`
            }
          </div>
        </section>

        <section class="detail-section">
          <div class="section-title">
            <p class="eyebrow">신뢰도</p>
            <h2>게이트별 성과</h2>
          </div>
          <div class="performance-list">
            ${
              byGate.length
                ? byGate.map(renderPerformanceGroup).join("")
                : `<div class="history-empty">게이트별 관측값이 아직 없습니다</div>`
            }
          </div>
        </section>

        <section class="detail-section">
          <div class="section-title">
            <p class="eyebrow">판단</p>
            <h2>최종 판단별 성과</h2>
          </div>
          <div class="performance-list">
            ${
              byFinalAction.length
                ? byFinalAction.map(renderPerformanceGroup).join("")
                : `<div class="history-empty">최종 판단별 관측값이 아직 없습니다</div>`
            }
          </div>
        </section>

        <section class="detail-section">
          <div class="section-title">
            <p class="eyebrow">반응</p>
            <h2>가격 반응별 성과</h2>
          </div>
          <div class="performance-list">
            ${
              byReaction.length
                ? byReaction.map(renderPerformanceGroup).join("")
                : `<div class="history-empty">가격 반응별 관측값이 아직 없습니다</div>`
            }
          </div>
        </section>

        <section class="detail-section">
          <div class="section-title">
            <p class="eyebrow">기간</p>
            <h2>관측 기간별 성과</h2>
          </div>
          <div class="performance-list">
            ${
              byHorizon.length
                ? byHorizon.map(renderPerformanceGroup).join("")
                : `<div class="history-empty">기간별 관측값이 아직 없습니다</div>`
            }
          </div>
        </section>

        <section class="detail-section">
          <div class="section-title">
            <p class="eyebrow">최고/최저</p>
            <h2>성과 범위</h2>
          </div>
          <div class="performance-extremes">
            ${performanceExtreme("최고", best)}
            ${performanceExtreme("최저", worst)}
          </div>
        </section>

        <section class="detail-section">
          <div class="section-title">
            <p class="eyebrow">후보 풀</p>
            <h2>성과 반영</h2>
          </div>
          <div class="performance-list">
            <div class="performance-row">
              <span>
                <strong>${escapeHtml(poolPerformance.updatedCount ?? 0)}개 후보 갱신</strong>
                <em>${escapeHtml(poolPerformance.message ?? "성과 검증 결과를 후보 풀에 반영합니다.")}</em>
              </span>
              <span>
                <strong class="${changeClass(poolPerformance.averageChange ?? "")}">${escapeHtml(poolPerformance.averageChange ?? "-")}</strong>
                <em>승률 ${escapeHtml(poolPerformance.hitRate ?? "-")} · 측정 ${escapeHtml(poolPerformance.measuredCount ?? 0)}건</em>
              </span>
            </div>
            ${
              poolUpdatedSymbols.length
                ? `<div class="performance-row">
                    <span>
                      <strong>반영 종목</strong>
                      <em>${escapeHtml(poolUpdatedSymbols.join(", "))}</em>
                    </span>
                    <span>
                      <strong>${escapeHtml(poolPerformance.positiveCount ?? 0)} 상승</strong>
                      <em>${escapeHtml(poolPerformance.negativeCount ?? 0)} 하락</em>
                    </span>
                  </div>`
                : `<div class="history-empty">아직 후보 풀에 연결된 성과가 없습니다</div>`
            }
          </div>
        </section>

        <section class="detail-section performance-wide">
          <div class="section-title">
            <p class="eyebrow">최근 관측</p>
            <h2>스냅샷별 후보 변화</h2>
          </div>
          <div class="performance-table">
            ${
              observations.length
                ? observations.slice(0, 18).map(renderPerformanceObservation).join("")
                : `<div class="history-empty">장마감 또는 장중 스냅샷을 먼저 저장하세요</div>`
            }
          </div>
        </section>
      </div>
    </div>
  `;
}

function renderPerformanceGroup(item) {
  return `
    <div class="performance-row">
      <span>
        <strong>${escapeHtml(item.label)}</strong>
        <em>${escapeHtml(item.measuredCount)} / ${escapeHtml(item.observationCount)}건 측정</em>
      </span>
      <span>
        <strong class="${changeClass(item.averageChange)}">${escapeHtml(item.averageChange)}</strong>
        <em>승률 ${escapeHtml(item.hitRate)} · 최근 ${escapeHtml(item.latestOutcome)}</em>
      </span>
    </div>
  `;
}

function performanceMetric(label, value, tone = "") {
  return `
    <div class="performance-metric">
      <span>${escapeHtml(label)}</span>
      <strong class="${escapeHtml(tone)}">${escapeHtml(value)}</strong>
    </div>
  `;
}

function renderSymbolPerformance(item) {
  return `
    <div class="performance-row">
      <span>
        <strong>${escapeHtml(item.name)}</strong>
        <em>${escapeHtml(item.symbol)} · ${escapeHtml(item.count)}회 관측</em>
      </span>
      <span>
        <strong class="${changeClass(item.averageChange)}">${escapeHtml(item.averageChange)}</strong>
        <em>${escapeHtml(item.positiveCount)}회 상승 · 최근 ${escapeHtml(item.latestOutcome)}</em>
      </span>
    </div>
  `;
}

function performanceExtreme(label, item) {
  if (!item) {
    return `
      <div class="performance-extreme">
        <span>${escapeHtml(label)}</span>
        <strong>-</strong>
        <em>측정 전</em>
      </div>
    `;
  }
  return `
    <div class="performance-extreme">
      <span>${escapeHtml(label)}</span>
      <strong class="${changeClass(item.change)}">${escapeHtml(item.change)}</strong>
      <em>${escapeHtml(item.name)} · ${escapeHtml(timeLabel(item.createdAt))}</em>
    </div>
  `;
}

function renderPerformanceObservation(item) {
  const tone = item.measured ? changeClass(item.change) : "";
  const gate = item.gateLabel || item.verdict || "미분류";
  const confidence = item.confidenceScore === null || item.confidenceScore === undefined ? "-" : item.confidenceScore;
  const reaction = item.reactionScore === null || item.reactionScore === undefined ? "-" : item.reactionScore;
  const horizon = item.horizonLabel || "기간 미확인";
  const priceNote = item.sanityMessage || `${horizon} · ${item.snapshotPrice} → ${item.currentPrice} · ${item.outcome}`;
  return `
    <div class="performance-observation">
      <span>
        <strong>${escapeHtml(item.name)}</strong>
        <em>${escapeHtml(modeLabel(item.mode))} · ${escapeHtml(timeLabel(item.createdAt))} · ${escapeHtml(gate)} · 신뢰 ${escapeHtml(confidence)} · 반응 ${escapeHtml(reaction)}</em>
      </span>
      <span>
        <strong class="${tone}">${escapeHtml(item.change)}</strong>
        <em>${escapeHtml(priceNote)}</em>
      </span>
    </div>
  `;
}

function statCard(label, value) {
  return `
    <div class="stat-card">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(value)}</strong>
    </div>
  `;
}

function tradeNowGuide(item, plan) {
  const current = `${item?.price ?? "-"} ${displayCandidateChangeText(item)}`.trim();
  const entry = rowValue(plan, "관찰 매수");
  const pullback = rowValue(plan, "눌림 대기");
  const rebound = rowValue(plan, "반등 확인");
  const stop = rowValue(plan, "손절 점검");
  const trim = rowValue(plan, "분할매도");
  const freshness = priceFreshnessInfo(item);

  if (plan.tone === "buy") {
    if (freshness.isBaseline) {
      return {
        tone: "wait",
        title: "장마감 기준가",
        summary: freshness.message || "장마감 기준가 분석입니다. 개장 후 가격·거래량 반응을 확인하세요.",
        current,
        focus: entry
      };
    }
    if (!freshness.isFresh) {
      return {
        tone: "wait",
        title: "가격 보강 대기",
        summary: freshness.message || "서버가 DB 가격 기준을 보강한 뒤 매수 가능 여부를 판단합니다.",
        current,
        focus: entry
      };
    }
    return {
      tone: "buy",
      title: "매수 관찰",
      summary: `${entry} 구간에서 가격·거래량 조건이 유지되는지 확인합니다.`,
      current,
      focus: entry
    };
  }
  if (plan.tone === "sell") {
    return {
      tone: "sell",
      title: "분할매도 점검",
      summary: `${trim} 기준에서 일부 이익 실현 또는 보유 유지 여부를 결정합니다.`,
      current,
      focus: trim
    };
  }
  if (plan.tone === "risk") {
    return {
      tone: "risk",
      title: "신규 진입 금지",
      summary: `${stop} 기준을 먼저 확인하고, 무리한 추가 매수는 피합니다.`,
      current,
      focus: stop
    };
  }
  if (String(plan.action).includes("반등")) {
    return {
      tone: "wait",
      title: "반등 확인",
      summary: `${rebound} 조건을 회복하기 전까지는 대기합니다.`,
      current,
      focus: rebound
    };
  }
  return {
    tone: "wait",
    title: String(plan.action).includes("눌림") ? "눌림 대기" : "진입 보류",
    summary: `${pullback} 또는 ${entry} 근처에서 재반응을 확인합니다.`,
    current,
    focus: pullback !== "-" ? pullback : entry
  };
}

function tradeZoneCards(plan) {
  return [
    ["매수 관찰", rowValue(plan, "관찰 매수"), "조건 유지 시"],
    ["눌림 확인", rowValue(plan, "눌림 대기"), "추격 대신 대기"],
    ["추격 금지", rowValue(plan, "추격 금지"), "이상은 관망"],
    ["손절 기준", rowValue(plan, "손절 점검"), "이탈 시 중단"],
    ["분할매도", rowValue(plan, "분할매도"), "과열·보유 수익 점검"]
  ];
}

function signalFlowStrip(item, plan, primaryDecision) {
  const stage = reactionStageForDisplay(item);
  const sourceMeta = candidateSignalMeta(item) || "출처 확인 중";
  return `
    <div class="signal-flow-strip">
      <div>
        <span>1. 뉴스 시그널</span>
        <strong>${escapeHtml(shortText(item.headline || item.thesis || "재료 확인 중", 46))}</strong>
        <em data-flow-news-meta>${escapeHtml(sourceMeta)}</em>
      </div>
      <div>
        <span>2. 가격 반응</span>
        <strong data-flow-price-label>${escapeHtml(stage.label)}</strong>
        <em data-flow-price-summary>${escapeHtml(stage.summary)}</em>
      </div>
      <div>
        <span>3. 최종 판단</span>
        <strong data-flow-final-label>${escapeHtml(primaryDecision.label)}</strong>
        <em data-flow-final-action>${escapeHtml(plan.action)}</em>
      </div>
    </div>
  `;
}

function newsSignalSection(item) {
  const evidence = candidateEvidenceSummary(item);
  const reasons = uniqueTexts([...(evidence.reasons ?? []), item.thesis, ...(item.why ?? [])], 4);
  const sourceCount = Array.isArray(item.sources) ? item.sources.length : 0;
  const latestSource = item.sources?.[0];
  const reliability = scoreTextFromValue(evidence.reliabilityScore);
  const impact = scoreTextFromValue(evidence.impactScore);
  const reaction = scoreTextFromValue(evidence.priceReactionComponent);
  const risk = scoreTextFromValue(evidence.riskPenalty, " 차감");
  const evidenceStats = evidenceScoreValue(evidence) != null;
  return `
    <section class="detail-section signal-story-section">
      <div class="section-title">
        <p class="eyebrow">뉴스 시그널</p>
        <h2>왜 움직였나</h2>
      </div>
      <ul class="bullet-list">
        ${reasons.map((text) => `<li>${escapeHtml(text)}</li>`).join("")}
      </ul>
      <div class="signal-mini-stats">
        ${
          evidenceStats
            ? `
              ${statCard("근거 신뢰", reliability)}
              ${statCard("재료 영향", impact)}
              ${statCard("가격 반응", reaction)}
              ${statCard("리스크", risk)}
            `
            : `
              ${statCard("확인 출처", sourceCount ? `${sourceCount}개` : "-")}
              ${statCard("재료 뉴스", item.trend?.materialNewsCount != null ? `${item.trend.materialNewsCount}건` : "-")}
              ${statCard("공시/IR", item.officialSignal?.count ? `${item.officialSignal.count}건` : "-")}
              ${statCard("최근 출처", latestSource ? `${latestSource.publisher} · ${latestSource.time}` : "-")}
            `
        }
      </div>
    </section>
  `;
}

function priceReactionSection(item) {
  const reaction = item?.priceReaction ?? {};
  const stage = reactionStageForDisplay(item);
  const confirmed = stage.confirmedFactors;
  const missing = stage.missingFactors;
  const reasons = uniqueTexts(reaction.reasons ?? [], 4);
  return `
    <section class="detail-section price-reaction-section">
      <div class="section-title">
        <p class="eyebrow">가격 반응</p>
        <h2 data-reaction-label>${escapeHtml(stage.label)}</h2>
        <p data-reaction-summary>${escapeHtml(stage.summary)}</p>
      </div>
      <div class="reaction-status-card reaction-${escapeHtml(stage.tone)}" data-reaction-status-card>
        <strong data-reaction-card-label>${escapeHtml(stage.label)}</strong>
        <span data-reaction-card-meta>${escapeHtml(priceMeta(item))}</span>
      </div>
      <details class="support-detail-section reaction-detail-toggle">
        <summary>
          <span>
            <em>가격 검증</em>
            <strong>실시간·거래량 세부 조건</strong>
          </span>
          <b>보기</b>
        </summary>
        <div class="reaction-live-grid" data-reaction-live-grid>
          ${reactionLiveGridHtml(item)}
        </div>
        <div class="reaction-check-grid" data-reaction-check-grid>
          ${reactionCheckGridHtml(stage)}
        </div>
        ${
          confirmed.length || reasons.length
            ? `<ul class="bullet-list entry-list">${uniqueTexts([...reasons, ...confirmed], 5).map((text) => `<li>${escapeHtml(text)}</li>`).join("")}</ul>`
            : ""
        }
        ${
          missing.length
            ? `<ul class="bullet-list risk-list">${missing.map((text) => `<li>${escapeHtml(text)}</li>`).join("")}</ul>`
            : ""
        }
      </details>
    </section>
  `;
}

function riskDecisionSection(item) {
  const entry = uniqueTexts(item.entryConditions, 4);
  const noEntry = uniqueTexts(item.noEntry, 4);
  const stopRules = uniqueTexts(item.stopRules, 4);
  return `
    <section class="detail-section decision-check-section">
      <div class="section-title">
        <p class="eyebrow">판단 기준</p>
        <h2>진입 전 체크</h2>
      </div>
      <div class="decision-check-grid">
        <div>
          <strong>매수 관찰 조건</strong>
          <ul class="bullet-list entry-list">
            ${entry.map((text) => `<li>${escapeHtml(text)}</li>`).join("")}
          </ul>
        </div>
        <div>
          <strong>오늘 제외 조건</strong>
          <ul class="bullet-list avoid-list">
            ${noEntry.map((text) => `<li>${escapeHtml(text)}</li>`).join("")}
          </ul>
        </div>
        <div>
          <strong>리스크 기준</strong>
          <ul class="bullet-list risk-list">
            ${stopRules.map((text) => `<li>${escapeHtml(text)}</li>`).join("")}
          </ul>
        </div>
      </div>
    </section>
  `;
}

function supportingDetailSection(item) {
  const signal = item.officialSignal ?? item.finalDecision?.officialSignal ?? {};
  const officialItems = Array.isArray(signal.items) ? signal.items.slice(0, 4) : [];
  const sources = Array.isArray(item.sources) ? item.sources.slice(0, 6) : [];
  const related = Array.isArray(item.related) ? item.related : [];
  const entry = uniqueTexts(item.entryConditions, 3);
  const noEntry = uniqueTexts(item.noEntry, 3);
  const stopRules = uniqueTexts(item.stopRules, 3);
  return `
    <details class="detail-section support-detail-section">
      <summary>
        <span>
          <em>보조 정보</em>
          <strong>공시·출처·연관 종목</strong>
        </span>
        <b>보기</b>
      </summary>
      <div class="support-grid">
        <div class="support-block">
          <div class="section-title">
            <p class="eyebrow">공식 이벤트</p>
            <h2>${escapeHtml(signal.summary || "공시 확인")}</h2>
          </div>
          <div class="stat-grid">
            ${statCard("공시 수", signal.count ? `${signal.count}건` : "-")}
            ${statCard("리스크", signal.riskCount != null ? `${signal.riskCount}건` : "-")}
          </div>
          <ul class="source-list official-event-list">
            ${
              officialItems.length
                ? officialItems
                    .map(
                      (event) => `
                        <li class="official-tone-${escapeHtml(event.eventTone || "neutral")}">
                          <strong>${escapeHtml(event.eventLabel || officialToneText(event.eventTone))} · ${escapeHtml(event.reportName || "-")}</strong>
                          <span>${escapeHtml(event.receivedDate || "-")}${event.url ? " · OpenDART" : ""}</span>
                        </li>
                      `
                    )
                    .join("")
                : `<li><strong>공시 이벤트 없음</strong><span>현재 후보와 연결된 주요 공시가 없습니다.</span></li>`
            }
          </ul>
        </div>

        <div class="support-block">
          <div class="section-title">
            <p class="eyebrow">판단 기준</p>
            <h2>진입 전 체크</h2>
          </div>
          <div class="compact-checks">
            <div>
              <strong>매수 관찰</strong>
              <ul class="bullet-list entry-list">${entry.map((text) => `<li>${escapeHtml(text)}</li>`).join("")}</ul>
            </div>
            <div>
              <strong>제외 조건</strong>
              <ul class="bullet-list avoid-list">${noEntry.map((text) => `<li>${escapeHtml(text)}</li>`).join("")}</ul>
            </div>
            <div>
              <strong>리스크</strong>
              <ul class="bullet-list risk-list">${stopRules.map((text) => `<li>${escapeHtml(text)}</li>`).join("")}</ul>
            </div>
          </div>
        </div>

        <div class="support-block">
          <div class="section-title">
            <p class="eyebrow">근거</p>
            <h2>확인한 출처</h2>
          </div>
          <ul class="source-list">
            ${
              sources.length
                ? sources
                    .map(
                      (source) => `
                        <li>
                          <strong>${escapeHtml(source.title)}</strong>
                          <span>${escapeHtml(source.publisher)} · ${escapeHtml(source.time)}${source.url ? " · 뉴스" : ""}</span>
                        </li>
                      `
                    )
                    .join("")
                : `<li><strong>출처 확인 중</strong><span>뉴스 또는 공시 출처가 아직 연결되지 않았습니다.</span></li>`
            }
          </ul>
        </div>

        <div class="support-block">
          <div class="section-title">
            <p class="eyebrow">연관 종목</p>
            <h2>같이 볼 대상</h2>
          </div>
          <ul class="related-list">
            ${
              related.length
                ? related
                    .map(
                      (entry) => `
                        <li>
                          <strong>${escapeHtml(entry.name)} <span class="${changeClass(entry.change)}">${escapeHtml(entry.change)}</span></strong>
                          <span>${escapeHtml(entry.symbol)} · ${escapeHtml(entry.relation)}</span>
                        </li>
                      `
                    )
                    .join("")
                : `<li><strong>연관 종목 없음</strong><span>현재 후보와 연결된 비교 대상이 없습니다.</span></li>`
            }
          </ul>
        </div>
      </div>
    </details>
  `;
}

function tradePlanSection(item) {
  const plan = tradePlan(item);
  const now = tradeNowGuide(item, plan);
  return `
    <section class="detail-section trade-plan-section">
      <div class="trade-plan-head">
        <div>
          <p class="eyebrow">최종 판단</p>
          <h2 data-plan-action>${escapeHtml(plan.action)}</h2>
          <p data-plan-summary>${escapeHtml(plan.summary)}</p>
        </div>
        <span class="action-pill ${escapeHtml(plan.tone)}" data-plan-action-pill>${escapeHtml(plan.action)}</span>
      </div>
      <div class="decision-now-card decision-${escapeHtml(now.tone)}" data-now-card>
        <div>
          <span>지금 할 일</span>
          <strong data-now-title>${escapeHtml(now.title)}</strong>
          <p data-now-summary>${escapeHtml(now.summary)}</p>
        </div>
        <div>
          <span>현재가</span>
          <strong data-now-current>${escapeHtml(now.current || "-")}</strong>
          <em data-now-focus>기준 ${escapeHtml(now.focus || "-")}</em>
        </div>
      </div>
      <div class="trade-zone-grid" data-trade-zone-grid>
        ${tradeZoneGridHtml(plan)}
      </div>
      <ul class="trade-reasons">
        ${plan.reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join("")}
      </ul>
    </section>
  `;
}

function decisionGroupSection(item) {
  const group = decisionGroupForDisplay(item);
  const serverGroup = item.decisionGroup ?? {};
  const qualityReason = item.discovery?.qualityReason;
  const qualityLabel = discoveryQualityLabel(item);
  const compression = compressionForDisplay(item);
  const confidence = item.dataConfidence ?? {};
  const sourceReliability = item.sourceReliability ?? {};
  const reaction = item.priceReaction ?? {};
  const reactionMetrics = reaction.metrics ?? {};
  const confirmedFactors = Array.isArray(reactionMetrics.confirmedFactors) ? reactionMetrics.confirmedFactors : [];
  const missingFactors = Array.isArray(reactionMetrics.missingFactors) ? reactionMetrics.missingFactors : [];
  const gate = item.qualityGate ?? {};
  const finalDecision = item.finalDecision ?? {};
  const holding = selectedHoldingFor(item);
  return `
    <section class="detail-section">
      <div class="section-title">
        <p class="eyebrow">후보 분류</p>
        <h2>${escapeHtml(finalDecision.action || group.label)}</h2>
      </div>
      <div class="stat-grid">
        ${statCard("압축 분류", `${compression.label} · ${compression.score}/100`)}
        ${finalDecision.action ? statCard("최종 판단", finalDecision.action) : ""}
        ${statCard("판단 점수", `${Math.round(Number(group.score ?? 0))}/100`)}
        ${statCard("분류", group.label)}
        ${qualityLabel ? statCard("품질", qualityLabel) : ""}
        ${confidence.score != null ? statCard("신뢰도", `${confidence.score}/100`) : ""}
        ${sourceReliability.score != null ? statCard("원천 신뢰", `${sourceReliability.label ?? "-"} · ${sourceReliability.score}/100`) : ""}
        ${reaction.score != null ? statCard("가격 반응", `${reaction.label ?? "-"} · ${reaction.score}/100`) : ""}
        ${reaction.reactionGate ? statCard("반응 게이트", reactionGateLabel(reaction.reactionGate)) : ""}
        ${reactionMetrics.confirmationCount != null ? statCard("반응 확인", `${reactionMetrics.confirmationCount}/${reactionMetrics.requiredConfirmations ?? 2}`) : ""}
        ${confirmedFactors.length ? statCard("확인 요소", confirmedFactors.join(", ")) : ""}
        ${missingFactors.length ? statCard("부족 요소", missingFactors.join(", ")) : ""}
        ${holding ? statCard("보유 손익", `${holding.profitLossRate ?? "-"} · ${holding.judgement ?? "보유"}`) : ""}
        ${holding ? statCard("평균단가", holding.averagePurchasePrice ?? "-") : ""}
        ${gate.label ? statCard("게이트", gate.label) : ""}
      </div>
      <ul class="bullet-list">
        ${finalDecision.summary ? `<li>${escapeHtml(`최종 판단: ${finalDecision.summary}`)}</li>` : ""}
        ${holding ? `<li>${escapeHtml(`보유 기준: ${holding.quantity ?? "-"}주 · 비중 ${holding.allocation ?? "-"}`)}</li>` : ""}
        ${compression.reason ? `<li>${escapeHtml(`압축 판단: ${compression.reason}`)}</li>` : ""}
        <li>${escapeHtml(group.reason)}</li>
        ${qualityReason ? `<li>${escapeHtml(`후보 품질: ${qualityReason}`)}</li>` : ""}
        ${(confidence.reasons ?? []).slice(0, 2).map((text) => `<li>${escapeHtml(`신뢰 근거: ${text}`)}</li>`).join("")}
        ${(sourceReliability.reasons ?? []).slice(0, 3).map((text) => `<li>${escapeHtml(`원천 근거: ${text}`)}</li>`).join("")}
        ${(sourceReliability.warnings ?? []).slice(0, 2).map((text) => `<li>${escapeHtml(`원천 보강: ${text}`)}</li>`).join("")}
        ${(sourceReliability.blockers ?? []).slice(0, 2).map((text) => `<li>${escapeHtml(`원천 차단: ${text}`)}</li>`).join("")}
        ${(reaction.reasons ?? []).slice(0, 2).map((text) => `<li>${escapeHtml(`가격 반응: ${text}`)}</li>`).join("")}
        ${confirmedFactors.length ? `<li>${escapeHtml(`반응 확인 요소: ${confirmedFactors.join(", ")}`)}</li>` : ""}
        ${missingFactors.length ? `<li>${escapeHtml(`반응 부족 요소: ${missingFactors.join(", ")}`)}</li>` : ""}
        ${(reaction.blockers ?? []).slice(0, 2).map((text) => `<li>${escapeHtml(`반응 차단: ${text}`)}</li>`).join("")}
        ${(reaction.warnings ?? []).slice(0, 2).map((text) => `<li>${escapeHtml(`반응 경고: ${text}`)}</li>`).join("")}
        ${(gate.reasons ?? []).slice(0, 2).map((text) => `<li>${escapeHtml(`게이트: ${text}`)}</li>`).join("")}
        ${
          serverGroup.reason && serverGroup.reason !== group.reason
            ? `<li>${escapeHtml(serverGroup.reason)}</li>`
            : ""
        }
      </ul>
    </section>
  `;
}

function candidatePoolSection(item) {
  const pool = candidatePoolStateForDisplay(item);
  const deltaText = pool.scoreDelta > 0 ? `+${pool.scoreDelta}` : `${pool.scoreDelta}`;
  const history = pool.transitionHistory.slice(-3).reverse();
  const rows = [
    ["상태", pool.label],
    ["관측 횟수", pool.observations ? `${pool.observations}회` : "-"],
    ["선정 횟수", pool.selectedCount ? `${pool.selectedCount}회` : "-"],
    ["재점검 점수", pool.retained && pool.retainScore ? `${pool.retainScore}/100` : "-"],
    ["재검토 우선도", pool.monitorScore ? `${pool.monitorLabel || "재검토"} · ${pool.monitorScore}/100` : "-"],
    ["최고 점수", pool.peakScore ? `${pool.peakScore}/100` : "-"],
    ["최고 준비도", pool.peakReadiness ? `${pool.peakReadiness}/100` : "-"],
    ["상태 변화", `${pool.promotionCount}회 승격 · ${pool.demotionCount}회 강등`],
    ["최근 변화", pool.momentumLabel ? `${pool.momentumLabel} ${deltaText}` : "-"],
    ["성과 관측", pool.performanceMeasuredCount ? `${pool.performanceMeasuredCount}건` : "-"],
    ["성과 승률", pool.performanceMeasuredCount ? pool.performanceHitRate || "-" : "-"],
    ["평균 성과", pool.performanceMeasuredCount ? pool.performanceAverageChange || "-" : "-"],
    ["최근 성과", pool.performanceMeasuredCount ? `${pool.performanceLatestOutcome || "-"} ${pool.performanceLatestChange || ""}`.trim() : "-"],
    ["강등 보류", pool.softDemotionCount ? `${pool.softDemotionCount}회` : "-"],
    ["최근 관측", timeLabel(pool.lastSeenAt)],
    ["최근 선정", pool.lastSelectedAt ? timeLabel(pool.lastSelectedAt) : "-"]
  ];
  return `
    <section class="detail-section">
      <div class="section-title">
        <p class="eyebrow">후보 풀</p>
        <h2>${escapeHtml(pool.label)}</h2>
      </div>
      <div class="stat-grid">
        ${rows.map(([label, value]) => statCard(label, value)).join("")}
      </div>
      <ul class="bullet-list">
        <li>${escapeHtml(pool.reason)}</li>
        ${pool.monitorReason ? `<li>${escapeHtml(`재검토 이유: ${pool.monitorReason}`)}</li>` : ""}
        ${pool.retained ? `<li>${escapeHtml(pool.retainReason || `${pool.retainStateLabel || "후보 풀"} 상태로 재점검 대상입니다.`)}</li>` : ""}
        ${
          pool.performanceMeasuredCount
            ? `<li>${escapeHtml(`사후 성과: ${pool.performanceMeasuredCount}건 관측 · 승률 ${pool.performanceHitRate || "-"} · 평균 ${pool.performanceAverageChange || "-"}`)}</li>`
            : ""
        }
        ${pool.stateChangedAt ? `<li>${escapeHtml(`최근 상태 변경: ${timeLabel(pool.stateChangedAt)}`)}</li>` : ""}
      </ul>
      ${
        history.length
          ? `<div class="selection-notes">
              <div class="section-title">
                <p class="eyebrow">상태 이력</p>
                <h2>최근 승격·강등</h2>
              </div>
              <ul class="bullet-list">
                ${history
                  .map((entry) => `<li>${escapeHtml(`${timeLabel(entry.at)} · ${entry.fromLabel || entry.from} → ${entry.toLabel || entry.to} · ${entry.reason || ""}`)}</li>`)
                  .join("")}
              </ul>
            </div>`
          : ""
      }
    </section>
  `;
}

function hiddenOpportunitySection(item) {
  const opportunity = item.hiddenOpportunity ?? {};
  const score = Number(opportunity.score ?? 0);
  const signals = uniqueTexts(opportunity.signals ?? [], 4);
  if (!score && !signals.length) return "";
  const tierText = opportunity.tier === "hidden" ? "숨은 후보" : "일반 후보";
  return `
    <section class="detail-section">
      <div class="section-title">
        <p class="eyebrow">발굴 신호</p>
        <h2>숨은 기회 ${escapeHtml(`${score}/18`)}</h2>
      </div>
      <div class="stat-grid">
        ${statCard("분류", tierText)}
        ${statCard("기회 점수", `${score}/18`)}
      </div>
      ${
        signals.length
          ? `<ul class="bullet-list">${signals.map((text) => `<li>${escapeHtml(text)}</li>`).join("")}</ul>`
          : ""
      }
    </section>
  `;
}

function signalValidationSection(item) {
  const validation = signalValidationForDisplay(item);
  if (!validation.label && !validation.score) return "";
  const reasons = uniqueTexts(validation.reasons ?? [], 4);
  const blockers = uniqueTexts([...(validation.blockers ?? []), ...(validation.reactionBlockers ?? [])], 6);
  return `
    <section class="detail-section">
      <div class="section-title">
        <p class="eyebrow">근거와 가격 검증</p>
        <h2>${escapeHtml(validation.label)}</h2>
      </div>
      <div class="stat-grid">
        ${statCard("검증 점수", `${validation.score}/100`)}
        ${statCard("발굴 근거", `${validation.evidenceScore}/100`)}
        ${statCard("가격 반응", `${validation.reactionScore}/100`)}
        ${validation.reactionGate ? statCard("반응 게이트", reactionGateLabel(validation.reactionGate)) : ""}
        ${statCard("데이터 신뢰", `${validation.confidenceScore}/100`)}
      </div>
      ${
        reasons.length
          ? `<ul class="bullet-list entry-list">${reasons.map((text) => `<li>${escapeHtml(text)}</li>`).join("")}</ul>`
          : ""
      }
      ${
        blockers.length
          ? `<ul class="bullet-list risk-list">${blockers.map((text) => `<li>${escapeHtml(text)}</li>`).join("")}</ul>`
          : ""
      }
    </section>
  `;
}

function discoveryEvidenceSection(item) {
  const evidence = discoveryEvidenceForDisplay(item);
  if (!evidence.label && !evidence.score && !evidence.newsItems && !evidence.filteredNewsItems) return "";
  const reasons = uniqueTexts(evidence.reasons ?? [], 4);
  const blockers = uniqueTexts(evidence.blockers ?? [], 4);
  const impactTypes = uniqueTexts(evidence.impactTypes ?? [], 4);
  return `
    <section class="detail-section">
      <div class="section-title">
        <p class="eyebrow">발굴 검증</p>
        <h2>${escapeHtml(evidence.label || "발굴 근거 확인")}</h2>
      </div>
      <div class="stat-grid">
        ${statCard("근거 점수", `${evidence.score}/100`)}
        ${statCard("고관련 뉴스", `${evidence.newsItems}건`)}
        ${statCard("뉴스 제외", `${evidence.filteredNewsItems}건`)}
        ${statCard("평균 관련성", evidence.averageRelevance ? `${evidence.averageRelevance}/100` : "-")}
      </div>
      ${
        impactTypes.length
          ? `<div class="chips">${impactTypes.map((label) => `<span class="chip">${escapeHtml(label)}</span>`).join("")}</div>`
          : ""
      }
      ${
        reasons.length
          ? `<ul class="bullet-list entry-list">${reasons.map((text) => `<li>${escapeHtml(text)}</li>`).join("")}</ul>`
          : ""
      }
      ${
        blockers.length
          ? `<ul class="bullet-list risk-list">${blockers.map((text) => `<li>${escapeHtml(text)}</li>`).join("")}</ul>`
          : ""
      }
    </section>
  `;
}

function analysisSummary(item) {
  const analysis = item.aiAnalysis;
  if (!analysis) return "";
  return `
    <div>
      <div class="section-title">
        <p class="eyebrow">AI 판단</p>
        <h2>${escapeHtml(actionBiasLabel(analysis.actionBias))}</h2>
      </div>
      <div class="stat-grid">
        ${statCard("영향", `${analysis.impactScore ?? 0}/100`)}
        ${statCard("리스크", `${analysis.riskScore ?? 0}/100`)}
        ${statCard("신뢰도", `${analysis.confidenceScore ?? 0}/100`)}
        ${statCard("출처", analysis.source === "openai" ? "OpenAI" : "로컬")}
      </div>
    </div>
  `;
}

function selectionNotes(item) {
  const notes = uniqueTexts(item.selection?.notes ?? [], 5);
  if (!notes.length) return "";
  const scoreChange = Number(item.selection?.scoreChange ?? 0);
  const changeText = scoreChange > 0 ? `+${scoreChange}` : `${scoreChange}`;
  return `
    <div class="selection-notes">
      <div class="section-title">
        <p class="eyebrow">선정 기준</p>
        <h2>실시간 신호 반영 ${escapeHtml(changeText)}</h2>
      </div>
      <ul class="bullet-list">
        ${notes.map((text) => `<li>${escapeHtml(text)}</li>`).join("")}
      </ul>
    </div>
  `;
}

function actionBiasLabel(value) {
  if (value === "watch") return "조건 충족 시 관찰";
  if (value === "avoid") return "오늘은 회피 우선";
  return "눌림 또는 확인 대기";
}

function priceMeta(item) {
  const freshness = priceFreshnessInfo(item);
  const candleText =
    item.liveCandles?.source === "toss"
      ? ` · 일봉 ${item.liveCandles.count ?? 0}개 반영`
      : item.liveCandles?.source === "stale"
        ? " · 일봉이 오래되어 등락률은 기존 기준 유지"
      : "";
  if (item.livePrice?.source === "toss") {
    const timestamp = freshness.ageText ? ` · ${freshness.ageText}` : "";
    const pollText = state.livePrice?.pollSeconds ? ` · ${state.livePrice.pollSeconds}초 갱신` : "";
    const retainedText = item.livePrice.retained ? " · 직전가 유지" : "";
    const changeText =
      item.livePrice.changeSource === "toss-prices"
        ? " · 등락률 실시간 반영"
        : item.livePrice.changeSource === "toss-candles"
          ? " · 전일 대비는 일봉 기준 추정"
          : item.livePrice.changeSource === "missing"
            ? " · 현재가 수신 · 등락률 확인중"
            : item.livePrice.changeSource === "pending-change"
              ? " · 현재가 수신 · 등락률 확인중"
              : item.livePrice.changeSource === "retained-change" || item.livePrice.changeSource === "stored-candidate-data"
                ? " · 저장 등락률 유지"
                : "";
    const warningText = item.livePrice.baselineWarning
      ? ` · 기준가 차이 확인 필요(${item.livePrice.baselineDifferencePercent ?? ""})`
      : "";
    const sourceText = freshness.isFresh ? "토스 실시간" : freshness.isBaseline ? "토스 장마감 기준가" : `토스 ${freshness.label}`;
    const holdText = freshness.isFresh ? "" : freshness.isBaseline ? " · 개장 후 실시간 반응 확인" : " · 신규 진입 판단 보류";
    return `현재가: ${sourceText}${timestamp}${pollText}${retainedText}${changeText}${warningText}${holdText}${candleText}`;
  }
  return `현재가: ${freshness.label} · ${freshness.message || item.livePrice?.message || "실시간 가격 대기"}${candleText}`;
}

function drawChart(values) {
  const canvas = document.querySelector("#miniChart");
  if (!canvas || !values?.length) return;

  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  const padding = 24;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = Math.max(max - min, 1);
  const points = values.map((value, index) => {
    const x = padding + (index / (values.length - 1)) * (width - padding * 2);
    const y = height - padding - ((value - min) / range) * (height - padding * 2);
    return { x, y };
  });

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#0d0f14";
  ctx.fillRect(0, 0, width, height);

  ctx.strokeStyle = "rgba(154, 167, 184, 0.16)";
  ctx.lineWidth = 1;
  for (let i = 0; i < 4; i += 1) {
    const y = padding + i * ((height - padding * 2) / 3);
    ctx.beginPath();
    ctx.moveTo(padding, y);
    ctx.lineTo(width - padding, y);
    ctx.stroke();
  }

  const gradient = ctx.createLinearGradient(0, padding, 0, height - padding);
  gradient.addColorStop(0, "rgba(123, 216, 143, 0.28)");
  gradient.addColorStop(1, "rgba(105, 210, 231, 0.02)");
  ctx.beginPath();
  ctx.moveTo(points[0].x, height - padding);
  points.forEach((point) => ctx.lineTo(point.x, point.y));
  ctx.lineTo(points[points.length - 1].x, height - padding);
  ctx.closePath();
  ctx.fillStyle = gradient;
  ctx.fill();

  ctx.beginPath();
  points.forEach((point, index) => {
    if (index === 0) ctx.moveTo(point.x, point.y);
    else ctx.lineTo(point.x, point.y);
  });
  ctx.strokeStyle = "#7bd88f";
  ctx.lineWidth = 5;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.stroke();

  const last = points[points.length - 1];
  ctx.fillStyle = "#f4f7fb";
  ctx.beginPath();
  ctx.arc(last.x, last.y, 7, 0, Math.PI * 2);
  ctx.fill();
}

function setWatchButtonState(watched, loading = false) {
  const button = document.querySelector("#watchButton");
  if (!button) return;
  const label = watched ? "관심 해제" : "관심 등록";
  button.classList.toggle("active", watched);
  button.classList.toggle("loading", loading);
  button.disabled = loading;
  button.setAttribute("aria-label", label);
  button.title = label;
  const hiddenLabel = button.querySelector(".sr-only");
  if (hiddenLabel) hiddenLabel.textContent = label;
}

function applyWatchStateToCandidate(candidate, symbol, watched) {
  if (!candidate || String(candidate.symbol) !== String(symbol)) return;
  candidate.isWatched = watched;
}

function setCandidateWatchState(symbol, watched) {
  (state.dashboard?.candidates ?? []).forEach((candidate) => {
    applyWatchStateToCandidate(candidate, symbol, watched);
  });
  applyWatchStateToCandidate(state.dashboard?.selected, symbol, watched);
  applyWatchStateToCandidate(state.selectedLookup, symbol, watched);
  if (state.stockSearch?.items?.length) {
    state.stockSearch.items.forEach((candidate) => {
      applyWatchStateToCandidate(candidate, symbol, watched);
    });
  }
}

function adjustWatchedSummary(symbol, previous, next) {
  if (!state.dashboard?.summary || previous === next) return;
  const hasCandidate = (state.dashboard?.candidates ?? []).some((candidate) => String(candidate.symbol) === String(symbol));
  if (!hasCandidate) return;
  const current = Number(state.dashboard.summary.watchedCount ?? 0);
  state.dashboard.summary.watchedCount = Math.max(0, current + (next ? 1 : -1));
  renderMetrics();
}

async function toggleWatch(item) {
  const symbol = item?.symbol;
  if (!symbol) return;
  const previous = Boolean(item.isWatched);
  const next = !previous;

  setCandidateWatchState(symbol, next);
  adjustWatchedSummary(symbol, previous, next);
  setWatchButtonState(next, true);
  renderFeed();
  renderTradeDecisionStatus();

  try {
    const payload = await postJson("/api/watchlist", { symbol, watch: next });
    const symbols = Array.isArray(payload?.symbols)
      ? new Set(payload.symbols.map((value) => String(value)))
      : null;
    const confirmed = symbols ? symbols.has(String(symbol)) : next;
    if (confirmed !== next) {
      setCandidateWatchState(symbol, confirmed);
      adjustWatchedSummary(symbol, next, confirmed);
    }
    setWatchButtonState(confirmed, false);
    renderFeed();
    renderTradeDecisionStatus();
    saveDashboardToBrowserCache(state.dashboard);
  } catch (error) {
    setCandidateWatchState(symbol, previous);
    adjustWatchedSummary(symbol, next, previous);
    setWatchButtonState(previous, false);
    renderFeed();
    renderTradeDecisionStatus();
    saveDashboardToBrowserCache(state.dashboard);
    window.alert("관심 목록 변경에 실패했습니다. 다시 시도해 주세요.");
  }
}

function updateViewButtons() {
  if (els.performanceButton) {
    els.performanceButton.classList.toggle("active", state.view === "performance");
    els.performanceButton.textContent = state.view === "performance" ? "데스크" : "성과";
  }
  if (els.settingsButton) {
    els.settingsButton.classList.toggle("active", state.view === "settings");
  }
}

function updateShellView() {
  const settingsOpen = state.view === "settings";
  if (els.workspaceView) {
    els.workspaceView.hidden = settingsOpen;
  }
  if (els.settingsView) {
    els.settingsView.hidden = !settingsOpen;
  }
}

async function showPerformanceView() {
  state.view = state.view === "performance" ? "signals" : "performance";
  updateViewButtons();
  updateShellView();
  if (state.view === "performance") {
    await loadPerformance();
  } else {
    renderDetail();
  }
}

function showSettingsView() {
  state.view = state.view === "settings" ? "signals" : "settings";
  updateViewButtons();
  updateShellView();
  if (state.view === "settings") {
    renderSettingsPanels();
  }
  if (state.view === "signals") {
    renderDetail();
  }
}

function showDeskView() {
  state.view = "signals";
  updateViewButtons();
  updateShellView();
  renderDetail();
}

function changeAnalysisMode(mode) {
  mode = normalizeAnalysisMode(mode);
  if (!mode || mode === state.mode) {
    state.modeAutoFollow = mode === normalizeAnalysisMode(detectedAnalysisMode());
    updateModeStatus();
    return;
  }
  state.view = "signals";
  updateViewButtons();
  updateShellView();
  state.mode = mode;
  state.modeAutoFollow = mode === normalizeAnalysisMode(detectedAnalysisMode());
  state.selectedSymbol = null;
  state.selectedLookup = null;
  updateModeStatus();
  loadDashboard();
}

if (els.modeSelect) {
  els.modeSelect.addEventListener("change", (event) => {
    changeAnalysisMode(event.target.value);
  });
}

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((target) => target.classList.remove("active"));
    button.classList.add("active");
    state.filter = button.dataset.filter;
    state.selectedLookup = null;
    state.feedExpanded = false;
    renderFeed();
    renderTradeDecisionStatus();
    renderDetail();
    refreshLivePrices();
  });
});

document.querySelectorAll(".strategy-button").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".strategy-button").forEach((target) => target.classList.remove("active"));
    button.classList.add("active");
    state.strategy = button.dataset.strategy || "action";
    state.selectedLookup = null;
    state.feedExpanded = false;
    renderFeed();
    renderTradeDecisionStatus();
    renderDetail();
    refreshLivePrices();
  });
});

els.searchInput.addEventListener("input", (event) => {
  state.query = event.target.value;
  state.selectedLookup = null;
  state.feedExpanded = false;
  if (state.searchTimer) {
    window.clearTimeout(state.searchTimer);
  }
  state.searchTimer = window.setTimeout(() => {
    loadStockSearch();
  }, 280);
  renderFeed();
  renderTradeDecisionStatus();
  renderDetail();
});

els.searchInput.addEventListener("keydown", (event) => {
  if (event.key === "ArrowDown" && shouldSearchStocks(state.query)) {
    event.preventDefault();
    if ((state.stockSearch.items ?? []).length) {
      setStockSearchActiveIndex(Number(state.stockSearch.activeIndex ?? -1) + 1);
    } else {
      loadStockSearch();
    }
    return;
  }
  if (event.key === "ArrowUp" && shouldSearchStocks(state.query)) {
    event.preventDefault();
    if ((state.stockSearch.items ?? []).length) {
      setStockSearchActiveIndex(Number(state.stockSearch.activeIndex ?? 0) - 1);
    }
    return;
  }
  if (event.key === "Enter") {
    const currentQuery = state.query.trim();
    const selected = state.stockSearch.query === currentQuery ? stockSearchActiveItem() : null;
    if (selected?.symbol) {
      event.preventDefault();
      openSearchResult(selected.symbol);
    } else if (shouldSearchStocks(state.query)) {
      event.preventDefault();
      loadStockSearch();
    }
  }
  if (event.key === "Escape") {
    applySearchQuery("");
  }
});

if (els.performanceButton) {
  els.performanceButton.addEventListener("click", showPerformanceView);
}

if (els.settingsButton) {
  els.settingsButton.addEventListener("click", showSettingsView);
}

if (els.deskButton) {
  els.deskButton.addEventListener("click", showDeskView);
}

els.refreshButton.addEventListener("click", () => {
  if (state.view === "performance") {
    loadPerformance();
    return;
  }
  loadDashboard();
});

function refreshAutoAnalysisMode() {
  const nextAutoMode = normalizeAnalysisMode(detectedAnalysisMode());
  const changed = nextAutoMode !== state.autoMode;
  state.autoMode = nextAutoMode;
  if (changed && state.modeAutoFollow && state.mode !== nextAutoMode) {
    state.mode = nextAutoMode;
    state.selectedSymbol = null;
    state.selectedLookup = null;
    updateModeStatus();
    if (state.view === "signals") {
      loadDashboard();
    }
    return;
  }
  updateModeStatus();
}

async function refreshSchedulerStatusOnly() {
  const status = await safeFetchJson("/api/scheduler/status", statusFallbacks().scheduler, 5000);
  const storage = await safeFetchJson("/api/storage/status", statusFallbacks().storage, 5000);
  const evidence = await safeFetchJson("/api/evidence/status", statusFallbacks().evidence, 5000);
  const stockMaster = await safeFetchJson("/api/stocks/master/status", statusFallbacks().stockMaster, 5000);
  const portfolio = await safeFetchJson("/api/portfolio/status", statusFallbacks().portfolio, 5000);
  state.schedulerStatus = status;
  state.storageStatus = storage;
  state.evidenceStatus = evidence;
  state.stockMasterStatus = stockMaster;
  state.portfolioStatus = portfolio;
  maybeNotifySchedulerRun(status);
  renderSchedulerStatus();
  renderStorageStatus();
  renderEvidenceStatus();
  renderStockMasterStatus();
  renderPortfolioStatus();
  renderSnapshotHistory();
}

window.setInterval(() => {
  refreshSchedulerStatusOnly();
}, 60000);

window.setInterval(() => {
  refreshAutoAnalysisMode();
}, 60000);

updateModeStatus();

loadDashboard().catch(() => {
  els.signalDetail.innerHTML = `
    <div class="empty-state">
      <h2>데이터를 불러오지 못했습니다</h2>
      <p>백엔드 서버가 실행 중인지 확인하세요.</p>
    </div>
  `;
});
