# app.py

from flask import Flask, request
from flask_restx import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields
from prettytable import prettytable

MOV_POST = {
    "title": "Новый фильм",
    "description": "новое описание",
    "trailer": "https://www",
    "year": 1111,
    "rating": 1.1,
    "genre_id": 1,
    "director_id": 1,
}
MOV_PUT = {
    "description": "Новое описание для фильма, теперь и рейтинг будет другой",
    "rating": 6.6,
}
DIR_POST = {
    "name": "NO_NAME"
}
DIR_PUT = {
    "name": "New director name"
}
GEN_POST = {
    "name": "NO_GENRE"
}
GEN_PUT = {
    "name": "New GENRE"
}

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False
db = SQLAlchemy(app)

api = Api(app)
mov_ns = api.namespace('movies')
dir_ns = api.namespace('directors')
gen_ns = api.namespace('genres')


class Movie(db.Model):
    __tablename__ = 'movie'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.String(255))
    trailer = db.Column(db.String(255))
    year = db.Column(db.Integer)
    rating = db.Column(db.Float)
    genre_id = db.Column(db.Integer, db.ForeignKey("genre.id"))
    genre = db.relationship("Genre")
    director_id = db.Column(db.Integer, db.ForeignKey("director.id"))
    director = db.relationship("Director")


# 2. сериализация модели
class MovieSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str()
    description = fields.Str()
    trailer = fields.Str()
    year = fields.Int()
    rating = fields.Float()
    genre_id = fields.Int()
    director_id = fields.Int()


mov_schema = MovieSchema()
mov_schemas = MovieSchema(many=True)


class Director(db.Model):
    __tablename__ = 'director'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


# 2. сериализация модели
class DirectorSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()


dir_schema = DirectorSchema()
dir_schemas = DirectorSchema(many=True)


class Genre(db.Model):
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


# 2. сериализация модели
class GenreSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()


gen_schema = GenreSchema()
gen_schemas = GenreSchema(many=True)


# 2. Сlass based view (CBV) для обработки GET-запроса:
# - `/movies` — возвращает список всех фильмов, разделенный по страницам;
# - `/movies/<id>` — возвращает подробную информацию о фильме.
@mov_ns.route('/')
class MoviesView(Resource):
    def get(self):  # TODO фильмов, разделенный по страницам
        the_query = db.session.query(Movie)  # Movie.query.all()
        # получим аргументы
        args = request.args
        director_id = args.get('director_id')
        if director_id is not None:  # используем их в фильтрах
            the_query = the_query.filter(Movie.director_id == director_id)
        genre_id = args.get('genre_id')
        if genre_id is not None:
            the_query = the_query.filter(Movie.genre_id == genre_id)
        # 1*
        # возвращ. фильмы с определенным режиссером и жанром по запросу типа /movies/?director_id=2&genre_id=4
        all_movies = the_query.all()  # выполняем запрос
        return mov_schemas.dump(all_movies), 200

    def post(self):
        the_movie = mov_schema.load(request.json)  # ТУТ ВОЗНИКАЕТ ОШИБКА:
        # marshmallow.exceptions.ValidationError: {'_schema': ['Invalid input type.']},
        # если запрос передаю через ПОСТМАНа,
        # при отправлении запроса из МАЙН - всё срабатывает без ошибок!
        # КАК С ЭТИМ РАЗБИРАТЬСЯ - НЕ ПОНИМАЮ :(
        db.session.add(Movie(**the_movie))
        db.session.commit()
        return None, 201


