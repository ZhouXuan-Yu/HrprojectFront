# 智能招聘系统 · README

> Python Flask + Vue 3 · 邮箱收简历 → AI 解析画像 → 人岗匹配 → 面试(飞书) → Offer → 入职

## 快速启动

```bash
cd backend/ && pip install -r requirements.txt && python app.py  # :5000
cd frontend/ && npm run dev                                      # :5173
cd frontend/ && npm test                                         # 33 E2E
```

浏览器打开 `http://127.0.0.1:5173/login`

## 项目结构

```
hr-web/
├── frontend/          Vue 3 + Vite (9 页面, 8 API 模块)
├── backend/           Flask (50 .py, 45+ 端点, 27 表)
│   ├── app/api/       9 个 Blueprint
│   ├── app/services/  13 个业务服务
│   ├── app/models/    27 张表
│   └── tasks/         Celery 异步
└── docs/              设计文档
```

## 技术栈

| 层 | 选型 |
|----|------|
| 前端 | Vue 3 + Vite + Vue Router + Three.js |
| 后端 | Flask + SQLAlchemy + Celery |
| 数据库 | SQLite(dev) / MySQL(prod) |
| AI | DeepSeek API + ai_engine 降级 |
| 集成 | 飞书 CLI + Boss CLI |
| 测试 | Playwright 33 E2E |

## 7 轮完成记录

〇 环境 → 一 骨架 → 二 联调 → 三 业务 → 四 验收 → 五 数据库 → 六 DeepSeek → 七 Boss ✅

## 跟踪文档

| 文件 | 作用 |
|------|------|
| `Memory.md` | 进度 + 下一步 |
| `Learning.md` | 复盘 + 规则 |
| `Wiki.md` | 业务口径 + 架构 |
| `README.md` | (本文件) 概览 |
