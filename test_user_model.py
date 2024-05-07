"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from sqlalchemy.exc import IntegrityError
from unittest import TestCase
from flask_bcrypt import Bcrypt

from models import db, dbx, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database
os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

# Now we can import app
from app import app
app.app_context().push()

# instantiate Bcrypt to create hashed passwords for test data
bcrypt = Bcrypt()

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.drop_all()
db.create_all()


class UserModelTestCase(TestCase):
    def setUp(self):
        dbx(db.delete(User))
        db.session.commit()

        hashed_password = (bcrypt
            .generate_password_hash("password")
            .decode('UTF-8')
        )

        u1 = User(
            username="u1",
            email="u1@email.com",
            password=hashed_password,
            image_url=None,
        )

        u2 = User(
            username="u2",
            email="u2@email.com",
            password=hashed_password,
            image_url=None,
        )

        db.session.add_all([u1, u2])
        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id

    def tearDown(self):
        db.session.rollback()

    def test_user_model(self):
        u1 = db.session.get(User, self.u1_id)

        # User should have no messages & no followers
        self.assertEqual(len(u1.messages), 0)
        self.assertEqual(len(u1.followers), 0)

    # #################### Following tests

    def test_user_follows(self):
        u1 = db.session.get(User, self.u1_id)
        u2 = db.session.get(User, self.u2_id)

        u1.follow(u2)

        self.assertEqual(u2.following, [])
        self.assertEqual(u2.followers, [u1])
        self.assertEqual(u1.followers, [])
        self.assertEqual(u1.following, [u2])

    def test_is_following(self):
        u1 = db.session.get(User, self.u1_id)
        u2 = db.session.get(User, self.u2_id)

        u1.follow(u2)
        db.session.commit()

        self.assertTrue(u1.is_following(u2))
        self.assertFalse(u2.is_following(u1))

    def test_is_followed_by(self):
        u1 = db.session.get(User, self.u1_id)
        u2 = db.session.get(User, self.u2_id)

        u1.follow(u2)
        db.session.commit()

        self.assertTrue(u2.is_followed_by(u1))
        self.assertFalse(u1.is_followed_by(u2))

    # #################### Signup Tests

    def test_valid_signup(self):
        u3 = User.signup("u3", "u3@email.com", "password", None)

        self.assertEqual(u3.username, "u3")
        self.assertEqual(u3.email, "u3@email.com")
        self.assertNotEqual(u3.password, "password")
        # Bcrypt strings should start with $2b$
        self.assertTrue(u3.password.startswith("$2b$"))

    def test_invalid_signup(self):
        # Assert that user signup raises an integrity error when we make a user
        # with the same username

        with self.assertRaises(IntegrityError):
            User.signup("u1", "u1@email.com", "password", None)
            db.session.commit()

    # #################### Authentication Tests

    def test_valid_authentication(self):
        u1 = db.session.get(User, self.u1_id)
        u = User.authenticate("u1", "password")
        self.assertEqual(u, u1)

    def test_invalid_username(self):
        self.assertFalse(User.authenticate("bad-username", "password"))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate("u1", "bad-password"))
