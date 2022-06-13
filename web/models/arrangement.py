from typing import List

from db import db


class ArrangementModel(db.Model):
    __tablename__ = "arrangements"

    id = db.Column(db.Integer, primary_key=True)
    destination = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float(precision=2), nullable=False)
    date_start = db.Column(db.String(10), nullable=False)
    date_end = db.Column(db.String(10), nullable=False)
    nr_places_available = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    tour_guide_id = db.Column(db.Integer)

    users_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    ## If you use backref you don't need to declare the relationship on the second table !!!
    user_reservations = db.relationship("UserModel", secondary="reservations", overlaps="user_reservations,reservations,user,arrangement")


    @classmethod
    def find_by_name(cls, destination: str) -> "ArrangementModel":
        return cls.query.filter_by(destination=destination).first()


    @classmethod
    def find_by_id(cls, id: int) -> "ArrangementModel":
        return cls.query.filter_by(id=id).first()

    
    @classmethod
    def find_by_description(cls, description: str) -> "ArrangementModel":
        return cls.query.filter_by(description=description).first()


    @classmethod
    def find_all_by_tour_guide_id(cls, tour_guide_id: int) -> List["ArrangementModel"]:
        return cls.query.filter_by(tour_guide_id=tour_guide_id)


    @classmethod
    def find_all(cls) -> List["ArrangementModel"]:
        return cls.query.all()


    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()


    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()
