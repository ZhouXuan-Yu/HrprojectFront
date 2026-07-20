# RecruitAI 招聘辅助中心 — UI 重设计方案 v3.0

> 日期: 2026-07-18 · 基于 HeroUIPro 14 个 AI 组件完整源码分析

---

## 一、HeroUIPro 源码级模式提取

### 1.1 核心状态机 (ChatStatus)

HeroUIPro 所有 AI 组件共享同一定义：
```ts
type ChatStatus = 'ready' | 'submitted' | 'streaming' | 'error'
```

| status | PromptInput.Send 图标 | 含义 |
|--------|---------------------|------|
| `ready` | ArrowUp (蓝色箭头) | 等待用户输入 |
| `submitted` | Spinner (旋转圆环) | 请求已发送，等待首个 token |
| `streaming` | Stop 方块 (■) | 正在流式输出 token |
| `error` | Xmark (✕) | 出错 |

**Vue 3 落地**：每个 Tab 内使用 `ref<'ready'|'submitted'|'streaming'|'error'>('ready')`

### 1.2 复合组件模式 (React Object.assign → Vue provide/inject)

HeroUIPro 用 `Object.assign(RootComp, { Sub1, Sub2 })` 实现复合组件。Vue 3 使用 `provide/inject` 同构：

```js
// 父组件: AiPromptInput.vue 的 <script setup>
const status = ref('ready')
provide('promptInput', { status, disabled, value, onSubmit, onStop })

// 子组件: AiPromptInputSend.vue
const { status, disabled, onSubmit, onStop } = inject('promptInput')
```

### 1.3 data-slot CSS 约定

每个子组件根元素都会设置 `data-slot="component-name"`，CSS 通过 `[data-slot]` 选择器定位，不依赖 class 命名：
```css
[data-slot="prompt-input"] { ... }
[data-slot="chat-message-assistant"] { ... }
[data-slot="chain-of-thought-step"] { ... }
```

**Vue 落地**：组件 scoped style 使用 `[data-slot]` 选择器，全局 token 通过 CSS 变量覆盖。

### 1.4 模板对话页布局 (template-chat → chat-page.tsx)

```
┌─────────────────────────────────────────┐
│ ChatConversation (flex:1, overflow:hidden)│
│   ChatConversation.Content              │
│     messages.map(ThreadMessage)         │
│   ChatConversation.ScrollAnchor         │
│ ChatConversation.ScrollButton (fixed)   │
├─────────────────────────────────────────┤
│ ChatComposer (shrink-0, 底部固定)        │
│   PromptInput.Shell                     │
│     PromptInput.Textarea                │
│     PromptInput.Toolbar                 │
│       PromptInput.ToolbarEnd            │
│         PromptInput.Send                │
│   PromptInput.Footer (免责声明)           │
└─────────────────────────────────────────┘
```

### 1.5 ThreadMessage 渲染状态机 (thread-message.tsx)

```
AssistantMessage:
  skeleton   → ChatLoader.Skeleton (头像 + 3 行骨架)
  streaming  → TextShimmer + ChatLoader.Dots
  complete   → ChainOfThought? → ChatTool[]? → Markdown → Sources → Actions
  error      → 红色错误信息 + 重试按钮

UserMessage:
  始终渲染 → ChatMessage.Bubble → ChatMessage.Content (纯文本)
```

### 1.6 ChatTool 自动生成模式

当无 children 时，ChatToolRoot 自动构建完整结构：
```
ChatToolRoot (无 children)
  → ChatToolTrigger    (工具名 + StatusIcon)
  → ChatToolContent
      → ChatToolArgs   (JSON CodeBlock)
      → ChatToolResult (JSON CodeBlock)
      → ChatToolApproval (同意/拒绝按钮)
      → ChatToolMeta (toolCallId)
```

**Vue 落地**：使用 `<slot>` 提供默认内容，`v-if="!$slots.default"` 触发自动生成。

### 1.7 TextShimmer 组件

```ts
<TextShimmer duration={1.5} as="span">
  {content}
</TextShimmer>
```
CSS: `@keyframes shimmer` 从左到右的渐变扫光动画，`background-size: 200% 100%`。

