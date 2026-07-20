"""Boss CLI service — wraps @joohw/boss-cli as subprocess.

All commands run via subprocess.run(['boss', ...]) with timeouts.
Output is parsed into structured dicts. Times out after configurable seconds
(default: 120s) because browser automation is inherently slow.

Design:
    - Every public function returns {"ok": True/False, ...}
    - All commands and results are logged
    - boss-cli must be installed globally and ``boss login`` completed beforehand
    - boss-cli uses Puppeteer's persistent user data dir for login state
    - subprocess uses shell=True on Windows (.CMD files need shell execution)
"""

import json
import logging
import os
import shutil
import subprocess
import time
from typing import Optional

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

def _get_timeout() -> int:
    try:
        from config import Config
        return Config.BOSS_CLI_TIMEOUT
    except Exception:
        return 120


def _get_enabled() -> bool:
    try:
        from config import Config
        return Config.BOSS_CLI_ENABLED
    except Exception:
        return True


# ---------------------------------------------------------------------------
# Availability check
# ---------------------------------------------------------------------------

def is_available() -> bool:
    """Check if the boss CLI is installed and executable."""
    if not _get_enabled():
        log.info("boss-cli disabled via BOSS_CLI_ENABLED config")
        return False
    return shutil.which("boss") is not None


# ---------------------------------------------------------------------------
# Login & session management
# boss-cli uses Puppeteer with persistent user data dir (~/.boss-cli-browser/).
# Login state persists across sessions — user only needs to login once.
# ---------------------------------------------------------------------------

def login() -> dict:
    """Open the BOSS login page in a browser via ``boss login``.

    Returns immediately after launching the browser. boss-cli saves browser
    profile (cookies, localStorage) to ~/.boss-cli-browser/ so login state
    persists across sessions.

    Check ``GET /api/boss/status`` afterwards to verify login completed.
    """
    if not is_available():
        return {"ok": False, "error": "boss-cli 未安装或未启用，请先执行 npm i -g @joohw/boss-cli"}
    try:
        result = _run(["login"], timeout=30)
        return {
            "ok": True,
            "login_url": "https://www.zhipin.com/web/user/",
            "instruction": "请在打开的浏览器窗口中扫码登录，完成后调用 GET /api/boss/status 验证",
            "persistence": "登录状态保存在 ~/.boss-cli-browser/ 目录，重启后无需重新登录",
            "output": (result.stdout or "").strip(),
        }
    except subprocess.TimeoutExpired:
        # login opens the browser and hangs; timeout is expected
        return {
            "ok": True,
            "login_url": "https://www.zhipin.com/web/user/",
            "instruction": "请在打开的浏览器窗口中扫码登录，完成后调用 GET /api/boss/status 验证",
            "persistence": "登录状态保存在 ~/.boss-cli-browser/ 目录，重启后无需重新登录",
            "output": "browser launched (timeout expected)",
        }
    except FileNotFoundError:
        return {"ok": False, "error": "boss-cli 未安装。请执行: npm i -g @joohw/boss-cli"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def is_logged_in() -> dict:
    """Quick check: can boss-cli read chat list? If yes, login is active.

    Uses ``boss list`` as a lightweight read — if it works, we're logged in.
    boss-cli's Puppeteer profile persists login state across sessions.
    """
    if not is_available():
        return {"ok": False, "logged_in": False, "error": "unavailable"}
    try:
        result = _run(["list"], timeout=30, check=False)
        ok = result.returncode == 0 and "ERR" not in (result.stderr or "")[:50]
        return {"ok": True, "logged_in": ok, "output": (result.stdout or "")[:200]}
    except Exception:
        return {"ok": False, "logged_in": False, "error": "check failed"}


def check_session() -> dict:
    """Detailed session check — returns session persistence info."""
    available = is_available()
    logged_in = False
    session_dir = os.path.expanduser("~/.boss-cli-browser")
    session_exists = os.path.isdir(session_dir)

    if available:
        try:
            login_status = is_logged_in()
            logged_in = login_status.get("logged_in", False)
        except Exception:
            logged_in = False

    return {
        "ok": True,
        "available": available,
        "logged_in": logged_in,
        "session_persistent": session_exists,
        "session_dir": session_dir if session_exists else None,
        "status": "connected" if logged_in else ("need_login" if available else "unavailable"),
        "message": (
            "BOSS 已连接，登录状态持久化" if logged_in
            else ("boss-cli 可用但未登录，请执行 boss login 完成首次登录" if available
            else "boss-cli 未安装或未启用")
        ),
    }


# ---------------------------------------------------------------------------
# Core subprocess runner
# ---------------------------------------------------------------------------

def _run(args: list, timeout: int = None, check: bool = False) -> subprocess.CompletedProcess:
    """Run a boss CLI command and return the CompletedProcess.

    Args:
        args: Command args after 'boss', e.g. ['positions'].
        timeout: Seconds before kill (default: BOSS_CLI_TIMEOUT, 120s).
        check: If True, raise CalledProcessError on non-zero exit.

    Returns:
        subprocess.CompletedProcess with .stdout, .stderr, .returncode.
    """
    if timeout is None:
        timeout = _get_timeout()

    cmd = ["boss"] + args
    cmd_str = " ".join(cmd)
    log.info("boss-cli executing: %s (timeout=%ds)", cmd_str, timeout)

    t0 = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd(),
            shell=True,  # Windows: .CMD files need shell execution
        )
        elapsed = time.time() - t0
        log.info(
            "boss-cli completed: %s rc=%d elapsed=%.1fs stdout=%d stderr=%d",
            cmd_str,
            result.returncode,
            elapsed,
            len(result.stdout or ""),
            len(result.stderr or ""),
        )
        if check and result.returncode != 0:
            raise subprocess.CalledProcessError(
                result.returncode, cmd, output=result.stdout, stderr=result.stderr
            )
        return result
    except subprocess.TimeoutExpired:
        elapsed = time.time() - t0
        log.error("boss-cli timed out after %.1fs: %s", elapsed, cmd_str)
        raise
    except FileNotFoundError:
        log.error("boss-cli not found on PATH. Install: npm i -g @joohw/boss-cli")
        raise
    except Exception as exc:
        log.warning("boss-cli unexpected error: %s", cmd_str, exc_info=True)
        raise


