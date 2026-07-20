"""Tests for the hire API (/api/hire/*) — Offer and Entry management."""

import pytest


@pytest.fixture
def created_offer_no(client, auth_headers):
    """Create an offer and return its offer_no (e.g. 'OF202607...')."""
    resp = client.post('/api/hire/offer/create', json={
        'resumeId': 1,
        'processId': 1,
        'demandId': 1,
        'sendUserId': 1,
        'offerContent': '尊敬的候选人，欢迎您加入我司……',
    }, headers=auth_headers)
    assert resp.status_code == 200, f'create offer failed: {resp.get_json()}'
    return resp.get_json()['data']['id']


class TestOffer:
    """Offer and Entry endpoint tests.

    These endpoints create and retrieve Offer and Entry records in the DB.
    All write operations go through the real service layer against the
    in-memory SQLite database.
    """

    def test_create_offer(self, client, auth_headers):
        """POST /api/hire/offer/create returns an id starting with 'OF'."""
        resp = client.post('/api/hire/offer/create', json={
            'resumeId': 1,
            'processId': 1,
            'demandId': 1,
            'sendUserId': 1,
        }, headers=auth_headers)
        assert resp.status_code == 200
        body = resp.get_json()
        assert 'data' in body
        assert body['data']['id'].startswith('OF')
        assert body['data']['created'] is True

    def test_get_offer(self, created_offer_no, client, auth_headers):
        """GET /api/hire/offer/{id} returns offer detail with statusLabel."""
        resp = client.get(
            f'/api/hire/offer/{created_offer_no}',
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert 'data' in body
        data = body['data']
        assert data['id'] == created_offer_no
        assert 'statusLabel' in data
        assert 'sendTime' in data
        assert 'validDeadline' in data

    def test_create_entry(self, client, auth_headers):
        """POST /api/hire/entry/create returns an id starting with 'EN'."""
        resp = client.post('/api/hire/entry/create', json={
            'eventId': 1,
            'resumeId': 1,
            'deptId': 1,
            'positionId': 1,
            'entryDate': '2026-08-01',
        }, headers=auth_headers)
        assert resp.status_code == 200
        body = resp.get_json()
        assert 'data' in body
        assert body['data']['id'].startswith('EN')
        assert body['data']['created'] is True