### 1.8 ChatLoader 4 种变体

| 变体 | 渲染 | 使用场景 |
|------|------|---------|
| `Dots` | 3 个跳动的点 | streaming 中 |
| `Pulse` | 单个脉动圆 | 简短等待 |
| `Spinner` | 旋转圆环 | 初始加载 |
| `Skeleton` | 头像 + 3行骨架 | 对话加载占位 |

---

## 二、组件映射 (React → Vue 3)

| HeroUIPro (React) | Vue 3 对应 | 行数估计 | 优先级 |
|---|:---:|:--:|:--:|
| PromptInput (8 variants) | `AiPromptInput.vue` | ~150 | P0 |
| ChatMessage (User/Assistant/Bubble/Content/Avatar/Actions) | `AiChatMessage.vue` | ~180 | P0 |
| ChatLoader (Dots/Pulse/Spinner/Skeleton) | `AiSkeleton.vue` | ~80 | P0 |
| ChainOfThought (Root/Trigger/Content/Steps/Step) | `AiChainOfThought.vue` | ~120 | P1 |
| Markdown (static + streamdown streaming) | `AiMarkdown.vue` | ~100 | P1 |
| ChatConversation (Content/ScrollAnchor/ScrollButton) | `AiChatConversation.vue` | ~100 | P1 |
| ChatTool (Root/Trigger/StatusIcon/Args/Result/Error/Approval) | `AiChatTool.vue` | ~150 | P4 |
| ChatSource (Root/Trigger/Icon/Title/Preview) | `AiChatSource.vue` | ~100 | P4 |
| PromptSuggestion (Root/Group/Item pill+card) | `AiPromptSuggestion.vue` | ~100 | P4 |
| ChatMessageActions (Copy/Thumbs/Regenerate/Menu) | 整合入 `AiChatMessage.vue` | — | P0 |

---

## 三、新文件清单

```
src/components/ai/                    ← 新增目录
├── AiPromptInput.vue                 ← P0 · PromptInput 等效
├── AiChatMessage.vue                 ← P0 · ChatMessage 等效 (含 Avatar + Actions)
├── AiChatConversation.vue            ← P1 · ChatConversation 等效 (ResizeObserver 自动滚底)
├── AiChainOfThought.vue              ← P1 · ChainOfThought 等效 (TextShimmer + Disclosure)
├── AiMarkdown.vue                    ← P1 · Markdown 等效 (marked 库静态渲染)
├── AiChatTool.vue                    ← P4 · ChatTool 等效
├── AiChatSource.vue                  ← P4 · ChatSource 等效
├── AiPromptSuggestion.vue            ← P4 · 建议卡片/药丸
├── AiSkeleton.vue                    ← P0 · 统一骨架屏 (text/dots/pulse 三变体)
└── AiDisclaimer.vue                  ← P0 · 统一免责声明 (全局常量)

src/views/ai/                         ← 新增目录 (tab 子组件)
├── AiTabJD.vue                       ← P2 · JD 草稿生成
├── AiTabSearch.vue                   ← P2 · 语义简历搜索
├── AiTabMatch.vue                    ← P2 · 人岗匹配工作台
├── AiTabInterview.vue                ← P2 · 面试辅助
├── AiTabReport.vue                   ← P2 · 招聘深度报表
├── AiTabCommunication.vue            ← P2 · 候选人沟通助手
└── AiTabBase.js                      ← P2 · 共享 composable (status 状态机 + useStreaming 封装)
```

---

## 四、RecruitAI.vue 重构后结构

```vue
<template>
  <WorkbenchLayout title="招聘辅助中心" :breadcrumb="breadcrumb">
    <!-- Tab bar -->
    <div class="tabs" role="tablist">
      <button v-for="tab in tabs" :key="tab.id" class="tab"
        :class="{ active: activeTab === tab.id }"
        role="tab" :aria-selected="activeTab === tab.id"
        @click="activeTab = tab.id">{{ tab.number }} {{ tab.title }}</button>
    </div>

    <!-- Dynamic tab rendering -->
    <KeepAlive>
      <component :is="activeComponent" :key="activeTab" />
    </KeepAlive>

    <!-- BOSS integration -->
    <BossIntegration :compact="true" />

    <!-- Embedded AI table (preserved) -->
    <AiCapabilitiesTable />
  </WorkbenchLayout>
</template>

<script setup>
const activeTab = ref('jd')
const activeComponent = computed(() => tabComponents[activeTab.value])
const tabComponents = {
  jd: AiTabJD, search: AiTabSearch, match: AiTabMatch,
  interview: AiTabInterview, report: AiTabReport, chat: AiTabCommunication
}
</script>
```

