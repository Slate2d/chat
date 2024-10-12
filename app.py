from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

chat_msgs = []  # Хранение сообщений
MAX_MESSAGES_COUNT = 100
user_nicknames = set()  # Множество для хранения никнеймов

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/get_messages')
def get_messages():
    return jsonify({'messages': [{'id': msg[0], 'nickname': msg[1], 'msg': msg[2], 'timestamp': msg[3].isoformat()} for msg in chat_msgs]})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    nickname = data.get('nickname')
    if nickname in user_nicknames:
        return jsonify({'status': 'fail', 'message': 'Никнейм уже используется.'})
    user_nicknames.add(nickname)
    return jsonify({'status': 'success'})

@socketio.on('new_message')
def new_message(data):
    global chat_msgs
    nickname = data['nickname']
    msg = data['msg']
    message_id = len(chat_msgs) + 1  # Простой способ создания уникального идентификатора
    timestamp = datetime.now()
    chat_msgs.append((message_id, nickname, msg, timestamp))
    print(f"Добавлено сообщение: {message_id}, {nickname}, {msg}, {timestamp}")  # Отладка
    if len(chat_msgs) > MAX_MESSAGES_COUNT:
        chat_msgs = chat_msgs[len(chat_msgs) // 2:]
    emit('message', {'id': message_id, 'nickname': nickname, 'msg': msg}, broadcast=True)

@socketio.on('delete_message')
def delete_message(data):
    global chat_msgs
    message_id = int(data['id'])
    print(f"Json распакован, id---{message_id}")
    print(f"type1---{type(message_id)}")
    print(f"type2---{type(chat_msgs[1][0])}")

    now = datetime.now()
    for i, (msg_id, nickname, msg, timestamp) in enumerate(chat_msgs):
        if msg_id == message_id:
            print(f"Сообщение найдено: {msg_id}, текущее время: {now}, время отправки: {timestamp}")  # Отладка
            if now - timestamp < timedelta(minutes=5):
                chat_msgs.pop(i)
                emit('message_deleted', {'id': message_id}, broadcast=True)
                return
            else:
                print("Сообщение старше 5 минут")  # Отладка
        else:
            print(f"Сообщение не найдено: {message_id}")  # Отладка
    emit('message_delete_failed', {'id': message_id}, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, debug=True)
