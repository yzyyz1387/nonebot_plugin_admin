(function () {
  const bootstrap = window.ADMIN_DASHBOARD_BOOTSTRAP || {};
  const tokenStorageKey = "nb2-admin-dashboard-token:" + (bootstrap.apiBasePath || "");
  const tokenTimestampKey = "nb2-admin-dashboard-token-ts:" + (bootstrap.apiBasePath || "");
  var TOKEN_TTL_MS = 24 * 60 * 60 * 1000;

  const state = {
    token: "",
    meta: null,
    groups: [],
    currentPage: "dashboard",
    overview: null,
    operationsOverview: null,
    logsOverview: null,
    latestLogs: null,
    accountOverview: null,
    recentContacts: null,
    recentLogs: null,
    currentGroupId: "",
    currentWorkspace: null,
    currentMembers: null,
    selectedMemberId: "",
    logs: {
      page: 1,
      page_size: 50,
      level: "",
      keyword: ""
    }
  };

  const els = {};
  let tokenDialog = null;
  let mobileDrawer = null;
  let groupSearchTimer = null;
  let memberSearchTimer = null;
  let logsSearchTimer = null;

  document.addEventListener("DOMContentLoaded", init);

  function init() {
    cacheElements();
    restoreToken();
    initMduiInstances();
    bindEvents();
    paintBootstrap();
    loadBootstrap();
  }

  function cacheElements() {
    [
      "page-title",
      "drawer-title",
      "page-subtitle",
      "connection-chip",
      "dashboard-generated-at",
      "group-panel-meta",
      "group-status-box",
      "desktop-group-list",
      "mobile-group-list",
      "group-search-input",
      "mobile-group-search-input",
      "refresh-all-btn",
      "refresh-groups-btn",
      "refresh-logs-btn",
      "refresh-group-workspace-btn",
      "open-token-btn",
      "sidebar-settings-btn",
      "token-input",
      "save-token-btn",
      "clear-token-btn",
      "token-hint-box",
      "dashboard-metrics",
      "trend-chart",
      "trend-status-box",
      "logs-donut",
      "logs-overview-status",
      "top-group-list",
      "recent-log-list",
      "account-overview-box",
      "recent-contact-list",
      "log-level-filter",
      "logs-search-input",
      "logs-status-box",
      "logs-console-list",
      "logs-pagination-info",
      "logs-prev-btn",
      "logs-next-btn",
      "group-title",
      "group-subtitle",
      "group-metrics",
      "chat-status-box",
      "chat-message-list",
      "load-older-messages-btn",
      "reload-latest-messages-btn",
      "group-message-input",
      "send-group-message-btn",
      "announcement-list",
      "file-system-summary",
      "group-file-table-body",
      "essence-list",
      "honor-list",
      "bot-profile-box",
      "feature-switch-list",
      "whole-ban-toggle-input",
      "mark-read-btn",
      "group-actions-status",
      "selected-member-box",
      "mute-duration-input",
      "special-title-input",
      "mute-member-btn",
      "set-title-btn",
      "kick-member-btn",
      "group-member-search-input",
      "member-status-box",
      "group-member-list"
    ].forEach(function (id) {
      els[id] = document.getElementById(id);
    });
  }

  function initMduiInstances() {
    if (window.mdui && document.getElementById("token-dialog")) {
      tokenDialog = new mdui.Dialog("#token-dialog");
      mobileDrawer = new mdui.Drawer("#mobile-drawer", { swipe: true });
    }
  }

  function bindEvents() {
    document.querySelectorAll("[data-page]").forEach(function (node) {
      node.addEventListener("click", function () {
        const page = node.getAttribute("data-page");
        setPage(page);
        if (mobileDrawer) {
          mobileDrawer.close();
        }
      });
    });

    [els["open-token-btn"], els["sidebar-settings-btn"]].forEach(function (node) {
      if (!node) return;
      node.addEventListener("click", function () {
        openTokenDialog();
      });
    });

    els["save-token-btn"].addEventListener("click", async function () {
      state.token = (els["token-input"].value || "").trim();
      persistToken();
      if (tokenDialog) {
        tokenDialog.close();
      }
      await refreshAll(true);
    });

    els["clear-token-btn"].addEventListener("click", async function () {
      state.token = "";
      els["token-input"].value = "";
      persistToken();
      showSnackbar("已清除本地 Token");
      if (tokenDialog) {
        tokenDialog.close();
      }
      await refreshAll(true);
    });

    els["refresh-all-btn"].addEventListener("click", function () {
      refreshAll(false);
    });

    els["refresh-groups-btn"].addEventListener("click", function () {
      loadGroups();
    });

    els["refresh-logs-btn"].addEventListener("click", function () {
      loadLogs(false);
    });

    els["refresh-group-workspace-btn"].addEventListener("click", function () {
      if (!state.currentGroupId) {
        showSnackbar("请先选择一个群组");
        return;
      }
      loadGroupWorkspace(state.currentGroupId, true);
    });

    const onGroupSearch = function (value) {
      clearTimeout(groupSearchTimer);
      groupSearchTimer = window.setTimeout(function () {
        els["group-search-input"].value = value;
        els["mobile-group-search-input"].value = value;
        renderGroupLists(value);
      }, 120);
    };

    els["group-search-input"].addEventListener("input", function (event) {
      onGroupSearch(event.target.value || "");
    });
    els["mobile-group-search-input"].addEventListener("input", function (event) {
      onGroupSearch(event.target.value || "");
    });

    const onMemberSearch = function (value) {
      clearTimeout(memberSearchTimer);
      memberSearchTimer = window.setTimeout(function () {
        if (!state.currentGroupId) return;
        loadGroupMembers(value || "");
      }, 200);
    };
    els["group-member-search-input"].addEventListener("input", function (event) {
      onMemberSearch(event.target.value || "");
    });

    const onLogsSearch = function (value) {
      clearTimeout(logsSearchTimer);
      logsSearchTimer = window.setTimeout(function () {
        state.logs.keyword = (value || "").trim();
        state.logs.page = 1;
        loadLogs(false);
      }, 220);
    };
    els["logs-search-input"].addEventListener("input", function (event) {
      onLogsSearch(event.target.value || "");
    });

    els["log-level-filter"].addEventListener("click", function (event) {
      const trigger = event.target.closest("[data-log-level]");
      if (!trigger) return;
      state.logs.level = trigger.getAttribute("data-log-level") || "";
      state.logs.page = 1;
      renderLogLevelFilters();
      loadLogs(false);
    });

    els["logs-prev-btn"].addEventListener("click", function () {
      if (state.logs.page <= 1) return;
      state.logs.page -= 1;
      loadLogs(false);
    });
    els["logs-next-btn"].addEventListener("click", function () {
      const pagination = ((state.latestLogs || {}).pagination) || {};
      if (!pagination.has_next) return;
      state.logs.page += 1;
      loadLogs(false);
    });

    els["desktop-group-list"].addEventListener("click", handleGroupListClick);
    els["mobile-group-list"].addEventListener("click", handleGroupListClick);
    els["top-group-list"].addEventListener("click", handleTopGroupClick);

    els["group-member-list"].addEventListener("click", function (event) {
      const trigger = event.target.closest("[data-user-id]");
      if (!trigger) return;
      state.selectedMemberId = String(trigger.getAttribute("data-user-id"));
      renderSelectedMember();
      renderMemberList(state.currentMembers);
    });

    els["feature-switch-list"].addEventListener("change", function (event) {
      const input = event.target.closest("input[data-switch-key]");
      if (!input || !state.currentGroupId) return;
      const switchKey = input.getAttribute("data-switch-key");
      const enabled = !!input.checked;
      updateFeatureSwitch(switchKey, enabled, input);
    });

    els["whole-ban-toggle-input"].addEventListener("change", function (event) {
      if (!state.currentGroupId) {
        event.target.checked = false;
        return;
      }
      updateWholeBan(!!event.target.checked, event.target);
    });

    els["mark-read-btn"].addEventListener("click", function () {
      if (!state.currentGroupId) {
        showSnackbar("请先选择一个群组");
        return;
      }
      markCurrentGroupRead();
    });

    els["load-older-messages-btn"].addEventListener("click", function () {
      loadOlderMessages();
    });

    els["reload-latest-messages-btn"].addEventListener("click", function () {
      if (!state.currentGroupId) return;
      loadLatestMessages(state.currentGroupId);
    });

    els["send-group-message-btn"].addEventListener("click", function () {
      sendCurrentGroupMessage();
    });

    els["mute-member-btn"].addEventListener("click", function () {
      performMemberAction("mute");
    });
    els["set-title-btn"].addEventListener("click", function () {
      performMemberAction("title");
    });
    els["kick-member-btn"].addEventListener("click", function () {
      performMemberAction("kick");
    });
  }

  async function loadBootstrap() {
    try {
      state.meta = await apiFetch("/meta", { auth: false });
      updateConnectionChip();
      if (state.meta.auth_required && !state.token) {
        showAuthRequiredState();
        openTokenDialog();
        return;
      }
      await refreshAll(false);
    } catch (error) {
      showFatalState("初始化失败：" + error.message);
    }
  }

  function paintBootstrap() {
    document.title = bootstrap.title || "Admin Dashboard";
    els["page-title"].textContent = bootstrap.title || "Admin Dashboard";
    els["drawer-title"].textContent = bootstrap.title || "Admin Dashboard";
    els["token-input"].value = state.token;
  }

  function restoreToken() {
    try {
      var ts = window.sessionStorage.getItem(tokenTimestampKey);
      if (ts && Date.now() - parseInt(ts, 10) > TOKEN_TTL_MS) {
        window.sessionStorage.removeItem(tokenStorageKey);
        window.sessionStorage.removeItem(tokenTimestampKey);
        state.token = "";
        return;
      }
      state.token = window.sessionStorage.getItem(tokenStorageKey) || "";
    } catch (error) {
      state.token = "";
    }
  }

  function persistToken() {
    try {
      if (state.token) {
        window.sessionStorage.setItem(tokenStorageKey, state.token);
        window.sessionStorage.setItem(tokenTimestampKey, String(Date.now()));
      } else {
        window.sessionStorage.removeItem(tokenStorageKey);
        window.sessionStorage.removeItem(tokenTimestampKey);
      }
    } catch (error) {
      showSnackbar("本地保存 Token 失败：" + error.message);
    }
  }

  function openTokenDialog() {
    els["token-input"].value = state.token || "";
    if (tokenDialog) {
      tokenDialog.open();
    }
  }

  function showFatalState(message) {
    els["connection-chip"].textContent = "初始化失败";
    els["trend-status-box"].textContent = message;
    els["logs-status-box"].textContent = message;
    els["group-status-box"].textContent = message;
    showSnackbar(message);
  }

  function showAuthRequiredState() {
    updateConnectionChip();
    els["trend-status-box"].textContent = "API 已开启鉴权，请先输入 X-Admin-Token。";
    els["logs-status-box"].textContent = "API 已开启鉴权，请先输入 X-Admin-Token。";
    els["group-status-box"].textContent = "API 已开启鉴权，请先输入 X-Admin-Token。";
    els["token-hint-box"].textContent = "当前 API 已启用鉴权，请输入正确的 X-Admin-Token。";
  }

  async function refreshAll(resetPage) {
    if (state.meta && state.meta.auth_required && !state.token) {
      showAuthRequiredState();
      return;
    }
    if (resetPage) {
      state.logs.page = 1;
    }
    updateConnectionChip("loading");
    try {
      await Promise.all([
        loadDashboardSurface(),
        loadGroups(),
        loadLogs(false)
      ]);
      if (!state.currentGroupId && state.groups.length) {
        state.currentGroupId = String(state.groups[0].group_id);
      }
      if (state.currentGroupId) {
        await loadGroupWorkspace(state.currentGroupId, false);
      } else {
        renderEmptyWorkspace();
      }
      updateConnectionChip("ready");
    } catch (error) {
      updateConnectionChip("error");
      showSnackbar("刷新失败：" + error.message);
    }
  }

  async function loadDashboardSurface() {
    const [overview, operations, logsOverview, latestLogs, accountOverview, recentContacts] = await Promise.all([
      apiFetch("/overview"),
      apiFetch("/operations/overview"),
      apiFetch("/logs/overview"),
      apiFetch("/logs?page=1&page_size=6"),
      apiFetch("/account/overview"),
      apiFetch("/contacts/recent?count=8")
    ]);
    state.overview = overview;
    state.operationsOverview = operations;
    state.logsOverview = logsOverview;
    state.recentLogs = latestLogs;
    state.accountOverview = accountOverview;
    state.recentContacts = recentContacts;
    renderDashboard();
  }

  async function loadGroups() {
    els["group-status-box"].textContent = "正在加载群列表…";
    const payload = await apiFetch("/groups");
    const items = Array.isArray(payload.items) ? payload.items.slice() : [];
    items.sort(function (a, b) {
      return (Number(b.today_message_count) || 0) - (Number(a.today_message_count) || 0);
    });
    state.groups = items;
    els["group-panel-meta"].textContent = "已接入 " + items.length + " 个群";
    renderGroupLists(els["group-search-input"].value || "");
    els["group-status-box"].textContent = items.length ? "群列表已就绪。" : "暂未发现任何群数据。";
  }

  async function loadLogs() {
    els["logs-status-box"].textContent = "正在加载日志…";
    const query = [
      "page=" + encodeURIComponent(String(state.logs.page)),
      "page_size=" + encodeURIComponent(String(state.logs.page_size)),
      "level=" + encodeURIComponent(state.logs.level || ""),
      "keyword=" + encodeURIComponent(state.logs.keyword || "")
    ].join("&");
    const payload = await apiFetch("/logs?" + query);
    state.latestLogs = payload;
    renderLogsPage(payload);
    els["logs-status-box"].textContent = "日志已更新。";
  }

  async function loadGroupWorkspace(groupId, preserveSelection) {
    const normalizedGroupId = String(groupId || "");
    if (!normalizedGroupId) return;
    state.currentGroupId = normalizedGroupId;
    setPage(state.currentPage === "groups" ? "groups" : state.currentPage, true);
    els["group-subtitle"].textContent = "正在加载群工作台…";
    els["chat-status-box"].textContent = "正在加载群消息…";
    const payload = await apiFetch(
      "/groups/" + encodeURIComponent(normalizedGroupId) + "/workspace?message_limit=40&member_page_size=20"
    );
    state.currentWorkspace = payload;
    state.currentMembers = payload.members || { items: [] };
    if (!preserveSelection || !findSelectedMember()) {
      state.selectedMemberId = "";
    }
    if (payload.group_profile && typeof payload.group_profile.group_all_shut !== "undefined") {
      els["whole-ban-toggle-input"].checked = !!payload.group_profile.group_all_shut;
    } else {
      els["whole-ban-toggle-input"].checked = false;
    }
    if (!preserveSelection) {
      els["group-member-search-input"].value = "";
    }
    renderCurrentGroup();
    renderGroupLists(els["group-search-input"].value || "");
  }

  async function loadGroupMembers(keyword) {
    if (!state.currentGroupId) return;
    els["member-status-box"].textContent = "正在检索成员…";
    const query = "/groups/" + encodeURIComponent(state.currentGroupId) + "/members?page=1&page_size=80&keyword=" + encodeURIComponent(keyword || "");
    const payload = await apiFetch(query);
    state.currentMembers = payload;
    if (!findSelectedMember()) {
      state.selectedMemberId = "";
    }
    renderMemberList(payload);
    renderSelectedMember();
    els["member-status-box"].textContent = "已显示 " + ((payload.pagination || {}).total || (payload.items || []).length) + " 位成员。";
  }

  async function loadLatestMessages(groupId) {
    const normalizedGroupId = String(groupId || state.currentGroupId || "");
    if (!normalizedGroupId) return;
    els["chat-status-box"].textContent = "正在加载最新消息…";
    const payload = await apiFetch("/groups/" + encodeURIComponent(normalizedGroupId) + "/messages?limit=40");
    if (!state.currentWorkspace) {
      state.currentWorkspace = {};
    }
    state.currentWorkspace.messages = payload;
    renderMessages(payload);
    els["chat-status-box"].textContent = "消息已刷新。";
  }

  async function loadOlderMessages() {
    if (!state.currentGroupId || !state.currentWorkspace || !state.currentWorkspace.messages) {
      return;
    }
    const pagination = state.currentWorkspace.messages.pagination || {};
    if (!pagination.next_before_id) {
      showSnackbar("没有更多历史消息了");
      return;
    }
    els["chat-status-box"].textContent = "正在加载更早消息…";
    const payload = await apiFetch(
      "/groups/" + encodeURIComponent(state.currentGroupId) + "/messages?limit=40&before_id=" + encodeURIComponent(String(pagination.next_before_id))
    );
    const existingItems = (state.currentWorkspace.messages.items || []).slice();
    const incomingItems = Array.isArray(payload.items) ? payload.items : [];
    const merged = [];
    const seen = new Set();
    incomingItems.concat(existingItems).forEach(function (item) {
      const key = String(item.id || item.message_id || JSON.stringify(item));
      if (seen.has(key)) return;
      seen.add(key);
      merged.push(item);
    });
    merged.sort(function (a, b) {
      return (Number(a.id) || 0) - (Number(b.id) || 0);
    });
    state.currentWorkspace.messages = {
      group_id: payload.group_id,
      mode: payload.mode,
      orm_enabled: payload.orm_enabled,
      record_enabled: payload.record_enabled,
      items: merged,
      pagination: payload.pagination
    };
    renderMessages(state.currentWorkspace.messages);
    els["chat-status-box"].textContent = "已追加更早消息。";
  }

  async function sendCurrentGroupMessage() {
    if (!state.currentGroupId) {
      showSnackbar("请先选择一个群组");
      return;
    }
    const message = (els["group-message-input"].value || "").trim();
    if (!message) {
      showSnackbar("消息不能为空");
      return;
    }
    els["send-group-message-btn"].classList.add("is-loading");
    els["send-group-message-btn"].setAttribute("aria-busy", "true");
    try {
      await apiPost("/groups/" + encodeURIComponent(state.currentGroupId) + "/messages", { message: message });
      els["group-message-input"].value = "";
      showSnackbar("消息发送成功");
      await loadLatestMessages(state.currentGroupId);
    } catch (error) {
      showSnackbar("发送消息失败：" + error.message);
    } finally {
      els["send-group-message-btn"].classList.remove("is-loading");
      els["send-group-message-btn"].removeAttribute("aria-busy");
    }
  }

  async function updateFeatureSwitch(switchKey, enabled, input) {
    if (!state.currentGroupId) return;
    try {
      await apiPost("/groups/" + encodeURIComponent(state.currentGroupId) + "/feature-switches/" + encodeURIComponent(switchKey), {
        enabled: enabled
      });
      const switches = (((state.currentWorkspace || {}).detail || {}).feature_switches) || [];
      switches.forEach(function (item) {
        if (item.key === switchKey) {
          item.enabled = enabled;
        }
      });
      renderFeatureSwitches(switches);
      showSnackbar("已更新功能开关：" + switchKey);
    } catch (error) {
      input.checked = !enabled;
      showSnackbar("更新功能开关失败：" + error.message);
    }
  }

  async function updateWholeBan(enabled, input) {
    if (!state.currentGroupId) return;
    try {
      await apiPost("/groups/" + encodeURIComponent(state.currentGroupId) + "/actions/whole-ban", {
        enabled: enabled
      });
      if (state.currentWorkspace && state.currentWorkspace.group_profile) {
        state.currentWorkspace.group_profile.group_all_shut = enabled;
      }
      renderBotProfile();
      showSnackbar(enabled ? "已开启全员禁言" : "已关闭全员禁言");
    } catch (error) {
      input.checked = !enabled;
      showSnackbar("修改全员禁言失败：" + error.message);
    }
  }

  async function markCurrentGroupRead() {
    try {
      await apiPost("/groups/" + encodeURIComponent(state.currentGroupId) + "/actions/mark-read", {});
      els["group-actions-status"].textContent = "已成功标记当前群消息为已读。";
      showSnackbar("已标记群消息为已读");
    } catch (error) {
      showSnackbar("标记已读失败：" + error.message);
    }
  }

  async function performMemberAction(action) {
    const member = findSelectedMember();
    if (!state.currentGroupId || !member) {
      showSnackbar("请先选择一个成员");
      return;
    }
    if (action === "kick" && !window.confirm("确定将成员 “" + member.display_name + "” 踢出当前群吗？")) {
      return;
    }

    try {
      if (action === "mute") {
        const duration = Math.max(parseInt(els["mute-duration-input"].value || "0", 10) || 0, 0);
        await apiPost("/groups/" + encodeURIComponent(state.currentGroupId) + "/actions/mute", {
          user_id: member.user_id,
          duration: duration
        });
        showSnackbar("已对成员执行禁言");
      }
      if (action === "title") {
        await apiPost("/groups/" + encodeURIComponent(state.currentGroupId) + "/actions/special-title", {
          user_id: member.user_id,
          special_title: els["special-title-input"].value || ""
        });
        showSnackbar("头衔设置成功");
      }
      if (action === "kick") {
        await apiPost("/groups/" + encodeURIComponent(state.currentGroupId) + "/actions/kick", {
          user_id: member.user_id,
          reject_add_request: false
        });
        showSnackbar("已踢出成员");
      }
      await loadGroupWorkspace(state.currentGroupId, true);
    } catch (error) {
      showSnackbar("成员操作失败：" + error.message);
    }
  }

  function handleGroupListClick(event) {
    const trigger = event.target.closest("[data-group-id]");
    if (!trigger) return;
    const groupId = String(trigger.getAttribute("data-group-id"));
    state.currentGroupId = groupId;
    setPage("groups");
    loadGroupWorkspace(groupId, false);
    if (mobileDrawer) {
      mobileDrawer.close();
    }
  }

  function handleTopGroupClick(event) {
    const trigger = event.target.closest("[data-group-id]");
    if (!trigger) return;
    const groupId = String(trigger.getAttribute("data-group-id"));
    state.currentGroupId = groupId;
    setPage("groups");
    loadGroupWorkspace(groupId, false);
  }

  function setPage(page, skipTitle) {
    state.currentPage = page;
    document.querySelectorAll(".workspace-page").forEach(function (node) {
      node.classList.toggle("is-active", node.getAttribute("data-page") === page);
    });
    document.querySelectorAll("[data-page]").forEach(function (node) {
      node.classList.toggle("is-active", node.getAttribute("data-page") === page);
    });
    if (!skipTitle) {
      const titleMap = {
        dashboard: "主页数据面板",
        logs: "日志中心",
        groups: state.currentGroupId ? "群聊工作台 · " + state.currentGroupId : "群聊工作台"
      };
      els["page-subtitle"].textContent = titleMap[page] || "Admin Dashboard";
    }
  }

  function renderDashboard() {
    renderDashboardMetrics();
    renderTrendChart((state.overview || {}).daily_trend || []);
    renderLogsDonut((state.logsOverview || {}).level_totals || {});
    renderTopGroups((state.overview || {}).top_groups || (state.operationsOverview || {}).top_groups || []);
    renderRecentLogs((state.recentLogs || {}).items || []);
    renderAccountOverview(state.accountOverview || {});
    renderRecentContacts((state.recentContacts || {}).items || []);
    els["dashboard-generated-at"].textContent = (state.overview || {}).generated_at ? "最近生成：" + formatDateTime(state.overview.generated_at) : "尚未生成";
  }

  function renderDashboardMetrics() {
    const metrics = [
      {
        label: "总群数",
        value: formatNumber((state.overview || {}).group_count),
        hint: "已识别接入的群总数"
      },
      {
        label: "今日总消息数",
        value: formatNumber((state.overview || {}).today_message_count),
        hint: "来自聚合 overview.daily_trend / 统计快照"
      },
      {
        label: "可管理群数",
        value: formatNumber((state.operationsOverview || {}).manageable_group_count),
        hint: "基础群管已启用的群数"
      },
      {
        label: "在线客户端",
        value: formatNumber((state.accountOverview || {}).client_count),
        hint: "当前账号在线终端数量"
      }
    ];
    els["dashboard-metrics"].innerHTML = metrics.map(function (item) {
      return [
        '<div class="mdui-col-xs-12 mdui-col-sm-6 mdui-col-lg-3">',
        '  <div class="workspace-metric-card">',
        '    <div class="workspace-metric-label">' + escapeHtml(item.label) + '</div>',
        '    <div class="workspace-metric-value">' + escapeHtml(item.value) + '</div>',
        '    <div class="workspace-metric-hint">' + escapeHtml(item.hint) + '</div>',
        '  </div>',
        '</div>'
      ].join("");
    }).join("");
  }

  function renderTrendChart(items) {
    if (!Array.isArray(items) || !items.length) {
      els["trend-chart"].innerHTML = '<div class="workspace-empty">暂无趋势数据</div>';
      els["trend-status-box"].textContent = "暂无可绘制的趋势数据。";
      return;
    }
    const width = 680;
    const height = 280;
    const padding = { top: 22, right: 20, bottom: 34, left: 42 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;
    const maxValue = Math.max.apply(null, items.map(function (item) {
      return Number(item.message_count) || 0;
    }).concat([1]));

    const points = items.map(function (item, index) {
      const x = padding.left + (chartWidth / Math.max(items.length - 1, 1)) * index;
      const y = padding.top + chartHeight - ((Number(item.message_count) || 0) / maxValue) * chartHeight;
      return { x: x, y: y, item: item };
    });
    const polyline = points.map(function (point) {
      return point.x.toFixed(2) + "," + point.y.toFixed(2);
    }).join(" ");
    const area = [padding.left + "," + (padding.top + chartHeight)].concat(points.map(function (point) {
      return point.x.toFixed(2) + "," + point.y.toFixed(2);
    })).concat([(padding.left + chartWidth) + "," + (padding.top + chartHeight)]).join(" ");

    const yTicks = [0, maxValue / 2, maxValue].map(function (value) {
      return Math.round(value);
    });

    const xLabels = points.map(function (point) {
      return '<text class="workspace-axis-label" x="' + point.x.toFixed(2) + '" y="' + (height - 8) + '" text-anchor="middle">' + escapeHtml(String(point.item.date).slice(5)) + '</text>';
    }).join("");

    const circles = points.map(function (point) {
      return [
        '<circle cx="' + point.x.toFixed(2) + '" cy="' + point.y.toFixed(2) + '" r="4.5" fill="#4455d8"></circle>',
        '<text class="workspace-axis-label" x="' + point.x.toFixed(2) + '" y="' + (point.y - 12).toFixed(2) + '" text-anchor="middle">' + escapeHtml(formatNumber(point.item.message_count)) + '</text>'
      ].join("");
    }).join("");

    const yGrid = yTicks.map(function (value) {
      const y = padding.top + chartHeight - (value / maxValue) * chartHeight;
      return [
        '<line x1="' + padding.left + '" y1="' + y.toFixed(2) + '" x2="' + (padding.left + chartWidth) + '" y2="' + y.toFixed(2) + '" stroke="#dce3f0" stroke-dasharray="4 4"></line>',
        '<text class="workspace-axis-label" x="' + (padding.left - 8) + '" y="' + (y + 4).toFixed(2) + '" text-anchor="end">' + escapeHtml(formatNumber(value)) + '</text>'
      ].join("");
    }).join("");

    els["trend-chart"].innerHTML = [
      '<svg viewBox="0 0 ' + width + ' ' + height + '" role="img" aria-label="7 日消息趋势图">',
      '  <defs>',
      '    <linearGradient id="trendArea" x1="0" x2="0" y1="0" y2="1">',
      '      <stop offset="0%" stop-color="#4455d8" stop-opacity="0.28"></stop>',
      '      <stop offset="100%" stop-color="#4455d8" stop-opacity="0.03"></stop>',
      '    </linearGradient>',
      '  </defs>',
      yGrid,
      '  <polygon points="' + area + '" fill="url(#trendArea)"></polygon>',
      '  <polyline points="' + polyline + '" fill="none" stroke="#4455d8" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"></polyline>',
      circles,
      xLabels,
      '</svg>'
    ].join("");
    els["trend-status-box"].textContent = "已聚合 " + items.length + " 天的消息量趋势。";
  }

  function renderLogsDonut(levelTotals) {
    const entries = Object.keys(levelTotals || {}).filter(function (key) {
      return Number(levelTotals[key]) > 0;
    }).map(function (key) {
      return { key: key, value: Number(levelTotals[key]) || 0 };
    });
    if (!entries.length) {
      els["logs-donut"].innerHTML = '<div class="workspace-empty">暂无日志级别分布</div>';
      return;
    }
    const palette = ["#4455d8", "#47a65e", "#ef7d3c", "#d9544f", "#9aa3b4"];
    const total = entries.reduce(function (sum, item) { return sum + item.value; }, 0);
    let offset = 0;
    const radius = 64;
    const circumference = 2 * Math.PI * radius;
    const segments = entries.map(function (item, index) {
      const dash = (item.value / total) * circumference;
      const circle = '<circle cx="120" cy="120" r="' + radius + '" fill="none" stroke="' + palette[index % palette.length] + '" stroke-width="26" stroke-linecap="round" stroke-dasharray="' + dash.toFixed(2) + ' ' + (circumference - dash).toFixed(2) + '" stroke-dashoffset="' + (-offset).toFixed(2) + '"></circle>';
      offset += dash;
      return circle;
    }).join("");
    const legends = entries.map(function (item, index) {
      const percent = total ? ((item.value / total) * 100).toFixed(1) : "0.0";
      return [
        '<div class="workspace-ranked-item">',
        '  <span class="workspace-rank-index" style="background:' + palette[index % palette.length] + ';color:#fff;">' + escapeHtml(item.key.slice(0, 1)) + '</span>',
        '  <div class="workspace-rank-body">',
        '    <div class="workspace-rank-title">' + escapeHtml(item.key) + '</div>',
        '    <div class="workspace-rank-meta">' + escapeHtml(formatNumber(item.value)) + ' 条 · ' + percent + '%</div>',
        '  </div>',
        '</div>'
      ].join("");
    }).join("");

    els["logs-donut"].innerHTML = [
      '<div class="mdui-row">',
      '  <div class="mdui-col-xs-12 mdui-col-sm-5">',
      '    <svg viewBox="0 0 240 240" role="img" aria-label="日志级别环图">',
      '      <circle cx="120" cy="120" r="' + radius + '" fill="none" stroke="#eef1f7" stroke-width="26"></circle>',
      segments,
      '      <text x="120" y="112" text-anchor="middle" style="font-size:18px;font-weight:700;fill:#1f2937;">' + escapeHtml(formatNumber(total)) + '</text>',
      '      <text x="120" y="136" text-anchor="middle" style="font-size:12px;fill:#6b7489;">总日志数</text>',
      '    </svg>',
      '  </div>',
      '  <div class="mdui-col-xs-12 mdui-col-sm-7">',
      legends,
      '  </div>',
      '</div>'
    ].join("");
  }

  function renderTopGroups(items) {
    if (!Array.isArray(items) || !items.length) {
      els["top-group-list"].innerHTML = '<div class="workspace-empty">暂无活跃群组数据</div>';
      return;
    }
    els["top-group-list"].innerHTML = items.map(function (item, index) {
      return [
        '<a href="javascript:;" class="workspace-ranked-item" data-group-id="' + escapeHtml(String(item.group_id)) + '">',
        '  <span class="workspace-rank-index">' + escapeHtml(String(index + 1)) + '</span>',
        '  <div class="workspace-rank-body">',
        '    <div class="workspace-rank-title">' + escapeHtml(item.group_name || item.group_id) + '</div>',
        '    <div class="workspace-rank-meta">群号 ' + escapeHtml(String(item.group_id)) + ' · 成员 ' + escapeHtml(formatNumber(item.member_count)) + '</div>',
        '  </div>',
        '  <span class="workspace-rank-value">' + escapeHtml(formatNumber(item.today_message_count)) + ' 条</span>',
        '</a>'
      ].join("");
    }).join("");
  }

  function renderRecentLogs(items) {
    if (!Array.isArray(items) || !items.length) {
      els["recent-log-list"].innerHTML = '<div class="workspace-empty">暂无日志事件</div>';
      return;
    }
    els["recent-log-list"].innerHTML = items.map(function (item) {
      return [
        '<div class="workspace-event-item">',
        '  <div class="workspace-event-title">' + escapeHtml(item.module || item.source || "日志") + '</div>',
        '  <div class="workspace-event-meta">' + escapeHtml((item.timestamp || "未知时间") + ' · ' + (item.level || "INFO")) + '</div>',
        '  <div class="workspace-resource-text">' + escapeHtml(item.message || item.detail || "") + '</div>',
        '</div>'
      ].join("");
    }).join("");
  }

  function renderAccountOverview(account) {
    if (!account || !account.available) {
      els["account-overview-box"].innerHTML = '<div class="workspace-empty">暂无账号信息</div>';
      return;
    }
    const chips = [
      account.online ? statusChip("在线", "is-green") : statusChip("离线", "is-red"),
      account.good ? statusChip("状态正常", "is-green") : statusChip("状态异常", "is-yellow")
    ].join("");
    els["account-overview-box"].innerHTML = [
      '<div class="workspace-ranked-item">',
      '  <span class="workspace-avatar-circle">' + escapeHtml(avatarText(account.nickname || account.self_id || "B")) + '</span>',
      '  <div class="workspace-rank-body">',
      '    <div class="workspace-rank-title">' + escapeHtml(account.nickname || "Bot") + '</div>',
      '    <div class="workspace-rank-meta">QQ ' + escapeHtml(String(account.self_id || "未知")) + '</div>',
      '  </div>',
      '</div>',
      '<div style="margin-top:12px;">' + chips + '</div>',
      '<div class="workspace-kv-grid" style="margin-top:12px;">',
      kvItem("在线群数", formatNumber(account.group_count)),
      kvItem("好友数", formatNumber(account.friend_count)),
      kvItem("客户端数", formatNumber(account.client_count)),
      kvItem("实例数", formatNumber(account.bot_count)),
      '</div>'
    ].join("");
  }

  function renderRecentContacts(items) {
    if (!Array.isArray(items) || !items.length) {
      els["recent-contact-list"].innerHTML = '<div class="workspace-empty">暂无最近会话</div>';
      return;
    }
    els["recent-contact-list"].innerHTML = items.map(function (item) {
      const actionAttrs = item.group_id ? ' data-group-id="' + escapeHtml(String(item.group_id)) + '"' : "";
      return [
        '<div class="workspace-contact-item"' + actionAttrs + '>',
        '  <div class="workspace-contact-title">' + escapeHtml(item.title || item.peer_id || "未知会话") + '</div>',
        '  <div class="workspace-contact-meta">' + escapeHtml((item.chat_kind === "group" ? "群聊" : "私聊") + ' · ' + (item.msg_time || "未知时间")) + '</div>',
        '  <div class="workspace-resource-text">' + escapeHtml(item.preview || "（空消息）") + '</div>',
        item.subtitle ? '  <div class="workspace-contact-meta">发送者：' + escapeHtml(item.subtitle) + '</div>' : '',
        '</div>'
      ].join("");
    }).join("");
    els["recent-contact-list"].querySelectorAll("[data-group-id]").forEach(function (node) {
      node.addEventListener("click", function () {
        const groupId = node.getAttribute("data-group-id");
        state.currentGroupId = String(groupId);
        setPage("groups");
        loadGroupWorkspace(groupId, false);
      });
    });
  }

  function renderLogLevelFilters() {
    const levelTotals = (state.logsOverview || {}).level_totals || {};
    const buttons = [{ key: "", label: "All", total: sumObject(levelTotals) }].concat(Object.keys(levelTotals).map(function (key) {
      return { key: key, label: key, total: levelTotals[key] };
    }));
    els["log-level-filter"].innerHTML = buttons.map(function (item) {
      const active = state.logs.level === item.key;
      return '<a href="javascript:;" class="workspace-chip-filter' + (active ? ' is-active' : '') + '" data-log-level="' + escapeHtml(item.key) + '">' + escapeHtml(item.label) + (typeof item.total !== "undefined" ? " · " + escapeHtml(formatNumber(item.total)) : "") + '</a>';
    }).join("");
  }

  function renderLogsPage(payload) {
    renderLogLevelFilters();
    const items = Array.isArray(payload.items) ? payload.items : [];
    const pagination = payload.pagination || {};
    els["logs-search-input"].value = state.logs.keyword || "";
    els["logs-pagination-info"].textContent = "第 " + formatNumber(pagination.page || 1) + " / " + formatNumber(pagination.total_pages || 1) + " 页 · 共 " + formatNumber(pagination.total || items.length) + " 条";
    if (!items.length) {
      els["logs-console-list"].innerHTML = '<div class="workspace-empty">暂无匹配日志</div>';
      return;
    }
    els["logs-console-list"].innerHTML = items.map(function (item) {
      const timeText = item.timestamp ? String(item.timestamp).slice(11, 19) : "--:--:--";
      return [
        '<div class="workspace-log-line">',
        '  <span class="workspace-log-time">[' + escapeHtml(timeText) + ']</span>',
        '  <span class="workspace-log-level ' + escapeHtml(String(item.level || "INFO").toUpperCase()) + '">[' + escapeHtml(String(item.level || "INFO").toUpperCase()) + ']</span>',
        '  <span>' + escapeHtml((item.module || item.source || "runtime") + (item.group_id ? ' · 群 ' + item.group_id : '') + ' — ' + (item.message || item.detail || '')) + '</span>',
        '</div>'
      ].join("");
    }).join("");
  }

  function renderGroupLists(filterValue) {
    const filter = String(filterValue || "").trim().toLowerCase();
    const items = state.groups.filter(function (item) {
      if (!filter) return true;
      return String(item.group_id || "").toLowerCase().indexOf(filter) >= 0 || String(item.group_name || "").toLowerCase().indexOf(filter) >= 0;
    });
    const html = items.length ? items.map(function (item) {
      const active = String(item.group_id) === String(state.currentGroupId);
      return [
        '<a href="javascript:;" class="mdui-list-item mdui-ripple' + (active ? ' is-active' : '') + '" data-group-id="' + escapeHtml(String(item.group_id)) + '">',
        '  <span class="mdui-list-item-avatar">' + escapeHtml(avatarText(item.group_name || item.group_id)) + '</span>',
        '  <div class="mdui-list-item-content">',
        '    <div class="workspace-list-primary">' + escapeHtml(item.group_name || item.group_id) + '</div>',
        '    <div class="workspace-list-secondary">群号 ' + escapeHtml(String(item.group_id)) + ' · 今日 ' + escapeHtml(formatNumber(item.today_message_count)) + ' · 历史 ' + escapeHtml(formatNumber(item.history_message_count)) + '</div>',
        '  </div>',
        '</a>'
      ].join("");
    }).join("") : '<div class="workspace-empty">没有匹配的群组</div>';
    els["desktop-group-list"].innerHTML = html;
    els["mobile-group-list"].innerHTML = html;
  }

  function renderCurrentGroup() {
    const workspace = state.currentWorkspace || {};
    const detail = workspace.detail || {};
    const summary = detail.summary || {};
    const groupProfile = workspace.group_profile || {};
    const groupName = groupProfile.group_name || summary.group_name || state.currentGroupId || "群聊工作台";
    els["group-title"].textContent = groupName;
    els["group-subtitle"].textContent = "群号 " + escapeHtml(String(summary.group_id || state.currentGroupId || "")) + " · " + (groupProfile.group_remark ? ("备注：" + groupProfile.group_remark) : "工作台已加载");
    els["page-subtitle"].textContent = "群聊工作台 · " + groupName;

    const metricItems = [
      { label: "成员数", value: formatNumber(groupProfile.member_count || summary.member_count), hint: "群当前成员规模" },
      { label: "今日消息", value: formatNumber(((detail.statistics || {}).today_message_count)), hint: "今日累计消息数" },
      { label: "历史消息", value: formatNumber(((detail.statistics || {}).history_message_count)), hint: "记录 / 历史消息总数" },
      { label: "启用功能", value: formatNumber((detail.feature_switches_summary || {}).enabled_count), hint: "当前群打开的插件功能开关" }
    ];
    els["group-metrics"].innerHTML = metricItems.map(function (item) {
      return [
        '<div class="mdui-col-xs-12 mdui-col-sm-6 mdui-col-lg-3">',
        '  <div class="workspace-metric-card">',
        '    <div class="workspace-metric-label">' + escapeHtml(item.label) + '</div>',
        '    <div class="workspace-metric-value">' + escapeHtml(item.value) + '</div>',
        '    <div class="workspace-metric-hint">' + escapeHtml(item.hint) + '</div>',
        '  </div>',
        '</div>'
      ].join("");
    }).join("");

    renderBotProfile();
    renderFeatureSwitches(detail.feature_switches || []);
    renderMessages(workspace.messages || { items: [] });
    renderAnnouncements((workspace.announcements || {}).items || []);
    renderFiles(workspace.files || {});
    renderEssence((workspace.essence || {}).items || []);
    renderHonors(workspace.honors || {});
    renderMemberList(state.currentMembers || workspace.members || { items: [] });
    renderSelectedMember();

    els["group-actions-status"].textContent = "Bot 能力与群动作已就绪。";
    els["chat-status-box"].textContent = "消息模式：" + escapeHtml(((workspace.messages || {}).mode) || "unknown");
    els["member-status-box"].textContent = "已加载 " + escapeHtml(formatNumber((((state.currentMembers || {}).pagination || {}).total) || ((state.currentMembers || {}).items || []).length)) + " 位成员。";
    if (window.mdui) {
      mdui.mutation();
    }
  }

  function renderEmptyWorkspace() {
    els["group-title"].textContent = "群聊工作台";
    els["group-subtitle"].textContent = "请先从左侧选择一个群组";
    els["group-metrics"].innerHTML = "";
    els["chat-message-list"].innerHTML = '<div class="workspace-empty">尚未选择群组</div>';
    els["announcement-list"].innerHTML = '<div class="workspace-empty">尚未选择群组</div>';
    els["group-file-table-body"].innerHTML = '<tr><td colspan="4" class="workspace-empty-row">尚未选择群组</td></tr>';
    els["file-system-summary"].innerHTML = "";
    els["essence-list"].innerHTML = '<div class="workspace-empty">尚未选择群组</div>';
    els["honor-list"].innerHTML = '<div class="workspace-empty">尚未选择群组</div>';
    els["bot-profile-box"].innerHTML = '<div class="workspace-empty">尚未选择群组</div>';
    els["feature-switch-list"].innerHTML = '<div class="workspace-empty">尚未选择群组</div>';
    els["group-member-list"].innerHTML = '<div class="workspace-empty">尚未选择群组</div>';
    els["selected-member-box"].innerHTML = "请从下方列表中选择成员";
  }

  function renderBotProfile() {
    const workspace = state.currentWorkspace || {};
    const botProfile = workspace.bot_profile || {};
    const groupProfile = workspace.group_profile || {};
    if (!botProfile.self_id) {
      els["bot-profile-box"].innerHTML = '<div class="workspace-empty">暂无 Bot 信息</div>';
      return;
    }
    const chips = [
      statusChip(botProfile.role || "member", botProfile.role === "owner" ? "is-green" : (botProfile.role === "admin" ? "is-yellow" : "")),
      groupProfile.group_all_shut ? statusChip("全员禁言中", "is-red") : statusChip("未全员禁言", "is-green"),
      statusChip(((workspace.messages || {}).mode) || "unknown", "")
    ].join("");
    const capabilities = Object.keys((botProfile.capabilities || {})).filter(function (key) {
      return !!botProfile.capabilities[key];
    }).map(function (key) {
      return '<span class="workspace-inline-chip">' + escapeHtml(key) + '</span>';
    }).join("");
    els["bot-profile-box"].innerHTML = [
      '<div class="workspace-ranked-item">',
      '  <span class="workspace-avatar-circle">' + escapeHtml(avatarText(botProfile.card || botProfile.nickname || botProfile.self_id || "B")) + '</span>',
      '  <div class="workspace-rank-body">',
      '    <div class="workspace-rank-title">' + escapeHtml(botProfile.card || botProfile.nickname || "Bot") + '</div>',
      '    <div class="workspace-rank-meta">Bot QQ ' + escapeHtml(String(botProfile.self_id)) + '</div>',
      '  </div>',
      '</div>',
      '<div style="margin-top:12px;">' + chips + '</div>',
      '<div class="workspace-resource-text">' + (capabilities || '暂无能力标签') + '</div>'
    ].join("");
  }

  function renderFeatureSwitches(items) {
    if (!Array.isArray(items) || !items.length) {
      els["feature-switch-list"].innerHTML = '<div class="workspace-empty">暂无功能开关</div>';
      return;
    }
    els["feature-switch-list"].innerHTML = items.map(function (item) {
      return [
        '<div class="workspace-switch-card">',
        '  <div class="workspace-switch-copy">',
        '    <strong>' + escapeHtml(item.label || item.key) + '</strong>',
        '    <span>' + escapeHtml(item.key || "") + '</span>',
        '  </div>',
        '  <label class="mdui-switch">',
        '    <input type="checkbox" data-switch-key="' + escapeHtml(String(item.key)) + '"' + (item.enabled ? ' checked' : '') + '>',
        '    <i class="mdui-switch-icon"></i>',
        '  </label>',
        '</div>'
      ].join("");
    }).join("");
  }

  function renderMessages(payload) {
    const items = Array.isArray(payload.items) ? payload.items : [];
    const selfId = String((((state.currentWorkspace || {}).bot_profile || {}).self_id) || "");
    if (!items.length) {
      els["chat-message-list"].innerHTML = '<div class="workspace-empty">暂无消息记录</div>';
      return;
    }
    els["chat-message-list"].innerHTML = items.map(function (item) {
      const isSelf = selfId && String(item.user_id || "") === selfId;
      return [
        '<div class="workspace-message-row' + (isSelf ? ' is-self' : '') + '">',
        '  <span class="workspace-message-avatar">' + escapeHtml(avatarText(item.display_name || item.user_id || "M")) + '</span>',
        '  <div class="workspace-message-bubble">',
        '    <div class="workspace-message-header">',
        '      <span class="workspace-message-name">' + escapeHtml(item.display_name || item.user_id || "未知成员") + '</span>',
        '      <span class="workspace-message-time">' + escapeHtml(formatDateTime(item.created_at) || "未知时间") + '</span>',
        '    </div>',
        '    <div class="workspace-message-body">' + escapeHtml(item.plain_text || "（空消息）") + '</div>',
        '  </div>',
        '</div>'
      ].join("");
    }).join("");
    els["chat-message-list"].scrollTop = els["chat-message-list"].scrollHeight;
  }

  function renderAnnouncements(items) {
    if (!Array.isArray(items) || !items.length) {
      els["announcement-list"].innerHTML = '<div class="workspace-empty">暂无群公告</div>';
      return;
    }
    els["announcement-list"].innerHTML = items.map(function (item) {
      return [
        '<div class="workspace-resource-card">',
        '  <div class="workspace-resource-title">公告 #' + escapeHtml(String(item.notice_id || "")) + '</div>',
        '  <div class="workspace-resource-meta">' + escapeHtml((item.publish_time || "未知时间") + ' · 发送者 ' + (item.sender_id || "未知")) + '</div>',
        '  <div class="workspace-resource-text">' + escapeHtml(item.text || "（空内容）") + '</div>',
        item.image_count ? '  <div class="workspace-resource-meta">附带图片 ' + escapeHtml(String(item.image_count)) + ' 张</div>' : '',
        '</div>'
      ].join("");
    }).join("");
  }

  function renderFiles(payload) {
    const systemInfo = payload.system_info || {};
    const folders = Array.isArray(payload.folders) ? payload.folders : [];
    const folderChips = folders.length ? '<div class="workspace-resource-text" style="margin-top:12px;">' + folders.slice(0, 8).map(function (item) {
      return '<span class="workspace-inline-chip">' + escapeHtml(item.folder_name || item.folder_id || "文件夹") + '</span>';
    }).join("") + '</div>' : '';
    els["file-system-summary"].innerHTML = payload.available === false ? '<div class="workspace-empty">当前环境不支持群文件接口：' + escapeHtml(payload.error || "unknown") + '</div>' : [
      '<div class="workspace-kv-grid">',
      kvItem("文件数", formatNumber(systemInfo.file_count)),
      kvItem("容量上限", formatFileSize(systemInfo.total_space)),
      kvItem("已用空间", formatFileSize(systemInfo.used_space)),
      kvItem("文件数量上限", formatNumber(systemInfo.limit_count)),
      '</div>',
      folderChips
    ].join("");
    const files = Array.isArray(payload.files) ? payload.files : [];
    if (!files.length) {
      els["group-file-table-body"].innerHTML = '<tr><td colspan="4" class="workspace-empty-row">暂无群文件</td></tr>';
      return;
    }
    els["group-file-table-body"].innerHTML = files.map(function (item) {
      return [
        '<tr>',
        '  <td>' + escapeHtml(item.file_name || item.file_id || "未知文件") + '</td>',
        '  <td>' + escapeHtml(formatFileSize(item.size || item.file_size)) + '</td>',
        '  <td>' + escapeHtml(item.uploader_name || item.uploader || "未知") + '</td>',
        '  <td>' + escapeHtml(formatDateTime(item.upload_time_iso || item.upload_time)) + '</td>',
        '</tr>'
      ].join("");
    }).join("");
  }

  function renderEssence(items) {
    if (!Array.isArray(items) || !items.length) {
      els["essence-list"].innerHTML = '<div class="workspace-empty">暂无精华消息</div>';
      return;
    }
    els["essence-list"].innerHTML = items.map(function (item) {
      return [
        '<div class="workspace-resource-card">',
        '  <div class="workspace-resource-title">' + escapeHtml(item.sender_nick || item.sender_id || "未知成员") + '</div>',
        '  <div class="workspace-resource-meta">设精者 ' + escapeHtml(item.operator_nick || item.operator_id || "未知") + ' · ' + escapeHtml(formatDateTime(item.operator_time)) + '</div>',
        '  <div class="workspace-resource-text">' + escapeHtml(item.plain_text || "（非文本内容）") + '</div>',
        '</div>'
      ].join("");
    }).join("");
  }

  function renderHonors(payload) {
    if (!payload || payload.available === false) {
      els["honor-list"].innerHTML = '<div class="workspace-empty">暂无群荣誉数据' + (payload && payload.error ? '：' + escapeHtml(payload.error) : '') + '</div>';
      return;
    }
    const sections = Array.isArray(payload.sections) ? payload.sections : [];
    const cards = sections.filter(function (section) {
      return section.count > 0;
    }).map(function (section) {
      const people = (section.items || []).slice(0, 5).map(function (item) {
        const nickname = item.nickname || item.nick || item.user_id || item.uin || "未知成员";
        return '<span class="workspace-inline-chip">' + escapeHtml(String(nickname)) + '</span>';
      }).join("");
      return [
        '<div class="workspace-resource-card">',
        '  <div class="workspace-resource-title">' + escapeHtml(section.label) + '</div>',
        '  <div class="workspace-resource-meta">' + escapeHtml(formatNumber(section.count)) + ' 人</div>',
        '  <div class="workspace-resource-text">' + (people || '暂无详情') + '</div>',
        '</div>'
      ].join("");
    });
    els["honor-list"].innerHTML = cards.length ? cards.join("") : '<div class="workspace-empty">暂无群荣誉</div>';
  }

  function renderMemberList(payload) {
    const items = Array.isArray(payload.items) ? payload.items : [];
    if (!items.length) {
      els["group-member-list"].innerHTML = '<div class="workspace-empty">暂无成员</div>';
      return;
    }
    els["group-member-list"].innerHTML = items.map(function (item) {
      const active = String(item.user_id) === String(state.selectedMemberId);
      return [
        '<a href="javascript:;" class="mdui-list-item mdui-ripple' + (active ? ' is-active' : '') + '" data-user-id="' + escapeHtml(String(item.user_id)) + '">',
        '  <span class="mdui-list-item-avatar">' + escapeHtml(avatarText(item.display_name || item.user_id)) + '</span>',
        '  <div class="mdui-list-item-content">',
        '    <div class="workspace-list-primary">' + escapeHtml(item.display_name || item.user_id) + '</div>',
        '    <div class="workspace-list-secondary">' + escapeHtml(String(item.role || "member")) + (item.title ? ' · ' + escapeHtml(String(item.title)) : '') + '</div>',
        '  </div>',
        '</a>'
      ].join("");
    }).join("");
  }

  function renderSelectedMember() {
    const member = findSelectedMember();
    if (!member) {
      els["selected-member-box"].classList.add("empty");
      els["selected-member-box"].innerHTML = "请从下方列表中选择成员";
      return;
    }
    els["selected-member-box"].classList.remove("empty");
    els["selected-member-box"].innerHTML = [
      '<div class="workspace-resource-title">' + escapeHtml(member.display_name || member.user_id) + '</div>',
      '<div class="workspace-resource-meta">QQ ' + escapeHtml(String(member.user_id || "")) + ' · ' + escapeHtml(String(member.role || "member")) + '</div>',
      member.title ? '<div class="workspace-resource-meta">当前头衔：' + escapeHtml(String(member.title)) + '</div>' : '',
      typeof member.last_sent_time !== "undefined" && member.last_sent_time !== null ? '<div class="workspace-resource-meta">最后发言：' + escapeHtml(formatUnix(member.last_sent_time)) + '</div>' : ''
    ].join("");
  }

  function findSelectedMember() {
    const items = ((state.currentMembers || {}).items) || [];
    return items.find(function (item) {
      return String(item.user_id) === String(state.selectedMemberId);
    }) || null;
  }

  function updateConnectionChip(mode) {
    const authRequired = !!((state.meta || {}).auth_required);
    const hasToken = !!state.token;
    let text = "已连接";
    let className = "workspace-badge-chip";
    if (mode === "loading") {
      text = "同步中…";
    } else if (mode === "error") {
      text = "连接异常";
    } else if (authRequired && !hasToken) {
      text = "需要 Token";
    } else if (authRequired && hasToken) {
      text = "已鉴权";
    }
    els["connection-chip"].className = className;
    els["connection-chip"].textContent = text;
  }

  async function apiFetch(path, options) {
    const config = options || {};
    const auth = config.auth !== false;
    const response = await window.fetch((bootstrap.apiBasePath || "") + path, {
      method: config.method || "GET",
      headers: buildHeaders(auth, config.headers),
      body: config.body
    });
    if (response.status === 401) {
      updateConnectionChip();
      throw new Error("鉴权失败，请检查 X-Admin-Token");
    }
    if (!response.ok) {
      let detail = response.statusText || "Request failed";
      try {
        const payload = await response.json();
        detail = payload.detail || payload.message || JSON.stringify(payload);
      } catch (error) {
        try {
          detail = await response.text();
        } catch (innerError) {
          detail = response.statusText || detail;
        }
      }
      throw new Error(detail);
    }
    return response.json();
  }

  function apiPost(path, payload) {
    return apiFetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload || {})
    });
  }

  function buildHeaders(auth, extraHeaders) {
    const headers = Object.assign({}, extraHeaders || {});
    if (auth && state.token) {
      headers["X-Admin-Token"] = state.token;
    }
    return headers;
  }

  function showSnackbar(message) {
    if (window.mdui && typeof mdui.snackbar === "function") {
      mdui.snackbar({ message: message, timeout: 2600, position: "right-top" });
    }
  }

  function statusChip(label, className) {
    return '<span class="workspace-status-chip ' + (className || '') + '">' + escapeHtml(label) + '</span>';
  }

  function kvItem(key, value) {
    return [
      '<div class="workspace-kv-item">',
      '  <div class="workspace-kv-key">' + escapeHtml(key) + '</div>',
      '  <div class="workspace-kv-value">' + escapeHtml(value) + '</div>',
      '</div>'
    ].join("");
  }

  function sumObject(obj) {
    return Object.keys(obj || {}).reduce(function (sum, key) {
      return sum + (Number(obj[key]) || 0);
    }, 0);
  }

  function formatNumber(value) {
    if (value === null || value === undefined || value === "") return "0";
    const num = Number(value);
    if (Number.isNaN(num)) return String(value);
    return num.toLocaleString("zh-CN");
  }

  function formatDateTime(value) {
    if (!value) return "--";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return [date.getFullYear(), pad2(date.getMonth() + 1), pad2(date.getDate())].join("-") + " " + [pad2(date.getHours()), pad2(date.getMinutes()), pad2(date.getSeconds())].join(":");
  }

  function formatUnix(value) {
    if (!value) return "--";
    const date = new Date(Number(value) * 1000);
    if (Number.isNaN(date.getTime())) return String(value);
    return formatDateTime(date.toISOString());
  }

  function formatFileSize(value) {
    const num = Number(value || 0);
    if (!num) return "0 B";
    const units = ["B", "KB", "MB", "GB", "TB"];
    let size = num;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex += 1;
    }
    return size.toFixed(size >= 10 || unitIndex === 0 ? 0 : 1) + " " + units[unitIndex];
  }

  function avatarText(value) {
    const text = String(value || "?").trim();
    return text ? text.slice(0, 1).toUpperCase() : "?";
  }

  function pad2(value) {
    return String(value).padStart(2, "0");
  }

  function escapeHtml(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }
})();
