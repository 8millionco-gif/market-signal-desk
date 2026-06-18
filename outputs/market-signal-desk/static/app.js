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
  strategy: "core",
  query: "",
  dashboard: null,
  stockSearch: {
    query: "",
    loading: false,
    items: [],
    message: "",
    status: null,
    analyzingSymbol: null
  },
  selectedLookup: null,
  searchTimer: null,
  performance: null,
  performanceLoading: false,
  authEnabled: false,
  authRequired: false,
  adminToken: readStoredValue("marketSignalAdminToken", ""),
  schedulerStatus: null,
  discoveryBotStatus: null,
  storageStatus: null,
  portfolioStatus: null,
  viewingSnapshot: null,
  selectedSymbol: null,
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
  candidateCount: document.querySelector("#candidateCount"),
  candidateSource: document.querySelector("#candidateSource"),
  searchInput: document.querySelector("#searchInput"),
  quickSearch: document.querySelector("#quickSearch"),
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
  marketStatus: document.querySelector("#marketStatus"),
  authStatus: document.querySelector("#authStatus"),
  notificationStatus: document.querySelector("#notificationStatus"),
  candidatePoolStatus: document.querySelector("#candidatePoolStatus"),
  schedulerStatus: document.querySelector("#schedulerStatus"),
  discoveryBotStatus: document.querySelector("#discoveryBotStatus"),
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
      config: { enabled: false, jobs: [] },
      state: { started: false, running: false, lastError: "" },
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
  startActivity("오늘 후보 갱신 중", "국내/해외 후보와 시장 지표를 불러옵니다");
  state.viewingSnapshot = null;
  const fallbacks = statusFallbacks();
  updateActivity("연결 상태 확인 중", "토스·뉴스·공시·OpenAI 연결 상태를 점검합니다");
  const statusPromise = Promise.all([
    safeFetchJson("/api/auth/status", fallbacks.auth),
    safeFetchJson("/api/scheduler/status", fallbacks.scheduler),
    safeFetchJson("/api/discovery/status", fallbacks.discoveryBot),
    safeFetchJson("/api/storage/status", fallbacks.storage),
    safeFetchJson("/api/portfolio/status", fallbacks.portfolio),
    safeFetchJson("/api/network/outbound-ip", fallbacks.network),
    safeFetchJson("/api/integrations/toss/status", fallbacks.toss),
    safeFetchJson("/api/integrations/dart/status", fallbacks.dart),
    safeFetchJson("/api/integrations/news/status", fallbacks.news),
    safeFetchJson("/api/integrations/openai/status", fallbacks.openai)
  ]).then(([authStatus, schedulerStatus, discoveryBotStatus, storageStatus, portfolioStatus, networkStatus, tossStatus, dartStatus, newsStatus, openaiStatus]) => {
    state.authEnabled = Boolean(authStatus?.enabled);
    state.schedulerStatus = schedulerStatus;
    state.discoveryBotStatus = discoveryBotStatus;
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
    renderDiscoveryBotStatus();
    renderReadinessStatus();
    renderStorageStatus();
    renderPortfolioStatus();
    renderSnapshotHistory();
    renderNotificationStatus();
    renderMarketStatus();
    renderNetworkStatus();
    renderTossStatus();
    renderDartStatus();
    renderNewsStatus();
    renderOpenAIStatus();
  });

  try {
    updateActivity("후보 분석 중", "뉴스, 공시, 가격 반응으로 후보 점수를 계산합니다");
    const dashboard = await fetchJson(`/api/dashboard?mode=${state.mode}`, 30000);
    await statusPromise;
    state.dashboard = dashboard;
    if (!state.selectedSymbol) {
      const defaultCandidate = bestCandidate(state.dashboard.candidates ?? []);
      state.selectedSymbol = defaultCandidate?.symbol ?? state.dashboard.selected?.symbol ?? null;
    }
    updateActivity("화면 구성 중", "선정 후보와 가격 행동 지표를 정리합니다");
    render();
    finishActivity();
  } catch (error) {
    await statusPromise;
    state.dashboard = null;
    finishActivity();
    if (isAuthError(error)) {
      renderAuthGate();
      return;
    }
    renderLoadError(error);
  }
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
  els.metricCandidates.textContent = 0;
  els.metricHighScore.textContent = 0;
  els.metricReady.textContent = 0;
  els.metricWatched.textContent = 0;
  if (els.candidatePoolStatus) {
    els.candidatePoolStatus.innerHTML = `
      <div>
        <span>후보 풀</span>
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
  return sortCandidatesForStrategy(applyStrategyFilter(baseFilteredCandidates()), state.strategy);
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
  if (state.strategy === "all") return candidates;
  if (state.strategy === "core") return candidates.filter(isCoreCandidate);
  if (state.strategy === "review") return candidates.filter(isReviewCandidate);
  if (state.strategy === "pullback") return candidates.filter(isPullbackCandidate);
  if (state.strategy === "hidden") return candidates.filter(isHiddenOpportunity);
  if (state.strategy === "momentum") return candidates.filter(hasMomentumSignal);
  if (state.strategy === "holding") return candidates.filter(isHoldingCandidate);
  if (state.strategy === "exclude") return candidates.filter(isExcludeCandidate);
  if (state.strategy === "action") return candidates.filter(isActionCandidate);
  return candidates;
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
    confidenceScore: Number(validation.confidenceScore ?? item?.dataConfidence?.score ?? 0),
    reasons: Array.isArray(validation.reasons) ? validation.reasons : [],
    blockers: Array.isArray(validation.blockers) ? validation.blockers : []
  };
}

function candidatePoolStateForDisplay(item) {
  const pool = item?.candidatePool ?? {};
  const memory = item?.discovery?.poolMemory ?? {};
  const fallbackByCompression = {
    core: ["entry_candidate", "진입 후보"],
    review: ["validating", "검증중"],
    wait: ["watching", "관찰중"],
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
    scoreDelta: Number(pool.scoreDelta ?? 0),
    momentumLabel: pool.momentumLabel || "",
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
    pullback: candidates.filter(isPullbackCandidate).length,
    hidden: candidates.filter(isHiddenOpportunity).length,
    momentum: candidates.filter(hasMomentumSignal).length,
    holding: candidates.filter(isHoldingCandidate).length,
    exclude: candidates.filter(isExcludeCandidate).length,
    all: candidates.length
  };
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
  const compression = compressionForDisplay(item);
  const validation = signalValidationForDisplay(item);
  const currentRow = plan.rows.find(([label]) => label === "관찰 매수")?.[1] ?? "-";
  const holdingRow = plan.holding ? `${plan.holding.judgement ?? "보유"} · ${plan.holding.profitLossRate ?? "-"}` : "미보유";
  const rows = [
    ["선택", true, item.name ?? item.symbol ?? "-"],
    ["압축", compression.tier === "core", `${compression.label} · ${compression.score}/100`],
    ["검증", validation.entryReady, `${validation.label} · ${validation.score}/100`],
    ["액션", tradeActionOk(item), plan.action],
    ["관찰 매수", plan.tone === "buy", currentRow],
    ["현재가", plan.hasPrice, `${item.price ?? "-"} ${item.change ?? ""}`.trim()],
    ["보유", Boolean(plan.holding), holdingRow]
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
  const improving = Number(summary.candidatePoolImprovingCount ?? pool.improvingCount ?? 0);
  const weakening = Number(summary.candidatePoolWeakeningCount ?? pool.weakeningCount ?? 0);
  const topText = top.length
    ? top
        .slice(0, 2)
        .map((item) => `${item.name || item.symbol} ${item.stateLabel || ""} ${item.peakScore ?? item.score ?? "-"}점`)
        .join(" · ")
    : "상위 관찰 후보 없음";
  const rows = [
    ["활성 후보", active > 0, `${active}/${total}`],
    ["진입/검증", (counts.entry_candidate ?? 0) + (counts.validating ?? 0) > 0, `진입 ${counts.entry_candidate ?? 0} · 검증 ${counts.validating ?? 0}`],
    ["눌림/관찰", (counts.pullback_wait ?? 0) + (counts.watching ?? 0) > 0, `눌림 ${counts.pullback_wait ?? 0} · 관찰 ${counts.watching ?? 0}`],
    ["재점검", retained > 0 || selected > 0, `스캔 ${retained} · 선정 ${selected}`],
    ["흐름", improving >= weakening, `개선 ${improving} · 약화 ${weakening}`],
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

function render() {
  updateShellView();
  renderMarket();
  renderMetrics();
  renderTradeDecisionStatus();
  renderCandidatePoolStatus();
  renderAuthStatus();
  renderSchedulerStatus();
  renderDiscoveryBotStatus();
  renderReadinessStatus();
  renderStorageStatus();
  renderPortfolioStatus();
  renderSnapshotHistory();
  renderNotificationStatus();
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
  if (els.candidateSource) els.candidateSource.textContent = "관리자 토큰 필요";
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
  const discovery = state.dashboard?.integrations?.discovery ?? {};
  const actions = candidateActionSummary(state.dashboard?.candidates ?? []);
  const hiddenCount = (state.dashboard?.candidates ?? []).filter(isHiddenOpportunity).length;
  const hiddenOpportunityCount = Number(summary.hiddenOpportunityCount ?? 0);
  const averageOpportunityScore = Number(summary.averageOpportunityScore ?? 0);
  els.candidateCount.textContent = `${summary.candidateCount ?? 0}개`;
  if (els.candidateSource) {
    const sourceLabel =
      summary.candidateSource === "auto-news"
        ? "자동 뉴스 선정"
        : summary.candidateSource === "auto-universe"
          ? "자동 유니버스 선정"
          : "샘플 후보";
    const scanned = summary.scannedCount ?? discovery.scannedCount;
    const newsCount = summary.discoveryNewsCount ?? discovery.newsItemCount;
    const materialNews = summary.selectedMaterialNewsCount ?? discovery.selectedMaterialNewsItemCount ?? summary.materialNewsCount ?? discovery.materialNewsItemCount;
    const filtered = summary.filteredNewsCount ?? discovery.filteredNewsCount;
    const domestic = summary.domesticSelected ?? discovery.domesticSelected;
    const overseas = summary.overseasSelected ?? discovery.overseasSelected;
    const target = summary.targetCandidateCount ?? discovery.targetCandidateCount;
    const domesticShortfall = Number(summary.domesticShortfall ?? discovery.domesticShortfall ?? 0);
    const overseasShortfall = Number(summary.overseasShortfall ?? discovery.overseasShortfall ?? 0);
    const shortfallText =
      domesticShortfall || overseasShortfall
        ? ` · 부족 국내 ${domesticShortfall} · 해외 ${overseasShortfall}`
        : "";
    const splitText =
      domestic || overseas
        ? ` · 목표 ${target ?? "-"} · 국내 ${domestic ?? 0}/${summary.domesticLimit ?? discovery.domesticLimit ?? 10} · 해외 ${overseas ?? 0}/${summary.overseasLimit ?? discovery.overseasLimit ?? 10}${shortfallText}`
        : "";
    const actionText = actions.buy || actions.wait || actions.exclude ? ` · 진입 ${actions.buy} · 대기 ${actions.wait} · 제외 ${actions.exclude}` : "";
    const hiddenText = hiddenCount ? ` · 숨은 ${hiddenCount}` : "";
    const opportunityText = hiddenOpportunityCount ? ` · 기회 ${hiddenOpportunityCount} · 평균 ${averageOpportunityScore}/18` : "";
    const groups = summary.decisionGroups ?? {};
    const gates = summary.qualityGateCounts ?? {};
    const reactions = summary.priceReactionCounts ?? {};
    const decisions = summary.finalDecisionCounts ?? {};
    const compressionCounts = summary.candidateCompressionCounts ?? {};
    const coreCount = Number(summary.coreCandidateCount ?? compressionCounts.core ?? 0);
    const reviewCount = Number(summary.reviewCandidateCount ?? compressionCounts.review ?? 0);
    const waitCompressionCount = Number(summary.waitCandidateCompressionCount ?? compressionCounts.wait ?? 0);
    const portfolioCompressionCount = Number(summary.portfolioCandidateCompressionCount ?? compressionCounts.portfolio ?? 0);
    const excludeCompressionCount = Number(summary.excludeCandidateCompressionCount ?? compressionCounts.exclude ?? 0);
    const validationCounts = summary.signalValidationCounts ?? {};
    const confirmedSignals = Number(summary.confirmedSignalCount ?? validationCounts.confirmed ?? 0);
    const evidenceWaitSignals = Number(summary.evidenceWaitSignalCount ?? validationCounts.evidence_wait ?? 0);
    const reactionOnlySignals = Number(summary.reactionOnlySignalCount ?? validationCounts.reaction_only ?? 0);
    const blockedSignals = Number(summary.blockedSignalCount ?? validationCounts.blocked ?? 0);
    const confidence = summary.averageDataConfidence;
    const averageReaction = summary.averagePriceReaction;
    const officialCounts = summary.officialEventCounts ?? {};
    const officialCandidates = Number(summary.officialEventCandidateCount ?? 0);
    const officialRisk = Number(summary.officialRiskCandidateCount ?? officialCounts.highRisk ?? 0);
    const gateText =
      gates.actionable || gates.watch || gates.defer || gates.exclude
        ? ` · 실전 ${gates.actionable ?? 0} · 관찰 ${gates.watch ?? 0} · 대기 ${gates.defer ?? 0} · 제외 ${gates.exclude ?? 0}`
        : "";
    const confidenceText = confidence != null ? ` · 평균 신뢰 ${confidence}/100` : "";
    const reactionText =
      reactions.strong || reactions.confirmed || reactions.weak || reactions.missing
        ? ` · 가격반응 강 ${reactions.strong ?? 0} · 확인 ${reactions.confirmed ?? 0} · 약 ${reactions.weak ?? 0} · 부족 ${reactions.missing ?? 0}`
        : "";
    const averageReactionText = averageReaction != null ? ` · 평균 반응 ${averageReaction}/100` : "";
    const portfolioLinked = Number(summary.portfolioLinkedCandidateCount ?? 0);
    const portfolioText = portfolioLinked
      ? ` · 보유연결 ${portfolioLinked} · 추가 ${decisions.add ?? 0} · 보유 ${decisions.hold ?? 0} · 매도 ${decisions.trim ?? 0} · 손절 ${decisions.stop ?? 0}`
      : "";
    const officialText = officialCandidates
      ? ` · 공식 ${officialCandidates} · 긍정 ${officialCounts.positive ?? 0} · 리스크 ${officialRisk}`
      : "";
    const compressionText =
      coreCount || reviewCount || waitCompressionCount || portfolioCompressionCount || excludeCompressionCount
        ? ` · 압축 핵심 ${coreCount}/${summary.coreCandidateLimit ?? 3} · 검토 ${reviewCount} · 대기 ${waitCompressionCount} · 보유 ${portfolioCompressionCount} · 제외 ${excludeCompressionCount}`
        : "";
    const validationText =
      confirmedSignals || evidenceWaitSignals || reactionOnlySignals || blockedSignals
        ? ` · 검증 확인 ${confirmedSignals} · 반응대기 ${evidenceWaitSignals} · 가격선행 ${reactionOnlySignals} · 차단 ${blockedSignals}`
        : "";
    const poolCounts = summary.candidatePoolStatusCounts ?? {};
    const poolTotal = Number(summary.candidatePoolCount ?? 0);
    const poolActive = Number(summary.candidatePoolActiveCount ?? 0);
    const poolText =
      poolTotal || poolActive
        ? ` · 후보풀 ${poolActive}/${poolTotal} · 풀재점검 ${summary.candidatePoolRetainedScanCount ?? 0} · 풀선정 ${summary.candidatePoolSelectedCount ?? 0} · 진입 ${poolCounts.entry_candidate ?? 0} · 검증 ${poolCounts.validating ?? 0} · 관찰 ${poolCounts.watching ?? 0} · 눌림 ${poolCounts.pullback_wait ?? 0} · 개선 ${summary.candidatePoolImprovingCount ?? 0} · 약화 ${summary.candidatePoolWeakeningCount ?? 0}`
        : "";
    const groupText =
      groups.action || groups.hidden || groups.momentum
        ? ` · 그룹 진입 ${groups.action ?? 0} · 숨은 ${groups.hidden ?? 0} · 모멘텀 ${groups.momentum ?? 0}`
        : "";
    const qualityPrimary = summary.qualitySelectedPrimary ?? discovery.qualitySelectedPrimary;
    const qualityReserve = summary.qualitySelectedReserve ?? discovery.qualitySelectedReserve;
    const qualityFallback = summary.qualitySelectedFallback ?? discovery.qualitySelectedFallback;
    const qualityRejected = summary.qualityRejectedCount ?? discovery.qualityRejectedCount;
    const evidenceStrong = Number(summary.evidenceStrongCount ?? discovery.evidenceStrongCount ?? 0);
    const evidenceQualified = Number(summary.evidenceQualifiedCount ?? discovery.evidenceQualifiedCount ?? 0);
    const evidenceThin = Number(summary.evidenceThinCount ?? discovery.evidenceThinCount ?? 0);
    const evidenceRisk = Number(summary.evidenceRiskCount ?? discovery.evidenceRiskCount ?? 0);
    const evidenceWeak = Number(summary.evidenceWeakCount ?? discovery.evidenceWeakCount ?? 0);
    const evidenceAverage = summary.averageEvidenceScore ?? discovery.averageEvidenceScore;
    const qualityText =
      qualityPrimary != null || qualityReserve != null || qualityFallback != null || qualityRejected != null
        ? ` · 품질 1차 ${qualityPrimary ?? 0} · 보조 ${qualityReserve ?? 0}${qualityFallback ? ` · 예비 ${qualityFallback}` : ""} · 제외 ${qualityRejected ?? 0}`
        : "";
    const evidenceText =
      evidenceStrong || evidenceQualified || evidenceThin || evidenceRisk || evidenceWeak
        ? ` · 발굴 근거 강 ${evidenceStrong} · 검증 ${evidenceQualified} · 약 ${evidenceThin} · 리스크 ${evidenceRisk} · 부족 ${evidenceWeak}${evidenceAverage != null ? ` · 평균 ${evidenceAverage}/100` : ""}`
        : "";
    const detail = scanned
      ? ` · ${scanned}종목 점검${splitText}${poolText}${hiddenText}${opportunityText}${compressionText}${validationText}${gateText}${confidenceText}${reactionText}${averageReactionText}${officialText}${portfolioText}${groupText}${qualityText}${evidenceText}${actionText}${newsCount ? ` · 뉴스 ${newsCount}건` : ""}${materialNews ? ` · 재료뉴스 ${materialNews}건` : ""}${filtered ? ` · 뉴스 제외 ${filtered}건` : ""}`
      : "";
    els.candidateSource.textContent = `${sourceLabel}${detail}`;
  }
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
  const modeText = status.mode === "filesystem" ? "파일 저장" : status.mode || "-";
  const database = status.database ?? {};
  const migration = database.migration ?? {};
  const counts = database.counts ?? {};
  const persistenceText = status.persistent ? "영구 설정" : "임시 보존";
  const latestText = status.latestRunCreatedAt
    ? `${status.recentRunCount ?? 0}건 · ${String(status.latestRunCreatedAt).replace("T", " ").slice(5, 16)}`
    : `${status.recentRunCount ?? 0}건`;
  const nextText = status.persistent ? "자동 실행 가능" : "DB/디스크 검토";
  const dbText = database.urlConfigured
    ? database.ready
      ? "Postgres 준비"
      : shortText(database.error || "DB 연결 확인", 28)
    : "미연결";
  const migrationText = migration.enabled
    ? migration.error
      ? shortText(migration.error, 28)
      : migration.done
      ? `완료 · 스냅샷 ${migration.snapshotsInserted ?? 0}/${migration.snapshotsScanned ?? 0}`
      : "대기"
    : "꺼짐";
  const recordText = counts.snapshotCount != null
    ? `스냅샷 ${counts.snapshotCount} · 풀 ${counts.candidatePoolActiveCount ?? 0}/${counts.candidatePoolCount ?? 0}`
    : "-";
  const rows = [
    ["저장 방식", Boolean(status.mode), modeText],
    ["쓰기 가능", Boolean(status.writable), status.writable ? "가능" : shortText(status.error || "확인 필요", 28)],
    ["DB 상태", Boolean(database.ready), dbText],
    ["DB 이관", Boolean(migration.done), migrationText],
    ["DB 기록", counts.snapshotCount != null, recordText],
    ["보존성", Boolean(status.persistent), persistenceText],
    ["최근 기록", Number(status.recentRunCount ?? 0) > 0, latestText],
    ["다음", status.persistent && status.writable, nextText]
  ];
  const canMigrate = Boolean(database.urlConfigured && database.ready);
  const actionMarkup = `
    <div class="storage-actions">
      <button type="button" data-storage-action="refresh">새로고침</button>
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
      if (action === "migrate") {
        await runStorageMigration();
      }
    });
  });
}

