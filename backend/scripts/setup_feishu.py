"""Enterprise deployment setup script for Feishu/Lark integration.

Checks:
  1. Whether lark-cli is installed and available in PATH
  2. Current auth status (bot identity readiness)
  3. Missing scopes that need to be applied for at open.feishu.cn
  4. Calendar scope application URL
  5. Prints instructions for completing setup

Usage:
    python scripts/setup_feishu.py

Returns a structured JSON report on stdout and a human-readable summary.
"""

import json
import os
import shutil
import subprocess
import sys
from typing import Any, Dict, List


def _run_cli(*args: str, timeout: int = 15) -> Dict[str, Any]:
    """Run lark-cli and return parsed result."""
    cli = shutil.which("lark-cli") or shutil.which("lark-cli.cmd") or "lark-cli"
    full_cmd = [cli] + list(args)
    try:
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        data = None
        if stdout:
            try:
                data = json.loads(stdout)
            except json.JSONDecodeError:
                data = stdout

        return {
            "success": result.returncode == 0,
            "data": data,
            "stdout": stdout,
            "stderr": stderr,
            "returncode": result.returncode,
            "command": " ".join(full_cmd),
        }
    except FileNotFoundError:
        return {"success": False, "data": None, "stdout": "", "stderr": "Binary not found", "returncode": -1, "command": " ".join(full_cmd)}
    except subprocess.TimeoutExpired:
        return {"success": False, "data": None, "stdout": "", "stderr": f"Timeout after {timeout}s", "returncode": -1, "command": " ".join(full_cmd)}
    except Exception as exc:
        return {"success": False, "data": None, "stdout": "", "stderr": str(exc), "returncode": -1, "command": " ".join(full_cmd)}


# ============================================================================
# Checks
# ============================================================================

def check_lark_cli() -> Dict[str, Any]:
    """Check whether lark-cli is installed and report its version."""
    cli_path = shutil.which("lark-cli") or shutil.which("lark-cli.cmd")
    if not cli_path:
        return {
            "status": "missing",
            "path": None,
            "version": None,
            "message": "lark-cli not found in PATH. Install with: npm install -g lark-cli",
        }

    result = _run_cli("--version")
    version = None
    if result["success"]:
        raw = result.get("stdout", "").strip()
        # lark-cli --version output is usually "lark-cli/1.0.65 ..."
        if raw:
            version = raw.split()[0] if " " in raw else raw
        else:
            version = raw

    return {
        "status": "ok" if result["success"] else "error",
        "path": cli_path,
        "version": version,
        "message": f"Found at {cli_path}" + (f" (v{version})" if version else ""),
    }


def check_auth_status() -> Dict[str, Any]:
    """Check lark-cli auth status (bot + user identities)."""
    result = _run_cli("auth", "+status")
    if not result["success"]:
        return {
            "status": "error",
            "bot_ready": False,
            "user_ready": False,
            "details": result.get("stderr", "Unknown error"),
            "raw_data": None,
        }

    data = result.get("data")
    bot_ready = False
    user_ready = False
    details: List[str] = []

    if isinstance(data, dict):
        # Different possible shapes of auth status output
        bot_info = data.get("bot") or data.get("bot_info") or data.get("app") or {}
        user_info = data.get("user") or data.get("user_info") or {}
        identities = data.get("identities") or []

        # Check bot readiness
        if isinstance(identities, list):
            for identity in identities:
                if isinstance(identity, dict):
                    if identity.get("type") == "bot" and identity.get("status") == "ready":
                        bot_ready = True
                    if identity.get("type") == "user" and identity.get("status") == "ready":
                        user_ready = True
        else:
            bot_ready = bool(bot_info)
            user_ready = bool(user_info)

        if bot_ready:
            details.append("Bot identity: READY — can send IM messages")
        else:
            details.append("Bot identity: NOT READY — run `lark-cli auth +login` with bot token")

        if user_ready:
            details.append("User identity: READY — can search contacts")
        else:
            details.append("User identity: NOT READY — need user authorization")

        # Check scopes
        scopes = data.get("scopes") or data.get("scope") or []
        if isinstance(scopes, list) and scopes:
            details.append(f"Scopes ({len(scopes)}): {', '.join(scopes[:10])}")
            if len(scopes) > 10:
                details[-1] += f" ... and {len(scopes) - 10} more"
        else:
            details.append("No scope information available")

    return {
        "status": "ok",
        "bot_ready": bot_ready,
        "user_ready": user_ready,
        "details": details,
        "raw_data": data,
    }


