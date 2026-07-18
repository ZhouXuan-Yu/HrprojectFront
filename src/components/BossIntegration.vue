<template>
  <div class="boss-integration" :class="{ compact }">
    <!-- ===== Section A: BOSS Status Bar ===== -->
    <div class="card">
      <div class="card-title">
        <svg viewBox="0 0 24 24" style="width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
        BOSS 连接状态
      </div>
      <div class="status-row">
        <div class="status-info">
          <span class="status-dot" :class="statusClass"></span>
          <span class="status-label">{{ statusText }}</span>
          <span v-if="statusVersion" class="status-version">v{{ statusVersion }}</span>
        </div>
        <div class="status-actions">
          <button
            class="btn btn-outline btn-sm"
            :disabled="statusLoading"
            @click="refreshStatus"
            aria-label="刷新 BOSS 连接状态"
          >
            <span v-if="statusLoading" class="spinner-inline-dark"></span>
            刷新状态
          </button>
          <button
            v-if="statusState !== 'connected'"
            class="btn btn-primary btn-sm"
            :disabled="statusLoading"
            @click="handleLogin"
            aria-label="登录 BOSS 直聘"
          >
            <span v-if="statusLoading" class="spinner-inline"></span>
            登录 BOSS
          </button>
        </div>
      </div>
      <div v-if="statusError" class="error-msg">
        {{ statusError }}
        <button class="btn btn-text btn-sm" @click="refreshStatus" aria-label="重试获取状态">重试</button>
      </div>
      <!-- Slow operation hint -->
      <div v-if="statusLoading" class="slow-hint">
        <svg viewBox="0 0 24 24" style="width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        操作进行中，请稍候... boss-cli 通过浏览器自动化操作，预计需要 5-15 秒
      </div>
    </div>

    <!-- ===== Section B: Position Sync ===== -->
    <div class="card">
      <div class="card-title">
        <svg viewBox="0 0 24 24" style="width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>
        岗位同步
        <span class="card-subtitle">基于 boss-cli 读取 BOSS 平台岗位</span>
      </div>
      <div class="section-toolbar">
        <button
          class="btn btn-primary btn-sm"
          :disabled="positionsLoading"
          @click="loadPositions"
          aria-label="同步 BOSS 岗位"
        >
          <span v-if="positionsLoading" class="spinner-inline"></span>
          {{ positionsLoading ? '同步中...' : '同步 BOSS 岗位' }}
        </button>
        <span class="note-text">
          <svg viewBox="0 0 24 24" style="width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
          boss-cli 目前仅支持<b>读取</b>岗位信息，不支持在 BOSS 平台创建或发布岗位
        </span>
      </div>
      <div v-if="positionsError" class="error-msg">
        {{ positionsError }}
        <button class="btn btn-text btn-sm" @click="loadPositions" aria-label="重试同步岗位">重试</button>
      </div>
      <div v-if="positionsLoading" class="slow-hint">
        <svg viewBox="0 0 24 24" style="width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        操作进行中，请稍候...
      </div>
      <div v-if="positions.length && !positionsLoading" class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>岗位名称</th>
              <th style="text-align:right">状态</th>
              <th style="text-align:right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in positions" :key="p.name">
              <td>
                <button
                  class="btn btn-text"
                  :style="{ fontWeight: 600, color: 'var(--c-primary)', textAlign: 'left' }"
                  @click="togglePositionDetail(p.name)"
                  :aria-expanded="expandedPosition === p.name ? 'true' : 'false'"
                  :aria-label="'查看 ' + p.name + ' 详情'"
                >
                  {{ p.name }}
                  <svg viewBox="0 0 24 24" style="width:12px;height:12px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round" :style="{ transform: expandedPosition === p.name ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform .2s' }"><polyline points="6 9 12 15 18 9"/></svg>
                </button>
                <!-- Expanded JD detail -->
                <div v-if="expandedPosition === p.name" class="position-detail">
                  <div v-if="positionDetails[p.name] && positionDetails[p.name].loading" class="sk-line w80" style="margin:8px 0"></div>
                  <div v-else-if="positionDetails[p.name] && positionDetails[p.name].error" class="error-msg" style="margin:8px 0">
                    {{ positionDetails[p.name].error }}
                    <button class="btn btn-text btn-sm" @click.stop="loadPositionDetail(p.name)" aria-label="重试加载岗位详情">重试</button>
                  </div>
                  <div v-else-if="positionDetails[p.name] && positionDetails[p.name].jd" class="jd-preview">
                    <div class="jd-preview-text">{{ positionDetails[p.name].jd }}</div>
                  </div>
                  <div v-else class="jd-empty">暂无 JD 信息</div>
                </div>
              </td>
              <td class="num-cell">
                <StatusBadge :type="p.status === 'open' ? 'done' : (p.status === 'pending' ? 'warn' : 'draft')">{{ positionStatusLabel(p.status) }}</StatusBadge>
              </td>
              <td class="num-cell">
                <button class="btn btn-text btn-sm" @click="togglePositionDetail(p.name)" :aria-label="'查看 ' + p.name + ' JD'">查看 JD</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div class="table-count">共 {{ positions.length }} 个岗位</div>
      </div>
      <div v-if="!positionsLoading && positions.length === 0 && positionsFetched" class="empty-state">
        <p>暂无同步的岗位数据，点击"同步 BOSS 岗位"获取</p>
      </div>
    </div>

    <!-- ===== Section C: Candidate Search ===== -->
    <div class="card">
      <div class="card-title">
        <svg viewBox="0 0 24 24" style="width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        候选人搜索
      </div>
      <div class="search-form">
        <div class="search-row">
          <div class="form-group" style="flex:1;margin-bottom:0">
            <label for="boss-search-keyword">关键字</label>
            <input
              id="boss-search-keyword"
              v-model="searchForm.keyword"
              type="text"
              placeholder="输入候选人姓名、技能或职位关键字..."
              @keydown.enter="searchCandidates"
            >
          </div>
          <div class="form-group" style="margin-bottom:0">
            <label for="boss-search-job">岗位筛选</label>
            <select id="boss-search-job" v-model="searchForm.job">
              <option value="">全部岗位</option>
              <option v-for="p in positions" :key="p.name" :value="p.name">{{ p.name }}</option>
            </select>
          </div>
          <div class="form-group" style="margin-bottom:0">
            <label for="boss-search-match">匹配度</label>
            <select id="boss-search-match" v-model="searchForm.match">
              <option value="">不限</option>
              <option value="high">高匹配</option>
              <option value="medium">中等匹配</option>
            </select>
          </div>
        </div>
        <div class="form-actions" style="margin-top:12px">
          <button
            class="btn btn-primary"
            :disabled="!searchForm.keyword.trim() || searchLoading"
            @click="searchCandidates"
            aria-label="搜索候选人"
          >
            <span v-if="searchLoading" class="spinner-inline"></span>
            {{ searchLoading ? '搜索中...' : '搜索' }}
          </button>
          <span v-if="searchLoading" class="slow-hint" style="margin:0">
            <svg viewBox="0 0 24 24" style="width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            操作进行中，请稍候...
          </span>
        </div>
      </div>
      <div v-if="searchError" class="error-msg" style="margin-top:12px">
        {{ searchError }}
        <button class="btn btn-text btn-sm" @click="searchCandidates" aria-label="重试搜索">重试</button>
      </div>
      <div v-if="candidateResults.length && !searchLoading" class="table-wrap" style="margin-top:16px">
        <table>
          <thead>
            <tr>
              <th>姓名</th>
              <th style="text-align:right">匹配度</th>
              <th style="text-align:right">当前状态</th>
              <th style="text-align:right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in candidateResults" :key="c.name || c.id">
              <td><b>{{ c.name }}</b></td>
              <td class="num-cell">
                <span :style="{ color: (c.match_score || c.match) >= 80 ? 'var(--c-done)' : ((c.match_score || c.match) >= 60 ? 'var(--c-warn)' : 'var(--c-draft)') }">
                  {{ c.match_score || c.match || '-' }}
                </span>
              </td>
              <td class="num-cell">
                <StatusBadge :type="candidateStatusType(c.status)">{{ c.status || '未知' }}</StatusBadge>
              </td>
              <td class="num-cell" style="white-space:nowrap">
                <button class="btn btn-text btn-sm" @click="handlePreviewResume(c.name)" aria-label="查看简历">查看简历</button>
                <button class="btn btn-outline btn-sm" @click="confirmGreet(c.name)" aria-label="打招呼">打招呼</button>
                <button class="btn btn-outline btn-sm" @click="openChatWith(c.name)" aria-label="聊一聊">聊一聊</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div class="table-count">共 {{ candidateResults.length }} 条结果</div>
      </div>
      <div v-if="!searchLoading && candidateResults.length === 0 && searchAttempted" class="empty-state" style="margin-top:16px">
        <p>未找到匹配的候选人，请调整搜索条件重试</p>
      </div>
      <!-- Warning -->
      <div class="warning-bar" style="margin-top:16px">
        <svg viewBox="0 0 24 24" style="width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;flex-shrink:0"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        BOSS 平台无官方聊天 API，请通过 boss-cli 辅助窗口进行人工沟通
      </div>
    </div>

    <!-- ===== Section D: Chat List ===== -->
    <div class="card">
      <div class="card-title">
        <svg viewBox="0 0 24 24" style="width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        聊天列表
      </div>
      <div class="section-toolbar">
        <div class="toolbar-left">
          <button
            class="btn btn-outline btn-sm"
            :disabled="chatListLoading"
            @click="loadChatList"
            aria-label="刷新聊天列表"
          >
            <span v-if="chatListLoading" class="spinner-inline-dark"></span>
            刷新聊天列表
          </button>
          <label class="toggle-label" style="margin-left:12px">
            <input
              type="checkbox"
              v-model="unreadOnly"
              @change="loadChatList"
              aria-label="仅显示未读"
            >
            仅显示未读
          </label>
        </div>
      </div>
      <div v-if="chatListError" class="error-msg" style="margin-top:12px">
        {{ chatListError }}
        <button class="btn btn-text btn-sm" @click="loadChatList" aria-label="重试加载聊天列表">重试</button>
      </div>
      <div v-if="chatListLoading" class="slow-hint" style="margin-bottom:0">
        <svg viewBox="0 0 24 24" style="width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        操作进行中，请稍候...
      </div>
      <div v-if="chats.length && !chatListLoading" class="table-wrap" style="margin-top:16px">
        <table>
          <thead>
            <tr>
              <th>候选人</th>
              <th style="text-align:right">未读数</th>
              <th>最近消息</th>
              <th style="text-align:right">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="ch in chats" :key="ch.name">
              <td><b>{{ ch.name }}</b></td>
              <td class="num-cell">
                <span v-if="ch.unread" class="unread-badge">{{ ch.unread }}</span>
                <span v-else style="color:var(--c-draft)">-</span>
              </td>
              <td>
                <span class="last-msg">{{ truncateText(ch.last_msg || '', 40) }}</span>
              </td>
              <td class="num-cell">
                <button class="btn btn-outline btn-sm" @click="selectChat(ch.name)" aria-label="和 {{ ch.name }} 聊天">打开对话</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div class="table-count">共 {{ chats.length }} 个对话</div>
      </div>
      <div v-if="!chatListLoading && chats.length === 0 && chatListFetched" class="empty-state" style="margin-top:16px">
        <p>暂无聊天记录</p>
      </div>

      <!-- Chat Panel -->
      <div v-if="activeChat" class="chat-panel">
        <div class="chat-panel-header">
          <div class="chat-panel-title">
            <svg viewBox="0 0 24 24" style="width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            {{ activeChat }}
          </div>
          <button class="btn btn-ghost btn-sm" @click="closeChatPanel" aria-label="关闭聊天面板">关闭</button>
        </div>
        <div class="chat-input-area">
          <textarea
            v-model="chatMessage"
            rows="3"
            placeholder="输入消息内容..."
            aria-label="聊天消息输入"
          ></textarea>
          <div class="chat-actions">
            <label class="toggle-label">
              <input
                type="checkbox"
                v-model="requestResume"
                aria-label="求简历"
              >
              求简历
            </label>
            <button
              class="btn btn-primary btn-sm"
              :disabled="!chatMessage.trim() || chatSendLoading"
              @click="handleSendMessage"
              aria-label="发送消息"
            >
              <span v-if="chatSendLoading" class="spinner-inline"></span>
              {{ chatSendLoading ? '发送中...' : '发送' }}
            </button>
          </div>
          <div v-if="chatSendError" class="error-msg" style="margin-top:8px">
            {{ chatSendError }}
          </div>
          <div v-if="chatSendLoading" class="slow-hint" style="margin-top:8px;margin-bottom:0">
            <svg viewBox="0 0 24 24" style="width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            操作进行中，请稍候...
          </div>
        </div>
      </div>

      <!-- Warning -->
      <div class="warning-bar" style="margin-top:16px">
        <svg viewBox="0 0 24 24" style="width:16px;height:16px;stroke:var(--c-warn);fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;flex-shrink:0"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
        所有沟通均为真实 BOSS 平台操作，请谨慎使用
      </div>
    </div>

    <!-- ===== Greet Confirmation Modal ===== -->
    <Teleport to="body">
      <div v-if="showGreetModal" class="modal-overlay open" @click.self="cancelGreet">
        <div class="modal-box" style="width:420px">
          <h3>
            <svg viewBox="0 0 24 24" style="width:18px;height:18px;vertical-align:-3px;stroke:var(--c-warn);fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
            确认打招呼
          </h3>
          <p style="font-size:13px;color:var(--c-body);margin:12px 0;line-height:1.8">
            即将向候选人 <b>{{ greetTarget }}</b> 发送打招呼消息。此操作会消耗 BOSS 平台的主动沟通配额，请确认后继续。
          </p>
          <div v-if="greetError" class="error-msg" style="margin-bottom:12px">{{ greetError }}</div>
          <div class="modal-actions">
            <button class="btn btn-ghost btn-sm" @click="cancelGreet" :disabled="greetingLoading">取消</button>
            <button class="btn btn-primary btn-sm" @click="executeGreet" :disabled="greetingLoading">
              <span v-if="greetingLoading" class="spinner-inline"></span>
              {{ greetingLoading ? '发送中...' : '确认发送' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import {
  fetchBossStatus,
  fetchPositions,
  fetchPositionDetail,
  searchCandidates as apiSearchCandidates,
  fetchChatList,
  openChat,
  sendMessage,
  previewResume,
  greetCandidate,
} from '../api/boss.js';

const props = defineProps({
  compact: { type: Boolean, default: false },
});

// ===== Section A: Status =====
const statusLoading = ref(false);
const statusError = ref('');
const statusState = ref('unknown'); // 'connected' | 'need_login' | 'unavailable' | 'unknown'
const statusVersion = ref('');

const statusClass = computed(() => ({
  online: statusState.value === 'connected',
  offline: statusState.value === 'need_login',
  unavailable: statusState.value === 'unavailable',
  unknown: statusState.value === 'unknown',
}));

const statusText = computed(() => {
  const map = {
    connected: '已连接',
    need_login: '需要登录',
    unavailable: '不可用',
    unknown: '未知',
  };
  return map[statusState.value] || '未知';
});

async function refreshStatus() {
  statusLoading.value = true;
  statusError.value = '';
  try {
    const { ok, data, error } = await fetchBossStatus();
    if (ok && data) {
      if (data.available) {
        statusState.value = 'connected';
      } else {
        statusState.value = 'need_login';
      }
      statusVersion.value = data.version || '';
    } else {
      statusError.value = error || '无法获取状态';
      statusState.value = 'unavailable';
    }
  } catch (e) {
    statusError.value = e.message || '连接失败';
    statusState.value = 'unavailable';
  } finally {
    statusLoading.value = false;
  }
}

function handleLogin() {
  alert('[sample] 请通过 boss-cli 终端窗口打开 BOSS 直聘页面并扫码登录。\n\n登录完成后点击"刷新状态"确认连接。');
  refreshStatus();
}

// ===== Section B: Positions =====
const positions = ref([]);
const positionsLoading = ref(false);
const positionsError = ref('');
const positionsFetched = ref(false);
const expandedPosition = ref(null);
const positionDetails = reactive({});

function positionStatusLabel(s) {
  const map = { open: '开放中', pending: '审核中', closed: '已关闭' };
  return map[s] || s || '未知';
}

async function loadPositions() {
  positionsLoading.value = true;
  positionsError.value = '';
  try {
    const { ok, data, error } = await fetchPositions();
    if (ok && data) {
      positions.value = data.positions || [];
      positionsFetched.value = true;
    } else {
      positionsError.value = error || '同步失败';
    }
  } catch (e) {
    positionsError.value = e.message || '同步失败';
  } finally {
    positionsLoading.value = false;
  }
}

async function togglePositionDetail(name) {
  if (expandedPosition.value === name) {
    expandedPosition.value = null;
    return;
  }
  expandedPosition.value = name;
  if (!positionDetails[name]) {
    positionDetails[name] = { loading: true, jd: null, error: '' };
    await loadPositionDetail(name);
  }
}

async function loadPositionDetail(name) {
  if (!positionDetails[name]) {
    positionDetails[name] = { loading: true, jd: null, error: '' };
  } else {
    positionDetails[name].loading = true;
    positionDetails[name].error = '';
  }
  try {
    const { ok, data, error } = await fetchPositionDetail(name);
    if (ok && data) {
      positionDetails[name].jd = data.jd_markdown || data.jd || '暂无 JD 详情';
    } else {
      positionDetails[name].error = error || '加载失败';
    }
  } catch (e) {
    positionDetails[name].error = e.message || '加载失败';
  } finally {
    positionDetails[name].loading = false;
  }
}

// ===== Section C: Candidate Search =====
const searchForm = reactive({
  keyword: '',
  job: '',
  core: '',
  bonus: '',
  match: '',
});
const candidateResults = ref([]);
const searchLoading = ref(false);
const searchError = ref('');
const searchAttempted = ref(false);

function candidateStatusType(s) {
  if (!s) return 'draft';
  const map = { 'active': 'done', '沟通中': 'progress', '已查看': 'progress', '新候选人': 'done' };
  return map[s] || 'draft';
}

async function searchCandidates() {
  if (!searchForm.keyword.trim()) return;
  searchLoading.value = true;
  searchError.value = '';
  searchAttempted.value = true;
  try {
    const params = { keyword: searchForm.keyword.trim() };
    if (searchForm.job) params.job = searchForm.job;
    if (searchForm.core) params.core = searchForm.core;
    if (searchForm.bonus) params.bonus = searchForm.bonus;
    if (searchForm.match) params.match = searchForm.match;

    const { ok, data, error } = await apiSearchCandidates(params);
    if (ok && data) {
      candidateResults.value = data.results || [];
    } else {
      searchError.value = error || '搜索失败';
    }
  } catch (e) {
    searchError.value = e.message || '搜索失败';
  } finally {
    searchLoading.value = false;
  }
}

async function handlePreviewResume(name) {
  try {
    const { ok, data, error } = await previewResume(name);
    if (ok) {
      alert('[sample] 简历预览:\n' + JSON.stringify(data, null, 2));
    } else {
      alert('获取简历失败: ' + (error || '未知错误'));
    }
  } catch (e) {
    alert('获取简历失败: ' + e.message);
  }
}

// ===== Greet Modal =====
const showGreetModal = ref(false);
const greetTarget = ref('');
const greetJob = ref('');
const greetingLoading = ref(false);
const greetError = ref('');

function confirmGreet(name) {
  greetTarget.value = name;
  greetError.value = '';
  showGreetModal.value = true;
}

function cancelGreet() {
  showGreetModal.value = false;
  greetTarget.value = '';
  greetJob.value = '';
  greetError.value = '';
}

async function executeGreet() {
  greetingLoading.value = true;
  greetError.value = '';
  try {
    const { ok, error } = await greetCandidate(greetTarget.value, greetJob.value || undefined);
    if (ok) {
      alert('[sample] 已向 ' + greetTarget.value + ' 发送打招呼消息');
      cancelGreet();
    } else {
      greetError.value = error || '打招呼失败';
    }
  } catch (e) {
    greetError.value = e.message || '打招呼失败';
  } finally {
    greetingLoading.value = false;
  }
}

// ===== Section D: Chat =====
const chats = ref([]);
const chatListLoading = ref(false);
const chatListError = ref('');
const chatListFetched = ref(false);
const unreadOnly = ref(false);

const activeChat = ref(null);
const chatMessage = ref('');
const requestResume = ref(false);
const chatSendLoading = ref(false);
const chatSendError = ref('');

async function loadChatList() {
  chatListLoading.value = true;
  chatListError.value = '';
  try {
    const { ok, data, error } = await fetchChatList(unreadOnly.value);
    if (ok && data) {
      chats.value = data.chats || [];
      chatListFetched.value = true;
    } else {
      chatListError.value = error || '加载失败';
    }
  } catch (e) {
    chatListError.value = e.message || '加载失败';
  } finally {
    chatListLoading.value = false;
  }
}

async function openChatWith(name) {
  try {
    const { ok, error } = await openChat(name);
    if (ok) {
      selectChat(name);
    } else {
      alert('打开对话失败: ' + (error || '未知错误'));
    }
  } catch (e) {
    alert('打开对话失败: ' + e.message);
  }
}

function selectChat(name) {
  activeChat.value = name;
  chatMessage.value = '';
  requestResume.value = false;
  chatSendError.value = '';
}

function closeChatPanel() {
  activeChat.value = null;
  chatMessage.value = '';
  requestResume.value = false;
}

async function handleSendMessage() {
  if (!chatMessage.value.trim() || !activeChat.value) return;
  chatSendLoading.value = true;
  chatSendError.value = '';
  try {
    const { ok, error } = await sendMessage(chatMessage.value.trim(), requestResume.value);
    if (ok) {
      chatMessage.value = '';
      alert('[sample] 消息已发送');
    } else {
      chatSendError.value = error || '发送失败';
    }
  } catch (e) {
    chatSendError.value = e.message || '发送失败';
  } finally {
    chatSendLoading.value = false;
  }
}

// ===== Shared Utilities =====
function truncateText(text, max) {
  if (!text) return '';
  return text.length > max ? text.slice(0, max) + '...' : text;
}

// Auto-refresh status on mount
onMounted(() => {
  refreshStatus();
});
</script>

<style scoped>
/* ===== Container ===== */
.boss-integration {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.boss-integration.compact .card {
  padding: 16px;
}

.boss-integration.compact .card-title {
  font-size: 14px;
  margin-bottom: 12px;
}

/* ===== Card ===== */
.card {
  background: var(--c-card);
  border-radius: var(--radius);
  padding: 20px;
  border: 1px solid var(--c-border);
}

.card-title {
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 14px;
  color: var(--c-text);
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-title svg {
  stroke: var(--c-primary);
}

.card-subtitle {
  font-size: 11px;
  font-weight: 400;
  color: var(--c-sub);
  margin-left: 8px;
}

/* ===== Section A: Status ===== */
.status-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.status-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--c-draft);
}

.status-dot.online {
  background: var(--c-done);
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.15);
}

.status-dot.offline {
  background: var(--c-warn);
  box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.15);
}

