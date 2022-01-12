import sqlalchemy as sql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from settings import db

Base = declarative_base()
engine = sql.create_engine(db)
Session = sessionmaker(bind=engine)
session = Session()


class User(Base):
    __tablename__ = 'user'
    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    first_name = sql.Column(sql.String)
    last_name = sql.Column(sql.String)
    id_vk = sql.Column(sql.Integer, unique=True)
    city = sql.Column(sql.Integer)
    age_from = sql.Column(sql.Integer)
    age_to = sql.Column(sql.Integer)
    sex = sql.Column(sql.Integer)


class Match(Base):
    __tablename__ = 'match'
    id = sql.Column(sql.Integer, primary_key=True, autoincrement=True)
    first_name = sql.Column(sql.String)
    last_name = sql.Column(sql.String)
    link = sql.Column(sql.String)
    id_vk = sql.Column(sql.Integer, unique=True)
    id_user = sql.Column(sql.Integer, sql.ForeignKey('user.id_vk', ondelete='CASCADE'))


class BlackList(Base):
    __tablename__ = 'black_list'
    id = sql.Column(sql.Integer, primary_key=True)
    id_vk = sql.Column(sql.Integer, unique=True)
    first_name = sql.Column(sql.String)
    last_name = sql.Column(sql.String)
    link = sql.Column(sql.String)


def create_tables():
    Base.metadata.create_all(engine)


def add_user(id_vk):
    session.expire_on_commit = False
    new_user = User(id_vk=id_vk)
    session.add(new_user)
    session.commit()
    return True


def add_match(first_name, last_name, link, id_vk, id_user):
    session.expire_on_commit = False
    add_new_match = Match(first_name=first_name, last_name=last_name, link=link, id_vk=id_vk, id_user=id_user)
    session.add(add_new_match)
    session.commit()
    return True


def register_user(id_vk):
    session.expire_on_commit = False
    new_user = User(id_vk=id_vk)
    session.add(new_user)
    session.commit()
    return True


def check(user_id):
    current_user_id = session.query(User).filter_by(id_vk=user_id).first()
    fav_users = session.query(Match).filter_by(id_user=current_user_id.id_vk).all()
    return fav_users


def add_to_black_list(id_vk, first_name, last_name, link):
    add_bl = BlackList(id_vk=id_vk, first_name=first_name, last_name=last_name, link=link)
    session.add(add_bl)
    session.commit()
    return True
