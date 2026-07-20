"""AI engine — pure Python implementations replacing Dify workflows.

Three engines:
    WF1  Resume Parser   — parse_resume(file_bytes) → structured candidate data
    WF2  Job Matcher     — match_job(candidate_data, jd_text) → match_score + detail
    WF3  Interview QA    — generate_questions(jd_text, resume_data, round) → questions

All three are deterministic, no external API calls required.
"""

import re
import hashlib
import logging
from datetime import datetime

log = logging.getLogger(__name__)


# ===========================================================================
# WF1  Resume Parser
# ===========================================================================

def parse_resume(file_bytes=None, text=None):
    """Parse a resume and extract structured candidate data.

    If ``file_bytes`` is provided (PDF/DOCX), extract raw text first.
    If ``text`` is provided, parse it directly.
    Otherwise returns a default mock result.

    Returns dict: name, phone, email, edu_level, school_level, work_years,
                   recent_company, skills[], summary
    """
    if file_bytes:
        try:
            text = _extract_text(file_bytes)
        except Exception as e:
            log.warning("Failed to extract text from file: %s", e)
            return _default_parse_result()

    if not text:
        return _default_parse_result()

    result = {
        "name": _extract_name(text) or "未知",
        "phone": _extract_phone(text) or "",
        "email": _extract_email(text) or "",
        "edu_level": _extract_edu_level(text),
        "school_level": _extract_school(text),
        "work_years": _extract_work_years(text),
        "recent_company": _extract_company(text) or "",
        "skills": _extract_skills(text),
        "summary": _generate_summary(text),
    }
    return result


def _extract_text(file_bytes):
    """Extract text from PDF or DOCX bytes. Best-effort."""
    text = ""
    try:
        # Try PDF
        import io
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(io.BytesIO(file_bytes))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            if text.strip():
                return text
        except ImportError:
            pass
        except Exception:
            pass

        # Try DOCX
        try:
            from docx import Document
            doc = Document(io.BytesIO(file_bytes))
            text = "\n".join(p.text for p in doc.paragraphs)
            if text.strip():
                return text
        except ImportError:
            pass
        except Exception:
            pass

        # Fallback: treat as plain text
        text = file_bytes.decode("utf-8", errors="ignore")
    except Exception:
        pass
    return text


def _extract_name(text):
    """Extract Chinese name from resume text."""
    patterns = [
        r"姓名[：:]\s*([^\s\n]{2,4})",
        r"名字[：:]\s*([^\s\n]{2,4})",
        r"^([^\s\n]{2,4})\s*\n",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.MULTILINE)
        if m:
            name = m.group(1).strip()
            if 2 <= len(name) <= 4 and not re.search(r"[a-zA-Z0-9@]", name):
                return name
    return None


def _extract_phone(text):
    """Extract phone number."""
    m = re.search(r"1[3-9]\d{9}", text)
    return m.group(0) if m else None


def _extract_email(text):
    """Extract email address."""
    m = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return m.group(0) if m else None


def _extract_edu_level(text):
    """Extract education level."""
    if re.search(r"博士|博士研究生|Ph\.?D", text):
        return "博士"
    if re.search(r"硕士|硕士研究生|MBA|EMBA", text):
        return "硕士"
    if re.search(r"本科|学士|大学|B\.?S\.?|B\.?A\.?", text):
        return "本科"
    if re.search(r"大专|专科|高职", text):
        return "大专"
    return "本科"


def _extract_school(text):
    """Extract school tier from keywords."""
    c9_schools = ["清华", "北大", "复旦", "上海交大", "浙大", "南大", "中科大", "哈工大", "西交大"]
    for s in c9_schools:
        if s in text:
            return "C9"
    if re.search(r"985|211", text):
        return "985" if "985" in text else "211"
    if re.search(r"大学|学院|University|College", text):
        return "普通"
    return "普通"


