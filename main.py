import os
import smtplib
from flask_gravatar import Gravatar
from datetime import date
from functools import wraps
from flask_ckeditor import CKEditor
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from forms import RegistrationForm, LoginForm, Form, CommentForm
from flask import Flask, render_template, redirect, url_for, abort, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user

app = Flask(__name__)

# db config
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# bootstrap config
Bootstrap(app)

# ckeditor config
ckeditor = CKEditor(app)

# flask_login config
login_manager = LoginManager()
login_manager.init_app(app)

# Gravatar
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print("Hello")
        return f(*args, **kwargs)

        try:
            print(current_user.id)
            if current_user.id == 1:
                return f(*args, **kwargs)
            else:
                print("else entered")
                return abort(403)
        except:

            print('Except eneterd')
            return abort(403)

    return decorated_function


# ---------------------------------------- DataBase -----------------------------------------


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(1000), nullable=False)

    posts = relationship('BlogPost', back_populates='author')
    comments = relationship('Comment', back_populates='author')
    # comments = relationship('Message', back_populates='')


class BlogPost(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    post_type = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)

    # one to many relation form users to blogpost
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    author = relationship('User', back_populates='posts')

    comments = relationship('Comment', back_populates='post')


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    author = relationship('User', back_populates='comments')

    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    post = relationship('BlogPost', back_populates='comments')


db.create_all()


# ------------------------------------- default routes ---------------------------------------------


@app.route('/')
def home():
    if current_user.is_authenticated:
        print(current_user.id)
    posts = db.session.query(BlogPost).all()
    return render_template("index.html", posts=posts, logged_in=current_user.is_authenticated,
                           current_user=current_user)


@app.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):

    curr_post = BlogPost.query.get(id)
    comment_form = CommentForm()
    user_comments = db.session.query(Comment).all()

    if comment_form.validate_on_submit():
        if current_user.is_authenticated:

            new_msg = Comment(id=len(db.session.query(Comment).all()) + 1, text=comment_form.commentBox.data, author=current_user, post=curr_post)

            db.session.add(new_msg)
            db.session.commit()
            comment_form.commentBox.data = None
            return redirect(url_for('post', id=id))
        else:
            flash('Login here to Comment on the post!')
            return redirect(url_for('login'))

    return render_template('post.html', post=curr_post, logged_in=current_user.is_authenticated, form=comment_form)


@app.route('/contact', methods=['POST'])
def form_data():

    with smtplib.SMTP('smtp.gmail.com') as connection:
        connection.starttls()
        connection.login(user=os.getenv('FROM_MAIL'), password=os.getenv('FROM_PASS'))
        connection.sendmail(from_addr=os.getenv('FROM_MAIL'), to_addrs=os.getenv('TO_MAIL'),
                            msg=f"Subject: reply to blog\n\nHey, I'm {request.form['name']}.\n{request.form['message']}\n{request.form['email']}")

    return render_template('success.html', logged_in=current_user.is_authenticated)


# ------------------------------------ Rest API methods ----------------------------------------------


@app.route('/new_post', methods=["GET", "POST"])
@admin
def make_post():
    form = Form()
    posts = db.session.query(BlogPost).all()

    if form.validate_on_submit():
        post = BlogPost(id=len(posts) + 1, author=current_user, post_type=form.post_type.data, title=form.title.data, subtitle=form.subtitle.data, body=form.body.data, date=date.today().strftime("%B %d, %Y"), img_url=form.img_url.data)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('home'))

    return render_template('make-post.html', form=form, page_title='New Post', logged_in=current_user.is_authenticated)


@app.route('/edit_post/<id>', methods=['GET', 'POST'])
@admin
def edit_post(id):
    post = BlogPost.query.get(id)
    form = Form(
        post_type=post.post_type,
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )

    if form.validate_on_submit():
        print(form.title.data)
        post.post_type = form.post_type.data
        post.title = form.title.data
        post.subtitle = form.subtitle.data
        post.body = form.body.data
        post.img_url = form.img_url.data

        db.session.commit()
        return redirect(url_for('post', id=post.id))

    return render_template('make-post.html', form=form, page_title='Edit Post', logged_in=current_user.is_authenticated)


@app.route('/delete_post/<id>', methods=['GET'])
@admin
def delete_post(id):
    print(id)
    post = BlogPost.query.get(id)
    print(post.title)
    db.session.delete(post)
    db.session.commit()

    return redirect(url_for('home'))


# --------------------------------- Authentication and Encryption ---------------------------------


@app.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegistrationForm()

    if register_form.validate_on_submit():
        email = register_form.email.data

        if User.query.filter_by(email=email).first():
            flash("Email is already registered, Login here!")
            return redirect(url_for('login'))
        hashed_pass = generate_password_hash(register_form.password.data, method='pbkdf2:sha256', salt_length=8)

        new_user = User(name=register_form.name.data, email=register_form.email.data, password=hashed_pass)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for('home'))

    return render_template('register.html', form=register_form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()

    if login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data).first()
        if not user:
            flash("Email doesn't exist, login using registered email!")
        elif not check_password_hash(user.password, login_form.password.data):
            flash("Incorrect password, Try again!")
        else:
            login_user(user)
            return redirect(url_for('home'))

    return render_template('login.html', form=login_form, logged_in=current_user.is_authenticated)


@app.route('/admin_login')
def admin_login():
    login_form = LoginForm()
    return render_template('admin_login.html', form=login_form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)
