"""Boss CLI API: /api/boss/*

Provides REST endpoints that wrap boss-cli subprocess calls.
All responses follow the unified {data, message} / {error: {code, message}} format.

Important notes for consumers:
    - boss-cli is browser automation — endpoints may take 30-120s
    - boss-cli requires a logged-in browser (run `boss login` first)
    - Rate limits apply: daily resume views, greeting quota, deep-search matches
"""

import logging

from flask import Blueprint, request

from app.utils.response import success, error
from app.services import boss_cli_service as boss

log = logging.getLogger(__name__)

bp = Blueprint("boss", __name__)


# ===========================================================================
# POST /api/boss/login — launch BOSS login page in browser
# ===========================================================================

@bp.route("/login", methods=["POST"])
def boss_login():
    """Launch ``boss login`` to open the BOSS login page in a browser.

    This command returns immediately after opening the browser; it does
    NOT wait for or poll the login result.  Call ``GET /api/boss/status``
    afterwards to verify whether login was completed.
    """
    result = boss.login()
    if result.get("ok"):
        return success({
            "login_url": result.get("login_url", "https://www.zhipin.com/web/user/"),
            "instruction": "请在打开的浏览器窗口中扫码登录，完成后前端调用 GET /api/boss/status 验证",
        })
    return error("BOSS_LOGIN_FAILED", result.get("error", "启动登录页面失败"), status_code=502)


# ===========================================================================
# GET /api/boss/status — check boss-cli availability + login state
# ===========================================================================

@bp.route("/status")
def get_status():
    """Check if boss-cli is installed, enabled, and logged in."""
    available = boss.is_available()
    logged_in = False
    if available:
        login_status = boss.is_logged_in()
        logged_in = login_status.get("logged_in", False)

    return success({
        "available": available,
        "logged_in": logged_in,
        "status": "connected" if logged_in else ("need_login" if available else "unavailable"),
        "message": "BOSS 已连接" if logged_in else ("boss-cli 可用但未登录" if available else "boss-cli 未安装或未启用"),
    })


# ===========================================================================
# GET /api/boss/positions — list all positions
# ===========================================================================

@bp.route("/positions")
def list_positions():
    result = boss.get_positions()
    if result.get("ok"):
        return success(result["data"])
    return error("BOSS_POSITIONS_FAILED", result.get("error", "获取职位列表失败"), status_code=502)


# ===========================================================================
# GET /api/boss/positions/<name> — fetch position JD detail
# ===========================================================================

@bp.route("/positions/<name>")
def get_position_detail(name):
    result = boss.get_position_detail(name)
    if result.get("ok"):
        return success(result["data"])
    return error("BOSS_JD_FAILED", result.get("error", f"获取 JD 失败: {name}"), status_code=502)


# ===========================================================================
# POST /api/boss/candidates/search — search candidates
# ===========================================================================

@bp.route("/candidates/search", methods=["POST"])
def search_candidates():
    body = request.get_json(silent=True) or {}
    keyword = body.get("keyword")
    job = body.get("job")
    core = body.get("core")
    bonus = body.get("bonus")
    match = body.get("match", False)

    result = boss.search_candidates(
        keyword=keyword,
        job=job,
        core=core,
        bonus=bonus,
        match=match,
    )
    if result.get("ok"):
        return success(result["data"])
    return error("BOSS_SEARCH_FAILED", result.get("error", "搜索候选人失败"), status_code=502)


# ===========================================================================
# GET /api/boss/chat/list — get chat list
# ===========================================================================

@bp.route("/chat/list")
def chat_list():
    unread_only = request.args.get("unread", "0") == "1"
    result = boss.get_chat_list(unread_only=unread_only)
    if result.get("ok"):
        return success(result["data"])
    return error("BOSS_CHAT_LIST_FAILED", result.get("error", "获取聊天列表失败"), status_code=502)


# ===========================================================================
# POST /api/boss/chat/open — open a conversation
# ===========================================================================

@bp.route("/chat/open", methods=["POST"])
def chat_open():
    body = request.get_json(silent=True) or {}
    name = body.get("name", "")
    if not name:
        return error("INVALID_PARAM", "name 为必填字段", status_code=400)

    index = body.get("index")
    unread = body.get("unread", False)
    strict = body.get("strict", False)

    result = boss.open_chat(name=name, index=index, unread=unread, strict=strict)
    if result.get("ok"):
        return success(result["data"])
    return error("BOSS_CHAT_OPEN_FAILED", result.get("error", "打开会话失败"), status_code=502)


# ===========================================================================
# POST /api/boss/chat/send — send a message
# ===========================================================================

@bp.route("/chat/send", methods=["POST"])
def chat_send():
    body = request.get_json(silent=True) or {}
    text = body.get("text", "")
    if not text:
        return error("INVALID_PARAM", "text 为必填字段", status_code=400)

    request_resume = body.get("request_resume", False)

    result = boss.send_message(text=text, request_resume=request_resume)
    if result.get("ok"):
        return success(result["data"])
    return error("BOSS_SEND_FAILED", result.get("error", "发送消息失败"), status_code=502)


# ===========================================================================
# POST /api/boss/action — execute an action on current candidate
# ===========================================================================

@bp.route("/action", methods=["POST"])
def action():
    body = request.get_json(silent=True) or {}
    action_type = body.get("action", "")
    if not action_type:
        return error("INVALID_PARAM", "action 为必填字段", status_code=400)

    remark = body.get("remark")  # optional, only for 'remark' action

    result = boss.do_action(action=action_type, remark=remark)
    if result.get("ok"):
        return success(result["data"])
    return error("BOSS_ACTION_FAILED", result.get("error", "操作失败"), status_code=502)


# ===========================================================================
# POST /api/boss/resume/preview — preview online resume
# ===========================================================================

@bp.route("/resume/preview", methods=["POST"])
def resume_preview():
    body = request.get_json(silent=True) or {}
    name = body.get("name", "")
    if not name:
        return error("INVALID_PARAM", "name 为必填字段", status_code=400)

    result = boss.preview_resume(name=name)
    if result.get("ok"):
        return success(result["data"])
    return error("BOSS_PREVIEW_FAILED", result.get("error", "预览简历失败"), status_code=502)


# ===========================================================================
# POST /api/boss/greet — greet a candidate
# ===========================================================================

@bp.route("/greet", methods=["POST"])
def greet_candidate():
    body = request.get_json(silent=True) or {}
    name = body.get("name", "")
    if not name:
        return error("INVALID_PARAM", "name 为必填字段", status_code=400)

    job = body.get("job")  # optional

    result = boss.greet_candidate(name=name, job=job)
    if result.get("ok"):
        return success(result["data"])
    return error("BOSS_GREET_FAILED", result.get("error", "打招呼失败"), status_code=502)
