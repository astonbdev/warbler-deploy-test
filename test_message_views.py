"""Message View tests."""

# run these tests like:
#
#    FLASK_DEBUG=False python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, dbx, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"
os.environ["FLASK_DEBUG"] = "0"

# Now we can import app

from app import app, CURR_USER_KEY
app.app_context().push()

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageBaseViewTestCase(TestCase):
    def setUp(self):
        dbx(db.delete(User))
        db.session.commit()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        db.session.flush()

        m1 = Message(text="m1-text", user_id=u1.id)
        db.session.add_all([m1])
        db.session.commit()

        self.u1_id = u1.id
        self.m1_id = m1.id


class MessageAddViewTestCase(MessageBaseViewTestCase):
    def test_add_message(self):
        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            # Now, that session setting is saved, so we can have
            # the rest of ours test
            resp = c.post("/messages/new", data={"text": "Hello"})

            self.assertEqual(resp.status_code, 302)

            q = db.select(Message).filter_by(text="Hello")
            message = dbx(q).scalar_one_or_none()
            self.assertIsNotNone(message)

    def test_add_no_session(self):
        with app.test_client() as c:
            resp = c.post(
                "/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_add_invalid_user(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 987654321  # user does not exist

            resp = c.post(
                "/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))


class MessageShowViewTestCase(MessageBaseViewTestCase):
    def test_message_show(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f'/messages/{self.m1_id}')
            self.assertEqual(resp.status_code, 200)
            self.assertIn("m1-text", str(resp.data))

    def test_message_show_no_authentication(self):
        with app.test_client() as c:
            resp = c.get(f'/messages/{self.m1_id}', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))
            self.assertIn("Happening?", str(resp.data))

    def test_invalid_message_show(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get('/messages/987654321')

            self.assertEqual(resp.status_code, 404)


class MessageDeleteViewTestCase(MessageBaseViewTestCase):
    def test_message_delete(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(
                f"/messages/{self.m1_id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            m1 = db.session.get(Message, self.m1_id)
            self.assertIsNone(m1)

    def test_unauthorized_message_delete(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 76543 # a user who is not the message's author

            resp = c.post(
                f"/messages/{self.m1_id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            m1 = db.session.get(Message, self.m1_id)
            self.assertIsNotNone(m1)

    def test_message_delete_no_authentication(self):
        with app.test_client() as c:
            resp = c.post(
                f"/messages/{self.m1_id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            m1 = db.session.get(Message, self.m1_id)
            self.assertIsNotNone(m1)
