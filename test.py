import unittest
import json
from app import app

class ChatTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_get_messages(self):
        response = self.app.get('/get_messages')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('messages', data)

    def test_new_message(self):
        response = self.app.post('/new_message', json={"nickname": "user", "msg": "Hello!"})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')

    def test_delete_message(self):
        # Add message first
        self.app.post('/new_message', json={"nickname": "user", "msg": "Test message"})
        # Attempt to delete
        response = self.app.post('/delete_message/1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')

if __name__ == '__main__':
    unittest.main()
