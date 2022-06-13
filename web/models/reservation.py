from typing import List

from db import db


class ReservationModel(db.Model):
    __tablename__ = "reservations"

    id = db.Column(db.Integer, primary_key=True)

    reserver_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    arrangement_id = db.Column(db.Integer, db.ForeignKey("arrangements.id"))
    num_reservations = db.Column(db.Integer, unique=False)

    user = db.relationship("UserModel", backref="reservations")
    arrangement = db.relationship("ArrangementModel", backref="reservations")


    @classmethod
    def find_by_id(cls, reserver_user_id: int) -> List["ReservationModel"]:
        return cls.query.filter_by(reserver_user_id=reserver_user_id)


    @classmethod
    def find_by_arrangement_id_and_reserver_user_id(cls, arrangement_id: int, reserver_user_id: int) -> "ReservationModel":
        return cls.query.filter_by(arrangement_id=arrangement_id, reserver_user_id=reserver_user_id).first()


    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()


    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()
