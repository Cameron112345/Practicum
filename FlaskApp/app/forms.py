from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import DataRequired, Email, ValidationError, EqualTo
from app.models import User
import requests

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class AddUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = EmailField('Email', validators=[Email(), DataRequired()])
    password1 = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password1')])
    isAdmin = BooleanField("Admin")
    submit = SubmitField('Add User')

    def validate_username(self, username):
        user = User.query.filter_by(username=self.username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')
        

class AddArchiveForm(FlaskForm):
    prefix = StringField('Prefix')
    recursive = BooleanField('Recursive')
    submit = SubmitField('Create Archive')

    def validate_prefix(self, prefix):
        if not requests.get('https://www.mvnu.edu' + prefix.data).ok:
            raise ValidationError('Invalid prefix')