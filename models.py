"""SQLAlchemy models for Warbler."""

from datetime import datetime

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()

db = SQLAlchemy()
dbx = db.session.execute

DEFAULT_IMAGE_URL = (
    "https://icon-library.com/images/default-user-icon/" +
    "default-user-icon-28.jpg")

DEFAULT_HEADER_IMAGE_URL = (
    "https://images.unsplash.com/photo-1519751138087-5bf79df62d5b?ixlib=" +
    "rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=for" +
    "mat&fit=crop&w=2070&q=80")


class Follow(db.Model):
    """Connection of a follower <-> followed_user."""

    __tablename__ = 'follows'

    __table_args__ = (
        db.UniqueConstraint("user_being_followed_id", "user_following_id"),
    )

    user_being_followed_id = db.mapped_column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
        nullable=False,
    )

    user_following_id = db.mapped_column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
        nullable=False,
    )

    followed_user = db.relationship(
        "User",
        foreign_keys=[user_following_id],
        back_populates="followers_users",
    )

    following_user = db.relationship(
        "User",
        foreign_keys=[user_being_followed_id],
        back_populates="following_users",
    )


class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.mapped_column(
        db.Integer,
        db.Identity(),
        primary_key=True,
    )

    email = db.mapped_column(
        db.String(50),
        nullable=False,
        unique=True,
    )

    username = db.mapped_column(
        db.String(30),
        nullable=False,
        unique=True,
    )

    image_url = db.mapped_column(
        db.String(255),
        nullable=False,
        default=DEFAULT_IMAGE_URL,
    )

    header_image_url = db.mapped_column(
        db.String(255),
        nullable=False,
        default=DEFAULT_HEADER_IMAGE_URL,
    )

    bio = db.mapped_column(
        db.Text,
        nullable=False,
        default="",
    )

    location = db.mapped_column(
        db.String(30),
        nullable=False,
        default="",
    )

    password = db.mapped_column(
        db.String(100),
        nullable=False,
    )

    following_users = db.relationship(
        "Follow",
        foreign_keys=[Follow.user_following_id],
        back_populates="followed_user",
        cascade="all, delete-orphan",
    )

    followers_users = db.relationship(
        "Follow",
        foreign_keys=[Follow.user_being_followed_id],
        back_populates="following_user",
        cascade="all, delete-orphan",
    )

    messages = db.relationship(
        "Message",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    likes = db.relationship(
        "Like",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    @property
    def following(self):
        return [follow.following_user for follow in self.following_users]

    @property
    def followers(self):
        return [follow.followed_user for follow in self.followers_users]

    @property
    def liked_messages(self):
        return [db.session.get(Message, like.message_id) for like in self.likes]

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    @classmethod
    def signup(cls, username, email, password, image_url=DEFAULT_IMAGE_URL):
        """Sign up user.

        Hashes password and adds user to session.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
            image_url=image_url,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If this can't find matching user (or if password is wrong), returns
        False.
        """

        q = db.select(cls).filter_by(username=username)
        user = dbx(q).scalar_one_or_none()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False

    def follow(self, other_user):
        """Follow another user."""

        follow = Follow(
            user_being_followed_id=other_user.id,
            user_following_id=self.id
        )
        db.session.add(follow)

    def unfollow(self, other_user):
        """Stop following another user."""

        q = (db
            .delete(Follow)
            .filter_by(
                user_being_followed_id=other_user.id,
                user_following_id=self.id)
        )
        dbx(q)

    def is_followed_by(self, other_user):
        """Is this user followed by `other_user`?"""

        found_user_list = [
            user for user in self.followers if user == other_user]
        return len(found_user_list) == 1

    def is_following(self, other_user):
        """Is this user following `other_user`?"""

        found_user_list = [
            user for user in self.following if user == other_user]
        return len(found_user_list) == 1

    def toggle_like(self, msg):
        """Like or unlike a message."""

        if msg in self.liked_messages:
            q = db.delete(Like).filter_by(user_id=self.id, message_id=msg.id)
            dbx(q)
        else:
            like = Like(user_id=self.id, message_id=msg.id)
            db.session.add(like)


class Message(db.Model):
    """An individual message ("warble")."""

    __tablename__ = 'messages'

    id = db.mapped_column(
        db.Integer,
        db.Identity(),
        primary_key=True,
    )

    text = db.mapped_column(
        db.String(140),
        nullable=False,
    )

    timestamp = db.mapped_column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    user_id = db.mapped_column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
    )

    user = db.relationship(
        "User",
        back_populates="messages",
    )

    likes = db.relationship(
        "Like",
        back_populates="message",
        cascade="all, delete-orphan",
    )


class Like(db.Model):
    """Join table between users and messages (the join represents a like)."""

    __tablename__ = 'likes'

    user_id = db.mapped_column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        primary_key=True,
    )

    message_id = db.mapped_column(
        db.Integer,
        db.ForeignKey('messages.id', ondelete='CASCADE'),
        nullable=False,
        primary_key=True,
    )

    user = db.relationship(
        "User",
        back_populates="likes",
    )

    message = db.relationship(
        "Message",
        back_populates="likes",
    )
