// kpiIcons.js — KPI 数据卡片统一线性图标集
// 参考样式：浅紫灰圆角方形背景（.metric-icon 负责底色）+ 蓝色线性图标（stroke: currentColor）。
// 统一 24×24 viewBox、stroke-width 2、圆角线帽，线宽适中、配色克制，适配企业级后台白底 KPI 卡片。

const S = '<svg viewBox="0 0 24 24" style="width:20px;height:20px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round">';
const E = '</svg>';

export const KPI_ICONS = {
  // 参考图标：蓝色线性时钟（默认）
  clock: S + '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>' + E,
  calendar: S + '<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>' + E,
  edit: S + '<path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>' + E,
  briefcase: S + '<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>' + E,
  userCheck: S + '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><polyline points="16 11 18 13 22 9"/>' + E,
  users: S + '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>' + E,
  star: S + '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>' + E,
  trendingUp: S + '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>' + E,
  check: S + '<polyline points="20 6 9 17 4 12"/>' + E,
  checkSquare: S + '<path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>' + E,
  fileText: S + '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/>' + E,
  mail: S + '<rect x="2" y="4" width="20" height="16" rx="2"/><polyline points="22,6 12,13 2,6"/>' + E,
  ban: S + '<circle cx="12" cy="12" r="10"/><line x1="4.9" y1="4.9" x2="19.1" y2="19.1"/>' + E,
  settings: S + '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>' + E,
  bell: S + '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>' + E,
  messageSquare: S + '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>' + E,
};

// 按 KPI 标签关键字匹配图标（优先级从上到下）
const LABEL_MAP = [
  [/均分|评分|star/i, 'star'],
  [/评价/i, 'edit'],
  [/面试/i, 'calendar'],
  [/岗位|需求|审批/i, 'briefcase'],
  [/入职/i, 'userCheck'],
  [/候选人|跟进|人才/i, 'users'],
  [/通过率|转化率/i, 'trendingUp'],
  [/完成/i, 'check'],
];

/**
 * 解析 KPI 卡片图标：优先用数据自带 icon，缺失时按 label 匹配，兜底用时钟。
 * @param {object} kpi - KPI 数据项（可能只有 val/label/trend，没有 icon）
 * @returns {string} 可直接用于 v-html 的 svg 字符串
 */
export function resolveKpiIcon(kpi) {
  if (kpi && kpi.icon) return kpi.icon;
  const label = (kpi && kpi.label) || '';
  for (const [re, name] of LABEL_MAP) {
    if (re.test(label)) return KPI_ICONS[name];
  }
  return KPI_ICONS.clock;
}
