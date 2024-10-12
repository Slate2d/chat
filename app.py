from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'efnwof-2#mfne-fewm#-2dmfnppek'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
db = SQLAlchemy(app)
socketio = SocketIO(app)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(50))
    msg = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

user_nicknames = set()  # Множество для хранения никнеймов

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/get_messages')
def get_messages():
    messages = Message.query.order_by(Message.timestamp).all()
    return jsonify({'messages': [{'id': msg.id, 'nickname': msg.nickname, 'msg': msg.msg, 'timestamp': msg.timestamp.isoformat()} for msg in messages]})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    nickname = data.get('nickname')
    if nickname in user_nicknames:
        return jsonify({'status': 'fail', 'message': 'Никнейм уже используется.'})
    user_nicknames.add(nickname)
    return jsonify({'status': 'success'})

@app.route('/clear_chat', methods=['POST'])
def clear_chat():
    if request.json.get('secret') == 'efnwof-2#mfne-fewm#-2dmfnppek':  # Защита маршрута
        Message.query.delete()
        db.session.commit()
        socketio.emit('chat_cleared')  # Отправка события очищенного чата
        return jsonify({'status': 'success', 'message': 'Чат очищен'})
    else:
        return jsonify({'status': 'fail', 'message': 'Не авторизовано'})

@socketio.on('new_message')
def new_message(data):
    nickname = data['nickname']
    msg = data['msg']
    message = Message(nickname=nickname, msg=msg)
    db.session.add(message)
    db.session.commit()
    emit('message', {'id': message.id, 'nickname': nickname, 'msg': msg}, broadcast=True)

@socketio.on('delete_message')
def delete_message(data):
    message_id = data['id']
    message = Message.query.get(message_id)
    now = datetime.utcnow()
    if message and now - message.timestamp < timedelta(minutes=5):
        db.session.delete(message)
        db.session.commit()
        emit('message_deleted', {'id': message_id}, broadcast=True)
    else:
        emit('message_delete_failed', {'id': message_id}, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