.status-dot.unavailable {
  background: var(--c-draft);
}

.status-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--c-text);
}

.status-version {
  font-size: 11px;
  color: var(--c-sub);
  background: var(--c-surface-elevated);
  padding: 1px 8px;
  border-radius: 4px;
}

.status-actions {
  display: flex;
  gap: 8px;
}

/* ===== Section Toolbar ===== */
.section-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.note-text {
  font-size: 12px;
  color: var(--c-sub);
  display: flex;
  align-items: center;
  gap: 4px;
}

.note-text svg {
  stroke: var(--c-warn);
}

/* ===== Search Form ===== */
.search-form {
  margin-bottom: 4px;
}

.search-row {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  flex-wrap: wrap;
}

.search-row .form-group {
  margin-bottom: 0;
}

.search-row .form-group input,
.search-row .form-group select {
  padding: 8px 12px;
  border: 1px solid var(--c-border);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-family: inherit;
  background: var(--c-card);
  color: var(--c-body);
  transition: border-color .15s;
  min-width: 140px;
  box-sizing: border-box;
}

.search-row .form-group input:focus,
.search-row .form-group select:focus {
  outline: none;
  border-color: var(--c-primary);
}

/* ===== Position Detail ===== */
.position-detail {
  padding: 12px 0 4px;
}