**主文件目标行数**: < 80 行

---

## 五、P0 立即实施清单

### 5.1 AiSkeleton.vue (最小骨架组件)

```vue
<template>
  <div data-slot="ai-skeleton" :data-variant="variant" role="status" aria-label="加载中">
    <template v-if="variant === 'dots'">
      <span data-slot="ai-skeleton-dot" v-for="i in 3" :key="i" :style="{ animationDelay: (i-1)*0.15 + 's' }"></span>
    </template>
    <template v-else-if="variant === 'text'">
      <div data-slot="ai-skeleton-line" v-for="i in lines" :key="i" :class="'w' + widths[i-1]"></div>
    </template>
    <template v-else-if="variant === 'spinner'">
      <div data-slot="ai-skeleton-spinner"></div>
    </template>
  </div>
</template>

<script setup>
defineProps({
  variant: { default: 'text', validator: v => ['text','dots','spinner'].includes(v) },
  lines: { default: 3 },
  widths: { default: () => ['80%','60%','90%'] },
})
</script>
```

### 5.2 AiDisclaimer.vue (统一免责声明)

```vue
<template>
  <div data-slot="ai-disclaimer">
    <svg>...</svg>
    {{ text }}
  </div>
</template>
<script setup>
defineProps({ text: { default: '此内容由AI生成，请人工审核确认后使用' } })
</script>
```

### 5.3 AiPromptInput.vue (核心输入组件)

```vue
<template>
  <div data-slot="prompt-input" :data-status="status">
    <div data-slot="prompt-input-shell">
      <div data-slot="prompt-input-content">
        <textarea
          data-slot="prompt-input-textarea"
          :value="modelValue"
          :placeholder="placeholder"
          :disabled="disabled"
          @input="onInput"
          @keydown.enter.exact.prevent="handleSubmit"
          @keydown.escape="handleStop"
          ref="textareaRef"
          rows="1"
        ></textarea>
      </div>
      <div data-slot="prompt-input-toolbar">
        <div data-slot="prompt-input-toolbar-start">
          <slot name="toolbar-start" />
        </div>
        <div data-slot="prompt-input-toolbar-end">
          <button
            data-slot="prompt-input-send"
            :data-status="status"
            :disabled="status === 'ready' && !modelValue.trim()"
            @click="status === 'streaming' ? handleStop() : handleSubmit()"
            :aria-label="status === 'streaming' ? '停止生成' : '发送'"
          >
            <AiSkeleton v-if="status === 'submitted'" variant="spinner" />
            <svg v-else-if="status === 'streaming'"><rect x="6" y="6" width="12" height="12" /></svg>
            <svg v-else><!-- ArrowUp --></svg>
          </button>
        </div>
      </div>
    </div>
    <div v-if="hint" data-slot="prompt-input-footer">{{ hint }}</div>
  </div>
</template>

<script setup>
const props = defineProps({
  modelValue: String,
  placeholder: { default: '输入您的问题...' },
  disabled: Boolean,
  status: { default: 'ready' },  // 'ready'|'submitted'|'streaming'|'error'
  hint: String,
})
const emit = defineEmits(['update:modelValue', 'submit', 'stop'])
const textareaRef = ref(null)

function onInput(e) { emit('update:modelValue', e.target.value); autosize(e.target) }
function handleSubmit() { if (props.status === 'ready') emit('submit') }
function handleStop() { if (props.status === 'streaming') emit('stop') }

function autosize(el) {
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 200) + 'px'
}
</script>
```

### 5.4 AiChatMessage.vue (消息气泡)

