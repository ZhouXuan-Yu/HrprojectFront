<template>
  <WorkbenchLayout title="招聘辅助中心" :breadcrumb="{ text: '招聘管理', href: '/recruit-dashboard' }">
    <div class="permission-bar">
      本页面仅<b>系统管理员</b>可见 · 集中所有<b>用户主动发起</b>的招聘辅助能力 · 流程内嵌的简历解析、匹配评分、联系话术辅助已嵌入各业务页面
    </div>

    <!-- 6 Tab navigation -->
    <div class="tabs" role="tablist" aria-label="招聘辅助功能">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="tab"
        :class="{ active: activeTab === tab.id }"
        :aria-selected="activeTab === tab.id ? 'true' : 'false'"
        role="tab"
        @click="activeTab = tab.id"
      >{{ tab.number }} {{ tab.title }}</button>
    </div>

    <!-- Tab panels -->
    <div class="tab-panels">
      <!-- Tab 1: JD 草稿生成 -->
      <div class="tab-panel" :class="{ active: activeTab === 'jd' }" role="tabpanel" aria-label="JD 草稿生成">
        <h3 class="panel-title">JD 草稿生成</h3>
        <div class="ai-card">
          <div class="card-title">
            <svg viewBox="0 0 24 24" style="width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
            生成新 JD 草稿
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="jd-position">岗位名称 *</label>
              <input id="jd-position" v-model="jdForm.position" type="text" placeholder="例如：高级Java工程师">
            </div>
            <div class="form-group">
              <label for="jd-dept">部门 *</label>
              <select id="jd-dept" v-model="jdForm.department">
                <option value="">请选择部门</option>
                <option v-for="d in departments" :key="d" :value="d">{{ d }}</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label for="jd-level">职级</label>
            <div class="radio-row">
              <label v-for="lv in levels" :key="lv" class="radio-chip" :class="{ active: jdForm.level === lv }">
                <input type="radio" v-model="jdForm.level" :value="lv" class="sr-only">
                {{ lv }}
              </label>
            </div>
          </div>
          <div class="form-group">
            <label for="jd-reqs">核心要求</label>
            <textarea id="jd-reqs" v-model="jdForm.requirements" rows="4" placeholder="描述岗位核心要求，例如：5年Java经验、大厂背景、熟悉微服务架构、有团队管理经验..."></textarea>
          </div>
          <div class="form-actions">
            <button class="btn btn-primary" :disabled="!jdForm.position || !jdForm.department || jdLoading" @click="generateJd" aria-label="生成JD草稿">
              <span v-if="jdLoading" class="spinner-inline"></span>
              {{ jdLoading ? '生成中...' : '生成 JD' }}
            </button>
          </div>
        </div>

        <!-- JD Result -->
        <div v-if="jdError" class="ai-card error-state">
          <div class="error-msg">{{ jdError }}</div>
          <button class="btn btn-outline btn-sm" @click="generateJd" aria-label="重试生成JD">重试</button>
        </div>

        <div v-if="jdLoading && !jdResult" class="ai-card skeleton" aria-busy="true">
          <div class="sk-line w60"></div><div class="sk-line w80"></div><div class="sk-line w100"></div><div class="sk-line w70"></div><div class="sk-line w90"></div>
        </div>

        <div v-if="jdResult && !jdLoading" class="ai-card jd-result">
          <div class="jd-header">
            <h4>{{ jdResult.position }}</h4>
            <span class="jd-dept">{{ jdResult.department }}</span>
          </div>
          <div class="jd-section">
            <div class="jd-section-title">岗位职责</div>
            <ol class="jd-list">
              <li v-for="(r, i) in jdResult.responsibilities" :key="'r'+i">{{ r }}</li>
            </ol>
          </div>
          <div class="jd-section">
            <div class="jd-section-title">必备技能</div>
            <div class="skill-table">
              <div v-for="s in jdResult.required_skills" :key="s.name" class="skill-row">
                <span class="skill-name">{{ s.name }}</span>
                <StatusBadge :type="s.weight === '必须' ? 'done' : 'progress'">{{ s.weight }}</StatusBadge>
                <span class="skill-desc">{{ s.description }}</span>
              </div>
            </div>
          </div>
          <div v-if="jdResult.plus_skills && jdResult.plus_skills.length" class="jd-section">
            <div class="jd-section-title">加分项</div>
            <ul class="jd-list">
              <li v-for="s in jdResult.plus_skills" :key="s.name">{{ s.name }} — {{ s.description }}</li>
            </ul>
          </div>
          <div class="jd-section">
            <div class="jd-section-title">任职资格</div>
            <div class="info-grid">
              <div v-for="(v, k) in jdResult.qualifications" :key="k" class="info-item">
                <span class="info-label">{{ qualLabels[k] || k }}</span>
                <span class="info-value">{{ v }}</span>
              </div>
            </div>
          </div>
          <div class="form-actions" style="margin-top:16px">
            <button class="btn btn-outline btn-sm" @click="copyText(jdResult)" aria-label="复制JD内容">复制</button>
            <button class="btn btn-ghost btn-sm" @click="generateJd" :disabled="jdLoading" aria-label="重新生成JD">重新生成</button>
          </div>
          <div class="disclaimer-bar">{{ jdResult.disclaimer }}</div>
        </div>
      </div>

      <!-- Tab 2: 语义简历搜索 -->
      <div class="tab-panel" :class="{ active: activeTab === 'search' }" role="tabpanel" aria-label="语义简历搜索">
        <h3 class="panel-title">语义简历搜索</h3>
        <div class="ai-card">
          <div class="card-title">
            <svg viewBox="0 0 24 24" style="width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            语义搜索简历
          </div>
          <div class="search-box">
            <textarea
              id="search-query"
              v-model="searchQuery"
              rows="3"
              placeholder="描述你想要的候选人，例如：5年Java 大厂背景 做过微服务架构 熟悉K8s..."
              @keydown.ctrl.enter="searchResume"
              aria-label="搜索描述"
            ></textarea>
            <div class="form-actions">
              <button class="btn btn-primary" :disabled="!searchQuery.trim() || searchLoading" @click="searchResume" aria-label="开始搜索">
                <span v-if="searchLoading" class="spinner-inline"></span>
                {{ searchLoading ? '搜索中...' : '搜索' }}
              </button>
              <span class="input-hint">Ctrl + Enter 快速搜索</span>
            </div>
          </div>
        </div>

        <div v-if="searchError" class="ai-card error-state">
          <div class="error-msg">{{ searchError }}</div>
          <button class="btn btn-outline btn-sm" @click="searchResume" aria-label="重试搜索">重试</button>
        </div>

        <div v-if="searchLoading && !searchResults.length" class="ai-card skeleton" aria-busy="true">
          <div class="sk-line w100"></div><div class="sk-line w80"></div><div class="sk-line w60"></div>
        </div>

        <div v-if="searchResults.length && !searchLoading" class="ai-card">
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>姓名</th>
                  <th style="text-align:right">画像分</th>
                  <th style="text-align:right">匹配度</th>
                  <th>匹配理由</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in searchResults" :key="r.id">
                  <td><b>{{ r.name }}</b></td>
                  <td class="num-cell">{{ r.portraitScore }}</td>
                  <td class="num-cell">
                    <span :style="{ color: r.matchScore >= 90 ? 'var(--c-done)' : r.matchScore >= 75 ? 'var(--c-warn)' : 'var(--c-draft)' }">{{ r.matchScore }}</span>
                  </td>
                  <td>
                    <div class="reason-tags">
                      <span v-for="(m, mi) in r.match_reasons" :key="mi" class="reason-tag">{{ m }}</span>
                    </div>
                  </td>
                  <td>
                    <button class="btn btn-text btn-sm" @click="viewResume(r.id)" aria-label="查看简历">查看简历</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-if="!searchLoading && searchResults.length === 0 && searchQuery && searchAttempted" class="ai-card empty-state">
          <div class="empty-icon">
            <svg viewBox="0 0 24 24" style="width:32px;height:32px;stroke:var(--c-sub);fill:none;stroke-width:1.5;stroke-linecap:round;stroke-linejoin:round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          </div>
          <p>未找到匹配的候选人，尝试调整搜索描述</p>
        </div>
      </div>

      <!-- Tab 3: 人岗匹配工作台 -->
      <div class="tab-panel" :class="{ active: activeTab === 'match' }" role="tabpanel" aria-label="人岗匹配工作台">
        <h3 class="panel-title">人岗匹配工作台</h3>
        <div class="ai-card">
          <div class="card-title">
            <svg viewBox="0 0 24 24" style="width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            人岗匹配
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="match-candidate">候选人</label>
              <select id="match-candidate" v-model="matchForm.candidateId">
                <option value="">请选择候选人</option>
                <option v-for="c in candidates" :key="c.id" :value="c.id">{{ c.name }} — {{ c.title }}</option>
              </select>
            </div>
            <div class="form-group">
              <label for="match-demand">岗位/需求</label>
              <select id="match-demand" v-model="matchForm.demandId">
                <option value="">请选择岗位</option>
                <option v-for="d in demands" :key="d.id" :value="d.id">{{ d.name }} · {{ d.dept }}</option>
              </select>
            </div>
          </div>
          <div class="form-actions">
            <button class="btn btn-primary" :disabled="!matchForm.candidateId || !matchForm.demandId || matchLoading" @click="runMatch" aria-label="开始匹配">
              <span v-if="matchLoading" class="spinner-inline"></span>
              {{ matchLoading ? '匹配中...' : '开始匹配' }}
            </button>
          </div>
        </div>

        <div v-if="matchError" class="ai-card error-state">
          <div class="error-msg">{{ matchError }}</div>
          <button class="btn btn-outline btn-sm" @click="runMatch" aria-label="重试匹配">重试</button>
        </div>

        <div v-if="matchLoading && !matchResult" class="ai-card skeleton" aria-busy="true">
          <div class="sk-kpi"></div><div class="sk-line w80"></div><div class="sk-line w60"></div><div class="sk-line w100"></div>
        </div>

        <div v-if="matchResult && !matchLoading" class="ai-card">
          <div class="match-score-area">
            <div class="match-big-score">
              <span class="match-score-num">{{ matchResult.overall_score }}</span>
              <span class="match-score-label">综合匹配得分</span>
            </div>
            <div class="match-breakdown">
              <div class="breakdown-item">
                <span class="breakdown-label">画像分</span>
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: matchResult.profile_score + '%' }"></div>
                </div>
                <span class="breakdown-val">{{ matchResult.profile_score }}</span>
              </div>
              <div class="breakdown-item">
                <span class="breakdown-label">匹配分</span>
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: matchResult.match_score + '%' }"></div>
                </div>
                <span class="breakdown-val">{{ matchResult.match_score }}</span>
              </div>
              <div class="breakdown-item">
                <span class="breakdown-label">综合等级</span>
                <StatusBadge :type="matchResult.grade === 'A' ? 'done' : matchResult.grade === 'B' ? 'progress' : 'warn'">{{ matchResult.grade }} 级</StatusBadge>
              </div>
            </div>
          </div>

          <div class="jd-section">
            <div class="jd-section-title">匹配优势</div>
            <ul class="jd-list">
              <li v-for="(s, i) in matchResult.strengths" :key="'s'+i">{{ s }}</li>
            </ul>
          </div>

          <div v-if="matchResult.missing_skills && matchResult.missing_skills.length" class="jd-section">
            <div class="jd-section-title">待补足技能</div>
            <div class="skill-table">
              <div v-for="ms in matchResult.missing_skills" :key="ms.skill" class="skill-row">
                <span class="skill-name">{{ ms.skill }}</span>
                <StatusBadge :type="ms.importance === '加分项' ? 'draft' : 'warn'">{{ ms.importance }}</StatusBadge>
                <span class="skill-desc">{{ ms.note }}</span>
              </div>
            </div>
          </div>

          <div class="jd-section">
            <div class="jd-section-title">详细理由</div>
            <ul class="jd-list">
              <li v-for="(r, i) in matchResult.reasons" :key="'mr'+i">{{ r }}</li>
            </ul>
          </div>

          <div class="disclaimer-bar">{{ matchResult.disclaimer }}</div>
        </div>
      </div>

      <!-- Tab 4: 面试辅助 -->
      <div class="tab-panel" :class="{ active: activeTab === 'interview' }" role="tabpanel" aria-label="面试辅助">
        <h3 class="panel-title">面试辅助</h3>
        <div class="ai-card">
          <div class="card-title">
            <svg viewBox="0 0 24 24" style="width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            生成面试问题
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="iv-candidate">候选人</label>
              <select id="iv-candidate" v-model="interviewForm.candidateId">
                <option value="">请选择候选人</option>
                <option v-for="c in candidates" :key="c.id" :value="c.id">{{ c.name }} — {{ c.title }}</option>
              </select>
            </div>
            <div class="form-group">
              <label for="iv-demand">岗位</label>
              <select id="iv-demand" v-model="interviewForm.demandId">
                <option value="">请选择岗位</option>
                <option v-for="d in demands" :key="d.id" :value="d.id">{{ d.name }} · {{ d.dept }}</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label for="iv-round">面试轮次</label>
            <div class="radio-row">
              <label v-for="rnd in interviewRounds" :key="rnd.value" class="radio-chip" :class="{ active: interviewForm.round === rnd.value }">
                <input type="radio" v-model="interviewForm.round" :value="rnd.value" class="sr-only">
                {{ rnd.label }}
              </label>
            </div>
          </div>
          <div class="form-actions">
            <button class="btn btn-primary" :disabled="!interviewForm.candidateId || !interviewForm.demandId || interviewLoading" @click="generateQuestions" aria-label="生成面试问题">
              <span v-if="interviewLoading" class="spinner-inline"></span>
              {{ interviewLoading ? '生成中...' : '生成面试问题' }}
            </button>
          </div>
        </div>

        <div v-if="interviewError" class="ai-card error-state">
          <div class="error-msg">{{ interviewError }}</div>
          <button class="btn btn-outline btn-sm" @click="generateQuestions" aria-label="重试生成面试问题">重试</button>
        </div>

        <div v-if="interviewLoading && !interviewQuestions.length" class="ai-card skeleton" aria-busy="true">
          <div class="sk-line w100"></div><div class="sk-line w80"></div><div class="sk-line w60"></div><div class="sk-line w90"></div>
        </div>

        <div v-if="interviewQuestions.length && !interviewLoading" class="ai-card">
          <div class="form-actions" style="margin-bottom:16px">
            <button class="btn btn-outline btn-sm" @click="copyQuestions" aria-label="复制全部问题">复制全部</button>
          </div>
          <ol class="question-list">
            <li v-for="(q, qi) in interviewQuestions" :key="qi" class="question-item">
              <div class="question-text">{{ q.question }}</div>
              <div class="question-meta">
                <StatusBadge type="progress">{{ q.dimension }}</StatusBadge>
                <button class="btn btn-text btn-sm" @click="toggleHint(qi)" :aria-expanded="expandedHints[qi] ? 'true' : 'false'" :aria-label="expandedHints[qi] ? '收起回答提示' : '展开回答提示'">
                  {{ expandedHints[qi] ? '收起提示' : '回答提示' }}
                  <svg viewBox="0 0 24 24" style="width:12px;height:12px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round" :style="{ transform: expandedHints[qi] ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform .2s' }"><polyline points="6 9 12 15 18 9"/></svg>
                </button>
              </div>
              <div v-if="expandedHints[qi]" class="hint-box">{{ q.expected_answer_hints }}</div>
            </li>
          </ol>
          <div class="disclaimer-bar">{{ interviewDisclaimer }}</div>
        </div>
      </div>

      <!-- Tab 5: 招聘深度报表 -->
      <div class="tab-panel" :class="{ active: activeTab === 'report' }" role="tabpanel" aria-label="招聘深度报表">
        <h3 class="panel-title">招聘深度报表</h3>
        <div class="ai-card">
          <div class="card-title">
            <svg viewBox="0 0 24 24" style="width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
            生成分析报告
          </div>
          <div class="form-group">
            <label for="report-type">报告类型</label>
            <select id="report-type" v-model="reportForm.type">
              <option v-for="rt in reportTypes" :key="rt.value" :value="rt.value">{{ rt.label }}</option>
            </select>
          </div>
          <div class="form-actions">
            <button class="btn btn-primary" :disabled="reportLoading" @click="generateReport" aria-label="生成分析报告">
              <span v-if="reportLoading" class="spinner-inline"></span>
              {{ reportLoading ? '生成中...' : '生成分析报告' }}
            </button>
          </div>
        </div>

        <div v-if="reportError" class="ai-card error-state">
          <div class="error-msg">{{ reportError }}</div>
          <button class="btn btn-outline btn-sm" @click="generateReport" aria-label="重试生成报告">重试</button>
        </div>

        <div v-if="reportLoading && !reportResult" class="ai-card skeleton" aria-busy="true">
          <div class="sk-line w100"></div><div class="sk-line w60"></div><div class="sk-line w80"></div><div class="sk-line w90"></div><div class="sk-line w70"></div>
        </div>

        <div v-if="reportResult && !reportLoading" class="ai-card">
          <div class="jd-section">
            <div class="jd-section-title">综合分析</div>
            <p class="report-summary">{{ reportResult.summary }}</p>
          </div>

          <div class="jd-section">
            <div class="jd-section-title">关键洞察</div>
            <ul class="jd-list">
              <li v-for="(ins, i) in reportResult.insights" :key="'ins'+i">{{ ins }}</li>
            </ul>
          </div>

          <div v-if="reportResult.anomalies && reportResult.anomalies.length" class="jd-section">
            <div class="jd-section-title">异常标注</div>
            <ul class="jd-list anomaly-list">
              <li v-for="(a, i) in reportResult.anomalies" :key="'an'+i">{{ a }}</li>
            </ul>
          </div>

          <div class="jd-section">
            <div class="jd-section-title">改进建议</div>
            <ul class="jd-list">
              <li v-for="(r, i) in reportResult.recommendations" :key="'rc'+i">{{ r }}</li>
            </ul>
          </div>

          <div class="form-actions" style="margin-top:16px">
            <button class="btn btn-outline btn-sm" @click="copyReport" aria-label="复制报告内容">复制报告</button>
            <button class="btn btn-ghost btn-sm" @click="generateReport" :disabled="reportLoading" aria-label="重新生成报告">重新生成</button>
          </div>
          <div class="disclaimer-bar">{{ reportResult.disclaimer }}</div>
        </div>
      </div>

      <!-- Tab 6: 候选人沟通助手 -->
      <div class="tab-panel" :class="{ active: activeTab === 'chat' }" role="tabpanel" aria-label="候选人沟通助手">
        <h3 class="panel-title">候选人沟通助手</h3>
        <div class="ai-card">
          <div class="card-title">
            <svg viewBox="0 0 24 24" style="width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round"><path d="M14 9a2 2 0 0 1-2 2H6l-4 4V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2z"/><path d="M18 9h2a2 2 0 0 1 2 2v11l-4-4h-6a2 2 0 0 1-2-2v-1"/></svg>
            生成沟通话术
          </div>
          <div class="form-row">
            <div class="form-group">
              <label for="chat-candidate">候选人</label>
              <select id="chat-candidate" v-model="chatForm.candidateId">
                <option value="">请选择候选人</option>
                <option v-for="c in candidates" :key="c.id" :value="c.id">{{ c.name }} — {{ c.title }}</option>
              </select>
            </div>
            <div class="form-group">
              <label for="chat-channel">沟通渠道</label>
              <select id="chat-channel" v-model="chatForm.channel">
                <option value="">请选择渠道</option>
                <option value="phone">电话</option>
                <option value="email">邮件</option>
                <option value="feishu">飞书</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label for="chat-purpose">沟通目的</label>
            <div class="radio-row">
              <label v-for="p in purposes" :key="p.value" class="radio-chip" :class="{ active: chatForm.purpose === p.value }">
                <input type="radio" v-model="chatForm.purpose" :value="p.value" class="sr-only">
                {{ p.label }}
              </label>
            </div>
          </div>
          <div class="form-group">
            <label for="chat-context">补充背景（选填）</label>
            <textarea id="chat-context" v-model="chatForm.context" rows="3" placeholder="可补充特殊说明，例如：候选人希望了解技术团队规模、项目方向等信息..."></textarea>
          </div>
          <div class="form-actions">
            <button class="btn btn-primary" :disabled="!chatForm.candidateId || !chatForm.channel || !chatForm.purpose || chatLoading" @click="generateDraft" aria-label="生成沟通话术">
              <span v-if="chatLoading" class="spinner-inline"></span>
              {{ chatLoading ? '生成中...' : '生成沟通话术' }}
            </button>
          </div>
        </div>

        <div v-if="chatError" class="ai-card error-state">
          <div class="error-msg">{{ chatError }}</div>
          <button class="btn btn-outline btn-sm" @click="generateDraft" aria-label="重试生成话术">重试</button>
        </div>

        <div v-if="chatLoading && !chatResult" class="ai-card skeleton" aria-busy="true">
          <div class="sk-line w100"></div><div class="sk-line w80"></div><div class="sk-line w60"></div><div class="sk-line w90"></div>
        </div>

        <div v-if="chatResult && !chatLoading" class="ai-card">
          <div class="jd-section">
            <div class="jd-section-title">话术草稿</div>
            <div class="draft-text" style="white-space:pre-wrap;line-height:1.8;">{{ chatResult.draft }}</div>
          </div>

          <div v-if="chatResult.suggestions && chatResult.suggestions.length" class="jd-section">
            <div class="jd-section-title">沟通建议</div>
            <ul class="jd-list">
              <li v-for="(s, si) in chatResult.suggestions" :key="'sg'+si">{{ s }}</li>
            </ul>
          </div>

          <div class="form-actions" style="margin-top:16px">
            <button class="btn btn-outline btn-sm" @click="copyText(chatResult)" aria-label="复制话术内容">复制话术</button>
            <button class="btn btn-ghost btn-sm" @click="generateDraft" :disabled="chatLoading" aria-label="重新生成话术">重新生成</button>
          </div>
          <div class="disclaimer-bar">{{ chatResult.disclaimer }}</div>
        </div>
      </div>
    </div>

    <!-- BOSS 直聘集成 -->
    <div class="card" style="margin-top:24px">
      <div class="card-title">
        <svg viewBox="0 0 24 24" style="width:18px;height:18px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
        BOSS 直聘集成
        <span class="card-subtitle">基于 boss-cli 浏览器自动化</span>
      </div>
      <BossIntegration :compact="true" />
    </div>

    <!-- Embedded AI capabilities table -->
    <div style="margin-top:32px">
      <div class="section-label" style="font-size:14px;margin-bottom:12px">已嵌入各业务页面的辅助能力（流程内触发，不在此页面操作）</div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>辅助能力</th><th>所属页面</th><th>触发方式</th><th>Dify 工作流</th><th>状态</th></tr>
          </thead>
          <tbody>
            <tr v-for="(item, i) in embeddedAI" :key="i">
              <td v-html="item.ability"></td>
              <td>{{ item.page }}</td>
              <td>{{ item.trigger }}</td>
              <td>{{ item.workflow }}</td>
              <td><StatusBadge :type="item.status">{{ statusLabel(item.status) }}</StatusBadge></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- API architecture info -->
    <div class="permission-bar" style="margin-top:20px">
      <b>API 调用规则</b>：所有 AI 能力统一走 <b>后端代理转发</b>（前端 -> Flask 后端 -> Dify），前端不直连 Dify。<br>
      <b>三个 Dify 工作流底座</b>： 简历画像解析 ·  人岗匹配打分 ·  面试问题生成 + 未来新增候选人沟通 / JD生成 / Offer / 入职<br>
      <b>数据存储</b>：解析结果 -> <code>t_hr_resume</code> · 匹配分 -> <code>t_hr_resume_match</code> · 画像标签 -> <code>t_hr_candidate</code> + <code>t_hr_candidate_tag_rel</code><br>
      <b>远期辅助能力</b>：支持生成 Offer、入职包和会议安排草稿，关键动作必须经过人工确认
    </div>
  </WorkbenchLayout>
