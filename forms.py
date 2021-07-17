from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, url
from flask_ckeditor import CKEditorField
from wtforms import StringField, IntegerField, SubmitField, TextAreaField


class Form(FlaskForm):
    post_type = IntegerField('Post type', validators=[DataRequired()], render_kw={"placeholder": "like 1 2 3 ..."})
    title = StringField('Blog title', validators=[DataRequired()])
    subtitle = StringField('subtitle', validators=[DataRequired()])
    body = CKEditorField('Blog Content', validators=[DataRequired()], render_kw={"rows": 10})
    img_url = StringField('Image url', validators=[DataRequired(), url()])
    submit = SubmitField('Submit Post')


class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()], render_kw={'placeholder': 'Enter your name'})
    email = StringField('Email', validators=[DataRequired()], render_kw={'placeholder': 'email...'})
    password = StringField('Password', validators=[DataRequired()], render_kw={'placeholder': 'password...'})
    submit = SubmitField('Sign me up')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()], render_kw={'placeholder': 'your email...'})
    password = StringField('Password', validators=[DataRequired()], render_kw={'placeholder': 'password...'})
    submit = SubmitField('Let me in')


class CommentForm(FlaskForm):
    commentBox = TextAreaField('', validators=[DataRequired()], render_kw={"rows": 10})
    submit = SubmitField('Post Comment')