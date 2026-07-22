# Learning.md — 复盘记录

> 记录每次出错：哪里做错了、为什么错、下次如何避免。

---

## 规则沉淀

| 规则 | 说明 |
|------|------|
| 新增优先 | 只做 cp/mkdir，不做 rm/mv |
| 删除需确认 | 任何删除操作先问用户 |
| 四文档同步 | 每轮结束更新 Memory/Learning/Wiki/README |
| Grep 先查 | 并发编辑前确认无重复声明 |
| 改数据跑测试 | Mock 变更后立即 E2E |
| 跨DB验证 | Model 变更后 `db.create_all()` + INSERT |

---

## 复盘 #4 — 并发冲突 + AI引擎 (7/18)

- Agent 与主线程同文件冲突 → 先 Grep 再 Edit
- Dify 替换为纯 Python `ai_engine.py`
- E2E `共 2 人` vs 实际 `共 1 人` → 改 mock 后跑测试

## 复盘 #5 — SQLite (7/18)

- `BigInteger` 在 SQLite 不生成主键 → `.with_variant(INTEGER, 'sqlite')`
- `_mock_list_demands` 缺变量 → params 解析补回

## 复盘 #6 — E2E flaky (7/18)

- sidebar/command-palette 偶发失败 (~3-5%)
- Vue 响应式 + Playwright 时序竞态，与后端无关
- 标记为已知 flaky，不阻塞

## 复盘 #7 — DeepSeek/Boss 集成 (7/18)

- 用户添加 `deepseek_client.py` + `boss_cli_service.py` + `boss.py` + `ai.py` 重写
- 47→50 文件，AI 3→6 工作流
- E2E 33/33 保持不变

## 复盘 #8 — 项目复现 & 审批还原 (7/22)

- **模型加字段要重建 DB**：给 `RecruitDemand` 加 `position_name` 列后，旧 SQLite 文件仍存在，`create_all()` 不会自动 ALTER TABLE。必须 `drop_all()` + `create_all()` 或手动 ALTER。
- **审批 `commit()` 顺序**：`_fire_match_batch()` 在 `commit()` 之前执行会卡死 HTTP 响应——匹配任务调 DeepSeek API 超时导致 commit 永远不执行。应先 commit 再触发异步任务。
- **模板传参类型**：`@click="fn(d.id)"` 传字符串，函数里 `d.id` 就是 `undefined`。Vue 模板传对象要写 `@click="fn(d)"`。
- **前端事件不可靠**：`@blur` / `@change` 在某些交互顺序下不触发。改用 Vue `watch` 监听数据变化更可靠。
- **邮箱重复添加**：`email_address` 有 unique 约束，软删除的记录也会冲突。创建前先查是否存在，软删除的复用、活跃的报错。
- **变更前确认**：修改了大量业务代码后用户要求还原，因为没有 git 只能手动逐文件 revert。以后大改动前先 `git init` + `git commit` 保存基线。