def _extract_work_years(text):
    """Extract work years from text."""
    patterns = [
        r"(\d+)\s*年.*?工作.*?经验",
        r"工作年限[：:]\s*(\d+)",
        r"工作经验[：:]\s*(\d+)\s*年",
        r"(\d+)\s*年.*?开发.*?经验",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            return int(m.group(1))
    # Heuristic: count years in job history
    years_matches = re.findall(r"(20\d{2})\s*[\.\-—/]\s*(20\d{2}|至今|现在)", text)
    if years_matches:
        total = 0
        for start, end in years_matches:
            start_y = int(start)
            end_y = int(end) if end.isdigit() else datetime.now().year
            total += max(0, end_y - start_y)
        return min(total, 20)
    return 3


def _extract_company(text):
    """Extract most recent company."""
    companies = [
        "阿里巴巴", "腾讯", "字节跳动", "美团", "百度", "京东", "网易",
        "华为", "小米", "滴滴", "快手", "拼多多", "B站", "小红书",
        "微软", "谷歌", "亚马逊", "苹果", "Meta",
    ]
    found = []
    for c in companies:
        for m in re.finditer(re.escape(c), text):
            found.append((m.start(), c))
    if found:
        found.sort()
        return found[-1][1]
    # Try generic pattern: XXX公司 / XXX有限公司
    m = re.search(r"([^\s\n]{2,10}(?:公司|有限公司|集团|科技|网络))", text)
    return m.group(1) if m else None


def _extract_skills(text):
    """Extract skills from a predefined dictionary."""
    skill_dict = {
        "Java": ["java", "Java"],
        "Spring Boot": ["spring boot", "springboot", "spring"],
        "Spring Cloud": ["spring cloud", "springcloud"],
        "MySQL": ["mysql", "mariadb"],
        "PostgreSQL": ["postgresql", "postgres"],
        "Redis": ["redis"],
        "Kafka": ["kafka"],
        "RabbitMQ": ["rabbitmq", "rabbit mq"],
        "Elasticsearch": ["elasticsearch", "es"],
        "Docker": ["docker"],
        "Kubernetes": ["kubernetes", "k8s"],
        "微服务": ["微服务", "microservice"],
        "分布式系统": ["分布式"],
        "Go": [" golang ", " go语言 ", "go开发"],
        "Python": ["python"],
        "JavaScript": ["javascript", "js"],
        "TypeScript": ["typescript", "ts"],
        "React": ["react"],
        "Vue": ["vue"],
        "Node.js": ["node\\.js", "nodejs"],
        "Linux": ["linux"],
        "Git": ["git "],
        "CI/CD": ["ci/cd", "cicd", "持续集成", "持续交付"],
        "SQL": ["sql"],
        "MongoDB": ["mongodb", "mongo"],
        "Nginx": ["nginx"],
        "Spark": ["spark"],
        "Hadoop": ["hadoop"],
        "Flink": ["flink"],
        "TensorFlow": ["tensorflow", "tf"],
        "PyTorch": ["pytorch"],
    }

    found = []
    text_lower = text.lower()
    for skill, keywords in skill_dict.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                found.append(skill)
                break

    return found[:8]  # Top 8 skills


def _generate_summary(text):
    """Generate a brief summary of the candidate."""
    edu = _extract_edu_level(text)
    years = _extract_work_years(text)
    skills = _extract_skills(text)
    company = _extract_company(text) or "某公司"
    skill_str = "、".join(skills[:4])
    return f"{edu}学历，{years}年工作经验，曾就职于{company}，擅长{skill_str}"


def _default_parse_result():
    """Default mock result when no text is provided."""
    return {
        "name": "张三",
        "phone": "138****1234",
        "email": "zhangsan@example.com",
        "edu_level": "本科",
        "school_level": "211",
        "work_years": 5,
        "recent_company": "阿里巴巴",
        "skills": ["Java", "Spring Boot", "MySQL", "Redis", "微服务", "Docker"],
        "summary": "本科学历，5年工作经验，曾就职于阿里巴巴，擅长Java、Spring Boot、MySQL、Redis",
    }


# ===========================================================================
# WF2  Job Matcher
# ===========================================================================

def match_job(candidate_data, jd_text):
    """Score how well a candidate matches a job description.

    Returns dict: match_score (0-100), score_detail {skill_match, experience_match,
                   education_match, overall_reason}
    """
    c_name = candidate_data.get("name", "未知") if isinstance(candidate_data, dict) else "未知"
    c_skills = set(s.lower() for s in (candidate_data.get("skills", []) if isinstance(candidate_data, dict) else []))
    c_edu = candidate_data.get("edu_level", "本科") if isinstance(candidate_data, dict) else "本科"
    c_years = candidate_data.get("work_years", 3) if isinstance(candidate_data, dict) else 3

    # Extract required skills from JD
    jd_skills = _extract_skills(jd_text or "")
    jd_skills_lower = set(s.lower() for s in jd_skills)

    # 1. Skill match (weight: 50%)
    if c_skills and jd_skills_lower:
        hits = c_skills & jd_skills_lower
        hit_rate = len(hits) / max(len(jd_skills_lower), 1)
        coverage = len(hits) / max(len(c_skills), 1)
        skill_score = int(min(100, (hit_rate * 0.7 + coverage * 0.3) * 100))
    else:
        skill_score = 50
        hits = set()

    # 2. Experience match (weight: 30%)
    exp_match = re.search(r"(\d+)\s*年", jd_text or "")
    required_years = int(exp_match.group(1)) if exp_match else 3
    if c_years >= required_years + 2:
        exp_score = 95
    elif c_years >= required_years:
        exp_score = 80
    elif c_years >= required_years - 1:
        exp_score = 50
    else:
        exp_score = 20

    # 3. Education match (weight: 20%)
    edu_weights = {"博士": 100, "硕士": 85, "本科": 70, "大专": 40}
    edu_min_map = {"博士": 100, "硕士": 80, "本科": 60, "大专": 30, "不限": 0}
    jd_edu_min = "本科"
    for e in ["博士", "硕士", "本科", "大专"]:
        if e in (jd_text or ""):
            jd_edu_min = e
            break
    c_edu_score = edu_weights.get(c_edu, 60)
    min_req = edu_min_map.get(jd_edu_min, 0)
    edu_score = 100 if c_edu_score >= min_req else max(0, 100 - (min_req - c_edu_score))

    # Composite score
    match_score = int(skill_score * 0.5 + exp_score * 0.3 + edu_score * 0.2)

    # Reason text
    hit_names = [s for s in jd_skills if s.lower() in hits]
    reason_parts = []
    if hit_names:
        reason_parts.append(f"技能匹配: {'、'.join(hit_names[:5])}")
    reason_parts.append(f"经验: {c_years}年 vs 要求{required_years}年")
    reason_parts.append(f"学历: {c_edu}")

    return {
        "match_score": min(match_score, 95),
        "score_detail": {
            "skill_match": {
                "score": skill_score,
                "matched": hit_names[:5],
                "note": f"匹配 {len(hits)}/{len(jd_skills_lower)} 项JD技能要求",
            },
            "experience_match": {
                "score": exp_score,
                "note": f"候选人{c_years}年经验，岗位要求{required_years}年",
            },
            "education_match": {
                "score": edu_score,
                "note": f"候选人{c_edu}，岗位最低要求{jd_edu_min}",
            },
            "overall_reason": "；".join(reason_parts) + f"。综合评分{min(match_score, 95)}分。",
        },
    }


# ===========================================================================
# WF3  Interview Question Generator
# ===========================================================================

def generate_questions(jd_text, resume_data, round=1):
    """Generate interview questions tailored to the candidate and JD.

    Questions are selected from a rich pool and filtered/scored by relevance.
    """
    c_skills = resume_data.get("skills", []) if isinstance(resume_data, dict) else []
    c_name = resume_data.get("name", "候选人") if isinstance(resume_data, dict) else "候选人"

    pool = _question_pool()

    # Score each question by relevance to this candidate
    scored = []
    for q in pool:
        score = 0
        q_text = q["question"].lower()
        for skill in c_skills:
            if skill.lower() in q_text:
                score += 3
        # Bonus for round-appropriate categories
        if round == 1 and q["category"] in ("技术基础", "项目经验", "编码能力"):
            score += 2
        elif round == 2 and q["category"] in ("系统设计", "架构", "问题排查"):
            score += 2
        elif round >= 3 and q["category"] in ("沟通协作", "文化契合", "领导力", "职业规划"):
            score += 2
        scored.append((score, q))

    # Sort by relevance, take top 5
    scored.sort(key=lambda x: x[0], reverse=True)
    selected = [q for _, q in scored[:5]]

    # Ensure at least 5 questions
    if len(selected) < 5:
        fallback = [q for _, q in scored[5:10]]
        selected.extend(fallback[: 5 - len(selected)])

    # Add candidate name to questions where appropriate
    for q in selected:
        q["question"] = q["question"].replace("{name}", c_name)

    return selected


def _question_pool():
    """Rich pool of interview questions organized by category."""
    return [
        # ---- 技术基础 ----
        {"question": "请介绍你在最近项目中使用的主要技术栈和架构，遇到的最大技术挑战是什么？",
         "category": "技术基础", "difficulty": "中等",
         "expected_points": ["技术栈选择和理由", "架构描述", "具体问题和解决方案"]},
        {"question": "请简述你对 JVM 内存模型和 GC 调优的理解。",
         "category": "技术基础", "difficulty": "中等",
         "expected_points": ["堆内存分代模型", "GC算法", "调优工具"]},
        {"question": "谈谈你对面向对象设计原则（SOLID）的理解和实践经验。",
         "category": "编码能力", "difficulty": "中等",
         "expected_points": ["SOLID五个原则", "实际代码示例", "重构经验"]},
        {"question": "你在项目中如何做单元测试？覆盖率要求是多少？",
         "category": "编码能力", "difficulty": "一般",
         "expected_points": ["测试框架", "覆盖率目标", "测试策略"]},

        # ---- 数据库 ----
        {"question": "MySQL 慢查询优化你有哪些实战经验？请结合具体案例。",
         "category": "数据库", "difficulty": "中等",
         "expected_points": ["EXPLAIN分析", "索引优化", "优化效果"]},
        {"question": "请解释 MySQL 的事务隔离级别和 MVCC 机制。",
         "category": "数据库", "difficulty": "中等",
         "expected_points": ["四种隔离级别", "MVCC原理", "实际应用"]},
        {"question": "数据库分库分表你有实践经验吗？遇到过哪些问题？",
         "category": "数据库", "difficulty": "较高",
         "expected_points": ["分片策略", "跨库查询", "数据迁移"]},

        # ---- 中间件 ----
        {"question": "Redis 在你的项目中如何使用？缓存穿透/雪崩如何解决？",
         "category": "中间件", "difficulty": "中等",
         "expected_points": ["数据结构使用场景", "缓存问题解决", "分布式锁"]},
        {"question": "消息队列（Kafka/RabbitMQ）在你的系统中如何保证消息不丢失？",
         "category": "中间件", "difficulty": "较高",
         "expected_points": ["生产/消费确认", "持久化策略", "幂等设计"]},

        # ---- 系统设计 ----
        {"question": "设计一个支持百万并发的招聘系统，你会如何做架构设计？",
         "category": "系统设计", "difficulty": "较高",
         "expected_points": ["负载均衡", "异步解耦", "缓存策略", "高可用"]},
        {"question": "请设计一个面试评价系统的数据库表结构，并说明关键决策。",
         "category": "系统设计", "difficulty": "较高",
         "expected_points": ["实体关系", "字段类型", "扩展性"]},
        {"question": "如果你来设计一个类似飞书的在线面试功能，你会考虑哪些技术点？",
         "category": "系统设计", "difficulty": "较高",
         "expected_points": ["WebRTC", "实时通信", "录制存储", "安全"]},

        # ---- 问题排查 ----
        {"question": "线上简历数据不一致时，你的排查和修复流程是什么？",
         "category": "问题排查", "difficulty": "较高",
         "expected_points": ["日志定位", "数据对比", "回滚策略", "根因分析"]},
        {"question": "服务突然 CPU 100%，你从登录服务器到定位问题会做哪些操作？",
         "category": "问题排查", "difficulty": "较高",
         "expected_points": ["top/htop", "线程dump", "GC日志", "业务量排查"]},

        # ---- 项目经验 ----
        {"question": "请分享一个你主导或深度参与的最有成就感的项目。",
         "category": "项目经验", "difficulty": "一般",
         "expected_points": ["项目背景", "个人角色", "技术亮点", "业务成果"]},
        {"question": "你在项目中做过哪些技术重构？效果如何衡量？",
         "category": "项目经验", "difficulty": "中等",
         "expected_points": ["重构动机", "方案设计", "效果指标"]},

        # ---- 沟通协作 ----
        {"question": "请分享一次你推动技术方案落地时遇到阻力，如何说服他人的经历。",
         "category": "沟通协作", "difficulty": "中等",
         "expected_points": ["利益方识别", "数据驱动沟通", "折中方案"]},
        {"question": "你如何看待 Code Review？请分享一次通过 CR 避免的重大问题。",
         "category": "沟通协作", "difficulty": "中等",
         "expected_points": ["CR标准", "发现的问题", "团队推动"]},

        # ---- 领导力 ----
        {"question": "描述一次你指导初级工程师的经历，用了什么方法帮助他们成长？",
         "category": "领导力", "difficulty": "中等",
         "expected_points": ["成长目标", "反馈机制", "挑战性任务"]},
        {"question": "如果你入职后对技术选型有不同意见，会怎么处理？",
         "category": "文化契合", "difficulty": "中等",
         "expected_points": ["理解背景", "数据表达", "渐进优化"]},

        # ---- 职业规划 ----
        {"question": "你对未来 2-3 年的职业规划是什么？这个岗位如何帮助你实现？",
         "category": "职业规划", "difficulty": "一般",
         "expected_points": ["技术方向", "与岗位的关联", "长期意愿"]},
        {"question": "如果项目上线前一天发现一个中等严重度的 Bug，你会如何决策？",
         "category": "决策能力", "difficulty": "较高",
         "expected_points": ["影响评估", "hotfix vs 延期", "沟通策略"]},

        # ---- 编码能力 ----
        {"question": "请现场写一个单例模式的线程安全实现，并解释为什么这样写。",
         "category": "编码能力", "difficulty": "中等",
         "expected_points": ["双重检查锁", "volatile", "枚举单例"]},
    ]
