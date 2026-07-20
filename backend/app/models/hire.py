"""Hire tables: t_hr_hire_event, t_hr_offer, t_hr_entry."""
from sqlalchemy import Column, BigInteger, String, Integer, Date, DateTime, Text, JSON
from app.models.base import BaseModel


class HireEvent(BaseModel):
    __tablename__ = 't_hr_hire_event'

    event_no = Column(String(32), unique=True, nullable=False, comment='事件编号')
    process_id = Column(BigInteger, nullable=True, comment='外部流程ID，内调NULL')
    employee_id = Column(BigInteger, nullable=True, comment='内部员工ID，外招NULL')
    offer_id = Column(BigInteger, nullable=True, comment='Offer ID，内调NULL')
    hire_type = Column(Integer, nullable=False, comment='1外部Offer录用 2内部调岗 3离职返聘')
    event_status = Column(Integer, nullable=False, default=0, comment='0待办理 1已生成入职单 2作废')


class Offer(BaseModel):
    __tablename__ = 't_hr_offer'

    offer_no = Column(String(32), unique=True, nullable=False, comment='Offer编号')
    resume_id = Column(BigInteger, nullable=False, comment='简历ID')
    process_id = Column(BigInteger, nullable=False, comment='流程ID')
    demand_id = Column(BigInteger, nullable=False, comment='需求ID')
    last_interview_id = Column(BigInteger, nullable=True, comment='最后一面面试记录ID')
    offer_content = Column(Text, nullable=True, comment='Offer正文')
    salary_json = Column(JSON, nullable=True, comment='薪资/补贴/试用期结构化数据')
    valid_deadline = Column(DateTime, nullable=False, comment='截止时间')
    offer_status = Column(Integer, nullable=False, default=0, comment='0草稿 1已发送 2已接受 3已拒绝 4已过期')
    send_user_id = Column(BigInteger, nullable=False, comment='发放HR')
    send_time = Column(DateTime, nullable=False, comment='发放时间')
    offer_file_id = Column(BigInteger, nullable=True, comment='Offer附件ID')


class Entry(BaseModel):
    __tablename__ = 't_hr_entry'

    entry_no = Column(String(32), unique=True, nullable=False, comment='入职编号')
    event_id = Column(BigInteger, nullable=False, comment='录用事件ID')
    resume_id = Column(BigInteger, nullable=False, comment='简历ID')
    dept_id = Column(BigInteger, nullable=False, comment='入职部门ID')
    position_id = Column(BigInteger, nullable=False, comment='入职岗位ID')
    entry_date = Column(Date, nullable=False, comment='实际入职日期')
    checklist_json = Column(JSON, nullable=True, comment='入职待办/转正记录快照')