def _run_json(args: list, timeout: int = None) -> dict:
    """Run a boss CLI command and return {"ok": True, "data": ..., ...}."""
    if not is_available():
        return {"ok": False, "error": "boss-cli 未安装或未启用，请先执行 npm i -g @joohw/boss-cli && boss login"}
    try:
        result = _run(args, timeout=timeout)
        stdout = (result.stdout or "").strip()
        return {
            "ok": True,
            "data": _parse_stdout(stdout),
            "_raw": stdout,
            "_returncode": result.returncode,
            "_stderr": (result.stderr or "").strip(),
        }
    except FileNotFoundError:
        return {"ok": False, "error": "boss-cli 未安装。请执行: npm i -g @joohw/boss-cli"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"boss-cli 命令超时 (>{_get_timeout()}s)，浏览器自动化操作较慢，请重试"}
    except subprocess.CalledProcessError as e:
        return {"ok": False, "error": f"boss-cli 执行失败 (exit={e.returncode}): {e.stderr or e.stdout}"}
    except Exception as e:
        log.exception("boss-cli command failed")
        return {"ok": False, "error": str(e)}


def _parse_stdout(stdout: str):
    """Best-effort: try JSON, then return raw text."""
    if not stdout:
        return ""
    try:
        return json.loads(stdout)
    except (json.JSONDecodeError, TypeError):
        return stdout


# ---------------------------------------------------------------------------
# Position management
# ---------------------------------------------------------------------------

def get_positions() -> list:
    """Get position list from BOSS."""
    result = _run_json(["positions"])
    if result["ok"] and isinstance(result.get("data"), str):
        parsed = _parse_positions_table(result["data"])
        result["data"] = parsed
    return result


