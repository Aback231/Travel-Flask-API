from typing import List
import datetime

from db import db
from models.reservation import ReservationModel
from models.arrangement import ArrangementModel


class UserModel(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(80), nullable=False, unique=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(300), nullable=False)
    acc_type_requested = db.Column(db.String(50), nullable=False)
    acc_type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now())

    # Key points to arrangements created by ADMIN user id
    items = db.relationship('ArrangementModel', lazy="dynamic", backref='item')

    # Key points to arrangements reserved by TOURIST user id; many to many using reservations table
    arrangements_reservations = db.relationship("ArrangementModel", secondary="reservations", overlaps="user_reservations,reservations,user,arrangement")


    @classmethod
    def find_by_username(cls, username: str) -> "UserModel":
        return cls.query.filter_by(username=username).first()


    @classmethod
    def find_by_email(cls, email: str) -> "UserModel":
        return cls.query.filter_by(email=email).first()


    @classmethod
    def find_by_id(cls, id: int) -> "UserModel":
        return cls.query.filter_by(id=id).first()


    @classmethod
    def find_by_acc_type(cls, acc_type: int) -> List["UserModel"]:
        return cls.query.filter_by(acc_type=acc_type)


    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()


    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()