# tests/test_app.py
import pytest
from chat.app import app, db, Nickname, Message


@pytest.fixture
def client():
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


def test_login(client):
    response = client.post('/login', json={'nickname': 'testuser'})
    assert response.json['status'] == 'success'

    existing_nickname = Nickname.query.filter_by(nickname='testuser').first()
    assert existing_nickname is not None


def test_get_messages(client):
    message = Message(nickname='testuser', msg='Hello, world!')
    db.session.add(message)
    db.session.commit()

    response = client.get('/get_messages')
    assert response.status_code == 200
    assert len(response.json['messages']) > 0
    assert response.json['messages'][0]['msg'] == 'Hello, world!'

def test_clear_chat(client):
    message = Message(nickname='testuser', msg='Message to clear')
    db.session.add(message)
    db.session.commit()

    assert Message.query.count() == 1

    response = client.post('/clear_chat', json={'secret': 'fwenfwo-23498##12ojdp_emfw0o'})
    assert response.json['status'] == 'success'

    assert Message.query.count() == 0