</template>

<script setup>
import { ref, reactive, computed } from 'vue';
import WorkbenchLayout from '../layouts/WorkbenchLayout.vue';
import StatusBadge from '../components/StatusBadge.vue';
import BossIntegration from '../components/BossIntegration.vue';
import { AI_TABS, EMBEDDED_AI, MOCK_CANDIDATES, MOCK_DEMANDS, MOCK_DEPARTMENTS } from '../data/ai.js';
import {
  runJdGenerate, runResumeSearch, runMatch as apiRunMatch,
  runInterviewQuestions, runCommunicationDraft, runReportAnalysis,
} from '../api/ai.js';

// --- Shared data ---
const tabs = AI_TABS;
const activeTab = ref('jd');
const embeddedAI = ref(EMBEDDED_AI);
const candidates = MOCK_CANDIDATES;
const demands = MOCK_DEMANDS;
const departments = MOCK_DEPARTMENTS;

// --- Tab 1: JD ---
const levels = ['初级', '中级', '高级', '资深', '专家'];
const jdForm = reactive({ position: '', department: '', level: '高级', requirements: '' });
const jdResult = ref(null);
const jdLoading = ref(false);
const jdError = ref('');

const qualLabels = { education: '学历', experience: '经验', industry: '行业', soft: '软技能' };

