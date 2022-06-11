from typing import List

from db import db


class ReservationModel(db.Model):
    __tablename__ = "reservations"

    id = db.Column(db.Integer, primary_key=True)
    reserver_user_id = db.Column(db.Integer, unique=False)
    arrangement_id = db.Column(db.Integer, nullable=False, unique=False)
    num_reservations = db.Column(db.Integer, nullable=False, unique=False)


    @classmethod
    def find_by_id(cls, id: int) -> "ReservationModel":
        return cls.query.filter_by(id=id).first()


    @classmethod
    def find_by_arrangement_id_and_reserver_user_id(cls, arrangement_id: int, reserver_user_id: int) -> "ReservationModel":
        return cls.query.filter_by(arrangement_id=arrangement_id, reserver_user_id=reserver_user_id).first()


    @classmethod
    def find_all(cls) -> List["ReservationModel"]:
        return cls.query.all()


    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()


    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()
