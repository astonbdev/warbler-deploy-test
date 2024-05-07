from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField
from wtforms.validators import InputRequired, Email, Length, URL, Optional


class CSRFProtection(FlaskForm):
    """CSRFProtection form, intentionally has no fields."""


class MessageForm(FlaskForm):
    """Form for adding/editing messages."""

    text = TextAreaField('text', validators=[InputRequired()])


class UserAddForm(FlaskForm):
    """Form for adding users."""

    username = StringField(
        'Username',
        validators=[InputRequired(), Length(max=30)],
    )

    email = StringField(
        'E-mail',
        validators=[InputRequired(), Email(), Length(max=50)],
    )

    password = PasswordField(
        'Password',
        validators=[InputRequired(), Length(min=6, max=50)],
    )

    image_url = StringField(
        '(Optional) Image URL',
        validators=[Optional(), URL(), Length(max=255)]
    )


class UserEditForm(FlaskForm):
    """Form for editing users."""

    username = StringField(
        'Username',
        validators=[InputRequired(), Length(max=30)],
    )

    email = StringField(
        'Email',
        validators=[InputRequired(), Email(), Length(max=50)],
    )

    image_url = StringField(
        '(Optional) Image URL',
        validators=[Optional(), Length(max=255), URL()]
    )

    header_image_url = StringField(
        '(Optional) Header Image URL',
        validators=[Optional(), Length(max=255), URL()]
    )

    bio = TextAreaField(
        '(Optional) Tell us about yourself',
    )

    password = PasswordField(
        'Password',
        validators=[InputRequired(), Length(min=6, max=50)],
    )


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField(
        'Username',
        validators=[InputRequired(), Length(max=30)],
    )

    password = PasswordField(
        'Password',
        validators=[InputRequired(), Length(min=6, max=50)],
    )
