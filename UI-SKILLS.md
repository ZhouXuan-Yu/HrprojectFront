# UI-SKILLS.md — ui-skills 设计质量工具参考

> 本文件记录 `npx ui-skills` CLI 工具的使用方法和下载的设计技能手册，
> 作为项目 UI 审美优化和设计质量控制的指导参考。
>
> 来源：[ui-skills.com](https://www.ui-skills.com/) · [github.com/ibelick/ui-skills](https://github.com/ibelick/ui-skills)

---

## 一、快速开始

```bash
# 在交互式终端中启动 UI 技能路由
npx ui-skills start

# 列出所有分类
npx ui-skills categories

# 按分类列出技能
npx ui-skills list --category visual
npx ui-skills list --category typography

# 下载具体技能文档
npx ui-skills get <author>/<skill-name>
```

---

## 二、已下载的核心技能（适用于本项目）

| 技能 | 作者 | 用途 | 下载命令 |
|------|------|------|----------|
| **impeccable** | pbakaus | 旗舰 UI 设计技能，含 craft/shape/critique/audit/polish 等 20+ 子命令 | `npx ui-skills get pbakaus/impeccable` |
| **baseline-ui** | ibelick | 快速清除 AI 生成感，修复间距/层级/字体 | `npx ui-skills get ibelick/baseline-ui` |
| **typeset** | pbakaus | 字体排版系统改进 | `npx ui-skills get pbakaus/typeset` |
| **colorize** | pbakaus | 色彩系统策略设计 | `npx ui-skills get pbakaus/colorize` |
| **polish** | pbakaus | 上线前最终质量检查 | `npx ui-skills get pbakaus/polish` |
| **layout** | pbakaus | 间距/构图/层级节奏修复 | `npx ui-skills get pbakaus/layout` |

---

## 三、技能核心规则速查

### 3.1 baseline-ui — 反 AI 生成感基线

```
间距       → 使用一致的 spacing scale（不出现随机 13px）
字体       → 正文必须 test-balance / text-pretty，数据用 tabular-nums
动画       → 只动 transform/opacity，不超过 200ms，必须支持 prefers-reduced-motion
交互       → 破坏性操作必须用 AlertDialog，加载态用 skeleton
布局       → 固定 z-index 尺度（无任意值 z-*）
禁止       → 渐变、紫色多色渐变、glow 效果、纯色侧边条
空状态     → 必须给一个明确的下一步操作
强调色     → 每视图限制一个强调色
```

### 3.2 impeccable — 旗舰设计技能

**通用规则**：

| 维度 | 规则 |
|------|------|
| **对比度** | 正文字体 ≥ 4.5:1，大字体(≥18px 或粗体≥14px) ≥ 3:1 |
| **字体选择** | 不使用两个相近的无衬线体配对（如 Inter + Roboto）；用一个家族多字重或对比配对（衬线+无衬线） |
| **行宽** | 正文段限制在 65-75ch |
| **间距** | 必须有节奏变化（紧密分组 + 宽松分隔），不能全部等距 |
| **卡片** | 卡片是偷懒的答案；嵌套卡片永远是错的 |
| **z-index** | 语义化层级：dropdown → sticky → modal-backdrop → modal → toast → tooltip |
| **动画** | 只用 ease-out（quart/quint/expo），无 bounce/elastic |
| **减少动效** | 每个动画必须有 `@media (prefers-reduced-motion: reduce)` 兜底 |

**绝对禁止清单**（详见 impeccable 文档）：

```
❌ border-left/right > 1px 的彩色侧边条
❌ background-clip: text + gradient 文字渐变
❌ 默认玻璃拟态（装饰性 blur）
❌ "大数字+小标签" SaaS 模板
❌ 相同尺寸的图标+标题+文字卡片网格
❌ 每个 section 上方的小写字母追踪标签（"ABOUT" "PROCESS"）
❌ 数字序号标记（01·About / 02·Process）作为默认脚手架
❌ 文字溢出容器
❌ 圆角 ≥ 32px 的卡片
❌ 手绘/SVG 粗糙插画
❌ repeating-linear-gradient 条纹背景
❌ CSS 装饰性网格背景（linear-gradient 模拟的网格线）
```

### 3.3 typeset — 字体排版

```
字号体系   → 5 级就够了：caption / secondary / body / subheading / heading
正文字号   → 最小 16px / 1rem（当前项目 13px 偏小）
层    级   → 字号+字重+颜色+间距组合，不要只靠字号
行    宽   → max-width: 65ch（ch 单位）
行    高   → 标题 1.1-1.2，正文 1.5-1.7
字    距   → 大写/小型大写字母加 0.05-0.12em tracking
数据数字   → font-variant-numeric: tabular-nums
禁    止   → px 单位字体、user-scalable=no、相同风格双字体配对
```

### 3.4 colorize — 色彩系统

```
策略选择   → 克制型(≤10%强调色) / 投入型(30-60%主色) / 全调色板(3-4色) / 浸入型(底色即色彩)
60-30-10  → 60% 中性背景 + 30% 文字/边框 + 10% 强调色（CTAs/高亮）
色彩空间   → 使用 OKLCH，不选用 HSL
中性色     → 向品牌色方向加 0.005-0.015 色度（不默认偏暖或偏冷）
暗色模式   → 深度来自表面亮度差（15%/20%/25%），不靠阴影
禁    止   → 超过 4 种颜色、彩虹调色板、颜色作为唯一信息载体
```

### 3.5 layout — 间距与构图

```
间距系统   → 4pt 基准（4/8/12/16/24/32/48/64/96px），8pt 太粗
节    奏   → 紧密分组(8-12px) + 宽松分隔(48-96px) 交替
工具选择   → Flexbox 用于 1D，Grid 用于 2D，named grid areas 用于复杂页面
可复用网格 → repeat(auto-fit, minmax(280px, 1fr))
深度层级   → 一致的 shadow scale（sm/md/lg/xl），阴影是微妙的
触控目标   → 最小 44×44px
禁    止   → 任意间距值、所有间距相等、网格包裹一切、卡片嵌套卡片
```

### 3.6 polish — 最终质量关卡

```
① 设计系统对齐 → 先查项目设计规范，漂移必须归类（缺少token/未复用组件/概念偏移）
② 视觉对齐     → 像素级对齐、间距使用 token、响应式一致性
③ 信息架构     → 渐进式展示、功能形态匹配邻近功能、命名和心智模型一致
④ 字体细化     → 层级一致性、行宽、孤行处理、字距
⑤ 色彩与对比   → WCAG 合规、token 使用、深色模式
⑥ 交互状态     → 每个可交互元素必须覆盖：default/hover/focus/active/disabled/loading/error/success
⑦ 微交互       → 150-300ms 过渡、一致缓动、60fps、prefers-reduced-motion
⑧ 文案         → 统一术语、大小写一致、无错别字
⑨ 空/错误/加载 → 每个 async 操作都有反馈
⑩ 表单         → 标签一致性、tab 顺序、验证时机
```

---

## 四、对本项目的针对性应用

根据前期 UI 评审（见 conversation 记录），以下技能的规则可以解决当前问题：

| 问题 | 对应技能 | 关键规则 |
|------|----------|----------|
| 信息密度过高（11 筛/13 列） | layout, distill | 节奏变化、密度匹配内容类型 |
| 视觉层级扁平 | layout, typeset | 字号阶梯、空间层次、60-30-10 |
| 所有卡片同质 white+#E1E6EF | layout, colorize | 表面层级(raised/flat/sunken)、中性色微调色相 |
| 字体 13px 偏小 | typeset | 正文最小 16px、5 级字号体系 |
| 颜色系统纯蓝+灰 | colorize | 色彩策略选择、暖色介入、OKLCH |
| FunnelHero 视觉过重 | baseline-ui | 动画约束（transform/opacity）、不做装饰性动画 |
| 无 loading 态/空状态 | polish, harden | 加载骨架、空状态有下一步操作 |
| 侧边 stripe + 渐变 | impeccable bans | respect 绝对禁止清单 |

---

## 五、推荐工作流

每轮 UI 优化时按以下顺序应用：

```
1. layout       → 先修复间距系统和视觉节奏（最根基）
2. typeset      → 再修复字体层级和可读性（视觉信息载体）
3. colorize     → 然后引入色彩策略（情感与识别）
4. baseline-ui  → 清除 AI 生成感（细节收敛）
5. polish       → 最终质量关卡（对齐→细化→验证）
```

---

## 六、npm 包信息

```
包名: ui-skills
版本: 0.2.3
许可证: MIT
作者: ibelick (pro@motion-primitives.com)
仓库: github.com/ibelick/ui-skills
网站: https://www.ui-skills.com/
```