async function generateJd() {
  if (!jdForm.position || !jdForm.department) return;
  jdError.value = '';
  jdLoading.value = true;
  try {
    const result = await runJdGenerate({ ...jdForm });
    jdResult.value = result;
  } catch (e) {
    jdError.value = e.message || '生成失败，请重试';
  } finally {
    jdLoading.value = false;
  }
}

// --- Tab 2: Search ---
const searchQuery = ref('');
const searchResults = ref([]);
const searchLoading = ref(false);
const searchError = ref('');
const searchAttempted = ref(false);

async function searchResume() {
  if (!searchQuery.value.trim()) return;
  searchError.value = '';
  searchLoading.value = true;
  searchAttempted.value = true;
  try {
    const result = await runResumeSearch({ query: searchQuery.value, limit: 10 });
    searchResults.value = result.results || [];
  } catch (e) {
    searchError.value = e.message || '搜索失败，请重试';
  } finally {
    searchLoading.value = false;
  }
}

function viewResume(id) {
  alert('[sample] 查看简历: ' + id);
}

// --- Tab 3: Match ---
const matchForm = reactive({ candidateId: '', demandId: '' });
const matchResult = ref(null);
const matchLoading = ref(false);
const matchError = ref('');

async function runMatch() {
  if (!matchForm.candidateId || !matchForm.demandId) return;
  matchError.value = '';
  matchLoading.value = true;
  try {
    const result = await apiRunMatch({ candidate_id: matchForm.candidateId, demand_id: matchForm.demandId });
    matchResult.value = result;
  } catch (e) {
    matchError.value = e.message || '匹配失败，请重试';
  } finally {
    matchLoading.value = false;
  }
}

