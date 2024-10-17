    let selectedMessage = null;
    let currentUser = null;
    const socket = io();

    window.addEventListener('load', () => {
        const savedNickname = localStorage.getItem('nickname');
        if (savedNickname) {
            fetch(`/check_nickname?nickname=${savedNickname}`)
                .then(response => response.json())
                .then(data => {
                    if (data.exists) {
                        currentUser = savedNickname;
                        document.getElementById('login').style.display = 'none';
                        document.getElementById('chat').style.display = 'block';
                        loadMessages();
                    } else {
                        localStorage.removeItem('nickname');
                        window.location.href = '/chat';
                    }
                })
                .catch(error => console.error('Error checking nickname:', error));
        }
    });

    if (Notification.permission !== "granted") {
        Notification.requestPermission();
    }

    function loadMessages() {
        fetch('/get_messages').then(response => response.json()).then(data => {
            const chatDiv = document.getElementById('chat-messages');
            chatDiv.innerHTML = '';
            data.messages.forEach(message => {
                const messageDiv = document.createElement('div');
                messageDiv.classList.add('message');
                messageDiv.setAttribute('data-id', message.id);
                messageDiv.setAttribute('data-nickname', message.nickname);
                messageDiv.innerHTML = `<b>${message.nickname}</b>: ${message.msg}`;
                messageDiv.addEventListener('click', () => {
                    if (selectedMessage) {
                        selectedMessage.classList.remove('selected');
                    }
                    messageDiv.classList.add('selected');
                    selectedMessage = messageDiv;
                });
                chatDiv.appendChild(messageDiv);
            });
        }).catch(error => console.error('Error loading messages:', error));
    }

    document.getElementById('loginButton').addEventListener('click', () => {
        const nickname = document.getElementById('nickname').value;
        if (!nickname) {
            alert("Nickname cannot be empty")
            return
        }
        fetch('/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({nickname})
        }).then(response => response.json()).then(data => {
            if (data.status === 'success') {
                currentUser = nickname;
                localStorage.setItem('nickname', nickname);
                document.getElementById('login').style.display = 'none';
                document.getElementById('chat').style.display = 'block';
                loadMessages();
            } else {
                alert('Никнейм уже используется. Попробуйте другой.');
            }
        }).catch(error => console.error('Login error:', error));
    });

    document.getElementById('sendButton').addEventListener('click', () => {
        const message = document.getElementById('message').value;
        sendMessage(message);
    });

    document.getElementById('message').addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            const message = document.getElementById('message').value;
            sendMessage(message);
        }
    });

    document.getElementById('nickname').addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            const nickname = document.getElementById('nickname').value;
            sendLogin(nickname)

        }
    });

    function sendLogin(nickname) {
        if (!nickname) {
            alert("Message cannot be empty")
            return
        }
        fetch('/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({nickname})
        }).then(response => response.json()).then(data => {
            if (data.status === 'success') {
                currentUser = nickname;
                localStorage.setItem('nickname', nickname);
                document.getElementById('login').style.display = 'none';
                document.getElementById('chat').style.display = 'block';
                loadMessages();
            } else {
                alert('Никнейм уже используется. Попробуйте другой.');
            }
        }).catch(error => console.error('Login error:', error));
    }

    function sendMessage(message) {
        if (!message) {
            alert("Message cannot be empty")
            return
        }
        socket.emit('new_message', {nickname: currentUser, msg: message});
        document.getElementById('message').value = '';
    }

    document.getElementById('deleteButton').addEventListener('click', () => {
        if (selectedMessage) {
            const messageId = selectedMessage.getAttribute('data-id');
            const messageNickname = selectedMessage.getAttribute('data-nickname');
            if (currentUser === messageNickname) {
                socket.emit('delete_message', {id: messageId});
            } else {
                alert('Вы можете удалять только свои сообщения.');
            }
        } else {
            alert('Выберите сообщение для удаления.');
        }
    });

    socket.on('disconnect', function () {
        console.log('Соединение с сервером потеряно. Перезагрузка страницы...');
        location.reload();
    });
    socket.on('message', (data) => {
        const chatDiv = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.setAttribute('data-id', data.id);
        messageDiv.setAttribute('data-nickname', data.nickname);
        messageDiv.innerHTML = `<b>${data.nickname}</b>: ${data.msg}`;
        messageDiv.addEventListener('click', () => {
            if (selectedMessage) {
                selectedMessage.classList.remove('selected');
            }
            messageDiv.classList.add('selected');
            selectedMessage = messageDiv;
        });
        chatDiv.appendChild(messageDiv);
        chatDiv.scrollTop = chatDiv.scrollHeight;  // Прокрутка вниз для нового сообщения
    });

    socket.on('message_deleted', (data) => {
        const messageDiv = document.querySelector(`.message[data-id='${data.id}']`);
        if (messageDiv) {
            messageDiv.remove();
        }
    });


    socket.on('message_delete_failed', (data) => {
        alert('Сообщение не может быть удалено.');
    });

    socket.on('chat_cleared', () => {
        const chatDiv = document.getElementById('chat-messages');
        chatDiv.innerHTML = '';
    });

    socket.on('mentioned', (data) => {
        if (data.user === currentUser) {
            const mentionDiv = document.getElementById('mention-notification');
            const mentionText = document.getElementById('mention-text');
            mentionText.textContent = `Вас упомянул ${data.nickname}: ${data.message}`;
            mentionDiv.style.display = 'block';
            console.log("user finded")

            const mentionSound = document.getElementById('mention-sound');
            console.log("sound finded")
            mentionSound.play();
            console.log("sound played")
            alert(`Вас упомянули в сообщении: ${data.nickname}: ${data.message}`);

            setTimeout(() => {
                mentionDiv.style.display = 'none';
            }, 5000);
        }
    });