@mov_ns.route('/<int:uid>')
class MovieView(Resource):
    def get(self, uid: int):
        movie = Movie.query.get(uid)
        if movie is None:
            return "", 404
        return mov_schema.dump(movie), 200

    # удалить данные с соответсвующим id
    def delete(self, uid: int):
        note = Movie.query.get(uid)
        if note is None:
            return "", 404
        db.session.delete(note)
        db.session.commit()
        return "", 204

    # обновление по идентификатору
    def put(self, uid: int):
        note = Movie.query.get(uid)
        if note is None:
            return "", 404
        rj = request.json
        if "title" in rj:
            note.title = rj.get("title")
        if "description" in rj:
            note.description = rj.get("description")
        if "trailer" in rj:
            note.trailer = rj.get("trailer")
        if "year" in rj:
            note.year = rj.get("year")
        if "rating" in rj:
            note.rating = rj.get("rating")
        if "genre_id" in rj:
            note.genre_id = rj.get("genre_id")
        if "director_id" in rj:
            note.director_id = rj.get("director_id")
        db.session.add(note)
        db.session.commit()
        return "", 204


# 2* реализаця GET, POST для режиссера
@dir_ns.route('/')
class DView(Resource):
    def get(self):
        director = db.session.query(Director).all()
        if director is None:
            return {}, 404
        return dir_schemas.dump(director), 200

    def post(self):
        rj = request.json
        new_note = Director(**rj)
        with db.session.begin():
            db.session.add(new_note)
        return "", 201


# 2* реализаця GET, PUT, DELETE для режиссера c ID
@dir_ns.route('/<int:uid>')
class DirView(Resource):
    def get(self, uid: int):
        director = db.session.query(Director).filter(Director.id == uid).first()
        if director is None:
            return {}, 404
        return dir_schema.dump(director), 200

    # обновление по идентификатору
    def put(self, uid: int):
        note = Director.query.get(uid)
        if note is None:
            return "", 404
        rj = request.json
        if "name" in rj:
            note.name = rj.get("name")
        db.session.add(note)
        db.session.commit()
        return "", 204

    # удалить данные с соответсвующим id
    def delete(self, uid: int):
        note = Director.query.get(uid)
        if not note:
            return "", 404
        db.session.delete(note)
        db.session.commit()
        return "", 204


# 3* Реализация GET, POST для жанра.
@gen_ns.route('/')
class GView(Resource):
    def get(self):
        genre = db.session.query(Genre).all()
        if genre is None:
            return {}, 404
        return gen_schemas.dump(genre), 200

    def post(self):
        rj = request.json
        new_note = Genre(**rj)
        with db.session.begin():
            db.session.add(new_note)
        return "", 201


# 3* Реализация методов GET, PUT, DELETE для жанра c ID
@gen_ns.route('/<int:uid>')
class GenView(Resource):
    def get(self, uid: int):
        genre = db.session.query(Genre).filter(Genre.id == uid).first()
        if genre is None:
            return {}, 404
        return gen_schema.dump(genre), 200

    # обновление по идентификатору
    def put(self, uid: int):
        note = Genre.query.get(uid)
        if not note:
            return "", 404
        rj = request.json
        if "name" in rj:
            note.name = rj.get("name")
        db.session.add(note)
        db.session.commit()
        return "", 204

    # удалить данные с соответсвующим id
    def delete(self, uid: int):
        note = Genre.query.get(uid)
        if not note:
            return "", 404
        db.session.delete(note)
        db.session.commit()
        return "", 204


if __name__ == '__main__':
#    app.run(debug=True)

# ТЕСТИРУЕМЫЕ ВАРИАНТЫ:
    client = app.test_client()
# 1
    #response = client.post('/movies/', json=MOV_POST)
    #response = client.delete('/movies/22', json='')
    # response = client.put('/movies/22', json=MOV_PUT)
    session = db.session()
    cursor = session.execute("SELECT * FROM movie").cursor
# 2*
# response = client.post('/directors/', json=DIR_POST)
# response = client.put('/directors/21', json=DIR_PUT)
# response = client.delete('/directors/21', json='')
# session = db.session()
# cursor = session.execute("SELECT * FROM director").cursor
# 3*
# response = client.post('/genres/', json=GEN_POST)
# response = client.put('/genres/19', json=GEN_PUT)
# response = client.delete('/genres/19', json='')
# session = db.session()
# cursor = session.execute("SELECT * FROM genre").cursor

    mytable = prettytable.from_db_cursor(cursor)
    mytable.max_width = 30
    print("ТАБЛИЦА:")
    print(mytable)
