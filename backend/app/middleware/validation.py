"""Request validation middleware.

Provides decorators to validate incoming request data with consistent error
responses. All validation errors use the format:

    {"error": {"code": "VALIDATION_ERROR", "message": "...", "fields": {"field_name": "error detail"}}}

Decorators skip validation automatically for GET requests.
"""

from functools import wraps

from flask import request

from app.utils.response import error


def require_fields(*required_fields):
    """Validate that the JSON body contains all required fields.

    Usage::

        @api.route('/candidates', methods=['POST'])
        @require_fields('name', 'phone')
        def create_candidate():
            ...

    Args:
        *required_fields: One or more field names that must be present
            and non-null in the JSON request body.

    Returns:
        400 with structured error if any field is missing or None.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if request.method == 'GET':
                return f(*args, **kwargs)

            body = request.get_json(silent=True) or {}
            missing = [
                field for field in required_fields
                if field not in body or body[field] is None
            ]
            if missing:
                return error(
                    'VALIDATION_ERROR',
                    f'缺少必填字段: {", ".join(missing)}',
                    400,
                    fields={f: 'required' for f in missing},
                )
            return f(*args, **kwargs)
        return wrapper
    return decorator


def validate_enum(field, allowed_values):
    """Validate that a field's value is one of the allowed values.

    Usage::

        @api.route('/candidates/<int:id>/status', methods=['PATCH'])
        @validate_enum('status', ['new', 'contacted', 'interviewed'])
        def update_status(id):
            ...

    Args:
        field: The field name to check in the JSON body.
        allowed_values: Iterable of permitted values.

    Returns:
        400 if the field exists but its value is not allowed.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if request.method == 'GET':
                return f(*args, **kwargs)

            body = request.get_json(silent=True) or {}
            if field in body and body[field] not in allowed_values:
                return error(
                    'VALIDATION_ERROR',
                    f'字段 {field} 的值无效',
                    400,
                    fields={
                        field: f'值 "{body[field]}" 不在允许范围内: {", ".join(allowed_values)}'
                    },
                )
            return f(*args, **kwargs)
        return wrapper
    return decorator


def validate_length(field, min_len=None, max_len=None):
    """Validate that a string field's length is within bounds.

    Usage::

        @api.route('/notes', methods=['POST'])
        @validate_length('content', min_len=1, max_len=5000)
        def create_note():
            ...

    Args:
        field: The field name to check in the JSON body.
        min_len: Minimum character length (inclusive). None means no minimum.
        max_len: Maximum character length (inclusive). None means no maximum.

    Returns:
        400 if the field exists and its length is out of range.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if request.method == 'GET':
                return f(*args, **kwargs)

            body = request.get_json(silent=True) or {}
            if field not in body or body[field] is None:
                return f(*args, **kwargs)

            val = body[field]
            if not isinstance(val, str):
                return error(
                    'VALIDATION_ERROR',
                    f'字段 {field} 必须是字符串类型',
                    400,
                    fields={field: 'not a string'},
                )

            length = len(val)
            detail_parts = []
            if min_len is not None and length < min_len:
                detail_parts.append(f'最少 {min_len} 个字符')
            if max_len is not None and length > max_len:
                detail_parts.append(f'最多 {max_len} 个字符')

            if detail_parts:
                return error(
                    'VALIDATION_ERROR',
                    f'字段 {field} 长度不符合要求',
                    400,
                    fields={field: '; '.join(detail_parts)},
                )
            return f(*args, **kwargs)
        return wrapper
    return decorator
