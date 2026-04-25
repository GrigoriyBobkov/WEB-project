from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from waitress import serve

from data import db_session
from data.users import User
from data.places import SavedPlace, Route
from forms.user import RegisterForm, LoginForm
from forms.route import RouteForm
from api.maps_api import get_coordinates, get_static_map

app = Flask(__name__)
app.config['SECRET_KEY'] = 'my-secret-key-123'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


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
        if form.password.data != form.password_again.data:
            flash('Пароли не совпадают!', 'danger')
            return render_template('register.html', title='Регистрация', form=form)

        db_sess = db_session.create_session()

        if db_sess.query(User).filter(User.username == form.username.data).first():
            flash('Пользователь с таким именем уже существует!', 'danger')
            return render_template('register.html', title='Регистрация', form=form)

        user = User(
            username=form.username.data,
            password=form.password.data
        )

        db_sess.add(user)
        db_sess.commit()

        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(
            User.username == form.username.data,
            User.password == form.password.data
        ).first()

        if user:
            login_user(user)
            flash(f'Добро пожаловать, {user.username}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль!', 'danger')

    return render_template('login.html', title='Вход', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))


@app.route('/map')
@login_required
def map_page():
    db_sess = db_session.create_session()
    routes = db_sess.query(Route).filter(Route.user_id == current_user.id).all()
    return render_template('map.html', title='Карта', city_name=None, map_url=None, zoom=15, routes=routes)


@app.route('/search', methods=['POST'])
@login_required
def search():
    city = request.form.get('city')
    zoom = request.form.get('zoom', 15)

    try:
        zoom = int(zoom)
    except:
        zoom = 15

    if zoom < 10:
        zoom = 10
    if zoom > 20:
        zoom = 20

    if not city:
        flash('Введите название города!', 'danger')
        return redirect(url_for('map_page'))

    lon, lat = get_coordinates(city)

    if lon is None or lat is None:
        flash(f'Город "{city}" не найден!', 'danger')
        return redirect(url_for('map_page'))

    map_url = get_static_map(lon, lat, zoom=zoom)

    db_sess = db_session.create_session()
    routes = db_sess.query(Route).filter(Route.user_id == current_user.id).all()

    return render_template('map.html', title='Карта', city_name=city, map_url=map_url, zoom=zoom, routes=routes,
                           search_city=city)


@app.route('/place/add_to_route_from_map', methods=['POST'])
@login_required
def add_to_route_from_map():
    route_id = request.form.get('route_id')
    place_name = request.form.get('place_name')
    place_city = request.form.get('place_city')

    if not route_id or not place_name:
        flash('Ошибка: не выбран маршрут', 'danger')
        return redirect(url_for('map_page'))

    db_sess = db_session.create_session()

    route = db_sess.query(Route).filter(
        Route.id == int(route_id),
        Route.user_id == current_user.id
    ).first()

    if not route:
        flash('Маршрут не найден', 'danger')
        return redirect(url_for('map_page'))

    existing = db_sess.query(SavedPlace).filter(
        SavedPlace.user_id == current_user.id,
        SavedPlace.name == place_name,
        SavedPlace.route_id == int(route_id)
    ).first()

    if existing:
        flash(f'"{place_name}" уже есть в маршруте "{route.name}"', 'warning')
    else:
        place = SavedPlace(
            name=place_name,
            city=place_city or 'Неизвестный город',
            place_type='город',
            user_id=current_user.id,
            route_id=int(route_id)
        )
        db_sess.add(place)
        db_sess.commit()
        flash(f'✅ "{place_name}" добавлено в маршрут "{route.name}"!', 'success')

    return redirect(url_for('map_page'))


@app.route('/place/add_to_favorite_from_map', methods=['POST'])
@login_required
def add_to_favorite_from_map():
    place_name = request.form.get('place_name')
    place_city = request.form.get('place_city')

    if not place_name:
        flash('Ошибка при добавлении в избранное', 'danger')
        return redirect(url_for('map_page'))

    db_sess = db_session.create_session()

    existing = db_sess.query(SavedPlace).filter(
        SavedPlace.user_id == current_user.id,
        SavedPlace.name == place_name,
        SavedPlace.route_id == None
    ).first()

    if existing:
        flash(f'"{place_name}" уже есть в избранном!', 'warning')
    else:
        place = SavedPlace(
            name=place_name,
            city=place_city or 'Неизвестный город',
            place_type='город',
            user_id=current_user.id,
            route_id=None
        )
        db_sess.add(place)
        db_sess.commit()
        flash(f'⭐ "{place_name}" добавлено в избранное!', 'success')

    return redirect(url_for('map_page'))


