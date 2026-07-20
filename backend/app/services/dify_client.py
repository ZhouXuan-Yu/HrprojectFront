"""AI engine — pure Python implementations (no Dify required).

Three workflows:
    WF1  Resume Parser   — parse_resume(file_bytes) → structured candidate data
    WF2  Job Matcher     — match_job(candidate_data, jd_text) → match_score + detail
    WF3  Interview QA    — generate_questions(jd_text, resume_data, round) → questions

All functions re-exported from the ai_engine module.
"""

from app.services.ai_engine import parse_resume, match_job, generate_questions