.jd-preview {
  background: var(--c-surface-elevated);
  border: 1px solid var(--c-border-light);
  border-radius: var(--radius-sm);
  padding: 12px;
  margin-top: 8px;
}

.jd-preview-text {
  font-size: 13px;
  color: var(--c-body);
  line-height: 1.8;
  white-space: pre-wrap;
  max-height: 200px;
  overflow-y: auto;
}

.jd-empty {
  font-size: 12px;
  color: var(--c-sub);
  padding: 8px 0;
}

/* ===== Chat Panel ===== */
.chat-panel {
  margin-top: 16px;
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  overflow: hidden;
}

.chat-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--c-surface-elevated);
  border-bottom: 1px solid var(--c-border);
}

.chat-panel-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--c-text);
  display: flex;
  align-items: center;
  gap: 8px;
}

.chat-panel-title svg {
  stroke: var(--c-primary);
}

.chat-input-area {
  padding: 12px 16px;
}

.chat-input-area textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--c-border);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-family: inherit;
  box-sizing: border-box;
  resize: vertical;
  color: var(--c-text);
  background: var(--c-card);
  transition: border-color .15s;
}

.chat-input-area textarea:focus {
  outline: none;
  border-color: var(--c-primary);
}

.chat-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 10px;
}

/* ===== Unread Badge ===== */
.unread-badge {
  display: inline-block;
  min-width: 20px;
  padding: 1px 6px;
  background: var(--c-reject);
  color: #fff;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 700;
  text-align: center;
  font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum";
}

