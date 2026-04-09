from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os

from data import db_session
from data.users import User
from forms.user import RegisterForm, LoginForm

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, int(user_id))


@app.route('/')
def index():
    return render_template('index.html', title='Главная')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        db_sess = db_session.create_session()

        if db_sess.query(User).filter(User.email == form.email.data).first():
            flash('Пользователь с таким email уже существует', 'danger')
            return render_template('register.html', title='Регистрация', form=form)

        user = User(
            name=form.name.data,
            email=form.email.data
        )
        user.set_password(form.password.data)

        db_sess.add(user)
        db_sess.commit()

        flash('Регистрация успешно завершена! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash(f'С возвращением, {user.name}!', 'success')

            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Неверный email или пароль', 'danger')

    return render_template('login.html', title='Вход', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы успешно вышли из системы', 'info')
    return redirect(url_for('index'))


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', title='Личный кабинет')


if __name__ == '__main__':
    os.makedirs('db', exist_ok=True)

    db_session.global_init("db/travel.db")

    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)