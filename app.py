from flask import Flask, render_template, request, jsonify, url_for
from datetime import datetime, timedelta, timezone
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy

import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fwenfwo-23498##12ojdp_emfw0o'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
db = SQLAlchemy(app)
socketio = SocketIO(app)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(50))
    msg = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.now(tz=None))


class Nickname(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(50), unique=True, nullable=False)


# def add_nicknames():
#     nicknames = ['vlad', 'lesha']  # Список никнеймов для добавления
#
#     for nick in nicknames:
#         # Проверяем, нет ли уже такого никнейма в базе
#         existing_nickname = Nickname.query.filter_by(nickname=nick).first()
#         if not existing_nickname:
#             new_nickname = Nickname(nickname=nick)
#             db.session.add(new_nickname)  # Добавляем новый никнейм
#             print(f"Никнейм '{nick}' добавлен в базу данных.")
#         else:
#             print(f"Никнейм '{nick}' уже существует в базе данных.")
#
#     db.session.commit()

with app.app_context():
    db.create_all()
    print("SERVER STARTED----------------")
    # add_nicknames()

    db.session.query(Nickname).delete()
    db.session.commit()
    all_nicknames = db.session.query(Nickname).all()
    nickname_list = [nickname.nickname for nickname in all_nicknames]
    print("Nicknames in the database:", nickname_list)


@app.route('/chat')
def chat():
    return render_template('chat.html')


@app.route('/get_messages')
def get_messages():
    messages = db.session.query(Message).order_by(Message.timestamp).all()
    return jsonify({'messages': [
        {'id': msg.id, 'nickname': msg.nickname, 'msg': msg.msg, 'timestamp': msg.timestamp.isoformat()} for msg in
        messages]})


@app.route('/ping')
def ping():
    return '', 200


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    usernickname = data.get('nickname')

    existing_nickname = db.session.query(Nickname).filter_by(nickname=usernickname).first()

    if existing_nickname:
        return jsonify({'status': 'fail', 'message': 'Никнейм уже используется.'})

    # Добавление никнейма в базу данных
    new_nickname = Nickname(nickname=usernickname)
    db.session.add(new_nickname)
    db.session.commit()

    join_message = f"{usernickname} присоединился к чату."
    new_message = Message(nickname="Система", msg=join_message)
    db.session.add(new_message)
    db.session.commit()
    socketio.emit('new_message', {'nickname': "Система", 'msg': join_message})
    return jsonify({'status': 'success'})


@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    if request.json.get('secret') == 'fwenfwo-23498##12ojdp_emfw0o':  # Защита маршрута
        db.session.query(Message).delete()
        db.session.commit()
        socketio.emit('chat_cleared')  # Emit событие очистки чата
        return jsonify({'status': 'success', 'message': 'Чат очищен'})
    else:
        return jsonify({'status': 'fail', 'message': 'Не авторизовано'})


@app.route('/check_nickname', methods=['GET'])
def check_nickname():
    nickname = request.args.get('nickname')
    existing_nickname = Nickname.query.filter_by(nickname=nickname).first()
    if existing_nickname:
        return jsonify({'exists': True})
    else:
        return jsonify({'exists': False})


@socketio.on('new_message')
def new_message(data):
    nickname = data['nickname']
    msg = data['msg']
    message = Message(nickname=nickname, msg=msg)
    db.session.add(message)
    db.session.commit()
    emit('message', {'id': message.id, 'nickname': nickname, 'msg': msg}, broadcast=True)
    all_nicknames = db.session.query(Nickname).all()
    nickname_list = [nickname.nickname for nickname in all_nicknames]
    print("Nicknames in the database:", nickname_list)

    # Проверка упоминаний никнеймов
    mentioned_users = re.findall(r'@(\w+)', msg)
    for user in mentioned_users:
        print(f"mentioned_users: {user}, type: {type(user)}")
        existing_nickname = Nickname.query.filter_by(nickname=nickname).first()
        if existing_nickname:
            print(f"User finded in db: {user}")
            emit('mentioned', {'user': user, 'message': msg, 'nickname': nickname}, broadcast=True)


@socketio.on('disconnect')
def handle_disconnect():
    print('Пользователь отключился----------------------------------------------------------')


@socketio.on('delete_message')
def delete_message(data):
    message_id = data['id']
    session = db.session()
    message = session.get(Message, message_id)
    now = datetime.now(tz=None)
    diff = now - message.timestamp
    if message and diff < timedelta(minutes=5):
        db.session.delete(message)
        db.session.commit()
        emit('message_deleted', {'id': message_id}, broadcast=True)
    else:
        emit('message_delete_failed', {'id': message_id}, broadcast=True)
    session.close()


if __name__ == "__main__":
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
