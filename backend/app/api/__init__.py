from flask import Blueprint
from flask import current_app


def register_blueprints(app):
    """Register all API blueprints."""
    from app.api.auth import bp as auth_bp
    from app.api.dashboard import bp as dashboard_bp
    from app.api.demand import bp as demand_bp
    from app.api.talent import bp as talent_bp
    from app.api.interview import bp as interview_bp
    from app.api.ai import bp as ai_bp
    from app.api.config import bp as config_bp
    from app.api.boss import bp as boss_bp
    from app.api.health import bp as health_bp
    from app.api.hire import bp as hire_bp
    from app.api.dedup import bp as dedup_bp
    from app.api.confirm import bp as confirm_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(demand_bp, url_prefix='/api/demand')
    app.register_blueprint(talent_bp, url_prefix='/api/talent')
    app.register_blueprint(interview_bp, url_prefix='/api/interview')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(config_bp, url_prefix='/api/config')
    app.register_blueprint(boss_bp, url_prefix='/api/boss')
    app.register_blueprint(health_bp, url_prefix='/api/health')
    app.register_blueprint(hire_bp, url_prefix='/api/hire')
    app.register_blueprint(dedup_bp, url_prefix='/api/dedup')
    # 候选人确认页（GET /confirm/<token>）与提交（POST /api/confirm/<token>），无需登录
    app.register_blueprint(confirm_bp)
