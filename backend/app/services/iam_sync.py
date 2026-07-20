"""IAM data sync service.

Syncs orgs (departments), positions, and users from the hr-master IAM
source into local cache tables.  v0.1 uses mock data; the real version
will pull from the IAM database configured via IAM_DB_URL.

Startup + daily cron: call sync_iam_data() to refresh the caches.
"""

import logging

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# In-memory caches (v0.1 – no DB persistence; later replaced with IAM tables)
# ---------------------------------------------------------------------------
_orgs_cache = None
_users_cache = None
_positions_cache = None


# ===========================================================================
# Public API
# ===========================================================================

def sync_iam_data():
    """Sync orgs, positions, users from IAM source to local cache tables.

    v0.1: Startup + daily cron.  Uses mock data for now.
    """
    global _orgs_cache, _users_cache, _positions_cache

    log.info("[MOCK] IAM sync started — loading mock data into caches")
    _orgs_cache = _mock_orgs()
    _users_cache = _mock_users()
    _positions_cache = _mock_positions()
    log.info(
        "[MOCK] IAM sync complete — orgs=%d users=%d positions=%d",
        len(_orgs_cache), len(_users_cache), len(_positions_cache),
    )


def get_orgs():
    """Return department list from local IAM cache."""
    if _orgs_cache is None:
        sync_iam_data()
    return _orgs_cache


def get_users():
    """Return user list from local IAM cache."""
    if _users_cache is None:
        sync_iam_data()
    return _users_cache


def get_positions():
    """Return position list from local IAM cache."""
    if _positions_cache is None:
        sync_iam_data()
    return _positions_cache


# ===========================================================================
# Mock data
# ===========================================================================

def _mock_orgs():
    """Mock department data matching the IamDept model schema."""
    return [
        {
            "dept_id": 1,
            "dept_name": "技术部",
            "parent_dept_id": None,
            "dept_path": "/技术部",
            "sort_num": 1,
            "status": 1,
        },
        {
            "dept_id": 2,
            "dept_name": "产品部",
            "parent_dept_id": None,
            "dept_path": "/产品部",
            "sort_num": 2,
            "status": 1,
        },
        {
            "dept_id": 3,
            "dept_name": "运营部",
            "parent_dept_id": None,
            "dept_path": "/运营部",
            "sort_num": 3,
            "status": 1,
        },
        {
            "dept_id": 4,
            "dept_name": "数据部",
            "parent_dept_id": None,
            "dept_path": "/数据部",
            "sort_num": 4,
            "status": 1,
        },
        {
            "dept_id": 5,
            "dept_name": "财务部",
            "parent_dept_id": None,
            "dept_path": "/财务部",
            "sort_num": 5,
            "status": 1,
        },
    ]


def _mock_users():
    """Mock user data matching the IamUser model schema."""
    return [
        {
            "user_id": 1,
            "username": "liubo",
            "real_name": "刘博",
            "dept_id": 1,
            "dept_name": "技术部",
            "role_code": "dept_manager",
            "email": "liubo@company.com",
            "mobile": "1380001001",
            "feishu_open_id": "ou_liubo",
            "status": 1,
        },
        {
            "user_id": 2,
            "username": "zhanghr",
            "real_name": "张HR",
            "dept_id": 3,
            "dept_name": "运营部",
            "role_code": "hr_specialist",
            "email": "zhanghr@company.com",
            "mobile": "1380001002",
            "feishu_open_id": "ou_zhanghr",
            "status": 1,
        },
        {
            "user_id": 3,
            "username": "chenzong",
            "real_name": "陈总",
            "dept_id": 5,
            "dept_name": "财务部",
            "role_code": "dept_manager",
            "email": "chenzong@company.com",
            "mobile": "1380001003",
            "feishu_open_id": "ou_chenzong",
            "status": 1,
        },
        {
            "user_id": 4,
            "username": "zhoubo",
            "real_name": "周博",
            "dept_id": 2,
            "dept_name": "产品部",
            "role_code": "dept_manager",
            "email": "zhoubo@company.com",
            "mobile": "1380001004",
            "feishu_open_id": "ou_zhoubo",
            "status": 1,
        },
        {
            "user_id": 5,
            "username": "linterviewer",
            "real_name": "李面试官",
            "dept_id": 1,
            "dept_name": "技术部",
            "role_code": "interviewer",
            "email": "li@company.com",
            "mobile": "1380001005",
            "feishu_open_id": "ou_li",
            "status": 1,
        },
        {
            "user_id": 6,
            "username": "winterviewer",
            "real_name": "王面试官",
            "dept_id": 1,
            "dept_name": "技术部",
            "role_code": "interviewer",
            "email": "wang@company.com",
            "mobile": "1380001006",
            "feishu_open_id": "ou_wang",
            "status": 1,
        },
        {
            "user_id": 7,
            "username": "datalead",
            "real_name": "赵博",
            "dept_id": 4,
            "dept_name": "数据部",
            "role_code": "dept_manager",
            "email": "zhaobo@company.com",
            "mobile": "1380001007",
            "feishu_open_id": "ou_zhaobo",
            "status": 1,
        },
    ]


def _mock_positions():
    """Mock position data matching the IamPosition model schema."""
    return [
        {
            "position_id": 1,
            "position_name": "高级Java工程师",
            "dept_id": 1,
            "dept_name": "技术部",
            "status": 1,
        },
        {
            "position_id": 2,
            "position_name": "前端工程师",
            "dept_id": 1,
            "dept_name": "技术部",
            "status": 1,
        },
        {
            "position_id": 3,
            "position_name": "产品经理",
            "dept_id": 2,
            "dept_name": "产品部",
            "status": 1,
        },
        {
            "position_id": 4,
            "position_name": "运营总监",
            "dept_id": 3,
            "dept_name": "运营部",
            "status": 1,
        },
        {
            "position_id": 5,
            "position_name": "数据分析师",
            "dept_id": 4,
            "dept_name": "数据部",
            "status": 1,
        },
    ]
