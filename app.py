from flask import Flask, render_template, request, jsonify
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
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))


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
    all_nicknames = Nickname.query.all()  # Получаем все записи из таблицы Nickname
    nickname_list = [nickname.nickname for nickname in all_nicknames]  # Список никнеймов
    print("Nicknames in the database:", nickname_list)


@app.route('/chat')
def chat():
    return render_template('chat.html')


@app.route('/get_messages')
def get_messages():
    messages = Message.query.order_by(Message.timestamp).all()
    return jsonify({'messages': [
        {'id': msg.id, 'nickname': msg.nickname, 'msg': msg.msg, 'timestamp': msg.timestamp.isoformat()} for msg in
        messages]})


@app.route('/ping')
def ping():
    return '', 200  # Возвращает код 200 OK


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    usernickname = data.get('nickname')

    # Проверка, есть ли никнейм в базе данных
    existing_nickname = Nickname.query.filter_by(nickname=usernickname).first()

    if existing_nickname:
        return jsonify({'status': 'fail', 'message': 'Никнейм уже используется.'})

    # Добавление никнейма в базу данных
    new_nickname = Nickname(nickname=usernickname)
    db.session.add(new_nickname)
    db.session.commit()

    return jsonify({'status': 'success'})


@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    if request.json.get('secret') == 'fwenfwo-23498##12ojdp_emfw0o':  # Защита маршрута
        Message.query.delete()
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
    all_nicknames = Nickname.query.all()  # Получаем все записи из таблицы Nickname
    nickname_list = [nickname.nickname for nickname in all_nicknames]  # Список никнеймов
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
    message = Message.query.get(message_id)
    now = datetime.now(timezone.utc)
    if message and now - message.timestamp < timedelta(minutes=5):
        db.session.delete(message)
        db.session.commit()
        emit('message_deleted', {'id': message_id}, broadcast=True)
    else:
        emit('message_delete_failed', {'id': message_id}, broadcast=True)


if __name__ == "__main__":
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
