"""Tests for the auth API (/api/auth/*)."""


class TestAuth:
    """Authentication endpoint tests.

    Covers login, invalid credentials, token verification, and
    middleware-enforced authentication on protected endpoints.
    """

    def test_login_valid(self, client):
        """POST /api/auth/login with admin role returns 200 and a token."""
        resp = client.post('/api/auth/login', json={'role': 'admin'})
        assert resp.status_code == 200
        body = resp.get_json()
        assert 'data' in body
        data = body['data']
        assert 'token' in data, 'Response should contain a JWT token'
        assert data['user']['role'] == 'admin'
        assert 'menus' in data

    def test_login_invalid_role(self, client):
        """POST /api/auth/login with an unknown role returns 400."""
        resp = client.post('/api/auth/login', json={'role': 'bogus_role'})
        assert resp.status_code == 400
        body = resp.get_json()
        assert 'error' in body
        assert body['error']['code'] == 'INVALID_ROLE'

    def test_no_token_returns_401(self, client):
        """GET /api/dashboard/kpi without Authorization header returns 401.

        /api/dashboard/kpi is a protected endpoint that requires a valid
        JWT token. This test verifies the auth middleware rejects requests
        that carry no token.
        """
        resp = client.get('/api/dashboard/kpi')
        assert resp.status_code == 401
        body = resp.get_json()
        assert body['error']['code'] == 'UNAUTHORIZED'
        assert '请先登录' in body['error']['message']

    def test_invalid_token_returns_401(self, client):
        """GET /api/dashboard/kpi with a malformed/bogus token returns 401."""
        resp = client.get(
            '/api/dashboard/kpi',
            headers={'Authorization': 'Bearer this.is.a.bad.token'},
        )
        assert resp.status_code == 401
        body = resp.get_json()
        assert body['error']['code'] == 'INVALID_TOKEN'
        assert '无效令牌' in body['error']['message']

    def test_valid_token_works(self, client, auth_headers):
        """GET /api/dashboard/kpi with a valid JWT token returns 200."""
        resp = client.get('/api/dashboard/kpi', headers=auth_headers)
        assert resp.status_code == 200
        body = resp.get_json()
        assert 'data' in body
