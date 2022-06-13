from ma import ma
from db import db

from models.reservation import ReservationModel
from models.user import UserModel
from models.arrangement import ArrangementModel


class ReservationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        sqla_session = db.session
        model = ReservationModel
        ordered = True
        include_fk = True
        load_instance = True

