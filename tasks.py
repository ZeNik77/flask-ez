import sqlalchemy
from db_session import SqlAlchemyBase


class Task(SqlAlchemyBase):
    __tablename__ = 'tasks'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    glob_id = sqlalchemy.Column(sqlalchemy.Integer, unique=True)
    topic_id = sqlalchemy.Column(sqlalchemy.Integer)
    task = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)