@app.route('/place/add_favorite_to_route/<int:place_id>/<int:route_id>')
@login_required
def add_favorite_to_route(place_id, route_id):
    db_sess = db_session.create_session()

    place = db_sess.query(SavedPlace).filter(
        SavedPlace.id == place_id,
        SavedPlace.user_id == current_user.id
    ).first()

    route = db_sess.query(Route).filter(
        Route.id == route_id,
        Route.user_id == current_user.id
    ).first()

    if not place or not route:
        flash('Ошибка при добавлении', 'danger')
        return redirect(url_for('profile'))

    if place.route_id is not None:
        flash(f'"{place.name}" уже в маршруте!', 'warning')
    else:
        place.route_id = route_id
        db_sess.commit()
        flash(f'✅ "{place.name}" добавлено в маршрут "{route.name}"!', 'success')

    return redirect(url_for('profile'))


@app.route('/place/remove_favorite/<int:place_id>')
@login_required
def remove_favorite(place_id):
    db_sess = db_session.create_session()
    place = db_sess.query(SavedPlace).filter(
        SavedPlace.id == place_id,
        SavedPlace.user_id == current_user.id,
        SavedPlace.route_id == None
    ).first()

    if place:
        db_sess.delete(place)
        db_sess.commit()
        flash('Место удалено из избранного', 'info')

    return redirect(url_for('profile'))


@app.route('/place/remove_from_route/<int:place_id>')
@login_required
def remove_place_from_route(place_id):
    db_sess = db_session.create_session()
    place = db_sess.query(SavedPlace).filter(
        SavedPlace.id == place_id,
        SavedPlace.user_id == current_user.id
    ).first()

    if place:
        route_id = place.route_id
        place.route_id = None
        db_sess.commit()
        flash('Место удалено из маршрута', 'info')
        return redirect(url_for('view_route', route_id=route_id))

    return redirect(url_for('profile'))


@app.route('/place/open_on_map/<int:place_id>')
@login_required
def open_place_on_map(place_id):
    db_sess = db_session.create_session()
    place = db_sess.query(SavedPlace).filter(
        SavedPlace.id == place_id,
        SavedPlace.user_id == current_user.id
    ).first()

    if not place:
        flash('Место не найдено', 'danger')
        return redirect(url_for('profile'))

    city_name = place.city if place.city else place.name
    lon, lat = get_coordinates(city_name)

    if lon is None or lat is None:
        flash(f'Не удалось найти координаты для "{city_name}"', 'danger')
        if place.route_id:
            return redirect(url_for('view_route', route_id=place.route_id))
        return redirect(url_for('profile'))

    map_url = get_static_map(lon, lat, zoom=15)
    routes = db_sess.query(Route).filter(Route.user_id == current_user.id).all()

    return render_template('map.html', title='Карта', city_name=city_name, map_url=map_url, zoom=15, routes=routes)


@app.route('/route/create', methods=['GET', 'POST'])
@login_required
def create_route():
    form = RouteForm()

    if form.validate_on_submit():
        db_sess = db_session.create_session()
        route = Route(
            name=form.name.data,
            description=form.description.data,
            user_id=current_user.id
        )
        db_sess.add(route)
        db_sess.commit()
        flash(f'Маршрут "{route.name}" создан!', 'success')
        return redirect(url_for('profile'))

    return render_template('route_form.html', title='Создание маршрута', form=form)


@app.route('/route/<int:route_id>')
@login_required
def view_route(route_id):
    db_sess = db_session.create_session()
    route = db_sess.query(Route).filter(
        Route.id == route_id,
        Route.user_id == current_user.id
    ).first()

    if not route:
        flash('Маршрут не найден', 'danger')
        return redirect(url_for('profile'))

    return render_template('route_view.html', title=route.name, route=route)


@app.route('/route/delete/<int:route_id>')
@login_required
def delete_route(route_id):
    db_sess = db_session.create_session()
    route = db_sess.query(Route).filter(
        Route.id == route_id,
        Route.user_id == current_user.id
    ).first()

    if route:
        for place in route.places:
            place.route_id = None
        db_sess.delete(route)
        db_sess.commit()
        flash('Маршрут удален', 'info')

    return redirect(url_for('profile'))


@app.route('/profile')
@login_required
def profile():
    db_sess = db_session.create_session()
    favorites = db_sess.query(SavedPlace).filter(
        SavedPlace.user_id == current_user.id,
        SavedPlace.route_id == None
    ).all()
    routes = db_sess.query(Route).filter(
        Route.user_id == current_user.id
    ).all()

    return render_template('profile.html', title='Личный кабинет',
                           favorites=favorites, routes=routes)


if __name__ == '__main__':
    os.makedirs('db', exist_ok=True)
    db_session.global_init("db/travel.db")
    # app.run(debug=True, port=8080)
    serve(app, host='0.0.0.0', port=8080)