```vue
<template>
  <div data-slot="chat-message" :data-role="role">
    <!-- Avatar -->
    <div v-if="role === 'ai'" data-slot="chat-message-avatar">AI</div>

    <div data-slot="chat-message-body">
      <div data-slot="chat-message-bubble">
        <!-- Loading state -->
        <AiSkeleton v-if="status === 'loading'" variant="text" :lines="3" />

        <!-- Streaming state -->
        <template v-else-if="status === 'streaming'">
          <AiSkeleton variant="dots" />
          <span data-slot="chat-message-shimmer">{{ streamingContent }}</span>
        </template>

        <!-- Error state -->
        <div v-else-if="status === 'error'" data-slot="chat-message-error">
          <slot name="error" />
        </div>

        <!-- Complete: render content + tools + sources -->
        <template v-else>
          <div data-slot="chat-message-content">
            <slot />
          </div>
          <AiChatTool v-for="(tool, i) in tools" :key="i" v-bind="tool" />
          <AiChatSource v-if="sources?.length" :sources="sources" />
        </template>
      </div>

      <!-- Actions (copy/regenerate) -->
      <div v-if="status === 'complete'" data-slot="chat-message-actions">
        <slot name="actions" />
      </div>
    </div>

    <!-- User avatar -->
    <div v-if="role === 'user'" data-slot="chat-message-avatar">{{ userInitial }}</div>
  </div>
</template>

<script setup>
defineProps({
  role: { default: 'ai', validator: v => ['user','ai'].includes(v) },
  status: { default: 'complete', validator: v => ['loading','streaming','complete','error'].includes(v) },
  streamingContent: String,
  tools: Array,
  sources: Array,
  userInitial: { default: 'HR' },
})
</script>
```

---

## 六、色板与 CSS 变量

所有 AI 组件使用项目已有 CSS token，不新建变量：

| 用途 | CSS 变量 |
|------|---------|
| 主操作色 | `var(--primary)` #4F6EF7 |
| 背景 | `var(--bg)` #F6F8FB |
| 卡片背景 | `var(--surface)` #FFFFFF |
| 主文字 | `var(--text-primary)` #172033 |
| 辅助文字 | `var(--text-secondary)` #5B6475 |
| 禁用文字 | `var(--text-muted)` #8C95A6 |
| 边框 | `var(--border)` #E1E6EF |
| 成功 | `var(--success)` #22C55E |
| 警告 | `var(--warning)` #F59E0B |
| 错误 | `var(--error)` #EF4444 |
| AI 消息气泡背景 | `#F0F4FF` (浅蓝，硬编码于 scoped style) |
| 用户消息气泡背景 | `var(--bg)` |
| 免责声明背景 | `#FFF8E1` |

---

## 七、实施路径

| Phase | 内容 | 新建文件 | 行数变化 |
|-------|------|:--:|------|
| **P0** | AiSkeleton + AiDisclaimer + AiPromptInput + AiChatMessage | 4 | 新增 ~500 行 |
| **P1** | AiChainOfThought + AiMarkdown + AiChatConversation | 3 | 新增 ~350 行 |
| **P2** | 6 个 AiTab* 子组件 + AiTabBase.js + RecruitAI.vue 重构 | 8 | RecruitAI: 1344→80, tab 组件: ~150×6 |
| **P3** | 后端 SSE 端点 + useStreaming composable | 4 | 新增 ~250 行 |
| **P4** | AiChatTool + AiChatSource + AiPromptSuggestion | 3 | 新增 ~350 行 |
| **P5** | useClipboard + toast + 移动端响应式 + a11y | 2 | 修改 ~200 行 |

## 八、验收基线

- [ ] `npm run build` 通过
- [ ] `npm test` 33/33 通过
- [ ] RecruitAI.vue < 80 行
- [ ] 0 硬编码 hex 颜色 (scoped 浅蓝气泡底色可接受)
- [ ] 0 "AI 外呼/自动拨打"
- [ ] 所有 tab 统一 PromptInput → ChatMessage 对话流
- [ ] 流式 SSE 至少覆盖 Tab 1 (JD) 和 Tab 3 (Match)
- [ ] 复制反馈使用 CSS transition 而非 alert()
