from ma import ma

from models.reservation import ReservationModel
from models.user import UserModel
from models.arrangement import ArrangementModel


class ReservationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ReservationModel
        ordered = True
        include_fk = True
        load_instance = True
