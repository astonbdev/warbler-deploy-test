"""User View tests."""

# run these tests like:
#
#    FLASK_DEBUG=False python -m unittest test_user_views.py


import os
from unittest import TestCase

from bs4 import BeautifulSoup

from models import Follow, Like, Message, User, db, dbx

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler_test"

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


class UserBaseViewTestCase(TestCase):
    def setUp(self):
        dbx(db.delete(User))
        db.session.commit()

        u1 = User.signup("u1", "u1@email.com", "password", None)
        u2 = User.signup("u2", "u2@email.com", "password", None)
        u3 = User.signup("u3", "u3@email.com", "password", None)
        u4 = User.signup("u4", "u4@email.com", "password", None)
        db.session.add_all([u1, u2, u3, u4])
        db.session.commit()

        self.u1_id = u1.id
        self.u2_id = u2.id
        self.u3_id = u3.id
        self.u4_id = u4.id

    def tearDown(self):
        db.session.rollback()


class UserListShowTestCase(UserBaseViewTestCase):
    def setUp(self):
        super().setUp()
        m1 = Message(text="text", user_id=self.u1_id)
        db.session.add(m1)

    def test_users_index(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get("/users")

            self.assertIn("@u1", str(resp.data))
            self.assertIn("@u2", str(resp.data))
            self.assertIn("@u3", str(resp.data))
            self.assertIn("@u4", str(resp.data))

    def test_users_search(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get("/users?q=1")

            self.assertIn("@u1", str(resp.data))
            self.assertNotIn("@u2", str(resp.data))

    def test_user_show(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f"/users/{self.u1_id}")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@u1", str(resp.data))

    def test_users_show_no_authentication(self):
        with app.test_client() as c:
            resp = c.get("/users", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))
            self.assertIn("Happening?", str(resp.data))

    def test_single_user_show_no_authentication(self):
        with app.test_client() as c:
            resp = c.get(f"/users/{self.u1_id}", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))
            self.assertIn("Happening?", str(resp.data))

    def test_user_delete_profile(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post("/users/delete", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Join Warbler today.", str(resp.data))

    def test_user_delete_profile_no_authentication(self):
        with app.test_client() as c:
            resp = c.post("/users/delete", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))
            self.assertIn("Happening?", str(resp.data))


class UserProfileViewTestCase(UserBaseViewTestCase):
    def test_view_profile_form(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get("/users/profile")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Edit Your Profile", str(resp.data))

    def test_view_profile_form_no_authentication(self):
        with app.test_client() as c:
            resp = c.get("/users/profile", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))
            self.assertIn("Happening?", str(resp.data))

    def test_edit_profile(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(
                "/users/profile",
                data={
                    "username": "updatedU",
                    "password": "password",
                    "email": "email@email.com",
                    "image_url": "",
                    "header_image_url": "",
                    "bio": "",
                },
                follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@updatedU", str(resp.data))

    def test_edit_profile_invalid_email(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(
                "/users/profile",
                data={
                    "username": "updatedU",
                    "email": "t",
                    "password": "password",
                    "image_url": "",
                    "header_image_url": "",
                    "bio": "",
                },
                follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Invalid email address.", str(resp.data))

    def test_edit_profile_invalid_password(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(
                "/users/profile",
                data={
                    "username": "updatedU",
                    "password": "wrongpassword",
                    "email": "email@email.com",
                    "image_url": "",
                    "header_image_url": "",
                    "bio": "",
                },
                follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Wrong password, please try again.", str(resp.data))

    def test_edit_profile_dupe_username(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(
                "/users/profile",
                data={
                    "username": "u2",
                    "password": "password",
                    "email": "updatedemail@email.com",
                    "image_url": "",
                    "header_image_url": "",
                    "bio": "",
                },
                follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Username already taken", str(resp.data))


class UserLikeTestCase(UserBaseViewTestCase):
    def setUp(self):
        super().setUp()
        m1 = Message(text="text", user_id=self.u2_id)
        db.session.add_all([m1])
        db.session.flush()
        k1 = Like(user_id=self.u1_id, message_id=m1.id)
        db.session.add_all([k1])
        db.session.commit()

        self.m1_id = m1.id

    def test_user_show_with_likes(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f"/users/{self.u1_id}")

            self.assertEqual(resp.status_code, 200)

            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})

            self.assertEqual(len(found), 4)
            self.assertIn("1", found[3].text)  # Test for a count of 1 like

    def test_add_like(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u3_id

            resp = c.post(
                f"/messages/{self.m1_id}/like",
                data={"came_from": f"/messages/{self.m1_id}"},
                follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            # check that we get redirected back to the correct location
            self.assertIn("message display page", str(resp.data))

            q = db.select(Like).where(Like.message_id == self.m1_id)
            likes = dbx(q).scalars().all()
            self.assertEqual(len(likes), 2)

    def test_remove_like(self):
        q = db.select(Like).where(
            Like.user_id == self.u1_id and Like.message_id == self.m1_id
        )
        k = dbx(q).scalar_one_or_none()
        self.assertIsNotNone(k)

        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(
                f"/messages/{self.m1_id}/like",
                data={"came_from": "/"},
                follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("home page for logged-in users", str(resp.data))

            q = db.select(Like).where(Like.message_id == self.m1_id)
            likes = dbx(q).all()
            self.assertEqual(len(likes), 0)

    def test_toggle_like_no_authentication(self):
        with app.test_client() as c:
            resp = c.post(
                f"/messages/{self.m1_id}/like", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))
            self.assertIn("Happening?", str(resp.data))

    def test_show_likes_page(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f"/users/{self.u1_id}/likes")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@u2", str(resp.data))

    def test_show_likes_page_no_authentication(self):
        with app.test_client() as c:
            resp = c.get(
                f"/users/{self.u1_id}/likes", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))
            self.assertIn("Happening?", str(resp.data))


class UserFollowingViewTestCase(UserBaseViewTestCase):
    def setUp(self):
        super().setUp()

        # u1 followed by u2, u3
        # u2 followed by u1
        f1 = Follow(
            user_being_followed_id=self.u1_id,
            user_following_id=self.u2_id)
        f2 = Follow(
            user_being_followed_id=self.u1_id,
            user_following_id=self.u3_id)
        f3 = Follow(
            user_being_followed_id=self.u2_id,
            user_following_id=self.u1_id)

        db.session.add_all([f1, f2, f3])
        db.session.commit()

    def test_user_show_with_follows(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f"/users/{self.u1_id}")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@u1", str(resp.data))

            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})

            self.assertEqual(len(found), 4)
            # Test for a count of 1 following
            self.assertIn("1", found[1].text)
            self.assertIn("2", found[2].text)  # Test for a count of 2 follower

    def test_show_following(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f"/users/{self.u1_id}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@u1", str(resp.data))
            self.assertIn("@u2", str(resp.data))
            self.assertNotIn("@u3", str(resp.data))

    def test_show_followers(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.get(f"/users/{self.u2_id}/followers")
            self.assertIn("@u1", str(resp.data))
            self.assertNotIn("@u3", str(resp.data))

    def test_show_followers_no_authentication(self):
        with app.test_client() as c:
            resp = c.get(
                f"/users/{self.u1_id}/followers",
                follow_redirects=True
            )
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))
            self.assertIn("Happening?", str(resp.data))

    def test_add_new_follow(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(
                f"/users/follow/{self.u3_id}",
                follow_redirects=True
            )
            self.assertIn("@u3", str(resp.data))

    def test_add_new_follow_no_authentication(self):
        with app.test_client() as c:
            resp = c.get(
                f"/users/{self.u1_id}/followers",
                follow_redirects=True
            )
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))
            self.assertIn("Happening?", str(resp.data))

    def test_stop_following(self):
        with app.test_client() as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            resp = c.post(
                f"/users/stop-following/{self.u2_id}",
                follow_redirects=True
            )
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@u1", str(resp.data))
            self.assertNotIn("@u2", str(resp.data))
            self.assertNotIn("@u3", str(resp.data))

    def test_stop_following_no_authentication(self):
        with app.test_client() as c:
            resp = c.post(
                f"/users/stop-following/{self.u2_id}",
                follow_redirects=True
            )
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized.", str(resp.data))
            self.assertIn("Happening?", str(resp.data))
