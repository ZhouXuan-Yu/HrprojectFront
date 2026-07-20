"""Scoring utilities: profile score, match score, decay, comprehensive ranking."""
from datetime import datetime, timezone


def calc_decay_coefficient(storage_time, now=None):
    """
    Calculate time-decay coefficient for a resume.
    <= 30 days: 1.0
    30-90 days: 0.85
    > 90 days: 0.70
    """
    if now is None:
        now = datetime.now(timezone.utc)
    if storage_time.tzinfo is None:
        storage_time = storage_time.replace(tzinfo=timezone.utc)

    days = (now - storage_time).days
    if days <= 30:
        return 1.0
    elif days <= 90:
        return 0.85
    else:
        return 0.70


def calc_profile_score(edu_level=0, school_level=0, work_years=0, big_company=0, cert_count=0):
    """
    Static profile score using hard rules (0-100 scale).

    Edu: 0=none, 1=college, 2=bachelor, 3=master, 4=phd
    School: 0=none, 1=ordinary, 2=211, 3=985, 4=C9/overseas-top
    WorkYears: actual integer
    BigCompany: 0=no, 1=yes
    CertCount: integer count
    """
    score = 0
    # Education (max 25)
    edu_scores = {0: 0, 1: 5, 2: 15, 3: 20, 4: 25}
    score += edu_scores.get(edu_level, 0)
    # School tier (max 20)
    school_scores = {0: 0, 1: 5, 2: 10, 3: 15, 4: 20}
    score += school_scores.get(school_level, 0)
    # Work years (max 25)
    if work_years >= 10:
        score += 25
    elif work_years >= 5:
        score += 20
    elif work_years >= 3:
        score += 15
    elif work_years >= 1:
        score += 8
    # Big company (max 20)
    score += 20 if big_company else 0
    # Certificates (max 10)
    score += min(cert_count * 3, 10)
    return min(score, 100)


def calc_recommend_score(profile_score, match_score, storage_time, now=None):
    """
    Comprehensive recommendation score.
    Pool search: profileScore * 0.1 + matchScore * decay * 0.9
    """
    decay = calc_decay_coefficient(storage_time, now)
    return round(profile_score * 0.1 + match_score * decay * 0.9, 1)


def calc_direct_score(profile_score, match_score):
    """
    Direct application score (no decay).
    profileScore * 0.1 + matchScore * 0.9
    """
    return round(profile_score * 0.1 + match_score * 0.9, 1)


def profile_grade(score):
    """Convert numeric score to letter grade."""
    if score >= 95:
        return 'A+'
    elif score >= 85:
        return 'A'
    elif score >= 80:
        return 'A-'
    elif score >= 75:
        return 'B+'
    elif score >= 70:
        return 'B'
    elif score >= 65:
        return 'B-'
    elif score >= 60:
        return 'C+'
    else:
        return 'C'


def match_color(score):
    """Score color: >=80 green, 60-79 orange, <60 gray."""
    if score >= 80:
        return 'score-high'
    elif score >= 60:
        return 'score-mid'
    else:
        return 'score-low'
