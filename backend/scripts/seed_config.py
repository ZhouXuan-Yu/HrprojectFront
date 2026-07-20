"""Seed config tables: notify templates, audit logs, mail accounts."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from datetime import datetime

app = create_app('development')

def seed_config():
    with app.app_context():
        # ── Notify templates ──
        from app.models.auxiliary import NotifyTemplate
        if not NotifyTemplate.active().first():
            db.session.add_all([
                NotifyTemplate(
                    template_name='面试邀请通知', template_type='面试',
                    send_method='飞书 + 短信',
                    subject='面试邀请 - {{position}}',
                    body='{{candidate}} 您好，诚邀您参加 {{position}} 的面试。\n时间：{{time}}\n方式：{{method}}\n地点：{{location}}',
                    status=1,
                ),
                NotifyTemplate(
                    template_name='Offer 发送模板', template_type='Offer',
                    send_method='邮件',
                    subject='Offer Letter - {{position}}',
                    body='恭喜您通过面试！正式 Offer 详情请查收附件。\n如有疑问请联系 HR。',
                    status=1,
                ),
                NotifyTemplate(
                    template_name='未通过通知', template_type='淘汰',
                    send_method='短信',
                    subject='面试结果通知',
                    body='感谢您参加 {{position}} 面试，很遗憾本次未能匹配。期望未来有机会合作！',
                    status=1,
                ),
                NotifyTemplate(
                    template_name='面试提醒（前一天）', template_type='提醒',
                    send_method='飞书 + 短信',
                    subject='面试提醒',
                    body='明天 {{time}} 您有 {{position}} 面试，请准时参加。\n候选人：{{candidate}}\n方式：{{method}}',
                    status=1,
                ),
            ])
            db.session.commit()
            print(f"Notify templates: {NotifyTemplate.active().count()} seeded")

        # ── Mail accounts ──
        from app.models.auxiliary import RecruitMailAccount
        if not RecruitMailAccount.active().filter(RecruitMailAccount.email_address.like('hr-recruit%')).first():
            db.session.add_all([
                RecruitMailAccount(
                    email_address='hr-recruit@company.com', account_name='HR 企业邮箱',
                    imap_host='outlook.office365.com', imap_port=993,
                    mail_type='corp', sync_freq=30, status=1,
                    monitor_folder='INBOX',
                    last_sync_time=datetime(2026, 7, 19, 14, 30),
                ),
                RecruitMailAccount(
                    email_address='hr-recruit@qq.com', account_name='HR QQ邮箱',
                    imap_host='imap.qq.com', imap_port=993,
                    mail_type='qq', sync_freq=60, status=0,
                    monitor_folder='招聘简历',
                    last_sync_time=datetime(2026, 7, 13, 9, 0),
                ),
            ])
            db.session.commit()
            print(f"Mail accounts: {RecruitMailAccount.active().count()} seeded")

        # ── Audit logs ──
        from app.models.auxiliary import AuditLog
        if not AuditLog.active().first():
            db.session.add_all([
                AuditLog(operator_name='张HR', module='面试', action='发起面试',
                         detail='张三 → 高级Java工程师初试，面试官李面试官',
                         operate_time=datetime(2026, 7, 19, 14, 30)),
                AuditLog(operator_name='李面试官', module='面试', action='提交评价',
                         detail='郑一·前端终面·通过',
                         operate_time=datetime(2026, 7, 19, 11, 20)),
                AuditLog(operator_name='张HR', module='需求', action='新建需求',
                         detail='DM2026070005 高级Java工程师·技术部·2人',
                         operate_time=datetime(2026, 7, 19, 10, 5)),
                AuditLog(operator_name='系统', module='邮件', action='自动同步',
                         detail='hr-recruit@company.com 拉取 3 封邮件，识别 2 封简历',
                         operate_time=datetime(2026, 7, 19, 9, 0)),
            ])
            db.session.commit()
            print(f"Audit logs: {AuditLog.active().count()} seeded")

        print("Config seed complete.")

if __name__ == '__main__':
    seed_config()
