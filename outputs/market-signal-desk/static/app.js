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

const state = {
  view: "signals",
  mode: "close",
  filter: "all",
  query: "",
  dashboard: null,
  stockSearch: {
    query: "",
    loading: false,
    items: [],
    message: "",
    status: null
  },
  selectedLookup: null,
  searchTimer: null,
  performance: null,
  performanceLoading: false,
  authEnabled: false,
  authRequired: false,
  adminToken: readStoredValue("marketSignalAdminToken", ""),
  schedulerStatus: null,
  storageStatus: null,
  portfolioStatus: null,
  viewingSnapshot: null,
  selectedSymbol: null,
  notificationsEnabled: readStoredValue("marketSignalNotifications") === "1",
  lastNotifiedKey: readStoredValue("marketSignalLastNotifiedKey", ""),
  lastRunNotifiedId: readStoredValue("marketSignalLastRunNotifiedId", ""),
  schedulerStatusInitialized: false
};

const els = {
  candidateFeed: document.querySelector("#candidateFeed"),
  signalDetail: document.querySelector("#signalDetail"),
  workspaceView: document.querySelector("#workspaceView"),
  settingsView: document.querySelector("#settingsView"),
  candidateCount: document.querySelector("#candidateCount"),
  searchInput: document.querySelector("#searchInput"),
  stockSearchResults: document.querySelector("#stockSearchResults"),
  principles: document.querySelector("#principles"),
  kospiValue: document.querySelector("#kospiValue"),
  kosdaqValue: document.querySelector("#kosdaqValue"),
  nasdaqValue: document.querySelector("#nasdaqValue"),
  usdKrwValue: document.querySelector("#usdKrwValue"),
  marketNote: document.querySelector("#marketNote"),
  metricCandidates: document.querySelector("#metricCandidates"),
  metricHighScore: document.querySelector("#metricHighScore"),
  metricReady: document.querySelector("#metricReady"),
  metricWatched: document.querySelector("#metricWatched"),
  tradeDecisionStatus: document.querySelector("#tradeDecisionStatus"),
  nextSteps: document.querySelector("#nextSteps"),
  marketStatus: document.querySelector("#marketStatus"),
  authStatus: document.querySelector("#authStatus"),
  notificationStatus: document.querySelector("#notificationStatus"),
  schedulerStatus: document.querySelector("#schedulerStatus"),
  readinessStatus: document.querySelector("#readinessStatus"),
  storageStatus: document.querySelector("#storageStatus"),
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

function scoreClass(score) {
  if (score >= 75) return "";
  if (score >= 55) return "warn";
  return "low";
}

function changeClass(change) {
  return String(change).trim().startsWith("-") ? "change-down" : "change-up";
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
      config: { enabled: false, jobs: [] },
      state: { started: false, running: false, lastError: "" },
      recentRuns: []
    },
    storage: {
      mode: "filesystem",
      implementation: "filesystem",
      runsDir: "",
      writable: false,
      persistent: false,
      recentRunCount: 0
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

async function loadDashboard() {
  state.viewingSnapshot = null;
  const fallbacks = statusFallbacks();
  const statusPromise = Promise.all([
    safeFetchJson("/api/auth/status", fallbacks.auth),
    safeFetchJson("/api/scheduler/status", fallbacks.scheduler),
    safeFetchJson("/api/storage/status", fallbacks.storage),
    safeFetchJson("/api/portfolio/status", fallbacks.portfolio),
    safeFetchJson("/api/network/outbound-ip", fallbacks.network),
    safeFetchJson("/api/integrations/toss/status", fallbacks.toss),
    safeFetchJson("/api/integrations/dart/status", fallbacks.dart),
    safeFetchJson("/api/integrations/news/status", fallbacks.news),
    safeFetchJson("/api/integrations/openai/status", fallbacks.openai)
  ]).then(([authStatus, schedulerStatus, storageStatus, portfolioStatus, networkStatus, tossStatus, dartStatus, newsStatus, openaiStatus]) => {
    state.authEnabled = Boolean(authStatus?.enabled);
    state.schedulerStatus = schedulerStatus;
    state.storageStatus = storageStatus;
    state.portfolioStatus = portfolioStatus;
    state.networkStatus = networkStatus;
    state.tossStatus = tossStatus;
    state.dartStatus = dartStatus;
    state.newsStatus = newsStatus;
    state.openaiStatus = openaiStatus;
    maybeNotifySchedulerRun(schedulerStatus);
    renderAuthStatus();
    renderSchedulerStatus();
    renderReadinessStatus();
    renderStorageStatus();
    renderPortfolioStatus();
    renderSnapshotHistory();
    renderNotificationStatus();
    renderNextSteps();
    renderMarketStatus();
    renderNetworkStatus();
    renderTossStatus();
    renderDartStatus();
    renderNewsStatus();
    renderOpenAIStatus();
  });

  try {
    const dashboard = await fetchJson(`/api/dashboard?mode=${state.mode}`, 30000);
    state.dashboard = dashboard;
    if (!state.selectedSymbol && state.dashboard.selected) {
      state.selectedSymbol = state.dashboard.selected.symbol;
    }
    await statusPromise;
    render();
  } catch (error) {
    await statusPromise;
    state.dashboard = null;
    if (isAuthError(error)) {
      renderAuthGate();
      return;
    }
    renderLoadError(error);
  }
}

async function loadPerformance() {
  state.performanceLoading = true;
  renderPerformance();
  try {
    state.performance = await fetchJson("/api/performance?limit=12&top=3", 30000);
  } catch (error) {
    if (isAuthError(error)) {
      state.performanceLoading = false;
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
    renderPerformance();
  }
}

function renderLoadError(error) {
  const message = error?.name === "AbortError" ? "외부 API 응답이 지연되고 있습니다." : "백엔드 서버 응답을 받지 못했습니다.";
  els.candidateCount.textContent = "0개";
  els.metricCandidates.textContent = 0;
  els.metricHighScore.textContent = 0;
  els.metricReady.textContent = 0;
  els.metricWatched.textContent = 0;
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

function selectedCandidate() {
  if (state.selectedLookup?.symbol === state.selectedSymbol) {
    return state.selectedLookup;
  }
  const candidates = state.dashboard?.candidates ?? [];
  return (
    candidates.find((item) => item.symbol === state.selectedSymbol) ||
    candidates[0] ||
    null
  );
}

function candidateFromSearchResult(item) {
  const tags = uniqueTexts([
    "종목 검색",
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
    headline: item.headline || "후보 편입 전 종목 조회",
    verdict: "후보 편입 전",
    stage: "lookup",
    totalScore: 0,
    triggerReadiness: 0,
    preopenPriority: 0,
    score: {},
    tags,
    thesis: "오늘 후보로 점수화되기 전의 직접 조회 결과입니다. 뉴스, 공시, 가격 반응을 확인한 뒤 후보 편입 여부를 먼저 판단해야 합니다.",
    why: [
      `${item.name || item.symbol} 기본정보를 조회했습니다.`,
      item.price && item.price !== "-" ? `현재가 ${item.price} 기준으로 추가 분석을 시작할 수 있습니다.` : "현재가는 아직 연결되지 않았습니다.",
      "후보 점수화 전에는 신규 매수 판단보다 관찰 목록 편입 여부를 먼저 봅니다."
    ],
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
    lookupOnly: true
  };
}

function tradeActionText(item) {
  const score = Number(item?.totalScore ?? 0);
  const verdict = String(item?.verdict ?? "");
  if (score >= 75 && !verdict.includes("회피")) return "조건 확인 후 관찰";
  if (score >= 55) return "가격대 대기";
  return "오늘은 제외 우선";
}

function tradeActionOk(item) {
  const score = Number(item?.totalScore ?? 0);
  const verdict = String(item?.verdict ?? "");
  return score >= 55 && !verdict.includes("회피");
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
  const rows = [
    ["선택", true, item.name ?? item.symbol ?? "-"],
    ["점수", Number(item.totalScore ?? 0) >= 75, `${item.totalScore ?? 0}/100`],
    ["현재가", Boolean(item.price), `${item.price ?? "-"} ${item.change ?? ""}`.trim()],
    ["판정", tradeActionOk(item), tradeActionText(item)]
  ];
  els.tradeDecisionStatus.innerHTML = rows
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

function render() {
  updateShellView();
  renderMarket();
  renderMetrics();
  renderTradeDecisionStatus();
  renderAuthStatus();
  renderSchedulerStatus();
  renderReadinessStatus();
  renderStorageStatus();
  renderPortfolioStatus();
  renderSnapshotHistory();
  renderNotificationStatus();
  renderNextSteps();
  renderMarketStatus();
  renderNetworkStatus();
  renderTossStatus();
  renderDartStatus();
  renderNewsStatus();
  renderOpenAIStatus();
  renderPrinciples();
  renderFeed();
  renderCurrentView();
  if (state.view === "signals") {
    maybeNotifyDashboard();
  }
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
  if (state.authEnabled) {
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
  const hasToken = Boolean(state.adminToken);
  const rows = [
    ["보호 상태", enabled, enabled ? "켜짐" : "꺼짐"],
    ["토큰 저장", !enabled || hasToken, hasToken ? "있음" : enabled ? "필요" : "불필요"],
    ["API 접근", !enabled || (hasToken && !state.authRequired), !enabled ? "공개" : state.authRequired ? "확인 필요" : "허용"]
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
  return candidates.find((item) => {
    const score = Number(item.totalScore ?? 0);
    const readiness = Number(item.triggerReadiness ?? 0);
    const verdict = String(item.verdict ?? "");
    return score >= 75 || readiness >= 70 || verdict.includes("조건 충족") || verdict.includes("준비");
  });
}

function notificationKeyForCandidate(item) {
  return [
    "candidate",
    state.dashboard?.generatedAt ?? "",
    item.symbol ?? "",
    item.totalScore ?? "",
    item.triggerReadiness ?? ""
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
  const item = notificationCandidate();
  if (!item || !notificationEnabled()) return;
  const key = notificationKeyForCandidate(item);
  if (state.lastNotifiedKey === key) return;
  const body = shortText(`${item.name} ${item.totalScore}점 · ${item.verdict || item.headline}`, 90);
  if (sendBrowserNotification("관찰 후보 감지", body, key)) {
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
    "조건이 준비된 후보가 나오면 이 방식으로 알림을 보냅니다.",
    "market-signal-test"
  );
}

function renderNotificationStatus() {
  if (!els.notificationStatus) return;
  const supported = notificationSupported();
  const permission = notificationPermission();
  const enabled = notificationEnabled();
  const candidate = notificationCandidate();
  const autoText = enabled ? "켜짐" : state.notificationsEnabled ? "권한 필요" : "꺼짐";
  const rows = [
    ["브라우저 지원", supported, supported ? "가능" : "미지원"],
    ["권한", permission === "granted", notificationPermissionLabel(permission)],
    ["자동 알림", enabled, autoText],
    ["감시 조건", Boolean(candidate), candidate ? `${candidate.name} ${candidate.totalScore}점` : "대기"]
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

function renderMarket() {
  const market = state.dashboard?.market ?? {};
  els.kospiValue.textContent = market.kospi ?? "-";
  els.kosdaqValue.textContent = market.kosdaq ?? "-";
  els.nasdaqValue.textContent = market.nasdaq ?? "-";
  els.usdKrwValue.textContent = market.usdKrw ?? "-";
  const fxSource = market.usdKrwSource;
  const fxText =
    fxSource?.source === "fx-api"
      ? `환율: ${fxSource.provider}${fxSource.timestamp ? ` · ${fxSource.timestamp}` : ""}`
      : fxSource?.source === "sample"
        ? "환율: 샘플"
        : "";
  const indexSource = market.indexSource;
  const indexText =
    indexSource?.source === "index-api"
      ? `지수: ${indexSource.provider}${indexSource.timestamp ? ` · ${indexSource.timestamp}` : ""}`
      : indexSource?.source === "index-api-partial"
        ? `지수: ${indexSource.provider} 일부`
        : indexSource?.source === "sample"
          ? "지수: 샘플"
          : "";
  const snapshotText = state.viewingSnapshot
    ? `스냅샷 보기: ${modeLabel(state.viewingSnapshot.mode)} · ${timeLabel(state.viewingSnapshot.createdAt)}`
    : "";
  els.marketNote.textContent = [snapshotText, market.note, fxText, indexText].filter(Boolean).join(" ");
}

function renderMetrics() {
  const summary = state.dashboard?.summary ?? {};
  els.candidateCount.textContent = `${summary.candidateCount ?? 0}개`;
  els.metricCandidates.textContent = summary.candidateCount ?? 0;
  els.metricHighScore.textContent = summary.highScoreCount ?? 0;
  els.metricReady.textContent = summary.readyCount ?? 0;
  els.metricWatched.textContent = summary.watchedCount ?? 0;
}

function renderNextSteps() {
  if (!els.nextSteps) return;
  const readiness = readinessState();
  const steps = [];
  if (!readiness.tossReady) {
    steps.push("Toss 출처 확인");
    steps.push("허용 IP 점검");
    steps.push("현재가부터 재검증");
  } else if (!readiness.contextReady) {
    steps.push("뉴스·공시·AI 점검");
    steps.push("분석 출처 확인");
    steps.push("후보 점수 재확인");
  } else if (!readiness.manualRunReady) {
    steps.push("장마감 수동 실행");
    steps.push("스냅샷 저장 확인");
    steps.push("성과 화면 점검");
  } else if (!readiness.autoEnabled) {
    steps.push("자동 실행 켜기");
    steps.push("장전·장마감 예약 확인");
    steps.push("알림 조건 확정");
  } else {
    steps.push("성과 리포트 관찰");
    steps.push("선정 기준 튜닝");
    steps.push("외부 알림 채널 확장");
  }
  els.nextSteps.innerHTML = steps
    .map((step, index) => `
      <div>
        <strong>${index + 1}</strong>
        <span>${escapeHtml(step)}</span>
      </div>
    `)
    .join("");
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
  if (mode === "preopen") return "장전";
  if (mode === "intraday") return "장중";
  return "장마감";
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
  const rows = [
    ["자동 실행", config.enabled, config.enabled ? "켜짐" : "꺼짐"],
    ["실행 상태", !schedulerState.running && !schedulerState.lastError, schedulerState.running ? "실행 중" : schedulerState.lastError ? "확인 필요" : "대기"],
    ["예약", true, jobText],
    ["다음 실행", Boolean(config.enabled && nextRun?.runAt), nextRunText],
    ["최근 실행", Boolean(latest), runText]
  ];
  const lastError = schedulerState.lastError
    ? `<div><span>최근 오류</span><strong class="warn">${escapeHtml(schedulerState.lastError)}</strong></div>`
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
    <div class="schedule-actions">
      <button type="button" data-scheduler-mode="close">장마감 실행</button>
      <button type="button" data-scheduler-mode="preopen">장전 실행</button>
    </div>
  `;
  els.schedulerStatus.querySelectorAll("[data-scheduler-mode]").forEach((button) => {
    button.addEventListener("click", async () => {
      await runSchedulerMode(button.dataset.schedulerMode);
    });
  });
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
  const modeText = status.mode === "filesystem" ? "파일 저장" : status.mode || "-";
  const persistenceText = status.persistent ? "영구 설정" : "임시 보존";
  const latestText = status.latestRunCreatedAt
    ? `${status.recentRunCount ?? 0}건 · ${String(status.latestRunCreatedAt).replace("T", " ").slice(5, 16)}`
    : `${status.recentRunCount ?? 0}건`;
  const nextText = status.persistent ? "자동 실행 가능" : "DB/디스크 검토";
  const rows = [
    ["저장 방식", Boolean(status.mode), modeText],
    ["쓰기 가능", Boolean(status.writable), status.writable ? "가능" : shortText(status.error || "확인 필요", 28)],
    ["보존성", Boolean(status.persistent), persistenceText],
    ["최근 기록", Number(status.recentRunCount ?? 0) > 0, latestText],
    ["다음", status.persistent && status.writable, nextText]
  ];
  els.storageStatus.innerHTML = rows
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

function isPositiveText(value) {
  const text = String(value ?? "").trim();
  return Boolean(text && text !== "-" && !text.startsWith("-"));
}

function renderPortfolioStatus() {
  if (!els.portfolioStatus) return;
  const status = state.portfolioStatus;
  if (!status) return;
  const summary = status.summary ?? {};
  const buyingPower = status.buyingPower ?? {};
  const selectedAccount = status.selectedAccount ?? {};
  const items = Array.isArray(status.items) ? status.items : [];
  const krwPower = buyingPower.KRW?.cashBuyingPower ?? "-";
  const usdPower = buyingPower.USD?.cashBuyingPower ?? "-";
  const accountLabel = selectedAccount.accountNoPreview || (status.selectedAccountSeq ? "연결됨" : "-");
  const rows = [
    [
      "자산 조회",
      Boolean(status.enabled && status.ready && status.source === "toss"),
      !status.enabled ? "꺼짐" : status.ready ? "읽기 가능" : "대기"
    ],
    ["계좌", Boolean(status.selectedAccountSeq), accountLabel],
    ["보유", Number(summary.holdingCount ?? 0) > 0, `${summary.holdingCount ?? 0}종목`],
    ["총 손익률", isPositiveText(summary.profitLossRate), summary.profitLossRate ?? "-"],
    ["오늘", isPositiveText(summary.dailyProfitLossRate), summary.dailyProfitLossRate ?? "-"],
    ["매수 가능", krwPower !== "-" || usdPower !== "-", `${krwPower}${usdPower !== "-" ? ` · ${usdPower}` : ""}`]
  ];
  const holdingRows = items.slice(0, 3).map((item) => [
    item.name || item.symbol || "보유 종목",
    !String(item.judgement ?? "").includes("경계"),
    `${item.judgement ?? "보유"} · ${item.profitLossRate ?? "-"}`
  ]);
  els.portfolioStatus.innerHTML = [...rows, ...holdingRows]
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
    maybeNotifySchedulerRun(state.schedulerStatus);
    renderSchedulerStatus();
    renderStorageStatus();
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
          : "샘플"
    ],
    [
      "환율 조회",
      fxOk,
      fxStatus?.source === "fx-api" ? `${fxStatus.provider ?? "API"}` : "샘플"
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
  els.tossStatus.innerHTML = rows
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

function tossSourceLabel(status, liveEnabled, countKey) {
  if (!liveEnabled || status?.enabled === false) return "라이브 꺼짐";
  if (!status) return "확인 중";
  if (status.error) return status.status ? `오류 ${status.status}` : "오류";
  if (status.source === "skipped") return "제한";
  if (status.source === "stale") return "오래됨";
  if (status.source === "toss") return `토스 ${status[countKey] ?? 0}건`;
  return "샘플";
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
      disclosureStatus?.source === "opendart" ? `${disclosureStatus.disclosureCount ?? 0}건` : "샘플"
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

function newsSourceLabel(status, liveSource, sampleLabel = "샘플") {
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
  return sampleLabel;
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

function renderFeed() {
  const candidates = filteredCandidates();
  renderStockSearchResults();
  if (!candidates.length) {
    els.candidateFeed.innerHTML = `
      <div class="empty-state">
        <h2>조건에 맞는 후보가 없습니다</h2>
        <p>후보 밖 종목은 코드나 티커로 직접 조회할 수 있습니다.</p>
      </div>
    `;
    return;
  }

  els.candidateFeed.innerHTML = candidates
    .map((item) => {
      const active = item.symbol === state.selectedSymbol ? "active" : "";
      return `
        <button class="feed-item ${active}" data-symbol="${escapeHtml(item.symbol)}">
          <span class="logo-mark">${escapeHtml(initials(item.name))}</span>
          <span>
            <span class="feed-title">
              <strong>${escapeHtml(item.name)}</strong>
              <span>${escapeHtml(item.symbol)}</span>
            </span>
            <span class="feed-subtitle">${escapeHtml(item.headline)}</span>
          </span>
          <span class="feed-meta">
            <span class="score-pill ${scoreClass(item.totalScore)}">${item.totalScore}</span>
            <span class="feed-time">${escapeHtml(item.updated)}</span>
          </span>
        </button>
      `;
    })
    .join("");

  document.querySelectorAll(".feed-item").forEach((button) => {
    button.addEventListener("click", () => {
      state.view = "signals";
      updateShellView();
      updateViewButtons();
      state.selectedSymbol = button.dataset.symbol;
      renderFeed();
      renderTradeDecisionStatus();
      renderDetail();
    });
  });
}

function stockSearchSubtitle(item) {
  const parts = [
    item.sourceLabel,
    item.market,
    item.securityType,
    item.status,
    item.price && item.price !== "-" ? item.price : ""
  ].filter(Boolean);
  return parts.join(" · ") || "종목 검색 결과";
}

function openSearchResult(symbol) {
  const item = (state.stockSearch.items ?? []).find((entry) => entry.symbol === symbol);
  if (!item) return;
  const candidate = (state.dashboard?.candidates ?? []).find((entry) => entry.symbol === symbol);
  state.view = "signals";
  updateShellView();
  updateViewButtons();
  if (candidate) {
    state.selectedLookup = null;
    state.selectedSymbol = candidate.symbol;
  } else {
    state.selectedLookup = candidateFromSearchResult(item);
    state.selectedSymbol = item.symbol;
  }
  renderFeed();
  renderTradeDecisionStatus();
  renderDetail();
}

function renderStockSearchResults() {
  if (!els.stockSearchResults) return;
  const query = state.query.trim();
  const payload = state.stockSearch;
  if (query.length < 2) {
    els.stockSearchResults.hidden = true;
    els.stockSearchResults.innerHTML = "";
    return;
  }

  const items = payload.items ?? [];
  const stale = payload.query !== query;
  const loading = payload.loading || stale;
  const message = payload.message || payload.status?.message || "";
  els.stockSearchResults.hidden = false;
  els.stockSearchResults.innerHTML = `
    <div class="stock-search-head">
      <strong>종목 검색</strong>
      <span>${loading ? "조회 중" : items.length ? `${items.length}건` : "결과 없음"}</span>
    </div>
    ${
      items.length
        ? `<div class="stock-search-list">
            ${items
              .slice(0, 5)
              .map(
                (item) => `
                  <button class="stock-result" type="button" data-search-symbol="${escapeHtml(item.symbol)}">
                    <span class="logo-mark">${escapeHtml(initials(item.name || item.symbol))}</span>
                    <span>
                      <strong>${escapeHtml(item.name || item.symbol)}</strong>
                      <em>${escapeHtml(stockSearchSubtitle(item))}</em>
                    </span>
                    <span>${escapeHtml(item.inCandidates ? "후보 열기" : "조회")}</span>
                  </button>
                `
              )
              .join("")}
          </div>`
        : `<p>${escapeHtml(message || "후보 밖 종목은 005930, AAPL처럼 코드로 입력하세요.")}</p>`
    }
    ${message && items.length ? `<p>${escapeHtml(message)}</p>` : ""}
  `;

  els.stockSearchResults.querySelectorAll("[data-search-symbol]").forEach((button) => {
    button.addEventListener("click", () => openSearchResult(button.dataset.searchSymbol));
  });
}

async function loadStockSearch() {
  const query = state.query.trim();
  if (query.length < 2) {
    state.stockSearch = {
      query,
      loading: false,
      items: [],
      message: "",
      status: null
    };
    renderStockSearchResults();
    return;
  }

  state.stockSearch = {
    ...state.stockSearch,
    query,
    loading: true,
    message: ""
  };
  renderStockSearchResults();

  const payload = await safeFetchJson(
    `/api/stocks/search?query=${encodeURIComponent(query)}&limit=8`,
    { query, items: [], message: "종목 검색을 불러오지 못했습니다.", status: null },
    10000
  );
  if (state.query.trim() !== query) return;
  state.stockSearch = {
    query,
    loading: false,
    items: Array.isArray(payload.items) ? payload.items : [],
    message: payload.message || "",
    status: payload.status || null
  };
  renderStockSearchResults();
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

  els.signalDetail.innerHTML = `
    <div class="detail-hero">
      <div>
        <div class="hero-title">
          <span class="logo-mark">${escapeHtml(initials(item.name))}</span>
          <h2>${escapeHtml(item.name)}</h2>
          <span>${escapeHtml(item.price)}</span>
          <span class="${changeClass(item.change)}">${escapeHtml(item.change)}</span>
          <button class="watch-button ${item.isWatched ? "active" : ""}" id="watchButton">
            ${item.isWatched ? "관심 해제" : "관심 등록"}
          </button>
        </div>
        <p class="headline">${escapeHtml(item.headline)}</p>
        <p class="thesis">${escapeHtml(item.thesis)}</p>
        <p class="data-source">${escapeHtml(priceMeta(item))}</p>
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

    <div class="detail-grid">
      <section class="detail-section">
        <div class="section-title">
          <p class="eyebrow">진입 판단</p>
          <h2>조건 충족 시에만 관찰</h2>
        </div>
        <ul class="bullet-list entry-list">
          ${uniqueTexts(item.entryConditions, 6).map((text) => `<li>${escapeHtml(text)}</li>`).join("")}
        </ul>
      </section>

      <section class="detail-section">
        <div class="section-title">
          <p class="eyebrow">금지 조건</p>
          <h2>이 경우 진입하지 않음</h2>
        </div>
        <ul class="bullet-list avoid-list">
          ${uniqueTexts(item.noEntry, 6).map((text) => `<li>${escapeHtml(text)}</li>`).join("")}
        </ul>
      </section>

      <section class="detail-section">
        <div class="section-title">
          <p class="eyebrow">왜 후보인가</p>
          <h2>뉴스와 가격 반응</h2>
        </div>
        <ul class="bullet-list">
          ${uniqueTexts(item.why, 5).map((text) => `<li>${escapeHtml(text)}</li>`).join("")}
        </ul>
        ${selectionNotes(item)}
      </section>

      <section class="detail-section info-stack">
        <div>
          <div class="section-title">
            <p class="eyebrow">트렌드</p>
            <h2>관심도와 수급</h2>
          </div>
          <div class="stat-grid">
            ${statCard("뉴스", `${item.trend?.newsCount ?? 0}건`)}
            ${statCard("해외 뉴스", item.trend?.globalNewsCount != null ? `${item.trend.globalNewsCount}건` : "-")}
            ${statCard("뉴스 증가", item.trend?.newsSpike ?? "-")}
            ${statCard("거래량", item.trend?.volumeSpike ?? "-")}
            ${statCard("일 거래량", item.trend?.dailyVolume ?? "-")}
            ${statCard("체결", item.trend?.tradePressure ?? "-")}
            ${statCard("호가", item.trend?.orderbookPressure ?? "-")}
            ${statCard("스프레드", item.trend?.spread ?? "-")}
            ${statCard("감성", item.trend?.sentiment ?? "-")}
          </div>
        </div>
        ${analysisSummary(item)}
      </section>

      <section class="detail-section">
        <div class="section-title">
          <p class="eyebrow">손절 기준</p>
          <h2>매수 전에 정할 것</h2>
        </div>
        <ul class="bullet-list risk-list">
          ${uniqueTexts(item.stopRules, 5).map((text) => `<li>${escapeHtml(text)}</li>`).join("")}
        </ul>
      </section>

      <section class="detail-section">
        <div class="section-title">
          <p class="eyebrow">근거</p>
          <h2>뉴스와 공시 메모</h2>
        </div>
        <ul class="source-list">
          ${item.sources
            .map(
              (source) => `
                <li>
                  <strong>${escapeHtml(source.title)}</strong>
                  <span>${escapeHtml(source.publisher)} · ${escapeHtml(source.time)}${source.url ? " · 뉴스" : ""}</span>
                </li>
              `
            )
            .join("")}
        </ul>
      </section>

      <section class="detail-section">
        <div class="section-title">
          <p class="eyebrow">공시/리스크</p>
          <h2>확인할 문장</h2>
        </div>
        <ul class="bullet-list risk-list">
          ${uniqueTexts(item.disclosures, 6).map((text) => `<li>${escapeHtml(text)}</li>`).join("")}
        </ul>
      </section>

      <section class="detail-section">
        <div class="section-title">
          <p class="eyebrow">연관 종목</p>
          <h2>같이 볼 대상</h2>
        </div>
        <ul class="related-list">
          ${item.related
            .map(
              (related) => `
                <li>
                  <strong>${escapeHtml(related.name)} <span class="${changeClass(related.change)}">${escapeHtml(related.change)}</span></strong>
                  <span>${escapeHtml(related.symbol)} · ${escapeHtml(related.relation)}</span>
                </li>
              `
            )
            .join("")}
        </ul>
      </section>
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
  const priceSource = payload.priceStatus?.source === "toss" ? "토스 현재가" : "샘플 가격";
  const threshold = payload.config?.successThreshold ?? "+1.0%";
  const best = summary.best;
  const worst = summary.worst;

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
        ${performanceMetric("관측", summary.measuredCount ?? 0)}
        ${performanceMetric("상승 비율", summary.hitRate ?? "-")}
        ${performanceMetric("평균 변화", summary.averageChange ?? "-", changeClass(summary.averageChange ?? ""))}
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
            <p class="eyebrow">최고/최저</p>
            <h2>성과 범위</h2>
          </div>
          <div class="performance-extremes">
            ${performanceExtreme("최고", best)}
            ${performanceExtreme("최저", worst)}
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
                : `<div class="history-empty">장마감 또는 장전 스냅샷을 먼저 저장하세요</div>`
            }
          </div>
        </section>
      </div>
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
  return `
    <div class="performance-observation">
      <span>
        <strong>${escapeHtml(item.name)}</strong>
        <em>${escapeHtml(modeLabel(item.mode))} · ${escapeHtml(timeLabel(item.createdAt))} · ${escapeHtml(item.score)}점</em>
      </span>
      <span>
        <strong class="${tone}">${escapeHtml(item.change)}</strong>
        <em>${escapeHtml(item.snapshotPrice)} → ${escapeHtml(item.currentPrice)} · ${escapeHtml(item.outcome)}</em>
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
  const candleText =
    item.liveCandles?.source === "toss"
      ? ` · 일봉 ${item.liveCandles.count ?? 0}개 반영`
      : item.liveCandles?.source === "stale"
        ? " · 일봉이 오래되어 등락률은 기존 기준 유지"
      : "";
  if (item.livePrice?.source === "toss") {
    const timestamp = item.livePrice.timestamp ? ` · ${item.livePrice.timestamp}` : "";
    const changeText = item.livePrice.changeSource === "toss-candles" ? " · 전일 대비는 일봉 기준 추정" : "";
    const warningText = item.livePrice.baselineWarning
      ? ` · 기준가 차이 확인 필요(${item.livePrice.baselineDifferencePercent ?? ""})`
      : "";
    return `현재가 출처: 토스증권 Open API${timestamp}${changeText}${warningText}${candleText}`;
  }
  return `${item.livePrice?.message || "현재가 출처: 샘플 데이터"}${candleText}`;
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

async function toggleWatch(item) {
  await postJson("/api/watchlist", { symbol: item.symbol, watch: !item.isWatched });
  await loadDashboard();
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

document.querySelectorAll(".mode-button").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".mode-button").forEach((target) => target.classList.remove("active"));
    button.classList.add("active");
    state.view = "signals";
    updateViewButtons();
    updateShellView();
    state.mode = button.dataset.mode;
    state.selectedSymbol = null;
    state.selectedLookup = null;
    loadDashboard();
  });
});

document.querySelectorAll(".tab").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((target) => target.classList.remove("active"));
    button.classList.add("active");
    state.filter = button.dataset.filter;
    renderFeed();
  });
});

els.searchInput.addEventListener("input", (event) => {
  state.query = event.target.value;
  if (state.searchTimer) {
    window.clearTimeout(state.searchTimer);
  }
  state.searchTimer = window.setTimeout(() => {
    loadStockSearch();
  }, 280);
  renderFeed();
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

async function refreshSchedulerStatusOnly() {
  const status = await safeFetchJson("/api/scheduler/status", statusFallbacks().scheduler, 5000);
  const storage = await safeFetchJson("/api/storage/status", statusFallbacks().storage, 5000);
  const portfolio = await safeFetchJson("/api/portfolio/status", statusFallbacks().portfolio, 5000);
  state.schedulerStatus = status;
  state.storageStatus = storage;
  state.portfolioStatus = portfolio;
  maybeNotifySchedulerRun(status);
  renderSchedulerStatus();
  renderStorageStatus();
  renderPortfolioStatus();
  renderSnapshotHistory();
}

window.setInterval(() => {
  refreshSchedulerStatusOnly();
}, 60000);

loadDashboard().catch(() => {
  els.signalDetail.innerHTML = `
    <div class="empty-state">
      <h2>데이터를 불러오지 못했습니다</h2>
      <p>백엔드 서버가 실행 중인지 확인하세요.</p>
    </div>
  `;
});
