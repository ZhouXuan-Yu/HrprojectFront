"""SMTP mail sender — sends notification emails through the configured
recruit mailbox (the same account used for IMAP resume collection).

SMTP host is derived from the account's mail_type / domain, with env
overrides MAIL_SMTP_HOST / MAIL_SMTP_PORT / MAIL_SMTP_SSL for custom
corporate servers.
"""
import logging
import os
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid

log = logging.getLogger(__name__)

# mail_type / domain → (smtp_host, port, use_ssl)
_SMTP_PRESETS = {
    'qq': ('smtp.qq.com', 465, True),
    'qq.com': ('smtp.qq.com', 465, True),
    'exmail.qq.com': ('smtp.exmail.qq.com', 465, True),
    '163': ('smtp.163.com', 465, True),
    '163.com': ('smtp.163.com', 465, True),
    '126.com': ('smtp.126.com', 465, True),
    'gmail': ('smtp.gmail.com', 587, False),
    'gmail.com': ('smtp.gmail.com', 587, False),
    'corp': ('smtp.exmail.qq.com', 465, True),  # 腾讯企业邮箱
}


def _smtp_config(account):
    """Resolve (host, port, use_ssl) for a RecruitMailAccount."""
    host = os.environ.get('MAIL_SMTP_HOST')
    port = int(os.environ.get('MAIL_SMTP_PORT', '465'))
    use_ssl = os.environ.get('MAIL_SMTP_SSL', 'true').lower() != 'false'
    if host:
        return host, port, use_ssl

    mail_type = (getattr(account, 'mail_type', None) or '').strip().lower()
    if mail_type in _SMTP_PRESETS:
        return _SMTP_PRESETS[mail_type]

    domain = (account.email_address or '').split('@')[-1].lower()
    if domain in _SMTP_PRESETS:
        return _SMTP_PRESETS[domain]
    # 企业邮箱常见默认
    return f'smtp.{domain}', 465, True


def _pick_sender_account(account_id=None):
    """Pick a sender account: explicit id, else first active with a password."""
    from app.models.auxiliary import RecruitMailAccount
    q = RecruitMailAccount.active().filter(RecruitMailAccount.status == 1)
    if account_id:
        acct = q.filter_by(id=account_id).first()
        if acct:
            return acct
    return (q.filter(RecruitMailAccount.password_encrypted.isnot(None))
             .order_by(RecruitMailAccount.id).first())


def _log_mail(account, to, subject, mail_type, ok, message):
    """外发邮件落日志（best-effort，绝不影响发送主流程）。"""
    try:
        from app.models.auxiliary import MailLog
        from app.extensions import db
        db.session.add(MailLog(
            sender_account_id=getattr(account, 'id', None),
            sender_email=getattr(account, 'email_address', None) or '(未配置)',
            recipient=to,
            subject=subject[:250],
            mail_type=mail_type,
            status=1 if ok else 0,
            error_msg=None if ok else str(message)[:500],
        ))
        db.session.commit()
    except Exception as exc:
        log.warning("mail log persist failed: %s", exc)
        try:
            from app.extensions import db
            db.session.rollback()
        except Exception:
            pass


def send_mail(to, subject, html_body, text_body=None, account_id=None,
              sender_name='招聘中心', mail_type='other'):
    """Send an HTML email via the configured recruit mailbox.

    Returns (ok: bool, message: str). Never raises — callers treat
    notification delivery as best-effort.
    """
    account = None
    try:
        account = _pick_sender_account(account_id)
        if not account:
            return False, '未配置可用的发件邮箱（需要有密码/授权码的启用账号）'

        from app.services.email_sync_service import _get_password
        password = _get_password(account)
        if not password:
            return False, f'发件邮箱 {account.email_address} 未配置密码/授权码'

        host, port, use_ssl = _smtp_config(account)

        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr((str(Header(sender_name, 'utf-8')), account.email_address))
        msg['To'] = to
        msg['Subject'] = Header(subject, 'utf-8')
        # 缺 Date/Message-ID 的邮件在收件箱里时间显示为空、排序沉底，易被当成"没收到"
        msg['Date'] = formatdate(localtime=True)
        msg['Message-ID'] = make_msgid('hr-recruit')
        if text_body:
            msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, timeout=20)
        else:
            server = smtplib.SMTP(host, port, timeout=20)
            server.starttls()
        try:
            server.login(account.email_address, password)
            server.sendmail(account.email_address, [to], msg.as_string())
        finally:
            try:
                server.quit()
            except Exception:
                pass

        log.info("Mail sent via %s to %s: %s", account.email_address, to, subject)
        _log_mail(account, to, subject, mail_type, True, '发送成功')
        return True, '发送成功'
    except smtplib.SMTPAuthenticationError as exc:
        log.error("SMTP auth failed: %s", exc)
        _log_mail(account, to, subject, mail_type, False, exc)
        return False, f'发件认证失败，请检查邮箱授权码: {exc}'
    except Exception as exc:
        log.error("SMTP send failed: %s", exc, exc_info=True)
        _log_mail(account, to, subject, mail_type, False, exc)
        return False, f'发送失败: {exc}'