// --- Tab 4: Interview ---
const interviewRounds = [
  { value: 'first', label: '初试' },
  { value: 'second', label: '复试' },
  { value: 'final', label: '终面' },
];
const interviewForm = reactive({ candidateId: '', demandId: '', round: 'first' });
const interviewQuestions = ref([]);
const interviewDisclaimer = ref('');
const interviewLoading = ref(false);
const interviewError = ref('');
const expandedHints = ref({});

async function generateQuestions() {
  if (!interviewForm.candidateId || !interviewForm.demandId) return;
  interviewError.value = '';
  interviewLoading.value = true;
  try {
    const result = await runInterviewQuestions({
      candidate_id: interviewForm.candidateId,
      demand_id: interviewForm.demandId,
      round: interviewForm.round,
    });
    interviewQuestions.value = result.questions || [];
    interviewDisclaimer.value = result.disclaimer || '';
    expandedHints.value = {};
  } catch (e) {
    interviewError.value = e.message || '生成失败，请重试';
  } finally {
    interviewLoading.value = false;
  }
}

function toggleHint(index) {
  expandedHints.value = { ...expandedHints.value, [index]: !expandedHints.value[index] };
}

function copyQuestions() {
  const text = interviewQuestions.value.map((q, i) => `${i + 1}. ${q.question}\n   维度: ${q.dimension}\n   提示: ${q.expected_answer_hints}`).join('\n\n');
  copyToClipboard(text);
}

