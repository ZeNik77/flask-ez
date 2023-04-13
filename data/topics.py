import sqlalchemy
from .db_session import SqlAlchemyBase


class Topic(SqlAlchemyBase):
    __tablename__ = 'topics'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    glob_id = sqlalchemy.Column(sqlalchemy.Integer,
                                unique=True)
    topic = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)