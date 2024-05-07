"""Auth View tests."""

# run these tests like:
#
#    FLASK_DEBUG=False python -m unittest test_auth_views.py


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

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class AuthViewTestCase(TestCase):
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

    def tearDown(self):
        db.session.rollback()

    def test_signup_success(self):
        with app.test_client() as c:
            resp = c.post(
                "/signup",
                data={
                    "username": "newU",
                    "password": "password",
                    "email": "newEmail@email.com",
                    "image_url": "",
                },
                follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@newU", str(resp.data))

    def test_signup_dupe_username(self):
        with app.test_client() as c:
            resp = c.post(
                "/signup",
                data={
                    "username": "u1",
                    "password": "password",
                    "email": "newEmail@email.com",
                    "image_url": "",
                },
                follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Username already taken", str(resp.data))

    def test_signup_dupe_email(self):
        with app.test_client() as c:
            resp = c.post(
                "/signup",
                data={
                    "username": "newU",
                    "password": "password",
                    "email": "u1@email.com",
                    "image_url": "",
                },
                follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Username already taken", str(resp.data))

    def test_login(self):
        with app.test_client() as c:
            resp = c.post(
                "/login",
                data={
                    "username": "u1",
                    "password": "password",
                },
                follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Hello, u1!", str(resp.data))
            self.assertIn("@u1", str(resp.data))

    def test_login_wrong_password(self):
        with app.test_client() as c:
            resp = c.post(
                "/login",
                data={
                    "username": "u1",
                    "password": "badpassword",
                },
                follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Invalid credentials.", str(resp.data))
            self.assertIn("Welcome back.", str(resp.data))

    def test_login_wrong_password_username(self):
        with app.test_client() as c:
            resp = c.post(
                "/login",
                data={
                    "username": "badu1",
                    "password": "badpassword",
                },
                follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Invalid credentials.", str(resp.data))
            self.assertIn("Welcome back.", str(resp.data))

    def test_logout(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(
                "/logout",
                follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Welcome back.", str(resp.data))

    def test_logout_no_authentication(self):
        with app.test_client() as c:

            resp = c.post(
                "/logout",
                follow_redirects=True)

            self.assertIn("Access unauthorized.", str(resp.data))
            self.assertIn("Happening?", str(resp.data))