/* ===== Last Message ===== */
.last-msg {
  font-size: 13px;
  color: var(--c-sub);
}

/* ===== Shared States ===== */
.error-msg {
  color: var(--c-reject);
  font-size: 13px;
  padding: 8px 0;
}

.empty-state {
  text-align: center;
  padding: 32px 20px;
}

.empty-state p {
  color: var(--c-sub);
  font-size: 14px;
}

.slow-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--c-sub);
  background: var(--c-surface-elevated);
  border: 1px solid var(--c-border);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  margin-bottom: 12px;
  margin-top: 8px;
}

.slow-hint svg {
  stroke: var(--c-primary);
  flex-shrink: 0;
}

.warning-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--c-warn);
  background: #FFFBF5;
  border: 1px solid #FEE9CC;
  border-radius: var(--radius-sm);
  padding: 10px 14px;
  line-height: 1.6;
}

/* ===== Toggle ===== */
.toggle-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--c-body);
  cursor: pointer;
  user-select: none;
}

.toggle-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: var(--c-primary);
  cursor: pointer;
}

/* ===== Table cells ===== */
.num-cell {
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum";
}

/* ===== Skeleton ===== */
.sk-line {
  height: 14px;
  background: var(--c-border-light);
  border-radius: 4px;
  animation: boss-pulse 1.5s ease-in-out infinite;
}

.w80 { width: 80%; }

@keyframes boss-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: .4; }
}

/* ===== Spinner ===== */
.spinner-inline {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: boss-spin .6s linear infinite;
  margin-right: 4px;
}

.spinner-inline-dark {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid var(--c-border);
  border-top-color: var(--c-primary);
  border-radius: 50%;
  animation: boss-spin .6s linear infinite;
  margin-right: 4px;
}

@keyframes boss-spin {
  to { transform: rotate(360deg); }
}

/* ===== Modal ===== */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-overlay.open {
  opacity: 1;
  visibility: visible;
}

.modal-box {
  background: var(--c-card);
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-modal);
  border: 1px solid var(--c-border);
}

.modal-box h3 {
  font-size: 15px;
  font-weight: 700;
  color: var(--c-text);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.modal-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

/* ===== Reduce motion ===== */
@media (prefers-reduced-motion: reduce) {
  .spinner-inline,
  .spinner-inline-dark {
    animation: none;
  }
  .sk-line {
    animation: none;
  }
}
</style>
