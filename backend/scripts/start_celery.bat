@echo off
REM ============================================================
REM  Celery Worker + Beat 一体化启动（Windows 开发环境）
REM
REM  作用：
REM    - worker  : 执行异步任务（邮件同步、面试通知、批量匹配）
REM    - --beat  : 内嵌定时调度，每 15 分钟触发一次邮箱同步 tick，
REM                每个邮箱按自己的"同步周期"(sync_freq) 到期才真正拉取
REM
REM  前置条件：
REM    1. Redis 已启动（broker: redis://127.0.0.1:6379/0）
REM       Windows 可用 Memurai / Docker: docker run -d -p 6379:6379 redis
REM    2. backend\.env 已配置 SECRET_KEY / JWT_SECRET_KEY / DEEPSEEK_API_KEY
REM ============================================================
cd /d %~dp0\..
.venv\Scripts\celery.exe -A tasks.celery_app:celery_app worker --beat --pool=solo --loglevel=info