def _parse_positions_table(text: str) -> list:
    """Parse ``boss positions`` text output into structured list."""
    if not text:
        return []
    lines = text.strip().split("\n")
    positions = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2:
            status = "unknown"
            name_parts = []
            for part in parts:
                if part in ("开放", "待开放", "已关闭", "open", "pending", "closed"):
                    status = part
                elif part.isdigit() and len(part) <= 2:
                    continue
                else:
                    name_parts.append(part)
            name = " ".join(name_parts)
            if name:
                positions.append({"name": name, "status": status, "_raw": line})
    return positions


def get_position_detail(name: str) -> dict:
    """Fetch position JD detail and cache as .md file."""
    return _run_json(["jd", name])


# ---------------------------------------------------------------------------
# Candidate search
# ---------------------------------------------------------------------------

def search_candidates(
    keyword: str = None,
    job: str = None,
    core: list = None,
    bonus: list = None,
    match: bool = False,
) -> dict:
    """Search candidates via boss search or boss deep-search."""
    has_deep = job or core or bonus or match
    if has_deep:
        args = ["deep-search"]
        if keyword:
            args.append(keyword)
        if job:
            args.extend(["--job", job])
        if core:
            for c in core:
                args.extend(["--core", c])
        if bonus:
            for b in bonus:
                args.extend(["--bonus", b])
        if match:
            args.append("--match")
        return _run_json(args)
    else:
        args = ["search"]
        if keyword:
            args.append(keyword)
        return _run_json(args)


# ---------------------------------------------------------------------------
# Chat management
# ---------------------------------------------------------------------------

def get_chat_list(unread_only: bool = False) -> list:
    """Get chat list from BOSS."""
    args = ["list"]
    if unread_only:
        args.append("--unread")
    result = _run_json(args)
    if result["ok"] and isinstance(result.get("data"), str):
        parsed = _parse_chat_list(result["data"])
        result["data"] = parsed
    return result


def _parse_chat_list(text: str) -> list:
    """Parse ``boss list`` text output into structured list."""
    if not text:
        return []
    lines = text.strip().split("\n")
    chats = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        chats.append({"name": line, "unread": 0, "_raw": line})
    return chats


def open_chat(name: str, index: int = None, unread: bool = False, strict: bool = False) -> dict:
    """Open a conversation with a candidate."""
    args = ["chat", name]
    if index is not None:
        args.extend(["--index", str(index)])
    if unread:
        args.append("--unread")
    if strict:
        args.append("--strict")
    return _run_json(args)


def send_message(text: str, request_resume: bool = False) -> dict:
    """Send a text message in the current chat."""
    args = ["send", "--text", text]
    if request_resume:
        args.append("--request-resume")
    return _run_json(args)


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

VALID_ACTIONS = {
    "resume", "not-fit", "remark", "agree-resume",
    "request-attachment-resume", "history", "wechat",
}


def do_action(action: str, remark: str = None) -> dict:
    """Execute an action on the current candidate."""
    if action not in VALID_ACTIONS:
        return {
            "ok": False,
            "error": f"无效操作: {action}。支持: {', '.join(sorted(VALID_ACTIONS))}",
        }
    args = ["action", action]
    if remark:
        if action != "remark":
            log.warning("--remark provided but action is %s, ignoring", action)
        else:
            args.extend(["--remark", remark])
    return _run_json(args)


# ---------------------------------------------------------------------------
# Resume preview
# ---------------------------------------------------------------------------

def preview_resume(name: str) -> dict:
    """Preview a candidate's online resume."""
    return _run_json(["preview", name])


# ---------------------------------------------------------------------------
# Greeting
# ---------------------------------------------------------------------------

def greet_candidate(name: str, job: str = None) -> dict:
    """Greet a candidate from the current recommend/deep-search list.

    NOTE: Consumes greeting quota. Costs are high. Use carefully.
    """
    args = ["greet", name]
    if job:
        args.extend(["--job", job])
    return _run_json(args)