def check_missing_scopes() -> List[Dict[str, Any]]:
    """Identify scopes that are likely missing based on current setup."""
    missing = []

    # Calendar scopes are almost always missing for bot identity
    missing.append({
        "scope": "calendar:calendar",
        "reason": "Bot calendar access — needed for check_freebusy and create_calendar_event",
        "apply_url": "https://open.feishu.cn/app?api_scope=calendar:calendar",
    })

    # im:message.send_as_user is often missing
    missing.append({
        "scope": "im:message.send_as_user",
        "reason": "Send messages as user identity — needed for search_user -> send to searched user",
        "apply_url": "https://open.feishu.cn/app?api_scope=im:message.send_as_user",
    })

    return missing


def check_env_vars() -> Dict[str, Any]:
    """Check Feishu-related environment variables."""
    relevant = {
        "FEISHU_APP_ID": bool(os.getenv("FEISHU_APP_ID")),
        "FEISHU_APP_SECRET": bool(os.getenv("FEISHU_APP_SECRET")),
        "FEISHU_MOCK_MODE": os.getenv("FEISHU_MOCK_MODE", "true"),
        "FEISHU_CLI_TIMEOUT": os.getenv("FEISHU_CLI_TIMEOUT", "30"),
        "FEISHU_RECIPIENT_OPEN_IDS": bool(os.getenv("FEISHU_RECIPIENT_OPEN_IDS")),
        "LARK_CLI_PATH": os.getenv("LARK_CLI_PATH", "(uses PATH lookup)"),
    }
    issues = []

    if relevant.get("FEISHU_RECIPIENT_OPEN_IDS"):
        # Validate as JSON
        raw = os.getenv("FEISHU_RECIPIENT_OPEN_IDS", "")
        try:
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                issues.append("FEISHU_RECIPIENT_OPEN_IDS should be a JSON object (map of name->open_id)")
        except json.JSONDecodeError:
            issues.append("FEISHU_RECIPIENT_OPEN_IDS is not valid JSON")

    if relevant.get("FEISHU_APP_ID") and not relevant.get("FEISHU_APP_SECRET"):
        issues.append("FEISHU_APP_ID is set but FEISHU_APP_SECRET is missing")

    return {
        "status": "ok" if not issues else "warnings",
        "env_vars": relevant,
        "issues": issues,
    }


def check_bot_send() -> Dict[str, Any]:
    """Quick check: can the bot identity send IM messages?"""
    # We avoid actually sending a message — just check if the bot identity is ready
    auth = check_auth_status()
    if auth["bot_ready"]:
        return {
            "status": "ready",
            "message": "Bot identity is ready to send IM messages",
        }
    return {
        "status": "not_ready",
        "message": "Bot identity is not ready — cannot send IM messages",
    }


# ============================================================================
# Main
# ============================================================================

