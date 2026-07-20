"""Infrastructure tables: files, t_hr_tag_dict, t_hr_recruit_channel, t_hr_score_rule."""
from sqlalchemy import Column, BigInteger, String, Integer, Text, DECIMAL, JSON
from app.models.base import BaseModel


class File(BaseModel):
    __tablename__ = 'files'

    file_name = Column(String(256), nullable=False, comment='原始文件名')
    file_url = Column(String(512), nullable=False, comment='文件存储地址')
    file_extension = Column(String(16), nullable=True, comment='后缀 pdf/doc/png')
    file_size = Column(BigInteger, nullable=True, comment='文件大小字节')
    biz_type = Column(String(64), nullable=True, comment='业务类型 resume/offer/audio')


class TagDict(BaseModel):
    __tablename__ = 't_hr_tag_dict'

    tag_code = Column(String(64), unique=True, nullable=False, comment='标签唯一编码')
    tag_name = Column(String(64), nullable=False, comment='前端展示标签名')
    tag_category = Column(String(32), nullable=False, comment='一级分类 edu/school/skill/industry/cert/exp')
    tag_sub_category = Column(String(32), nullable=True, comment='二级细分')
    match_weight = Column(DECIMAL(5, 2), nullable=False, default=1.00, comment='JD匹配权重')
    support_target = Column(Integer, nullable=False, comment='1仅简历 2仅员工 3通用')
    sort_num = Column(Integer, nullable=False, default=0, comment='排序号')
    remark = Column(String(512), nullable=True, comment='备注/解析规则')
    status = Column(Integer, nullable=False, default=1, comment='1启用 0停用')


class RecruitChannel(BaseModel):
    __tablename__ = 't_hr_recruit_channel'

    channel_name = Column(String(50), nullable=False, comment='渠道名称')
    channel_type = Column(Integer, nullable=False, comment='1官网 2第三方 3内推')
    status = Column(Integer, nullable=False, default=1, comment='1启用 0停用')


class ScoreRule(BaseModel):
    __tablename__ = 't_hr_score_rule'

    score_scene = Column(Integer, nullable=False, comment='1时效分规则 2岗位匹配规则')
    weight_json = Column(JSON, nullable=False, comment='时效衰减+两套分数线')
    pool_min_score = Column(DECIMAL(4, 1), nullable=True, comment='存量简历准入最低分')
    auto_invite_min_score = Column(DECIMAL(4, 1), nullable=True, comment='自动邀约分数线')
    status = Column(Integer, nullable=False, default=1, comment='1启用 0停用')
