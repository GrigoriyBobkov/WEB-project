import datetime
import sqlalchemy
from sqlalchemy import orm
from flask_login import UserMixin

from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True,
                           autoincrement=True)
    username = sqlalchemy.Column(sqlalchemy.String,
                                 index=True,
                                 unique=True,
                                 nullable=False)
    password = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)

    saved_places = orm.relationship("SavedPlace", back_populates="user")
    routes = orm.relationship("Route", back_populates="user")

    def __repr__(self):
        return f'<User> {self.id} {self.username}'