async function refreshStorageStatus() {
  const buttons = els.storageStatus?.querySelectorAll("[data-storage-action]") ?? [];
  buttons.forEach((button) => {
    button.disabled = true;
  });
  try {
    state.storageStatus = await safeFetchJson("/api/storage/status", statusFallbacks().storage, 10000);
  } finally {
    renderStorageStatus();
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
  return {
    action: decision.action || "확인 대기",
    tone: decision.tone || "wait",
    summary: decision.summary || "가격, 신뢰도, 수급 조건을 추가 확인합니다.",
    holding,
    hasPrice: Boolean(item?.price),
    signalCards: signalCards.length
      ? signalCards
      : [
          ["현재 판단", decision.action || "확인 대기"],
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

  let action = "가격 확인 대기";
  let tone = "wait";
  let summary = "현재가가 확인되면 매수·대기·매도 구간을 계산합니다.";
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
      summary = "후보 점수는 있으나 바로 진입보다 가격 확인이 필요합니다.";
    }
  }

  const template = item?.price ?? "";
  const immediateText =
    !hasPrice
      ? "현재가 확인 후 판단"
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
                : `가격대 확인`;

  return {
    action,
    tone,
    summary,
    holding,
    hasPrice,
    signalCards: [
      ["현재 판단", immediateText],
      ["매수 구간", band ? band.entryRangeText : "현재가 확인 후 계산"],
      ["위험 기준", band ? `${formatPriceFromTemplate(band.stopLine, template)} 이탈` : "-"]
    ],
    rows: [
      ["관찰 매수", band ? band.entryRangeText : "현재가 확인 후 계산"],
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

async function runDiscoveryBot() {
  const buttons = els.discoveryBotStatus?.querySelectorAll("[data-discovery-action]") ?? [];
  buttons.forEach((button) => {
    button.disabled = true;
  });
  startActivity("발굴 봇 실행 중", "최신 뉴스, 가격, 공시 신호로 후보를 다시 점검합니다");
  try {
    const payload = await postJson("/api/discovery/run", { mode: state.mode }, 70000);
    state.discoveryBotStatus = payload.status ?? state.discoveryBotStatus;
    renderDiscoveryBotStatus();
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

function applySearchQuery(query) {
  state.query = String(query ?? "").trim();
  if (els.searchInput) {
    els.searchInput.value = state.query;
  }
  if (state.searchTimer) {
    window.clearTimeout(state.searchTimer);
    state.searchTimer = null;
  }
  renderFeed();
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
    return rows.find(([label]) => label === "눌림 대기")?.[1] ?? "눌림 확인 대기";
  }
  if (String(plan?.action ?? "").includes("반등")) {
    return rows.find(([label]) => label === "반등 확인")?.[1] ?? "반등 확인 대기";
  }
  return rows.find(([label]) => label === "관찰 매수")?.[1] ?? plan?.summary ?? "가격대 확인";
}

function feedActionLabel(item, plan) {
  const compression = compressionForDisplay(item);
  if (compression.tier === "core") return "핵심 후보";
  const finalDecision = item?.finalDecision ?? {};
  if (finalDecision.portfolioAware && finalDecision.action) return finalDecision.action;
  const gate = item?.qualityGate;
  if (gate?.key === "actionable") return "매수 후보";
  if (gate?.key === "watch") return "관찰 후보";
  if (gate?.key === "defer") return "확인 대기";
  if (gate?.key === "exclude") return "오늘 제외";
  const group = decisionGroupForDisplay(item);
  if (isActionCandidate(item)) return "매수 후보";
  if (plan.tone === "sell") return "매도 검토";
  if (plan.tone === "risk") return "오늘 제외";
  if (group.key === "holding") return "보유 대응";
  if (String(plan.action).includes("눌림")) return "눌림 대기";
  if (String(plan.action).includes("반등")) return "반등 확인";
  if (group.key === "hidden") return "숨은 후보";
  if (group.key === "momentum") return "모멘텀 확인";
  return "관찰 대기";
}

function renderFeed() {
  renderStrategyCounts();
  const candidates = filteredCandidates();
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
    return;
  }

  els.candidateFeed.innerHTML = candidates
    .map((item) => {
      const active = item.symbol === state.selectedSymbol ? "active" : "";
      const plan = tradePlan(item);
      const group = decisionGroupForDisplay(item);
      const compression = compressionForDisplay(item);
      const poolState = candidatePoolStateForDisplay(item);
      const validation = signalValidationForDisplay(item);
      const opportunityScore = Number(item.hiddenOpportunity?.score ?? 0);
      const qualityLabel = discoveryQualityLabel(item);
      const evidence = discoveryEvidenceForDisplay(item);
      const actionLabel = feedActionLabel(item, plan);
      const priceGuide = primaryPriceGuide(plan);
      const gate = item.qualityGate ?? {};
      const confidence = item.dataConfidence ?? {};
      const reaction = item.priceReaction ?? {};
      const official = item.officialSignal ?? item.finalDecision?.officialSignal ?? {};
      const materialNews = Number(item.trend?.materialNewsCount ?? item.discovery?.materialNewsItems ?? 0);
      const officialBadge = official.count
        ? official.riskLevel === "high"
          ? "공시위험"
          : official.positiveCount
            ? `공식+${official.positiveCount}`
            : `공식 ${official.count}`
        : "";
      return `
        <button class="feed-item ${active}" data-symbol="${escapeHtml(item.symbol)}">
          <span class="logo-mark">${escapeHtml(initials(item.name))}</span>
          <span>
            <span class="feed-title">
              <strong>${escapeHtml(item.name)}</strong>
              <span>${escapeHtml(item.symbol)}</span>
              <span class="feed-badge compression-badge compression-${escapeHtml(compression.tier)}">${escapeHtml(compression.label)}${compression.tier === "core" ? ` #${escapeHtml(compression.rank)}` : ""}</span>
              <span class="feed-badge pool-state-badge pool-${escapeHtml(poolState.key)}">${escapeHtml(poolState.label)}</span>
              ${poolState.retained ? `<span class="feed-badge pool-retained-badge">풀재점검 ${escapeHtml(poolState.retainScore || "")}</span>` : ""}
              ${poolState.momentumLabel ? `<span class="feed-badge pool-momentum pool-momentum-${escapeHtml(poolState.momentumLabel === "개선" ? "up" : poolState.momentumLabel === "약화" ? "down" : "flat")}">${escapeHtml(poolState.momentumLabel)}${poolState.scoreDelta ? ` ${poolState.scoreDelta > 0 ? "+" : ""}${escapeHtml(poolState.scoreDelta)}` : ""}</span>` : ""}
              <span class="feed-badge ${escapeHtml(decisionGroupClass(group.key))}">${escapeHtml(group.label)}</span>
              ${qualityLabel ? `<span class="feed-badge quality-badge">${escapeHtml(qualityLabel)}</span>` : ""}
              ${evidence.label ? `<span class="feed-badge evidence-badge evidence-${escapeHtml(evidence.grade || "weak")}">${escapeHtml(evidence.label)} ${escapeHtml(evidence.score)}</span>` : ""}
              ${validation.label ? `<span class="feed-badge validation-badge validation-${escapeHtml(validation.key)}">${escapeHtml(validation.label)} ${escapeHtml(validation.score)}</span>` : ""}
              ${gate.label ? `<span class="feed-badge gate-badge gate-${escapeHtml(gate.key || "wait")}">${escapeHtml(gate.label)}</span>` : ""}
              ${officialBadge ? `<span class="feed-badge official-badge official-${escapeHtml(official.riskLevel || "low")}">${escapeHtml(officialBadge)}</span>` : ""}
              ${materialNews ? `<span class="feed-badge news-badge">재료뉴스 ${escapeHtml(materialNews)}</span>` : ""}
              ${confidence.score != null ? `<span class="feed-badge confidence-badge">신뢰 ${escapeHtml(confidence.score)}</span>` : ""}
              ${reaction.score != null ? `<span class="feed-badge reaction-badge">반응 ${escapeHtml(reaction.score)}</span>` : ""}
              ${isHiddenOpportunity(item) ? `<span class="feed-badge">숨은</span>` : ""}
              ${opportunityScore >= 8 ? `<span class="feed-badge">기회 ${opportunityScore}</span>` : ""}
            </span>
            <span class="feed-subtitle">${escapeHtml(item.headline)}</span>
            <span class="feed-signal-line ${escapeHtml(plan.tone)}">
              <strong>${escapeHtml(actionLabel)}</strong>
              <em>${escapeHtml(shortText(priceGuide, 34))}</em>
            </span>
          </span>
          <span class="feed-meta">
            <span class="feed-action ${escapeHtml(plan.tone)}">${escapeHtml(plan.action)}</span>
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

function strategyLabel(value) {
  if (value === "core") return "핵심 후보";
  if (value === "review") return "검토 후보";
  if (value === "action") return "진입 가능";
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

function shouldSearchStocks(query) {
  const text = String(query ?? "").trim();
  if (!text) return false;
  if (/[가-힣]/.test(text)) return text.length >= 1;
  return text.length >= 2;
}

async function openSearchResult(symbol) {
  const item = (state.stockSearch.items ?? []).find((entry) => entry.symbol === symbol);
  if (!item) return;
  const candidate = (state.dashboard?.candidates ?? []).find((entry) => entry.symbol === symbol);
  state.view = "signals";
  updateShellView();
  updateViewButtons();
  if (candidate) {
    state.selectedLookup = null;
    state.selectedSymbol = candidate.symbol;
    state.stockSearch = { ...state.stockSearch, analyzingSymbol: null };
    renderFeed();
    renderTradeDecisionStatus();
    renderDetail();
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
  els.stockSearchResults.hidden = false;
  els.stockSearchResults.innerHTML = `
    <div class="stock-search-head">
      <strong>종목 자동완성</strong>
      <span>${loading ? "조회 중" : items.length ? `${items.length}건` : "결과 없음"}</span>
    </div>
    ${
      items.length
        ? `<div class="stock-search-list">
            ${items
              .slice(0, 8)
              .map(
                (item) => `
                  <button class="stock-result" type="button" data-search-symbol="${escapeHtml(item.symbol)}">
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
        : `<p>${escapeHtml(message || "삼성, 하이닉스, 엔비, AAPL처럼 입력하세요.")}</p>`
    }
    ${message && items.length ? `<p>${escapeHtml(message)}</p>` : ""}
  `;

  els.stockSearchResults.querySelectorAll("[data-search-symbol]").forEach((button) => {
    button.addEventListener("click", () => openSearchResult(button.dataset.searchSymbol));
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
      analyzingSymbol: null
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
    analyzingSymbol: state.stockSearch.analyzingSymbol
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
      ${tradePlanSection(item)}
      ${decisionGroupSection(item)}
      ${candidatePoolSection(item)}
      ${signalValidationSection(item)}
      ${discoveryEvidenceSection(item)}
      ${hiddenOpportunitySection(item)}
      ${officialSignalSection(item)}

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
            ${statCard("공식 이벤트", item.officialSignal?.count ? `${item.officialSignal.count}건` : "-")}
            ${statCard("재료 뉴스", item.trend?.materialNewsCount != null ? `${item.trend.materialNewsCount}건` : "-")}
            ${statCard("뉴스 관련성", item.trend?.newsRelevance != null ? `${item.trend.newsRelevance}/100` : "-")}
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
                  <span>${escapeHtml(source.publisher)} · ${escapeHtml(source.time)}${source.url ? " · 뉴스" : ""}${source.relevanceScore != null ? ` · 관련성 ${escapeHtml(source.relevanceScore)}` : ""}${source.impactTypes?.length ? ` · ${escapeHtml(source.impactTypes.slice(0, 2).join(","))}` : ""}</span>
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
  const byGate = Array.isArray(payload.byGate) ? payload.byGate : [];
  const byFinalAction = Array.isArray(payload.byFinalAction) ? payload.byFinalAction : [];
  const byReaction = Array.isArray(payload.byReaction) ? payload.byReaction : [];
  const byHorizon = Array.isArray(payload.byHorizon) ? payload.byHorizon : [];
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
        ${performanceMetric("실전 관측", summary.actionableMeasuredCount ?? 0)}
        ${performanceMetric("실전 승률", summary.actionableHitRate ?? "-")}
        ${performanceMetric("매수 판단", summary.buyDecisionMeasuredCount ?? 0)}
        ${performanceMetric("매수 승률", summary.buyDecisionHitRate ?? "-")}
        ${performanceMetric("추가 판단", summary.addDecisionMeasuredCount ?? 0)}
        ${performanceMetric("추가 승률", summary.addDecisionHitRate ?? "-")}
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

function tradePlanSection(item) {
  const plan = tradePlan(item);
  return `
    <section class="detail-section trade-plan-section">
      <div class="trade-plan-head">
        <div>
          <p class="eyebrow">가격 행동</p>
          <h2>${escapeHtml(plan.action)}</h2>
          <p>${escapeHtml(plan.summary)}</p>
        </div>
        <span class="action-pill ${escapeHtml(plan.tone)}">${escapeHtml(plan.action)}</span>
      </div>
      <div class="trade-signal-cards">
        ${plan.signalCards
          .map(
            ([label, value]) => `
              <div>
                <span>${escapeHtml(label)}</span>
                <strong>${escapeHtml(value)}</strong>
              </div>
            `
          )
          .join("")}
      </div>
      <div class="trade-plan-grid">
        ${plan.rows
          .map(
            ([label, value]) => `
              <div>
                <span>${escapeHtml(label)}</span>
                <strong>${escapeHtml(value)}</strong>
              </div>
            `
          )
          .join("")}
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
  const reaction = item.priceReaction ?? {};
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
        ${reaction.score != null ? statCard("가격 반응", `${reaction.label ?? "-"} · ${reaction.score}/100`) : ""}
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
        ${(reaction.reasons ?? []).slice(0, 2).map((text) => `<li>${escapeHtml(`가격 반응: ${text}`)}</li>`).join("")}
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
    ["최고 점수", pool.peakScore ? `${pool.peakScore}/100` : "-"],
    ["최고 준비도", pool.peakReadiness ? `${pool.peakReadiness}/100` : "-"],
    ["상태 변화", `${pool.promotionCount}회 승격 · ${pool.demotionCount}회 강등`],
    ["최근 변화", pool.momentumLabel ? `${pool.momentumLabel} ${deltaText}` : "-"],
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
        ${pool.retained ? `<li>${escapeHtml(pool.retainReason || `${pool.retainStateLabel || "후보 풀"} 상태로 재점검 대상입니다.`)}</li>` : ""}
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
  const blockers = uniqueTexts(validation.blockers ?? [], 5);
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

document.querySelectorAll(".strategy-button").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".strategy-button").forEach((target) => target.classList.remove("active"));
    button.classList.add("active");
    state.strategy = button.dataset.strategy || "action";
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

els.searchInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    const currentQuery = state.query.trim();
    const first = state.stockSearch.query === currentQuery ? state.stockSearch.items?.[0] : null;
    if (first?.symbol) {
      event.preventDefault();
      openSearchResult(first.symbol);
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
