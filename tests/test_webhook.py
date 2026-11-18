import json
from src.models import Event

URL = "/webhooks/customer-events"
BODY = json.dumps({"event": "customer.created", "id": 1}).encode()


def test_valid_signature(client, sign, db_session):
    r = client.post(URL, content=BODY, headers={"X-Signature": sign(BODY)})
    assert r.status_code == 200
    assert r.json() == {"status": "accepted"}
    # background task has saved the event
    assert db_session.query(Event).count() == 1


def test_tampered_payload(client, sign):
    sig = sign(BODY)
    r = client.post(URL, content=BODY + b" ", headers={"X-Signature": sig})
    assert r.status_code == 401
    assert r.json() == {"detail": "Invalid signature"}


def test_wrong_secret(client, sign):
    r = client.post(URL, content=BODY,
                    headers={"X-Signature": sign(BODY, secret="other")})
    assert r.status_code == 401


def test_missing_signature(client):
    assert client.post(URL, content=BODY).status_code == 401