// --- Tab 5: Report ---
const reportTypes = [
  { value: 'funnel', label: '招聘漏斗' },
  { value: 'channel', label: '渠道效果' },
  { value: 'cycle', label: '招聘周期' },
  { value: 'offer', label: 'Offer分析' },
  { value: 'interviewer', label: '面试官统计' },
];
const reportForm = reactive({ type: 'funnel' });
const reportResult = ref(null);
const reportLoading = ref(false);
const reportError = ref('');

async function generateReport() {
  reportError.value = '';
  reportLoading.value = true;
  try {
    const result = await runReportAnalysis({ type: reportForm.type, params: {} });
    reportResult.value = result;
  } catch (e) {
    reportError.value = e.message || '报告生成失败，请重试';
  } finally {
    reportLoading.value = false;
  }
}

function copyReport() {
  const r = reportResult.value;
  const text = [
    '综合分析',
    r.summary,
    '',
    '关键洞察',
    ...r.insights.map((s, i) => `${i + 1}. ${s}`),
    '',
    '异常标注',
    ...(r.anomalies || []).map((s, i) => `${i + 1}. ${s}`),
    '',
    '改进建议',
    ...r.recommendations.map((s, i) => `${i + 1}. ${s}`),
  ].join('\n');
  copyToClipboard(text);
}

