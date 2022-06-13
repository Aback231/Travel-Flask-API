from ma import ma
from db import db

from models.arrangement import ArrangementModel
from models.user import UserModel
from models.reservation import ReservationModel
from schemas.reservation import ReservationSchema


class ArrangementSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        sqla_session = db.session
        model = ArrangementModel
        ordered = True
        include_fk = True
        load_instance = True


class ArrangementSchemaBasic(ArrangementSchema):
    class Meta(ArrangementSchema.Meta):
        exclude = ('nr_places_available', "description", "users_id", "tour_guide_id")