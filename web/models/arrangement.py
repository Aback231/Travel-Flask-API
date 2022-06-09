from typing import List

from db import db


class ArrangementModel(db.Model):
    __tablename__ = "arrangements"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    price = db.Column(db.Float(precision=2), nullable=False)

    agencies_id = db.Column(db.Integer, db.ForeignKey("agencies.id"), nullable=False)
    agency = db.relationship("AgencyModel")

    @classmethod
    def find_by_name(cls, name: str) -> "ArrangementModel":
        return cls.query.filter_by(name=name).first()

    @classmethod
    def find_all(cls) -> List["ArrangementModel"]:
        return cls.query.all()

    def save_to_db(self) -> None:
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self) -> None:
        db.session.delete(self)
        db.session.commit()