// --- Tab 6: Communication ---
const purposes = [
  { value: 'first_contact', label: '初次联系' },
  { value: 'interview_invite', label: '面试邀请' },
  { value: 'offer_notice', label: 'Offer通知' },
  { value: 'follow_up', label: '跟进' },
];
const chatForm = reactive({ candidateId: '', channel: '', purpose: '', context: '' });
const chatResult = ref(null);
const chatLoading = ref(false);
const chatError = ref('');

async function generateDraft() {
  if (!chatForm.candidateId || !chatForm.channel || !chatForm.purpose) return;
  chatError.value = '';
  chatLoading.value = true;
  try {
    const candidate = candidates.find(c => c.id === chatForm.candidateId);
    const result = await runCommunicationDraft({
      candidate_name: candidate?.name || '',
      channel: chatForm.channel,
      purpose: chatForm.purpose,
      context: chatForm.context,
    });
    chatResult.value = result;
  } catch (e) {
    chatError.value = e.message || '话术生成失败，请重试';
  } finally {
    chatLoading.value = false;
  }
}

// --- Shared utilities ---
function statusLabel(status) {
  return { done: '一期开发', warn: '二期', draft: '远期' }[status] || status;
}

function copyText(result) {
  if (!result) return;
  const text = result.draft || result.jd_text || '';
  copyToClipboard(text);
}

