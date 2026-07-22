"""Tests for interview send-offer flow (/api/interview/<id>/offer).

Regression coverage for the "draft trap" bug:
- First send creates an Offer and actually sends it (status: draft -> sent).
- Retrying the same send reuses the existing draft instead of failing
  with DUPLICATE_OFFER.
- A second send after the Offer is already sent blocks with a clear message.
"""

import pytest
from datetime import datetime


def _create_book(client, auth_headers):
    resp = client.post('/api/interview/create', json={
        'candidate': '张三',
        'position': '后端工程师',
        'interviewer': '李四',
        'date': '2026-08-01',
        'time': '10:00',
        'mode_id': '4',
        'mode': '线下',
        'round': '终面(2轮)',
        'address': '北京市朝阳区',
    }, headers=auth_headers)
    assert resp.status_code == 200, f'create interview failed: {resp.get_json()}'
    return resp.get_json()['data']['book_id']


def _pass_interview(app, book_id):
    """Mark the interview as passed (interview_result=1) and link real ids.

    The interview create API stores resume_id/demand_id as 0 in tests;
    the duplicate-offer guard only fires for non-zero ids, so set them here.
    """
    from app.extensions import db
    from app.models.interview import InterviewBook, InterviewRecord

    with app.app_context():
        book = InterviewBook.query.filter_by(id=book_id).first()
        book.resume_id = 8
        book.demand_id = 5
        record = InterviewRecord(
            book_id=book.id,
            process_id=book.process_id,
            interviewer_ids=[1],
            submit_interviewer_id=1,
            is_arrive=1,
            interview_result=1,
        )
        db.session.add(record)
        db.session.commit()


class TestInterviewSendOffer:
    def _send(self, client, auth_headers, book_id):
        return client.post(f'/api/interview/{book_id}/offer',
                           json={'offer_content': '欢迎加入', 'salary_json': {}},
                           headers=auth_headers)

    def test_first_send_actually_sends(self, app, client, auth_headers):
        """Offer ends in status=1 (sent), not stuck as draft."""
        from app.models.hire import Offer

        book_id = _create_book(client, auth_headers)
        _pass_interview(app, book_id)

        resp = self._send(client, auth_headers, book_id)
        assert resp.status_code == 200, f'send offer failed: {resp.get_json()}'
        data = resp.get_json()['data']
        assert data['sent'] is True
        assert data['reused'] is False
        assert data['id'].startswith('OF')

        with app.app_context():
            offer = Offer.query.filter_by(offer_no=data['id']).first()
            assert offer.offer_status == 1  # sent, not draft

    def test_retry_reuses_draft(self, app, client, auth_headers):
        """A leftover draft from a previous attempt is reused, not blocked."""
        from app.extensions import db
        from app.models.hire import Offer
        from app.models.interview import InterviewBook

        book_id = _create_book(client, auth_headers)
        _pass_interview(app, book_id)

        # Simulate the old buggy path: a draft offer left behind
        with app.app_context():
            book = InterviewBook.query.filter_by(id=book_id).first()
            from app.services.hire_service import create_offer
            draft = create_offer({
                'resumeId': book.resume_id,
                'processId': book.process_id,
                'demandId': book.demand_id,
            })
            draft_no = draft['id']

        resp = self._send(client, auth_headers, book_id)
        assert resp.status_code == 200, f'retry send failed: {resp.get_json()}'
        data = resp.get_json()['data']
        assert data['reused'] is True
        assert data['id'] == draft_no  # same offer, not a new one

        with app.app_context():
            offer = Offer.query.filter_by(offer_no=draft_no).first()
            assert offer.offer_status == 1
            # exactly one offer for this candidate+demand
            assert Offer.query.filter_by(
                resume_id=offer.resume_id, demand_id=offer.demand_id,
                is_deleted=0).count() == 1

    def test_already_sent_blocks_with_clear_message(self, app, client, auth_headers):
        """Re-sending an already-sent offer raises DUPLICATE_OFFER with status label."""
        book_id = _create_book(client, auth_headers)
        _pass_interview(app, book_id)

        first = self._send(client, auth_headers, book_id)
        assert first.status_code == 200

        second = self._send(client, auth_headers, book_id)
        assert second.status_code == 400
        body = second.get_json()
        assert body['error']['code'] == 'DUPLICATE_OFFER'
        assert '已发送' in body['error']['message']

    def test_not_evaluated_blocks(self, client, auth_headers):
        """Interview without a passing evaluation cannot send an offer."""
        book_id = _create_book(client, auth_headers)
        resp = self._send(client, auth_headers, book_id)
        assert resp.status_code == 400
        assert resp.get_json()['error']['code'] == 'INVALID_STATE'
