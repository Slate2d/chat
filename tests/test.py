import unittest
from chat.app import app, db, Message


class MessageModelTest(unittest.TestCase):

    def setUp(self):
        self.app = app
        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

        self.app_context.pop()

    def test_add_message(self):
        new_message = Message(msg="Test message")
        db.session.add(new_message)
        db.session.commit()

        message_in_db = Message.query.filter_by(msg="Test message").first()
        self.assertIsNotNone(message_in_db)

    def test_delete_message(self):
        new_message = Message(msg="Message to delete")
        db.session.add(new_message)
        db.session.commit()

        message_in_db = Message.query.filter_by(msg="Message to delete").first()
        self.assertIsNotNone(message_in_db)

        db.session.delete(message_in_db)
        db.session.commit()

        deleted_message = Message.query.filter_by(msg="Message to delete").first()
        self.assertIsNone(deleted_message)

    def test_update_message(self):
        new_message = Message(msg="Old message")
        db.session.add(new_message)
        db.session.commit()

        # Обновляем сообщение
        message_in_db = Message.query.filter_by(msg="Old message").first()
        message_in_db.msg = "Updated message"
        db.session.commit()

        updated_message = Message.query.filter_by(msg="Updated message").first()
        self.assertIsNotNone(updated_message)
        self.assertEqual(updated_message.msg, "Updated message")

    def test_get_all_messages(self):
        messages = [
            Message(msg="First message"),
            Message(msg="Second message"),
            Message(msg="Third message")
        ]
        db.session.add_all(messages)
        db.session.commit()

        all_messages = Message.query.all()
        self.assertEqual(len(all_messages), 3)
        self.assertIn(messages[0], all_messages)
        self.assertIn(messages[1], all_messages)
        self.assertIn(messages[2], all_messages)

    def test_message_exists_after_addition(self):
        new_message = Message(msg="Check existence")
        db.session.add(new_message)
        db.session.commit()

        message_in_db = Message.query.filter_by(msg="Check existence").first()
        self.assertIsNotNone(message_in_db)

    def test_message_not_exists_after_deletion(self):
        new_message = Message(msg="To be deleted")
        db.session.add(new_message)
        db.session.commit()

        message_in_db = Message.query.filter_by(msg="To be deleted").first()
        self.assertIsNotNone(message_in_db)

        db.session.delete(message_in_db)
        db.session.commit()

        deleted_message = Message.query.filter_by(msg="To be deleted").first()
        self.assertIsNone(deleted_message)


if __name__ == '__main__':
    unittest.main()