function copyToClipboard(text) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(() => {
      alert('已复制到剪贴板');
    }).catch(() => {
      fallbackCopy(text);
    });
  } else {
    fallbackCopy(text);
  }
}

function fallbackCopy(text) {
  const ta = document.createElement('textarea');
  ta.value = text;
  ta.style.position = 'fixed';
  ta.style.left = '-9999px';
  document.body.appendChild(ta);
  ta.select();
  try { document.execCommand('copy'); alert('已复制到剪贴板'); } catch { alert('复制失败，请手动复制'); }
  document.body.removeChild(ta);
}
</script>

<style scoped>
/* ===== Common ===== */
.permission-bar {
  font-size: var(--fs-caption);
  color: var(--c-sub);
  background: var(--c-surface-elevated);
  padding: 10px 16px;
  border-radius: var(--radius);
  border: 1px solid var(--c-border);
  line-height: 1.8;
  margin-bottom: var(--gap);
}

.ai-card {
  background: var(--c-card);
  border-radius: var(--radius);
  padding: 20px;
  border: 1px solid var(--c-border);
  margin-bottom: 16px;
}

.card-title {
  font-size: 15px;
  font-weight: 700;
  margin-bottom: 16px;
  color: var(--c-text);
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-title svg {
  stroke: var(--c-primary);
}

/* ===== Form elements ===== */
.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}

.form-group {
  margin-bottom: 14px;
}

.form-group label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 4px;
  color: var(--c-text);
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--c-border);
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-family: inherit;
  box-sizing: border-box;
  background: var(--c-card);
  color: var(--c-body);
  transition: border-color .15s;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: var(--c-primary);
}

.form-group textarea {
  resize: vertical;
}

.form-actions {
  padding: 4px 0 0;
  display: flex;
  gap: 8px;
  align-items: center;
}

.radio-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.radio-chip {
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  border: 1px solid var(--c-border);
  border-radius: var(--radius-sm);
  font-size: 13px;
  cursor: pointer;
  color: var(--c-body);
  transition: all .15s;
  user-select: none;
}

.radio-chip:hover {
  border-color: var(--c-primary);
  color: var(--c-primary);
}

.radio-chip.active {
  border-color: var(--c-primary);
  background: var(--c-primary-subtle);
  color: var(--c-primary);
  font-weight: 600;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}

.input-hint {
  font-size: var(--fs-caption);
  color: var(--c-sub);
  margin-left: 8px;
}

.search-box textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--c-border);
  border-radius: var(--radius);
  font-size: 14px;
  font-family: inherit;
  box-sizing: border-box;
  background: var(--c-card);
  color: var(--c-text);
  resize: vertical;
  transition: border-color .15s;
}

.search-box textarea:focus {
  outline: none;
  border-color: var(--c-primary);
}

/* ===== States ===== */
.skeleton {
  padding: 24px 20px;
}

.sk-line {
  height: 14px;
  background: var(--c-border-light);
  border-radius: 4px;
  margin-bottom: 12px;
  animation: pulse 1.5s ease-in-out infinite;
}

.sk-kpi {
  width: 80px;
  height: 48px;
  background: var(--c-border-light);
  border-radius: 4px;
  margin-bottom: 16px;
  animation: pulse 1.5s ease-in-out infinite;
}

.w100 { width: 100%; }
.w90  { width: 90%; }
.w80  { width: 80%; }
.w70  { width: 70%; }
.w60  { width: 60%; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: .4; }
}

.spinner-inline {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin .6s linear infinite;
  margin-right: 4px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-state {
  border-color: var(--c-reject);
  background: #FFF5F5;
}

.error-msg {
  color: var(--c-reject);
  font-size: 13px;
  margin-bottom: 8px;
}

.empty-state {
  text-align: center;
  padding: 48px 20px;
}

.empty-icon {
  margin-bottom: 12px;
  opacity: .5;
}

.empty-state p {
  color: var(--c-sub);
  font-size: 14px;
}

/* ===== JD Result ===== */
.jd-result {
  padding: 24px;
}

.jd-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--c-border);
}

