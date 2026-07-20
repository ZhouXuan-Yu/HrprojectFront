# Wiki.md — 项目常识库

> 长期稳定的项目背景、业务口径、术语定义。

---

## 项目背景

智能招聘系统：**邮箱收简历 → AI 解析画像 → 人岗匹配 → 面试(飞书) → Offer → 入职**

## 架构

| 层 | 选型 |
|----|------|
| 前端 | Vue 3 + Vite + Vue Router + Three.js |
| 后端 | Python Flask + SQLAlchemy + Celery |
| 数据库 | SQLite(dev) / MySQL(prod) — 27 表 |
| AI | DeepSeek API + 本地 ai_engine 降级 |
| 集成 | 飞书 CLI (lark-cli) + Boss CLI |
| 测试 | Playwright 33 E2E |

## 后端目录 (50 .py)

```
backend/
├── app.py, config.py
├── app/
│   ├── models/      (10 files, 27 tables)
│   ├── api/         (9 files: auth/dashboard/demand/talent/interview/ai/config/boss/errors)
│   ├── services/    (11 files: ai_engine/deepseek/approval/match/interview/feishu/iam/dashboard/demand/talent/config/boss_cli/dify)
│   ├── middleware/   (auth)
│   └── utils/       (response/enums/scoring)
├── tasks/           (celery_app/email_sync/match_batch/notify)
└── scripts/seed.py
```

## 关键决策

| # | 决策 | 结论 |
|---|------|------|
| 1 | AI | Dify 去除 → 纯 Python 引擎 + DeepSeek API |
| 2 | 审批 | v0.1 三步硬编码，v0.2 引擎化 |
| 3 | 数据库 | `BigInteger().with_variant(INTEGER, 'sqlite')` 兼容 |
| 4 | 飞书 | lark-cli 子进程，MOCK_MODE 切换 |
| 5 | Boss | boss-cli 子进程，`/api/boss/*` 10 端点 |