def run_setup_checks() -> Dict[str, Any]:
    """Run all setup checks and return a structured report."""
    report: Dict[str, Any] = {
        "tool": {
            "name": "lark-cli",
        },
        "checks": {},
        "summary": {
            "overall": "unknown",
            "blocking": [],
            "warnings": [],
        },
    }

    # 1. lark-cli availability
    cli_check = check_lark_cli()
    report["tool"] = {
        "name": "lark-cli",
        "path": cli_check["path"],
        "version": cli_check["version"],
        "status": cli_check["status"],
    }
    report["checks"]["lark_cli_installed"] = cli_check

    if cli_check["status"] == "missing":
        report["summary"]["blocking"].append(
            "lark-cli is not installed. Run: npm install -g lark-cli"
        )

    # 2. Auth status
    auth_check = check_auth_status()
    report["checks"]["auth_status"] = auth_check
    report["auth"] = {
        "bot_ready": auth_check.get("bot_ready", False),
        "user_ready": auth_check.get("user_ready", False),
    }

    if not auth_check.get("bot_ready"):
        report["summary"]["blocking"].append(
            "Bot identity is not ready. Run `lark-cli auth +login` or configure app_id/app_secret."
        )
    if not auth_check.get("user_ready"):
        report["summary"]["warnings"].append(
            "User identity is not ready. Some features (contact search) will be unavailable "
            "until user auth is configured."
        )

    # 3. Missing scopes
    missing = check_missing_scopes()
    report["checks"]["missing_scopes"] = missing
    if missing:
        report["summary"]["warnings"].append(
            f"{len(missing)} scope(s) need to be applied for at open.feishu.cn"
        )
        for ms in missing:
            report["summary"]["warnings"].append(
                f"  - {ms['scope']}: {ms['reason']}"
            )

    # 4. Calendar scope URL
    calendar_url = "https://open.feishu.cn/app?api_scope=calendar:calendar"
    report["calendar_scope_url"] = calendar_url
    report["checks"]["calendar_scope"] = {
        "url": calendar_url,
        "instructions": (
            "Go to the Feishu Open Platform console, open your app, "
            "navigate to 'Permissions' -> 'Calendar', add the calendar scopes, "
            "and publish the app version."
        ),
    }

    # 5. Bot send readiness
    bot_check = check_bot_send()
    report["checks"]["bot_send_ready"] = bot_check

    # 6. Env var check
    env_check = check_env_vars()
    report["checks"]["env_vars"] = env_check
    if env_check.get("issues"):
        report["summary"]["warnings"].extend(env_check["issues"])

    # Overall summary
    if report["summary"]["blocking"]:
        report["summary"]["overall"] = "blocked"
    elif report["summary"]["warnings"]:
        report["summary"]["overall"] = "ready_with_warnings"
    else:
        report["summary"]["overall"] = "ready"

    return report


def print_human_readable(report: Dict[str, Any]) -> None:
    """Print a human-readable summary of the setup report."""
    print("=" * 60)
    print("  Feishu / Lark Integration — Setup Report")
    print("=" * 60)
    print()

    # Tool
    tool = report["tool"]
    print(f"  lark-cli:       {tool.get('status', '?')}")
    print(f"  Path:           {tool.get('path', 'N/A')}")
    print(f"  Version:        {tool.get('version', 'N/A')}")
    print()

    # Auth
    auth = report.get("auth", {})
    bot_status = "READY" if auth.get("bot_ready") else "NOT READY"
    user_status = "READY" if auth.get("user_ready") else "NOT READY"
    print(f"  Bot identity:   {bot_status}")
    print(f"  User identity:  {user_status}")
    print()

    # Summary
    summary = report.get("summary", {})
    print(f"  Overall:        {summary.get('overall', 'unknown').upper()}")
    print()

    if summary.get("blocking"):
        print("  [BLOCKING]")
        for item in summary["blocking"]:
            print(f"    - {item}")
        print()

    if summary.get("warnings"):
        print("  [WARNINGS]")
        for item in summary["warnings"]:
            print(f"    - {item}")
        print()

    print(f"  Calendar scope URL:")
    print(f"    {report.get('calendar_scope_url', 'N/A')}")
    print()

    print("  Next steps:")
    print("    If blocked: resolve blocking issues above and re-run this script.")
    print("    If ready:   set FEISHU_MOCK_MODE=false and FEISHU_RECIPIENT_OPEN_IDS")
    print("                in production, then verify by calling feishu_client functions.")
    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Feishu/Lark integration setup checker")
    parser.add_argument("--json", action="store_true", help="Output raw JSON report instead of human-readable")
    args = parser.parse_args()

    report = run_setup_checks()

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_human_readable(report)
