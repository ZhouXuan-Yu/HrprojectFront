from flask import Blueprint, jsonify
from app.utils.response import error as err_resp
from app.utils.response import AppError


errors_bp = Blueprint('errors', __name__)


@errors_bp.app_errorhandler(AppError)
def handle_app_error(e):
    return err_resp(e.code, e.message, e.status_code)


@errors_bp.app_errorhandler(400)
def handle_400(e):
    return err_resp('BAD_REQUEST', str(e.description) if e.description else '请求参数有误', 400)


@errors_bp.app_errorhandler(401)
def handle_401(e):
    return err_resp('UNAUTHORIZED', '请先登录', 401)


@errors_bp.app_errorhandler(403)
def handle_403(e):
    return err_resp('FORBIDDEN', '无权限访问', 403)


@errors_bp.app_errorhandler(404)
def handle_404(e):
    return err_resp('NOT_FOUND', '资源不存在', 404)


@errors_bp.app_errorhandler(405)
def handle_405(e):
    return err_resp('METHOD_NOT_ALLOWED', '请求方法不允许', 405)


@errors_bp.app_errorhandler(500)
def handle_500(e):
    import logging
    logging.getLogger('app.error').error(
        'Unhandled 500: %s', getattr(e, 'original_exception', e), exc_info=True)
    return err_resp('INTERNAL_ERROR', '服务器内部错误', 500)