.jd-header h4 {
  font-size: 18px;
  font-weight: 700;
  color: var(--c-text);
  margin: 0;
}

.jd-dept {
  font-size: 12px;
  color: var(--c-sub);
  background: var(--c-surface-elevated);
  padding: 2px 10px;
  border-radius: 10px;
  border: 1px solid var(--c-border);
}

.jd-section {
  margin-bottom: 20px;
}

.jd-section:last-child {
  margin-bottom: 0;
}

.jd-section-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--c-text);
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.jd-section-title::before {
  content: '';
  width: 3px;
  height: 14px;
  background: var(--c-primary);
  border-radius: 2px;
}

.jd-list {
  padding-left: 18px;
  font-size: 13px;
  color: var(--c-body);
  line-height: 2;
}

.jd-list li {
  padding: 2px 0;
}

.skill-table {
  border: 1px solid var(--c-border);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.skill-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-bottom: 1px solid var(--c-border-light);
  font-size: 13px;
}

.skill-row:last-child {
  border-bottom: none;
}

.skill-name {
  font-weight: 600;
  color: var(--c-text);
  min-width: 80px;
}

.skill-desc {
  color: var(--c-sub);
  flex: 1;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.info-item {
  display: flex;
  gap: 8px;
  padding: 8px 0;
  font-size: 13px;
}

.info-label {
  color: var(--c-sub);
  min-width: 48px;
  flex-shrink: 0;
}

.info-value {
  color: var(--c-text);
  font-weight: 500;
}

/* ===== Search Results ===== */
.num-cell {
  text-align: right;
  font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum";
  font-weight: 600;
}

.reason-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.reason-tag {
  display: inline-block;
  font-size: 11px;
  color: var(--c-progress);
  background: var(--c-primary-subtle);
  padding: 2px 8px;
  border-radius: 4px;
}

/* ===== Match Result ===== */
.match-score-area {
  display: flex;
  gap: 32px;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--c-border);
}

.match-big-score {
  text-align: center;
  min-width: 120px;
}

.match-score-num {
  display: block;
  font-size: 48px;
  font-weight: 900;
  color: var(--c-primary);
  font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum";
  line-height: 1;
}

.match-score-label {
  font-size: var(--fs-caption);
  color: var(--c-sub);
  margin-top: 4px;
  display: block;
}

.match-breakdown {
  flex: 1;
}

.breakdown-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
  font-size: 13px;
}

.breakdown-label {
  color: var(--c-sub);
  min-width: 56px;
}

.breakdown-val {
  font-weight: 700;
  color: var(--c-text);
  font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum";
  min-width: 28px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: var(--c-border-light);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--c-primary);
  border-radius: 4px;
  transition: width .6s ease;
}

/* ===== Interview Questions ===== */
.question-list {
  padding-left: 20px;
}

.question-item {
  padding: 14px 0;
  border-bottom: 1px solid var(--c-border-light);
}

.question-item:last-child {
  border-bottom: none;
}

.question-text {
  font-size: 14px;
  color: var(--c-text);
  font-weight: 600;
  line-height: 1.6;
  margin-bottom: 8px;
}

.question-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.question-meta .btn-text {
  font-size: 12px;
  color: var(--c-sub);
}

.question-meta .btn-text:hover {
  color: var(--c-primary);
}

.hint-box {
  margin-top: 10px;
  padding: 12px;
  background: var(--c-surface-elevated);
  border-radius: var(--radius-sm);
  border: 1px solid var(--c-border-light);
  font-size: 13px;
  color: var(--c-body);
  line-height: 1.8;
}

/* ===== Report ===== */
.report-summary {
  font-size: 14px;
  line-height: 1.9;
  color: var(--c-body);
}

.anomaly-list li {
  color: var(--c-warn);
}

.anomaly-list li::marker {
  color: var(--c-warn);
}

/* ===== Communication Draft ===== */
.draft-text {
  font-size: 14px;
  color: var(--c-body);
  background: var(--c-surface-elevated);
  padding: 16px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--c-border-light);
}

/* ===== Disclaimer ===== */
.disclaimer-bar {
  margin-top: 16px;
  padding: 10px 14px;
  background: #FFFBF5;
  border: 1px solid #FEE9CC;
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--c-warn);
  display: flex;
  align-items: center;
  gap: 6px;
}

.disclaimer-bar::before {
  content: '';
  width: 16px;
  height: 16px;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 24 24' fill='none' stroke='%23F59E0B' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' xmlns='http://www.w3.org/2000/svg'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3Cline x1='12' y1='8' x2='12' y2='12'/%3E%3Cline x1='12' y1='16' x2='12.01' y2='16'/%3E%3C/svg%3E");
  background-size: contain;
  flex-shrink: 0;
}

/* ===== Section label ===== */
.section-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--c-text);
}

.panel-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--c-text);
  margin: 0 0 16px;
}
</style>
